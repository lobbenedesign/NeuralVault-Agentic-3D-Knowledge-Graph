"""
neuralvault.storage.parquet_store
───────────────────────────────
Storage Parquet per il tier semantico (storage permanente).
Colonnare, compresso (Zstd), predisposto per analytics (DuckDB).
"""

from __future__ import annotations
import json
import pyarrow as pa
import pyarrow.parquet as pq
from pathlib import Path
import numpy as np
try:
    import duckdb
    HAS_DUCKDB = True
except ImportError:
    HAS_DUCKDB = False
from typing import Iterator, List

from index.node import VaultNode, MemoryTier, SemanticEdge, RelationType

# Schema Arrow per un VaultNode
VAULT_SCHEMA = pa.schema([
    pa.field("id",                    pa.string()),
    pa.field("text",                  pa.string()),
    pa.field("collection",            pa.string()),
    pa.field("namespace",             pa.string()),
    pa.field("vector",                pa.list_(pa.float32())),
    pa.field("metadata_json",         pa.string()),
    pa.field("edges_json",            pa.string()),
    pa.field("access_count",          pa.int32()),
    pa.field("last_accessed",         pa.float64()),
    pa.field("created_at",            pa.float64()),
    pa.field("agent_relevance_score", pa.float32()),
])

ROWS_PER_FILE = 100_000

