import time
import json
import os
import shutil
import uuid
import numpy as np
import resource
from pathlib import Path
from typing import Optional, Any, Callable, OrderedDict, List, Dict
from itertools import islice
import threading
import hashlib

# Core Imports
from index.node import VaultNode, QueryResult, RelationType, MemoryTier, SemanticEdge
from index.hnsw import AdaptiveHNSW
from graph.graph import ContextGraph
from graph.ingester import AutoKnowledgeLinker
from index.turboquant import TurboQuantizer, TwoStageTurboSearch
from index.sparse import BM25SEncoder
from retrieval.fusion import FusionRanker
from agent.session import SessionManager
from retrieval.prefilter import DuckDBPrefilter
from memory_tiers import MemoryTierManager
from retrieval.prefilter import DuckDBPrefilter
from memory_tiers import MemoryTierManager
from utils.logger import NeuralLogger
from storage.snapshot import SnapshotEngine
from utils.backpressure import backpressure

# [Phase 32] Structural Ingester
from retrieval.parsers import extract_structural_chunks

# v0.4.0 Mesh Network Imports
from network.consensus import SovereignConsensus
from index.sharding import ShardManager
from security.homomorphic import SovereignShield

# v0.5.0 Synaptic Imports
from index.cognitive import CognitiveDecayEngine, WisdomSummarizer, CognitiveDecayDaemon
from retrieval.bridge import LatentBridge
from network.gossip import GossipManager
from network.ledger import SovereignLedger
from agent007_lab import Agent007Lab
from utils.benchmark import ModelBenchmarkTracker

class QueryIntent:
    SEMANTIC = "semantic"
    ANALYTIC = "analytic"
    RELATIONAL = "relational"
    HYBRID = "hybrid"

class NeuralQueryPlanner:
    def plan(self, query: str) -> str:
        q_lower = query.lower()
        analytic_words = ["mostra", "quanti", "data", "filtra", "dove", "somma", "media"]
        relational_words = ["legato a", "connessione", "perché", "relazione", "collegamento"]
        a_score = sum(1 for w in analytic_words if w in q_lower)
        r_score = sum(1 for w in relational_words if w in q_lower)
        if (a_score > 0 and r_score > 0) or (a_score == 0 and r_score == 0):
            return QueryIntent.HYBRID
        if a_score > r_score: return QueryIntent.ANALYTIC
        if r_score > a_score: return QueryIntent.RELATIONAL
        return QueryIntent.HYBRID

from enum import Enum

class ComputeMode(str, Enum):
    ECO = "ECO"       # CPU Only (NEON/AVX)
    HYBRID = "HYBRID" # RAM + GPU Inference
    WARP = "WARP"     # FULL VRAM / NVIDIA VERA Mode

