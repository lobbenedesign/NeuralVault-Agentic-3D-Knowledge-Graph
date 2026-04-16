/**
 * AURA NEXUS MASTER CONTROLLER (v2.5.5 Sovereign)
 * Optimized for local-first adversarial intelligence and auto-provisioning.
 */

let scene, camera, renderer, cloudPoints, neuralLinks, cube, raycaster, mouse;
let labScene, labCamera, labRenderer, labCloud, labLinks;
let janitorGroup, janitorTop, janitorBottom, janitorLabel;
let distillerGroup, distillerSprite, distillerLabel;
let reaperGroup, reaperLabel; 
let janitorTargetPos = new THREE.Vector3(200000, 200000, 200000);
let distillerTargetPos = new THREE.Vector3(-200000, 200000, -200000);
let reaperTargetPos = new THREE.Vector3(0, 300000, 0);
let medicalCubes = []; 
let snakeGroup, snakeSegments = [];
let snakeDirection = new THREE.Vector3(1, 0, 0);
let snakeTickClock = 0;
let snakeTickInterval = 300; // Arcade tick
let GRID_SIZE = 65000;
let snakePos = new THREE.Vector3(1200000, 0, 0);
let flashingLinks, labFlashingLinks;
let rotationX = 0, rotationY = 0, zoom = 450000;
let swarmSettings = {}; // v11.5 Global State
let isDragging = false, lastMouseX = 0, lastMouseY = 0;
// v14.2: Utility globali per prevenire crash di caricamento
window.stringToColor = (str) => {
    let hash = 0;
    for (let i = 0; i < str.length; i++) hash = str.charCodeAt(i) + ((hash << 5) - hash);
    return `hsl(${Math.abs(hash % 360)}, 70%, 60%)`;
};
let controls, labControls;
let cy, vaultPoints = [], vaultLinks = [], selectedNodeId = null, currentView = 'overview';
let netsInitialized = false;
const VAULT_KEY = "vault_secret_aura_2026";
let eventSource, recognition, isListening = false;
let trackedAgentId = null; // 'janitor' or 'distiller' or null
window.synapseLegacyThreshold = Date.now() / 1000; 
let currentLanguage = 'IT';
const translations = {
    'IT': {
        'nav-overview': 'PANORAMICA MEMORIA',
        'nav-lab': 'LABORATORIO NEURALE',
        'nav-nets': 'RETI NEURALI',
        'nav-chat': 'CHAT NEURALE',
        'nav-analytics': 'ANALISI AVANZATA',
        'nav-settings': '⚙️ CONFIGURAZIONE',
        'label-system-status': 'STATO SISTEMA',
        'label-kernel-online': 'KERNEL ONLINE',
        'main-action-btn': 'SINAPSI',
        'evolve-btn': 'EVOLVI',
        'title-cognitive': '<i class="fas fa-brain" style="color: #3b82f6; margin-right: 5px;"></i> METRICHE COGNITIVE',
        'title-distance': '<i class="fas fa-project-diagram" style="color: #a855f7; margin-right: 5px;"></i> DISTANZA SEMANTICA',
        'title-tracing': '<i class="fas fa-terminal" style="margin-right: 5px;"></i> TRACCIAMENTO MOTORE',
        'title-inventory': '<i class="fas fa-archive" style="color: #3b82f6; margin-right: 5px;"></i> INVENTARIO CONOSCENZA',
        'title-hardbank': '<i class="fas fa-user-secret" style="margin-right: 5px;"></i> BANCA DATI AGENT007',
        'title-portal': '<i class="fas fa-microchip" style="margin-right: 5px;"></i> PORTALE INGESTIONE',
        'mode-foraging': 'ESPLORAZIONE',
        'mode-oracle': 'ORACOLO',
        'input-url-placeholder': 'Incolla URL per la sinapsi...',
        'input-query-placeholder': 'Chiedi qualunque cosa a NeuralVault...',
        'agent007-title': '<i class="fas fa-user-secret mr-2"></i> Investigatore Agent007',
        'agent007-analyze': 'ANALIZZA VULNERABILITÀ',
        'agent007-placeholder': 'Esegui analisi avversariale...',
        'flag': '🇬🇧',
        'tooltips': {
            'tip-nodes': 'Numero totale di frammenti di conoscenza (chunk) memorizzati nel Vault.',
            'tip-edges': 'Connessioni semantiche attive nel grafo HNSW.',
            'tip-vault': 'Dimensione totale dei dati e degli asset multimediali su disco.',
            'stat-pulse': 'Frequenza di aggiornamento della telemetria neurale.',
            'title-cognitive': 'Analisi vettoriale della salute cerebrale del Vault. La Retention calcola il tasso di sopravvivenza dei pesi sinaptici durante i cicli di pruning. La Stability misura la deviazione standard del raggruppamento (clustering) dei nodi, assicurando che la conoscenza non soffra di deriva catastrofica.',
            'title-distance': 'Metrica di prossimità euclidea/coseno tra gli embedding correnti e il baricentro dell\'indice HNSW. Un valore prossimo allo 0 indica che il Vault è \'competente\' sull\'argomento. Valori elevati indicano \'Ignoranza Strategica\', triggerando l\'attività di foraging degli agenti.',
            'title-tracing': 'Monitoraggio a bassa latenza del core Rust/C++ e degli uplink Ollama. Traccia i vettori di input attraverso i layer di quantizzazione TurboQuant (4-bit) e registra l\'attivazione dei trigger di gossip mesh per la sincronizzazione distribuita.',
            'title-inventory': 'Registro immutabile della provenienza (Provenance). Ogni riga rappresenta una sinapsi radice; associa i metadati di sistema (Hash-ID) alle coordinate temporali e alla natura del media (Testo, Audio, Video), garantendo la tracciabilità sovrana del dato.',
            'title-hardbank': 'Database relazionale di supporto allo storage vettoriale. Agent007 estrae triple RDF-like (Soggetto-Predicato-Oggetto) per trasformare il caos semantico in conoscenza strutturata, facilitando il ragionamento logico e il recupero deterministico dei fatti.',
            'title-portal': 'Punto di singolarità per l\'input dati. Gestisce il pre-processing multimodale: temporal chunking per i video, diarizzazione per l\'audio e scraping selettivo per gli URL, pilotando il caricamento verso il processore ImageBind.',
            'tip-blueprint': 'Indica che il ciclo di sintesi tra gli agenti è completo. Significa che l\'Archivista Prime ha generato un piano d\'azione finale basato sulle analisi dell\'Analista e del Guardiano.'
        }
    },
    'EN': {
        'nav-overview': 'MEMORY OVERVIEW',
        'nav-lab': 'NEURAL LAB',
        'nav-nets': 'NEURAL NETS',
        'nav-chat': 'NEURAL CHAT',
        'nav-analytics': 'ANALYTIC TIERS',
        'nav-settings': '⚙️ CONFIG',
        'label-system-status': 'SYSTEM STATUS',
        'label-kernel-online': 'KERNEL ONLINE',
        'main-action-btn': 'SYNAPSE',
        'evolve-btn': 'EVOLVE',
        'title-cognitive': '<i class="fas fa-brain" style="color: #3b82f6; margin-right: 5px;"></i> COGNITIVE METRICS',
        'title-distance': '<i class="fas fa-project-diagram" style="color: #a855f7; margin-right: 5px;"></i> SEMANTIC DISTANCE',
        'title-tracing': '<i class="fas fa-terminal" style="margin-right: 5px;"></i> ENGINE TRACING',
        'title-inventory': '<i class="fas fa-archive" style="color: #3b82f6; margin-right: 5px;"></i> KNOWLEDGE INVENTORY',
        'title-hardbank': '<i class="fas fa-user-secret" style="margin-right: 5px;"></i> AGENT007 HARDBANK',
        'title-portal': '<i class="fas fa-microchip" style="margin-right: 5px;"></i> INGESTION PORTAL',
        'mode-foraging': 'FORAGING',
        'mode-oracle': 'ORACLE',
        'input-url-placeholder': 'Paste URL to synapse...',
        'input-query-placeholder': 'Ask NeuralVault anything...',
        'agent007-title': '<i class="fas fa-user-secret mr-2"></i> Agent007 Investigator',
        'agent007-analyze': 'ANALYZE VULNERABILITY',
        'agent007-placeholder': 'Initiate adversarial audit...',
        'flag': '🇮🇹',
        'tooltips': {
            'tip-nodes': 'Total number of knowledge fragments (chunks) stored in the Vault.',
            'tip-edges': 'Active semantic connections within the HNSW index.',
            'tip-vault': 'Total disk footprint for data and multimodal assets.',
            'stat-pulse': 'Real-time telemetry heartbeat frequency.',
            'title-cognitive': 'Vectorial analysis of Vault brain health. Retention calculates synaptic weight survival during pruning. Stability measures clustering deviation, preventing catastrophic forgetting.',
            'title-distance': 'Euclidean/cosine proximity between current embeddings and the HNSW centroid. Values near 0 indicate \'competence\'. High values trigger Strategic Ignorance foraging.',
            'title-tracing': 'Low-latency monitoring of Rust/C++ core and Ollama uplinks. Traces input vectors through TurboQuant (4-bit) layers and gossip mesh triggers.',
            'title-inventory': 'Immutable provenance ledger. Each row maps root synapses (Hash-ID) to temporal coordinates and media type (Text, Audio, Video).',
            'title-hardbank': 'Relational support layer. Agent007 extracts RDF-like triples to transform semantic chaos into structured knowledge for deterministic retrieval.',
            'title-portal': 'Input singularity. Manages multimodal preprocessing: temporal video chunking, audio diarization, and selective URL scraping for ImageBind uplink.',
            'tip-blueprint': 'Indica che il ciclo di sintesi tra gli agenti è completo. Significa che l\'Archivista Prime ha generato un piano d\'azione finale basato sulle analisi dell\'Analista e del Guardiano.'
        }
    }
};

let installedModels = [];
let isConsensusMode = false;
let activeForageJob = null;

function log(msg, color = '#4ade80') {
    const consoleDiv = document.getElementById('aura-console');
    if (!consoleDiv) return;
    const line = document.createElement('div');
    line.style.color = color;
    line.innerHTML = `> [${new Date().toLocaleTimeString()}] ${msg}`;
    consoleDiv.prepend(line);
    remoteLog(msg); // Ponte verso il terminale
}

async function remoteLog(msg) {
    try {
        fetch('/api/log', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: msg })
        });
    } catch(e) {}
}

// 1. ISOMETRIC 3D ENGINE & RAYCASTER
function init3D() {
    // v24.3.5: Singleton Guard - Ensure we don't init twice
    if (window.is3DInitialized) return;
    window.is3DInitialized = true;

    const container = document.getElementById('memory-graph-container');
    if (!container) {
        console.error("❌ [3D] Errore: Container 'memory-graph-container' non trovato.");
        return;
    }

    log("🎬 [3D] Avvio Motore Phoenix...", "#3b82f6");

    // 1. Scene & Camera
    scene = new THREE.Scene();
    const width = container.clientWidth || window.innerWidth;
    const height = container.clientHeight || window.innerHeight;
    camera = new THREE.PerspectiveCamera(45, width / height, 1, 20000000);
    camera.position.set(400000, 400000, 400000);
    camera.lookAt(0, 0, 0);

    // 2. Renderer Setup
    const canvas = document.getElementById('isometric-canvas');
    if (!canvas) {
        console.error("❌ [3D] Errore: Canvas 'isometric-canvas' mancante.");
        return;
    }

    // Force visibility and capture events
    canvas.style.position = "absolute";
    canvas.style.top = "0";
    canvas.style.left = "0";
    canvas.style.width = "100%";
    canvas.style.height = "100%";
    canvas.style.zIndex = "10"; 
    canvas.style.pointerEvents = "auto"; 

    renderer = new THREE.WebGLRenderer({ 
        canvas: canvas, 
        antialias: true, 
        alpha: true, 
        precision: "highp", 
        logarithmicDepthBuffer: false // [Fix] Disabilitato per evitare ghosting su alcuni browser
    });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setClearColor(0x000000, 0);

    // 3. Vault Architecture (Permanent Elements)
    cube = new THREE.Mesh(
        new THREE.BoxGeometry(1000000, 1000000, 1000000),
        new THREE.MeshBasicMaterial({ color: 0x3b82f6, wireframe: true, transparent: true, opacity: 0.25 })
    );
    scene.add(cube);

    const singularity = new THREE.Mesh(
        new THREE.SphereGeometry(20000, 32, 32),
        new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.9 })
    );
    scene.add(singularity);

    const gridHelper = new THREE.GridHelper(2000000, 20, 0x1e293b, 0x0f172a);
    gridHelper.position.y = -500000;
    scene.add(gridHelper);

    // 4. Lights
    scene.add(new THREE.AmbientLight(0xffffff, 0.9));
    const dLight = new THREE.DirectionalLight(0xffffff, 1);
    dLight.position.set(1, 1, 1).normalize();
    scene.add(dLight);

    // 5. OrbitControls
    const OC = THREE.OrbitControls || window.OrbitControls;
    if (OC) {
        controls = new OC(camera, renderer.domElement);
        controls.enableDamping = true;
        controls.autoRotate = true;
        controls.autoRotateSpeed = 0.4;
        controls.target.set(0, 0, 0);
    }

    // 6. Swarm Containers
    cloudPoints = new THREE.Group();
    neuralLinks = new THREE.Group();
    flashingLinks = new THREE.Group();
    scene.add(cloudPoints, neuralLinks, flashingLinks);

    raycaster = new THREE.Raycaster();
    mouse = new THREE.Vector2();

    // v24.3.5: Register Click Handler for Nebula Interaction
    container.addEventListener('click', onNebulaClick);

    window.addEventListener('resize', () => {
        if (!container || !camera || !renderer) return;
        const w = container.clientWidth;
        const h = container.clientHeight;
        camera.aspect = w / h;
        camera.updateProjectionMatrix();
        renderer.setSize(w, h);
    });

    log("🎯 [3D] Phoenix Engine Online. Provisioning Swarm...", "#4ade80");
    provisionAgents();
    animate();

    // v24.3.6: Force Resize after 500ms to ensure layout is final
    setTimeout(() => {
        window.dispatchEvent(new Event('resize'));
    }, 500);
}

