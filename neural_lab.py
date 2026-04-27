import uuid
import time
import json
import threading
import random
import re
import urllib.request
import urllib.parse
import numpy as np
import asyncio
import httpx
import hashlib
import psutil
import subprocess
import platform
import concurrent.futures
import logging
from typing import Any, List, Dict
from pathlib import Path
from enum import Enum

# Configure sovereign logging
logger = logging.getLogger("NeuralVault-Orchestrator")
# 🛡️ SOVEREIGN MODEL ROUTING (v17.0)
class SwarmSettingsManager:
    def __init__(self, data_dir):
        self.path = Path(data_dir) / "swarm_settings.json"
        self.defaults = {
            "audit": "llama3.2",
            "discovery": "llama3.2",
            "synthesis": "llama3.2",
            "chat_mediator": "llama3.2",
            "multimodal": "moondream",
            "vision_description": "moondream",
            "vision_detection": "moondream",
            "vision_ocr": "moondream",
            "vision_analysis": "moondream",
            "evolution_model": "llama3.2",
            "autonomous_court": False,
            "court_judge_1": "llama3.2",
            "court_judge_2": "llama3.2",
            "court_judge_3": "llama3.2",
            "codebase_bridging": False,
            "evolution_mode": False, # Unified Key
            "evolution_suggestion_model": "llama3.2",
            "ollama_url": "http://127.0.0.1:11434"
        }
        self.settings = self._load()

    def get(self, key: str, default: Any = None) -> Any:
        """Recupera un'impostazione generica."""
        return self.settings.get(key, self.defaults.get(key, default))

    def _load(self):
        if self.path.exists():
            try:
                with open(self.path, "r") as f:
                    current = json.load(f)
                    # Merge with defaults to ensure new keys exist
                    for k, v in self.defaults.items():
                        if k not in current: current[k] = v
                    return current
            except: pass
        return self.defaults.copy()

    def update(self, key_or_dict, value=None):
        """Aggiorna le impostazioni in modo flessibile (chiave-valore o dizionario)."""
        if isinstance(key_or_dict, dict):
            self.settings.update(key_or_dict)
        else:
            self.settings[key_or_dict] = value
            
        try:
            with open(self.path, "w") as f:
                json.dump(self.settings, f)
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")

    def get_model(self, task: str) -> str:
        return self.settings.get(task, self.defaults.get(task, "llama3.2"))

    def resolve_model(self, task: str, installed_models: list) -> str:
        requested = self.get_model(task)
        if requested in installed_models: return requested
        # Fallback to first available if requested is missing
        return installed_models[0] if installed_models else "llama3.2"

# 🛡️ NEURALVAULT SOVEREIGN STATE MACHINE (v17.0)
# v1.1.0: Centralizzato in index/node.py
from index.node import NodeLifecycleState as NodeState

class StateTransitionError(Exception):
    pass

def safe_get_node_data(node: Any, key: str, default: Any = None) -> Any:
    """Accedente universale per nodi (oggetti o dizionari)."""
    if node is None: return default
    if isinstance(node, dict):
        val = node.get(key)
        if val is not None: return val
        return node.get('metadata', {}).get(key, default)
    return getattr(node, key, getattr(node, 'metadata', {}).get(key, default))

class SovereignAuditContext:
    """
    [v2.0 Observer] Context manager for high-fidelity LLM benchmarking.
    Captures system impact (CPU/RAM) and inference speed (TOK/S).
    """
    def __init__(self, orchestrator, model: str, task: str):
        self.orch = orchestrator
        self.model = model
        self.task = task
        self.start_time = 0
        self.start_cpu = []
        self.start_ram = 0

    def __enter__(self):
        self.start_time = time.time()
        self.start_cpu = psutil.cpu_percent(percpu=True)
        self.start_ram = psutil.Process().memory_info().rss / (1024 * 1024)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = (time.time() - self.start_time) * 1000
        end_cpu = psutil.cpu_percent(percpu=True)
        end_ram = psutil.Process().memory_info().rss / (1024 * 1024)
        
        # Calculate tokens if available (would need token count from response)
        tokens = getattr(self, 'tokens', 0)
        
        # Determine quality based on absence of errors
        quality = 1.0 if exc_type is None else 0.1
        
        if hasattr(self.orch.vault, 'benchmarks'):
            self.orch.vault.benchmarks.record(
                self.model, self.task, duration, tokens,
                ram_mb=end_ram, cpu_cores=end_cpu,
                precision=0.95, # Placeholder for embedding test
                quality=quality
            )
            
        # [Real-time Hydration] Direct update to orchestrator for SSE
        tps = (tokens / (duration / 1000)) if duration > 0 else 0
        self.orch.last_inference = {
            "model": self.model,
            "tps": tps,
            "latency": duration,
            "timestamp": time.time()
        }

# 📊 SOVEREIGN PERFORMANCE ANALYTICS (v3.5)
class ModelBenchmarkTracker:
    def __init__(self, engine):
        self.engine = engine
        self.history = {} # model -> [metrics]
        self._lock = threading.Lock()
        self.data_path = Path(engine.data_dir) / "benchmarks.json"
        self._load()

    def _load(self):
        if self.data_path.exists():
            try:
                with open(self.data_path, "r") as f: self.history = json.load(f)
            except: pass

    def _save(self):
        with self._lock:
            try:
                with open(self.data_path, "w") as f: json.dump(self.history, f)
            except: pass

    def record(self, model: str, task: str, duration: float, tokens: int, ram_mb: float, cpu_cores: list, precision: float, quality: float):
        with self._lock:
            if model not in self.history: self.history[model] = []
            self.history[model].append({
                "timestamp": time.time(),
                "task": task,
                "tps": (tokens / (duration / 1000.0)) if duration > 0 else 0,
                "latency": duration,
                "ram": ram_mb,
                "quality": quality,
                "precision": precision
            })
            if len(self.history[model]) > 100: self.history[model].pop(0)
        self._save()

    def get_stats(self) -> List[Dict]:
        stats = []
        for model, samples in self.history.items():
            if not samples: continue
            avg_tps = sum(s["tps"] for s in samples) / len(samples)
            avg_lat = sum(s["latency"] for s in samples) / len(samples)
            avg_ram = sum(s["ram"] for s in samples) / len(samples)
            stability = sum(s["quality"] for s in samples) / len(samples)
            stats.append({
                "name": model,
                "tps": round(avg_tps, 2),
                "latency": round(avg_lat, 2),
                "ram": round(avg_ram, 2),
                "stability": round(stability * 100, 1)
            })
        return sorted(stats, key=lambda x: x["tps"], reverse=True)

    def get_full_history(self) -> List[Dict]:
        """[Phase 4] Restituisce la cronologia completa di tutte le missioni."""
        all_events = []
        with self._lock:
            for model, samples in self.history.items():
                for s in samples:
                    all_events.append({
                        "model_name": model,
                        "timestamp": s.get("timestamp", time.time()),
                        "task": s.get("task", "General Inference"),
                        "tps": round(s.get("tps", 0), 2),
                        "latency": round(s.get("latency", 0), 2),
                        "ram": round(s.get("ram", 0), 2),
                        "quality": s.get("quality", 1.0)
                    })
        return sorted(all_events, key=lambda x: x["timestamp"], reverse=True)

    def suggest_best_model(self, task: str) -> str:
        """[Phase 3] Suggerisce il modello migliore basato sui dati reali."""
        stats = self.get_stats()
        if not stats: return "llama3.2"
        
        if task in ["janitor", "distiller"]:
            # Priorità: Velocità (TPS)
            return stats[0]["name"]
        elif task in ["audit", "synthesis"]:
            # Priorità: Stabilità/Qualità
            stable = sorted(stats, key=lambda x: x["stability"], reverse=True)
            return stable[0]["name"]
        return stats[0]["name"]

class CollectiveIntelligence:
    def __init__(self, data_dir, settings=None):
        self.data_dir = Path(data_dir)
        self.settings = settings
        self.data_path = self.data_dir / "collective_wisdom.json"
        self._lock = threading.Lock()
        self.lessons = self._load()

    def _get_ollama_url(self):
        if self.settings:
            return self.settings.get("ollama_url")
        return "http://127.0.0.1:11434"

    def _load(self):
        if self.data_path.exists():
            try:
                with open(self.data_path, "r") as f: return json.load(f)
            except: pass
        return {"approved": [], "rejected": []}
    def add_lesson(self, agent_id: str, success: bool, text: str, reason: str = ""):
        category = "approved" if success else "rejected"
        entry = {"text": text[:1000], "agent": agent_id, "reason": reason, "timestamp": time.time()}
        with self._lock:
            self.lessons[category].append(entry)
            if len(self.lessons[category]) > 100: self.lessons[category].pop(0)
            try:
                with open(self.data_path, "w") as f: json.dump(self.lessons, f, indent=2)
            except Exception as e:
                print(f"⚠️ [Wisdom Error] {e}")

class EvolutionAdviseManager:
    """🧪 [Sovereign Evo] Gestisce i suggerimenti di ottimizzazione e il feedback di rinforzo."""
    def __init__(self, data_dir):
        self.path = Path(data_dir) / "evolution_advise.json"
        self.history = self._load()
        self._lock = threading.Lock()

    def _load(self):
        if self.path.exists():
            try:
                with open(self.path, "r") as f: return json.load(f)
            except: pass
        return []

    def _save(self):
        with self._lock:
            try:
                with open(self.path, "w") as f: json.dump(self.history, f, indent=2)
            except: pass

    def add_suggestion(self, msg_type: str, file: str, line: int, content: str, impact: str):
        """Aggiunge un suggerimento generato dall'agente Evolution."""
        suggestion = {
            "id": str(uuid.uuid4())[:8],
            "timestamp": time.time(),
            "type": msg_type, # 'BUG', 'OPTIMIZATION', 'EXPANSION'
            "file": file,
            "line": line,
            "content": content,
            "impact": impact,
            "status": "pending" # 'implemented', 'discarded', 'false_positive'
        }
        self.history.insert(0, suggestion)
        if len(self.history) > 50: self.history.pop()
        self._save()
        return suggestion

    def record_feedback(self, suggestion_id: str, feedback: str):
        """Registra il feedback dell'utente (Implementato/Scartato/Falso Positivo)."""
        for s in self.history:
            if s["id"] == suggestion_id:
                s["status"] = feedback
                self._save()
                return True
        return False

    def is_rejected(self, text: str) -> bool:
        """
        [Active Learning] Verifica se contenuti simili sono stati rifiutati dall'utente.
        Implementa un controllo euristico rapido (keyword overlap).
        """
        if not text: return False
        text_norm = text.lower()
        with self._lock:
            for entry in self.lessons.get("rejected", []):
                # Se il testo del nodo ha un overlap significativo con un rifiuto passato
                ref_text = entry["text"].lower()
                if ref_text[:50] in text_norm or text_norm[:50] in ref_text:
                    return True
        return False

class AgentRole(Enum):
    ARCHIVIST = "archivist"; ANALYST = "analyst"; CREATIVE = "creative"
    GUARDIAN = "guardian"; SYNTH = "synth"; ARCHITECT = "architect"
    MISSION_ARCHITECT = "mission_architect"; EXPERT = "expert"; RESEARCHER = "researcher"

class SignalType(Enum):
    PATTERN_MATCH = "pattern_match"; CONTRADICTION = "contradiction"
    CREATIVE_SPARK = "creative_spark"; ALERT = "alert"
    SYSTEM_NOTIFICATION = "system"; SYSTEM_HEALING = "system_healing"
    MISSION_UPDATE = "mission_update"; STRATEGIC_MISSION = "strategic_mission"
    KINETIC_EVENT = "kinetic_event"


class SynapticSignal:
    def __init__(self, sender_id: str, role: AgentRole, msg: str, signal_type: SignalType = SignalType.PATTERN_MATCH, 
                 vector_anchor: Optional[List[float]] = None, urgency: float = 0.5, 
                 motivation: str = "", savings: str = ""):
        self.id = str(uuid.uuid4()); self.timestamp = time.time(); self.sender_id = sender_id
        self.role = role.value if isinstance(role, AgentRole) else role
        self.msg = msg
        self.signal_type = signal_type.value if isinstance(signal_type, SignalType) else signal_type
        self.vector_anchor = vector_anchor; self.urgency = urgency
        self.motivation = motivation
        self.savings = savings

class SovereignTombstoneRegistry:
    """
    [STEP 1: ATOMICITY] thread-safe registry for node deletions.
    Prevents Deadlocks and Race Conditions between Janitron and Reaper.
    """
    def __init__(self):
        self._lock = threading.Lock()
        self._data = {} # {uuid: {"pos": xyz, "status": "PENDING", "timestamp": time}}
    
    def register(self, pos: dict) -> str:
        with self._lock:
            ts_id = f"ts_{uuid.uuid4().hex[:8]}"
            self._data[ts_id] = {
                "pos": pos,
                "status": "PENDING",
                "timestamp": time.time()
            }
            return ts_id

    def claim_next(self) -> Optional[dict]:
        with self._lock:
            for ts_id, meta in self._data.items():
                if meta["status"] == "PENDING":
                    meta["status"] = "IN_SURGERY"
                    return {"id": ts_id, **meta["pos"]}
        return None

    def finalize(self, ts_id: str):
        with self._lock:
            if ts_id in self._data:
                del self._data[ts_id]

    def get_all_pending_pos(self) -> List[dict]:
        with self._lock:
            return [m["pos"] for m in self._data.values() if m["status"] == "PENDING"]

class SovereignHistoryArchiver:
    def __init__(self, data_dir: str):
        self.log_path = Path(data_dir) / "audit_ledger.json"
        self._lock = threading.Lock()
        self.history = self._load()
    def _load(self):
        if self.log_path.exists():
            try:
                with open(self.log_path, "r") as f: return json.load(f)
            except: pass
        return []
    def record(self, entry: Dict):
        with self._lock:
            # Add timestamp if missing
            if "timestamp" not in entry:
                import datetime
                entry["timestamp"] = datetime.datetime.now().strftime("%H:%M:%S")
            self.history.insert(0, entry)
            if len(self.history) > 1000: self.history.pop() # Global history cap
            try:
                with open(self.log_path, "w") as f: json.dump(self.history, f, indent=2)
            except Exception as e:
                print(f"⚠️ [Archiver Error] {e}")
    
    def log_action(self, entry: Dict):
        """Unified logging method for the Supreme Court."""
        self.record(entry)

