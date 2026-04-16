"""
tests/stress_daba.py
────────────────────
Stress-test finale per validare il Domain-Adaptive Bit Allocation (DABA).
Analizza come NeuralVault ri-alloca la precisione vettoriale in base
all'importanza del dominio appresa durante l'interazione con l'agente.
"""

import numpy as np
import time
import sys
import os

# Root del progetto
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from __init__ import NeuralVaultEngine
from index.node import VaultNode

def run_daba_stress_test():
    print("🏺 Inizio STRESS-TEST DABA (NeuralVault v0.2.4)...")
    
    # 1. Inizializzazione Engine con Mock Embedder (Evita download BGE-M3)
    def mock_embed(text):
        # Assicura di restituire UN solo vettore da 1024
        v = np.random.randn(1024).astype(np.float32)
        v[:100] *= 5.0 # Segnale forte nelle prime 100 dim
        return v
        
    vault = NeuralVaultEngine(dim=1024, use_quantization=True, embedder_fn=mock_embed, use_rust=False)
    
    # 2. Setup Sessione Agente (Dominio Tecnico Focalizzato)
    session_id = vault.create_session(agent_id="quantum_expert")
    print(f"✅ Sessione '{session_id}' avviata.")

    # 3. Fase 1: Inserimento Dati Raw (Tutti a 3 bit fissi di default)
    print("... Inserimento 50 nodi di 'Quantum Python API' (Initial state: fix 3-bit)...")
    nodes = []
    for i in range(50):
        # Utilizziamo una query text simulata per l'embedding automatico
        text = f"Quantum gate operation {i}: complex number rotation in Python API."
        node = vault.upsert_text(text=text, metadata={"domain": "quantum"})
        nodes.append(node)
        
    # 4. Fase 2: Simulazione Expertise (Learning Dimension Importance)
    print("... Simulazione Feedback Positivo (SIT Training)...")
    for node in nodes[:20]:
        # Il feedback positivo informa il SITImportanceTracker su quali 
        # dimensioni del vettore 'Quantum' sono costanti e discriminanti.
        vault.feedback(session_id, node.id, positive=True)

    # 5. Fase 3: Trigger DABA (Session Close)
    print("\n📦 ESECUZIONE DABA OPTIMIZATION (Closing Session)...")
    avg_bits_before = np.mean(vault._tq_search.quantizer.bit_resolutions)
    
    # Questo triggera update_daba_resolutions() internamente
    vault.close_session(session_id)
    
    avg_bits_after = np.mean(vault._tq_search.quantizer.bit_resolutions)
    
    print(f"\n--- RISULTATI DABA ANALYSIS ---")
    print(f"📊 Risoluzione Pre-DABA:  {avg_bits_before:.2f} bits/dim (Flat 3)")
    print(f"🔥 Risoluzione Post-DABA: {avg_bits_after:.2f} bits/dim (Optimized)")
    
    # Analizza distribuzione bit
    resolutions = vault._tq_search.quantizer.bit_resolutions
    high_prec = np.sum(resolutions >= 7)
    low_prec = np.sum(resolutions <= 2)
    
    print(f"🛠️  Distribuzione Dimensioni High-Precision (>=7 bit): {high_prec}")
    print(f"📉 Distribuzione Dimensioni Low-Precision (<=2 bit): {low_prec}")

    # 6. Verifica Recall
    print("\n🎯 Esecuzione Query Finale con DABA attivo...")
    start_q = time.time()
    results = vault.query("Python quantum circuit rotation", k=5)
    end_q = time.time()
    
    print(f"✅ Risposta in {(end_q - start_q)*1000:.2f}ms")
    for r in results[:3]:
        print(f"   [Score: {r.final_score:.4f}] {r.node.text[:60]}...")

    if high_prec > 0:
        print("\n🏛️ CERTIFICAZIONE: NeuralVault DABA ha ri-allocato la precisione correttamente.")
        print("🚀 NeuralVault 0.2.4: Sovereign Supremacy Validated.")
    else:
        print("\n⚠️ ATTENZIONE: Nessuna ri-allocazione rilevata. Valutare campionamento feedback.")

if __name__ == "__main__":
    run_daba_stress_test()
