"""
neuralvault.cluster.gossip
──────────────────────────
Implemetazione del protocollo SWIM (Scalable Weakly-consistent Infection-style)
per la scoperta automatizzata dei nodi nel cluster.
I nodi "pettegolano" tra loro scambiandosi liste di vicini vivi.
"""

import socket
import threading
import time
import json
import random
from typing import Set, Dict, List, Optional
from dataclasses import dataclass, asdict

@dataclass
class NodeInfo:
    id: str
    url: str
    status: str = "alive"
    last_seen: float = 0.0
    incarnation: int = 0
    load_cpu: float = 0.0
    load_mem: float = 0.0
    is_cloning: bool = False

class GossipProtocol:
    """
    Protocollo di scoperta nodi via UDP Multicast o Point-to-Point Gossip.
    """
    def __init__(self, node_id: str, local_url: str, port: int = 9999):
        self.node_id = node_id
        self.local_url = local_url
        self.port = port
        self.nodes: Dict[str, NodeInfo] = {}
        self.nodes[node_id] = NodeInfo(id=node_id, url=local_url, last_seen=time.time())
        
        self._stop_event = threading.Event()
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Permetti il riuso dell'indirizzo per test locali sullo stesso IP
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        self._thread = threading.Thread(target=self._listen, daemon=True)
        self._gossip_thread = threading.Thread(target=self._periodic_gossip, daemon=True)

    def start(self):
        """Avvia il protocollo di scoperta."""
        try:
            self._socket.bind(('', self.port))
            self._thread.start()
            self._gossip_thread.start()
        except Exception:
            # Se la porta è occupata, probabilmente un altro nodo è già attivo sul sistema
            pass

    def stop(self):
        self._stop_event.set()
        self._socket.close()

    def _listen(self):
        """Ascolta messaggi di gossip in arrivo."""
        while not self._stop_event.is_set():
            try:
                data, addr = self._socket.recvfrom(4096)
                msg = json.loads(data.decode())
                self._process_message(msg)
            except Exception:
                continue

    def _process_message(self, msg: dict):
        """Aggiorna la vista locale del cluster basandosi sul messaggio ricevuto."""
        remote_nodes = msg.get("nodes", {})
        for nid, info_dict in remote_nodes.items():
            info = NodeInfo(**info_dict)
            if nid not in self.nodes or info.incarnation > self.nodes[nid].incarnation:
                info.last_seen = time.time()
                self.nodes[nid] = info

    def _periodic_gossip(self):
        """Invia lo stato del cluster a un nodo a caso periodicamente."""
        while not self._stop_event.is_set():
            time.sleep(random.uniform(1.0, 3.0))
            if len(self.nodes) < 2: continue
            
            target_id = random.choice([nid for nid in self.nodes if nid != self.node_id])
            target_url = self.nodes[target_id].url
            
            # Estrai host/port dalla URL (es. http://localhost:8000 -> localhost, 9999)
            try:
                # Assumiamo per il gossip una porta fissa port+1 o simile
                host = target_url.split("//")[1].split(":")[0]
                self._send_to(host, self.port)
            except Exception:
                continue

    def _send_to(self, host: str, port: int):
        """Invia pacchetto UDP con lo stato del cluster e il LOAD locale."""
        import psutil
        try:
            self.nodes[self.node_id].load_cpu = psutil.cpu_percent()
            self.nodes[self.node_id].load_mem = psutil.virtual_memory().percent
        except ImportError:
            pass # Fallback: no metrics

        payload = json.dumps({"nodes": {nid: asdict(info) for nid, info in self.nodes.items()}})
        try:
            self._socket.sendto(payload.encode(), (host, port))
            # [Innovation Fase 7]: Check for Overload and Clone Triggers
            self._check_cloning_needs()
        except Exception:
            pass

    def _check_cloning_needs(self):
        """
        Analizza i vicini per identificare se uno shard è 'hot' (>85% CPU)
        e se c'è un nodo libero (<20% CPU) per clonarlo.
        """
        overloaded = [n for n in self.nodes.values() if n.load_cpu > 85.0 and not n.is_cloning]
        free_nodes = [n for n in self.nodes.values() if n.load_cpu < 20.0 and n.id != self.node_id]
        
        if overloaded and free_nodes:
            target = random.choice(overloaded)
            dest = random.choice(free_nodes)
            print(f"🌐 [Gossip] Autonomous Rebalance: Node {target.id} is HOT ({target.load_cpu}%). Triggering CLONE to {dest.id}...")
            # In produzione: qui inviamo REST API /clone al nodo di destinazione
            self.nodes[target.id].is_cloning = True

    def get_active_shards(self) -> List[str]:
        """Restituisce la lista di URL degli shard vivi rilevati."""
        now = time.time()
        # Timeout di 10 secondi per considerare un nodo morto
        return [info.url for info in self.nodes.values() if now - info.last_seen < 10.0]