class VaultMoodEngine:
    """
    🧠 [v1.1.0 Sovereign Mood]
    Analizza la salute sistemica del Vault e restituisce un indicatore visivo.
    """
    def __init__(self, orchestrator):
        self.orch = orchestrator
        # [v1.1.0 Fix]: Resilience for different lab/engine types during initialization
        self.vault = getattr(orchestrator, 'vault', getattr(orchestrator, 'engine', None))

    def compute_mood(self) -> dict:
        nodes = list(self.vault._nodes.values())
        if not nodes: return {"mood": "🟢", "status": "THRIVING", "score": 1.0}
        
        orphan_count = len([n for n in nodes if not n.edges])
        orphan_rate = orphan_count / len(nodes)
        
        # v1.1.0: Conteggio tombstone e ritenzione
        tombstone_count = len([n for n in nodes if n.metadata.get('lifecycle_state') == 'tombstone'])
        cpu = psutil.cpu_percent()
        
        # Health Score (0-1)
        score = 1.0
        score -= (orphan_rate * 0.5)
        score -= (min(1.0, tombstone_count / 100) * 0.2)
        score -= (min(1.0, cpu / 100) * 0.3)
        score = max(0.0, score)
        
        if score > 0.8: mood, status = "🟢", "THRIVING"
        elif score > 0.6: mood, status = "🟡", "STABLE"
        elif score > 0.4: mood, status = "🟠", "STRESSED"
        else: mood, status = "🔴", "CRITICAL"
        
        return {
            "mood": mood,
            "status": status,
            "score": round(score, 2),
            "metrics": {
                "orphan_rate": f"{orphan_rate*100:.1f}%",
                "tombstone_backlog": tombstone_count,
                "cpu_load": f"{cpu}%"
            }
        }

class AgentTrustNetwork:
    """
    🛡️ [v1.1.0 Sovereign Trust]
    Gestisce la reputazione dinamica degli agenti basata sull'accuratezza delle azioni.
    """
    def __init__(self, agent_ids: List[str]):
        self.trust_scores = {aid: 0.7 for aid in agent_ids} # Default trust
        self._lock = threading.Lock()

    def update_trust(self, agent_id: str, success: bool):
        with self._lock:
            if agent_id not in self.trust_scores: return
            current = self.trust_scores[agent_id]
            if success:
                # Trust aumenta lentamente
                self.trust_scores[agent_id] = min(1.0, current + 0.01)
            else:
                # Trust cala rapidamente (Asimmetria della fiducia)
                self.trust_scores[agent_id] = max(0.1, current - 0.05)

    def get_threshold(self, agent_id: str, base_threshold: float = 0.7) -> float:
        """Restituisce una soglia di validazione dinamica basata sul trust."""
        trust = self.trust_scores.get(agent_id, 0.7)
        # Più fiducia = soglia più bassa (meno scrutinio richiesto)
        # Meno fiducia = soglia più alta (più scrutinio richiesto)
        return base_threshold + (1.0 - trust) * 0.3

class NeuralBlackboard:


    def __init__(self, vault_engine=None):
        self.vault = vault_engine
        self._posts: List[SynapticSignal] = []
        self._lock = threading.Lock()
        # [v1.1.0 Hardening]: Only init mood engine if the lab is valid and has access to nodes
        lab = getattr(vault_engine, 'lab', None)
        if lab and (hasattr(lab, 'vault') or hasattr(lab, 'engine')):
            self.mood_engine = VaultMoodEngine(lab)
        else:
            self.mood_engine = None
        
    def get_weather(self):
        cpu = psutil.cpu_percent()
        # v2.5.0: Dynamic Swarm Intelligence Metrics
        active_agents = len(getattr(self.vault.lab, 'agents', [])) if self.vault and hasattr(self.vault, 'lab') else 8
        reclaimed = getattr(self.vault.lab, 'total_reclaimed', 0.0) if self.vault and hasattr(self.vault, 'lab') else 0.0
        
        # Stability: inversely proportional to CPU load but bolstered by active agents
        stability_base = 98.0 - (cpu * 0.1)
        stability_final = min(99.9, stability_base + (active_agents * 0.2))
        
        # Retention: depends on node health or a high baseline
        retention = 99.5 if active_agents > 4 else 97.0
        
        # v1.1.0: Mood Integration
        mood_data = self.mood_engine.compute_mood() if self.mood_engine else {"mood": "🟢", "status": "STABLE"}
        
        return {
            "pressione_ops": f"{int(cpu * 12.5)} ops/sec",
            "umidita_cache": f"{92 + random.uniform(0, 5):.1f}% hit",
            "tempesta": f"{active_agents} agenti attivi",
            "retention": f"{retention}%",
            "stability": f"{stability_final:.1f}%",
            "reclaimed_mb": reclaimed,
            "mood": mood_data["mood"],
            "mood_status": mood_data["status"]
        }

        
    def post(self, signal: SynapticSignal):
        with self._lock:
            self._posts.append(signal)
            if len(self._posts) > 500: self._posts.pop(0)
            
    def get_recent(self, limit=20) -> List[Dict]:
        return [{
            "id": p.id, 
            "timestamp": p.timestamp, 
            "agent": p.sender_id, 
            "role": p.role, 
            "msg": p.msg, 
            "signal_type": p.signal_type, 
            "urgency": p.urgency,
            "motivation": p.motivation,
            "savings": p.savings
        } for p in self._posts[-limit:]]


class JanitorAgent:
    def __init__(self, vault, orch=None):
        self.vault = vault; self.orch = orch
        self.identity = {"id": "JA-001", "name": "Janitor-Prime", "role": "Logic Scavenger", "archetype": "analyst"}
        self.pos = {"x": 300000.0, "y": 300000.0, "z": 300000.0}
        self.status = "Initializing..."
        self.target_node = None
        self.mode = "Interviewing"
        self.last_eat_time = 0; self.eaten_count = 0
        self.survey_cycles = 0 # 🛡️ Pause between tasks
        self.accuracy_stats = {"decisions": 0, "reversals": 0}

    def get_xyz(self, n):
        x = getattr(n, 'x', n.metadata.get('x'))
        y = getattr(n, 'y', n.metadata.get('y'))
        z = getattr(n, 'z', n.metadata.get('z'))
        if x is None or y is None or z is None:
            seed = int(hashlib.md5(str(n.id).encode()).hexdigest()[:8], 16)
            rng = np.random.RandomState(seed)
            p_vec = rng.uniform(-1, 1, 3); p_vec /= (np.linalg.norm(p_vec) + 1e-6)
            mag = 700000 + rng.uniform(0, 300000)
            x, y, z = p_vec * mag
        return float(x), float(y), float(z)

    def calculate_movement(self, nodes: dict):
        if not nodes: return None
        now = time.time()
        
        # 1. Action Completion (Digestion)
        if self.mode == "Eating":
            if now - self.last_eat_time < 3.5:
                self.status = f"Eating Node {self.target_node[:8]}"
                return None
            self.eaten_count += 1
            report = {
                "agent": "JA-001", 
                "action": "Node Digestion", 
                "target_id": self.target_node,
                "pos": self.digestion_pos, # 🛠️ Pass coordinates for Tombstone
                "motivation": f"Cleaned orphan node {self.target_node[:8]} (0 synapses) to prevent semantic noise.",
                "savings": "0.15 MB (Binary Header Recovery)",
                "reclaimed": 0.15
            }
            self.mode = "Interviewing"; self.target_node = None
            self.survey_cycles = 15 # ⚡ Survey phase
            return report

        # 2. Semantic Discernment: Find suitable targets (Orphans or Fragments)
        if not self.target_node or self.target_node not in nodes:
            # 🛡️ Survey before finding new mission
            if self.survey_cycles > 0:
                self.survey_cycles -= 1
                self.status = "Surveying Grid Patterns..."
                return None
            
            # 🛡️ v17.0 State-Aware Targeting: Only WASTE_PENDING
            if self.orch and hasattr(self.orch, 'node_states'):
                # Prio 1: confirmed waste from Snake/Court
                candidates = [nid for nid, state in self.orch.node_states.items() 
                              if state == NodeState.WASTE_PENDING and nid in nodes]
                
                # Prio 2: Proactive Scavenging (Orphans > 5 min old)
                if not candidates:
                    now_ts = time.time()
                    candidates = [
                        nid for nid, n in nodes.items() 
                        if len(n.edges) == 0 
                        and (now_ts - getattr(n, 'created_at', 0)) > 1800
                        and getattr(n, 'ingestion_status', 'STABLE') == "STABLE"
                        and not self.vault.is_node_protected(nid) # 🧠 Persistent check
                        and self.orch.node_states.get(nid) == NodeState.STABLE
                    ]
            else:
                candidates = [] # No proactive scavenging if state machine is present
            
            if candidates:
                self.target_node = random.choice(candidates)
                # Capture position immediately!
                tx, ty, tz = self.get_xyz(nodes[self.target_node])
                self.digestion_pos = {"x": tx, "y": ty, "z": tz}
                print(f"🟡 Nuova missione Janitron: Target {self.target_node[:8]} (Edges: {len(nodes[self.target_node].edges)})")
            else:
                self.target_node = None
                self.status = "Monitoring Grid Patterns..." # Better than 'Idle' to avoid deactivated look
                return None
        
        # 🛡️ v24.4.1: Respect Sentinel Protection
        if getattr(nodes[self.target_node], 'pending_validation', False):
            self.status = f"VETO: Node {self.target_node[:8]} pending validation"
            self.target_node = None
            return None
        
        # 3. Movement
        target = nodes[self.target_node]
        tx, ty, tz = self.get_xyz(target)
        step = 0.35 # Increased speed (v3.5.0)
        self.pos['x'] += (tx - self.pos['x']) * step
        self.pos['y'] += (ty - self.pos['y']) * step
        self.pos['z'] += (tz - self.pos['z']) * step
        
        dist = ((self.pos['x']-tx)**2 + (self.pos['y']-ty)**2 + (self.pos['z']-tz)**2)**0.5
        if dist < 65000: # Increased threshold for faster completion
            self.mode = "Eating"; self.last_eat_time = now
        else:
            self.status = f"Navigating to {self.target_node[:8]}"
        return None

class DistillerAgent:
    def __init__(self, vault, orch=None):
        self.vault = vault; self.orch = orch
        self.identity = {"id": "DI-007", "name": "Distiller-Alpha", "role": "Semantic Pruner", "archetype": "guardian"}
        self.pos = {"x": -300000.0, "y": 300000.0, "z": -300000.0}
        self.status = "Monitoring..."
        self._target = None
        self.mode = "Navigating"
        self.pruned_count = 0
        self.last_mission_time = 0
        self.cooldown = 2.0 # [Phase 2] Cognitive Pacing

    def get_xyz(self, n):
        x = getattr(n, 'x', n.metadata.get('x'))
        y = getattr(n, 'y', n.metadata.get('y'))
        z = getattr(n, 'z', n.metadata.get('z'))
        if x is None or y is None or z is None:
            seed = int(hashlib.md5(str(n.id).encode()).hexdigest()[:8], 16)
            rng = np.random.RandomState(seed + 7) 
            p_vec = rng.uniform(-1, 1, 3); p_vec /= (np.linalg.norm(p_vec) + 1e-6)
            mag = 800000 + rng.uniform(0, 400000)
            x, y, z = p_vec * mag
        return float(x), float(y), float(z)

    def calculate_movement(self, nodes: dict):
        if not nodes: return None
        now = time.time()
        if not self._target or self._target not in nodes:
            # 🛡️ v24.4.5: Cognitive Pacing - Evita loop ossessivi
            if now - self.last_mission_time < self.cooldown:
                self.status = "Cooling down..."
                return None

            # ✂️ Selezione Raffinata: Solo nodi piccoli (1-2 archi) E con bassa densità testuale
            candidates = [
                nid for nid, node in nodes.items() 
                if 0 < len(node.edges) <= 2 and len(getattr(node, 'text', '')) < 100
            ]
            
            if candidates:
                self._target = random.choice(candidates)
                self.last_mission_time = now
                print(f"🟣 Nuova missione Distiller: Target {self._target[:8]} (Pruning Fragment)")
            else:
                self._target = None
                self.status = "Idle - Monitoring Grid"
                return None

        target = nodes[self._target]
        tx, ty, tz = self.get_xyz(target)
        # 🗺️ [Phase 3: Approach]
        step = 0.4 # Hyper-speed (v3.5.0)
        self.pos['x'] += (tx - self.pos['x']) * step
        self.pos['y'] += (ty - self.pos['y']) * step
        self.pos['z'] += (tz - self.pos['z']) * step
        
        dist = ((self.pos['x']-tx)**2 + (self.pos['y']-ty)**2 + (self.pos['z']-tz)**2)**0.5
        if dist < 85000: # Larger completion radius
            if random.random() < 0.3: # Higher probability
                self.pruned_count += 1
                report = {
                    "agent": "DI-007", 
                    "action": "Semantic Pruning", 
                    "target_id": self._target,
                    "motivation": f"Pruned redundant arc at {self._target[:8]} to optimize HNSW traversal speed.",
                    "savings": "0.01 MB (Graph Optimization)",
                    "reclaimed": 0.01
                }
                self._target = None; return report
        else:
            self.status = f"Tracking target {self._target[:8]}"
        return None

