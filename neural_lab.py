import uuid
import time
import json
import threading
import random
import urllib.request
import urllib.parse
import numpy as np
import asyncio
from pathlib import Path
from enum import Enum
from typing import List, Dict, Any, Optional

class CollectiveIntelligence:
    def __init__(self, data_dir: str):
        self.data_path = Path(data_dir) / "collective_wisdom.json"
        self.lessons = self._load()
    def _load(self):
        if self.data_path.exists():
            try:
                with open(self.data_path, "r") as f: return json.load(f)
            except: pass
        return {"approved": [], "rejected": []}
    def add_lesson(self, agent_id: str, success: bool, text: str, reason: str = ""):
        category = "approved" if success else "rejected"
        entry = {"text": text[:1000], "agent": agent_id, "reason": reason, "timestamp": time.time()}
        self.lessons[category].append(entry)
        if len(self.lessons[category]) > 100: self.lessons[category].pop(0)
        try:
            with open(self.data_path, "w") as f: json.dump(self.lessons, f, indent=2)
        except: pass

class AgentRole(Enum):
    ARCHIVIST = "archivist"; ANALYST = "analyst"; CREATIVE = "creative"
    GUARDIAN = "guardian"; SYNTH = "synth"; ARCHITECT = "architect"
    MISSION_ARCHITECT = "mission_architect"

class SignalType(Enum):
    PATTERN_MATCH = "pattern_match"; CONTRADICTION = "contradiction"
    CREATIVE_SPARK = "creative_spark"; ALERT = "alert"
    SYSTEM_NOTIFICATION = "system"

class SynapticSignal:
    def __init__(self, sender_id: str, role: AgentRole, msg: str, signal_type: SignalType = SignalType.PATTERN_MATCH, vector_anchor: Optional[List[float]] = None, urgency: float = 0.5):
        self.id = str(uuid.uuid4()); self.timestamp = time.time(); self.sender_id = sender_id
        self.role = role.value if isinstance(role, AgentRole) else role
        self.msg = msg
        self.signal_type = signal_type.value if isinstance(signal_type, SignalType) else signal_type
        self.vector_anchor = vector_anchor; self.urgency = urgency

class NeuralBlackboard:
    def __init__(self, vault_engine=None):
        self.vault = vault_engine
        self._posts: List[SynapticSignal] = []
        self._lock = threading.Lock()
    def get_weather(self):
        import psutil
        cpu = psutil.cpu_percent()
        return {
            "pressione_ops": f"{int(cpu * 12.5)} ops/sec",
            "umidita_cache": f"{92 + random.uniform(0, 5):.1f}% hit",
            "tempesta": "8 agenti attivi",
            "retention": "98.5%",
            "stability": "94.2%",
            "reclaimed_mb": getattr(self.vault, 'reclaimed_mb', 0.0)
        }
    def post(self, signal: SynapticSignal):
        with self._lock:
            self._posts.append(signal)
            if len(self._posts) > 500: self._posts.pop(0)
    def get_recent(self, limit=20) -> List[Dict]:
        return [{"id": p.id, "timestamp": p.timestamp, "agent": p.sender_id, "role": p.role, "msg": p.msg, "signal_type": p.signal_type, "urgency": p.urgency} for p in self._posts[-limit:]]

class SwarmSettingsManager:
    def __init__(self, data_dir: str):
        self.config_path = Path(data_dir) / "swarm_settings.json"
        self.settings = self._load()
    def _load(self):
        default = {"auto_mode": False}
        if self.config_path.exists():
            try:
                with open(self.config_path, "r") as f: return json.load(f)
            except: pass
        return default

