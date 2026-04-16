import ast
import re
import hashlib
from typing import List, Dict, Any

class SovereignParser:
    """Il 'Cervello' che decide come scomporre la conoscenza (v1.0 STRUTTURALE)."""
    
    @staticmethod
    def parse_python(code: str, filename: str = "source.py") -> List[Dict[str, Any]]:
        """Estrae Classi, Funzioni e Call Graph."""
        try:
            tree = ast.parse(code)
            chunks = []
            
            # Mappa delle definizioni per cross-referencing
            definitions = set()
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
                    definitions.add(node.name)

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
                    start_line = node.lineno
                    end_line = getattr(node, 'end_lineno', start_line + 5)
                    code_lines = code.split('\n')[start_line-1:end_line]
                    content = '\n'.join(code_lines)
                    
                    # Sanificazione ID Univoco (v1.6) - Previene collisioni tra moduli
                    path_hash = hashlib.md5(filename.encode()).hexdigest()[:6]
                    safe_name = node.name.replace(".", "_")
                    node_id = f"{path_hash}__{safe_name}"

                    # Rilevamento chiamate interne per linkare il grafo
                    calls = []
                    for child in ast.walk(node):
                        if isinstance(child, ast.Call) and isinstance(child.func, ast.Name):
                            if child.func.id in definitions:
                                calls.append(f"{path_hash}__{child.func.id}")

                    chunks.append({
                        "id": node_id,
                        "text": f"[{'Class' if isinstance(node, ast.ClassDef) else 'Function'}] {node.name}\n{content}",
                        "metadata": {
                            "type": "code_structure",
                            "name": node.name,
                            "kind": "class" if isinstance(node, ast.ClassDef) else "function",
                            "file": filename,
                            "refs": calls,
                            "v": "Structural_v1.3"
                        }
                    })
            return chunks
        except Exception as e:
            print(f"⚠️ AST Parser Fail: {e}")
            return []

    @staticmethod
    def parse_structural_text(text: str, source: str = "doc") -> List[Dict[str, Any]]:
        """Scompone manuali e testi basandosi sulla struttura (Titoli, Capoversi)."""
        # Regex per titoli Markdown o Sezioni numerate (es. 1.1 Introduzione)
        sections = re.split(r'\n(?=# |## |### |\d+\.\d+ )', text)
        chunks = []
        
        for i, section in enumerate(sections):
            if len(section.strip()) < 50: continue # Salta i titoli vuoti
            
            # Se la sezione è troppo lunga, applichiamo un chunking semantico leggero
            if len(section) > 1500:
                paragraphs = [p.strip() for p in section.split("\n\n") if len(p.strip()) > 50]
                for j, p in enumerate(paragraphs):
                    chunks.append({
                        "id": f"{source}_s{i}_p{j}",
                        "text": p,
                        "metadata": {"type": "manual_section", "source": source, "index": i}
                    })
            else:
                chunks.append({
                    "id": f"{source}_s{i}",
                    "text": section.strip(),
                    "metadata": {"type": "manual_section", "source": source, "index": i}
                })
        return chunks

def extract_structural_chunks(text: str, filename: str = "unknown") -> List[Dict[str, Any]]:
    """Logica di Routing Universale (v1.2)."""
    fn = filename.lower()
    if fn.endswith(".py"):
        return SovereignParser.parse_python(text, filename)
    
    # Per tutto il resto del codice e testi strutturati
    structural_exts = (".md", ".txt", ".pdf", ".html", ".js", ".css", ".cpp", ".h", ".xml", ".sql", ".yaml", ".json")
    if fn.endswith(structural_exts):
        return SovereignParser.parse_structural_text(text, filename)
    
    return [] 
