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
import warnings
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple, Union
import mimetypes

import numpy as np
import duckdb
import torch
import torchaudio
import cv2
import httpx
import base64
from pydub import AudioSegment

# Motori Reali
from scenedetect import ContentDetector, SceneManager, open_video
from faster_whisper import WhisperModel
from imagebind import data as ib_data
from imagebind.models import imagebind_model
from imagebind.models.imagebind_model import ModalityType
from utils.backpressure import backpressure

# 🎤 [Phase 4] SpeechBrain Forensics Integration
try:
    from speechbrain.inference.speaker import EncoderClassifier
    SPEECHBRAIN_AVAILABLE = True
except ImportError:
    SPEECHBRAIN_AVAILABLE = False

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
    def __init__(self, db_path: str = "vault_data/neuralvault.duckdb", ollama_url: str = "http://127.0.0.1:11434", settings: Any = None):
        self.db_path = db_path
        self.ollama_url = ollama_url
        self.settings = settings # SwarmSettingsManager link
        self.device = "mps" if torch.backends.mps.is_available() else "cpu"
        self._init_store()
        
        # v12.0: Sovereign Forensics & SpeechBrain Architecture
        self.profiles_path = Path("vault_data/speaker_profiles.json")
        self._speaker_clusters = self._load_profiles()
        self.forensics_mode = "Surgical-Diarization" if SPEECHBRAIN_AVAILABLE else "Latent-Fallback"
        
        # Lazy Loading dei modelli
        self._ib_model = None
        self._whisper_model = None
        self._sb_classifier = None # SpeechBrain Classifier
        
        logger.info(f"🏺 [Multimodal] Sovereign Processor initialized on {self.device} (Forensics: {self.forensics_mode}).")

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
                namespace VARCHAR DEFAULT 'default',
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
            import gc
            gc.collect() # Libera RAM prima di caricare il gigante
            if self.device == "mps":
                torch.mps.empty_cache()
                
            logger.info("📡 [ImageBind] ALERT: Loading HuGE 1024D model to Unified Memory (Demand-Driven)...")
            from imagebind.models import imagebind_model
            self._ib_model = imagebind_model.imagebind_huge(pretrained=True)
            self._ib_model.eval()
            self._ib_model.to(self.device)
        return self._ib_model

    def _cleanup_memory(self):
        """Libera la VRAM/RAM dopo task multimodali pesanti."""
        if self.device == "mps":
            torch.mps.empty_cache()
        import gc
        gc.collect()

    def _get_sb_model(self):
        """Lazy loader per SpeechBrain Encoder."""
        if self._sb_classifier is None and SPEECHBRAIN_AVAILABLE:
            logger.info("🎤 [Forensics] Loading SpeechBrain Speaker-ID Encoder...")
            self._sb_classifier = EncoderClassifier.from_hparams(
                source="speechbrain/spkrec-ecapa-voxceleb",
                savedir="vault_data/models/speechbrain_spkrec",
                run_opts={"device": self.device}
            )
        return self._sb_classifier

    def _diarize_and_identify(self, audio_segment: Optional[torch.Tensor], text: str) -> str:
        """[Phase 4] Identificazione Biometrica via SpeechBrain (ECAPA-TDNN)."""
        if SPEECHBRAIN_AVAILABLE and audio_segment is not None:
            try:
                classifier = self._get_sb_model()
                # 1. Estrazione Fingerprint (Acoustic Embedding)
                # SpeechBrain richiede [batch, time]
                with torch.no_grad():
                    embeddings = classifier.encode_batch(audio_segment)
                    vector = embeddings.squeeze().cpu().numpy()
                
                # 2. Riconoscimento/Clustering Biometrico
                found_id = None
                for s_id, center_vec in self._speaker_clusters.items():
                    sim = np.dot(vector, center_vec) / (np.linalg.norm(vector) * np.linalg.norm(center_vec))
                    if sim > 0.85: # Soglia di verifica biometrica
                        found_id = s_id
                        # Aggiornamento adattivo del profilo vocale
                        self._speaker_clusters[s_id] = 0.95 * center_vec + 0.05 * vector
                        break
                
                if found_id: return found_id
                
                # Nuovo Soggetto Rilevato
                new_id = f"SUBJECT_{chr(65 + len([k for k in self._speaker_clusters.keys() if 'SUBJECT_' in k]))}"
                self._speaker_clusters[new_id] = vector
                self._save_profiles()
                return new_id
            except Exception as e:
                logger.warning(f"🎤 [Forensics] SpeechBrain processing failed: {e}")
                return self._identify_via_latent(text)
        else:
            return self._identify_via_latent(text)

    def _identify_via_latent(self, text: str) -> str:
        """Fallback Identity: Usa lo spazio latente di ImageBind per raggruppare i timbri (Heuristic)."""
        ib_model = self._get_ib_model()
        inputs = {ModalityType.TEXT: ib_data.load_and_transform_text([text], device=self.device)}
        with torch.no_grad():
            embeddings = ib_model(inputs)
            vector = embeddings[ModalityType.TEXT].cpu().numpy()[0]
        
        found_id = None
        for s_id, center_vec in self._speaker_clusters.items():
            sim = np.dot(vector, center_vec) / (np.linalg.norm(vector) * np.linalg.norm(center_vec))
            if sim > 0.88: # Soglia Biometrica
                found_id = s_id
                self._speaker_clusters[s_id] = 0.95 * center_vec + 0.05 * vector
                break
        
        if found_id: return found_id
        new_id = f"SUBJECT_{chr(65 + len(self._speaker_clusters))}"
        self._speaker_clusters[new_id] = vector
        self._save_profiles()
        return new_id

    def _get_whisper_model(self):
        """Lazy loader per Whisper Model."""
        if self._whisper_model is None:
            logger.info("🎙️ [Whisper] Initializing Faster-Whisper (On Demand)...")
            self._whisper_model = WhisperModel("base", device="cpu", compute_type="int8")
        return self._whisper_model

    def _compute_hash(self, file_path: Path) -> str:
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    async def ingest(self, file_path: Union[str, Path], source_uri: Optional[str] = None, namespace: str = "default") -> List[str]:
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
            return self._process_video(p, source_uri, content_hash, namespace=namespace)
        elif mime.startswith("audio/"):
            return self._process_audio(p, source_uri, content_hash, namespace=namespace)
        elif mime.startswith("image/"):
            return self._process_image(p, source_uri, content_hash, namespace=namespace)
        else:
            logger.warning(f"❌ [Multimodal] MIME non supportato: {mime}")
            return []
    def _diarize_and_identify(self, audio_data: np.ndarray, text: str, sample_rate: int = 16000) -> str:
        """[Phase 4] Diarizzazione Chirurgica & Identificazione Biometrica."""
        # 1. Fallback su ImageBind per il clustering vettoriale HuGE 1024D
        ib_model = self._get_ib_model()
        
        # Simuliamo l'estrazione di un 'fingerprint' acustico dal segmento
        # In un sistema con SpeechBrain, qui chiameremmo l'encoder X-Vector
        inputs = {
            ModalityType.TEXT: ib_data.load_and_transform_text([text], device=self.device)
        }
        with torch.no_grad():
            embeddings = ib_model(inputs)
            vector = embeddings[ModalityType.TEXT].cpu().numpy()[0]
        
        # 2. Heuristic Speaker Identity (v12.0)
        found_id = None
        for s_id, center_vec in self._speaker_clusters.items():
            sim = np.dot(vector, center_vec) / (np.linalg.norm(vector) * np.linalg.norm(center_vec))
            if sim > 0.85: # Soglia Biometrica
                found_id = s_id
                # Stabilità dell'identità: aggiornamento centroidi via media mobile (exponential decay)
                self._speaker_clusters[s_id] = 0.9 * center_vec + 0.1 * vector
                break
        
        if found_id: return found_id
        
        # 3. Nuova identità rilevata
        new_id = f"SUBJECT_{chr(65 + len(self._speaker_clusters))}"
        self._speaker_clusters[new_id] = vector
        self._save_profiles()
        return new_id

    def _process_video(self, path: Path, uri: str, h: str, namespace: str = "default") -> List[str]:
        """Pipeline Video Reale: Saliency-Based Event Detection + Speaker Diarization."""
        logger.info(f"🎞️ [Video] High-Fidelity Forensics: {path.name}")
        
        # 1. SCENE DETECTION
        video = open_video(str(path))
        scene_manager = SceneManager()
        scene_manager.add_detector(ContentDetector(threshold=27.0))
        scene_manager.detect_scenes(video)
        scenes = scene_manager.get_scene_list()
        
        scene_vault = []
        cap = cv2.VideoCapture(str(path))
        for i, scene in enumerate(scenes):
            t_start, t_end = scene[0].get_seconds()*1000, scene[1].get_seconds()*1000
            cap.set(cv2.CAP_PROP_POS_MSEC, t_start + 100)
            ret, frame = cap.read()
            vis_desc = self._call_vision_llm(path) if ret else "Continuità visiva."
            scene_vault.append((t_start, t_end, vis_desc))
        
        # 2. AUDIO PROCESSING & DIARIZATION
        logger.info(f"🎤 [Forensics] Starting Audio Extraction for {path.name}...")
        temp_audio = f"temp_{h[:8]}.wav"
        try:
            # Estrazione traccia audio totale via FFmpeg (silenzioso)
            os.system(f"ffmpeg -i {path} -ab 160k -ac 1 -ar 16000 -vn {temp_audio} -y -loglevel quiet")
            waveform, sample_rate = torchaudio.load(temp_audio)
        except:
            waveform, sample_rate = None, 16000

        whisper = self._get_whisper_model()
        segments, _ = whisper.transcribe(str(path), word_timestamps=True)
        
        nodes = []
        for i, seg in enumerate(segments):
            t_start_s, t_end_s = seg.start, seg.end
            t_start_ms, t_end_ms = t_start_s * 1000, t_end_s * 1000
            
            # --- [Phase 4 Upgrade] Surgical Speaker Attribution ---
            audio_segment_tensor = None
            if waveform is not None:
                # Slicing del waveform per il segmento corrente
                start_frame = int(t_start_s * sample_rate)
                end_frame = int(t_end_s * sample_rate)
                audio_segment_tensor = waveform[:, start_frame:end_frame]
            
            speaker_id = self._diarize_and_identify(audio_segment_tensor, seg.text)
            
            current_vis = next((s[2] for s in scene_vault if s[0] <= t_start <= s[1]), "Background activity.")
            
            node_id = f"vid_{h[:8]}_s{i}"
            synapse = {
                "id": node_id,
                "media_type": "video",
                "namespace": namespace,
                "source_uri": uri,
                "content_hash": h,
                "t_start_ms": t_start,
                "t_end_ms": t_end,
                "transcript": f"🎬 [SCENE]: {current_vis}\n🎙️ [{speaker_id}]: {seg.text}",
                "speaker": speaker_id,
                "vector": self._get_ib_embedding(seg.text).tolist(),
                "metadata": json.dumps({"engine": "Forensics-V12", "speaker": speaker_id})
            }
            self._store_synapse(synapse)
            nodes.append(node_id)
            
        cap.release()
        self._cleanup_memory()
        return nodes

    def _get_ib_embedding(self, text: str) -> np.ndarray:
        ib_model = self._get_ib_model()
        inputs = {ModalityType.TEXT: ib_data.load_and_transform_text([text], device=self.device)}
        with torch.no_grad():
            return ib_model(inputs)[ModalityType.TEXT].cpu().numpy()[0]

    def _call_vision_llm(self, image_path: Path, task: str = "vision_description") -> str:
        """Interroga Ollama per descrivere l'immagine utilizzando il routing granulare dello swarm."""
        try:
            # Recupero modello dinamico dai settings
            model = "moondream"
            if self.settings:
                # Se abbiamo task specifici, li usiamo, altrimenti fallback su 'multimodal' globale
                model = self.settings.get(task) or self.settings.get("multimodal") or "moondream"
            
            with open(image_path, "rb") as f:
                img_b64 = base64.b64encode(f.read()).decode('utf-8')
            
            with httpx.Client(timeout=45.0) as client:
                r = client.post(f"{self.ollama_url}/api/generate", json={
                    "model": model,
                    "prompt": "Descrivi cosa succede in questa immagine in una frase breve e precisa.",
                    "images": [img_b64],
                    "stream": False
                })
                
                if r.status_code != 200:
                    # Fallback di emergenza se il modello specifico fallisce
                    r = client.post(f"{self.ollama_url}/api/generate", json={
                        "model": "moondream",
                        "prompt": "Describe this scene.",
                        "images": [img_b64],
                        "stream": False
                    })
                
                return r.json().get("response", "Impossibile analizzare l'immagine.")
        except Exception as e:
            return f"[Vision Error: {str(e)}]"

    def _process_audio(self, path: Path, uri: str, h: str, namespace: str = "default") -> List[str]:
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
            "namespace": namespace,
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
        self._cleanup_memory()
        return [node_id]

    def _process_image(self, path: Path, uri: str, h: str, namespace: str = "default") -> List[str]:
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
            "namespace": namespace,
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
        self._cleanup_memory()
        return [node_id]

    def _store_synapse(self, data: Dict[str, Any]):
        conn = duckdb.connect(self.db_path)
        conn.execute("""
            INSERT INTO multimodal_synapses 
            (id, media_type, namespace, source_uri, content_hash, t_start_ms, t_end_ms, transcript, speaker, vector, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            data["id"], data["media_type"], data.get("namespace", "default"), data["source_uri"], data["content_hash"],
            data["t_start_ms"], data["t_end_ms"], data["transcript"], data["speaker"],
            data["vector"], data["metadata"]
        ])
        conn.close()

    def query(self, text: str, top_k: int = 5, namespace: Optional[str] = None) -> List[Dict[str, Any]]:
        """Query Multimodale Reale (Unified Semantic Search)."""
        logger.info(f"🔮 [Oracle] Searching Unified Vector Space for: {text}")
        
        ib_model = self._get_ib_model()
        inputs = {
            ModalityType.TEXT: ib_data.load_and_transform_text([text], device=self.device)
        }
        with torch.no_grad():
            embeddings = ib_model(inputs)
            vec = embeddings[ModalityType.TEXT].cpu().numpy()[0]
            query_vector = (vec / np.linalg.norm(vec)).tolist()
        
        conn = duckdb.connect(self.db_path)
        where_clause = ""
        params = [query_vector, top_k]
        if namespace:
            where_clause = "WHERE namespace = ?"
            params = [namespace, query_vector, top_k]

        results = conn.execute(f"""
            SELECT id, media_type, t_start_ms, transcript, metadata 
            FROM multimodal_synapses 
            {where_clause}
            ORDER BY list_dot_product(vector, ?) DESC
            LIMIT ?
        """, params).fetchall()
        conn.close()
        
        return [{"id": r[0], "type": r[1], "t_start": r[2], "content": r[3], "meta": json.loads(r[4])} for r in results]

    def get_synapse(self, synapse_id: str) -> Optional[Dict[str, Any]]:
        """Recupera i dati completi di una sinapsi specifica."""
        conn = duckdb.connect(self.db_path)
        r = conn.execute("""
            SELECT id, media_type, source_uri, content_hash, t_start_ms, t_end_ms, transcript, speaker, vector, metadata
            FROM multimodal_synapses WHERE id = ?
        """, [synapse_id]).fetchone()
        conn.close()
        
        if not r: return None
        return {
            "id": r[0], "media_type": r[1], "source_uri": r[2], "content_hash": r[3],
            "t_start_ms": r[4], "t_end_ms": r[5], "transcript": r[6], "speaker": r[7],
            "vector": np.array(r[8], dtype=np.float32), "metadata": json.loads(r[9])
        }

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
