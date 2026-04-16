"""
neuralvault.agent.session + feedback
──────────────────────────────────────
Gestione sessioni agente e feedback loop.

Una sessione è il contesto di una conversazione agente. Traccia:
- Quali nodi sono stati usati
- Quali query sono state fatte
- Co-occorrenze tra nodi (per inferire edges)
- Feedback esplicito e implicito

Il feedback loop aggiorna agent_relevance_score dei nodi e può triggerare
la creazione di nuovi semantic edges.
"""

from __future__ import annotations

import time
import uuid
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Any

from index.node import RelationType, VaultNode
import json


# ─────────────────────────────────────────────
# AgentSession
# ─────────────────────────────────────────────

@dataclass
class AgentSession:
    """
    Sessione di un agente. Aperta all'inizio di una conversazione,
    chiusa alla fine (o per TTL).

    Ogni query aggiorna lo stato della sessione. Alla chiusura,
    le co-occorrenze vengono usate per aggiornare il context graph.
    """
    session_id:    str   = field(default_factory=lambda: str(uuid.uuid4()))
    agent_id:      str   = "default"
    created_at:    float = field(default_factory=time.time)
    last_active:   float = field(default_factory=time.time)
    ttl_seconds:   float = 3600.0

    # Tracciamento query
    query_count:   int   = 0
    query_history: list[dict] = field(default_factory=list)

    # Tracciamento nodi usati
    used_node_ids:       set[str]              = field(default_factory=set)
    positive_node_ids:   set[str]              = field(default_factory=set)  # feedback +
    negative_node_ids:   set[str]              = field(default_factory=set)  # feedback -

    # Co-occorrenze: (node_id_a, node_id_b) → count
    cooccurrences: dict[tuple[str, str], int]  = field(default_factory=lambda: defaultdict(int))

    # Cluster di accesso: quali zone del feature space interroga questo agente
    # (per adaptive HNSW promotion)
    access_cluster: list[str] = field(default_factory=list)
    access_history: list[str] = field(default_factory=list) # Storico completo

    def is_expired(self) -> bool:
        return time.time() > self.last_active + self.ttl_seconds

    def record_query(self, query_text: str, result_ids: list[str]) -> None:
        """Registra una query e i suoi risultati."""
        self.query_count += 1
        self.last_active = time.time()

        # Registra co-occorrenze tra tutti i risultati di questa query
        for i, id_a in enumerate(result_ids):
            for id_b in result_ids[i + 1:]:
                # Ordina per avere sempre (min, max) come chiave
                key = (min(id_a, id_b), max(id_a, id_b))
                self.cooccurrences[key] += 1

        self.used_node_ids.update(result_ids)
        self.access_history.extend(result_ids) # Aggiorna storico completo
        self.query_history.append({
            "query":      query_text,
            "result_ids": result_ids,
            "timestamp":  time.time(),
        })

        # Aggiorna access cluster (ultimi 50 nodi usati)
        self.access_cluster.extend(result_ids)
        self.access_cluster = self.access_cluster[-50:]

    def record_feedback(self, node_id: str, positive: bool) -> None:
        """Registra feedback esplicito su un nodo."""
        if positive:
            self.positive_node_ids.add(node_id)
            self.negative_node_ids.discard(node_id)
        else:
            self.negative_node_ids.add(node_id)
            self.positive_node_ids.discard(node_id)
        self.last_active = time.time()

    def get_strong_cooccurrences(self, min_count: int = 3) -> list[tuple[str, str, int]]:
        """Restituisce coppie di nodi con co-occorrenze forti."""
        return [
            (a, b, count)
            for (a, b), count in self.cooccurrences.items()
            if count >= min_count
        ]

    def to_json(self) -> str:
        """Serializza la sessione in JSON per la persistenza."""
        data = {
            "session_id":        self.session_id,
            "agent_id":          self.agent_id,
            "created_at":        self.created_at,
            "last_active":       self.last_active,
            "ttl_seconds":       self.ttl_seconds,
            "query_count":       self.query_count,
            "query_history":     self.query_history,
            "used_node_ids":     list(self.used_node_ids),
            "positive_node_ids": list(self.positive_node_ids),
            "negative_node_ids": list(self.negative_node_ids),
            # Co-occorrenze serializzate come stringhe per JSON keys
            "cooccurrences":     {f"{k[0]}|{k[1]}": v for k, v in self.cooccurrences.items()},
            "access_cluster":    self.access_cluster,
            "access_history":    self.access_history,
        }
        return json.dumps(data)

    @staticmethod
    def from_json(json_str: str) -> AgentSession:
        """Ricostruisce la sessione da JSON."""
        d = json.loads(json_str)
        s = AgentSession(
            session_id=d["session_id"],
            agent_id=d["agent_id"],
            created_at=d["created_at"],
            last_active=d["last_active"],
            ttl_seconds=d["ttl_seconds"],
            query_count=d["query_count"],
            query_history=d["query_history"],
            used_node_ids=set(d["used_node_ids"]),
            positive_node_ids=set(d["positive_node_ids"]),
            negative_node_ids=set(d["negative_node_ids"]),
            access_cluster=d.get("access_cluster", []),
            access_history=d.get("access_history", []),
        )
        # Ripristina co-occorrenze (tuple keys)
        for k_str, count in d.get("cooccurrences", {}).items():
            a, b = k_str.split("|")
            s.cooccurrences[(a, b)] = count
        return s


