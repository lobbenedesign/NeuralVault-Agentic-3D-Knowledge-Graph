"""
neuralvault.agent.feedback
──────────────────────────
Il "Feedback Loop" algoritmico di NeuralVault.
Prende i segnali di successo/fallimento dell'agente e li usa per 
ristrutturare la conoscenza a livello di Tier Semantico.
"""

from __future__ import annotations
import time
from typing import Dict, List, Any, Callable
from index.node import VaultNode, RelationType, MemoryTier
from index.innovations import SpectralImportanceTracker

class AgentFeedbackProcessor:
    """
    Processa il feedback degli utenti/agenti per migliorare la retrieval futura.
    L'obiettivo è far evolvere il database da statico a dinamico.
    """
    def __init__(self, dim: int, storage_put_fn: Callable[[VaultNode, MemoryTier], None]):
        self.storage_put = storage_put_fn
        self.dim = dim
        # Tracker per l'importanza delle dimensioni (SIT)
        self.importance_tracker = SpectralImportanceTracker(dim=dim)
        # Mappa per il tracking temporaneo delle co-occorrenze
        self._session_cache: dict[str, list[str]] = {}

    def record_success(self, session_id: str, query_vector: np.ndarray, nodes: list[VaultNode]):
        """
        Registra che questi nodi sono stati scelti come 'ottimi' dall'agente.
        1. Aggiorna SIT (Spectral Importance Tracker) per affinare i pesi del dominio.
        2. Aumenta agent_relevance_score per i nodi usati.
        3. Crea semantic edges per co-occorrenza.
        """
        if not nodes:
            return
            
        # 1. Update Dimension Importance (SIT)
        # Questo è il cuore dell'apprendimento del dominio dell'agente.
        # Solo i vettori dei nodi che l'agente ha effettivamente usato vengono passati come 'ground truth'.
        node_vectors = [n.vector for n in nodes if n.vector is not None]
        if node_vectors:
            self.importance_tracker.update(query_vector, node_vectors)

        # 2. Rinforzo dei nodi e creazione relazioni
        for i, node in enumerate(nodes):
            # Aumenta score di rilevanza (EMA implicito via delta)
            self.process_node_feedback(node, positive=True)
            
            # Crea relazioni sequenziali tra i nodi usati insieme
            for target_node in nodes[i+1:]:
                node.add_edge(
                    target_id=target_node.id,
                    relation=RelationType.SEQUENTIAL,
                    weight=0.5,
                    source="agent_session_feedback"
                )
                self.storage_put(node, MemoryTier.WORKING)

    def process_node_feedback(self, node: VaultNode, positive: bool):
        """Aggiorna lo score di un singolo nodo e lo promuove/degrada."""
        delta = 0.05 if positive else -0.1
        node.agent_relevance_score = max(0.0, min(1.0, node.agent_relevance_score + delta))
        
        # Se il punteggio è molto alto, il nodo diventa 'hot' permanentemente
        node.touch()
        
        # Scrivi nel tier persistente
        self.storage_put(node, MemoryTier.WORKING)

    def learn_relations(self, nodes: List[VaultNode]):
        """
        Analisi di gruppo: trova nuovi edge semantici.
        Se più nodi appaiono spesso insieme nel context di risposte positive, 
        segnala una relazione 'SAME_ENTITY' o 'SEQUENTIAL'.
        """
        if len(nodes) < 2:
            return

        main_node = nodes[0]
        for related in nodes[1:]:
            # Crea un arco se non esiste o rinforza il peso
            main_node.add_edge(
                target_id=related.id,
                relation=RelationType.SEQUENTIAL,
                weight=0.5,
                source="agent_autolearn"
            )
            # Riscrivi il nodo per salvare il nuovo edge
            self.storage_put(main_node, MemoryTier.WORKING)
