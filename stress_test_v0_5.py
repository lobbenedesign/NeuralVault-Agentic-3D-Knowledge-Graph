import time
import numpy as np
from index.node import VaultNode
from __init__ import NeuralVaultEngine

def stress_test_v0_5():
    print("🏺 [v0.5.0] Inizio STRESS TEST: 25.000 Ingestions con Cognitive Layer...")
    dim = 1024
    engine = NeuralVaultEngine(dim=dim)
    
    nodes = []
    for i in range(25000):
        v = np.random.randn(dim).astype(np.float32)
        node = VaultNode(id=f"stress_{i}", text=f"Data point {i}", vector=v)
        nodes.append(node)
    
    start_t = time.time()
    # Eseguiamo a blocchi per simulare carico reale
    batch_size = 1000
    for i in range(0, len(nodes), batch_size):
        engine.upsert_batch(nodes[i:i+batch_size])
        if i % 5000 == 0:
            print(f"📦 Processati {i} nodi...")
            
    total_time = time.time() - start_t
    print(f"\n🏆 STRESS TEST COMPLETATO")
    print(f"⏱️ Tempo totale per 25k ops: {total_time:.2f}s")
    print(f"🚀 Ops/sec: {25000/total_time:.2f}")
    
    if total_time < 80:
        print("✅ PERFORMANCE CERTIFICATA: Sotto la soglia critica dei 80s.")
    else:
        print("⚠️ WARNING: Lieve regressione rilevata.")
        
    engine.close()

if __name__ == "__main__":
    stress_test_v0_5()
