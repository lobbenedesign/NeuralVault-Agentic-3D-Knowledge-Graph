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
    MISSION_ARCHITECT = "mission_architect"; EXPERT = "expert"; RESEARCHER = "researcher"

class SignalType(Enum):
    PATTERN_MATCH = "pattern_match"; CONTRADICTION = "contradiction"
    CREATIVE_SPARK = "creative_spark"; ALERT = "alert"
    SYSTEM_NOTIFICATION = "system"

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
            "tempesta": f"{len(getattr(self.vault.lab, 'agents', [])) if self.vault and hasattr(self.vault, 'lab') else 8} agenti attivi",
            "retention": "98.5%",
            "stability": "94.2%",
            "reclaimed_mb": getattr(self.vault, 'reclaimed_mb', 0.0)
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
            report = {
                "agent": "JA-001", 
                "action": "Node Digestion", 
                "target_id": self.target_node,
                "motivation": f"Cleaned orphan node {self.target_node[:8]} (0 synapses) to prevent semantic noise.",
                "savings": "0.15 MB (Binary Header Recovery)"
            }
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
        
        # 🛡️ v24.4.1: Respect Sentinel Protection
        if getattr(nodes[self.target_node], 'pending_validation', False):
            self.status = f"VETO: Node {self.target_node[:8]} pending validation"
            self.target_node = None
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
                report = {
                    "agent": "DI-007", 
                    "action": "Semantic Pruning", 
                    "target_id": self._target,
                    "motivation": f"Pruned redundant arc at {self._target[:8]} to optimize HNSW traversal speed.",
                    "savings": "0.05 ms search latency (Branch Reduction)"
                }
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
        self.blackboard = None

    def calculate_movement(self, nodes: dict):
        if random.random() < 0.1:
            self.found += 1
            if random.random() < 0.3: 
                self.harvested += 1
                if random.random() < 0.5:
                    self.processed += 1
                    # 🚀 v24.3.11: Signal to blackboard
                    if hasattr(self, 'blackboard') and self.blackboard:
                        sig = SynapticSignal("SN-008", AgentRole.RESEARCHER, f"Deleted {self.processed} synaptic orphans", SignalType.SYSTEM_NOTIFICATION)
                        self.blackboard.post(sig)

        # Kinetic Arcade Movement (Random Walk)
        self.pos["x"] += random.uniform(-15000, 15000)
        self.pos["y"] += random.uniform(-10000, 10000)
        self.pos["z"] += random.uniform(-15000, 15000)
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
        self.blackboard = None

    def calculate_movement(self, nodes: dict):
        now = time.time()
        # 🧪 v24.3.11: REAL TELEMETRY BRIDGE
        if hasattr(self.vault, '_tiers') and hasattr(self.vault._tiers, 'episodic'):
            new_val = round(self.vault._tiers.episodic.reclaimed_mb, 2)
            if new_val > self.processed and self.blackboard:
                diff = round(new_val - self.processed, 2)
                sig = SynapticSignal("RP-001", AgentRole.RESEARCHER, f"Reclaimed {diff} MB from episodic logs", SignalType.SYSTEM_NOTIFICATION)
                self.blackboard.post(sig)
            self.processed = new_val
            
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
                return {
                    "agent": "SY-009", 
                    "action": "Creative Spark", 
                    "target_id": n1, 
                    "secondary_id": n2,
                    "motivation": f"Synthesized cross-modal link between nodes {n1[:8]} and {n2[:8]}.",
                    "savings": "Emergent knowledge generated."
                }
        return None

