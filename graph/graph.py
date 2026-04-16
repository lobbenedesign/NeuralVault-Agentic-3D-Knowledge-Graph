"""
neuralvault.core.graph
──────────────────────
Context graph traversal engine.

Implementa la navigazione degli semantic edges tra VaultNode.
Parte dai risultati ANN (seed) ed espande il grafo seguendo le relazioni
semantiche esplicite.

Questa è l'innovazione che distingue NeuralVault da ogni altro VDB:
la possibilità di combinare similarità geometrica (HNSW) con struttura
logica (relazioni semantiche) in una singola query.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Any

from index.node import RelationType, VaultNode


# ─────────────────────────────────────────────
# Configurazione traversal
# ─────────────────────────────────────────────

# Quali relazioni espandere di default e con quale moltiplicatore di score.
# Un moltiplicatore > 1 significa che seguire questa relazione AUMENTA la
# rilevanza percepita (es. trovare il prerequisito di un chunk già rilevante
# è molto utile). Un moltiplicatore < 1 la diminuisce.

DEFAULT_RELATION_CONFIG: dict[RelationType, dict] = {
    RelationType.PREREQUISITE: {
        "expand":     True,
        "multiplier": 0.9,   # molto utile — includi sempre il prerequisito
        "direction":  "both", # segui l'edge in entrambe le direzioni
    },
    RelationType.SEQUENTIAL: {
        "expand":     True,
        "multiplier": 0.75,
        "direction":  "forward",
    },
    RelationType.CITES: {
        "expand":     True,
        "multiplier": 0.7,
        "direction":  "forward",
    },
    RelationType.EXAMPLE_OF: {
        "expand":     True,
        "multiplier": 0.65,
        "direction":  "both",
    },
    RelationType.SAME_ENTITY: {
        "expand":     True,
        "multiplier": 0.8,
        "direction":  "both",
    },
    RelationType.UPDATES: {
        "expand":     True,
        "multiplier": 0.85,  # la versione aggiornata è molto rilevante
        "direction":  "forward",
    },
    RelationType.CONTRADICTS: {
        "expand":     False,  # default: non espandere contraddizioni automaticamente
        "multiplier": 0.4,
        "direction":  "both",
    },
}


# ─────────────────────────────────────────────
# GraphNode — nodo interno per la traversal
# ─────────────────────────────────────────────

@dataclass
class GraphTraversalNode:
    """Rappresenta un nodo durante la traversal del context graph."""
    node_id:   str
    score:     float
    hop:       int
    path:      str
    relations: list[str] = field(default_factory=list)  # relazioni seguite per arrivare qui


# ─────────────────────────────────────────────
# ContextGraph
# ─────────────────────────────────────────────

class ContextGraph:
    """
    Engine per la traversal del context graph.

    Non memorizza il grafo internamente: lavora direttamente sui VaultNode
    che già contengono i loro edges. Questo evita duplicazione di stato.

    Supporta tre modalità di traversal:
    - BFS (Breadth-First Search): esplora per livelli di hop. Default.
    - Greedy: segue sempre l'edge con score più alto a ogni passo.
    - Weighted BFS: BFS con pruning anticipato su score troppo bassi.
    """

    def __init__(
        self,
        nodes:                dict[str, VaultNode],
        relation_config:      dict[RelationType, dict] | None = None,
        min_score_threshold:  float = 0.1,  # scarta nodi con score < questa soglia
    ):
        self.nodes               = nodes
        self.relation_config     = relation_config or DEFAULT_RELATION_CONFIG
        self.min_score_threshold = min_score_threshold

    def expand(
        self,
        seed_ids:              list[str],
        seed_scores:           dict[str, float] | None = None,
        max_hops:              int   = 2,
        max_nodes:             int   = 30,
        relation_filter:       list[RelationType] | list[str] | None = None,
        include_contradictions: bool = False,
        mode:                  str  = "bfs",  # "bfs" | "greedy" | "weighted_bfs"
    ) -> list[GraphTraversalNode]:
        """
        Espande il grafo a partire dai seed.

        Args:
            seed_ids: ID dei nodi di partenza (tipicamente risultati HNSW)
            seed_scores: score associati ai seed (da HNSW o RRF). Se None,
                         tutti i seed hanno score 1.0
            max_hops: profondità massima di traversal. 1 = solo vicini diretti.
                      Per RAG di precisione: 1-2. Per esplorazione: 3-4.
            max_nodes: numero massimo di nodi nel risultato (seed + espansi)
            relation_filter: se specificato, usa solo queste relazioni.
                             Se None, usa le relazioni configurate in relation_config.
            include_contradictions: se True, include anche nodi contraddittori.
                                    Utile per query di tipo "argomento vs controargomento".
            mode: strategia di traversal

        Returns:
            Lista di GraphTraversalNode ordinata per score decrescente.
            Include i seed stessi come nodi con hop=0.
        """
        if not seed_ids:
            return []

        # Normalizza relation_filter
        if relation_filter:
            allowed_relations = {
                RelationType(r) if isinstance(r, str) else r
                for r in relation_filter
            }
        else:
            allowed_relations = {
                rel for rel, cfg in self.relation_config.items()
                if cfg.get("expand", True)
            }

        # Aggiungi contraddizioni se richiesto
        if include_contradictions:
            allowed_relations.add(RelationType.CONTRADICTS)

        # Score iniziali dei seed
        if seed_scores is None:
            seed_scores = {sid: 1.0 for sid in seed_ids}

        # Dispatch alla strategia scelta
        if mode == "greedy":
            return self._greedy_expand(seed_ids, seed_scores, max_hops, max_nodes, allowed_relations)
        else:
            return self._bfs_expand(seed_ids, seed_scores, max_hops, max_nodes, allowed_relations)

    def find_path(
        self,
        source_id: str,
        target_id: str,
        max_hops:  int = 5,
    ) -> list[str] | None:
        """
        Trova il percorso più breve tra due nodi nel context graph.
        Utile per debugging e per spiegare perché due chunk sono correlati.

        Returns:
            Lista di node_id che formano il percorso, o None se non esiste.
        """
        if source_id not in self.nodes or target_id not in self.nodes:
            return None

        visited = {source_id}
        queue = deque([(source_id, [source_id])])

        while queue:
            current_id, path = queue.popleft()
            if len(path) > max_hops + 1:
                continue

            current = self.nodes.get(current_id)
            if current is None:
                continue

            for edge in current.edges:
                if edge.target_id == target_id:
                    return path + [target_id]
                if edge.target_id not in visited:
                    visited.add(edge.target_id)
                    queue.append((edge.target_id, path + [edge.target_id]))

        return None  # nessun percorso trovato

    def get_neighborhood(
        self,
        node_id:   str,
        relation:  RelationType | None = None,
        max_hops:  int = 1,
    ) -> dict[str, list[str]]:
        """
        Restituisce il vicinato di un nodo, opzionalmente filtrato per relazione.
        Utile per visualizzare la struttura del grafo intorno a un nodo specifico.

        Returns:
            dict: {node_id: [relazioni verso parent]}
        """
        result: dict[str, list[str]] = {}
        visited = {node_id}
        queue = deque([(node_id, 0)])

        while queue:
            current_id, hop = queue.popleft()
            if hop >= max_hops:
                continue

            current = self.nodes.get(current_id)
            if not current:
                continue

            for edge in current.edges:
                if relation and edge.relation != relation:
                    continue
                tid = edge.target_id
                if tid not in result:
                    result[tid] = []
                result[tid].append(f"{edge.relation.value} (w={edge.weight:.2f})")
                if tid not in visited:
                    visited.add(tid)
                    queue.append((tid, hop + 1))

        return result

    def infer_edges_from_cooccurrence(
        self,
        cooccurrence_map: dict[tuple[str, str], int],
        min_cooccurrences: int = 3,
        weight_scale:      float = 0.1,
    ) -> list[tuple[str, str, RelationType, float]]:
        """
        Inferisce semantic edges dalle co-occorrenze nell'uso dell'agente.

        Quando due nodi vengono recuperati insieme frequentemente nella stessa
        sessione, probabilmente hanno una relazione semantica.
        Questo metodo crea edges "agent_cooccurrence" con peso proporzionale
        alla frequenza.

        Args:
            cooccurrence_map: {(node_id_a, node_id_b): count}
            min_cooccurrences: soglia minima per creare un edge
            weight_scale: moltiplicatore per convertire count in weight

        Returns:
            Lista di (source_id, target_id, relation, weight) da aggiungere
        """
        edges = []
        for (a_id, b_id), count in cooccurrence_map.items():
            if count < min_cooccurrences:
                continue
            weight = min(count * weight_scale, 0.8)  # cap a 0.8 (non 1.0 — è inferito)
            edges.append((a_id, b_id, RelationType.SEQUENTIAL, weight))
        return edges

    # ─────────────────────────────────────────
    # Implementazioni delle strategie
    # ─────────────────────────────────────────

    def _bfs_expand(
        self,
        seed_ids:          list[str],
        seed_scores:       dict[str, float],
        max_hops:          int,
        max_nodes:         int,
        allowed_relations: set[RelationType],
    ) -> list[GraphTraversalNode]:
        """
        BFS standard con decay dello score per hop.

        Il decay è: score * edge.weight * multiplier * (hop_decay ^ hop)
        dove hop_decay = 0.7 significa che ogni hop riduce lo score del 30%.
        """
        hop_decay = 0.7

        visited  = set(seed_ids)
        result   = []
        queue    = deque()

        # Inizializza con i seed
        for sid in seed_ids:
            if sid not in self.nodes:
                continue
            t = GraphTraversalNode(
                node_id=sid, score=seed_scores.get(sid, 1.0), hop=0, path="seed"
            )
            result.append(t)
            queue.append(t)

        while queue and len(result) < max_nodes:
            current = queue.popleft()
            if current.hop >= max_hops:
                continue

            node = self.nodes.get(current.node_id)
            if not node:
                continue

            for edge in node.edges:
                if edge.relation not in allowed_relations:
                    continue
                if edge.target_id in visited:
                    continue
                if edge.target_id not in self.nodes:
                    continue

                visited.add(edge.target_id)

                # Calcola score con decay [v3.0 Bio-Mimetic]
                rel_cfg    = self.relation_config.get(edge.relation, {})
                multiplier = rel_cfg.get("multiplier", 0.5)
                # Il logic_weight potenzia o depotenzia il ramo in base alla rilevanza logica
                new_score  = current.score * edge.weight * multiplier * edge.logic_weight * (hop_decay ** (current.hop + 1))

                if new_score < self.min_score_threshold:
                    continue  # pruna rami con score troppo basso

                t = GraphTraversalNode(
                    node_id=edge.target_id,
                    score=new_score,
                    hop=current.hop + 1,
                    path=f"{current.path} →[{edge.relation.value}]",
                    relations=current.relations + [edge.relation.value],
                )
                result.append(t)
                queue.append(t)

                if len(result) >= max_nodes:
                    break

        return sorted(result, key=lambda x: x.score, reverse=True)

    def _greedy_expand(
        self,
        seed_ids:          list[str],
        seed_scores:       dict[str, float],
        max_hops:          int,
        max_nodes:         int,
        allowed_relations: set[RelationType],
    ) -> list[GraphTraversalNode]:
        """
        Greedy: a ogni passo espande l'edge con score massimo.
        Più focalizzata di BFS, utile quando la qualità conta più dell'esaustività.
        """
        import heapq

        visited = set(seed_ids)
        result  = []

        # Priority queue: (negative_score, traversal_node)
        pq = []
        for sid in seed_ids:
            if sid not in self.nodes:
                continue
            t = GraphTraversalNode(
                node_id=sid, score=seed_scores.get(sid, 1.0), hop=0, path="seed"
            )
            result.append(t)
            heapq.heappush(pq, (-t.score, id(t), t))

        while pq and len(result) < max_nodes:
            neg_score, _, current = heapq.heappop(pq)
            if current.hop >= max_hops:
                continue

            node = self.nodes.get(current.node_id)
            if not node:
                continue

            for edge in node.edges:
                if edge.relation not in allowed_relations:
                    continue
                if edge.target_id in visited or edge.target_id not in self.nodes:
                    continue

                visited.add(edge.target_id)
                rel_cfg    = self.relation_config.get(edge.relation, {})
                multiplier = rel_cfg.get("multiplier", 0.5)
                new_score  = current.score * edge.weight * multiplier * (0.7 ** (current.hop + 1))

                if new_score < self.min_score_threshold:
                    continue

                t = GraphTraversalNode(
                    node_id=edge.target_id,
                    score=new_score,
                    hop=current.hop + 1,
                    path=f"{current.path} →[{edge.relation.value}]",
                )
                result.append(t)
                heapq.heappush(pq, (-new_score, id(t), t))

        return sorted(result, key=lambda x: x.score, reverse=True)
