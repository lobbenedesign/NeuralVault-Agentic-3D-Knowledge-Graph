# 🌌 NEURAL VAULT: ARCHITETTURA TECNICA v4.0.1

Benvenuti nel manuale tecnico ufficiale di **Neural Vault**. Questo documento descrive l'architettura sovrana del sistema, mappando ogni modulo dalla persistenza binaria alla visualizzazione 3D in tempo reale. Il sistema bilancia velocità bruta e integrità crittografica per trasformare l'informazione in saggezza attiva.

---

## 📂 1. STRUTTURA DELLE CARTELLE: TARGET ARCHITECTURE (Fase 5.0)

*Nota di Audit: La seguente struttura rappresenta l'architettura modulare obiettivo. Attualmente, per massimizzare la velocità di sviluppo e ridurre i tempi di context-switching, il sistema opera con un approccio ibrido e altamente performante concentrato in `api.py` e `neural_lab.py`, con visualizzazione delegata a `/dashboard`.*

L'ecosistema in fase di consolidamento sarà organizzato in moduli atomici:

*   **`/` (Root)**: Contiene l'entry point dell'API (`api.py`), l'orchestratore (`neural_lab.py`) e il kernel dell'engine (`__init__.py`).
*   **`/index`**: Il cuore della memoria (HNSW, Lifecycle, TurboQuant, Cognitive Decay).
*   **`/graph`**: Gestione della topologia semantica e monitoraggio dell'entropia.
*   **`/retrieval`**: Pipeline di estrazione, Fusion Ranking e Multimodal Synapse Processing.
*   **`/network`**: Layer di comunicazione mesh, mDNS Discovery e Sovereign Ledger.
*   **`/storage`**: Persistenza fisica (Aegis-Log AOBF, Snapshot Engine).
*   **`/dashboard`**: Interfaccia di comando (CMD-SWARM) basata su Three.js.

---

## 🏗️ 2. COGNITIVE ENGINE (STORAGE E PERSISTENZA)

L'architettura bilancia velocità bruta e integrità crittografica su tre livelli (Tiers):

### 💎 Tier L1: Atomic Cache (RAM)
Accesso istantaneo per il rendering 3D a 60fps. I nodi più rilevanti sono mantenuti in memoria per query sub-millisecondo. Questa cache viene idratata proattivamente all'avvio tramite la **Hot Hydration**.

### 💎 Tier L2: AegisLogStore (AOBF)
Cuore binario a spreco zero. Utilizza un formato **Append-Only Binary Format** (ael) per garantire che ogni scrittura sia atomica.
- **The Tombstone Paradox**: Le eliminazioni non rimuovono fisicamente i dati istantaneamente, ma applicano una "lapide" (Tombstone) logica. Questo permette operazioni di cancellazione non bloccanti e rollback immediati.
- **Aegis Reaper (Compaction)**: Modulo asincrono che analizza il log binario e ricicla lo spazio fisico dei nodi eliminati durante i periodi di bassa attività hardware.

### 💎 Tier L3: Contextual Archive (DuckDB L2)
Il "Cervello Analitico" per i metadati e la ricerca ibrida SQL/Vector. DuckDB permette di eseguire query strutturate (es. "trovami tutti i PDF del 2023") incrociandole con la similarità semantica.

---

## 🤖 3. AGENTIC LOGIC: IL KINETIC SWARM

Il **Neural Lab Orchestrator** coordina uno sciame di 9 agenti specializzati che operano autonomamente nella nebula:

1.  **🟡 JA-001 (Janitron)**: Esegue lo scavenging dei nodi orfani e la pulizia dei frammenti a bassa rilevanza.
2.  **🟣 DI-007 (Distiller)**: Analizza i cluster semantici per estrarre saggezza collettiva e riassumere i concetti chiave.
3.  **🐍 SN-008 (Snake)**: Recupero e trasporto nodi isolati; "striscia" tra i nodi per riconnettere cluster distanti.
4. - **🏗️ QA-101 (Quantum)**: Urbanistica semantica (Golden Clusters).
- **🛡️ SE-007 (Sentinel)**: Validazione e Consenso (Supreme Court).
- **🧬 EV-001 (Advisor)**: Motore di Auto-Evoluzione.

