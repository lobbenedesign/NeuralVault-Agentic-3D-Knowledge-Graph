"""
retrieval/prefilter.py
───────────────────────
DuckDB Prefilter: Database relazionale incorporato per pre-filtraggio metadati.
Permette ricerche SQL-like ultra-veloci (Fisicamente pronti per un milione di nodi).
"""

import duckdb
import pandas as pd
import threading
from pathlib import Path
from typing import List, Dict, Optional

class DuckDBPrefilter:
    """
    Motore di ricerca su metadati strutturati (v0.2.5).
    Responsabile del routing analitico del Query Planner.
    """
    def __init__(self, db_path: Optional[Path] = None):
        self._lock = threading.Lock()
        if db_path:
            try:
                self.con = duckdb.connect(database=str(db_path / "vault_metadata.db"))
                # [Optimization]: Consolidamento WAL per risparmio spazio
                self.con.execute("PRAGMA checkpoint_threshold = '512MB';")
                self.con.execute("CHECKPOINT;")
                print("🦆 [DuckDB] Hyper-Optimization Active (Checkpoint/WAL consolidation).")
            except Exception as e:
                print(f"⚠️ [Prefilter] WAL Conflict or Internal Error: {e}")
                db_file = str(db_path / "vault_metadata.db")
                import os
                wal_path = f"{db_file}.wal"
                if os.path.exists(wal_path):
                    try: os.remove(wal_path)
                    except: pass
                
                try:
                    self.con = duckdb.connect(db_file)
                except:
                    print(f"☣️ [Prefilter] Recovery failed. Resetting metadata index.")
                    try: os.remove(db_file)
                    except: pass
                    self.con = duckdb.connect(db_file)
        else:
            self.con = duckdb.connect(":memory:")
            
        # Creazione schema iniziale (v0.5.0: Synaptic Pillars)
        self.con.execute("""
            CREATE TABLE IF NOT EXISTS vault_metadata (
                id VARCHAR PRIMARY KEY,
                collection VARCHAR,
                created_at TIMESTAMP,
                last_access TIMESTAMP,
                access_count INTEGER DEFAULT 0,
                importance DOUBLE DEFAULT 1.0,
                modality VARCHAR DEFAULT 'text',
                content_hash VARCHAR,
                lifecycle_state VARCHAR DEFAULT 'stable',
                metadata JSON
            )
        """)

        # Memoria Episodica Persistente (v1.1.0 Sovereign Hardening)
        self.con.execute("""
            CREATE TABLE IF NOT EXISTS episodic_memory (
                node_id VARCHAR PRIMARY KEY,
                protected_at TIMESTAMP DEFAULT now(),
                rejected_by VARCHAR,
                reason VARCHAR,
                protection_level INTEGER DEFAULT 1,
                confidence DOUBLE DEFAULT 1.0
            )
        """)

        # 📊 Telemetria Agenti Persistente (v3.5.0)
        self.con.execute("""
            CREATE TABLE IF NOT EXISTS agent_telemetry (
                agent_id VARCHAR,
                counter_name VARCHAR,
                val DOUBLE DEFAULT 0,
                last_updated TIMESTAMP DEFAULT now(),
                PRIMARY KEY (agent_id, counter_name)
            )
        """)
        
        # Migrazione schema se necessario (v0.5.5 Deduplication + v1.1.0 Lifecycle)
        try:
            cols = self.con.execute("PRAGMA table_info('vault_metadata')").fetchall()
            col_names = [c[1] for c in cols]
            
            if 'lifecycle_state' not in col_names:
                print("🔄 [v1.1.0] Aggiunta colonna Lifecycle State...")
                self.con.execute("ALTER TABLE vault_metadata ADD COLUMN lifecycle_state VARCHAR DEFAULT 'stable'")

            if 'last_access' not in col_names:
                print("🧠 [v0.5.0] Migrazione schema: Aggiunta pilastri cognitivi...")
                self.con.execute("ALTER TABLE vault_metadata ADD COLUMN last_access TIMESTAMP DEFAULT now()")
                self.con.execute("ALTER TABLE vault_metadata ADD COLUMN access_count INTEGER DEFAULT 1")
                self.con.execute("ALTER TABLE vault_metadata ADD COLUMN importance DOUBLE DEFAULT 1.0")
                self.con.execute("ALTER TABLE vault_metadata ADD COLUMN modality VARCHAR DEFAULT 'text'")
            
            if 'content_hash' not in col_names:
                print("🔒 [v0.5.5] Inizializzazione motore di Deduplicazione...")
                self.con.execute("ALTER TABLE vault_metadata ADD COLUMN content_hash VARCHAR")
                self.con.execute("CREATE INDEX IF NOT EXISTS idx_content_hash ON vault_metadata(content_hash)")
        except Exception as e:
            print(f"⚠️ [DuckDB Migration] {e}")

        print("🦆 NeuralVault: DuckDB Analytical Engine online.")

    def add_node(self, node_id: str, collection: str, metadata: Dict):
        """Indicizza un singolo nodo (Fallback)."""
        import json
        self.add_nodes_batch([(node_id, collection, metadata)])

    def add_nodes_batch(self, nodes_data: List[tuple]):
        """Indicizza nodi in batch con supporto cognitivo e transazione atomica (v0.5.2)."""
        import json
        
        # Prepariamo i dati per l'inserimento di massa
        data_to_insert = []
        for node_id, collection, metadata in nodes_data:
            meta_json = json.dumps(metadata)
            modality = metadata.get("modality", "text")
            importance = metadata.get("importance", 1.0)
            c_hash = metadata.get("content_hash")
            l_state = metadata.get("lifecycle_state", "stable")
            data_to_insert.append((node_id, collection, importance, modality, c_hash, l_state, meta_json))

        # Esecuzione in una singola transazione (Turbo Mode)
        try:
            self.executemany("""
                INSERT OR REPLACE INTO vault_metadata 
                (id, collection, created_at, last_access, access_count, importance, modality, content_hash, lifecycle_state, metadata)
                VALUES (?, ?, now(), now(), 1, ?, ?, ?, ?, ?)
            """, data_to_insert)
        except Exception as e:
            print(f"⚠️ Errore nel Batch Ingest Prefilter: {e}")

    def check_duplicate(self, content_hash: str) -> Optional[str]:
        """Controlla se esiste già un nodo con questo hash. Restituisce l'ID del primo duplicato."""
        if not content_hash: return None
        res = self.execute("SELECT id FROM vault_metadata WHERE content_hash = ? LIMIT 1", (content_hash,)).fetchone()
        return res[0] if res else None

    def hit_node(self, node_id: str):
        """Rinforzo sinaptico: Aggiorna l'ultimo accesso e aumenta il conteggio."""
        self.execute(
            "UPDATE vault_metadata SET last_access = now(), access_count = access_count + 1 WHERE id = ?",
            (node_id,)
        )

    def delete(self, node_id: str) -> bool:
        """Rimuove permanentemente un nodo dai metadati DuckDB."""
        try:
            self.execute("DELETE FROM vault_metadata WHERE id = ?", (node_id,))
            return True
        except Exception as e:
            print(f"DuckDB Delete Error: {e}")
            return False

    def filter(self, sql_where: str) -> List[str]:
        """Esegue una query SQL per trovare gli ID che soddisfano il filtro."""
        try:
            # Query ultra-veloce (DuckDB vince su tutto per analytics locale)
            query = f"SELECT id FROM vault_metadata WHERE {sql_where}"
            res = self.execute(query).fetchall()
            return [r[0] for r in res]
        except Exception as e:
            print(f"⚠️ Errore nel Prefilter SQL: {e}")
            return []

    def count(self) -> int:
        return self.execute("SELECT count(*) FROM vault_metadata").fetchone()[0]

    # --- v1.1.0: Lifecycle & Episodic Memory ---
    
    def update_lifecycle_state(self, node_id: str, new_state: str):
        """Aggiorna lo stato del nodo nella macchina a stati (v1.1.0)."""
        self.execute(
            "UPDATE vault_metadata SET lifecycle_state = ? WHERE id = ?",
            (new_state.lower(), node_id)
        )

    def protect_node_persistent(self, node_id: str, rejected_by: str, reason: str, level: int = 1, confidence: float = 1.0):
        """Salva permanentemente un rifiuto utente o un'istruzione di protezione."""
        try:
            self.execute("""
                INSERT OR REPLACE INTO episodic_memory 
                (node_id, protected_at, rejected_by, reason, protection_level, confidence)
                VALUES (?, now(), ?, ?, ?, ?)
            """, (node_id, rejected_by, reason, level, confidence))
            # Promuove il nodo a PROTECTED anche nel lifecycle
            self.update_lifecycle_state(node_id, "protected")
        except Exception as e:
            print(f"⚠️ [Episodic Memory Store] {e}")

    def is_node_protected(self, node_id: str) -> bool:
        """Controlla se un nodo è sotto protezione persistente (Episodic Memory)."""
        res = self.execute("SELECT node_id FROM episodic_memory WHERE node_id = ?", (node_id,)).fetchone()
        return res is not None

    def get_protected_nodes(self) -> List[str]:
        """Restituisce tutti gli ID protetti."""
        res = self.execute("SELECT node_id FROM episodic_memory").fetchall()
        return [r[0] for r in res]

    def get_knowledge_sources(self) -> List[Dict]:
        """Raggruppa la conoscenza per sorgente originaria (Analytic Hub)."""
        try:
            # Estraiamo 'source' e 'title' dal JSON dei metadati
            query = """
                SELECT 
                    metadata->>'$.source' as source,
                    metadata->>'$.title' as title,
                    count(*) as node_count,
                    min(created_at) as first_seen,
                    max(created_at) as last_seen
                FROM vault_metadata
                GROUP BY source, title
                ORDER BY first_seen DESC
            """
            res = self.execute(query).fetchall()
            sources = []
            for r in res:
                sources.append({
                    "source": r[0] or "Unknown Source",
                    "title": r[1] or r[0] or "Agent Asset",
                    "nodes": r[2],
                    "date": r[3].strftime("%Y-%m-%d %H:%M:%S") if r[3] else "---",
                    "timestamp": r[3].timestamp() if r[3] else 0
                })
            return sources
        except Exception as e:
            print(f"⚠️ Errore aggregazione Inventory: {e}")
            return []

    def execute(self, query: str, params: tuple = ()):
        """Esegue una query SQL in modo thread-safe."""
        with self._lock:
            return self.con.execute(query, params)

    def executemany(self, query: str, params: List[tuple]):
        """Esegue un batch di query SQL in modo thread-safe."""
        with self._lock:
            return self.con.executemany(query, params)

    def fetchdf(self, query: str, params: tuple = ()):
        """Recupera un DataFrame in modo thread-safe."""
        with self._lock:
            return self.con.execute(query, params).fetchdf()

    def close(self):
        """Chiude la connessione DuckDB in modo sicuro."""
        if self.con:
            self.con.close()
            self.con = None
