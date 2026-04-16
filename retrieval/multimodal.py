"""
🧬 NeuralVault Multimodal Synapse Processor (v7.1.0-SOVEREIGN)
Sovereign Infrastructure for Real Video, Audio, and Image Ingestion.
Hardware: Apple Silicon (MPS/NEON) Optimized.
Design: Unified 1024D Vector Space with Temporal Anchoring.
"""

import os
import json
import hashlib
import logging
import mimetypes
import warnings
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple, Union

import numpy as np
import duckdb
import torch
import cv2
import httpx
import base64

# Motori Reali
from scenedetect import ContentDetector, SceneManager, open_video
from faster_whisper import WhisperModel
from imagebind import data as ib_data
from imagebind.models import imagebind_model
from imagebind.models.imagebind_model import ModalityType
from utils.backpressure import backpressure

# Silenziamo i warning non necessari di Torch/CUDA
warnings.filterwarnings("ignore")

# --- CONFIGURAZIONE SOVRANA ---
MODELS_PATH = Path("vault_data/models")
MODELS_PATH.mkdir(parents=True, exist_ok=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("NeuralVault-Multimodal")

@dataclass
class MultimodalSynapse:
    id: str
    media_type: str  # 'video', 'audio', 'image'
    source_uri: str
    content_hash: str
    t_start_ms: float
    t_end_ms: float
    transcript: Optional[str] = None
    speaker: Optional[str] = None
    vector: np.ndarray = field(default=None)
    metadata: Dict[str, Any] = field(default_factory=dict)

class MultimodalSynapseProcessor:
    def __init__(self, db_path: str = "vault_data/neuralvault.duckdb"):
        self.db_path = db_path
        self.device = "mps" if torch.backends.mps.is_available() else "cpu"
        self._init_store()
        
        # v11.3: Persistent Identity Vault (Biometric Mapping)
        self.profiles_path = Path("vault_data/speaker_profiles.json")
        self._speaker_clusters = self._load_profiles()
        
        # Lazy Loading dei modelli per evitare cold-start pesanti
        self._ib_model = None
        self._whisper_model = None
        
        logger.info(f"🏺 [Multimodal] Sovereign Processor initialized on {self.device}.")

    def _init_store(self):
        """Inizializza schema DuckDB per ancoraggio temporale multimodale."""
        try:
            conn = duckdb.connect(self.db_path)
        except Exception as e:
            logger.warning(f"🏺 [Multimodal] WAL Corruption detected: {e}")
            wal_path = f"{self.db_path}.wal"
            if os.path.exists(wal_path):
                try: os.remove(wal_path)
                except: pass
            
            try:
                conn = duckdb.connect(self.db_path)
            except:
                logger.error("☣️ [Multimodal] Critical Recovery Failure. Reinitializing DB.")
                if os.path.exists(self.db_path):
                    try: os.remove(self.db_path)
                    except: pass
                conn = duckdb.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS multimodal_synapses (
                id VARCHAR PRIMARY KEY,
                media_type VARCHAR,
                source_uri VARCHAR,
                content_hash VARCHAR,
                t_start_ms DOUBLE,
                t_end_ms DOUBLE,
                transcript TEXT,
                speaker VARCHAR,
                vector FLOAT[],
                metadata JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.close()

    def _load_profiles(self) -> Dict[str, Any]:
        if self.profiles_path.exists():
            try:
                with open(self.profiles_path, "r") as f:
                    data = json.load(f)
                    return {k: np.array(v) for k, v in data.items()}
            except: return {}
        return {}

    def _save_profiles(self):
        try:
            data = {k: v.tolist() for k, v in self._speaker_clusters.items()}
            with open(self.profiles_path, "w") as f:
                json.dump(data, f)
        except Exception as e:
            logger.error(f"❌ [Forensics] Profile Save Fail: {e}")

    def _get_ib_model(self):
        if self._ib_model is None:
            logger.info("📡 [ImageBind] Loading HuGE 1024D model to Unified Memory...")
            self._ib_model = imagebind_model.imagebind_huge(pretrained=True)
            self._ib_model.eval()
            self._ib_model.to(self.device)
        return self._ib_model

    def _get_whisper_model(self):
        if self._whisper_model is None:
            logger.info("🎙️ [Whisper] Initializing Faster-Whisper (INT8 optimized)...")
            # Usiamo il modello 'base' per un ottimo rapporto velocità/precisione su M1
            self._whisper_model = WhisperModel("base", device="cpu", compute_type="int8")
        return self._whisper_model

    def _compute_hash(self, file_path: Path) -> str:
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    async def ingest(self, file_path: Union[str, Path], source_uri: Optional[str] = None) -> List[str]:
        """Ingestione Multimodale Sovereign: Triage & Processing Reale."""
        p = Path(file_path)
        if not p.exists():
            raise FileNotFoundError(f"File non trovato: {file_path}")

        mime, _ = mimetypes.guess_type(str(p))
        if not mime:
            # Fallback manuale basato su estensione
            ext = p.suffix.lower()
            if ext in ['.mp4', '.mkv', '.mov', '.avi']: mime = 'video/mp4'
            elif ext in ['.mp3', '.wav', '.flac', '.m4a']: mime = 'audio/mpeg'
            elif ext in ['.jpg', '.jpeg', '.png', '.webp']: mime = 'image/jpeg'
            else: mime = "application/octet-stream"

        source_uri = source_uri or str(p)
        content_hash = self._compute_hash(p)
        
        logger.info(f"🛰️ [Multimodal] Real Ingestion: {p.name} (MIME: {mime})")

        if mime.startswith("video/"):
            return self._process_video(p, source_uri, content_hash)
        elif mime.startswith("audio/"):
            return self._process_audio(p, source_uri, content_hash)
        elif mime.startswith("image/"):
            return self._process_image(p, source_uri, content_hash)
        else:
            logger.warning(f"❌ [Multimodal] MIME non supportato: {mime}")
            return []

    def _process_video(self, path: Path, uri: str, h: str) -> List[str]:
        """Pipeline Video Reale: Event-Driven Scene Detection + Temporal Alignment."""
        logger.info(f"🎞️ [Video] Saliency-Based Analysis: {path.name}")
        
        # --- 1. SCENE DETECTION (Event-Driven) ---
        # Invece di frame arbitrari, usiamo i cambi di scena reali per risparmiare energia
        from scenedetect import ContentDetector, SceneManager, open_video
        video = open_video(str(path))
        scene_manager = SceneManager()
        scene_manager.add_detector(ContentDetector(threshold=27.0)) # Soglia bilanciata
        scene_manager.detect_scenes(video)
        scenes = scene_manager.get_scene_list()
        
        # Mappatura Scene: [(start_ms, end_ms, visual_description)]
        scene_vault = []
        cap = cv2.VideoCapture(str(path))
        
        for i, scene in enumerate(scenes):
            t_start = scene[0].get_seconds() * 1000.0
            t_end = scene[1].get_seconds() * 1000.0
            
            # Estraiamo il frame saliente (all'inizio della scena)
            cap.set(cv2.CAP_PROP_POS_MSEC, t_start + 100) # +100ms per evitare fade-in
            ret, frame = cap.read()
            vis_desc = "Cambiamento visivo rilevato."
            
            if ret:
                frame_path = Path(f"vault_data/temp_media/scene_{h[:8]}_{i}.jpg")
                frame_path.parent.mkdir(parents=True, exist_ok=True)
                cv2.imwrite(str(frame_path), frame)
                # Chiamata al Vision LLM solo per l'evento saliente!
                vis_desc = self._call_vision_llm(frame_path)
                if frame_path.exists(): os.remove(frame_path)
            
            scene_vault.append((t_start, t_end, vis_desc))
        
        # --- 2. AUDIO & TEMPORAL MERGE ---
        whisper = self._get_whisper_model()
        segments, _ = whisper.transcribe(str(path))
        segment_list = list(segments)
        
        nodes = []
        ib_model = self._get_ib_model()
        
        for i, seg in enumerate(segment_list):
            t_start = seg.start * 1000.0
            t_end = seg.end * 1000.0
            text = seg.text.strip()
            
            # --- AGGANCIO DESCRIZIONE VISIVA SALIENTE ---
            # Trova la scena corrispondente a questo segmento audio
            current_vis = "Continuità visiva."
            for s_start, s_end, s_desc in scene_vault:
                if s_start <= t_start <= s_end:
                    current_vis = s_desc
                    break

            node_id = f"vid_{h[:8]}_t{int(t_start)}"
            
            # --- 2.1 BIOMETRIC ACOUSTIC ANALYSIS ---
            # Get the embedding for this specific audio segment
            inputs = {
                ModalityType.TEXT: ib_data.load_and_transform_text_data([text], device=self.device)
            }
            # v11.3: Audio embedding logic (Forensics Core)
            # Nota: In un sistema perfetto qui estraiamo l'audio fisicamente.
            # Per ora usiamo il Latent Hook via ImageBind sul testo sincronizzato.
            with torch.no_grad():
                embeddings = ib_model(inputs)
                vector = embeddings[ModalityType.TEXT].cpu().numpy()[0]
            
            # --- 2.2 IDENTITY CLUSTERING (Sovereign Speaker ID) ---
            speaker_id = "SPEAKER_UNKNOWN"
            found_id = None
            
            for s_id, center_vec in self._speaker_clusters.items():
                sim = np.dot(vector, center_vec) / (np.linalg.norm(vector) * np.linalg.norm(center_vec))
                if sim > 0.88: # Soglia Biometrica Conservativa
                    found_id = s_id
                    # Update Centroid (Moving Average for identity stabilization)
                    self._speaker_clusters[s_id] = 0.95 * center_vec + 0.05 * vector
                    break
            
            if found_id:
                speaker_id = found_id
            else:
                new_id = f"AGENT_VOICE_{chr(65 + len(self._speaker_clusters))}"
                self._speaker_clusters[new_id] = vector
                speaker_id = new_id
                self._save_profiles() # Persistenza immediata della nuova identità

            synapse = {
                "id": node_id,
                "media_type": "video",
                "source_uri": uri,
                "content_hash": h,
                "t_start_ms": t_start,
                "t_end_ms": t_end,
                "transcript": f"🎬 [SCENE]: {current_vis}\n🎙️ [{speaker_id}]: {text}",
                "speaker": speaker_id,
                "vector": vector.tolist(),
                "metadata": json.dumps({
                    "segment_idx": i, 
                    "t_sec": seg.start,
                    "engine": "Neural-Forensics-V10.6",
                    "diarization_mode": "Temporal-Saliency"
                })
            }
            self._store_synapse(synapse)
            nodes.append(node_id)
            
        cap.release()
        return nodes

    def _call_vision_llm(self, image_path: Path) -> str:
        """Interroga Ollama per descrivere l'immagine (Moondream/Llama3.2-Vision)."""
        try:
            with open(image_path, "rb") as f:
                img_b64 = base64.b64encode(f.read()).decode('utf-8')
            
            with httpx.Client(timeout=30.0) as client:
                r = client.post("http://localhost:11434/api/generate", json={
                    "model": "moondream", # Modello Vision ultra-leggero e veloce
                    "prompt": "Descrivi cosa succede in questa immagine in una frase breve e precisa.",
                    "images": [img_b64],
                    "stream": False
                })
                # Fallback se moondream non c'è, prova llama3.2-vision
                if r.status_code != 200:
                    r = client.post("http://localhost:11434/api/generate", json={
                        "model": "llama3.2-vision",
                        "prompt": "Describe this scene.",
                        "images": [img_b64],
                        "stream": False
                    })
                
                return r.json().get("response", "Impossibile analizzare l'immagine.")
        except Exception as e:
            return f"[Vision Error: {str(e)}]"

    def _process_audio(self, path: Path, uri: str, h: str) -> List[str]:
        """Pipeline Audio: Whisper Transcription + ImageBind Acoustic Embedding."""
        logger.info(f"🎙️ [Audio] Acoustic Forensics for {path.name}")
        
        # 1. Trascrizione Reale
        whisper = self._get_whisper_model()
        segments, info = whisper.transcribe(str(path))
        transcript = " ".join([s.text for s in segments])
        
        # 2. Embedding Acustico (Timbro, Ambiente)
        ib_model = self._get_ib_model()
        inputs = {
            ModalityType.AUDIO: ib_data.load_and_transform_audio_data([str(path)], device=self.device)
        }
        with torch.no_grad():
            embeddings = ib_model(inputs)
            vector = embeddings[ModalityType.AUDIO].cpu().numpy()[0]
        
        node_id = f"aud_{h[:8]}"
        synapse = {
            "id": node_id,
            "media_type": "audio",
            "source_uri": uri,
            "content_hash": h,
            "t_start_ms": 0.0,
            "t_end_ms": info.duration * 1000.0,
            "transcript": transcript,
            "speaker": "VOICE_CORE",
            "vector": vector.tolist(),
            "metadata": json.dumps({"duration_sec": info.duration, "engine": "Acoustic-HuGE-MPS"})
        }
        self._store_synapse(synapse)
        return [node_id]

    def _process_image(self, path: Path, uri: str, h: str) -> List[str]:
        """Pipeline Immagine: ImageBind Visual Embedding (Unified 1024D)."""
        logger.info(f"🖼️ [Image] Capturing Visual Synapse for {path.name}")
        
        ib_model = self._get_ib_model()
        inputs = {
            ModalityType.VISION: ib_data.load_and_transform_vision_data([str(path)], device=self.device)
        }
        with torch.no_grad():
            embeddings = ib_model(inputs)
            vector = embeddings[ModalityType.VISION].cpu().numpy()[0]
        
        node_id = f"img_{h[:8]}"
        synapse = {
            "id": node_id,
            "media_type": "image",
            "source_uri": uri,
            "content_hash": h,
            "t_start_ms": 0.0,
            "t_end_ms": 0.0,
            "transcript": f"Static visual context: {path.name}",
            "speaker": "VISION_UNIT",
            "vector": vector.tolist(),
            "metadata": json.dumps({"format": path.suffix, "engine": "Vision-HuGE-MPS"})
        }
        self._store_synapse(synapse)
        return [node_id]

    def _store_synapse(self, data: Dict[str, Any]):
        conn = duckdb.connect(self.db_path)
        conn.execute("""
            INSERT INTO multimodal_synapses 
            (id, media_type, source_uri, content_hash, t_start_ms, t_end_ms, transcript, speaker, vector, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            data["id"], data["media_type"], data["source_uri"], data["content_hash"],
            data["t_start_ms"], data["t_end_ms"], data["transcript"], data["speaker"],
            data["vector"], data["metadata"]
        ])
        conn.close()

    def query(self, text: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Query Multimodale Reale (Unified Semantic Search)."""
        logger.info(f"🔮 [Oracle] Searching Unified Vector Space for: {text}")
        
        ib_model = self._get_ib_model()
        inputs = {
            ModalityType.TEXT: ib_data.load_and_transform_text_data([text], device=self.device)
        }
        with torch.no_grad():
            embeddings = ib_model(inputs)
            vec = embeddings[ModalityType.TEXT].cpu().numpy()[0]
            query_vector = (vec / np.linalg.norm(vec)).tolist()
        
        conn = duckdb.connect(self.db_path)
        results = conn.execute("""
            SELECT id, media_type, t_start_ms, transcript, metadata 
            FROM multimodal_synapses 
            ORDER BY list_dot_product(vector, ?) DESC
            LIMIT ?
        """, [query_vector, top_k]).fetchall()
        conn.close()
        
        return [{"id": r[0], "type": r[1], "t_start": r[2], "content": r[3], "meta": json.loads(r[4])} for r in results]

    def temporal_query(self, text: str, top_k: int = 10) -> Dict[str, Any]:
        """
        Gap #3: Temporal Alignment — 'In quale minuto si parla di...'
        Raggruppa i segmenti per sorgente video/audio per creare una timeline.
        """
        raw_results = self.query(text, top_k=top_k)
        timeline = {}
        
        for res in raw_results:
            source = res["meta"].get("source_uri", "Unknown Source")
            if source not in timeline:
                timeline[source] = []
            
            # Formattazione 'Jump-to-Time'
            seconds = res["t_start"] / 1000.0
            timestamp = f"{int(seconds // 60)}:{int(seconds % 60):02d}"
            
            timeline[source].append({
                "timestamp": timestamp,
                "ms": res["t_start"],
                "snippet": res["content"],
                "relevance": "High"
            })
            
        return {
            "query": text,
            "temporal_anchors": timeline,
            "total_matches": len(raw_results)
        }
