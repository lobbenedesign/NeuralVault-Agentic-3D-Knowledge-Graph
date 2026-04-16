import os
import hashlib
from pathlib import Path
from typing import List, Dict
import numpy as np

class LatentBridge:
    """🔗 [Super-Synapse] Collega la documentazione web al codice sorgente locale.
    Ridenominato da CodeDocBridger per compatibilità con il Kernel v0.5.0.
    """
    def __init__(self, vault=None, project_root=None, **kwargs):
        self.vault = vault
        # Se project_root non è fornito, cerchiamo di indovinarlo o usiamo la cartella corrente
        self.project_root = Path(project_root) if project_root else Path(".").absolute()
        self.code_signatures = self._scan_codebase()
        self.unified_dim = kwargs.get("unified_dim", 1024)

    def _scan_codebase(self) -> Dict[str, Path]:
        signatures = {}
        for ext in ['*.py', '*.md', '*.rs', '*.js']:
            for path in self.project_root.rglob(ext):
                if 'venv' in str(path) or '.git' in str(path): continue
                try:
                    content = path.read_text()
                    for line in content.splitlines():
                        if 'class ' in line or 'def ' in line:
                            parts = line.split('(')
                            if len(parts) > 0:
                                name = parts[0].replace('class', '').replace('def', '').strip()
                                if len(name) > 3:
                                    signatures[name.lower()] = path
                except: pass
        return signatures

    def bridge_nodes(self, vault=None) -> int:
        target_vault = vault or self.vault
        if not target_vault: return 0
        
        bridges_created = 0
        recent_nodes = [nid for nid, node in target_vault._nodes.items() 
                        if node.metadata.get("origin") == "web_forager"]
        
        for nid in recent_nodes:
            node = target_vault._nodes[nid]
            text_lower = node.text.lower()
            for sig, path in self.code_signatures.items():
                if sig in text_lower:
                    rel_path = str(path.relative_to(self.project_root))
                    if "code_bridges" not in node.metadata:
                        node.metadata["code_bridges"] = []
                    if rel_path not in node.metadata["code_bridges"]:
                        node.metadata["code_bridges"].append(rel_path)
                        bridges_created += 1
        return bridges_created
