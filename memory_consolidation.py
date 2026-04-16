import numpy as np
from typing import List, Tuple
import time

class WisdomDistiller:
    """
    Distillatore di Sapienza: consolida cluster di ricordi sbiaditi.
    """
    def __init__(self, engine):
        self.engine = engine

    def find_clusters(self, threshold: float = 0.92) -> List[List[str]]:
        """Trova gruppi di nodi semanticamente simili per la consolidazione."""
        clusters = []
        visited = set()
        nodes = list(self.engine._nodes.values())
        
        for i, node in enumerate(nodes):
            if node.id in visited or node.vector is None: continue
            
            # Cerca vicini stretti tramite query HNSW
            results = self.engine.query(node.text, limit=10, query_vector=node.vector)
            current_cluster = [node.id]
            visited.add(node.id)
            
            for res in results:
                if res.node.id not in visited and res.final_score > threshold:
                    current_cluster.append(res.node.id)
                    visited.add(res.node.id)
            
            if len(current_cluster) > 3: # Solo cluster significativi
                clusters.append(current_cluster)
        
        return clusters

    def distill(self, node_ids: List[str]) -> str:
        """
        Consolida un cluster in un Supernodo di Saggezza (v3.5).
        Invece di cancellare, crea una gerarchia: Supernodo -> Nodi Foglia.
        """
        if not node_ids: return ""
        
        vectors = []
        texts = []
        nodes_to_link = []
        
        for nid in node_ids:
            # v13.0: Accesso robusto ai nodi (Fix Gardening Error)
            node = self.engine._nodes.get(nid)
            if node and node.vector is not None:
                vectors.append(node.vector)
                texts.append(node.text)
                nodes_to_link.append(node)
        
        if not vectors: return ""

        # 1. Media dei vettori per il centroide del cluster
        distilled_vector = np.mean(vectors, axis=0)
        
        # 2. Sintesi Reale (The Voice of Wisdom)
        distilled_text = self._generate_wisdom_text(texts)
        
        # 3. Creazione del Supernodo
        wisdom_id = f"wisdom_{int(time.time() * 1000)}"
        wisdom_node = self.engine.upsert_text(
            text=distilled_text,
            metadata={"type": "supernode", "child_count": len(node_ids), "color": "#f59e0b"}, # Oro
            node_id=wisdom_id
        )
        # Sovrascriviamo il vettore col centroide perfetto
        wisdom_node.vector = distilled_vector
        
        # 4. Collegamento Gerarchico (Linkage)
        from index.node import RelationType
        for node in nodes_to_link:
            # Collega il figlio al padre (Saggezza)
            node.add_edge(wisdom_id, RelationType.CITES, weight=1.0)  # v13.1: CITATION→CITES
            # Collega il padre al figlio
            wisdom_node.add_edge(node.id, RelationType.SYNAPSE, weight=0.8)
            
        return wisdom_id

    def _generate_wisdom_text(self, texts: List[str]) -> str:
        """Generazione tramite Ollama con prompt di sintesi estrema."""
        import httpx
        # Campionamento del contesto (max 5 nodi per non sovraccaricare il prompt)
        context = "\n---\n".join(texts[:5])
        prompt = f"Sei l'Archivista Prime. Sintetizza questi frammenti di memoria in un unico principio di saggezza coerente e denso. Sii tecnico e preciso.\n\nFRAMMENTI:\n{context}\n\nSINTESI FINALE:"
        
        try:
            with httpx.Client(timeout=20.0) as client:
                r = client.post("http://localhost:11434/api/generate", json={
                    "model": "mistral:latest",
                    "prompt": prompt,
                    "stream": False
                })
                if r.status_code == 200:
                    return r.json().get("response", "Sintesi fallita.")
        except: pass
        return f"[CONSOLIDA] Sintesi di {len(texts)} memorie correlate."
