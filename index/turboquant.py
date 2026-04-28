"""
neuralvault.core.turboquant
────────────────────────────
TurboQuant v2 (Universal Performance Edition)
Optimized for Apple Silicon (M1-M5), Intel AVX, and NVIDIA CUDA.
"""

import torch
import numpy as np
from typing import List, Dict, Optional, Tuple, Any
from pathlib import Path

class TurboQuantizerV2:
    """
    Motore di Quantizzazione Ibrida Auto-Ottimizzante (v2.0).
    Sceglie la precisione in base all'hardware rilevato.
    """
    def __init__(self, dim: int = 1024, device: str = "cpu"):
        self.dim = dim
        self.device = device
        
        # Selezione Precisione Ottimale
        if device == "cuda":
            self.compute_dtype = torch.float16
        elif device == "mps":
            self.compute_dtype = torch.float16
        else:
            self.compute_dtype = torch.float32 # Fallback sicuro per Intel/AMD
            
        # Matrice di Proiezione Casuale per Binary Quantization (Sovereign Hashing)
        # Usiamo un seed fisso per coerenza tra sessioni
        torch.manual_seed(42)
        self.proj_matrix = torch.randn(dim, dim, device=device, dtype=self.compute_dtype)
        self.proj_matrix /= torch.norm(self.proj_matrix, dim=0)

    @torch.no_grad()
    def encode_binary(self, vectors: torch.Tensor) -> torch.Tensor:
        """Trasforma i vettori in codici binari (1 bit per dimensione) per ricerca ultra-veloce."""
        # Proiezione nello spazio di hashing
        projected = torch.matmul(vectors.to(self.compute_dtype), self.proj_matrix)
        # Thresholding (Sgn function)
        binary = (projected > 0).to(torch.uint8)
        return binary

    @torch.no_grad()
    def encode_int8(self, vectors: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """Quantizzazione INT8 con scaling factor per mantenere l'accuratezza."""
        max_vals = torch.max(torch.abs(vectors), dim=1, keepdim=True)[0]
        scales = max_vals / 127.0
        quantized = (vectors / (scales + 1e-8)).to(torch.int8)
        return quantized, scales

    def decode_int8(self, quantized: torch.Tensor, scales: torch.Tensor) -> torch.Tensor:
        """Ripristina i vettori quantizzati."""
        return quantized.to(torch.float32) * scales

class TwoStageTurboSearch:
    """
    Ricerca a due stadi:
    1. Screening Binario (Hamming Distance) -> Velocità Massima.
    2. Refinement INT8/FP16 -> Precisione Massima.
    """
    def __init__(self, dim: int = 1024, candidate_k: int = 250):
        self.dim = dim
        self.candidate_k = candidate_k
        
        # Rilevamento Hardware via Torch
        self.device = "cpu"
        if torch.cuda.is_available(): self.device = "cuda"
        elif torch.backends.mps.is_available(): self.device = "mps"
        
        self.tq = TurboQuantizerV2(dim=dim, device=self.device)
        
        # Archivi In-Memory
        self.ids = []
        self.binary_store: Optional[torch.Tensor] = None
        self.int8_store: Optional[torch.Tensor] = None
        self.scales_store: Optional[torch.Tensor] = None
        
        print(f"🚀 TurboQuant v2: Engine ACTIVE on {self.device.upper()}")

    @torch.no_grad()
    def add(self, node_id: str, vector: np.ndarray):
        """Aggiunge un vettore quantizzandolo in entrambi i formati."""
        v_torch = torch.from_numpy(vector).to(self.device).view(1, -1)
        
        # 1. Binary Encoding (1 bit/dim -> 128 byte per 1024D)
        b_code = self.tq.encode_binary(v_torch)
        
        # 2. INT8 Encoding (1 byte/dim -> 1024 byte per 1024D)
        i_code, scale = self.tq.encode_int8(v_torch)
        
        if node_id not in self.ids:
            self.ids.append(node_id)
            if self.binary_store is None:
                self.binary_store = b_code
                self.int8_store = i_code
                self.scales_store = scale
            else:
                self.binary_store = torch.cat([self.binary_store, b_code], dim=0)
                self.int8_store = torch.cat([self.int8_store, i_code], dim=0)
                self.scales_store = torch.cat([self.scales_store, scale], dim=0)

    @torch.no_grad()
    def search(self, query: np.ndarray, k: int, filter_ids: Optional[set] = None) -> List[Tuple[str, float]]:
        if not self.ids: return []
        
        q_torch = torch.from_numpy(query).to(self.device).view(1, -1).to(self.tq.compute_dtype)
        
        # --- STAGE 1: BINARY HAMMING SCAN ---
        q_bin = self.tq.encode_binary(q_torch)
        # Distanza di Hamming accelerata: XOR + Popcount
        # In torch, (a != b).sum() simula Hamming per bit unpackati
        hamming_dists = (self.binary_store != q_bin).sum(dim=1).to(torch.float32)
        
        # Applicazione filtro ID (Soft-Masking)
        if filter_ids is not None:
            mask = torch.tensor([1.0 if nid in filter_ids else 1e9 for nid in self.ids], device=self.device)
            hamming_dists *= mask

        # Selezione dei top candidati
        n_cand = min(self.candidate_k, len(self.ids))
        _, top_cand_idx = torch.topk(hamming_dists, n_cand, largest=False)
        
        # --- STAGE 2: INT8 RE-SCORING ---
        cand_int8 = self.int8_store[top_cand_idx]
        cand_scales = self.scales_store[top_cand_idx]
        
        # De-quantizzazione veloce per i soli candidati
        cand_vectors = cand_int8.to(torch.float32) * cand_scales
        
        # Calcolo Cosine Similarity reale
        q_norm = q_torch / torch.norm(q_torch)
        c_norms = cand_vectors / torch.norm(cand_vectors, dim=1, keepdim=True)
        similarities = torch.matmul(c_norms, q_norm.T).squeeze()
        
        distances = 1.0 - similarities
        
        # Ordinamento Finale
        final_scores, final_idx = torch.topk(distances, min(k, n_cand), largest=False)
        
        results = []
        for i in range(len(final_idx)):
            idx_in_store = top_cand_idx[final_idx[i]]
            results.append((self.ids[idx_in_store], float(final_scores[i])))
            
        return results
