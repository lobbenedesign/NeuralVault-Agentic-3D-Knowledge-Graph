import os
import sys
import py_compile
import logging
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger("NeuralVault-Actuator")

class EvolutionActuator:
    """
    🛠️ [EVOLUTION ACTUATOR]
    Responsabile dell'applicazione fisica delle modifiche al codice sorgente.
    Include meccanismi di validazione sintattica pre-commit.
    """
    def __init__(self, project_root: str):
        self.root = Path(project_root)

    def apply_fix(self, file_path: str, line_number: int, new_content: str) -> Dict:
        """
        Applica chirurgicamente una modifica a un file .py.
        """
        full_path = self.root / file_path
        if not full_path.exists():
            return {"success": False, "error": f"File {file_path} not found."}

        try:
            with open(full_path, "r") as f:
                lines = f.readlines()

            # Backup temporaneo per validazione
            temp_path = full_path.with_suffix(".py.tmp")
            
            # Applicazione modifica (Se line_number è 0, aggiungiamo in fondo o cerchiamo match)
            if 0 < line_number <= len(lines):
                # Sostituzione riga specifica (1-indexed)
                lines[line_number - 1] = new_content + "\n"
            else:
                # Fallback: Append se non specificata riga valida
                lines.append("\n" + new_content + "\n")

            with open(temp_path, "w") as f:
                f.writelines(lines)

            # --- VALIDAZIONE SINTATTICA ---
            try:
                py_compile.compile(str(temp_path), doraise=True)
            except py_compile.PyCompileError as e:
                if temp_path.exists(): os.remove(temp_path)
                return {"success": False, "error": f"Syntax Error in suggested code: {e}"}

            # Se valida, sovrascriviamo l'originale
            os.replace(temp_path, full_path)
            logger.info(f"✅ [Actuator] Fix applied successfully to {file_path}")
            return {"success": True, "file": file_path}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def dry_run_diff(self, file_path: str, line_number: int, new_content: str) -> Optional[str]:
        """Genera un'anteprima (diff) della modifica senza applicarla."""
        full_path = self.root / file_path
        if not full_path.exists(): return None
        
        try:
            with open(full_path, "r") as f:
                old_content = f.readlines()
            
            new_lines = old_content.copy()
            if 0 < line_number <= len(new_lines):
                new_lines[line_number - 1] = new_content + "\n"
            else:
                new_lines.append(new_content + "\n")
                
            import difflib
            diff = difflib.unified_diff(
                old_content, new_lines, 
                fromfile=f"a/{file_path}", tofile=f"b/{file_path}"
            )
            return "".join(diff)
        except:
            return None
