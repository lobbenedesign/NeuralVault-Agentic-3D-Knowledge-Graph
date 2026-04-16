"""
neuralvault.graph.ingester
──────────────────────────
AutoKnowledgeLinker: popola automaticamente il Context Graph durante l'ingestion.
Analizza i chunk in fase di upload per rilevare relazioni semantiche esplicite
e strutturali (sequential, cites, prerequisite).
"""

from __future__ import annotations
import re
from typing import List, Optional, Any, Callable
from index.node import VaultNode, RelationType, SemanticEdge


class AutoKnowledgeLinker:
    """
    Motore di analisi automatica dei documenti per la creazione del grafo.
    """
    def __init__(self, llm_fn: Optional[Callable[[str, str], str]] = None):
        """
        Args:
            llm_fn: Funzione opzionale che accetta (chunk_a, chunk_b) e restituisce
                    il tipo di relazione rilevata o "none".
        """
        self.llm_fn = llm_fn
        # Pattern comuni per citazioni e prerequisiti
        self._cites_patterns = [
            re.compile(r"come (descritto|visto|menzionato) nel? (capitolo|sezione|paragrafo) [\d\w]+", re.I),
            re.compile(r"\(cfr\.? [^\)]+\)", re.I),
            re.compile(r"vedi anche [^\.]+", re.I),
        ]
        self._prereq_patterns = [
            re.compile(r"prima di procedere (bisogna|è necessario) (aver letto|conoscere)", re.I),
            re.compile(r"presuppone la conoscenza di", re.I),
            re.compile(r"basato s(u|ull[oa]) [^\.]+", re.I),
        ]

    def link_batch(self, nodes: List[VaultNode], use_llm: bool = False) -> int:
        """
        Analizza un batch di nodi e crea edges tra loro.
        Ritorna il numero di archi creati.
        """
        if len(nodes) < 2:
            return 0

        edges_created = 0
        
        # 1. Relazioni STRUTTURALI (Sequential)
        # Se i nodi appartengono alla stessa collection e sono in sequenza nel batch,
        # probabilmente sono sequenza logica (stesso documento).
        for i in range(len(nodes) - 1):
            curr, nxt = nodes[i], nodes[i+1]
            if curr.collection == nxt.collection:
                curr.add_edge(nxt.id, RelationType.SEQUENTIAL, weight=1.0, source="auto_ingest")
                edges_created += 1

        # 2. Relazioni SEMANTICHE (Pattern matching & Euristiche)
        for i, source in enumerate(nodes):
            for target in nodes:
                if source.id == target.id: continue
                
                # Check Citazioni
                if any(p.search(source.text) for p in self._cites_patterns) and \
                   self._are_semantically_close(source, target):
                    source.add_edge(target.id, RelationType.CITES, weight=0.85, source="auto_ingest")
                    edges_created += 1
                
                # Check Prerequisiti
                if any(p.search(source.text) for p in self._prereq_patterns) and \
                   self._are_semantically_close(source, target):
                    # Se Source dice "richiede conoscenza di..." e Target è vicino semanticamente,
                    # allora Target è prerequisito di Source.
                    source.add_edge(target.id, RelationType.PREREQUISITE, weight=0.9, source="auto_ingest")
                    edges_created += 1

        # 3. Analisi LLM (Opzionale: molto accurata ma costosa)
        if use_llm and self.llm_fn:
            # In produzione: limitiamo l'analisi LLM solo ai top-N candidati (N-squared è troppo caro)
            for i in range(min(10, len(nodes))):
                for j in range(i + 1, min(10, len(nodes))):
                    res = self.llm_fn(nodes[i].text, nodes[j].text)
                    if res != "none":
                        try:
                            rel = RelationType(res.lower())
                            nodes[i].add_edge(nodes[j].id, rel, weight=0.95, source="llm_ingest")
                            edges_created += 1
                        except ValueError: pass

        return edges_created

    def _are_semantically_close(self, a: VaultNode, b: VaultNode, threshold: float = 0.65) -> bool:
        """Helper per evitare link casuali basati solo su regex."""
        if a.vector is None or b.vector is None:
            return False
        # Dot product (assunti normalizzati)
        similarity = float(np.dot(a.vector, b.vector))
        return similarity > threshold


# Import numpy lazily to avoid startup overhead
import numpy as np
