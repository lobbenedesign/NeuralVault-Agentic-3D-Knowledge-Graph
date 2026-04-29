import os
import sys

# 🛡️ [Mac/Sovereign] Aggressive Environment Stabilization
# Must be set BEFORE any other imports to silence OBJC/FFmpeg conflicts
os.environ["OBJC_DISABLE_INITIALIZE_FORK_SAFETY"] = "YES"
os.environ["OBJC_PRINT_REPLACED_CLASSES"] = "NO"
os.environ["AV_LOG_LEVEL"] = "quiet"
os.environ["OPENCV_LOG_LEVEL"] = "OFF"
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["PYAV_SKIP_DLOPEN_CHECK"] = "1"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

import logging
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

import sys

# v2.6.0: Environment Stabilization & Warning Suppression
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false" # Evita warning di deadlock in f-strings
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE" # Per librerie Intel/OpenMP

# Silenzia i warning di caricamento di sentence-transformers / transformers
logging.getLogger("transformers.modeling_utils").setLevel(logging.ERROR)

# v21.2: Suppress OBJC Duplicate warnings for cleaner log
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["OBJC_DISABLE_INITIALIZE_FORK_SAFETY"] = "YES"

import uvicorn
import httpx
import os

# 🛡️ [Mac Fix] Suppress FFmpeg duplicate implementation warnings
os.environ["OPENCV_VIDEOIO_PRIORITY_BACKEND"] = "0"
os.environ["KINETIC_FFMPEG_FIX"] = "1"

import torch
from fastapi import FastAPI, UploadFile, File, Request, Depends, HTTPException, BackgroundTasks, Header, Form
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx

# Centralized Agentic Fabric Imports
from neural_lab import SynapticSignal, AgentRole, SignalType, NeuralLabOrchestrator

class QueryRequest(BaseModel):
    query: str
    modality: str = "text"
    top_k: int = 5
    consensus: bool = False
    # [v3.6.0] Advanced Filtering
    namespace: Optional[str] = None
    file_type: Optional[str] = None
    year: Optional[int] = None
    month: Optional[int] = None

# CORE ENGINE IMPORT
from __init__ import NeuralVaultEngine
from network.gossip import SyncSignal
from retrieval.web_forager import SovereignWebForager
from retrieval.multimodal import MultimodalSynapseProcessor

app = FastAPI(title="Aura Nexus: NeuralVault API")
app.state.boot_time = datetime.now()

def json_serializer(obj):
    if hasattr(obj, 'tolist'): return obj.tolist()
    if isinstance(obj, (datetime, date)): return obj.timestamp()
    try: return float(obj)
    except: return str(obj)

# --- 🛡️ SOVEREIGN SHUTDOWN PROTOCOL (v4.0) ---
_shutdown_lock = threading.Lock()
_is_shutting_down = False

@app.on_event("shutdown")
async def shutdown_event():
    """Arresto controllato via lifecycle FastAPI."""
    global _is_shutting_down
    with _shutdown_lock:
        if _is_shutting_down: return
        _is_shutting_down = True
        
    print("\n🛑 [Lifecycle] Eutanasia Digitale in corso...")
    if hasattr(app.state, 'lab') and app.state.lab:
        app.state.lab.stop()
    if engine:
        engine.close()
    print("✅ [Lifecycle] Core spento.")

def signal_handler(sig, frame):
    """Handler di emergenza per segnali OS (SIGINT/SIGTERM)."""
    global _is_shutting_down
    # Se il lifecycle ha già iniziato lo shutdown, usciamo e basta
    with _shutdown_lock:
        if _is_shutting_down: 
            # Diamo tempo al lifecycle di finire o forziamo l'uscita se sigint ripetuto
            os._exit(0)
        _is_shutting_down = True

    print(f"\n⚠️ [Signal {sig}] Interruzione forzata ricevuta.")
    try:
        if hasattr(app.state, 'lab') and app.state.lab:
            app.state.lab.stop()
        if engine:
            engine.close()
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

def get_custom_models_path():
    storage_dir = Path(os.getenv("NEURALVAULT_DATA_DIR", "./vault_data"))
    if not storage_dir.exists(): storage_dir.mkdir(parents=True, exist_ok=True)
    return storage_dir / "custom_models.json"

def load_custom_models():
    path = get_custom_models_path()
    if path.exists():
        try:
            with open(path, "r") as f: return json.load(f)
        except: return {}
    return {}

def save_custom_models(models):
    path = get_custom_models_path()
    with open(path, "w") as f: json.dump(models, f, indent=2)

# v21.0: Idle Tracking & Background Consolidation
app.state.last_activity = time.time()
app.state.auto_evolve_active = False
app.state.is_dreaming = False # Flag for background evolution

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

# settings tracking
@app.get("/api/swarm/config")
async def get_swarm_config_alias():
    """Alias di compatibilità per il vecchio endpoint config."""
    return await get_system_settings()

@app.get("/api/system/settings")
async def get_system_settings():
    storage_dir = Path(os.getenv("NEURALVAULT_DATA_DIR", "./vault_data"))
    settings_file = storage_dir / "swarm_settings.json"
    if settings_file.exists():
        try:
            with open(settings_file, "r") as f:
                return json.load(f)
        except: pass
    return {"theme": "dark"}

@app.post("/api/system/priority")
async def set_system_priority(request: Request):
    """Sospende o riprende l'attività degli agenti per dare priorità all'utente."""
    try:
        data = await request.json()
        priority = data.get("active", False)
        app.state.lab.pause_agents = priority
        status = "PRIORITY_FOCUS_ACTIVE" if priority else "SWARM_RESUMED"
        print(f"⚡ [System] Shifted Priority: {status}")
        return {"status": status, "paused": app.state.lab.pause_agents}
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/system/recommendations")
async def get_recommendations():
    """Ritorna i consigli basati su hardware e modelli installati (Gap #22)."""
    from utils.recommendations import SovereignRecommendationEngine
    import httpx
    
    # Ottieni modelli installati (via Ollama)
    base_url = app.state.lab.settings.get("ollama_url") if hasattr(app.state, 'lab') else "http://127.0.0.1:11434"
    installed_models = []
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{base_url}/api/tags")
            if resp.status_code == 200:
                installed_models = [m["name"] for m in resp.json().get("models", [])]
    except: pass

    engine_rec = SovereignRecommendationEngine(installed_models)
    return {
        "hw_info": engine_rec.hw_info,
        "recommendations": engine_rec.get_all_recommendations()
    }

@app.post("/api/system/settings")
async def update_system_settings(req: Dict[str, Any]):
    # We use a simple auth check without Depends if needed, but here we'll just check the vault key
    if req.get("api_key") != VAULT_KEY:
         raise HTTPException(status_code=403, detail="Invalid Vault Key")
    
    storage_dir = Path(os.getenv("NEURALVAULT_DATA_DIR", "./vault_data"))
    if not storage_dir.exists(): storage_dir.mkdir(parents=True, exist_ok=True)
    
    settings_file = storage_dir / "swarm_settings.json"
    current = {}
    if settings_file.exists():
        try:
            with open(settings_file, "r") as f:
                current = json.load(f)
        except: pass
    
    # Remove api_key from stored settings
    data = {k:v for k,v in req.items() if k != "api_key"}
    current.update(data)
    
    with open(settings_file, "w") as f:
        json.dump(current, f)
    
    # Sync with live state
    if hasattr(app.state, 'lab'):
        app.state.lab.settings.update(data)
        if "evolution_active" in req:
            app.state.lab.evolution_active = req["evolution_active"]
        if "auto_evolve_active" in req:
             app.state.auto_evolve_active = req["auto_evolve_active"]
             
        # 🔗 [v4.0] Live Sync Git Bridge
        if "github_token" in data or "github_repo" in data:
            tk = current.get("github_token")
            rp = current.get("github_repo")
            if tk and rp:
                app.state.lab.git_bridge.setup_github(tk, rp)
                
        print(f"🧬 [Sovereign State] Live Sync Complete. Evolution Mode: {getattr(app.state.lab, 'evolution_active', False)}")

    return {"status": "success", "settings": current}