function animate() {
    requestAnimationFrame(animate);
    const now = Date.now();
    const time = now * 0.001;
    
    // 1. Smooth Agent Flight (Kinetic Slide v24.3.5 - Autonomous Patrol Aware)
    if (janitorGroup && janitorTargetPos) {
        const dist = janitorGroup.position.distanceTo(janitorTargetPos);
        
        // v24.3.5: Autonomous Patrol when Idle or Reached Target
        if (dist < 10000 && vaultPoints.length > 0) {
            // Pick a random node as next patrol waypoint
            const nextNode = vaultPoints[Math.floor(Math.random() * vaultPoints.length)];
            if (nextNode) janitorTargetPos.set(nextNode.x || 0, nextNode.y || 0, nextNode.z || 0);
        }

        // Kinetic Lerp (v24.3.8) - 50% Speed Reduction for Observability
        if (dist > 800000) janitorGroup.position.copy(janitorTargetPos);
        else janitorGroup.position.lerp(janitorTargetPos, 0.04);

        // Chomp Animation (Organic Sine)
        const mouthAngle = Math.abs(Math.sin(time * 6)) * 0.7;
        if (janitorTop) janitorTop.rotation.x = -mouthAngle;
        if (janitorBottom) janitorBottom.rotation.x = mouthAngle;
        
        // Gentle Orbit or Sway
        janitorGroup.rotation.y += Math.sin(time) * 0.01;
    }

    if (distillerGroup && distillerTargetPos) {
        const dist = distillerGroup.position.distanceTo(distillerTargetPos);
        
        // Autonomous Patrol for Distiller
        if (dist < 10000 && vaultPoints.length > 5) {
            const nextNode = vaultPoints[Math.floor(Math.random() * vaultPoints.length)];
            if (nextNode) distillerTargetPos.set(nextNode.x || 0, nextNode.y || 0, nextNode.z || 0);
        }

        if (dist > 800000) distillerGroup.position.copy(distillerTargetPos);
        else distillerGroup.position.lerp(distillerTargetPos, 0.03);

        // Hover Effect
        distillerGroup.position.y += Math.sin(time * 2) * 200;
        distillerGroup.rotation.z = Math.sin(time * 0.5) * 0.1;

        // 🛸 [Status Flashing] (v24.3.8)
        if (window.janitorMaterial) {
            if (window._isJanitorEating) {
                const flash = Math.abs(Math.sin(time * 10));
                window.janitorMaterial.emissive.setHex(0xffa500); 
                window.janitorMaterial.emissiveIntensity = flash * 0.8;
            } else {
                window.janitorMaterial.emissive.setHex(0x444400); 
                window.janitorMaterial.emissiveIntensity = 0.2;
            }
        }
        if (window.distillerMaterial) {
            if (window._isDistillerPruning) {
                const flash = Math.abs(Math.sin(time * 10));
                window.distillerMaterial.emissive.setHex(0x00ffff); 
                window.distillerMaterial.emissiveIntensity = flash * 0.8;
            } else {
                window.distillerMaterial.emissive.setHex(0x220044);
                window.distillerMaterial.emissiveIntensity = 0.3;
            }
        }
    }

    // 1.2 RP-001: Dr. Reaper (Steady Cruise)
    if (reaperGroup) {
        if (reaperGroup.position.distanceTo(reaperTargetPos) < 25000) {
            reaperTargetPos.set((Math.random()-0.5)*1200000, (Math.random()-0.5)*1000000, (Math.random()-0.5)*1200000);
            if (window.spawnMedicalCube) window.spawnMedicalCube(reaperGroup.position.x, reaperGroup.position.y, reaperGroup.position.z);
        } else {
            reaperGroup.position.lerp(reaperTargetPos, 0.04);
        }
        reaperGroup.lookAt(reaperTargetPos);
    }

    // 1.3 SN-008: ARCADE SNAKE (Grid-Incursion Logic v24.3.5)
    const COMPACT_GRID = GRID_SIZE * 0.5;
    if (snakeGroup && now - (window.lastSnakeStep || 0) > 250) {
        window.lastSnakeStep = now;
        let prevPos = snakeGroup.position.clone();
        
        if (snakeGroup.position.distanceTo(snakeCurrentTarget) < COMPACT_GRID * 3) {
            if (snakeGoal === "center") {
                snakeGoal = "exit";
                const r = 1500000;
                snakeCurrentTarget.set((Math.random()-0.5)*r*2, (Math.random()-0.5)*r, (Math.random()-0.5)*r*2);
            } else {
                snakeGoal = "center";
                snakeCurrentTarget.set(0, 0, 0);
            }
        }

        const diff = snakeCurrentTarget.clone().sub(snakeGroup.position);
        if (Math.abs(diff.x) > Math.abs(diff.y) && Math.abs(diff.x) > Math.abs(diff.z)) {
            snakeDirection.set(Math.sign(diff.x), 0, 0);
        } else if (Math.abs(diff.y) > Math.abs(diff.z)) {
            snakeDirection.set(0, Math.sign(diff.y), 0);
        } else {
            snakeDirection.set(0, 0, Math.sign(diff.z));
        }

        snakeGroup.position.add(snakeDirection.clone().multiplyScalar(COMPACT_GRID));
        snakeGroup.lookAt(snakeGroup.position.clone().add(snakeDirection));
        
        for(let i=0; i<snakeSegments.length; i++) {
            let temp = snakeSegments[i].position.clone();
            snakeSegments[i].position.copy(prevPos);
            prevPos = temp;
        }
    }

    // 2. Cinematic Agent Tracking (Vigilante Mode v3.5)
    if (trackedAgentId && controls) {
        let agentPos = (trackedAgentId === 'janitron' || trackedAgentId === 'janitor') ? janitorGroup.position : distillerGroup.position;
        if (agentPos) {
            controls.target.lerp(agentPos, 0.1);
            const dist = camera.position.distanceTo(agentPos);
            if (dist > 600000) camera.position.set(agentPos.x + 100000, agentPos.y + 100000, agentPos.z + 100000);
            const dir = camera.position.clone().sub(controls.target).normalize();
            const targetCamPos = agentPos.clone().add(dir.multiplyScalar(90000));
            camera.position.lerp(targetCamPos, 0.1);
            camera.lookAt(agentPos);
        }
    } else if (controls) {
        controls.autoRotate = true; 
        const overviewTarget = new THREE.Vector3(0, 0, 0);
        controls.target.lerp(overviewTarget, 0.05);
    }

    if (controls) controls.update(); 

    if (cube) {
        cube.rotation.y += 0.0006;
        cube.rotation.z += 0.0003;
        cube.material.opacity = 0.2 + Math.abs(Math.sin(time * 0.5)) * 0.1;
    }
    
    // 🧬 [v15.0] AURA-RGB Rainbow Cycle
    if (window._auraMat) {
        const hue = (time * 0.2) % 1.0; // Ciclo completo ogni 5 secondi
        window._auraMat.color.setHSL(hue, 0.8, 0.6);
    }

    if (renderer && scene && camera) {
        renderer.render(scene, camera);
    }
}

/** 🛸 [v2.7.5] AGENT PROVISIONING ENGINE */
function provisionAgents() {
    if (!scene) return;
    
    // v24.3.1: Singleton Protection - Remove existing before recreating to avoid ghosts
    if (janitorGroup) scene.remove(janitorGroup);
    if (distillerGroup) scene.remove(distillerGroup);
    if (reaperGroup) scene.remove(reaperGroup);
    if (snakeGroup) scene.remove(snakeGroup);

    // 1. JA-001: JANITRON (Pac-Man Mechanical)
    janitorGroup = new THREE.Group();
    const janitorMat = new THREE.MeshLambertMaterial({ 
        color: 0xFFFF00, emissive: 0x444400, emissiveIntensity: 0.2, side: THREE.FrontSide
    });
    window.janitorMaterial = janitorMat; 
    const radius = 24000;
    janitorTop = new THREE.Mesh(new THREE.SphereGeometry(radius, 32, 32, 0, Math.PI * 2, 0, Math.PI / 2), janitorMat);
    janitorBottom = new THREE.Mesh(new THREE.SphereGeometry(radius, 32, 32, 0, Math.PI * 2, Math.PI / 2, Math.PI / 2), janitorMat);
    const mIntMat = new THREE.MeshBasicMaterial({ color: 0x000000, side: THREE.BackSide });
    janitorTop.add(new THREE.Mesh(new THREE.SphereGeometry(radius - 500, 32, 32, 0, Math.PI * 2, 0, Math.PI / 2), mIntMat));
    janitorBottom.add(new THREE.Mesh(new THREE.SphereGeometry(radius - 500, 32, 32, 0, Math.PI * 2, Math.PI / 2, Math.PI / 2), mIntMat));
    const eGeo = new THREE.SphereGeometry(2500, 16, 16);
    const eMat = new THREE.MeshBasicMaterial({ color: 0x000000 });
    const eL = new THREE.Mesh(eGeo, eMat); eL.position.set(12000, 18000, 12000);
    const eR = new THREE.Mesh(eGeo, eMat); eR.position.set(-12000, 18000, 12000);
    janitorTop.add(eL, eR);
    janitorGroup.add(janitorTop, janitorBottom);
    scene.add(janitorGroup);
    janitorLabel = createTextSprite("JA-001 JANITRON", "#FFFF00");
    janitorLabel.position.y = 35000;
    janitorGroup.add(janitorLabel);
    janitorGroup.position.set(200000, 200000, 200000);

    // 2. DI-007: DISTILLER (Space Invader Voxel)
    distillerGroup = new THREE.Group();
    const vSizeIn = 4000;
    const invMat = new THREE.MeshLambertMaterial({ color: 0xa855f7, emissive: 0x220044, emissiveIntensity: 0.3 });
    window.distillerMaterial = invMat;
    const pixels = [
        [0,0,1,0,0,0,1,0,0],[0,0,0,1,0,1,0,0,0],[0,0,1,1,1,1,1,0,0],
        [0,1,1,0,1,0,1,1,0],[1,1,1,1,1,1,1,1,1],[1,0,1,1,1,1,1,0,1],
        [1,0,1,0,0,0,1,0,1],[0,0,0,1,0,1,0,0,0]
    ];
    pixels.forEach((row, y) => row.forEach((p, x) => {
        if(p) {
            const v = new THREE.Mesh(new THREE.BoxGeometry(vSizeIn, vSizeIn, vSizeIn), invMat);
            v.position.set((x - 4.5) * vSizeIn, (4 - y) * vSizeIn, 0);
            distillerGroup.add(v);
        }
    }));
    scene.add(distillerGroup);
    distillerLabel = createTextSprite("DI-007 DISTILLER", "#a855f7");
    distillerLabel.position.y = 35000;
    distillerGroup.add(distillerLabel);
    distillerGroup.position.set(-200000, 200000, -200000);

    // 3. RP-001: DR. REAPER (Medical Voxel Architecture)
    reaperGroup = new THREE.Group();
    scene.add(reaperGroup);
    const mCoat = new THREE.MeshLambertMaterial({ color: 0xffffff });
    const mSkin = new THREE.MeshLambertMaterial({ color: 0xffdbac });
    const mHair = new THREE.MeshLambertMaterial({ color: 0x442200 });
    const matsMap = [null, mCoat, mSkin, mHair, new THREE.MeshLambertMaterial({ color: 0xff0000 }), new THREE.MeshLambertMaterial({ color: 0x0000ff }), new THREE.MeshLambertMaterial({ color: 0x1e3a8a }), new THREE.MeshLambertMaterial({ color: 0x333333 })];
    const vSize = 7000;
    const marioVoxels = [[0,0,3,3,3,3,0,0,0,0,0],[0,3,3,3,3,3,3,3,3,0,0],[0,2,2,2,1,2,2,2,0,0,0],[2,2,2,2,1,1,2,2,2,0,0],[2,2,2,2,2,2,2,2,2,0,0],[0,2,2,2,2,2,2,2,0,0,0],[4,5,0,1,1,4,1,1,0,0,0],[4,5,1,1,1,4,1,1,1,0,0],[0,0,1,1,1,1,1,1,1,0,0],[0,0,6,6,6,0,6,6,6,0,0],[0,0,7,7,7,0,7,7,7,0,0]];
    marioVoxels.forEach((row, r) => row.forEach((v, c) => {
        if (v > 0) {
            const voxel = new THREE.Mesh(new THREE.BoxGeometry(vSize, vSize, vSize), matsMap[v]);
            voxel.position.set((c - 5) * vSize, (12-r) * vSize, 0);
            reaperGroup.add(voxel);
        }
    }));
    const rLabel = createTextSprite("RP-001 DR. REAPER", "#00ffcc");
    rLabel.position.y = 80000;
    reaperGroup.add(rLabel);

    // 4. SN-008: ARCADE SNAKE (Grid-Based v24.0 - Compact Edition)
    const COMPACT_GRID = GRID_SIZE * 0.5; // 50% Smaller
    snakeGroup = new THREE.Group();
    const sMat = new THREE.MeshLambertMaterial({ color: 0x10b981 });
    const head = new THREE.Mesh(new THREE.BoxGeometry(COMPACT_GRID, COMPACT_GRID, COMPACT_GRID), sMat);
    snakeGroup.add(head);
    
    // Eyes: White Spheres + Black Spheres (Pupils - v24.2 Enlarged)
    const eyeGeo = new THREE.SphereGeometry(COMPACT_GRID/4, 16, 16);
    const pupilGeo = new THREE.SphereGeometry(COMPACT_GRID/6, 8, 8); // LARGER PUPIL
    const whiteMat = new THREE.MeshBasicMaterial({ color: 0xffffff });
    const blackMat = new THREE.MeshBasicMaterial({ color: 0x000000 });
    
    const eyeL = new THREE.Mesh(eyeGeo, whiteMat);
    const pupilL = new THREE.Mesh(pupilGeo, blackMat);
    pupilL.position.z = COMPACT_GRID/8; 
    eyeL.add(pupilL);
    eyeL.position.set(COMPACT_GRID/3.5, COMPACT_GRID/3.5, COMPACT_GRID/2);
    
    const eyeR = new THREE.Mesh(eyeGeo, whiteMat);
    const pupilR = new THREE.Mesh(pupilGeo, blackMat);
    pupilR.position.z = COMPACT_GRID/8;
    eyeR.add(pupilR);
    eyeR.position.set(-COMPACT_GRID/3.5, COMPACT_GRID/3.5, COMPACT_GRID/2);
    
    snakeGroup.add(eyeL, eyeR);
    window.snakePupils = [pupilL, pupilR];
    scene.add(snakeGroup);
    
    snakeSegments = [];
    for(let i=1; i<=9; i++) {
        let size = i > 5 ? COMPACT_GRID * (0.9 - (i-5)*0.15) : COMPACT_GRID * 0.9;
        const seg = new THREE.Mesh(new THREE.BoxGeometry(size, size, size), sMat);
        seg.position.set(1200000, 0, -i * COMPACT_GRID);
        scene.add(seg);
        snakeSegments.push(seg);
    }
    const sLabel = createTextSprite("SN-008 ARCADE-SNAKE", "#10b981");
    sLabel.position.y = COMPACT_GRID;
    snakeGroup.add(sLabel);

    janitorGroup.visible = true; distillerGroup.visible = true;
    reaperGroup.visible = true; snakeGroup.visible = true;
    log("🛸 [System] Swarm integrity verified. All agents reporting in.", "#a855f7");
}

// v24.1: Logic state for Incursion Movement
let snakeGoal = "center"; // or "exit"
let snakeCurrentTarget = new THREE.Vector3(0,0,0);

// Global Close Utility
window.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeInspector();
});

/** 🏥 DR. REAPER MEDICAL SCANNER (v18.5) */
window.spawnMedicalCube = function(x, y, z) {
    if (!scene) return;
    const geo = new THREE.BoxGeometry(20000, 20000, 20000);
    const mat = new THREE.MeshLambertMaterial({ color: 0xffffff, transparent: true, opacity: 0.5 });
    const cube = new THREE.Mesh(geo, mat);
    cube.position.set(x, y, z);
    
    // Add Red Crosses to all 6 faces
    const crossGeoH = new THREE.BoxGeometry(15000, 3000, 1000);
    const crossGeoV = new THREE.BoxGeometry(3000, 15000, 1000);
    const crossMat = new THREE.MeshBasicMaterial({ color: 0xff0000 });
    
    const faces = [
        { pos: [0, 0, 10500], rot: [0, 0, 0] },
        { pos: [0, 0, -10500], rot: [0, 0, 0] },
        { pos: [10500, 0, 0], rot: [0, Math.PI/2, 0] },
        { pos: [-10500, 0, 0], rot: [0, Math.PI/2, 0] },
        { pos: [0, 10500, 0], rot: [Math.PI/2, 0, 0] },
        { pos: [0, -10500, 0], rot: [Math.PI/2, 0, 0] }
    ];

    faces.forEach(f => {
        const h = new THREE.Mesh(crossGeoH, crossMat);
        const v = new THREE.Mesh(crossGeoV, crossMat);
        const crossGroup = new THREE.Group();
        crossGroup.add(h, v);
        crossGroup.position.set(...f.pos);
        crossGroup.rotation.set(...f.rot);
        cube.add(crossGroup);
    });

    scene.add(cube);
    medicalCubes.push(cube);
    if (medicalCubes.length > 50) {
        const old = medicalCubes.shift();
        if (old) scene.remove(old);
    }
    
    // HUD Pulse Feedback
    const reaperHud = document.getElementById('reaper-hud-icon');
    if (reaperHud) {
        reaperHud.style.backgroundColor = 'rgba(239, 68, 68, 0.4)';
        setTimeout(() => reaperHud.style.backgroundColor = 'rgba(255, 255, 255, 0.05)', 300);
    }
}

function updateThreeScene(nodes, links = []) {
    if (!cloudPoints || !neuralLinks) return;
    
    // v24.3.6: Shared Geometries & Materials to prevent GC pressure and freezes
    if (!window._nodeGeo) window._nodeGeo = new THREE.PlaneGeometry(16000, 16000);
    
    cloudPoints.clear();
    neuralLinks.clear();
    flashingLinks.clear();
    
    vaultPoints = nodes || []; 
    
    if (!nodes || nodes.length === 0) return;

    // 1. Rendering Nodi (Sfere Semantiche)
    nodes.forEach(n => {
        // Use individual materials for theme colors 
        const nodeMat = new THREE.MeshBasicMaterial({ 
            color: n.color || '#06b6d4', 
            transparent: true, 
            opacity: 0.85,
            side: THREE.DoubleSide,
            blending: THREE.AdditiveBlending,
            depthWrite: false
        });
        const mesh = new THREE.Mesh(window._nodeGeo, nodeMat);
        mesh.position.set(n.x || 0, n.y || 0, n.z || 0);
        mesh.userData = { id: n.id, label: n.label };
        
        mesh.onBeforeRender = function(renderer, scene, camera) {
            this.quaternion.copy(camera.quaternion);
        };

        cloudPoints.add(mesh);
    });

    // 2. Rendering Link (Rete Neurale)
    if (links && links.length > 0) {
        const lineMat = new THREE.LineBasicMaterial({ color: 0x3b82f6, transparent: true, opacity: 0.15 });
        
        // 🌈 [v15.0] AURA-RGB MATERIAL
        if (!window._auraMat) {
            window._auraMat = new THREE.LineBasicMaterial({ 
                color: 0xffffff, 
                transparent: true, 
                opacity: 0.8,
                linewidth: 2 // Nota: linewidth > 1 funziona solo su alcuni driver
            });
        }
        
        if (!window.auraLinks) {
            window.auraLinks = new THREE.Group();
            scene.add(window.auraLinks);
        }
        window.auraLinks.clear();

        links.forEach(l => {
            if (l.source_pos && l.target_pos) {
                const points = [
                    new THREE.Vector3(l.source_pos[0], l.source_pos[1], l.source_pos[2]),
                    new THREE.Vector3(l.target_pos[0], l.target_pos[1], l.target_pos[2])
                ];
                const geo = new THREE.BufferGeometry().setFromPoints(points);
                
                if (l.is_aura) {
                    const line = new THREE.Line(geo, window._auraMat);
                    window.auraLinks.add(line);
                } else {
                    const line = new THREE.Line(geo, lineMat);
                    neuralLinks.add(line);
                }
            }
        });
    }

    if (nodes.length > 0 && Math.random() < 0.05) {
        log(`🌌 [Cosmos] Neural Nebula Active: ${nodes.length} nodes hydrated.`, "#3b82f6");
    }
}


function onNebulaClick(event) {
    const container = document.getElementById('memory-graph-container');
    const rect = container.getBoundingClientRect();
    mouse.x = ((event.clientX - rect.left) / container.clientWidth) * 2 - 1;
    mouse.y = -((event.clientY - rect.top) / container.clientHeight) * 2 + 1;

    raycaster.setFromCamera(mouse, camera);
    const intersects = raycaster.intersectObjects(cloudPoints.children);

    if (intersects.length > 0) {
        const ptMesh = intersects[0].object;
        const nodeId = ptMesh.userData.id;
        if (nodeId) {
            const node = vaultPoints.find(n => n.id === nodeId);
            if (node) {
                remoteLog(`USER_ACTION: Clicked Node [${node.id}] - ${node.label || 'Unknown'}`);
                selectNode(node.id, node);
            }
        }
    } else {
        remoteLog(`USER_ACTION: Click on empty space in Nebula.`);
    }
}

