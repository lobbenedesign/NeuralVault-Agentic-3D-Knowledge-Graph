import os
import time
from typing import Any, Optional
from pathlib import Path

import numpy as np
from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from __init__ import NeuralVaultEngine
from index.node import RelationType, VaultNode
from utils.embedder import EmbedderFactory

# ─────────────────────────────────────────────
# Config & State
# ─────────────────────────────────────────────

DATA_ROOT = Path(os.getenv("NEURALVAULT_DATA_DIR", "./data"))
DATA_ROOT.mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title="NeuralVault",
    description="Agent-native vector database with context graph and memory tiers",
    version="0.1.1",
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Registry dei vault caricati
_vaults: dict[str, NeuralVaultEngine] = {}

def get_vault(name: str) -> NeuralVaultEngine:
    if name not in _vaults:
        raise HTTPException(status_code=404, detail=f"Collection '{name}' not found")
    return _vaults[name]

# ─────────────────────────────────────────────
# Pydantic schemas
# ─────────────────────────────────────────────

class CreateCollectionRequest(BaseModel):
    name:             str
    dim:              int   = 1024
    hnsw_M:           int   = 16
    use_quantization: bool  = True
    use_rust:         bool  = True
    embedder_type:    str   = "none" # "none", "bge-m3", "openai"
    openai_key:       Optional[str] = None

class UpsertNodeRequest(BaseModel):
    id:         str | None = None
    text:       str
    vector:     list[float] | None = None
    metadata:   dict[str, Any]    = Field(default_factory=dict)
    namespace:  str               = "default"

class UpsertBatchRequest(BaseModel):
    nodes: list[UpsertNodeRequest]

class QueryRequest(BaseModel):
    query_text:             str
    query_vector:           list[float] | None = None
    k:                      int   = 10
    ef:                     int   = 50
    graph_hops:             int   = 1
    relations:              list[str] | None   = None
    metadata_filter:        dict  | None       = None
    alpha:                  float = 0.7
    session_id:             str   | None       = None
    include_contradictions: bool               = False

class AddEdgeRequest(BaseModel):
    source_id: str
    target_id: str
    relation:  str
    weight:    float = 1.0

# ─────────────────────────────────────────────
# Bootstrapping
# ─────────────────────────────────────────────

@app.on_event("startup")
def bootstrap_server():
    """Carica tutte le collection esistenti sul disco all'avvio."""
    print(f"NeuralVault: Bootstrapping from {DATA_ROOT}...")
    for coll_dir in DATA_ROOT.iterdir():
        if coll_dir.is_dir() and (coll_dir / "semantic").exists():
            name = coll_dir.name
            print(f"Found collection: {name}")
            _vaults[name] = NeuralVaultEngine(
                data_dir=coll_dir,
                collection=name
            )
    print("NeuralVault: Bootstrap complete.")

@app.on_event("shutdown")
def shutdown_server():
    """Flush di tutte le collection prima di chiudere."""
    for name, vault in _vaults.items():
        print(f"Flushing {name}...")
        vault.flush()

# ─────────────────────────────────────────────
# Routes: Collections
# ─────────────────────────────────────────────

@app.post("/collections", status_code=201)
def create_collection(req: CreateCollectionRequest):
    if req.name in _vaults:
        raise HTTPException(status_code=409, detail=f"Collection '{req.name}' already exists")
    
    col_dir = DATA_ROOT / req.name
    
    # Configure embedder
    embedder = None
    if req.embedder_type == "bge-m3":
        embedder = EmbedderFactory.sentence_transformers()
    elif req.embedder_type == "openai":
        embedder = EmbedderFactory.openai(api_key=req.openai_key)

    _vaults[req.name] = NeuralVaultEngine(
        dim=req.dim,
        hnsw_M=req.hnsw_M,
        data_dir=col_dir,
        use_quantization=req.use_quantization,
        use_rust=req.use_rust,
        embedder_fn=embedder,
        collection=req.name
    )
    return {"name": req.name, "dim": req.dim, "persistent": True}

@app.get("/collections")
def list_collections():
    return {
        "collections": [
            {"name": name, "stats": vault.stats(), "persistent": vault.data_dir is not None}
            for name, vault in _vaults.items()
        ]
    }

# ─────────────────────────────────────────────
# Routes: Core Ops (Upsert & Search)
# ─────────────────────────────────────────────

@app.post("/collections/{name}/upsert")
def upsert_node(name: str, req: UpsertNodeRequest, background_tasks: BackgroundTasks):
    vault = get_vault(name)
    vector = np.array(req.vector, dtype=np.float32) if req.vector else None
    
    if vector is None and hasattr(vault, '_embedder_fn') and vault._embedder_fn is not None:
        node = vault.upsert_text(
            text=req.text, 
            metadata=req.metadata, 
            node_id=req.id, 
            namespace=req.namespace
        )
    else:
        node = VaultNode(
            id=req.id or VaultNode.generate_id(),
            text=req.text,
            vector=vector,
            metadata=req.metadata,
            collection=name,
            namespace=req.namespace,
        )
        vault.upsert(node)
    
    background_tasks.add_task(vault.flush)
    
    return {"id": node.id, "upserted": True}

@app.post("/collections/{name}/query")
def query_vault(name: str, req: QueryRequest):
    vault = get_vault(name)
    
    query_vector = None
    if req.query_vector:
        query_vector = np.array(req.query_vector, dtype=np.float32)

    t0 = time.perf_counter()
    results = vault.query(
        query_text=req.query_text,
        query_vector=query_vector,
        k=req.k,
        ef=req.ef,
        graph_hops=req.graph_hops,
        relations=req.relations,
        metadata_filter=req.metadata_filter,
        alpha=req.alpha,
        session_id=req.session_id,
        include_contradictions=req.include_contradictions,
    )
    elapsed_ms = (time.perf_counter() - t0) * 1000

    return {
        "results": [
            {
                "id":           r.node.id,
                "text":         r.node.text,
                "metadata":     r.node.metadata,
                "scores":       {"final": round(r.final_score, 4)},
                "tier":         r.node.tier.value,
            }
            for r in results
        ],
        "meta": {
            "elapsed_ms": round(elapsed_ms, 2),
            "count":      len(results),
        }
    }

# ─────────────────────────────────────────────
# Routes: Sessions
# ─────────────────────────────────────────────

class FeedbackRequest(BaseModel):
    node_id:    str
    positive:   bool

@app.post("/sessions")
def create_session(agent_id: str = "default"):
    """Apre una nuova sessione agente."""
    if not _vaults:
        raise HTTPException(status_code=400, detail="No collections exist")
    vault = next(iter(_vaults.values()))
    session_id = vault.create_session(agent_id=agent_id)
    return {"session_id": session_id}

@app.post("/sessions/{session_id}/feedback")
def session_feedback(session_id: str, req: FeedbackRequest):
    """Registra feedback su un nodo."""
    for vault in _vaults.values():
        if vault.feedback(session_id, req.node_id, req.positive):
            return {"recorded": True}
    raise HTTPException(status_code=404, detail="Session not found")

@app.delete("/sessions/{session_id}")
def close_session(session_id: str):
    """Chiude una sessione e processa il feedback."""
    edges_created = 0
    for vault in _vaults.items():
        edges_created += vault[1].close_session(session_id)
    return {"closed": True, "edges_created": edges_created}


# ─────────────────────────────────────────────
# Health & info
# ─────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "collections": list(_vaults.keys()), "data_dir": str(DATA_ROOT)}

@app.get("/")
def root():
    return {
        "name":    "NeuralVault",
        "version": "0.1.1",
        "docs":    "/docs",
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
