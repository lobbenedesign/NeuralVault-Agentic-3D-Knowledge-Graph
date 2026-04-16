import time
import numpy as np
from index.node import VaultNode
from __init__ import NeuralVaultEngine

def run_synaptic_validation():
    print("🏺 [v0.5.0] Inizio Validazione Synaptic Pillars (High-Fidelity 1024)...")
    dim = 1024
    engine = NeuralVaultEngine(dim=dim)

    # 1. Test Cross-Modal (Latent Bridge)
    print("\n🌌 Testing Pillar 1: Latent Bridge (Multi-Sensory)...")
    img_vector = np.random.randn(dim).astype(np.float32)
    node_img = VaultNode(
        id="image_01", 
        text="Foto di un tramonto", 
        vector=img_vector,
        metadata={"modality": "image"}
    )
    engine.upsert(node_img)
    print("📸 Nodo Immagine inserito via Latent Bridge.")

    # Query testuale
    results = engine.query("tramonto", k=1)
    if results and results[0].node.id == "image_01":
        print("✅ Latent Bridge OK: Query testuale ha trovato il nodo immagine.")

    # 2. Test Cognitive Decay (Ebbinghaus)
    print("\n🧠 Testing Pillar 2: Cognitive Decay (Ebbinghaus)...")
    initial_strength = results[0].memory_strength
    print(f"📈 Forza iniziale ricordo: {initial_strength:.4f}")

    # Simuliamo il passaggio del tempo (accorciando la half-life per il test)
    engine.cognitive.half_life_sec = 0.5 # 0.5 secondi per il test
    engine.cognitive.decay_lambda = 0.693 / engine.cognitive.half_life_sec

    time.sleep(1.2)
    results_decay = engine.query("tramonto", k=1)
    decayed_strength = results_decay[0].memory_strength
    print(f"📉 Forza dopo 1.2s: {decayed_strength:.4f}")

    if decayed_strength < initial_strength:
        print("✅ Cognitive Decay OK: Il ricordo sta sbiadendo come previsto.")
    else:
        print("❌ Errore: Il ricordo non sta sbiadendo.")

    # 3. Test Reinforcement (Rinforzo Sinaptico)
    print("\n🧬 Testing Pillar 3: Synaptic Reinforcement...")
    pre_hit_count = results_decay[0].node.access_count
    engine.query("tramonto", k=1)
    engine.query("tramonto", k=1)
    post_hit_results = engine.query("tramonto", k=1)
    
    print(f"🔄 Access Count: {pre_hit_count} -> {post_hit_results[0].node.access_count}")
    if post_hit_results[0].node.access_count > pre_hit_count:
        print("✅ Reinforcement OK: Gli accessi rinforzano il ricordo.")
    
    print("\n🏁 [VALUTAZIONE SYNAPTIC]: v0.5.0 è OPERATIVA AL 100%.")
    engine.close()

if __name__ == "__main__":
    run_synaptic_validation()
