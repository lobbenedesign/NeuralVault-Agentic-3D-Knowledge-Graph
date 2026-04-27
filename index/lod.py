"""
neuralvault.index.lod
──────────────────────
Level of Detail (LOD) Manager per la visualizzazione di milioni di nodi.
Fase 4: Nebula Reach.
"""

import numpy as np
from typing import List, Dict, Any
from index.node import VaultNode

class LODManager:
    """
    Gestisce l'aggregazione spaziale dei nodi per la visualizzazione.
    Invece di inviare 1.000.000 di punti, invia dei 'Centroidi' 
    che rappresentano cluster di nodi.
    """
    def __init__(self, engine):
        self.engine = engine

    def get_aggregated_nodes(self, level: int = 1) -> List[Dict[str, Any]]:
        """
        Restituisce nodi aggregati basati sul livello di dettaglio richiesto.
        Livello 0: Tutti i nodi (Full Detail)
        Livello 1: Cluster di medie dimensioni
        Livello 2: Super-cluster (Nebulose)
        """
        nodes = list(self.engine._nodes.values())
        if not nodes: return []
        
        if level == 0:
            return [n.to_dict() for n in nodes]
        
        # Algoritmo di Grid-based Clustering per LOD ultra-veloce
        # Dividiamo lo spazio in una griglia e calcoliamo il centroide per ogni cella
        grid_size = 0.2 * level # Aumenta con il livello
        clusters: Dict[tuple, List[VaultNode]] = {}
        
        for node in nodes:
            if node.vector is None: continue
            # Usiamo le prime 3 dimensioni del vettore come coordinate spaziali (proiezione semplice)
            pos = node.vector[:3]
            grid_key = tuple((pos / grid_size).astype(int))
            if grid_key not in clusters:
                clusters[grid_key] = []
            clusters[grid_key].append(node)
            
        aggregated = []
        for key, cluster_nodes in clusters.items():
            # Calcola il centroide
            centroid_vector = np.mean([n.vector for n in cluster_nodes], axis=0)
            
            # Crea un nodo virtuale che rappresenta il cluster
            aggregated.append({
                "id": f"cluster_{level}_{key}",
                "text": f"Cluster LOD {level} ({len(cluster_nodes)} nodes)",
                "vector": centroid_vector.tolist(),
                "is_cluster": True,
                "node_count": len(cluster_nodes),
                "importance": sum(n.agent_relevance_score for n in cluster_nodes) / len(cluster_nodes)
            })
            
        return aggregated
