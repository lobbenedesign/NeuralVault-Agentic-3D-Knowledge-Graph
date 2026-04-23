"""
neuralvault.core.sparse
───────────────────────
BM25S sparse encoder — implementazione vettorializzata di BM25 che produce
vettori sparsi compatibili con il dot product per hybrid search.

BM25 (Best Match 25) è l'algoritmo di ranking di Information Retrieval più
usato. La versione S (Sparse) codifica ogni documento come un dizionario
{token_id: score} che può essere moltiplicato efficientemente con la query.

Parametri BM25:
- k1 = 1.5: controlla la saturazione della term frequency.
             Valori alti = più peso a TF alta. Range tipico: 1.2–2.0
- b = 0.75:  controlla la normalizzazione per lunghezza documento.
             b=0 = no normalizzazione, b=1 = normalizzazione completa.
             Range tipico: 0.5–0.9
"""

from __future__ import annotations

import math
import re
from collections import Counter, defaultdict
from typing import Iterable


# ─────────────────────────────────────────────
# Tokenizer
# ─────────────────────────────────────────────

def simple_tokenize(text: str) -> list[str]:
    """
    Tokenizer minimalista: lowercase + split su non-alfanumerici.
    Rimuove token corti (< 2 char) e stopwords italiane/inglesi comuni.
    Per produzione, sostituire con un tokenizer dedicato (es. spaCy).
    """
    STOPWORDS = {
        "il", "lo", "la", "i", "gli", "le", "un", "una", "uno",
        "di", "a", "da", "in", "con", "su", "per", "tra", "fra",
        "e", "o", "ma", "se", "che", "non", "si", "è", "ha", "ho",
        "the", "a", "an", "in", "on", "at", "to", "for", "of", "and",
        "or", "but", "not", "is", "are", "was", "were", "be", "been",
    }
    tokens = re.findall(r'\b\w+\b', (text or "").lower())
    return [t for t in tokens if len(t) >= 2 and t not in STOPWORDS]


# ─────────────────────────────────────────────
# BM25S Encoder
# ─────────────────────────────────────────────

