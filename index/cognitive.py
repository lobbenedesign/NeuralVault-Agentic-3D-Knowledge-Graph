"""
index/cognitive.py — [v0.5.0 Synaptic Cognitive Layer]
────────────────────────────────────────────────────
Implementa la "Memoria Viva" di NeuralVault:
1. Ebbinghaus Decay: Calcolo runtime della forza del ricordo.
2. Summarized Wisdom: Consolidamento asincrono di cluster sbiaditi.
3. Decay Daemon: Monitoraggio e potatura/distillazione asincrona.
"""

import math
import time
import threading
import numpy as np
from typing import List, Dict, Optional
from index.node import VaultNode

class CognitiveDecayEngine:
    """Implementa la curva dell'oblio biologica (Ebbinghaus) con rinforzo (v1.1.0)."""
    
    OPACITY_CEILING = 1.0        # 100% opacity (recent)
    OPACITY_FLOOR = 0.15         # 15% opacity (minimum visible)
    OPACITY_HIDE_THRESHOLD = 0.1 # < 10% -> stop rendering

    def __init__(self, half_life_hours: float = 168): # Default: 1 settimana
        self.half_life_sec = half_life_hours * 3600
        self.reinforce_factor = 1.8

    def calculate_strength(self, last_access: float, importance: float, access_count: int, emotional_weight: float = 0.5) -> float:
        """
        [v1.1.0 Sovereign Ebbinghaus]
        R(t) = e^(-t/S)
        t = ore dall'ultimo accesso
        S = stabilità (influenzata da importanza e ripetizione)
        """
        elapsed_hours = (time.time() - last_access) / 3600.0
        
        # Stabilità: Cresce con ogni accesso (Spaced Repetition)
        # S base = 168h (1 settimana) per default
        stability = (self.half_life_sec / 3600.0) * (self.reinforce_factor ** (access_count - 1))
        
        # Modulazione emotiva/importanza
        stability *= (0.5 + emotional_weight + importance)
        
        # Calcolo Ritenzione (R)
        retention = math.exp(-elapsed_hours / max(stability, 0.1))
        
        # Mappa R [0,1] -> [OPACITY_FLOOR, OPACITY_CEILING]
        strength = self.OPACITY_FLOOR + retention * (self.OPACITY_CEILING - self.OPACITY_FLOOR)
        
        return min(strength, 1.0)

