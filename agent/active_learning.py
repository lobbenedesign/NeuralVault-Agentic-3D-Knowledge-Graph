"""
neuralvault.agent.active_learning
──────────────────────────────────
Implementazione del SelfTuningCircuitBreaker e logiche di Active Learning.
Apprende dai "Reject" dell'agente per regolare la sensibilità del sistema.
"""

import time
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional

@dataclass
class CircuitState:
    reject_rate: float = 0.0
    threshold: float = 0.7  # Soglia critica di reject per "aprire" il circuito
    sensitivity: float = 0.8 # Moltiplicatore per i filtri di ricerca
    is_open: bool = False
    last_tuned: float = field(default_factory=time.time)

class SelfTuningCircuitBreaker:
    """
    Monitora le performance del sistema e "stacca la spina" o regola i parametri
    se rileva troppi 'Reject' (nodi scartati dall'agente o dalla Supreme Court).
    """
    def __init__(self, window_size: int = 100, ema_alpha: float = 0.1):
        self.window_size = window_size
        self.ema_alpha = ema_alpha
        self.stats = CircuitState()
        self._history: List[bool] = [] # True = Success, False = Reject

    def record_event(self, success: bool):
        """Registra un evento di successo o fallimento (Reject)."""
        self._history.append(success)
        if len(self._history) > self.window_size:
            self._history.pop(0)

        # Calcola reject rate tramite EMA
        current_reject = 0.0 if success else 1.0
        self.stats.reject_rate = (1 - self.ema_alpha) * self.stats.reject_rate + self.ema_alpha * current_reject

        # Update Circuit State
        if self.stats.reject_rate > self.stats.threshold:
            if not self.stats.is_open:
                print(f"🚨 [CircuitBreaker] High Reject Rate ({self.stats.reject_rate:.2f}). Opening Circuit.")
            self.stats.is_open = True
        else:
            if self.stats.is_open and self.stats.reject_rate < (self.stats.threshold * 0.5):
                print(f"🟢 [CircuitBreaker] Stability restored ({self.stats.reject_rate:.2f}). Closing Circuit.")
                self.stats.is_open = False

        # Self-Tuning logic: ogni 10 eventi, regola la sensibilità
        if len(self._history) % 10 == 0:
            self._tune_sensitivity()

    def _tune_sensitivity(self):
        """
        Regola la sensibilità del sistema basandosi sul reject rate.
        Se ci sono troppi reject, aumentiamo la sensibilità (filtri più stretti).
        Se tutto va bene, allentiamo i filtri (più creatività/discovery).
        """
        # Se siamo sopra lo 0.3 di reject, iniziamo a stringere
        if self.stats.reject_rate > 0.3:
            # Aumenta sensibilità (max 1.0)
            self.stats.sensitivity = min(1.0, self.stats.sensitivity + 0.02)
        elif self.stats.reject_rate < 0.1:
            # Allenta sensibilità (min 0.5)
            self.stats.sensitivity = max(0.5, self.stats.sensitivity - 0.01)
        
        self.stats.last_tuned = time.time()

    def get_query_multiplier(self) -> float:
        """
        Restituisce un moltiplicatore per la soglia di similarità.
        Se il circuito è aperto, restituiamo un valore molto alto per filtrare tutto tranne l'eccellenza.
        """
        if self.stats.is_open:
            return 1.5 # Filtra il 50% in più
        return self.stats.sensitivity

@dataclass
class ActiveLearningModule:
    """
    Modulo di Active Learning che integra il Circuit Breaker
    con l'apprendimento dai campioni negativi.
    """
    def __init__(self, engine):
        self.engine = engine
        self.cb = SelfTuningCircuitBreaker()
        
    def process_rejection(self, node_id: str, reason: str = "agent_reject"):
        """Gestisce un nodo rifiutato dall'utente o dall'agente."""
        self.cb.record_event(success=False)
        
        # Penalizza il nodo nell'engine
        node = self.engine._nodes.get(node_id)
        if node:
            # Penalità pesante (-0.2)
            node.agent_relevance_score = max(-1.0, node.agent_relevance_score - 0.2)
            node.metadata["reject_reason"] = reason
            node.metadata["last_reject_ts"] = time.time()
            
            # Se è nel tier Working, forziamo il flush per persistere la penalità
            self.engine.storage_put(node)

            # 🧠 [v1.1.0] Persistenza Episodica: Protezione nel DB DuckDB
            try:
                self.engine.protect_node_persistent(node_id, reason=reason, rejected_by="user")
                # v1.1.0: Trust Update
                proposer = node.metadata.get("agent_proposer") or node.metadata.get("created_by")
                if proposer and hasattr(self.engine, 'lab') and self.engine.lab.trust_network:
                    self.engine.lab.trust_network.update_trust(proposer, success=False)
            except: pass

    def process_success(self, node_id: str):
        """Gestisce un nodo confermato come utile."""
        self.cb.record_event(success=True)
        node = self.engine._nodes.get(node_id)
        if node:
            # Rinforzo positivo
            node.agent_relevance_score = min(1.0, node.agent_relevance_score + 0.05)
            self.engine.storage_put(node)
            
            # v1.1.0: Reward the agent
            proposer = node.metadata.get("agent_proposer") or node.metadata.get("created_by")
            if proposer and hasattr(self.engine, 'lab') and self.engine.lab.trust_network:
                self.engine.lab.trust_network.update_trust(proposer, success=True)
