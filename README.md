---

<div align="center">

### 👤 Chi sono

**Giuseppe Lobbene** — Appassionato di programmazione, architetture software e ricerca tecnologica.

Non sono un ingegnere formato nelle grandi aziende tech. Sono qualcuno che ha scelto di **imparare facendo**, spinto da una curiosità genuina per l'evoluzione dell'intelligenza artificiale e dei sistemi software complessi.

In Italia, trovare un'azienda che punti davvero alla innovazione — che ti permetta di fare **ricerca**, sperimentare architetture all'avanguardia, e crescere tecnicamente mentre costruisci qualcosa di nuovo — è una sfida rara. La realtà del mercato del lavoro italiano nel settore IT è spesso quella di mantenere sistemi legacy o implementare soluzioni già consolidate altrove.

**NeuralVault nasce da questa frustrazione trasformata in energia creativa.**

È il risultato di centinaia di ore di studio autonomo su paper di ricerca (ICLR, NeurIPS), sperimentazione con Rust, Python e architetture distribuite, e un'ostinazione nel voler capire *come funzionano davvero* le cose — non solo come si usano.

> *"Se nessuno ti offre la possibilità di fare ricerca, falla da solo."*

</div>

---

## 🏺 NeuralVault — The Sovereign Agentic Memory Engine

