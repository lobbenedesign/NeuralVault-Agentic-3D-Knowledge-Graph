import time
import json
import os
from pathlib import Path
from typing import Dict, List, Optional

class ModelBenchmarkTracker:
    """
    Sistema di Benchmark Sovrano per il monitoraggio delle performance LLM locali.
    Traccia: Latency (ms), Throughput (tok/s), e Success Rate.
    """
    def __init__(self, vault_engine):
        self.vault = vault_engine
        self._init_db()

    def _init_db(self):
        try:
            self.vault._prefilter.con.execute("""
                CREATE TABLE IF NOT EXISTS model_benchmarks (
                    model_name VARCHAR,
                    task_type VARCHAR,
                    duration_ms DOUBLE,
                    token_count INTEGER,
                    tokens_per_sec DOUBLE,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
        except Exception as e:
            print(f"⚠️ [Benchmark] Error init DB: {e}")

    def record(self, model: str, task: str, duration_ms: float, token_count: int = 0):
        tps = (token_count / (duration_ms / 1000)) if duration_ms > 0 else 0
        try:
            self.vault._prefilter.con.execute(
                "INSERT INTO model_benchmarks (model_name, task_type, duration_ms, token_count, tokens_per_sec) VALUES (?, ?, ?, ?, ?)",
                [model, task, duration_ms, token_count, tps]
            )
        except Exception as e:
            print(f"⚠️ [Benchmark] Error recording: {e}")

    def get_stats(self) -> List[Dict]:
        try:
            res = self.vault._prefilter.con.execute("""
                SELECT 
                    model_name, 
                    COUNT(*) as total_tasks,
                    AVG(duration_ms) as avg_latency,
                    AVG(tokens_per_sec) as avg_tps,
                    MAX(tokens_per_sec) as peak_tps
                FROM model_benchmarks
                GROUP BY model_name
                ORDER BY avg_latency ASC
            """).fetchdf()
            return res.to_dict('records')
        except:
            return []
