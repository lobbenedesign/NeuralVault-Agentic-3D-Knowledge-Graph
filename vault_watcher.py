import os
import PyPDF2 # v1.2.0 Support
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from vault_sdk import NeuralVaultClient

class NewFileHandler(FileSystemEventHandler):
    def __init__(self, client):
        self.client = client

    def on_created(self, event):
        if event.is_directory: return
        filename = event.src_path
        ext = filename.lower()
        
        print(f"🕵️ Watcher: New file detected: {os.path.basename(filename)}")
        
        try:
            content = ""
            if ext.endswith(('.txt', '.py', '.md', '.log')):
                with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
            elif ext.endswith('.pdf'):
                # PDF Text Extraction logic
                with open(filename, 'rb') as f:
                    pdf = PyPDF2.PdfReader(f)
                    for page in pdf.pages:
                        content += page.extract_text() + "\n"
            
            if content:
                res = self.client.synapse_text(content, {
                    "source": os.path.basename(filename), 
                    "origin": "watcher",
                    "type": "pdf" if ext.endswith('.pdf') else "text"
                })
                print(f"✅ Auto-synapsed: {res.get('id')}")
        except Exception as e:
            print(f"❌ Watcher error processing {filename}: {e}")

if __name__ == "__main__":
    # Ensure watch directory exists
    WATCH_PATH = "./inbound_knowledge"
    if not os.path.exists(WATCH_PATH):
        os.makedirs(WATCH_PATH)
        
    client = NeuralVaultClient()
    event_handler = NewFileHandler(client)
    observer = Observer()
    observer.schedule(event_handler, WATCH_PATH, recursive=False)
    
    print(f"🛰️ NeuralVault Watcher active on: {os.path.abspath(WATCH_PATH)}")
    print("Drop files into this folder to sync them automatically.")
    
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
