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
        # Se project_root è None, disattiviamo la scansione della codebase locale
        self.project_root = Path(project_root) if project_root else None
        self.code_signatures = self._scan_codebase() if self.project_root else {}
        self.unified_dim = kwargs.get("unified_dim", 1024)

    def _scan_codebase(self) -> Dict[str, Path]:
        signatures = {}
        root = self.project_root
        if not root: return signatures
        # Estendiamo le estensioni supportate
        for ext in ['*.py', '*.md', '*.rs', '*.js', '*.ts', '*.html', '*.css']:
            try:
                for path in root.rglob(ext):
                    # Escludiamo cartelle di sistema e build
                    if any(x in str(path) for x in ['venv', '.git', '__pycache__', 'node_modules', 'dist', 'build']):
                        continue
                    try:
                        content = path.read_text()
                        for line in content.splitlines():
                            if 'class ' in line or 'def ' in line or 'function ' in line:
                                parts = line.split('(')
                                if len(parts) > 0:
                                    # Estrazione nome pulito
                                    name = parts[0].replace('class', '').replace('def', '').replace('async', '').replace('function', '').strip()
                                    if len(name) > 3 and not name.startswith('_'):
                                        signatures[name.lower()] = path
                    except: pass
            except: pass
        return signatures

    def _extract_body(self, lines: List[str], start_idx: int) -> str:
        """Estrae il blocco di codice basandosi sull'indentazione (Pythonic)."""
        first_line = lines[start_idx]
        indent = len(first_line) - len(first_line.lstrip())
        body = [first_line]
        for i in range(start_idx + 1, len(lines)):
            line = lines[i]
            if not line.strip(): 
                body.append(line)
                continue
            curr_indent = len(line) - len(line.lstrip())
            if curr_indent <= indent: break
            body.append(line)
        return "\n".join(body[:50]) # Limite per evitare nodi giganteschi legati a file enormi

    def ingest_codebase(self):
        """Versione v2.5.1: Ingestione proattiva con re-scan delle signature."""
        if not self.vault or not self.project_root: return
        
        # 🔄 Re-scan signatures to find new functions/classes
        self.code_signatures = self._scan_codebase()
        
        print(f"🏗️ [Bridge] Ingestione codebase granulare da {self.project_root}...")
        nodes_created = 0
        for name, path in self.code_signatures.items():
            try:
                content = path.read_text()
                lines = content.splitlines()
                body = ""
                for i, line in enumerate(lines):
                    if name in line.lower() and any(k in line for k in ['def ', 'class ', 'function ']):
                        body = self._extract_body(lines, i)
                        break
                
                node_id = f"src_{hashlib.md5(name.encode()).hexdigest()[:8]}"
                if node_id not in self.vault._nodes:
                    self.vault.add_node(
                        node_id, 
                        f"SOURCE_CODE_SIGNATURE [{name.upper()}]\nFILE: {path.name}\n\n{body}", 
                        metadata={
                            "source": str(path.relative_to(self.project_root)),
                            "origin": "local_bridge",
                            "type": "code_signature",
                            "name": name,
                            "color": "#3b82f6" 
                        }
                    )
                    nodes_created += 1
            except: pass
        print(f"✅ [Bridge] Codebase sincronizzata: {nodes_created} nuovi nodi sorgente.")

    def _bridge_nodes_legacy(self, target_vault) -> int:
        """Fallback: Matching testuale se i vettori non sono disponibili."""
        bridges_created = 0
        web_nodes = [nid for nid, node in target_vault._nodes.items() if node.metadata.get("origin") == "web_forager"]
        src_nodes = [nid for nid, node in target_vault._nodes.items() if node.metadata.get("origin") == "local_bridge"]
        for wnid in web_nodes:
            wnode = target_vault._nodes[wnid]
            for snid in src_nodes:
                snode = target_vault._nodes[snid]
                name = snode.metadata.get("name", "").lower()
                if not name: continue
                import re
                if re.search(rf"\b{re.escape(name)}\b", (wnode.text or "").lower()):
                    if not any(e.target_id == snid for e in wnode.edges):
                        from index.node import SemanticEdge, RelationType
                        edge = SemanticEdge(target_id=snid, relation=RelationType.EQUIVALENT, source="bridge_legacy")
                        setattr(edge, 'is_aura', True)
                        wnode.edges.append(edge)
                        
                        # 📝 [v14.5 Fix] Set metadata for engine stats
                        if "code_bridges" not in wnode.metadata: wnode.metadata["code_bridges"] = []
                        wnode.metadata["code_bridges"].append(name)
                        
                        bridges_created += 1
        return bridges_created

    def bridge_nodes(self, vault=None, threshold=0.82) -> int:
        """🔗 [CB-003 Upgrade] Semantic Bridging: Collega codice e docs tramite similarità vettoriale."""
        target_vault = vault or self.vault
        if not target_vault: return 0
        
        # 1. Triage dei Nodi (Web vs Local Code)
        web_nodes = [n for n in target_vault._nodes.values() if n.metadata.get("origin") == "web_forager" and n.vector is not None]
        src_nodes = [n for n in target_vault._nodes.values() if n.metadata.get("origin") == "local_bridge" and n.vector is not None]
        
        if not web_nodes or not src_nodes:
            return self._bridge_nodes_legacy(target_vault)
        
        print(f"📡 [Bridge] Analisi Semantica: {len(web_nodes)} documenti web vs {len(src_nodes)} file sorgente...")
        
        # 2. Calcolo Matrice di Similarità (Batch Vector Support)
        # Nodi normalizzati in post_init -> dot product = cosine similarity
        web_vectors = np.array([n.vector for n in web_nodes], dtype=np.float32)
        src_vectors = np.array([n.vector for n in src_nodes], dtype=np.float32)
        
        sim_matrix = np.dot(web_vectors, src_vectors.T)
        matches = np.where(sim_matrix > threshold)
        
        bridges_created = 0
        from index.node import SemanticEdge, RelationType
        
        for w_idx, s_idx in zip(*matches):
            wnode = web_nodes[w_idx]
            snode = src_nodes[s_idx]
            score = float(sim_matrix[w_idx, s_idx])
            
            # Evita duplicati
            if any(e.target_id == snode.id for e in wnode.edges):
                continue
                
            # 3. Creazione Super-Sinapsi (Aura RGB)
            reason = f"Semantic Match ({int(score*100)}%): Code logic correlates with web findings."
            
            # Legame Doc -> Codice
            edge_doc = SemanticEdge(target_id=snode.id, relation=RelationType.SIMILARITY, weight=score, source="bridge_aura")
            setattr(edge_doc, 'is_aura', True)
            setattr(edge_doc, 'reason', reason)
            wnode.edges.append(edge_doc)
            
            # 📝 [v14.5 Fix] Set metadata for engine stats
            if "code_bridges" not in wnode.metadata: wnode.metadata["code_bridges"] = []
            wnode.metadata["code_bridges"].append(snode.metadata.get("name", "unknown"))

            # Legame Codice -> Doc (Bidirezionale)
            edge_code = SemanticEdge(target_id=wnode.id, relation=RelationType.SIMILARITY, weight=score, source="bridge_aura")
            setattr(edge_code, 'is_aura', True)
            setattr(edge_code, 'reason', reason)
            snode.edges.append(edge_code)
            
            bridges_created += 1
            
        # 4. Fallback per precisione nominale
        legacy_count = self._bridge_nodes_legacy(target_vault)
        
        return bridges_created + legacy_count
