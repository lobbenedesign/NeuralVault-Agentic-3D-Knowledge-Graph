"""
retrieval/fusion.py
────────────────────
Fusion Ranker: v0.2.5 Industrial Version.
Combina HNSW, BM25S e Graph con Speculative Reranking (Heuristic Cross-Encoder).
"""

from __future__ import annotations
from dataclasses import dataclass, field
import numpy as np
import logging
# [SOVEREIGN LOGGING] Silencing verbose model loading reports
logging.getLogger("transformers").setLevel(logging.ERROR)
logging.getLogger("sentence_transformers").setLevel(logging.WARNING)

from sentence_transformers import CrossEncoder
from index.node import QueryResult, VaultNode

def reciprocal_rank_fusion(ranked_lists: list[list[str]], k: int = 60, weights: list[float] | None = None) -> dict[str, float]:
    if weights is None:
        weights = [1.0] * len(ranked_lists)
    scores: dict[str, float] = {}
    for ranked_list, weight in zip(ranked_lists, weights):
        for rank, node_id in enumerate(ranked_list, start=1):
            scores[node_id] = scores.get(node_id, 0.0) + weight / (k + rank)
    return scores

class FusionRanker:
    """
    Fusion Ranker industrializzato con Speculative Reranking.
    """
    def __init__(self, alpha: float = 0.7, use_reranker: bool = True):
        self.alpha = alpha
        self.use_reranker = use_reranker
        self.rrf_k = 60
        self._ce_model = None
        if use_reranker:
            try:
                # Modello ultra-leggero e veloce (Gap #4)
                # v11.6.7: Bypass aggressivo se HF è offline o instabile
                print("⏳ [Fusion] Attivazione Neural Reranker (TinyBERT)...")
                import os
                # Tentiamo di caricare solo se è già in cache o se il network risponde
                self._ce_model = CrossEncoder('cross-encoder/ms-marco-TinyBERT-L-2-v2', max_length=512, device='cpu')
                print("🎯 [Fusion] Cross-Encoder Activated [OFFLINE/LOCAL READY].")
            except Exception as e:
                print(f"📡 [Fusion] HuggingFace unreachable or model missing. Switching to Jaccard Fallback.")
                self._ce_model = None

    def fuse(
        self,
        dense_results:  list[tuple[str, float]],
        sparse_results: list[tuple[str, float]],
        graph_results:  list[tuple[str, float]],
        nodes:          dict[str, VaultNode],
        query_text:     str | None = None,
        top_k:          int = 10,
        rerank_n:       int = 50,
    ) -> list[QueryResult]:
        
        if not dense_results and not sparse_results and not graph_results:
            return []

        # 1. RRF Fusion
        # Dense results per HNSW sono (id, dist), sort ASC
        dense_ranked = [nid for nid, _ in sorted(dense_results, key=lambda x: x[1])]
        # Sparse e Graph sono (id, score), sort DESC
        sparse_ranked = [nid for nid, _ in sorted(sparse_results, key=lambda x: x[1], reverse=True)]
        graph_ranked = [nid for nid, _ in sorted(graph_results, key=lambda x: x[1], reverse=True)]
        
        ranked_lists = [l for l in [dense_ranked, sparse_ranked, graph_ranked] if l]
        weights = [self.alpha if l is dense_ranked else (1.0-self.alpha) for l in ranked_lists]
        
        rrf_scores = reciprocal_rank_fusion(ranked_lists, k=self.rrf_k, weights=weights)

        # 2. Converti in QueryResult
        candidates = []
        for nid, rrf in rrf_scores.items():
            if nid not in nodes: continue
            node = nodes[nid]
            candidates.append(QueryResult(
                node=node,
                final_score=rrf,
                dense_score=1.0 - next((d for n, d in dense_results if n == nid), 1.0),
                sparse_score=next((s for n, s in sparse_results if n == nid), 0.0),
                path="fused"
            ))

        # Sort by RRF
        candidates.sort(key=lambda x: x.final_score, reverse=True)
        top_pool = candidates[:rerank_n]

        # 3. Cross-Encoder Reranking (Gap #4 — Precision Factor)
        if self.use_reranker and query_text and top_pool:
            if self._ce_model:
                # Batch Reranking
                pairs = [[query_text, res.node.text] for res in top_pool]
                ce_scores = self._ce_model.predict(pairs, show_progress_bar=False)
                
                for res, ce_score in zip(top_pool, ce_scores):
                    res.rerank_score = float(ce_score)
                    # Normalizzazione Sigmoid dello score Cross-Encoder
                    sig_ce = 1 / (1 + np.exp(-ce_score))
                    res.final_score = (res.final_score * 0.4) + (sig_ce * 0.6)
            else:
                # Fallback Jaccard
                q_text = (query_text or "").lower()
                q_tokens = set(q_text.split())
                for res in top_pool:
                    n_text = (res.node.text or "").lower()
                    n_tokens = set(n_text.split())
                    intersection = len(q_tokens & n_tokens)
                    union = len(q_tokens | n_tokens)
                    jaccard = (intersection / union) if union > 0 else 0.0
                    res.rerank_score = jaccard
                    res.final_score = (res.final_score * 0.7) + (jaccard * 0.3)
            
            top_pool.sort(key=lambda x: x.final_score, reverse=True)

        return top_pool[:top_k]
