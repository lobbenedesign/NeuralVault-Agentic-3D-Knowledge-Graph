"""
neuralvault.utils.crdt
────────────────────────
Implementazione di Conflict-free Replicated Data Types (CRDT).
Garantisce la convergenza dei dati senza l'uso di lock globali, 
fondamentale per la Fase 3: Cognitive Overdrive.
"""

import time
from typing import Any, Dict, Generic, TypeVar, Set

T = TypeVar("T")

class LWWRegister(Generic[T]):
    """Last-Write-Wins Register."""
    def __init__(self, value: T, timestamp: float = 0):
        self.value = value
        self.timestamp = timestamp or time.time()

    def merge(self, other: "LWWRegister[T]"):
        if other.timestamp > self.timestamp:
            self.value = other.value
            self.timestamp = other.timestamp

class PNCounter:
    """Positive-Negative Counter."""
    def __init__(self):
        self.p: Dict[str, int] = {} # Incrementi per nodo
        self.n: Dict[str, int] = {} # Decrementi per nodo

    def increment(self, node_id: str, delta: int = 1):
        self.p[node_id] = self.p.get(node_id, 0) + delta

    def decrement(self, node_id: str, delta: int = 1):
        self.n[node_id] = self.n.get(node_id, 0) + delta

    @property
    def value(self) -> int:
        return sum(self.p.values()) - sum(self.n.values())

    def merge(self, other: "PNCounter"):
        for node_id, count in other.p.items():
            self.p[node_id] = max(self.p.get(node_id, 0), count)
        for node_id, count in other.n.items():
            self.n[node_id] = max(self.n.get(node_id, 0), count)

class LWWMap(Generic[T]):
    """Last-Write-Wins Map per metadati e proprietà dei nodi."""
    def __init__(self):
        self._entries: Dict[str, LWWRegister[T]] = {}
        self._removals: Dict[str, float] = {}

    def set(self, key: str, value: T):
        self._entries[key] = LWWRegister(value, time.time())

    def remove(self, key: str):
        self._removals[key] = time.time()

    def get(self, key: str) -> Optional[T]:
        if key in self._removals:
            reg = self._entries.get(key)
            if reg and reg.timestamp > self._removals[key]:
                return reg.value
            return None
        return self._entries[key].value if key in self._entries else None

    def merge(self, other: "LWWMap[T]"):
        for key, other_reg in other._entries.items():
            if key not in self._entries:
                self._entries[key] = other_reg
            else:
                self._entries[key].merge(other_reg)
        
        for key, ts in other._removals.items():
            self._removals[key] = max(self._removals.get(key, 0), ts)

class GSet(Generic[T]):
    """Grow-only Set."""
    def __init__(self):
        self.elements: Set[T] = set()

    def add(self, element: T):
        self.elements.add(element)

    def merge(self, other: "GSet[T]"):
        self.elements.update(other.elements)