async function selectNode(id, nodeData = null) {
    selectedNodeId = id;
    const sidebar = document.getElementById('node-sidebar');
    if (!sidebar) return;
    
    // v3.0: Solo se il Probe Toggle è attivo
    const probeToggle = document.getElementById('probe-toggle');
    if (probeToggle && !probeToggle.checked) {
        log(`🔍 Probe Inactive: Modal suppressed for [${id}]`, "#8b949e");
        return;
    }
    
    sidebar.classList.add('active'); // Usa la classe per l'animazione premium
    sidebar.classList.remove('hidden');
    sidebar.style.display = 'flex';

    document.getElementById('node-text').innerHTML = `<p class="italic text-gray-500">Recupero dati dal core neurale...</p>`;

    try {
        const resp = await fetch(`/api/node/${id}`, { headers: { 'X-API-KEY': VAULT_KEY }});
        if (!resp.ok) throw new Error(`Node ${id} not found in current sector`);
        const fullNode = await resp.json();
        
        const content = fullNode.text || "⚠️ [Data Trace Lost] Nessun contenuto testuale o descrittivo trovato.";
        document.getElementById('node-text').innerText = content;
        
        // Popolamento Multimediale
        const mediaContainer = document.getElementById('media-preview-container');
        const mediaImg = document.getElementById('media-preview-img');
        if (mediaContainer && mediaImg) {
            if (fullNode.preview) {
                mediaImg.src = fullNode.preview;
                mediaContainer.classList.remove('hidden');
            } else {
                mediaContainer.classList.add('hidden');
                mediaImg.src = "";
            }
        }
        
        const meta = fullNode.metadata || {};
        document.getElementById('node-meta').innerText = JSON.stringify(meta, null, 2);

        // Rendering Connessioni (v3.5)
        const connList = document.getElementById('connections-list');
        if (fullNode.connections && fullNode.connections.length > 0) {
            connList.innerHTML = fullNode.connections.map(c => `
                <div class="cursor-pointer bg-blue-500/10 border border-blue-500/30 px-2 py-1 rounded text-[9px] hover:bg-blue-500/30 transition-all" onclick="selectNode('${c.node}')">
                    ${c.relation.toUpperCase()}: ${c.node}
                </div>
            `).join('');
        } else {
            connList.innerHTML = '<span style="color:gray; font-size:0.6rem;">Nessun arco diretto rilevato.</span>';
        }

        // Reset e Gestione Traduzione
        const transContainer = document.getElementById('node-translation-container');
        const transText = document.getElementById('node-text-translated');
        if (transContainer) transContainer.classList.add('hidden');
        
        if (content && content.length > 5) {
            // Se la lingua corrente è ENG e il testo non è brevissimo, offriamo traduzione/feedback
            fetch('/api/translate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-API-KEY': VAULT_KEY },
                body: JSON.stringify({ text: content.slice(0, 1500), lang: currentLanguage })
            })
            .then(r => r.json())
            .then(data => {
                if (data.translated && data.translated !== content) {
                    if (transContainer && transText) {
                        transContainer.classList.remove('hidden');
                        transText.innerText = data.translated;
                    }
                }
            }).catch(err => console.error("Neural Translation Fail", err));
        }

    } catch (e) {
        document.getElementById('node-text').innerHTML = `<div style="color:#ef4444; border:1px solid #ef4444; padding:0.8rem; border-radius:8px;">❌ <b>Errore Investigazione:</b> ${e.message}</div>`;
        document.getElementById('node-meta').innerText = "{}";
        console.error("Deep search fail:", e);
    }

    // Initial report state
    const reportDiv = document.getElementById('investigator-report');
    if (reportDiv) reportDiv.innerHTML = '<p class="text-gray-400 italic">Awaiting tactical focus...</p>';
}

async function analyzeNodeVulnerability() {
    if (!selectedNodeId) return;
    const reportDiv = document.getElementById('investigator-report');
    if (!reportDiv) {
        console.warn("⚠️ Investigator container not found in current sector.");
        return;
    }
    
    reportDiv.innerHTML = '<div class="flex items-center gap-2"><i class="fas fa-spinner fa-spin"></i> Audit avversariale in corso...</div>';
    
    try {
        const resp = await fetch(`/api/report/${selectedNodeId}`, { headers: { 'X-API-KEY': VAULT_KEY }});
        if (resp.ok) {
            const verdict = await resp.json();
            displayWeaknessReport(verdict);
        } else {
            const err = await resp.json();
            reportDiv.innerHTML = `<p style="color:#ef4444;">❌ Errore Audit: ${err.detail || 'Access Denied'}</p>`;
        }
    } catch (e) {
        const grid = document.getElementById('investigator-report');
        if (grid) grid.innerHTML = `<div style="padding:2rem; color:#ef4444;">[FAIL]: ${e.message}</div>`;
    }
}

function closeAuditLedger() {
    const modal = document.getElementById('audit-ledger-modal');
    if (modal) {
        modal.classList.add('hidden');
        setTimeout(() => { modal.style.display = 'none'; }, 300);
    }
}

function displayWeaknessReport(v) {
    const reportDiv = document.getElementById('investigator-report');
    if (!reportDiv) return;
    
    // Supporto versatile per diversi formati di risposta
    const risk = v.stability !== undefined ? v.stability : (v.risk_score !== undefined ? (1 - v.risk_score) : 0.5);
    const list = v.vulnerabilities || v.weaknesses || [];
    const note = v.agent_notes || v.investigator_note || v.recommendation || "Analisi completata.";

    const html = `
        <div class="space-y-4">
            <div class="flex justify-between border-b border-white/5 pb-2">
                <span class="text-purple-400 font-bold" style="font-size: 0.6rem;">STABILITÀ:</span>
                <span class="${risk < 0.5 ? 'text-red-400' : 'text-green-400'} font-black" style="font-size: 0.7rem;">${(risk * 100).toFixed(1)}%</span>
            </div>
            <div>
                <div class="text-[0.6rem] text-gray-500 mb-1">PUNTI CRITICI:</div>
                <ul class="list-disc list-inside text-gray-300" style="font-size: 0.65rem;">
                    ${list.length > 0 ? list.map(w => `<li>${w}</li>`).join('') : `<li>Nessuna vulnerabilità critica rilevata.</li>`}
                </ul>
            </div>
            <div class="bg-purple-900/20 p-2 rounded text-purple-300 italic border-l-2 border-purple-500" style="font-size: 0.65rem; margin-top: 10px;">
                "${note}"
            </div>
        </div>
    `;
    reportDiv.innerHTML = html;
}

function closeInspector() {
    const sidebar = document.getElementById('node-sidebar');
    if (sidebar) sidebar.classList.add('hidden');
    selectedNodeId = null;
}

// 3. SOVEREIGN MODEL MANAGEMENT
let currentHubFilterOnlyInstalled = false;

async function refreshModels() {
    try {
        const r = await fetch('/api/models/status', { headers: { 'X-API-KEY': VAULT_KEY }});
        const d = await r.json();
        installedModels = d.installed; // Ora è una lista di oggetti con {name, size, metadata}
        updateModelSelector();
        if (document.getElementById('model-hub-modal').style.display === 'flex') {
            renderModelHubTable();
        }
    } catch (e) { console.error("Ollama sync failed", e); }
}

function updateModelSelector() {
    const selector = document.getElementById('ai-model-selector');
    if (!selector) return;

    selector.innerHTML = installedModels.map(m => 
        `<option value="${m.name}">${m.name.toUpperCase()} (${m.size})</option>`
    ).join('');
    
    if (installedModels.length === 0) {
        selector.innerHTML = `<option value="">NESSUNA IA RILEVATA</option>`;
    }
}

async function openModelHub() {
    document.getElementById('model-hub-modal').style.display = 'flex';
    renderModelHubTable();
}

function closeModelHub() {
    document.getElementById('model-hub-modal').style.display = 'none';
}

function toggleHubFilter(onlyInstalled) {
    currentHubFilterOnlyInstalled = onlyInstalled;
    renderModelHubTable();
}

async function renderModelHubTable() {
    const tbody = document.getElementById('hub-model-table-body');
    const catalogResp = await fetch('/api/models/catalog', { headers: { 'X-API-KEY': VAULT_KEY }});
    const catalog = await catalogResp.json();
    
    tbody.innerHTML = '';
    
    // Uniamo modelli del catalogo e modelli rilevati installati
    const catalogIds = Object.keys(catalog);
    const installedIds = installedModels.map(m => m.name);
    const allUniqueIds = Array.from(new Set([...catalogIds, ...installedIds]));
    
    const installedMap = {};
    installedModels.forEach(m => { installedMap[m.name] = m; });

    allUniqueIds.sort((a, b) => {
        // Mantiene i modelli del catalogo in alto, poi gli altri
        const aInCat = catalogIds.includes(a);
        const bInCat = catalogIds.includes(b);
        if (aInCat && !bInCat) return -1;
        if (!aInCat && bInCat) return 1;
        return a.localeCompare(b);
    });

    allUniqueIds.forEach(id => {
        const isInstalled = !!installedMap[id];
        if (currentHubFilterOnlyInstalled && !isInstalled) return;

        const info = catalog[id] || { 
            name: id, 
            size: isInstalled ? installedMap[id].size : "N/D", 
            category: "CUSTOM / LOCAL",
            caveau: "Rilevato autonomamente sul dispositivo.",
            forza: "Dipende dall'architettura originale.",
            task: "General Inference",
            synergy: []
        };
        
        const source = isInstalled ? (installedMap[id].source || "Ollama") : "Cloud/Catalog";
        const row = document.createElement('tr');
        row.style.background = isInstalled ? 'rgba(59, 130, 246, 0.05)' : 'transparent';
        row.style.borderBottom = '1px solid rgba(255,255,255,0.05)';
        row.style.transition = 'all 0.3s ease';
        
        row.innerHTML = `
            <td style="padding: 1.5rem 1rem;">
                <div style="font-weight: 800; color: #fff; display: flex; align-items: center; gap: 0.5rem;">
                    ${info.name} ${isInstalled ? '<span style="font-size: 0.5rem; background: #4ade80; color: black; padding: 0.1rem 0.4rem; border-radius: 4px; font-weight: 900;">LIVE</span>' : ''}
                </div>
                <div style="font-size: 0.6rem; color: #3b82f6; font-family: 'JetBrains Mono'; margin-top: 0.3rem;">
                    SIZE: ${isInstalled ? installedMap[id].size : info.size} | <span style="color: #a855f7;">SRC: ${source}</span>
                </div>
            </td>
            <td style="padding: 1.5rem 1rem;">
                <span style="background: rgba(59, 130, 246, 0.1); color: #3b82f6; padding: 0.2rem 0.6rem; border-radius: 4px; font-size: 0.6rem; font-weight: 800;">${info.category}</span>
            </td>
            <td style="padding: 1.5rem 1rem; color: #94a3b8; font-size: 0.7rem; line-height: 1.4;">${info.caveau || 'N/D'}</td>
            <td style="padding: 1.5rem 1rem; color: #4ade80; font-size: 0.7rem; line-height: 1.4; font-weight: 600;">${info.forza || 'N/D'}</td>
            <td style="padding: 1.5rem 1rem;">
                <div style="font-size: 0.65rem; color: #a855f7; font-weight: 800; text-transform: uppercase;">TASK: ${info.task}</div>
                <div style="font-size: 0.55rem; color: #8b949e; margin-top: 0.3rem;">Sinergia: ${info.synergy && info.synergy.length ? info.synergy.join(', ') : 'NESSUNA'}</div>
            </td>
            <td style="padding: 1.5rem 1rem; text-align: center;">
                ${isInstalled ? 
                    `<button onclick="deleteModel('${id}')" style="background: rgba(239, 68, 68, 0.1); border: 1px solid #ef4444; color: #ef4444; padding: 0.4rem 1rem; border-radius: 6px; font-size: 0.6rem; font-weight: 800; cursor: pointer; transition: 0.3s;" onmouseover="this.style.background='rgba(239, 68, 68, 0.3)'" onmouseout="this.style.background='rgba(239, 68, 68, 0.1)'">DESTRUCT</button>` :
                    `<button onclick="startInstallation('${id}')" style="background: #3b82f6; border: none; color: white; padding: 0.4rem 1.5rem; border-radius: 6px; font-size: 0.6rem; font-weight: 800; cursor: pointer; transition: 0.3s; box-shadow: 0 0 15px rgba(59, 130, 246, 0.3);" onmouseover="this.style.transform='scale(1.05)'" onmouseout="this.style.transform='scale(1)'">INSTALL UPLINK</button>`
                }
            </td>
        `;
        tbody.appendChild(row);
    });
}

async function deleteModel(modelName) {
    if (!confirm(`Sei sicuro di voler distruggere la sinapsi ${modelName}? Questa operazione è irreversibile.`)) return;
    
    log(`⚠️ Iniziata procedura di DESTRUCT per ${modelName}...`, "#ef4444");
    try {
        const r = await fetch(`/api/models/delete/${modelName}`, { 
            method: 'DELETE',
            headers: { 'X-API-KEY': VAULT_KEY }
        });
        const d = await r.json();
        if (d.status === 'deleted') {
            log(`✅ Sinapsi ${modelName} rimossa con successo dal disco.`, "#4ade80");
            refreshModels();
        } else {
            throw new Error(d.message);
        }
    } catch (e) {
        log(`❌ Errore durante la rimozione: ${e.message}`, "#ef4444");
    }
}

function openInstallModal(model) {
    const modal = document.getElementById('install-modal');
    document.getElementById('modal-title').innerText = `SINAPSI MANCANTE: ${model.toUpperCase()}`;
    document.getElementById('modal-confirm-btn').onclick = () => startInstallation(model);
    modal.style.display = 'flex';
}

function closeInstallModal() {
    document.getElementById('install-modal').style.display = 'none';
}

async function startInstallation(model) {
    const progressDiv = document.getElementById('install-progress');
    const fill = document.getElementById('install-progress-fill');
    const text = document.getElementById('install-status-text');
    
    // Auto-open install modal and close hub
    document.getElementById('install-modal').style.display = 'flex';
    document.getElementById('modal-title').innerText = `SINAPSI IN UPLINK: ${model.toUpperCase()}`;
    closeModelHub();
    
    progressDiv.style.display = 'block';
    log(`Agent007: Initiating real-time pull for ${model}...`, "#a855f7");
    
    try {
        const resp = await fetch('/api/models/install', {
            method: 'POST',
            headers: { 'X-API-KEY': VAULT_KEY, 'Content-Type': 'application/json' },
            body: JSON.stringify({ model: model })
        });
        
        if (!resp.ok) throw new Error("Trigger failed");

        // Polling Progress
        const pollInterval = setInterval(async () => {
            try {
                const pResp = await fetch('/api/models/progress', { headers: { 'X-API-KEY': VAULT_KEY } });
                const progress = await pResp.json();
                const myModel = progress[model];

                if (myModel) {
                    fill.style.width = `${myModel.percentage}%`;
                    text.innerText = `SYNAPSE [${model}]: ${myModel.percentage}% - ${myModel.status.toUpperCase()}`;
                    
                    if (myModel.status === 'success' || (myModel.status === 'idle' && myModel.percentage === 100)) {
                        clearInterval(pollInterval);
                        log(`✅ ${model} Synapse Integrated.`, "#4ade80");
                        setTimeout(() => { closeInstallModal(); refreshModels(); }, 1500);
                    }
                    if (myModel.status === 'error') {
                        clearInterval(pollInterval);
                        log(`❌ Download Error: ${myModel.message}`, "#ef4444");
                        text.innerText = "ERROR IN SYNAPSE UPLINK";
                    }
                }
            } catch (e) { console.error(e); }
        }, 800);

    } catch (e) { 
        log("Install trigger failed.", "#ef4444"); 
        progressDiv.style.display = 'none';
    }
}