### 🛡️ Protocollo Safe-Genesis (Git Checkpoint)
Prima di ogni intervento di scrittura autonoma del codice, il sistema esegue:
1. **Snap-Commit**: Commit istantaneo dello stato attuale sul branch `main`.
2. **Tagging Certificato**: Generazione di un Git Tag `vX.X.X-VERIFICATO`.
3. **Remote Mirror**: Push immediato su GitHub del checkpoint stabile.
*Questo garantisce un fallback deterministico al 100% in caso di allucinazioni del motore evolutivo.*

> [!IMPORTANT]
> **SOVEREIGN PRIVACY**: Tutte le operazioni di sincronizzazione con GitHub avvengono esclusivamente in **Modalità Privata**. Il sistema forza la creazione di repository non pubblici per garantire che il codice e l'evoluzione rimangano proprietà esclusiva dell'utente.

5.  **🛡️ SE-007 (Sentinel)**: Validatore della mesh; verifica l'integrità dei nodi e delle sinapsi, applicando veti se necessario.
6.  **✨ SY-009 (Synth)**: Sintesi creativa; genera "Creative Sparks" collegando concetti distanti tramite inferenza LLM.
7.  **CB-003 (Bridger)**: Mantiene attivi i ponti semantici tra il codice sorgente locale e la conoscenza esterna (Latent Bridge).
8.  **FS-77 (SkyWalker)**: Esploratore proattivo che esce dal Vault per cercare nuova conoscenza sul web (Mission Mode).
9.  **Sovereign Auditor**: Monitora costantemente le performance (TPS/Latency) e il consumo hardware durante le inferenze.

---

## 🔄 4. FLUSSO DEI DATI (RAG): DALL'INPUT ALLA SINAPSI

Il percorso di un'informazione segue una pipeline ad alta fedeltà:

1.  **Ingestion Phase**: I dati entrano tramite URL (WebForager), File (MultimodalProcessor) o Testo Raw.
2.  **Atomic Chunking**: Il testo viene spezzato seguendo confini logici (paragrafi, firme di codice) per mantenere la coesione.
3.  **Vectorization**: Ogni frammento viene convertito in un vettore da 1024D (BGE-M3 o CLIP) e normalizzato per il calcolo della similarità coseno.
4.  **Hybrid Search (BM25 + HNSW)**: Il sistema combina la forza del testo esatto (BM25) con la profondità semantica (HNSW).
5.  **RRF & Reranking**: I risultati sono fusi tramite **Reciprocal Rank Fusion** e ri-ordinati da un modello **TinyBERT Cross-Encoder** per eliminare i falsi positivi.

---

## 🛡️ 5. GOVERNANCE & INTEGRITY (BLOCKCHAIN)

### Sovereign Ledger (Merkle Audit)
Generazione di hash radice (Merkle Root) per l'intero stato del Vault. Permette di generare "Proof of Integrity" dimostrando che un nodo esisteva in un determinato momento senza rivelare l'intero contenuto del vault.

### Supreme Court Consensus
Protocollo di validazione a 3 giudici (Alpha, Beta, Gamma). Quando un agente propone un'estrazione critica, i tre modelli votano indipendentemente. Solo se c'è consenso il dato viene promosso a "Conoscenza Verificata".

---

## 🛡️ 6. HARDENING & INTELLIGENZA PERSISTENTE (v3.5.0)

### 1. Macchina a Stati Formale (Node Lifecycle)
Ogni nodo segue un percorso deterministico gestito da un Enum centrale:
- **PENDING**: Protetto per un **Grace Period** di 30 minuti per permettere correzioni o rivalutazioni.
- **STABLE**: Indicizzato e pronto per l'analisi profonda.
- **PROTECTED**: Marcato come intoccabile (Memoria Episodica in DuckDB).
- **TOMBSTONE**: Lapide crittografica post-eliminazione che permette ad **Aegis Reaper** di recuperare spazio fisico in modo asincrono.

### 2. Pacing Adattivo (Warp Speed)
Monitoraggio dinamico del carico hardware:
- **WARP (0.1s)**: Operatività massima se CPU < 30%.
- **NORMAL (2.0s)**: Pacing operativo standard.
- **COOLING (5-10s)**: Se CPU > 85%, lo sciame rallenta per preservare le prestazioni.

### 3. Ottimizzazione macOS (Apple Silicon)
NeuralVault è temprato per l'architettura ARM di Apple:
- **Silencing OBJC/FFmpeg**: Risoluzione dei conflitti di libreria tramite variabili d'ambiente mirate (`OBJC_DISABLE_INITIALIZE_FORK_SAFETY`).
- **Daemon Threading**: Il servizio di Discovery e i loop di evoluzione sono isolati in thread daemon per non bloccare l'event loop di FastAPI.

