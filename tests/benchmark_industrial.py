"""
tests/benchmark_industrial.py
──────────────────────────────────
Benchmark Industriale per NeuralVault v0.2.5.
Generazione della 'Tabella della Verità' (Recall vs Bit Dimension).
"""

import numpy as np
import time
import sys
import os

# Root del progetto
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from index.turboquant import TurboQuantizer

def run_industrial_benchmark(dim=1024, n=10000):
    print(f"📊 NEURALVAULT INDUSTRIAL BENCHMARK (N={n}, Dim={dim})")
    
    # 1. Generazione Dataset Realistico (Segnale + Rumore)
    data = np.random.randn(n, dim).astype(np.float32)
    # Introduciamo una struttura semantica nelle prime 100 dimensioni
    data[:, :100] *= 5.0
    for i in range(n):
        data[i] /= np.linalg.norm(data[i])
        
    query = np.random.randn(dim).astype(np.float32)
    query[:100] *= 5.0
    query /= np.linalg.norm(query)

    # 2. Ground Truth (FP32)
    start_fp = time.time()
    scores_fp32 = np.dot(data, query)
    ground_truth_top10 = np.argsort(scores_fp32)[-10:][::-1]
    latency_fp = (time.time() - start_fp) * 1000
    print(f"✅ Ground Truth (FP32): Calcolato in {latency_fp:.2f}ms")

    # 3. Test multi-livello DABA
    # Config: (Target Bits, Label)
    configs = [
        (8.0, "High Precision (8-bit)"),
        (4.0, "Standard (4-bit)"),
        (3.5, "Sovereign Target (3.5-bit)"),
        (2.0, "Ultra Compressed (2-bit)"),
        (1.2, "Experimental (1.2-bit)")
    ]
    
    print("\n| Configurazione | Avg Bits | Recall@10 | Memory (%) | Latency (ms) |")
    print("| :--- | :--- | :--- | :--- | :--- |")
    
    # Baseline FP32
    print(f"| FP32 (Full) | 32.0 | 1.000 | 100.0% | {latency_fp:.2f} |")

    # Simuliamo pesi SIT (Prime 100 dim importanti)
    weights = np.ones(dim)
    weights[:100] = 5.0 

    for target_bits, label in configs:
        q = TurboQuantizer(dim=dim, bits_main=3)
        q.update_daba_resolutions(weights, max_avg_bits=target_bits)
        
        # Encoding
        start_enc = time.time()
        reprs = [q.encode(v) for v in data]
        
        # Search
        start_search = time.time()
        scores_tq = [q.unbiased_dot(query, r) for r in reprs]
        top10_tq = np.argsort(scores_tq)[-10:][::-1]
        latency_tq = (time.time() - start_search) * 1000
        
        # Calcolo Recall@10
        hits = len(set(ground_truth_top10) & set(top10_tq))
        recall = hits / 10.0
        
        mem_pct = (target_bits / 32.0) * 100
        print(f"| {label} | {np.mean(q.bit_resolutions):.2f} | {recall:.3f} | {mem_pct:.1f}% | {latency_tq:.2f} |")

    print("\n🏺 NeuralVault: Benchmark completato. Dati pronti per ARCHITECTURE_README update.")

if __name__ == "__main__":
    run_industrial_benchmark()
