"""
neuralvault.storage.snapshot
────────────────────────────
Fase 26: Sovereign Snapshot Engine (Instant Boot).
Permette il dump dell'HNSW (grafo) e DuckDB (metadata) verso un formato
statico compatto, per consentire un resume a freddo in meno di un secondo
senza iterare su tutti i nodi nel tier episodico.
"""

import os
import time
import pickle
import tarfile
from pathlib import Path
from tempfile import TemporaryDirectory

class SnapshotEngine:
    def __init__(self, data_dir: Path, engine):
        self.data_dir = data_dir
        self.engine = engine
        self.snapshot_dir = self.data_dir / "snapshots"
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)
        self.latest_snapshot = self.snapshot_dir / "latest.tar.gz"

    def take_snapshot(self) -> bool:
        """
        Produce un archivio contenente HNSW struct e DuckDB export in Parquet.
        Questo elimina il WAL di DuckDB e la frammentazione.
        """
        print("📸 [Snapshot] Inizio Sovereign Snapshot Engine...")
        t0 = time.time()
        with TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # 1. HNSW Snapshot
            hnsw_path = tmpdir / "hnsw_state.pkl"
            state = {
                "layers": self.engine._hnsw.layers,
                "entry_point": self.engine._hnsw.entry_point,
                "max_level": self.engine._hnsw.max_level,
                "hit_counter": self.engine._hnsw._hit_counter,
                "promotion_count": self.engine._hnsw._promotion_count,
            }
            with open(hnsw_path, "wb") as f:
                pickle.dump(state, f, protocol=pickle.HIGHEST_PROTOCOL)
                
            # 2. Parquet Export (Eliminazione WAL)
            pq_path = tmpdir / "vault_metadata.parquet"
            if hasattr(self.engine._prefilter, "con") and self.engine._prefilter.con:
                self.engine._prefilter.con.execute(f"COPY vault_metadata TO '{pq_path}' (FORMAT PARQUET)")
                
            # 3. Pacchetto snapshot compresso
            with tarfile.open(self.latest_snapshot, "w:gz") as tar:
                tar.add(hnsw_path, arcname="hnsw_state.pkl")
                if pq_path.exists():
                    tar.add(pq_path, arcname="vault_metadata.parquet")
                    
        print(f"📸 [Snapshot] Dump completato in {time.time() - t0:.2f}s ({self.latest_snapshot.stat().st_size // 1024} KB)")
        return True

    def load_snapshot(self) -> bool:
        """Ripristina lo stato da snapshot, abilitando Instant Boot (cold-boot <1s)."""
        if not self.latest_snapshot.exists():
            return False
            
        print("⚡ [Snapshot] Instant Boot attivato: caricamento da snapshot...")
        t0 = time.time()
        
        with TemporaryDirectory() as tmpdir:
            with tarfile.open(self.latest_snapshot, "r:gz") as tar:
                tar.extractall(path=tmpdir)
                
            # Ripristino HNSW
            hnsw_path = Path(tmpdir) / "hnsw_state.pkl"
            if hnsw_path.exists():
                with open(hnsw_path, "rb") as f:
                    state = pickle.load(f)
                    self.engine._hnsw.layers = state.get("layers", [])
                    self.engine._hnsw.entry_point = state.get("entry_point")
                    self.engine._hnsw.max_level = state.get("max_level", -1)
                    self.engine._hnsw._hit_counter = state.get("hit_counter", {})
                    self.engine._hnsw._promotion_count = state.get("promotion_count", {})
                    
            # Ripristino Parquet in memoria o su DuckDB
            pq_path = Path(tmpdir) / "vault_metadata.parquet"
            if pq_path.exists() and hasattr(self.engine._prefilter, "con"):
                # Clean tabelle vecchie per rigenerare senza WAL
                try:
                    self.engine._prefilter.con.execute("TRUNCATE vault_metadata")
                    self.engine._prefilter.con.execute(f"INSERT INTO vault_metadata SELECT * FROM read_parquet('{pq_path}')")
                except:
                    pass
                    
        print(f"⚡ [Snapshot] Instant Boot completato in {time.time() - t0:.2f}s.")
        return True