class NeuralVaultEngine:
    """
    CORE ENGINE v2.2.0 (Agent007-march High-Performance Edition)
    ────────────────────────────────────────────────────────
    Supporta calcolo eterogeneo (CPU/GPU) e ottimizzazione 
    per l'architettura NVIDIA Rubin (2026).
    """
    def __init__(self, dim=1024, data_dir=None, use_quantization=True, use_rust=False, embedder_fn=None, collection="default", use_float16=True):
        self.dim = dim
        self.use_float16 = use_float16 # Priority #1 Gap
        self.data_dir = Path(data_dir) if data_dir else Path("./data")
        self.compute_mode = ComputeMode.HYBRID # Default sicuro
        self._lock = threading.Lock()
        
        # Rilevazione Hardware Proattiva (v1.6.0: Granular Check)
        self.has_cuda = False
        try:
            import subprocess
            res = subprocess.run(['nvidia-smi'], capture_output=True, timeout=1.0)
            if res.returncode == 0: self.has_cuda = True
        except: pass

        self.has_metal = False
        try:
            import platform
            if platform.system() == "Darwin": self.has_metal = True
        except: pass

        self.hardware_dna = f"CUDA: {self.has_cuda} | METAL: {self.has_metal}"
        print(f"🧬 NeuralVault: Hardware Trace -> {self.hardware_dna}")
        
        # [System Check] Disk Space Guard
        try:
            total, used, free = shutil.disk_usage(self.data_dir.parent)
            if free < 524288000: # 500MB
                print(f"⚠️ [CRITICAL] Spazio disco quasi esaurito: {free // (1024*1024)}MB disponibili.")
                print("   ➞ Questo causerà la corruzione dei database DuckDB (WAL) e crash casuali!")
        except: pass

        self.default_collection = collection
        self._embedder_fn = embedder_fn
        self._query_planner = NeuralQueryPlanner()
        self.logger = NeuralLogger(log_dir=self.data_dir / "logs" if self.data_dir else None)
        self._tiers = MemoryTierManager(data_dir=self.data_dir, dim=dim)
        self._nodes = {}
        self._sessions = SessionManager(data_dir=self.data_dir)
        storage_get_fn = lambda nid: self._tiers.get(nid)
        self._hnsw = AdaptiveHNSW(dim=dim, use_rust=use_rust, storage_get_fn=storage_get_fn)
        # In AdaptiveHNSW, se use_rust è False, usiamo il dtype desiderato
        if not use_rust:
            self._hnsw.vector_dtype = np.float16 if use_float16 else np.float32

        self._prefilter = DuckDBPrefilter(db_path=self.data_dir)
        self._sparse = BM25SEncoder()
        # Abilitiamo il Cross-Encoder (Gap #4)
        self._ranker = FusionRanker(use_reranker=True)
        # Inizializzazione Benchmark Hub (v2.9: AI Observability)
        self.benchmarks = ModelBenchmarkTracker(self)
        
        # Self-Healing System (Auto-Guard)
        self._graph_ingester = AutoKnowledgeLinker()
        self._graph = None
        self._tq_search = None
        if use_quantization:
            self._tq_search = TwoStageTurboSearch(dim=dim, use_rust=use_rust)
            
        # v0.4.0 Pillars
        # --- [Persistence STABILIZATION] ---
        node_id_file = self.data_dir / "node_id.json"
        if node_id_file.exists():
            try:
                with open(node_id_file, 'r') as f:
                    self.node_id = json.load(f).get("node_id")
            except:
                self.node_id = f"vault_{uuid.uuid4().hex[:8]}"
        else:
            self.node_id = f"vault_{uuid.uuid4().hex[:8]}"
            with open(node_id_file, 'w') as f:
                json.dump({"node_id": self.node_id}, f)

        self.consensus = SovereignConsensus(
            node_id=self.node_id,
            data_dir=str(self.data_dir / "consensus")
        )
        self.shards = ShardManager(engine_data_dir=self.data_dir)
        self.shield = SovereignShield()
        
        # v0.5.0 Synaptic Pillars
        self.cognitive = CognitiveDecayEngine()
        self.wisdom = WisdomSummarizer(self)
        self.bridge = LatentBridge(unified_dim=dim)
        
        # v1.4.0 Engine Metabolism: Cognitive Decay Daemon
        self.decay_daemon = CognitiveDecayDaemon(self)
        self.decay_daemon.start()
        self.logger.info("Cognitive Decay Daemon: ONLINE")
        
        # Fase 26: Sovereign Snapshot Engine
        self.snapshot_engine = SnapshotEngine(data_dir=self.data_dir, engine=self)
        
        # v0.5.5 Indestructible: Auto-Recovery on Startup
        self._recovery_boot()

        # v2.1.0 Agent007-march: Discrete Intelligence Engine
        from agent007_intelligence import Agent007Intelligence, Agent007Investigator
        from agent007_blueprint import Agent007Blueprint
        
        self.agent007 = Agent007Intelligence(db_path=str(self.data_dir / "agent007.db"), engine=self)
        self.blueprint = Agent007Blueprint(self)
        
        # Condividiamo la connessione DuckDB esistente per efficienza
        # Linea 141 rimossa per mantenere l'indipedenza e persistenza di agent007.db
        self.investigator = Agent007Investigator(self.agent007)
        self.lab = Agent007Lab(self)
        # v1.0.0 Enterprise: Gossip Mesh Initializer
        self.gossip = GossipManager(local_node_id=self.node_id)
        
        # v1.0.0 Enterprise: Ledger Initializer (Immutability)
        self.ledger = SovereignLedger()
        
        print("🕵️ Agent007-march: Sovereign Intelligence Engine ONLINE.")
        print("🏛️ Agent007-Blueprint: Mission Architect READY.")
        print("🏛️ Sovereign Ledger: Integrity Chain ACTIVE.")

    def _recovery_boot(self):
        """Ripristina lo stato atomico della Mesh e l'integrità dei nodi."""
        print("🛡️ [System] Inizio procedura di Self-Healing...")
        
        # 1. Replay Consensus Ledger (Integrità Transazionale)
        history = self.consensus.replay_full_history()
        if history:
            print(f"✅ Consensus: {len(history)} eventi nel ledger ripristinati.")

        # 2. Migration Bridge (Recupero dati pre-Aegis)
        self._bridge_legacy_migration()
        
        # 3. Fase 26: Instant Boot da Snapshot (Struttura HNSW)
        snapshot_loaded = self.snapshot_engine.load_snapshot()
        
        # 4. Hot Hydration (Dati Nodi -> RAM)
        # v11.6.8: Carichiamo sempre i nodi per visibilità 3D.
        # Con il backend Rust, possiamo gestire 50.000+ nodi senza rallentamenti.
        limit = 50000 
        print(f"🕯️ [Boot] Avvio Hot Hydration (Limit: {limit})...")
        
        recent_nodes = self._tiers.get_all_recent(limit=limit)
        total_hydration = len(recent_nodes)
        
        if total_hydration > 0:
            print(f"🏺 [Hydration] Iniezione di {total_hydration} nodi nella Neural Grid...")
            for i, node in enumerate(recent_nodes):
                self._nodes[str(node.id)] = node
                if snapshot_loaded:
                    self._hnsw.nodes[str(node.id)] = node
                else:
                    self._hnsw.insert(node)
                
                if i % 100 == 0 or i == total_hydration - 1:
                    percent = ((i + 1) / total_hydration) * 100
                    print(f"\r   ➞ Sincronizzazione: {percent:.1f}% ({i+1}/{total_hydration})", end="", flush=True)
            print(f"\n✅ [Hydration] Sincronizzazione completata.")
            
            # v11.6: Persistenza Snapshot per accelerare il prossimo avvio (Instant Boot)
            try:
                self.snapshot_engine.take_snapshot()
            except Exception as e:
                print(f"⚠️ [Snapshot Error] Auto-save failed: {e}")
        else:
            print("⚠️ [Boot] Aegis-Log vuoto. Tentativo di Deep Recovery da DuckDB...")
            self._deep_recovery_from_duckdb()
            if len(self._nodes) == 0:
                self._autonomous_discovery_recovery()

    def _deep_recovery_from_duckdb(self):
        """Recupera i nodi dai metadati DuckDB estraendo i dati dal campo JSON."""
        try:
            print("🔍 [Deep Recovery] Analisi strutturale vault_metadata...")
            # 1. Identifichiamo le colonne disponibili
            cols = [c[1] for c in self._prefilter.con.execute("PRAGMA table_info('vault_metadata')").fetchall()]
            
            # 2. Query dinamica basata sul campo JSON 'metadata'
            id_col = "id" if "id" in cols else "metadata->>'$.id'"
            text_query = "metadata->>'$.text'"
            
            query = f"SELECT {id_col}, {text_query}, metadata FROM vault_metadata LIMIT 5000"
            res = self._prefilter.con.execute(query).fetchall()
            
            if res:
                print(f"✨ [Deep Recovery] Individuati {len(res)} nodi potenziali. Innesco ricostruzione mesh...")
                recovered_count = 0
                for r_id, r_text, r_meta in res:
                    if not r_id: continue
                    # Se il testo è nullo nella root, lo cerchiamo nel dizionario metadata (se r_meta è già dict)
                    import json
                    meta_dict = json.loads(r_meta) if isinstance(r_meta, str) else r_meta
                    final_text = r_text or meta_dict.get("text", "")
                    
                    vec = self._embed_text(final_text)
                    node = VaultNode(id=r_id, text=final_text, vector=vec, metadata=meta_dict)
                    
                    self._nodes[str(r_id)] = node
                    self._hnsw.insert(node)
                    self._tiers.episodic.put(node, immediate=False)
                    recovered_count += 1
                
                self._tiers.episodic._fd.flush()
                print(f"✅ [Deep Recovery] {recovered_count} nodi riemersi dal Cold-Storage.")
            else:
                print("⚠️ [Deep Recovery] DuckDB non contiene record validi.")
        except Exception as e:
            print(f"⚠️ [Deep Recovery] Fallito: {e}")
            import traceback
            traceback.print_exc()

    def _autonomous_discovery_recovery(self):
        """Tenta il recupero da backup o percorsi di benchmark se il caveau è vuoto."""
        potential_paths = [
            self.data_dir.parent / "data" / "episodic",
            self.data_dir.parent / "benchmarks" / "ann-benchmarks-main" / "vault_data" / "episodic"
        ]
        for path in potential_paths:
            if (path / "data.mdb").exists():
                print(f"🔍 [Discovery] Trovato database potenziale in {path}. Tento il recupero...")
                try:
                    from storage.lmdb_store import LmdbStore
                    with LmdbStore(path) as db:
                        nodes = list(db.iter_all())
                        if nodes:
                            print(f"✨ [Discovery] Recuperati {len(nodes)} nodi. Migrazione in corso...")
                            self._tiers.episodic.put_batch(nodes)
                            # Riavvia hydration
                            recent = self._tiers.get_all_recent(limit=3000)
                            for n in recent: self._nodes[str(n.id)] = n
                            return
                except:
                    pass

    def _bridge_legacy_migration(self):
        """Migra i dati dal vecchio LMDB al nuovo Aegis-Log se necessario."""
        lmdb_path = self.data_dir / "episodic" / "data.mdb"
        aegis_path = self.data_dir / "episodic" / "vault_stream.ael"
        
        if lmdb_path.exists() and (not aegis_path.exists() or aegis_path.stat().st_size == 0):
            print("🚚 [Migration] Rilevato vecchio database LMDB. Analisi integrità...")
            from storage.lmdb_store import LmdbStore
            try:
                legacy_store = LmdbStore(self.data_dir / "episodic")
                # Tentativo di recupero massivo
                nodes = []
                print("🚚 [Migration] Estrazione nodi in corso (potrebbe richiedere tempo)...")
                for node in legacy_store.iter_all():
                    nodes.append(node)
                
                if nodes:
                    print(f"🚚 [Migration] Trovati {len(nodes)} nodi. Innesco trasferimento atomico verso Aegis-Log...")
                    self._tiers.episodic.put_batch(nodes)
                    print(f"✅ [Migration] Migrazione completata: {len(nodes)} nodi messi in sicurezza.")
                    # Verifichiamo il file Aegis-Log
                    print(f"✅ [Migration] Aegis-Log size: {aegis_path.stat().st_size / (1024*1024):.2f} MB")
                else:
                    print("⚠️ [Migration] Nessun nodo trovato nel vecchio database (vuoto o incompatibile).")
                legacy_store.close()
            except Exception as e:
                print(f"⚠️ [Migration] Errore critico durante il bridge: {e}")
                import traceback
                traceback.print_exc()

    def run_compaction(self):
        """Fase 27: Aegis Reaper (Async Compaction) & Snapshot Trigger."""
        def _compact_bg():
            print("💀 [Aegis Reaper] Avvio compattazione asincrona...")
            try:
                if hasattr(self._tiers, 'episodic') and hasattr(self._tiers.episodic, 'compact'):
                    self._tiers.episodic.compact()
                self.snapshot_engine.take_snapshot()
                print("💀 [Aegis Reaper] Compattazione e Snapshot completati.")
            except Exception as e:
                print(f"⚠️ [Aegis Reaper] Errore: {e}")
                
        threading.Thread(target=_compact_bg, daemon=True).start()

    def upsert(self, node: VaultNode):
        """Inserisce un singolo nodo garantendo la persistenza atomica."""
        start_t = time.time()
        self.upsert_batch([node])
        dur = (time.time() - start_t) * 1000
        self.logger.log_ingestion(node.id, dur)

    def get_node(self, node_id: str) -> Optional[VaultNode]:
        """
        [Fase 2.9: Universal Accessor]
        Recupera un nodo in modo affidabile cercando in RAM (Neural Grid) 
        e poi nei Tiers di memoria persistenti.
        """
        node_id = str(node_id)
        # 1. Check RAM (Neural Grid)
        node = self._nodes.get(node_id)
        if node: return node
        
        # 2. Check Persistenza (Aegis-Log/EPISODIC)
        try:
            return self._tiers.get(node_id)
        except:
            return None

    def _get_semantic_chunks(self, text: str) -> List[str]:
        """
        Spezza il testo seguendo confini logici (Fase Singolarità: Modulo 1).
        Evita di tagliare frasi a metà e mantiene i paragrafi coesi.
        """
        if not text: return []
        
        # Se il testo è breve, un unico chunk
        if len(text) < 300: return [text]
        
        # Euristica: Spezziamo su doppi a capo o singoli a capo se il testo è denso
        split_token = "\n\n" if "\n\n" in text else "\n"
        raw_chunks = [p.strip() for p in text.split(split_token) if p.strip()]
        final_chunks = []
        current_chunk = ""
        
        for p in raw_chunks:
            if len(current_chunk) + len(p) < 1200:
                current_chunk += "\n\n" + p if current_chunk else p
            else:
                if current_chunk: final_chunks.append(current_chunk)
                current_chunk = p
                
        if current_chunk:
            final_chunks.append(current_chunk)
            
        return final_chunks

    def delete_node(self, node_id: str):
        """
        Cancellazione Atomica: Rimuove un nodo da tutto l'ecosistema sovrano.
        """
        node_id = str(node_id)
        with self._lock:
            # 1. Rimuove dalla Neural Grid (RAM)
            node = self._nodes.get(node_id)
            self._nodes.pop(node_id, None)
            
            # 2. Rimuove dall'indice HNSW
            try:
                self._hnsw.delete(node_id)
            except: pass
            
            # 3. Rimuove dai Tiers di Memoria (LRU + Disk)
            self._tiers.delete(node_id)
            
            # 4. Rimuove dai metadati DuckDB
            self._prefilter.delete(node_id)
            
            # 5. Invalida Shards e Cache Associate
            if node:
                self.shards.create_shard("hot_node", lambda n: n.id == node_id, {node_id: node})
            
        print(f"🗑️ [Engine] Nodo {node_id[:8]} cancellato permanentemente.")
        return True

    def rollback_node(self, node_id: str) -> bool:
        """
        [Fase 25: Rollback] Ripristina un nodo eliminato (soft-delete) dal log AOBF.
        Protocollo Guardian: Ripristina l'integrità del Vault in caso di errore.
        """
        node_id = str(node_id)
        with self._lock:
            # 1. Tenta il rollback dal tier persistente (AOBF)
            success = self._tiers.undelete(node_id)
            if not success:
                print(f"❌ [Rollback] Impossibile recuperare il nodo {node_id[:8]}. Forse già compattato?")
                return False
                
            # 2. Nodo recuperato, ora re-idratiamo i motori
            node = self._tiers.get(node_id)
            if node:
                # 3. Ripristina nella Neural Grid (RAM)
                self._nodes[node_id] = node
                
                # 4. Re-inserisce nell'HNSW Index
                try:
                    self._hnsw.insert(node)
                except: pass
                
                # 5. Re-inserisce nei metadati DuckDB (se non sono stati già eliminati e sono irrecuperabili)
                try:
                    # Se DuckDB ha la riga ancora (magari è stato solo cancellato fisicamente l'indice), facciamo finta
                    # In realtà DuckDB non ha rollback facile, ma possiamo re-inserire metadati minimi se necessario
                    self._prefilter.add_node(node)
                except: pass
                
                print(f"♻️ [Engine] Rollback completato: Nodo {node_id[:8]} ripristinato con successo.")
                return True
        return False

    def check_integrity(self) -> List[str]:
        """
        [Fase 25: Diagnostica] Rileva archi rotti o nodi mancanti richiamati semanticamente.
        Ritorna una lista di IDs che richiedono Rollback (Self-Healing).
        """
        broken_ids = set()
        with self._lock:
            for node in self._nodes.values():
                for edge in node.edges:
                    if edge.target_id not in self._nodes:
                        # Verifica se è almeno nel tier persistente
                        if not self._tiers.get(edge.target_id):
                            broken_ids.add(edge.target_id)
        return list(broken_ids)

    def insert(self, text, metadata=None, node_id=None, collection=None):
        """
        v1.3.0: High-Fidelity Semantic Ingestion.
        """
        meta = metadata or {}
        filename = meta.get("source", "raw_input")

    def upsert_text(self, text, metadata=None, node_id=None):
        """
        v1.3.0: High-Fidelity Semantic Ingestion.
        """
        meta = metadata or {}
        filename = meta.get("source", "raw_input")
        
        # 1. Semantic Boundary Analysis
        semantic_chunks = self._get_semantic_chunks(text)
        
        if len(semantic_chunks) > 1:
            nodes = []
            for i, chunk_text in enumerate(semantic_chunks):
                cid = f"{node_id or uuid.uuid4().hex[:6]}_{i}"
                v = self._embed_text(chunk_text)
                nodes.append(VaultNode(id=cid, text=chunk_text, vector=v, metadata={**meta, "chunk_idx": i}))
            
            # Creazione sinapsi sequenziali automatiche (Narrative Chain)
            for i in range(len(nodes) - 1):
                nodes[i].edges.append(SemanticEdge(target_id=nodes[i+1].id, relation=RelationType.SEQUENTIAL))
            
            self.upsert_batch(nodes)
            
            print(f"🧠 [Kernel] Structural Ingest: Created {len(nodes)} logic nodes for {filename}.")
            return nodes[0]
            
        # 2. Fallback: Spezziamo testi lunghi se non strutturati
        if len(text) > 1000:
            paragraphs = [p.strip() for p in text.split("\n\n") if len(p.strip()) > 20]
            if len(paragraphs) > 1:
                nodes = []
                for i, p in enumerate(paragraphs[:100]):
                    p_id = f"{node_id or 'doc'}_{int(time.time()) % 1000}_{i}"
                    v = self._embed_text(p)
                    nodes.append(VaultNode(id=p_id, text=p, vector=v, metadata=meta))
                self.upsert_batch(nodes)
                return nodes[0]
        
        vector = self._embed_text(text)
        node = VaultNode(id=node_id or f"node_{uuid.uuid4().hex[:6]}", text=text, vector=vector, metadata=meta)
        self.upsert(node)
        return node

    def add_node(self, node_id, text, metadata=None):
        """Ingestione atomica con propagazione di tensione avversariale."""
        vector = self._embed_text(text)
        node = VaultNode(
            id=node_id,
            text=text,
            vector=vector,
            metadata=metadata or {},
            created_at=time.time()
        )
        if "color" not in node.metadata:
            node.metadata["color"] = "#a855f7"
        
        # Ingestione core (HNSW + Persistenza + Mesh)
        self.upsert(node)
            
        # 🧪 JANITRON LAB: Propagazione Tensione
        try:
            self.lab.propagate_tension(node_id, vector)
        except Exception:
            pass
            
        return node

    def upsert_batch(self, nodes: list[VaultNode]):
        print(f"🧠 [Kernel] Ingesting batch of {len(nodes)} nodes...")
        
        # --- BACKPRESSURE PROTOCOL (Gap #2) ---
        backpressure.wait_if_clogged()
        
        for node in nodes:
            # v1.1.0: ID Fortification
            node.id = str(node.id)
            if node.vector is None:
                node.vector = self._embed_text(node.text or "")
            
            self._nodes[node.id] = node
            if node.vector is not None:
                self._hnsw.insert(node)
                if self._tq_search:
                    self._tq_search.add(node.id, node.vector)
            
            # v1.2.0: Persistence Hardening (Atomic Log)
            self.consensus.replicate_log(op_type=1, data_summary=node.id)
            self._tiers.put(node, tier=MemoryTier.WORKING)
            
        # v14.3: Async Agent007 (Non-blocking ingestion)
        def run_agent007_tasks(node_list):
            for n in node_list:
                try:
                    is_foraging = getattr(n, 'metadata', {}).get('forage_job') is not None
                    use_fast_mode = len(node_list) > 10 or is_foraging
                    self.agent007.extract_entities(n.text, n.id, fast_mode=use_fast_mode)
                except Exception: pass

        if self.agent007:
            threading.Thread(target=run_agent007_tasks, args=(nodes,), daemon=True).start()

        print(f"✅ [Kernel] Engine now contains {len(self._nodes)} active nodes.")
        
        # v2.2.0: Active Decay Trigger (Expanded to 100k for High-Density Storage)
        if len(self._nodes) > 100000:
            self.apply_cognitive_decay(max_nodes=100000)
            
        # v1.3.0: Autonomous Synaptic Discovery Trigger
        self.discover_synapses()

        # v0.5.2: Batch Metadata Ingestion (Turbo Mode)
        meta_batch = [(n.id, self.default_collection, n.metadata) for n in nodes]
        self._prefilter.add_nodes_batch(meta_batch)

        # 🏛️ LEDGER COMMIT: Firma il batch per l'integrità Merkle-Tree
        self.ledger.commit_batch([n.id for n in nodes])

        if self.data_dir:
            self._tiers.episodic.flush()
        if nodes:
            # v0.5.6 Sliding Window Linking: Colleghiamo i nodi tra loro e con i più recenti (ULTIMI 20)
            subset = nodes + list(self._nodes.values())[-20:]
            self._graph_ingester.link_batch(subset)
            self._graph = None

        # 🛰️ MESH BROADCAST: Propaga i nuovi dati ai peer conosciuti
        # Inserito in un thread separato per non bloccare l'ingestione locale
        def _bg_broadcast():
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            for node in nodes:
                loop.run_until_complete(self.gossip.broadcast_upsert(node.to_dict()))
            loop.close()
            
        threading.Thread(target=_bg_broadcast, daemon=True).start()

    def query(self, query_text: str, **kwargs) -> list[QueryResult]:
        start_t = time.time()
        
        # v0.5.0 Cross-Modal Logic
        modality = kwargs.pop('modality', 'text')
        
        # v0.4.0 Encryption Shield Logic
        use_shield = kwargs.pop('privacy_mode', False)
        
        q_v = kwargs.pop('query_vector', None)
        if q_v is None:
            q_v = self._embed_text(query_text)
        
        # v0.5.0 latent bridge for non-text queries
        if modality != "text":
            q_v = self.bridge.align(q_v, modality)
            
        if use_shield:
            print("🛡️ [Security] Privacy Mode attivo: Cifratura query in corso...")
            q_v = self.shield.shield_vector(q_v)
            
        intent = kwargs.pop('intent', None) or self._query_planner.plan(query_text)
        results = self._query_internal(query_text, q_v, intent, **kwargs)
        
        # v0.5.0 Cognitive Scoring (Ebbinghaus Decay)
        now = time.time()
        for res in results:
            # Recupera metadati cognitivi dal prefilter
            meta = self._prefilter.con.execute(
                "SELECT last_access, access_count, importance FROM vault_metadata WHERE id = ?",
                (res.node.id,)
            ).fetchone()
            
            if meta:
                # Conversione sicura: DuckDB potrebbe restituire datetime o float
                val = meta[0]
                if hasattr(val, 'timestamp'):
                    l_acc = val.timestamp()
                elif isinstance(val, (int, float)):
                    l_acc = val
                else:
                    l_acc = time.time() # Fallback

                strength = self.cognitive.calculate_strength(l_acc, meta[2], meta[1])
                res.cognitive_score = strength
                res.memory_strength = strength
                # Applica il peso al punteggio finale (Decay by Retrieval)
                res.final_score *= (1.0 + strength)
            
            # Rinforzo Sinaptico: Il ricordo viene "toccato" perché recuperato
            self._prefilter.hit_node(res.node.id)
            res.node.touch()

        dur_ms = (time.time() - start_t) * 1000
        self.logger.log_query(intent, dur_ms, len(results))
        return sorted(results, key=lambda x: x.final_score, reverse=True)

    def get_synapse_count(self) -> int:
        """Restituisce il numero totale di sinapsi (archi) nel sistema."""
        return sum(len(node.edges) for node in self._nodes.values())

    def scan_recent(self, limit: int = 1000) -> list[tuple[VaultNode, float]]:
        """Restituisce i nodi più recenti per la telemetria 3D."""
        # Ordiniamo per data di creazione decrescente
        sorted_nodes = sorted(self._nodes.values(), key=lambda x: x.created_at, reverse=True)
        return [(n, 1.0) for n in sorted_nodes[:limit]]

    _stats_cache = {"time": 0, "data": None}

    def stats(self, limit: int = 10000) -> dict:
        """Telemetria 3D ottimizzata: campionamento, proiezione e posizionamento (v14.0 APEX)."""
        now = time.time()
        if now - self._stats_cache["time"] < 1.0 and self._stats_cache["data"]:
            return self._stats_cache["data"]

        nodes = list(self._nodes.values())
        sample_size = min(len(nodes), 10000)
        all_nodes = nodes[:sample_size]
        
        point_cloud = []
        all_edges = []
        node_positions = {}
        color_zones = {}
        next_zone_idx = 0

        # ── Campionamento Sicuro ──────────────────────────────────────────
        raw = self.scan_recent(limit=limit)
        all_nodes = [item[0] if isinstance(item, (tuple, list)) else item for item in raw]

        # ── Proiezione PCA/SVD (campionata per prestazioni) ───────────────
        nodes_with_vectors = [n for n in all_nodes if n.vector is not None]
        norm_projections = {}
        if len(nodes_with_vectors) >= 4:
            try:
                # v14.1: SVD completa su tutti i nodi con vettore (dimensione 1024 completa)
                # Sicuro perché stats() gira in run_in_executor (thread pool, non blocca l'event loop)
                vectors = np.array([n.vector for n in nodes_with_vectors], dtype=np.float32)
                v_mean = np.mean(vectors, axis=0)
                v_centered = vectors - v_mean
                _, _, vh = np.linalg.svd(v_centered, full_matrices=False)
                proj = np.dot(v_centered, vh[:3].T)
                p_min, p_max = proj.min(axis=0), proj.max(axis=0)
                rng = (p_max - p_min) + 1e-9
                normed = 2 * (proj - p_min) / rng - 1
                for i, n in enumerate(nodes_with_vectors):
                    norm_projections[n.id] = normed[i]
            except Exception as e:
                print(f"⚠️ [Stats/PCA] {e}")

        # ── Costruzione Point Cloud ───────────────────────────────────────
        for n in all_nodes:
            try:
                cluster_key = n.metadata.get("source", n.collection or "default")
                c_hash = hashlib.md5(cluster_key.encode()).hexdigest()
                r1 = int(c_hash[0:2], 16) % 200 + 55
                g1 = int(c_hash[2:4], 16) % 200 + 55
                b1 = int(c_hash[4:6], 16) % 200 + 55
                color1 = f"#{r1:02x}{g1:02x}{b1:02x}"

                if n.id in norm_projections:
                    p_vec = norm_projections[n.id]
                    node_opacity = 1.0
                    node_color = color1
                else:
                    seed = int(hashlib.md5(str(n.id).encode()).hexdigest()[:8], 16)
                    p_vec = np.random.RandomState(seed).uniform(-1, 1, 3)
                    node_opacity = 0.5
                    node_color = "#475569"

                if color1 not in color_zones:
                    # v10.0: Spherical Diffusion (50% Spacing Increase)
                    golden_ratio = (1 + 5**0.5) / 2
                    phi = 2 * np.pi * next_zone_idx / golden_ratio
                    z_pos = 1 - ((next_zone_idx % 40) / 40.0) * 2 
                    radius = max(0.01, (1 - min(1.0, z_pos * z_pos)) ** 0.5)
                    
                    # 450,000 scale (50% increase from 300,000)
                    color_zones[color1] = (
                        radius * np.cos(phi) * 450000,
                        z_pos * 450000,
                        radius * np.sin(phi) * 450000
                    )
                    next_zone_idx += 1

                # v11.6: Dynamic Scaling (Safe Range: 50,000 - 150,000)
                # Reduced from 450k to ensure the nodes don't fly past the camera far plane
                off_x, off_y, off_z = color_zones[color1]
                # v14.2: Move cluster multiplier OUTSIDE or apply only to the local copy correctly
                # Spaziatura cluster aumentata (ulteriori 400%) - 2.6 is fine if applied once
                cx, cy, cz = off_x * 2.6, off_y * 2.6, off_z * 2.6
                
                node_seed = int(hashlib.md5(str(n.id).encode()).hexdigest()[:8], 16)
                node_rng = np.random.RandomState(node_seed)
                
                r_scatter = node_rng.uniform(100000, 500000) # Scatter esteso (500%+) per evitare densità eccessiva
                p_norm = np.linalg.norm(p_vec) + 1e-6
                p_dir = p_vec / p_norm
                rand_dir = node_rng.normal(0, 1, 3)
                rand_dir /= np.linalg.norm(rand_dir) + 1e-6
                final_dir = (p_dir * 0.7 + rand_dir * 0.3)
                final_dir /= np.linalg.norm(final_dir) + 1e-6

                x = float(np.real(cx + final_dir[0] * r_scatter))
                y = float(np.real(cy + final_dir[1] * r_scatter))
                z = float(np.real(cz + final_dir[2] * r_scatter))

                # v11.6: Persist spatial metadata for agent navigation
                n.metadata['x'], n.metadata['y'], n.metadata['z'] = x, y, z

                node_positions[str(n.id)] = (x, y, z)
                point_cloud.append({
                    "id": str(n.id),
                    "x": x, "y": y, "z": z,
                    "color": node_color,
                    "opacity": node_opacity,
                    "theme": cluster_key,
                    "label": (n.text[:40] + "...") if n.text else "...",
                    "created_at": n.created_at
                })
            except Exception:
                continue

        # ── Costruzione Sinapsi (limite 500 nodi per prestazioni UI) ──────
        for n in all_nodes[:500]:
            if str(n.id) not in node_positions:
                continue
            
            # 1. Sinapsi Reali (SemanticEdges)
            for edge in (n.edges or []):
                try:
                    target_id = str(edge.target_id)
                    if target_id in node_positions:
                        all_edges.append({
                            "source": str(n.id),
                            "target": target_id,
                            "source_pos": list(node_positions[str(n.id)]),
                            "target_pos": list(node_positions[target_id]),
                            "color": "#ffffff",
                            "is_aura": False, # Link standard
                            "created_at": time.time()
                        })
                except Exception: continue

            # 2. 🌈 Super-Sinapsi Aura (Code-Doc Bridges)
            if "code_bridges" in n.metadata:
                for target_path in n.metadata["code_bridges"]:
                    # Cerchiamo se esiste un nodo che rappresenta questo file
                    # Per ora cerchiamo match parziali nell'ID o nel testo
                    for other_id, other_pos in node_positions.items():
                        if target_path in other_id or (other_id in self._nodes and target_path in self._nodes[other_id].text):
                            all_edges.append({
                                "source": str(n.id),
                                "target": other_id,
                                "source_pos": list(node_positions[str(n.id)]),
                                "target_pos": list(other_pos),
                                "color": "rainbow", # Placeholder per il frontend
                                "is_aura": True,    # IL TRIGGER PER IL RGB LED
                                "created_at": time.time()
                            })
                            break

        res = {
            "nodes_count": len(self._nodes),
            "edges_count": len(all_edges),
            "point_cloud": point_cloud,
            "edge_sample": all_edges[:1000],
        }
        self._stats_cache = {"time": now, "data": res}
        print(f"📡 [Stats v14] {len(point_cloud)} punti | {len(all_edges)} archi")
        return res


    def apply_cognitive_decay(self, max_nodes: int = 20000):
        """
        v1.2.0: Cognitive Decay Engine
        Prunes least relevant nodes to prevent active memory saturation.
        """
        if len(self._nodes) <= max_nodes: return
        
        print(f"🛡️ [Decay] Threshold reached. Pruning {len(self._nodes) - max_nodes} nodes...")
        
        # Ordiniamo per accesso recente (se implementato) o semplicemente per ordine di inserimento (FIFO fallback)
        all_ids = list(self._nodes.keys())
        to_prune = all_ids[:(len(self._nodes) - max_nodes)]
        
        for nid in to_prune:
            # Assicuriamoci che siano nel Tier persistente prima di rimuoverli dall'attivo
            node = self._nodes.pop(nid)
            self._tiers.put(node, tier=MemoryTier.EPISODIC)
            
        print(f"✅ [Decay] Memory optimized. Current active: {len(self._nodes)}")

    def discover_synapses(self, threshold: float = 0.85):
        """
        v1.3.0: Autonomous Synaptic Discovery
        Scans active nodes for latent semantic connections.
        """
        nodes = list(self._nodes.values())
        if len(nodes) < 2: return
        
        # Prendiamo gli ultimi 20 nodi per una scansione proattiva (performance optimization)
        recent = nodes[-20:]
        found_links = 0
        
        for i, node_a in enumerate(recent):
            for node_b in recent[i+1:]:
                # Evitiamo auto-link o link già esistenti
                if node_a.id == node_b.id: continue
                if any(e.target_id == node_b.id for e in node_a.edges): continue
                
                # Calcolo similarità coseno
                if node_a.vector is not None and node_b.vector is not None:
                    sim = np.dot(node_a.vector, node_b.vector) / (np.linalg.norm(node_a.vector) * np.linalg.norm(node_b.vector))
                    if sim > threshold:
                        node_a.add_edge(node_b.id, RelationType.SYNAPSE, weight=float(sim))
                        node_b.add_edge(node_a.id, RelationType.SYNAPSE, weight=float(sim))
                        found_links += 1
        
        if found_links > 0:
            print(f"🧬 [Auto-Linker] Discovered {found_links} latent synapses.")

    def _query_internal(self, query_text, query_vector, intent, **kwargs):
        k = kwargs.get('k', 10)
        ef = kwargs.get('ef', 50)
        allowed_ids = kwargs.get('filter_ids')
        if self._tq_search and not kwargs.get('use_progressive', True):
            dense_res = self._tq_search.search(query_vector, k=k*3, filter_ids=allowed_ids)
        else:
            dense_res = self._hnsw.search(query_vector, k=k*2, ef=ef)
        graph_res = []
        if intent == QueryIntent.RELATIONAL and dense_res:
            seed_ids = [r[0] for r in dense_res]
            seed_scores = {r[0]: 1.0 - r[1] for r in dense_res}
            # v3.9.5: Conversione GraphTraversalNode -> (id, score) per FusionRanker
            graph_raw = self._get_graph().expand(seed_ids, seed_scores=seed_scores, max_hops=1)
            graph_res = [(gr.node_id, gr.score) for gr in graph_raw]
        return self._ranker.fuse(dense_results=dense_res, sparse_results=[], graph_results=graph_res, nodes=self._nodes, query_text=query_text, top_k=k)

    def feedback(self, node_id: str, success: bool = True):
        node = self._nodes.get(node_id)
        if node is not None and self._tq_search is not None and node.vector is not None:
            impact = 0.15 if success else -0.10
            self._tq_search.quantizer.update_daba_resolutions(np.abs(node.vector) * impact)
            
    def _embed_text(self, text: str) -> np.ndarray:
        dtype = np.float16 if self.use_float16 else np.float32
        if self._embedder_fn: return np.array(self._embedder_fn(text), dtype=dtype)
        return np.random.randn(self.dim).astype(dtype)

    def _get_graph(self) -> ContextGraph:
        if self._graph is None: self._graph = ContextGraph(self._nodes)
        return self._graph

    def get_synapses(self) -> list[dict]:
        """Estrae l'intera topologia delle relazioni nel Vault (Fase 1)."""
        synapses = []
        for node in self._nodes.values():
            for edge in node.edges:
                if edge.target_id in self._nodes:
                    synapses.append({
                        "source": node.id,
                        "target": edge.target_id,
                        "type": "SYNAPSE",
                        "strength": edge.weight
                    })
        return synapses

    def get_projections(self) -> list[dict]:
        """Proietta i vettori 1024-dim in uno spazio 2D per i Cluster (Fase 2)."""
        projections = []
        for node in self._nodes.values():
            if node.vector is not None:
                v = node.vector
                # Lite PCA/Projection logic
                projections.append({
                    "id": str(node.id),
                    "u": float(np.sum(v[:512])),
                    "v": float(np.sum(v[512:]))
                })
        return projections

    def get_analytics_report(self) -> dict:
        """Esegue interrogazioni SQL su DuckDB per estrarre metriche reali."""
        with self._lock:
            # Calcolo hit rate reale basato sugli accessi agli ultimi 100 nodi
            try:
                res = self._prefilter.con.execute("""
                    SELECT 
                        count(*) filter (where access_count > 0) * 100.0 / count(*) as hit_rate,
                        avg(access_count) as avg_reuse
                    FROM vault_metadata
                """).fetchone()
                hit_rate = float(res[0]) if res and res[0] else 0.0
            except:
                hit_rate = 0.0

            return {
                "node_count": len(self._nodes),
                "synapse_count": self.get_synapse_count(),
                "classes": sum(1 for n in self._nodes.values() if n.metadata.get("kind") == "class"),
                "functions": sum(1 for n in self._nodes.values() if n.metadata.get("kind") == "function"),
                "hit_rate": f"{hit_rate:.2f}%",
                "active_agents": len(self.lab.agents) if hasattr(self, 'lab') else 0
            }

    def evolve_graph(self) -> int:
        """Esegue il Fact Mining accelerato tramite HNSW (O(log N))."""
        new_links = 0
        node_list = list(self._nodes.values())
        
        for node in node_list:
            if node.vector is None: continue
            
            # Ottimizzazione: Usiamo direttamente il vettore per evitare re-embedding
            candidates = self.query("", query_vector=node.vector, k=6) 
            for cand in candidates:
                if cand.node.id == node.id: continue
                # Se la similarità è molto alta (sopra 0.88) e non c'è già un arco
                if cand.final_score > 0.88:
                    if not any(e.target_id == cand.node.id for e in node.edges):
                        # Creazione sinapsi bidirezionale
                        node.add_edge(cand.node.id, RelationType.SYNAPSE, weight=float(cand.final_score))
                        cand.node.add_edge(node.id, RelationType.SYNAPSE, weight=float(cand.final_score))
                        new_links += 1
        return new_links

    def purge_all(self):
        """Cancella ogni traccia dal disco e dalla memoria (v6.0: Protocollo VETRO Hardened)."""
        self.logger.info("☣️ NUCLEAR PURGE INITIATED. Protocollo VETRO active.")
        
        # 1. Clear Memory State
        self._nodes.clear()
        self._hnsw = AdaptiveHNSW(dim=self.dim)
        
        # 2. Force Close All Potential Resource Handles (DuckDB, Agent007, etc.)
        import shutil, time, os, signal
        
        print("☣️ Terminating background agents and closing DB locks...")
        try:
            # Chiude pre-filter (DuckDB)
            if self._prefilter:
                try: self._prefilter.con.close()
                except: pass
            
            # Chiude Agent007 (SQLAlchemy/DuckDB)
            if hasattr(self, 'agent007'):
                try: self.agent007.close()
                except: pass
                
            # Chiude Tiers (HNSW Index points)
            if self._tiers:
                try: self._tiers.close()
                except: pass
            
            # Pausa critica per rilascio kernel-level dei file
            time.sleep(1.0)
        except Exception as e:
            print(f"⚠️ Warning durante shutdown risorse: {e}")

        # 3. Scorched Earth Deletion (Multi-tier)
        if self.data_dir and os.path.exists(self.data_dir):
            try:
                # Tentativo 1: Standard Python
                shutil.rmtree(self.data_dir, ignore_errors=False)
            except Exception as e:
                print(f"⚠️ Shutil fail: {e}. Falling back to OS-level purge...")
                try:
                    # Tentativo 2: Forza bruta via sistema (Mac/Linux)
                    os.system(f"rm -rf \"{self.data_dir}\"")
                except:
                    pass
            
            # 4. Re-stabilizzazione struttura
            try:
                os.makedirs(self.data_dir, exist_ok=True)
                os.makedirs(os.path.join(self.data_dir, "media"), exist_ok=True)
                print("✅ [VETRO] Neural Vault structure re-initialized to ZERO.")
            except:
                pass
        
        print("☢️ TABULA RASA: Engine stabilized.")
        # Reinizializziamo i componenti persistenti
        from retrieval.prefilter import DuckDBPrefilter
        from memory_tiers import MemoryTierManager
        from agent007_intelligence import Agent007Intelligence
        
        self._prefilter = DuckDBPrefilter(db_path=self.data_dir)
        self._tiers = MemoryTierManager(data_dir=self.data_dir)
        self.agent007 = Agent007Intelligence(db_path=str(self.data_dir / "agent007.db"), engine=self)
        
        # Re-init consensus con nuova directory pulita
        from network.consensus import SovereignConsensus
        self.consensus = SovereignConsensus(
            node_id=f"vault_reset_{uuid.uuid4().hex[:4]}",
            data_dir=str(self.data_dir / "consensus")
        )
            
        self.logger.info("✅ Vault is now a Tabula Rasa. Ready for new consciousness.")

    def remove_node(self, node_id: str):
        """Rimuove un nodo dal sistema e ricalcola le dipendenze (Fase 6)."""
        if node_id in self._nodes:
            # 1. Rimozione dalla memoria attiva
            node = self._nodes.pop(node_id)
            # 2. Rimozione dall'indice vettoriale
            self._hnsw.remove(node_id)
            # 3. Rimozione dalla persistenza (Cold Tier)
            self._tiers.remove(node_id)
            # 4. Rimozione dal prefiltro metadata
            self._prefilter.remove_node(node_id)
            
            self.logger.info(f"Neural Pruning: Node {node_id} removed from the grid.")
            return True
        return False

    def close(self):
        # [Fase 16 Hardening]: Proper Shutdown
        if hasattr(self, 'decay_daemon'): self.decay_daemon.stop()
        if hasattr(self, 'consensus') and self.consensus: self.consensus.close()
        if self._sessions: self._sessions.close()
        if self._prefilter: self._prefilter.close()
        if self._tiers: self._tiers.close()
        if hasattr(self, 'agent007') and self.agent007: self.agent007.close()
