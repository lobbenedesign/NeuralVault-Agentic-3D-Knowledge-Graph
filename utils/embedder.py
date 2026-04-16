"""
neuralvault.utils.embedder
──────────────────────────
Embedder Factory di NeuralVault.
Gestisce modelli locali e remoti per testo e immagini (CLIP/DinoV2).
"""

from __future__ import annotations
import numpy as np
from typing import Callable, Any, List, Union
import os

class EmbedderFactory:
    """
    Factory per creare embedder per diversi tipi di dati.
    """
    
    @staticmethod
    def text_bge_m3() -> Callable[[str], np.ndarray]:
        """BAAI/bge-m3 (SOTA per RAG italiano/multilingua)."""
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            raise ImportError("pip install sentence-transformers")

        model = SentenceTransformer('BAAI/bge-m3')
        
        def _embed(text: str) -> np.ndarray:
            return model.encode(text, normalize_embeddings=True, show_progress_bar=False).astype(np.float32)
        return _embed

    @staticmethod
    def clip_openai() -> Callable[[Union[str, Any]], np.ndarray]:
        """
        OpenAI CLIP per ricerca multi-modale (testo -> immagine).
        Richiede: pip install pillow torch clip
        """
        try:
            import torch
            import clip
            from PIL import Image
        except ImportError:
            raise ImportError("pip install ftfy regex tqdm pillow torch clip-by-openai")

        device = "cuda" if torch.cuda.is_available() else "cpu"
        model, preprocess = clip.load("ViT-B/32", device=device)

        def _embed(content: Union[str, Any]) -> np.ndarray:
            """Gestisce sia stringhe (testo) che oggetti Image (PIL)."""
            with torch.no_grad():
                if isinstance(content, str):
                    # Embed testo
                    tokenized = clip.tokenize([content]).to(device)
                    vec = model.encode_text(tokenized)
                else:
                    # Embed immagine (PIL)
                    image = preprocess(content).unsqueeze(0).to(device)
                    vec = model.encode_image(image)
                
                # Normalizza per cosine similarity
                vec /= vec.norm(dim=-1, keepdim=True)
                return vec.cpu().numpy().flatten().astype(np.float32)
                
        return _embed

    @staticmethod
    def dinov2_meta() -> Callable[[Any], np.ndarray]:
        """Meta DinoV2 per feature extraction di altissimo livello (solo immagini)."""
        try:
            import torch
            from torchvision import transforms
            from PIL import Image
        except ImportError:
            raise ImportError("pip install torch torchvision pillow")

        # Carica il modello via torch hub
        device = "cuda" if torch.cuda.is_available() else "cpu"
        model = torch.hub.load('facebookresearch/dinov2', 'dinov2_vits14').to(device)
        model.eval()

        transform = transforms.Compose([
            transforms.Resize(256, interpolation=3),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])

        def _embed(img: Any) -> np.ndarray:
            """Riceve oggetto PIL Image."""
            img_t = transform(img).unsqueeze(0).to(device)
            with torch.no_grad():
                vec = model(img_t)
            return vec.cpu().numpy().flatten().astype(np.float32)
            
        return _embed