### 4. Precisione Biologica: Ebbinghaus v2 (Il Ritmo del Ricordo)
Il sistema implementa una versione computazionale della **Curva dell'Oblio di Hermann Ebbinghaus**. A differenza dei database statici, NeuralVault è un organismo vivo dove l'informazione "respira" e svanisce se non alimentata dall'attenzione umana.

- **La Formula del Decadimento**: Ogni nodo possiede un coefficiente di stabilità $S$ che decade secondo una funzione esponenziale negativa $R = e^{-t/S}$, dove $R$ è la ritenzione e $t$ è il tempo trascorso dall'ultima interazione.
- **Visual Ghosting (Opacità Dinamica)**: Nella Nebula 3D, il valore di $R$ mappa direttamente l'opacità del punto.
    *   **Piena Luce (R=1.0)**: Il nodo è stato appena creato o consultato. È una "Memoria Viva".
    *   **Dissolvenza (R < 0.5)**: Il nodo inizia a diventare traslucido, segnalando che la sua rilevanza sta scivolando nell'inconscio del sistema.
    *   **Soglia di Eclissi (R < 0.1)**: Il nodo scompare visivamente dal rendering 3D per evitare l'overload cognitivo, pur rimanendo accessibile via query testuale.
- **Memory Strengthening (Rinforzo)**: Ogni volta che un nodo viene richiamato da una ricerca (Query Hit) o citato in una conversazione, la sua curva di decadimento viene resettata e la sua stabilità $S$ aumenta. Questo simula il processo biologico per cui un concetto ricordato più volte diventa "permanente".
- **Ruolo degli Agenti**: Agenti come il **Janitron (JA-001)** monitorano i nodi con $R < 0.05$ (Stato di Oblio Profondo) per valutare se archiviarli fisicamente nel Tier L2 o procedere alla loro "digestione" definitiva per recuperare spazio hardware.

---

## 🌌 7. RENDERING 3D: LA VISUALIZZAZIONE DELLA NEBULA

La visualizzazione Three.js non è solo estetica, ma una mappa termica della tua mente:
- **Cluster Mapping**: Posizionamento basato sulla similarità semantica.
- **Aura Synapses**: Connessioni arcobaleno (Latent Bridge) che collegano codice e documenti.
- **Dynamic Icons**: Icone specifiche per immagini, audio e video integrate nel point cloud.

---

## 📦 8. DIPENDENZE CRITICHE
*   **FastAPI & Uvicorn**: API Layer asincrono.
*   **Three.js**: Rendering GPU accelerato.
*   **DuckDB**: Metadata & Hybrid Search Engine.
*   **Numpy & PyTorch**: Calcolo vettoriale e inferenza locale.
*   **Zeroconf**: Mesh Discovery (stile AirDrop).
*   **X25519 & AES-GCM**: Crittografia end-to-end per la mesh.

---

## 🚀 9. ROADMAP & STATO REALE (APRILE 2026)

### 📊 NEURALVAULT: STATO REALE
| Funzione | Stato | Note Tecniche |
| :--- | :--- | :--- |
| **X25519 + AES-GCM Encryption** | 100% ✅ | Handshake ellittico attivo su ogni pacchetto Mesh. |
| **mDNS/ZeroConf Discovery** | 100% ✅ | Peer detection automatica stabilizzata via background threading. |
| **Hybrid Search (BM25+HNSW+TinyBERT)** | 100% ✅ | Motore di fusione RRF con reranking neurale attivo. |
| **Supreme Court Consensus** | 100% ✅ | Protocollo a 3 giudici per la validazione della conoscenza. |
| **AOBF + Aegis Reaper** | 100% ✅ | Persistenza binaria atomica e compattazione asincrona operative. |
| **Sovereign Snapshot (Instant Boot)** | 100% ✅ | Caricamento sub-secondo tramite snapshot Parquet/Pickle. |
| **Latent Code-Doc Bridge** | 100% ✅ | Collegamento semantico tra codice locale e docs web (Agente CB-003). |
| **Swarm Agents (v24.3.1)** | 100% ✅ | Telemetria ripristinata per Quantum, Distiller, SkyWalker e Snake. Sincronizzazione contatori attiva. |
| **Node Lifecycle State Machine** | 100% ✅ | Gestione atomica degli stati (Pending/Stable/Tombstone/Protected). |
| **Ebbinghaus Decay Visual** | 100% ✅ | Opacità dinamica 3D e calcolo real-time della forza del ricordo con reset proattivo. |
| **Sovereign Priority Focus** | 100% ✅ | Stasi automatica agenti durante interazione utente (Lab). |
| **Skywalker Fallback Protocol** | 100% ✅ | Ricerca web intelligente automatica per lacune o nodi corrotti. |
| **Neural Model Hub (Apr 2026)** | 100% ✅ | Integrazione DeepSeek V4 Flash, Qwen 3.6 MoE, Gemma 4 Edge e Qwen Coder. |
| **Sovereign 3D Alignment** | 100% ✅ | Nebula centrata a y=1.000.000. Ispezione nodi (Raycaster) stabilizzata. |
| **Autonomous Evolution Engine** | 85% ✅ | Motore Safe-Genesis implementato (Git Tagging). Missioni X-Wing stabilizzate. |
| **Semantic Temperature Heatmap** | 40% ⚠️ | Monitor entropia attivo, visualizzazione 3D in fase di affinamento. |
| **Agentic Actuators Sandbox** | 10% ❌ | Inizio fase progettuale per esecuzione script protetta. |

