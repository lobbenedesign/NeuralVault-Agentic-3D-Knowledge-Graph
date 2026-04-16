"""
neuralvault.core.hnsw
─────────────────────
Implementazione dell'indice HNSW (Hierarchical Navigable Small World) con
adaptive sub-graph promotion.

HNSW standard: O(log N) per inserimento e ricerca.
AdaptiveHNSW:  O(log N) in media, sub-lineare per sub-spazi frequenti.

Riferimento paper: "Efficient and robust approximate nearest neighbor search
using Hierarchical Navigable Small World graphs" (Malkov & Yashunin, 2018).

La nostra estensione chiave: il metodo _promote_subgraph() che aumenta
dinamicamente la connettività locale delle zone più interrogate dall'agente.
"""

from __future__ import annotations

import heapq
import math
import random
from collections import defaultdict
from typing import Callable, Optional

import numpy as np

from index.node import VaultNode


# ─────────────────────────────────────────────
# Funzioni di distanza
# ─────────────────────────────────────────────

def cosine_distance(a: np.ndarray, b: np.ndarray, slice_dim: int | None = None) -> float:
    """
    1 - cosine_similarity. Supporta il troncamento Matryoshka.
    """
    if slice_dim is not None:
        a = a[:slice_dim]
        b = b[:slice_dim]
        # Nel Matryoshka reale, i sub-vettori vanno ri-normalizzati
        norm_a = np.linalg.norm(a) + 1e-8
        norm_b = np.linalg.norm(b) + 1e-8
        return 1.0 - float(np.dot(a / norm_a, b / norm_b))
        
    return 1.0 - float(np.dot(a, b))


def euclidean_distance(a: np.ndarray, b: np.ndarray) -> float:
    """Distanza euclidea. Alternativa a cosine per spazi non normalizzati."""
    return float(np.linalg.norm(a - b))


try:
    import neuralvault_rs
    RUST_AVAILABLE = True
except ImportError as e:
    RUST_AVAILABLE = False
    print(f"NeuralVault: Rust backend import failed with error: {e}")


# ─────────────────────────────────────────────
# AdaptiveHNSW
# ─────────────────────────────────────────────

