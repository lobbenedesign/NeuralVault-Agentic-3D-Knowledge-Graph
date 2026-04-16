#!/usr/bin/env python3
"""
scripts/quickstart.py
──────────────────────
Demo completa di NeuralVault: mostra tutte le feature principali
in ~60 righe di codice.

Esegui con:
    python scripts/quickstart.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from neuralvault import NeuralVaultEngine
from neuralvault.core.node import RelationType, VaultNode

print("=" * 60)
print("  NeuralVault — Quick Start Demo")
print("=" * 60)

# ── 1. Crea il vault ──────────────────────────────────────────
vault = NeuralVaultEngine(dim=128)
print("\n[1/6] Vault creato (dim=128)")

# ── 2. Inserisci documenti ────────────────────────────────────
docs = [
    ("doc_intro",  "Introduzione al machine learning: concetti base e applicazioni"),
    ("doc_reti",   "Le reti neurali artificiali: struttura e funzionamento"),
    ("doc_back",   "Backpropagation: algoritmo per il training delle reti neurali"),
    ("doc_gatto",  "Il gatto è un mammifero domestico della famiglia Felidae"),
    ("doc_python", "Python è un linguaggio versatile usato in data science e web"),
    ("doc_llm",    "I Large Language Models usano transformer e attention mechanism"),
]

def fake_embed(text: str, seed: int = None) -> np.ndarray:
    """Embedding sintetico deterministico per la demo."""
    if seed is None:
        seed = hash(text[:20]) % 1000
    rng = np.random.RandomState(seed)
    v   = rng.randn(128).astype(np.float32)
    return v / np.linalg.norm(v)

for node_id, text in docs:
    node = VaultNode(
        id=node_id,
        text=text,
        vector=fake_embed(text),
        metadata={"topic": "ml" if "neural" in text.lower() or "machine" in text.lower() else "other"},
    )
    vault.upsert(node)

print(f"[2/6] Inseriti {len(docs)} documenti")

# ── 3. Aggiungi semantic edges ────────────────────────────────
vault.add_edge("doc_intro", "doc_reti",   RelationType.SEQUENTIAL,   weight=0.9)
vault.add_edge("doc_reti",  "doc_back",   RelationType.PREREQUISITE, weight=0.95)
vault.add_edge("doc_reti",  "doc_llm",    RelationType.CITES,        weight=0.7)
print("[3/6] Semantic edges aggiunti")

# ── 4. Query con graph expansion ─────────────────────────────
print("\n[4/6] Query: 'reti neurali training'")
results = vault.query(
    query_text="reti neurali training",
    query_vector=fake_embed("reti neurali training"),
    k=4,
    graph_hops=2,
)
for i, r in enumerate(results, 1):
    print(f"  #{i} [{r.node.id}] score={r.final_score:.3f}  path={r.path}")
    print(f"      {r.node.text[:60]}...")

# ── 5. Sessione agente con feedback ───────────────────────────
print("\n[5/6] Sessione agente con feedback")
session_id = vault.create_session(agent_id="demo_agent")

results2 = vault.query(
    query_text="backpropagation algoritmo",
    query_vector=fake_embed("backpropagation"),
    k=3,
    session_id=session_id,
    graph_hops=1,
)
print(f"  Query eseguita, {len(results2)} risultati")

# Feedback positivo sul primo risultato
if results2:
    vault.feedback(session_id, results2[0].node.id, positive=True)
    print(f"  Feedback positivo su: {results2[0].node.id}")

edges_created = vault.close_session(session_id)
print(f"  Sessione chiusa — {edges_created} nuovi edges inferiti")

# ── 6. Stats finali ───────────────────────────────────────────
print("\n[6/6] Stats finali:")
stats = vault.stats()
print(f"  Nodi totali:       {stats['total_nodes']}")
print(f"  HNSW livelli:      {stats['hnsw']['total_levels']}")
print(f"  Working tier:      {stats['memory_tiers']['working_size']} nodi")
print(f"  Semantic tier:     {stats['memory_tiers']['semantic_size']} nodi")
print(f"  Vocab BM25:        {stats['sparse_vocab']} token")
print(f"  Hit rate tier:     {stats['memory_tiers']['hit_rate']:.1%}")

print("\n" + "=" * 60)
print("  Demo completata con successo!")
print("  Avvia il server con: uvicorn neuralvault.api.main:app --port 8000")
print("=" * 60)
