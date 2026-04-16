"""
retrieval/bridge.py — [v0.5.0 Multi-Sensory Latent Bridge]
────────────────────────────────────────────────────────
Permette il Cross-Modal alignment tra Testo, Immagini e Audio.
Usa matrici di proiezione (Semantic Hooks) per unificare gli spazi vettoriali.
"""

import numpy as np
import torch
import torch.nn as nn

class SemanticHook(nn.Module):
    """Piccolo MLP (Hook) per proiettare una modalità nello spazio unificato."""
    def __init__(self, in_dim: int, out_dim: int):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(in_dim, 512),
            nn.GELU(),
            nn.Linear(512, out_dim)
        )
    
    def forward(self, x):
        return self.net(x)

class LatentBridge:
    """Orchestra l'allineamento cross-modale (v0.5.0) con risoluzione dinamica."""
    def __init__(self, unified_dim: int = 1024):
        self.unified_dim = unified_dim
        # Registro degli hook inizializzati on-demand per gestire dimensioni variabili
        self._hooks = nn.ModuleDict()
    
    def _get_hook(self, modality: str, in_dim: int) -> SemanticHook:
        key = f"{modality}_{in_dim}"
        if key not in self._hooks:
            print(f"🌉 [Bridge] Inizializzazione Hook: {modality} ({in_dim} -> {self.unified_dim})")
            self._hooks[key] = SemanticHook(in_dim, self.unified_dim)
        return self._hooks[key]

    def align(self, vector: np.ndarray, modality: str) -> np.ndarray:
        """Proietta il vettore originale nello spazio unificato della Mesh."""
        # Se il vettore è 1D, prendiamo la sua lunghezza
        in_dim = vector.shape[0] if len(vector.shape) == 1 else vector.shape[1]
        hook = self._get_hook(modality, in_dim)
        
        with torch.no_grad():
            tensor_v = torch.from_numpy(vector).float()
            # Se batch dimension manca, la aggiungiamo
            was_1d = len(tensor_v.shape) == 1
            if was_1d: tensor_v = tensor_v.unsqueeze(0)
            
            aligned = hook(tensor_v).numpy()
            
            if was_1d: aligned = aligned.squeeze(0)
            
        return aligned
