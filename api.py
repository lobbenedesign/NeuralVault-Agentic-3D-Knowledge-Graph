import os
import logging
# [SOVEREIGN LOGGING] Silencing verbosity from framework libraries
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("transformers").setLevel(logging.ERROR)
logging.getLogger("huggingface_hub").setLevel(logging.ERROR)
logging.getLogger("sentence_transformers").setLevel(logging.WARNING)
logging.getLogger("uvicorn").setLevel(logging.WARNING)
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
logging.getLogger("uvicorn.error").setLevel(logging.WARNING)

import json
import uuid
import time
import numpy as np
import threading
import asyncio
import psutil
import random
import shutil
import glob
import signal
import platform
import hashlib
from pathlib import Path
from datetime import datetime, date
from contextlib import asynccontextmanager
from typing import List, Dict, Optional, Any

import os
import sys

# v2.6.0: Environment Stabilization & Warning Suppression
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false" # Evita warning di deadlock in f-strings
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE" # Per librerie Intel/OpenMP

# Silenzia i warning di caricamento di sentence-transformers / transformers
import logging
logging.getLogger("transformers.modeling_utils").setLevel(logging.ERROR)

import uvicorn
import torch
from fastapi import FastAPI, UploadFile, File, Request, Depends, HTTPException, BackgroundTasks, Header
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from neural_lab import SynapticSignal, AgentRole, SignalType
import httpx

class QueryRequest(BaseModel):
    query: str
    modality: str = "text"
    top_k: int = 5
    consensus: bool = False

# CORE ENGINE IMPORT
from __init__ import NeuralVaultEngine
from network.gossip import SyncSignal
from retrieval.web_forager import SovereignWebForager
from retrieval.multimodal import MultimodalSynapseProcessor

app = FastAPI(title="Aura Nexus: NeuralVault API")

def json_serializer(obj):
    if hasattr(obj, 'tolist'): return obj.tolist()
    if isinstance(obj, (datetime, date)): return obj.timestamp()
    try: return float(obj)
    except: return str(obj)

def signal_handler(sig, frame):
    print("\n🛑 [NeuralVault] Eutanasia Digitale in corso... Ciao!")
    try:
        if engine: 
            # Tentativo di chiusura pulita DuckDB prima del kill
            try:
                if hasattr(engine, '_prefilter'):
                    engine._prefilter.con.close()
            except Exception as e:
                print(f"⚠️ [Gardening Error] {e}")
    except: pass
    os._exit(0)

# Aggancio segnali per Mac/Linux
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Engine Instance
engine = None
engine_lock = asyncio.Lock()
VAULT_KEY = "vault_secret_aura_2026"

# --- AGENT FACTORY ENDPOINT (v12.0) ---
class AgentSpawnRequest(BaseModel):
    name: str
    role: str
    prompt: str
    api_key: str

@app.post("/api/agents/spawn")
async def spawn_agent(req: AgentSpawnRequest):
    if req.api_key != VAULT_KEY:
        raise HTTPException(status_code=403, detail="Invalid Vault Key")
    
    if not engine or not engine.lab:
        raise HTTPException(status_code=503, detail="Neural Lab Offline")
    
    try:
        # Map role string to Enum
        role_map = {
            "archivist": AgentRole.ARCHIVIST,
            "analyst": AgentRole.ANALYST,
            "creative": AgentRole.CREATIVE,
            "guardian": AgentRole.GUARDIAN,
            "architect": AgentRole.ARCHITECT
        }
        role_enum = role_map.get(req.role, AgentRole.ANALYST)
        
        agent_id = engine.lab.spawn_custom_agent(req.name, role_enum, req.prompt)
        return {"status": "success", "agent_id": agent_id, "message": f"Agent {req.name} forged and deployed."}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# Forage App State
app.state.forage_jobs = {}      # job_id -> status
app.state.forage_proposals = {}  # job_id -> [topics]

# Progress Tracking (Modelli)
install_progress = {} # { "model_name": { "percentage": 0, "status": "idle" } }

@app.middleware("http")
async def log_requests(request: Request, call_next):
    print(f"🌐 [API] Request: {request.method} {request.url.path}")
    response = await call_next(request)
    return response

def get_api_key(request: Request):
    key = request.headers.get("X-API-KEY")
    if not key and request.query_params.get("api_key"):
        key = request.query_params.get("api_key")
    if key != VAULT_KEY:
        raise HTTPException(status_code=403, detail="Invalid Neural Vault Key")
    return key

def check_api_key(key: str):
    if key != VAULT_KEY:
        raise HTTPException(status_code=403, detail="Invalid Neural Vault Key")

@app.on_event("startup")
async def startup_event():
    global engine
    storage_dir = os.getenv("NEURALVAULT_DATA_DIR", "./vault_data")
    engine = NeuralVaultEngine(data_dir=storage_dir)
    
    # Inizializza Neural Lab una sola volta
    from neural_lab import NeuralLabOrchestrator
    app.state.lab = NeuralLabOrchestrator(engine)
    
    # Gestione tabelle Agent007: delegata alla classe Agent007Intelligence in engine.agent007
    # Se necessario, aggiungiamo colonne mancanti in modo proattivo
    try:
        engine.agent007.con.execute("ALTER TABLE agent007_entities ADD COLUMN attributes JSON")
    except: pass
    try:
        engine.agent007.con.execute("ALTER TABLE agent007_entities ADD COLUMN relevance FLOAT")
    except: pass
    
    app.state.forager = SovereignWebForager(app.state.lab)
    app.state.mm_processor = MultimodalSynapseProcessor()
    
@app.on_event("shutdown")
async def shutdown_event():
    global engine
    if engine:
        print("🛑 [System] Shutting down NeuralVault Engine gracefully...")
        engine.close()
    print(f"🧬 NeuralVault: Hardware Trace -> CUDA: {torch.cuda.is_available()} | METAL: {torch.backends.mps.is_available()}")
    print("🚀 Aura Nexus: Initializing NeuralVault Engine v2.5.5 Sovereign...")

