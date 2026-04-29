"""
security/oauth_manager.py
─────────────────────────
Gestisce il flusso OAuth2 per i servizi esterni (Google/Microsoft).
Permette l'autenticazione sicura senza memorizzare password in chiaro.
"""

import os
import json
from pathlib import Path
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

class SovereignOAuthManager:
    SCOPES = [
        'https://mail.google.com/',
        'https://www.googleapis.com/auth/userinfo.email',
        'openid'
    ]

    def __init__(self, data_dir: Path):
        self.token_path = data_dir / "oauth_token.json"
        self.credentials_path = data_dir / "google_credentials.json"
        self.creds = None

    def get_credentials(self):
        """Carica o rinfresca i token OAuth2."""
        if self.token_path.exists():
            self.creds = Credentials.from_authorized_user_file(str(self.token_path), self.SCOPES)
        
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                try:
                    self.creds.refresh(Request())
                    self._save_token()
                except Exception:
                    self.creds = None # Token non più valido
            
        return self.creds

    def start_flow(self):
        """Avvia il flusso di autenticazione nel browser."""
        if not self.credentials_path.exists():
            raise FileNotFoundError(
                "❌ File 'google_credentials.json' mancante. Scaricalo dalla Google Cloud Console."
            )
        
        flow = InstalledAppFlow.from_client_secrets_file(
            str(self.credentials_path), self.SCOPES
        )
        # Avvia un server locale temporaneo per catturare il redirect
        self.creds = flow.run_local_server(port=0, host='127.0.0.1')
        self._save_token()
        return self.creds

    def _save_token(self):
        with open(self.token_path, 'w') as token:
            token.write(self.creds.to_json())

    def get_auth_string(self, user_email: str):
        """Genera la stringa XOAUTH2 per IMAP."""
        creds = self.get_credentials()
        if not creds: return None
        
        # Formato XOAUTH2: user=user@gmail.com\1auth=Bearer {token}\1\1
        auth_string = f"user={user_email}\1auth=Bearer {creds.token}\1\1"
        return auth_string
