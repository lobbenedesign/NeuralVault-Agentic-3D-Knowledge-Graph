"""
network/discovery.py
────────────────────
Sovereign Discovery: Implementazione mDNS/ZeroConf per NeuralVault.
Permette ai nodi della Mesh di trovarsi automaticamente sulla rete locale
senza configurazione manuale degli IP.
"""

import socket
import logging
import threading
from zeroconf import IPVersion, ServiceInfo, Zeroconf, ServiceBrowser, ServiceListener

class MeshDiscoveryListener(ServiceListener):
    def __init__(self, on_peer_found_callback):
        self.on_peer_found = on_peer_found_callback

    def update_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        pass

    def remove_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        pass

    def add_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        info = zc.get_service_info(type_, name)
        if info:
            addresses = [socket.inet_ntoa(addr) for addr in info.addresses]
            if addresses:
                port = info.port
                peer_address = f"http://{addresses[0]}:{port}"
                node_id = info.properties.get(b'node_id', b'unknown').decode('utf-8')
                pub_key = info.properties.get(b'pub_key', b'').decode('utf-8')
                self.on_peer_found(node_id, peer_address, pub_key)

class SovereignDiscovery:
    def __init__(self, node_id: str, port: int, public_key: str, on_peer_found_callback):
        self.node_id = node_id
        self.port = port
        self.public_key = public_key
        self.on_peer_found = on_peer_found_callback
        self.zeroconf = None
        self.browser = None
        self.service_info = None
        self.logger = logging.getLogger("Mesh-Discovery")

    def start(self):
        try:
            self.zeroconf = Zeroconf(ip_version=IPVersion.V4Only)
            
            # 1. Registrazione Servizio Locale
            desc = {
                'node_id': self.node_id,
                'pub_key': self.public_key,
                'version': '1.0.0'
            }
            
            # Otteniamo l'IP locale (non 127.0.0.1)
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                s.connect(("8.8.8.8", 80))
                local_ip = s.getsockname()[0]
            except Exception:
                local_ip = socket.gethostbyname(socket.gethostname())
            finally:
                s.close()

            self.service_info = ServiceInfo(
                "_neuralvault._tcp.local.",
                f"{self.node_id}._neuralvault._tcp.local.",
                addresses=[socket.inet_aton(local_ip)],
                port=self.port,
                properties=desc,
                server=f"{socket.gethostname()}.local."
            )
            
            self.zeroconf.register_service(self.service_info)
            self.logger.info(f"📡 Discovery: Servizio registrato su {local_ip}:{self.port}")

            # 2. Browser per altri nodi
            listener = MeshDiscoveryListener(self.on_peer_found)
            self.browser = ServiceBrowser(self.zeroconf, "_neuralvault._tcp.local.", listener)
            
        except Exception as e:
            import traceback
            self.logger.error(f"❌ Discovery Start Fail: {e}\n{traceback.format_exc()}")

    def stop(self):
        if self.zeroconf:
            if self.service_info:
                self.zeroconf.unregister_service(self.service_info)
            self.zeroconf.close()
            self.logger.info("🛑 Discovery arrestato.")