class BM25SEncoder:
    """
    Encoder BM25S per creare vettori sparsi da testo.

    Flusso:
    1. fit(corpus): calcola IDF su tutti i documenti
    2. encode_document(text): produce vettore sparso per indicizzazione
    3. encode_query(text): produce vettore sparso per ricerca
    4. score(query_vec, doc_vec): dot product per lo score

    Il vocabolario è costruito incrementalmente: nuovi token vengono aggiunti
    quando si codifica nuovo testo, ma gli IDF vengono aggiornati solo quando
    si chiama recompute_idf() (operazione più costosa).
    """

    def __init__(
        self,
        k1:          float = 1.5,
        b:           float = 0.75,
        tokenize_fn  = simple_tokenize,
    ):
        self.k1          = k1
        self.b           = b
        self.tokenize_fn = tokenize_fn

        # Vocabolario: token → intero ID
        self._vocab:        dict[str, int]  = {}
        self._vocab_rev:    dict[int, str]  = {}
        self._next_id:      int             = 0

        # Statistiche per IDF
        self._doc_count:    int             = 0
        self._df:           dict[int, int]  = defaultdict(int)  # token_id → doc frequency
        self._avg_doc_len:  float           = 0.0
        self._doc_lengths:  list[float]     = []

        # Cache IDF calcolata
        self._idf_cache:    dict[int, float] = {}
        self._idf_dirty:    bool             = True

    def _get_or_add_token(self, token: str) -> int:
        """Ottiene l'ID di un token, creandolo se non esiste."""
        if token not in self._vocab:
            self._vocab[token]           = self._next_id
            self._vocab_rev[self._next_id] = token
            self._next_id += 1
            self._idf_dirty = True
        return self._vocab[token]

    def fit(self, texts: list[str]) -> "BM25SEncoder":
        """
        Calcola statistiche del corpus per IDF.
        Deve essere chiamato prima di encode se si vuole IDF preciso.
        Per un sistema incrementale, usa update_stats() per ogni documento.
        """
        all_lengths = []
        for text in texts:
            tokens = self.tokenize_fn(text)
            doc_len = len(tokens)
            all_lengths.append(doc_len)

            token_ids = [self._get_or_add_token(t) for t in tokens]
            unique_ids = set(token_ids)

            for tid in unique_ids:
                self._df[tid] += 1

            self._doc_count += 1

        if all_lengths:
            self._avg_doc_len = sum(all_lengths) / len(all_lengths)
            self._doc_lengths.extend(all_lengths)

        self._recompute_idf()
        return self

    def update_stats(self, text: str) -> None:
        """
        Aggiorna le statistiche con un nuovo documento (online learning).
        Gli IDF vengono marcati come dirty — chiama recompute_idf() dopo
        un batch di aggiornamenti.
        """
        tokens  = self.tokenize_fn(text)
        doc_len = len(tokens)

        # Aggiorna avg_doc_len con media mobile
        self._doc_count += 1
        self._avg_doc_len = (
            (self._avg_doc_len * (self._doc_count - 1) + doc_len) / self._doc_count
        )
        self._doc_lengths.append(doc_len)

        token_ids = [self._get_or_add_token(t) for t in tokens]
        for tid in set(token_ids):
            self._df[tid] += 1

        self._idf_dirty = True

    def _recompute_idf(self) -> None:
        """Ricalcola gli IDF per tutti i token nel vocabolario."""
        N = max(self._doc_count, 1)
        for tid, df in self._df.items():
            # Formula IDF smooth: log((N - df + 0.5) / (df + 0.5) + 1)
            self._idf_cache[tid] = math.log((N - df + 0.5) / (df + 0.5) + 1)
        self._idf_dirty = False

    def encode_document(self, text: str) -> dict[int, float]:
        """
        Codifica un documento come vettore BM25S sparso.

        Returns:
            {token_id: bm25_score} — solo token con score > 0
        """
        if self._idf_dirty:
            self._recompute_idf()

        tokens  = self.tokenize_fn(text)
        doc_len = len(tokens)
        tf      = Counter(tokens)
        avg_dl  = max(self._avg_doc_len, 1.0)

        sparse = {}
        for token, count in tf.items():
            tid = self._get_or_add_token(token)
            idf = self._idf_cache.get(tid, 0.0)
            if idf <= 0:
                continue

            # Formula BM25: IDF * (TF * (k1 + 1)) / (TF + k1 * (1 - b + b * |D| / avgdl))
            tf_norm = count * (self.k1 + 1) / (
                count + self.k1 * (1 - self.b + self.b * doc_len / avg_dl)
            )
            score = idf * tf_norm
            if score > 0:
                sparse[tid] = score

        return sparse

    def encode_query(self, text: str) -> dict[int, float]:
        """
        Codifica una query come vettore sparso.
        Per le query, usiamo solo IDF (senza normalizzazione BM25 completa)
        perché le query sono molto corte.
        """
        if self._idf_dirty:
            self._recompute_idf()

        tokens = self.tokenize_fn(text)
        tf     = Counter(tokens)
        sparse = {}

        for token, count in tf.items():
            tid = self._vocab.get(token)
            if tid is None:
                continue  # token OOV: ignora (non contribuisce allo score)
            idf = self._idf_cache.get(tid, 0.0)
            if idf > 0:
                sparse[tid] = idf * count  # semplificato per query corte

        return sparse

    @staticmethod
    def dot_product(
        sparse_a: dict[int, float],
        sparse_b: dict[int, float],
    ) -> float:
        """
        Dot product tra due vettori sparsi.
        Itera sul vettore più corto per efficienza.
        O(min(|a|, |b|)) invece di O(vocab_size).
        """
        if len(sparse_a) > len(sparse_b):
            sparse_a, sparse_b = sparse_b, sparse_a
        return sum(v * sparse_b.get(k, 0.0) for k, v in sparse_a.items())

    def batch_search(
        self,
        query_sparse: dict[int, float],
        doc_sparses:  list[tuple[str, dict[int, float]]],
        top_k:        int = 10,
    ) -> list[tuple[str, float]]:
        """
        Ricerca sparsa su una lista di documenti.

        Args:
            query_sparse: vettore query sparso
            doc_sparses: lista di (doc_id, sparse_vector)
            top_k: numero di risultati

        Returns:
            Lista di (doc_id, score) ordinata per score decrescente
        """
        scores = []
        for doc_id, doc_vec in doc_sparses:
            s = self.dot_product(query_sparse, doc_vec)
            if s > 0:
                scores.append((doc_id, s))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]

    def vocab_size(self) -> int:
        return len(self._vocab)

    def get_token(self, token_id: int) -> str | None:
        return self._vocab_rev.get(token_id)