class AdaptiveHNSW:
    """
    HNSW con adaptive sub-graph promotion.

    Supporta backend Python (default) e backend Rust (se disponibile).
    Il backend Rust offre performance 50x superiori per dataset > 100k nodi.
    """

    def __init__(
        self,
        dim:                  int   = 1024,
        M:                    int   = 16,
        ef_construction:      int   = 200,
        distance_fn:          Callable = cosine_distance,
        promotion_threshold:  int   = 50,
        promotion_boost:      int   = 4,   # quante connessioni extra dopo promozione
        use_rust:             bool  = True, # auto-use Rust if available
        storage_get_fn:       Optional[Callable[[str], VaultNode]] = None,
    ):
        """
        Args:
            dim: dimensione dei vettori
            M: connessioni massime per nodo ai livelli > 0
            ef_construction: dimensione della lista dinamica durante costruzione.
            distance_fn: funzione di distanza.
            promotion_threshold: numero di hit prima di promuovere un sub-graph
            promotion_boost: quante connessioni locali aggiuntive dopo promozione
            use_rust: se True e disponibile, usa il core in Rust
            storage_get_fn: callback opzionale per recuperare nodi non in memoria
        """
        self.dim             = dim
        self.M               = M
        self.M_max0          = M * 2
        self.ef_construction = ef_construction
        self.distance_fn     = distance_fn
        self.promotion_threshold = promotion_threshold
        self.promotion_boost = promotion_boost
        self.storage_get     = storage_get_fn
        self.vector_dtype    = np.float16 if use_rust is False else np.float32 # Rust handles its own
        
        self.use_rust = use_rust and RUST_AVAILABLE
        self._rust_engine = None
        
        if self.use_rust:
            self._rust_engine = neuralvault_rs.PyHNSW(dim, M, ef_construction)
            print(f"NeuralVault: using Rust backend for HNSW (dim={dim})")

        # Struttura principale del grafo (Python fallback)
        self.nodes:       dict[str, VaultNode] = {}
        self.layers:      list[dict[str, list[str]]] = []
        self.entry_point: str | None = None
        self.max_level:   int = -1

        # Adaptive promotion tracking (Python fallback)
        self._hit_counter: dict[str, int] = defaultdict(int)
        self._promotion_count: dict[str, int] = defaultdict(int)

        self._mL = 1.0 / math.log(max(M, 2))

    # ─────────────────────────────────────────
    # Inserimento
    # ─────────────────────────────────────────

    def insert(self, node: VaultNode) -> None:
        """
        Inserisce un nodo nell'indice.

        Algoritmo:
        1. Assegna un livello casuale con distribuzione geometrica
        2. Scendi dalla cima dell'indice fino al livello del nodo (greedy search)
        3. A ogni livello dal livello del nodo fino a 0, trova i vicini
           e crea gli edges bidirezionali
        4. Se il nuovo nodo ha un livello più alto del massimo attuale,
           diventa il nuovo entry_point
        """
        if node.vector is None:
            raise ValueError(f"Node {node.id} has no vector — cannot insert into HNSW")

        if self.use_rust:
            self._rust_engine.insert(node.id, node.vector.tolist())
            # We still keep a reference to the node metadata in Python
            self.nodes[node.id] = node
            return

        level = self._random_level()
        self.nodes[node.id] = node

        # Assicura che esistano abbastanza livelli
        while len(self.layers) <= level:
            self.layers.append({})

        # Caso base: primo nodo
        if self.entry_point is None:
            for lv in range(level + 1):
                self.layers[lv][node.id] = []
            self.entry_point = node.id
            self.max_level   = level
            return

        # Fase 1: scendi dal livello massimo al livello del nodo (greedy, ef=1)
        ep = self.entry_point
        for lc in range(self.max_level, level, -1):
            if lc < len(self.layers):
                ep = self._greedy_descent(ep, node.vector, lc)

        # Fase 2: inserimento nei livelli da `level` a 0
        for lc in range(min(level, self.max_level), -1, -1):
            # Cerca i vicini con ef_construction
            candidates = self._search_layer(ep, node.vector, self.ef_construction, lc)

            # Seleziona i migliori M vicini (M_max0 al livello 0)
            max_conn = self.M_max0 if lc == 0 else self.M
            neighbors = self._select_neighbors_simple(candidates, max_conn)

            # Fallback: se non ci sono candidati, connetti almeno all'ep corrente
            if not neighbors and ep in self.nodes and ep != node.id:
                ep_node = self.nodes[ep]
                if ep_node.vector is not None:
                    ep_dist = self.distance_fn(ep_node.vector, node.vector)
                    neighbors = [(ep, ep_dist)]

            # Inizializza il nodo al livello corrente
            if node.id not in self.layers[lc]:
                self.layers[lc][node.id] = []

            # Aggiungi edges: nuovo nodo ↔ vicini
            for n_id, _ in neighbors:
                self.layers[lc][node.id].append(n_id)
                if n_id not in self.layers[lc]:
                    self.layers[lc][n_id] = []
                self.layers[lc][n_id].append(node.id)

                # Pota i vicini che hanno troppi vicini (mantieni invariante M)
                if len(self.layers[lc][n_id]) > max_conn:
                    # Ricostruisci lista tenendo solo i max_conn più vicini
                    n_node = self.nodes.get(n_id)
                    if n_node is not None and n_node.vector is not None:
                        n_neighbors = [
                            (nb, self.distance_fn(n_node.vector, self.nodes[nb].vector))
                            for nb in self.layers[lc][n_id]
                            if nb in self.nodes and self.nodes[nb].vector is not None
                        ]
                        n_neighbors.sort(key=lambda x: x[1])
                        self.layers[lc][n_id] = [nb for nb, _ in n_neighbors[:max_conn]]

            # Aggiorna entry point per il livello successivo (nodo più vicino trovato)
            if candidates:
                ep = min(candidates, key=lambda x: x[1])[0]  # x = (node_id, dist)

        # Aggiorna entry_point se questo nodo è al livello più alto
        if level > self.max_level:
            self.max_level   = level
            self.entry_point = node.id
            # Inizializza i livelli superiori
            for lv in range(self.max_level, level + 1):
                if lv >= len(self.layers):
                    self.layers.append({})
                self.layers[lv][node.id] = []

    def delete(self, node_id: str) -> bool:
        """
        Rimuove un nodo dall'indice.

        Nota: la rimozione da HNSW è complessa perché bisogna ricollegare
        i vicini del nodo rimosso. Implementazione: rimuoviamo il nodo e
        puliamo tutti gli edges che lo referenziano.
        """
        if node_id not in self.nodes:
            return False

        if self.use_rust:
            self._rust_engine.delete(node_id)
            del self.nodes[node_id]
            return True

        # Rimuovi dai layers
        for lc, layer in enumerate(self.layers):
            if node_id in layer:
                # Rimuovi riferimenti da tutti i vicini
                for neighbor_id in layer[node_id]:
                    if neighbor_id in layer:
                        try:
                            layer[neighbor_id].remove(node_id)
                        except ValueError:
                            pass
                del layer[node_id]

        # Aggiorna entry_point se necessario
        if self.entry_point == node_id:
            # Trova il prossimo entry_point (nodo al livello più alto)
            for lv in range(self.max_level, -1, -1):
                if self.layers[lv]:
                    self.entry_point = next(iter(self.layers[lv]))
                    self.max_level = lv
                    break
            else:
                self.entry_point = None
                self.max_level = -1

        del self.nodes[node_id]
        self._hit_counter.pop(node_id, None)
        self._promotion_count.pop(node_id, None)
        return True

    # ─────────────────────────────────────────
    # Ricerca
    # ─────────────────────────────────────────

    def _get_node(self, node_id: str) -> Optional[VaultNode]:
        """Recupera un nodo dalla cache o dallo storage persistente."""
        node = self.nodes.get(node_id)
        if not node and self.storage_get:
            node = self.storage_get(node_id)
            if node:
                self.nodes[node_id] = node
        return node

    def search(
        self,
        query_vector: np.ndarray,
        k:            int   = 10,
        ef:           int   = 50,
        session_id:   str | None = None,
        filter_ids:   set[str] | None = None,
        slice_dim:    int | None = None, # [PROD Innovation]: Matryoshka Slicing
    ) -> list[tuple[str, float]]:
        """
        Ricerca ANN con adaptive tracking.

        Args:
            query_vector: vettore di query (deve essere normalizzato)
            k: numero di risultati
            ef: dimensione lista dinamica durante ricerca. Aumentare per più recall.
                Tipicamente ef >= k. Default 50 è un buon compromesso.
            session_id: se fornito, traccia gli accessi per adaptive promotion
            filter_ids: se fornito, considera solo questi nodi come risultati validi.
                        ATTENZIONE: filter_ids=None significa "tutti i nodi".

        Returns:
            Lista di (node_id, distance) ordinata per distanza crescente.
        """
        if self.entry_point is None or not self.nodes:
            return []

        if len(query_vector.shape) == 1:
            query_vector = query_vector.astype(self.vector_dtype)
            norm = np.linalg.norm(query_vector.astype(np.float32))
            query_vector = query_vector / norm.astype(self.vector_dtype) if norm > 0 else query_vector

        if self.use_rust:
            # Rust engine handles the descent and layer search in one go
            # Se slice_dim è attivo, eseguiamo una ricerca 'oversampled' in Rust
            # e poi facciamo il rescoring locale (Matryoshka style)
            search_k = k if not slice_dim else k * 5
            rust_results = self._rust_engine.search(query_vector.tolist(), search_k, ef)
            
            results = rust_results
            if filter_ids:
                results = [(nid, d) for nid, d in results if nid in filter_ids]
            
            if slice_dim:
                # Slicing Rescoring (Hybrid Mode)
                refined = []
                for nid, _ in results:
                    node = self._get_node(nid)
                    if node and node.vector is not None:
                        d = self.distance_fn(node.vector, query_vector, slice_dim=slice_dim)
                        refined.append((nid, d))
                results = sorted(refined, key=lambda x: x[1])

            # Post-processing: promotion tracking
            if session_id and results:
                for node_id, _ in results[:k]:
                    self._hit_counter[node_id] += 1
            
            return results[:k]

        # Discesa greedy dai livelli alti
        ep = self.entry_point
        for lc in range(self.max_level, 0, -1):
            if lc < len(self.layers):
                ep = self._greedy_descent(ep, query_vector, lc, slice_dim=slice_dim)

        # Ricerca al livello 0 con lista dinamica di dimensione ef
        candidates = self._search_layer(ep, query_vector, max(ef, k), 0, slice_dim=slice_dim)

        # Filtra se necessario
        if filter_ids is not None:
            candidates = [(nid, d) for nid, d in candidates if nid in filter_ids]

        # candidates è già (node_id, dist) — ordina e prendi top-k
        results = sorted(candidates, key=lambda x: x[1])[:k]

        # Registra hit per adaptive promotion
        if session_id and results:
            for node_id, _ in results:
                self._hit_counter[node_id] += 1
                if self._hit_counter[node_id] >= self.promotion_threshold:
                    self._promote_subgraph(node_id)
                    self._hit_counter[node_id] = 0

        return results

    # ─────────────────────────────────────────
    # Adaptive promotion
    # ─────────────────────────────────────────

    def _promote_subgraph(self, center_id: str) -> None:
        """
        INNOVAZIONE CHIAVE: aumenta la connettività locale intorno a un nodo
        che viene frequentemente interrogato.

        Meccanismo: prende i vicini del nodo al livello 0 e aggiunge edges
        tra di loro (triangolazione locale). Questo crea "scorciatoie" nel
        grafo che velocizzano le query future nella stessa zona del feature space.

        Effetto: la prossima ricerca vicino a questo nodo avrà più connessioni
        locali da attraversare → maggiore probabilità di trovare i vicini
        esatti → migliore recall a parità di ef.

        Limite: al massimo `promotion_boost` nuovi edges per promozione,
        per evitare che il grafo diventi troppo denso.
        """
        max_promotions = 3  # non promuovere troppo lo stesso nodo
        if self._promotion_count[center_id] >= max_promotions:
            return

        if not self.layers or center_id not in self.layers[0]:
            return

        neighbors = self.layers[0][center_id][:8]  # considera max 8 vicini
        edges_added = 0

        for i, n1 in enumerate(neighbors):
            if edges_added >= self.promotion_boost:
                break
            for n2 in neighbors[i + 1:]:
                if edges_added >= self.promotion_boost:
                    break
                # Aggiungi edge bidirezionale se non esiste
                if n1 in self.layers[0] and n2 not in self.layers[0].get(n1, []):
                    # Controlla che entrambi i nodi esistano ancora
                    if n1 in self.nodes and n2 in self.nodes:
                        self.layers[0].setdefault(n1, []).append(n2)
                        self.layers[0].setdefault(n2, []).append(n1)
                        edges_added += 1

        self._promotion_count[center_id] += 1

    # ─────────────────────────────────────────
    # Metodi interni
    # ─────────────────────────────────────────

    def _random_level(self) -> int:
        """
        Genera un livello con distribuzione geometrica decrescente.
        La formula garantisce che la maggior parte dei nodi stia al livello 0,
        pochi al livello 1, pochissimi al livello 2, ecc.
        Questo crea la struttura "small world" di HNSW.
        """
        return int(-math.log(random.random()) * self._mL)

    def _greedy_descent(self, ep: str, query: np.ndarray, level: int, slice_dim: int | None = None) -> str:
        """
        Discesa greedy a un singolo livello.
        """
        current    = ep
        ep_node    = self._get_node(ep)
        if ep_node is None or ep_node.vector is None:
            return ep
        current_dist = self.distance_fn(ep_node.vector, query, slice_dim=slice_dim) if slice_dim else self.distance_fn(ep_node.vector, query)

        changed = True
        while changed:
            changed = False
            if level >= len(self.layers):
                break
            for neighbor_id in self.layers[level].get(current, []):
                nb_node = self._get_node(neighbor_id)
                if nb_node is None or nb_node.vector is None:
                    continue
                d = self.distance_fn(nb_node.vector, query, slice_dim=slice_dim) if slice_dim else self.distance_fn(nb_node.vector, query)
                if d < current_dist:
                    current, current_dist = neighbor_id, d
                    changed = True

        return current

    def _search_layer(
        self,
        ep:    str,
        query: np.ndarray,
        ef:    int,
        level: int,
        slice_dim: int | None = None,
    ) -> list[tuple[str, float]]:
        """
        Ricerca con lista dinamica di dimensione ef al livello specificato.
        """
        if level >= len(self.layers):
            return []

        ep_node = self._get_node(ep)
        if ep_node is None or ep_node.vector is None:
            return []

        ep_dist = self.distance_fn(ep_node.vector, query, slice_dim=slice_dim) if slice_dim else self.distance_fn(ep_node.vector, query)

        visited      = {ep}
        # heap interno usa (dist, id) per il min-heap
        candidates   = [(ep_dist, ep)]
        # dynamic_list usa (node_id, dist) — formato output
        dynamic_list = [(ep, ep_dist)]

        while candidates:
            c_dist, c_id = heapq.heappop(candidates)

            # Se il miglior candidato è peggiore del peggiore nella lista → stop
            worst_dist = max(d for _, d in dynamic_list)
            if c_dist > worst_dist:
                break

            for neighbor_id in self.layers[level].get(c_id, []):
                if neighbor_id in visited:
                    continue
                visited.add(neighbor_id)

                nb_node = self._get_node(neighbor_id)
                if nb_node is None or nb_node.vector is None:
                    continue

                nb_dist      = self.distance_fn(nb_node.vector, query, slice_dim=slice_dim) if slice_dim else self.distance_fn(nb_node.vector, query)
                current_worst = max(d for _, d in dynamic_list)

                if nb_dist < current_worst or len(dynamic_list) < ef:
                    heapq.heappush(candidates, (nb_dist, neighbor_id))
                    dynamic_list.append((neighbor_id, nb_dist))
                    # Mantieni solo ef elementi (rimuovi il peggiore)
                    if len(dynamic_list) > ef:
                        dynamic_list.sort(key=lambda x: x[1])
                        dynamic_list = dynamic_list[:ef]

        return sorted(dynamic_list, key=lambda x: x[1])

    def _select_neighbors_simple(
        self,
        candidates: list[tuple[str, float]],
        M:          int,
    ) -> list[tuple[str, float]]:
        """Seleziona i M vicini più vicini dalla lista (node_id, dist)."""
        return sorted(candidates, key=lambda x: x[1])[:M]

    # ─────────────────────────────────────────
    # Statistiche
    # ─────────────────────────────────────────

    def stats(self) -> dict:
        """Restituisce statistiche sull'indice per monitoring."""
        if self.use_rust:
            total_edges = self._rust_engine.total_edges()
            edge_sample = self._rust_engine.get_edges_sample(150) # Campione di 150 archi
        else:
            total_edges = sum(
                len(neighbors)
                for layer in self.layers
                for neighbors in layer.values()
            )
            # Semplice campionamento per fallback Python
            edge_sample = []
            if self.layers:
                count = 0
                for u, nbs in self.layers[0].items():
                    for v in nbs:
                        edge_sample.append((u, v))
                        count += 1
                        if count >= 150: break
                    if count >= 150: break

        hot_nodes = sum(
            1 for count in self._hit_counter.values()
            if count >= self.promotion_threshold // 2
        )
        return {
            "total_nodes":      len(self.nodes),
            "total_levels":     len(self.layers) if not self.use_rust else self._rust_engine.max_level() + 1,
            "total_edges":      total_edges,
            "edge_sample":      edge_sample,
            "hot_nodes":        hot_nodes,
            "promoted_nodes":   len([k for k, v in self._promotion_count.items() if v > 0]),
        }
