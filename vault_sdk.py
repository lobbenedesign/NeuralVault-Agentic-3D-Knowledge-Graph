import requests
import json
from typing import Optional, Dict, Any

class NeuralVaultClient:
    """
    NeuralVault SDK v1.0
    Professional integration client for local-first knowledge indexing.
    """
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url

    def synapse_text(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Send text to the vault for indexing and projection."""
        payload = {
            "text": text,
            "metadata": metadata or {}
        }
        response = requests.post(f"{self.base_url}/api/upload_text", json=payload)
        response.raise_for_status()
        return response.json()

    def query(self, text: str, limit: int = 5) -> Dict[str, Any]:
        """Search for semantic memories in the vault."""
        params = {"q": text, "limit": limit}
        # Assuming we have a search endpoint (if not, we'll add it)
        response = requests.get(f"{self.base_url}/api/search", params=params)
        return response.json()

    def get_stats(self) -> Dict[str, Any]:
        """Get telemetry data from the active kernel."""
        response = requests.get(f"{self.base_url}/stats")
        return response.json()

if __name__ == "__main__":
    # Test local connection
    client = NeuralVaultClient()
    try:
        print("🧬 SDK Test: Ingesting sample knowledge...")
        res = client.synapse_text("Il SDK di NeuralVault è ora attivo e comunicante.", {"type": "sdk_test"})
        print(f"✅ Success: {res}")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