| **Neural Shadow iOS** | 0% ❌ | Concept per Thin Client mobile non ancora iniziato. |

### 🚫 Feature Scartate (Out of Scope)
*   **Modulo Email / IMAP Ingestion**: Inizialmente previsto, questo modulo è stato **definitivamente rimosso dall'architettura**. NeuralVault è concepito come un *Sovereign Cognitive Engine* per l'evoluzione e la sintesi di architetture e conoscenze complesse. Ridurlo a un "assistente personale per la lettura delle email" ne banalizzerebbe e diluirebbe l'identità ingegneristica.

### 🐛 Changelog Architetturale & Bug Risolti (v4.0)
*   **Telemetria Burocratica**: Svincolato il conteggio delle azioni degli agenti (UI Counters) dalla rigorosa validazione della Macchina a Stati Finiti. In precedenza, se un agente operava su un nodo non perfettamente `STABLE`, il lavoro non veniva conteggiato nell'HUD.
*   **Z-Fighting WebGL**: Risolto lo sfarfallio visivo sollevando la geometria 3D dal piano della griglia. Ancoraggio assoluto (`cycloscope-immersion`) per garantire la persistenza dell'HUD su browser WebKit in modalità Full Screen.

### 🏗️ Le Grandi Sfide (Fase 4.0/5.0)
*   **📱 Neural Shadow iOS e android ( si potrebbe realizzare in flutter?? non so!)**: Costruzione del "Thin Client" per iPhonee android.
*   **🤖 Agentic Actuators (Sandboxed)**: Ambiente sicuro per permettere agli agenti di eseguire script Python sul sistema operativo.
*   **🧬 Autonomous Evolution**: Motore di self-writing per permettere al Vault di riscrivere i propri file .py in autonomia.

### 🗺️ Nuova Roadmap Implementativa (Sovereign Expansion)
*   **Fase 1 (Visiva e Sicurezza)**: Implementazione Semantic Heatmap 3D (Three.js) per visualizzazione entropia e risoluzione critica OAuth2 IMAP.
*   **Fase 2 (Gamification & Health)**: 
    *   **Vault Health Score**: Algoritmo per punteggio (0-100) basato su ritenzione, orfani e integrità crittografica.
    *   **Agent Leaderboard**: Tracciamento performance agenti (successi, latenza, impatto) con indicatori visivi (es. "corone" sopra gli sprite).
*   **Fase 3 (Evolution Safety)**: Sviluppo di un *Evolution Confidence Score* per determinare autonomamente l'applicazione, la richiesta di approvazione o lo scarto delle modifiche autogenerate dal codice.
*   **Fase 4 (Distribuzione)**: Release Globali GitHub e Agentic Actuators.

---

## 👤 CHI SONO
**Giuseppe Lobbene** — Architetto software e costruttore spinto dalla necessità di innovare. Ho guidato la crescita tecnica di una startup nel settore del booking balneare, portando il fatturato a un incremento di **10x in un solo anno**. **NeuralVault è il mio manifesto**: la prova che, anche di notte e dopo una giornata di lavoro, è possibile costruire il futuro della rivoluzione AI. Cerco sfide all'altezza della mia fame di innovazione, per dimostrare a me stesso e a mio figlio **Oliver** che il talento e la dedizione possono ancora cambiare il mondo.

---

🏺 **NeuralVault: Turning Information into Active Wisdom.**
**Temprato per la realtà. Sovrano per sempre.**