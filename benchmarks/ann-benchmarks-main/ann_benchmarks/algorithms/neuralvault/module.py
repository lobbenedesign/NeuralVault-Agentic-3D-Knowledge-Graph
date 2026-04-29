import sys
import os
import numpy as np
from ann_benchmarks.algorithms.base.module import BaseANN

# Rilevamento dinamico della root del progetto NeuralVault
# Si assume che ann-benchmarks-main sia dentro la cartella benchmarks/ di NeuralVault
try:
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../"))
    if project_root not in sys.path:
        sys.path.append(project_root)
    
    from __init__ import NeuralVaultEngine, VaultNode
except ImportError:
    print("⚠️ NeuralVault Engine non trovato nel path!")
    raise

class NeuralVault(BaseANN):
    def __init__(self, metric, method_param):
        self.name = "NeuralVault v0.3.0"
        self._metric = metric
        self._method_param = method_param
        self._engine = None

    def fit(self, X):
        """Carica il dataset del benchmark in NeuralVault."""
        dim = X.shape[1]
        print(f"🏺 [NeuralVault] Fitting dataset: {X.shape[0]} vettori, dim={dim}")
        
        # Inizializziamo l'engine con Rust nativo e TurboQuant attivo
        self._engine = NeuralVaultEngine(dim=dim, use_rust=True, use_quantization=True)
        
        # Inserimento ottimizzato in batch (Fase 16)
        nodes = [
            VaultNode(id=str(i), vector=X[i].astype(np.float32), text="")
            for i in range(len(X))
        ]
        self._engine.upsert_batch(nodes)

    def query(self, q, n):
        """Esegue la ricerca ANN standard richiamata da ann-benchmarks."""
        # Restituiamo solo gli ID interi (richiesto da ann-benchmarks)
        res = self._engine.query("", query_vector=q.astype(np.float32), k=n)
        return [int(r.node.id) for r in res]

    def __str__(self):
        return self.name
