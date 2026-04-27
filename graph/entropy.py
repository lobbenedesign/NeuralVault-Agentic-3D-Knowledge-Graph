"""
neuralvault.graph.entropy
──────────────────────────
Monitoraggio dell'Entropia del Grafo e Trigger per il Dreaming.
Fase 3: Cognitive Overdrive.
"""

import math
import time
from typing import Dict, List, Optional
import numpy as np

class EntropyMonitor:
    """
    Calcola l'Entropia Semantica del sistema.
    Se l'entropia supera una soglia, significa che il sistema è in uno stato
    di disordine/tensione e necessita di una fase di 'Sogno' (Dreaming) 
    per riorganizzare le sinapsi.
    """
    def __init__(self, engine, threshold: float = 0.65):
        self.engine = engine
        self.threshold = threshold
        self.last_entropy = 0.0
        self.is_dreaming = False

    def calculate_system_entropy(self) -> float:
        """
        Calcola l'entropia basata su:
        1. Tensioni semantiche (CONTRADICTS)
        2. Frammentazione dei cluster
        3. Volatilità dei feedback
        """
        nodes = self.engine._nodes
        if not nodes: return 0.0
        
        # 1. Tension Entropy
        total_tension = 0.0
        tension_count = 0
        for node in nodes.values():
            for edge in node.edges:
                if edge.relation.value == "contradicts":
                    total_tension += edge.weight
                    tension_count += 1
        
        tension_score = (total_tension / tension_count) if tension_count > 0 else 0.0
        
        # 2. Structural Disorder (Inverse of average degree)
        avg_degree = sum(len(n.edges) for n in nodes.values()) / len(nodes)
        structural_disorder = 1.0 / (1.0 + avg_degree)
        
        # 3. Cognitive Volatility (Basata sugli score degli agenti)
        scores = [n.agent_relevance_score for n in nodes.values()]
        volatility = float(np.std(scores)) if len(scores) > 1 else 0.0
        
        # Combinazione pesata: 40% Tensione, 40% Struttura, 20% Volatilità
        entropy = (tension_score * 0.4) + (structural_disorder * 0.4) + (volatility * 0.2)
        
        self.last_entropy = entropy
        return entropy

    def check_and_trigger(self):
        """Monitora e triggera il dreaming se necessario."""
        if self.is_dreaming: return
        
        entropy = self.calculate_system_entropy()
        if entropy > self.threshold:
            print(f"🌌 [Entropy] System Entropy Critical: {entropy:.2f} > {self.threshold}. Triggering DREAMING.")
            self._start_dreaming()

    def _start_dreaming(self):
        self.is_dreaming = True
        try:
            # Chiamata al processo di evoluzione del grafo (Dreaming)
            # Viene eseguito in un thread separato per non bloccare l'engine
            import threading
            thread = threading.Thread(target=self._dream_process)
            thread.daemon = True
            thread.start()
        except Exception as e:
            print(f"⚠️ [Dreaming] Failed to start dream process: {e}")
            self.is_dreaming = False

    def _dream_process(self):
        print("💤 [Dreaming] NeuralVault is dreaming... optimizing synapses.")
        start_ts = time.time()
        
        # Esegue l'evoluzione del grafo
        if hasattr(self.engine, 'evolve_graph'):
            self.engine.evolve_graph()
            
        # Discover new synapses
        if hasattr(self.engine, 'lab') and hasattr(self.engine.lab, 'discover_synapses'):
            # Campionamento casuale di nodi per discovery
            sample_ids = list(self.engine._nodes.keys())
            if len(sample_ids) > 10:
                import random
                sample_ids = random.sample(sample_ids, 10)
            
            for nid in sample_ids:
                node = self.engine._nodes.get(nid)
                if node: self.engine.lab.discover_synapses(nid, node.vector)
        
        duration = time.time() - start_ts
        print(f"✨ [Dreaming] Dream completed in {duration:.2f}s. Entropy stabilized.")
        self.is_dreaming = False
