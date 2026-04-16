"""
neuralvault.core.turboquant
────────────────────────────
Implementazione di TurboQuant per NeuralVault.
Fase 15: DABA EMA Feedback Loop.
"""

from __future__ import annotations
import math
from collections import OrderedDict
from dataclasses import dataclass, field
import numpy as np


@dataclass
class TurboQuantRepr:
    final_radius:  float
    angle_indices: list
    qjl_bits:      np.ndarray
    dim:           int
    num_levels:    int

    def nbytes(self) -> int:
        radius_b = 2
        angle_b  = sum(len(a) for a in self.angle_indices)
        qjl_b    = math.ceil(self.dim / 8)
        return radius_b + angle_b + qjl_b

    def compression_ratio(self) -> float:
        return (self.dim * 4) / self.nbytes()


def build_codebook(num_bits: int, level: int) -> np.ndarray:
    n = 1 << num_bits
    if level == 0:
        return np.linspace(0, 2 * np.pi, n + 1)[:-1].astype(np.float32)
    else:
        center = np.pi / 4.0
        sigma  = np.pi / (2.0 * math.sqrt(2 ** level))
        return np.linspace(center - 2.5*sigma, center + 2.5*sigma, n).astype(np.float32)


class TurboQuantizer:
    def __init__(self, dim: int = 1024, bits_main: int = 3, bits_l0: int = 4, seed: int = 42, ema_alpha: float = 0.15):
        assert dim > 0 and (dim & (dim - 1)) == 0
        self.dim        = dim
        self.bits_main  = bits_main
        self.bits_l0    = bits_l0
        self.seed       = seed
        self.ema_alpha  = ema_alpha  # Fase 15: Smoothing
        self.num_levels = int(math.log2(dim))
        
        self.bit_resolutions = np.full(dim, bits_main, dtype=np.uint8)
        self._importance_history = np.zeros(dim, dtype=np.float32)

        rng = np.random.RandomState(seed)
        G   = rng.randn(dim, dim).astype(np.float32)
        Q, R = np.linalg.qr(G)
        self._rotation = Q * np.sign(np.diag(R))

        rng2 = np.random.RandomState(seed + 1)
        S    = rng2.randn(dim, dim).astype(np.float32)
        self._qjl_proj = S / (np.linalg.norm(S, axis=0, keepdims=True) + 1e-8)

        self._daba_codebooks = {
            b: [build_codebook(b, lv) for lv in range(self.num_levels)]
            for b in range(1, 9)
        }
        self._codebooks = self._daba_codebooks[bits_main]

    def encode(self, x: np.ndarray) -> TurboQuantRepr:
        x = x.astype(np.float32)
        norm = float(np.linalg.norm(x))
        if norm < 1e-8:
            return TurboQuantRepr(0.0, [np.zeros(self.dim >> (lv+1), dtype=np.uint8) for lv in range(self.num_levels)], np.ones(self.dim, dtype=np.int8), self.dim, self.num_levels)

        x_unit = x / norm
        y      = self._rotation @ x_unit
        current = y.copy()
        angle_indices = []
        for lv in range(self.num_levels):
            r1, r2 = current[0::2], current[1::2]
            angles = np.arctan2(r2, r1)
            if lv == 0: angles = angles % (2 * np.pi)
            res_avg = int(np.mean(self.bit_resolutions[::(1<<lv)]))
            cb = self._daba_codebooks.get(res_avg, self._codebooks)[lv]
            indices = np.abs(angles[:, None] - cb).argmin(axis=1).astype(np.uint8)
            angle_indices.append(indices)
            current = np.sqrt(r1**2 + r2**2)

        final_r = float(current[0]) if len(current) == 1 else float(np.linalg.norm(current))
        x_recon = self._polar_decode(final_r, angle_indices)
        residual = y - (self._rotation @ x_recon)
        qjl = np.sign(self._qjl_proj.T @ residual).astype(np.int8)
        qjl[qjl == 0] = 1
        return TurboQuantRepr(norm, angle_indices, qjl, self.dim, self.num_levels)

    def update_daba_resolutions(self, weights: np.ndarray, max_avg_bits: float = 3.5):
        """Aggiornamento evolutivo con EMA Feedback (Fase 15)."""
        w = np.clip(weights, 0, 2)
        self._importance_history = (1.0 - self.ema_alpha) * self._importance_history + self.ema_alpha * w
        ideal = 1.0 + (self._importance_history**2 * 4.0)
        c_avg = np.mean(ideal)
        if c_avg > max_avg_bits:
            ideal *= (max_avg_bits / c_avg)
        self.bit_resolutions = np.clip(np.round(ideal), 1, 8).astype(np.uint8)
        print(f"📦 TurboQuant DABA (v0.3.0 EMA): Avg Bits: {np.mean(self.bit_resolutions):.2f}")

    def decode(self, repr_: TurboQuantRepr) -> np.ndarray:
        current = np.array([repr_.final_radius], dtype=np.float32)
        for lv in range(self.num_levels - 1, -1, -1):
            res_avg = int(np.mean(self.bit_resolutions[::(1<<lv)]))
            cb = self._daba_codebooks.get(res_avg, self._codebooks)[lv]
            theta = cb[repr_.angle_indices[lv]]
            r1, r2 = current * np.cos(theta), current * np.sin(theta)
            current = np.empty(len(r1) * 2, dtype=np.float32)
            current[0::2], current[1::2] = r1, r2
        return current @ self._rotation.T

    def _polar_decode(self, final_r: float, angle_indices: list) -> np.ndarray:
        current = np.array([final_r], dtype=np.float32)
        for lv in range(self.num_levels - 1, -1, -1):
            res_avg = int(np.mean(self.bit_resolutions[::(1<<lv)]))
            cb = self._daba_codebooks.get(res_avg, self._codebooks)[lv]
            theta = cb[angle_indices[lv]]
            r1, r2 = current * np.cos(theta), current * np.sin(theta)
            new = np.empty(len(r1) * 2, dtype=np.float32)
            new[0::2], new[1::2] = r1, r2
            current = new
        return self._rotation.T @ current

    def unbiased_dot(self, query: np.ndarray, repr_: TurboQuantRepr, weights: np.ndarray | None = None) -> float:
        x_mse = self.decode(repr_)
        ip_base = float(np.dot(query * weights, x_mse)) if weights is not None else float(np.dot(query, x_mse))
        p_query = self._qjl_proj.T @ query
        correction = float(np.dot(p_query, repr_.qjl_bits)) / self.dim
        return ip_base + correction

    def unbiased_cosine_distance(self, query: np.ndarray, repr_: TurboQuantRepr, weights: np.ndarray | None = None) -> float:
        qn = np.linalg.norm(query)
        if qn < 1e-8: return 1.0
        dot = self.unbiased_dot(query / qn, repr_, weights=weights)
        dot_n = dot / (repr_.final_radius + 1e-8)
        return float(np.clip(1.0 - dot_n, 0.0, 2.0))

    def binary_encode(self, x: np.ndarray) -> np.ndarray:
        xn = x / (np.linalg.norm(x) + 1e-8)
        y = self._rotation @ xn.astype(np.float32)
        return np.packbits((y > 0.0).astype(np.uint8))

    def hamming_batch(self, q_bin: np.ndarray, corpus_bin: np.ndarray) -> np.ndarray:
        xor = q_bin ^ corpus_bin
        return np.unpackbits(xor, axis=1).sum(axis=1).astype(np.float32)


