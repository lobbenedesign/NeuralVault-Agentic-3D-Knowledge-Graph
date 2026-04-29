"""
utils/mesh.py
─────────────
NeuralVault Mesh Protocol (v3.8.0)
P2P Synchronization using CRDTs and secure peer discovery.
"""

import time
import json
import logging
import threading
import httpx
from typing import List, Dict, Any, Optional, Set
from utils.crdt import GSet, LWWMap

class MeshNode:
    """Rappresentazione di un peer nella rete Mesh."""
    def __init__(self, node_id: str, base_url: str, api_key: str):
        self.node_id = node_id
        self.base_url = base_url
        self.api_key = api_key
        self.last_seen = 0.0

class MeshSyncManager:
    """
    Il cuore del protocollo Mesh.
    Gestisce la sincronizzazione P2P senza server centrale.
    """
    def __init__(self, engine: Any, local_node_id: str):
        self.engine = engine
        self.local_node_id = local_node_id
        self.peers: Dict[str, MeshNode] = {}
        
        # CRDT State: Grow-only Set di ID dei nodi conosciuti
        self.known_nodes = GSet()
        
        self.running = False
        self._thread: Optional[threading.Thread] = None
        self.logger = logging.getLogger("MeshSync")

    def add_peer(self, node_id: str, url: str, api_key: str):
        self.peers[node_id] = MeshNode(node_id, url, api_key)
        self.logger.info(f"🌐 Peer aggiunto alla Mesh: {node_id} ({url})")

    def start(self):
        self.running = True
        self._thread = threading.Thread(target=self._sync_loop, daemon=True)
        self._thread.start()
        self.logger.info("📡 Mesh Sync Engine AVVIATO.")

    def stop(self):
        self.running = False

    def _sync_loop(self):
        """Loop di sincronizzazione anti-entropia."""
        while self.running:
            # 1. Aggiorna lo stato locale dei nodi conosciuti
            local_ids = set(self.engine._nodes.keys())
            for nid in local_ids:
                self.known_nodes.add(nid)

            # 2. Tenta la sincronizzazione con ogni peer
            for peer_id, peer in self.peers.items():
                try:
                    self._sync_with_peer(peer)
                    peer.last_seen = time.time()
                except Exception as e:
                    self.logger.warning(f"⚠️ Errore sincronizzazione con peer {peer_id}: {e}")
            
            time.sleep(30) # Sincronizzazione ogni 30 secondi

    def _sync_with_peer(self, peer: MeshNode):
        """Protocollo di scambio: Diff -> Pull."""
        headers = {"X-API-Key": peer.api_key}
        
        # A. Scarica l'elenco degli ID dal peer (Inventory)
        # Assumiamo l'esistenza di un endpoint /api/mesh/inventory
        with httpx.Client(timeout=10.0) as client:
            r = client.get(f"{peer.base_url}/api/mesh/inventory", headers=headers)
            if r.status_code != 200: return
            
            peer_ids = set(r.json().get("ids", []))
            
            # B. Calcola la differenza (cosa ha lui che io non ho?)
            missing_ids = peer_ids - self.known_nodes.elements
            
            if not missing_ids:
                return

            self.logger.info(f"🔄 Mesh: Rilevati {len(missing_ids)} nuovi nodi dal peer {peer.node_id}")

            # C. Pull dei nodi mancanti (batch)
            r_pull = client.post(
                f"{peer.base_url}/api/mesh/pull", 
                headers=headers,
                json={"ids": list(missing_ids)[:50]} # Batch di 50 per stabilità
            )
            
            if r_pull.status_code == 200:
                new_data = r_pull.json().get("nodes", [])
                for node_data in new_data:
                    # Ingestione atomica nel Vault locale
                    self.engine.add_node(
                        node_id=node_data["id"],
                        text=node_data["text"],
                        metadata={**node_data.get("metadata", {}), "mesh_origin": peer.node_id}
                    )
                    self.known_nodes.add(node_data["id"])
                
                self.logger.info(f"✅ Mesh: Sincronizzati {len(new_data)} nodi da {peer.node_id}")
