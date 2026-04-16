"""
neuralvault.storage.wal
────────────────────────
Write-Ahead Log (WAL) per garantire l'atomicità delle operazioni.
Ogni operazione viene scritta sul log prima di essere applicata ai tier di memoria.
In caso di crash, il sistema esegue il replay del log per ripristinare la consistenza.
"""

import os
import json
import threading
import zlib
from pathlib import Path

class WAL:
    def __init__(self, data_dir: Path):
        self.log_file = data_dir / "vault.wal"
        self._lock = threading.Lock()
        
        if not self.log_file.exists():
            self.log_file.touch()

    def append(self, op_type: str, node_id: str, data: dict):
        """Append di una operazione al log (Sync)."""
        payload = json.dumps({
            "op": op_type,
            "id": node_id,
            "data": data,
            "status": "pending"
        })
        checksum = zlib.adler32(payload.encode())
        entry = f"{checksum}|{payload}\n"
        with self._lock:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
                f.flush()
                # fsync per garantire la scrittura fisica sul disco
                os.fsync(f.fileno())

    def commit(self, node_id: str):
        """Marca una operazione come completata."""
        payload = json.dumps({"id": node_id, "status": "committed"})
        checksum = zlib.adler32(payload.encode())
        entry = f"{checksum}|{payload}\n"
        with self._lock:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(entry)
                f.flush()
                os.fsync(f.fileno())

    def get_pending_operations(self) -> list[dict]:
        """Analizza il log e restituisce solo le operazioni non 'committed'."""
        if not self.log_file.exists():
            return []

        history = {}
        with self._lock:
            with open(self.log_file, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        if "|" not in line: continue
                        chk_str, payload = line.split("|", 1)
                        if zlib.adler32(payload.strip().encode()) != int(chk_str):
                            continue # Corrupt entry: skip
                        
                        entry = json.loads(payload)
                        node_id = entry["id"]
                        if entry.get("status") == "pending":
                            history[node_id] = entry
                        elif entry.get("status") == "committed":
                            if node_id in history:
                                del history[node_id]
                    except (json.JSONDecodeError, ValueError):
                        continue
        return list(history.values())

    def clear(self):
        """Pulisce il log dopo un checkpoint/flush completo su Parquet."""
        with self._lock:
            self.log_file.write_text("")