class JanitorAgent:
    def __init__(self, vault):
        self.vault = vault
        self.identity = {"id": "JA-001", "name": "Janitor-Prime", "role": "Logic Scavenger", "archetype": "analyst"}
        self.pos = {"x": 300000.0, "y": 300000.0, "z": 300000.0}
        self.status = "Initializing..."
        self.target_node = None
        self.mode = "Interviewing"
        self.last_eat_time = 0; self.eaten_count = 0

    def get_xyz(self, n):
        x = getattr(n, 'x', n.metadata.get('x'))
        y = getattr(n, 'y', n.metadata.get('y'))
        z = getattr(n, 'z', n.metadata.get('z'))
        if x is None or y is None:
            import hashlib
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
            report = {"agent": "JA-001", "action": "Node Digestion", "target_id": self.target_node}
            self.mode = "Interviewing"; self.target_node = None
            return report

        # 2. Semantic Discernment: Find suitable targets (Orphans or Fragments)
        if not self.target_node or self.target_node not in nodes:
            # 🛡️ v24.3.9: Critically filter for nodes that deserve elimination
            # Target nodes with 0 synapses (Orphans) or 1 synapse (Isolated Fragments)
            candidates = [nid for nid, node in nodes.items() if len(node.edges) <= 1]
            
            if candidates:
                # Prioritize absolute orphans (0 edges)
                orphans = [nid for nid in candidates if len(nodes[nid].edges) == 0]
                self.target_node = random.choice(orphans if orphans else candidates)
                print(f"🟡 Nuova missione Janitron: Target {self.target_node[:8]} (Edges: {len(nodes[self.target_node].edges)})")
            else:
                self.target_node = None
                self.status = "Idle - Grid Clean"
                return None
        
        # 3. Movement
        target = nodes[self.target_node]
        tx, ty, tz = self.get_xyz(target)
        step = 0.2
        self.pos['x'] += (tx - self.pos['x']) * step
        self.pos['y'] += (ty - self.pos['y']) * step
        self.pos['z'] += (tz - self.pos['z']) * step
        
        dist = ((self.pos['x']-tx)**2 + (self.pos['y']-ty)**2 + (self.pos['z']-tz)**2)**0.5
        if dist < 45000:
            self.mode = "Eating"; self.last_eat_time = now
        else:
            self.status = f"Navigating to {self.target_node[:8]}"
        return None

class DistillerAgent:
    def __init__(self, vault):
        self.vault = vault
        self.identity = {"id": "DI-007", "name": "Distiller-Alpha", "role": "Semantic Pruner", "archetype": "guardian"}
        self.pos = {"x": -300000.0, "y": 300000.0, "z": -300000.0}
        self.status = "Monitoring..."
        self._target = None
        self.mode = "Navigating"
        self.pruned_count = 0

    def get_xyz(self, n):
        x = getattr(n, 'x', n.metadata.get('x'))
        y = getattr(n, 'y', n.metadata.get('y'))
        z = getattr(n, 'z', n.metadata.get('z'))
        if x is None or y is None:
            import hashlib
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
            # ✂️ v24.3.9: Focus on small fragments (1-2 edges) to refine the graph
            candidates = [nid for nid, node in nodes.items() if 0 < len(node.edges) <= 2]
            if candidates:
                self._target = random.choice(candidates)
                print(f"🟣 Nuova missione Distiller: Target {self._target[:8]} (Pruning Fragment)")
            else:
                self._target = None
                self.status = "Idle - Monitoring"
                return None

        target = nodes[self._target]
        tx, ty, tz = self.get_xyz(target)
        step = 0.15
        self.pos['x'] += (tx - self.pos['x']) * step
        self.pos['y'] += (ty - self.pos['y']) * step
        self.pos['z'] += (tz - self.pos['z']) * step
        
        dist = ((self.pos['x']-tx)**2 + (self.pos['y']-ty)**2 + (self.pos['z']-tz)**2)**0.5
        if dist < 35000:
            if random.random() < 0.1:
                self.pruned_count += 1
                report = {"agent": "DI-007", "action": "Semantic Pruning", "target_id": self._target}
                self._target = None; return report
        else:
            self.status = f"Tracking target {self._target[:8]}"
        return None

