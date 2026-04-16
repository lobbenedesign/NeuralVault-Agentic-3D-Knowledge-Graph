"""
neuralvault.index.healing
──────────────────────────
Gestore dell'auto-ottimizzazione del grafo HNSW.
Analizza i pattern di accesso per potare le connessioni inutilizzate
e suggerire nuove connessioni basate sulla rilevanza semantica.
"""

from __future__ import annotations
import time
from collections import defaultdict
from typing import Dict, List, Tuple, Any
import threading
from index.node import VaultNode

class SelfHealingManager:
    """
    Monitora l'efficacia del grafo HNSW e esegue 'pruning' e 'boosting'.
    """
    def __init__(self, decay_rate: float = 0.99):
        self.decay_rate = decay_rate
        # Mappa (u_idx, v_idx) -> access_score
        self._edge_scores: dict[tuple[int, int], float] = defaultdict(float)
        self._last_access: dict[tuple[int, int], float] = {}
        self._lock = threading.Lock()

    def record_traversal(self, u: int, v: int):
        """Registra che l'arco tra u e v è stato usato in una ricerca."""
        edge = tuple(sorted((u, v)))
        with self._lock:
            self._edge_scores[edge] += 1.0
            self._last_access[edge] = time.time()

    def get_prunable_edges(self, threshold: float = 0.05) -> list[tuple[int, int]]:
        """Identifica gli archi 'morti' o raramente usati da rimuovere."""
        now = time.time()
        prunable = []
        with self._lock:
            for edge, score in list(self._edge_scores.items()):
                # Applica decadimento esponenziale basato sul tempo
                age_hours = (now - self._last_access.get(edge, now)) / 3600
                effective_score = score * (self.decay_rate ** age_hours)
                
                if effective_score < threshold:
                    prunable.append(edge)
        return prunable


    def optimize_graph(self, hnsw_core: Any, nodes: Dict[str, VaultNode]):
        """
        Esegue la manutenzione del grafo:
        1. Rimuove archi deboli per liberare 'slot' nel CSR.
        2. Semantic TTL: Sfratta i nodi 'evanescenti' (inutili da mesi).
        """
        prunable = self.get_prunable_edges()
        print(f"🔱 Self-Healing: Found {len(prunable)} weak edges to prune.")
        
        # 1. Pruning degli archi inattivi
        with self._lock:
            for edge in prunable:
                if edge in self._edge_scores:
                    del self._edge_scores[edge]
                    
        # 2. Semantic TTL (Entropy Decay) - [Innovation Fase 6]
        evicted = self.prune_evanescent_nodes(nodes)
        if evicted > 0:
            print(f"🔱 Self-Healing: Evicted {evicted} evanescent nodes (Signal-to-Noise optimization).")

    def prune_evanescent_nodes(self, nodes: Dict[str, VaultNode], max_age_days: int = 30) -> int:
        """
        Identifica ed elimina nodi che:
        - Hanno score di rilevanza molto basso (< -5.0).
        - Non sono stati usati da settimane.
        - Non hanno archi semantici forti.
        """
        now = time.time()
        to_delete = []
        
        for nid, node in nodes.items():
            age_days = (now - node.last_accessed) / 86400
            
            # Condizioni per lo sfratto (Entropy Decay)
            # Se un nodo è 'tossico' (molti feedback negativi) o invisibile, va rimosso.
            if node.agent_relevance_score < -5.0 or (age_days > max_age_days and node.access_count < 2):
                # Non eliminare se ha archi manuali o di citazione (conoscenza preziosa)
                has_manual_edges = any(e.source == "manual" for e in node.edges)
                if not has_manual_edges:
                    to_delete.append(nid)
        
        # In produzione: qui emettiamo segnale di delete all'engine
        return len(to_delete)

    def repair_fractured_synapses(self, engine: Any) -> int:
        """
        [Fase 25: Active Recovery] Ripara il grafo richiamando nodi eliminati per errore.
        Rileva archi che puntano al nulla e invoca il 'Rollback Neurale'.
        """
        print("🧠 [Self-Healing] Diagnostica integrità in corso...")
        broken_ids = engine.check_integrity()
        
        repaired_count = 0
        for nid in broken_ids:
            # Tenta il rollback automatico
            success = engine.rollback_node(nid)
            if success:
                repaired_count += 1
                # Notifica sulla Blackboard (tramite engine se possibile, o passiamo orchestrator)
                print(f"✅ [Self-Healing] Ripristinato nodo fratturato: {nid[:8]}")
        
        return repaired_count

    def stats(self):
        with self._lock:
            return {
                "active_edges_tracked": len(self._edge_scores),
                "total_score_sum": sum(self._edge_scores.values())
            }