// 4. TELEMETRY & HUD
function initSSE() {
    log("Synchronizing Neural Stream...", "#3b82f6");
    if (eventSource) eventSource.close();
    
    const sseUrl = `/events?api_key=${VAULT_KEY}`;
    eventSource = new EventSource(sseUrl);
    
    eventSource.onopen = () => {
        log("⚡ Neural Mesh Linked. Receiving telemetry...", "#4ade80");
        console.log("📡 SSE Heartbeat: OPEN");
        document.getElementById('stat-nodes').innerText = "SYNCING...";
    };

    eventSource.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            
            // [Phase 11.5] HOT-FIX: Sync settings IMMEDIATELY to suppress modals in this frame
            if (data.lab && data.lab.settings) {
                syncSwarmSettings(data.lab.settings);
            }

            const points = data.points || data.point_cloud;
            const synapses = data.links || data.synapses || data.edge_sample;
            
            if (points && points.length > 0) {
                console.log(`📦 [SSE] Ricevuti ${points.length} nodi e ${synapses ? synapses.length : 0} sinapsi.`);
                vaultPoints = points; 
                vaultLinks = synapses || [];
                updateThreeScene(points, synapses || []);
                if (currentView === 'nets') updateNets(points, synapses || []);
            }
            if (data.nodes_count !== undefined) {
                const el = document.getElementById('stat-nodes');
                if (el) el.innerText = data.nodes_count;
                const el2 = document.getElementById('stat-nodes-2');
                if (el2) el2.innerText = data.nodes_count;
            }
            if (data.edges_count !== undefined) {
                const el = document.getElementById('stat-synapses');
                if (el) el.innerText = data.edges_count;
                const el2 = document.getElementById('stat-synapses-2');
                if (el2) el2.innerText = data.edges_count;
            }
            if (data.storage) {
                const sEl = document.getElementById('stat-storage');
                const pEl = document.getElementById('stat-pulse');
                if (sEl) sEl.innerText = data.storage.total;
                if (pEl) {
                    pEl.innerText = data.storage.pulse;
                    pEl.style.color = data.storage.pulse === "STABLE" ? "#8b949e" : "#4ade80";
                    if (data.storage.pulse !== "STABLE") {
                        pEl.style.textShadow = "0 0 10px #4ade80";
                        setTimeout(() => { pEl.style.textShadow = "none"; }, 500);
                    }
                }
            }
            if (data.agent007) {
                const e = document.getElementById('stat-agent007-entities');
                const r = document.getElementById('stat-agent007-relations');
                if (e) e.innerText = data.agent007.entities_count;
                if (r) r.innerText = data.agent007.relations_count;
                const entEl = document.getElementById('stat-entities');
                if (entEl) entEl.innerText = data.agent007.entities_count;
                
                const distEl = document.getElementById('stat-distance');
                if (distEl && data.lab && data.lab.weather && data.lab.weather.umidita_cache) {
                    distEl.innerText = (parseFloat(data.lab.weather.umidita_cache) / 100).toFixed(2);
                }
            }
            if (data.system) updateHardwareObservatory(data.system);
            if (data.lab) {
                updateCognitiveWeather(data.lab.weather);
                renderLabSwarm(data.lab.agents);
                renderBlackboard(data.lab.blackboard);
                
                // 🛸 [Swarm Kinetics] Unified 3D Target Update (v24.2)
                const ag = data.lab.agents || {};
                
                // JANITRON Synchronization (JA-001)
                const jData = ag['JA-001'] || (data.lab && data.lab.janitor);
                if (jData && janitorGroup) {
                    janitorGroup.visible = true;
                    if (janitorLabel) janitorLabel.visible = true;
                    
                    const jX = parseFloat(jData.pos.x);
                    const jY = parseFloat(jData.pos.y);
                    const jZ = parseFloat(jData.pos.z);
                    
                    if (!isNaN(jX)) {
                        janitorTargetPos.set(jX, jY, jZ);
                        if (Math.random() < 0.1) remoteLog(`[TRACE-24] JA-001 Sync: ${Math.round(jX)}, ${Math.round(jY)}`);
                    }
                    
                    const jHud = document.getElementById('janitron-hud-icon');
                    if (jHud) jHud.classList.toggle('inactive-agent', jData.mode === "Waiting");
                    
                    const jStat = document.getElementById('janitron-mission-stat');
                    const eatenCount = (data.lab && data.lab.janitor && data.lab.janitor.purged) || jData.purged || 0;
                    if (jStat) jStat.innerText = `Nodes Eaten: ${eatenCount}`;

                    // v24.3.1: RE-ACTIVATED CHOMP ANIMATION
                    const isEating = jData.mode === "Eating" || (jData.status && jData.status.includes("Eating"));
                    window._isJanitorEating = isEating; 
                    const mouthAngle = Math.abs(Math.sin(Date.now() * 0.008)) * (isEating ? 0.9 : 0.6);
                    if (janitorTop && janitorBottom) {
                        janitorTop.rotation.x = -mouthAngle;
                        janitorBottom.rotation.x = mouthAngle;
                    }
                }

                // DISTILLER Synchronization (DI-007)
                const dData = ag['DI-007'] || (data.lab && data.lab.distiller);
                if (dData && distillerGroup) {
                    distillerGroup.visible = true;
                    if (distillerLabel) distillerLabel.visible = true;
                    
                    const dX = parseFloat(dData.pos.x);
                    const dY = parseFloat(dData.pos.y);
                    const dZ = parseFloat(dData.pos.z);
                    
                    if (!isNaN(dX)) {
                        distillerTargetPos.set(dX, dY, dZ);
                    }
                    window._isDistillerPruning = dData.mode === "Pruning" || (dData.status && dData.status.includes("Pruning"));
                    
                    const dHud = document.getElementById('distiller-hud-icon');
                    if (dHud) dHud.classList.toggle('inactive-agent', dData.mode === "Waiting");
                    
                    const dStat = document.getElementById('distiller-mission-stat');
                    const prunedCount = (data.lab && data.lab.distiller && data.lab.distiller.pruned) || dData.pruned || 0;
                    if (dStat) dStat.innerText = `Arcs Pruned: ${prunedCount}`;
                }
                
                // DR. REAPER Synchronization (RP-001)
                const rData = ag['RP-001'];
                if (rData && reaperGroup) {
                    const rStat = document.getElementById('reaper-mission-stat');
                    if (rStat) rStat.innerText = `MB Reclaimed: ${rData.processed || 0}`;
                }

                // 🐍 [Snake Telemetry] Focus SN-008 (v24.2 Final Keys)
                const sData = ag['SN-008'] || data.lab.snake;
                if (sData) {
                    const sHud = document.getElementById('snake-hud-icon');
                    if (sHud) sHud.classList.remove('inactive-agent');
                    const sFound = document.getElementById('snake-mission-found');
                    const sHarvest = document.getElementById('snake-mission-stat');
                    const sProc = document.getElementById('snake-mission-processed');
                    if (sFound) sFound.innerText = `Orphans Found: ${sData.found || 0}`;
                    if (sHarvest) sHarvest.innerText = `Orphans Harvested: ${sData.harvested || 0}`;
                    if (sProc) sProc.innerText = `Orphans Deleted: ${sData.processed || 0}`;
                    
                    // Enlarge pupils
                    if (window.snakePupils) {
                        window.snakePupils.forEach(p => p.scale.set(1.5, 1.5, 1.5));
                    }
                }

                // v7.5 Global Metrics: Sync Mission Control Title
                if (data.lab.metrics) {
                    const mTitle = document.querySelector('.mission-log-title');
                    if (mTitle) {
                        mTitle.innerHTML = `<i class="fas fa-satellite-dish" style="color:#a855f7;"></i> MISSION CONTROL <span style="color:#4ade80; font-size:0.5rem; margin-left:10px;">Nodes Ready: ${data.lab.metrics.total_nodes_created || 0}</span>`;
                    }
                }
                
                // 🚀 DYNAMIC SWARM RENDERING (v15.0)
                if (data.lab.agents) {
                    if (!window.swarmSprites) window.swarmSprites = {};
                    
                    // [Fix] Handle dictionary (Object) structure if backend sends agents as dict
                    const agentList = Array.isArray(data.lab.agents) ? data.lab.agents : Object.values(data.lab.agents);
                    
                    agentList.forEach(agent => {
                        if (!agent || !agent.identity) return;
                        // Salta Janitron e Distiller (gestiti separatamente)
                        if (agent.identity.id === "JA-001" || agent.identity.id === "DI-007") return;
                        
                        if (!window.swarmSprites[agent.id]) {
                            // Creazione Sprite per Nuovo Agente
                            const group = new THREE.Group();
                            const canvas = document.createElement('canvas');
                            const context = canvas.getContext('2d');
                            canvas.width = 256; canvas.height = 256;
                            const grad = context.createRadialGradient(128,128,0,128,128,128);
                            grad.addColorStop(0, 'rgba(168, 85, 247, 1)');
                            grad.addColorStop(0.5, 'rgba(168, 85, 247, 0.3)');
                            grad.addColorStop(1, 'rgba(168, 85, 247, 0)');
                            context.fillStyle = grad;
                            context.beginPath(); context.arc(128,128,110,0,Math.PI*2); context.fill();
                            
                            const tex = new THREE.CanvasTexture(canvas);
                            const mat = new THREE.SpriteMaterial({ map: tex, transparent: true, blending: THREE.AdditiveBlending });
                            const sprite = new THREE.Sprite(mat);
                            sprite.scale.set(15000, 15000, 1);
                            group.add(sprite);
                            
                            const label = createAgentLabel(agent.name, "#a855f7");
                            label.position.y = 10000;
                            group.add(label);
                            
                            group.position.set(parseFloat(agent.pos.x), parseFloat(agent.pos.y), parseFloat(agent.pos.z));
                            scene.add(group);
                            window.swarmSprites[agent.id] = { group, target: new THREE.Vector3() };
                        }
                        
                        // Update Cinetico
                        const entry = window.swarmSprites[agent.id];
                        entry.target.set(parseFloat(agent.pos.x), parseFloat(agent.pos.y), parseFloat(agent.pos.z));
                        entry.group.position.lerp(entry.target, 0.1);
                    });
                }

                if (data.lab.blackboard) {
                    const miniLog = document.getElementById('agent-mini-log');
                    if (miniLog) {
                        // v24.3.12: Clear initial placeholder
                        if (miniLog.innerText.includes("Probing synaptic grid...")) miniLog.innerHTML = '';
                        
                        const currentMessages = Array.from(miniLog.children).map(c => c.getAttribute('data-sig') || c.innerText);
                        
                        data.lab.blackboard.forEach(signal => {
                            const sigId = `${signal.sender_id}_${signal.timestamp || Date.now()}`;
                            if (!currentMessages.includes(sigId)) {
                                const timeStr = signal.timestamp ? new Date(signal.timestamp * 1000).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit', second:'2-digit'}) : new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit', second:'2-digit'});
                                
                                let color = "#a855f7";
                                if (signal.sender_id?.includes("JANITRON") || signal.sender_id === "JA-001") color = "#facc15";
                                if (signal.sender_id?.includes("REAPER") || signal.sender_id === "RP-001") color = "#ef4444";
                                if (signal.sender_id?.includes("SNAKE") || signal.sender_id === "SN-008") color = "#10b981";
                                if (signal.sender_id?.includes("QUANTUM") || signal.sender_id === "QA-101") color = "#3b82f6";
                                if (signal.sender_id?.includes("SYNTH") || signal.sender_id === "SY-009") color = "#f472b6";
                                if (signal.sender_id?.includes("SENTINEL") || signal.sender_id === "SE-007") color = "#a855f7";
                                
                                const entry = document.createElement('div');
                                entry.setAttribute('data-sig', sigId);
                                entry.style.marginBottom = "6px";
                                entry.style.borderLeft = `2px solid ${color}`;
                                entry.style.paddingLeft = "8px";
                                entry.innerHTML = `<span style="color:#6e7681; font-size:0.45rem;">[${timeStr}]</span> <span style="color:${color}; font-weight:bold;">${signal.sender_id}:</span> ${signal.msg}`;
                                
                                miniLog.prepend(entry);
                                if (miniLog.children.length > 25) miniLog.lastElementChild.remove();
                            }
                        });
                    }
                }
            }
        } catch (e) {
            console.error('SSE Error:', e);
        }
    };
    eventSource.onerror = (e) => {
        console.warn('SSE disconnected, retrying...');
    };
}

function updateHardwareObservatory(system) {
    if (!system) return;
    // CPU
    const grid = document.getElementById('cpu-core-grid');
    if (grid && system.cpu && system.cpu.cores) {
        if (grid.children.length !== system.cpu.cores.length) {
            grid.innerHTML = system.cpu.cores.map((_, i) => `<div style="height:35px; background:rgba(59,130,246,0.1); border-radius:4px; position:relative;"><div id="core-fill-${i}" style="position:absolute; bottom:0; width:100%; background:#3b82f6; transition:0.3s;"></div></div>`).join('');
        }
        system.cpu.cores.forEach((p, i) => { const f = document.getElementById(`core-fill-${i}`); if (f) f.style.height = `${p}%`; });
    }
    // Storage Hub
    const modeB = document.getElementById('active-compute-mode');
    if (modeB) {
        modeB.innerText = `MODE: ${system.compute_mode}`;
        modeB.style.background = system.compute_mode === 'WARP' ? '#a855f7' : '#3b82f6';
    }
    
    const dnaT = document.getElementById('hardware-dna-trace');
    if (dnaT && system.hardware_dna) {
        dnaT.innerText = system.hardware_dna;
    }
    const ramF = document.getElementById('ram-usage-fill');
    if (ramF) ramF.style.width = `${system.ram.used}%`;
    const embStatus = document.getElementById('embedding-status');
    if (embStatus) embStatus.innerText = system.embedding_engine || "BGE-M3 (LOCAL)";

    // AI Intelligence HUD (New v2.6)
    if (system.ai_intelligence) {
        const ai = system.ai_intelligence;
        const nameEl = document.getElementById('ai-model-name');
        const quantEl = document.getElementById('ai-model-quant');
        const speedEl = document.getElementById('ai-inference-speed');
        const statusEl = document.getElementById('ai-learning-status');
        const msgEl = document.getElementById('ai-learning-msg');

        if (nameEl) nameEl.innerText = ai.model;
        if (quantEl) quantEl.innerText = ai.quantization;
        if (speedEl) speedEl.innerText = ai.inference_speed;
        if (statusEl) statusEl.innerText = ai.learning_status.split(' ')[0];
        if (msgEl) msgEl.innerText = ai.learning_status;
    }
}

function updateCognitiveWeather(weather) {
    if (!weather) return;
    const ids = { 'w-ops': 'pressione_ops', 'w-cache': 'umidita_cache', 'w-agents': 'tempesta' };
    for (let [id, k] of Object.entries(ids)) { const el = document.getElementById(id); if (el) el.innerText = weather[k]; }
    
    // v3.8.0: Aggiornamento Metriche Cognitive Hard (Stack inferiore)
    const metricsEl = document.getElementById('metrics-data');
    if (metricsEl && weather.retention && weather.stability) {
        metricsEl.innerText = `Ret: ${weather.retention} | Stab: ${weather.stability}`;
    }
    
    // Stato Mission Blueprint
    const blueprintEl = document.getElementById('tip-blueprint');
    if (blueprintEl) {
        if (weather.blueprint_ready) {
            blueprintEl.innerText = "● MISSION BLUEPRINT READY";
            blueprintEl.style.color = "#4ade80";
            blueprintEl.style.background = "rgba(74, 222, 128, 0.1)";
        } else {
            blueprintEl.innerText = "● AWAITING DIRECTIVE";
            blueprintEl.style.color = "#94a3b8";
            blueprintEl.style.background = "rgba(255, 255, 255, 0.05)";
        }
    }
}

function renderLabSwarm(agents) {
    const grid = document.getElementById('agent-grid');
    if (!grid) return;
    if (!agents) return;

    let html = Object.entries(agents).map(([id, a]) => {
        if (!a || !a.identity) return ''; 
        return `
            <div class="agent-card-v2" onclick="openAgentConsole('${id}')">
                <div class="agent-header">
                    <div class="agent-role">${a.identity.role || 'Agent'}</div>
                    <div class="agent-status-badge ${a.mode === 'Mission Hold' ? 'status-hold' : 'status-active'}">
                        ${a.mode === 'Mission Hold' ? 'HOLD' : 'ONLINE'}
                    </div>
                </div>
                <div style="font-weight:800; color:white; font-size: 0.9rem;">${a.identity.name || id}</div>
                <div style="font-size: 0.6rem; color: #8b949e; margin-top: 0.4rem;">${(a.status || 'Active').slice(0, 50)}...</div>
            </div>
        `;
    }).join('');

    // v2.7.6: Add Custom Agent Factory Shortcut
    html += `
        <div class="agent-card-v2" onclick="openCustomAgentModal()" style="border: 2px dashed rgba(255,255,255,0.1); display: flex; align-items: center; justify-content: center; min-height: 100px; cursor: pointer; background: transparent;">
            <div style="text-align: center;">
                <i class="fas fa-plus-circle" style="font-size: 1.2rem; color: #8b949e; margin-bottom: 0.3rem;"></i>
                <div style="font-size: 0.5rem; color: #8b949e; font-weight: 800; letter-spacing: 1px;">FACTORY</div>
            </div>
        </div>
    `;
    
    grid.innerHTML = html;
    
    window._latestAgents = agents;
    checkMissionHolds(agents);
}

// 🏺 MISSION HOLD CONTROLLER (v10.6)
let currentHoldAgent = null;

function checkMissionHolds(agents) {
    // [Phase 11.5] SUPPRESS MODALS IF AUTO-PILOT IS ON
    if (swarmSettings && swarmSettings.auto_mode === true) {
        // We still close any open modal if auto-pilot just kicked in
        if (document.getElementById('mission-hold-modal').style.display === 'flex') {
            closeMissionHold();
        }
        return; 
    }

    // Evitiamo di riaprire se già aperto
    if (document.getElementById('mission-hold-modal').style.display === 'flex') return;

    for (const [id, agent] of Object.entries(agents)) {
        if (agent.mode === "Mission Hold" && agent.hold_data) {
            openMissionHold(id, agent.hold_data);
            break; 
        }
    }
}

function openMissionHold(agentId, data) {
    currentHoldAgent = agentId;
    const modal = document.getElementById('mission-hold-modal');
    document.getElementById('hold-agent-id').innerText = agentId.toUpperCase();
    document.getElementById('hold-node-text').innerText = data.text;
    document.getElementById('hold-oracle-box').style.display = 'none';
    document.getElementById('hold-human-tip').value = '';
    
    modal.style.display = 'flex';
}

function closeMissionHold() {
    document.getElementById('mission-hold-modal').style.display = 'none';
    currentHoldAgent = null;
}