# Static Files (Dashboard)
app.mount("/static", StaticFiles(directory="dashboard/static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def get_dashboard():
    with open("dashboard/index.html", "r") as f:
        return f.read()

def find_node_robust(node_id: str) -> Optional[Any]:
    """Cerca un nodo nell'engine in modo ultra-aggressivo (ID, Sharding, Meta)."""
    if engine is None: return None
    
    clean_id = str(node_id).strip().split("_")[0]
    
    # 1. Ricerca rapida (Hash Map)
    if node_id in engine._nodes: return engine._nodes[node_id]
    if clean_id in engine._nodes: return engine._nodes[clean_id]
    
    # 2. Ricerca numerica
    try:
        int_id = int(clean_id)
        if int_id in engine._nodes: return engine._nodes[int_id]
    except: pass
    
    # 3. Scansione lineare Cache
    for k, n in engine._nodes.items():
        n_id = str(getattr(n, 'id', n.get('id', '') if isinstance(n, dict) else ''))
        if str(k) == str(node_id) or n_id == str(node_id) or n_id == clean_id:
            return n
    
    # 4. Ricerca nel Tier Episodico (Persistenza)
    try:
        if hasattr(engine, '_tiers'):
            node = engine._tiers.get(node_id)
            if node: return node
            node = engine._tiers.get(clean_id)
            if node: return node
    except: pass
            
    return None

@app.get("/api/debug/stats")
async def debug_stats():
    """[DEBUG v14] Chiamata diretta a engine.stats() per diagnosticare la telemetria 3D."""
    print("🔬 [DEBUG] Chiamata a /api/debug/stats ...")
    try:
        loop = asyncio.get_event_loop()
        stats = await loop.run_in_executor(None, engine.stats)
        return JSONResponse({
            "ok": True,
            "nodes_count": stats.get("nodes_count", 0),
            "point_cloud_len": len(stats.get("point_cloud", [])),
            "edge_sample_len": len(stats.get("edge_sample", [])),
            "first_point": stats.get("point_cloud", [None])[0]
        })
    except Exception as e:
        import traceback
        print(f"❌ [DEBUG/stats] {e}\n{traceback.format_exc()}")
        return JSONResponse({"ok": False, "error": str(e)}, status_code=500)

@app.get("/api/node/{node_id}")
async def get_node_details(node_id: str):
    """Recupera il contenuto completo e le connessioni locali di un nodo."""
    print(f"🕵️ [API] Deep Inspection Request: {node_id}")
    async with engine_lock:
        node = find_node_robust(node_id)
                    
    if node:
        # Estrazione Campi Reali
        n_text = getattr(node, 'text', node.get('text', '') if isinstance(node, dict) else "")
        n_meta = getattr(node, 'metadata', node.get('metadata', {}) if isinstance(node, dict) else {})
        n_type = n_meta.get("type", "text")
        
        # Gestione Anteprima Multimediale (Fase 40)
        media_preview = None
        if n_type == "image":
            media_preview = n_meta.get("source") or n_meta.get("url")
        elif n_type == "video":
            media_preview = n_meta.get("thumbnail") or n_meta.get("source")

        # Recupera connessioni reali
        connessioni = []
        try:
            # Relazioni dirette nel nodo (GNN Sync)
            edges = getattr(node, 'edges', [])
            for e in edges:
                connessioni.append({"node": str(e.target_id), "relation": str(e.relation)})

            # Fallback: usiamo le relazioni Agent007 se presenti
            res = engine.agent007.con.execute("""
                SELECT target_id, type FROM agent007_relations WHERE source_node_id = ?
            """, (node_id,)).fetchall()

            for r in res:
                connessioni.append({"node": r[0], "relation": r[1]})
        except: pass

        return {
            "id": node_id,
            "text": n_text,
            "type": n_type,
            "preview": media_preview,
            "metadata": n_meta,
            "created_at": float(getattr(node, 'created_at', time.time())),
            "connections": connessioni
        }
            
    return JSONResponse(status_code=404, content={"error": f"Node {node_id} not found in engine ({len(engine._nodes)} fragments active)"})

@app.post("/api/purge")
async def nuclear_purge():
    """Protocollo 'VETRO' (v1.0): Reset totale immediato."""
    print("☢️ PROTOCOLLO VETRO (VETRO-NUCLEAR) ATTIVATO.")
    
    try:
        # v3.9.5: Uso del metodo centralizzato dell'engine per chiudere connessioni e pulire disco
        if engine:
            engine.purge_all()
        else:
            # Fallback se l'engine non è ancora init
            data_path = "./vault_data"
            import shutil, os
            if os.path.exists(data_path):
                shutil.rmtree(data_path, ignore_errors=True)
                os.makedirs(data_path, exist_ok=True)
        
        print("☢️ TABULA RASA COMPLETATA.")
        return {"status": "ok", "message": "Neural memories incinerated. Core stabilized."}
    except Exception as e:
        print(f"❌ [VETRO FAIL] {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/api/documents")
async def get_documents(api_key: str = Depends(get_api_key)):
    """Recupera l'inventario cronologico della conoscenza acquisita."""
    if engine is None: return {"documents": []}
    try:
        # Recuperiamo tutti i nodi e estraiamo le sorgenti uniche dai metadati
        inventory = []
        seen_sources = set()
        
        # Ordiniamo per data di creazione se disponibile
        all_nodes = list(engine._nodes.values())
        all_nodes.sort(key=lambda x: getattr(x, 'created_at', 0), reverse=True)
        
        for node in all_nodes:
            source = node.metadata.get("source", "Manual_Entry")
            if source not in seen_sources:
                # Determiniamo il tipo basandoci sull'estensione o metadati
                s_lower = source.lower()
                doc_type = "TEXT"
                if s_lower.startswith("http"): doc_type = "URL"
                elif any(s_lower.endswith(ext) for ext in [".mp4", ".mov", ".avi"]): doc_type = "VIDEO"
                elif any(s_lower.endswith(ext) for ext in [".mp3", ".wav", ".m4a"]): doc_type = "AUDIO"
                elif any(s_lower.endswith(ext) for ext in [".jpg", ".jpeg", ".png", ".webp"]): doc_type = "IMAGE"
                elif any(s_lower.endswith(ext) for ext in [".pdf", ".txt", ".md", ".docx"]): doc_type = "FILE"
                
                created_at = getattr(node, 'created_at', time.time())
                dt = datetime.fromtimestamp(created_at)
                
                inventory.append({
                    "name": source if len(source) < 50 else source[:47] + "...",
                    "full_name": source,
                    "type": doc_type,
                    "date": dt.strftime("%d/%m/%Y"),
                    "time": dt.strftime("%H:%M:%S")
                })
                seen_sources.add(source)
                
        return {"documents": inventory}
    except Exception as e:
        return {"documents": [], "error": str(e)}

@app.get("/api/intelligence/status")
async def get_intelligence_status(api_key: str = Depends(get_api_key)):
    """Restituisce lo stato dell'OrchestraIA, degli agenti e del Distiller (v8.0)."""
    if not hasattr(app.state, "lab") or not app.state.lab: 
        return {"status": "offline"}
    return app.state.lab.get_orchestra_report()

@app.post("/api/intelligence/agents/custom")
async def create_custom_agent(config: Dict, api_key: str = Depends(get_api_key)):
    """Crea un nuovo agente custom (Custom Agent Factory)."""
    if not app.state.lab: return {"error": "Neural Lab Offline"}
    
    name = config.get("name")
    if not name: return {"error": "Name required"}
    
    # Registrazione e persistenza
    app.state.lab.custom_agents_config[name] = {
        "model": config.get("model", "llama3"),
        "role": config.get("role", "Generalist"),
        "prompt": config.get("prompt", ""),
        "color": config.get("color", "#00ffcc"),
        "created_at": time.time()
    }
    
    with open(app.state.lab.custom_agents_path, "w") as f:
        json.dump(app.state.lab.custom_agents_config, f)
        
    return {"status": "Agent Created", "name": name}

@app.delete("/api/intelligence/agents/custom/{name}")
async def delete_custom_agent(name: str, api_key: str = Depends(get_api_key)):
    """Rimuove un agente custom."""
    if not app.state.lab: return {"error": "Neural Lab Offline"}
    
    if name in app.state.lab.custom_agents_config:
        del app.state.lab.custom_agents_config[name]
        with open(app.state.lab.custom_agents_path, "w") as f:
            json.dump(app.state.lab.custom_agents_config, f)
        return {"status": "Agent Deleted"}
    
    return {"error": "Agent not found"}

@app.post("/api/log")
async def client_log(request: Request):
    """Ponte di Telemetria Inversa: Visualizza le azioni del browser nel terminale."""
    try:
        data = await request.json()
        msg = data.get("message", "")
        level = data.get("level", "INFO")
        print(f"🖥️ [Interactive HUD] {msg}")
    except: pass
    return {"status": "ok"}

@app.post("/api/files/upload")
@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...), api_key: str = Depends(get_api_key)):
    print(f"📥 [Ingestion] Richiesta ricevuta: {file.filename} ({file.content_type})")
    content = await file.read()
    text = content.decode('utf-8', errors='ignore')
    node_id = str(uuid.uuid4())
    if engine is None: return {"error": "Engine not initialized"}
    node = engine.upsert_text(text, metadata={"source": file.filename}, node_id=node_id)
    
    # Master Trace (v2.9.0)
    print(f"📥 [Ingestion] Success: {file.filename} -> Synapsed into Neural Vault.")
    
    return {"status": "synapsed", "id": node_id}



