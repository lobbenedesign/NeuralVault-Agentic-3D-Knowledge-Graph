"""
neuralvault.core.node
─────────────────────
Unità fondamentale del sistema. v0.2.5 con Versioning (Fase 14).
"""

from __future__ import annotations
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any
import numpy as np


class MemoryTier(str, Enum):
    WORKING  = "working"
    EPISODIC = "episodic"
    SEMANTIC = "semantic"


class RelationType(str, Enum):
    CITES        = "cites"
    CONTRADICTS  = "contradicts"
    UPDATES      = "updates"
    PREREQUISITE = "prerequisite"
    EXAMPLE_OF   = "example_of"
    SAME_ENTITY  = "same_entity"
    SEQUENTIAL   = "sequential"
    SYNAPSE      = "synapse"
    SIMILARITY   = "similarity"
    EQUIVALENT   = "equivalent"
    PARENT       = "parent"
    CHILD        = "child"
    QUANTUM_LINK = "quantum_link"


@dataclass
class SemanticEdge:
    target_id:        str
    relation:         RelationType
    weight:           float = 1.0
    logic_weight:     float = 1.0  # [v3.0]: Ponderazione logica (Rilevanza per il task)
    emotional_weight: float = 0.5  # [v3.0]: Carica 'emotiva' o urgenza del dato
    bidirectional:    bool  = False
    created_at:       float = field(default_factory=time.time)
    source:           str   = "manual"
    reason:           Optional[str] = None # [Phase 3]: Perché questi nodi sono collegati?

    def __post_init__(self):
        if not 0.0 <= self.weight <= 1.0:
            raise ValueError(f"Edge weight must be in [0, 1], got {self.weight}")
        if isinstance(self.relation, str):
            self.relation = RelationType(self.relation)


@dataclass
class VaultNode:
    # ── Identificazione ──────────────────────────────────────
    id:             str
    collection:     str   = "default"
    namespace:      str   = "default"
    version:        int   = 1           # Fase 14: Cache Versioning

    # ── Contenuto ────────────────────────────────────────────
    text:           str   = ""
    vector:         np.ndarray | None = None
    sparse_vector:  dict[int, float] | None = None

    # ── Metadati utente ──────────────────────────────────────
    metadata:       dict[str, Any] = field(default_factory=dict)

    # ── Context graph ────────────────────────────────────────
    edges:          list[SemanticEdge] = field(default_factory=list)

    # ── Memory management ────────────────────────────────────
    tier:                  MemoryTier = MemoryTier.SEMANTIC
    access_count:          int        = 0
    last_accessed:         float      = field(default_factory=time.time)
    created_at:            float      = field(default_factory=time.time)
    agent_relevance_score: float      = 0.0

    def __post_init__(self):
        if self.vector is not None and not isinstance(self.vector, np.ndarray):
            # Se siamo in float16 mode, convertiamo subito
            self.vector = np.array(self.vector, dtype=self.vector.dtype if hasattr(self.vector, 'dtype') else np.float32)
        
        if self.vector is not None:
            # Assicuriamoci che la normalizzazione avvenga con precisione sufficiente
            # anche se il vettore è float16
            norm = np.linalg.norm(self.vector.astype(np.float32))
            if norm > 0:
                self.vector = self.vector / norm.astype(self.vector.dtype)

    def bump_version(self) -> None:
        """Incrementa la versione del nodo dopo un aggiornamento."""
        self.version += 1
        self.last_accessed = time.time()

    def touch(self) -> None:
        self.access_count += 1
        self.last_accessed = time.time()

    def add_edge(self, target_id: str, relation: RelationType | str, weight: float = 1.0, source: str = "manual") -> SemanticEdge:
        if isinstance(relation, str):
            relation = RelationType(relation)
        edge = SemanticEdge(target_id=target_id, relation=relation, weight=weight, source=source)
        existing = {(e.target_id, e.relation) for e in self.edges}
        if (target_id, relation) not in existing:
            self.edges.append(edge)
        return edge

    def to_dict(self) -> dict:
        return {
            "id":                    self.id,
            "collection":            self.collection,
            "namespace":             self.namespace,
            "version":               self.version,
            "text":                  self.text,
            "vector":                self.vector.tolist() if self.vector is not None else None,
            "metadata":              self.metadata,
            "edges":                 [
                {
                    "target_id":     e.target_id,
                    "relation":      e.relation.value,
                    "weight":        e.weight,
                    "logic_weight":  e.logic_weight,
                    "emotional_weight": e.emotional_weight,
                    "bidirectional": e.bidirectional,
                    "created_at":    e.created_at,
                    "source":        e.source,
                }
                for e in self.edges
            ],
            "tier":                  self.tier.value,
            "access_count":          self.access_count,
            "last_accessed":         self.last_accessed,
            "created_at":            self.created_at,
            "agent_relevance_score": self.agent_relevance_score,
        }

    @classmethod
    def from_dict(cls, data: dict, vector: np.ndarray | None = None,
                  sparse_vector: dict | None = None) -> "VaultNode":
        edges = [
            SemanticEdge(
                target_id=e["target_id"],
                relation=RelationType(e["relation"]),
                weight=e["weight"],
                logic_weight=e.get("logic_weight", 1.0),
                emotional_weight=e.get("emotional_weight", 0.5),
                bidirectional=e.get("bidirectional", False),
                created_at=e.get("created_at", time.time()),
                source=e.get("source", "manual"),
            )
            for e in data.get("edges", [])
        ]
        node = cls(
            id=data["id"],
            collection=data.get("collection", "default"),
            namespace=data.get("namespace", "default"),
            version=data.get("version", 1),
            text=data.get("text", ""),
            vector=vector,
            sparse_vector=sparse_vector,
            metadata=data.get("metadata", {}),
            edges=[
                SemanticEdge(
                    target_id=e["target_id"],
                    relation=RelationType(e["relation"]),
                    weight=e["weight"],
                    logic_weight=e.get("logic_weight", 1.0),
                    emotional_weight=e.get("emotional_weight", 0.5),
                    bidirectional=e.get("bidirectional", False),
                    created_at=e.get("created_at", time.time()),
                    source=e.get("source", "manual"),
                )
                for e in data.get("edges", [])
            ],
            tier=MemoryTier(data.get("tier", "semantic")),
            access_count=data.get("access_count", 0),
            last_accessed=data.get("last_accessed", time.time()),
            created_at=data.get("created_at", time.time()),
            agent_relevance_score=data.get("agent_relevance_score", 0.0),
        )
        if vector is not None:
            node.vector = vector
        elif "vector" in data and data["vector"] is not None:
            node.vector = np.array(data["vector"], dtype=np.float32)

        return node


    @staticmethod
    def generate_id() -> str:
        return str(uuid.uuid4())


@dataclass
class QueryResult:
    node:         VaultNode
    dense_score:  float = 0.0
    sparse_score: float = 0.0
    graph_score:  float = 0.0
    rerank_score: float = 0.0
    cognitive_score: float = 0.0
    memory_strength: float = 1.0
    final_score:  float = 0.0
    path:         str   = "direct"

    def __lt__(self, other: "QueryResult") -> bool:
        return self.final_score > other.final_score
