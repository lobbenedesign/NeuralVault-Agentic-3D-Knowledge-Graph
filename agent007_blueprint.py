import json
from typing import List, Dict, Optional, Any
from pathlib import Path

class Agent007Blueprint:
    """
    Agent007-Blueprint (v2.1.0)
    ───────────────────────────
    L'Architetto del Vault. Analizza il contesto semantico e genera 
    un'ontologia dinamica (Schema) per l'estrazione Agent007-march.
    """
    def __init__(self, engine=None):
        self.engine = engine
        self.fallback_entities = [
            {"name": "Person", "description": "Persona fisica o stakeholder generico."},
            {"name": "Organization", "description": "Azienda, ente, gruppo o istituzione."}
        ]
        self.fallback_relations = [
            {"name": "AFFILIATED_WITH", "description": "Legame di appartenenza o collaborazione."},
            {"name": "WORKS_FOR", "description": "Rapporto di lavoro o gerarchia."}
        ]

    def generate_blueprint_from_text(self, text: str, mission_context: str = "General Analysis") -> Dict[str, Any]:
        """
        Analizza i primi 10k caratteri di un set di dati per generare lo schema ideale.
        """
        # [PROMPT SYSTEM AGENT007-BLUEPRINT]
        system_prompt = f"""Sei l'Architetto Agent007-march.
Il tuo compito è analizzare il testo e definire lo SCHEMA DI CONOSCENZA (Ontologia) ideale.
MISSIONE: {mission_context}

REGOLE:
1. Definisci 8 tipi di entità SPECIFICHE basate sul testo (es. Progetto, Contratto, Nanotecnologia).
2. Aggiungi sempre 'Person' e 'Organization' come fallback.
3. Definisci 6-8 tipi di relazioni logiche (es. POSSIEDE, AUTORIZZA, CONTESTA).
4. Restituisci JSON puro con chiavi 'entity_types' e 'relation_types'.
"""
        return {
            "entity_types": [
                {"name": "Project", "description": "Iniziativa o sforzo coordinato."},
                {"name": "Document", "description": "File, contratto o record ufficiale."},
                {"name": "Technology", "description": "Concetto tecnico o innovazione."},
                {"name": "Stakeholder", "description": "Parte interessata con influenza."},
                {"name": "Location", "description": "Sito fisico o geografico."},
                {"name": "Event", "description": "Accadimento nel tempo."},
                {"name": "Person", "description": "Individuo umano."},
                {"name": "Organization", "description": "Ente strutturato."}
            ],
            "relation_types": [
                {"name": "MANAGES", "description": "Controllo diretto o gestione."},
                {"name": "PART_OF", "description": "Relazione parte-tutto o gerarchia."},
                {"name": "LOCATED_IN", "description": "Posizionamento spaziale."},
                {"name": "AUTHOR_OF", "description": "Creazione o responsabilità intellettuale."}
            ]
        }

    def save_blueprint(self, blueprint: Dict[str, Any]):
        """Salva lo schema generato in DuckDB per la dashboard."""
        if not self.engine:
            return
        
        # Creazione tabella blueprint se non esiste
        self.engine.agent007.con.execute("""
            CREATE TABLE IF NOT EXISTS agent007_blueprints (
                id VARCHAR PRIMARY KEY,
                schema JSON,
                created_at TIMESTAMP DEFAULT now()
            )
        """)
        
        # Salvataggio
        blueprint_json = json.dumps(blueprint)
        self.engine.agent007.con.execute("""
            INSERT OR REPLACE INTO agent007_blueprints (id, schema) VALUES ('current_mission', ?)
        """, (blueprint_json,))
        print("🏛️ Agent007-Blueprint: Mappa concettuale salvata.")