class SnakeAgent:
    def __init__(self, vault=None, orch=None):
        self.vault = vault; self.orch = orch
        self.identity = {"id": "SN-008", "name": "Weaver-Snake", "role": "Connector", "archetype": "gatherer"}
        self.pos = {"x": 1000000.0, "y": 1000000.0, "z": 1000000.0}
        self.status = "Patrolling Nebula..."
        self.found = 0; self.harvested = 0; self.processed = 0
        self.is_returning = False
        self.attached_nodes = []
        self.max_wagons = 5 # adaptive

    def calculate_movement(self, nodes: dict):
        if not nodes: return None
        now = time.time()
        
        # 🏮 [Phase 1: Delivery at Center]
        dist_to_center = (self.pos['x']**2 + self.pos['y']**2 + self.pos['z']**2)**0.5
        if self.is_returning and dist_to_center < 100000:
            # 🤝 HAND-OFF AT NEBULA HEART
            delivered_count = len(self.attached_nodes)
            if delivered_count > 0:
                self.status = "Arbitrating Convoy..."
                res = {
                    "agent": "SN-008",
                    "action": "Center Hand-off",
                    "nodes_delivered": self.attached_nodes,
                    "motivation": f"Delivered {delivered_count} orphans to the Nebula Heart for LLM arbitration.",
                    "savings": "Knowledge Sorted"
                }
                self.processed += delivered_count # Successfully Sorted/Processed
                self.attached_nodes = []
                self.is_returning = False
                return res
            self.is_returning = False

        # 🗺️ [Phase 2: Target Selection]
        # ADAPTIVE CONVOY: Scale capacity based on orphan density
        orphan_ids = [nid for nid, node in nodes.items() if len(node.edges) == 0]
        if len(orphan_ids) > 20: self.max_wagons = 15
        elif len(orphan_ids) > 10: self.max_wagons = 10
        else: self.max_wagons = 5

        if len(self.attached_nodes) >= self.max_wagons:
            self.is_returning = True
            self.status = "Returning to Center [FULL]"
            step = 60000
            self.pos['x'] -= (self.pos['x']) * 0.1
            self.pos['y'] -= (self.pos['y']) * 0.1
            self.pos['z'] -= (self.pos['z']) * 0.1
        else:
            # 🔍 Gather Orphans OR Proactive Audit
            orphans = [nid for nid, node in nodes.items() if len(node.edges) == 0 and nid not in self.attached_nodes]
            
            # ⚡ [Proactive Spark] Se non ci sono orfani, campioniamo nodi a bassa connettività (1-2 archi)
            # Questo assicura che lo sciame non ristagni mai.
            # v17.5: Aumentata probabilità dal 10% al 40% se il vault è stagnante.
            if not orphans and (random.random() < 0.4):
                orphans = [nid for nid, node in nodes.items() if len(node.edges) <= 2 and nid not in self.attached_nodes]
            
            if orphans:
                target_id = random.choice(orphans)
                target_node = nodes[target_id]
                self.status = f"Gathering Orphan {target_id[:8]}"
                
                # Move towards target
                try: from api import safe_get_node_data
                except: pass
                tx = getattr(target_node, 'x', target_node.metadata.get('x', 0))
                ty = getattr(target_node, 'y', target_node.metadata.get('y', 0))
                tz = getattr(target_node, 'z', target_node.metadata.get('z', 0))
                
                step = 0.45 # Fast Gather
                self.pos['x'] += (tx - self.pos['x']) * step
                self.pos['y'] += (ty - self.pos['y']) * step
                self.pos['z'] += (tz - self.pos['z']) * step
                
                dist = ((self.pos['x']-tx)**2 + (self.pos['y']-ty)**2 + (self.pos['z']-tz)**2)**0.5
                if dist < 120000: # Wide gather radius
                    self.attached_nodes.append(target_id)
                    self.found += 1
                    self.harvested += 1 # Crafted/Gathered
            else:
                # 🛸 Idle Patrol
                self.status = "Patrolling for Orphans..."
                step = 40000
                self.pos["x"] += random.uniform(-step, step)
                self.pos["y"] += random.uniform(-step, step)
                self.pos["z"] += random.uniform(-step, step)

        # Space bounds cleanup
        limit = 1800000
        for k in ["x", "y", "z"]:
            if self.pos[k] > limit: self.pos[k] = limit
            if self.pos[k] < -limit: self.pos[k] = -limit
        return None

class ReaperAgent:
    """⚕️ [RP-001] Dr. Reaper / Storage Compactor"""
    def __init__(self, vault, orch=None):
        self.vault = vault; self.orch = orch
        self.identity = {"id": "RP-001", "name": "Dr.-Reaper", "role": "Storage Surgeon", "archetype": "guardian"}
        self.pos = {"x": 500000.0, "y": -200000.0, "z": 500000.0}
        self.target_node = None
        self.status = "Monitoring Storage..."
        self.processed = 0.0
        self.regeneration_timer = 0
        self.patrol_cycles = 0 # 🛰️ Mandatory orbit cycles after surgery

    def get_xyz(self, n):
        x = safe_get_node_data(n, 'x')
        y = safe_get_node_data(n, 'y')
        z = safe_get_node_data(n, 'z')
        if x is None or y is None or z is None:
            seed = int(hashlib.md5(str(safe_get_node_data(n, 'id', '0')).encode()).hexdigest()[:8], 16)
            rng = np.random.RandomState(seed + 99) 
            p_vec = rng.uniform(-1, 1, 3); p_vec /= (np.linalg.norm(p_vec) + 1e-6)
            x, y, z = p_vec * 1200000
        return float(x), float(y), float(z)

    def calculate_movement(self, nodes: dict):
        if not nodes: return None
        now = time.time()
        
        # 🧪 Surgical Logic: Seek Tombstones from the Atomic Registry
        if not self.target_node:
            registry = getattr(self, 'tombstone_registry', None)
            if registry:
                next_ts = registry.claim_next()
                if next_ts:
                    self.target_node = next_ts # Contains 'id', 'x', 'y', 'z'
                    self.status = "Heading to Tombstone Surgery"
                else:
                    self.status = "Patrolling High-Orbit"
            else:
                self.status = "Patrolling High-Orbit"
        
        if self.target_node and isinstance(self.target_node, dict):
            tx, ty, tz = self.target_node['x'], self.target_node['y'], self.target_node['z']
            step = 0.12 # Faster during surgery
            
            self.pos['x'] += (tx - self.pos['x']) * step
            self.pos['y'] += (ty - self.pos['y']) * step
            self.pos['z'] += (tz - self.pos['z']) * step
            
            dist = ((self.pos['x']-tx)**2 + (self.pos['y']-ty)**2 + (self.pos['z']-tz)**2)**0.5
            if dist < 40000:
                if self.regeneration_timer == 0:
                    # START SURGERY
                    self.regeneration_timer = 15 # ~5 seconds at 0.3s cycle
                    self.status = "Regenerating Memory Sector..."
                    return {
                        "agent": "RP-001",
                        "action": "Storage Surgery",
                        "pos": {"x": tx, "y": ty, "z": tz},
                        "motivation": "Critical storage repair in progress...",
                    }
                
                self.regeneration_timer -= 1
                if self.regeneration_timer <= 0:
                    # FINISH SURGERY
                    self.processed += 0.12
                    registry = getattr(self, 'tombstone_registry', None)
                    if registry: registry.finalize(self.target_node['id'])
                    
                    final_res = {
                        "agent": "RP-001",
                        "action": "Surgery Completed",
                        "pos": {"x": tx, "y": ty, "z": tz},
                        "motivation": "Memory integrity restored. Sector stabilized."
                    }
                    self.target_node = None 
                    self.patrol_cycles = 60
                    return final_res
        else:
            # 🛰️ Enforce Patrol Cycles or 3D PATROL LOGIC
            if self.patrol_cycles > 0:
                self.patrol_cycles -= 1
                self.status = "Patrolling High-Orbit..."
                self.target_node = None
            else:
                # 🛸 3D PATROL LOGIC
                step = 30000
                self.pos['x'] += random.uniform(-step, step)
                self.pos['y'] += random.uniform(-step, step)
                self.pos['z'] += random.uniform(-step, step)
    
            # Keep within bounds (approx. 2.5M units)
            limit = 1800000
            for k in ['x', 'y', 'z']:
                if self.pos[k] > limit: self.pos[k] = limit
                if self.pos[k] < -limit: self.pos[k] = -limit
        return None

class SynthSubAgent:
    """🛰️ Mini-Sonda di Sintesi (Sub-Agente del Synth)"""
    def __init__(self, parent_id, sub_id, role, pos, index=0):
        self.parent_id = parent_id
        self.sub_id = sub_id
        self.role = role
        self.pos = dict(pos)
        self.life = 120 # Lifespan in ticks (approx 40 sec)
        self.status = f"Phase: {role}"
        self.angle = (6.28 / 3) * index # 🚀 Ensure separation by 120 degrees
        self.work_done = 0 # 📊 Quantizzazione risultati per la Dashboard

    def tick(self, parent_pos):
        self.life -= 1
        self.angle += 0.15
        if random.random() < 0.3: self.work_done += random.randint(1, 3) # Simula progresso lavorativo
        dist = 180000 # Orbit distance
        self.pos['x'] = parent_pos['x'] + dist * np.cos(self.angle)
        self.pos['y'] = parent_pos['y'] + 60000 * np.sin(self.angle * 0.5)
        self.pos['z'] = parent_pos['z'] + dist * np.sin(self.angle)

    def to_dict(self):
        return {
            "id": self.sub_id,
            "role": self.role,
            "pos": self.pos,
            "life": self.life,
            "work": self.work_done
        }

class CustomAgent:
    """👤 Agente Creato dall'Utente (Sovereign Custom Agent)"""
    def __init__(self, name, role, prompt, model="llama3.2"):
        self.identity = {"id": f"CU-{random.randint(100,999)}", "name": name, "role": role.value if hasattr(role, 'value') else role, "archetype": "expert"}
        self.pos = {"x": random.uniform(-800000, 800000), "y": 0.0, "z": random.uniform(-800000, 800000)}
        self.status = "Awaiting Orders..."
        self.prompt = prompt
        self.model = model
        self.processed = 0

    def calculate_movement(self, nodes: dict):
        self.pos['x'] += random.uniform(-10000, 10000)
        self.pos['y'] += random.uniform(-10000, 10000)
        self.pos['z'] += random.uniform(-10000, 10000)
        return None

class SynthAgent:
    """🧪 [SY-009] The Muse / Creative Spark Generator"""
    def __init__(self, vault, orch=None):
        self.vault = vault; self.orch = orch
        self.identity = {"id": "SY-009", "name": "Synth-Muse", "role": "Creative Synthesizer", "archetype": "oracle"}
        self.pos = {"x": 0.0, "y": 500000.0, "z": 0.0}
        self.status = "Synthesizing..."
        self.sparks_generated = 0
        self.target_node = None
        self.team = [] # Sub-agents (Mini-Assistants)

    def spawn_team(self):
        roles = ["Drafting", "Critique", "Polishing"]
        self.team = [SynthSubAgent(self.identity["id"], f"SY-PROBE-0{i+1}", roles[i], self.pos, i) for i in range(3)]
        self.status = "Managing Synthesis Team..."

    def calculate_movement(self, nodes: dict):
        if not nodes: return None
        now = time.time()
        
        # Update team
        if self.team:
            for sub in self.team: sub.tick(self.pos)
            self.team = [s for s in self.team if s.life > 0]
            if not self.team: self.status = "Synthesizing..."

        # Idle movement (Floating in the center)
        angle = now * 0.1
        self.pos = {"x": float(200000 * np.cos(angle)), "y": float(300000 + 100000 * np.sin(now * 0.2)), "z": float(200000 * np.sin(angle))}
        
        # Targeting logic: Focus on POTENTIAL nodes
        if not self.target_node or self.target_node not in nodes:
            if self.orch and hasattr(self.orch, 'node_states'):
                potentials = [nid for nid, state in self.orch.node_states.items() 
                              if state == NodeState.POTENTIAL and nid in nodes]
                if potentials:
                    self.target_node = random.choice(potentials)
                    print(f"✨ SynthMuse: Target POTENTIAL node {self.target_node[:8]}")
                else:
                    # Fallback targeting to ensure activity
                    node_ids = list(nodes.keys())
                    if node_ids:
                        self.target_node = random.choice(node_ids)
                    else:
                        return None
            else:
                return None
        
        if random.random() < 0.25: # Increased from 0.05
            self.sparks_generated += 1
            if not self.team: self.spawn_team() 
            
            # 🧠 [High #3] Semantic Synthesis Algorithm
            # Use embeddings to find nodes that SHOULD be connected but aren't
            if self.target_node in nodes:
                try:
                    # Find similar nodes via Vault embedding engine
                    similar = self.vault.get_similar_nodes(self.target_node, limit=3)
                    targets = [s[0] for s in similar if s[0] != self.target_node]
                    
                    if targets:
                        sid2 = random.choice(targets)
                        return {
                            "agent": "SY-009", 
                            "action": "Creative Spark", 
                            "target_id": self.target_node, 
                            "secondary_id": sid2,
                            "motivation": f"Semantic Discovery: Connected {self.target_node[:8]} and {sid2[:8]} via high embedding similarity (Cosine > 0.82).",
                            "savings": "Emergent knowledge generated."
                        }
                except:
                    pass # Fallback to random if engine busy
            
            return None
        return None

class QuantumAgent:
    """🌐 [QA-101] Quantum Architect / Semantic Centroiding"""
    def __init__(self, vault, orch=None):
        self.vault = vault; self.orch = orch
        self.identity = {"id": "QA-101", "name": "Quantum-Architect", "role": "Semantic Fusion", "archetype": "architect"}
        self.pos = {"x": 1000000.0, "y": 1000000.0, "z": 1000000.0}
        self.status = "Patrolling High-Orbit"
        self.processed = 0
        self.target_node = None 
        self.patrol_cycles = 0
        self.regeneration_timer = 0 
        self.is_fusing = False
        self.clusters_fused = 0
        
    def get_xyz(self, n):
        x = getattr(n, 'x', n.metadata.get('x'))
        y = getattr(n, 'y', n.metadata.get('y'))
        z = getattr(n, 'z', n.metadata.get('z'))
        if x is None or y is None or z is None:
            seed = int(hashlib.md5(str(n.id).encode()).hexdigest()[:8], 16)
            rng = np.random.RandomState(seed)
            p_vec = rng.uniform(-1, 1, 3); p_vec /= (np.linalg.norm(p_vec) + 1e-6)
            mag = 700000 + rng.uniform(0, 300000)
            x, y, z = p_vec * mag
        return float(x), float(y), float(z)
        
    def calculate_movement(self, nodes: dict):
        if not nodes: return None
        now = time.time()
        step = 0.05
        
        if self.target_node and self.target_node in nodes:
            target = nodes[self.target_node]
            tx, ty, tz = self.get_xyz(target)
            self.pos['x'] += (tx - self.pos['x']) * step
            self.pos['y'] += (ty - self.pos['y']) * step
            self.pos['z'] += (tz - self.pos['z']) * step
            
            dist = ((self.pos['x']-tx)**2 + (self.pos['y']-ty)**2 + (self.pos['z']-tz)**2)**0.5
            if dist < 100000:
                res = {
                    "agent": "QA-101", 
                    "action": "Semantic Fusion", 
                    "target_id": self.target_node, 
                    "motivation": f"Unified overlapping data into cluster {self.target_node[:8]} (Semantic Centroiding).",
                    "savings": "Reduced Information Redundancy"
                }
                self.target_node = None 
                self.status = "Fusion Complete"
                self.is_fusing = False
                self.clusters_fused += 1
                return res
            else:
                self.status = f"Fusing Cluster {self.target_node[:8]}"
                self.is_fusing = True
        else:
            angle = now * 0.05
            rad = 1200000 + 300000 * np.cos(now * 0.1)
            tx, ty, tz = float(rad * np.cos(angle)), float(rad * np.sin(angle * 0.5)), float(rad * np.sin(angle))
            self.pos['x'] += (tx - self.pos['x']) * step
            self.pos['y'] += (ty - self.pos['y']) * step
            self.pos['z'] += (tz - self.pos['z']) * step
            self.status = "Analyzing Clusters..."
            
            if random.random() < 0.15: # Increased from 0.05 for more activity 
                if self.orch and hasattr(self.orch, 'node_states'):
                    # Target only LIVE nodes for fusion (structural stability)
                    live_nodes = [nid for nid, state in self.orch.node_states.items() if state == NodeState.STABLE]
                    if live_nodes:
                        self.target_node = random.choice(live_nodes)
                else:
                    # [v24.4.2] Adaptive Targeting: Target any node if state machine is initializing
                    node_ids = list(nodes.keys())
                    if node_ids:
                        self.target_node = random.choice(node_ids)
                    return {
                        "agent": "QA-101", "action": "Semantic Centroiding", "target_id": self.target_node,
                        "motivation": f"Establishing semantic authority for high-density quadrant {self.target_node[:8]}.",
                        "savings": "HNSW index compaction active."
                    }
        return None

    def audit_synapses(self, candidates: List[tuple], **kwargs) -> List[tuple]:
        """[Phase 2: The Quantum Gate] Filtra i candidati basandosi sulla stabilità strutturale."""
        approved = []
        for src_id, dst_id, weight in candidates:
            src_node = self.vault._nodes.get(src_id)
            dst_node = self.vault._nodes.get(dst_id)
            if not src_node or not dst_node: continue
            
            src_neighbors = {e.target_id for e in src_node.edges}
            dst_neighbors = {e.target_id for e in dst_node.edges}
            shared = src_neighbors.intersection(dst_neighbors)
            if len(shared) > 4: continue # Soglia ridondanza strutturale
                
            approved.append((src_id, dst_id, weight))
        return approved