# ─────────────────────────────────────────────
# AgentFeedbackProcessor
# ─────────────────────────────────────────────

class AgentFeedbackProcessor:
    """
    Processa il feedback della sessione e aggiorna:
    1. agent_relevance_score dei nodi
    2. Semantic edges nel context graph (da co-occorrenze)
    3. Statistiche per adaptive HNSW

    Viene chiamato:
    - Durante la sessione: per feedback espliciti real-time
    - Alla chiusura della sessione: per processare co-occorrenze
    """

    def __init__(
        self,
        positive_weight:     float = 0.15,   # quanto aumenta lo score per feedback +
        negative_weight:     float = 0.10,   # quanto diminuisce per feedback -
        decay_factor:        float = 0.95,   # decay dello score nel tempo
        cooccurrence_weight: float = 0.08,   # peso del bonus da co-occorrenza
        min_cooccurrences:   int   = 3,      # soglia per creare un edge
    ):
        self.positive_weight     = positive_weight
        self.negative_weight     = negative_weight
        self.decay_factor        = decay_factor
        self.cooccurrence_weight = cooccurrence_weight
        self.min_cooccurrences   = min_cooccurrences

    def apply_explicit_feedback(
        self,
        node:     VaultNode,
        positive: bool,
        strength: float = 1.0,  # 0.5 = feedback debole, 1.0 = forte
    ) -> None:
        """
        Aggiorna agent_relevance_score con feedback esplicito.

        Usa una media mobile esponenziale (EMA) per evitare che un singolo
        feedback positivo/negativo domini la storia del nodo.

        score_new = score_old + learning_rate * (target - score_old)
        dove target = +1 per positivo, -1 per negativo.
        """
        target        = 1.0 if positive else -1.0
        learning_rate = (self.positive_weight if positive else self.negative_weight) * strength
        node.agent_relevance_score = (
            node.agent_relevance_score + learning_rate * (target - node.agent_relevance_score)
        )
        # Clamp in [-1, 1]
        node.agent_relevance_score = max(-1.0, min(1.0, node.agent_relevance_score))

    def apply_implicit_feedback(
        self,
        retrieved_nodes: list[VaultNode],
        used_in_context: set[str],   # node_id che l'agente ha incluso nel prompt
        ignored:         set[str],   # node_id che l'agente ha scartato
    ) -> None:
        """
        Inferisce feedback implicito dall'uso dell'agente.

        - Nodi usati nel context → feedback positivo debole
        - Nodi ignorati dopo retrieval → feedback negativo molto debole
          (potrebbe essere stato ignorato per motivi di spazio, non di qualità)
        """
        for node in retrieved_nodes:
            if node.id in used_in_context:
                self.apply_explicit_feedback(node, positive=True, strength=0.5)
            elif node.id in ignored:
                self.apply_explicit_feedback(node, positive=False, strength=0.2)

    def apply_decay(self, nodes: list[VaultNode]) -> None:
        """
        Applica decay graduale agli score per far "invecchiare" il feedback.
        Senza decay, lo score converge a ±1 e smette di essere informativo.
        Chiamare periodicamente (es. ogni giorno).
        """
        for node in nodes:
            # Decay verso 0 (neutro)
            node.agent_relevance_score *= self.decay_factor

    def process_session_close(
        self,
        session:     AgentSession,
        nodes:       dict[str, VaultNode],
    ) -> list[tuple[str, str, RelationType, float]]:
        """
        Processa i dati di una sessione alla sua chiusura.

        1. Applica feedback esplicito ai nodi positivi/negativi
        2. Inferisce nuovi semantic edges dalle co-occorrenze
        3. Applica feedback implicito ai nodi usati/ignorati

        Returns:
            Lista di (source_id, target_id, relation, weight) — nuovi edges da aggiungere
        """
        new_edges = []

        # 1. Feedback esplicito
        for node_id in session.positive_node_ids:
            node = nodes.get(node_id)
            if node:
                self.apply_explicit_feedback(node, positive=True, strength=1.0)

        for node_id in session.negative_node_ids:
            node = nodes.get(node_id)
            if node:
                self.apply_explicit_feedback(node, positive=False, strength=1.0)

        # 2. Nuovi edges da co-occorrenze
        for a_id, b_id, count in session.get_strong_cooccurrences(self.min_cooccurrences):
            if a_id not in nodes or b_id not in nodes:
                continue
            # Il peso è proporzionale alle co-occorrenze, capped a 0.7
            weight = min(count * self.cooccurrence_weight, 0.7)
            new_edges.append((a_id, b_id, RelationType.SEQUENTIAL, weight))

            # Feedback positivo implicito per i nodi co-occorrenti
            for node_id in [a_id, b_id]:
                node = nodes.get(node_id)
                if node:
                    self.apply_explicit_feedback(node, positive=True, strength=0.3)

        return new_edges


