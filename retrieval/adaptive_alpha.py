"""
retrieval/adaptive_alpha.py
──────────────────────────
Adaptive Alpha Computer: Bilanciamento dinamico per la Ricerca Ibrida.
Calcola il peso ottimale (α) tra ricerca Vettoriale (HNSW) e Lessicale (BM25)
in base alle caratteristiche della query.
"""

import re
import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

@dataclass
class AlphaMetrics:
    gap_signal: float
    lexical_signal: float
    length_signal: float
    final_alpha: float

class AdaptiveAlphaComputer:
    def __init__(self):
        # Pattern tecnici che indicano una ricerca "esatta" o "codice"
        self.technical_patterns = [
            r'\d{3,}',              # Numeri lunghi (ID, porte, errori)
            r'[A-Z]{2,}_[A-Z]+',   # COSTANTI_MAIUSCOLE
            r'\w+\.\w+\(',          # Chiamate: os.path.join(
            r'[./\\]\w+',           # Percorsi: ./src/api
            r'0x[0-9a-fA-F]+',      # Esadecimali
            r'v\d+\.\d+',           # Versioni: v1.2.0
            r'[A-Z][a-z]+Error',    # Eccezioni: TypeError
            r'--\w+',               # Flag CLI: --verbose
        ]

    def compute(self, query: str, bm25_scores: List[float]) -> AlphaMetrics:
        """
        Calcola α (alpha). 
        α = 1.0 -> Domina HNSW (Semantico)
        α = 0.0 -> Domina BM25 (Esatto/Lessicale)
        """
        # 1. BM25 GAP SIGNAL (Il segnale più forte)
        # Se il primo risultato BM25 stacca nettamente gli altri, è un match esatto.
        gap_signal = self._get_gap_signal(bm25_scores)
        
        # 2. LEXICAL SIGNAL
        # Presenza di pattern tecnici o sintassi codice
        lexical_signal = self._get_lexical_signal(query)
        
        # 3. LENGTH SIGNAL
        # Query corte (1-2 parole) tendono ad essere keyword esatte.
        # Query lunghe tendono ad essere descrittive/semantiche.
        length_signal = self._get_length_signal(query)
        
        # FUSIONE DEI SEGNALI (Media ponderata)
        # BM25 Gap ha il peso maggiore (40%), Lexical (35%), Length (25%)
        raw_alpha = (gap_signal * 0.45) + (lexical_signal * 0.35) + (length_signal * 0.20)
        
        # Clamp in range [0.15, 0.85] per evitare estremismi che ignorano una delle due anime
        final_alpha = max(0.15, min(0.85, raw_alpha))
        
        return AlphaMetrics(
            gap_signal=gap_signal,
            lexical_signal=lexical_signal,
            length_signal=length_signal,
            final_alpha=final_alpha
        )

    def _get_gap_signal(self, scores: List[float]) -> float:
        """Misura la 'sicurezza' del BM25."""
        if not scores or len(scores) < 2 or scores[0] == 0:
            return 0.7 # Default verso semantico se BM25 non trova nulla
        
        top = scores[0]
        mean_others = np.mean(scores[1:min(6, len(scores))])
        
        if mean_others == 0: return 0.2 # Match unico e isolato -> Molto probabile esatto
        
        ratio = top / mean_others
        # Se ratio > 5, BM25 è molto sicuro (alpha basso)
        # Se ratio ~ 1, BM25 è incerto (alpha alto)
        alpha = 0.8 * np.exp(-0.2 * (ratio - 1))
        return float(np.clip(alpha, 0.1, 0.9))

    def _get_lexical_signal(self, query: str) -> float:
        """Rileva se la query 'sembra' codice o un termine tecnico."""
        matches = sum(1 for p in self.technical_patterns if re.search(p, query))
        
        if matches == 0: return 0.85 # Molto semantico
        if matches == 1: return 0.40 # Bilanciato
        return 0.20 # Molto tecnico/lessicale

    def _get_length_signal(self, query: str) -> float:
        """Pesa la lunghezza della query."""
        words = query.strip().split()
        count = len(words)
        
        if count <= 2: return 0.30 # Corta -> Probabile keyword
        if count <= 5: return 0.60 # Media
        return 0.85 # Lunga -> Descrittiva