@app.post("/api/github/test")
async def test_github_connection(req: Dict[str, Any]):
    """Verifica la validità del token e l'accesso al repository."""
    if req.get("api_key") != VAULT_KEY:
         raise HTTPException(status_code=403, detail="Invalid Vault Key")
    
    token = req.get("token")
    repo = req.get("repo")
    if not token or not repo:
        return {"success": False, "error": "Token o Repository mancanti."}
    
    try:
        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
            r = await client.get(f"https://api.github.com/repos/{repo}", headers=headers)
            if r.status_code == 200:
                return {"success": True, "data": r.json().get("full_name")}
            else:
                return {"success": False, "error": f"GitHub Error: {r.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

async def neural_dreaming_loop():
    """Consolida la conoscenza in background quando l'utente è inattivo."""
    await asyncio.sleep(15) 
    batch_size = 200 
    offset = 0
    
    while not _is_shutting_down:
        try:
            now = time.time()
            idle_time = now - app.state.last_activity
            
            # Idle Threshold: 120 secondi
            if app.state.auto_evolve_active and idle_time > 120 and not app.state.is_dreaming:
                app.state.is_dreaming = True
                print(f"🌙 [Neural Dreaming] Inizio batch consolidamento (Offset: {offset})...")
                
                # Signal activity to blackboard (USING GLOBAL IMPORTS)
                try:
                    sig = SynapticSignal("SYSTEM", AgentRole.ARCHITECT, "🌙 Connessione neurale di sottofondo attiva...", SignalType.SYSTEM_NOTIFICATION)
                    app.state.lab.blackboard.post(sig)
                except Exception as e: 
                    print(f"⚠️ [Dreaming Signal Fail] {e}")
                
                # Eseguiamo il batch
                await _run_hybrid_evolution(limit=batch_size, offset=offset)
                
                offset += batch_size
                
                # Check for FULL CYCLE COMPLETION (Autonomous Expansion Phase 1)
                total_nodes = len(engine._nodes)
                if offset >= total_nodes:
                    offset = 0
                    print("🌌 [Neural Dreaming] Ciclo consolidamento completo. Analisi vuoti per FS-77...")
                    
                    # Identifichiamo un cluster "poco denso"
                    try:
                        sparse_topic = "Agentic Workflows" # Fallback
                        # Recupriamo una lista di sorgenti meno connesse
                        counts = {}
                        for n in engine._nodes.values():
                            src = n.metadata.get("source", "unknown")
                            counts[src] = counts.get(src, 0) + 1
                        
                        if counts:
                            sparse_topic = min(counts, key=counts.get)
                        
                        # Lanciamo l'X-Wing!
                        asyncio.create_task(app.state.lab.dispatch_skywalker_mission(sparse_topic))
                    except Exception as e:
                        print(f"⚠️ [Expansion Fail] {e}")

                app.state.is_dreaming = False
                print(f"✨ [Neural Dreaming] Consolidation Batch Complete.")
            
            await asyncio.sleep(60)
            
        except Exception as e:
            print(f"⚠️ [Dreaming Loop Error] {e}")
            app.state.is_dreaming = False
            await asyncio.sleep(30)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    # Update last activity for all API calls (excluding health checks or static)
    if request.url.path.startswith("/api/"):
        app.state.last_activity = time.time()
    
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
    
    # 1. Load Swarm Settings first
    from neural_lab import SwarmSettingsManager
    settings_manager = SwarmSettingsManager(storage_dir)
    engine.settings = settings_manager # Shared access
    base_url = settings_manager.get("ollama_url")
    
    # 2. Initialize Multimodal Engine with dynamic URL & Routing Settings
    app.state.mm_processor = MultimodalSynapseProcessor(ollama_url=base_url, settings=settings_manager)
    engine.mm_processor = app.state.mm_processor # Attach for health
    # 3. Initialize Forager & Neural Lab (Orchestrator)
    engine.forager = SovereignWebForager(max_depth=1, max_pages=10)
    app.state.lab = NeuralLabOrchestrator(engine)

    # 4. Agent007 Schema Gardening
    try:
        engine.agent007.ensure_schema()
    except: pass

    # 5. Mesh Discovery & Crypto Handshake (v4.0.0)
    def on_peer_found(node_id, address, public_key):
        if engine and engine.gossip:
            engine.gossip.add_peer(node_id, address, public_key)

    if engine and engine.crypto:
        from network.discovery import SovereignDiscovery
        pub_key = engine.crypto.get_public_key_base64()
        # In un sistema reale, la porta dovrebbe essere rilevata dinamicamente
        engine.discovery = SovereignDiscovery(
            node_id=engine.node_id,
            port=8001, 
            public_key=pub_key,
            on_peer_found_callback=on_peer_found
        )
        import threading
        threading.Thread(target=engine.discovery.start, daemon=True).start()
        print(f"📡 [Mesh] Discovery Online. PubKey: {pub_key[:10]}...")
    try:
        engine.agent007.con.execute("ALTER TABLE agent007_entities ADD COLUMN attributes JSON")
        engine.agent007.con.execute("ALTER TABLE agent007_entities ADD COLUMN relevance FLOAT")
    except: pass
    
    # 5. Pre-load UI settings
    settings = await get_system_settings()
    app.state.auto_evolve_active = settings.get("auto_evolve_active", False)
    
    # Start background loops
    asyncio.create_task(neural_dreaming_loop())
    asyncio.create_task(shard_maintenance_loop())

async def shard_maintenance_loop():
    """v3.0: Automated Shard Maintenance (Cloning & Backup). Runs every 30 minutes."""
    iteration = 0
    while not _is_shutting_down:
        try:
            if engine and hasattr(engine, 'shards'):
                # 1. Incremental Backup (Every 30m)
                print("🛡️ [Maintenance] Running automated shard backup...")
                storage_dir_path = Path(os.getenv("NEURALVAULT_DATA_DIR", "./vault_data"))
                await asyncio.to_thread(engine.shards.auto_backup, storage_dir_path)
                
                # 2. Full Shard Cloning (Every 12 hours = 24 iterations of 30m)
                if iteration % 24 == 0:
                    shards = getattr(engine.shards, 'active_shards', {})
                    if shards:
                        print(f"🛡️ [Maintenance] Creating clones for {len(shards)} shards...")
                        for shard_id in list(shards.keys()):
                            await asyncio.to_thread(engine.shards.clone_shard, shard_id)
                    else:
                        print("🛡️ [Maintenance] No active shards to clone.")
                
                # Signal on blackboard
                if hasattr(app.state, 'lab'):
                    msg = "📦 [ShardGuard] Backup automatico completato."
                    if iteration % 24 == 0: msg = "🛡️ [ShardGuard] Clone e Backup completati."
                    sig = SynapticSignal("SYSTEM", AgentRole.GUARDIAN, msg, SignalType.SYSTEM_NOTIFICATION)
                    app.state.lab.blackboard.post(sig)
        except Exception as e:
            print(f"❌ [Maintenance Error] {e}")
            
        iteration += 1
        await asyncio.sleep(1800) # 30 minutes


# Static Files (Dashboard)

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

        # 🧠 [Ebbinghaus Reinforcement] v4.8
        # Reset della curva dell'oblio ad ogni consultazione profonda
        try:
            n_meta["last_access"] = time.time()
            n_meta["access_count"] = n_meta.get("access_count", 1) + 1
            # Se il nodo è un oggetto VaultNode reale, salviamo la modifica
            if hasattr(node, 'metadata'):
                # Innesca il salvataggio asincrono nel tier persistente se necessario
                pass 
        except: pass

        # Recupera connessioni reali
        connessioni = []
        try:
            # Relazioni dirette nel nodo (GNN Sync)
            edges = getattr(node, 'edges', [])
            for e in edges:
                connessioni.append({
                    "node": str(e.target_id), 
                    "relation": str(e.relation), 
                    "reason": getattr(e, 'reason', None)
                })

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

@app.get("/api/node/verify/{node_id}")
async def verify_node_coherence(node_id: str):
    """Verifica la coerenza logica di un nodo rispetto alla Nebula (Neural Audit)."""
    node = engine.get_node(node_id)
    if not node: return {"error": "Node not found"}
    
    # Recuperiamo il contesto circostante (vicini semantici) per la verifica
    neighbors = engine.query(node.text, k=3)
    context = "\n".join([f"Vicino: {n.node.text}" for n in neighbors if n.node.id != node_id])
    
    prompt = f"""ANALISI COERENZA NEURALE (SOVEREIGN AUDIT)
Nodo da verificare: {node.text}

Contesto circostante:
{context}

Analizza se il nodo è coerente con il contesto o se presenta allucinazioni, errori tecnici o conflitti logici. 
Rispondi in modo tecnico e conciso (max 3 frasi). Inizia con [COERENTE] o [INCOERENTE]."""

    try:
        # 🧠 [v17.5] Dynamic Sovereign Audit Model Selection
        base_url = app.state.lab.settings.get("ollama_url") if hasattr(app.state, 'lab') else "http://127.0.0.1:11434"
        audit_model = app.state.lab.settings.get("evolution_model", "llama3.2") if hasattr(app.state, 'lab') else "llama3.2"
        
        async with httpx.AsyncClient(timeout=45.0) as client:
            r = await client.post(f"{base_url}/api/generate", json={
                "model": audit_model, "prompt": prompt, "stream": False
            })
            res = r.json()
            if "error" in res:
                return {"audit": f"Errore dal Modello ({audit_model}): {res['error']}"}
            return {"audit": res.get("response", "Audit fallito senza risposta.")}
    except Exception as e:
        return {"audit": f"Errore durante l'audit: {str(e)}"}

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

# --- MULTIMODAL BRIDGE ENDPOINTS (v4.0) ---

@app.post("/api/multimodal/upload")
async def upload_multimodal(file: UploadFile = File(...), api_key: str = Header(None)):
    """Ingestione Drag-and-Drop: Caricamento e processamento di Immagini/Audio/Video."""
    if api_key != VAULT_KEY:
        raise HTTPException(status_code=403, detail="Invalid Vault Key")
    
    if engine is None:
        raise HTTPException(status_code=503, detail="Neural Engine Offline")

    try:
        # 1. Salvataggio temporaneo
        temp_dir = engine.data_dir / "temp_uploads"
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = temp_dir / f"{uuid.uuid4().hex}_{file.filename}"
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # 2. Ingestione nel Vault (Estrae trascrizioni, descrizioni e vettori)
        nodes = await engine.upsert_multimodal(str(file_path))
        
        # 3. Pulizia (Opcionale, potremmo voler tenere i file originali)
        # os.remove(file_path) 
        
        return {
            "status": "success",
            "ingested_nodes": len(nodes),
            "source": file.filename,
            "message": f"Ingeriti {len(nodes)} segmenti multimodali."
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# --- SHARDING & CLONING AUTOMATION (v1.0) ---

@app.post("/api/sharding/clone")
async def manual_shard_clone(api_key: str = Depends(get_api_key)):
    """Clonazione manuale dello shard attivo (Snapshot atomico)."""
    if not engine or not hasattr(engine, 'shards'):
        raise HTTPException(status_code=503, detail="Sharding System Offline")
    
    try:
        shard_id = engine.shards.clone_shard()
        return {"status": "success", "shard_id": shard_id, "message": "Clonazione shard completata."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/sharding/backup")
async def manual_shard_backup(api_key: str = Depends(get_api_key)):
    """Trigger manuale per il backup fisico dei segmenti (.ael, .db)."""
    if not engine or not hasattr(engine, 'shards'):
        raise HTTPException(status_code=503, detail="Sharding System Offline")
    
    try:
        engine.shards.auto_backup()
        return {"status": "success", "message": "Backup fisico completato."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        level = data.get("level", "INFO")
        print(f"🖥️ [Interactive HUD] {msg}")
    except: pass
    return {"status": "ok"}

@app.post("/api/files/upload")
@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...), namespace: Optional[str] = Form("default"), api_key: str = Depends(get_api_key)):
    print(f"📥 [Ingestion] Richiesta ricevuta: {file.filename} ({file.content_type})")
    content = await file.read()
    text = content.decode('utf-8', errors='ignore')
    node_id = str(uuid.uuid4())
    if engine is None: return {"error": "Engine not initialized"}
    
    # [v3.6.0] Scalar Metadata Extraction
    ext = Path(file.filename).suffix.lower().replace('.', '') or 'text'
    node = engine.upsert_text(text, metadata={"source": file.filename, "namespace": namespace, "file_type": ext}, node_id=node_id)
    
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
    model_name = (data.get("name") or data.get("model") or "").strip()
    
    # 🧬 HARDWARE DNA CHECK
    os_name = platform.system()
    arch = platform.machine()
    print(f"🧠 [Auto-Installer] Platform: {os_name} {arch} | Requested Model: '{model_name}'")

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
                    async with httpx.AsyncClient(timeout=10.0) as client:
                        base_url = app.state.lab.settings.get("ollama_url") if hasattr(app.state, 'lab') else "http://127.0.0.1:11434"
                        r = await client.get(f"{base_url}/api/tags")
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
                base_url = app.state.lab.settings.get("ollama_url") if hasattr(app.state, 'lab') else "http://127.0.0.1:11434"
                async with client.stream("POST", f"{base_url}/api/pull", json={"name": model_name}) as resp:
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
            async with httpx.AsyncClient(timeout=10.0) as client:
                base_url = app.state.lab.settings.get("ollama_url") if hasattr(app.state, 'lab') else "http://127.0.0.1:11434"
                v_resp = await client.get(f"{base_url}/api/tags")
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
    if hasattr(app.state, 'lab') and hasattr(app.state.lab, 'benchmarks'):
        stats = app.state.lab.benchmarks.get_stats()
        if not stats: 
            return {"benchmarks": [], "radar": [50, 50, 50, 50, 50]}
            
        top = stats[0]
        # Calibrazione Sovrana (v3.1): Benchmarks reali normalizzati
        # SPEED: Target 40 TPS | ACCURACY: Stability + Penality Latency | DENSITY: RAM Impact (16GB Scale)
        radar_data = [
            min(100, (top.get('tps', 0) / 40.0) * 100),         # SPEED
            min(100, top.get('stability', 50) * 0.9 + (2000 / (top.get('latency', 2000) + 1)) * 10), # ACCURACY
            top.get('stability', 50),                           # STABILITY
            min(100, (top.get('ram', 0) / 16384) * 100),        # DENSITY (MB)
            min(100, (top.get('stability', 50) * 0.7 + (top.get('tps', 0) / 40.0) * 30)) # REASONING
        ]
        return {
            "benchmarks": stats, 
            "radar": radar_data,
            "history": app.state.lab.benchmarks.get_full_history()[:50] # Ultime 50 missioni
        }
    return {"benchmarks": [], "radar": [0,0,0,0,0], "history": []}

# --- 🧪 EVOLUTION MODE ENDPOINTS ---
@app.get("/api/lab/evolution/suggestions")
async def get_evolution_suggestions(api_key: str = Depends(get_api_key)):
    """Recupera la cronologia dei suggerimenti evolutivi dello sciame."""
    if hasattr(app.state, 'lab') and hasattr(app.state.lab, 'evolution_advise'):
        return app.state.lab.evolution_advise.history
    return []

@app.post("/api/lab/evolution/feedback")
async def record_evolution_feedback(request: Request, api_key: str = Depends(get_api_key)):
    """Registra il feedback di rinforzo (Implementato/Scartato/Falso Positivo)."""
    data = await request.json()
    sid = data.get("id")
    feedback = data.get("feedback")
    if hasattr(app.state, 'lab') and hasattr(app.state.lab, 'evolution_advise'):
        success = app.state.lab.evolution_advise.record_feedback(sid, feedback)
        return {"status": "recorded" if success else "not_found"}
    return {"status": "error"}

@app.get("/api/lab/wisdom/all")
async def get_wisdom_all(api_key: str = Depends(get_api_key)):
    """Ritorna tutto l'apprendimento accumulato dagli agenti."""
    if not hasattr(app.state, 'lab'): return {"approved": [], "rejected": []}
    return app.state.lab.wisdom.lessons

@app.post("/api/lab/settings")
async def update_lab_settings(req: Dict, api_key: str = Depends(get_api_key)):
    """Aggiorna le impostazioni dello Swarm (es. Supreme Court Judges, Evolution Mode)."""
    if not hasattr(app.state, 'lab'): raise HTTPException(status_code=500, detail="Lab not initialized")
    
    # Aggiorna il manager persistente
    app.state.lab.settings.update(req)
    
    # 🔄 Trigger Mode Logic
    if "auto_mode" in req:
        status = "AUTONOMA" if req["auto_mode"] else "MANUALE"
        sig = SynapticSignal("ORCHESTRATOR", AgentRole.MISSION_ARCHITECT, f"⚠️ SUPERVISIONE CAMBIATA: Ora in modalità {status}.", SignalType.SYSTEM_NOTIFICATION)
        app.state.lab.blackboard.post(sig)

    # Note: frontend might send 'codebase_bridging' OR 'evolution_mode'
    is_evol = req.get("evolution_mode") or req.get("codebase_bridging")
    if is_evol is not None:
        app.state.lab.evolution_active = is_evol
        if is_evol:
            # Activate Bridger with current working directory (v17.6: Access via .bridger.project_root)
            from pathlib import Path
            app.state.lab.bridger_agent.bridger.project_root = Path(os.getcwd())
            app.state.lab.trigger_evolution_scan()
            msg = "🚀 EVOLUTION MODE ATTIVATA: Ibridazione codebase/web iniziata."
        else:
            app.state.lab.bridger_agent.bridger.project_root = None # Research mode
            msg = "🛡️ RESEARCH MODE ATTIVATA: Focus esclusivo sui dati esterni."
        
        app.state.lab.blackboard.post(SynapticSignal("ORCHESTRATOR", AgentRole.MISSION_ARCHITECT, msg, SignalType.SYSTEM_NOTIFICATION))

    return {"status": "success", "settings": app.state.lab.settings.settings}

@app.post("/api/lab/wisdom/record")
async def record_human_wisdom(data: dict, api_key: str = Depends(get_api_key)):
    """Human-in-the-loop: Inserisce manualmente un'istruzione di protezione o rifiuto."""
    if not hasattr(app.state, 'lab'): raise HTTPException(status_code=500)
    
    text = data.get("text")
    success = data.get("approve", False)
    reason = data.get("reason", "Human Override")
    
    app.state.lab.wisdom.add_lesson("HUMAN", success, text, reason)
    return {"status": "recorded", "category": "approved" if success else "rejected"}

# --- NEW: NEURAL MODEL CATALOG (v4.0 Sovereign - Categorized) ---
MODEL_CATALOG = {
    # ── CATEGORIA: [TINY_KINETIC] - Leggerissimi & Ultra-Veloci (0-2GB) ────────────────
    "llama3.2:1b": {
        "name": "Llama 3.2 (1B)", "size": "1.3GB", "category": "TINY_KINETIC", 
        "pros": "Velocità estrema (100+ t/s), zero lag", "cons": "Cognizione base", 
        "caveau": "L'Ombra Silenziosa per il background.", "forza": "Parsing testuale rapido e routing di segnali.",
        "synergy": ["phi3:latest"], "task": "Fast Signal Routing",
        "ram": "2GB RAM", "cpu": "2 Cores", "vram": "1GB",
        "capabilities": ["Text Summarization", "Format Conversion", "Token Filtering", "Intent Detection"]
    },
    "qwen2.5:0.5b": {
        "name": "Qwen 2.5 (0.5B)", "size": "394MB", "category": "TINY_KINETIC", 
        "pros": "Il più piccolo al mondo con logica reale", "cons": "Memoria a breve termine limitata", 
        "caveau": "Il micro-cervello per task atomici.", "forza": "Esecuzione istantanea su CPU datate.",
        "synergy": ["llama3.2:1b"], "task": "Atomic Logic",
        "ram": "1GB RAM", "cpu": "1 Core",
        "capabilities": ["Micro-Classification", "Language ID", "Basic Logic", "Text Cleaning"]
    },
    "ministral:latest": {
        "name": "Ministral 3B", "size": "2.1GB", "category": "TINY_KINETIC", 
        "pros": "Stato dell'arte per modelli sotto i 5B", "cons": "Finestra di contesto 128k richiede molta RAM", 
        "caveau": "Il piccolo Titano di Mistral.", "forza": "Densità di intelligenza estrema e logica impeccabile.",
        "synergy": ["mistral:latest"], "task": "Edge Intelligence",
        "ram": "4GB RAM", "vram": "2GB",
        "capabilities": ["High-Density Logic", "Complex Reasoning", "Large Context (128k)", "Italian Mastery"]
    },
    "deepseek-r1:1.5b": {
        "name": "DeepSeek R1 (1.5B Distill)", "size": "1.1GB", "category": "TINY_KINETIC", 
        "pros": "Ragionamento logico estremo in 1GB", "cons": "Più lento dei modelli non-R1", 
        "caveau": "Il Pensatore in miniatura.", "forza": "Risoluzione di problemi matematici e logici complessi.",
        "synergy": ["qwen2.5:1.5b"], "task": "Logical Reasoning",
        "ram": "2GB RAM", "vram": "1GB",
        "capabilities": ["Complex Reasoning", "Math Solving", "Step-by-step Logic", "Code Analysis"]
    },
    "deepseek-r1:8b": {
        "name": "DeepSeek R1 (8B Distill - Llama)", "size": "4.7GB", "category": "SOVEREIGN_MID_CORE", 
        "pros": "Logica Llama 3.1 potenziata dal ragionamento R1", "cons": "Richiede 8GB RAM libera", 
        "caveau": "Il Saggio della fascia media.", "forza": "Scrittura creativa e debug di codice complesso.",
        "synergy": ["mistral:latest"], "task": "Advanced Reasoning",
        "ram": "8GB RAM", "vram": "4GB",
        "capabilities": ["Expert Coding", "Philosophical Reasoning", "Complex Instructions", "Multilingual Logic"]
    },
    "llama3.2:3b": {
        "name": "Llama 3.2 (3B)", "size": "2.0GB", "category": "TINY_KINETIC", 
        "pros": "Il miglior rapporto intelligenza/peso di Meta", "cons": "Meno profondo della versione 8B", 
        "caveau": "L'Assistente Bilanciato.", "forza": "Comprensione del linguaggio naturale e chat fluida.",
        "synergy": ["phi3.5:latest"], "task": "Balanced Chat",
        "ram": "4GB RAM", "vram": "2GB",
        "capabilities": ["General Chat", "Summarization", "Entity Extraction", "Intent Detection"]
    },
    "smollm2:1.7b": {
        "name": "SmolLM2 (1.7B)", "size": "1.0GB", "category": "TINY_KINETIC", 
        "pros": "Velocità di risposta istantanea", "cons": "Conoscenza enciclopedica limitata", 
        "caveau": "Il Lampo di HuggingFace.", "forza": "Task atomici e classificazione rapida in background.",
        "synergy": ["llama3.2:1b"], "task": "Fast Processing",
        "ram": "2GB RAM", "vram": "1GB",
        "capabilities": ["Text Classification", "Keyword Extraction", "Fast Summaries", "Log Parsing"]
    },
    "qwen2.5:1.5b": {
        "name": "Qwen 2.5 (1.5B)", "size": "1.2GB", "category": "TINY_KINETIC", 
        "pros": "Efficienza estrema con intelligenza da 7B", "cons": "Capacità ridotte per task lunghi", 
        "caveau": "La Scintilla Neurale.", "forza": "Routing intelligente e parsing istantaneo.",
        "synergy": ["llama3.2:1b"], "task": "Micro-Logic",
        "ram": "2GB RAM", "vram": "1GB",
        "capabilities": ["Smart Routing", "Text Cleanup", "Format Validation", "Fast Chat"]
    },
    "gemma4:e2b": {
        "name": "Gemma 4 (Edge 2B)", "size": "1.6GB", "category": "TINY_KINETIC", 
        "pros": "Release Aprile 2026, logica superiore ai vecchi 7B", "cons": "Richiede driver aggiornati per Apple Silicon", 
        "caveau": "Il Futuro Tascabile di Google.", "forza": "Ragionamento complesso in meno di 2GB di spazio.",
        "synergy": ["qwen3.6:moe"], "task": "Ultra-Fast Reasoning",
        "ram": "4GB RAM", "vram": "2GB",
        "capabilities": ["Advanced Logic", "Text Synthesis", "Smart Filtering", "Precise Summarization"]
    },
    "gemma2:2b": {
        "name": "Gemma 2 (2B)", "size": "1.8GB", "category": "TINY_KINETIC", 
        "pros": "Architettura Google v2, ultra-compressa", "cons": "Tende alla brevità", 
        "caveau": "Il Nucleo di Cristallo.", "forza": "Spiegazioni concise e logica matematica solida in formato pocket.",
        "synergy": ["qwen2.5:1.5b"], "task": "Pocket Reasoning",
        "ram": "4GB RAM", "vram": "2GB",
        "capabilities": ["Math Solving", "Concise Summaries", "Code Snippets", "Logical Filters"]
    },
    "qwen2.5-coder:7b": {
        "name": "Qwen 2.5 Coder (7B)", "size": "4.7GB", "category": "SOVEREIGN_MID_CORE", 
        "pros": "Il nuovo standard mondiale per il coding sotto i 10B", "cons": "Meno creativo nel linguaggio naturale", 
        "caveau": "L'Architetto del Codice.", "forza": "Scrittura, debug e refactoring di Python, JS e Rust.",
        "synergy": ["deepseek-v4-flash"], "task": "Full-Stack Development",
        "ram": "8GB RAM", "vram": "6GB",
        "capabilities": ["Expert Coding", "Repo-level Analysis", "Code Completion", "Bug Fixing"]
    },
    
    # ── CATEGORIA: [MULTIMODAL_SENSORY] - Visione, Video & Immagini ───────────────────
    "moondream:latest": {
        "name": "Moondream 2", "size": "1.6GB", "category": "MULTIMODAL_SENSORY", 
        "pros": "Visione eccelsa in formato Nano", "cons": "Solo immagini statiche", 
        "caveau": "L'occhio vigile del Vault.", "forza": "Descrizione visiva chirurgica e Q&A su immagini.",
        "synergy": ["florence2:latest"], "task": "Visual Reasoning",
        "ram": "4GB RAM", "vram": "2GB",
        "capabilities": ["Image Captioning", "Visual Q&A", "Object Identification", "OCR Basic"]
    },
    "phi3:vision": {
        "name": "Phi-3.5 Vision (4.2B)", "size": "2.6GB", "category": "MULTIMODAL_SENSORY", 
        "pros": "Ragionamento logico applicato alla visione", "cons": "Lento nel caricamento immagini", 
        "caveau": "L'Analista Visivo Logico.", "forza": "Interpretazione di grafici, diagrammi e screenshot tecnici.",
        "synergy": ["florence2:latest"], "task": "Technical Vision",
        "ram": "6GB RAM", "vram": "4GB",
        "capabilities": ["Chart Reading", "Diagram Analysis", "Technical OCR", "Visual Reasoning"]
    },
    "florence2:latest": {
        "name": "Microsoft Florence-2", "size": "1.1GB", "category": "MULTIMODAL_SENSORY", 
        "pros": "Leader mondiale nel Grounding visivo", "cons": "Richiede Python Runtime", 
        "caveau": "L'Analista Forense delle Immagini.", "forza": "Individuazione coordinate oggetti e OCR denso.",
        "synergy": ["moondream:latest"], "task": "Visual Forensics",
        "ram": "4GB RAM", "vram": "2GB",
        "capabilities": ["Detailed Captioning", "Object Detection (BBox)", "Dense OCR", "Region Description"]
    },
    "qwen2-vl:2b": {
        "name": "Qwen2-VL (2B)", "size": "2.4GB", "category": "MULTIMODAL_SENSORY", 
        "pros": "Supporto Video Nativo", "cons": "Richiede molta VRAM per video lunghi", 
        "caveau": "Il Cinema neurale.", "forza": "Comprensione di sequenze video e multi-immagine.",
        "synergy": ["imagebind:native"], "task": "Video Synthesis",
        "ram": "8GB RAM", "vram": "4GB",
        "capabilities": ["Video Action Recognition", "Event Sequencing", "Visual Storytelling", "Complex OCR"]
    },
    "llava:7b": {
        "name": "LLaVA v1.6 (7B)", "size": "4.5GB", "category": "MULTIMODAL_SENSORY", 
        "pros": "Standard Industry Vision", "cons": "Lento su hardware medio", 
        "caveau": "Il ponte tra testo e immagine.", "forza": "Ragionamento astratto su scene complesse.",
        "synergy": ["mistral:latest"], "task": "Visual Logic",
        "ram": "12GB RAM", "vram": "8GB",
        "capabilities": ["Deep Visual Analysis", "Chart Reading", "Document Parsing", "Common Sense Vision"]
    },
    "imagebind:native": {
        "name": "Meta ImageBind (Lib)", "size": "2.1GB", "category": "MULTIMODAL_SENSORY", 
        "pros": "Audio/Video/Thermal/Depth in un unico spazio", "cons": "Sola Ingestione (No Chat)", 
        "caveau": "Il Sistema Nervoso Centrale.", "forza": "Creazione di vettori 1024D cross-modali.",
        "synergy": ["whisper:native"], "task": "Neural Ingestion",
        "ram": "8GB RAM", "vram": "4GB (MPS Opt)",
        "capabilities": ["Cross-Modal Search", "Audio-to-Image", "Video-to-Text Alignment", "Thermal Data Sync"]
    },
    "internvl2:latest": {
        "name": "InternVL 2 (VLM)", "size": "12GB", "category": "MULTIMODAL_SENSORY", 
        "pros": "Stato dell'arte nella visione open source", "cons": "Esigente in termini di VRAM", 
        "caveau": "L'Occhio di Falco del Lab.", "forza": "Riconoscimento di pattern visivi complessi e OCR estremo.",
        "synergy": ["qwen2-vl:2b"], "task": "Advanced Vision",
        "ram": "16GB RAM", "vram": "12GB",
        "capabilities": ["High-Res Visual Q&A", "Document Understanding", "Action Recognition", "Multi-Image Reasoning"]
    },
    "openvla:latest": {
        "name": "OpenVLA (Robotica)", "size": "7.5GB", "category": "MULTIMODAL_SENSORY", 
        "pros": "Modello Vision-Language-Action nativo", "cons": "Specializzato in robotica/azione", 
        "caveau": "Il Pilota Robotico.", "forza": "Traduzione di istruzioni visive in coordinate e comandi.",
        "synergy": ["internvl2:latest"], "task": "Visual Grounding",
        "ram": "12GB RAM", "vram": "8GB",
        "capabilities": ["Spatial Reasoning", "Instruction Following", "Object Grounding", "Robotic Control Simulation"]
    },
    "openvl:latest": {
        "name": "OpenVL (General)", "size": "4.2GB", "category": "MULTIMODAL_SENSORY", 
        "pros": "Efficienza bilanciata tra analisi e velocità", "cons": "Meno dettagliato di InternVL", 
        "caveau": "Il Sensore Ambientale.", "forza": "Analisi rapida di scene e tagging automatico.",
        "synergy": ["moondream:latest"], "task": "Scene Intelligence",
        "ram": "8GB RAM", "vram": "4GB",
        "capabilities": ["Fast Captioning", "Tagging", "Environmental Analysis", "Basic OCR"]
    },

    # ── CATEGORIA: [SOVEREIGN_MID_CORE] - Prestazioni PC Fascia Media (4-12GB) ─────────
    "mistral:latest": {
        "name": "Mistral 7B v0.3", "size": "4.1GB", "category": "SOVEREIGN_MID_CORE", 
        "pros": "Affidabilità granitica, finestra 32k", "cons": "No native CoT", 
        "caveau": "Il Motore primario del Vault.", "forza": "Sintesi di documenti e stabilità logica.",
        "synergy": ["deepseek-r1:7b"], "task": "General Knowledge",
        "ram": "8GB RAM", "vram": "6GB",
        "capabilities": ["Document Synthesis", "Code Writing", "Email Drafting", "Knowledge Retrieval"]
    },
    "llama3.1:8b": {
        "name": "Llama 3.1 (8B)", "size": "4.7GB", "category": "SOVEREIGN_MID_CORE", 
        "pros": "Ecosistema vastissimo, ottimo italiano", "cons": "Censura occasionale", 
        "caveau": "Il Console del Dialogo.", "forza": "Capacità conversazionale e sfumature linguistiche.",
        "synergy": ["gemma2:9b"], "task": "Advanced Chat",
        "ram": "10GB RAM", "vram": "8GB",
        "capabilities": ["Nuanced Conversation", "Creative Writing", "Roleplay", "Tool Calling"]
    },
    "deepseek-r1:7b": {
        "name": "DeepSeek R1 (7B Distill)", "size": "4.7GB", "category": "SOVEREIGN_MID_CORE", 
        "pros": "Ragionamento matematico d'élite", "cons": "Uscite in cinese rari", 
        "caveau": "Il Matematico del Lab.", "forza": "Chain of Thought (CoT) per risolvere enigmi logici.",
        "synergy": ["mistral:latest"], "task": "Problem Solving",
        "ram": "8GB RAM", "vram": "6GB",
        "capabilities": ["Mathematical Reasoning", "Logic Puzzles", "Code Debugging", "Step-by-step Planning"]
    },
    "phi3.5:latest": {
        "name": "Phi-3.5 Mini (3.8B)", "size": "2.2GB", "category": "SOVEREIGN_MID_CORE", 
        "pros": "Incredibile densità di intelligenza", "cons": "Finestra contesto corta", 
        "caveau": "Il piccolo genio di Microsoft.", "forza": "Logica da 7B in meno di 3GB di RAM.",
        "synergy": ["qwen2.5:1.5b"], "task": "Logical Verification",
        "ram": "4GB RAM", "vram": "2GB",
        "capabilities": ["Fact Checking", "Logic Validation", "Brief Summaries", "Data Extraction"]
    },
    "qwen3.6:35b": {
        "name": "Qwen 3.6 (35B-A3B MoE)", "size": "12GB (Quant)", "category": "SOVEREIGN_MID_CORE", 
        "pros": "Intelligenza da 35B con velocità di un 3B", "cons": "Uso VRAM variabile", 
        "caveau": "L'Illusionista di Alibaba.", "forza": "Prestazioni d'élite con consumo energetico minimo.",
        "synergy": ["gemma4:e2b"], "task": "Hybrid Intelligence",
        "ram": "16GB RAM", "vram": "8GB",
        "capabilities": ["MoE Efficiency", "High-Fidelity Code", "Complex Planning", "Scientific Logic"]
    },

    # ── CATEGORIA: [ELITE_HEAVY_WEIGHT] - Massima Potenza & Conoscenza (15GB+) ──────────
    "gemma2:27b": {
        "name": "Gemma 2 (27B)", "size": "16GB", "category": "ELITE_HEAVY_WEIGHT", 
        "pros": "Prestazioni da 70B in taglia ridotta", "cons": "Molto pesante su 16GB Mac", 
        "caveau": "L'Oracolo della Verità.", "forza": "Comprensione enciclopedica e zero allucinazioni.",
        "synergy": ["deepseek-r1:14b"], "task": "Scientific Research",
        "ram": "32GB RAM", "vram": "16GB",
        "capabilities": ["Scientific Analysis", "Philosophical Discourse", "Cross-Domain Synthesis", "Truth Verification"]
    },
    "hermes3:latest": {
        "name": "Hermes 3 (8B - Llama 3.1)", "size": "4.7GB", "category": "SOVEREIGN_MID_CORE", 
        "pros": "Incredibile naturalezza e aderenza alle istruzioni", "cons": "Meno focalizzato sulla sicurezza (uncensored)", 
        "caveau": "Il Console Sovrano.", "forza": "Dialoghi complessi, roleplay tecnico e creatività senza vincoli.",
        "synergy": ["llama3.1:8b"], "task": "Unconstrained Logic",
        "ram": "10GB RAM", "vram": "8GB",
        "capabilities": ["Instruction Following", "Creative Writing", "Technical Roleplay", "System Prompt Mastery"]
    },
    "deepseek-r1:14b": {
        "name": "DeepSeek R1 (14B)", "size": "9.0GB", "category": "ELITE_HEAVY_WEIGHT", 
        "pros": "Il miglior compromesso tra 7B e 32B", "cons": "Lentezza su CPU", 
        "caveau": "L'Ingegnere Senior del Vault.", "forza": "Programmazione complessa e logica formale.",
        "synergy": ["phi4:latest"], "task": "Engineering Task",
        "ram": "16GB RAM", "vram": "10GB",
        "capabilities": ["Full-Stack Coding", "Algorithmic Design", "Complex Planning", "Expert Critique"]
    },
    "qwen2.5-coder:14b": {
        "name": "Qwen 2.5 Coder (14B)", "size": "9.1GB", "category": "ELITE_HEAVY_WEIGHT", 
        "pros": "Potenza di ragionamento codice superiore a GPT-4o-mini", "cons": "Richiede 16GB RAM per fluidità", 
        "caveau": "Il Maestro Artigiano.", "forza": "Sistemi complessi e architetture software multi-file.",
        "synergy": ["deepseek-v4-flash"], "task": "Software Architecture",
        "ram": "16GB RAM", "vram": "10GB",
        "capabilities": ["Complex Software Design", "Unit Test Generation", "Security Auditing", "CI/CD Logic"]
    },
    "deepseek-v4-flash": {
        "name": "DeepSeek V4 Flash (284B MoE)", "size": "14GB (Quantized)", "category": "ELITE_HEAVY_WEIGHT", 
        "pros": "Efficienza MoE estrema, 1M Context Window", "cons": "Richiede download massiccio iniziale", 
        "caveau": "L'Oracolo della Conoscenza Globale.", "forza": "Ragionamento ad altissimo contesto e sintesi di interi repository.",
        "synergy": ["qwen2.5-coder:14b"], "task": "Massive Context Analysis",
        "ram": "24GB+ RAM", "vram": "16GB (Quant)",
        "capabilities": ["1 Million Token Context", "High-Throughput Reasoning", "Deep Repository Synthesis", "Cross-Domain Logic"]
    },
    "gemma4:26b": {
        "name": "Gemma 4 MoE (Unsloth Elite)", "size": "12.5GB (GGUF)", "category": "ELITE_HEAVY_WEIGHT", 
        "pros": "26B Total / 4B Active. Velocità da 4B con logica da 26B", "cons": "Ottimizzato principalmente per ragionamento/code", 
        "caveau": "Il Motore Efficace di Unsloth.", "forza": "Context window da 256k e ragionamento step-by-step nativo.",
        "synergy": ["qwen3.6:35b"], "task": "High-Efficiency Reasoning",
        "ram": "16GB RAM", "vram": "12GB (MPS Opt)",
        "capabilities": ["256K Context Window", "Mixture-of-Experts (MoE)", "Tool-Calling Native", "Chain-of-Thought reasoning"]
    },
    "nemotron:latest": {
        "name": "NVIDIA Nemotron 70B", "size": "39GB", "category": "ELITE_HEAVY_WEIGHT", 
        "pros": "Incredibile naturalezza, dati NVIDIA", "cons": "Richiede Mac Studio/Ultra", 
        "caveau": "Il Titano del Dialogo.", "forza": "Dialoghi umani al 100% e analisi di mercato.",
        "synergy": ["llama3.1:70b"], "task": "Enterprise Intelligence",
        "ram": "64GB RAM", "vram": "40GB",
        "capabilities": ["Human-like Interaction", "Strategic Consulting", "Market Simulation", "Extreme Context Synthesis"]
    },
    "qwen2.5:32b": {
        "name": "Qwen 2.5 (32B)", "size": "18GB", "category": "ELITE_HEAVY_WEIGHT", 
        "pros": "Logica di livello enterprise", "cons": "Richiede molta VRAM", 
        "caveau": "Il Super-Cervello del Vault.", "forza": "Ragionamento astratto di livello superiore e multilinguismo perfetto.",
        "synergy": ["gemma2:27b"], "task": "Strategic Intelligence",
        "ram": "32GB RAM", "vram": "24GB",
        "capabilities": ["Quantum Logic", "Strategic Planning", "Infinite Context", "Zero-Shot Synthesis"]
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
    """Sincronizzazione Unificata: Modelli Installati + Catalogo Disponibile."""
    import httpx
    full_list = []
    seen_in_api = set()

    # 1. Recupero Modelli INSTALLATI (Ollama)
    base_url = app.state.lab.settings.get("ollama_url") if hasattr(app.state, 'lab') else "http://127.0.0.1:11434"
    ollama_urls = [os.environ.get("OLLAMA_HOST", base_url), base_url]
    for url in ollama_urls:
        if seen_in_api: break
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                r = await client.get(f"{url.rstrip('/')}/api/tags")
                if r.status_code == 200:
                    data = r.json()
                    for m in data.get("models", []):
                        name = m.get("name")
                        cat_info = MODEL_CATALOG.get(name) or MODEL_CATALOG.get(name.split(":")[0] + ":latest") or {}
                        
                        full_list.append({
                            "name": name,
                            "status": "INSTALLED",
                            "size": f"{round(m.get('size', 0) / (1024**3), 2)}GB",
                            "category": cat_info.get("category", "General"),
                            "pros": cat_info.get("pros", "Custom Node"),
                            "synergy": cat_info.get("synergy", ["None"]),
                            "task": cat_info.get("task", "General Reasoning"),
                            "strengths": cat_info.get("forza", "Hardware-Attached Analysis"),
                            "capabilities": cat_info.get("capabilities", []),
                            "ram": cat_info.get("ram", "N/D"),
                            "vram": cat_info.get("vram", "N/D")
                        })
                        seen_in_api.add(name)
        except: continue

    # 2. Recupero Modelli DISPONIBILI (Dal Catalogo, non ancora installati)
    for model_id, info in MODEL_CATALOG.items():
        if model_id not in seen_in_api:
            full_list.append({
                "name": model_id,
                "status": "AVAILABLE",
                "size": info.get("size", "N/D"),
                "category": info.get("category", "General"),
                "pros": info.get("pros", "N/D"),
                "synergy": info.get("synergy", ["None"]),
                "task": info.get("task", "General Reasoning"),
                "strengths": info.get("forza", "Elite Training"),
                "capabilities": info.get("capabilities", []),
                "ram": info.get("ram", "N/D"),
                "vram": info.get("vram", "N/D")
            })

    # 3. Recupero Modelli CUSTOM (Dalla Neural Forge)
    custom_models = load_custom_models()
    for name, info in custom_models.items():
        # Se è un modello Ollama, verifichiamo se è già presente (magari con nome diverso)
        # Ma in generale, li trattiamo come INSTALLED se il provider è 'ollama' o 'local'
        full_list.append({
            "name": f"{name} (Custom)",
            "status": "INSTALLED",
            "size": "N/D",
            "category": "CUSTOM_FORGE",
            "pros": f"User Integrated via {info.get('provider', 'Custom')}",
            "synergy": ["User_Workflow"],
            "task": "Specialized Purpose",
            "strengths": f"Puntatore: {info.get('path')}",
            "capabilities": ["Personal Training", "Custom Knowledge", "Private Core"],
            "ram": "Varie",
            "vram": "Varie"
        })

    return {"installed": full_list, "total_detected": len(full_list)}

@app.post("/api/lab/hub/custom/register")
async def register_custom_model(req: Dict, api_key: str = Depends(get_api_key)):
    """Registra un modello custom nel Vault."""
    name = req.get("name")
    provider = req.get("provider")
    path = req.get("path")
    
    if not name or not path:
        raise HTTPException(status_code=400, detail="Name and Path are required")
    
    custom = load_custom_models()
    custom[name] = {
        "provider": provider,
        "path": path,
        "registered_at": time.time()
    }
    save_custom_models(custom)
    
    # Se il provider è Ollama, possiamo anche tentare un 'ollama run' o simile per verificare
    print(f"🛠️ [Neural Forge] Modello registrato: {name} ({provider}) -> {path}")
    return {"status": "success", "model": name}

@app.delete("/api/models/delete/{model_name:path}")
async def delete_model(model_name: str, api_key: str = Depends(get_api_key)):
    """Rimuove fisicamente un modello per liberare spazio."""
    import httpx
    model_name = model_name.strip()
    try:
        async with httpx.AsyncClient() as client:
            base_url = app.state.lab.settings.get("ollama_url") if hasattr(app.state, 'lab') else "http://127.0.0.1:11434"
            r = await client.request("DELETE", f"{base_url}/api/delete", json={"name": model_name})
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
    namespace = data.get("namespace", "default")
    
    node_id = str(uuid.uuid4())
    engine.add_node(node_id, text, metadata={"source": filename, "namespace": namespace})
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
    data = signal.data
    
    # 🔐 Decrittazione se necessario (X25519 + AES-GCM)
    if signal.encrypted_data and engine and engine.crypto:
        peer = engine.gossip.peers.get(signal.source_node_id)
        if peer and peer.public_key:
            try:
                if not peer.shared_key:
                    peer.shared_key = engine.crypto.derive_shared_key(peer.public_key)
                
                decrypted_json = engine.crypto.decrypt(signal.encrypted_data, peer.shared_key)
                data = json.loads(decrypted_json)
            except Exception as e:
                print(f"🚨 [Mesh] Decrittazione fallita da {signal.source_node_id}: {e}")
                return {"status": "error", "message": "decryption_failed"}
        else:
            print(f"⚠️ [Mesh] Segnale cifrato ricevuto da peer sconosciuto o senza chiave: {signal.source_node_id}")

    if signal.payload_type == "upsert" and data:
        # Inserimento atomico in background del nodo sincronizzato
        node_id = data.get("id")
        text = data.get("text")
        # Evitiamo loop infiniti di gossip controllando se il nodo esiste già
        if node_id not in engine._nodes:
            engine.add_node(node_id, text, metadata=data.get("metadata", {}))
            return {"status": "synced", "node_id": node_id}
    return {"status": "ignored"}
    
# 🔑 SOVEREIGN AUTH ENDPOINTS
@app.get("/api/auth/google")
async def google_auth(api_key: str = Depends(get_api_key)):
    """Avvia il flusso OAuth2 per Google (Gmail/Pollers)."""
    if not engine or not engine.oauth:
        raise HTTPException(status_code=500, detail="OAuth Manager non inizializzato")
    
    try:
        # Questo aprirà il browser sul Mac dell'utente
        creds = engine.oauth.start_flow()
        return {
            "status": "ok", 
            "message": "Autenticazione completata con successo",
            "token_expiry": creds.expiry.isoformat() if creds.expiry else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore durante l'autenticazione: {str(e)}")

# 🕸️ MESH PROTOCOL v3.8.0
@app.get("/api/mesh/inventory")
async def mesh_inventory(api_key: str = Depends(get_api_key)):
    """Ritorna l'indice atomico dei nodi locali per il diffing Mesh."""
    return {"ids": list(engine._nodes.keys())}

@app.post("/api/mesh/pull")
async def mesh_pull(request: Request, api_key: str = Depends(get_api_key)):
    """Espone i nodi richiesti dai peer per la sincronizzazione."""
    data = await request.json()
    ids = data.get("ids", [])
    nodes = []
    for nid in ids:
        node = engine._nodes.get(nid)
        if node:
            nodes.append({
                "id": node.id,
                "text": node.text,
                "metadata": node.metadata
            })
    return {"nodes": nodes}

@app.post("/api/mesh/peers/add")
async def add_mesh_peer(request: Request, api_key: str = Depends(get_api_key)):
    """Aggiunge un dispositivo fidato alla rete Mesh."""
    data = await request.json()
    node_id = data.get("id") or f"peer_{len(engine.mesh.peers)}"
    url = data.get("url")
    peer_api_key = data.get("api_key")
    if not url: raise HTTPException(status_code=400, detail="URL del peer obbligatorio")
    engine.mesh.add_peer(node_id, url, peer_api_key)
    return {"status": "peer_connected", "id": node_id}

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

async def _run_hybrid_evolution(limit=500, offset=0):
    """Esecuzione effettiva dell'evoluzione (Iterativa e Non-Bloccante)."""
    async with engine_lock:
        if not engine: return
        total_nodes = len(engine._nodes)
        batch_size = 500
        current_offset = offset
        total_new_links = 0
        
        # Determine how many batches to process
        max_iterations = max(1, limit // batch_size)
        
        # Get settings from Orchestrator
        evol_model = app.state.lab.settings.get("evolution_model", "llama3.2")

        print(f"🧬 [Evolution] Batch active: {limit} nodes from {offset} using {evol_model}")

        for i in range(max_iterations):
            res = await asyncio.to_thread(engine.evolve_graph, dry_run=True, limit=batch_size, offset=current_offset)
            candidates = res["candidates"]
            current_offset = res["next_offset"]
            
            if not candidates: break

            sig_audit = SynapticSignal("QA-101", AgentRole.ARCHITECT, f"🛡️ EVOLUZIONE [BATCH {i+1}]: Analisi {len(candidates)} sinapsi...", SignalType.MISSION_UPDATE)
            app.state.lab.blackboard.post(sig_audit)
            
            approved = await asyncio.to_thread(app.state.lab.quantum.audit_synapses, candidates, model=evol_model)
            batch_top = sorted(approved, key=lambda x: x[2], reverse=True)[:2]
            
            synapses_data = []
            for src_id, dst_id, weight in approved:
                reason = None
                if (src_id, dst_id, weight) in batch_top:
                    n1 = engine._nodes.get(src_id)
                    n2 = engine._nodes.get(dst_id)
                    if n1 and n2:
                        app.state.lab.blackboard.post(SynapticSignal("SY-009", AgentRole.SYNTH, f"✨ SYNTHETIC INSIGHT: Legame {src_id[:8]} <-> {dst_id[:8]}", SignalType.MISSION_UPDATE))
                        ctx = f"A: {n1.text[:400]}\n\nB: {n2.text[:400]}"
                        q = "Spiega in 10 parole perché questi due concetti sono collegati."
                        reason = await app.state.lab.get_consensus_response(q, ctx, model=evol_model)
                synapses_data.append((src_id, dst_id, weight, reason))

            for src_id, dst_id, weight, reason in synapses_data:
                src_node = engine._nodes.get(src_id)
                dst_node = engine._nodes.get(dst_id)
                if src_node and dst_node:
                    from index.node import RelationType, SemanticEdge
                    src_node.edges.append(SemanticEdge(dst_id, RelationType.SYNAPSE, weight=weight, reason=reason, source="evolution_oracle"))
                    dst_node.edges.append(SemanticEdge(src_id, RelationType.SYNAPSE, weight=weight, reason=reason, source="evolution_oracle"))
                    total_new_links += 1
            await asyncio.sleep(0.3)

        app.state.lab.blackboard.post(SynapticSignal("SYSTEM", AgentRole.MISSION_ARCHITECT, f"✨ EVOLUZIONE COMPLETATA: {total_new_links} sinapsi.", SignalType.SYSTEM_NOTIFICATION))
        app.state.lab.quantum.is_fusing = False
        app.state.lab.synth.mode = "Navigating"

@app.post("/api/evolve")
async def evolve_mesh(background_tasks: BackgroundTasks, api_key: str = Depends(get_api_key)):
    """Trigger manuale per un'evoluzione massiva."""
    try:
        if not hasattr(app.state, 'lab'):
            raise HTTPException(status_code=500, detail="Lab not ready.")
        app.state.lab.dispatch_evolution_mission()
        background_tasks.add_task(_run_hybrid_evolution, limit=2000)
        return {
            "status": "mission_dispatched",
            "message": "Protocollo di Evoluzione Cognitiva avviato."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ingest/media")
async def ingest_media(file: UploadFile = File(...), namespace: Optional[str] = Form("default"), api_key: str = Depends(get_api_key)):
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
            # [v3.6.0] Logical Namespacing & Scalar Extraction
            file_type = ext.replace('.', '')
            node = engine.upsert_text(content, metadata={"source": file.filename, "namespace": namespace, "file_type": file_type})
            return {"status": "success", "nodes_created": 1, "ids": [node.id]}
            
        node_ids = await app.state.mm_processor.ingest(temp_path, namespace=namespace)
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

@app.get("/api/namespaces")
async def get_namespaces(api_key: str = Depends(get_api_key)):
    """[v3.6.0] Esploratore di Compartimenti: Restituisce l'elenco dei namespace attivi."""
    try:
        # 1. Query dai metadati testuali
        res = engine._prefilter.con.execute("SELECT DISTINCT namespace FROM vault_metadata").fetchall()
        text_ns = [r[0] for r in res if r[0]]
        
        # 2. Query dai metadati multimodali
        mm_ns = []
        try:
            if hasattr(app.state, 'mm_processor'):
                conn = duckdb.connect(app.state.mm_processor.db_path)
                res_mm = conn.execute("SELECT DISTINCT namespace FROM multimodal_synapses").fetchall()
                mm_ns = [r[0] for r in res_mm if r[0]]
                conn.close()
        except: pass
        
        # Merge e rimozione duplicati
        all_ns = sorted(list(set(text_ns + mm_ns + ["default", "Lavoro", "Privato", "Oliver"])))
        return {"namespaces": all_ns}
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
        
        base_url = app.state.lab.settings.get("ollama_url") if hasattr(app.state, 'lab') else "http://127.0.0.1:11434"
        async with httpx.AsyncClient(timeout=45.0) as client:
            r = await client.post(f"{base_url}/api/generate", json={
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
    
    timings = {}
    total_start = time.time()
    
    # 1. Ricerca Semantica Intelligente (Quantum Expansion v1.0)
    exp_start = time.time()
    search_query = await app.state.lab.expand_query(request.query)
    timings['expansion'] = (time.time() - exp_start) * 1000
    
    print(f"🔍 [Quantum Search] Query espansa: {search_query}")
    
    ret_start = time.time()
    results = engine.query(
        search_query, 
        k=request.top_k, 
        namespace=request.namespace,
        file_type=request.file_type,
        year=request.year,
        month=request.month
    )
    timings['retrieval'] = (time.time() - ret_start) * 1000
    
    try:
        mm_results = app.state.mm_processor.query(request.query, top_k=3, namespace=request.namespace)
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

    # 3. [SOVEREIGN FALLBACK] v4.9: Skywalker Web Incursion if Local Vault is empty or corrupted
    is_context_poor = len(context_text.strip()) < 50 # Soglia minima per considerare il contesto utile
    
    if (not results and not mm_results) or is_context_poor:
        corrupted_nodes = [r.node.id for r in results if len(r.node.text) < 20]
        print(f"📡 [Fallback] Knowledge Gap or Corrupted Nodes identified for '{request.query}'. Mobilizing FS-77 Skywalker...")
        try:
            # Attendiamo una "Incursione Rapida" (max 12s)
            await asyncio.wait_for(app.state.lab.forage_web_topic(request.query), timeout=12.0)
            # Rieseguiamo la query per pescare i nuovi dati
            results = engine.query(search_query, k=request.top_k, namespace=request.namespace)
            
            disclaimer = "⚠️ [AVVISO: RICERCA ESTERNA ATTIVATA]"
            if corrupted_nodes:
                disclaimer += f" - Nodi locali corrotti individuati: {', '.join(corrupted_nodes)}."
            else:
                disclaimer += " - Nessuna informazione locale trovata."
                
            context_text = f"{disclaimer}\n"
            for r in results:
                context_text += f"\n[FONTE ESTERNA - FS-77]: {r.node.text}"
                source_nodes.append(r.node.id)
        except Exception as e:
            print(f"⚠️ [Skywalker Fallback Error] {e}")

    full_context = context_text if context_text else "Nessun contesto trovato nel Vault."
    
    # [SOVEREIGN FOCUS] Sospendiamo gli agenti background per dare massimo respiro a Ollama
    app.state.lab.pause_agents = True
    
    gen_start = time.time()
    try:
        # PROTOCOLLO CONSENSUS (v3.0)
        if request.consensus:
            print(f"🏛️ [Consensus Mode] Attivazione Swarm per: {request.query}")
            answer = await app.state.lab.get_consensus_response(request.query, full_context)
        else:
            # Risposta standard a modello singolo
            try:
                # [v4.5] Enhanced LLM Resilience: Adaptive Timeout & Dynamic Model Discovery
                res = await asyncio.to_thread(os.popen("ollama list").read)
                installed = [line.split()[0] for line in res.splitlines()[1:] if line.strip()]
                
                # Priorità: Mistral > Primo Modello Installato > Fallback
                model = "mistral:latest" if "mistral:latest" in installed else (installed[0] if installed else "mistral")
                base_url = app.state.lab.settings.get("ollama_url") if hasattr(app.state, 'lab') else "http://127.0.0.1:11434"
                
                async with httpx.AsyncClient(timeout=120.0) as client:
                    try:
                        r = await client.post(f"{base_url}/api/generate", json={
                            "model": model, 
                            "prompt": f"Contesto:\n{full_context}\n\nQ: {request.query}", 
                            "stream": False
                        })
                        r.raise_for_status()
                        answer = r.json().get("response", "Nessuna risposta generata dall'IA.")
                    except httpx.TimeoutException:
                        answer = "⚠️ Neural Timeout: L'IA sta impiegando troppo tempo per rispondere (modelli pesanti in caricamento). Riprova tra 30 secondi."
                    except httpx.ConnectError:
                        answer = "❌ Connection Refused: Ollama non risponde. Assicurati che l'app Ollama sia aperta."
                    except Exception as inner_e:
                        answer = f"🌐 Neural Link Error: {str(inner_e)}"
            except Exception as e:
                answer = f"🧠 Cognitive Fault: {str(e)}"
    finally:
        # Ripristiniamo il background work
        app.state.lab.pause_agents = False
    
    timings['generation'] = (time.time() - gen_start) * 1000
    timings['total'] = (time.time() - total_start) * 1000

    return {
        "answer": answer,
        "context_nodes": source_nodes,
        "mode": "CONSENSUS" if request.consensus else "SINGLE_AGENT",
        "telemetry": timings
    }

@app.get("/events")
async def sse_stream(request: Request):
    """Il battito cardiaco della Dashboard: Telemetria Real-time."""
    # Helper per calcolare il peso del cervello digitale
    _cached_size = {"val": 0, "time": 0}
    def get_dir_size(path):
        """Versione ottimizzata (v3.0): Cache di 60s per evitare I/O costante in SSE."""
        now = time.time()
        if now - _cached_size["time"] < 60:
            return _cached_size["val"]
            
        total = 0
        try:
            p = Path(path)
            if not p.exists(): return 0
            for f in p.glob('*.db'): total += f.stat().st_size
            for f in p.glob('*.ael'): total += f.stat().st_size
            if total == 0: total = 1024 * 1024 # 1MB fallback
        except: pass
        
        _cached_size["val"] = total
        _cached_size["time"] = now
        return total

    v_initial = engine.data_dir if engine else Path("./data")
    last_size = get_dir_size(v_initial)

    async def event_generator():
        last_size = 0
        try:
            # 1. KEEPALIVE / INITIAL SYNC
            loop = asyncio.get_event_loop()
            stats = await loop.run_in_executor(None, engine.stats, 30000)
            initial_data = {
                "points": stats.get("point_cloud", []),
                "links": stats.get("edge_sample", []),
                "nodes_count": len(engine._nodes),
                "edges_count": stats.get("edges_count", 0),
                "storage": {"total": "INIT", "pulse": "SYNCING"},
                "lab": app.state.lab.get_status() if hasattr(app.state, 'lab') else {}, 
                "system": {}, 
                "agent007": {"entities_count": 0, "relations_count": 0}
            }
            yield f"data: {json.dumps(initial_data, default=json_serializer)}\n\n"
            
            while not _is_shutting_down:
                if await request.is_disconnected():
                    break

                try:
                    # 2. Storage Metrics
                    v_path = engine.data_dir if engine else Path("./data")
                    current_size = get_dir_size(v_path)
                    growth = current_size - last_size
                    last_size = current_size
                    
                    size_mb = round(current_size / (1024 * 1024), 2)
                    storage_hud = {
                        "total": f"{size_mb} MB" if size_mb < 1024 else f"{round(size_mb/1024, 2)} GB",
                        "pulse": f"+{round(growth/1024, 1)} KB" if growth > 0 else "STABLE"
                    }

                    # 3. 3D Engine Stats (Offloaded)
                    try:
                        stats = await loop.run_in_executor(None, engine.stats)
                    except: stats = {}
                    
                    # 4. Neural Lab & System Status
                    async with engine_lock:
                        lab_status = app.state.lab.get_status() if hasattr(app.state, 'lab') else {}
                        
                        from utils.hardware import HardwareTuner
                        tuner = HardwareTuner(data_dir=engine.data_dir if hasattr(engine, 'data_dir') else "./vault_data")
                        hw_stats = tuner.get_telemetry()

                        # 🕵️ Agent007 Hardbank (Protect from DB Locks)
                        a007_data = {"entities_count": 0, "relations_count": 0}
                        try:
                            if hasattr(engine, 'agent007') and engine.agent007:
                                ent_res = engine.agent007.con.execute("SELECT count(*) FROM agent007_entities").fetchone()
                                rel_res = engine.agent007.con.execute("SELECT count(*) FROM agent007_relations").fetchone()
                                ent = ent_res[0] if ent_res else 0
                                rel = rel_res[0] if rel_res else 0
                                a007_data = {"entities_count": ent, "relations_count": rel}
                        except Exception as e:
                            if "not subscriptable" not in str(e): # Silencing the common NoneType race condition
                                print(f"🕵️ [Agent007/DB] {e}")

                        # 🧬 Global Cluster Detection (Vault Total)
                        try:
                            # 1. Check historical unique collections from persistent store
                            res = engine._prefilter.con.execute("SELECT COUNT(DISTINCT collection) FROM vault_metadata WHERE collection != 'default' AND collection IS NOT NULL").fetchone()
                            db_clusters = res[0] if res else 0
                            
                            # 2. Fetch current session activity from Quantum Agent
                            session_fused = 0
                            if 'QA-101' in lab_status.get('agents', {}):
                                session_fused = lab_status['agents']['QA-101'].get('fused_clusters', 0)
                            
                            # 3. Calculate Global Cumulative Total
                            # We use source as a fallback for collection to handle existing nodes (v17.6 Fix)
                            mem_clusters = len(set(
                                n.collection if n.collection != 'default' else n.metadata.get('source', 'default') 
                                for n in engine._nodes.values() 
                                if (n.collection != 'default' or n.metadata.get('source', 'default') != 'default')
                            ))
                            clusters_count = max(db_clusters, session_fused, mem_clusters)
                        except Exception as e:
                            # Fallback if DB query fails
                            clusters_count = len(set(
                                n.collection if n.collection != 'default' else n.metadata.get('source', 'default') 
                                for n in engine._nodes.values() 
                                if (n.collection != 'default' or n.metadata.get('source', 'default') != 'default')
                            ))

                        # 📏 Semantic Distance Calculation (Cohesion Metric)
                        try:
                            # We use the standard deviation of projections as a proxy for 'distance'
                            # Higher SD = nodes are more spread out (Semantic Diversity)
                            # Lower SD = nodes are clustered (Semantic Focus)
                            if points_array := [[p.get("x", 0), p.get("y", 0), p.get("z", 0)] for p in stats.get("point_cloud", [])]:
                                p_arr = np.array(points_array)
                                dist_val = float(np.std(p_arr)) / 500000.0 # Normalized for UI
                            else: dist_val = 0.84 # Baseline
                        except: dist_val = 0.84

                        # 🧬 [v4.8] Cognitive Health Metrics
                        try:
                            sample_nodes = list(engine._nodes.values())[:100]
                            if sample_nodes:
                                avg_ret = sum(engine.cognitive.calculate_strength(
                                    n.metadata.get("last_access", n.created_at),
                                    n.metadata.get("importance", 0.5),
                                    n.metadata.get("access_count", 1)
                                ) for n in sample_nodes) / len(sample_nodes)
                                
                                # Stability is derived from average access count and importance
                                avg_stab = sum(min(1.0, (n.metadata.get("access_count", 1) * 0.2) + n.metadata.get("importance", 0.5)) for n in sample_nodes) / len(sample_nodes)
                            else:
                                avg_ret, avg_stab = 1.0, 1.0
                        except: avg_ret, avg_stab = 0.98, 0.99

                        data = {
                            "points": stats.get("point_cloud", []),
                            "links": stats.get("edge_sample", []),
                            "nodes_count": len(engine._nodes),
                            "edges_count": stats.get("edges_count", 0),
                            "clusters_count": int(clusters_count),
                            "semantic_distance": round(dist_val, 2),
                            "cognitive": {
                                "retention": round(avg_ret, 4),
                                "stability": round(avg_stab, 4)
                            },
                            "storage": storage_hud,
                            "lab": lab_status,
                            "hardware": hw_stats, # [v4.0] Sovereign Telemetry
                            "weather": app.state.lab.blackboard.get_weather() if hasattr(app.state, 'lab') else {},
                            "agent007": a007_data
                        }
                        yield f"data: {json.dumps(data, default=json_serializer)}\n\n"

                except Exception as e:
                    print(f"⚠️ [SSE/Loop] {e}")
                    yield f"data: {json.dumps({'status': 'RECOVERING'})}\n\n"
                    await asyncio.sleep(2)
                
                await asyncio.sleep(1.0)
        finally:
            print("🔌 [SSE] Stream telemetria terminato pulitamente.")

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
        return {"status": "ok"}
    return {"status": "error", "message": "Lab not initialized"}

# 🤖 SWARM DYNAMIC ORCHESTRATION (v12.0)

class SpawnAgentRequest(BaseModel):
    name: str
    role: str
    prompt: Optional[str] = ""
    model: Optional[str] = "llama3.2"
    api_key: str

@app.post("/api/swarm/spawn")
async def spawn_custom_agent(req: SpawnAgentRequest):
    if req.api_key != VAULT_KEY: raise HTTPException(status_code=403, detail="Invalid Vault Key")
    if hasattr(app.state, 'lab'):
        role_map = {
            "archivist": AgentRole.EXPERT,
            "analyst": AgentRole.ANALYST,
            "creative": AgentRole.CREATIVE,
            "guardian": AgentRole.GUARDIAN,
            "architect": AgentRole.ARCHITECT
        }
        aid = app.state.lab.spawn_custom_agent(req.name, role_map.get(req.role, AgentRole.EXPERT), req.prompt, req.model)
        return {"status": "ok", "agent_id": aid}
    return {"status": "error", "message": "Lab not initialized"}

class BroadcastCommandRequest(BaseModel):
    command: str
    api_key: str

@app.post("/api/swarm/broadcast")
async def broadcast_swarm_command(req: BroadcastCommandRequest):
    if req.api_key != VAULT_KEY: raise HTTPException(status_code=403, detail="Invalid Vault Key")
    if hasattr(app.state, 'lab'):
        if req.command == "SCAN":
            app.state.lab.dispatch_evolution_mission()
        elif req.command == "PURGE":
            app.state.lab.blackboard.post_signal("SYSTEM", "PURGE_REQUEST", "⚠️ GLOBAL PURGE INITIALIZED: Cleaning semantic cache...", 2.0)
            # Logica di purge effettiva dipenderà dall'implementazione specifica degli agenti
        return {"status": "ok", "command": req.command}
    return {"status": "error", "message": "Lab not initialized"}

@app.post("/api/swarm/delete")
async def delete_swarm_agent(agent_id: str, api_key: str):
    if api_key != VAULT_KEY: raise HTTPException(status_code=403, detail="Invalid Vault Key")
    if hasattr(app.state, 'lab'):
        if agent_id in app.state.lab.agents:
            del app.state.lab.agents[agent_id]
            return {"status": "ok"}
    return {"status": "error", "message": "Agent not found or Lab not initialized"}

@app.get("/api/audit/ledger")
async def get_audit_ledger(full: bool = False, key: str = Depends(get_api_key)):
    """[Chrono-Log] Recupera la storia delle missioni completa o di sessione."""
    if not hasattr(app.state, 'lab'):
        return []
        
    logs = []
    # 1. Recupero log di sessione (Memory)
    try:
        logs = app.state.lab.get_audit_ledger()
    except: pass
    
    # 2. Se richiesto, integriamo l'Archivio Permanente (DuckDB via Archiver)
    if full:
        try:
            if hasattr(app.state.lab, 'archiver') and app.state.lab.archiver:
                # Merge e Sort per timestamp decrescente
                history = app.state.lab.archiver.history
                seen_ids = {f"{l.get('timestamp')}-{l.get('agent')}" for l in logs}
                for entry in history:
                    unique_id = f"{entry.get('timestamp')}-{entry.get('agent')}"
                    if unique_id not in seen_ids:
                        logs.append(entry)
        except: pass
    
    # Sort finale: i più recenti in alto
    logs.sort(key=lambda x: str(x.get('timestamp', '')), reverse=True)
    
    # 🛡️ [v4.0.1] Session Isolation: Se non è richiesto il log completo, 
    # filtriamo via qualsiasi cosa sia più vecchia dell'avvio del server.
    if not full:
        server_boot_str = app.state.boot_time.strftime("%Y-%m-%d %H:%M:%S")
        logs = [l for l in logs if str(l.get('timestamp', '')) >= server_boot_str]

    print(f"📄 [Audit] Serving {len(logs)} mission records (Full: {full})")
    return logs

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
# 🏛️ [Phase 3] SUPREME COURT VERDICT REVIEW ENDPOINTS
@app.get("/api/swarm/audit-queue")
async def get_court_queue(api_key: str = Depends(get_api_key)):
    """Espone la coda di arbitraggio della Corte Suprema (Supreme Court)."""
    if not hasattr(app.state, 'lab'): return []
    return app.state.lab.autonomous_audit_queue

@app.post("/api/swarm/resolve-verdict")
async def resolve_verdict(request: Request, api_key: str = Depends(get_api_key)):
    """Risolve un verdetto pendente della Corte Suprema (Approvazione/Rifiuto manuale)."""
    data = await request.json()
    idx = data.get("index")
    decision = data.get("decision")
    
    if not hasattr(app.state, 'lab'):
        raise HTTPException(status_code=500, detail="Laboratory not active")
    
    queue = app.state.lab.autonomous_audit_queue
    if idx is None or idx >= len(queue):
        raise HTTPException(status_code=404, detail="Verdict not found in queue")
    
    # Preleviamo l'item dalla coda
    audit_item = queue.pop(idx)
    
    if decision == 'approve':
        src = audit_item.get("src")
        dst = audit_item.get("dst")
        if src in engine._nodes and dst in engine._nodes:
            engine.add_relation(src, dst, type=9, weight=0.98) 
            app.state.lab.blackboard.post(SynapticSignal("SUPREME_COURT", AgentRole.OPTIMIZER, 
                f"✅ VERDICT_OVERRIDE: Synapse between {src[:8]} and {dst[:8]} approved by Sovereign.", 
                SignalType.SYSTEM_HEALING))
    else:
        app.state.lab.blackboard.post(SynapticSignal("SUPREME_COURT", AgentRole.OPTIMIZER, 
            f"❌ VERDICT_REJECTED: Synapse proposal dismissed by Sovereign decree.", 
            SignalType.SYSTEM_NOTIFICATION))
            
    return {"status": "ok"}

# 🧠 SOVEREIGN RECOMMENDATION ENGINE API (v1.0)
@app.get("/api/system/recommendations")
async def get_system_recommendations():
    """Restituisce consigli sugli LLM basati su hardware e modelli installati."""
    try:
        from utils.recommendations import SovereignRecommendationEngine
        
        # Recupera modelli installati via Ollama
        installed = []
        if hasattr(app.state, 'lab'):
            installed = app.state.lab.settings.get_installed_models()
        
        engine_rec = SovereignRecommendationEngine(installed)
        return {
            "hw_info": engine_rec.hw_info,
            "recommendations": engine_rec.get_all_recommendations()
        }
    except Exception as e:
        print(f"❌ [Rec API Error] {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    print("🚀 [BOOT-TRACE-77i] CARICAMENTO CORE NEURALE v4.0.1 Sovereign...")
    # Avvio del server su 127.0.0.1 con LOG INFO per vedere lo stato
    uvicorn.run(app, host="127.0.0.1", port=8001, log_level="info")
