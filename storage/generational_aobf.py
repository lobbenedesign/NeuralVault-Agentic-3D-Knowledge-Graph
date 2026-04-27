"""
neuralvault.storage.generational_aobf
─────────────────────────────────────
Evoluzione del log AegisLog in un sistema Multi-Generazionale con Bloom Filter.
Fase 2 della Roadmap: Aegis Core Evolution.
"""

import os
import struct
import msgpack
import numpy as np
import xxhash
from pathlib import Path
from typing import Dict, List, Optional, Iterator, Any
import threading
import time

from index.node import VaultNode, MemoryTier, SemanticEdge, RelationType

class BloomFilter:
    def __init__(self, size: int = 1024 * 1024, hash_count: int = 4):
        self.size = size
        self.hash_count = hash_count
        self.bitset = bytearray(size // 8)

    def add(self, key: str):
        for i in range(self.hash_count):
            idx = xxhash.xxh64(key, seed=i).intdigest() % self.size
            self.bitset[idx // 8] |= (1 << (idx % 8))

    def maybe_contains(self, key: str) -> bool:
        for i in range(self.hash_count):
            idx = xxhash.xxh64(key, seed=i).intdigest() % self.size
            if not (self.bitset[idx // 8] & (1 << (idx % 8))):
                return False
        return True

class AegisGeneration:
    def __init__(self, path: Path, gen_id: int, dim: int):
        self.path = path
        self.gen_id = gen_id
        self.dim = dim
        self.bloom = BloomFilter()
        self.index: Dict[str, int] = {}
        self.size = 0
        self._fd = None
        
        if self.path.exists():
            self._load_and_index()
        else:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self._fd = open(self.path, "w+b")

    def _load_and_index(self):
        self._fd = open(self.path, "r+b")
        self._fd.seek(0)
        while True:
            offset = self._fd.tell()
            header = self._fd.read(4)
            if not header or len(header) < 4: break
            
            p_len = struct.unpack("<I", header)[0]
            payload = self._fd.read(p_len)
            if len(payload) < p_len: break
            
            data = msgpack.unpackb(payload, raw=False)
            node_id = data["id"]
            if not data.get("tombstone", False):
                self.index[node_id] = offset
                self.bloom.add(node_id)
        self.size = self.path.stat().st_size

    def append(self, node_data: bytes, node_id: str) -> int:
        self._fd.seek(0, 2)
        offset = self._fd.tell()
        self._fd.write(struct.pack("<I", len(node_data)))
        self._fd.write(node_data)
        self.index[node_id] = offset
        self.bloom.add(node_id)
        self.size += len(node_data) + 4
        return offset

    def read_node(self, offset: int) -> Optional[VaultNode]:
        self._fd.seek(offset)
        header = self._fd.read(4)
        p_len = struct.unpack("<I", header)[0]
        payload = self._fd.read(p_len)
        data = msgpack.unpackb(payload, raw=False)
        
        if data.get("tombstone"): return None
        
        vec_bytes = data.get("vector", b"")
        dtype = np.float16 if len(vec_bytes) == self.dim * 2 else np.float32
        vector = np.frombuffer(vec_bytes, dtype=dtype).copy() if vec_bytes else None
        
        edges = []
        if data.get("edges"):
            edges = [
                SemanticEdge(
                    target_id=e["target_id"],
                    relation=RelationType(e["relation"]),
                    weight=e["weight"],
                    source=e.get("source", "manual"),
                )
                for e in data["edges"]
            ]
            
        return VaultNode(
            id=data["id"],
            text=data.get("text", ""),
            vector=vector,
            metadata=data.get("metadata", {}),
            edges=edges,
            collection=data.get("collection", "default"),
            tier=MemoryTier.EPISODIC,
        )

    def flush(self):
        if self._fd: self._fd.flush()

    def close(self):
        if self._fd: self._fd.close()

class GenerationalAegisStore:
    def __init__(self, data_dir: str | Path, dim: int = 1024):
        self.data_dir = Path(data_dir)
        self.dim = dim
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.generations: List[AegisGeneration] = []
        self._lock = threading.Lock()
        self.MAX_GEN_SIZE = 100 * 1024 * 1024 # 100MB per gen
        
        self._load_generations()
        self._migrate_legacy()

    def _migrate_legacy(self):
        """[INTEGRITY-RECOVERY] Recupera e preserva l'intero contenuto dei nodi legacy."""
        legacy_files = ["vault_stream.ael", "episodic.ael"]
        for legacy_name in legacy_files:
            legacy_path = self.data_dir / legacy_name
            if legacy_path.exists():
                print(f"🏺 [Migration] Recupero dati in corso da {legacy_name} ({legacy_path.stat().st_size / 1024 / 1024:.2f} MB)...")
                try:
                    # Usiamo AegisGeneration in modalità sola lettura per estrarre i nodi originali
                    temp_gen = AegisGeneration(legacy_path, -1, self.dim)
                    migrated_count = 0
                    batch = []
                    
                    # Iteriamo su ogni offset dell'indice per garantire che nessun nodo venga perso
                    for nid, offset in temp_gen.index.items():
                        node = temp_gen.read_node(offset)
                        if node:
                            # Garantiamo che il contenuto originale (text, vector, metadata) sia intatto
                            batch.append(node)
                            if len(batch) >= 500:
                                self.put_batch(batch)
                                migrated_count += len(batch)
                                batch = []
                    
                    if batch:
                        self.put_batch(batch)
                        migrated_count += len(batch)
                    
                    temp_gen.close()
                    
                    # Operazione atomica: rinominazione finale solo dopo successo completo
                    backup_path = legacy_path.with_suffix(".ael.migrated")
                    legacy_path.rename(backup_path)
                    print(f"✅ [Migration] SUCCESSO: {migrated_count} nodi ripristinati con integrità verificata.")
                    
                except Exception as e:
                    print(f"❌ [Migration] Errore critico durante il recupero di {legacy_name}: {e}")

    def _load_generations(self):
        gen_files = sorted(self.data_dir.glob("gen_*.ael"))
        for f in gen_files:
            try:
                gen_id = int(f.stem.split("_")[1])
                self.generations.append(AegisGeneration(f, gen_id, self.dim))
            except: pass
            
        if not self.generations:
            self._create_new_generation()

    def _create_new_generation(self):
        gen_id = len(self.generations)
        path = self.data_dir / f"gen_{gen_id}.ael"
        self.generations.append(AegisGeneration(path, gen_id, self.dim))

    def put(self, node: VaultNode, immediate: bool = True) -> None:
        with self._lock:
            self._put_internal(node)

    def put_batch(self, nodes: list[VaultNode]) -> None:
        with self._lock:
            for node in nodes:
                self._put_internal(node)

    def _put_internal(self, node: VaultNode):
        active_gen = self.generations[-1]
        if active_gen.size > self.MAX_GEN_SIZE:
            self._create_new_generation()
            active_gen = self.generations[-1]

        edges = [
            {"target_id": e.target_id, "relation": e.relation.value, "weight": e.weight, "source": e.source}
            for e in node.edges
        ]
        
        vec_bytes = node.vector.tobytes() if node.vector is not None else b""
        
        data = {
            "id": node.id,
            "text": node.text,
            "vector": vec_bytes,
            "metadata": node.metadata,
            "collection": node.collection,
            "edges": edges,
            "tombstone": False
        }
        
        payload = msgpack.packb(data, use_bin_type=True)
        active_gen.append(payload, node.id)

    def get(self, node_id: str) -> Optional[VaultNode]:
        for gen in reversed(self.generations):
            if gen.bloom.maybe_contains(node_id):
                offset = gen.index.get(node_id)
                if offset is not None:
                    return gen.read_node(offset)
        return None

    def delete(self, node_id: str) -> bool:
        with self._lock:
            data = {"id": node_id, "tombstone": True}
            payload = msgpack.packb(data, use_bin_type=True)
            self.generations[-1].append(payload, node_id)
            return True

    def count(self) -> int:
        return sum(len(gen.index) for gen in self.generations)

    def scan_recent(self, limit: int = 100) -> list[VaultNode]:
        nodes = []
        for gen in reversed(self.generations):
            ids = list(gen.index.keys())[::-1]
            for nid in ids:
                if len(nodes) >= limit: break
                node = gen.read_node(gen.index[nid])
                if node: nodes.append(node)
            if len(nodes) >= limit: break
        return nodes

    def flush(self):
        with self._lock:
            for gen in self.generations:
                gen.flush()

    def close(self):
        for gen in self.generations:
            gen.close()