> **"Non un database vettoriale. Un'architettura di orchestrazione agentica autonoma."**

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue?logo=python)](https://www.python.org/)
[![Rust](https://img.shields.io/badge/Core-Rust%20%2B%20PyO3-orange?logo=rust)](https://www.rust-lang.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Version](https://img.shields.io/badge/version-1.0.0%20Enterprise%20Mesh-purple)](CHANGELOG.md)
[![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20macOS%20%7C%20Windows-lightgrey)](https://github.com)

---

## Indice

- [Cos'è NeuralVault](#cosè-neuralvault)
- [Stato del Progetto (Onesto)](#stato-del-progetto-onesto)
- [Architettura](#architettura)
- [Installazione](#installazione)
- [Quick Start](#quick-start)
- [Dashboard Aura Nexus](#dashboard-aura-nexus)
- [Aura Bridge (Browser Extension)](#aura-bridge-browser-extension)
- [API Reference](#api-reference)
- [Comparazione con i Competitor](#comparazione-con-i-competitor)
- [Benchmark](#benchmark)
- [Use Cases](#use-cases)
- [Roadmap](#roadmap)

---

## Cos'è NeuralVault

NeuralVault è un **motore di memoria agentica locale-first** costruito attorno a un'idea semplice ma radicale: la conoscenza non dovrebbe essere statica. Dovrebbe **sbiadire**, **consolidarsi**, **rafforzarsi** e **connettersi** — esattamente come fa la memoria biologica.

A differenza dei database vettoriali tradizionali (Chroma, Pinecone, Weaviate), NeuralVault non si limita a cercare. **Pensa, organizza e dimentica in modo selettivo**, mantenendo solo l'essenza di ciò che è stato elaborato.

### Cosa fa, concretamente:

1. **Indicizza** testi, codice, PDF e URL trasformandoli in vettori semantici ad alta fedeltà.
2. **Connette** i concetti tramite un grafo di relazioni semantiche (PREREQUISITE, CITES, CONTRADICTS, SEQUENTIAL...).
3. **Decade** i ricordi inutilizzati seguendo la curva di Ebbinghaus, distillando la conoscenza stantia in **Ghost Memories** (riassunti sintetici).
4. **Rinforza** i ricordi ogni volta che vengono recuperati con successo (Spaced Repetition).
5. **Coordina** uno sciame di agenti AI autonomi (Neural Lab) che evolvono il grafo della conoscenza anche quando sei offline.
6. **Autentica e Verifica** l'integrità della memoria tramite un **Sovereign Ledger** (Blockchain Merkle-Tree), garantendo che i dati non siano stati manomessi.
7. **Sincronizza** la memoria con altri Vault sulla rete via Gossip Protocol.

---

## Dual-Mode: Per gli Umani **e** per le IA

Una delle domande più frequenti è: *"NeuralVault è uno strumento per l'utente umano o per i modelli AI?"*

**La risposta è: entrambi — con lo stesso Vault, due lenti diverse.**

### Come funziona per un utente umano

NeuralVault offre un'esperienza comparabile a Supermemory o Notion AI:

- **Dashboard Aura Nexus** con nebula 3D interattiva, Neural Chat e Node Inspector → esplori e interroghi visivamente la tua memoria.
- **Neural Chat** (`/api/chat`) → fai una domanda in linguaggio naturale, il Vault risponde attingendo ai suoi ricordi.
- **Aura Bridge** (estensione Chrome) → catturi contenuti mentre navighi sul web, li ritrovi cercando per concetto.
- **Time Machine** → esplori come la tua conoscenza si è evoluta nel tempo.

### Come funziona per un agente LLM

Lo stesso identico Vault, interrogato via API, si comporta come una **memoria a lungo termine per modelli LLM**:

- `vault.query("argomento")` restituisce il **contesto semantico pre-digerito** ideale da inserire nel system prompt.
- Ogni risultato include un **`cognitive_score`** → l'LLM sa quali ricordi sono "freschi e rinforzsati" vs "sbiaditi" e può pesarli di conseguenza.
- La **Ghost Memory** (distillazione cognitiva) riduce il rumore: invece di recuperare 50 chunk simili, ottieni un riassunto sintetico delle conoscenze consolidate — fondamentale per non sprecare token di contesto.
- Il **`logic_weight`** e l'**`emotional_weight`** delle sinapsi orientano il retrieval verso i percorsi logicamente prioritari, non solo quelli matematicamente simili.

### Schema: un Vault, due utilizzi

```
                 ┌─────────────────────────────┐
                 │         NEURALVAULT          │
                 │    (Unico Grafo Cognitivo)   │
                 └───────────┬─────────────────┘
                             │
              ┌──────────────┴──────────────────┐
              │                                 │
    HUMAN MODE (Dashboard)              AI MODE (API)
              │                                 │
   Dashboard 3D visiva              query() → context
   Neural Chat (chat UI)            cognitive_score filtro
   Node Inspector                   Ghost Memory distillata
   Time Machine Slider              logic/emotional weight
   Aura Bridge (cattura web)        Speculative Preloader
```

### Il ciclo virtuoso

Il punto più importante: le due modalità **si potenziano a vicenda**.

> Quando un utente umano usa la dashboard e consulta frequentemente un nodo (o lo segna come importante), aumenta il suo `access_count` e il suo peso cognitivo. La prossima volta che un agente LLM interroga il Vault sullo stesso argomento, quel nodo riceverà automaticamente priorità nel retrieval.

**L'umano rinforza la memoria → l'IA la usa in modo più preciso → l'IA porta risultati migliori all'umano → l'umano interagisce di più → il ciclo continua.**

Questa è la differenza fondamentale con Supermemory: Supermemory è progettato **esclusivamente** per l'utente umano. NeuralVault è progettato per entrambi — e li fa **cooperare sulla stessa base di conoscenza**.

---

## Stato del Progetto (Onesto)

> Questa sezione è fondamentale. Leggi attentamente cosa è **implementato e funzionante**, cosa è **funzionante ma simulato** e cosa è ancora **un'architettura in costruzione**.

### ✅ Implementato e Funzionante

| Componente | Modulo | Note |
|---|---|---|
| Indice HNSW | `neuralvault_rs/` (Rust) | Core ad alte prestazioni, compilato |
| Quantizzazione TurboQuant | `index/turboquant.py` | PRQ + DABA attivi |
| Memory Tier System | `memory_tiers.py` | Working (LRU) + Episodic (AOBF/AegisLog) |
| DuckDB Metadata Prefilter | `retrieval/prefilter.py` | SQL analytics attivi |
| Hybrid Fusion (RRF) | `retrieval/fusion.py` | Dense + Sparse + Graph fusione |
| Cognitive Decay Daemon | `index/cognitive.py` | Ebbinghaus Decay attivo |
| Ghost Memory (Wisdom) | `index/cognitive.py` | Distillazione cluster attiva |
| Bio-Mimetic Synapses | `index/node.py` | logic_weight + emotional_weight |
| Neural Lab Orchestrator | `neural_lab.py` | Swarm 4 agenti + Blackboard (Zero-Waste) |
| Agent007 Hard Memory | `agent007_intelligence.py` | Entità + Relazioni in DuckDB |
| Agent007 NER Engine | `agent007_intelligence.py` | Motore Heuristics-NER attivo (Local-First) |
| Cognitive Weather | `neural_lab.py` | Metriche hardware reali (CPU/Cache/Agents) |
| Agent007 Lab (Avversariale) | `agent007_lab.py` | Dibattito Prosecutor/Defender |
| Sovereign Consensus Log | `network/consensus.py` | Log binario mmap |
| Sovereign Ledger | `network/ledger.py` | Blockchain Merkle-Tree attiva (Audit / Integrity) |
| Gossip Mesh Protocol | `network/gossip.py` | Sincronizzazione async tra nodi |
| Sovereign Shield (Privacy) | `security/homomorphic.py` | Proiezione JL (non CKKS completo) |
| REST API (FastAPI) | `api.py` | 15+ endpoint attivi |
| Dashboard Aura Nexus | `dashboard/index.html` | 3D, Lab, Analytics, Chat |
| Aura Bridge Extension | `aura-extension/` | Chrome Extension MV3 |
| Hardware Pinning (Rust) | `neuralvault_rs/src/lib.rs` | mlock su Unix |
| Self-Healing Graph | `index/healing.py` | Pruning archi + Active Recovery Rollback |
| Matryoshka Embeddings | `index/matryoshka.py` | Multi-level vector slicing |
| Spectral Importance Tracker | `index/innovations.py` | Domain-Adaptive Query |
| Speculative Preloader | `retrieval/speculative.py` | Prefetch asincrono |

### ⚠️ Funzionante ma Parzialmente Simulato

| Componente | Stato | Cosa manca |
|---|---|---|
| Agent007 Lab Verdetti | Logica presente, vulnerability score random | Connessione a LLM locale per analisi reale |
| Homomorphic Shield | JL projection (preserva distanze) | Non è vera crittografia CKKS/Paillier |

### 🚧 Architettura in Costruzione

| Feature | Stato |
|---|---|
| RAFT Full Consensus (multi-nodo) | Struttura presente, logica elezione base |
| NVIDIA VRAM HBM Pinning diretto | Richiede librerie CUDA specifiche |
| L2 Blockchain Anchor | `api/ledger/status` | Mockup L2 attivo. Ready for Web3 bridging. |

---

## Architettura

```
┌─────────────────────────────────────────────────────────────────┐
│                     NEURALVAULT v1.0.0                          │
│                   "Enterprise Mesh Edition"                     │
├──────────────────┬──────────────────┬───────────────────────────┤
│  INGESTION LAYER │  COGNITIVE LAYER │    RETRIEVAL LAYER        │
│                  │                  │                           │
│  SovereignParser │ EbbinghausEngine │  AdaptiveHNSW (Rust)     │
│  (AST + Struct)  │ CognitiveDecay   │  TurboQuant (PRQ+DABA)   │
│  AutoKnowledge   │ WisdomSummarizer │  MatryoshkaSearch         │
│  Linker          │ GhostMemory      │  FusionRanker (RRF)       │
│                  │ DecayDaemon      │  DuckDB Prefilter (SQL)   │
├──────────────────┴──────────────────┴───────────────────────────┤
│                      KNOWLEDGE GRAPH                            │
│  VaultNode (vector + text + edges) + SemanticEdge               │
│  RelationType: CITES, CONTRADICTS, PREREQUISITE, SEQUENTIAL...  │
│  Bio-Mimetic: logic_weight + emotional_weight per arco          │
├─────────────────┬───────────────────┬───────────────────────────┤
│  MEMORY TIERS   │  NEURAL LAB       │  ENTERPRISE MESH          │
│                 │                   │                           │
│  Working (LRU)  │  4 Agents Swarm   │  Gossip Protocol          │
│  Episodic (AOBF)│  NeuralBlackboard │  SovereignLedger (Merkle) │
│  Semantic (PKT) │  Circadian Engine │  SovereignConsensus (Raft)│
│  MatryoshkaTier │  Mission Control  │  ShardManager (Warp)      │
├─────────────────┴───────────────────┴───────────────────────────┤
│                    HARDWARE LAYER                               │
│  Silicon-Agnostic · ARM NEON/SVE · x64 AVX-512/AMX             │
│  Apple Metal · NVIDIA CUDA · Hardware Memory Pinning (mlock)    │
└─────────────────────────────────────────────────────────────────┘
```

### I Pilastri dell'Architettura

---

### 1. 🦀 Core HNSW in Rust (`neuralvault_rs/`)

Il cuore di NeuralVault è scritto in **Rust** e compilato come modulo Python nativo via **PyO3/Maturin**.

**Cosa fa:**
- Indice **HNSW** (Hierarchical Navigable Small World) per la ricerca ANN (*Approximate Nearest Neighbor*).
- Calcolo vettoriale con **SIMD auto-detection**: su Intel/AMD usa AVX-512, su Apple/ARM usa NEON/SVE, su NVIDIA Grace usa AArch64.
- **Hardware Memory Pinning** (`mlock`) per bloccare le strutture dati critiche nella RAM fisica, prevenendo lo swap su disco.

**Cosa NON fa (onestà):**
- Non ha ancora la gestione diretta delle memorie HBM4 di NVIDIA Rubin (richiederebbe CUDA driver specifici ancora non rilasciati publicly al momento della stesura).

```rust
// neuralvault_rs/src/distance.rs
// SIMD auto-detection via simsimd library
pub fn cosine_distance(a: &[f32], b: &[f32]) -> f32 {
    1.0 - f32::cosine(a, b).unwrap_or(0.0) as f32
    // Esegue AVX-512 su Intel, NEON su ARM, SVE su Grace — automaticamente.
}
```

---

### 2. 🧠 Cognitive Decay Engine (`index/cognitive.py`)

Implementazione della **curva dell'oblio di Ebbinghaus**: `R = e^(-λt)`.

**Formula aggiornata (v3.0 Bio-Mimetic):**
```
strength = importance × e^(-λ / (0.5 + emotional_weight) × elapsed_hours) + min(access_count × 0.05, 0.4)
```

- `emotional_weight = 1.0`: dati critici/urgenti, decadimento quasi azzerato.
- `emotional_weight = 0.0`: dati di bassa priorità, decadimento rapido.
- `access_count`: ogni query rinforza il ricordo (Spaced Repetition biologico).

**Ghost Memory (v0.6.0):** Quando un cluster di nodi scende sotto il 15% di forza, il `CognitiveDecayDaemon` li converte in un singolo **Ghost Memory Node** che contiene:
- Il centroide semantico medio di tutti i nodi originali.
- Le entità chiave estratte da Agent007.
- Il periodo di vita originale (data inizio/fine).
- I frammenti testuali più significativi (mosaico).

---

### 3. 🗺️ Knowledge Graph & Bio-Mimetic Synapses (`graph/graph.py`, `index/node.py`)

Ogni relazione tra nodi ora ha **tre pesi**:

| Campo | Significato | Range |
|---|---|---|
| `weight` | Similarità semantica coseno | 0.0 – 1.0 |
| `logic_weight` | Rilevanza logica per il task corrente (impostabile dagli agenti) | 0.0 – 1.0 |
| `emotional_weight` | Urgenza / importanza memoriale del legame | 0.0 – 1.0 |

La traversal BFS del grafo moltiplica tutti e tre i pesi nella formula dello score:
```python
new_score = current.score × edge.weight × multiplier × edge.logic_weight × (0.7 ^ hop)
```

Tipi di relazione supportati: `CITES`, `CONTRADICTS`, `UPDATES`, `PREREQUISITE`, `EXAMPLE_OF`, `SAME_ENTITY`, `SEQUENTIAL`, `SYNAPSE`.

---

### 4. 🏗️ TurboQuant (`index/turboquant.py`)

**Polar-Recursive Quantization (PRQ)** con **Domain-Adaptive Bit Allocation (DABA)**.

Invece di quantizzare tutti i vettori con la stessa precisione, NeuralVault analizza le dimensioni più discriminanti del dominio e alloca più bit dove servono davvero.

- **Risparmio di memoria:** 85-89% su vettori a 1024 dimensioni.
- **Recall@10 preservato:** > 0.90 in modalità High-Precision.
- **Due fasi di ricerca:** Stage 1 binario (Hamming distance) per screening rapido, Stage 2 preciso sui candidati selezionati.

---

### 5. 🏛️ Neural Lab — Multi-Agent Swarm (`neural_lab.py`)

Uno sciame di **4 agenti** sempre attivi in background, coordinati tramite una **Synaptic Blackboard** (ThoughtMesh) persistente su DuckDB.

| Agente | Ruolo | Comportamento |
|---|---|---|
| **L'Archivista Prime** | Organizzazione | Cataloga e metadatetica ogni inserimento |
| **Analista Alpha** | Pattern Recognition | Trova correlazioni nascoste nei cluster |
| **Creativo Omega** | Sintesi | Genera nuove ipotesi e connessioni inattese |
| **Il Guardiano** | Coerenza | Verifica l'integrità logica del Vault |

Il **Circadian Engine** esegue task di manutenzione ogni 5 minuti (configurabile): memory gardening, scan contraddizioni, e consolidamento sinapsi deboli.

---

### 6. 🕵️ Agent007 — Hard Memory + Lab (`agent007_intelligence.py`, `agent007_lab.py`)

Mentre il sistema vettoriale gestisce la **Memoria Soft** (sfumature semantiche), Agent007 gestisce la **Memoria Hard**: fatti discreti, entità e relazioni.

- **Hard Memory Tables:** `agent007_entities` e `agent007_relations` in DuckDB.
- **Propagazione Tensione:** Ogni nuovo nodo verifica se crea "dissonanza cognitiva" con i nodi esistenti.
- **Digital Courtroom:** Un dibattito avversariale (Prosecutor vs Defender) valuta le vulnerabilità di ogni dato.

---

### 7. 🛰️ Enterprise Mesh (`network/`)

**Gossip Protocol** (`network/gossip.py`):
- Ogni inserimento viene propagato asincronicamente agli altri nodi Vault nella rete.
- Anti-loop: il nodo ricevente ignora i dati già presenti.

**Sovereign Ledger** (`network/ledger.py`):
- Ogni batch di inserimento genera un **Merkle Root** e viene aggiunto a una catena.
- Permette di verificare in qualsiasi momento che la memoria non sia stata manomessa.

**Sovereign Consensus** (`network/consensus.py`):
- Log binario memory-mapped (128 byte per entry, zero overhead Python).
- Binary search per recovery istantanea post-crash.
- UDP Gossip Beacon per sincronizzazione di stato.

---

### 8. 💾 Memory Tier System (`memory_tiers.py`)

Tre livelli gerarchici di memorizzazione:

```
Working Tier (LRU Cache, RAM)  ← Accesso più rapido
    ↓ eviction
Episodic Tier (LMDB, SSD)      ← Persistenza atomica
    ↓ consolidation
Semantic Tier (Parquet/DuckDB) ← Cold storage analitico
```

Con supporto per **Lazy Invalidation**: se un nodo in RAM è obsoleto (versione inferiore), viene ricaricato automaticamente dal tier persistente.

---

## Installazione

### Prerequisiti

| Requisito | Versione minima | Note |
|---|---|---|
| Python | 3.11+ | Obbligatorio |
| Rust + Cargo | 1.75+ | Per il core HNSW |
| pip | 23+ | `pip install --upgrade pip` |
| RAM | 4 GB | 8 GB consigliati per dataset reali |

**Installazione Rust (se non presente):**
```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source ~/.cargo/env
```

### Installazione Rapida

```bash
# 1. Clona il repository
git clone https://github.com/your-org/neuralvault
cd neuralvault

# 2. Usa lo script di deploy automatico (consigliato)
bash deploy.sh

# 3. Oppure, installazione manuale:
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

pip install --upgrade pip setuptools wheel maturin
pip install -r REQUIREMENTS_FULL.txt

# 4. Compila il core Rust (OBBLIGATORIO per le prestazioni)
cd neuralvault_rs/
maturin develop --release
cd ..

# 5. Avvia il server
python api.py
# Il server è disponibile su http://localhost:8001
```

### Installazione per Sviluppo

```bash
pip install -e ".[full,dev]"
cd neuralvault_rs && maturin develop && cd ..
```

### Su Windows

**Nota:** `mlock` (Hardware Pinning) non è disponibile su Windows nativamente; il sistema funziona comunque senza pinning. Il resto del codice è completamente cross-platform.

```powershell
# Installa rustup da https://rustup.rs
# Poi:
pip install -r REQUIREMENTS_FULL.txt
cd neuralvault_rs
maturin develop --release
cd ..
python api.py
```

---

## Quick Start

### Esempio Base: Indicizzare e Cercare

```python
from __init__ import NeuralVaultEngine
from index.node import VaultNode
import numpy as np

# 1. Avvia il Vault (la prima volta crea la struttura dati)
vault = NeuralVaultEngine(dim=1024, data_dir="./mio_vault")

# 2. Inserisci un documento
vault.upsert_text(
    "NVIDIA ha annunciato Grace Blackwell GB200 con memoria unificata CPU-GPU.",
    metadata={"source": "tech_news", "importance": 0.9}
)

# 3. Cerca semanticamente
results = vault.query("processori ARM di nuova generazione per AI", k=5)
for r in results:
    print(f"[{r.final_score:.3f}] {r.node.text[:80]}...")
    print(f"  Forza cognitiva: {r.cognitive_score:.2f}")
```

### Esempio Avanzato: Grafo con Sinapsi Bio-Mimetiche

```python
from index.node import VaultNode, SemanticEdge, RelationType

# Crea due nodi correlati
n1 = VaultNode(id="doc_gpu", text="Le GPU modere usano HBM3e per larghezze di banda >1TB/s")
n2 = VaultNode(id="doc_ai", text="I modelli transformer richiedono alta larghezza di banda di memoria")

# Connettili con una sinapsi logicamente importante
n1.add_edge(
    target_id="doc_ai",
    relation=RelationType.PREREQUISITE,
    weight=0.9
)
# Imposta il logic_weight alto: questo collegamento è vitale per il task
n1.edges[-1].logic_weight = 1.0
n1.edges[-1].emotional_weight = 0.8  # Urgente: non deve sbiadire presto

vault.upsert_batch([n1, n2])

# Query con espansione del grafo
results = vault.query("bandwidth memoria AI", k=3, intent="relational")
```

### Esempio: Ingestione di Codice Python

```python
# Il parser AST estrae automaticamente classi e funzioni
with open("mio_modulo.py", "r") as f:
    code = f.read()

vault.upsert_text(code, metadata={"source": "mio_modulo.py"})
# Vengono creati nodi separati per ogni classe e funzione
# e collegati tramite sinapsi SEQUENTIAL automatiche
```

### Esempio: SDK Per Applicazioni Esterne

```python
from vault_sdk import NeuralVaultClient

client = NeuralVaultClient(base_url="http://localhost:8001")

# Ingestione
client.synapse_text("Testo importante", metadata={"priority": "high"})

# Ricerca
results = client.query("argomento di ricerca", limit=5)
```

---

## Dashboard Aura Nexus

La dashboard è disponibile su `http://localhost:8001` dopo aver avviato `python api.py`.

### Sezioni della Dashboard

#### 1. Memory Overview (3D)
Visualizzazione 3D della nebula di memoria usando **Three.js**. Ogni punto è un nodo, il colore ne indica il tipo. Il **Time Machine Slider** permette di osservare l'evoluzione della conoscenza nel tempo (filtra i nodi per data di creazione).

- **Web Foraging Bar**: incolla un URL per indicizzarlo direttamente nel Vault.
- **EVOLVE Button**: avvia la scoperta di nuove sinapsi latenti.
- **Node Inspector**: clicca su un punto per vedere il testo, i metadati e il report Agent007 del nodo.

#### 2. Neural Lab
Pannello di controllo dello sciame di agenti. Visualizza:
- **Agent Swarm**: stato e capacità di ognuno dei 4 agenti.
- **ThoughtMesh Board**: messaggi in tempo reale tra gli agenti.
- **Cognitive Weather Widget**: pressione operativa, hit-rate cache, numero agenti attivi.
- **Mission Control**: invia una missione collettiva a tutto lo sciame.

#### 3. Neural Nets
Grafo interattivo delle relazioni tra nodi, renderizzato con **Cytoscape.js**. Permette di esplorare visivamente le connessioni semantiche.

#### 4. Neural Chat
Interfaccia di dialogo con la memoria del Vault. Combina la **Memoria Soft** (vettoriale) e la **Memoria Hard** (Agent007 entità) per fornire risposte contestualizzate.

#### 5. Analytic Tiers
- **Cognitive Density Chart**: densità della conoscenza nel tempo.
- **Knowledge Growth Chart**: crescita dei nodi.
- **Hardware Observatory**: utilizzo CPU core-per-core in tempo reale, RAM, embedding engine attivo, DNA Trace dell'hardware.
- **Compute Mode Selector**: ECO / HYBRID / WARP.

#### 6. Config
- **Intelligence Tier**: seleziona il modello AI (Llama3 locale, Gemini, o Consensus Mode multi-agente).
- **Visual Scale**: controlla la scala della visualizzazione 3D.
- **⚠️ Nuclear Purge**: elimina **tutta** la memoria in modo irreversibile (con conferma).

---

## Aura Bridge (Browser Extension)

**Aura Bridge** è un'estensione Chrome (Manifest V3) che permette di inviare contenuti dal browser direttamente al Vault.

### Installazione

1. Apri Chrome → `chrome://extensions/`
2. Attiva la **Modalità Sviluppatore** (in alto a destra).
3. Clicca **"Carica estensione non compressa"**.
4. Seleziona la cartella `aura-extension/`.

> **Prerequisito:** Il server NeuralVault deve essere in esecuzione su `http://localhost:8001`.

### Utilizzo

**Via Menu Conte stuale:**
1. Seleziona del testo su qualsiasi pagina web.
2. Clicca con il tasto destro → **"🧬 Synapse to NeuralVault"**.
3. Il testo selezionato viene indicizzato nel Vault con metadati URL e timestamp.

**Via Popup:**
1. Clicca sull'icona dell'estensione nella barra degli strumenti.
2. Scrivi o incolla un testo nel campo **"Quick synapse..."**.
3. Premi **SYNAPSE**.

### Ricevere Dati nel Vault

L'estensione invia i dati all'endpoint `POST /api/upload_text`. Il Vault li processa automaticamente, crea i nodi semantici e li collega al grafo.

---

## API Reference

> Tutti gli endpoint autenticati richiedono l'header `X-API-KEY: vault_secret_aura_2026` oppure il parametro `?api_key=vault_secret_aura_2026`.

### Endpoint Principali

| Metodo | Path | Autenticato | Descrizione |
|---|---|---|---|
| `GET` | `/` | No | Dashboard HTML |
| `POST` | `/api/upload` | Sì | Upload file (multipart) |
| `POST` | `/api/upload_text` | Sì | Ingestione testo diretto |
| `POST` | `/api/ingest` | Sì | Ingestione con filename |
| `GET` | `/api/documents` | Sì | Lista sorgenti indicizzate |
| `POST` | `/api/chat` | Sì | Query + risposta contestuale |
| `POST` | `/api/analyze` | Sì | Avvia analisi avversariale |
| `GET` | `/api/report/{id}` | Sì | Recupera report vulnerabilità |
| `GET` | `/api/models/status` | Sì | Modelli Ollama installati |
| `POST` | `/api/models/install` | Sì | Installa modello via Ollama |
| `POST` | `/api/gossip/sync` | No | Sync Mesh da peer |
| `GET` | `/events` | No | SSE stream telemetria real-time |

### Esempio cURL

```bash
# Ingestione testo
curl -X POST http://localhost:8001/api/ingest \
  -H "X-API-KEY: vault_secret_aura_2026" \
  -H "Content-Type: application/json" \
  -d '{"text": "NeuralVault è un sistema di memoria agentica.", "filename": "test.txt"}'

# Chat / Query
curl -X POST http://localhost:8001/api/chat \
  -H "X-API-KEY: vault_secret_aura_2026" \
  -H "Content-Type: application/json" \
  -d '{"query": "cosa sai di NeuralVault?"}'
```

---

## Comparazione con i Competitor

> Questa sezione è **onesta e comparativa**. Non esistono benchmark apples-to-apples perfetti, ma le differenze architetturali sono reali e verificabili nel codice.

### NeuralVault vs Database Vettoriali Classici

| Caratteristica | ChromaDB | Pinecone | Weaviate | Qdrant | **NeuralVault** |
|---|---|---|---|---|---|
| **Tipo** | VDB Locale | VDB Cloud | VDB Hybrid | VDB Locale | Cognitive Memory Engine |
| **Decay / Oblio** | ❌ | ❌ | ❌ | ❌ | ✅ Ebbinghaus |
| **Graph Traversal** | ❌ | ❌ | ✅ (base) | ❌ | ✅ (Multi-hop + Bio-Mimetic) |
| **Agenti Autonomi** | ❌ | ❌ | ❌ | ❌ | ✅ (Neural Lab) |
| **Multi-Tier Memory** | ❌ | ❌ | ❌ | ❌ | ✅ (Working/Episodic/Semantic) |
| **Quantizzazione Adattiva** | ❌ | Binary | ✅ (base) | ✅ | ✅ PRQ + DABA |
| **Hard Memory (Entità)** | ❌ | ❌ | ⚠️ (classe) | ❌ | ✅ Agent007 DuckDB |
| **Integrity Ledger** | ❌ | ❌ | ❌ | ❌ | ✅ Merkle-Tree |
| **Gossip Sync** | ❌ | Cloud-only | ✅ | ✅ | ✅ (async) |
| **Local-First** | ✅ | ❌ | ⚠️ | ✅ | ✅ Sovereign |
| **Core** | Python | Cloud | Java/Go | Rust | Python + Rust |
| **Dashboard** | ❌ | ✅ (cloud) | ✅ (basic) | ✅ | ✅ 3D + Lab |

### NeuralVault vs Supermemory

[Supermemory](https://supermemory.ai) è un ottimo strumento per la **personal knowledge management** (PKM). La sua forza è nella facilità di ingestione da browser, API pulita, e integrazione con prodotti di terze parti.

| Aspetto | Supermemory | **NeuralVault** |
|---|---|---|
| **Target** | Utenti che salvano contenuti web | Agenti AI che necessitano di memoria evolutiva |
| **Architettura** | VDB standard + API cloud | Hybrid Cognitive Mesh (Vettori + Grafi + Decay) |
| **Decay** | Non presente | Nativo (Ebbinghaus) |
| **Agenti** | Non presenti | Swarm autonomo attivo |
| **Privacy** | Cloud-based | Completamente locale (Sovereign) |
| **Installazione** | SaaS, zero setup | Richiede setup (compila Rust) |
| **Semplicità** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Controllo** | ⭐⭐ | ⭐⭐⭐⭐⭐ |

**Onestà:** Supermemory è più semplice da usare oggi. NeuralVault è più potente ma richiede più configurazione.

### NeuralVault vs Mem0

Mem0 si focalizza sulla **memoria persistente per LLM**, con update automatici e supporto multi-modale.

| Aspetto | Mem0 | **NeuralVault** |
|---|---|---|
| **Approccio** | Memory-as-a-Service | Sovereign Engine |
| **Aggiornamento** | Automatico per LLM | Manuale + Autonomo (agenti) |
| **Decay** | ❌ | ✅ Biologico |
| **Privacy** | API remota | 100% locale |
| **Flessibilità** | Alta per LLM | Alta per agenti custom |

---

## Benchmark

### Risultati Interni (v0.5.2 "Synaptic" su Apple M-series)

> ⚠️ Questi benchmark sono stati eseguiti internamente e non sono stati validati da terze parti. I numeri sono reali ma le condizioni di test specifiche (hardware, dataset) possono NON essere comparabili con benchmark pubblici di altri prodotti.

| Test | Risultato | Condizioni |
|---|---|---|
| Stress Test Concorrenza | 10.588 query/sec, 0 errori | 10.000 utenti simultanei |
| Soak Test Longevità | 0% memory leak, 265MB δ-RAM | 25.000 operazioni continue |
| ANN Recall@10 (HNSW) | 0.90+ | PRQ-HP compression |
| Latenza Query p50 | < 12.5ms | M-series, HNSW Rust |
| Ingestione 25k nodi | ~155 secondi | 1024 dim + Agent007 NER |

**Nota Onesta sull'Ingestione:**  
L'ingestione è più lenta rispetto alla v0.4.6 (~71s) perché la v0.5.2 esegue in parallelo il Cognitive Framing, l'estrazione Agent007 NER e la scoperta automatica di sinapsi. Non è pura velocità di inserimento: è **velocità di comprensione**.

### Comparazione ANN (ann-benchmarks Framework)

NeuralVault ha un modulo compatibile con `ann-benchmarks` in `benchmarks/ann-benchmarks-main/ann_benchmarks/algorithms/neuralvault/`. Puoi eseguire il benchmark standardizzato con:

```bash
cd benchmarks/ann-benchmarks-main
python run.py --algorithm neuralvault --dataset glove-100-angular
```

---

## Use Cases

### 1. 🤖 Memoria Persistente per Agenti AI Locali

```python
# Collegato a un LLM via Ollama
vault = NeuralVaultEngine(dim=1024, data_dir="./agent_brain")

# L'agente apprende nuove informazioni
vault.upsert_text(meeting_transcript, metadata={"source": "meeting", "date": "2026-04-08"})

# Recupera contesto rilevante prima di rispondere
context = vault.query(f"discuss {user_question}", k=5)
system_prompt = "\n".join([r.node.text for r in context])
# → passa system_prompt al tuo LLM preferito
```

### 2. 📚 Knowledge Base Tecnica Auto-Organizzante

```python
# Indicizza un intero repository Git
import os
for root, dirs, files in os.walk("./my_project"):
    for f in files:
        if f.endswith(".py"):
            with open(os.path.join(root, f)) as fp:
                vault.upsert_text(fp.read(), metadata={"source": f})
# Il parser AST crea nodi separati per ogni classe/funzione
# e le collega semanticamente in automatico
```

### 3. ⚖️ Compliance Legale ed eDiscovery
Usa la bockchain di NeuralVault per garantire l'immutabilità delle prove digitali archiviate. Il Ledger fornisce la prova crittografica che ogni documento analizzato dall'IA è identico alla fonte originale senza manomissioni nel tempo.

### 4. 🧬 Proprietà Intellettuale in Ricerca Scientifica
Proteggi le tue intuizioni: ogni batch di dati ingerito nel Vault genera un timestamp notarile (L2 Anchor) che attesta la data di scoperta e la provenienza del dato, tutelando la tua IP su rete pubblica senza esporre i contenuti.

### 5. 🌐 Knowledge Mesh (Sedi Remote Sincronizzate)
In una rete mesh di più Vault, il Ledger garantisce che tutti i nodi condividano la stessa "Verità Aziendale", risolvendo conflitti di versione e garantendo un'unica linea temporale di eventi immutabili tra sedi distaccate.

### 4. 🏢 Enterprise Multi-Vault

```python
# Nodo A (Milano): inserisce un report
vault_a = NeuralVaultEngine(data_dir="./vault_milan")
vault_a.gossip.add_peer("http://192.168.1.50:8001")  # Nodo Roma
vault_a.upsert_text("Q1 2026 Revenue: +23% YoY")

# Il Gossip Protocol propaga automaticamente al Nodo B (Roma)
# senza intervento manuale
```

---

## Roadmap

### v1.0.0 ✅ (Attuale — "Enterprise Mesh")
- Core HNSW Rust + Hardware Pinning
- Cognitive Decay + Ghost Memory
- Neural Lab v2.0 (4 agenti)
- Bio-Mimetic Synapses (logic + emotional weight)
- Sovereign Ledger (Merkle)
- Gossip Mesh Protocol
- Aura Bridge Extension

### v1.1.0 
- [ ] Integrazione Ollama per NER real (Agent007 fully live)
- [ ] WebSocket stream per Dashboard real-time migliorata
- [ ] `remove_node()` completo con cascade HNSW
- [ ] Benchmark pubblici validati su dataset ann-benchmarks standard

### v1.2.0 (Zero-Waste Sovereign Persistence) 🟢 ATTUALE
- [x] **Phase 1: AOBF Binary Ring Buffer**: Implementazione dello storage Append-Only a dimensione fissa per eliminare l'allocazione fantasma (Zero-Waste). ✅
- [x] **Phase 2: Neural Circuit Breakers**: Integrazione di soglie di confidenza (70%) e protocolli "Human-in-the-loop" per la sicurezza dello Swarm. ✅
- [x] **Phase 3: Event-Driven Performance**: Campionamento Keyframe Salienti per l'ingestione multimodale (ottimizzazione termica Apple Silicon). ✅
- [ ] Fase 26: Snapshot del Grafo e Parquet Export (Rimozione totale WAL di DuckDB)
- [ ] Fase 27: Compattazione asincrona (Aegis Reaper GC)

### v2.0.0 (Medio Termine)
- [ ] RAFT Consensus completo (multi-nodo)
- [ ] Privacy Shield CKKS/Paillier (vera crittografia omomorfica)
- [ ] Matryoshka embedding nativo (integrazione BGE-M3/GTE)
- [ ] NVIDIA CUDA explicit memory management

---

## Installazione Dipendenze (Dettaglio)

```
# Core
numpy >= 1.26
scipy >= 1.10
msgpack >= 1.0
pandas >= 2.0
pyarrow >= 12.0      # Semantic Tier (Parquet)
lmdb >= 1.4.1        # Episodic Tier
duckdb >= 0.9.0      # Metadata Prefilter + Agent007

# Performance
maturin >= 1.1.0     # Compilatore Rust
pyo3 >= 0.19.0       # Bridge Rust/Python
bm25s >= 0.1.8       # Sparse search (BM25)

# API
fastapi >= 0.100.0
uvicorn >= 0.22.0
httpx >= 0.24.1      # Gossip Protocol
pydantic >= 2.0.0

# Security
cryptography >= 41.0.0

# AI/Embeddings
sentence-transformers >= 2.2.2  # BGE-M3 e simili
torch >= 2.0.0

# Dashboard
rich >= 13.4.2
psutil >= 5.9.5
```

---

## Struttura del Progetto

```
neuralvault/
├── __init__.py              # NeuralVaultEngine — cuore del sistema
├── api.py                   # FastAPI REST server (porta 8001)
├── neural_lab.py            # NeuralLabOrchestrator (swarm agenti)
├── memory_tiers.py          # MemoryTierManager (LRU + LMDB)
├── agent007_intelligence.py # Agent007 Hard Memory (NER)
├── agent007_lab.py          # Digital Courtroom (avversariale)
├── agent007_blueprint.py    # Mission architecture
├── vault_sdk.py             # Client SDK semplificato
├── quickstart.py            # Demo rapida
├── deploy.sh                # Script deploy automatico
│
├── index/
│   ├── hnsw.py              # AdaptiveHNSW (wrappa il core Rust)
│   ├── node.py              # VaultNode, SemanticEdge, QueryResult
│   ├── cognitive.py         # Decay Engine + WisdomSummarizer + Daemon
│   ├── turboquant.py        # TurboQuant PRQ + DABA
│   ├── sparse.py            # BM25S (sparse search)
│   ├── healing.py           # Self-Healing graph optimizer
│   ├── matryoshka.py        # Multi-level vector slicing
│   ├── innovations.py       # Spectral Importance Tracker (SIT)
│   └── sharding.py          # ShardManager (Neural Warp)
│
├── graph/
│   ├── graph.py             # ContextGraph (BFS + Greedy traversal)
│   ├── ingester.py          # AutoKnowledgeLinker
│   ├── gnn_layer.py         # GNN layer (sperimentale)
│   └── joint_space.py       # Spazio congiunto testo/grafo
│
├── retrieval/
│   ├── fusion.py            # FusionRanker (RRF) + Speculative Reranker
│   ├── prefilter.py         # DuckDB Metadata Prefilter
│   ├── parsers.py           # SovereignParser (AST + Structural)
│   ├── bridge.py            # LatentBridge (multi-modal alignment)
│   └── speculative.py       # Speculative Preloader (async prefetch)
│
├── network/
│   ├── consensus.py         # SovereignConsensus (binary mmap log)
│   ├── gossip.py            # GossipManager (peer sync)
│   └── ledger.py            # SovereignLedger (Merkle integrity)
│
├── security/
│   └── homomorphic.py       # SovereignShield (JL projection)
│
├── agent/
│   ├── session.py           # SessionManager + Feedback
│   ├── query_planner.py     # NeuralQueryPlanner
│   └── feedback.py          # Feedback loop
│
├── neuralvault_rs/          # Core Rust (HNSW + TurboQuant + Pinning)
│   ├── src/
│   │   ├── lib.rs           # Entry point PyO3
│   │   ├── hnsw_core.rs     # HNSW implementation
│   │   ├── distance.rs      # SIMD distance (simsimd)
│   │   └── turboquant.rs    # Polar Quantizer
│   └── Cargo.toml
│
├── dashboard/
│   └── index.html           # Aura Nexus Dashboard (Three.js + Cytoscape)
│
└── aura-extension/          # Chrome Extension MV3
    ├── manifest.json
    ├── background.js         # Service Worker + Context Menu
    └── popup.html/js         # Quick Synapse UI
```

---

## Contribuire

NeuralVault è un progetto open-source in fase attiva. Le aree dove il contributo è più utile:

1. **Connettore Ollama real per Agent007 NER** — la struttura è pronta, manca l'integrazione HTTP.
2. **Benchmark pubblici** — validazione su dataset ann-benchmarks standard con metodologia chiara.
3. **Test e Coverage** — la cartella `tests/` è al momento minimale.
4. **Windows Compatibility** — il codice Python è cross-platform, ma `mlock` non è disponibile su Windows.

---

## Licenza
COPYRIGHT GIUSEPPE LOBBENE @2026

---

> 🏺 **NeuralVault: Turning Information into Active Wisdom.**
> *Costruito per agenti. Temprato per la realtà. Sovrano per sempre.*