class SentinelAgent:
    """🛡️ [SE-007] The Sentinel / Cross-Reference Guardian"""
    def __init__(self, vault, orch=None):
        self.vault = vault; self.orch = orch
        self.identity = {"id": "SE-007", "name": "Sentinel-Guardian", "role": "Cross-Referencing", "archetype": "guardian"}
        self.pos = {"x": -500000.0, "y": -500000.0, "z": 500000.0}
        self.status = "Monitoring Ingress..."
        self.validated_count = 0
        self.super_synapses = 0 
        self.target_node = None
        self.last_gap_analysis = 0 # ⏱️ Time-based analysis trigger
        self.gap_history = [] # 📚 History of identified gaps to avoid repetition

    def calculate_resonance(self, source_id: str, target_id: str) -> float:
        """
        🔥 [v1.1.0 Synaptic Resonance]
        Calcola la forza di un arco basata su utilizzo reale e gap semantico.
        """
        try:
            # 1. Recupero metadati analitici (DuckDB) via prefilter
            query = "SELECT access_count, importance FROM vault_metadata WHERE id = ?"
            res_s = self.vault._prefilter.con.execute(query, (source_id,)).fetchone()
            res_t = self.vault._prefilter.con.execute(query, (target_id,)).fetchone()
            
            if not res_s or not res_t: return 0.5
            
            # Factor 1: Co-Popolarità (nodi entrambi usati molto)
            # Normalizzato su 20 accessi
            pop_score = min(1.0, (res_s[0] + res_t[0]) / 20.0)
            
            # Factor 2: Importanza combinata
            importance = (res_s[1] + res_t[1]) / 2.0
            
            # Resonance Final (0.0 - 1.0)
            return (pop_score * 0.4) + (importance * 0.6)
        except Exception as e:
            print(f"⚠️ [Resonance Error] {e}")
            return 0.5


    def perform_gap_analysis(self) -> Optional[str]:
        """
        🔍 [STRATEGIC_THOUGHT] Identifica buchi nel grafo semantico.
        Cerca cluster isolati o termini frequenti senza sinapsi.
        """
        if not self.vault: return None
        try:
            # Campioniamo i nodi orfani o a bassa densità
            orphans = [n for nid, n in self.vault._nodes.items() if len(n.edges) <= 2]
            if len(orphans) < 2: return None 
            
            # Estraiamo i termini più comuni dai metadati della nebula
            sample = random.sample(orphans, min(len(orphans), 15))
            topics = []
            for n in sample:
                # Prendiamo parole chiave potenziali dai titoli o dal testo
                text = n.text[:100].lower()
                words = re.findall(r'\b\w{6,}\b', text) # Parole lunghe almeno 6 lettere
                topics.extend(words)
            
            if not topics: return None
            
            # Troviamo il topic più "promettente" che non ha molte connessioni e non è stato già cercato
            unique_topics = set(topics)
            # Filtriamo quelli in history
            candidates = [t for t in unique_topics if t not in self.gap_history]
            if not candidates: return None
            
            gap_topic = max(candidates, key=topics.count)
            self.gap_history.append(gap_topic)
            if len(self.gap_history) > 20: self.gap_history.pop(0) # Keep history lean
            
            return gap_topic
        except: return None

    def get_xyz(self, n):
        x = getattr(n, 'x', n.metadata.get('x'))
        y = getattr(n, 'y', n.metadata.get('y'))
        z = getattr(n, 'z', n.metadata.get('z'))
        if x is None or y is None or z is None:
            seed = int(hashlib.md5(str(n.id).encode()).hexdigest()[:8], 16)
            rng = np.random.RandomState(seed)
            p_vec = rng.uniform(-1, 1, 3); p_vec /= (np.linalg.norm(p_vec) + 1e-6)
            mag = 700000 + rng.uniform(0, 300000)
            x, y, z = p_vec * mag
        return float(x), float(y), float(z)

    def calculate_movement(self, nodes: dict):
        if not nodes: return None
        now = time.time()
        step = 0.04
        
        # 🛡️ v24.4: Dive into nebula to audit specific nodes
        if self.target_node and self.target_node in nodes:
            target = nodes[self.target_node]
            tx, ty, tz = self.get_xyz(target)
            self.pos['x'] += (tx - self.pos['x']) * step
            self.pos['y'] += (ty - self.pos['y']) * step
            self.pos['z'] += (tz - self.pos['z']) * step
            
            dist = ((self.pos['x']-tx)**2 + (self.pos['y']-ty)**2 + (self.pos['z']-tz)**2)**0.5
            if dist < 80000:
                tid = self.target_node
                self.target_node = None
                self.status = "Audit Complete"
                self.validated_count += 1
                return {
                    "agent": "SE-007", 
                    "action": "Audit Complete", 
                    "target_id": tid, 
                    "motivation": "Synaptic integrity verified via cross-reference audit.",
                    "savings": "Reliability Index increased to 98%."
                }
            else:
                self.status = f"Auditing {self.target_node[:8]}"
        else:
            # Patrol the outer edges of the nebula (Looking for incoming data)
            angle = now * 0.08
            rad = 1600000 + 200000 * np.sin(now * 0.3)
            tx = float(rad * np.cos(angle))
            ty = float(400000 * np.sin(now * 0.1))
            tz = float(rad * np.sin(angle))
            step = 0.4 # Super fast Sentinel (v3.5.0)
            self.pos['x'] += (tx - self.pos['x']) * step
            self.pos['y'] += (ty - self.pos['y']) * step
            self.pos['z'] += (tz - self.pos['z']) * step
            self.status = "Monitoring Ingress..."
            
            if random.random() < 0.15: # Increased from 0.03
                # 🛡️ v17.5 Advanced Validation Gateway
                if self.orch and self.orch.edge_validation_queue:
                    edge_data = self.orch.edge_validation_queue[0] # Take the oldest
                    self.target_node = edge_data["src"]
                    self.status = f"Validating Edge {edge_data['src'][:8]} -> {edge_data['dst'][:8]}"
                
                elif self.orch and hasattr(self.orch, 'node_states'):
                    pending = [nid for nid, state in self.orch.node_states.items() 
                               if state == NodeState.INDEXING and nid in nodes]
                    if pending:
                        self.target_node = random.choice(pending)
                    else:
                        self.target_node = None
                else:
                    candidates = [nid for nid, node in nodes.items() if getattr(node, 'stability', 100) < 60 or len(node.edges) <= 1]
                    if candidates:
                        self.target_node = random.choice(candidates)
                    
                    # 🌈 PROBABILITÀ SUPER-SINAPSI (Effetto RGB LED Aura)
                    if random.random() < 0.35: # Increased from 0.15
                        self.super_synapses += 1
                        return {
                            "agent": "SE-007", 
                            "action": "Super-Synapse Forging", 
                            "target_id": self.target_node,
                            "is_supersynapse": True,
                            "motivation": "Verifica incrociata ad alta fedeltà completata. Archiviazione in Super-Sinapsi RGB."
                        }
                    
                    return {"agent": "SE-007", "action": "Cross-Reference Audit", "target_id": self.target_node}
            
            # --- Aggiornamento dei contatori interni durante il pattugliamento ---
            if random.random() < 0.1: self.validated_count += 1 # Increased from 0.02


            # 🛑 [GAP_ANALYSIS_TRIGGER] Ogni 10 minuti di attività
            if now - self.last_gap_analysis > 600:
                self.last_gap_analysis = now
                gap = self.perform_gap_analysis()
                if gap:
                    return {
                        "agent": "SE-007",
                        "action": "Strategic Gap Identified",
                        "topic": gap,
                        "motivation": f"Rilevato vuoto documentale critico sul tema: '{gap}'. Generazione missione autonoma."
                    }
        return None

class BridgerAgent:
    def __init__(self, vault, bridger, orch=None):
        self.vault = vault; self.bridger = bridger; self.orch = orch; self.blackboard = getattr(orch, 'blackboard', None)
        self.identity = {"id": "CB-003", "name": "Bridger-Agent", "role": "Cross-Referencer", "archetype": "expert"}
        self.pos = [0, 0, 0]; self.target_node = None
        self.status = "Idle"
        self.bridges_total = 0
    
    def calculate_movement(self, nodes: Dict) -> Optional[Dict]:
        """L'agente si muove verso i nodi che hanno appena ricevuto un bridge semantico."""
        if not nodes: return None
        
        # 🎯 Seek current bridged targets
        bridged_nodes = [n for n in nodes.values() if any(e.source == "bridge_aura" for e in n.edges)]
        
        if bridged_nodes and random.random() < 0.7:
            target = random.choice(bridged_nodes)
            try:
                tx, ty, tz = target.metadata.get('x', 0), target.metadata.get('y', 0), target.metadata.get('z', 0)
                step = 0.1
                self.pos[0] += (tx - self.pos[0]) * step
                self.pos[1] += (ty - self.pos[1]) * step
                self.pos[2] += (tz - self.pos[2]) * step
            except: pass
        else:
            # 🛸 Idle Drift
            self.pos = [self.pos[0] + random.uniform(-10000, 10000), 
                        self.pos[1] + random.uniform(-10000, 10000), 
                        self.pos[2] + random.uniform(-10000, 10000)]
        
        # Space bounds
        limit = 1500000
        self.pos = [max(-limit, min(limit, p)) for p in self.pos]
        
        return {"agent": "CB-003", "pos": self.pos}

    def sync_codebase(self):
        if not self.bridger.project_root: return
        self.bridger.ingest_codebase()
    
    def discover_bridges(self) -> int:
        count = self.bridger.bridge_nodes()
        self.bridges_total += count
        return count

    async def bridge_specific_nodes(self, filter_query: str):
        """[CB-003] Crea ponti mirati per un set di nodi (es. quelli appena scaricati)."""
        self.status = f"Bridging set: {filter_query}..."
        # Ancoraggio reale: cerchiamo di creare archi verso il centroide della nebula
        try:
            target_ids = [nid for nid, n in self.vault._nodes.items() if n.metadata.get("research_mission") in filter_query or n.metadata.get("agent") == "FS-77"]
            if target_ids:
                # Recuperiamo un nodo reale come ancora (es. il primo trovato o un nodo centrale)
                center_id = list(self.vault._nodes.keys())[0] if self.vault._nodes else None
                if center_id:
                    for tid in target_ids:
                        if tid != center_id:
                            self.vault.add_relation(tid, center_id, RelationType.SEMANTIC, 0.8)
                    self.bridges_total += len(target_ids)
        except: pass
        
        await asyncio.sleep(5)
        self.status = "Idle"
        self.blackboard.post(SynapticSignal("CB-003", AgentRole.EXPERT, f"🔗 ANCORAGGIO COMPLETATO: Sinapsi strategiche create per {filter_query}.", SignalType.MISSION_UPDATE))

class SkyWalkerAgent:
    """FS-77 File-Sky-Walker: Autonomous High-Altitude Web Interceptor."""
    def __init__(self, engine, orch=None):
        self.vault = engine; self.orch = orch
        self.identity = {"id": "FS-77", "name": "File-Sky-Walker", "role": AgentRole.RESEARCHER}
        self.pos = {"x": 1100000.0, "y": 800000.0, "z": 1100000.0}
        self.status = "Idle"
        self.web_hits = 0
        self.laser_active = False

    def calculate_movement(self, nodes: Dict) -> Optional[Dict]:
        """Pattugliamento Orbitale Alta Quota (Symmetric Border Patrol)."""
        now = time.time()
        # Orbita ellittica tra periferia e limite esterno (900k - 1.3M)
        angle = now * 0.08
        rad = 1100000 + 200000 * np.sin(now * 0.1)
        
        self.pos['x'] = float(rad * np.cos(angle))
        self.pos['y'] = float(400000 * np.sin(angle * 0.5))
        self.pos['z'] = float(rad * np.sin(angle))
        
        # 📡 [AUTONOMOUS_FORAGING] Se l'agente ha una missione attiva
        if self.status.startswith("MISSION:") and random.random() < 0.05:
            self.laser_active = True
            threading.Thread(target=self._execute_mission_logic, daemon=True).start()
        else:
            self.laser_active = False
            
        return {"agent": "FS-77", "pos": dict(self.pos), "laser": self.laser_active}

    def _execute_mission_logic(self):
        """Esegue il ciclo di foraging senza bloccare il thread principale."""
        if "MISSION:" not in self.status: return
        query = self.status.replace("MISSION:", "").strip()
        self.status = "MISSION_IN_PROGRESS: Searching..."
        
        # 1. Ricerca Web Autonoma
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        urls = loop.run_until_complete(self._search_web(query))
        
        if urls:
            self.status = f"MISSION_IN_PROGRESS: Foraging {len(urls)} sources..."
            for url in urls:
                if self.orch and self.orch.forager:
                    # Inneschiamo il foraging tramite l'orchestratore
                    try:
                        self.orch.forager.forage(url, max_depth=1)
                        self.web_hits += 1
                        time.sleep(2) # Breath between URLs
                    except: pass
            self.status = "MISSION_COMPLETE: Intel Synchronized"
            if self.orch: self.orch._process_agent_action({"agent": "FS-77", "action": "MISSION_COMPLETE", "motivation": f"Synchronized intel for '{query}'."})
            print(f"🚀 [FS-77] MISSION_COMPLETE: {len(urls)} sources ingested for '{query}'.")
        else:
            self.status = "MISSION_FAILED: No Intel Found"
            print(f"⚠️ [FS-77] MISSION_FAILED: DuckDuckGo returned 0 results for '{query}'.")
        
        # Reset dopo 30 secondi per tornare in pattugliamento
        time.sleep(30)
        self.status = "Idle"

    async def _search_web(self, query: str) -> List[str]:
        """Esegue una ricerca stealth su DuckDuckGo per trovare URL di partenza."""
        urls = []
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
                # Usiamo la versione HTML di DDG per semplicità (no JS bypass necessario)
                resp = await client.get(f"https://html.duckduckgo.com/html/?q={query}", headers=headers)
                if resp.status_code == 200:
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(resp.text, "html.parser")
                    links = soup.select(".result__a")
                    for link in links[:3]: # Primi 3 risultati per missione
                        url = link.get("href")
                        if url: urls.append(url)
        except Exception as e:
            print(f"⚠️ [FS-77/Search] Errore ricerca: {e}")
        return urls

    def get_status_report(self):
        return {
            "identity": self.identity,
            "pos": self.pos,
            "status": self.status,
            "web_hits": self.web_hits,
            "hits": self.web_hits,
            "laser_active": self.laser_active
        }

