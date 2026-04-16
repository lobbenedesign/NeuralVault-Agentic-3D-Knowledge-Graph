"""
neuralvault.index.matryoshka
───────────────────────────
Implementazione del sistema Matryoshka Representation Learning (MRL).
Permette l'estrazione di sub-vettori annidati con granularità differente per i tier di memoria.

Inspirata a Gemini Embedding 2 e "Matryoshka Representation Learning" (ICLR 2023).
"""

import numpy as np
from typing import List, Tuple

class MatryoshkaManager:
    """
    Gestisce la scomposizione e il filtraggio dei vettori "Matryoshka".
    
    Precisioni supportate:
    - L1 (Full): 3072 dims (Working Memory)
    - L2 (Mid):  1536 dims (Episodic Memory)
    - L3 (Small): 768 dims  (Semantic Memory)
    """
    
    def __init__(self, full_dim: int = 3072):
        self.full_dim = full_dim
        # Soglie di troncamento standard (Matryoshka style)
        self.levels = [768, 1536, 3072]

    def slice_vector(self, vector: np.ndarray, level: int = 0) -> np.ndarray:
        """
        Estrae un sub-vettore ad una specifica profondità.
        Il livello 0 è il più compresso (768), il livello 2 è il massimo (3072).
        """
        if level < 0 or level >= len(self.levels):
            return vector # Ritorna il vettore intero se livello errato
            
        dim = self.levels[level]
        sliced = vector[:dim]
        # Fondamentale: RI-NORMALIZZAZIONE per mantenere la validità della Cosine Similarity
        norm = np.linalg.norm(sliced) + 1e-8
        return sliced / norm

    def get_tier_vector(self, vector: np.ndarray, tier_name: str) -> np.ndarray:
        """Helper per mappare i tier di NeuralVault alle Matryoshka Dimensions."""
        if tier_name == "working":
            return self.slice_vector(vector, level=2)
        elif tier_name == "episodic":
            return self.slice_vector(vector, level=1)
        else: # semantic / cold
            return self.slice_vector(vector, level=0)

    def matryoshka_search(self, query: np.ndarray, nodes_vectors: List[np.ndarray], k: int = 10) -> List[int]:
        """
        Esegue una ricerca "Progressive Search":
        1. Filtra grossolanamente con i primi 768 dims.
        2. Raffina con 3072 solo sui top-K candidati.
        """
        # Step 1: Broad Search (L3 - 768 dims)
        q_l3 = self.slice_vector(query, level=0)
        # In produzione: qui usiamo dot-product vettorializzato
        broad_scores = []
        for i, v in enumerate(nodes_vectors):
            v_l3 = self.slice_vector(v, level=0)
            broad_scores.append((i, np.dot(q_l3, v_l3)))
            
        # Prendi i top 50 per il raffinamento
        top_broad = sorted(broad_scores, key=lambda x: x[1], reverse=True)[:50]
        
        # Step 2: Refining (L1 - 3072 dims)
        refined_scores = []
        q_l1 = query # full dim
        for idx, _ in top_broad:
            v_l1 = nodes_vectors[idx]
            refined_scores.append((idx, np.dot(q_l1, v_l1)))
            
        return [idx for idx, _ in sorted(refined_scores, key=lambda x: x[1], reverse=True)[:k]]
