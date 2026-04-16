"""
neuralvault.graph.gnn_layer
──────────────────────────
Inferenzia nuovi semantic edges basandosi sulla topologia del grafo 
e sulla similarità vettoriale. Predice relazioni "mancanti".
"""

import numpy as np
from typing import Dict, List, Tuple, Set
from index.node import VaultNode, RelationType, SemanticEdge

class GNNInferenceManager:
    """
    Simula lo strato GNN per l'inferenza di archi transittivi.
    
    Usa una combinazione di:
    1. Triangular Closure: (A->B, B->C) => (A?->C)
    2. Semantic Proximity: Distanza coseno bassa tra A e C
    """
    def __init__(self, threshold: float = 0.85):
        self.threshold = threshold

    def predict_missing_edges(
        self, 
        nodes: Dict[str, VaultNode],
        max_hops: int = 3
    ) -> List[Tuple[str, str, float, RelationType]]:
        """
        Analizza il grafo corrente e restituisce una lista di archi probabili.
        [Innovation Fase 6]: Multi-hop Transitive Inference.
        
        Se A -> B -> C -> D, e A è semanticamente vicino a D, allora A -> D è un 'shortcut' semantico.
        """
        predicted = []
        node_ids = list(nodes.keys())
        
        for a_id in node_ids:
            a_node = nodes[a_id]
            visited = {a_id}
            
            # BFS multi-hop per trovare percorsi transittivi
            queue = [(a_id, 0)]  # (current_id, level)
            while queue:
                curr_id, level = queue.pop(0)
                if level >= max_hops: continue
                
                curr_node = nodes.get(curr_id)
                if not curr_node: continue
                
                for edge in curr_node.edges:
                    c_id = edge.target_id
                    if c_id not in visited:
                        visited.add(c_id)
                        c_node = nodes.get(c_id)
                        if not c_node: continue
                        
                        # Se siamo oltre il primo hop, valutiamo la transitività semantica
                        if level >= 1:
                            if a_node.vector is not None and c_node.vector is not None:
                                sim = float(np.dot(a_node.vector, c_node.vector))
                                if sim > self.threshold:
                                    # Determina tipo relazione: se il percorso è A->B->C, 
                                    # probabilmente A e C sono in una SEQUENZA di apprendimento.
                                    predicted.append((a_id, c_id, float(sim * 0.85), RelationType.SEQUENTIAL))
                        
                        queue.append((c_id, level + 1))
                            
        return predicted

    def apply_predictions(self, nodes: Dict[str, VaultNode]) -> int:
        """Applica gli archi predetti al grafo."""
        predictions = self.predict_missing_edges(nodes)
        added = 0
        for src, dst, weight, rel_type in predictions:
            source_node = nodes[src]
            if not any(e.target_id == dst for e in source_node.edges):
                source_node.add_edge(dst, rel_type, weight=weight, source="gnn_transitive")
                added += 1
        return added
