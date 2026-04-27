"""
neuralvault.storage.arrow_ipc
──────────────────────────────
Implementazione dello scambio dati via Apache Arrow (Zero-Copy).
Permette di convertire i batch di nodi in formati tabulari Arrow 
che possono essere letti direttamente da C++/Rust senza overhead di parsing.
"""

import pyarrow as pa
import numpy as np
from typing import List
from index.node import VaultNode

class SovereignArrowIPC:
    """
    Gestore per la serializzazione e condivisione di memoria via Arrow.
    Fornisce il protocollo 'Zero-Copy' per il kernel v1.0.
    """
    
    # Definizione dello schema Arrow per un VaultNode
    NODE_SCHEMA = pa.schema([
        pa.field("id",                    pa.string()),
        pa.field("text",                  pa.string()),
        pa.field("vector",                pa.list_(pa.float32())),
        pa.field("agent_relevance_score", pa.float32()),
        pa.field("created_at",            pa.float64()),
        pa.field("collection",            pa.string()),
    ])

    @staticmethod
    def serialize_batch(nodes: List[VaultNode]) -> pa.Buffer:
        """Serializza una lista di nodi in un buffer Arrow IPC."""
        data = {
            "id":                    [n.id for n in nodes],
            "text":                  [n.text for n in nodes],
            "vector":                [n.vector.tolist() if n.vector is not None else [] for n in nodes],
            "agent_relevance_score": [n.agent_relevance_score for n in nodes],
            "created_at":            [n.created_at for n in nodes],
            "collection":            [n.collection for n in nodes],
        }
        
        table = pa.table(data, schema=SovereignArrowIPC.NODE_SCHEMA)
        
        sink = pa.BufferOutputStream()
        with pa.ipc.new_file(sink, table.schema) as writer:
            writer.write_table(table)
            
        return sink.getvalue()

    @staticmethod
    def deserialize_batch(buffer: pa.Buffer) -> pa.Table:
        """Legge un buffer Arrow IPC in una tabella Arrow (Zero-Copy)."""
        reader = pa.ipc.open_file(buffer)
        return reader.read_all()

    @staticmethod
    def share_memory_with_rust(nodes: List[VaultNode]):
        """
        [PHASE 2] Esempio di integrazione Zero-Copy: 
        Ritorna il puntatore e la lunghezza del buffer Arrow per il backend Rust.
        """
        buf = SovereignArrowIPC.serialize_batch(nodes)
        return buf.address, buf.size
