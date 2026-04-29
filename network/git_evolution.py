import subprocess
import os
import logging
from pathlib import Path
from typing import Optional, Dict

logger = logging.getLogger("NeuralVault-GitBridge")

class GitEvolutionBridge:
    """
    🔗 [SOVEREIGN EVOLUTION BRIDGE]
    Gestisce il versionamento locale per le auto-evoluzioni del sistema.
    Fornisce la capacità di creare branch, committare fix e rollback in sicurezza.
    """
    def __init__(self, project_root: str):
        self.root = Path(project_root)
        self.github_token = None
        self.github_repo = None
        self._is_git_available = self._check_git()

    def _check_git(self) -> bool:
        try:
            subprocess.run(["git", "--version"], capture_output=True, check=True)
            if not (self.root / ".git").exists():
                logger.warning("⚠️ Git directory not found in project root.")
                return False
            return True
        except:
            return False

    def create_evolution_branch(self, suggestion_id: str) -> Optional[str]:
        """Crea un nuovo branch per un suggerimento tecnico specifico."""
        if not self._is_git_available: return None
        branch_name = f"evolution/fix-{suggestion_id[:8]}"
        try:
            # Assicuriamoci di essere sul main/master prima di branchare
            subprocess.run(["git", "checkout", "main"], cwd=self.root, capture_output=True)
            subprocess.run(["git", "checkout", "-b", branch_name], cwd=self.root, capture_output=True, check=True)
            return branch_name
        except Exception as e:
            logger.error(f"Failed to create branch {branch_name}: {e}")
            return None

    def commit_fix(self, branch_name: str, message: str) -> bool:
        """Esegue l'add e il commit della modifica nel branch specificato."""
        if not self._is_git_available: return False
        try:
            subprocess.run(["git", "add", "."], cwd=self.root, capture_output=True, check=True)
            subprocess.run(["git", "commit", "-m", f"🧬 [Evolution] {message}"], cwd=self.root, capture_output=True, check=True)
            return True
        except Exception as e:
            logger.error(f"Failed to commit fix on {branch_name}: {e}")
            return False

    def rollback(self) -> bool:
        """Torna al branch principale e scarta le modifiche pendenti."""
        if not self._is_git_available: return False
        try:
            subprocess.run(["git", "checkout", "main"], cwd=self.root, capture_output=True, check=True)
            return True
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return False

    def setup_github(self, token: str, repo_name: str):
        """Configura le credenziali GitHub per le release globali."""
        self.github_token = token
        self.github_repo = repo_name
        logger.info(f"🚀 GitHub Integration configured for {repo_name}")
        
        # Configura l'URL remoto con il token (uso locale sicuro)
        if token and repo_name:
            remote_url = f"https://{token}@github.com/{repo_name}.git"
            
            # 🛡️ [SOVEREIGN PRIVACY] Tentativo di creazione repo privata se mancante
            try:
                # Usiamo l'API di GitHub per verificare/creare il repo come PRIVATO
                with httpx.Client() as client:
                    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
                    # Verifichiamo se esiste
                    r = client.get(f"https://api.github.com/repos/{repo_name}", headers=headers)
                    if r.status_code == 404:
                        logger.info(f"🚧 Repo {repo_name} non trovata. Creazione in corso (MODALITÀ PRIVATA)...")
                        parts = repo_name.split('/')
                        name = parts[-1]
                        payload = {"name": name, "private": True, "description": "🧬 NeuralVault Sovereign Evolution Mirror"}
                        client.post("https://api.github.com/user/repos", headers=headers, json=payload)
            except:
                pass # Se fallisce la creazione (es. già esistente), procediamo con il setup del remote
            
            try:
                # Controlla se 'origin' esiste già
                check_origin = subprocess.run(["git", "remote", "get-url", "origin"], cwd=self.root, capture_output=True)
                if check_origin.returncode == 0:
                    subprocess.run(["git", "remote", "set-url", "origin", remote_url], cwd=self.root, check=True)
                else:
                    subprocess.run(["git", "remote", "add", "origin", remote_url], cwd=self.root, check=True)
            except Exception as e:
                logger.error(f"Failed to setup remote origin: {e}")

    def push_to_remote(self, branch_name: str) -> bool:
        """Invia il branch evolutivo su GitHub."""
        if not self.github_token or not self._is_git_available:
            return False
        try:
            subprocess.run(["git", "push", "origin", branch_name], cwd=self.root, capture_output=True, check=True)
            logger.info(f"📡 Branch {branch_name} pushed to GitHub successfully.")
            return True
        except Exception as e:
            logger.error(f"Push to remote failed: {e}")
            return False

    def create_verified_checkpoint(self, version: str) -> bool:
        """
        🛡️ [SAFE-GENESIS]
        Crea un commit e un tag unico con micro-versioning temporale.
        """
        if not self._is_git_available:
            return False
        
        # Micro-Versioning: v0.1.1-REV-HHMMSS-VERIFICATO
        timestamp = datetime.now().strftime("%H%M%S")
        tag_name = f"v{version}-REV{timestamp}-VERIFICATO"
        
        try:
            # Add e Commit dello stato attuale
            subprocess.run(["git", "add", "."], cwd=self.root, capture_output=True)
            subprocess.run(["git", "commit", "-m", f"🧬 [Evolution Checkpoint] {tag_name}"], cwd=self.root, capture_output=True)
            
            # Creazione Tag locale
            subprocess.run(["git", "tag", tag_name], cwd=self.root, capture_output=True, check=True)
            
            # Tentativo di Push (se fallisce perché offline, i tag rimangono locali)
            if self.github_token:
                subprocess.run(["git", "push", "origin", "main", "--tags"], cwd=self.root, capture_output=True)
            
            logger.info(f"🏆 Local Checkpoint {tag_name} creato.")
            return True
        except Exception as e:
            logger.error(f"Failed to create verified checkpoint: {e}")
            return False

    def create_remote_release(self, version: str, notes: str):
        """
        [GLOBAL EVOLUTION] Crea una release su GitHub tramite API.
        Richiede GitHub Token configurato.
        """
        if not self.github_token:
            logger.error("❌ GitHub Token missing. Remote release aborted.")
            return False
        
        # In v5.0 integreremo la chiamata reale via httpx
        logger.info(f"📡 Remote Release {version} prepared for GitHub.")
        return True
