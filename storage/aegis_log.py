"""
neuralvault.storage.aegis_log
───────────────────────────────
Zero-Waste Append-Only Binary Format (AOBF) per VaultNode.
Evoluzione Generazionale (Fase 2 Roadmap).
"""

from __future__ import annotations
from pathlib import Path
from storage.generational_aobf import GenerationalAegisStore as AegisLogStore

# Esporta AegisLogStore per compatibilità con il resto del sistema.
__all__ = ["AegisLogStore"]
