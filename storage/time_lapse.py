"""
neuralvault.storage.time_lapse
───────────────────────────────
Gestore della cronologia e replay dell'evoluzione del Vault.
Fase 4: Nebula Reach.
"""

import time
from typing import List, Dict, Any
from pathlib import Path

class TimeLapseManager:
    """
    Gestisce la visualizzazione dello stato del vault in momenti passati.
    Sfrutta DuckDB per interrogare i nodi in base a created_at.
    """
    def __init__(self, engine):
        self.engine = engine

    def get_snapshot_at(self, timestamp: float) -> List[str]:
        """Restituisce gli ID dei nodi presenti nel vault al timestamp indicato."""
        # Query DuckDB tramite il prefilter dell'engine
        if not hasattr(self.engine, '_prefilter'): return []
        
        sql = f"created_at <= '{self._format_ts(timestamp)}'"
        return self.engine._prefilter.filter(sql)

    def get_history_stats(self) -> List[Dict[str, Any]]:
        """Restituisce statistiche temporali sulla crescita del vault."""
        query = """
            SELECT 
                date_trunc('hour', created_at) as hour,
                count(*) as node_count
            FROM vault_metadata
            GROUP BY hour
            ORDER BY hour ASC
        """
        res = self.engine._prefilter.con.execute(query).fetchall()
        return [
            {"time": r[0].timestamp(), "count": r[1]}
            for r in res
        ]

    def _format_ts(self, ts: float) -> str:
        return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(ts))
