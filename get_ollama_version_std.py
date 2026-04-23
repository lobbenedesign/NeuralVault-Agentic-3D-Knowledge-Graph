import urllib.request
import json

def get_version():
    urls = ["http://127.0.0.1:11434/api/version", "http://localhost:11434/api/version"]
    for url in urls:
        try:
            with urllib.request.urlopen(url, timeout=3) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode())
                    return data.get("version", "Unknown")
        except:
            continue
    return "Offline"

print(get_version())
