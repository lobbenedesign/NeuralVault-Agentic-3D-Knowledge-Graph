import time
import uuid
import json
import numpy as np
import httpx
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from enum import Enum

@dataclass
class TensionNode:
    node_id: str
    tension: float        # 0.0 -> 1.0
    hop: int              # Distanza dalla sorgente
    relation: str         # "amplifies" | "contradicts" | "cites"

class DebateStance(Enum):
    PROSECUTOR = "prosecutor"   # Cerca debolezze e rischi
    DEFENDER = "defender"       # Cerca punti forti e precedenti
    ARBITRATOR = "arbitrator"   # Sintetizza la verità

@dataclass
class DebateMove:
    move_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    agent_id: str = ""
    stance: DebateStance = DebateStance.ARBITRATOR
    argument: str = ""
    evidence_nodes: List[str] = field(default_factory=list)
    tension_score: float = 0.5

class Agent007Lab:
    """
    IL LABORATORIO DI INTELLIGENZA ADVERSARIALE.
    Qui la memoria diventa dibattito e la verità viene estratta dal conflitto.
    """
    def __init__(self, engine):
        self.engine = engine
        # Usiamo la connessione DuckDB dell'engine
        self.con = engine.agent007.con if hasattr(engine, 'agent007') else engine._prefilter.con
        self._init_db()
        self.agents = ["Prosecutor", "Defender", "Arbitrator"] # Per analytics report

    def _init_db(self):
        """Prepara le tabelle per la tensione e i dibattiti."""
        self.con.execute("""
            CREATE TABLE IF NOT EXISTS semantic_tension (
                source_id VARCHAR,
                target_id VARCHAR,
                tension DOUBLE,
                relation VARCHAR,
                timestamp DOUBLE
            )
        """)
        self.con.execute("""
            CREATE TABLE IF NOT EXISTS debate_history (
                session_id VARCHAR,
                node_id VARCHAR,
                verdict JSON,
                timestamp DOUBLE
            )
        """)

    def propagate_tension(self, source_node_id: str, vector: np.ndarray) -> List[TensionNode]:
        """
        Analisi di propagazione reale: calcola la tensione semantica basata sulle distanze vettoriali effettive.
        """
        # Recupero i vicini tramite l'engine (distanza reale)
        results = self.engine.query("", query_vector=vector, k=10)
        tensions = []
        
        for res in results:
            if res.node.id == source_node_id: continue
            
            # La similarità è già calcolata nell'engine (cosino, o dot product normalizzato)
            # Supponiamo che res.final_score sia la similarità [0, 1]
            sim = res.final_score
            dist = 1.0 - sim
            
            # Classificazione reale della relazione
            if sim > 0.92: relation = "amplifies"
            elif sim > 0.75: relation = "cites"
            else: relation = "contradicts"
            
            # La tensione è alta se sono vicini ma "contradicts" (discrepanza semantica)
            tension = sim if relation != "contradicts" else dist
            
            t_node = TensionNode(node_id=res.node.id, tension=float(tension), hop=1, relation=relation)
            tensions.append(t_node)
            
            # Persistenza
            self.con.execute(
                "INSERT INTO semantic_tension VALUES (?, ?, ?, ?, ?)",
                (source_node_id, res.node.id, float(tension), relation, time.time())
            )
            
        return tensions

    async def run_adversarial_session(self, node_id: str, text: str) -> Dict:
        """
        LA CORTE DIGITALE (REAL).
        Avvia un dibattito tra Prosecutor e Defender su un nodo specifico usando Ollama.
        """
        session_id = str(uuid.uuid4())
        
        # 1. Recupero evidenze contrastanti reali
        contradictions = self.con.execute("""
            SELECT target_id, tension FROM semantic_tension 
            WHERE source_id = ? AND relation = 'contradicts' 
            ORDER BY tension DESC LIMIT 3
        """, (node_id,)).fetchall()
        
        # Recuperiamo il contenuto delle evidenze
        evidence_texts = []
        for cid in contradictions:
            node = self.engine._nodes.get(cid[0])
            if node: evidence_texts.append(node.text)

        # 2. Generazione Argomenti via SLM (Ollama)
        p_arg = await self._generate_agent_move("Prosecutor", text, evidence_texts)
        d_arg = await self._generate_agent_move("Defender", text, [])
        v_report = await self._generate_verdict(text, [p_arg, d_arg])

        verdict = {
            "vulnerability_score": v_report.get("score", 5),
            "top_risks": v_report.get("risks", ["Ambiguity"]),
            "recommendation": v_report.get("rec", "No recommendation."),
            "debate_log": [p_arg, d_arg]
        }
        
        self.con.execute(
            "INSERT INTO debate_history VALUES (?, ?, ?, ?)",
            (session_id, node_id, json.dumps(verdict), time.time())
        )
        
        return verdict

    async def _generate_agent_move(self, role: str, target_text: str, evidence: List[str]) -> str:
        prompt = f"Role: {role}. Analyze this text: '{target_text}'. "
        if evidence:
            prompt += f"Contradicting evidence: {' '.join(evidence)}. "
        prompt += "Provide a short, sharp professional analysis."
        
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post("http://localhost:11434/api/generate", json={
                    "model": "phi3", "prompt": prompt, "stream": False
                }, timeout=10.0)
                if resp.status_code == 200:
                    return resp.json().get("response", f"{role} analysis unavailable.")
        except:
            pass
        return f"[STATIC] {role} considers this node " + ("problematic" if role == "Prosecutor" else "stable")

    async def _generate_verdict(self, text: str, arguments: List[str]) -> Dict:
        prompt = f"Arbitrate this debate on the text: '{text}'. Arguments: {arguments}. Return JSON with 'score' (0-10), 'risks' (list), 'rec' (string)."
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post("http://localhost:11434/api/generate", json={
                    "model": "phi3", "prompt": prompt, "stream": False, "format": "json"
                }, timeout=10.0)
                if resp.status_code == 200:
                    return json.loads(resp.json().get("response", "{}"))
        except:
            pass
        return {"score": 5, "risks": ["Manual review needed"], "rec": "Ollama offline."}

    def get_weakness_report(self, node_id: str) -> Optional[Dict]:
        """Recupera l'ultimo report di vulnerabilità."""
        res = self.con.execute(
            "SELECT verdict FROM debate_history WHERE node_id = ? ORDER BY timestamp DESC LIMIT 1",
            (node_id,)
        ).fetchone()
        return json.loads(res[0]) if res else None