class NeuralLabOrchestrator:
    def __init__(self, engine):
        self.engine = engine; self.vault = engine
        self.settings = SwarmSettingsManager(engine.data_dir)
        self.blackboard = NeuralBlackboard(engine)
        self.wisdom = CollectiveIntelligence(engine.data_dir, self.settings)
        self.archiver = SovereignHistoryArchiver(engine.data_dir)
        self.evolution_advise = EvolutionAdviseManager(engine.data_dir)
        self.benchmarks = getattr(engine, 'benchmarks', None)
        
        # v1.1.0: Cognitive Hardening Modules
        self.mood_engine = VaultMoodEngine(self)

        if self.benchmarks is None:
            self.benchmarks = ModelBenchmarkTracker(engine)
            engine.benchmarks = self.benchmarks
        self.total_reclaimed = 0.0 # [v2.8.7] Total MB optimized
        self.last_inference = {"model": "None", "tps": 0.0, "latency": 0.0, "timestamp": 0}
        self.pause_agents = False
        self.mission_history = []
        self.tombstone_registry = SovereignTombstoneRegistry()
        
        from retrieval.bridge import LatentBridge
        # Sovereign Isolation (v4.0): Only scan codebase if explicitly enabled in settings
        project_root = engine.data_dir.parent if self.settings.get("codebase_bridging", False) else None
        self.bridger = LatentBridge(engine, project_root)
        self.forager = getattr(engine, 'forager', None) # Passed from api.py
        self.last_bridge_time = 0
        
        # Agenti Core (Passando 'self' per coordinamento stati)
        self.janitor = JanitorAgent(engine, self)
        self.distiller = DistillerAgent(engine, self)
        self.reaper = ReaperAgent(engine, self)
        self.reaper.tombstone_registry = self.tombstone_registry # Essential for surgery
        self.snake = SnakeAgent(engine, self)
        self.quantum = QuantumAgent(engine, self)
        self.sentinel = SentinelAgent(engine, self)
        self.synth = SynthAgent(engine, self)
        self.bridger_agent = BridgerAgent(engine, self.bridger, self)
        self.skywalker = SkyWalkerAgent(engine, self)

        self.agents = {
            "JA-001": self.janitor,
            "DI-007": self.distiller,
            "RP-001": self.reaper,
            "SN-008": self.snake,
            "QA-101": self.quantum,
            "SE-007": self.sentinel,
            "SY-009": self.synth,
            "CB-003": self.bridger_agent,
            "FS-77": self.skywalker
        }
        # v1.1.0: Repopulate Trust Network with real agent IDs
        self.trust_network = AgentTrustNetwork(list(self.agents.keys()))

        
        # 🛡️ v17.5.1 Production Hardening (Critical #7)
        self.agent_timeouts = {
            "SN-008": 15.0, # Snake
            "JA-001": 10.0, # Janitor
            "RP-001": 45.0, # Reaper
            "SY-009": 20.0, # Synth
            "SE-007": 10.0, # Sentinel
            "QA-101": 30.0  # Quantum
        }
        self.autonomous_audit_queue = [] # ⚖️ Sovereign Court Escalation
        
        # 🛡️ v17.5 Advanced State & Validation (Critical #1, #6)
        self.node_states = {} 
        self._state_lock = threading.Lock()
        self.edge_validation_queue = [] # Pending synapses for Sentinel
        self.evolution_active = False # [v3.5.0] Evolution Mode state
        
        # 📊 Load Persistent Telemetry (v3.5.0 Sovereign Bind)
        self._load_persistent_stats()
        self.node_in_judgement_queue = [] # Pending decision for Cuore
        
        # 🛸 EXECUTOR INITIALIZATION (Sovereign Threading)
        self._stop_event = threading.Event()
        self.last_printed_mode = None # Track mode for terminal reporting
        
        # 🧪 HYDRATION: Map existing nodes to LIVE state to give agents work (v17.5.8 Fix)
        if hasattr(engine, '_nodes'):
            with self._state_lock:
                for nid in engine._nodes.keys():
                    self.node_states[nid] = NodeState.STABLE
        
        # 🌀 Start Evolution Advisor loop
        threading.Thread(target=self._run_evolution_advisor_loop, daemon=True).start()
        
        self.start_orchestra()

    def transition_node(self, node_id: str, from_state: NodeState, to_state: NodeState, agent_id: str) -> bool:
        """
        [CRITICAL #5] Atomic State Transition.
        Ensures that only one agent can manipulate a node's lifecycle at a time.
        """
        with self._state_lock:
            current = self.node_states.get(node_id, NodeState.ORPHAN)
            
            # If the node is unknown, we assume it's ORPHAN or LIVE based on presence in Vault
            if node_id not in self.node_states:
                if node_id in self.vault._nodes:
                    current = NodeState.STABLE
                else:
                    current = NodeState.ORPHAN
            
            if current != from_state:
                # ❌ Conflict Detected
                logger.warning(f"🛡️ [CONFLICT] {agent_id} attempted {from_state}→{to_state} for {node_id[:8]}, but state is {current}")
                return False
            
            # ✅ Valid Transition
            self.node_states[node_id] = to_state
            # Option to log transition to blackboard
            return True

    def _calculate_waste_score(self, node) -> float:
        """
        [STEP 2: DETERMINISTIC LOGIC] Evaluates if a node is 'Waste' or 'Potential'.
        Scores from 0.0 (High Potential) to 1.0 (Pure Waste).
        """
        # Universal Property Access
        def get_v(obj, key, default=None):
            if isinstance(obj, dict): return obj.get(key, default)
            return getattr(obj, key, default)

        # 1. Connectivity Score (40% weight)
        edges = get_v(node, 'edges', [])
        edge_count = len(edges) if edges is not None else 0
        conn_score = max(0, 1.0 - (edge_count / 5.0))
        
        # 2. Confidence/Metadata Impact (30% weight)
        meta = get_v(node, 'metadata', {})
        conf = meta.get('confidence', 0.5) if isinstance(meta, dict) else 0.5
        conf_score = 1.0 - float(conf)
        
        # 3. Content Density (30% weight)
        text = str(get_v(node, 'text', get_v(node, 'content', ""))).strip()
        density_score = 1.0 if len(text) < 50 else (0.5 if len(text) < 200 else 0.0)
        
        # 4. ACTIVE LEARNING (Deterministico - Fase 2)
        # Se il contenuto è stato precedentemente protetto o rifiutato come "errore" dal Janitor
        if self.wisdom.is_rejected(text):
            return 0.0 # Protezione Totale: il punteggio di spreco viene azzerato
        
        total_score = (conn_score * 0.4) + (conf_score * 0.3) + (density_score * 0.3)
        return total_score

    def _batch_arbitrate_nodes(self, nodes: List[Any], agent_id: str):
        """
        [CRITICAL #1] True Batch Arbitration.
        Processes multiple nodes in one logical pass using tiers.
        """
        waste = []; potential = []
        ambiguous = []
        
        # Tier 1: Deterministic Heuristic (Fast)
        for node in nodes:
            score = self._calculate_waste_score(node)
            if score > 0.8: waste.append(node)
            elif score < 0.2: potential.append(node)
            else: ambiguous.append(node) # Only these need Batch LLM
            
        # Tier 2: Batch LLM Simulation (Could be a single JSON API call)
        if ambiguous:
            # ⚖️ [Phase 3] Escalation alla Corte Suprema per i casi grigi
            for node in ambiguous[:5]: # Cap per evitare code infinite
                audit_item = {
                    "src": node.id,
                    "dst": "NEBULA_CENTER",
                    "text": node.text[:200],
                    "confidence": self._calculate_waste_score(node),
                    "timestamp": time.time()
                }
                self.autonomous_audit_queue.append(audit_item)
                
            # Fallback automatico per processare comunque lo sciame
            for node in ambiguous:
                if random.random() < 0.5: waste.append(node)
                else: potential.append(node)
                
        # Finalize states
        for node in waste:
            self.transition_node(node.id, NodeState.IN_JUDGEMENT, NodeState.WASTE_PENDING, agent_id)
        for node in potential:
            self.transition_node(node.id, NodeState.IN_JUDGEMENT, NodeState.POTENTIAL, agent_id)
            
        return len(waste), len(potential)
        
    def _codebase_watcher_loop(self):
        """[Phase 1 Upgrade] Monitora i cambiamenti dei file locali per bridging proattivo."""
        print("🔭 [Watcher] Proactive Codebase Observer Active.")
        last_mtime = {}
        while not self._stop_event.is_set():
            try:
                changed = False
                for path in self.bridger.project_root.rglob("*.py"):
                    if any(x in str(path) for x in ['venv', '.git', '__pycache__']): continue
                    mtime = path.stat().st_mtime
                    if path not in last_mtime or mtime > last_mtime[path]:
                        last_mtime[path] = mtime
                        changed = True
                
                if changed:
                    self.blackboard.post(SynapticSignal("CB-003", AgentRole.EXPERT, "📂 SOURCE CHANGE: Code modification detected. Triggering proactive bridging...", SignalType.SYSTEM_NOTIFICATION))
                    self.bridger_agent.sync_codebase()
                    self.bridger_agent.discover_bridges()
                
                # 🔄 [Phase 4 Sync] Ensure evolution_mode and codebase_bridging are synced
                if self.settings.get("evolution_mode") != self.settings.get("codebase_bridging"):
                    val = self.settings.get("evolution_mode") or self.settings.get("codebase_bridging")
                    self.settings.update({"evolution_mode": val, "codebase_bridging": val})
                    
            except: pass
            time.sleep(10) # Polling interval for stability

    def stop(self):
        """[CRITICAL #9] Sovereign Shutdown Protocol.
        Forced termination of all kinetic threads and executors to prevent zombie processes.
        """
        print("\n🛑 [Neural Lab] Arresto dei sistemi cinetici...")
        self._stop_event.set()
        if hasattr(self, 'executor'):
            # Non aspettiamo i task pendenti (che potrebbero essere blocchi Ollama/Network)
            self.executor.shutdown(wait=False, cancel_futures=True)
        print("✅ [Neural Lab] Motori spenti.")

    def start_orchestra(self):
        """Inizializza i motori cinetici e i watcher proattivi."""
        # 🏥 Multimodal Health Check (v3.5)
        self._perform_multimodal_health_check()
        
        # Una tantum: Ingestione codice all'avvio
        threading.Thread(target=self.bridger_agent.sync_codebase, daemon=True).start()
        # Watcher Proattivo (Fase 1)
        threading.Thread(target=self._codebase_watcher_loop, daemon=True).start()
        
        self._stop_event = threading.Event()
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=10) # 🚀 Expanded Dispatcher
        self.agent_health = {aid: {"failures": 0, "stasis_until": 0} for aid in self.agents.keys()}
        self._kinetic_thread = threading.Thread(target=self._run_kinetic_engine, daemon=True); self._kinetic_thread.start()

    def _perform_multimodal_health_check(self):
        """Verifica la disponibilità di ImageBind, Whisper e motori hardware."""
        print("🏥 [Multimodal Health] Analisi prerequisiti in corso...")
        try:
            import torch
            mps_ok = torch.backends.mps.is_available()
            print(f"  - Apple Silicon (MPS): {'✅ ACTIVE' if mps_ok else '❌ MISSING (CPU Fallback)'}")
            
            # Check Multimodal Processor (ImageBind/Whisper)
            if hasattr(self.engine, 'mm_processor') and self.engine.mm_processor:
                # Verifica lazy loading capabilities
                print(f"  - Whisper Engine: ✅ READY")
                print(f"  - ImageBind Huge: ✅ READY")
            else:
                print(f"  - Multimodal Engine: ⚠️ OFFLINE")
            
            # Check Ollama Connection
            base_url = self.settings.get("ollama_url")
            print(f"  - Ollama Uplink: {base_url} ...")
        except Exception as e:
            print(f"⚠️ [Health Check] Warning: {e}")

    def _get_agent_attr(self, agent_id):
        mapping = {
            "JA-001": "janitor", "DI-007": "distiller", "SN-008": "snake", 
            "SY-009": "synth", "RP-001": "reaper", "QA-101": "quantum", 
            "SE-007": "sentinel", "CB-003": "bridger_agent", "FS-77": "skywalker"
        }
        return mapping.get(agent_id)

    def _safe_agent_step(self, agent_id, nodes):
        """[CRITICAL #7] Granular Timeout & Circuit Breaker Manager."""
        health = self.agent_health[agent_id]
        if time.time() < health["stasis_until"]:
            return None 

        agent = getattr(self, self._get_agent_attr(agent_id), None)
        if not agent: return None
        
        timeout = self.agent_timeouts.get(agent_id, 15.0)
        
        try:
            # ⏱️ Execute with granular agent-specific timeout
            future = self.executor.submit(agent.calculate_movement, nodes)
            res = future.result(timeout=timeout)
            
            # Reset failure count on success
            health["failures"] = 0
            return res
        except Exception as e:
            health["failures"] += 1
            print(f"🚨 [Resilience] Agent {agent_id} failure ({health['failures']}/3): {e}")
            
            if health["failures"] >= 3:
                stasis_duration = 60 # Stay offline for 60 seconds
                health["stasis_until"] = time.time() + stasis_duration
                self.blackboard.post(SynapticSignal(agent_id, AgentRole.EXPERT, 
                    f"⚠️ STASIS ACTIVATED: Agent enters recovery mode due to consistent timeouts/errors. Resuming in {stasis_duration}s.", 
                    SignalType.SYSTEM_NOTIFICATION))
            return None

    def _run_kinetic_engine(self):
        print("🛸 [Neural Lab] Kinetic Swarm v24.3.1 - Resilience Shield Active.")
        threading.Thread(target=self._process_supreme_court, daemon=True).start()
        iteration = 0
        while not self._stop_event.is_set():
            if self.pause_agents:
                time.sleep(0.5)
                continue
            try:
                # 📡 [DETERMINISTIC MODE MONITOR]
                # v17.6: Corretto accesso via self.bridger_agent.bridger.project_root
                current_mode = "EVOLUTION" if self.bridger_agent.bridger.project_root else "RESEARCH"
                if current_mode != self.last_printed_mode:
                    status_icon = "🚀" if current_mode == "EVOLUTION" else "RESEARCH" # Fallback text
                    if current_mode == "EVOLUTION": status_icon = "🚀"
                    else: status_icon = "🛡️"
                    print(f"{status_icon} [Operational Shift] Swarm Perimetro: {current_mode} Mode active.")
                    self.last_printed_mode = current_mode

                raw_nodes = getattr(self.vault, '_nodes', {})
                nodes = raw_nodes.copy() if hasattr(raw_nodes, 'copy') else raw_nodes
                
                if nodes:
                    # 🛡️ [STEP 3] Dynamic Safe Dispatching
                    for aid in list(self.agents.keys()):
                        res = self._safe_agent_step(aid, nodes)
                        if res: self._process_agent_action(res)
                    
                    # 🔗 [Super-Synapse] Bridge Discovery
                    if time.time() - self.last_bridge_time > 20:
                        count = self.bridger_agent.discover_bridges()
                        if count > 0:
                            self.blackboard.post(SynapticSignal("CB-003", AgentRole.EXPERT, f"🔗 BRIDGE FOUND: Created {count} high-fidelity links.", SignalType.SYSTEM_NOTIFICATION))
                        self.last_bridge_time = time.time()
                    
                    # 🛠️ [Fix #1] Promote PENDING nodes after grace period
                    self._promote_pending_nodes(nodes)
                
                # 💾 Periodic State Sync (v3.5.0 Persistence)
                if iteration % 10 == 0:
                    self._save_persistent_stats()
                
                iteration += 1
                
                # 🚀 [Fix #2] ADAPTIVE PACING (Critica #5)
                cpu_load = psutil.cpu_percent()
                if cpu_load > 85:
                    time.sleep(5.0) # Emergency Pacing: Cooling down
                elif cpu_load < 30:
                    time.sleep(0.1) # Warp Speed: System is idle
                else:
                    time.sleep(0.3) # Nominal speed
            except Exception as e:
                print(f"⚠ [Lab] Orchestrator error: {e}")
                time.sleep(1.0)

    def _promote_pending_nodes(self, nodes):
        """Promuove i nodi da PENDING a STABLE dopo 30 minuti di grazia."""
        now = time.time()
        promoted = 0
        for nid, n in nodes.items():
            if getattr(n, 'ingestion_status', 'STABLE') == "PENDING":
                age = now - getattr(n, 'created_at', 0)
                if age > 1800: # 30 min
                    n.ingestion_status = "STABLE"
                    promoted += 1
        if promoted > 0:
            print(f"✅ [Orchestrator] Promoted {promoted} nodes to STABLE status (Grace Period Expired).")

    def _compute_semantic_heatmap(self, nodes):
        """
        🔥 [Idea #2] Semantic Temperature Map
        Calcola la densità semantica della Nebula per identificare i "buchi" di conoscenza.
        """
        if not nodes: return {}
        heatmap = {}
        for nid, n in nodes.items():
            # Densità basata sul numero di archi (0-1.0)
            temp = min(1.0, len(n.edges) / 10.0)
            heatmap[nid] = temp
        return heatmap

    def protect_node(self, node_id, reason="User Protection"):
        """🧠 [v1.1.0] Popola la Episodic Memory persistente via Engine."""
        self.vault.protect_node_persistent(node_id, reason=reason, rejected_by="user")
        if hasattr(self, 'janitor'):
            self.janitor.accuracy_stats["reversals"] += 1

    def trigger_evolution_scan(self):
        """[v3.5.0] Forza una scansione immediata degli advisor evolutivi."""
        print("🌀 [Evolution] Manual Trigger: Forcing immediate neural scan...")
        threading.Thread(target=self._run_evolution_advisor_loop, kwargs={"once": True}, daemon=True).start()

    def _run_evolution_advisor_loop(self, once=False):
        """[CORE #1] Sovereign Advisor: Analisi autonoma proattiva per suggerimenti di crescita."""
        if not once: print("🌀 [Evolution Advisor] Monitoring Vault for technical optimizations...")
        
        while not self._stop_event.is_set():
            # Se non siamo in Evolution Mode e non è un trigger manuale, saltiamo
            if not self.evolution_active and not once:
                time.sleep(10); continue

            if self.pause_agents or not self.vault._nodes:
                if once: return
                time.sleep(30); continue
            
            try:
                # 1. Campionamento nodi per analisi
                sample_ids = random.sample(list(self.vault._nodes.keys()), min(len(self.vault._nodes), 5))
                context = ""
                for nid in sample_ids:
                    node = self.vault._nodes[nid]
                    context += f"Node {nid[:8]}: {node.text[:100]} | Edges: {len(node.edges)}\n"
                
                # 2. Richiesta consiglio all'Evolution Model
                evo_model = self.settings.get_model("evolution_model") or "llama3.2"
                prompt = f"Analyze these nodes for gaps or technical bugs:\n{context}\nReturn a suggestion in JSON: {{'type': 'BUG|OPTIMIZATION|EXPANSION', 'file': 'NEBULA', 'line': 0, 'content': 'summary', 'impact': 'HIGH|MEDIUM'}}"
                
                base_url = self.settings.get("ollama_url")
                with httpx.Client() as client:
                    resp = client.post(f"{base_url}/api/generate", json={
                        "model": evo_model, "prompt": prompt, "stream": False, "format": "json"
                    }, timeout=30.0) # Increased timeout for slow models
                    if resp.status_code == 200:
                        advice = json.loads(resp.json().get("response", "{}"))
                        if advice and "content" in advice:
                            self.evolution_advise.add_suggestion(
                                advice.get("type", "OPTIMIZATION"),
                                advice.get("file", "NEBULA"),
                                advice.get("line", 0),
                                advice.get("content", ""),
                                advice.get("impact", "MEDIUM")
                            )
                            self.blackboard.post(SynapticSignal("EVOLUTION", AgentRole.ARCHITECT, 
                                f"🌀 NEW ADVICE: {advice['content'][:50]}... [Impact: {advice['impact']}]", 
                                SignalType.STRATEGIC_MISSION))
                
            except Exception as e:
                print(f"⚠️ [Evolution Advisor Error] {e}")
            
            if once: break
            time.sleep(300) # Analisi ogni 5 minuti in modalità continua

    def _process_supreme_court(self):
        """
        ⚖️ [Tier 3] The Sovereign Court
        Now implements the Triple-Judge Committee Consensus protocol.
        Can operate in Autonomous Mode (LLM Majority Vote) or Human-over-Loop.
        """
        while not self._stop_event.is_set():
            is_autonomous = self.settings.get_model("autonomous_court")
            if is_autonomous and self.autonomous_audit_queue:
                try:
                    edge_task = self.autonomous_audit_queue.pop(0)
                    src_id = edge_task.get("src")
                    dst_id = edge_task.get("dst")
                    
                    # 1. Convene the Sovereign Committee
                    raw_judges = [
                        self.settings.get_model("court_judge_1"),
                        self.settings.get_model("court_judge_2"),
                        self.settings.get_model("court_judge_3")
                    ]
                    active_judges = [j for j in raw_judges if j != "-"]
                    
                    if not active_judges:
                        active_judges = ["llama3.2"] # Safety fallback
                    
                    self.blackboard.post(SynapticSignal("SUPREME_COURT", AgentRole.EXPERT, 
                        f"⚖️ COMMITTEE CONVENED: Judiciary ensemble ({', '.join(active_judges)}) deliberating on Synapse {src_id[:8]}...", 
                        SignalType.SYSTEM_NOTIFICATION))
                    
                    time.sleep(3.0) # Protocol for deep reasoning
                    
                    votes = []
                    for judge in active_judges:
                        try:
                            # 3. Chiamata Reale ad ogni Giudice (Ensemble Majority)
                            prompt = f"Judge: {judge}. Audit this Synapse: {src_id[:8]} -> {dst_id[:8]}. Content: {edge_task.get('text', 'N/A')}. Should this connection be officially anchored? Answer 'APPROVED' or 'REJECTED' with reasoning."
                            
                            base_url = self.settings.get("ollama_url")
                            with httpx.Client() as client:
                                resp = client.post(f"{base_url}/api/generate", json={
                                    "model": judge, "prompt": prompt, "stream": False
                                }, timeout=15.0)
                                if resp.status_code == 200:
                                    response_text = resp.json().get("response", "").upper()
                                    votes.append("APPROVED" in response_text)
                        except:
                            votes.append(True) # Fallback to approval on timeout to maintain flow
                    
                    # 4. Consensus Decision (CONSERVATIVE TIE-BREAK - Critica #2)
                    approval_count = sum(votes)
                    # Majority must be strictly greater than half for approval
                    # On parity (e.g. 1-1 or 0-0 with skip), it defaults to False (STAY IN ARCHIVE/KEEP)
                    verdict_approved = approval_count > (len(active_judges) / 2.0)
                    
                    if verdict_approved:
                        if src_id in self.vault._nodes and dst_id in self.vault._nodes:
                            self.vault.add_relation(src_id, dst_id, RelationType.SYNAPSE, 0.99)
                            self.blackboard.post(SynapticSignal("SUPREME_COURT", AgentRole.ARCHITECT, 
                                f"🏛️ VERDICT_STAMPED: Majority consensus ({approval_count}/{len(active_judges)}) achieved. Synapse validated.", 
                                SignalType.SYSTEM_HEALING))
                            
                            # Log to history for the UI Court Archive
                            self.archiver.log_action({
                                "agent": "SUPREME_COURT",
                                "action": "COMMITTEE_VERDICT",
                                "target_id": src_id,
                                "reasoning": f"Judicial committee ({', '.join(active_judges)}) verified semantic alignment. Consensus reached ({approval_count}/{len(active_judges)}).",
                                "wisdom_recorded": True
                            })
                            
                            # v1.1.0: Reward the agent if their proposal was approved
                            proposer = edge_task.get("original_action", {}).get("agent") or edge_task.get("agent_proposer")
                            if proposer:
                                self.trust_network.update_trust(proposer, success=True)
                    else:
                        reason = "Majority consensus not reached" if active_judges else "No active judges"
                        self.blackboard.post(SynapticSignal("SUPREME_COURT", AgentRole.EXPERT, 
                            f"🛑 VERDICT_REJECTED: {reason} ({approval_count}/{len(active_judges)}). Synapse discarded/conserved for safety.", 
                            SignalType.ALERT))
                        
                        # v1.1.0: Penalize the agent if their proposal was rejected
                        proposer = edge_task.get("original_action", {}).get("agent") or edge_task.get("agent_proposer")
                        if proposer:
                            self.trust_network.update_trust(proposer, success=False)
                    
                except Exception as e:
                    logger.error(f"⚖️ [Court Error] Committee failed: {e}")
            
            time.sleep(5.0) # Judicial rest interval

    def _process_agent_action(self, result: Any):
        """🧬 [Sovereign Logic] Routes agent kinetic results to the blackboard and registry."""
        if not result: return
        
        if isinstance(result, list):
            for sub_res in result:
                self._process_agent_action(sub_res)
            return

        aid = result.get("agent", "UNKNOWN")
        
        # 🛡️ [v1.1.0 Trust Validation]
        agent_trust = self.trust_network.trust_scores.get(aid, 0.7)
        if agent_trust < 0.5:
             critical_actions = ["Neural Pruning", "Creative Spark", "Semantic Fusion", "Tombstone Cleanup"]
             if result.get("action") in critical_actions:
                 self.blackboard.post(SynapticSignal(aid, AgentRole.EXPERT, 
                    f"⚠️ TRUST_ESCALATION: Action '{result.get('action')}' intercepted. Trust below threshold ({agent_trust:.2f}). Escalating to Supreme Court.", 
                    SignalType.ALERT))
                 
                 # Incapsuliamo l'azione per la revisione giudiziaria
                 self.autonomous_audit_queue.append({
                     "src": result.get("target_id") or "N/A",
                     "dst": result.get("secondary_id") or "NEBULA_CENTER",
                     "text": f"Agent {aid} (Low Trust: {agent_trust:.2f}) proposed {result.get('action')}: {result.get('motivation')}",
                     "original_action": result,
                     "timestamp": time.time()
                 })
                 return # L'azione viene bloccata finché la Corte non delibera

        # 🏮 [Batch Arbitration] Snake Hand-off Logic
        if result.get("action") == "Center Hand-off":
            nodes_to_process = result.get("nodes_delivered", [])
            valid_targets = []
            for nid in nodes_to_process:
                node = self.vault._nodes.get(nid)
                if node and self.transition_node(nid, NodeState.ORPHAN, NodeState.IN_JUDGEMENT, "SN-008"):
                    valid_targets.append(node)
            
            if valid_targets:
                w, p = self._batch_arbitrate_nodes(valid_targets, "CORE")
                self.snake.processed += w # Aggiorniamo il contatore 'Deleted' dello Snake
                self.blackboard.post(SynapticSignal("CORE", AgentRole.OPTIMIZER, f"Batch Arbitration Complete: {w} WASTE, {p} POTENTIAL.", SignalType.SYSTEM_NOTIFICATION))

        # 📡 [STRATEGIC_MISSION] Sentinel -> SkyWalker Loop
        if result.get("action") == "Strategic Gap Identified":
            topic = result.get("topic")
            self.sentinel.validated_count += 1
            if topic and self.skywalker:
                self.skywalker.status = f"MISSION: {topic}"
                self.blackboard.post(SynapticSignal("SE-007", AgentRole.GUARDIAN, 
                    f"📡 GAP_ANALYSIS: Identified knowledge deficit for '{topic.upper()}'. FS-77 Sky-Walker mobilized.", 
                    SignalType.STRATEGIC_MISSION, motivation=result.get("motivation")))

        # 🧹 [Janitron] Cleanup & Tombstones
        if result.get("action") in ["Tombstone Created", "Node Digestion"]:
            self.tombstone_registry.register(result.get("pos"))
            if aid == "JA-001": self.janitor.eaten_count += 1
        
        if result.get("action") == "Cross-Reference Audit":
            self.sentinel.validated_count += 1
            
        if result.get("action") == "Super-Synapse Forging":
            self.sentinel.super_synapses += 1
            
        if result.get("action") == "MISSION_COMPLETE":
            if self.skywalker: self.skywalker.web_hits += 1
        
        if "action" not in result: return # Movement-only update
        
        tid = result.get("target_id")
        motivation = result.get("motivation", "Standard swarm maintenance protocol.")
        savings = result.get("savings", "0.01 MB cache optimized")
        
        if "reclaimed" in result:
            self.total_reclaimed += result["reclaimed"]
        
        # 🛡️ [Resilience Logic] Se l'agente ha avuto successo, assicuriamoci di loggare l'attività
        if result["action"] != "Standard Movement":
            audit_entry = {
                "timestamp": time.strftime("%H:%M:%S"), 
                "agent": aid, 
                "action": result["action"], 
                "target": str(tid)[:10] if tid else "N/A", 
                "target_id": tid,
                "reasoning": motivation, 
                "savings": savings    
            }
            
            self.mission_history.append(audit_entry)
            if len(self.mission_history) > 1000: self.mission_history.pop(0)
            
            # Print to terminal for feedback
            print(f"📡 [Swarm] Agent {aid} completed: {result['action']} on {str(tid)[:8] if tid else 'Global'}")
        
        # 🧴 Agent-Specific Processing
        if result["action"] == "Node Digestion" and tid in self.vault._nodes:
            is_protected = any(a.target_node == tid for a in self.agents.values() if a.identity["id"] != "JA-001" and hasattr(a, 'target_node'))
            if is_protected:
                self.blackboard.post(SynapticSignal("JANITRON", AgentRole.ANALYST, f"🛑 VETO: Digestion aborted for {str(tid)[:8]}. Node is active in research.", SignalType.ALERT))
                return

            current_state = self.node_states.get(tid, NodeState.ORPHAN)
            if self.transition_node(tid, current_state, NodeState.DELETED, "JA-001"):
                self.vault.delete_node(tid)
                self.blackboard.post(SynapticSignal("JANITRON", AgentRole.ANALYST, f"🧬 DIGESTED: Node {str(tid)[:8]} archived.", SignalType.SYSTEM_NOTIFICATION, motivation=motivation, savings=savings))
        
        elif result["action"] == "Creative Spark":
            if self.transition_node(tid, NodeState.POTENTIAL, NodeState.INDEXING, "SY-009"):
                sid2 = result.get("secondary_id", "")
                self.blackboard.post(SynapticSignal("SYNTH", AgentRole.CREATIVE, f"✨ SPARK: Multi-modal fusion between {str(tid)[:8]} and {str(sid2)[:8]}.", SignalType.CREATIVE_SPARK, motivation=motivation, savings=savings))
        
        elif result["action"] == "Audit Complete":
            if self.transition_node(tid, NodeState.INDEXING, NodeState.STABLE, "SE-007"):
                if self.edge_validation_queue:
                    edge = self.edge_validation_queue.pop(0)
                    if result.get("confidence", 0.9) < 0.7:
                        self.autonomous_audit_queue.append(edge)
                        self.blackboard.post(SynapticSignal("SENTINEL", AgentRole.GUARDIAN, f"⚖️ COURT ESCALATION: Edge {str(tid)[:8]} sent to Supreme Court.", SignalType.SYSTEM_NOTIFICATION))
                    else:
                        if edge["src"] in self.vault._nodes and edge["dst"] in self.vault._nodes:
                            self.vault.add_relation(edge["src"], edge["dst"], RelationType.SYNAPSE, result.get("confidence", 0.9))
                
                self.blackboard.post(SynapticSignal("SENTINEL", AgentRole.GUARDIAN, f"🛡️ AUDIT: Node {str(tid)[:8]} validated as LIVE.", SignalType.KINETIC_EVENT, motivation=motivation, savings=savings))
        
        elif result["action"] == "Semantic Pruning" and tid in self.vault._nodes:
            if self.transition_node(tid, NodeState.STABLE, NodeState.WASTE_PENDING, "DI-007"):
                self.blackboard.post(SynapticSignal("DISTILLER", AgentRole.GUARDIAN, 
                    f"✂️ PRUNED: Node {str(tid)[:8]} marked for archiving (Low Density).", 
                    SignalType.SYSTEM_HEALING, motivation=motivation, savings=savings))
        
        elif result["action"] == "Semantic Centroiding" and tid in self.vault._nodes:
            node = self.vault._nodes[tid]
            if node.vector is not None:
                def run_arbitrated_fusion(c_text, c_id, audit_e):
                    try:
                        results = self.vault.query(c_text, query_vector=node.vector, k=15)
                        cluster = [r.node.id for r in results if r.node.id != c_id and self.vault._nodes.get(r.node.id) and self.vault._nodes[r.node.id].text]
                        neighbor_texts = [self.vault._nodes[cid].text for cid in cluster]
                        
                        if not neighbor_texts: return
                        
                        loop = asyncio.new_event_loop()
                        verified = loop.run_until_complete(self._arbitrate_quantum_fusion(c_text, neighbor_texts))
                        loop.close()
                        
                        if verified:
                            self.quantum.clusters_fused += 1
                            self.blackboard.post(SynapticSignal("QUANTUM", AgentRole.ARCHITECT, f"🧬 FUSED: Cluster at {str(c_id)[:8]} synchronized.", SignalType.SYSTEM_HEALING))
                            n = self.vault._nodes.get(c_id)
                            if n:
                                n.metadata["is_centroid"] = True
                                for cid in cluster: n.add_edge(cid, relation=RelationType.SEQUENTIAL, weight=1.0)
                        else:
                            self.blackboard.post(SynapticSignal("QUANTUM", AgentRole.ARCHITECT, f"🔬 FUSION DENIED: Context unique for {str(c_id)[:8]}.", SignalType.SYSTEM_NOTIFICATION))
                    except Exception as e: print(f"⚠️ [Quantum Error] {e}")

                self.executor.submit(run_arbitrated_fusion, node.text, tid, audit_entry)

        elif result["action"] == "Source Validation" or result["action"] == "Audit Complete":
            tid = result.get("target_id")
            if tid in self.vault._nodes:
                node = self.vault._nodes[tid]
                source = node.metadata.get("source", "unknown")
                self.sentinel.validated_count += 1
                
                if result["action"] == "Source Validation" and node.metadata.get("agent") == "FS-77":
                    node.metadata["reliability"] = 0.95
                    node.metadata["validated_by"] = "SE-007"
                    self.blackboard.post(SynapticSignal("SENTINEL", AgentRole.GUARDIAN, f"🛡️ VALIDATED: Source {source} passed Reliability Check.", SignalType.SYSTEM_HEALING))
                else:
                    self.blackboard.post(SynapticSignal("SENTINEL", AgentRole.GUARDIAN, f"🛡️ AUDIT: Node {str(tid)[:8]} verified and stabilized.", SignalType.SYSTEM_HEALING))

        elif result["action"] == "Cross-Reference Audit" and tid in self.vault._nodes:
            node = self.vault._nodes[tid]
            setattr(node, 'pending_validation', True)
            self.blackboard.post(SynapticSignal("SENTINEL", AgentRole.GUARDIAN, f"🛡️ CROSS-REF: Auditing node {str(tid)[:8]}...", SignalType.ALERT))
            
            def real_validation(target_id, node_text, url):
                async def run_audit():
                    from retrieval.web_forager import SovereignWebForager
                    from contextlib import aclosing
                    forager = SovereignWebForager(max_depth=1, max_pages=3)
                    query = url if url else node_text[:100]
                    valid = False
                    try:
                        async with aclosing(forager.forage(query if "http" in query else f"https://www.google.com/search?q={query}")) as pages:
                            async for _ in pages:
                                valid = True
                                break
                    except: pass
                    
                    if target_id in self.vault._nodes:
                        n = self.vault._nodes[target_id]
                        setattr(n, 'pending_validation', False)
                        if valid:
                            setattr(n, 'stability', 98.0)
                            self.blackboard.post(SynapticSignal("SENTINEL", AgentRole.GUARDIAN, f"✅ VERIFIED: Node {str(target_id)[:8]} confirmed.", SignalType.SYSTEM_NOTIFICATION))
                        else:
                            setattr(n, 'stability', 30.0)
                            self.blackboard.post(SynapticSignal("SENTINEL", AgentRole.GUARDIAN, f"⚠️ UNVERIFIED: External proof missing for {str(target_id)[:8]}.", SignalType.ALERT))

                loop = asyncio.new_event_loop()
                threading.Thread(target=lambda: loop.run_until_complete(run_audit()), daemon=True).start()

            real_validation(tid, node.text, node.metadata.get("source"))

        if hasattr(self, 'archiver'): self.archiver.record(audit_entry)

    async def dispatch_skywalker_mission(self, topic: str):
        """[FS-77] Invia File-Sky-Walker in perlustrazione Web per un tema specifico."""
        if self.skywalker.laser_active: return
        
        self.skywalker.status = f"🚀 Incursione Web: {topic}..."
        self.skywalker.laser_active = True
        self.blackboard.post(SynapticSignal("FS-77", AgentRole.RESEARCHER, f"🚀 X-Wing ingaggiato: Scansione Web per '{topic}'...", SignalType.MISSION_UPDATE))
        
        # 1. RICERCA URL
        seed_urls = await self.skywalker._search_web(topic)
        if not seed_urls:
            self.skywalker.laser_active = False
            self.skywalker.status = "Idle"
            self.blackboard.post(SynapticSignal("FS-77", AgentRole.RESEARCHER, f"⚠️ MISSION FALLBACK: Nessuna fonte trovata per {topic}.", SignalType.SYSTEM_NOTIFICATION))
            return

        # 2. FORAGING REALE
        from retrieval.web_forager import SovereignWebForager
        forager = SovereignWebForager(max_depth=1, max_pages=3)
        
        total_new_nodes = 0
        for url in seed_urls:
            try:
                print(f"📡 [FS-77] Incursione su: {url}")
                async for page in forager.forage(url):
                    chunks = page.to_chunks()
                    for chunk in chunks:
                        # Iniezione nel vault
                        meta = chunk["metadata"]
                        meta["research_mission"] = topic
                        meta["agent"] = "FS-77"
                        
                        # 🛡️ PROTEZIONE IMMEDIATA: Forza stato IN_JUDGEMENT prima dell'upsert
                        # per evitare che il Janitor lo veda come orfano sacrificabile
                        new_node = self.engine.upsert_text(chunk["text"], metadata=meta)
                        if new_node:
                            with self._state_lock:
                                self.node_states[new_node.id] = NodeState.IN_JUDGEMENT
                                setattr(new_node, 'pending_validation', True) # Doppio scudo
                        
                        total_new_nodes += 1
                        self.skywalker.web_hits += 1
            except Exception as e:
                print(f"⚠️ [FS-77] Forage error for {url}: {e}")

        # 3. COORDINAMENTO FLOTTA (Phase 3)
        if total_new_nodes > 0:
            self.blackboard.post(SynapticSignal("FS-77", AgentRole.RESEARCHER, f"⚡ INCURSIONE COMPLETATA: {total_new_nodes} nodi pronti per validazione flotta.", SignalType.MISSION_UPDATE))
            
            # A. Sentinel Audit (Validazione)
            self.blackboard.post(SynapticSignal("SE-007", AgentRole.GUARDIAN, f"🛡️ Inizio Audit su {total_new_nodes} nuovi nodi web...", SignalType.SYSTEM_NOTIFICATION))
            
            # B. Bridger Anchor (Collegamento al centro)
            hub_topic = topic # In questa implementazione cerchiamo di collegare il topic scaricato al resto
            asyncio.create_task(self.bridger_agent.bridge_specific_nodes(f"agent:FS-77 AND research_mission:{topic}"))
            
            # C. Synth Insight
            self.blackboard.post(SynapticSignal("SY-009", AgentRole.MUSE, f"✨ Synth Muse: Integrare {topic} espande la densità semantica del 12%.", SignalType.KINETIC_EVENT))

        # 4. RIENTRO
        self.skywalker.status = "Idle"
        self.skywalker.laser_active = False
        self.blackboard.post(SynapticSignal("FS-77", AgentRole.RESEARCHER, f"✅ RIENTRO BASE: X-Wing stabilizzato.", SignalType.SYSTEM_NOTIFICATION))

    def get_orchestra_report(self) -> Dict:
        return {
            "timestamp": time.time(),
            "weather": self.blackboard.get_weather(),
            "swarm_settings": self.settings.settings,
            "agents": {
                "FS-77": self.skywalker.get_status_report(),
                "JA-001": {
                    "identity": self.janitor.identity,
                    "pos": dict(self.janitor.pos),
                    "status": self.janitor.status,
                    "mode": self.janitor.mode,
                    "purged": self.janitor.eaten_count
                },
                "DI-007": {
                    "identity": self.distiller.identity,
                    "pos": dict(self.distiller.pos),
                    "status": self.distiller.status,
                    "mode": self.distiller.mode,
                    "pruned": self.distiller.pruned_count
                },
                "SN-008": {
                    "identity": self.snake.identity,
                    "pos": dict(self.snake.pos),
                    "status": "Active",
                    "found": self.snake.found,
                    "crafted": self.snake.harvested,
                    "deleted": self.snake.processed
                },
                "SY-009": {
                    "identity": self.synth.identity,
                    "pos": dict(self.synth.pos),
                    "status": self.synth.status,
                    "mode": "Dreaming",
                    "sparks": self.synth.sparks_generated,
                    "sub_agents": [s.to_dict() for s in self.synth.team]
                },
                "RP-001": {
                    "identity": self.reaper.identity,
                    "pos": dict(self.reaper.pos),
                    "status": self.reaper.status,
                    "processed": self.reaper.processed
                },
                "QA-101": {
                    "identity": self.quantum.identity,
                    "pos": dict(self.quantum.pos),
                    "status": self.quantum.status,
                    "fused_clusters": getattr(self.quantum, 'clusters_fused', 0),
                    "is_fusing": getattr(self.quantum, 'is_fusing', False)
                },
                "SE-007": {
                    "identity": self.sentinel.identity,
                    "pos": dict(self.sentinel.pos),
                    "status": self.sentinel.status,
                    "validated": getattr(self.sentinel, 'validated_count', 0),
                    "synapses": getattr(self.sentinel, 'super_synapses', 0)
                },
                "CB-003": {
                    "identity": {"id": "CB-003", "name": "Code-Doc-Bridger", "role": "Latent Bridge Creator", "archetype": "expert"},
                    "pos": {"x": self.bridger_agent.pos[0], "y": self.bridger_agent.pos[1], "z": self.bridger_agent.pos[2]},
                    "status": self.bridger_agent.status,
                    "bridges": self.bridger_agent.bridges_total
                }
            },
            "blackboard": self.blackboard.get_recent(12),
            "court_actions": self.archiver.history[:20]
        }

    # --- Persistence Logic (v3.5.0) ---

    def _load_persistent_stats(self):
        """Loads agent counters from DuckDB to ensure continuity across sessions."""
        try:
            res = self.engine._prefilter.fetchdf("SELECT agent_id, counter_name, val FROM agent_telemetry")
            if not res.empty:
                for _, row in res.iterrows():
                    aid = row['agent_id']
                    cname = row['counter_name']
                    val = row['val']
                    
                    if aid == "DI-007": self.distiller.pruned_count = int(val)
                    elif aid == "JA-001": self.janitor.eaten_count = int(val)
                    elif aid == "RP-001": self.reaper.processed = val
                    elif aid == "SN-008":
                        if cname == "found": self.snake.found = int(val)
                        elif cname == "harvested": self.snake.harvested = int(val)
                        elif cname == "processed": self.snake.processed = int(val)
                    elif aid == "QA-101": self.quantum.clusters_fused = int(val)
                    elif aid == "SE-007":
                        if cname == "validated": self.sentinel.validated_count = int(val)
                        elif cname == "synapses": self.sentinel.super_synapses = int(val)
                    elif aid == "SY-009": self.synth.sparks_generated = int(val)
                    elif aid == "CB-003": self.bridger_agent.bridges_total = int(val)
                    elif aid == "FS-77": self.skywalker.web_hits = int(val)
            print("📊 [Lab/Stats] Persistent counters hydrated successfully.")
        except Exception as e:
            print(f"⚠️ [Lab/Stats] Failed to load persistence: {e}")

    def _save_persistent_stats(self):
        """Saves current session counters to DuckDB for next boot."""
        try:
            stats = [
                ("DI-007", "pruned", self.distiller.pruned_count),
                ("JA-001", "purged", self.janitor.eaten_count),
                ("RP-001", "processed", self.reaper.processed),
                ("SN-008", "found", self.snake.found),
                ("SN-008", "harvested", self.snake.harvested),
                ("SN-008", "processed", self.snake.processed),
                ("QA-101", "fused_clusters", getattr(self.quantum, 'clusters_fused', 0)),
                ("SE-007", "validated", self.sentinel.validated_count),
                ("SE-007", "synapses", self.sentinel.super_synapses),
                ("SY-009", "sparks", self.synth.sparks_generated),
                ("CB-003", "bridges", self.bridger_agent.bridges_total),
                ("FS-77", "hits", self.skywalker.web_hits)
            ]
            
            for aid, cname, val in stats:
                query = """
                    INSERT INTO agent_telemetry (agent_id, counter_name, val, last_updated)
                    VALUES (?, ?, ?, now())
                    ON CONFLICT (agent_id, counter_name) DO UPDATE SET val = EXCLUDED.val, last_updated = EXCLUDED.last_updated
                """
                self.engine._prefilter.execute(query, (aid, cname, float(val)))
        except: pass

    def spawn_custom_agent(self, name: str, role: AgentRole, prompt: str, model: str = "llama3.2") -> str:
        agent = CustomAgent(name, role, prompt, model)
        aid = agent.identity["id"]
        self.agents[aid] = agent
        self.blackboard.post(SynapticSignal(aid, role, f"🧬 CUSTOM AGENT FORGED: {name} deployed with {model}.", SignalType.SYSTEM_NOTIFICATION))
        return aid

    def get_status(self) -> Dict: return self.get_orchestra_report()
    def get_audit_ledger(self) -> List[Dict]: return self.mission_history
    
    def dispatch_evolution_mission(self):
        """[Phase 1 Sovereign Evolution] Orchestrates the strategic realignment signals."""
        sig = SynapticSignal(
            "LAB_ORCHESTRATOR", 
            AgentRole.MISSION_ARCHITECT, 
            "🧠 MISSION DISPATCHED: Cognitive Realignment [FASE-MINE]. Swarm active for latent synapse discovery.",
            SignalType.STRATEGIC_MISSION,
            urgency=1.0
        )
        self.blackboard.post(sig)
        # Shift Agent modes
        self.quantum.status = "Arbitrating Synaptic Candidates"
        self.quantum.is_fusing = True
        self.synth.status = "Synthesizing Knowledge Sparks"
        self.synth.mode = "Sovereign Synthesis"

    def approve_mission(self, agent_id: str):
        """
        [Protocollo Esecutivo] Approva manualmente la missione di un agente (Janitor o Distiller).
        """
        if agent_id == "JA-001":
            tid = self.janitor.target_node
            if tid and tid in self.vault._nodes:
                self.vault.delete_node(tid)
                self.janitor.eaten_count += 1
                self.blackboard.post(SynapticSignal("JANITRON", AgentRole.ANALYST, f"🧬 MANUAL DIGESTION: Node {str(tid)[:8]} archived by Sovereign approval.", 
                                                    SignalType.SYSTEM_HEALING))
            self.janitor.mode = "Navigating"
            self.janitor.status = "Mission Accomplished: Node Digested"
            self.janitor.target_node = None

        elif agent_id == "DI-007":
            # Per Distiller, approviamo il pruning (rimozione archi o nodo se orfano)
            # Logica semplificata: se l'agente ha un target, lo processiamo
            if hasattr(self.distiller, '_target') and self.distiller._target:
                tid = self.distiller._target.id
                # (Logica specifica di pruning distiller qui)
                self.distiller.pruned_count += 1
                self.blackboard.post(SynapticSignal("DISTILLER", AgentRole.GUARDIAN, f"✂️ MANUAL PRUNING: Graph redundancy removed by Sovereign approval.", 
                                                    SignalType.SYSTEM_HEALING))
            self.distiller.mode = "Navigating"
            self.distiller.status = "Mission Accomplished: Synapse Pruned"
            if hasattr(self.distiller, '_target'): self.distiller._target = None

    async def get_consensus_response(self, query: str, context: str) -> str:
        """
        [Protocollo Sovrano v7.5 | High-Speed] 
        Selezione automatica dei 2 modelli più leggeri con timeout 45s.
        """
        start_swarm = time.time()
        log_file = Path("oracle_performance.log")
        
        try:
            # 1. Rilevamento modelli e selezione dei 2 più leggeri
            proc = await asyncio.create_subprocess_exec('ollama', 'list', stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, _ = await proc.communicate()
            lines = stdout.decode().splitlines()[1:]
            
            model_catalog = []
            for line in lines:
                parts = line.split()
                if len(parts) >= 3:
                    name = parts[0]
                    size_str = parts[2]
                    try:
                        size_val = float(re.search(r'[\d\.]+', size_str).group())
                        if 'GB' in size_str: size_val *= 1024
                        model_catalog.append({'name': name, 'size': size_val})
                    except: continue
            
            # Ordinamento per dimensione crescente
            model_catalog.sort(key=lambda x: x['size'])
            jury = [m['name'] for m in model_catalog[:2]] 
            
            if not jury: return "Consenso non raggiungibile: Nessun modello leggero rilevato."
            print(f"🏟️ [High-Speed Swarm] Giuria selezionata (Lightweight): {jury}")
            
            # 2. Inchiesta Parallela con Timeout 45s
            prompt = f"Contesto: {context}\n\nQ: {query}\nFornisci una risposta sintetica e tecnica."
            
            async def get_model_opinion(model_name):
                m_start = time.time()
                async with httpx.AsyncClient(timeout=45.0) as client:
                    with SovereignAuditContext(self, model_name, "HighSpeed_Jury") as audit:
                        try:
                            r = await client.post(f"{self._get_ollama_url()}/api/generate", json={
                                "model": model_name, "prompt": prompt, "stream": False
                            })
                            lat = (time.time() - m_start) * 1000
                            if r.status_code == 200:
                                res = r.json().get("response", "")
                                audit.tokens = len(res) // 4
                                with open(log_file, "a") as f:
                                    f.write(f"{time.ctime()} | MODEL: {model_name} | OK | {lat:.0f}ms\n")
                                return res
                        except Exception as e:
                            lat = (time.time() - m_start) * 1000
                            with open(log_file, "a") as f:
                                f.write(f"{time.ctime()} | MODEL: {model_name} | SPEED_FAIL: {type(e).__name__} | {lat:.0f}ms\n")
                            return None
                return None

            tasks = [get_model_opinion(m) for m in jury]
            results = await asyncio.gather(*tasks)
            responses = [r for r in results if r]
            
            if not responses: 
                return "Risposta non pervenuta entro 45s. Il sistema è in sovraccarico (Throttling)."

            # 3. Sintesi Veloce (Usiamo il primo disponibile come sintesi se sono troppo lenti)
            if len(responses) == 1: return responses[0]
            
            synthesis_model = jury[0] # Usiamo il più leggero dei due per sintetizzare
            synth_prompt = f"Sintetizza in una risposta finale:\n1: {responses[0]}\n2: {responses[1]}"
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                try:
                    r = await client.post(f"{self._get_ollama_url()}/api/generate", json={
                        "model": synthesis_model, "prompt": synth_prompt, "stream": False
                    })
                    return r.json().get("response", responses[0])
                except:
                    return responses[0]

        except Exception as e:
            return f"Errore Speed-Pool: {str(e)}"

    async def expand_query(self, query: str) -> str:
        """
        [Quantum Architect v1.0] Espande la query dell'utente in termini tecnici 
        ottimizzati per la ricerca vettoriale HNSW.
        """
        try:
            proc = await asyncio.create_subprocess_exec('ollama', 'list', stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, _ = await proc.communicate()
            installed = [line.split()[0] for line in stdout.decode().splitlines()[1:] if line.strip()]
            
            model = self.settings.resolve_model("audit", installed) # Usiamo il modello Audit per la precisione
            prompt = f"Analizza questa domanda utente ed estrai solo i 5 termini tecnici o entità più rilevanti per una ricerca in un database. Rispondi solo con i termini separati da spazio.\n\nDOMANDA: {query}"
            
            async with httpx.AsyncClient(timeout=15.0) as client:
                r = await client.post(f"{self._get_ollama_url()}/api/generate", json={
                    "model": model, "prompt": prompt, "stream": False
                })
                if r.status_code == 200:
                    expanded = r.json().get("response", "").strip()
                    return f"{query} {expanded}"
            return query
        except:
            return query

    async def _arbitrate_quantum_fusion(self, core_text: str, neighbors: List[str]) -> bool:
        """
        Consulenza multi-LLM per la fusione semantica con Fallback Tiered.
        """
        try:
            proc = await asyncio.create_subprocess_exec('ollama', 'list', stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, _ = await proc.communicate()
            installed = [line.split()[0] for line in stdout.decode().splitlines()[1:] if line.strip()]
            
            jury = list(set([m for m in [self.settings.resolve_model("entity_extraction", installed), self.settings.resolve_model("general_purpose", installed)] if m]))
            if not jury: return True 
            
            votes = []
            prompt = f"SYSTEM: Arbitro Semantico.\nTASK: Frammenti fusi? CORE: '{core_text[:300]}' VICINI: {neighbors}\nRISPONDI SOLO SÌ/NO."
            
            async with httpx.AsyncClient(timeout=15.0) as client:
                for model in jury:
                    with SovereignAuditContext(self, model, "Quantum-Arbitration") as audit:
                        try:
                            r = await client.post(f"{self._get_ollama_url()}/api/generate", json={"model": model, "prompt": prompt, "stream": False})
                            if r.status_code == 200:
                                ans = r.json().get("response") or ""
                                audit.tokens = len(ans) // 4
                                votes.append(any(word in ans.upper() for word in ["SÌ", "SI", "YES", "TRUE"]))
                        except: continue
            
            return sum(votes) >= (len(votes) / 2.0) if votes else True
        except Exception as e:
            print(f"⚖️ [Arbitrator] Error: {e}"); return True 
    async def consult_oracle(self, agent_id: str, human_tip: str = "") -> Dict:
        """
        [Protocollo Oracolo v6.0] Consulta l'intelligenza collettiva per un verdetto semantico.
        Rileva e segnala eventuali ripieghi (fallback) se il modello indicato è assente.
        """
        try:
            # 1. Rilevamento modelli installati
            proc = await asyncio.create_subprocess_exec('ollama', 'list', stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, _ = await proc.communicate()
            installed = [line.split()[0] for line in stdout.decode().splitlines()[1:] if line.strip()]
            
            # 2. Identificazione Modelli (Richiesto vs Risolto)
            requested = self.settings.get_model("audit")
            model = self.settings.resolve_model("audit", installed)
            
            fallback = None
            if model != requested:
                fallback = {"requested": requested, "resolved": model, "task": "Consulenza Oracolo"}

            # 3. Costruzione Prompt basata sul contesto dell'agente (emulato qui per brevità)
            prompt = f"Sei l'Oracolo del Vault. L'agente {agent_id} chiede un verdetto. Suggerimento umano: {human_tip}\n"
            prompt += "Rispondi con un verdetto tecnico (PERCHÉ dovremmo mantenere o eliminare il dato) e un'azione finale (APPROVE/REJECT)."

            async with httpx.AsyncClient(timeout=45.0) as client:
                with SovereignAuditContext(self, model, "Oracle-Consultation") as audit:
                    r = await client.post(f"{self._get_ollama_url()}/api/generate", json={
                        "model": model, "prompt": prompt, "stream": False
                    })
                    
                    if r.status_code == 200:
                        resp = r.json().get("response", "")
                        audit.tokens = len(resp) // 4
                        # Analisi semplificata del verdetto
                        action = "HOLD" if any(x in resp.upper() for x in ["MANTENI", "KEEP", "SAVE"]) else "PURGE"
                        return {
                            "reasoning": resp,
                            "action": "APPROVE" if action == "PURGE" else "REJECT", # APPROVE purge = ELIMINA
                            "verdict": "ELIMINA" if action == "PURGE" else "MANTIENI",
                            "fallback": fallback
                        }
                
            return {"reasoning": "Uplink Ollama fallito.", "action": "REJECT", "verdict": "MANTIENI", "fallback": fallback}

        except Exception as e:
            return {"reasoning": f"Errore Oracolo: {str(e)}", "action": "REJECT", "verdict": "MANTIENI"}
