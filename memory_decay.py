import math
import time
from dataclasses import dataclass
from typing import Dict, List, Optional
import threading

@dataclass
class DecayProfile:
    """Profilo di decadimento per un nodo neurale."""
    node_id: str
    last_accessed: float
    access_count: int
    stability: float       # 'S' nella curva di Ebbinghaus
    importance: float      # Peso semantico (DABA)
    
class EbbinghausDecay:
    """
    Motore di decadimento basato sulla curva di Ebbinghaus.
    R(t) = e^(-t / S)
    """
    REINFORCE_FACTOR = 1.8
    STABILITY_MAP = {
        "working": 1.0,    # 1 ora
        "episodic": 24.0,  # 24 ore
        "semantic": 720.0  # 30 giorni
    }

    def calculate_retention(self, profile: DecayProfile) -> float:
        """Calcola quanto un ricordo è 'vivo' (0.0 a 1.0)."""
        now = time.time()
        elapsed_hours = (now - profile.last_accessed) / 3600.0
        # Stabilità modulata dall'importanza
        effective_stability = profile.stability * (1.0 + profile.importance)
        return math.exp(-elapsed_hours / effective_stability)

    def reinforce(self, profile: DecayProfile) -> DecayProfile:
        """Rinforza il ricordo ad ogni accesso (Spaced Repetition)."""
        now = time.time()
        # La stabilità cresce con gli accessi, ma con rendimento decrescente
        boost = self.REINFORCE_FACTOR / (1.0 + math.log1p(profile.access_count))
        profile.stability *= boost
        profile.last_accessed = now
        profile.access_count += 1
        return profile

class DecayDaemon:
    """Demone di background per la gestione del decadimento e pulizia."""
    def __init__(self, engine, interval: float = 300.0):
        self.engine = engine
        self.interval = interval
        self.decay_engine = EbbinghausDecay()
        self.running = False
        self._thread = None

    def start(self):
        self.running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def _run_loop(self):
        while self.running:
            try:
                self._process_decay()
            except Exception as e:
                print(f"[DecayDaemon] Error: {e}")
            time.sleep(self.interval)

    def _process_decay(self):
        """Analizza i nodi e decide se consolidare o eliminare."""
        now = time.time()
        for node_id, node in list(self.engine.nodes.items()):
            # Se il nodo non ha un profilo, crealo (default episodic)
            if not hasattr(node, 'decay_profile'):
                node.decay_profile = DecayProfile(
                    node_id=node_id,
                    last_accessed=node.created_at,
                    access_count=1,
                    stability=24.0,
                    importance=0.5
                )
            
            retention = self.decay_engine.calculate_retention(node.decay_profile)
            
            # Soglie critiche
            if retention < 0.1: # 10% retention -> Consolidamento
                print(f"[DecayDaemon] Consolidating node {node_id} (retention: {retention:.2f})")
                # Qui chiameremmo il Consolidation Loop (Fase 22)
            elif retention < 0.01: # 1% retention -> Eutanasia Cognitiva
                print(f"[DecayDaemon] Deleting decayed node {node_id}")
                self.engine.remove_node(node_id)
