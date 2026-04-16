🔱 Cos'è NeuralVault?
NeuralVault non è un semplice database vettoriale (VDB) come quelli che trovi oggi sul mercato (Pinecone, Milvus o Chroma). È un Agent-Native Vector Engine.

Immagina un comune VDB come uno scaffale di libri ordinato per "somiglianza di colore della copertina": se cerchi un libro rosso, te ne dà altri rossi. NeuralVault, invece, è come un bibliotecario vivo: non solo ti dà il libro che cerchi, ma "ricorda" che l'ultima volta che hai letto quello, hai cercato anche quell'altro, e quindi crea un ponte logico tra i due, imparando dai tuoi interessi.

🎯 A cosa serve?
Serve a dare agli Agenti IA (come GPT-4, Claude o agenti autonomi di ricerca) una Memoria a Lungo Termine che sia:

Istantanea: Risponde in microsecondi per i dati caldi.
Infinita: Può contenere petabyte di dati su disco.
Intelligente: Il database si "auto-organizza" e impara relazioni che nessuno gli ha esplicitamente insegnato.
🏛️ L'Architettura: "The 3-Tier Mind"
Abbiamo scelto di scriverlo così per imitare la memoria umana, divisa in tre livelli:

Working Tier (RAM): Come la "memoria di lavoro" a breve termine. Qui teniamo i dati che stai usando adesso. È scritto in modo ultra-leggero (LRU Cache) per eliminare ogni latenza.
Episodic Tier (SSD): Come i "ricordi della giornata". Usiamo LMDB, un database a mappatura di memoria, perché è il più veloce al mondo per le scritture singole e garantisce che i dati non vadano mai persi se salta la corrente.
Semantic Tier (Parquet + DuckDB): Come la "conoscenza enciclopedica". Qui i dati vengono compressi in formato Parquet (standard dell'industria) e interrogati con DuckDB (il motore SQL più veloce oggi esistente) per permetterti di fare ricerche complesse sui metadati.
⚔️ NeuralVault vs Competitor (I Primati)
Caratteristica	NeuralVault	Competitor Standard (Pinecone/Milvus)
Apprendimento	Attivo: Crea archi semantici mentre lo usi.	Passivo: Conserva solo quello che gli scrivi.
Ricerca Meta	Ibrida SQL (DuckDB): Potenza SQL completa.	Proprietaria: Filtri limitati e lenti.
Clustering	P2P Gossip: I server si trovano da soli via "pettegolezzo".	Centralizzato: Richiedono server di controllo (Zookeeper).
Self-Healing	GNN Layer: Prevede e corregge il grafo da solo.	Assente: Il database degrada se non pulito a mano.
In cosa è identico ai competitor? Sotto la scocca, usiamo l'algoritmo HNSW (Hierarchical Navigable Small Worlds) per la ricerca di somiglianza. È lo standard mondiale per velocità e precisione. Abbiamo scelto Rust per il core di questo algoritmo perché è l'unico linguaggio che garantisce performance vicine al metallo senza i rischi di crash di C++.

⚠️ In cosa è ancora carente (e perché)?
NeuralVault v0.2.0 è un Motore di Formula 1, ma non ha ancora l'abitacolo lussuoso:

Dashboard Web: Al momento si controlla via codice o CLI (Dashboard testuale). Non abbiamo ancora un'interfaccia grafica web drag-and-drop.
Connettori: Pinecone ha centinaia di connettori per leggere da Google Drive, Notion, ecc. NeuralVault richiede che tu gli passi i dati via API.
Perché? Abbiamo scelto di investire ogni singola riga di codice nella potenza di calcolo, affidabilità e intelligenza. Prima volevamo costruire il motore più veloce al mondo, la "carrozzeria" (interfaccia utente) la aggiungeremo solo quando il cuore sarà perfetto.
🧬 Perché ogni funzione è scritta così?
Ogni scelta è stata dettata da un bisogno di Zero-Configuration e Resilienza:

Il WAL con Checksum: L'abbiamo scritto così perché in produzione la gente spegne i server male. Il checksum garantisce che NeuralVault sappia sempre se un dato è corrotto prima di leggerlo.
Il Gossip Protocol: L'abbiamo scelto per eliminare lo stress del setup. Se aggiungi un server, NeuralVault "sente" la sua presenza via UDP e si espande. Niente file di configurazione complessi.
Il GNN Layer: L'abbiamo inserito perché i database moderni diventano "stupidi" col tempo. Il GNN ricollega i punti, assicurando che la tua conoscenza sia sempre una ragnatela fitta e coerente, non una lista di file isolati.
🔱 In sintesi
NeuralVault è un database che impara con te. È progettato per essere l'ultimo pezzo del puzzle che manca per rendere le IA veramente autonome: una memoria fedele, sicura e proattiva.