async function consultOracle() {
    const btn = document.getElementById('btn-hold-consult');
    const box = document.getElementById('hold-oracle-box');
    const reasoning = document.getElementById('hold-oracle-reasoning');
    const context = document.getElementById('hold-oracle-context');
    const tip = document.getElementById('hold-human-tip').value;

    btn.innerText = "CONSULTO IN CORSO...";
    btn.disabled = true;
    box.style.display = 'block';
    reasoning.innerHTML = `<i class="fas fa-spinner fa-spin"></i> L'Oracolo sta analizzando la memoria neurale...`;

    try {
        const resp = await fetch(`/api/lab/consult_oracle`, {
            method: 'POST',
            headers: { 'X-API-KEY': VAULT_KEY, 'Content-Type': 'application/json' },
            body: JSON.stringify({ agent_id: currentHoldAgent, feedback: tip })
        });
        const d = await resp.json();
        
        const modelId = d.oracle_model || "Ollama Substrate";
        context.innerText = `TEMA VAULT: ${d.vault_context}`;
        reasoning.innerHTML = `
            <div style="font-size: 0.55rem; color:#a855f7; margin-bottom:5px; font-weight:800; border-bottom:1px solid rgba(168,85,247,0.2); padding-bottom:5px;">
                🔮 ORACLE IDENTITY: ${modelId}
            </div>
            <strong>${d.verdict}</strong>: ${d.reasoning}
        `;
        btn.innerText = "CONSULTO COMPLETATO";
    } catch (e) {
        reasoning.innerText = "Errore durante il consulto: " + e.message;
        btn.innerText = "CHIEDI ALL'ORACOLO";
        btn.disabled = false;
    }
}

async function resolveMission(verdict) {
    if (!currentHoldAgent) return;
    
    try {
        const feedback = document.getElementById('hold-human-tip').value;
        const resp = await fetch(`/api/lab/resolve_mission`, {
            method: 'POST',
            headers: { 'X-API-KEY': VAULT_KEY, 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                agent_id: currentHoldAgent, 
                resolution: verdict, 
                feedback: feedback 
            })
        });
        
        if (verdict === 'APPROVE') {
            log(`✅ Missione Approvata per ${currentHoldAgent}`, "#4ade80");
        } else {
            log(`❌ Missione Rifiutata per ${currentHoldAgent}. Il nodo verrà mantenuto.`, "#ef4444");
        }
        
        closeMissionHold();
    } catch (e) {
        alert("Errore risoluzione: " + e.message);
    }
}

window.openAgentConsole = (id) => {
    const agent = window._latestAgents[id];
    if (!agent) return;
    
    const modal = document.getElementById('agent-modal');
    document.getElementById('modal-agent-name').innerText = `🧬 ${agent.identity.name.toUpperCase()}`;
    document.getElementById('modal-agent-bio').innerText = agent.identity.bio;
    document.getElementById('modal-agent-response').innerText = `Awaiting task directive for ${agent.identity.name}...`;
    
    modal.style.display = 'flex';
    
    // Configura tasto INVIO
    document.getElementById('send-agent-task-btn').onclick = () => sendAgentTask(id);
};

window.closeAgentModal = () => {
    document.getElementById('agent-modal').style.display = 'none';
};

async function sendAgentTask(id) {
    const input = document.getElementById('agent-task-input');
    const task = input.value.trim();
    if (!task) return;
    
    const display = document.getElementById('modal-agent-response');
    display.innerHTML = `<span class="animate-pulse">🔄 Agente in fase di computazione...</span>`;
    input.value = '';
    
    try {
        const resp = await fetch(`/api/lab/agent/${id}/task`, {
            method: 'POST',
            headers: { 'X-API-KEY': VAULT_KEY, 'Content-Type': 'application/json' },
            body: JSON.stringify({ task })
        });
        const d = await resp.json();
        display.innerText = d.response;
        log(`🏆 Agent ${d.agent} completed task.`, '#a855f7');
    } catch(e) {
        display.innerText = "❌ Neural uplink error: " + e.message;
    }
}

function renderBlackboard(posts) {
    const board = document.getElementById('lab-blackboard');
    if (!board) return;
    board.innerHTML = posts.reverse().slice(0, 15).map(p => `
        <div class="thought-packet" style="border-left:2px solid #a855f7; background:rgba(168,85,247,0.05); padding:0.8rem; border-radius:8px; margin-bottom:0.6rem; animation: fadeInSlide 0.3s ease-out;">
            <div style="font-size:0.6rem; color:#a855f7; font-weight:800; margin-bottom:0.2rem;">@${p.role.toUpperCase()} <span style="font-size:0.5rem; color:gray; float:right;">${new Date(p.timestamp * 1000).toLocaleTimeString()}</span></div>
            <div style="font-size:0.8rem; color:#e2e8f0; line-height:1.4;">${p.msg}</div>
        </div>
    `).join('');
}

// --- 2D NEURAL NETS (CYTOSCAPE) ---
function initNets() {
    if (netsInitialized) return;
    cy = cytoscape({
        container: document.getElementById('cy'),
        style: [
            { selector: 'node', style: { 
                'background-color': 'data(color)', 
                'label': 'data(label)', 
                'color': '#fff', 
                'font-size': '8px', 
                'width': 32, 
                'height': 32,
                'text-valign': 'top',
                'text-margin-y': -5,
                'font-family': 'JetBrains Mono',
                'font-weight': 'bold',
                'border-width': 1,
                'border-color': 'rgba(255,255,255,0.1)'
            } },
            { selector: 'edge', style: { 
                'width': 1.5, 
                'line-color': '#ffffff', 
                'target-arrow-color': '#ffffff', 
                'target-arrow-shape': 'triangle', 
                'curve-style': 'bezier',
                'opacity': 0.6
            } }
        ],
        layout: { name: 'cose', animate: false }
    });
    netsInitialized = true;
}

function updateNets(nodes, links = []) {
    if (!cy) return;
    
    cy.batch(() => {
        const currentIds = new Set(cy.nodes().map(n => n.id()));
        // Prendiamo gli ultimi 100 nodi in modo deterministico per evitare balzelli (v3.6)
        const nextNodes = nodes.slice(-100);
        const nextIds = new Set(nextNodes.map(n => n.id));

        // Rimuovi nodi obsoleti
        cy.nodes().forEach(n => {
            if (!nextIds.has(n.id())) n.remove();
        });

        // Aggiungi nuovi nodi con Tematizzazione Colore (v3.9.0)
        nextNodes.forEach(n => {
            if (!currentIds.has(n.id)) {
                // Generazione colore basata su tema se mancante
                const themeColor = n.color || stringToColor(n.label || "Cognitive");
                cy.add({ data: { 
                    id: n.id, 
                    label: n.label || n.text.slice(0, 15), 
                    color: themeColor 
                } });
            }
        });

        // Aggiorna Archi
        cy.edges().remove();
        links.forEach(l => {
            if (cy.getElementById(l.source).length && cy.getElementById(l.target).length) {
                cy.add({ data: { source: l.source, target: l.target } });
            }
        });
    });

    // v3.8.0: Layout Statico e Intelligente (Alta Repulsione per chiarezza)
    const currentStructure = `${nodes.length}-${links.length}`;
    if (window.lastGraphStructure !== currentStructure) {
        cy.layout({ 
            name: 'cose', 
            animate: true, 
            animationDuration: 1000,
            nodeRepulsion: 60000,   // Nodi molto più distanti
            idealEdgeLength: 150,
            gravity: 0.1,
            numIter: 1000,
            initialTemp: 200
        }).run();
        window.lastGraphStructure = currentStructure;
        if (cy.nodes().length < 40) cy.fit();
    }
}

window.addEventListener('resize', () => {
    if (labRenderer && labCamera && document.getElementById('lab-three-container')) {
        const container = document.getElementById('lab-three-container');
        labCamera.aspect = container.clientWidth / container.clientHeight;
        labCamera.updateProjectionMatrix();
        labRenderer.setSize(container.clientWidth, container.clientHeight);
    }
});

// 🌐 KNOWLEDGE EXPANSION PROTOCOL (v4.0)
async function checkExpansionProposals(jobId) {
    try {
        const r = await fetch(`/api/forage/proposals/${jobId}`);
        const d = await r.json();
        if (d.proposals && d.proposals.length > 0) {
            showExpansionModal(jobId, d.proposals);
        }
    } catch (e) {}
}

function showExpansionModal(jobId, proposals) {
    const modal = document.getElementById('expansion-modal');
    const container = document.getElementById('proposal-container');
    if (!modal || !container) return;
    
    // Filtriamo proposte uniche per evitare duplicati visivi
    const uniqueProposals = proposals.reduce((acc, current) => {
        const x = acc.find(item => item.topic === current.topic);
        if (!x) return acc.concat([current]);
        else return acc;
    }, []);

    // Salviamo il jobId corrente per l'approvazione globale
    window.currentForageJobId = jobId; 
    
    container.innerHTML = uniqueProposals.map(p => `
        <div style="background:rgba(59,130,246,0.1); border:1px solid rgba(59,130,246,0.2); padding:0.8rem; border-radius:12px; display:flex; flex-direction:column; gap:0.4rem; animation: fadeInSlide 0.3s ease-out;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <span style="font-size:0.75rem; color:#fff; font-weight:800; letter-spacing:0.5px;">🔍 ${p.topic}</span>
                <span style="font-size:0.5rem; background:#3b82f6; color:black; padding:0.1rem 0.4rem; border-radius:4px; font-weight:800;">EXTERNAL POI</span>
            </div>
            <div style="font-size:0.55rem; color:#3b82f6; font-family:'JetBrains Mono'; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">URL: ${p.url}</div>
            <div style="font-size:0.55rem; color:#94a3b8; font-style:italic; line-height:1.3;">Scoperto in: ${p.context}</div>
        </div>
    `).join('');
    
    modal.style.display = 'flex';
}

function closeExpansionModal() {
    const modal = document.getElementById('expansion-modal');
    if (modal) modal.style.display = 'none';
}

async function approveExpansion() {
    const jobId = window.currentForageJobId;
    if (!jobId) return;
    
    log("🚀 [Deep Research] Espansione autorizzata. Attivazione Swarm multi-lingua...", "#f59e0b");
    closeExpansionModal();
    
    try {
        const r = await fetch(`/api/forage/approve/${jobId}`, { 
            method: 'POST',
            headers: { 'X-API-KEY': VAULT_KEY }
        });
        const d = await r.json();
        log(`🌐 [Expansion] Missione approvata: ${d.mission_count} aree di ricerca in coda.`, "#4ade80");
        log(`📡 [Neural Mesh] Creazione nodi oro per filamenti esterni...`, "#f59e0b");
    } catch (e) { 
        log(`Expansion uplink failed: ${e.message}`, '#ef4444'); 
    }
}

// 🧠 NEURAL EVOLUTION ENGINE (v5.0)
async function triggerEvolution() {
    // v3.9.5: La soglia di invecchiamento viene fissata all'INIZIO dell'evoluzione.
    // Tutto ciò che esisteva prima diventa "Legacy" (Grigio).
    // Le nuove sinapsi generate dall'algoritmo avranno un timestamp superiore e rimarranno bianche/pulsanti.
    window.synapseLegacyThreshold = Date.now() / 1000;

    const btn = document.getElementById('evolve-btn');
    if (btn) {
        btn.disabled = true;
        btn.innerText = 'EVOLVING...';
        btn.style.background = '#6366f1';
    }

    log("🧠 EVOLUTION: Inizio protocollo di manutenzione cognitiva...", "#a855f7");
    
    try {
        const r = await fetch('/api/evolve', {
            method: 'POST',
            headers: { 'X-API-KEY': VAULT_KEY }
        });
        
        if (!r.ok) {
            const errorData = await r.json().catch(() => ({}));
            throw new Error(errorData.detail || "Evolution Uplink Failed");
        }
        
        const d = await r.json();
        
        // Feedback Visivo: Pulse sulla Nebula e Re-aging
        if (typeof vaultPoints !== 'undefined' && vaultPoints) {
            log("✨ Nebula Re-aligned. Legacy synapses solidified.", "#4ade80");
            updateThreeScene(vaultPoints, vaultLinks || []);
        }

        log(`✅ ${d.report}`, '#4ade80');
        log(`📊 Ottimizzati ${d.nodes_optimized} nodi | Realizzate ${d.new_synapses || 0} nuove sinapsi | Potati ${d.edges_pruned} archi.`, '#3b82f6');
        
        // Forza un refresh dei nodi per visualizzare la migrazione (se gestita da SSE)
        updateKnowledgeInventory();

    } catch (e) {
        log(`❌ Evolution Error: ${e.message}`, '#ef4444');
    } finally {
        if (btn) {
            btn.disabled = false;
            const lang = translations[currentLanguage];
            btn.innerText = lang['evolve-btn'];
            btn.style.background = '#a855f7';
        }
    }
}

function initLab3D() {
    const container = document.getElementById('lab-three-container');
    if (!container) return;
    
    const canvas = document.getElementById('lab-canvas');
    if (!canvas) {
        container.innerHTML = '<canvas id="lab-canvas" style="width:100%; height:100%; cursor: move;"></canvas>';
    }
    const targetCanvas = document.getElementById('lab-canvas');
    
    labScene = new THREE.Scene();
    const width = container.clientWidth || 600;
    const height = container.clientHeight || 400;

    labCamera = new THREE.PerspectiveCamera(45, width / height, 1, 20000000);
    labCamera.position.set(300000, 300000, 300000);
    labCamera.lookAt(0, 0, 0);

    labRenderer = new THREE.WebGLRenderer({ canvas: targetCanvas, antialias: true, alpha: true });
    labRenderer.setSize(width, height);
    labRenderer.setClearColor(0x000000, 0);

    // [v2.7.5] Phoenix Architecture Sync
    labCube = new THREE.Mesh(
        new THREE.BoxGeometry(200000, 200000, 200000),
        new THREE.MeshBasicMaterial({ color: 0x3b82f6, wireframe: true, transparent: true, opacity: 0.15 })
    );
    labScene.add(labCube);

    labGrid = new THREE.GridHelper(1000000, 20, 0x1e1b4b, 0x1e1b4b);
    labGrid.position.y = -100000;
    labScene.add(labGrid);

    labSun = new THREE.Mesh(
        new THREE.SphereGeometry(10000, 32, 32),
        new THREE.MeshBasicMaterial({ color: 0xffffff })
    );
    labScene.add(labSun);

    const animateLab = () => {
        requestAnimationFrame(animateLab);
        labCube.rotation.y += 0.001;
        if (labRenderer && labScene && labCamera) {
            labRenderer.render(labScene, labCamera);
        }
    };
    animateLab();
}

/** [v2.7.5] Lab Fullscreen Controller */
function toggleLabFullscreen() {
    const container = document.getElementById('lab-view');
    if (!document.fullscreenElement) {
        container.requestFullscreen().catch(e => console.error(e));
        // Show Fullscreen UI
        injectLabFullscreenHUD();
    } else {
        document.exitFullscreen();
        removeLabFullscreenHUD();
    }
}

function injectLabFullscreenHUD() {
    let hud = document.getElementById('lab-fs-hud');
    if (hud) return;
    
    hud = document.createElement('div');
    hud.id = 'lab-fs-hud';
    hud.style = "position: fixed; inset: 0; z-index: 9999; pointer-events: none; display: flex; flex-direction: column; padding: 2rem;";
    
    hud.innerHTML = `
        <!-- Top Prompt (Mission Control) -->
        <div style="pointer-events: auto; background: rgba(15, 23, 42, 0.9); backdrop-filter: blur(20px); border: 1px solid #a855f7; border-radius: 12px; padding: 1rem; width: 60%; margin: 0 auto; display: flex; flex-direction: column; gap: 0.5rem; box-shadow: 0 10px 40px rgba(0,0,0,0.8);">
            <div style="font-size: 0.6rem; color: #a855f7; font-weight: 800; letter-spacing: 2px;">SYS_MISSION_CONTROL</div>
            <div style="display: flex; gap: 1rem;">
                <input type="text" id="lab-fs-input" placeholder="Enter mission directive..." style="flex: 1; background: transparent; border: none; border-bottom: 1px solid rgba(255,255,255,0.2); color: white; outline: none; font-family: 'JetBrains Mono';">
                <button onclick="sendLabDirective()" style="background: #a855f7; color: white; border: none; padding: 0.5rem 1.5rem; border-radius: 6px; font-weight: 800; cursor: pointer;">DISPATCH</button>
            </div>
            <div id="lab-fs-feedback" style="font-size: 0.6rem; color: #4ade80; font-family: 'JetBrains Mono'; margin-top: 5px;">[AWAITING_INPUT]</div>
        </div>
        
        <!-- Right Agent Bar -->
        <div id="lab-fs-agent-bar" style="pointer-events: auto; position: absolute; right: 2rem; top: 10rem; bottom: 2rem; width: 280px; background: rgba(15, 23, 42, 0.85); backdrop-filter: blur(15px); border-left: 2px solid #a855f7; padding: 1.5rem; overflow-y: auto; border-radius: 12px; box-shadow: -10px 0 30px rgba(0,0,0,0.5);">
            <div style="font-size: 0.7rem; color: #a855f7; font-weight: 900; margin-bottom: 1.5rem; text-align: center;">AGENT_SWARM_COMS</div>
            <div id="lab-fs-agent-list"></div>
        </div>
        
        <!-- Exit Button -->
        <button onclick="document.exitFullscreen()" style="pointer-events: auto; position: absolute; bottom: 2rem; left: 2rem; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); color: #8b949e; padding: 0.8rem; border-radius: 50%; cursor: pointer;"><i class="fas fa-compress"></i></button>
    `;
    
    document.body.appendChild(hud);
    syncLabAgentsToFS();
}

function removeLabFullscreenHUD() {
    const hud = document.getElementById('lab-fs-hud');
    if (hud) hud.remove();
}

