"""
neuralvault.cluster.shard
─────────────────────────
Gestore dello Sharding e del Cloning per NeuralVault v0.3.0.
Permette di segmentare la memoria per scalabilità orizzontale.
"""

import shutil
import uuid
from pathlib import Path
from typing import Optional, List

class ShardManager:
    """
    Gestore della segmentazione fisica della memoria.
    Supporta il "Cloning" di shard per ridondanza e failover.
    """
    def __init__(self, base_path: Path):
        self.base_path = base_path
        self._shards_dir = base_path / "shards"
        self._shards_dir.mkdir(parents=True, exist_ok=True)

    def create_shard(self, shard_id: Optional[str] = None) -> str:
        """Crea un nuovo segmento di memoria isolato."""
        sid = shard_id or str(uuid.uuid4())[:8]
        shard_path = self._shards_dir / sid
        shard_path.mkdir(exist_ok=True)
        (shard_path / "episodic").mkdir(exist_ok=True)
        (shard_path / "semantic").mkdir(exist_ok=True)
        return sid

    def clone_shard(self, source_id: str, target_id: Optional[str] = None) -> str:
        """
        [Fase 17]: Shard Cloning Logic.
        Crea una copia fisica esatta di uno shard per ridondanza locale.
        """
        tid = target_id or f"{source_id}_replica_{int(time.time())}"
        src_path = self._shards_dir / source_id
        dst_path = self._shards_dir / tid
        
        if not src_path.exists():
            raise FileNotFoundError(f"Shard sorgente {source_id} non trovato.")
            
        shutil.copytree(src_path, dst_path, dirs_exist_ok=True)
        print(f"🧬 Shard Clone: Created replica {tid} from {source_id}")
        return tid

    def list_shards(self) -> List[str]:
        return [d.name for d in self._shards_dir.iterdir() if d.is_dir()]
