import time
import json
import os
import psutil
from pathlib import Path
from typing import Dict, List, Optional

class ModelBenchmarkTracker:
    """
    Sovereign Benchmark System v2.0
    Monitoring real-time LLM performance, system impact, and cognitive quality.
    """
    def __init__(self, vault_engine):
        self.vault = vault_engine
        self._init_db()

    def _init_db(self):
        try:
            # Upgrade table with deep telemetry columns
            self.vault._prefilter.execute("""
                CREATE TABLE IF NOT EXISTS model_benchmarks (
                    model_name VARCHAR,
                    task_type VARCHAR,
                    duration_ms DOUBLE,
                    token_count INTEGER,
                    tokens_per_sec DOUBLE,
                    ram_usage_mb DOUBLE,
                    cpu_cores_json JSON,
                    precision_score DOUBLE,
                    gen_quality DOUBLE,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
        except Exception as e:
            print(f"⚠️ [Benchmark] Error init DB: {e}")

    def record(self, model: str, task: str, duration_ms: float, token_count: int = 0, 
               ram_mb: float = 0, cpu_cores: list = None, precision: float = 0, quality: float = 0):
        tps = (token_count / (duration_ms / 1000)) if duration_ms > 0 else 0
        cpu_json = json.dumps(cpu_cores) if cpu_cores else "[]"
        
        try:
            self.vault._prefilter.execute(
                "INSERT INTO model_benchmarks (model_name, task_type, duration_ms, token_count, tokens_per_sec, ram_usage_mb, cpu_cores_json, precision_score, gen_quality) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [model, task, duration_ms, token_count, tps, ram_mb, cpu_json, precision, quality]
            )
        except Exception as e:
            print(f"⚠️ [Benchmark] Error recording: {e}")

    def get_stats(self) -> List[Dict]:
        try:
            # Enhanced stats for Recommendation Engine
            res = self.vault._prefilter.fetchdf("""
                SELECT 
                    model_name, 
                    COUNT(*) as total_tasks,
                    ROUND(AVG(duration_ms), 2) as avg_latency,
                    ROUND(AVG(tokens_per_sec), 2) as tps,
                    ROUND(AVG(ram_usage_mb) / 1024, 2) as ram,
                    ROUND(AVG(gen_quality) * 10, 1) as score,
                    MAX(tokens_per_sec) as peak_tps
                FROM model_benchmarks
                GROUP BY model_name
                ORDER BY score DESC, tps DESC
            """)
            return res.to_dict('records')
        except Exception as e:
            print(f"⚠️ [Benchmark] Stats error: {e}")
            return []

    def get_task_recommendation(self, task: str) -> Optional[Dict]:
        """Returns the best model for a specific task based on historical score."""
        try:
            res = self.vault._prefilter.execute("""
                SELECT model_name, AVG(gen_quality) as q
                FROM model_benchmarks
                WHERE task_type = ?
                GROUP BY model_name
                ORDER BY q DESC
                LIMIT 1
            """, [task]).fetchone()
            return {"model": res[0], "score": res[1]} if res else None
        except:
            return None

    def get_latest(self, limit: int = 5) -> List[Dict]:
        """Returns the most recent N benchmark records."""
        try:
            res = self.vault._prefilter.fetchdf(
                "SELECT * FROM model_benchmarks ORDER BY timestamp DESC LIMIT ?",
                [limit]
            )
            # Handle potential timestamp conversion issues if necessary, but DuckDB df usually works
            return res.to_dict('records')
        except Exception as e:
            print(f"⚠️ [Benchmark] Get latest error: {e}")
            return []

    def get_full_history(self, limit: int = 100) -> List[Dict]:
        """[Phase 4] Recupera la cronologia completa delle missioni da DuckDB."""
        try:
            res = self.vault._prefilter.fetchdf("""
                SELECT 
                    model_name, 
                    task_type as task, 
                    duration_ms as latency, 
                    tokens_per_sec as tps, 
                    ram_usage_mb as ram, 
                    gen_quality as quality,
                    epoch(timestamp) as timestamp
                FROM model_benchmarks 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, [limit])
            return res.to_dict('records')
        except Exception as e:
            print(f"⚠️ [Benchmark] History error: {e}")
            return []
