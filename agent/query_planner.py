"""
neuralvault.agent.query_planner
──────────────────────────────
Pianificatore intelligente delle query.
Analizza il testo della query per ottimizzare i parametri di ricerca (alpha, hops, ef)
senza che l'utente debba configurarli manualmente.
"""

from __future__ import annotations
import re
from dataclasses import dataclass
from typing import Optional

@dataclass
class QueryStrategy:
    alpha: float           # 1.0 = solo dense, 0.0 = solo sparse
    graph_hops: int        # Profondità expansion
    ef_search: int         # Accuratezza HNSW
    use_cross_encoder: bool # Se fare o meno il reranking pesante
    use_speculative: bool  # Se attivare il pre-fetching

class AgentQueryPlanner:
    """
    Decide la strategia di retrieval analizzando il 'mood' e le keyword della query.
    """
    
    # Keyword che suggeriscono una ricerca per parole chiave esatte (sparse)
    TECHNICAL_KEYWORDS = {
        "errore", "error", "codice", "id", "versione", "v. ", "202", "uuid", 
        "json", "xml", "syntax", "timestamp", "log", "null", "undefined"
    }
    
    # Keyword che richiedono contesto espanso (graph)
    GRAPH_KEYWORDS = {
        "contesto", "riferimenti", "relazione", "collegamento", "storia", 
        "evoluzione", "perché", "causa", "conseguenza", "derivato", "background"
    }

    def plan(self, query_text: str) -> QueryStrategy:
        """
        Analizza la query e produce una strategia ottimizzata.
        """
        q_lower = (query_text or "").lower()
        
        # 1. Calcola Alpha (Bilanciamento Hybrid)
        # Se ci sono molti termini tecnici o ID, abbassiamo alpha (più importanza al BM25)
        technical_matches = sum(1 for k in self.TECHNICAL_KEYWORDS if k in q_lower)
        alpha = 0.8 # Default: favoriamo il denso
        if technical_matches > 0:
            alpha = max(0.3, 0.8 - (technical_matches * 0.15))
            
        # 2. Calcola Graph Hops
        # Se l'utente chiede relazioni o contesto, aumentiamo la profondità
        use_graph = any(k in q_lower for k in self.GRAPH_KEYWORDS)
        hops = 2 if use_graph else 1
        
        # 3. Calcola EF Search (Accuratezza)
        # Query lunghe o complesse richiedono più sforzo dall'HNSW
        words = len((query_text or "").strip().split())
        ef = 50
        if words > 15 or "?" in query_text:
            ef = 120
            
        # 4. Cross-Encoder (Reranking)
        # Attivato solo per query esplicative ("perché", "come")
        use_reranker = any(k in q_lower for k in ["perché", "why", "come", "how"])

        return QueryStrategy(
            alpha=alpha,
            graph_hops=hops,
            ef_search=ef,
            use_cross_encoder=use_reranker,
            use_speculative=True # Sempre attivo se disponibile
        )