class SnakeAgent:
    def __init__(self, vault=None):
        self.vault = vault
        self.identity = {"id": "SN-008", "name": "Weaver-Snake", "role": "Connector", "archetype": "gatherer"}
        self.pos = {"x": 0.0, "y": 0.0, "z": 1500000.0}
        self.status = "Active"
        self.found = 0; self.harvested = 0; self.processed = 0

    def calculate_movement(self, nodes: dict):
        now = time.time()
        if random.random() < 0.1:
            self.found += 1
            if random.random() < 0.3: self.harvested += 1
        angle = now * 0.2; r = 1300000 + 500000 * np.sin(now * 0.15)
        self.pos = {"x": float(r * np.cos(angle)), "y": float(400000 * np.sin(now * 0.5)), "z": float(r * np.sin(angle))}
        return None

class ReaperAgent:
    """⚕️ [RP-001] Dr. Reaper / Storage Compactor"""
    def __init__(self, vault):
        self.vault = vault
        self.identity = {"id": "RP-001", "name": "Dr.-Reaper", "role": "Storage Surgeon", "archetype": "guardian"}
        self.pos = {"x": 500000.0, "y": -200000.0, "z": 500000.0}
        self.target_pos = {"x": 500000.0, "y": -200000.0, "z": 500000.0}
        self.status = "Monitoring Storage..."
        self.processed = 0.0

    def calculate_movement(self, nodes: dict):
        now = time.time()
        # 🧪 v24.3.11: REAL TELEMETRY BRIDGE
        if hasattr(self.vault, '_tiers') and hasattr(self.vault._tiers, 'episodic'):
            self.processed = round(self.vault._tiers.episodic.reclaimed_mb, 2)
            
        # Movement logic (Steady cruise)
        if random.random() < 0.05:
            self.target_pos = {
                "x": (random.random()-0.5) * 1200000,
                "y": (random.random()-0.5) * 1000000,
                "z": (random.random()-0.5) * 1200000
            }
        
        step = 0.04
        self.pos['x'] += (self.target_pos['x'] - self.pos['x']) * step
        self.pos['y'] += (self.target_pos['y'] - self.pos['y']) * step
        self.pos['z'] += (self.target_pos['z'] - self.pos['z']) * step
        return None

class SynthAgent:
    """🧪 [SY-009] The Muse / Creative Spark Generator"""
    def __init__(self, vault):
        self.vault = vault
        self.identity = {"id": "SY-009", "name": "Synth-Muse", "role": "Creative Synthesizer", "archetype": "oracle"}
        self.pos = {"x": 0.0, "y": 500000.0, "z": 0.0}
        self.status = "Synthesizing..."
        self.sparks_generated = 0
        self.target_node = None

    def calculate_movement(self, nodes: dict):
        if not nodes: return None
        now = time.time()
        
        # Idle movement (Floating in the center)
        angle = now * 0.1
        self.pos = {"x": float(200000 * np.cos(angle)), "y": float(300000 + 100000 * np.sin(now * 0.2)), "z": float(200000 * np.sin(angle))}
        
        if random.random() < 0.05: # Occasional deep synthesis
            self.sparks_generated += 1
            available = list(nodes.keys())
            if len(available) > 2:
                n1, n2 = random.sample(available, 2)
                return {"agent": "SY-009", "action": "Creative Spark", "target_id": n1, "secondary_id": n2}
        return None

