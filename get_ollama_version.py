import httpx
import json

async def check_ollama_version():
    urls = ["http://127.0.0.1:11434/api/version", "http://localhost:11434/api/version"]
    for url in urls:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                r = await client.get(url)
                if r.status_code == 200:
                    return r.json().get("version", "Unknown")
        except Exception as e:
            continue
    return "Error: Could not connect to Ollama API"

import asyncio
print(asyncio.run(check_ollama_version()))
