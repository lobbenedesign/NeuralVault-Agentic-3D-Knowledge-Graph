"""
memory_tiers.py
────────────────
Gestore avanzato dei Tier di Memoria per NeuralVault v0.2.5.
Supporta Working (LRU), Episodic (LMDB) e Semantic (Parquet/DuckDB).
Fase 14: Batching & Lazy Invalidation.
"""

from __future__ import annotations
import os
import json
import uuid
import time
from pathlib import Path
from typing import Optional, Any, OrderedDict as OrderedDictType
from collections import OrderedDict
import numpy as np
import pyarrow as pa
import struct
import threading
from index.node import VaultNode, MemoryTier
from storage.aegis_log import AegisLogStore

# ─────────────────────────────────────────────
# 1. Ephemeral Tier: Working Memory (LRU Cache)
# ─────────────────────────────────────────────

class LRUCache:
    def __init__(self, capacity: int = 512):
        self.capacity = capacity
        self._cache: OrderedDictType[str, VaultNode] = OrderedDict()

    def get(self, node_id: str) -> VaultNode | None:
        if node_id not in self._cache: return None
        self._cache.move_to_end(node_id)
        return self._cache[node_id]

    def put(self, node: VaultNode) -> VaultNode | None:
        evicted = None
        if node.id in self._cache:
            self._cache.move_to_end(node.id)
        else:
            if len(self._cache) >= self.capacity:
                _, evicted = self._cache.popitem(last=False)
            self._cache[node.id] = node
        node.tier = MemoryTier.WORKING
        return evicted

    def invalidate(self, node_id: str):
        """Rimuove forzatamente un nodo dalla cache (Cache Invalidation)."""
        self._cache.pop(node_id, None)

# 2. Sequential Tier: Episodic Memory (AOBF - AegisLog)
# ─────────────────────────────────────────────



# ─────────────────────────────────────────────
# Tier Manager Core (v3.0 Zero-Waste)
# ─────────────────────────────────────────────

class MemoryTierManager:
    def __init__(self, data_dir: Optional[Path] = None, working_cap: int = 1000, dim: int = 1024):
        self.working = LRUCache(capacity=working_cap)
        self.data_dir = data_dir
        self.dim = dim
        self.is_persistent = False
        
        # Fase 14: Tracking delle versioni per Lazy Invalidation
        self._metadata_versions: dict[str, int] = {}
        
        if data_dir:
            self.episodic = AegisLogStore(data_dir / "episodic", dim=dim)
            self.is_persistent = True

    def put(self, node: VaultNode, tier: MemoryTier = MemoryTier.WORKING):
        """
        Ingestione Multi-Tier con Version Tracking.
        """
        # Aggiorna la versione globale conosciuta
        self._metadata_versions[node.id] = node.version
        
        if tier == MemoryTier.WORKING:
            evicted = self.working.put(node)
            if self.is_persistent:
                # [Fix]: Salva sempre nel tier Episodico (AOBF) per persistenza anche se i nodi
                # sono nel tier WORKING e non sono stati sfrattati!
                self.episodic.put(node, immediate=True)
                
            if evicted and self.is_persistent:
                # Eviction (gia salvato)
                self.episodic.put(evicted, immediate=True)
        elif self.is_persistent:
            self.episodic.put(node, immediate=True)

    def get(self, node_id: str) -> Optional[VaultNode]:
        """
        Routing della lettura con Validazione Semantica (Fase 14).
        """
        node = self.working.get(node_id)
        
        # LAZY INVALIDATION: Se il nodo in RAM è obsoleto, ricaricalo
        if node and self.is_persistent:
            latest_v = self._metadata_versions.get(node_id, 0)
            if node.version < latest_v:
                print(f"🔄 Cache Invalidation: Reloading stale node {node_id} (v{node.version} < v{latest_v})")
                self.working.invalidate(node_id)
                node = None # Forza ricarica dal disco
        
        if node: return node
        
        if self.is_persistent:
            return self.episodic.get(node_id)
        return None

    def delete(self, node_id: str) -> bool:
        """Rimuove il nodo da tutti i tier di memoria."""
        # 1. Invalida Working Memory (LRU)
        self.working.invalidate(node_id)
        
        # 2. Rimuove Version Tracking
        self._metadata_versions.pop(node_id, None)
        
        # 3. Invalida Episodic Tier (AOBF/Disk)
        if self.is_persistent:
            return self.episodic.delete(node_id)
        return True

    def undelete(self, node_id: str) -> bool:
        """[Fase 25: Rollback] Ripristina un nodo dal Tier Episodico (AOBF)."""
        if not self.is_persistent: return False
        success = self.episodic.undelete(node_id)
        if success:
            # Re-idrata il working tier dopo il rollback
            node = self.episodic.get(node_id)
            if node:
                self._metadata_versions[node.id] = node.version
                self.working.put(node)
            return True
        return False

    def get_all_recent(self, limit: int = 100) -> list[VaultNode]:
        """Innesca il caricamento di massa dal Tier Episodio (Fase 35)."""
        if not self.is_persistent: return []
        raw_nodes = self.episodic.scan_recent(limit)
        nodes = []
        for node in raw_nodes:
            self._metadata_versions[node.id] = node.version
            self.working.put(node)
            nodes.append(node)
        return nodes

    def remove(self, node_id: str):
        """Rimuove un nodo da tutti i tier (Working + Episodic)."""
        self.working.invalidate(node_id)
        if self.is_persistent:
            try:
                self.episodic.delete(node_id)
            except: pass

    def close(self):
        if hasattr(self, 'episodic') and self.episodic:
            self.episodic.close()
