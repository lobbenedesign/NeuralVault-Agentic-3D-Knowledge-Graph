"""
neuralvault.utils.logger
────────────────────────
Structured Logging Engine per NeuralVault v0.3.0.
Genera log in formato JSON compatibili con Prometheus/Grafana.
"""

import json
import time
import os
import resource
from pathlib import Path
from datetime import datetime
from typing import Optional

class NeuralLogger:
    """
    Motore di osservabilità strutturata.
    Traccia metriche di latenza, memoria e integrità del sistema.
    """
    def __init__(self, log_dir: Optional[Path] = None):
        self.log_dir = log_dir
        if self.log_dir:
            self.log_dir.mkdir(parents=True, exist_ok=True)
            self.log_file = self.log_dir / "neural_metrics.jsonl"
        else:
            self.log_file = None

    def info(self, message: str):
        """Logga un messaggio informativo di sistema."""
        print(f"✨ [NeuralVault] {message}")
        self.log_event("system_info", {"message": message})

    def log_event(self, event_type: str, data: dict):
        """Registra un evento strutturato."""
        raw_mem = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        mem_mb = raw_mem / (1024 * 1024) if os.uname().sysname == 'Darwin' else raw_mem / 1024
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event": event_type,
            "metrics": {
                "ram_usage_mb": round(mem_mb, 2),
                **data
            }
        }
        
        if self.log_file:
            try:
                with open(self.log_file, "a") as f:
                    f.write(json.dumps(log_entry) + "\n")
            except Exception:
                pass

    def log_query(self, intent: str, duration_ms: float, results_count: int):
        self.log_event("query_execution", {
            "intent": intent,
            "duration_ms": round(duration_ms, 3),
            "results_count": results_count
        })

    def log_ingestion(self, node_id: str, duration_ms: float):
        self.log_event("ingestion_active", {
            "node_id": node_id,
            "duration_ms": round(duration_ms, 3)
        })
