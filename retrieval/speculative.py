"""
neuralvault.retrieval.speculative
───────────────────────────────
Esecutore speculativo.
Monitora le query e pre-carica i chunk previsti mentre l'HNSW è ancora in ricerca.
"""

from __future__ import annotations
import asyncio
from typing import List, Callable, Any
from index.node import VaultNode

class SpeculativePreloader:
    """
    Anticipa i bisogni dell'agente basandosi sulla storia recente delle query.
    """
    def __init__(self, storage_get_fn: Callable[[str], VaultNode | None]):
        self.storage_get = storage_get_fn
        # Mappa (query_prefix_hash -> list of predicted node_ids)
        self._pattern_cache: dict[int, list[str]] = {}
        self._prefetch_buffer: dict[str, VaultNode] = {}
        self._lock = asyncio.Lock()

    def record_access(self, query: str, node_id: str):
        """Traccia quale nodo è stato scelto per una data query (training locale)."""
        key = hash(query[:20]) # Basato sui primi 20 caratteri per velocità
        if key not in self._pattern_cache:
            self._pattern_cache[key] = []
        
        if node_id not in self._pattern_cache[key]:
            self._pattern_cache[key].append(node_id)
            if len(self._pattern_cache[key]) > 5:
                self._pattern_cache[key].pop(0)

    async def prefetch(self, query: str):
        """Avvia il prefetch asincrono dei chunk previsti."""
        key = hash(query[:20])
        predicted_ids = self._pattern_cache.get(key, [])
        
        async def _load_task(node_id: str):
            node = self.storage_get(node_id)
            if node:
                async with self._lock:
                    self._prefetch_buffer[node_id] = node

        # Fire and forget preloading
        for node_id in predicted_ids:
            asyncio.create_task(_load_task(node_id))

    async def get_prefetched(self, node_id: str) -> VaultNode | None:
        """Controlla se il nodo è già stato pre-caricato."""
        async with self._lock:
            return self._prefetch_buffer.pop(node_id, None)

    async def clear_buffer(self):
        async with self._lock:
            self._prefetch_buffer.clear()
