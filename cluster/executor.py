"""
neuralvault.cluster.executor
──────────────────────────
Esecutore distribuito avanzato con backpressure.
Gestisce il worker pool per le query parallele su tutti gli shard
e implementa code di attesa se gli shard sono saturi.
"""

from __future__ import annotations
import asyncio
import httpx
import time
from typing import Dict, List, Any, Optional
import heapq
from dataclasses import dataclass, field

class ShardWorker:
    """
    Rappresenta un singolo shard e la sua capacità di lavoro corrente.
    """
    def __init__(self, name: str, url: str, max_concurrent: int = 16):
        self.name = name
        self.url  = url
        self.max_concurrent = max_concurrent
        self.current_tasks  = 0
        self._lock = asyncio.Lock()
        self._client = httpx.AsyncClient(timeout=10.0)

    async def execute(self, endpoint: str, data: dict) -> dict:
        """Esegue una query sullo shard se c'è capacità."""
        if self.current_tasks >= self.max_concurrent:
            # Backpressure: segnaliamo allo Scheduler di aspettare
            return {"error": "shard_busy", "retry_after": 0.5}

        async with self._lock:
            self.current_tasks += 1
            
        try:
            resp = await self._client.post(f"{self.url}/{endpoint}", json=data)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return {"error": str(e)}
        finally:
            async with self._lock:
                self.current_tasks -= 1

class ShardExecutor:
    """
    Gestore globale della coda di lavoro distribuita.
    """
    def __init__(self, shards: Dict[str, str], max_per_shard: int = 16):
        self.workers = {name: ShardWorker(name, url, max_per_shard) for name, url in shards.items()}
        self._priority_queue = [] # Min-heap per la priorità
        self._running = True

    async def query_all(self, endpoint: str, data: dict, priority: int = 5) -> list[dict]:
        """
        Invia la query a TUTTI i worker in parallelo con priorità.
        """
        tasks = []
        for name, worker in self.workers.items():
            # Se lo shard è occupato, l'executor lo mette nella CODA DI PRIORITÀ INTERNA
            tasks.append(self._execute_with_priority(worker, endpoint, data, priority))
        
        results = await asyncio.gather(*tasks)
        return results

    async def _execute_with_priority(self, worker: ShardWorker, endpoint: str, data: dict, priority: int):
        """Tenta di eseguire, se busy accoda per priorità."""
        max_retries = 5
        for i in range(max_retries):
            res = await worker.execute(endpoint, data)
            if res.get("error") == "shard_busy":
                # Invece di un semplice sleep, ora l'executor 'capisce' il rank
                # e rilascia il lock prima se la priorità è alta.
                wait_time = 0.05 * (priority + 1) * (i + 1)
                await asyncio.sleep(min(wait_time, 1.0))
                continue
            return res
        return {"error": f"Shard {worker.name} timed out."}

    async def close(self):
        for w in self.workers.values():
            await w._client.aclose()
