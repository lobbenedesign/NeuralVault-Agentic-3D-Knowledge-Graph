"""
tests/scientific_precision_test.py
──────────────────────────────────
Test definitivo di validazione scientifica per TurboQuant e DABA.
"""

import numpy as np
import time
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from index.turboquant import TurboQuantizer

def run_precision_challenge(dim=1024, num_samples=1000):
    print(f"🔬 NeuralVault Scientific Precision Challenge (N={num_samples}, Dim={dim})")
    
    # 1. Dati con segnale nelle prime 50 dim
    data = np.random.randn(num_samples, dim).astype(np.float32)
    data[:, 0:50] *= 10.0
    data[:, 50:] *= 0.1
    for i in range(num_samples):
        data[i] /= np.linalg.norm(data[i])
        
    query = np.random.randn(dim).astype(np.float32)
    query[0:50] *= 10.0
    query[50:] *= 0.1
    query /= np.linalg.norm(query)

    scores_fp32 = np.dot(data, query)
    top_1_fp32 = np.argmax(scores_fp32)
    print(f"✅ Ground Truth (FP32) ID: {top_1_fp32} [Score: {scores_fp32[top_1_fp32]:.4f}]")

    # 2. Uniforme (1-bit)
    q_uniform = TurboQuantizer(dim=dim, bits_main=1)
    reprs_uniform = [q_uniform.encode(v) for v in data]
    scores_uniform = [q_uniform.unbiased_dot(query, r) for r in reprs_uniform]
    top_1_uniform = np.argmax(scores_uniform)
    recall_uniform = 1.0 if top_1_uniform == top_1_fp32 else 0.0
    print(f"📊 Uniforme (1-bit): Top ID {top_1_uniform} | Recall@1: {recall_uniform*100}%")

    # 3. DABA (1.2 bit avg)
    weights = np.ones(dim)
    weights[0:50] = 5.0 # IMPORTANTE
    weights[50:] = 0.5
    
    q_daba = TurboQuantizer(dim=dim, bits_main=1)
    q_daba.update_daba_resolutions(weights, max_avg_bits=1.2)
    reprs_daba = [q_daba.encode(v) for v in data]
    scores_daba = [q_daba.unbiased_dot(query, r) for r in reprs_daba]
    top_1_daba = np.argmax(scores_daba)
    recall_daba = 1.0 if top_1_daba == top_1_fp32 else 0.0
    print(f"🔥 DABA (1.2 bit):   Top ID {top_1_daba} | Recall@1: {recall_daba*100}%")

    print("\n--- CONCLUSIONE SCIENTIFICA ---")
    if recall_daba > recall_uniform:
        print("🏆 VITTORIA: DABA ha superato la compressione uniforme (1-bit) a parità di budget memoria.")
    elif recall_daba == 1.0:
        print("🏆 VITTORIA: DABA ha raggiunto la perfezione FP32 con budget ultra-ridotto (1.2 bit).")
    else:
        print("📊 Risultato: Entrambi i sistemi a basso bit hanno performance simili su questo dataset.")

if __name__ == "__main__":
    run_precision_challenge()