class WisdomSummarizer:
    """Trasforma cluster di dati in principi universali (Saggezza)."""
    
    def __init__(self, engine):
        self.engine = engine

    def summarize_cluster(self, node_ids: List[str]) -> Optional[VaultNode]:
        """
        [v0.6.0 Ghost Memory] 
        Trasforma un cluster di nodi 'sbiaditi' in una 'Saggezza Sintetica' ricca.
        Mantiene l'impronta semantica, entità chiave e statistiche di vita.
        """
        if not node_ids: return None
        
        active_nodes = []
        for nid in node_ids:
            if nid in self.engine._nodes:
                active_nodes.append(self.engine._nodes[nid])
        
        if not active_nodes: return None
        
        # 1. Sintesi Vettoriale (Centroide Semantico)
        vectors = [n.vector for n in active_nodes if n.vector is not None]
        if not vectors: return None
        wisdom_vector = np.mean(vectors, axis=0)
        
        # 2. Estrazione dati strutturati (Impronta Tecnica)
        total_hits = sum(n.metadata.get("access_count", 0) for n in active_nodes)
        sources = list(set(n.metadata.get("source", "unknown") for n in active_nodes))
        timestamps = [n.created_at for n in active_nodes]
        t_start = time.strftime('%Y-%m-%d', time.localtime(min(timestamps)))
        t_end = time.strftime('%Y-%m-%d', time.localtime(max(timestamps)))
        
        # 3. Recupero Entità dalla Hard Memory (Agent007)
        ghost_entities = []
        try:
            placeholders = ', '.join(['?'] * len(node_ids))
            query = f"SELECT DISTINCT name FROM agent007_entities WHERE source_node_id IN ({placeholders}) LIMIT 10"
            res = self.engine.agent007.con.execute(query, node_ids).fetchall()
            ghost_entities = [r[0] for r in res]
        except: pass
        
        # 4. Generazione Mosaic Summary
        wisdom_id = f"wisdom_ghost_{int(time.time())}"
        summary = f"🏺 [GHOST MEMORY] Archetipo consolidato il {time.strftime('%Y-%m-%d %H:%M')}\n"
        summary += f"📅 Periodo: {t_start} -> {t_end} | 📈 Vitalità originale: {total_hits} hits\n"
        summary += f"📂 Sorgenti: {', '.join(sources[:3])}\n"
        if ghost_entities:
            summary += f"🧬 Entità Emergenti: {', '.join(ghost_entities)}\n"
        
        summary += "\n--- MOSAICO CONTENUTI ---\n"
        for n in active_nodes[:5]: # Prendi un pezzetto da più nodi
            snippet = n.text[:80].replace("\n", " ").strip()
            summary += f"• [...] {snippet} [...]\n"
        
        wisdom_node = VaultNode(
            id=wisdom_id,
            text=summary,
            vector=wisdom_vector,
            metadata={
                "type": "wisdom_ghost", 
                "source_count": len(active_nodes),
                "total_legacy_hits": total_hits,
                "entities": ghost_entities,
                "temporal_span": [min(timestamps), max(timestamps)]
            }
        )
        return wisdom_node

class CognitiveDecayDaemon:
    """Monitora asincronamente lo sbiadimento dei ricordi."""
    
    def __init__(self, engine, check_interval: float = 300.0): # Ogni 5 minuti
        self.engine = engine
        self.interval = check_interval
        self.running = False
        self._thread = None

    def start(self):
        self.running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        while self.running:
            try:
                self._analyze_metabolism()
            except Exception as e:
                print(f"⚠️ [Metabolism] Daemon Error: {e}")
            time.sleep(self.interval)

    def _analyze_metabolism(self):
        """Scansiona i nodi e decide chi deve essere distillato o eliminato."""
        if not self.engine._nodes: return
        
        now = time.time()
        to_consolidate = []
        
        # Analisi campionata (per non bloccare il sistema se ci sono milioni di nodi)
        nodes = list(self.engine._nodes.values())
        for node in nodes:
            # Usiamo i metadati salvati per calcolare la forza
            # In NeuralVault v1.4.0, questi dati sono gestiti dal prefilter DuckDB
            l_acc = node.metadata.get("last_access", node.created_at)
            impact = node.metadata.get("importance", 0.5)
            count = node.metadata.get("access_count", 1)
            
            strength = self.engine.cognitive.calculate_strength(l_acc, impact, count)
            
            # 💡 [Idea #3] Ebbinghaus Visual Decay: Imposta la trasparenza basata sulla forza
            node.metadata["opacity"] = max(0.1, float(strength))
            
            if strength < 0.15: # Sotto il 15% di forza -> Candidato al consolidamento
                to_consolidate.append(node.id)
                
        if len(to_consolidate) >= 5: # Soglia minima per un cluster di saggezza
            print(f"😴 [REM Sleep] Consolidating {len(to_consolidate)} weak nodes into Synthetic Wisdom...")
            wisdom_node = self.engine.wisdom.summarize_cluster(to_consolidate)
            if wisdom_node:
                self.engine.upsert(wisdom_node)
                # La rimozione dei nodi originali è gestita dall'upsert o esplicitamente
                for nid in to_consolidate:
                    if nid != wisdom_node.id:
                        self.engine.remove_node(nid)
    def stop(self):
        """Ferma il daemon in modo sicuro (v13.1)."""
        self.running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