function syncLabAgentsToFS() {
    const list = document.getElementById('lab-fs-agent-list');
    const sourceGrid = document.getElementById('agent-grid');
    if (list && sourceGrid) {
        list.innerHTML = sourceGrid.innerHTML;
        // Inject styles compatibility
        list.querySelectorAll('.agent-card').forEach(el => {
            el.style.marginBottom = "1rem";
            el.style.background = "rgba(0,0,0,0.2)";
        });
    }
}

async function sendLabDirective() {
    const input = document.getElementById('lab-fs-input');
    const fb = document.getElementById('lab-fs-feedback');
    if (!input || !input.value) return;

    const query = input.value;
    fb.innerText = `[AWAITING_SYNAPSI]: ${query.toUpperCase()}`;
    log(`🛰️ [Lab Mission] Dispatching: ${query}`, "#a855f7");
    input.value = '';

    try {
        const resp = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'X-API-KEY': VAULT_KEY, 'Content-Type': 'application/json' },
            body: JSON.stringify({ query })
        });
        
        const data = await resp.json();
        fb.innerHTML = `<span style="color: #a855f7;">[ORACLE]:</span> ${data.answer}`;
        
        if (data.context_nodes && data.context_nodes.length > 0) {
            log(`🎯 [Lab] Highlighting ${data.context_nodes.length} context nodes.`, "#4ade80");
            // Highlight nodes in Main 3D if needed, or implement Lab highlight
        }
    } catch (e) {
        fb.innerText = `[ERROR]: Synaptic failure during alignment.`;
        log(`❌ Lab Coms Error: ${e.message}`, '#ef4444');
    }
}

window.toggleLabFullscreen = toggleLabFullscreen;
window.sendLabDirective = sendLabDirective;
// 5. CORE ACTIONS
async function runAdversarialAnalysis() {
    if (!selectedNodeId) return;
    const reportDiv = document.getElementById('weakness-report');
    reportDiv.innerHTML = '<div class="animate-pulse text-purple-400">Debating in Digital Courtroom...</div>';
    try {
        const r = await fetch('/api/analyze', { method: 'POST', headers: { 'X-API-KEY': VAULT_KEY, 'Content-Type': 'application/json' }, body: JSON.stringify({ id: selectedNodeId }) });
        const d = await r.json();
        displayWeaknessReport(d.verdict);
    } catch (e) { log("Analysis failed.", "#ef4444"); }
}


async function uploadFile(file) {
    log(`Ingesting: ${file.name}`, '#3b82f6');
    const formData = new FormData();
    formData.append('file', file);
    try {
        const r = await fetch('/api/ingest/media', { method: 'POST', headers: { 'X-API-KEY': VAULT_KEY }, body: formData });
        if (!r.ok) {
            const errText = await r.text();
            throw new Error(`Server Error (${r.status}): ${errText.slice(0, 100)}`);
        }
        const res = await r.json();
        const mainId = res.ids ? res.ids[0] : res.id;
        log(`Synapsed with ID: ${mainId}`, '#4ade80');
        updateKnowledgeInventory();
    } catch (e) { log(`Error: ${e.message}`, '#ef4444'); }
}

async function updateKnowledgeInventory() {
    try {
        const r = await fetch('/api/inventory?api_key=' + VAULT_KEY);
        const sources = await r.json();
        
        const listCard = document.getElementById('knowledge-inventory-list');
        if (listCard) {
            if (sources.length === 0) {
                listCard.innerHTML = '<div style="color:gray; font-size:0.7rem; text-align:center; padding:1rem;">Awaiting first ingestion...</div>';
                return;
            }

            listCard.innerHTML = sources.map(s => {
                const isUrl = s.source.startsWith('http');
                const icon = isUrl ? 'fa-globe' : 'fa-file-alt';
                const color = isUrl ? '#3b82f6' : '#a855f7';
                
                return `
                    <div style="background: rgba(255,255,255,0.03); border-left: 3px solid ${color}; padding: 0.8rem; margin-bottom: 0.8rem; border-radius: 4px; display: flex; flex-direction: column; gap: 0.3rem;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span style="font-size: 0.8rem; font-weight: 800; color: #e2e8f0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 70%;">
                                <i class="fas ${icon}" style="color: ${color}; margin-right: 0.5rem;"></i> ${s.title}
                            </span>
                            <span style="font-size: 0.6rem; color: #8b949e;">${s.date}</span>
                        </div>
                        <div style="font-size: 0.65rem; color: #64748b; font-family: 'JetBrains Mono'; word-break: break-all;">
                            SOURCE: ${s.source}
                        </div>
                        <div style="display: flex; gap: 1rem; margin-top: 0.3rem;">
                            <div style="font-size: 0.6rem; background: rgba(59, 130, 246, 0.1); color: #3b82f6; padding: 0.1rem 0.4rem; border-radius: 100px;">
                                <i class="fas fa-circle" style="font-size: 0.4rem; vertical-align: middle; margin-right: 0.2rem;"></i> ${s.nodes} NODES
                            </div>
                            <div style="font-size: 0.6rem; background: rgba(168, 85, 247, 0.1); color: #a855f7; padding: 0.1rem 0.4rem; border-radius: 100px;">
                                <i class="fas fa-bolt" style="font-size: 0.4rem; vertical-align: middle; margin-right: 0.2rem;"></i> ${s.edges} EDGES
                            </div>
                        </div>
                    </div>
                `;
            }).join('');
        }
    } catch (e) {
        console.error("Inventory update failed:", e);
    }
}

// 🕸️ WEB FORAGER — Completo con feedback visivo
async function forageWebFloating() {
    const input   = document.getElementById('floating-url-input');
    const btn     = document.querySelector('[onclick="forageWebFloating()"]');
    const url     = input ? input.value.trim() : '';

    if (!url || !url.startsWith('http')) {
        log('⚠️ URL non valido. Usa http:// o https://', '#ef4444');
        return;
    }

    // --- Feedback visivo: stato LOADING sul bottone ---
    if (btn) {
        btn.disabled = true;
        btn.innerText = '⏳ FORAGING...';
        btn.style.background = '#a855f7';
    }
    // v3.9.5: Soglia invecchiamento all'inizio del Foraging.
    window.synapseLegacyThreshold = Date.now() / 1000;
    log(`🕸️ Avvio Web Foraging: ${url}`, '#a855f7');

    try {
        // Mostra HUD Telemetrico
        const hud = document.getElementById('forage-telemetry-hud');
        if (hud) hud.style.display = 'flex';

        const resp = await fetch('/api/forage', {
            method: 'POST',
            headers: { 'X-API-KEY': VAULT_KEY, 'Content-Type': 'application/json' },
            body: JSON.stringify({ url, max_depth: 10, max_pages: 9999, same_domain_only: true })
        });

        if (!resp.ok) {
            const err = await resp.json();
            log(`❌ Forage fallito: ${err.detail}`, '#ef4444');
            return;
        }

        const data = await resp.json();
        log(`✅ Forage avviato (job: ${data.job_id.slice(0,8)}) — Segui il progresso nel Neural Lab`, '#4ade80');
        log(`🌐 Sovereign Mode: Ingestione ILLIMITATA attivata per ${url}`, '#3b82f6');

        if (input) input.value = '';

        // --- Polling del ThoughtMesh per mostrare pagine indicizzate ---
        activeForageJob = data.job_id;
        let pollCount = 0;
        const pollInterval = setInterval(async () => {
            pollCount++;
            try {
                const s = await fetch('/api/forage/status?api_key=' + VAULT_KEY);
                const sData = await s.json();
                
                const statNodes = document.getElementById('stat-nodes');
                if (statNodes && sData.total_nodes > 0) {
                    statNodes.innerText = sData.total_nodes;
                }

                // --- LIVE TELEMETRY UPDATE (v4.6) ---
                if (activeForageJob && sData.jobs && sData.jobs[activeForageJob]) {
                    const job = sData.jobs[activeForageJob];
                    const bar = document.getElementById('forage-progress-bar');
                    const stats = document.getElementById('forage-telemetry-stats');
                    
                    if (bar) bar.style.width = `${job.progress}%`;
                    if (stats) {
                        stats.innerHTML = `
                            <span style="color:#a855f7;">⏱️ ${job.elapsed}</span> | 
                            <span style="color:#3b82f6;">📊 ${job.progress}%</span> | 
                            <span style="color:#4ade80;">📄 ${job.pages} pag</span>
                        `;
                        stats.style.display = 'block';
                    }
                }

                // Mostra le ultime pagine indicizzate nella console
                if (sData.messages && sData.messages.length > 0) {
                    const lastMsg = sData.messages[sData.messages.length - 1];
                    if (lastMsg && lastMsg.msg) {
                        log(lastMsg.msg.slice(0, 80), '#a855f7');
                    }
                }

                // Ferma il polling dopo 600 secondi o al completamento
                if (pollCount > 400 || (sData.jobs && sData.jobs[activeForageJob] && sData.jobs[activeForageJob].status === "COMPLETE")) {
                    clearInterval(pollInterval);
                    log('🏁 Forage primario completato.', '#4ade80');
                    
                    if (sData.jobs && sData.jobs[activeForageJob] && sData.jobs[activeForageJob].status === "COMPLETE") {
                        if (typeof checkExpansionProposals === 'function') checkExpansionProposals(activeForageJob);
                    }

                    if (btn) {
                        btn.disabled = false;
                        btn.innerText = 'SYNAPSE';
                        btn.style.background = '#3b82f6';
                    }
                    updateKnowledgeInventory();
                    activeForageJob = null;
                }
            } catch (e) { console.error("Polling error:", e); }
        }, 1500);

    } catch(e) {
        log(`❌ Errore connessione: ${e.message}`, '#ef4444');
        if (btn) {
            btn.disabled = false;
            btn.innerText = 'SYNAPSE';
            btn.style.background = '#3b82f6';
        }
    }
}

// --- NEURAL ORACLE MODE (v6.0) ---
let currentCommandMode = 'FORAGING'; // 'FORAGING' or 'QUERY'

function toggleCommandMode() {
    const badge = document.getElementById('mode-badge');
    const urlInput = document.getElementById('floating-url-input');
    const queryInput = document.getElementById('floating-query-input');
    const actionBtn = document.getElementById('main-action-btn');
    const lang = translations[currentLanguage];
    
    if (currentCommandMode === 'FORAGING') {
        currentCommandMode = 'QUERY';
        badge.innerText = lang['mode-oracle'];
        badge.style.color = '#3b82f6';
        badge.style.background = 'rgba(59, 130, 246, 0.1)';
        urlInput.style.display = 'none';
        queryInput.style.display = 'block';
        actionBtn.innerText = 'ORACLE';
        actionBtn.style.background = '#3b82f6';
        actionBtn.onclick = queryNeuralVault;
    } else {
        currentCommandMode = 'FORAGING';
        badge.innerText = lang['mode-foraging'];
        badge.style.color = '#a855f7';
        badge.style.background = 'rgba(168, 85, 247, 0.1)';
        urlInput.style.display = 'block';
        queryInput.style.display = 'none';
        actionBtn.innerText = lang['main-action-btn'];
        actionBtn.style.background = '#3b82f6';
        actionBtn.onclick = forageWebFloating;
    }
}

function toggleLanguage() {
    currentLanguage = (currentLanguage === 'IT') ? 'EN' : 'IT';
    const lang = translations[currentLanguage];
    
    // Update Sidebar Navigation
    document.getElementById('nav-overview').innerText = lang['nav-overview'];
    document.getElementById('nav-lab').innerText = lang['nav-lab'];
    document.getElementById('nav-nets').innerText = lang['nav-nets'];
    document.getElementById('nav-chat').innerText = lang['nav-chat'];
    document.getElementById('nav-analytics').innerText = lang['nav-analytics'];
    document.getElementById('nav-settings').innerText = lang['nav-settings'];
    
    // Update System Status
    document.getElementById('label-system-status').innerText = lang['label-system-status'];
    document.getElementById('label-kernel-online').innerText = lang['label-kernel-online'];
    document.getElementById('current-flag').innerText = lang['flag'];
    
    // Update Main Buttons
    document.getElementById('main-action-btn').innerText = (currentCommandMode === 'FORAGING') ? lang['main-action-btn'] : 'ORACLE';
    document.getElementById('evolve-btn').innerText = lang['evolve-btn'];
    
    // Update Placeholders
    document.getElementById('floating-url-input').placeholder = lang['input-url-placeholder'];
    document.getElementById('floating-query-input').placeholder = lang['input-query-placeholder'];
    
    // Update Pillars Titles
    document.getElementById('title-cognitive').innerHTML = lang['title-cognitive'];
    document.getElementById('title-distance').innerHTML = lang['title-distance'];
    document.getElementById('title-tracing').innerHTML = lang['title-tracing'];
    document.getElementById('title-inventory').innerHTML = lang['title-inventory'];
    document.getElementById('title-hardbank').innerHTML = lang['title-hardbank'];
    document.getElementById('title-portal').innerHTML = lang['title-portal'];
    
    // Update Mode Badge
    const badge = document.getElementById('mode-badge');
    badge.innerText = (currentCommandMode === 'FORAGING') ? lang['mode-foraging'] : lang['mode-oracle'];

    // Update Agent007 Panel
    document.getElementById('label-agent007-title').innerHTML = lang['agent007-title'];
    document.getElementById('btn-analyze-vulnerability').innerText = lang['agent007-analyze'];
    const reportPlace = document.getElementById('label-agent007-placeholder');
    if (reportPlace) reportPlace.innerText = lang['agent007-placeholder'];

    updateTooltips();

    log(`🌐 Lingua impostata su: ${currentLanguage === 'IT' ? 'ITALIANO' : 'ENGLISH'}`, '#a855f7');
}

function updateTooltips() {
    const tips = translations[currentLanguage].tooltips;
    for (const [id, text] of Object.entries(tips)) {
        const el = document.getElementById(id);
        if (el) el.setAttribute('data-tooltip', text);
    }
}

function copyTracingLog() {
    const console = document.getElementById('aura-console');
    if (!console) return;
    const text = console.innerText;
    navigator.clipboard.writeText(text).then(() => {
        log("📋 Engine logs copied to clipboard.", "#4ade80");
    }).catch(err => {
        console.error('Failed to copy: ', err);
    });
}

async function queryNeuralVault() {
    const query = document.getElementById('floating-query-input').value;
    if (!query) return;

    const responseHud = document.getElementById('oracle-response-hud');
    const answerEl = document.getElementById('oracle-answer');
    const sourcesEl = document.getElementById('oracle-sources');
    
    responseHud.style.display = 'flex';
    answerEl.innerText = "Consultazione sinapsi in corso...";
    
    log(`🔮 [Oracle] Interrogazione: "${query}"`, "#3b82f6");

    try {
        const resp = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'X-API-KEY': VAULT_KEY, 'Content-Type': 'application/json' },
            body: JSON.stringify({ query })
        });
        
        const data = await resp.json();
        answerEl.innerText = data.answer;
        sourcesEl.innerText = `Sorgenti attivate: [${data.context_nodes.length}]`;
        
        if (data.context_nodes && data.context_nodes.length > 0) {
            highlightAndZoomToNodes(data.context_nodes);
        }

    } catch (e) {
        answerEl.innerText = "Errore nell'allineamento dei vettori.";
        log(`❌ Oracle Error: ${e.message}`, '#ef4444');
    }
}

function highlightAndZoomToNodes(nodeIds) {
    if (!window.nodesGroup) return;
    
    let targetX = 0, targetY = 0, targetZ = 0;
    let foundCount = 0;
    
    window.nodesGroup.children.forEach(mesh => {
        if (nodeIds.includes(mesh.userData.id)) {
            mesh.material.emissive.setHex(0xffffff);
            mesh.scale.set(3, 3, 3);
            
            targetX += mesh.position.x;
            targetY += mesh.position.y;
            targetZ += mesh.position.z;
            foundCount++;
            
            setTimeout(() => {
                mesh.material.emissive.setHex(0x000000);
                mesh.scale.set(1, 1, 1);
            }, 5000);
        } else {
            mesh.material.opacity = 0.2;
            setTimeout(() => mesh.material.opacity = 1.0, 5000);
        }
    });

    if (foundCount > 0) {
        targetX /= foundCount;
        targetY /= foundCount;
        targetZ /= foundCount;
        
        const offset = 300;
        const camTarget = { x: targetX + offset, y: targetY + offset, z: targetZ + offset };
        
        log(`🛸 [Fly-through] Navigazione verso cluster semantico...`, "#3b82f6");
        
        if (window.camera) {
            if (window.controls) {
                window.controls.target.set(targetX, targetY, targetZ);
            }
            window.camera.position.set(camTarget.x, camTarget.y, camTarget.z);
        }
    }
}

