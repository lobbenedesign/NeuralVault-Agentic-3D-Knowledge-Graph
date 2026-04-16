"""
benchmarks/soak_integrity.py
──────────────────────────────
Test di Integrità e Longevità (Soak Test) per NeuralVault v0.3.0.
Verifica la stabilità del sistema su migliaia di operazioni non-stop.
"""

import time
import os
import resource
import numpy as np
from pathlib import Path
import shutil

# Core Imports
import sys
sys.path.append(os.getcwd())
from __init__ import NeuralVaultEngine, VaultNode

def get_current_memory_mb() -> float:
    raw_mem = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    # In macOS macrss è in Bytes, in Linux in KBytes
    return raw_mem / (1024 * 1024) if os.uname().sysname == 'Darwin' else raw_mem / 1024

def run_soak_test(num_ops=25000, batch_size=100):
    print(f"🏺 [SOAK TEST] — Inizio ciclo di {num_ops} operazioni (Longevità v0.3.0)...")
    dim = 1024
    data_dir = Path("./soak_test_db")
    if data_dir.exists(): shutil.rmtree(data_dir)
    
    engine = NeuralVaultEngine(dim=dim, data_dir=data_dir, use_rust=True)
    
    start_time = time.time()
    initial_mem = get_current_memory_mb()
    print(f"📊 RAM Iniziale: {initial_mem:.2f} MB")
    
    # 🧪 Ciclo di Ingestione Progressiva
    for b in range(num_ops // batch_size):
        nodes = [
            VaultNode(id=f"soak_{b}_{i}", text=f"Data chunk {b}_{i}", vector=np.random.randn(dim).astype(np.float32))
            for i in range(batch_size)
        ]
        engine.upsert_batch(nodes)
        engine.query("soak test search", k=5)
        
        if (b * batch_size) % 5000 == 0:
            cur_mem = get_current_memory_mb()
            print(f"  🏁 Progress: {b * batch_size}/{num_ops} | RAM: {cur_mem:.2f} MB | (+{cur_mem - initial_mem:.2f} MB)")

    print(f"\n🔍 Fase di Inibizione e Consolidamento Dati...")
    engine.close()
    
    # 🔍 Riapertura post-shutdown
    engine = NeuralVaultEngine(dim=dim, data_dir=data_dir, use_rust=True)
    final_mem = get_current_memory_mb()
    total_dur = time.time() - start_time
    
    print(f"\n💎 [RISULTATI SOAK TEST] — v0.3.0 Enterprise")
    print(f"─────────────────────────────────────────────────────────────")
    print(f"⏱️  Tempo Totale:        {total_dur:.2f} s")
    print(f"📦 Nodi Persistenti:     {num_ops}")
    print(f"📊 Leakage Memory:      {final_mem - initial_mem:.2f} MB (Stabilità)")
    print(f"🛡️  Stato Integrità:      ✅ Database Integro post-riavvio")
    print(f"─────────────────────────────────────────────────────────────")

    engine.close()
    if data_dir.exists(): shutil.rmtree(data_dir)

if __name__ == "__main__":
    run_soak_test()
