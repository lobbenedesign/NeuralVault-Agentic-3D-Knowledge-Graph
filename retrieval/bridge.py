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

    def ingest_codebase(self):
        """Versione v2.0: Inietta il codice sorgente locale nel Vault come nodi di conoscenza."""
        if not self.vault: return
        
        print(f"🏗️ [Bridge] Ingestione codebase in corso da {self.project_root}...")
        nodes_created = 0
        for name, path in self.code_signatures.items():
            try:
                # Recuperiamo il corpo della funzione/classe (primi 500 caratteri)
                content = path.read_text()
                body = ""
                lines = content.splitlines()
                for i, line in enumerate(lines):
                    if name in line.lower() and ('def ' in line or 'class ' in line):
                        body = "\n".join(lines[max(0, i-2):i+10]) # Contesto: 2 righe prima, 10 dopo
                        break
                
                node_id = f"src_{hashlib.md5(name.encode()).hexdigest()[:8]}"
                if node_id not in self.vault._nodes:
                    self.vault.add_node(
                        node_id, 
                        f"SOURCE_CODE [{name.upper()}]:\n{body}", 
                        metadata={
                            "source": str(path.relative_to(self.project_root)),
                            "origin": "local_bridge",
                            "type": "code_signature",
                            "name": name,
                            "color": "#3b82f6" # Blu per il codice
                        }
                    )
                    nodes_created += 1
            except: pass
        print(f"✅ [Bridge] Codebase sincronizzata: {nodes_created} nuovi nodi sorgente.")

    def bridge_nodes(self, vault=None) -> int:
        target_vault = vault or self.vault
        if not target_vault: return 0
        
        bridges_created = 0
        # Cerchiamo nodi web (documentazione) e nodi sorgente (codice)
        web_nodes = [nid for nid, node in target_vault._nodes.items() if node.metadata.get("origin") == "web_forager"]
        src_nodes = [nid for nid, node in target_vault._nodes.items() if node.metadata.get("origin") == "local_bridge"]
        
        for wnid in web_nodes:
            wnode = target_vault._nodes[wnid]
            text_lower = (wnode.text or "").lower()
            
            for snid in src_nodes:
                snode = target_vault._nodes[snid]
                sig = snode.metadata.get("name", "").lower()
                
                if sig and sig in text_lower:
                    # Abbiamo un match! Creiamo una Super-Sinapsi (Aura RGB)
                    from index.node import SemanticEdge, RelationType
                    
                    # Verifica se il legame esiste già
                    exists = any(e.target_id == snid for e in wnode.edges)
                    if not exists:
                        # Legame bidirezionale v3.0
                        edge = SemanticEdge(target_id=snid, relation=RelationType.EQUIVALENT)
                        edge.is_aura = True # Attiva effetto RGB
                        wnode.edges.append(edge)
                        
                        rev_edge = SemanticEdge(target_id=wnid, relation=RelationType.EQUIVALENT)
                        rev_edge.is_aura = True
                        snode.edges.append(rev_edge)
                        
                        bridges_created += 1
        return bridges_created
