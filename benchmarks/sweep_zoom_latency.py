"""
benchmarks/sweep_zoom_latency.py
──────────────────────────────────
Benchmarking script for Sovereign Evolution Phase 1.
Validates 'Sweep' (broad search) and 'Zoom' (deep localized search) latencies.
"""

import time
import sys
from pathlib import Path

# Add parent to path
sys.path.append(str(Path(__file__).parent.parent))

from __init__ import NeuralVaultEngine
import numpy as np

def run_benchmark():
    print("🏺 [SWEEP/ZOOM LATENCY BENCHMARK] NEURALVAULT v1.0-ALPHA")
    print("─────────────────────────────────────────────────────────────")
    
    dim = 1024
    num_nodes = 10000
    engine = NeuralVaultEngine(dim=dim, use_rust=True, data_dir="./data_bench")
    
    # 1. Popolamento rapido
    print(f"🚀 Ingesting {num_nodes} nodes for benchmarking...")
    nodes = []
    for i in range(num_nodes):
        # Create some clusters for Zooming
        collection = "cluster_a" if i < 1000 else "cluster_b" if i < 2000 else "default"
        engine.upsert_text(
            f"Sovereign node {i} in collection {collection}", 
            id=f"n_{i}", 
            metadata={"collection": collection, "index": i}
        )
    
    print("✅ Ingestion complete. Running Latency Tests...\n")
    
    # 2. SWEEP LATENCY (Broad Search, high K)
    print("🔭 Testing SWEEP Latency (k=100, Global Scan)...")
    sweep_times = []
    for _ in range(50):
        v = np.random.randn(dim).astype(np.float32)
        t0 = time.time()
        engine.query("Sweep query", query_vector=v, k=100)
        sweep_times.append((time.time() - t0) * 1000)
    
    avg_sweep = sum(sweep_times) / len(sweep_times)
    p99_sweep = np.percentile(sweep_times, 99)
    print(f"   - Avg: {avg_sweep:.4f} ms")
    print(f"   - p99: {p99_sweep:.4f} ms")
    
    # 3. ZOOM LATENCY (Filtered/Localized Search, low K)
    print("\n🔍 Testing ZOOM Latency (k=5, Filtered by Collection)...")
    zoom_times = []
    for _ in range(50):
        v = np.random.randn(dim).astype(np.float32)
        t0 = time.time()
        # Prefilter zoom
        engine.query("Zoom query", query_vector=v, k=5, collection="cluster_a")
        zoom_times.append((time.time() - t0) * 1000)
        
    avg_zoom = sum(zoom_times) / len(zoom_times)
    p99_zoom = np.percentile(zoom_times, 99)
    print(f"   - Avg: {avg_zoom:.4f} ms")
    print(f"   - p99: {p99_zoom:.4f} ms")
    
    print("\n─────────────────────────────────────────────────────────────")
    print("🏆 BENCHMARK COMPLETE.")
    
    # Cleanup
    engine.close()

if __name__ == "__main__":
    run_benchmark()
