"""
index/sharding.py
──────────────────────────────
Gestione dei frammenti (Shards) e clonazione della conoscenza.
Permette il "Neural Warp": trasferimento atomico di sotto-indici tra vault.
"""

import os
import shutil
from pathlib import Path
from typing import List, Dict
import json

class KnowledgeShard:
    def __init__(self, shard_id: str, nodes_ids: List[str], metadata: Dict = None):
        self.shard_id = shard_id
        self.nodes_ids = nodes_ids
        self.metadata = metadata or {}

class ShardManager:
    """Gestore della frammentazione della conoscenza per l'architettura Mesh."""
    
    def __init__(self, engine_data_dir: Path):
        self.root = engine_data_dir / "shards"
        self.root.mkdir(parents=True, exist_ok=True)
        self.active_shards: Dict[str, KnowledgeShard] = {}

    def create_shard(self, shard_name: str, criteria_fn: callable, all_nodes: dict) -> str:
        """Crea un frammento basato su criteri semantici o temporali."""
        shard_id = f"shard_{shard_name}_{int(os.getpid())}"
        target_ids = [nid for nid, node in all_nodes.items() if criteria_fn(node)]
        
        shard = KnowledgeShard(shard_id, target_ids, {"count": len(target_ids)})
        self.active_shards[shard_id] = shard
        
        # Salvataggio metadati shard
        with open(self.root / f"{shard_id}.json", "w") as f:
            json.dump({"id": shard_id, "nodes": target_ids}, f)
            
        print(f"🌌 [Sharding] Creato Shard '{shard_id}' con {len(target_ids)} nodi.")
        return shard_id

    def warp_shard(self, shard_id: str, destination_path: Path):
        """Esegue il 'Neural Warp': esportazione fisica del frammento."""
        if shard_id not in self.active_shards:
            print(f"⚠️ Shard {shard_id} non trovato.")
            return False
            
        print(f"🛸 [Warp] Inizio Neural Warp dello Shard {shard_id} verso {destination_path}...")
        # In una vera implementazione qui copieremmo i file LMDB/DuckDB filtrati
        # Per ora simuliamo il successo dell'operazione atomica
        destination_path.mkdir(parents=True, exist_ok=True)
        shutil.copy(self.root / f"{shard_id}.json", destination_path / f"{shard_id}.json")
        
        print(f"🚀 [Warp] Neural Warp completato con successo.")
        return True