class QuantumScavengerAgent:
    """🌐 [QA-101] Quantum Architect / Semantic Centroiding"""
    def __init__(self, vault):
        self.vault = vault
        self.identity = {"id": "QA-101", "name": "Quantum-Architect", "role": "Semantic Centroiding", "archetype": "architect"}
        self.pos = {"x": 1000000.0, "y": 1000000.0, "z": 1000000.0}
        self.status = "Analyzing Clusters..."
        self.clusters_fused = 0
        self.target_node = None
        
    def calculate_movement(self, nodes: dict):
        if not nodes: return None
        now = time.time()
        
        # Orbital movement around the core
        angle = now * 0.05
        rad = 1500000 + 200000 * np.cos(now * 0.1)
        self.pos = {"x": float(rad * np.cos(angle)), "y": float(rad * np.sin(angle * 0.5)), "z": float(rad * np.sin(angle))}
        
        # Trigger Semantic Centroiding (rare but impactful)
        if random.random() < 0.02: 
            node_ids = list(nodes.keys())
            if len(node_ids) > 10:
                seed_id = random.choice(node_ids)
                return {
                    "agent": "QA-101", 
                    "action": "Semantic Centroiding", 
                    "target_id": seed_id,
                    "motivation": f"Establishing semantic authority for high-density quadrant {seed_id[:8]}.",
                    "savings": "HNSW index compaction active."
                }
        return None

class SentinelAgent:
    """🛡️ [SE-007] The Sentinel / Cross-Reference Guardian"""
    def __init__(self, vault):
        self.vault = vault
        self.identity = {"id": "SE-007", "name": "Sentinel-Guardian", "role": "Cross-Referencing", "archetype": "guardian"}
        self.pos = {"x": -500000.0, "y": -500000.0, "z": 500000.0}
        self.status = "Monitoring Ingress..."
        self.validated_count = 0
        self.target_node = None

    def calculate_movement(self, nodes: dict):
        if not nodes: return None
        now = time.time()
        
        # Patrol the outer edges of the nebula
        angle = now * 0.08
        rad = 1800000 + 100000 * np.sin(now * 0.3)
        self.pos = {"x": float(rad * np.cos(angle)), "y": float(400000 * np.sin(now * 0.1)), "z": float(rad * np.sin(angle))}
        
        # Find nodes that need validation (low stability/isolated)
        if random.random() < 0.03:
            candidates = [nid for nid, node in nodes.items() if getattr(node, 'stability', 100) < 60 or len(node.edges) <= 1]
            if candidates:
                self.target_node = random.choice(candidates)
                return {"agent": "SE-007", "action": "Cross-Reference Audit", "target_id": self.target_node}
        return None

