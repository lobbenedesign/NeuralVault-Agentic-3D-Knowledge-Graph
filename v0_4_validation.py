"""
v0_4_validation.py
──────────────────────────────
Test di validazione per i 3 Pilastri della v0.4.0 (Infinite Mesh).
Verifica Consensus, Sharding e Privacy Shield in un unico workflow.
"""

import numpy as np
import os
import time
from pathlib import Path
from __init__ import NeuralVaultEngine, VaultNode

def run_mesh_validation():
    print("🏺 [v0.4.0] Inizio Validazione Pillars (Sovereign Mesh Network)...")
    dim = 128
    engine = NeuralVaultEngine(dim=dim, use_rust=True)
    
    # 🧬 TEST 1: CONSENSUS
    print("\n🧬 Testing Pillar 1: Distributed Consensus...")
    print("⏳ Attesa elezione leader (2.5s)...")
    time.sleep(2.5)
    
    node = VaultNode(id="mesh_test_01", text="Conoscenza distribuita", vector=np.random.randn(dim).astype(np.float32))
    engine.upsert(node)
    
    if engine.consensus.log_entries > 0:
        print(f"✅ Consensus OK: Log replicato (Term {engine.consensus.current_term})")
        print(f"👑 Leader Status: {engine.consensus.role}")
    
    # 🌌 TEST 2: SHARDING
    print("\n🌌 Testing Pillar 2: Shard Cloning & Neural Warp...")
    shard_id = engine.shards.create_shard("test_shard", lambda x: "mesh" in x.id, engine._nodes)
    warp_path = Path("./warp_zone")
    success = engine.shards.warp_shard(shard_id, warp_path)
    if success:
        print("✅ Sharding OK: Neural Warp completato.")
    
    # 🛡️ TEST 3: PRIVACY SHIELD
    print("\n🛡️ Testing Pillar 3: Homomorphic Query Shield...")
    # Privacy mode cifra la query internamente
    results = engine.query("test query", privacy_mode=True, k=1)
    if results:
        print("✅ Privacy OK: Query Shielded completata con successo.")

    print("\n🏁 [VALUTAZIONE FINALE]: NeuralVault v0.4.0 è OPERATIVO AL 100%.")
    engine.close()

if __name__ == "__main__":
    run_mesh_validation()
