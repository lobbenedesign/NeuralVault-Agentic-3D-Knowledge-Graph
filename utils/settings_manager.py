import json
import os
from pathlib import Path
from typing import Dict

class SwarmSettingsManager:
    """Gestore persistente delle impostazioni del Swarm e del routing modelli."""
    def __init__(self, data_dir: Path):
        self.config_path = data_dir / "swarm_settings.json"
        self.default_settings = {
            "routing": {
                "audit": "deepseek-r1",
                "entity_extraction": "llama3.2",
                "synthesis": "mistral",
                "foraging_analysis": "deepseek-v3",
                "chat_mediator": "llama3.2",
                "general_purpose": "llama3.2"
            },
            "agents": {
                "janitron_mode": "conservative",
                "sentinel_active": True,
                "quantum_threshold": 0.92
            },
            "hydration_limit": 50000,
            "ollama_url": "http://127.0.0.1:11434"
        }
        self.settings = self._load()

    def _load(self) -> Dict:
        if not self.config_path.exists():
            self._save(self.default_settings)
            return self.default_settings
        try:
            with open(self.config_path, 'r') as f:
                loaded = json.load(f)
                # Ensure structure integrity (v2.9.11)
                full_settings = self.default_settings.copy()
                for k, v in loaded.items():
                    if isinstance(v, dict) and k in full_settings:
                        full_settings[k].update(v)
                    else:
                        full_settings[k] = v
                return full_settings
        except:
            return self.default_settings

    def _save(self, data: Dict):
        with open(self.config_path, 'w') as f:
            json.dump(data, f, indent=4)

    def get(self, key: str, default=None):
        """Recupera un'impostazione generica."""
        return self.settings.get(key, default)

    def get_model(self, task: str) -> str:
        """Ritorna il modello configurato per un determinato compito."""
        return self.settings.get("routing", {}).get(task, "llama3.2")

    def resolve_model(self, task: str, installed_models: list) -> str:
        """
        Ritorna il modello configurato, o il miglior fallback se non disponibile (Tiered Priority).
        """
        requested = self.get_model(task)
        if requested in installed_models:
            return requested
            
        # Registro Priorità Fallback (v5.0 Sovereign)
        # Ordine decrescente di potenza cognitiva
        priority_bridge = [
            "llama3.1-nemotron-70b", "deepseek-r1:32b", "nemotron:latest", 
            "deepseek-r1:14b", "mistral:latest", "llama3.1:latest", 
            "llama3.2:3b", "qwen2.5:1.5b", "llama3.2:1b"
        ]
        
        for p in priority_bridge:
            if p in installed_models:
                return p
        
        # Ultima speranza: il primo disponibile (o il richiesto originale se non c'è nulla)
        return installed_models[0] if installed_models else requested

    def update_routing(self, new_routing: Dict):
        if "routing" not in self.settings:
            self.settings["routing"] = {}
        self.settings["routing"].update(new_routing)
        self._save(self.settings)

    def get_all(self):
        return self.settings