class TwoStageTurboSearch:
    def __init__(self, dim: int = 1024, candidate_k: int = 100, cache_size: int = 1000, use_rust: bool = True):
        self.dim = dim
        self.quantizer = TurboQuantizer(dim=dim)
        self.candidate_k = candidate_k
        self._reprs: dict[str, TurboQuantRepr] = {}
        self._ids: list[str] = []
        self._bin_corpus: np.ndarray | None = None
        self._fp32_cache: OrderedDict[str, np.ndarray] = OrderedDict()
        self.cache_size = cache_size
        self._rust_tq = None
        if use_rust:
            try:
                from neuralvault_rs import RustTurboQuant
                self._rust_tq = RustTurboQuant(dim, self.quantizer.bits_main)
                print("🦀 NeuralVault: Rust TurboQuant backend activated.")
            except ImportError:
                print("🐍 NeuralVault: Rust backend not found, falling back to Python.")

    def add(self, node_id: str, vector: np.ndarray) -> None:
        self._reprs[node_id] = self.quantizer.encode(vector)
        if node_id not in self._ids:
            self._ids.append(node_id)
            b_vec = self.quantizer.binary_encode(vector)
            self._bin_corpus = b_vec[None, :] if self._bin_corpus is None else np.vstack([self._bin_corpus, b_vec])
        self._fp32_cache[node_id] = vector.copy()
        if len(self._fp32_cache) > self.cache_size: self._fp32_cache.popitem(last=False)

    def remove(self, node_id: str) -> None:
        if node_id in self._reprs:
            idx = self._ids.index(node_id)
            self._ids.pop(idx)
            self._bin_corpus = np.delete(self._bin_corpus, idx, axis=0)
            self._reprs.pop(node_id)
            self._fp32_cache.pop(node_id, None)

    def search(self, query: np.ndarray, k: int, filter_ids: set[str] | None = None, domain_weights: np.ndarray | None = None) -> list[tuple[str, float]]:
        if not self._reprs or self._bin_corpus is None: return []
        q_bin = self.quantizer.binary_encode(query)
        h_dists = self.quantizer.hamming_batch(q_bin, self._bin_corpus)
        if filter_ids is not None:
            for i, nid in enumerate(self._ids):
                if nid not in filter_ids: h_dists[i] += 9999.0
        n_cand = min(self.candidate_k, len(self._ids))
        top_idx = np.argpartition(h_dists, n_cand - 1)[:n_cand]
        candidates = [(self._ids[i], h_dists[i]) for i in top_idx]
        if filter_ids is not None: candidates = [c for c in candidates if c[0] in filter_ids]
        q_unit = query / (np.linalg.norm(query) + 1e-8)
        rescored = []
        for cid, _ in candidates:
            if cid in self._fp32_cache and domain_weights is None:
                v = self._fp32_cache[cid]
                d = 1.0 - float(np.dot(q_unit, v / (np.linalg.norm(v) + 1e-8)))
            elif self._rust_tq and domain_weights is None:
                repr_ = self._reprs[cid]
                d = 1.0 - (self._rust_tq.unbiased_dot(query.tolist(), repr_.final_radius, repr_.angle_indices) / (repr_.final_radius + 1e-8))
            else:
                d = self.quantizer.unbiased_cosine_distance(query, self._reprs[cid], weights=domain_weights)
            rescored.append((cid, d))
        rescored.sort(key=lambda x: x[1])
        return rescored[:k]
