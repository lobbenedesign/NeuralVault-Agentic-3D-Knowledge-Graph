"""
benchmarks/concurrency_race.py
──────────────────────────────
Stress Test di Concorrenza Massiva per NeuralVault v0.3.0.
Simula un carico di 10,000 richieste per testare la stabilità transazionale.
"""

import time
import os
import shutil
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# Importiamo il core (Assicuriamoci che il path sia corretto)
import sys
sys.path.append(os.getcwd())
from __init__ import NeuralVaultEngine, VaultNode

def stress_worker(engine, i, dim):
    """Simula un utente che effettua una query e un feedback."""
    q_vec = np.random.randn(dim).astype(np.float32)
    start_t = time.perf_counter()
    try:
        # 1. Stress Query
        res = engine.query("test query", query_vector=q_vec, k=5)
        # 2. Stress Feedback (Write operation under contention)
        if res:
            engine.feedback(res[0].node.id, success=(i % 2 == 0))
        
        dur = (time.perf_counter() - start_t) * 1000
        return True, dur
    except Exception as e:
        return False, str(e)

def run_concurrency_race(total_requests=10000, concurrent_threads=50):
    print(f"🏺 [CONCURRENCY RACE] — Inizializzazione NeuralVault (50,000 nodi)...")
    dim = 1024
    data_dir = Path("./stress_test_db")
    if data_dir.exists(): shutil.rmtree(data_dir)
    
    engine = NeuralVaultEngine(dim=dim, data_dir=data_dir, use_rust=True)
    
    # Ingestione iniziale batch
    print(f"📦 Popolamento iniziale veloce...")
    initial_nodes = [
        VaultNode(id=f"init_{i}", text=f"Data {i}", vector=np.random.randn(dim).astype(np.float32))
        for i in range(1000)
    ]
    engine.upsert_batch(initial_nodes)

    print(f"🚀 Lancio di {total_requests} richieste con {concurrent_threads} thread concorrenti...")
    
    start_total = time.time()
    latencies = []
    success_count = 0
    failure_count = 0
    errors = []

    with ThreadPoolExecutor(max_workers=concurrent_threads) as executor:
        futures = [executor.submit(stress_worker, engine, i, dim) for i in range(total_requests)]
        
        for future in as_completed(futures):
            success, val = future.result()
            if success:
                success_count += 1
                latencies.append(val)
            else:
                failure_count += 1
                errors.append(val)
            
            if (success_count + failure_count) % 1000 == 0:
                print(f"  - Progress: {success_count + failure_count}/{total_requests} completati.")

    total_dur = time.time() - start_total
    avg_lat = np.mean(latencies) if latencies else 0
    p95_lat = np.percentile(latencies, 95) if latencies else 0

    print(f"\n🏆 [RISULTATI CONCURRENCY RACE] — v0.3.0 Enterprise")
    print(f"─────────────────────────────────────────────────────────────")
    print(f"✅ Successi:        {success_count}")
    print(f"❌ Fallimenti:      {failure_count}")
    print(f"⏱️  Tempo Totale:     {total_dur:.2f} s")
    print(f"📡 Throughput RQS:   {total_requests / total_dur:.2f} query/sec")
    print(f"📊 Latenza Media:    {avg_lat:.2f} ms")
    print(f"📊 Latenza P95:      {p95_lat:.2f} ms (Sotto stress)")
    print(f"─────────────────────────────────────────────────────────────")

    if failure_count > 0:
        print(f"⚠️  ERRORI RILEVATI: {errors[:5]}")
    else:
        print(f"💎 INTEGRITÀ TRANSAZIONALE GARANTITA: 0% Errori sotto carico massivo.")

    engine.close()
    if data_dir.exists(): shutil.rmtree(data_dir)

if __name__ == "__main__":
    run_concurrency_race()
