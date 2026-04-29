"""
retrieval/pollers.py
────────────────────
Sovereign Pollers: Connettori proattivi pull-based.
Permettono l'ingestione sicura senza webhook o porte aperte.
"""

import time
import threading
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import httpx
import xml.etree.ElementTree as ET

class BasePoller:
    """Classe base per tutti i pollers sovrani."""
    def __init__(self, name: str, interval: int = 3600, namespace: str = "default"):
        self.name = name
        self.interval = interval
        self.namespace = namespace
        self.running = False
        self._thread: Optional[threading.Thread] = None
        self.logger = logging.getLogger(f"Poller-{name}")

    def start(self, engine: Any):
        self.running = True
        self._thread = threading.Thread(target=self._loop, args=(engine,), daemon=True)
        self._thread.start()
        self.logger.info(f"🚀 Poller {self.name} avviato (Intervallo: {self.interval}s)")

    def stop(self):
        self.running = False
        self.logger.info(f"🛑 Poller {self.name} arrestato.")

    def _loop(self, engine: Any):
        while self.running:
            try:
                self.poll(engine)
            except Exception as e:
                self.logger.error(f"❌ Errore durante il polling di {self.name}: {e}")
            
            # Attesa intelligente
            for _ in range(self.interval):
                if not self.running: break
                time.sleep(1)

    def poll(self, engine: Any):
        """Metodo da implementare nelle sottoclassi."""
        raise NotImplementedError

class RSSPoller(BasePoller):
    """Poller per feed RSS/Atom."""
    def __init__(self, url: str, name: str, interval: int = 3600, namespace: str = "news"):
        super().__init__(name, interval, namespace)
        self.url = url
        self._last_seen_id: Optional[str] = None

    def poll(self, engine: Any):
        self.logger.info(f"📡 Polling RSS: {self.url}")
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.get(self.url)
                if response.status_code != 200: return
                
                root = ET.fromstring(response.content)
                # Supporto base per RSS 2.0
                items = root.findall(".//item")
                
                new_nodes = 0
                for item in reversed(items): # Dal più vecchio al più recente
                    title = item.find("title").text if item.find("title") is not None else "Untitled"
                    link = item.find("link").text if item.find("link") is not None else ""
                    desc = item.find("description").text if item.find("description") is not None else ""
                    
                    item_id = link or title
                    if self._last_seen_id == item_id: break
                    
                    content = f"📰 {title}\n\n{desc}\n\nLink: {link}"
                    engine.upsert_text(content, metadata={
                        "source": f"RSS: {self.name}",
                        "url": link,
                        "namespace": self.namespace,
                        "file_type": "rss_item"
                    })
                    new_nodes += 1
                    self._last_seen_id = item_id
                
                if new_nodes > 0:
                    self.logger.info(f"✅ Ingeriti {new_nodes} nuovi articoli da {self.name}")
        except Exception as e:
            self.logger.error(f"⚠️ RSS Poll Fail: {e}")


class TelegramPoller(BasePoller):
    """Poller per Telegram Bot API (Pull-based)."""
    def __init__(self, token: str, name: str, interval: int = 10, namespace: str = "telegram"):
        super().__init__(name, interval, namespace)
        self.token = token
        self.url = f"https://api.telegram.org/bot{token}"
        self._last_offset = 0

    def poll(self, engine: Any):
        try:
            with httpx.Client(timeout=10.0) as client:
                r = client.get(f"{self.url}/getUpdates", params={"offset": self._last_offset + 1})
                if r.status_code != 200: return
                
                updates = r.json().get("result", [])
                new_nodes = 0
                for up in updates:
                    self._last_offset = up["update_id"]
                    msg = up.get("message")
                    if not msg: continue
                    
                    text = msg.get("text")
                    sender = msg.get("from", {}).get("username", "Unknown")
                    
                    if text:
                        content = f"💬 TELEGRAM da @{sender}:\n\n{text}"
                        engine.upsert_text(content, metadata={
                            "source": f"Telegram: {self.name}",
                            "sender": sender,
                            "namespace": self.namespace,
                            "file_type": "telegram_msg"
                        })
                        new_nodes += 1
                
                if new_nodes > 0:
                    self.logger.info(f"✅ Ingeriti {new_nodes} messaggi Telegram.")
        except Exception as e:
            self.logger.error(f"⚠️ Telegram Poll Fail: {e}")

class PollerManager:
    """Gestore centralizzato dei pollers attivi."""
    def __init__(self, engine: Any):
        self.engine = engine
        self.pollers: List[BasePoller] = []

    def add_poller(self, poller: BasePoller):
        self.pollers.append(poller)
        poller.start(self.engine)

    def stop_all(self):
        for p in self.pollers:
            p.stop()
