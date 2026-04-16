
import sys
import os
from pathlib import Path

# Aggiungi la directory corrente al path per importare l'engine
sys.path.append(os.getcwd())

from __init__ import NeuralVaultEngine

def check_engine():
    print("🔍 [Diagnosis] Avvio diagnostica NeuralVault...")
    engine = NeuralVaultEngine(data_dir="./vault_data")
    
    # Simula il caricamento (senza avviare tutti i daemon)
    engine._recovery_boot()
    
    print(f"📊 Nodi in RAM (self._nodes): {len(engine._nodes)}")
    
    nodes_with_vectors = [n for n in engine._nodes.values() if n.vector is not None]
    print(f"🧬 Nodi con vettori: {len(nodes_with_vectors)}")
    
    if nodes_with_vectors:
        sample = nodes_with_vectors[0]
        print(f"📍 Esempio vettore ID {sample.id[:8]}: Shape {sample.vector.shape}, Dtype {sample.vector.dtype}")
    
    stats = engine.stats(limit=100)
    print(f"🌌 Punti nel Point Cloud: {len(stats.get('point_cloud', []))}")
    if len(stats.get('point_cloud', [])) > 0:
        p = stats['point_cloud'][0]
        print(f"✨ Esempio punto 3D: x={p['x']}, y={p['y']}, z={p['z']}")

if __name__ == "__main__":
    check_engine()
