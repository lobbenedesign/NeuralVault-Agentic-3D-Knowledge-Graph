import subprocess
import json

try:
    # Attempt to list models
    res_list = subprocess.run(["ollama", "list"], capture_output=True, text=True)
    # Attempt to show gemma4:e4b
    res_show = subprocess.run(["ollama", "show", "gemma4:e4b"], capture_output=True, text=True)
    
    with open("vault_data/model_check.log", "w") as f:
        f.write("--- OLLAMA LIST ---\n")
        f.write(res_list.stdout)
        f.write(res_list.stderr)
        f.write("\n\n--- OLLAMA SHOW GEMMA4:E4B ---\n")
        f.write(res_show.stdout)
        f.write(res_show.stderr)
except Exception as e:
    with open("vault_data/model_check.log", "w") as f:
        f.write(f"ERROR: {str(e)}")
