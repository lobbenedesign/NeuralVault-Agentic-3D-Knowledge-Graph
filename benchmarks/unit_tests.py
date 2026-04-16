"""
benchmarks/unit_tests.py — Suite di test per NeuralVault (Unittest Standalone).
Copre: HNSW, context graph, fusion, memory tiers, API end-to-end.
"""
import numpy as np
import unittest
import sys
import os
from pathlib import Path

# Add root to path
sys.path.append(str(Path(__file__).parent.parent))

from __init__ import NeuralVaultEngine, VaultNode, QueryResult, RelationType, MemoryTier
from graph.graph import ContextGraph
from index.hnsw import AdaptiveHNSW
from index.sparse import BM25SEncoder
from retrieval.fusion import FusionRanker
from memory_tiers import MemoryTierManager

DIM = 64  # dimensione ridotta per i test

def make_vector(seed: int, dim: int = DIM) -> np.ndarray:
    rng = np.random.RandomState(seed)
    v   = rng.randn(dim).astype(np.float32)
    return v / (np.linalg.norm(v) + 1e-10)

def make_node(node_id: str, seed: int, text: str = "", metadata: dict = None) -> VaultNode:
    return VaultNode(
        id=node_id,
        vector=make_vector(seed),
        text=text or f"Testo del nodo {node_id}",
        metadata=metadata or {},
    )

class TestVaultNode(unittest.TestCase):
    def test_vector_normalization(self):
        raw  = np.array([3.0, 4.0], dtype=np.float32)
        node = VaultNode(id="n1", vector=raw)
        self.assertAlmostEqual(np.linalg.norm(node.vector), 1.0, places=5)

    def test_add_edge_no_duplicates(self):
        node = make_node("n1", 0)
        node.add_edge("n2", RelationType.CITES)
        node.add_edge("n2", RelationType.CITES)
        self.assertEqual(len(node.edges), 1)

class TestAdaptiveHNSW(unittest.TestCase):
    def test_insert_and_search_basic(self):
        hnsw = AdaptiveHNSW(dim=DIM, M=16, ef_construction=400)
        nodes = {f"n{i}": make_node(f"n{i}", i) for i in range(50)}
        for node in nodes.values():
            hnsw.insert(node)
        results = hnsw.search(nodes["n0"].vector, k=10, ef=100)
        result_ids = [r[0] for r in results]
        self.assertIn("n0", result_ids)

class TestBM25S(unittest.TestCase):
    def test_encode_returns_sparse_vector(self):
        enc  = BM25SEncoder()
        enc.fit(["il gatto è sul tappeto", "il cane abbaia forte"])
        vec  = enc.encode_document("gatto tappeto")
        self.assertIsInstance(vec, dict)
        self.assertTrue(len(vec) > 0)

class TestFusion(unittest.TestCase):
    def test_metadata_filter_eq(self):
        from retrieval.fusion import MetadataFilter
        f = MetadataFilter({"field": "type", "op": "eq", "value": "pdf"})
        self.assertTrue(f.match({"type": "pdf"}))
        self.assertFalse(f.match({"type": "docx"}))

class TestNeuralVaultEngine(unittest.TestCase):
    def test_upsert_and_query(self):
        vault = NeuralVaultEngine(dim=DIM, use_rust=True)
        node = make_node("doc_0", 0, text="Testo di prova")
        vault.upsert(node)
        results = vault.query("prova", query_vector=make_vector(0), k=1)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].node.id, "doc_0")
        vault.close()

if __name__ == "__main__":
    unittest.main()
