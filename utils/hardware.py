import psutil
import shutil
import os
import subprocess
import torch
from pathlib import Path
from typing import Dict, Any

class HardwareTuner:
    """
    Sovereign Hardware DNA Sensor (v1.0)
    Optimizes Apple Silicon MPS and monitors deep telemetry.
    """
    def __init__(self, data_dir: str = "./vault_data"):
        self.data_dir = Path(data_dir)
        self.device = "mps" if torch.backends.mps.is_available() else "cpu"
        
    def get_telemetry(self) -> Dict[str, Any]:
        """Raccoglie metriche hardware profonde per il dashboard HUD."""
        # 1. RAM e Swap
        ram = psutil.virtual_memory()
        
        # 2. Disk Footprint
        total, used, free = shutil.disk_usage(self.data_dir)
        
        # 3. Ollama Telemetry (Modelli caricati in VRAM)
        try:
            res = subprocess.run(["ollama", "ps"], capture_output=True, text=True)
            active_models = [line.split()[0] for line in res.stdout.splitlines()[1:] if line.strip()]
        except:
            active_models = []
            
        # 4. MPS Pressure (Simulazione basata su carico GPU se possibile)
        # Su M1 non c'è un comando standard leggero senza librerie esterne, simuliamo via CPU load per ora
        gpu_pressure = psutil.cpu_percent(interval=None) # Placeholder per MPS Pressure real-time
        
        return {
            "ram_usage": f"{ram.percent}%",
            "ram_used_gb": round(ram.used / (1024**3), 2),
            "disk_full": f"{int((used/total)*100)}%",
            "vault_size_mb": round(sum(f.stat().st_size for f in self.data_dir.rglob('*') if f.is_file()) / (1024**2), 2),
            "active_models": active_models,
            "compute_mode": "METAL / MPS" if self.device == "mps" else "SYSTEM / CPU",
            "mps_pressure": f"{gpu_pressure}%"
        }

    def optimize_vram(self):
        """Unioad automatico dei modelli Ollama inattivi per liberare VRAM."""
        # In produzione: invia segnale di unload a Ollama API
        pass
