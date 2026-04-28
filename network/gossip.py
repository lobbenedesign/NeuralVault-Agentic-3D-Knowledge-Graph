"""
neuralvault.network.gossip
──────────────────────────
Protocollo di sincronizzazione asincrona tra nodi della Mesh.
Implementa un meccanismo di 'Epidemic Broadcast' per propagare 
nuove sinapsi e nodi critici tra istanze diverse, ora con crittografia X25519.
"""

import time
import json
import asyncio
import httpx
import logging
from typing import List, Dict, Optional
from pydantic import BaseModel

class SyncSignal(BaseModel):
    source_node_id: str
    timestamp: float
    payload_type: str # "upsert", "delete", "meta_update"
    data: Optional[Dict] = None # In chiaro (solo per reti sicure/test)
    encrypted_data: Optional[str] = None # Cifrato con AES-GCM (Base64)

class GossipNode:
    def __init__(self, node_id: str, address: str, public_key: str = None):
        self.node_id = node_id
        self.address = address # es. "http://192.168.1.50:8000"
        self.public_key = public_key
        self.shared_key: Optional[bytes] = None
        self.last_seen = time.time()
        self.is_active = True

class GossipManager:
    def __init__(self, local_node_id: str, crypto=None):
        self.local_node_id = local_node_id
        self.crypto = crypto
        self.peers: Dict[str, GossipNode] = {}
        self.logger = logging.getLogger("Mesh-Gossip")
        self.client = httpx.AsyncClient(timeout=5.0)
        self._sync_queue = asyncio.Queue()

    def add_peer(self, node_id: str, address: str, public_key: str = None):
        """Aggiunge o aggiorna un peer nella mesh."""
        if node_id == self.local_node_id: return
        
        if node_id in self.peers:
            peer = self.peers[node_id]
            peer.address = address
            if public_key and public_key != peer.public_key:
                peer.public_key = public_key
                peer.shared_key = None # Forza ricalcolo
            peer.last_seen = time.time()
            peer.is_active = True
        else:
            self.logger.info(f"🤝 [Mesh] Nuovo peer rilevato: {node_id} @ {address}")
            self.peers[node_id] = GossipNode(node_id, address, public_key)

    async def broadcast_upsert(self, node_data: Dict):
        """Invia un nuovo nodo a tutti i peer conosciuti (Fan-out)."""
        tasks = []
        for peer in self.peers.values():
            if peer.is_active:
                # Creiamo un segnale specifico per ogni peer (se cifrato)
                tasks.append(self._send_signal_to_peer(peer, "upsert", node_data))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _send_signal_to_peer(self, peer: GossipNode, p_type: str, data: Dict):
        try:
            signal_data = {
                "source_node_id": self.local_node_id,
                "timestamp": time.time(),
                "payload_type": p_type
            }

            # Crittografia se disponibile
            if self.crypto and peer.public_key:
                if not peer.shared_key:
                    peer.shared_key = self.crypto.derive_shared_key(peer.public_key)
                
                json_payload = json.dumps(data)
                signal_data["encrypted_data"] = self.crypto.encrypt(json_payload, peer.shared_key)
            else:
                signal_data["data"] = data

            url = f"{peer.address}/api/gossip/sync"
            response = await self.client.post(url, json=signal_data)
            
            if response.status_code == 200:
                peer.last_seen = time.time()
                peer.is_active = True
            else:
                self.logger.warning(f"⚠️ [Mesh] Peer {peer.node_id} ha risposto con status {response.status_code}")
                peer.is_active = False
        except Exception as e:
            # self.logger.debug(f"❌ [Mesh] Errore invio a {peer.node_id}: {e}")
            peer.is_active = False

    async def close(self):
        await self.client.aclose()
