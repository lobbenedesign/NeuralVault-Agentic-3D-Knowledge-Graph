"""
neuralvault.network.gossip
──────────────────────────
Protocollo di sincronizzazione asincrona tra nodi della Mesh.
Implementa un meccanismo di 'Epidemic Broadcast' per propagare 
nuove sinapsi e nodi critici tra istanze diverse.
"""

import time
import asyncio
import httpx
from typing import List, Dict, Optional
from pydantic import BaseModel

class SyncSignal(BaseModel):
    source_node_id: str
    timestamp: float
    payload_type: str # "upsert", "delete", "meta_update"
    data: Dict

class GossipNode:
    def __init__(self, node_id: str, address: str):
        self.node_id = node_id
        self.address = address # es. "http://192.168.1.50:8000"
        self.last_seen = time.time()
        self.is_active = True

class GossipManager:
    def __init__(self, local_node_id: str, peers: List[str] = None):
        self.local_node_id = local_node_id
        self.peers: Dict[str, GossipNode] = {}
        if peers:
            for p in peers:
                self.add_peer(p)
        
        self.client = httpx.AsyncClient(timeout=2.0)
        self._sync_queue = asyncio.Queue()

    def add_peer(self, address: str):
        # Genera un ID temporaneo finché non avviene l'handshake
        temp_id = f"peer_{len(self.peers)}"
        self.peers[temp_id] = GossipNode(temp_id, address)

    async def broadcast_upsert(self, node_data: Dict):
        """Invia un nuovo nodo a tutti i peer conosciuti (Fan-out)."""
        signal = SyncSignal(
            source_node_id=self.local_node_id,
            timestamp=time.time(),
            payload_type="upsert",
            data=node_data
        )
        
        tasks = []
        for peer in self.peers.values():
            if peer.is_active:
                tasks.append(self._send_signal(peer, signal))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _send_signal(self, peer: GossipNode, signal: SyncSignal):
        try:
            url = f"{peer.address}/api/gossip/sync"
            response = await self.client.post(url, json=signal.model_dump())
            if response.status_code == 200:
                peer.last_seen = time.time()
                peer.is_active = True
            else:
                peer.is_active = False
        except Exception:
            peer.is_active = False

    async def close(self):
        await self.client.aclose()