# ─────────────────────────────────────────────
# SessionManager
# ─────────────────────────────────────────────

class SessionManager:
    """
    Gestisce il ciclo di vita delle sessioni agente con PERSISTENZA LMDB.
    """
    def __init__(self, data_dir: Optional[Path] = None, default_ttl: float = 3600.0):
        self.default_ttl = default_ttl
        self._sessions:  dict[str, AgentSession] = {}
        self._feedback   = AgentFeedbackProcessor()
        self._data_dir   = data_dir
        self._env        = None
        
        if self._data_dir:
            import lmdb
            session_path = self._data_dir / "sessions"
            session_path.mkdir(parents=True, exist_ok=True)
            self._env = lmdb.open(str(session_path), map_size=1 * 1024**3) # 1GB per sessioni

    def create_session(
        self,
        agent_id: str = "default",
        ttl:      float | None = None,
    ) -> AgentSession:
        """Crea, registra e persiste una nuova sessione."""
        session = AgentSession(
            agent_id=agent_id,
            ttl_seconds=ttl or self.default_ttl,
        )
        self._sessions[session.session_id] = session
        self._persist_session(session)
        return session

    def _persist_session(self, session: AgentSession):
        """Salva la sessione su LMDB."""
        if self._env:
            with self._env.begin(write=True) as txn:
                txn.put(session.session_id.encode(), session.to_json().encode())

    def get_session(self, session_id: str) -> AgentSession | None:
        """Ottieni una sessione. Carica da LMDB se non in memoria."""
        if session_id in self._sessions:
            s = self._sessions[session_id]
            if s.is_expired():
                self.close_session(session_id, {})
                return None
            return s
            
        # Tenta caricamento da disco
        if self._env:
            with self._env.begin(write=False) as txn:
                data = txn.get(session_id.encode())
                if data:
                    s = AgentSession.from_json(data.decode())
                    if not s.is_expired():
                        self._sessions[session_id] = s
                        return s
                    else:
                        # Scaduta su disco: rimuovi
                        self._delete_disk_session(session_id)
        return None

    def _delete_disk_session(self, session_id: str):
        if self._env:
            with self._env.begin(write=True) as txn:
                txn.delete(session_id.encode())

    def close_session(
        self,
        session_id: str,
        nodes:      dict[str, VaultNode],
    ) -> list[tuple[str, str, RelationType, float]]:
        """
        Chiude una sessione, processa il feedback e rimuove dal disco.
        """
        session = self.get_session(session_id)
        if session is None:
            return []
            
        self._sessions.pop(session_id, None)
        self._delete_disk_session(session_id)
        return self._feedback.process_session_close(session, nodes)

    def record_feedback(
        self,
        session_id: str,
        node_id:    str,
        positive:   bool,
    ) -> bool:
        """Registra feedback esplicito durante la sessione."""
        session = self.get_session(session_id)
        if session is None:
            return False
        session.record_feedback(node_id, positive)
        self._persist_session(session) # Aggiorna disco
        return True

    def gc(self) -> int:
        """Rimuove sessioni scadute."""
        expired_ids = [
            sid for sid, session in self._sessions.items()
            if session.is_expired()
        ]
        for sid in expired_ids:
            del self._sessions[sid]
        return len(expired_ids)

    def active_sessions(self) -> list[dict]:
        """Lista delle sessioni attive per monitoring."""
        return [
            {
                "session_id":  s.session_id,
                "agent_id":    s.agent_id,
                "query_count": s.query_count,
                "nodes_used":  len(s.used_node_ids),
                "age_seconds": time.time() - s.created_at,
            }
            for s in self._sessions.values()
            if not s.is_expired()
        ]

    def close(self):
        """Libera l'ambiente LMDB delle sessioni (Fase 16 Hardening)."""
        if self._env:
            self._env.close()
            self._env = None