async function uploadMediaSynapse(file) {
    if (!file) return;
    log(`📎 [Media] Preparazione sinapsi per: ${file.name}`, "#a855f7");
    
    const telemetryHud = document.getElementById('forage-telemetry-hud');
    const statsEl = document.getElementById('forage-telemetry-stats');
    const barEl = document.getElementById('forage-progress-bar');
    
    if (telemetryHud) telemetryHud.style.display = 'flex';
    if (statsEl) statsEl.innerHTML = `<span>UPLOADING: ${file.name}</span> <span id="upload-percent">0%</span>`;
    
    const formData = new FormData();
    formData.append("file", file);
    
    try {
        const xhr = new XMLHttpRequest();
        xhr.open("POST", "/api/ingest/media", true);
        xhr.setRequestHeader("X-API-KEY", VAULT_KEY);
        
        xhr.upload.onprogress = (e) => {
            if (e.lengthComputable) {
                const percent = Math.round((e.loaded / e.total) * 100);
                if (barEl) barEl.style.width = `${percent}%`;
                const upP = document.getElementById('upload-percent');
                if (upP) upP.innerText = `${percent}%`;
            }
        };
        
        xhr.onload = function() {
            if (xhr.status === 200) {
                const data = JSON.parse(xhr.responseText);
                log(`✅ [Media] Sinapsi completata. Creati ${data.nodes_created} nodi sensoriali.`, "#4ade80");
                if (statsEl) statsEl.innerHTML = `<span>COMPLETED: ${file.name}</span> <span>${data.nodes_created} NODES</span>`;
                setTimeout(() => { if (telemetryHud) telemetryHud.style.display = 'none'; }, 3000);
            } else {
                log(`❌ [Media] Errore nell'upload: ${xhr.statusText}`, "#ef4444");
            }
        };
        xhr.send(formData);
    } catch (e) {
        log(`❌ [Media] Errore critico: ${e.message}`, "#ef4444");
    }
}

// 💬 NEURAL CHAT & VOICE
function toggleVoice() {
    if (isListening) {
        recognition.stop();
        return;
    }
    
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
        log("Voice sensing not supported in this browser.", "#ef4444");
        return;
    }

    recognition = new SpeechRecognition();
    recognition.lang = 'it-IT';
    recognition.interimResults = false;

    recognition.onstart = () => {
        isListening = true;
        document.getElementById('mic-icon').innerText = '🔴';
        document.getElementById('voice-trigger').style.boxShadow = '0 0 15px #ef4444';
        log("Voice Sensing ACTIVE. Speak now...", "#a855f7");
    };

    recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        document.getElementById('chat-input').value = transcript;
        log(`Transcribed: "${transcript}"`, "#4ade80");
    };

    recognition.onend = () => {
        isListening = false;
        document.getElementById('mic-icon').innerText = '🎤';
        document.getElementById('voice-trigger').style.boxShadow = 'none';
        log("Voice Sensing SLEEP.", "#3b82f6");
    };

    recognition.start();
}

function toggleConsensusUI() {
    isConsensusMode = !isConsensusMode;
    const btn = document.getElementById('consensus-btn');
    const status = document.getElementById('consensus-status');
    if (isConsensusMode) {
        btn.style.borderColor = "#a855f7";
        btn.style.color = "#a855f7";
        btn.style.background = "rgba(168,85,247,0.15)";
        status.innerText = "ON";
        log("🏛️ CONSENSUS MODE ACTIVATED: Multi-agent strategic reasoning enabled.", "#a855f7");
    } else {
        btn.style.borderColor = "rgba(168,85,247,0.2)";
        btn.style.color = "#8b949e";
        btn.style.background = "rgba(168,85,247,0.05)";
        status.innerText = "OFF";
        log("⚡ SINGLE-AGENT MODE: Faster, direct neural response.", "#3b82f6");
    }
}

async function sendNeuralProbe() {
    const input = document.getElementById('chat-input');
    const chatBox = document.getElementById('chat-box');
    const query = input ? input.value.trim() : '';
    if (!query) return;

    // Mostra messaggio utente
    chatBox.innerHTML += `<div style="text-align:right; margin-bottom:0.8rem;"><span style="background:#3b82f6; color:white; padding:0.4rem 0.8rem; border-radius:12px; font-size:0.8rem;">${query}</span></div>`;
    input.value = '';
    chatBox.scrollTop = chatBox.scrollHeight;

    // Thinking placeholder
    const thinkId = 'think-' + Date.now();
    const thinkMsg = isConsensusMode ? "🏛️ SWARM DEBATING..." : "⚡ Searching neural mesh...";
    chatBox.innerHTML += `<div id="${thinkId}" style="margin-bottom:0.8rem;"><span class="animate-pulse" style="background:rgba(168,85,247,0.2); color:#a855f7; padding:0.4rem 0.8rem; border-radius:12px; font-size:0.8rem; font-style:italic;">${thinkMsg}</span></div>`;
    chatBox.scrollTop = chatBox.scrollHeight;

    try {
        const r = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'X-API-KEY': VAULT_KEY, 'Content-Type': 'application/json' },
            body: JSON.stringify({ query, consensus: isConsensusMode })
        });
        const d = await r.json();
        const thinking = document.getElementById(thinkId);
        if (thinking) {
            const prefix = isConsensusMode ? `<div style="font-size:0.55rem; color:#a855f7; margin-bottom:0.3rem; font-weight:800; padding: 0 0.5rem;">🏛️ NEURAL CONSENSUS VERDICT:</div>` : "";
            thinking.innerHTML = `
                ${prefix}
                <span style="background:rgba(255,255,255,0.05); color:#e2e8f0; padding:0.5rem 0.8rem; border-radius:12px; font-size:0.8rem; display:block; border-left:2px solid ${isConsensusMode ? "#a855f7" : "#3b82f6"}; white-space: pre-wrap;">${d.answer}</span>
            `;
        }
    } catch(e) {
        log('Neural Chat error: ' + e.message, '#ef4444');
    }
    chatBox.scrollTop = chatBox.scrollHeight;
}

// 🏛️ MISSION CONTROL
async function dispatchMission() {
    const mission = prompt('🏛️ NEURAL MISSION DIRECTIVE\n\nInserisci l\'obiettivo per lo Swarm:');
    if (!mission) return;
    
    const blueprintEl = document.getElementById('tip-blueprint');
    if (blueprintEl) {
        blueprintEl.innerText = "⏳ ANALYZING MISSION...";
        blueprintEl.style.color = "#a855f7";
    }

    log(`🏛️ MISSION DISPATCHED: "${mission}"`, '#a855f7');
    
    try {
        const resp = await fetch('/api/mission', {
            method: 'POST',
            headers: { 'X-API-KEY': VAULT_KEY, 'Content-Type': 'application/json' },
            body: JSON.stringify({ mission })
        });
        if (resp.ok) {
            log("🏛️ Swarm directive acknowledged. Agents processing...", "#4ade80");
            if (blueprintEl) {
                blueprintEl.innerText = "● SWARM ACTIVE: " + (mission.length > 20 ? mission.slice(0, 20) + "..." : mission);
                blueprintEl.style.color = "#3b82f6";
            }
            // Suggerimento per l'utente
            log("💡 Tip: View agents and their thoughts in the NEURAL LAB section.", "#8b949e");
        } else {
            if (blueprintEl) {
                blueprintEl.innerText = "❌ MISSION UPLINK FAILED";
                blueprintEl.style.color = "#ef4444";
            }
        }
    } catch(e) { 
        log("Mission uplink failed.", "#ef4444"); 
        if (blueprintEl) {
            blueprintEl.innerText = "❌ CONNECTION ERROR";
            blueprintEl.style.color = "#ef4444";
        }
    }
}

async function refreshAnalytics() {
    try {
        const r = await fetch('/api/analytics', { headers: { 'X-API-KEY': VAULT_KEY }});
        const d = await r.json();
        const container = document.getElementById('analytics-data-container');
        if (container) {
            container.innerHTML = `
                <div class="stat-card">
                    <h3 style="color:#a855f7;">Neural Nodes</h3>
                    <div style="font-size:1.5rem; font-weight:800; margin:0.5rem 0;">${d.node_count}</div>
                    <div style="font-size:0.6rem; color:gray;">Hit Rate: ${d.hit_rate}</div>
                </div>
                <div class="stat-card">
                    <h3 style="color:#3b82f6;">Hardware DNA</h3>
                    <div style="font-size:1rem; font-weight:800; margin:0.5rem 0; color:#4ade80;">${d.compute_mode}</div>
                    <div style="font-size:0.6rem; color:gray;">RAM: ${d.ram_usage} (${d.ram_used_gb} GB)</div>
                </div>
                <div class="stat-card">
                    <h3 style="color:#f59e0b;">Vault Storage</h3>
                    <div style="font-size:1.5rem; font-weight:800; margin:0.5rem 0;">${d.vault_size_mb} MB</div>
                    <div style="font-size:0.6rem; color:gray;">Disk Full: ${d.disk_full}</div>
                </div>
                <div class="stat-card">
                    <h3 style="color:#ec4899;">Active Models</h3>
                    <div style="font-size:0.8rem; font-weight:800; margin:0.5rem 0;">${d.active_models.length > 0 ? d.active_models.join(', ') : 'IDLE'}</div>
                    <div style="font-size:0.6rem; color:gray;">MPS Pressure: ${d.mps_pressure}</div>
                </div>
            `;
        }
    } catch(e) {}
}

// ☣️ NUCLEAR PURGE
async function nuclearPurge() {
    if (!confirm('⚠️ ATTENZIONE: Questa operazione cancellerà TUTTA la memoria del Vault. Sei sicuro?')) return;
    if (!confirm('Ultima conferma: questa azione è IRREVERSIBILE.')) return;
    
    log('☣️ Nuclear Purge iniziato...', '#ef4444');
    
    try {
        const resp = await fetch('/api/purge', {
            method: 'POST',
            headers: { 'X-API-KEY': VAULT_KEY }
        });
        
        if (resp.ok) {
            log('☣️ Purge completato: TABULA RASA eseguita.', '#4ade80');
            vaultPoints = [];
            if (cloudPoints) cloudPoints.clear();
            if (neuralLinks) neuralLinks.clear();
            if (flashingLinks) flashingLinks.clear();
            if (cy) cy.elements().remove();
            
            document.getElementById('stat-nodes').innerText = '0';
            document.getElementById('stat-synapses').innerText = '0';
            document.getElementById('stat-entities').innerText = '0';
        } else {
            log('❌ Errore durante il purge.', '#ef4444');
        }
    } catch (e) {
        log('❌ Errore di connessione durante il purge.', '#ef4444');
    }
}

window.showSection = (s) => {
    currentView = s;
    document.querySelectorAll('.view-container').forEach(v => v.style.display = 'none');
    
    const target = document.getElementById(`${s}-view`);
    if (target) {
        // v2.7.5: Preserve flex hierarchy for 3D stability
        target.style.display = (s === 'lab' || s === 'analytics') ? 'grid' : 'flex';
    }
    
    if (s === 'analytics') {
        refreshAnalytics();
    }
    
    if (s === 'nets') {
        initNets();
        setTimeout(() => { if(cy) { cy.resize(); updateNets(vaultPoints); } }, 100);
    }
    if (s === 'overview') {
        const overviewContainer = document.getElementById('memory-graph-container');
        // v2.7.6: Force Resize and Refresh to prevent 3D disappearance
        if (renderer && overviewContainer) {
            const w = overviewContainer.clientWidth;
            const h = overviewContainer.clientHeight;
            if (w > 0 && h > 0) {
                camera.aspect = w / h;
                camera.updateProjectionMatrix();
                renderer.setSize(w, h);
                // Trigger an immediate frame if animate isn't enough
                renderer.render(scene, camera);
            }
        }
    }
    
    if (s === 'lab') {
        if (!labRenderer) initLab3D();
        // Use latest agents received from SSE for immediate consistency
        if (window._latestAgents) renderLabSwarm(window._latestAgents);
    }

    // Aggiorna navigazione
    document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
    // Trova l'elemento nav corrispondente (semplificato)
};



/** [v14.3] Unified Event Initializer */

/** [v14.3] Unified Event Initializer */
function initAuraHandlers() {
    console.log("🧬 [Aura] INITIALIZING HANDLERS...");
    
    // 1. Ingestion Portal Drag & Drop
    const dropZone = document.getElementById('drop-zone');
    if (dropZone) {
        console.log("✅ Drop Zone Found.");
        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.style.background = 'rgba(168, 85, 247, 0.2)';
        });
        dropZone.addEventListener('dragleave', () => {
            dropZone.style.background = 'transparent';
        });
        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            console.log("📂 File Dropped!");
            const f = e.dataTransfer.files[0];
            if (f) uploadFile(f);
        });
    }

    // 2. Fallback Click Upload
    const fileInput = document.getElementById('file-input');
    if (fileInput) {
        fileInput.addEventListener('change', (e) => {
            const f = e.target.files[0];
            if (f) uploadFile(f);
        });
    }

    // 3. Navigation & Chat
    const chatInput = document.getElementById('chat-input');
    if (chatInput) {
        chatInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') sendNeuralProbe();
        });
    }
}

async function refreshSwarmConfig() {
    try {
        const r = await fetch('/config');
        const settings = await r.json();
        if (settings && !settings.message) {
            syncSwarmSettings(settings);
        }
    } catch(e) { console.error("Config Sync Error", e); }
}

document.addEventListener('DOMContentLoaded', async () => {
    try { init3D(); } catch(e) { console.error("3D Error", e); }
    try { initSSE(); } catch(e) { console.error("SSE Error", e); }
    try { refreshSwarmConfig(); } catch(e) { console.error("Config Error", e); }
    try { refreshModels(); } catch(e) { console.error("Models Error", e); }
    try { updateKnowledgeInventory(); } catch(e) { console.error("Inventory Error", e); }
    try { showSection('overview'); } catch(e) { console.error("UI Error", e); }
    try { initAuraHandlers(); } catch(e) { console.error("Handlers Error", e); }
    log("Aura Nexus Sovereign v2.7.5 Online (Master Mode).", "#a855f7");
});

// 🧠 AGENT SWARM & CUSTOM FACTORY (v1.5)
const DEFAULT_AGENTS = [
    { name: "Agent007 Analyst", role: "Critical Analysis", icon: "fa-brain", color: "#3b82f6", bio: "Esperto in estrazione di triple logiche e analisi della coerenza semantica." },
    { name: "Agent007 Guardian", role: "Security Audit", icon: "fa-shield-alt", color: "#10b981", bio: "Monitora le vulnerabilità e protegge l'integrità sovrana del Vault." },
    { name: "Agent007 Archivist", role: "Deep Indexing", icon: "fa-archive", color: "#a855f7", bio: "Ottimizza il pruning e la gerarchia dei nodi nel grafo HNSW." },
    { name: "Agent-Distiller", role: "Memory Gardening", icon: "fa-cut", color: "#a855f7", bio: "L'alieno di Arkanoid: distilla la conoscenza ed elimina la ridondanza." },
    { name: "JANITRON", role: "Mechanical Chomp", icon: "fa-trash-alt", color: "#facc15", bio: "Il mangiatore meccanico: pulisce i nodi obsoleti e mantiene il Vault leggero." }
];

// [v2.7.6] Agents consolidated in renderLabSwarm

function dispatchAgentAction(agentName) {
    log(`🛰️ [Dispatch] Segnale inviato a ${agentName}. In attesa di sintonizzazione...`, "#3b82f6");
    const blackboard = document.getElementById('lab-blackboard');
    if (blackboard) {
        const msg = document.createElement('div');
        msg.className = 'status-msg';
        msg.style.borderLeft = `2px solid #3b82f6`;
        msg.innerHTML = `<strong>${agentName}:</strong> Analisi della maglia neurale in corso... <span class="pulse-text">ACTIVE</span>`;
        blackboard.prepend(msg);
        
        // Simula risposta dell'agente dopo 2s
        setTimeout(() => {
            const resp = document.createElement('div');
            resp.className = 'status-msg';
            resp.style.color = '#4ade80';
            resp.innerHTML = `<strong>${agentName}:</strong> Segnale agganciato. Cluster di conoscenza ottimizzati.`;
            blackboard.prepend(resp);
        }, 2000);
    }
}

function openCustomAgentModal() {
    const modal = document.getElementById('custom-agent-modal');
    if (modal) {
        modal.style.display = 'flex';
        // Popola selettore modelli
        const sel = document.getElementById('custom-agent-model');
        const mainSel = document.getElementById('ai-model-selector');
        if (sel && mainSel) sel.innerHTML = mainSel.innerHTML;
    }
}

function closeCustomAgentModal() {
    const modal = document.getElementById('custom-agent-modal');
    if (modal) modal.style.display = 'none';
}

async function saveCustomAgent() {
    const name = document.getElementById('custom-agent-name').value;
    const model = document.getElementById('custom-agent-model').value;
    const prompt = document.getElementById('custom-agent-prompt').value;
    
    if (!name) return alert("Inserisci un nome per l'agente.");
    
    try {
        const r = await fetch('/api/intelligence/agents/custom', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-API-KEY': VAULT_KEY },
            body: JSON.stringify({ name, model, prompt, role: "Custom Agent" })
        });
        if (r.ok) {
            log(`🧬 Agente "${name}" creato con successo Factory.`, "#4ade80");
            closeCustomAgentModal();
            // SSE will update the grid automatically
        }
    } catch (e) { log("Errore creazione agente custom.", "#ef4444"); }
}

async function deleteCustomAgent(name) {
    if (!confirm(`Rimuovere l'agente ${name}?`)) return;
    try {
        const r = await fetch(`/api/intelligence/agents/custom/${name}`, {
            method: 'DELETE',
            headers: { 'X-API-KEY': VAULT_KEY }
        });
        if (r.ok) {
            // SSE will update the grid automatically
        }
    } catch (e) {}
}

window.openCustomAgentModal = openCustomAgentModal;
window.closeCustomAgentModal = closeCustomAgentModal;
window.saveCustomAgent = saveCustomAgent;
window.deleteCustomAgent = deleteCustomAgent;
window.dispatchAgentAction = dispatchAgentAction;


