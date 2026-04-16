"""
cluster/router.py
───────────────────
Implementazione di uno Shard Router distribuito per NeuralVault.
Gestisce il partizionamento dei dati (Sharding) tra diversi nodi del cluster
utilizzando il Consistent Hashing.
"""

import hashlib
import bisect
from typing import List, Dict, Any, Optional

class ShardRouter:
    """
    Router intelligente per il cluster NeuralVault.
    Mappa gli ID dei nodi (e le query) sui server fisici disponibili.
    
    Utilizza Consistent Hashing per minimizzare il rimescolamento dei dati
    quando un nodo entra o esce dal pool (SWIM protocol compliant).
    """

    def __init__(self, node_urls: List[str] = None, replicas: int = 40):
        """
        Args:
            node_urls: Lista di URL (es. ["http://10.0.0.1:8001", ...])
            replicas: Numero di nodi virtuali per ogni nodo fisico (bilanciamento).
        """
        self.replicas = replicas
        self.ring: List[int] = []
        self._nodes: Dict[int, str] = {}
        
        if node_urls:
            for url in node_urls:
                self.add_node(url)

    def _hash(self, key: str) -> int:
        """Genera un hash deterministico per una chiave."""
        return int(hashlib.md5(key.encode('utf-8')).hexdigest(), 16)

    def add_node(self, node_url: str):
        """Aggiunge un nodo fisico al cerchio di hashing."""
        for i in range(self.replicas):
            # Crea virtual nodes per bilanciare meglio il carico
            h = self._hash(f"{node_url}:{i}")
            self._nodes[h] = node_url
            bisect.insort(self.ring, h)

    def remove_node(self, node_url: str):
        """Rimuove un nodo fisico dal cerchio."""
        for i in range(self.replicas):
            h = self._hash(f"{node_url}:{i}")
            if h in self._nodes:
                del self._nodes[h]
                idx = bisect.bisect_left(self.ring, h)
                if idx < len(self.ring) and self.ring[idx] == h:
                    self.ring.pop(idx)

    def get_node(self, node_id: str) -> str:
        """
        Data un'ID risorsa (es. un VaultNode.id), restituisce l'URL del server 
        responsabile per quel dato.
        """
        if not self.ring:
            return "localhost" # Fallback se il cluster è vuoto

        h = self._hash(node_id)
        idx = bisect.bisect_right(self.ring, h)
        
        # Se siamo alla fine del cerchio, "ruotiamo" all'inizio (ring)
        if idx == len(self.ring):
            idx = 0
            
        return self._nodes[self.ring[idx]]

    def route_query(self, query_text: str) -> List[str]:
        """
        Decide a quali nodi inviare la query. 
        In una query globale, invia a TUTTI i nodi.
        In una query specifica per un namespace/shard, invia solo a quello.
        """
        # Per ora NeuralVault supporta query globali (Scatter-Gather)
        return list(set(self._nodes.values()))

    def stats(self) -> Dict[str, Any]:
        return {
            "total_physical_nodes": len(set(self._nodes.values())),
            "total_virtual_slots": len(self.ring),
            "distribution": {url: list(self._nodes.values()).count(url) for url in set(self._nodes.values())}
        }