class ParquetStore:
    """
    Storage Parquet per il tier semantico.
    Write path: buffer in memoria → flush su disco ogni ROWS_PER_FILE nodi.
    Read path: indice in-memory (node_id → file+row) per lookup O(1).
    """

    def __init__(self, data_dir: str | Path, dim: int = 1024):
        self.data_dir = Path(data_dir)
        self.dim = dim
        self.data_dir.mkdir(parents=True, exist_ok=True)
        # DB DuckDB in-memory se disponibile
        self._con = duckdb.connect(database=':memory:') if HAS_DUCKDB else None

        self._index: dict[str, tuple[str, int]] = {}
        self._write_buffer: list[VaultNode] = []
        self._file_counter = 0

        self._load_index()

    def _load_index(self):
        """Ricostruisce l'indice node_id → posizione da tutti i file Parquet."""
        index_path = self.data_dir / "_index.json"
        if index_path.exists():
            with open(index_path) as f:
                self._index = json.load(f)
            
            # Calcola il file counter basato sui file esistenti
            parquet_files = list(self.data_dir.glob("part-*.parquet"))
            if parquet_files:
                self._file_counter = len(parquet_files)
        else:
            # Se l'indice non esiste, facciamo uno scan dei file per ricostruirlo
            # (fondamentale per restart da crash)
            self._rebuild_index_from_files()

    def _rebuild_index_from_files(self):
        """Scan di tutti i file parquet per ricostruire l'indice ID -> Posizione."""
        for file_path in sorted(self.data_dir.glob("part-*.parquet")):
            table = pq.read_table(file_path, columns=["id"])
            ids = table.column("id").to_pylist()
            file_name = file_path.name
            for i, nid in enumerate(ids):
                self._index[nid] = (file_name, i)
        
        # Salva l'indice appena ricostruito
        self._save_index()
        parquet_files = list(self.data_dir.glob("part-*.parquet"))
        self._file_counter = len(parquet_files)

    def _save_index(self):
        index_path = self.data_dir / "_index.json"
        with open(index_path, "w") as f:
            json.dump(self._index, f)

    def put(self, node: VaultNode) -> None:
        """Aggiunge al buffer. Flush automatico quando il buffer è pieno."""
        self._write_buffer.append(node)
        if len(self._write_buffer) >= ROWS_PER_FILE:
            self.flush()

    def put_many(self, nodes: list[VaultNode]) -> None:
        """Aggiunge molti nodi al buffer."""
        for node in nodes:
            self.put(node)

    def flush(self) -> None:
        """Scrive il buffer su disco come file Parquet."""
        if not self._write_buffer:
            return

        file_name = f"part-{self._file_counter:04d}.parquet"
        file_path = self.data_dir / file_name

        data = {
            "id":                    [],
            "text":                  [],
            "collection":            [],
            "namespace":             [],
            "vector":                [],
            "metadata_json":         [],
            "edges_json":            [],
            "access_count":          [],
            "last_accessed":         [],
            "created_at":            [],
            "agent_relevance_score": [],
        }

        for node in self._write_buffer:
            data["id"].append(node.id)
            data["text"].append(node.text)
            data["collection"].append(node.collection)
            data["namespace"].append(node.namespace)
            data["vector"].append(node.vector.tolist() if node.vector is not None else [])
            data["metadata_json"].append(json.dumps(node.metadata))
            data["edges_json"].append(json.dumps([
                {"target_id": e.target_id, "relation": e.relation.value, "weight": e.weight, "source": e.source}
                for e in node.edges
            ]))
            data["access_count"].append(node.access_count)
            data["last_accessed"].append(node.last_accessed)
            data["created_at"].append(node.created_at)
            data["agent_relevance_score"].append(node.agent_relevance_score)

        table = pa.table(data, schema=VAULT_SCHEMA)
        pq.write_table(table, file_path, compression="zstd", compression_level=3)

        # Aggiorna indice
        for i, node in enumerate(self._write_buffer):
            self._index[node.id] = (file_name, i)

        self._file_counter += 1
        self._write_buffer.clear()
        self._save_index()

    def get(self, node_id: str) -> VaultNode | None:
        """Legge un singolo nodo tramite row group targeting."""
        if node_id not in self._index:
            # Controlla il buffer in memoria non ancora flushato
            for node in self._write_buffer:
                if node.id == node_id:
                    return node
            return None

        file_name, row_idx = self._index[node_id]
        file_path = self.data_dir / file_name

        # Legge solo la riga necessaria
        # Nota: read_table(columns=None) legge tutto, per ottimizzare latenza
        # su disco potremmo usare scan() ma per file singoli va bene così.
        table = pq.read_table(file_path)
        row_dict = {col: table.column(col)[row_idx].as_py() for col in table.schema.names}
        return self._row_to_node(row_dict)

    def iter_all(self, collection: str | None = None) -> Iterator[VaultNode]:
        """Itera su tutti i nodi."""
        for file_path in sorted(self.data_dir.glob("part-*.parquet")):
            table = pq.read_table(file_path)
            if collection:
                mask = pa.compute.equal(table.column("collection"), collection)
                table = table.filter(mask)
            
            # Iterazione su righe (Arrow Table)
            # Per performance estreme si userebbe .to_batches()
            for i in range(len(table)):
                row_dict = {col: table.column(col)[i].as_py() for col in table.schema.names}
                yield self._row_to_node(row_dict)

        # Includi il buffer
        for node in self._write_buffer:
            if collection is None or node.collection == collection:
                yield node

    def delete(self, node_id: str) -> bool:
        """Rimuove un nodo dall'indice. Non lo cancella dal file Parquet immediatamente."""
        if node_id in self._index:
            del self._index[node_id]
            self._save_index()
            return True
        return False

    def count(self) -> int:
        return len(self._index) + len(self._write_buffer)

    def query_metadata(self, sql_where: str) -> List[str]:
        """
        Esegue ricerca SQL se DuckDB è presente, altrimenti fallback su scan manuale.
        """
        parquet_path = self.data_dir / "part-*.parquet"
        if not list(self.data_dir.glob("part-*.parquet")):
            return []
            
        if HAS_DUCKDB:
            sql = f"SELECT id FROM read_parquet('{parquet_path}') WHERE {sql_where}"
            try:
                res = self._con.execute(sql).fetchall()
                return [r[0] for r in res]
            except Exception: return []
        else:
            # Fallback scan manuale per compatibilità
            ids = []
            for file_path in self.data_dir.glob("part-*.parquet"):
                table = pq.read_table(file_path, columns=["id"])
                ids.extend(table.column("id").to_pylist())
            return ids

    def scan(self) -> Iterator[VaultNode]:
        """Itera su tutti i nodi salvati nei file Parquet."""
        for file_path in self.data_dir.glob("part-*.parquet"):
            table = pq.read_table(file_path)
            for row in table.to_batches():
                dicts = row.to_pylist()
                for d in dicts:
                    yield self._row_to_node(d)

    def count(self) -> int:
        """Conta il numero totale di record nei file Parquet."""
        total = 0
        for file_path in self.data_dir.glob("part-*.parquet"):
            table = pq.read_table(file_path, columns=["id"])
            total += table.num_rows
        return total

    def __len__(self) -> int:
        return self.count()

    def _row_to_node(self, row: dict) -> VaultNode:
        # Rilevamento automatico Precisione (Gap #1)
        dtype = np.float16 if row["vector"] and len(row["vector"]) == self.dim else np.float32
        vector = np.array(row["vector"], dtype=dtype) if row["vector"] else None
        metadata = json.loads(row["metadata_json"]) if row["metadata_json"] else {}
        edge_data = json.loads(row["edges_json"]) if row["edges_json"] else []
        
        edges = [
            SemanticEdge(
                target_id=e["target_id"],
                relation=RelationType(e["relation"]),
                weight=e["weight"],
                source=e.get("source", "manual")
            )
            for e in edge_data
        ]

        return VaultNode(
            id=row["id"],
            text=row["text"],
            vector=vector,
            metadata=metadata,
            edges=edges,
            collection=row.get("collection", "default"),
            namespace=row.get("namespace", "default"),
            access_count=row.get("access_count", 0),
            last_accessed=row.get("last_accessed", 0.0),
            created_at=row.get("created_at", 0.0),
            agent_relevance_score=row.get("agent_relevance_score", 0.0),
            tier=MemoryTier.SEMANTIC,
        )
