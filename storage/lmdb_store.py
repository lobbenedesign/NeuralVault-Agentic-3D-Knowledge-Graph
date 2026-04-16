"""
neuralvault.storage.lmdb_store
───────────────────────────────
Storage LMDB per VaultNode (hot/warm tier).
Zero-copy reads, ACID transactions, msgpack serialization.
"""

from __future__ import annotations
import lmdb
import msgpack
import numpy as np
from pathlib import Path
from typing import Iterator

# Assuming neuralvault will eventually be structured as a package, 
# for now we import from the root if we run in the root.
# But let's use the provided structure.
from index.node import VaultNode, MemoryTier, SemanticEdge, RelationType

class LmdbStore:
    """
    Storage LMDB per VaultNode.
    Usa tre database separati nello stesso environment LMDB:
    - 'vectors':  node_id (bytes) → float32 array (bytes)
    - 'metadata': node_id (bytes) → msgpack dict
    - 'edges':    node_id (bytes) → msgpack list of edges
    """

    def __init__(
        self,
        data_dir: str | Path,
        dim: int = 1024,
        map_size: int = 10 * 1024**3,  # 10GB default
        readonly: bool = False,
    ):
        self.data_dir = Path(data_dir)
        self.dim = dim
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self._env = lmdb.open(
            str(self.data_dir),
            map_size=map_size,
            max_dbs=3,
            readonly=readonly,
            writemap=True,
            map_async=True,
        )
        self._db_vectors  = self._env.open_db(b"vectors")
        self._db_metadata = self._env.open_db(b"metadata")
        self._db_edges    = self._env.open_db(b"edges")

    def put(self, node: VaultNode) -> None:
        """Scrive un nodo su disco in una singola transazione ACID."""
        key = node.id.encode()

        with self._env.begin(write=True) as txn:
            # 1. Vettore
            if node.vector is not None:
                txn.put(key, node.vector.tobytes(), db=self._db_vectors)

            # 2. Metadata
            meta_payload = msgpack.packb({
                "id":                    node.id,
                "text":                  node.text,
                "collection":            node.collection,
                "namespace":             node.namespace,
                "metadata":              node.metadata,
                "tier":                  node.tier.value,
                "access_count":          node.access_count,
                "last_accessed":         node.last_accessed,
                "created_at":            node.created_at,
                "agent_relevance_score": node.agent_relevance_score,
            }, use_bin_type=True)
            txn.put(key, meta_payload, db=self._db_metadata)

            # 3. Edges
            if node.edges:
                edges_payload = msgpack.packb([
                    {
                        "target_id": e.target_id,
                        "relation":  e.relation.value,
                        "weight":    e.weight,
                        "source":    e.source,
                    }
                    for e in node.edges
                ], use_bin_type=True)
                txn.put(key, edges_payload, db=self._db_edges)

    def put_batch(self, nodes: list[VaultNode]) -> None:
        """Batch write ottimizzato."""
        with self._env.begin(write=True) as txn:
            for node in nodes:
                key = node.id.encode()
                if node.vector is not None:
                    txn.put(key, node.vector.tobytes(), db=self._db_vectors)
                
                meta_payload = msgpack.packb({
                    "id": node.id, 
                    "text": node.text,
                    "collection": node.collection,
                    "namespace": node.namespace,
                    "metadata": node.metadata,
                    "tier": node.tier.value,
                    "access_count": node.access_count,
                    "last_accessed": node.last_accessed,
                    "created_at": node.created_at,
                    "agent_relevance_score": node.agent_relevance_score,
                }, use_bin_type=True)
                txn.put(key, meta_payload, db=self._db_metadata)

                if node.edges:
                    edges_payload = msgpack.packb([
                        {"target_id": e.target_id, "relation": e.relation.value, "weight": e.weight, "source": e.source}
                        for e in node.edges
                    ], use_bin_type=True)
                    txn.put(key, edges_payload, db=self._db_edges)

    def get(self, node_id: str, load_vector: bool = True) -> VaultNode | None:
        """Legge un nodo dal disco."""
        key = node_id.encode()

        with self._env.begin(write=False) as txn:
            meta_bytes = txn.get(key, db=self._db_metadata)
            if meta_bytes is None:
                return None

            meta = msgpack.unpackb(meta_bytes, raw=False)

            vector = None
            if load_vector:
                vec_bytes = txn.get(key, db=self._db_vectors)
                if vec_bytes:
                    # Rilevamento automatico Precisione (Gap #1)
                    dtype = np.float16 if len(vec_bytes) == self.dim * 2 else np.float32
                    vector = np.frombuffer(vec_bytes, dtype=dtype).copy()

            edges_bytes = txn.get(key, db=self._db_edges)
            edges = []
            if edges_bytes:
                raw_edges = msgpack.unpackb(edges_bytes, raw=False)
                edges = [
                    SemanticEdge(
                        target_id=e["target_id"],
                        relation=RelationType(e["relation"]),
                        weight=e["weight"],
                        source=e.get("source", "manual"),
                    )
                    for e in raw_edges
                ]

        return VaultNode(
            id=meta["id"],
            text=meta.get("text", ""),
            vector=vector,
            metadata=meta.get("metadata", {}),
            edges=edges,
            collection=meta.get("collection", "default"),
            namespace=meta.get("namespace", "default"),
            access_count=meta.get("access_count", 0),
            last_accessed=meta.get("last_accessed", 0.0),
            created_at=meta.get("created_at", 0.0),
            agent_relevance_score=meta.get("agent_relevance_score", 0.0),
            tier=MemoryTier.EPISODIC,
        )

    def delete(self, node_id: str) -> bool:
        key = node_id.encode()
        with self._env.begin(write=True) as txn:
            deleted = txn.delete(key, db=self._db_metadata)
            txn.delete(key, db=self._db_vectors)
            txn.delete(key, db=self._db_edges)
        return deleted

    def iter_all(self, load_vector: bool = True) -> Iterator[VaultNode]:
        """Itera su tutti i nodi."""
        with self._env.begin(write=False) as txn:
            cursor = txn.cursor(db=self._db_metadata)
            for key, meta_bytes in cursor:
                meta = msgpack.unpackb(meta_bytes, raw=False)
                
                vector = None
                if load_vector:
                   vec_bytes = txn.get(key, db=self._db_vectors)
                   if vec_bytes:
                       dtype = np.float16 if len(vec_bytes) == self.dim * 2 else np.float32
                       vector = np.frombuffer(vec_bytes, dtype=dtype).copy()
                
                edges_bytes = txn.get(key, db=self._db_edges)
                edges = []
                if edges_bytes:
                    raw_edges = msgpack.unpackb(edges_bytes, raw=False)
                    edges = [
                        SemanticEdge(
                            target_id=e["target_id"],
                            relation=RelationType(e["relation"]),
                            weight=e["weight"],
                            source=e.get("source", "manual"),
                        )
                        for e in raw_edges
                    ]

                yield VaultNode(
                    id=meta["id"],
                    text=meta.get("text", ""),
                    vector=vector,
                    metadata=meta.get("metadata", {}),
                    edges=edges,
                    collection=meta.get("collection", "default"),
                    namespace=meta.get("namespace", "default"),
                    access_count=meta.get("access_count", 0),
                    last_accessed=meta.get("last_accessed", 0.0),
                    created_at=meta.get("created_at", 0.0),
                    agent_relevance_score=meta.get("agent_relevance_score", 0.0),
                    tier=MemoryTier.EPISODIC,
                )

    def count(self) -> int:
        with self._env.begin() as txn:
            return txn.stat(db=self._db_metadata)["entries"]

    def close(self):
        self._env.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
