"""
neuralvault.core.innovations
────────────────────────────
Implementazione di Spectral Importance Tracking (SIT) per NeuralVault.
Parte delle innovazioni "Domain-Adaptive" (ICLR 2026).

Questa tecnica permette all'agente di identificare quali dimensioni dei vettori
sono le più discriminanti per il suo dominio specifico, migliorando la precisione
del rescoring TurboQuant senza re-quantizzare l'intero database.
"""

from __future__ import annotations
import numpy as np
from dataclasses import dataclass, field


@dataclass
class SpectralImportanceTracker:
    """
    Traccia l'importanza delle dimensioni dei vettori in un dominio specifico.
    Usa EMA (Exponential Moving Average) per aggiornare i pesi basandosi sulle
    query di successo dell'agente.
    """
    dim:            int
    learning_rate: float = 0.05
    # Pesi iniziali uniformi (tutte le dimensioni contano uguale)
    weights:       np.ndarray = field(init=False)
    # Media mobile delle query di successo per detecting dei centroidi
    centroid_ema:  np.ndarray = field(init=False)
    # Varianza mobile per rilevare dimensioni discriminanti
    variance_ema:  np.ndarray = field(init=False)

    def __post_init__(self):
        self.weights      = np.ones(self.dim, dtype=np.float32)
        self.centroid_ema = np.zeros(self.dim, dtype=np.float32)
        self.variance_ema = np.ones(self.dim, dtype=np.float32)

    def update(self, query_vector: np.ndarray, successful_nodes_vectors: list[np.ndarray]):
        """
        Aggiorna i pesi basandosi su una query e i risultati che l'agente ha gradito.
        Le dimensioni con alta coerenza tra query e risultati promossi ricevono più peso.
        """
        if not successful_nodes_vectors:
            return

        # Normalizza vettore query
        q = query_vector / (np.linalg.norm(query_vector) + 1e-8)
        
        # 1. Update centroide del dominio
        avg_res = np.mean(successful_nodes_vectors, axis=0)
        avg_res = avg_res / (np.linalg.norm(avg_res) + 1e-8)
        
        self.centroid_ema = (1 - self.learning_rate) * self.centroid_ema + self.learning_rate * avg_res
        
        # 2. Update varianza (Dimensioni "vivaci" nel dominio)
        # Una dimensione è importante se varia significativamente rispetto al centroide del dominio
        # o se è coerentemente presente nelle query di successo.
        diff = np.abs(q - self.centroid_ema)
        self.variance_ema = (1 - self.learning_rate) * self.variance_ema + self.learning_rate * diff
        
        # 3. Calcolo pesi di importanza (SIT)
        # Normalizziamo la varianza mobile per ottenere i pesi in [0.5, 1.5]
        # In questo modo non distorciamo troppo la distanza originale, ma la "orientiamo".
        raw_weights = self.variance_ema / (np.mean(self.variance_ema) + 1e-8)
        # Applichiamo un clamp per evitare esplosioni numeriche o eliminazione totale di dimensioni
        self.weights = np.clip(raw_weights, 0.5, 1.5).astype(np.float32)

    def get_weighted_query(self, query_vector: np.ndarray) -> np.ndarray:
        """Applica i pesi di dominio a una query in fase di proiezione."""
        return query_vector * self.weights

    def reset(self):
        """Reset dei pesi ai valori uniformi."""
        self.weights.fill(1.0)
        self.centroid_ema.fill(0.0)
        self.variance_ema.fill(1.0)
