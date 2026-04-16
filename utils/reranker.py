"""
neuralvault.utils.reranker
──────────────────────────
Reranker di seconda fase per NeuralVault (Cross-Encoders).
Ottimizza la precisione del RAG raffinando i top-K risultati della ricerca ibrida.
"""

from __future__ import annotations
from typing import Callable, Optional
import numpy as np

class RerankerFactory:
    """Factory per crare reranker (Cross-Encoders)."""

    @staticmethod
    def bge_reranker(
        model_name: str = "BAAI/bge-reranker-v2-m3",
        device:     str = "cpu",
        batch_size: int = 16,
    ) -> Callable[[str, list[str]], list[float]]:
        """
        Crea un reranker locale basato su BAAI BGE-Reranker.
        I Cross-Encoder calcolano lo score di similarità direttamente tra query e testo,
        prevedendo un logit di probabilità di rilevanza.
        """
        try:
            from sentence_transformers import CrossEncoder
        except ImportError:
            raise ImportError("Installa sentence-transformers: pip install sentence-transformers")

        model = CrossEncoder(model_name, device=device)

        def rerank(query: str, documents: list[str]) -> list[float]:
            pairs = [[query, doc] for doc in documents]
            scores = model.predict(pairs, batch_size=batch_size, convert_to_numpy=True)
            # Sigmoid per normalizzare gli scores in [0, 1] se necessario
            return scores.tolist()

        return rerank

    @staticmethod
    def cohere(
        model:   str = "rerank-multilingual-v3.0",
        api_key: Optional[str] = None,
    ) -> Callable[[str, list[str]], list[float]]:
        """Crea un reranker basato su Cohere Rerank API (State-of-the-art cloud)."""
        try:
            import cohere
        except ImportError:
            raise ImportError("Installa cohere: pip install cohere")

        co = cohere.Client(api_key=api_key)

        def rerank(query: str, documents: list[str]) -> list[float]:
            # Cohere accetta un limite di documenti per richiesta (es. 100)
            batch = documents[:100]
            resp = co.rerank(model=model, query=query, documents=batch, top_n=len(batch))
            
            # Map back to original order
            ordered_scores = [0.0] * len(batch)
            for res in resp.results:
                ordered_scores[res.index] = res.relevance_score
            return ordered_scores

        return rerank

    @staticmethod
    def dummy() -> Callable[[str, list[str]], list[float]]:
        """Dummy reranker per test — restituisce score costanti."""
        return lambda q, docs: [1.0] * len(docs)