// 🎨 3D TEXT SPRITE ENGINE (v3.0 Sovereign)
function createTextSprite(text, color) {
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    canvas.width = 512; canvas.height = 128;
    
    ctx.font = 'Bold 36px JetBrains Mono';
    ctx.textAlign = 'center';
    ctx.fillStyle = color;
    ctx.shadowColor = 'rgba(0,0,0,1.0)';
    ctx.shadowBlur = 8;
    ctx.fillText(text, 256, 80);
    
    const texture = new THREE.CanvasTexture(canvas);
    const material = new THREE.SpriteMaterial({ map: texture, transparent: true, depthTest: false });
    const sprite = new THREE.Sprite(material);
    sprite.scale.set(100, 25, 1);
    return sprite;
}

function updateLegend(data) {
    const container = document.getElementById('nebula-legend');
    if (!container) return;
    
    // Generiamo l'HTML della legenda a scorrimento
    let html = `<div style="font-weight: 800; color: #a855f7; margin-bottom: 10px; border-bottom: 1px solid rgba(168,85,247,0.3); padding-bottom: 5px; font-size: 0.7rem;">📍 GALACTIC INDEX</div>`;
    data.forEach(item => {
        html += `
            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px; font-size: 0.65rem;">
                <div style="width: 10px; height: 10px; border-radius: 2px; background: ${item.color}; box-shadow: 0 0 5px ${item.color}"></div>
                <div style="color: #fff; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 150px;">${item.theme.toUpperCase()}</div>
            </div>
        `;
    });
    container.innerHTML = html;
}

function toggleLegend() {
    const wrapper = document.getElementById('nebula-legend-wrapper');
    if (wrapper) {
        const isHidden = wrapper.style.display === 'none';
        wrapper.style.display = isHidden ? 'block' : 'none';
        log(`📂 Legend ${isHidden ? "Visible" : "Hidden"}`, "#a855f7");
    }
}

// 📊 AI BENCHMARK HUB LOGIC (v3.0)
async function toggleBenchmarkHub() {
    const modal = document.getElementById('benchmark-modal');
    if (modal.style.display === 'flex') {
        modal.style.display = 'none';
    } else {
        modal.style.display = 'flex';
        await fetchModelBenchmarks();
    }
}

async function fetchModelBenchmarks() {
    try {
        const resp = await fetch(`/api/models/benchmarks?api_key=${VAULT_KEY}`);
        const data = await resp.json();
        const tbody = document.getElementById('benchmark-table-body');
        if (!tbody) return;

        tbody.innerHTML = '';
        if (data.benchmarks.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" style="text-align:center; padding:2rem; color:#8b949e;">Awaiting first inference for metrics...</td></tr>';
            return;
        }

        data.benchmarks.forEach(bench => {
            const row = `
                <tr style="border-bottom: 1px solid rgba(255,255,255,0.05);">
                    <td style="padding: 0.8rem; color: #fff; font-weight: 800;">${bench.model_name.toUpperCase()}</td>
                    <td style="padding: 0.8rem; color: #a855f7;">${bench.total_tasks}</td>
                    <td style="padding: 0.8rem; color: #3b82f6;">${bench.avg_latency.toFixed(0)} ms</td>
                    <td style="padding: 0.8rem; color: #10b981;">${bench.avg_tps.toFixed(2)} tok/s</td>
                    <td style="padding: 0.8rem; color: #f59e0b;">${bench.peak_tps.toFixed(2)} tok/s</td>
                </tr>
            `;
            tbody.innerHTML += row;
        });
    } catch (err) {
        console.error("Benchmark Fail:", err);
    }
}

// --------------------------------------------------------------------------------------
// FULLSCREEN CONTROLLER (v5.6)
// --------------------------------------------------------------------------------------
function toggleCycloscopeFullscreen() {
    const container = document.getElementById('memory-graph-container');
    
    if (!document.fullscreenElement) {
        if (container.requestFullscreen) {
            container.requestFullscreen().catch(err => console.log(err));
        } else if (container.webkitRequestFullscreen) {
            container.webkitRequestFullscreen();
        }
    } else {
        if (document.exitFullscreen) {
            document.exitFullscreen();
        } else if (document.webkitExitFullscreen) {
            document.webkitExitFullscreen();
        }
    }
}

document.addEventListener('fullscreenchange', () => {
    const icon = document.getElementById('fullscreen-icon');
    if (icon) {
        if (document.fullscreenElement) {
            icon.classList.remove('fa-expand');
            icon.classList.add('fa-compress');
        } else {
            icon.classList.remove('fa-compress');
            icon.classList.add('fa-expand');
        }
    }
});
async function openAuditLedger() {
    const modal = document.getElementById('audit-ledger-modal');
    const tbody = document.getElementById('audit-ledger-body');
    if (!modal || !tbody) return;

    modal.style.display = 'flex';
    tbody.innerHTML = '<tr><td colspan="6" style="padding:2rem; text-align:center; color:#a855f7;"><i class="fas fa-sync fa-spin"></i> Sincronizzazione verbali con lo Swarm...</td></tr>';

    try {
        const r = await fetch('/api/lab/audit?api_key=' + VAULT_KEY);
        const audit = await r.json();

        if (!audit || audit.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" style="padding:2rem; text-align:center; color:#8b949e;">Nessun verbale registrato. Gli agenti JA-001 e DI-007 sono in fase di calibrazione.</td></tr>';
            return;
        }

        tbody.innerHTML = audit.map(entry => `
            <tr style="border-bottom: 1px solid rgba(255,255,255,0.03); transition: 0.2s;" onmouseover="this.style.background='rgba(168,85,247,0.05)'" onmouseout="this.style.background='transparent'">
                <td style="padding: 1rem; color: #8b949e;">${entry.timestamp}</td>
                <td style="padding: 1rem;">
                    <span style="color: ${entry.agent.includes('JA') ? '#FFFF00' : '#a855f7'}; font-weight: 800;">
                        ${entry.agent}
                    </span>
                </td>
                <td style="padding: 1rem; color: #fff;">${entry.action.toUpperCase()}</td>
                <td style="padding: 1rem; color: #3b82f6;">${entry.target}</td>
                <td style="padding: 1rem; font-style: italic; color: #94a3b8; max-width: 300px; white-space: normal;">"${entry.reasoning}"</td>
                <td style="padding: 1rem; text-align: right; color: #4ade80; font-weight: 800;">${entry.savings}</td>
            </tr>
        `).reverse().join('');

    } catch (e) {
        tbody.innerHTML = `<tr><td colspan="6" style="padding:2rem; text-align:center; color:#ef4444;">Errore uplink audit: ${e.message}</td></tr>`;
    }
}
function toggleFollow(agentId) {
    const targetId = (agentId === 'janitor' || agentId === 'janitron') ? 'janitron' : 'distiller';
    const janitorIcon = document.getElementById('janitron-hud-icon');
    const distillerIcon = document.getElementById('distiller-hud-icon');

    if (trackedAgentId === targetId) {
        // Deselect
        trackedAgentId = null;
        if (controls) {
            const currentTarget = new THREE.Vector3(0, 0, 0);
            controls.target.lerp(currentTarget, 0.1);
        }
        log(`📡 Follow Mode: RELEASED`, "#8b949e");
    } else {
        // Select new
        trackedAgentId = targetId;
        log(`🎯 Tracking Lock-On: ${targetId.toUpperCase()}`, "#a855f7");
    }

    // UI Feedback
    if (janitorIcon) janitorIcon.classList.toggle('following-active', trackedAgentId === 'janitron');
    if (distillerIcon) distillerIcon.classList.toggle('following-active', trackedAgentId === 'distiller');
}

// --------------------------------------------------------------------------------------
// 🤖 SWARM CONFIGURATION & AUTO-PILOT (v11.5)
// --------------------------------------------------------------------------------------
function syncSwarmSettings(settings) {
    swarmSettings = settings; // Sync to global state
    const toggle = document.getElementById('autopilot-supervision-toggle');
    const oracleSel = document.getElementById('default-oracle-selector');
    
    if (toggle) {
        // auto_mode True means Auto-Pilot is ON (modals OFF)
        // supervision_toggle ON mean Manual mode (modals ON)
        toggle.checked = !settings.auto_mode;
    }
    
    if (oracleSel && settings.default_oracle) {
        oracleSel.value = settings.default_oracle;
    }
}

async function updateSwarmConfig(key, value) {
    console.log(`⚙️ Swarm Config Request: ${key} -> ${value}`);
    try {
        const resp = await fetch('/config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ key, value })
        });
        const d = await resp.json();
        if (d.status === 'success') {
            log(`⚙️ Swarm Config Update: ${key.toUpperCase()} SAVED`, "#4ade80");
        }
    } catch (e) {
        console.error("Config Update Fail:", e);
    }
}

function enableAutoPilotFromModal() {
    // Quando l'utente spunta "Fidati sempre" nel modale
    updateSwarmConfig('auto_mode', true);
    log("🤖 AUTO-PILOT ACTIVATED: Swarm will now resolve missions autonomously.", "#a855f7");
    
    // Mostriamo un feedback visivo immediato prima della chiusura (opzionale)
    const lbl = document.querySelector("#hold-trust-oracle-always").parentElement.nextElementSibling;
    if (lbl) lbl.innerText = "FIDUCIA ACCORDATA - AUTO-PILOT ATTIVO";
}

// --------------------------------------------------------------------------------------
// 🧬 AURA NEXUS: AGENT FACTORY & CUSTOM MANDATES (v12.0)
// --------------------------------------------------------------------------------------
function openAgentFactory() {
    const modal = document.getElementById('agent-factory-modal');
    if (modal) modal.style.display = 'flex';
}

function closeAgentFactory() {
    const modal = document.getElementById('agent-factory-modal');
    if (modal) modal.style.display = 'none';
}

async function createCustomAgent() {
    const name = document.getElementById('af-agent-name').value;
    const role = document.getElementById('af-agent-role').value;
    const prompt = document.getElementById('af-agent-prompt').value;

    if (!name || !prompt) {
        log("⚠️ [Factory] Mandato incompleto: specifica nome e istruzioni.", "#ef4444");
        return;
    }

    log(`🧬 Forging Mandate: ${name}...`, "#a855f7");
    try {
        const resp = await fetch('/api/agents/spawn', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, role, prompt, api_key: VAULT_KEY })
        });
        const d = await resp.json();
        if (d.status === 'success') {
            log(`✅ Agent Forge Success: ${name} is now ONLINE.`, "#4ade80");
            closeAgentFactory();
            // Reset form
            document.getElementById('af-agent-name').value = '';
            document.getElementById('af-agent-prompt').value = '';
        } else {
            log(`❌ Forge Error: ${d.message}`, "#ef4444");
        }
    } catch (e) {
        log(`❌ Uplink Error: ${e.message}`, "#ef4444");
    }
}

// Global Exports
window.toggleMissionControl = function() {
    const mc = document.getElementById('right-mission-control');
    const icon = document.getElementById('mc-toggle-icon');
    
    if (mc) {
        mc.classList.toggle('collapsed');
        const isCollapsed = mc.classList.contains('collapsed');
        
        if (icon) {
            icon.className = isCollapsed ? 'fas fa-chevron-left' : 'fas fa-chevron-right';
        }
        
        log(`📊 Mission Control ${isCollapsed ? 'STANDBY' : 'ACTIVE'}`, isCollapsed ? "#8b949e" : "#a855f7");
    }
};

window.toggleFollow = toggleFollow;
window.openAuditLedger = openAuditLedger;
window.closeAuditLedger = closeAuditLedger;
window.updateSwarmConfig = updateSwarmConfig;
window.enableAutoPilotFromModal = enableAutoPilotFromModal;
window.openAgentFactory = openAgentFactory;
window.closeAgentFactory = closeAgentFactory;
window.createCustomAgent = createCustomAgent;
// 🧠 [v3.0.0] SWARM MODEL HUB CONTROLLER
async function loadSwarmSettings() {
    try {
        const resp = await fetch('/settings/swarm');
        const data = await resp.json();
        const settings = data.settings;
        const available = data.available_models || [];

        // Populate all swarm selects
        const selects = ['route-audit', 'route-extraction', 'route-crossref', 'route-synthesis'];
        selects.forEach(id => {
            const select = document.getElementById(id);
            if (!select) return;
            select.innerHTML = '';
            
            // Add preferred model from settings if it exists
            const task = id.replace('route-', '');
            const current = settings.routing[task === 'crossref' ? 'foraging_analysis' : task] || 'llama3.2';

            available.forEach(m => {
                const opt = document.createElement('option');
                opt.value = m;
                opt.textContent = m;
                if (m === current) opt.selected = true;
                select.appendChild(opt);
            });
        });

        log("🧠 Model Hub: Settings Synced.", "#a855f7");
    } catch (e) {
        console.error("Failed to load swarm settings", e);
    }
}

async function saveSwarmRouting() {
    const payload = {
        routing: {
            audit: document.getElementById('route-audit').value,
            entity_extraction: document.getElementById('route-extraction').value,
            foraging_analysis: document.getElementById('route-crossref').value,
            synthesis: document.getElementById('route-synthesis').value
        }
    };

    try {
        const resp = await fetch('/settings/swarm', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        if (resp.ok) {
            log("✅ Swarm Configuration Saved & Propagated.", "#10b981");
            alert("Configurazione salvata con successo. Gli agenti utilizzeranno i nuovi parametri al prossimo compito.");
        }
    } catch (e) {
        log("❌ Failed to save swarm configuration.", "#ef4444");
    }
}

// 🧩 SETTINGS NAVIGATION (v3.5)
window.switchSettingsTab = (tab) => {
    document.querySelectorAll('.settings-tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.settings-content').forEach(c => c.style.display = 'none');
    
    const targetTab = document.querySelector(`.settings-tab[onclick*="${tab}"]`);
    if (targetTab) targetTab.classList.add('active');
    
    const targetContent = document.getElementById(`tab-${tab}`);
    if (targetContent) targetContent.style.display = 'block';
    
    if (tab === 'hub') refreshModels();
};

window.refreshModels = async () => {
    const tbody = document.getElementById('model-hub-table-body');
    if (!tbody) return;
    
    try {
        const r = await fetch('/api/models/status', { headers: { 'X-API-KEY': VAULT_KEY }});
        const data = await r.json();
        
        if (!data.models || data.models.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" style="text-align:center; padding:2rem; color:#8b949e;">Nessun modello rilevato. Assicurati che Ollama sia attivo.</td></tr>';
            return;
        }

        tbody.innerHTML = data.models.map(m => {
            const isInstalled = m.status === 'installed' || m.size > 0;
            const sizeGB = m.size ? (m.size / (1024*1024*1024)).toFixed(2) + " GB" : "N/D";
            
            // Hardcoded synergy logic for visual fidelity based on archetype
            let synergy = "Standard";
            if (m.name.includes("deepseek")) synergy = "High (Logic)";
            if (m.name.includes("llama")) synergy = "Extreme (General)";
            if (m.name.includes("mistral")) synergy = "Optimal (RAG)";

            return `
                <tr>
                    <td style="font-family:'JetBrains Mono'; font-weight:800;">${m.name}</td>
                    <td>
                        <span style="color: ${isInstalled ? '#10b981' : '#facc15'}; font-size: 0.6rem; font-weight:900;">
                            <i class="fas ${isInstalled ? 'fa-check-circle' : 'fa-cloud-download-alt'}"></i> 
                            ${isInstalled ? 'ATTIVO' : 'DISPONIBILE'}
                        </span>
                    </td>
                    <td><span style="color:#8b949e;">${sizeGB}</span></td>
                    <td><span class="synergy-badge">${synergy}</span></td>
                    <td>
                        <div style="display:flex; gap:0.5rem;">
                            ${isInstalled ? 
                                `<button onclick="deleteModel('${m.name}')" style="background:rgba(239,68,68,0.1); border:1px solid #ef4444; color:#ef4444; padding:0.3rem 0.6rem; border-radius:4px; font-size:0.5rem; cursor:pointer;"><i class="fas fa-trash"></i> DELETE</button>` :
                                `<button onclick="installModel('${m.name}')" style="background:rgba(59,130,246,0.1); border:1px solid #3b82f6; color:#3b82f6; padding:0.3rem 0.6rem; border-radius:4px; font-size:0.5rem; cursor:pointer;"><i class="fas fa-download"></i> INSTALL</button>`
                            }
                        </div>
                    </td>
                </tr>
            `;
        }).join('');
    } catch (e) {
        tbody.innerHTML = '<tr><td colspan="5" style="text-align:center; padding:2rem; color:#ef4444;">Errore nel recupero del catalogo.</td></tr>';
    }
};

window.deleteModel = async (name) => {
    if (!confirm(`Sei sicuro di voler eliminare definitivamente il modello ${name}?`)) return;
    try {
        const r = await fetch(`/api/models/delete/${encodeURIComponent(name)}`, { 
            method: 'DELETE',
            headers: { 'X-API-KEY': VAULT_KEY }
        });
        if (r.ok) {
            log(`🗑️ Modello ${name} eliminato.`, "#ef4444");
            refreshModels();
        }
    } catch (e) { log("Errore durante l'eliminazione del modello.", "#ef4444"); }
};

window.installModel = async (name) => {
    log(`📥 Avvio installazione modello ${name}...`, "#3b82f6");
    try {
        const r = await fetch('/api/models/install', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-API-KEY': VAULT_KEY },
            body: JSON.stringify({ model_name: name })
        });
        if (r.ok) {
            log(`⚙️ Segnale di installazione inviato per ${name}. Monitora il sistema.`, "#a855f7");
            refreshModels();
        }
    } catch (e) { log("Errore durante l'avvio dell'installazione.", "#ef4444"); }
};

// [Final Override Sync]
const originalShowSection = window.showSection;
window.showSection = function(id) {
    if (id === 'settings') {
        loadSwarmSettings();
        switchSettingsTab('swarm'); // Reset to default tab
    }
    if (typeof originalShowSection === 'function') originalShowSection(id);
};