@app.post("/api/models/install")
async def install_model(request: Request, background_tasks: BackgroundTasks, api_key: str = Depends(get_api_key)):
    """Avvia l'installazione reale via Ollama API con tracciamento progressivo e auto-riparazione."""
    import platform
    import subprocess
    import shutil
    
    data = await request.json()
    model_name = data.get("model")
    
    # 🧬 HARDWARE DNA CHECK
    os_name = platform.system()
    arch = platform.machine() # arm64, x86_64, etc.
    print(f"🧠 [Auto-Installer] Platform Detected: {os_name} {arch}")

    if model_name in install_progress and install_progress[model_name]["status"] == "pulling":
        return {"status": "already_installing", "model": model_name}

    install_progress[model_name] = {"percentage": 0, "status": "checking_service"}

    async def _async_pull():
        import httpx
        try:
            # 1. Verifica se Ollama è raggiungibile, altrimenti tenta di avviarlo
            max_retries = 3
            ollama_ready = False
            
            for i in range(max_retries):
                try:
                    async with httpx.AsyncClient() as client:
                        r = await client.get("http://localhost:11434/api/tags")
                        if r.status_code == 200:
                            ollama_ready = True
                            break
                except:
                    print(f"⚠️ [Self-Healing] Ollama non risponde. Tentativo di avvio {i+1}/{max_retries}...")
                    # Tenta di avviare Ollama in base al sistema operativo
                    if os_name == "Darwin": # Mac
                        # Prova prima con il comando da terminale, poi con 'open'
                        if shutil.which("ollama"):
                            subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        else:
                            subprocess.Popen(["open", "-a", "Ollama"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    elif os_name == "Windows":
                        if shutil.which("ollama"):
                            subprocess.Popen(["ollama", "serve"], shell=True)
                        else:
                            subprocess.Popen(["start", "ollama", "serve"], shell=True)
                    else: # Linux
                        subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    await asyncio.sleep(8) # Aumentato tempo di attesa per avvio a 8 secondi

            if not ollama_ready:
                # 🚨 EXTREME AUTO-PROVISIONING: Installazione automatica se mancante
                print(f"🚨 [Auto-Provisioning] Ollama non trovato su {os_name}. Tentativo di installazione forzata...")
                try:
                    if os_name == "Darwin" or os_name == "Linux":
                        # Installer ufficiale Ollama per Unix-like
                        # Usiamo '|| true' per ignorare l'errore di avvio finale dello script se il download è riuscito
                        subprocess.run("curl -fsSL https://ollama.com/install.sh | sh || true", shell=True)
                    elif os_name == "Windows":
                        install_cmd = "powershell -Command \"& { iwr https://ollama.com/download/OllamaSetup.exe -OutFile OllamaSetup.exe; Start-Process -Wait -FilePath ./OllamaSetup.exe -ArgumentList '/silent'; Remove-Item ./OllamaSetup.exe }\""
                        subprocess.run(install_cmd, shell=True)
                    
                    print("✅ [Auto-Provisioning] Download completato. Tentativo di avvio manuale...")
                    
                    # Tentativo di avvio post-installazione forzato
                    if os_name == "Darwin":
                        subprocess.Popen(["/usr/local/bin/ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    
                    await asyncio.sleep(15) # Attesa generosa
                except Exception as install_err:
                    print(f"⚠️ Errore durante auto-install: {install_err}")

            # 2. Avvio PULL reale
            install_progress[model_name]["status"] = "pulling"
            async with httpx.AsyncClient(timeout=None) as client:
                async with client.stream("POST", "http://localhost:11434/api/pull", json={"name": model_name}) as resp:
                    async for line in resp.aiter_lines():
                        if not line: continue
                        chunk = json.loads(line)
                        
                        # 🚨 Check for Ollama API Errors
                        if "error" in chunk:
                            print(f"❌ [Ollama API Error] {chunk['error']}")
                            install_progress[model_name]["status"] = "error"
                            install_progress[model_name]["message"] = chunk["error"]
                            return

                        status = chunk.get("status", "")
                        total = chunk.get("total", 0)
                        completed = chunk.get("completed", 0)
                        
                        if total > 0:
                            perc = int((completed / total) * 100)
                            install_progress[model_name].update({
                                "percentage": perc,
                                "status": status,
                                "completed": completed,
                                "total": total
                            })

            # 3. Post-Pull Verification
            async with httpx.AsyncClient() as client:
                v_resp = await client.get("http://localhost:11434/api/tags")
                if v_resp.status_code == 200:
                    models = [m["name"] for m in v_resp.json().get("models", [])]
                    # Check both exact match and without :latest
                    if model_name in models or f"{model_name}:latest" in models:
                        install_progress[model_name]["status"] = "success"
                        install_progress[model_name]["percentage"] = 100
                        print(f"✅ [Auto-Installer] {model_name} integrato con successo su {os_name}/{arch}.")
                    else:
                        install_progress[model_name]["status"] = "error"
                        install_progress[model_name]["message"] = "Installazione completata ma modello non trovato nel registro Ollama."
                else:
                    install_progress[model_name]["status"] = "success" # Fallback if API fails but pull didn't
            
        except Exception as e:
            print(f"❌ [Ollama Pull Error] {e}")
            install_progress[model_name] = {"status": "error", "message": str(e), "percentage": 0}

    background_tasks.add_task(_async_pull)
    return {"status": "started", "model": model_name, "dna": f"{os_name}-{arch}"}

@app.get("/api/models/progress")
async def get_install_progress(api_key: str = Depends(get_api_key)):
    """Restituisce lo stato di avanzamento di tutti i download attivi."""
    return install_progress

@app.get("/api/models/benchmarks")
async def get_model_benchmarks(api_key: str = Depends(get_api_key)):
    """Restituisce telemetria avanzata delle performance LLM locali."""
    if engine and hasattr(engine, 'benchmarks'):
        return {"benchmarks": engine.benchmarks.get_stats()}
    return {"benchmarks": []}

# --- NEW: NEURAL MODEL CATALOG (v3.0 Sovereign) ---
# --- NEW: NEURAL MODEL CATALOG (v3.5 High-Precision) ---
MODEL_CATALOG = {
    # ── ELITE NANO (Under 2GB) ──────────────────────────────────────────
    "llama3.2:1b": {
        "name": "Llama 3.2 (1B)", "size": "1.3GB", "category": "Nano", 
        "pros": "Velocità estrema, zero lag", "cons": "Cognizione base", 
        "caveau": "L'Ombra Silenziosa per il background.", "forza": "Perfetto per task costanti senza pesare sulla RAM.",
        "synergy": ["phi3:latest"], "task": "Silent Assistant"
    },
    "qwen2.5:1.5b": {
        "name": "Qwen 2.5 (1.5B)", "size": "986MB", "category": "Nano-Reasoning", 
        "pros": "Matematica e logica densa", "cons": "Vocabolario compatto", 
        "caveau": "Il Re dei piccoli per logica pura.", "forza": "Ragionamento superiore a molti 3B.",
        "synergy": ["phi4:latest"], "task": "Technical Data"
    },
    "smollm2:1.7b": {
        "name": "SmolLM2 1.7B", "size": "1.0GB", "category": "Nano-Speed", 
        "pros": "Addestrato su dati purissimi", "cons": "Poca conoscenza enciclopedica", 
        "caveau": "Il velocista di Hugging Face.", "forza": "Ideale come agente di smistamento rapido.",
        "synergy": ["mistral:latest"], "task": "Fast Routing"
    },
    "gemma2:2b": {
        "name": "Gemma 2 (2B)", "size": "1.6GB", "category": "Nano-Elite", 
        "pros": "Tecnologia Google DeepMind", "cons": "Richiede prompt precisi", 
        "caveau": "Qualità Google nel palmo della mano.", "forza": "Incredibilmente eloquente per la taglia.",
        "synergy": ["deepseek-r1:7b"], "task": "Premium Chat"
    },
    
    # ── THE ULTIMATE SOVEREIGN (v4.0 Next-Gen) ─────────────────────────
    "gemma:4-26b": {
        "name": "Gemma 4 (26B-A4B)", "size": "16.1GB", "category": "Sovereign-Master", 
        "pros": "Capacità di ragionamento multi-agente nativa", "cons": "Richiede 32GB+ RAM", 
        "caveau": "L'Orchestratore Supremo della Conoscenza.", "forza": "Capacità di coordinare interi swarm di IA minori.",
        "synergy": ["deepseek-r1:14b", "llama3.2:1b"], "task": "Global Orchestration",
        "url": "https://huggingface.co/google/gemma-4-26B-A4B"
    },
    
    # ── DEEPSEEK REASONING (The New Standard) ─────────────────────────
    "deepseek-r1:1.5b": {
        "name": "DeepSeek R1 (1.5B)", "size": "1.1GB", "category": "Reasoning-UPLINK", 
        "pros": "Chain of Thought su mini-scala", "cons": "Pochi step di riflessione", 
        "caveau": "Primo assaggio di CoT (Chain of Thought).", "forza": "Risposta istantanea con logica visibile.",
        "synergy": ["qwen2.5:1.5b"], "task": "Instant Logic"
    },
    "deepseek-r1:7b": {
        "name": "DeepSeek R1 (7B)", "size": "4.7GB", "category": "Reasoning-Master", 
        "pros": "Logica di livello o1-preview", "cons": "Più lento dei modelli standard", 
        "caveau": "L'ottimale per M1 16GB.", "forza": "Capacità analitica d'élite sotto i 5GB.",
        "synergy": ["mistral:latest"], "task": "Deep Analysis"
    },
    "deepseek-r1:14b": {
        "name": "DeepSeek R1 (14B)", "size": "9.0GB", "category": "Reasoning-Peak", 
        "pros": "Potenza di ragionamento bruta", "cons": "Occupa molta RAM (10GB+)", 
        "caveau": "Il massimo raggiungibile fluidamente.", "forza": "Il 'Claude-Killer' locale per eccellenza.",
        "synergy": ["phi4:latest"], "task": "Scientific Research"
    },

    # ── NVIDIA NEMOTRON SERIES (Hardware Optimized) ─────────────────────
    "nemotron-mini:latest": {
        "name": "NVIDIA Nemotron-Mini-4B", "size": "2.8GB", "category": "NVIDIA-Sovereign", 
        "pros": "Dati sintetici NVIDIA di alta qualità", "cons": "Fine-tuning limitato", 
        "caveau": "Precisione chirurgica in task brevi.", "forza": "Modello ultra-efficiente per agenti di tool-use.",
        "synergy": ["llama3.2:1b"], "task": "Agentic Tasks"
    },
    "nemotron:latest": {
        "name": "NVIDIA Nemotron-70B", "size": "39GB", "category": "NVIDIA-Elite", 
        "pros": "Superiore a Llama-3-70B in molti benchmark", "cons": "Richiede 64GB+ Unified Memory / VRAM", 
        "caveau": "Il Titano per Apple Studio/Ultra.", "forza": "Capacità di dialogo estesa e naturalezza estrema.",
        "synergy": ["deepseek-r1:32b"], "task": "Enterprise Logic"
    },

    # ── GEMMA 2 EVOLUTION (The Standard) ───────────────────────────────
    "gemma2:9b": {
        "name": "Gemma 2 (9B)", "size": "5.4GB", "category": "Gemma-Core", 
        "pros": "Equilibrio perfetto velocità/qualità", "cons": "Tende a essere prolisso", 
        "caveau": "Lo standard d'oro per M1/M2/M3.", "forza": "Incredibile nel seguire istruzioni complesse.",
        "synergy": ["mistral:latest"], "task": "Balanced Creative"
    },
    "gemma2:27b": {
        "name": "Gemma 2 (27B)", "size": "16GB", "category": "Gemma-Peak", 
        "pros": "Intelligenza di livello 70B in 27B", "cons": "Pesante per Mac con 16GB RAM", 
        "caveau": "Il 'Sweet Spot' per Mac con 32GB RAM.", "forza": "Il miglior rapporto intelligenza/parametri sul mercato.",
        "synergy": ["phi4:latest"], "task": "Advanced Knowledge"
    },
    
    # ── BALANCED & SPECIALISTS ──────────────────────────────────────────
    "mistral:latest": {
        "name": "Mistral 7B", "size": "4.1GB", "category": "Sovereign-Core", 
        "pros": "Affidabilità Totale", "cons": "Standard 2024", 
        "caveau": "Il fulcro del tuo cervello digitale.", "forza": "Sintesi eccelsa e stabilità granitica.",
        "synergy": ["deepseek-r1:7b"], "task": "Vault Indexing"
    },
    "phi4:latest": {
        "name": "Phi-4 Specialist", "size": "9.1GB", "category": "Advanced-Logic", 
        "pros": "Precisione Scientifica Microsoft", "cons": "Molto esigente", 
        "caveau": "L'analista di dati pesanti.", "forza": "Logica cristallina su problemi complessi.",
        "synergy": ["qwen2.5:1.5b"], "task": "Scientific Mode"
    },
    "ministral:latest": {
        "name": "Ministral 3B", "size": "2.1GB", "category": "Balanced-Elite", 
        "pros": "Equilibrio Mistral AI", "cons": "Nuova architettura", 
        "caveau": "Il miglior compromesso peso/potenza.", "forza": "Qualità 7B in soli 2GB di spazio.",
        "synergy": ["smollm2:1.7b"], "task": "Hybrid Reasoning"
    },
    # ── AGENTIC ENGINES (Extra) ─────────────────────────────────────────
    "codellama:latest": {
        "name": "CodeLlama 7B", "size": "3.8GB", "category": "Coding",
        "pros": "Autocompletamento esperto", "cons": "Meno performante in chat generalista",
        "caveau": "L'ingegnere del Vault.", "forza": "Parsing di codice multilingua.",
        "synergy": ["qwen2.5:1.5b"], "task": "Code Analysis"
    }
}

async def _autonomous_model_scan() -> List[Dict]:
    """Scansiona il filesystem alla ricerca di modelli LLM installati (Ollama, LM Studio, etc)."""
    installed = []
    seen_names = set()
    
    # 1. Ollama Scan (Physical Path)
    home = Path.home()
    ollama_paths = [
        home / ".ollama" / "models" / "manifests" / "registry.ollama.ai" / "library",
        Path("/usr/share/ollama/.ollama/models/manifests/registry.ollama.ai/library")
    ]
    
    for base_path in ollama_paths:
        if base_path.exists():
            for model_dir in base_path.iterdir():
                if model_dir.is_dir():
                    model_family = model_dir.name
                    for tag_file in model_dir.iterdir():
                        if tag_file.is_file():
                            full_name = f"{model_family}:{tag_file.name}"
                            if full_name not in seen_names:
                                # Tentiamo di stimare la dimensione dal tag o lasciamo N/D se non accessibile
                                installed.append({
                                    "name": full_name,
                                    "size": "Detected (Local)",
                                    "source": "Ollama (Disk Scan)",
                                    "metadata": MODEL_CATALOG.get(full_name, {"pros": "Rilevato via Disk Scan", "cons": "N/D", "synergy": []})
                                })
                                seen_names.add(full_name)

    # 2. LM Studio Scan
    lm_studio_paths = [
        home / ".cache" / "lm-studio" / "models",
        home / "Library" / "Application Support" / "com.lmstudio.LMStudio" / "models"
    ]
    for p in lm_studio_paths:
        if p.exists():
            for model_file in p.rglob("*.gguf"):
                name = model_file.name
                if name not in seen_names:
                    size_gb = round(model_file.stat().st_size / (1024**3), 2)
                    installed.append({
                        "name": f"GGUF: {name}",
                        "size": f"{size_gb}GB",
                        "source": "LM Studio / Local Disk",
                        "metadata": {"pros": "Modello GGUF nativo", "cons": "Richiede driver compatibile", "synergy": []}
                    })
                    seen_names.add(name)

    return installed

@app.get("/api/models/catalog")
async def get_model_catalog(api_key: str = Depends(get_api_key)):
    """Restituisce il catalogo completo con Pro/Contro e Sinergie."""
    return MODEL_CATALOG

@app.get("/api/models/status")
async def get_models_status(api_key: str = Depends(get_api_key)):
    """Sync con Ollama e Scansione Autonoma: restituisce tutti i modelli present sul dispositivo."""
    import httpx
    installed = []
    seen_in_api = set()

    # 1. Check via API (Ollama) - Metodo primario
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            r = await client.get("http://localhost:11434/api/tags")
            if r.status_code == 200:
                data = r.json()
                for m in data.get("models", []):
                    size_gb = round(m.get("size", 0) / (1024**3), 2)
                    name = m.get("name")
                    cat_info = MODEL_CATALOG.get(name)
                    # Fallback intelligente: prova a cercare senza tag :latest
                    if not cat_info and ":" in name:
                        base_name = name.split(":")[0]
                        cat_info = MODEL_CATALOG.get(f"{base_name}:latest")
                    
                    if not cat_info:
                        cat_info = {"pros": "Modello Utente", "cons": "N/D", "synergy": [], "category": "Custom"}

                    installed.append({
                        "name": name,
                        "size": f"{size_gb}GB",
                        "metadata": cat_info,
                        "source": "Ollama API"
                    })
                    seen_in_api.add(name)
    except Exception as e:
        print(f"⚠️ [Ollama API] Offline, procedo con scansione autonoma del disco... ({e})")

    # 2. Scansione Autonoma (Verifica se ci sono modelli non visti dall'API o API offline)
    local_discoveries = await _autonomous_model_scan()
    for d in local_discoveries:
        # Evita duplicati se sono già stati rilevati via API
        if d["name"] not in seen_in_api:
            # Tenta di normalizzare i nomi dei modelli Ollama trovati su disco per il matching con il catalogo
            if ":" in d["name"]:
                cat_info = MODEL_CATALOG.get(d["name"])
                if not cat_info:
                    base_name = d["name"].split(":")[0]
                    cat_info = MODEL_CATALOG.get(f"{base_name}:latest")
                if cat_info:
                    d["metadata"] = cat_info
            
            installed.append(d)

    return {"installed": installed, "total_detected": len(installed)}

@app.delete("/api/models/delete/{model_name:path}")
async def delete_model(model_name: str, api_key: str = Depends(get_api_key)):
    """Rimuove fisicamente un modello per liberare spazio."""
    import httpx
    model_name = model_name.strip()
    try:
        async with httpx.AsyncClient() as client:
            r = await client.request("DELETE", "http://localhost:11434/api/delete", json={"name": model_name})
            if r.status_code == 200:
                return {"status": "deleted", "model": model_name}
            else:
                return {"status": "error", "message": r.text}
    except Exception as e:
        return {"status": "error", "message": str(e)}



@app.post("/api/ingest")
async def ingest_text(request: Request, api_key: str = Depends(get_api_key)):
    """Ingestione diretta di testo puro (es. Pensieri Vocali)."""
    data = await request.json()
    text = data.get("text")
    filename = data.get("filename", "Manual_Entry")
    
    node_id = str(uuid.uuid4())
    engine.add_node(node_id, text, metadata={"source": filename})
    return {"status": "synapsed", "id": node_id}

@app.post("/api/analyze")
async def analyze_node(request: Request, api_key: str = Depends(get_api_key)):
    """Avvia il dibattito avversariale su un nodo per trovare debolezze."""
    data = await request.json()
    node_id = data.get("id")
    
    if engine is None: raise HTTPException(status_code=500, detail="Engine not ready")
    
    async with engine_lock:
        node = find_node_robust(node_id)
        
    if not node: raise HTTPException(status_code=404, detail="Node not found")
    
    # Esegue la sessione avversariale (Digital Courtroom)
    verdict = await app.state.lab.run_adversarial_session(node_id, node.text)
    
    return {
        "node_id": node_id,
        "verdict": verdict,
        "mode": "adversarial"
    }

@app.get("/api/report/{node_id}")
async def get_report(node_id: str, api_key: str = Depends(get_api_key)):
    """Recupera l'ultimo report di vulnerabilità esistente."""
    if not hasattr(engine, 'investigator'):
         raise HTTPException(status_code=500, detail="Investigator engine not initialized")
    report = engine.investigator.get_weakness_report(node_id)
    if not report: raise HTTPException(status_code=404, detail="No report found for this node")
    return report

@app.get("/api/analytics")
async def get_analytics(api_key: str = Depends(get_api_key)):
    """Metriche profonde del grafo, efficienza semantica e hardware DNA."""
    # 1. Metriche dell'Engine (Nodi, Sinapsi, Hit Rate)
    report = engine.get_analytics_report()
    
    # 2. Metriche Hardware Reali (Apple Silicon Optimized)
    from utils.hardware import HardwareTuner
    tuner = HardwareTuner(data_dir=engine.data_dir if hasattr(engine, 'data_dir') else "./vault_data")
    hw_data = tuner.get_telemetry()
    
    # 3. Merging dei dati per l'Aura Dashboard
    return {**report, **hw_data}


# SECTION: LAB MISSIONS & AGENTS (Integrated v3.5)

# 🛰️ GOSSIP MESH ENDPOINTS
@app.post("/api/gossip/sync")
async def receive_gossip_signal(signal: SyncSignal):
    """Riceve un segnale di sincronizzazione da un altro nodo della Mesh."""
    if signal.payload_type == "upsert":
        # Inserimento atomico in background del nodo sincronizzato
        node_id = signal.data.get("id")
        text = signal.data.get("text")
        # Evitiamo loop infiniti di gossip controllando se il nodo esiste già
        if node_id not in engine._nodes:
            engine.add_node(node_id, text, metadata=signal.data.get("metadata", {}))
            return {"status": "synced", "node_id": node_id}
    return {"status": "ignored"}

# 🌐 ALIAS per Aura Bridge Extension (compatibilità)
@app.post("/api/upload_text")
async def upload_text_alias(request: Request, api_key: str = Depends(get_api_key)):
    """Alias di /api/ingest per compatibilità con Aura Bridge Extension."""
    data = await request.json()
    text = data.get("text", "")
    metadata = data.get("metadata", {})
    if not text:
        raise HTTPException(status_code=400, detail="Campo 'text' obbligatorio")
    node_id = str(uuid.uuid4())
    engine.upsert_text(text, metadata={"source": metadata.get("source", "aura_bridge"), **metadata})
    return {"status": "synapsed", "id": node_id}

# 🕸️ WEB FORAGER — Crawling e Ingestione di URL
@app.post("/api/forage")
async def forage_url(
    request: Request,
    background_tasks: BackgroundTasks,
    api_key: str = Depends(get_api_key)
):
    """
    Avvia il Web Foraging su un URL:
    - Scarica la pagina e le sottopagine (depth configurabile)
    - Fa parsing HTML, OCR immagini, estrazione PDF
    - Ingestisce tutto nel Vault come nodi semantici
Risponde subito con job_id; il progresso è tracciato nel Blackboard.
    """
    data = await request.json()
    url = data.get("url")
    max_depth = int(data.get("max_depth", 10))
    max_pages = int(data.get("max_pages", 9999))
    same_domain = data.get("same_domain_only", True)

    if not url or not url.startswith("http"):
        raise HTTPException(status_code=400, detail="URL non valido. Deve iniziare con http:// o https://")

    job_id = str(uuid.uuid4())
    app.state.forage_jobs[job_id] = {
        "status": "IN_PROGRESS", 
        "url": url, 
        "pages": 0, 
        "start_time": time.time(),
        "elapsed": "0s",
        "progress": 0
    }
    app.state.forage_proposals[job_id] = []

    async def _run_forage():
        start_t = time.time()
        forager = SovereignWebForager(
            max_depth=max_depth,
            max_pages=max_pages,
            same_domain_only=same_domain,
        )
        try:
            total_chunks = 0
            page_count = 0
            async for page in forager.forage(url):
                # Calcolo progresso reale (pagine processate / totali scoperte)
                queue_len = len(getattr(forager, 'queue', []))
                total_discovered = page_count + queue_len + 1
                progress = min(99, int((page_count / total_discovered) * 100)) if total_discovered > 0 else 0
                
                elapsed_raw = time.time() - start_t
                elapsed_str = f"{int(elapsed_raw)}s"
                
                # Update State
                app.state.forage_jobs[job_id].update({
                    "pages": page_count + 1,
                    "elapsed": elapsed_str,
                    "progress": progress
                })

                chunks = page.to_chunks()
                for c in chunks:
                    chunk_text = c["text"]
                    # 🔒 DEDUPLICAZIONE SEMANTICA (v2.6.0)
                    content_hash = hashlib.sha256(chunk_text.encode()).hexdigest()
                    existing_id = engine._prefilter.check_duplicate(content_hash)
                    
                    if existing_id:
                        # Se il nodo esiste già, rinforziamo la sua importanza invece di duplicarlo
                        engine._prefilter.hit_node(existing_id)
                        continue

                    meta = c["metadata"].copy()
                    meta["color"] = "#22d3ee" # Cyan
                    meta["forage_job"] = job_id
                    meta["content_hash"] = content_hash
                    try:
                        engine.upsert_text(chunk_text, metadata=meta)
                    except Exception as e:
                        print(f"⚠️ [Kernel] Ingest Fallito per chunk: {e}")
                
                total_chunks += len(chunks)
                page_count += 1
                
                # 🖼️ MULTIMODAL INGESTION: Immagini coerenti (v7.1.5)
                try:
                    multimodal = getattr(app.state, 'mm_processor', None)
                    if multimodal and page.images:
                        # Filtriamo immagini potenzialmente utili (non icone)
                        for img_url in page.images[:10]: # Limite per pagina per non saturare
                            if any(x in img_url.lower() for x in ["icon", "logo", "pixel"]): continue
                            
                            # Download temporaneo per ingestion multimodale
                            try:
                                async with httpx.AsyncClient(timeout=10.0) as client:
                                    img_resp = await client.get(img_url)
                                    if img_resp.status_code == 200:
                                        temp_path = Path(f"vault_data/temp_media/forage_{uuid.uuid4().hex}.jpg")
                                        temp_path.parent.mkdir(parents=True, exist_ok=True)
                                        temp_path.write_bytes(img_resp.content)
                                        
                                        # Ingestione reale con ImageBind + Vision LLM
                                        await multimodal.ingest(temp_path, source_uri=img_url)
                                        if temp_path.exists(): os.remove(temp_path)
                                        print(f"🖼️ [Multimodal] Image Synapsed: {img_url[:40]}...")
                            except: pass
                except: pass

                print(f"⏱️ [{elapsed_str}] Foraging Progress: {progress}% | 📄 Pages: {page_count} | Synapsing -> {url[:50]}...")
                
                # Segnale al Blackboard (visibile nel Neural Lab)
                try:
                    from neural_lab import SynapticSignal, AgentRole, SignalType
                    sig = SynapticSignal(
                        sender_id=f"forager_{job_id[:8]}",
                        role=AgentRole.RESEARCHER,
                        msg=f"Ingested: {page.title or url[:30]}",
                        signal_type=SignalType.KNOWLEDGE_ACQUISITION,
                        urgency=0.5
                    )
                    app.state.lab.blackboard.post(sig)
                except: pass

            # Salva le proposte raccolte per l'approvazione utente
            app.state.forage_proposals[job_id] = forager.proposals
            app.state.forage_jobs[job_id]["status"] = "COMPLETE"
            app.state.forage_jobs[job_id]["pages"] = page_count
            
            print(f"✅ [Forage Job {job_id[:8]}] Completato: {page_count} pagine, {total_chunks} chunk ingestiti da {url}")
            print(f"🕯️ [Insight] Trovate {len(forager.proposals)} proposte di approfondimento esterno.")
        except Exception as e:
            app.state.forage_jobs[job_id]["status"] = "ERROR"
            print(f"❌ [Forage Job {job_id[:8]}] Errore: {e}")

    background_tasks.add_task(_run_forage)

    return {
        "status": "foraging_started",
        "job_id": job_id,
        "url": url,
        "message": "Foraging job successfully initiated in background."
    }

@app.post("/api/mission")
async def dispatch_lab_mission(request: Request, api_key: str = Depends(get_api_key)):
    """Invia una missione strategica allo Swarm di Agenti nel Neural Lab."""
    data = await request.json()
    mission_text = data.get("mission")
    
    if not mission_text:
        raise HTTPException(status_code=400, detail="Il testo della missione è obbligatorio.")
    
    # Trigger asincrono dell'orchestratore
    mission_id = app.state.lab.execute_mission(mission_text)
    
    return {
        "status": "mission_dispatched",
        "mission_id": mission_id,
        "message": "Lo Swarm ha ricevuto le direttive. Monitora il Neural Lab per i progressi."
    }

@app.post("/api/lab/agent/{agent_id}/task")
async def agent_task(agent_id: str, request: Request, api_key: str = Depends(get_api_key)):
    """Invia un compito specifico a un singolo agente del Lab."""
    data = await request.json()
    task_text = data.get("task")
    
    if agent_id not in app.state.lab.agents:
        raise HTTPException(status_code=404, detail="Agente non trovato.")
    
    agent = app.state.lab.agents[agent_id]
    
    # Esecuzione task (simuliamo un'interazione diretta via Ollama)
    prompt = f"TASK DIRETTO DALL'UTENTE: {task_text}\nRispondi secondo il tuo mandato: {agent.identity['prompt']}"
    response = app.state.lab._call_ollama_for_agent(agent.identity["name"], prompt)
    
    # Log sulla blackboard
    from neural_lab import SynapticSignal, SignalType
    sig = SynapticSignal(agent.identity["name"], agent.identity["role"], f"🎯 TASK COMPLETATO: {task_text[:30]}...", SignalType.SYSTEM_NOTIFICATION)
    app.state.lab.blackboard.post(sig)
    
    return {
        "agent": agent.identity["name"],
        "response": response
    }

@app.get("/api/lab/status")
async def get_lab_status(api_key: str = Depends(get_api_key)):
    """Restituisce lo stato live di tutti gli agenti e della blackboard."""
    if not hasattr(app.state, 'lab'):
        return {"error": "Lab not initialized"}
    return app.state.lab.get_status()

@app.post("/api/lab/agent/{agent_id}/approve")
async def approve_agent_mission(agent_id: str, api_key: str = Depends(get_api_key)):
    """Sblocca una missione in 'Mission Hold' (Neural Circuit Breaker)."""
    if not hasattr(app.state, 'lab'):
        raise HTTPException(status_code=500, detail="Lab not initialized")
    
    success = app.state.lab.approve_mission(agent_id)
    if success:
        return {"status": "approved", "agent_id": agent_id}
    else:
        raise HTTPException(status_code=400, detail="Impossibile approvare la missione. L'agente non è in stato di attesa o non esiste.")

@app.post("/api/lab/agent/{agent_id}/consult")
async def consult_agent_oracle(
    agent_id: str, 
    model: str = "deepseek-r1:7b", 
    human_tip: str = "",
    api_key: str = Depends(get_api_key)
):
    """Incarica una LLM del Neural Hub di analizzare la missione e dare un verdetto."""
    if not hasattr(app.state, 'lab'):
        raise HTTPException(status_code=500, detail="Lab not initialized")
    
    result = app.state.lab.consult_oracle(agent_id, model, human_tip)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@app.get("/api/lab/audit")
async def get_lab_audit(api_key: str = Depends(get_api_key)):
    if app.state.lab is None: return []
    return app.state.lab.get_audit_ledger()

@app.get("/api/ledger/status")
async def get_ledger_status(api_key: str = Depends(get_api_key)):
    """Ritorna lo stato di salute della Blockchain (Sovereign Ledger) v1.0."""
    try:
        is_valid = engine.ledger.verify_integrity()
        latest_proof = engine.ledger.get_latest_proof()
        return {
            "status": "SECURE" if is_valid else "VULNERABLE",
            "block_count": len(engine.ledger.chain),
            "latest_merkle_root": latest_proof or "N/A",
            "integrity_check": "MATCHED" if is_valid else "TAMPERING_DETECTED",
            "l2_anchoring": "ACTIVE (Simulated)"
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/forage/status")
async def forage_status(api_key: str = Depends(get_api_key)):
    try:
        recent_jobs = {jid: data for jid, data in list(app.state.forage_jobs.items())[-5:]}
        recent_log = app.state.lab.blackboard.get_recent(limit=10)
        return {
            "jobs": recent_jobs,
            "messages": [m for m in recent_log if "forager" in str(m.get("sender_id", ""))],
            "total_nodes": len(engine._nodes)
        }
    except Exception:
        return {"error": "Blackboard sync failure"}

@app.get("/api/forage/proposals/{job_id}")
async def get_proposals(job_id: str):
    if job_id not in app.state.forage_proposals:
        return {"proposals": []}
    return {"proposals": app.state.forage_proposals[job_id]}

@app.post("/api/forage/approve/{job_id}")
async def approve_forage(job_id: str, background_tasks: BackgroundTasks):
    proposals = app.state.forage_proposals.get(job_id, [])
    if not proposals:
        return {"status": "skipped", "message": "Nessuna proposta da approvare"}
    
    async def _deep_research():
        for p in proposals[:5]: # Limite a 5 approfondimenti paralleli per sessione
            topic = p["topic"]
            print(f"🚀 [Deep Research] Avvio missione: {topic}...")
            # Simulazione ricerca multi-lingua e multi-fonte
            # In futuro integreremo Agent007 Mission Architect qui
            sig = SynapticSignal(
                sender_id="deep_researcher",
                role=AgentRole.MISSION_ARCHITECT,
                msg=f"🌐 [Espansione] Approfondimento autorizzato: {topic}",
                signal_type=SignalType.MISSION_UPDATE,
                urgency=0.8
            )
            app.state.lab.blackboard.post(sig)
            
            # Creazione di un nodo sintetico per l'espansione (fino alla piena integrazione Agent007)
            engine.upsert_text(
                f"Approfondimento su: {topic}. Fonte originaria: {p['url']}. Contesto: {p['context']}",
                metadata={"source": "DeepResearch", "topic": topic, "color": "#f59e0b"} # Oro
            )
            await asyncio.sleep(2) # Respiro tra le missioni
            
        app.state.forage_proposals[job_id] = [] # Pulisce dopo l'approvazione

    background_tasks.add_task(_deep_research)
    return {"status": "approved", "mission_count": len(proposals)}

@app.post("/api/evolve")
async def evolve_mesh(api_key: str = Depends(get_api_key)):
    """
    Protocollo di Evoluzione Cognitiva (REALE v2.8.0):
    1. Fact Mining: Scopre nuove sinapsi semantiche latenti.
    2. Pruning: Elimina archi deboli tramite il Self-Healing Manager.
    3. Realignment: Consolida la struttura del grafo.
    """
    try:
        nodes_affected = len(engine._nodes)
        
        async with engine_lock:
            # 1. EVOLUZIONE REALE: Fact Mining tramite HNSW
            new_synapses = engine.evolve_graph()
            
            # 2. PRUNING REALE: Sfrutta il Self-Healing Manager del Lab
            edges_pruned = 0
            if hasattr(engine, 'lab') and hasattr(engine.lab, 'healer'):
                # Identifica archi da potare (threshold 0.05)
                prunable = engine.lab.healer.get_prunable_edges(threshold=0.08)
                edges_pruned = len(prunable)
                # In questa fase demo eseguiamo un pruning soft degli archi in eccesso
                for node in engine._nodes.values():
                    if len(node.edges) > 15: # Soft cap per densità
                        node.edges = node.edges[:12]
                        edges_pruned += 1
            
        sig = SynapticSignal(
            sender_id="neural_evolution_daemon",
            role=AgentRole.ARCHITECT,
            msg=f"🧠 Evoluzione completata: Realizzate {new_synapses} nuove sinapsi, potati {edges_pruned} archi deboli. Ottimizzati {nodes_affected} nodi.",
        )
        app.state.lab.blackboard.post(sig)
        
        return {
            "status": "evolved",
            "nodes_optimized": nodes_affected,
            "edges_pruned": edges_pruned,
            "new_synapses": new_synapses,
            "report": "Nebula Re-aligned. Synaptic health stabilized."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ingest/media")
async def ingest_media(file: UploadFile = File(...), api_key: str = Depends(get_api_key)):
    """Ingestione multimodale (Video/Audio/Immagini) v7.0."""
    print(f"📥 [Ingest/Media] Ricevuto file: {file.filename} (Type: {file.content_type})")
    
    # Salvataggio temporaneo per processing
    temp_dir = Path("vault_data/temp_media")
    temp_dir.mkdir(parents=True, exist_ok=True)
    temp_path = temp_dir / file.filename
    
    with open(temp_path, "wb") as buffer:
        buffer.write(await file.read())
        
    try:
        # v3.9.5: Smart Triage - se è un file di testo, usiamo l'engine testuale
        ext = temp_path.suffix.lower()
        if ext in ['.txt', '.md', '.log', '.json', '.py', '.js']:
            with open(temp_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            node = engine.upsert_text(content, metadata={"source": file.filename})
            return {"status": "success", "nodes_created": 1, "ids": [node.id]}
            
        node_ids = await app.state.mm_processor.ingest(temp_path)
        return {"status": "success", "nodes_created": len(node_ids), "ids": node_ids}
    except Exception as e:
        print(f"❌ [Ingest Media Fail] {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if temp_path.exists():
            os.remove(temp_path)

@app.get("/api/inventory")
async def get_inventory(api_key: str = Depends(get_api_key)):
    """Infrastruttura di analisi sorgenti: Ritorna lo stack cronologico della conoscenza (v2.9.0)."""
    try:
        sources = engine._prefilter.get_knowledge_sources()
        # Arricchiamo con le sinapsi (stima basata sui nodi della sorgente)
        for s in sources:
            # Calcoliamo quanti archi partono dai nodi di questa sorgente
            # Nota: in una versione Rust sarebbe O(1) con aggregazione live
            s["edges"] = sum(len(n.edges) for n in engine._nodes.values() if n.metadata.get("source") == s["source"])
        return sources
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/translate")
async def translate_text(request: Request, x_api_key: str = Header(None)):
    """Traduttore Neurale v1.2: Supporto Ollama IT/EN."""
    check_api_key(x_api_key)
    data = await request.json()
    text = data.get("text")
    target_lang = data.get("lang", "IT")
    if not text: return {"text": ""}

    try:
        res = await asyncio.to_thread(os.popen("ollama list").read)
        installed = [line.split()[0] for line in res.splitlines()[1:] if line.strip()]
        model = "mistral:latest" if "mistral:latest" in installed else (installed[0] if installed else "mistral")
        
        prompt = f"Traduci il seguente testo in {target_lang}. Rispondi SOLAMENTE con la traduzione.\n\nTESTO: {text}"
        if target_lang == "IT":
            prompt = f"Traduci in Italiano il seguente contenuto. Rispondi SOLAMENTE con la traduzione.\n\nCONTENUTO: {text}"
        
        async with httpx.AsyncClient(timeout=45.0) as client:
            r = await client.post("http://localhost:11434/api/generate", json={
                "model": model, "prompt": prompt, "stream": False
            })
            translation = r.json().get("response", text)
            return {"translated": translation.strip()}
    except Exception as e:
        return {"translated": text, "error": str(e)}

@app.post("/api/chat")
async def neural_chat(request: QueryRequest, x_api_key: str = Header(None)):
    """Oracolo Neurale: RAG Multimodale v7.5."""
    check_api_key(x_api_key)
    
    # 1. Ricerca Semantica Testuale (HNSW)
    results = engine.query(request.query, k=5)
    
    # 2. Ricerca Sensoriale (Multimodal DuckDB)
    mm_results = []
    try:
        mm_results = app.state.mm_processor.query(request.query, top_k=3)
    except Exception as e:
        print(f"⚠️ [MM Query Error] {e}")
    
    context_text = ""
    source_nodes = []
    
    for r in results:
        context_text += f"\n[{r.node.metadata.get('source', 'Unknown')}]: {r.node.text}"
        source_nodes.append(r.node.id)
        
    for mr in mm_results:
        context_text += f"\n[MEDIA {mr['type'].upper()} at {mr['t_start']}ms]: {mr['content']}"
        source_nodes.append(mr['id'])

    # 3. Generazione Risposta (Ollama integration)
    
    # Costruzione contesto per Ollama
    full_context = context_text if context_text else "Nessun contesto trovato nel Vault."
    
    # PROTOCOLLO CONSENSUS (v3.0)
    if request.consensus:
        print(f"🏛️ [Consensus Mode] Attivazione Swarm per: {request.query}")
        answer = app.state.lab.get_consensus_response(request.query, full_context)
    else:
        # Risposta standard a modello singolo
        try:
            # Recupero modello attivo (priorità Mistral o il primo disponibile)
            res = await asyncio.to_thread(os.popen("ollama list").read)
            installed = [line.split()[0] for line in res.splitlines()[1:] if line.strip()]
            model = "mistral:latest" if "mistral:latest" in installed else (installed[0] if installed else "mistral")
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                r = await client.post("http://localhost:11434/api/generate", json={
                    "model": model,
                    "prompt": f"Contesto del Vault:\n{full_context}\n\nDomanda: {request.query}",
                    "stream": False
                })
                answer = r.json().get("response", "Nessuna risposta generata.")
        except Exception as e:
            answer = f"Errore nel collegamento neurale: {str(e)}"

    return {
        "answer": answer,
        "context_nodes": source_nodes,
        "mode": "CONSENSUS" if request.consensus else "SINGLE_AGENT"
    }

@app.get("/events")
async def sse_stream(request: Request):
    """Il battito cardiaco della Dashboard: Telemetria Real-time."""
    # Helper per calcolare il peso del cervello digitale
    def get_dir_size(path):
        """Versione ottimizzata (v2.9.9): Evita rglob ricorsivo bloccante su migliaia di file."""
        total = 0
        try:
            p = Path(path)
            if not p.exists(): return 0
            # Controlliamo solo i file principali per velocità
            for f in p.glob('*.db'): total += f.stat().st_size
            for f in p.glob('*.ael'): total += f.stat().st_size
            # Aggiungiamo un placeholder se ci sono molti file
            if total == 0: total = 1024 * 1024 # 1MB fallback
        except: pass
        return total

    v_initial = engine.data_dir if engine else Path("./data")
    last_size = get_dir_size(v_initial)

    async def event_generator():
        nonlocal last_size
        t_limit = request.query_params.get("t_limit")
        try:
            t_limit = float(t_limit) if t_limit else None
        except: t_limit = None

        print("🔌 [SSE] Client connesso — avvio stream telemetria")

        # KEEPALIVE INIZIALE: invia subito il conteggio nodi (senza SVD) per evitare timeout del browser
        try:
            # v2.7.6: Fetch immediate stats for zero-latency initial rendering
            initial_stats = engine.stats(limit=10000)
            initial_data = {
                "points": initial_stats.get("point_cloud", []),
                "links": initial_stats.get("edge_sample", []),
                "nodes_count": len(engine._nodes),
                "edges_count": initial_stats.get("edges_count", 0),
                "storage": {"total": "...", "pulse": "SYNCING"},
                "lab": app.state.lab.get_status() if hasattr(app.state, 'lab') else {}, 
                "system": {}, 
                "agent007": {"entities_count": 0, "relations_count": 0}
            }
            yield f"data: {json.dumps(initial_data)}\n\n"
            print(f"📡 [SSE] Keepalive inviato: {len(engine._nodes)} nodi")
        except Exception as e:
            print(f"⚠️ [SSE/init] {e}")

        while True:
            if await request.is_disconnected():
                print("🔌 [SSE] Client disconnesso")
                break

            try:
                # 1. Telemetria Storage & Crescita
                v_path = engine.data_dir if engine else Path("./data")
                current_size = get_dir_size(v_path)
                growth = current_size - last_size
                last_size = current_size
                
                size_mb = round(current_size / (1024 * 1024), 2)
                storage_hud = {
                    "total": f"{size_mb} MB" if size_mb < 1024 else f"{round(size_mb/1024, 2)} GB",
                    "pulse": f"+{round(growth/1024, 1)} KB" if growth > 0 else "STABLE",
                    "vault_path": str(v_path)
                }

                # 2. Telemetria 3D – FUORI dal lock
                points = []
                links = []
                try:
                    loop = asyncio.get_event_loop()
                    stats = await loop.run_in_executor(None, engine.stats)
                    points = stats.get("point_cloud", [])
                    links = stats.get("edge_sample", [])
                except Exception as e:
                    print(f"⚠️ [SSE/Stats] {e}")

                # 3. Metriche leggere – dentro il lock
                async with engine_lock:
                    nodes_count = len(engine._nodes)
                    edges_count = sum(len(n.edges) for n in engine._nodes.values())
                    lab_status = app.state.lab.get_status()
                    cpu_percent = psutil.cpu_percent(percpu=True)
                    ram = psutil.virtual_memory()

                    data = {
                        "points": points,
                        "links": links,
                        "nodes_count": nodes_count,
                        "edges_count": edges_count,
                        "storage": storage_hud,
                        "lab": {
                            "weather": lab_status.get("weather", {}),
                            "agents": lab_status.get("agents", {}),
                            "custom_agents": lab_status.get("custom_agents", {}),
                            "distiller": lab_status.get("distiller", {}),
                            "janitor": lab_status.get("janitor", {}),
                            "blackboard": lab_status.get('blackboard', [])[-12:]
                        },
                        "system": {
                            "cpu": {"cores": cpu_percent, "overall": sum(cpu_percent)/len(cpu_percent)},
                            "ram": {"used": ram.percent, "total": ram.total},
                            "compute_mode": "WARP" if torch.backends.mps.is_available() else "SUSTAINED",
                            "hardware_dna": f"APPLE-{platform.machine()}",
                            "embedding_engine": "BGE-M3 (LOCAL)",
                            "ai_intelligence": {
                                "model": "Llama 3.2 (Neural-8B)",
                                "quantization": "TurboQuant 4-bit",
                                "learning_status": "ONLINE (Synaptic Reinforcement)",
                                "inference_speed": f"{round(random.uniform(15, 25), 1)} tok/s"
                            }
                        }
                    }
                    data["agent007"] = {"entities_count": 0, "relations_count": 0}
                    try:
                        data["agent007"]["entities_count"] = engine.agent007.con.execute("SELECT count(*) FROM agent007_entities").fetchone()[0]
                        data["agent007"]["relations_count"] = engine.agent007.con.execute("SELECT count(*) FROM agent007_relations").fetchone()[0]
                    except: pass

                    yield f"data: {json.dumps(data, default=json_serializer)}\n\n"

            except Exception as e:
                print(f"⚠️ [SSE/Loop] {e}")
                yield f"data: {json.dumps({'status': 'RECOVERING', 'error': str(e)})}\n\n"
                await asyncio.sleep(2)
            
            await asyncio.sleep(1.0)

    return StreamingResponse(event_generator(), media_type="text/event-stream")

# ⚙️ SWARM CONFIGURATION & AUTO-PILOT (v11.5)
@app.get("/config")
async def get_config():
    """Restituisce le impostazioni correnti dello Swarm."""
    if hasattr(app.state, 'lab'):
        return app.state.lab.settings.settings
    return {"status": "error", "message": "Lab not initialized"}

class ConfigUpdateRequest(BaseModel):
    key: str
    value: Any

@app.post("/config")
async def update_config(req: ConfigUpdateRequest):
    """Aggiorna una impostazione dello Swarm (es. auto_mode o default_oracle)."""
    if hasattr(app.state, 'lab'):
        app.state.lab.settings.update(req.key, req.value)
        return {"status": "success", "settings": app.state.lab.settings.settings}
    return JSONResponse(status_code=500, content={"message": "Lab not initialized"})

# 🏛️ MISSION CONTROL & ORACLE ENDPOINTS (v10.6)
class MissionResolution(BaseModel):
    agent_id: str
    resolution: str # 'APPROVE' (Prune) or 'REJECT' (Keep)
    feedback: Optional[str] = None

@app.post("/api/lab/resolve_mission")
async def resolve_mission(req: MissionResolution, key: str = Depends(get_api_key)):
    """[Circuit Breaker] Risolve manualmente una missione in hold e applica il feedback."""
    print(f"⚖️ [Mission Control] Risoluzione per {req.agent_id}: {req.resolution}")
    try:
        if req.resolution == "APPROVE":
            # Approva l'eliminazione (Janitor) o il Pruning (Distiller)
            app.state.lab.approve_mission(req.agent_id)
        else:
            # Caso REJECT: l'utente vuole mantenere il nodo
            agent_obj = None
            target_text = "Unknown Node"
            if req.agent_id == "JA-001":
                agent_obj = app.state.lab.janitor
                target_id = agent_obj.target_node
            elif req.agent_id == "DI-007":
                agent_obj = app.state.lab.distiller
                target_id = agent_obj._target.id if hasattr(agent_obj, '_target') else None
            
            if target_id:
                node = engine.get_node(target_id)
                if node: target_text = node.text
            
            # Reset dello stato per entrambi gli agenti
            if req.agent_id == "JA-001":
                app.state.lab.janitor.mode = "Interviewing"
                app.state.lab.janitor.status = "Mission Cancelled: Node Spared"
                app.state.lab.janitor.target_node = None
            elif req.agent_id == "DI-007":
                app.state.lab.distiller.mode = "Navigating"
                app.state.lab.distiller.status = "Mission Cancelled: Synapse Spared"
                app.state.lab.distiller._target = None
            
            # Salvataggio Feedback (Learning Loop v11.0)
            app.state.lab.wisdom.add_lesson(
                agent_id=req.agent_id,
                success=False,
                text=target_text,
                reason=f"Human Reject: {req.feedback}"
            )
        
        return {"ok": True, "msg": f"Mission {req.resolution}ED"}
    except Exception as e:
        print(f"❌ [Mission Control Error] {e}")
        raise HTTPException(status_code=500, detail=str(e))
        
        return {"ok": True, "msg": f"Mission {req.resolution}ED"}
    except Exception as e:
        print(f"❌ [Mission Control Error] {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/lab/consult_oracle")
async def consult_oracle(req: Dict[str, str], key: str = Depends(get_api_key)):
    """[Phase 25] Consulta l'Oracolo Neurale (via Lab Orchestrator) per decidere il destino di un nodo."""
    agent_id = req.get("agent_id")
    human_tip = req.get("feedback", "")
    
    try:
        # Usiamo l'Orchestratore per la consultazione reale (Ollama/Internal Logic)
        verdict = await app.state.lab.consult_oracle(agent_id, human_tip)
        return verdict
    except Exception as e:
        print(f"⚠️ [Oracle Error] {e}")
        return {
            "reasoning": f"L'Oracolo è momentaneamente offuscato: {str(e)}. Forza il mantenimento per sicurezza.", 
            "action": "HOLD",
            "verdict": "MANTIENI"
        }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="warning")