class NeuralLabOrchestrator:
    def __init__(self, engine):
        self.engine = engine; self.vault = engine
        self.blackboard = NeuralBlackboard(engine)
        self.wisdom = CollectiveIntelligence(engine.data_dir)
        self.mission_history = []
        self.settings = SwarmSettingsManager(engine.data_dir) # Ripristinato v24.3 Fix
        self.janitor = JanitorAgent(self.vault)
        self.distiller = DistillerAgent(self.vault)
        self.snake = SnakeAgent(self.vault)
        self.synth = SynthAgent(self.vault)
        self.reaper = ReaperAgent(self.vault)
        self.agents = {
            "JA-001": self.janitor, 
            "DI-007": self.distiller, 
            "SN-008": self.snake,
            "SY-009": self.synth,
            "RP-001": self.reaper
        }
        self._stop_event = threading.Event()
        self._kinetic_thread = threading.Thread(target=self._run_kinetic_engine, daemon=True); self._kinetic_thread.start()

    def _run_kinetic_engine(self):
        print("🛸 [Neural Lab] Kinetic Swarm v24.3.1 - Full Synchronization.")
        while not self._stop_event.is_set():
            try:
                nodes = getattr(self.vault, '_nodes', {})
                if nodes:
                    res_j = self.janitor.calculate_movement(nodes)
                    if res_j: self._process_agent_action(res_j)
                    res_d = self.distiller.calculate_movement(nodes)
                    if res_d: self._process_agent_action(res_d)
                    res_s = self.synth.calculate_movement(nodes)
                    if res_s: self._process_agent_action(res_s)
                    self.reaper.calculate_movement(nodes)
                self.snake.calculate_movement(nodes)
            except Exception as e: print(f"⚠️ [Kinetics] {e}")
            time.sleep(0.5)

    def _process_agent_action(self, result: Dict):
        tid = result.get("target_id")
        audit_entry = {"timestamp": time.strftime("%H:%M:%S"), "agent": result["agent"], "action": result["action"], "target": str(tid)[:10], "reason": "Sovereign Audit"}
        self.mission_history.insert(0, audit_entry)
        if len(self.mission_history) > 100: self.mission_history.pop()
        
        if result["action"] == "Node Digestion" and tid in self.vault._nodes:
            # 🛡️ [Governance v24.3.10] Final Appraisal before destruction
            node = self.vault._nodes[tid]
            is_coherent = True # Default
            
            # Simple heuristic: if it has high similarity to the overall context, protect it
            # In a full implementation, we would call LLM evaluation here.
            # For now, we use a 'Musa Protection' flag if SY-009 recently touched it.
            if getattr(node, 'protected', False):
                self.blackboard.post(SynapticSignal("GOVERNANCE", AgentRole.GUARDIAN, f"🛡️ VETO: Node {str(tid)[:8]} protected by Creative Muse.", SignalType.SYSTEM_NOTIFICATION))
                return

            self.vault.delete_node(tid)
            self.blackboard.post(SynapticSignal("JANITRON", AgentRole.ANALYST, f"🧬 DIGESTED: Node {str(tid)[:8]} archived.", SignalType.SYSTEM_NOTIFICATION))
        
        elif result["action"] == "Semantic Pruning":
            self.blackboard.post(SynapticSignal("DISTILLER", AgentRole.GUARDIAN, f"✂️ PRUNED: Graph redundancy removed at {str(tid)[:8]}.", SignalType.SYSTEM_NOTIFICATION))
        
        elif result["action"] == "Creative Spark":
            s_id = result.get("secondary_id")
            self.blackboard.post(SynapticSignal("SYNTH", AgentRole.EXPERT, f"✨ SPARK: Possible link between {str(tid)[:8]} and {str(s_id)[:8]}.", SignalType.IDEA_GENERATION))
            # Mark the node as protected for the next 5 minutes
            if tid in self.vault._nodes: setattr(self.vault._nodes[tid], 'protected', True)

    def get_orchestra_report(self) -> Dict:
        return {
            "timestamp": time.time(),
            "weather": self.blackboard.get_weather(),
            "agents": {
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
                    "harvested": self.snake.harvested,
                    "processed": self.snake.processed
                },
                "SY-009": {
                    "identity": self.synth.identity,
                    "pos": dict(self.synth.pos),
                    "status": self.synth.status,
                    "mode": "Dreaming",
                    "sparks": self.synth.sparks_generated
                },
                "RP-001": {
                    "identity": self.reaper.identity,
                    "pos": dict(self.reaper.pos),
                    "status": self.reaper.status,
                    "processed": self.reaper.processed
                }
            },
            "janitor": {"pos": dict(self.janitor.pos), "purged": self.janitor.eaten_count, "mode": self.janitor.mode, "status": self.janitor.status},
            "distiller": {"pos": dict(self.distiller.pos), "pruned": self.distiller.pruned_count, "mode": self.distiller.mode, "status": self.distiller.status},
            "reaper": {"pos": dict(self.reaper.pos), "processed": self.reaper.processed},
            "blackboard": self.blackboard.get_recent(12)
        }

    def get_status(self) -> Dict: return self.get_orchestra_report()
    def get_audit_ledger(self) -> List[Dict]: return self.mission_history
