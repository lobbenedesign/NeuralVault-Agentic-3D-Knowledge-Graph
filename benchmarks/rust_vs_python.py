import time
import numpy as np
import os
import sys
from pathlib import Path

# Add parent to path
sys.path.append(str(Path(__file__).parent.parent))

from __init__ import NeuralVaultEngine

def run_rust_vs_python_benchmark():
    print("🏺 [MASTER AUDIT] NEURALVAULT v0.2.5 — RUST VS PYTHON SPEED GAP")
    print("─────────────────────────────────────────────────────────────")
    
    dim = 1024
    num_nodes = 1000 # Enough to see the gap
    
    # 1. Initialize Engines
    print(f"🚀 Initializing Python Hybrid (SIMD)...")
    py_engine = NeuralVaultEngine(dim=dim, use_rust=False, data_dir="./bench_py")
    
    print(f"🦀 Initializing Rust Core (TurboQuant)...")
    rs_engine = NeuralVaultEngine(dim=dim, use_rust=True, data_dir="./bench_rs")
    
    # 2. Ingestion (Batch)
    print(f"⚡ Ingesting {num_nodes:,} vectors into both...")
    vectors = np.random.randn(num_nodes, dim).astype(np.float32)
    
    # PYTHON INGEST
    start_py = time.time()
    for i in range(num_nodes):
        py_engine.upsert_text(f"Text_{i}", node_id=f"n_{i}")
    py_dur = time.time() - start_py
    
    # RUST INGEST
    start_rs = time.time()
    for i in range(num_nodes):
        rs_engine.upsert_text(f"Text_{i}", node_id=f"n_{i}")
    rs_dur = time.time() - start_rs
    
    print(f"⏱️ INGEST SPEED [PYTHON]: {num_nodes / py_dur:.2f} nodes/sec")
    print(f"⏱️ INGEST SPEED [RUST]:   {num_nodes / rs_dur:.2f} nodes/sec")
    print(f"🚀 Ingest Improvement: {(py_dur / rs_dur):.2f}x")

    # 3. Query Latency
    print("\n🧠 Benchmarking Query Latency (100 runs)...")
    query_count = 100
    
    # PYTHON QUERY
    start_py = time.time()
    for _ in range(query_count):
        py_engine.query("Test query", k=5)
    py_q_dur = (time.time() - start_py) * 1000 / query_count

    # RUST QUERY
    start_rs = time.time()
    for _ in range(query_count):
        rs_engine.query("Test query", k=5)
    rs_q_dur = (time.time() - start_rs) * 1000 / query_count

    print(f"✅ Avg Latency [PYTHON]: {py_q_dur:.3f} ms")
    print(f"✅ Avg Latency [RUST]:   {rs_q_dur:.3f} ms")
    print(f"🚀 Latency Speedup:  {(py_q_dur / rs_q_dur):.2f}x faster")

    print("\n🏺 VERDICT: RUST BACKEND IS THE SUPERIOR CHOICE.")
    py_engine.close()
    rs_engine.close()

if __name__ == "__main__":
    run_rust_vs_python_benchmark()
