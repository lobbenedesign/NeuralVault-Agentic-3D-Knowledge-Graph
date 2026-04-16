"""
neuralvault.storage.aegis_log
───────────────────────────────
Zero-Waste Append-Only Binary Format (AOBF) per VaultNode.
Sostituisce LMDB pre-allocating B-Tree.

Scrive in modo sequenziale (append). L'overhead per vettore è ridotto al minimo, 
e il filesystem alloca solo lo spazio effettivamente utilizzato.
"""

from __future__ import annotations
import os
import struct
import msgpack
import numpy as np
from pathlib import Path
from typing import Iterator

from index.node import VaultNode, MemoryTier, SemanticEdge, RelationType

class AegisLogStore:
    def __init__(self, data_dir: str | Path, dim: int = 1024):
        self.data_dir = Path(data_dir)
        self.dim = dim
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.log_path = self.data_dir / "vault_stream.ael"
        self._index: dict[str, int] = {}
        self._deleted: set[str] = set()
        self.reclaimed_mb = 0.0 # 🧹 v24.3.11: Real Reclaim Tracker
        import threading
        self._compaction_lock = threading.Lock()

        # Apri il file. r+b per leggere e scrivere, w+b se non esiste
        if not self.log_path.exists():
            open(self.log_path, "w+b").close()
        
        self._fd = open(self.log_path, "r+b")
        self._build_index()

    def _build_index(self):
        """Scansiona l'intero log e costruisce l'indice offset in memoria."""
        self._fd.seek(0)
        self._index.clear()
        self._deleted.clear()
        
        while True:
            offset = self._fd.tell()
            header = self._fd.read(4)
            if not header or len(header) < 4:
                # Tronca log se ci sono byte corrotti alla fine (Crash Recovery istantaneo)
                if len(header) > 0:
                    self._fd.truncate(offset)
                break
                
            payload_len = struct.unpack("<I", header)[0]
            payload = self._fd.read(payload_len)
            
            if len(payload) < payload_len:
                self._fd.truncate(offset) # Tronca log corrotto
                break 
                
            data = msgpack.unpackb(payload, raw=False)
            node_id = data["id"]
            
            if data.get("tombstone", False):
                self._deleted.add(node_id)
                if node_id in self._index:
                    del self._index[node_id]
            else:
                self._index[node_id] = offset
                if node_id in self._deleted:
                    self._deleted.remove(node_id)
                    
        # Fissa l'offset finale per gli append successivi
        self._fd.seek(0, 2)

    def put(self, node: VaultNode, immediate: bool = True) -> None:
        with self._compaction_lock:
            self._put_internal(node)
            if immediate:
                self._fd.flush()

    def put_batch(self, nodes: list[VaultNode]) -> None:
        with self._compaction_lock:
            for node in nodes:
                self._put_internal(node)
            self._fd.flush()

    def _put_internal(self, node: VaultNode) -> None:
        edges = []
        if node.edges:
            edges = [
                {"target_id": e.target_id, "relation": e.relation.value, "weight": e.weight, "source": e.source}
                for e in node.edges
            ]
        
        # v0.5.5 Resilience: Convertiamo in bytes solo se è un oggetto numpy, altrimenti gestiamo liste
        vec_bytes = b""
        if node.vector is not None:
            if hasattr(node.vector, 'tobytes'):
                vec_bytes = node.vector.tobytes()
            else:
                # Se non ha dtype, usa float32 come default legacy
                vec_bytes = np.array(node.vector, dtype=np.float32).tobytes()

        data = {
            "id": node.id, 
            "text": node.text,
            "vector": vec_bytes,
            "sparse_vector": node.sparse_vector,
            "collection": node.collection,
            "namespace": node.namespace,
            "version": node.version,
            "metadata": node.metadata,
            "tier": node.tier.value,
            "access_count": node.access_count,
            "last_accessed": node.last_accessed,
            "created_at": node.created_at,
            "agent_relevance_score": node.agent_relevance_score,
            "edges": edges,
            "tombstone": False
        }
        
        payload = msgpack.packb(data, use_bin_type=True)
        payload_len = len(payload)
        
        self._fd.seek(0, 2) # Posizionati alla fine
        offset = self._fd.tell()
        
        self._fd.write(struct.pack("<I", payload_len))
        self._fd.write(payload)
        
        # O(1) in RAM Update
        self._index[node.id] = offset
        if node.id in self._deleted:
            self._deleted.remove(node.id)

    def get(self, node_id: str, load_vector: bool = True) -> VaultNode | None:
        if node_id not in self._index:
            return None
            
        offset = self._index[node_id]
        self._fd.seek(offset)
        header = self._fd.read(4)
        payload_len = struct.unpack("<I", header)[0]
        payload = self._fd.read(payload_len)
        self._fd.seek(0, 2) # rimettiti alla fine per sicurezza nel caso di thread access
        
        data = msgpack.unpackb(payload, raw=False)
        
        vector = None
        if load_vector and data.get("vector"):
            vec_bytes = data["vector"]
            # Rilevamento automatico Precisione (Gap #1)
            dtype = np.float16 if len(vec_bytes) == self.dim * 2 else np.float32
            vector = np.frombuffer(vec_bytes, dtype=dtype).copy()
            
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
            sparse_vector=data.get("sparse_vector"),
            metadata=data.get("metadata", {}),
            edges=edges,
            collection=data.get("collection", "default"),
            namespace=data.get("namespace", "default"),
            version=data.get("version", 1),
            access_count=data.get("access_count", 0),
            last_accessed=data.get("last_accessed", 0.0),
            created_at=data.get("created_at", 0.0),
            agent_relevance_score=data.get("agent_relevance_score", 0.0),
            tier=MemoryTier.EPISODIC,
        )

    def delete(self, node_id: str) -> bool:
        with self._compaction_lock:
            if node_id not in self._index:
                return False
                
            data = {
                "id": node_id,
                "tombstone": True
            }
            
            payload = msgpack.packb(data, use_bin_type=True)
            payload_len = len(payload)
            
            self._fd.seek(0, 2)
            self._fd.write(struct.pack("<I", payload_len))
            self._fd.write(payload)
            self._fd.flush()
            
            del self._index[node_id]
            self._deleted.add(node_id)
            return True

    def undelete(self, node_id: str) -> bool:
        """
        [Fase 25: Rollback] Ripristina un nodo eliminato recuperando l'ultimo stato valido dal log AOBF.
        Implementa il protocollo di sicurezza 'Rollback Neurale' con Circuit Breaker per performance.
        """
        # Circuit Breaker: se il log è enorme (>100MB), evitiamo scansioni lineari bloccanti durante il boot
        if self.log_path.stat().st_size > 100 * 1024 * 1024:
            print(f"⚠️ [AOBF] Log troppo grande per scansione lineare. Rollback ignorato per {node_id[:8]}")
            return False

        with self._compaction_lock:
            if node_id in self._index:
                return False # Il nodo è già attivo
                
            # Scansione lineare limitata (max 50,000 record per sicurezza)
            last_valid_offset = -1
            try:
                self._fd.seek(0)
                count = 0
                while count < 50000:
                    offset = self._fd.tell()
                    header = self._fd.read(4)
                    if not header or len(header) < 4: break
                        
                    payload_len = struct.unpack("<I", header)[0]
                    payload = self._fd.read(payload_len)
                    if len(payload) < payload_len: break
                        
                    data = msgpack.unpackb(payload, raw=False)
                    if data["id"] == node_id and not data.get("tombstone", False):
                        last_valid_offset = offset
                    count += 1
            except: pass
            
            if last_valid_offset != -1:
                self._index[node_id] = last_valid_offset
                if node_id in self._deleted:
                    self._deleted.remove(node_id)
                self._fd.seek(0, 2)
                return True
            
            self._fd.seek(0, 2)
            return False

    def iter_all(self, load_vector: bool = True) -> Iterator[VaultNode]:
        """Itera su tutti i nodi validi dal DB."""
        for node_id in list(self._index.keys()):
            node = self.get(node_id, load_vector)
            if node:
                yield node

    def count(self) -> int:
        return len(self._index)

    def compact(self):
        """
        [Fase 29: Aegis Reaper] Compattazione Fisica del Log.
        Riscrive il log eliminando record 'tombstone' e vecchie versioni.
        Libera spazio reale su disco e ottimizza i tempi di caricamento.
        """
        temp_path = self.path.with_suffix(".tmp_compact")
        new_index = {}
        
        with self._compaction_lock:
            with open(temp_path, "wb") as new_fd:
                # Iteriamo solo sui nodi attualmente indicizzati (i più recenti validi)
                for node_id, old_offset in self._index.items():
                    # Leggi il dato dal vecchio FD
                    self._fd.seek(old_offset)
                    header = self._fd.read(4)
                    if not header: continue
                    payload_len = struct.unpack("<I", header)[0]
                    payload = self._fd.read(payload_len)
                    
                    # Scrivi nel nuovo FD
                    new_offset = new_fd.tell()
                    new_fd.write(struct.pack("<I", payload_len))
                    new_fd.write(payload)
                    
                    # Aggiorna l'indice temporaneo
                    new_index[node_id] = new_offset
            
            # Switch dei file
            self._fd.close()
            os.replace(temp_path, self.path)
            
            # Riapriamo il file originale ora compattato
            self._fd = open(self.path, "r+b")
            self._index = new_index
            self._deleted.clear()
            
        print(f"🧹 [Aegis Reaper] Compattazione completata. Log compresso a {len(new_index)} record attivi.")

    def flush(self):
        """Forza la scrittura dei buffer OS su disco per garantire l'integrità fisica."""
        if self._fd:
            try:
                self._fd.flush()
                import os
                os.fsync(self._fd.fileno())
            except:
                pass

    def scan_recent(self, limit: int = 100) -> list[VaultNode]:
        """Recupera gli ultimi N nodi inseriti per la Hot Hydration."""
        nodes = []
        recent_offsets = sorted(self._index.values(), reverse=True)
        
        for offset in recent_offsets[:limit]:
            self._fd.seek(offset)
            header = self._fd.read(4)
            if len(header) < 4: continue
            payload_len = struct.unpack("<I", header)[0]
            payload = self._fd.read(payload_len)
            
            data = msgpack.unpackb(payload, raw=False)
            
            vector = None
            if data.get("vector"):
                vec_bytes = data["vector"]
                dtype = np.float16 if len(vec_bytes) == self.dim * 2 else np.float32
                vector = np.frombuffer(vec_bytes, dtype=dtype).copy()
                
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
                
            node = VaultNode(
                id=data["id"],
                text=data.get("text", ""),
                vector=vector,
                sparse_vector=data.get("sparse_vector"),
                metadata=data.get("metadata", {}),
                edges=edges,
                collection=data.get("collection", "default"),
                namespace=data.get("namespace", "default"),
                version=data.get("version", 1),
                access_count=data.get("access_count", 0),
                last_accessed=data.get("last_accessed", 0.0),
                created_at=data.get("created_at", 0.0),
                agent_relevance_score=data.get("agent_relevance_score", 0.0),
                tier=MemoryTier.EPISODIC,
            )
            nodes.append(node)
            
        self._fd.seek(0, 2)
        return nodes

    def compact(self) -> bool:
        """
        [Fase 27] Aegis Reaper: Compattazione asincrona lock-free (per la maggior parte).
        Consolida i record ghost / tombstoned per azzerare lo spazio perso.
        """
        # Creiamo un file temporaneo 
        import shutil
        tmp_path = self.log_path.with_suffix(".ael.tmp")
        
        # Iteriamo su tutti i nodi _validi_ e li scriviamo sul file tmp.
        # Operiamo su una copia in deep delle chiavi per evitare un lock troppo lungo
        valid_ids = list(self._index.keys()) 
        
        with open(tmp_path, "w+b") as tmp_fd:
            for node_id in valid_ids:
                node = self.get(node_id, load_vector=True)
                if not node: continue
                
                # Serializziamo esattamente come _put_internal, ottimizzando
                edges = [
                    {"target_id": e.target_id, "relation": e.relation.value, "weight": e.weight, "source": e.source}
                    for e in node.edges
                ]
                
                data = {
                    "id": node.id, 
                    "text": node.text,
                    "vector": node.vector.tobytes() if node.vector is not None else b"",
                    "sparse_vector": node.sparse_vector,
                    "collection": node.collection,
                    "namespace": node.namespace,
                    "version": node.version,
                    "metadata": node.metadata,
                    "tier": node.tier.value,
                    "access_count": node.access_count,
                    "last_accessed": node.last_accessed,
                    "created_at": node.created_at,
                    "agent_relevance_score": node.agent_relevance_score,
                    "edges": edges,
                    "tombstone": False
                }
                
                payload = msgpack.packb(data, use_bin_type=True)
                tmp_fd.write(struct.pack("<I", len(payload)))
                tmp_fd.write(payload)
                
            tmp_fd.flush()
            
        # Swap Atomico: usiamo il lock solo in questi <2ms
        with self._compaction_lock:
            old_size = self.log_path.stat().st_size
            self._fd.close()
            os.replace(tmp_path, self.log_path) # Swap zero-waste & atomico
            self._fd = open(self.log_path, "r+b")
            new_size = self.log_path.stat().st_size
            self.reclaimed_mb += (old_size - new_size) / (1024 * 1024)
            self._build_index()
            
        return True

    def close(self):
        if hasattr(self, '_fd') and self._fd and not self._fd.closed:
            self._fd.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