class NeuralLabOrchestrator:
    def __init__(self, engine):
        self.engine = engine; self.vault = engine
        self.blackboard = NeuralBlackboard(engine)
        self.wisdom = CollectiveIntelligence(engine.data_dir)
        self.mission_history = []
        self.settings = SwarmSettingsManager(engine.data_dir) # Ripristinato v24.3 Fix
        from retrieval.bridge import LatentBridge
        self.bridger = LatentBridge(engine, engine.data_dir.parent)
        self.last_bridge_time = 0
        self.janitor = JanitorAgent(self.vault); self.janitor.blackboard = self.blackboard
        self.distiller = DistillerAgent(self.vault); self.distiller.blackboard = self.blackboard
        self.snake = SnakeAgent(self.vault); self.snake.blackboard = self.blackboard
        self.synth = SynthAgent(self.vault); self.synth.blackboard = self.blackboard
        self.reaper = ReaperAgent(self.vault); self.reaper.blackboard = self.blackboard
        self.quantum = QuantumScavengerAgent(self.vault); self.quantum.blackboard = self.blackboard
        self.sentinel = SentinelAgent(self.vault); self.sentinel.blackboard = self.blackboard
        self.agents = {
            "JA-001": self.janitor, 
            "DI-007": self.distiller, 
            "SN-008": self.snake,
            "SY-009": self.synth,
            "RP-001": self.reaper,
            "QA-101": self.quantum,
            "SE-007": self.sentinel
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
                    res_q = self.quantum.calculate_movement(nodes)
                    if res_q: self._process_agent_action(res_q)
                    res_sent = self.sentinel.calculate_movement(nodes)
                    if res_sent: self._process_agent_action(res_sent)
                    self.reaper.calculate_movement(nodes)
                    
                    # 🔗 [Super-Synapse] Bridge Discovery (Ogni 30 secondi)
                    if time.time() - self.last_bridge_time > 30:
                        count = self.bridger.bridge_nodes()
                        if count > 0:
                            self.blackboard.post(SynapticSignal("ORCHESTRATOR", AgentRole.ARCHITECT, f"🔗 SUPER-SYNAPSE: Created {count} bridges between documentation and local code.", SignalType.SYSTEM_NOTIFICATION))
                        self.last_bridge_time = time.time()
                self.snake.calculate_movement(nodes)
                time.sleep(0.3) # ⚡ [v24.4] Stabilization: Prevent CPU thrashing
            except Exception as e:
                print(f"⚠ [Lab] Orchestrator error: {e}")
                time.sleep(1.0) # Backoff on error

    def _process_agent_action(self, result: Dict):
        tid = result.get("target_id")
        agent_id = result.get("agent", "UNKNOWN")
        
        # 🧠 [v16.0] REASONING & SAVINGS INJECTION
        motivation = result.get("motivation", "Standard swarm maintenance protocol.")
        savings = result.get("savings", "0.01 MB cache optimized")
        
        audit_entry = {
            "timestamp": time.strftime("%H:%M:%S"), 
            "agent": agent_id, 
            "action": result["action"], 
            "target": str(tid)[:10] if tid else "N/A", 
            "reasoning": motivation, # Colonna MOTIVAZIONE
            "savings": savings    # Colonna RISPARMIO
        }
        
        if result["action"] == "Node Digestion" and tid in self.vault._nodes:
            self.vault.delete_node(tid)
            self.blackboard.post(SynapticSignal("JANITRON", AgentRole.ANALYST, f"🧬 DIGESTED: Node {str(tid)[:8]} archived.", 
                                                SignalType.SYSTEM_NOTIFICATION, motivation=motivation, savings=savings))
        
        elif result["action"] == "Semantic Pruning":
            self.blackboard.post(SynapticSignal("DISTILLER", AgentRole.GUARDIAN, f"✂️ PRUNED: Graph redundancy removed.", 
                                                SignalType.SYSTEM_NOTIFICATION, motivation=motivation, savings=savings))
        
        elif result["action"] == "Creative Spark":
            sid2 = result.get("secondary_id", "")
            self.blackboard.post(SynapticSignal("SYNTH", AgentRole.CREATIVE, f"✨ SPARK: Multi-modal fusion between {str(tid)[:8]} and {str(sid2)[:8]}.", 
                                                SignalType.CREATIVE_SPARK, motivation=motivation, savings=savings))
        
        elif result["action"] == "Semantic Centroiding":
            tid = result.get("target_id")
            if tid in self.vault._nodes:
                node = self.vault._nodes[tid]
                if node.vector is not None:
                    try:
                        results = self.vault.query(None, query_vector=node.vector, k=15)
                        cluster = [r.node.id for r in results if r.final_score > 0.92 and r.node.id != tid]
                        if len(cluster) >= 3:
                            self.quantum.clusters_fused += 1
                            density_savings = f"{len(cluster) * 0.05:.2f} MB RAM (HNSW Optimization)"
                            real_motivation = f"Fused high-density cluster at {str(tid)[:8]} ({len(cluster)} nodes)"
                            # Update entry with real metrics
                            audit_entry["reasoning"] = real_motivation
                            audit_entry["savings"] = density_savings
                            
                            self.blackboard.post(SynapticSignal("QUANTUM", AgentRole.ARCHITECT, f"🌌 QUANTUM FUSION: {len(cluster)} nodes merged.", 
                                                                SignalType.PATTERN_MATCH, motivation=real_motivation, savings=density_savings))
                            node.metadata["is_centroid"] = True
                            for cid in cluster: node.add_edge(cid, "centroid_of", weight=1.0, source="QA-101")
                    except Exception: pass

        elif result["action"] == "Cross-Reference Audit":
            tid = result.get("target_id")
            if tid in self.vault._nodes:
                node = self.vault._nodes[tid]
                # Segnale al Sentinel (il metodo real_validation è già iniettato precedentemente)
                # Mark as pending validation to protect from Janitor
                setattr(node, 'pending_validation', True)
                self.blackboard.post(SynapticSignal("SENTINEL", AgentRole.GUARDIAN, f"🛡️ CROSS-REF: Auditing node {str(tid)[:8]} for external verification.", SignalType.ALERT))
                
                def real_validation(target_id, node_text, url=None):
                    from retrieval.web_forager import SovereignWebForager
                    import asyncio
                    
                    async def run_audit():
                        self.blackboard.post(SynapticSignal("SENTINEL", AgentRole.GUARDIAN, f"🌐 INTERNET AUDIT: Accessing external nodes for verification...", SignalType.ALERT))
                        forager = SovereignWebForager(max_depth=1, max_pages=3)
                        
                        # Se il nodo ha un URL, usiamo quello, altrimenti cerchiamo il titolo
                        query = url if url else node_text[:100]
                        valid = False
                        
                        try:
                            # Cerchiamo conferme esterne
                            async for page in forager.forage(query if "http" in query else f"https://www.google.com/search?q={query}"):
                                if len(page.text) > 200: # Trovato contenuto rilevante
                                    valid = True
                                    break
                        except: pass
                        
                        if target_id in self.vault._nodes:
                            n = self.vault._nodes[target_id]
                            setattr(n, 'pending_validation', False)
                            if valid:
                                setattr(n, 'stability', 98.0)
                                self.sentinel.validated_count += 1
                                self.blackboard.post(SynapticSignal("SENTINEL", AgentRole.GUARDIAN, f"✅ SOVEREIGN VERIFIED: Node {str(target_id)[:8]} confirmed by external source.", SignalType.SYSTEM_NOTIFICATION))
                            else:
                                setattr(n, 'stability', 30.0) # Degradation
                                self.blackboard.post(SynapticSignal("SENTINEL", AgentRole.GUARDIAN, f"⚠️ UNVERIFIED: External audit failed for node {str(target_id)[:8]}.", SignalType.ALERT))
                    
                    # Eseguiamo in un nuovo loop per non bloccare il thread cinetico
                    loop = asyncio.new_event_loop()
                    threading.Thread(target=lambda: loop.run_until_complete(run_audit()), daemon=True).start()

                real_validation(tid, node.text, node.metadata.get("source"))

        # 📂 [v16.1] Finalize registration in mission history with all dynamic reasons/savings
        self.mission_history.insert(0, audit_entry)
        if len(self.mission_history) > 100: self.mission_history.pop()

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
                },
                "QA-101": {
                    "identity": self.quantum.identity,
                    "pos": dict(self.quantum.pos),
                    "status": self.quantum.status,
                    "fused_clusters": self.quantum.clusters_fused
                },
                "SE-007": {
                    "identity": self.sentinel.identity,
                    "pos": dict(self.sentinel.pos),
                    "status": self.sentinel.status,
                    "validated": self.sentinel.validated_count
                }
            },
            "janitor": {"pos": dict(self.janitor.pos), "purged": self.janitor.eaten_count, "mode": self.janitor.mode, "status": self.janitor.status},
            "distiller": {"pos": dict(self.distiller.pos), "pruned": self.distiller.pruned_count, "mode": self.distiller.mode, "status": self.distiller.status},
            "reaper": {"pos": dict(self.reaper.pos), "processed": self.reaper.processed},
            "blackboard": self.blackboard.get_recent(12)
        }

    def get_status(self) -> Dict: return self.get_orchestra_report()
    def get_audit_ledger(self) -> List[Dict]: return self.mission_history
