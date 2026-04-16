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
                "general_purpose": "llama3.2"
            },
            "agents": {
                "janitron_mode": "conservative",
                "sentinel_active": True,
                "quantum_threshold": 0.92
            },
            "hydration_limit": 50000
        }
        self.settings = self._load()

    def _load(self) -> Dict:
        if not self.config_path.exists():
            self._save(self.default_settings)
            return self.default_settings
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except:
            return self.default_settings

    def _save(self, data: Dict):
        with open(self.config_path, 'w') as f:
            json.dump(data, f, indent=4)

    def get_model(self, task: str) -> str:
        """Ritorna il modello configurato per un determinato compito."""
        return self.settings.get("routing", {}).get(task, "llama3")

    def update_routing(self, new_routing: Dict):
        self.settings["routing"].update(new_routing)
        self._save(self.settings)

    def get_all(self):
        return self.settings
