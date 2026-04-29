"""
utils/recommendations.py
────────────────────────
Sovereign Recommendation Engine: Consiglia i migliori LLM in base a:
1. Modelli installati
2. Hardware rilevato (Apple Silicon / RAM)
3. Catalogo Neural Hub
"""

import platform
import psutil
import logging
from typing import Dict, List, Any

logger = logging.getLogger("NeuralVault-Recs")

class SovereignRecommendationEngine:
    # Catalogo Globale "Neural Hub" (Stato dell'arte Aprile 2026)
    NEURAL_HUB_BEST = {
        "audit": "deepseek-r1:32b",
        "extraction": "qwen2.5:7b-instruct",
        "crossref": "llama3.3:7b",
        "synthesis": "deepseek-r1:14b",
        "chat_mediator": "llama3.2:3b",
        "oracle_evolution": "qwen2.5:14b",
        "vision_general": "phi3.5-vision:latest",
        "scene_description": "moondream:latest",
        "vision_detection": "llava:7b",
        "vision_ocr": "llama3.2-vision:latest",
        "vision_analysis": "phi3.5-vision:latest",
        "coding_1": "deepseek-coder-v2:latest",
        "coding_2": "qwen2.5-coder:7b",
        "coding_supervisor": "deepseek-r1:32b",
        "evolution_suggestions": "llama3.3:7b",
        "court_judge_1": "llama3.3:7b",
        "court_judge_2": "deepseek-r1:14b",
        "court_judge_3": "phi3.5:latest"
    }

    def __init__(self, installed_models: List[str]):
        self.installed = [m.split(":")[0] for m in installed_models]
        self.full_installed = installed_models
        self.hw_info = self._detect_hardware()

    def _detect_hardware(self) -> Dict[str, Any]:
        """Rileva CPU, GPU (Apple Silicon) e RAM."""
        ram_gb = psutil.virtual_memory().total / (1024**3)
        processor = platform.processor()
        is_apple_silicon = "arm" in processor.lower() or "apple" in platform.platform().lower()
        
        # Determina il Tier hardware
        if is_apple_silicon:
            if ram_gb >= 32: tier = "ULTRA"
            elif ram_gb >= 16: tier = "PRO"
            else: tier = "BASE"
        else:
            if ram_gb >= 32: tier = "HIGH_END"
            else: tier = "ENTRY"
            
        return {
            "ram": round(ram_gb, 1),
            "is_apple_silicon": is_apple_silicon,
            "tier": tier
        }

    def get_recommendations_for_task(self, task: str) -> Dict[str, str]:
        """Ritorna i 3 consigli per un dato task."""
        best_hub = self.NEURAL_HUB_BEST.get(task, "llama3.2")
        
        # 1. Best for Hardware (Ottimizzato per il sistema dell'utente)
        best_hw = self._get_best_for_hw(task)
        
        # 2. Best Installed (Il migliore tra quelli che l'utente ha già)
        best_installed = self._get_best_installed(task)
        
        return {
            "best_installed": best_installed,
            "best_hw": best_hw,
            "best_hub": best_hub
        }

    def _get_best_for_hw(self, task: str) -> str:
        tier = self.hw_info["tier"]
        
        # Mappa semplificata Task -> Model Size basata sull'hardware
        if tier in ["ULTRA", "HIGH_END"]:
            sizes = {"audit": "32b", "coding": "14b", "vision": "7b", "default": "7b"}
        elif tier == "PRO":
            sizes = {"audit": "14b", "coding": "7b", "vision": "7b", "default": "3b"}
        else: # BASE / ENTRY
            sizes = {"audit": "7b", "coding": "3b", "vision": "tiny", "default": "1.5b"}

        # Logica di selezione specifica per task e size
        if "vision" in task:
            return "moondream:latest" if sizes["vision"] == "tiny" else "llava:7b"
        if "coding" in task:
            return f"qwen2.5-coder:{sizes['coding']}"
        if task == "audit":
            return f"deepseek-r1:{sizes['audit']}"
        
        return f"qwen2.5:{sizes['default']}"

    def _get_best_installed(self, task: str) -> str:
        """Cerca il miglior match tra i modelli installati."""
        # Se non ci sono modelli, fallback
        if not self.full_installed: return "Nessuno installato"
        
        # Logica di filtraggio per parole chiave
        keywords = {
            "audit": ["r1", "reasoning", "llama3.3", "phi3.5"],
            "coding": ["coder", "code", "qwen2.5-coder"],
            "vision": ["vision", "llava", "moondream"],
            "extraction": ["qwen", "llama3.2", "mistral"],
            "synthesis": ["r1", "synthesis", "llama3.3"]
        }
        
        target_keys = keywords.get(task.split("_")[0], ["llama"])
        
        # Cerca il primo modello installato che contiene una delle keyword
        for full_name in self.full_installed:
            name_lower = full_name.lower()
            if any(k in name_lower for k in target_keys):
                return full_name
                
        # Se nessun match specifico, ritorna il più pesante (spesso il più intelligente)
        return self.full_installed[0]

    def get_all_recommendations(self) -> Dict[str, Dict[str, str]]:
        tasks = list(self.NEURAL_HUB_BEST.keys())
        return {task: self.get_recommendations_for_task(task) for task in tasks}
