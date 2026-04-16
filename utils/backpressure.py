"""
utils/backpressure.py
───────────────────────
Backpressure Protocol (Sensor-Aware) v1.0.0
Monitors hardware telemetry to prevent system swap and maintain fluidity.
Optimized for Apple Silicon Unified Memory.
"""

import os
import psutil
import subprocess
import time
from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class HardwareSensors:
    cpu_percent: float
    ram_percent: float
    vram_percent: float  # Relevant for Apple Silicon Unified Memory
    is_clogged:   bool

class BackpressureManager:
    def __init__(self, ram_threshold: float = 85.0, cpu_threshold: float = 90.0):
        self.ram_threshold = ram_threshold
        self.cpu_threshold = cpu_threshold
        self._last_sensors = HardwareSensors(0, 0, 0, False)

    def get_sensors(self) -> HardwareSensors:
        """Legge i sensori hardware in tempo reale."""
        cpu = psutil.cpu_percent(interval=None)
        ram = psutil.virtual_memory().percent
        
        # Per Apple Silicon, il VRAM è parte della Unified Memory.
        # Possiamo usare 'powertetrics' o 'system_profiler' ma è lento.
        # Una euristica accettabile è usare il RAM percent dato che è unificata.
        vram = ram 
        
        is_clogged = (ram > self.ram_threshold) or (cpu > self.cpu_threshold)
        
        self._last_sensors = HardwareSensors(
            cpu_percent=cpu,
            ram_percent=ram,
            vram_percent=vram,
            is_clogged=is_clogged
        )
        return self._last_sensors

    def get_throttle_factor(self) -> float:
        """
        Ritorna un fattore da 0.0 (stop totale) a 1.0 (piena velocità).
        """
        s = self.get_sensors()
        if s.ram_percent > 95 or s.cpu_percent > 98:
            return 0.1 # Critical throttle
        if s.is_clogged:
            # Linear decay tra threshold e 95%
            excess = max(0, s.ram_percent - self.ram_threshold)
            range_val = 95 - self.ram_threshold
            return max(0.2, 1.0 - (excess / range_val))
        return 1.0

    def wait_if_clogged(self):
        """Blocca l'esecuzione se il sistema è sotto stress estremo (Versione Sincrona)."""
        s = self.get_sensors()
        if s.ram_percent > 96 or s.cpu_percent > 98:
            print(f"⚠️ [Backpressure] System Clogged (RAM: {s.ram_percent}%). Waiting for breath (2s)...")
            time.sleep(2)

    async def async_wait_if_clogged(self):
        """Blocca l'esecuzione se il sistema è sotto stress estremo (Versione Asincrona)."""
        import asyncio
        while True:
            s = self.get_sensors()
            if s.ram_percent < 96 and s.cpu_percent < 98:
                break
            print(f"⚠️ [Backpressure] System Clogged (RAM: {s.ram_percent}%). Waiting for breath...")
            await asyncio.sleep(2)

# Singleton Instance
backpressure = BackpressureManager()
