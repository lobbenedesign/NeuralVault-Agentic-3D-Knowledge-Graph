"""
neuralvault.simulation_evolution (v2.6.6 Sovereign Edition)
────────────────────────────────────────────────────────
Script di dimostrazione dell'Evoluzione Organica.
Simula il comportamento di un agente e verifica il rinforzo sinaptico.
"""

import time
import numpy as np
import sys
import os
import shutil
from pathlib import Path

# Fix path for local imports
sys.path.append(str(Path(__file__).parent.parent))

from __init__ import NeuralVaultEngine
from index.node import RelationType
from rich.console import Console
from rich.table import Table
from rich.progress import Progress

console = Console()

def run_agent_simulation():
    console.print("[bold cyan]🔱 AVVIO SIMULAZIONE EVOLUZIONE — NEURALVAULT v2.6.6[/]\n", justify="center")
    
    DATA_DIR = Path("./evolved_data")
    if DATA_DIR.exists(): shutil.rmtree(DATA_DIR)
    
    # Inizializziamo il Vault in modalità Hybrid
    vault = NeuralVaultEngine(data_dir=DATA_DIR, dim=1024, use_rust=False)
    console.print(f"📁 Database inizializzato in: [bold]{DATA_DIR}[/]")
    
    # 1. Ingestione dati (Manuale Tecnico X-500)
    console.print("[yellow]Fase 1: Ingestione Knowledge Base Standard...[/]")
    vault.upsert_text(text="Protocollo di sicurezza per l'avvio della turbina.", metadata={"type": "security"}, node_id="CH_A")
    vault.upsert_text(text="Parametri di pressione dell'olio (Range: 40-50 PSI).", metadata={"type": "parameters"}, node_id="CH_B")
    vault.upsert_text(text="La valvola di spurgo deve essere chiusa prima dell'iniezione.", metadata={"type": "valves"}, node_id="CH_C")
    
    node_a = vault._nodes.get("CH_A")
    console.print(f"   [dim]Stato iniziale: Edges CH_A = {len(node_a.edges) if node_a else 0}[/]")
    time.sleep(0.3)

    # 2. Simulazione Sessione Agente
    console.print("\n[yellow]Fase 2: Sessione Agente 'Manutenzione AI'...[/]")
    # Usiamo il SessionManager interno
    session = vault._sessions.create_session(agent_id="service_bot_01")
    session_id = session.session_id
    
    with Progress() as progress:
        task = progress.add_task("[cyan]L'agente lavora sulla documentazione...", total=5)
        
        # Simula accessi ripetuti a CH_B e CH_C via Query
        for _ in range(5):
            vault.query("Quali valvole controllare per la pressione?")
            progress.update(task, advance=1)
            time.sleep(0.1)
            
        # Segnale esplicito di successo per i nodi coinvolti
        vault.feedback("CH_B", success=True)
        vault.feedback("CH_C", success=True)

    # 3. Consolidamento
    console.print("\n[yellow]Fase 3: Consolidamento Conoscenza (Fact Mining)...[/]")
    vault._sessions.close_session(session_id, vault._nodes)
    new_synapses = vault.evolve_graph()
    console.print(f"   [bold green]🧬 Synaptic Discovery: Create {new_synapses} nuove relazioni.[/]")
    
    # 4. Risultati della Simulazione
    node_b = vault._nodes.get("CH_B")
    node_c = vault._nodes.get("CH_C")
    
    if node_b and node_c:
        table = Table(title="Evoluzione del Grafo Sovereign", header_style="bold magenta")
        table.add_column("Nodo", style="cyan")
        table.add_column("Accessi", justify="right")
        table.add_column("Relazioni", style="green")
        table.add_column("Relevance", style="yellow")

        new_edges = [f"{e.target_id} ({e.relation.value})" for e in node_b.edges]
        table.add_row(
            "CH_B (Pressione)", 
            str(node_b.access_count),
            ", ".join(new_edges) if new_edges else "Nessuno",
            f"{node_b.agent_relevance_score:.2f}"
        )
        
        console.print(table)
    
    # 5. Simulazione Decay (Autoguarigione)
    console.print("\n[yellow]Fase 4: Simulazione Cognitive Decay...[/]")
    vault.apply_cognitive_decay(max_nodes=1) # Forza il decay per vedere l'effetto
    console.print(f"   [dim]Il sistema ha spostato i ricordi meno rilevanti nel Cold Tier.[/]")
    console.print(f"   [dim]Nodi attivi rimasti: {len(vault._nodes)}[/]")

    console.print("\n[bold green]✅ SIMULAZIONE COMPLETATA SU ARCHITETTURA v2.6.6[/]")
    vault.close()

if __name__ == "__main__":
    run_agent_simulation()
