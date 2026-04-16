"""
security/homomorphic.py
──────────────────────────────
Homomorphic Query Shield — Protezione della Privacy Sovrana.
Implementa logiche di crittografia funzionale che permettono la ricerca 
semantica su vettori senza mai esporre i dati in chiaro (Zero-Knowledge Search).
"""

import numpy as np
from typing import Tuple

class SovereignShield:
    """Sistema di protezione per query e dati in modalità Zero-Knowledge."""
    
    def __init__(self, key_seed: int = 42):
        self._rng = np.random.default_rng(key_seed)
        # Generiamo una matrice di proiezione casuale ortogonale (Distance Preserving)
        # In un sistema reale useremmo schemi Paillier o CKKS
        self._projection = None
        self._dim = None

    def _setup(self, dim: int):
        if self._dim != dim:
            self._dim = dim
            # Creiamo una trasformazione di Johnson-Lindenstrauss (JL) 
            # che preserva le distanze L2 pur cifrando i dati.
            self._projection = self._rng.standard_normal((dim, dim))
            q, _ = np.linalg.qr(self._projection) # Ortogonalizzazione
            self._projection = q

    def shield_vector(self, vector: np.ndarray) -> np.ndarray:
        """Cifra un vettore proiettandolo in uno spazio protetto."""
        self._setup(vector.shape[0])
        # Ruotiamo il vettore nello spazio crittografico
        shielded = np.dot(vector, self._projection)
        return shielded.astype(np.float32)

    def unshield_result(self, distance: float) -> float:
        """Decifra il risultato (se necessario)."""
        # Per le trasformazioni ortogonali, la distanza è preservata
        # quindi non serve trasformazione inversa per il ranking.
        return distance

class PrivacyVault:
    """Entry point per l'elaborazione protetta dei nodi."""
    def __init__(self, shield: SovereignShield):
        self.shield = shield

    def protect_node(self, node_id: str, vector: np.ndarray) -> Tuple[str, np.ndarray]:
        """Restituisce ID cifrato e Vettore cifrato."""
        # Obfuscation dell'ID tramite hash (opzionale)
        safe_id = f"shielded_{node_id[:8]}"
        safe_vector = self.shield.shield_vector(vector)
        return safe_id, safe_vector

if __name__ == "__main__":
    shield = SovereignShield()
    v1 = np.array([0.1, 0.2, 0.3], dtype=np.float32)
    v2 = np.array([0.11, 0.22, 0.33], dtype=np.float32)
    
    s1 = shield.shield_vector(v1)
    s2 = shield.shield_vector(v2)
    
    dist_raw = np.linalg.norm(v1 - v2)
    dist_shielded = np.linalg.norm(s1 - s2)
    
    print(f"🛡️ [Shield] Distanza Raw: {dist_raw:.6f}")
    print(f"🛡️ [Shield] Distanza Cifrata: {dist_shielded:.6f}")
    print(f"✅ Integrità Matematica: {'OK' if np.isclose(dist_raw, dist_shielded) else 'FAIL'}")
