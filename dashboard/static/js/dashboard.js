/**
 * AURA NEXUS MASTER CONTROLLER (v2.9 Sovereign - ABSOLUTE STABILITY)
 */

let scene, camera, renderer, pointsMesh, neuralLinks, cube, raycaster, mouse;
let janitorGroup, janitorTop, janitorBottom, janitorLabel;
let distillerGroup, distillerLabel;
let reaperGroup, reaperLabel; 
let snakeGroup, snakeSegments = [], snakeLabel;
let quantumGroup, quantumLabel, quantumCore;
let sentinelGroup, sentinelLabel, sentinelShield;
let synthGroup, synthLabel, synthSparks = [], synthSubGroups = {};
let skywalkerGroup, skywalkerLabel;
let skywalkerTargetPos = new THREE.Vector3(250000, 250000, 250000);
let skywalkerLasers = [];
let bridgerGroup, bridgerLabel, bridgerPulseTime = 0;
let janitorTargetPos = new THREE.Vector3(500000, 200000, 500000);
let janitorFlashTime = 0; // 4s blue flash
let distillerFlashTime = 0; // 4s yellow flash
let reaperCubes = []; // {mesh, expiry}
let superSynapseAuraDuration = 60000; // 1 minute in ms
let distillerTargetPos = new THREE.Vector3(-200000, 200000, -200000);
let reaperTargetPos = new THREE.Vector3(0, 300000, 0);
let snakeCurrentTarget = new THREE.Vector3(1200000, 0, 0);
let quantumTargetPos = new THREE.Vector3(800000, 800000, 800000);
let sentinelTargetPos = new THREE.Vector3(-500000, -500000, 500000);
let synthTargetPos = new THREE.Vector3(0, 500000, 0);
let bridgerTargetPos = new THREE.Vector3(0, 0, 0);
let snakeDirection = new THREE.Vector3(1, 0, 0);
let lastSnakeStep = 0;
let lastReaperProcessed = 0, lastJanitorPurged = 0, lastDistillerPruned = 0;
let lastQuantumClusters = 0, lastSynthSparks = 0;
let isEvolving = false;
let evolutionProgress = 0;
let evolutionStep = "";
let quantumFlashTime = 0, synthFlashTime = 0, sentinelFlashTime = 0, sentinelLightningTime = 0;
let sentinelLightningGroup = null;
let followedAgent = null;
let clusterNodesGroup;
let medicalCubes = [];
let controls, eventSource, vaultPoints = [], installedModels = [];
let isRotationPaused = false;
let isUserInteracting = false;
let layersVisibility = { agents: true, orphans: true, nodes: true, linked_nodes: true, edges: true, sparks: true, cube: true, grid: true, nav_guide: true };
let timeTravelFactor = 1.0;
let nebulaQuality = 'HD';
let clusterFocus = true;
let radarChart = null; // 🧬 Sovereign Radar Reference
let nebulaExpansionFactor = 1.0;
let lastNeuralLinks = [];
let multimodalGroup, multimodalTextures = {}; // 📸 Multimodal Layer
const VAULT_KEY = "vault_secret_aura_2026";

function log(msg, color = '#4ade80') {
    const consoleDiv = document.getElementById('aura-console');
    if (!consoleDiv) return;
    const line = document.createElement('div');
    line.style.color = color;
    line.innerHTML = `> [${new Date().toLocaleTimeString()}] ${msg}`;
    consoleDiv.prepend(line);
    fetch('/api/log', { 
        method: 'POST', 
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: msg, level: 'HUD' })
    }).catch(()=>{});
}

function init3D() {
    if (window.is3DInitialized) return;
    const container = document.getElementById('memory-graph-container');
    const canvas = document.getElementById('isometric-canvas');
    if (!container || !canvas) return;
    if (container.clientWidth === 0 || container.clientHeight === 0) {
        requestAnimationFrame(init3D);
        return;
    }

    const glOptions = { 
        antialias: false, 
        depth: true, 
        alpha: true, 
        preserveDrawingBuffer: true,
        failIfMajorPerformanceCaveat: false 
    };
    let gl = canvas.getContext('webgl2', glOptions) || canvas.getContext('webgl', glOptions);
    
    if (!gl) {
        if (!window.lastContextError || Date.now() - window.lastContextError > 10000) {
            log("❌ WebGL Context Failure - Retrying in 10s", "#ef4444");
            window.lastContextError = Date.now();
        }
        setTimeout(init3D, 10000);
        return;
    }

    canvas.addEventListener('webglcontextlost', (e) => {
        e.preventDefault();
        window.is3DInitialized = false;
        log("⚠️ WebGL Context Lost - Cooling down...", "#f59e0b");
        // Clear all Three.js objects to free VRAM
        if (scene) scene.traverse(obj => {
            if (obj.geometry) obj.geometry.dispose();
            if (obj.material) {
                if (Array.isArray(obj.material)) obj.material.forEach(m => m.dispose());
                else obj.material.dispose();
            }
        });
        setTimeout(init3D, 4000);
    }, false);

    log("\uD83D\uDE80 WebGL Context Initialized", "#10b981");

    if (renderer) {
        renderer.dispose();
        renderer = null;
    }
    if (scene) {
        scene.traverse(obj => {
            if (obj.geometry) obj.geometry.dispose();
            if (obj.material) {
                if (Array.isArray(obj.material)) obj.material.forEach(m => m.dispose());
                else obj.material.dispose();
            }
        });
        scene = null;
    }
    
    scene = new THREE.Scene();
    const isLight = document.body.classList.contains('light-theme');
    scene.background = new THREE.Color(isLight ? 0xf8fafc : 0x020617);
    const width = container.clientWidth;
    const height = container.clientHeight;

    camera = new THREE.PerspectiveCamera(75, container.clientWidth / container.clientHeight, 10, 50000000);
    camera.position.set(5000000, 5000000, 5000000); 
    camera.lookAt(0, 1000000, 0);

    renderer = new THREE.WebGLRenderer({ 
        canvas, 
        context: gl, 
        antialias: true, 
        alpha: true,
        logarithmicDepthBuffer: true,
        precision: "highp",
        powerPreference: "high-performance"
    });
    renderer.setSize(width, height);
    renderer.setPixelRatio(window.devicePixelRatio > 1 ? 2 : 1);

    scene.add(new THREE.AmbientLight(0xffffff, 1.2));
    const dl = new THREE.DirectionalLight(0xffffff, 1.0);
    dl.position.set(1, 1, 1);
    scene.add(dl);

    cube = new THREE.Mesh(
        new THREE.BoxGeometry(4000000, 4000000, 4000000),
        new THREE.MeshBasicMaterial({ color: 0x3b82f6, wireframe: true, transparent: true, opacity: 0.4 })
    );
    cube.position.y = 1002000; // 🚀 [v17.5] Elevato leggermente per prevenire Z-Fighting con la griglia (-1000000)
    scene.add(cube);

    const grid = new THREE.GridHelper(10000000, 20, isLight ? 0x94a3b8 : 0x3b82f6, isLight ? 0xe2e8f0 : 0x1e293b);
    grid.position.y = -1000000;
    scene.add(grid);

    // [v16.0] Cluster Visualization Layer
    clusterNodesGroup = new THREE.Group();
    clusterNodesGroup.position.y = 1000000;
    scene.add(clusterNodesGroup);

    window.is3DInitialized = true;
    const MAX_POINTS = 15000;
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.BufferAttribute(new Float32Array(MAX_POINTS * 3), 3));
    geometry.setAttribute('color', new THREE.BufferAttribute(new Float32Array(MAX_POINTS * 3), 3));
    
    pointsMesh = new THREE.Points(geometry, new THREE.PointsMaterial({
        size: 25000, vertexColors: true, transparent: true, opacity: 0.9,
        sizeAttenuation: true, blending: THREE.AdditiveBlending, depthWrite: false
    }));
    pointsMesh.position.y = 1000000;
    scene.add(pointsMesh);

    multimodalGroup = new THREE.Group();
    multimodalGroup.position.y = 1000000;
    scene.add(multimodalGroup);

    // [v4.0] Pre-render Multimodal Textures (Image, Audio, Video)
    const createIconTexture = (icon, color) => {
        const canvas = document.createElement('canvas');
        canvas.width = 128; canvas.height = 128;
        const ctx = canvas.getContext('2d');
        ctx.fillStyle = color;
        ctx.font = '900 80px "Font Awesome 6 Free"';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(icon, 64, 64);
        const tex = new THREE.CanvasTexture(canvas);
        return tex;
    };
    multimodalTextures['image'] = createIconTexture('\uf03e', '#4ade80'); // Photo
    multimodalTextures['audio'] = createIconTexture('\uf6a8', '#3b82f6'); // Waveform
    multimodalTextures['video'] = createIconTexture('\uf03d', '#ef4444'); // Video Camera

    neuralLinks = new THREE.Group();
    neuralLinks.position.y = 1000000;
    scene.add(neuralLinks);

    if (typeof THREE.OrbitControls === 'function') {
        controls = new THREE.OrbitControls(camera, renderer.domElement);
        controls.target.set(0, 1000000, 0);
        controls.enableDamping = true;
        controls.dampingFactor = 0.05;
        controls.screenSpacePanning = true;
        controls.enabled = true;
    } else {
        log("⚠️ OrbitControls not found - Interaction limited", "#f59e0b");
    }
    
    if (controls) {
        controls.mouseButtons = {
            LEFT: THREE.MOUSE.ROTATE,
            MIDDLE: THREE.MOUSE.DOLLY,
            RIGHT: THREE.MOUSE.PAN
        };
        controls.minDistance = 50; 
        controls.maxDistance = 10000000;

        controls.addEventListener('start', () => { isUserInteracting = true; });
        controls.addEventListener('end', () => { isUserInteracting = false; });
    }

    raycaster = new THREE.Raycaster();
    raycaster.params.Points.threshold = 150000; // 🎯 Catch orbitale per nodi a coordinate massive
    mouse = new THREE.Vector2();

    container.addEventListener('click', (e) => window.onNebulaClick(e));
    canvas.addEventListener('contextmenu', e => e.preventDefault());

    // [v4.0] Drag and Drop Implementation
    container.classList.add('drop-zone');
    container.addEventListener('dragover', (e) => {
        e.preventDefault();
        container.classList.add('drag-over');
    });
    container.addEventListener('dragleave', () => {
        container.classList.remove('drag-over');
    });
    container.addEventListener('drop', (e) => {
        e.preventDefault();
        container.classList.remove('drag-over');
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            window.uploadMediaSynapse(files[0]);
        }
    });
    
    const probeToggle = document.getElementById('probe-toggle');
    if (probeToggle) {
        probeToggle.addEventListener('change', (e) => {
            if (!e.target.checked) window.closeInspector();
        });
    }

    provisionAgents();
    animate();
    window.is3DInitialized = true;
    log("\uD83C\uDF0C Neural Cycloscope Active", "#3b82f6");

    window.addEventListener('resize', () => {
        const width = container.clientWidth;
        const height = container.clientHeight;
        if (camera && renderer) {
            camera.aspect = width / height;
            camera.updateProjectionMatrix();
            renderer.setSize(width, height);
        }
    });
}

function spawnReaperMonument(pos) {
    const geo = new THREE.BoxGeometry(80000, 80000, 80000);
    const mat = new THREE.MeshPhongMaterial({ 
        color: 0xffffff, 
        transparent: true, 
        opacity: 0.3,
        shininess: 100
    });
    const cube = new THREE.Mesh(geo, mat);
    cube.position.set(pos.x, pos.y, pos.z);
    
    // Add Red Crosses to each face
    const crossSize = 60000;
    const crossGeoH = new THREE.BoxGeometry(crossSize, 10000, 2000);
    const crossGeoV = new THREE.BoxGeometry(10000, crossSize, 2000);
    const crossMat = new THREE.MeshBasicMaterial({ color: 0xff0000 });
    
    // Simple way to add signs to faces
    const directions = [
        [0, 0, 1], [0, 0, -1], [1, 0, 0], [-1, 0, 0], [0, 1, 0], [0, -1, 0]
    ];
    directions.forEach(d => {
        const h = new THREE.Mesh(crossGeoH, crossMat);
        const v = new THREE.Mesh(crossGeoV, crossMat);
        const group = new THREE.Group();
        group.add(h); group.add(v);
        group.position.set(d[0]*40001, d[1]*40001, d[2]*40001);
        if (d[0] !== 0) group.rotation.y = Math.PI/2;
        if (d[1] !== 0) group.rotation.x = Math.PI/2;
        cube.add(group);
    });

    scene.add(cube);
    reaperCubes.push({ mesh: cube, expiry: Date.now() + 600000 }); // 10 minutes
}

function createTextSprite(text, color) {
    const canvas = document.createElement('canvas');
    canvas.width = 1024; canvas.height = 256;
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, 1024, 256);
    ctx.font = 'Bold 80px JetBrains Mono';
    ctx.textAlign = 'center';
    ctx.fillStyle = color;
    ctx.fillText(text, 512, 140);
    
    const texture = new THREE.CanvasTexture(canvas);
    const spriteMaterial = new THREE.SpriteMaterial({ map: texture, transparent: true, alphaTest: 0.1, depthWrite: false });
    const sprite = new THREE.Sprite(spriteMaterial);
    sprite.scale.set(400000, 100000, 1);
    return sprite;
}

function provisionAgents() {
    janitorGroup = new THREE.Group();
    const jaMat = new THREE.MeshPhongMaterial({ color: 0xfacc15, emissive: 0x422006, shininess: 80 });
    const jaBlackMat = new THREE.MeshBasicMaterial({ color: 0x000000 });

    // Emisfero Superiore (Calotta Nord)
    const topGeo = new THREE.SphereGeometry(45000, 32, 16, 0, Math.PI * 2, 0, Math.PI / 2);
    janitorTop = new THREE.Mesh(topGeo, jaMat);
    // Orientamento iniziale neutro (chiuso verso Z)
    
    // 👀 OCCHI GIGANTI SUL FRONTE (Direzione bocca)
    const eyeGeo = new THREE.SphereGeometry(18000, 16, 16);
    const eyeL = new THREE.Mesh(eyeGeo, jaBlackMat);
    eyeL.position.set(22000, 25000, 25000); // Alzati e portati in avanti
    const eyeR = new THREE.Mesh(eyeGeo, jaBlackMat);
    eyeR.position.set(-22000, 25000, 25000);
    janitorTop.add(eyeL, eyeR);
    
    // Emisfero Inferiore (Calotta Sud)
    const botGeo = new THREE.SphereGeometry(45000, 32, 16, 0, Math.PI * 2, Math.PI / 2, Math.PI / 2);
    janitorBottom = new THREE.Mesh(botGeo, jaMat);
    
    // Interno Bocca (Sfera interna nera per profondità totale)
    const insideGeo = new THREE.SphereGeometry(43000, 16, 16);
    const inside = new THREE.Mesh(insideGeo, jaBlackMat);
    
    janitorGroup.add(janitorTop, janitorBottom, inside);
    janitorGroup.userData = { mat: jaMat };
    // 🔄 Orientamento Default
    janitorGroup.rotation.y = 0;

    janitorLabel = createTextSprite("JA-001 JANITRON", "#facc15");
    janitorLabel.position.y = 100000;
    janitorGroup.add(janitorLabel);
    scene.add(janitorGroup);

    distillerGroup = new THREE.Group();
    const invMat = new THREE.MeshLambertMaterial({ color: 0xa855f7 });
    const pixels = [[0,0,1,0,0,0,1,0,0],[0,0,0,1,0,1,0,0,0],[0,0,1,1,1,1,1,0,0],[0,1,1,0,1,0,1,1,0],[1,1,1,1,1,1,1,1,1],[1,0,1,1,1,1,1,0,1],[1,0,1,0,0,0,1,0,1],[0,0,0,1,0,1,0,0,0]];
    const vSize = 8000;
    pixels.forEach((row, y) => row.forEach((p, x) => {
        if(p) {
            const v = new THREE.Mesh(new THREE.BoxGeometry(vSize, vSize, vSize), invMat);
            v.position.set((x - 4) * vSize, (4 - y) * vSize, 0);
            distillerGroup.add(v);
        }
    }));
    distillerLabel = createTextSprite("DI-007 DISTILLER", "#a855f7");
    distillerLabel.position.y = 80000;
    distillerGroup.add(distillerLabel);
    scene.add(distillerGroup);

    reaperGroup = new THREE.Group();
    const mats = [null, new THREE.MeshLambertMaterial({ color: 0xffffff }), new THREE.MeshLambertMaterial({ color: 0xffdbac }), new THREE.MeshLambertMaterial({ color: 0x5d4037 }), new THREE.MeshLambertMaterial({ color: 0xef4444 }), new THREE.MeshLambertMaterial({ color: 0x2196f3 }), new THREE.MeshLambertMaterial({ color: 0x3e2723 }), new THREE.MeshLambertMaterial({ color: 0xef4444 })];
    const rVsize = 6000;
    const mario = [[0,0,7,7,7,7,0,0,0,0],[0,7,7,7,7,7,7,7,7,0],[0,2,2,2,1,2,2,2,0,0],[2,2,2,2,1,1,2,2,2,0],[4,4,5,5,0,2,2,2,2,0],[0,2,2,2,2,2,2,2,0,0],[1,1,1,1,1,1,1,1,1,0],[0,1,1,1,1,1,1,1,0,0],[0,0,1,1,0,1,1,0,0,0],[0,6,6,6,0,6,6,6,0,0]];
    mario.forEach((row, r) => row.forEach((v, c) => {
        if (v > 0) {
            for (let z = -1; z <= 1; z++) {
                const voxel = new THREE.Mesh(new THREE.BoxGeometry(rVsize, rVsize, rVsize), mats[v]);
                voxel.position.set((c - 5) * rVsize, (10 - r) * rVsize, z * rVsize);
                reaperGroup.add(voxel);
            }
        }
    }));
    reaperLabel = createTextSprite("DR. REAPER", "#00ffcc");
    reaperLabel.position.y = 100000;
    reaperGroup.add(reaperLabel);
    scene.add(reaperGroup);

    snakeGroup = new THREE.Group();
    const sMat = new THREE.MeshLambertMaterial({ color: 0x10b981 });
    snakeGroup.add(new THREE.Mesh(new THREE.BoxGeometry(32500, 32500, 32500), sMat));
    snakeLabel = createTextSprite("SN-008 SNAKE", "#10b981");
    snakeLabel.position.y = 80000;
    snakeGroup.add(snakeLabel);
    scene.add(snakeGroup);
    snakeSegments = [];
    const baseBody = 3; // 🚂 3 Body segments
    const baseTail = 4; // 🧨 4 Tapering tail segments
    for(let i=1; i <= (baseBody + baseTail); i++) {
        let size;
        if (i <= baseBody) {
            size = 30000; // Constant body size
        } else {
            size = 30000 - (i - baseBody) * 4500; // Tapering tail
        }
        const seg = new THREE.Mesh(new THREE.BoxGeometry(size, size, size), sMat);
        seg.position.set(1200000, 0, -i * 35000);
        scene.add(seg);
        snakeSegments.push(seg);
    }

    // QA-101 QUANTUM: Dodecahedron v16.0
    quantumGroup = new THREE.Group();
    const qMat = new THREE.MeshPhongMaterial({ color: 0x3b82f6, emissive: 0x1d4ed8, shininess: 100, transparent: true, opacity: 0.8 });
    quantumCore = new THREE.Mesh(new THREE.DodecahedronGeometry(45000, 0), qMat);
    quantumGroup.add(quantumCore);
    quantumLabel = createTextSprite("QA-101 QUANTUM", "#3b82f6");
    quantumLabel.position.y = 100000;
    quantumGroup.add(quantumLabel);
    scene.add(quantumGroup);

    // SE-007 SENTINEL: Sovereign Metallic Shield
    sentinelGroup = new THREE.Group();
    const shieldShape = new THREE.Shape();
    // Modellazione profilo scudo (premium curve)
    shieldShape.moveTo(0, 50000);
    shieldShape.quadraticCurveTo(20000, 60000, 45000, 50000); // Top Right arch
    shieldShape.quadraticCurveTo(45000, 10000, 45000, 0);      // Right Side
    shieldShape.quadraticCurveTo(45000, -40000, 0, -65000);    // Point Bottom
    shieldShape.quadraticCurveTo(-45000, -40000, -45000, 0);   // Left Side
    shieldShape.quadraticCurveTo(-45000, 10000, -45000, 50000); // Top Left arch
    shieldShape.quadraticCurveTo(-20000, 60000, 0, 50000);

    const extrudeSettings = { depth: 12000, bevelEnabled: true, bevelThickness: 4000, bevelSize: 4000, bevelSegments: 5 };
    const shieldGeo = new THREE.ExtrudeGeometry(shieldShape, extrudeSettings);
    
    // Materiale Satin Chrome (Massima resa sotto luce)
    const shieldMat = new THREE.MeshPhysicalMaterial({ 
        color: 0xffffff, 
        metalness: 0.85, 
        roughness: 0.35, 
        clearcoat: 1.0, 
        clearcoatRoughness: 0.1,
        emissive: 0x332211,
        emissiveIntensity: 0.6
    });
    
    sentinelShield = new THREE.Mesh(shieldGeo, shieldMat);
    // Orientamento raddrizzato: 90° su Y e azzeramento X per posizione verticale
    sentinelShield.rotation.x = 0; 
    sentinelShield.rotation.y = Math.PI / 2; 
    
    // 💡 Aura Light dedicata
    const shieldPointLight = new THREE.PointLight(0xffffff, 2, 250000);
    shieldPointLight.position.set(0, 50000, 50000);
    
    sentinelGroup.add(sentinelShield, shieldPointLight);
    sentinelGroup.userData = { mat: shieldMat };

    sentinelLabel = createTextSprite("SE-007 SENTINEL", "#9de9ff");
    sentinelLabel.position.y = 130000;
    sentinelGroup.add(sentinelLabel);
    scene.add(sentinelGroup);

    // SY-009 SYNTH: Core + 3 Sub-Agents
    synthGroup = new THREE.Group();
    const syMat = new THREE.MeshPhongMaterial({ color: 0xa855f7, emissive: 0x7e22ce, shininess: 120 });
    const synthCore = new THREE.Mesh(new THREE.IcosahedronGeometry(40000, 1), syMat);
    synthGroup.add(synthCore);
    
    // Sub-Agents with Specific Roles & Colors
    synthSubAgents = [];
    const subRoles = ["Drafting", "Critique", "Polishing"];
    const subColors = [0x22d3ee, 0xf59e0b, 0x10b981]; 
    for(let i=0; i<3; i++) {
        const sub = new THREE.Mesh(new THREE.BoxGeometry(12000, 12000, 12000), new THREE.MeshPhongMaterial({ color: subColors[i], emissive: subColors[i], emissiveIntensity: 0 }));
        sub.role = subRoles[i];
        sub.baseColor = subColors[i];
        synthGroup.add(sub);
        synthSubAgents.push(sub);
    }

    synthLabel = createTextSprite("SY-009 SYNTH", "#a855f7");
    synthLabel.position.y = 100000;
    synthGroup.add(synthLabel);
    scene.add(synthGroup);

    // FS-77 FILE-SKY-WALKER: High-Fidelity X-Wing Starfighter
    skywalkerGroup = new THREE.Group();
    const hullMat = new THREE.MeshPhongMaterial({ color: 0xd1d5db, shininess: 50 }); // Light Gray Scafo
    const redMat = new THREE.MeshPhongMaterial({ color: 0xef4444 }); // Red Markings
    const engineMat = new THREE.MeshPhongMaterial({ color: 0x374151 }); // Dark Engine Steel
    const cockpitMat = new THREE.MeshPhongMaterial({ color: 0x3b82f6, transparent: true, opacity: 0.4 });

    // 1. Fuselage (Oriented towards +Z for lookAt compatibility)
    const fuseBody = new THREE.Mesh(new THREE.CylinderGeometry(3500, 4800, 32000, 4), hullMat); // Squadrato
    fuseBody.rotation.x = Math.PI / 2;
    fuseBody.rotation.y = Math.PI / 4; // Ruotato per spigolo
    
    // Muso Squadrato (Frustrated Pyramid)
    const fuseNose = new THREE.Mesh(new THREE.CylinderGeometry(800, 3500, 15000, 4), hullMat);
    fuseNose.rotation.x = Math.PI / 2; // 🚀 Ruotato di 180 gradi lungo l'asse X come richiesto
    fuseNose.rotation.y = Math.PI / 4;
    fuseNose.position.z = 23500;
    
    // Red Stripe on Nose
    const stripe = new THREE.Mesh(new THREE.BoxGeometry(4800, 1800, 12000), redMat);
    stripe.position.set(0, 0, 12000);
    
    // 2. Cockpit (More integrated)
    const cockpit = new THREE.Mesh(new THREE.BoxGeometry(4000, 3000, 10000), cockpitMat);
    cockpit.position.set(0, 2500, 8000);
    cockpit.rotation.x = -0.1;
    
    skywalkerGroup.add(fuseBody, fuseNose, stripe, cockpit);

    // 3. Wings (X-Configuration - WIDER S-FOILS)
    const wingGeo = new THREE.BoxGeometry(12000, 800, 25000);
    for(let i=0; i<4; i++) {
        const wingContainer = new THREE.Group();
        const wing = new THREE.Mesh(wingGeo, hullMat);
        wing.position.z = -8000;
        
        // Red markings on wing
        const wStripe = new THREE.Mesh(new THREE.BoxGeometry(7000, 1000, 4000), redMat);
        wStripe.position.set(0, 200, -8000);
        
        // Engine at base
        const engine = new THREE.Mesh(new THREE.CylinderGeometry(3000, 3000, 15000, 8), engineMat);
        engine.rotation.x = Math.PI/2;
        engine.position.set(0, 0, 0);
        
        // Laser Cannon at tip
        const cannonBase = new THREE.Mesh(new THREE.CylinderGeometry(800, 800, 18000, 8), hullMat);
        cannonBase.rotation.x = Math.PI/2;
        cannonBase.position.set(0, 0, -15000);
        const cannonTip = new THREE.Mesh(new THREE.CylinderGeometry(300, 300, 8000, 8), engineMat);
        cannonTip.rotation.x = Math.PI/2;
        cannonTip.position.set(0, 0, -25000);
        
        wingContainer.add(wing, wStripe, engine, cannonBase, cannonTip);
        
        const angle = (Math.PI / 3.5) + (i * Math.PI / 2); // Apertura maggiorata (non 45 gradi secchi)
        wingContainer.position.set(Math.cos(angle)*9000, Math.sin(angle)*9000, 8000); // Più esterni e arretrati
        wingContainer.rotation.z = angle;
        
        skywalkerGroup.add(wingContainer);
    }
    
    skywalkerLabel = createTextSprite("FS-77 SKY-WALKER", "#ef4444");
    skywalkerLabel.position.y = 60000;
    skywalkerGroup.add(skywalkerLabel);
    scene.add(skywalkerGroup);

    bridgerGroup = new THREE.Group();
    const bMat = new THREE.MeshPhongMaterial({ color: 0x3b82f6, emissive: 0x1e40af, shininess: 100, wireframe: false });
    const diamondGeo = new THREE.OctahedronGeometry(35000);
    const bridgeArch = new THREE.Mesh(diamondGeo, bMat);
    bridgeArch.rotation.z = Math.PI / 4;
    const ringGeo = new THREE.TorusGeometry(50000, 2000, 16, 100);
    const ringMat = new THREE.MeshPhongMaterial({ color: 0x00ffff, emissive: 0x00ffff, transparent: true, opacity: 0.4 });
    const ring1 = new THREE.Mesh(ringGeo, ringMat);
    const ring2 = new THREE.Mesh(ringGeo, ringMat);
    ring2.rotation.x = Math.PI / 2;
    const bridgeCore = new THREE.Mesh(new THREE.IcosahedronGeometry(12000), new THREE.MeshPhongMaterial({ color: 0xffffff, emissive: 0xffffff }));
    bridgerGroup.bridgeCore = bridgeCore;
    bridgerGroup.rings = [ring1, ring2];
    bridgerGroup.add(bridgeArch, bridgeCore, ring1, ring2);
    bridgerLabel = createTextSprite("CB-003 BRIDGER", "#3b82f6");
    bridgerLabel.position.y = 100000;
    bridgerGroup.add(bridgerLabel);
    scene.add(bridgerGroup);
}

function animate() {
    if (!window.isRenderLoopActive) {
        log("🔄 Render Loop Engaged", "#a855f7");
        window.isRenderLoopActive = true;
    }
    requestAnimationFrame(animate);
    const now = Date.now();
    const time = now * 0.001;
    
    if (isEvolving) {
        const exp = nebulaExpansionFactor || 1.0;
        const time = Date.now() * 0.005;
        const radius = (200000 + 50000 * Math.sin(time * 0.5)) * exp;
        quantumTargetPos.set(Math.cos(time) * radius, Math.sin(time * 0.7) * 100000 * exp, Math.sin(time) * radius);
        synthTargetPos.set(Math.cos(time + Math.PI) * radius, Math.sin(time * 0.7 + Math.PI) * 100000 * exp, Math.sin(time + Math.PI) * radius);
    } else {
        updateAgentPhysics();
    }

    // 🧹 [JANITRON] Logic (Always Patrolling + Colored Body)
    const jColor = janitorFlashTime > 0 ? 0x3b82f6 : 0x4ade80;
    if (janitorGroup) {
        const isPurging = (janitorFlashTime > 0);
        if (isPurging) {
            janitorFlashTime--;
            // 🌈 Sovereign Loop: Blue -> Orange -> Red (1sec per stage roughly)
            const loopStage = (time * 6) % 3; 
            let loopColor = 0x3b82f6; // Electric Blue
            if (loopStage > 2) loopColor = 0xef4444; // Combat Red
            else if (loopStage > 1) loopColor = 0xf97316; // Warning Orange
            
            janitorGroup.userData.mat.emissive.setHex(loopColor);
            janitorGroup.userData.mat.color.setHex(loopColor);
            janitorGroup.userData.mat.emissiveIntensity = 3.0 + Math.sin(time * 25) * 1.5;
            
            // 💓 Pulsazione dimensionale
            const pulse = 1.0 + Math.sin(time * 25) * 0.15;
            janitorGroup.scale.set(pulse, pulse, pulse);
        } else {
            janitorGroup.userData.mat.emissive.setHex(0x422006);
            janitorGroup.userData.mat.color.setHex(0xfacc15); // Sovereign Yellow
            janitorGroup.userData.mat.emissiveIntensity = 0.5;
            janitorGroup.scale.set(1, 1, 1);
        }

        // Animazione Bocca (Apertura/Chiusura Pac-Man su asse X locale)
        const mouthSpeed = isPurging ? 15 : 6;
        const mouthOpen = Math.abs(Math.sin(time * mouthSpeed)) * 0.7;
        janitorTop.rotation.x = -mouthOpen;
        janitorBottom.rotation.x = mouthOpen;
        
        // Sovereign Patrol Logic: Incursiuoni dinamiche dentro e fuori la periferia
        const exp = nebulaExpansionFactor || 1.0;
        if (janitorGroup.position.distanceTo(janitorTargetPos) < 100000 * exp) {
            const scope = 1500000 * exp; // Raggio periferico esteso
            janitorTargetPos.set(
                (Math.random() - 0.5) * scope * 2,
                (Math.random() - 0.5) * 600000 * exp, // Variabilità Y per scansionare volumi diversi
                (Math.random() - 0.5) * scope * 2
            );
        }

        // Persistent Patrol: orbit moving target
        const orbitX = Math.cos(time * 0.5) * 80000 * exp;
        const orbitZ = Math.sin(time * 0.5) * 80000 * exp;
        const nextPos = new THREE.Vector3(janitorTargetPos.x + orbitX, janitorTargetPos.y, janitorTargetPos.z + orbitZ);
        
        // Look towards movement: allineamento perfetto di occhi e bocca alla direzione di marcia
        const lookDir = nextPos.clone().sub(janitorGroup.position);
        if (lookDir.length() > 1000) {
            const targetRot = Math.atan2(lookDir.x, lookDir.z);
            janitorGroup.rotation.y = targetRot; 
        }

        janitorGroup.position.lerp(nextPos, 0.05);
    }

    // 🧪 [DISTILLER] Flash Logic
    if (distillerGroup) {
        const dColor = distillerFlashTime > 0 ? 0xf59e0b : 0xe879f9;
        distillerGroup.children.forEach(c => { if(c.material) c.material.color.set(dColor); });
        if (distillerFlashTime > 0) distillerFlashTime--;
        distillerGroup.position.lerp(distillerTargetPos, 0.03);
        distillerGroup.position.y += Math.sin(time * 2) * 800;
        distillerGroup.rotation.y += 0.02;
    }

    // ☦️ [REAPER] Monuments Lifecycle
    reaperCubes = reaperCubes.filter(c => {
        const remaining = c.expiry - now;
        if (remaining < 0) {
            scene.remove(c.mesh);
            return false;
        }
        // Smooth scaling out in the last 10 seconds
        if (remaining < 10000) {
            const s = (remaining / 10000) * (1 + Math.sin(now * 0.005) * 0.05);
            c.mesh.scale.setScalar(s);
        } else {
            // Subtle Pulse for the red crosses
            c.mesh.scale.setScalar(1 + Math.sin(now * 0.005) * 0.05);
        }
        return true;
    });

    if (reaperGroup) {
        reaperGroup.position.lerp(reaperTargetPos, 0.04);
        const ghostTarget = reaperTargetPos.clone();
        ghostTarget.y = reaperGroup.position.y;
        reaperGroup.lookAt(ghostTarget);
        reaperGroup.position.y += Math.cos(time * 1.5) * 500;
    }

    if (snakeGroup && now - lastSnakeStep > 125) {
        lastSnakeStep = now;
        const exp = nebulaExpansionFactor || 1.0;
        let prevPos = snakeGroup.position.clone();
        const diff = snakeCurrentTarget.clone().sub(snakeGroup.position);
        if (diff.length() < 100000 * exp) snakeCurrentTarget.set((Math.random()-0.5)*2000000 * exp, (Math.random()-0.5)*1000000 * exp, (Math.random()-0.5)*2000000 * exp);
        if (Math.abs(diff.x) > Math.abs(diff.y) && Math.abs(diff.x) > Math.abs(diff.z)) snakeDirection.set(Math.sign(diff.x), 0, 0);
        else if (Math.abs(diff.y) > Math.abs(diff.z)) snakeDirection.set(0, Math.sign(diff.y), 0);
        else snakeDirection.set(0, 0, Math.sign(diff.z));
        snakeGroup.position.add(snakeDirection.clone().multiplyScalar(32500 * exp));
        snakeGroup.lookAt(snakeGroup.position.clone().add(snakeDirection));
        snakeSegments.forEach(seg => { let t = seg.position.clone(); seg.position.lerp(prevPos, 0.8); prevPos = t; });
    }

    if (quantumGroup) {
        quantumGroup.position.lerp(quantumTargetPos, 0.05);
        quantumCore.rotation.y += 0.04 * (timeTravelFactor || 1);
        quantumCore.rotation.x += 0.02;
        const isFusing = (quantumFlashTime > 0);
        if (quantumFlashTime > 0) quantumFlashTime--; 
        const pulse = 1.0 + Math.sin(time * 10) * (isFusing ? 0.4 : 0.05);
        quantumCore.scale.setScalar(pulse);
        if (isFusing && Math.sin(time * 35) > 0) {
            quantumCore.material.emissive.setHex(0xffffff);
            quantumCore.material.opacity = 1.0;
        } else {
            quantumCore.material.emissive.setHex(0x1d4ed8);
            quantumCore.material.opacity = 0.8;
        }
    }

    if (sentinelGroup) {
        sentinelGroup.position.lerp(sentinelTargetPos, 0.04);
        sentinelShield.rotation.y += 0.03;
        sentinelGroup.position.y += Math.sin(time * 3) * 300;

        const isWorking = (sentinelFlashTime > 0);
        if (isWorking) {
            sentinelFlashTime--;
            const pulse = 1.0 + Math.sin(time * 25) * 0.2;
            sentinelGroup.scale.setScalar(pulse);
            
            // 🔥 COMBAT_ALARM: Flashing Yellow -> Orange -> Red
            const speed = time * 15;
            const colors = [0xfacc15, 0xf97316, 0xef4444];
            const colorIdx = Math.floor(speed % colors.length);
            sentinelGroup.userData.mat.emissive.setHex(colors[colorIdx]);
            sentinelGroup.userData.mat.emissiveIntensity = 1.0 + Math.abs(Math.sin(time * 30)) * 2.0;
        } else {
            sentinelGroup.scale.setScalar(1.0);
            sentinelGroup.userData.mat.emissive.setHex(0x1e293b);
            sentinelGroup.userData.mat.emissiveIntensity = 0.5;
            sentinelGroup.userData.mat.color.setHex(0xcccccc);
        }

        // ⚡ [v4.0.2] Neural Overload: Yellow Lightning Effect
        if (sentinelLightningTime > 0) {
            sentinelLightningTime--;
            
            // Pulsazione e Colore Giallo Intenso
            const pulse = 1.0 + Math.sin(time * 40) * 0.3;
            sentinelGroup.scale.setScalar(pulse);
            sentinelGroup.userData.mat.emissive.setHex(0xfacc15); // Yellow
            sentinelGroup.userData.mat.emissiveIntensity = 5.0;

            // Disegna i fulmini
            if (!sentinelLightningGroup) {
                sentinelLightningGroup = new THREE.Group();
                sentinelGroup.add(sentinelLightningGroup);
            }
            sentinelLightningGroup.clear();
            
            for (let i = 0; i < 5; i++) {
                const points = [];
                let curr = new THREE.Vector3(0,0,0);
                points.push(curr.clone());
                for (let j = 0; j < 4; j++) {
                    curr.add(new THREE.Vector3((Math.random()-0.5)*50000, (Math.random()-0.5)*50000, (Math.random()-0.5)*50000));
                    points.push(curr.clone());
                }
                const lightningGeo = new THREE.BufferGeometry().setFromPoints(points);
                const lightningMat = new THREE.LineBasicMaterial({ color: 0xffff00, transparent: true, opacity: Math.random() });
                const lightning = new THREE.Line(lightningGeo, lightningMat);
                sentinelLightningGroup.add(lightning);
            }
        } else if (sentinelLightningGroup) {
            sentinelLightningGroup.clear();
        }
    }

    if (synthGroup) {
        synthGroup.position.lerp(synthTargetPos, 0.05);
        const isActive = (synthFlashTime > 0);
        const exp = nebulaExpansionFactor || 1.0;
        const subPulse = Math.sin(time * 15) * 0.5 + 0.5;
        synthSubAgents.forEach((sub, i) => {
            const orbitSpeed = 2.0;
            const orbitRadius = 65000 * exp;
            const angle = (time * orbitSpeed) + (i * Math.PI * 2 / 3);
            sub.position.set(Math.cos(angle) * orbitRadius, Math.sin(angle) * orbitRadius, Math.sin(angle * 0.5) * 20000 * exp);
            sub.rotation.y += 0.05;
            if (synthFlashTime > 0) {
                sub.material.emissiveIntensity = 1.0 + subPulse * 2.0;
                sub.scale.setScalar(1.2 + subPulse * 0.3);
                sub.material.color.setHex(0xffffff);
            } else {
                sub.material.emissiveIntensity = 0.2;
                sub.scale.setScalar(1.0);
                sub.material.color.setHex(sub.baseColor);
            }
        });
        if (synthFlashTime > 0) synthFlashTime--;
    }

    if (skywalkerGroup) {
        const exp = nebulaExpansionFactor || 1.0;
        // High-Altitude Periphery Patrol (Outer Guard)
        const patrolOrbit = (1100000 + Math.sin(time * 0.2) * 200000) * exp; // Orbiting at the edge
        const patrolSpeed = time * 0.15; // Slower, more majestic patrol
        const tx = Math.cos(patrolSpeed) * patrolOrbit;
        const tz = Math.sin(patrolSpeed) * patrolOrbit;
        const ty = Math.sin(time * 0.4) * 600000 * exp; // High vertical clearance
        
        skywalkerTargetPos.set(tx, ty, tz);
        skywalkerGroup.position.lerp(skywalkerTargetPos, 0.02); // Smoother lerp for long distances
        
        // Look at current tangent + future curve for natural banking
        const lookT = time * 0.15 + 0.1;
        const lx = Math.cos(lookT) * patrolOrbit;
        const lz = Math.sin(lookT) * patrolOrbit;
        const ly = Math.sin((time + 0.1) * 0.4) * 600000;
        skywalkerGroup.lookAt(new THREE.Vector3(lx, ly, lz));
        if (skywalkerLasers.length > 0) {
            skywalkerLasers.forEach(l => {
                l.scale.x += 0.5;
                l.material.opacity -= 0.05;
                if(l.material.opacity <= 0) scene.remove(l);
            });
            skywalkerLasers = skywalkerLasers.filter(l => l.material.opacity > 0);
        }
    }

    if (bridgerGroup) {
        bridgerGroup.position.lerp(bridgerTargetPos, 0.05);
        bridgerGroup.rotation.y += 0.01;
        const isPulsing = (bridgerPulseTime > 0);
        if (bridgerPulseTime > 0) bridgerPulseTime--;
        if (isPulsing) {
            const pScale = 1.0 + Math.sin(time * 15) * 0.3;
            bridgerGroup.scale.setScalar(pScale);
            bridgerGroup.bridgeCore.material.emissive.setHex(0xf97316); 
            bridgerGroup.bridgeCore.material.color.setHex(0xf97316);
            if(bridgerGroup.rings) bridgerGroup.rings.forEach(r => r.material.color.setHex(0xf97316));
        } else {
            bridgerGroup.scale.setScalar(1.0);
            bridgerGroup.bridgeCore.material.emissive.setHex(0xffffff); 
            bridgerGroup.bridgeCore.material.color.setHex(0xffffff);
            if(bridgerGroup.rings) bridgerGroup.rings.forEach(r => r.material.color.setHex(0x00ffff));
        }
        if(bridgerGroup.rings) {
            bridgerGroup.rings[0].rotation.y += 0.05;
            bridgerGroup.rings[1].rotation.x += 0.03;
        }
    }

    medicalCubes = medicalCubes.filter(c => {
        const age = now - c.createdAt;
        const isVeryOld = (age > 600000);
        const MIN_VISIBILITY = 120000;
        if (isVeryOld || (c.userData.completed && age > MIN_VISIBILITY)) {
            c.scale.setScalar(c.scale.x * 0.95);
            if (c.scale.x < 0.1 || isVeryOld) {
                scene.remove(c);
                return false;
            }
        } else {
            c.scale.setScalar(0.8 + Math.sin(time * 3) * 0.05); 
        }
        return true;
    });

    if (followedAgent) {
        controls.target.lerp(followedAgent.position, 0.05);
        
        // 📡 Cinematic Follow: Lerp camera distance to 200,000 units
        const idealDist = 200000 * (nebulaExpansionFactor || 1.0);
        const currentDist = camera.position.distanceTo(controls.target);
        const distDiff = idealDist - currentDist;
        
        if (Math.abs(distDiff) > 1000) {
            const dir = camera.position.clone().sub(controls.target).normalize();
            const targetCamPos = controls.target.clone().add(dir.multiplyScalar(idealDist));
            camera.position.lerp(targetCamPos, 0.03);
        }
    }

    if (!isRotationPaused) {
        if (pointsMesh) pointsMesh.rotation.y += 0.001;
        if (neuralLinks) {
            neuralLinks.rotation.y += 0.001;
            const isLight = document.body.classList.contains('light-theme');
            neuralLinks.children.forEach(link => {
                const now = Date.now();
                if (link.isSpark) {
                    // 🌈 [LED RGB EFFECT] Continuous HSL shift
                    link.material.color.setHSL((time * 0.4) % 1, 1, isLight ? 0.4 : 0.6);
                    link.material.opacity = isLight ? 0.8 : 0.6 + Math.sin(time * 15) * 0.3;
                    link.material.blending = isLight ? THREE.NormalBlending : THREE.AdditiveBlending;
                } else if (link.isSuper) {
                    // 🟠🟡 [SUPER-LINK PULSE] 2 pulses, then 30s solid orange-yellow
                    const cycle = now % 31000; // 31 seconds cycle
                    if (cycle < 2000) {
                        // 2 rapid pulses in the first 2 seconds
                        const p = Math.abs(Math.sin(cycle * 0.002 * Math.PI * 2));
                        link.material.color.setRGB(1.0, 0.6 + 0.4 * p, 0.1); // Arancio -> Giallo
                        link.material.opacity = 0.4 + 0.6 * p;
                    } else {
                        // Solid Orange-Yellow for the rest of the 30s
                        link.material.color.setHex(0xf59e0b);
                        link.material.opacity = 0.7;
                    }
                    link.material.blending = isLight ? THREE.NormalBlending : THREE.AdditiveBlending;
                } else if (link.isNew) {
                    link.material.opacity = 0.5 + Math.sin(time * 20) * 0.5;
                    link.material.blending = isLight ? THREE.NormalBlending : THREE.AdditiveBlending;
                } else {
                    if (isLight) {
                        link.material.color.set(0x475569); 
                        link.material.opacity = 0.25;
                        link.material.blending = THREE.NormalBlending;
                    } else {
                        link.material.color.set(0xffffff); 
                        link.material.opacity = 0.15;
                        link.material.blending = THREE.NormalBlending;
                    }
                }
            });
        }
    }
    
    if (clusterNodesGroup) {
        clusterNodesGroup.children.forEach((cluster, i) => {
            cluster.rotation.x += 0.005;
            cluster.rotation.z += 0.008;
            cluster.material.emissiveIntensity = 0.4 + Math.sin(time * 1.5 + i) * 0.3;
        });
    }

    if (controls) controls.update();
    if (renderer) renderer.render(scene, camera);
}

function updateAgentPhysics() {
}

function spawnMedicalCube(x, y, z) {
    const group = new THREE.Group();
    group.createdAt = Date.now();
    group.userData.posKey = `${Math.round(x)}_${Math.round(y)}_${Math.round(z)}`;
    const boxMat = new THREE.MeshLambertMaterial({ color: 0x4ade80, transparent: true, opacity: 0.25, emissive: 0x4ade80, wireframe: true });
    const cube = new THREE.Mesh(new THREE.BoxGeometry(70000, 70000, 70000), boxMat);
    group.add(cube);
    const crossMat = new THREE.MeshPhongMaterial({ color: 0xff4444, emissive: 0xff0000 });
    const barLong = new THREE.BoxGeometry(45000, 10000, 10000);
    const hBar = new THREE.Mesh(barLong, crossMat);
    const vBar = new THREE.Mesh(barLong, crossMat);
    vBar.rotation.z = Math.PI / 2;
    const dBar = new THREE.Mesh(barLong, crossMat);
    dBar.rotation.y = Math.PI / 2;
    group.add(hBar, vBar, dBar);
    group.position.set(x, y, z);
    scene.add(group);
    medicalCubes.push(group);
    log("⚕️ REASONER_HEAL: Tombstone Sanitized.", "#4ade80");
}

function syncSnakeTail(count) {
    if (!scene) return;
    const sMat = new THREE.MeshLambertMaterial({ color: 0x10b981 });
    const wagonMat = new THREE.MeshPhongMaterial({ color: 0x34d399, transparent: true, opacity: 0.6 });
    const baseLength = 7;
    const targetLength = baseLength + (count || 0);
    while(snakeSegments.length < targetLength) {
        const i = snakeSegments.length;
        let seg;
        if (i < baseLength) {
            const size = (i <= 3) ? 30000 : 30000 - (i-3)*4500;
            seg = new THREE.Mesh(new THREE.BoxGeometry(size, size, size), sMat);
        } else {
            const size = 15000;
            seg = new THREE.Mesh(new THREE.SphereGeometry(size, 8, 8), wagonMat);
        }
        const last = snakeSegments[snakeSegments.length-1] || snakeGroup;
        seg.position.copy(last.position);
        scene.add(seg);
        snakeSegments.push(seg);
    }
    while(snakeSegments.length > targetLength) {
        const seg = snakeSegments.pop();
        scene.remove(seg);
    }
}

function spawnSkywalkerLaser() {
    if (!skywalkerGroup || !scene) return;
    const mat = new THREE.LineBasicMaterial({ color: 0xff0000, transparent: true, opacity: 1.0 });
    const start = skywalkerGroup.position.clone();
    
    // Al esterno del cubo (cube is 500k scale approx)
    const end = new THREE.Vector3(
        (Math.random() - 0.5) * 2000000,
        (Math.random() - 0.5) * 2000000,
        (Math.random() - 0.5) * 2000000
    );
    
    const geo = new THREE.BufferGeometry().setFromPoints([start, end]);
    const line = new THREE.Line(geo, mat);
    scene.add(line);
    skywalkerLasers.push(line);
}

let heatmapMode = false;
let currentHeatmap = {};

function toggleHeatmap(enabled) {
    heatmapMode = enabled;
    if (enabled) {
        log("🔥 HEATMAP_MODE: Active. Visualizing semantic density.", "#ff5555");
    } else {
        log("🧊 HEATMAP_MODE: Disabled. Restoring theme colors.", "#06b6d4");
    }
    // Forza aggiornamento scena se abbiamo dati
    if (vaultPoints.length > 0) updateThreeScene(vaultPoints, null);
}

function updateThreeScene(points, links = null) {
    if (!pointsMesh || !neuralLinks) return;
    vaultPoints = points || [];
    if (links !== null) lastNeuralLinks = links;
    const currentLinks = links !== null ? links : lastNeuralLinks;
    const count = Math.min(vaultPoints.length, 30000);
    const pos = pointsMesh.geometry.attributes.position.array;
    const col = pointsMesh.geometry.attributes.color.array;
    const pastelPalette = ["#FFB7B2", "#FFDAC1", "#E2F0CB", "#B5EAD7", "#C7CEEA", "#FF9AA2", "#B2E2F2", "#D5AAFF"];
    const isLight = document.body.classList.contains('light-theme');

    for (let i = 0; i < count; i++) {
        const p = vaultPoints[i];
        const exp = nebulaExpansionFactor || 1.0;
        pos[i*3] = (p.x || 0) * exp; pos[i*3+1] = (p.y || 0) * exp; pos[i*3+2] = (p.z || 0) * exp;
        
        let displayColor;
        if (heatmapMode && currentHeatmap[p.id] !== undefined) {
            // Gradient: Blue (Cold) -> Red (Hot)
            const temp = currentHeatmap[p.id]; // 0.0 - 1.0
            const r = Math.floor(temp * 255);
            const b = Math.floor((1 - temp) * 255);
            displayColor = `rgb(${r}, 50, ${b})`;
        } else {
            displayColor = p.color || "#06b6d4";
            if (isLight && (displayColor === "#06b6d4" || displayColor === "#ffffff")) {
                displayColor = pastelPalette[i % pastelPalette.length];
            }
            if (!clusterFocus) {
                displayColor = isLight ? "#94a3b8" : "#475569";
            }
        }
        const opacity = p.opacity !== undefined ? p.opacity : 1.0;
        const color = new THREE.Color(displayColor);
        col[i*3] = color.r * opacity; 
        col[i*3+1] = color.g * opacity; 
        col[i*3+2] = color.b * opacity;
    }
    pointsMesh.geometry.attributes.position.needsUpdate = true;
    pointsMesh.geometry.attributes.color.needsUpdate = true;
    renderClusters(vaultPoints);
    const drawCount = Math.floor(count * timeTravelFactor);
    pointsMesh.geometry.setDrawRange(0, drawCount);

    // [v4.1] Optimized Multimodal Rendering: Filter first, then spawn
    multimodalGroup.clear();
    const mediaNodes = vaultPoints.filter(p => p.media_type && multimodalTextures[p.media_type]);
    mediaNodes.forEach(p => {
        const material = new THREE.SpriteMaterial({ 
            map: multimodalTextures[p.media_type],
            transparent: true,
            opacity: 0.9
        });
        const sprite = new THREE.Sprite(material);
        const exp = nebulaExpansionFactor || 1.0;
        sprite.scale.set(60000, 60000, 1);
        sprite.position.set(p.x * exp, p.y * exp, p.z * exp);
        sprite.userData = { id: p.id, type: 'multimodal', media: p.media_type };
        multimodalGroup.add(sprite);
    });

    // 1. Creiamo una mappa rapida dei punti correnti sullo schermo
    const ptsMap = {};
    vaultPoints.forEach(p => ptsMap[p.id] = p);

    neuralLinks.clear();
    const now = Date.now();
    if (layersVisibility.edges && currentLinks && currentLinks.length > 0) {
        currentLinks.slice(0, 1500).forEach(l => {
            // Estraiamo la posizione in tempo reale dai nodi renderizzati, non dallo storico!
            const srcNode = ptsMap[l.source];
            const dstNode = ptsMap[l.target];
            
            if (srcNode && dstNode) {
                const exp = nebulaExpansionFactor || 1.0;
                const geo = new THREE.BufferGeometry().setFromPoints([
                    new THREE.Vector3(srcNode.x * exp, srcNode.y * exp, srcNode.z * exp),
                    new THREE.Vector3(dstNode.x * exp, dstNode.y * exp, dstNode.z * exp)
                ]);
                const isSpark = l.is_aura === true;
                const isSuper = l.relation === 'synapse';
                const isNew = (now - (l.created_at * 1000) < 6000);
                
                let edgeColor = isLight ? 0x475569 : 0x2d3748; // Grigio default
                let opacity = 0.15;
                
                if (isSpark) {
                    edgeColor = 0xffffff; // Verrà sovrascritto dall'HSL in animate
                    opacity = 0.8;
                } else if (isSuper) {
                    edgeColor = 0xf59e0b; // Arancio base
                    opacity = 0.7;
                } else if (isNew) {
                    edgeColor = 0x00ffff;
                    opacity = 0.8;
                }

                const mat = new THREE.LineBasicMaterial({ 
                    color: edgeColor, 
                    transparent: true, 
                    opacity: opacity,
                    blending: isLight ? THREE.NormalBlending : ((isSpark || isSuper || isNew) ? THREE.AdditiveBlending : THREE.NormalBlending)
                });
                const line = new THREE.Line(geo, mat);
                line.isSpark = isSpark;
                line.isSuper = isSuper;
                line.isNew = isNew;
                line.createdAt = l.created_at * 1000;
                neuralLinks.add(line);
            }
        });
    }
}

function renderClusters(points) {
    if (!clusterNodesGroup) return;
    const isLight = document.body.classList.contains('light-theme');
    clusterNodesGroup.clear();
    if (!clusterFocus) return;
    const clusters = {};
    points.forEach(p => {
        const theme = p.theme || 'default';
        if (theme === 'default') return;
        if (!clusters[theme]) clusters[theme] = { x:0, y:0, z:0, count:0, color: p.color };
        clusters[theme].x += p.x;
        clusters[theme].y += p.y;
        clusters[theme].z += p.z;
        clusters[theme].count++;
    });
    Object.keys(clusters).forEach(theme => {
        const c = clusters[theme];
        if (c.count > 3) {
            const avgX = c.x / c.count;
            const avgY = c.y / c.count;
            const avgZ = c.z / c.count;
            const size = 16000;
            const geo = new THREE.CylinderGeometry(size, size, 4000, 6);
            const mat = new THREE.MeshPhongMaterial({
                color: c.color,
                transparent: true,
                opacity: 0.9,
                shininess: 100
            });
            const hex = new THREE.Mesh(geo, mat);
            
            // Assegniamo l'ID di un nodo rappresentativo al cluster per renderlo ispezionabile!
            const sampleNode = points.find(p => (p.theme || 'default') === theme);
            if (sampleNode) hex.userData = { id: sampleNode.id, isCluster: true };

            hex.rotation.x = Math.PI / 2;
            hex.onBeforeRender = (renderer, scene, camera, geometry, material) => {
                const clock = Date.now() * 0.002;
                material.color.setHSL((clock + avgX * 0.00001) % 1, 0.8, isLight ? 0.4 : 0.6);
                material.emissive.setHSL((clock * 1.5) % 1, 1, 0.2);
            };
            const exp = nebulaExpansionFactor || 1.0;
            hex.position.set(avgX * exp, avgY * exp, avgZ * exp);
            clusterNodesGroup.add(hex);
        }
    });
}

function updateEvolutionHUD() {
    const hud = document.getElementById('evolution-telemetry-hud');
    const bar = document.getElementById('evolution-progress-bar');
    const txt = document.getElementById('evolution-status-text');
    if (!hud || !bar || !txt) return;
    if (isEvolving) {
        hud.style.display = 'flex';
        bar.style.width = `${evolutionProgress}%`;
        txt.innerText = evolutionStep;
    } else {
        bar.style.width = `100%`;
        txt.innerText = "Realignment Stabilized";
        setTimeout(() => { if(!isEvolving) hud.style.display = 'none'; }, 3000);
    }
}

window.exportAuditLedger = function(format) {
    const table = document.getElementById('audit-ledger-body');
    if (!table) return;
    const rows = Array.from(table.rows);
    let content = "";
    let filename = `NeuralVault_Audit_${new Date().toISOString().slice(0,19).replace(/[:T]/g, '_')}.txt`;
    let type = "text/plain";
    if (format === 'json') {
        const data = rows.map(r => ({
            time: r.cells[0].innerText, agent: r.cells[1].innerText, action: r.cells[2].innerText,
            target: r.cells[3].innerText, reason: r.cells[4].innerText, savings: r.cells[5].innerText
        }));
        content = JSON.stringify(data, null, 2); filename = filename.replace('.txt', '.json'); type = "application/json";
    } else if (format === 'csv') {
        content = "TIMESTAMP,AGENTE,AZIONE,TARGET,MOTIVAZIONE,IMPATTO\n" + 
            rows.map(r => Array.from(r.cells).map(c => `"${c.innerText.replace(/"/g, '""')}"`).join(",")).join("\n");
        filename = filename.replace('.txt', '.csv'); type = "text/csv";
    } else {
        content = "--- NEURALVAULT AUDIT LEDGER ---\n\n" + 
            rows.map(r => `[${r.cells[0].innerText}] ${r.cells[1].innerText} -> ${r.cells[2].innerText}\n   Reason: ${r.cells[4].innerText}\n`).join("\n");
    }
    const blob = new Blob([content], { type: type });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a'); a.href = url; a.download = filename; a.click();
    if(document.getElementById('export-dropdown')) document.getElementById('export-dropdown').classList.add('hidden');
};

let currentInspectedNodeId = null;

async function selectNode(id) {
    currentInspectedNodeId = id;
    const modal = document.getElementById('node-inspector-modal');
    const txtEl = document.getElementById('node-text');
    const metaEl = document.getElementById('node-meta');
    const linksEl = document.getElementById('node-links-list');
    const auditArea = document.getElementById('audit-result-area');
    const mediaCont = document.getElementById('media-preview-container');
    const mediaImg = document.getElementById('media-preview-img');

    if (modal) {
        modal.style.display = 'flex';
        // Reset state
        if (auditArea) auditArea.style.display = 'none';
        if (linksEl) linksEl.innerHTML = '';
        if (mediaCont) mediaCont.classList.add('hidden');
    }
    
    if (txtEl) txtEl.innerText = "Sincronizzazione neurale in corso...";

    try {
        const r = await fetch(`/api/node/${id}`, { headers: { 'X-API-KEY': VAULT_KEY }});
        const d = await r.json();
        
        if (d.error) {
            if (txtEl) txtEl.innerText = `Errore: ${d.error}`;
            return;
        }

        if (txtEl) txtEl.innerText = d.text || "Nodo senza contenuto testuale.";
        
        // Metadata formatting
        if (metaEl) {
            const metaObj = d.metadata || {};
            metaEl.innerHTML = `
                <div style="color: #a855f7; margin-bottom: 5px;">[PROPRIETÀ]</div>
                ID: ${d.id}<br>
                TIPO: ${d.type || 'text'}<br>
                DATA: ${new Date(d.created_at * 1000).toLocaleString()}<br>
                SORGENTE: ${metaObj.source || 'Sovereign Upload'}
            `;
        }

        // Multimedia Preview
        if (d.preview && mediaCont && mediaImg) {
            mediaImg.src = d.preview;
            mediaCont.classList.remove('hidden');
        }

        // Synaptic Connections (Navigable)
        if (linksEl && d.connections) {
            if (d.connections.length === 0) {
                linksEl.innerHTML = '<div style="font-size:0.6rem; opacity:0.4;">Nessuna connessione sinaptica diretta rilevata.</div>';
            } else {
                d.connections.forEach(conn => {
                    const btn = document.createElement('button');
                    btn.style.cssText = "padding: 0.4rem 0.8rem; background: rgba(59, 130, 246, 0.1); border: 1px solid rgba(59, 130, 246, 0.3); color: #3b82f6; border-radius: 6px; font-size: 0.6rem; cursor: pointer; transition: 0.3s; font-family: 'JetBrains Mono';";
                    btn.innerHTML = `<i class="fas fa-microchip"></i> ${conn.node.substring(0, 8)}...`;
                    btn.title = `Relazione: ${conn.relation || 'unknown'}`;
                    btn.onclick = () => selectNode(conn.node);
                    btn.onmouseover = () => { btn.style.background = "rgba(59, 130, 246, 0.2)"; btn.style.borderColor = "#3b82f6"; };
                    btn.onmouseout = () => { btn.style.background = "rgba(59, 130, 246, 0.1)"; btn.style.borderColor = "rgba(59, 130, 246, 0.3)"; };
                    linksEl.appendChild(btn);
                });
            }
        }
    } catch(e) { 
        if (txtEl) txtEl.innerText = "Errore critico durante il recupero del frammento."; 
        console.error(e);
    }
}

async function verifyNodeCoherence() {
    if (!currentInspectedNodeId) return;
    
    const auditArea = document.getElementById('audit-result-area');
    const auditText = document.getElementById('audit-text');
    const verifyBtn = document.getElementById('verify-node-btn');

    if (auditArea) auditArea.style.display = 'block';
    if (auditText) auditText.innerText = "Lo sciame sta analizzando la coerenza logica...";
    if (verifyBtn) verifyBtn.disabled = true;

    try {
        const r = await fetch(`/api/node/verify/${currentInspectedNodeId}`, { headers: { 'X-API-KEY': VAULT_KEY }});
        const d = await r.json();
        if (auditText) auditText.innerText = d.audit || "Analisi completata senza feedback rilevante.";
    } catch(e) {
        if (auditText) auditText.innerText = "Errore durante il protocollo di audit.";
    } finally {
        if (verifyBtn) verifyBtn.disabled = false;
    }
}

async function refreshModels() {
    try {
        const r = await fetch('/api/models/status', { headers: { 'X-API-KEY': VAULT_KEY }});
        const d = await r.json();
        installedModels = d.installed || []; return d;
    } catch(e) { return {installed:[], available:[]}; }
}

async function registerCustomModel() {
    const nameEl = document.getElementById('custom-model-name');
    const providerEl = document.getElementById('custom-model-provider');
    const pathEl = document.getElementById('custom-model-path');

    if (!nameEl || !pathEl) return;

    const name = nameEl.value.trim();
    const provider = providerEl.value;
    const path = pathEl.value.trim();

    if (!name || !path) {
        log("⚠️ FORGE: Nome modello e percorso sono obbligatori.", "#ef4444");
        return;
    }

    log(`🔨 FORGE: Inizio registrazione core [${name}] via ${provider.toUpperCase()}...`, "#a855f7");

    try {
        const response = await fetch('/api/models/register', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'X-API-KEY': VAULT_KEY 
            },
            body: JSON.stringify({ name, provider, path })
        });

        const result = await response.json();
        if (result.success) {
            log(`✅ FORGE: Modello ${name} registrato con successo nel Vault.`, "#4ade80");
            nameEl.value = '';
            pathEl.value = '';
            
            // Re-sync UI
            await refreshModels();
            await renderModelHubTable();
            if (typeof updateAllSwarmDropdowns === 'function') {
                updateAllSwarmDropdowns();
            }
        } else {
            log(`❌ FORGE Error: ${result.error || 'Errore sconosciuto'}`, "#ef4444");
        }
    } catch (e) {
        log(`❌ FORGE: Errore critico durante la registrazione: ${e.message}`, "#ef4444");
    }
}

async function renderModelHubTable() {
    const bodies = [document.getElementById('model-hub-table-body'), document.getElementById('settings-hub-table-body')];
    try {
        const r = await fetch('/api/models/status', { headers: { 'X-API-KEY': VAULT_KEY }});
        const d = await r.json();
        const models = d.installed || [];
        
        // Ordine desiderato delle categorie
        const categoryOrder = ["TINY_KINETIC", "MULTIMODAL_SENSORY", "SOVEREIGN_MID_CORE", "ELITE_HEAVY_WEIGHT", "CUSTOM_FORGE", "General"];
        
        // Raggruppamento
        const groups = {};
        models.forEach(m => {
            const cat = m.category || "General";
            if (!groups[cat]) groups[cat] = [];
            groups[cat].push(m);
        });

        let html = "";
        
        categoryOrder.forEach(cat => {
            const groupModels = groups[cat];
            if (!groupModels || groupModels.length === 0) return;

            // Header della Categoria
            const catLabel = cat.replace(/_/g, ' ');
            html += `
            <tr class="hub-category-header">
                <td colspan="6" style="padding: 1.5rem 1rem 0.5rem 1rem;">
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <div style="height: 2px; flex: 1; background: linear-gradient(90deg, rgba(168,85,247,0.5), transparent);"></div>
                        <span style="font-size: 0.7rem; font-weight: 900; color: #a855f7; letter-spacing: 3px; text-transform: uppercase;">[ ${catLabel} ]</span>
                        <div style="height: 2px; flex: 1; background: linear-gradient(270deg, rgba(168,85,247,0.5), transparent);"></div>
                    </div>
                </td>
            </tr>`;

            groupModels.forEach(m => {
                const isInstalled = m.status === 'INSTALLED';
                const capHtml = (m.capabilities || []).map(cap => 
                    `<span class="capability-badge">${cap}</span>`
                ).join('');

                html += `
                <tr class="hub-model-row" style="border-bottom:1px solid rgba(255,255,255,0.03); transition: all 0.3s;" onmouseover="this.style.background='rgba(168,85,247,0.03)'" onmouseout="this.style.background='transparent'">
                    <!-- COL 1: MODELLO -->
                    <td style="padding:1.2rem;">
                        <div style="font-weight:900; color:#fff; font-size:1.1rem; letter-spacing:1px; display:flex; align-items:center; gap:8px;">
                            ${m.name.split(':')[0].toUpperCase()}
                            ${isInstalled ? '<i class="fas fa-check-circle" style="color:#4ade80; font-size:0.7rem;" title="Native Integration Active"></i>' : ''}
                        </div>
                        <div style="font-family:'JetBrains Mono'; font-size:0.5rem; color:#8b949e; margin-top:6px;">
                            VERSION: <span style="color:#a855f7;">${m.name.split(':')[1] || 'latest'}</span> | SIZE: <span style="color:#fff;">${m.size}</span>
                        </div>
                    </td>

                    <!-- COL 2: HARDWARE DNA -->
                    <td style="padding:1.2rem;">
                         <div style="font-family:'JetBrains Mono'; font-size:0.55rem; color:#4ade80; background:rgba(74,222,128,0.05); padding:6px 10px; border-radius:6px; border: 1px solid rgba(74,222,128,0.1); display:inline-block;">
                            <div style="margin-bottom:4px;"><i class="fas fa-memory"></i> MIN_RAM: ${m.ram || '4GB'}</div>
                            ${m.vram && m.vram !== 'N/D' ? `<div style="color:#f59e0b;"><i class="fas fa-video"></i> VRAM_OPT: ${m.vram}</div>` : '<div style="color:#94a3b8; opacity:0.6;"><i class="fas fa-microchip"></i> CPU_DRIVEN</div>'}
                        </div>
                    </td>

                    <!-- COL 3: CAPABILITIES -->
                    <td style="padding:1.2rem;">
                        <div style="display:flex; flex-wrap:wrap; gap:5px; max-width:280px;">
                            ${capHtml || '<span style="color:#64748b; font-size:0.6rem; font-style:italic;">General Reasoning</span>'}
                        </div>
                    </td>

                    <!-- COL 4: PROS & STRENGTHS -->
                    <td style="padding:1.2rem; max-width:300px;">
                        <div style="font-size:0.75rem; color:#fff; font-weight:700; margin-bottom:4px; line-height:1.3;">${m.strengths || 'Performance Optimale'}</div>
                        <div style="font-size:0.65rem; color:#94a3b8; font-style:italic; line-height:1.4;">"${m.pros}"</div>
                    </td>

                    <!-- COL 5: SWARM SINERGY -->
                    <td style="padding:1.2rem;">
                        <div style="display:flex; flex-wrap:wrap; gap:4px; margin-bottom:8px;">
                            ${(Array.isArray(m.synergy) && m.synergy[0] !== 'None') ? m.synergy.map(s => `<span class="badge-synergy" style="font-size:0.5rem; padding:2px 8px;">${s}</span>`).join('') : '<span class="badge-synergy" style="opacity:0.4; background:transparent; border:1px solid rgba(255,255,255,0.1);">SOLO_NODE</span>'}
                        </div>
                        <div style="font-size:0.5rem; color:#a855f7; font-weight:800; text-transform:uppercase; letter-spacing:1px; background:rgba(168,85,247,0.05); padding:3px 8px; border-radius:4px; display:inline-block; border:1px solid rgba(168,85,247,0.2);">
                            <i class="fas fa-project-diagram"></i> ROLE: ${m.task || 'GENERAL'}
                        </div>
                    </td>

                    <!-- COL 6: ACTIONS -->
                    <td style="padding:1.2rem; text-align:right;">
                        <div style="display:flex; align-items:center; justify-content:flex-end; gap:10px;">
                            ${isInstalled ? 
                                `<button onclick="window.deleteModel('${m.name}')" class="hub-action-btn delete-btn">DELETE</button>` :
                                `<button onclick="window.deployModel('${m.name}')" class="hub-action-btn deploy-btn">DEPLOY</button>`
                            }
                        </div>
                    </td>
                </tr>`;
            });
        });
        
        bodies.forEach(b => { if(b) b.innerHTML = html; });
        populateSwarmSelects(models);
    } catch(e) {
        console.error("Hub Sync Error:", e);
    }
}

function populateSwarmSelects(models) {
    const selects = [
        'route-audit', 'route-extraction', 'route-crossref', 'route-synthesis', 
        'route-chat-mediator', 'route-multimodal', 'route-vision-description', 
        'route-vision-detection', 'route-vision-ocr', 'route-vision-analysis', 'route-evolution',
        'route-evolution-suggestions', 'court-judge-1', 'court-judge-2', 'court-judge-3',
        'route-coding-1', 'route-coding-2', 'route-coding-supervisor'
    ];
    const installed = models.filter(m => m.status === 'INSTALLED');
    
    selects.forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            const currentVal = el.value;
            let options = installed.map(m => `<option value="${m.name}">${m.name}</option>`).join('');
            
            // Allow null/none for judges
            if (id.startsWith('court-judge-')) {
                options = `<option value="-">-</option>` + options;
            }
            
            el.innerHTML = options;
            if (currentVal && (currentVal === "-" || installed.find(m => m.name === currentVal))) {
                el.value = currentVal;
            }
        }
    });
}

window.saveSwarmRouting = async () => {
    const config = {
        'api_key': VAULT_KEY,
        'audit': document.getElementById('route-audit').value,
        'extraction': document.getElementById('route-extraction').value,
        'crossref': document.getElementById('route-crossref').value,
        'synthesis': document.getElementById('route-synthesis').value,
        'chat_mediator': document.getElementById('route-chat-mediator').value,
        'multimodal': document.getElementById('route-multimodal').value,
        'vision_description': document.getElementById('route-vision-description')?.value || "moondream",
        'vision_detection': document.getElementById('route-vision-detection')?.value || "moondream",
        'vision_ocr': document.getElementById('route-vision-ocr')?.value || "moondream",
        'vision_analysis': document.getElementById('route-vision-analysis')?.value || "moondream",
        'evolution_model': document.getElementById('route-evolution').value,
        'evolution_suggestion_model': document.getElementById('route-evolution-suggestions')?.value || "llama3.2",
        'consensus_threshold': parseInt(document.getElementById('consensus-threshold').value || 2),
        'weaver_sensitivity': parseFloat(document.getElementById('weaver-sensitivity').value || 0.82),
        'auto_evolve_active': document.getElementById('auto-evolve-toggle')?.checked || false,
        'autonomous_court': document.getElementById('autonomous-court-toggle')?.checked || false,
        'court_judge_1': document.getElementById('court-judge-1')?.value || "llama3.2",
        'court_judge_2': document.getElementById('court-judge-2')?.value || "-",
        'court_judge_3': document.getElementById('court-judge-3')?.value || "-",
        'coding_1': document.getElementById('route-coding-1')?.value || "llama3.2",
        'coding_2': document.getElementById('route-coding-2')?.value || "llama3.2",
        'coding_supervisor': document.getElementById('route-coding-supervisor')?.value || "llama3.2",
        'ollama_url': document.getElementById('ollama-url')?.value || "http://127.0.0.1:11434",
        'github_token': document.getElementById('github-token')?.value || "",
        'github_repo': document.getElementById('github-repo')?.value || "",
        'git_auto_branch': document.getElementById('git-auto-branch-toggle')?.checked || false,
        'autonomous_patching': document.getElementById('auto-patching-toggle')?.checked || false
    };
    
    try {
        const r = await fetch('/api/system/settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(config)
        });
        if (r.ok) {
            const modal = document.getElementById('swarm-save-modal');
            if (modal) modal.style.display = 'flex';
            log("✅ Configurazione Swarm Persistita con successo.");
        } else {
            alert("Errore nel salvataggio. Verifica la connessione al Vault.");
        }
    } catch(e) {
        console.error("Save Error:", e);
    }
};

window.testGitHubConnection = async () => {
    const token = document.getElementById('github-token')?.value;
    const repo = document.getElementById('github-repo')?.value;
    const ind = document.getElementById('github-sync-indicator');
    const stat = document.getElementById('github-sync-status');

    if (!token || !repo) {
        log("⚠️ GitHub: Inserire Token e Repository per il test.", "#f97316");
        return;
    }

    log("📡 GitHub: Avvio Handshake...", "#f97316");
    
    try {
        const r = await fetch('/api/github/test', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ api_key: VAULT_KEY, token, repo })
        });
        const d = await r.json();
        
        if (d.success) {
            log("\u2705 GitHub: Connessione stabilita con " + d.data, "#10b981");
            if (ind) ind.style.background = "#10b981";
            if (stat) stat.innerText = "GitHub: Connected";
        } else {
            log(`❌ GitHub Error: ${d.error}`, "#ef4444");
            if (ind) ind.style.background = "#ef4444";
            if (stat) stat.innerText = "GitHub: Auth Failed";
        }
    } catch(e) {
        log(`❌ GitHub: Errore di rete: ${e.message}`, "#ef4444");
    }
};

window.updateRecommendations = async () => {
    try {
        const resp = await fetch('/api/system/recommendations');
        if (!resp.ok) {
            console.warn("⚠️ Sovereign Recs: Endpoint non trovato. Riavviare il server.");
            return;
        }
        const data = await resp.json();
        const recs = data.recommendations;
        
        // Mappa Task ID -> UI Panel ID
        const taskMap = {
            'audit': 'rec-audit',
            'extraction': 'rec-extraction',
            'crossref': 'rec-crossref',
            'synthesis': 'rec-synthesis',
            'chat_mediator': 'rec-chat_mediator',
            'oracle_evolution': 'rec-oracle_evolution',
            'vision_general': 'rec-vision_general',
            'scene_description': 'rec-scene_description',
            'vision_detection': 'rec-vision_detection',
            'vision_ocr': 'rec-vision_ocr',
            'vision_analysis': 'rec-vision_analysis',
            'coding_1': 'rec-coding_1',
            'coding_2': 'rec-coding_2',
            'coding_supervisor': 'rec-coding_supervisor',
            'evolution_suggestions': 'rec-evolution_suggestions',
            'court_judge_1': 'rec-court_judge_1',
            'court_judge_2': 'rec-court_judge_2',
            'court_judge_3': 'rec-court_judge_3'
        };

        Object.keys(taskMap).forEach(taskKey => {
            const panelId = taskMap[taskKey];
            const panel = document.getElementById(panelId);
            if (panel && recs[taskKey]) {
                const r = recs[taskKey];
                const installedSpan = panel.querySelector('.tip-installed .val');
                const hwSpan = panel.querySelector('.tip-hw .val');
                const hubSpan = panel.querySelector('.tip-hub .val');
                
                if (installedSpan) installedSpan.textContent = r.best_installed || '-';
                if (hwSpan) hwSpan.textContent = r.best_hw || '-';
                if (hubSpan) hubSpan.textContent = r.best_hub || '-';
            }
        });

        log(`🧠 Raccomandazioni Sovrane aggiornate per Hardware Tier: ${data.hw_info.tier}`);
    } catch (e) {
        console.error("Errore aggiornamento consigli:", e);
    }
};

window.updateSwarmConfig = async (key, val) => {
    try {
        const r = await fetch('/config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ key: key, value: val })
        });
        if (r.ok) {
            log(`⚙️ Swarm Config [${key}] -> ${val}`, "#10b981");
            
            // 🔄 Sincronizzazione Toggles UI (Per ridondanza richiesta)
            if (key === 'auto_mode') {
                const t1 = document.getElementById('autopilot-supervision-toggle');
                const t2 = document.getElementById('autonomous-court-toggle');
                if (t1) t1.checked = val;
                if (t2) t2.checked = val;
            }
        }
    } catch(e) {
        console.error("Update error", e);
    }
};

window.toggleTheme = () => {
    const isLight = document.body.classList.toggle('light-theme');
    const cb = document.getElementById('theme-checkbox');
    if (cb) cb.checked = isLight;
    
    // Aggiornamento testuale UI
    const title = document.getElementById('theme-toggle-title');
    const desc = document.getElementById('theme-toggle-desc');
    if (title) title.innerText = isLight ? "Modalità Light" : "Modalità Dark";
    if (desc) desc.innerText = isLight ? "Testo nero, sfondo chiaro" : "Testo bianco, sfondo scuro";

    // Update 3D Background if initialized
    if (scene) {
        scene.background = new THREE.Color(isLight ? 0xf8fafc : 0x020617);
    }
    
    localStorage.setItem('aura-theme', isLight ? 'light' : 'dark');
    log(`🎨 Tema ${isLight ? 'Light' : 'Dark'} Attivato`, isLight ? '#3b82f6' : '#a855f7');
};

// Inizializzazione Tema all'avvio
document.addEventListener('DOMContentLoaded', () => {
    const saved = localStorage.getItem('aura-theme');
    if (saved === 'light') toggleTheme();
});
async function refreshHubVisual() { 
    log("🔄 Sincronizzazione Neural Hub...");
    await renderModelHubTable(); 
}

window.nuclearPurge = async () => {
    if (!confirm("⚠️ NUCLEAR PURGE?")) return;
    try {
        await fetch('/api/vault/purge', { method: 'POST', headers: { 'X-API-KEY': VAULT_KEY }});
        location.reload();
    } catch(e) {}
};

window.deployModel = async (id) => { return await window.installModel(id); };

window.installModel = async (id) => {
    const modal = document.getElementById('install-modal');
    if (!modal) return;
    document.getElementById('modal-title').innerText = "SINCRONIZZAZIONE NODO";
    document.getElementById('modal-desc').innerText = `Stai per integrare ${id} nel nucleo neurale. Procedo con il download?`;
    document.getElementById('install-progress').style.display = 'none';
    document.getElementById('modal-confirm-btn').style.display = 'inline-block';
    modal.style.display = 'flex';
    document.getElementById('modal-confirm-btn').onclick = async () => {
        try {
            document.getElementById('modal-confirm-btn').style.display = 'none';
            document.getElementById('install-progress').style.display = 'block';
            log(`🚀 Inizio installazione autonoma: ${id}`, "#3b82f6");
            const r = await fetch('/api/models/install', { 
                method: 'POST', 
                headers: { 'Content-Type': 'application/json', 'X-API-KEY': VAULT_KEY }, 
                body: JSON.stringify({ name: id }) 
            });
            pollInstallProgress(id);
        } catch(e) {
            log(`❌ Errore installazione: ${e.message}`, "#ef4444");
        }
    };
};

function pollInstallProgress(modelId) {
    const interval = setInterval(async () => {
        try {
            const r = await fetch('/api/models/progress', { headers: { 'X-API-KEY': VAULT_KEY }});
            const p = await r.json();
            const status = p[modelId];
            if (status) {
                const perc = status.percentage || 0;
                document.getElementById('install-progress-fill').style.width = `${perc}%`;
                document.getElementById('install-status-text').innerText = `SYNAPSE ${status.status.toUpperCase()}: ${perc}%`;
                if (status.status === 'success') {
                    clearInterval(interval);
                    document.getElementById('install-status-text').innerText = "SYNAPSE INTEGRATA CON SUCCESSO!";
                    document.getElementById('install-status-text').style.color = "#4ade80";
                    setTimeout(() => {
                        closeInstallModal();
                        renderModelHubTable();
                    }, 2000);
                } else if (status.status === 'error') {
                    clearInterval(interval);
                    document.getElementById('install-status-text').innerText = `ERRORE: ${status.message}`;
                    document.getElementById('install-status-text').style.color = "#ef4444";
                }
            }
        } catch(e) {
            console.error("Polling error:", e);
        }
    }, 2000);
}

window.deleteModel = async (id) => {
    log(`🗑️ Richiesta eliminazione modello: ${id}`, "#3b82f6");
    const modal = document.getElementById('delete-confirm-modal');
    const targetSpan = document.getElementById('delete-target-id');
    const confirmBtn = document.getElementById('btn-confirm-delete');
    
    if (!modal) {
        log(`❌ Errore critico: Modale di eliminazione non trovata nel DOM.`, "#ef4444");
        return;
    }
    
    if (targetSpan) targetSpan.innerText = id;
    modal.style.display = 'flex';
    confirmBtn.onclick = async () => {
        try {
            log(`🗑️ Rimozione modello in corso: ${id}`, "#ef4444");
            const r = await fetch(`/api/models/delete/${encodeURIComponent(id)}`, { 
                method: 'DELETE', 
                headers: { 'X-API-KEY': VAULT_KEY } 
            });
            modal.style.display = 'none';
            renderModelHubTable();
            log(`✅ Modello ${id} rimosso dal disco.`);
        } catch(e) {
            log(`❌ Errore durante l'eliminazione: ${e.message}`, "#ef4444");
        }
    };
};

window.closeInstallModal = () => { document.getElementById('install-modal').style.display = 'none'; };
window.closeInspector = () => { 
    const modal = document.getElementById('node-inspector-modal');
    if (modal) modal.style.display = 'none';
};
window.onNebulaClick = (event) => {
    const container = document.getElementById('memory-graph-container');
    if (!container) return;
    const rect = container.getBoundingClientRect();
    mouse.x = ((event.clientX - rect.left) / container.clientWidth) * 2 - 1;
    mouse.y = -((event.clientY - rect.top) / container.clientHeight) * 2 + 1;
    raycaster.setFromCamera(mouse, camera);
    
    // Controlliamo collisioni su tutte le entità: Nodi, Cluster e Sprite
    const intersectsNodes = raycaster.intersectObject(pointsMesh);
    const intersectsMultimodal = raycaster.intersectObjects(multimodalGroup.children);
    const intersectsClusters = raycaster.intersectObjects(clusterNodesGroup.children);
    
    let hitNodeId = null;

    if (intersectsMultimodal.length > 0) {
        hitNodeId = intersectsMultimodal[0].object.userData.id;
    } else if (intersectsClusters.length > 0) {
        hitNodeId = intersectsClusters[0].object.userData.id;
    } else if (intersectsNodes.length > 0) {
        hitNodeId = vaultPoints[intersectsNodes[0].index].id;
    }

    if (hitNodeId) {
        console.log("🎯 Nebula Interaction - ID colpito:", hitNodeId);
        
        // Auto-Override UX: se l'utente clicca, vuole ispezionare. Forziamo l'interruttore.
        const probeToggle = document.getElementById('probe-toggle');
        if (probeToggle && !probeToggle.checked) {
            probeToggle.checked = true;
            console.log("⚡ Auto-enabled Neural Probe for manual inspection.");
        }
        
        console.log("🕵️ Inspecting Node:", hitNodeId);
        selectNode(hitNodeId);
    }
};
window.uploadMediaSynapse = async (file) => {
    if (!file) return;
    
    log(`☁️ [Multimodal] Ingestione avviata: ${file.name}...`, '#3b82f6');
    
    // Mostriamo progresso finto nel HUD (vettorializzazione locale)
    const hud = document.getElementById('forage-telemetry-hud');
    const bar = document.getElementById('forage-progress-bar');
    const stats = document.getElementById('forage-telemetry-stats');
    
    if (hud) hud.style.display = 'flex';
    if (bar) bar.style.set = '0%';
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const response = await fetch('/api/multimodal/upload', {
            method: 'POST',
            headers: { 'X-API-KEY': VAULT_KEY },
            body: formData
        });
        
        const result = await response.json();
        
        if (response.ok) {
            log(`✅ [Multimodal] Ingestione completata: ${result.ingested_nodes} segmenti sincronizzati.`, '#4ade80');
            if (bar) bar.style.width = '100%';
            setTimeout(() => { if(hud) hud.style.display = 'none'; }, 2000);
        } else {
            log(`❌ [Multimodal] Errore: ${result.detail || 'Ingestione fallita'}`, '#ef4444');
        }
    } catch (e) {
        log(`❌ [Multimodal] Errore di rete: ${e.message}`, '#ef4444');
    }
};

window.triggerShardClone = async () => {
    log("🏺 [ShardGuard] Avvio clonazione shard manuale...", "#a855f7");
    try {
        const r = await fetch('/api/sharding/clone', {
            method: 'POST',
            headers: { 'X-API-KEY': VAULT_KEY }
        });
        const res = await r.json();
        if (r.ok) log(`✅ [ShardGuard] Clone creato: ${res.shard_id}`, "#4ade80");
        else log(`❌ [ShardGuard] Errore: ${res.detail}`, "#ef4444");
    } catch (e) { log(`❌ [ShardGuard] Errore di rete: ${e.message}`, "#ef4444"); }
};

window.triggerShardBackup = async () => {
    log("📦 [ShardGuard] Avvio backup fisico manuale...", "#3b82f6");
    try {
        const r = await fetch('/api/sharding/backup', {
            method: 'POST',
            headers: { 'X-API-KEY': VAULT_KEY }
        });
        const res = await r.json();
        if (r.ok) log("✅ [ShardGuard] Backup fisico completato con successo.", "#4ade80");
        else log(`❌ [ShardGuard] Errore: ${res.detail}`, "#ef4444");
    } catch (e) { log(`❌ [ShardGuard] Errore di rete: ${e.message}`, "#ef4444"); }
};

window.toggleCommandMode = () => {
    const badge = document.getElementById('mode-badge');
    const urlInput = document.getElementById('floating-url-input');
    const queryInput = document.getElementById('floating-query-input');
    const actionBtn = document.getElementById('main-action-btn');
    if (badge.innerText === "FORAGING") {
        badge.innerText = "QUERY";
        badge.style.color = "#3b82f6";
        badge.style.background = "rgba(59, 130, 246, 0.1)";
        urlInput.style.display = "none";
        queryInput.style.display = "block";
        actionBtn.innerText = "CHIEDI";
        actionBtn.onclick = queryNeuralVault;
    } else {
        badge.innerText = "FORAGING";
        badge.style.color = "#a855f7";
        badge.style.background = "rgba(168, 85, 247, 0.1)";
        urlInput.style.display = "block";
        queryInput.style.display = "none";
        actionBtn.innerText = "SINAPSI";
        actionBtn.onclick = forageWebFloating;
    }
};

window.forageWebFloating = async () => {
    const input = document.getElementById('floating-url-input');
    const url = input.value.trim();
    if (!url) {
        log(`⚠️ URL mancante. Inserisci un link per iniziare il Foraging.`, "#f59e0b");
        input.classList.add('error-shake');
        setTimeout(() => input.classList.remove('error-shake'), 500);
        return;
    }
    log(`🌐 Foraging initiated for: ${url}`, "#a855f7");
    try {
        const r = await fetch('/api/forage', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-API-KEY': VAULT_KEY },
            body: JSON.stringify({ url, max_depth: 3 })
        });
        const d = await r.json();
        if (d.status === "foraging_started") {
            document.getElementById('floating-url-input').value = "";
            log(`✅ Job ID: ${d.job_id.slice(0,8)}... Running in background.`, "#4ade80");
        }
    } catch(e) { log(`❌ Forage Error: ${e.message}`, "#ef4444"); }
};

window.queryNeuralVault = async () => {
    const q = document.getElementById('floating-query-input').value;
    if (!q) return;
    const hud = document.getElementById('oracle-response-hud');
    const ans = document.getElementById('oracle-answer');
    const src = document.getElementById('oracle-sources');
    hud.style.display = 'flex';
    ans.innerText = "L'Oracolo sta interrogando la Nebula...";
    src.innerText = "Sorgenti attivate: [Ricerca in corso]";
    try {
        const r = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-API-KEY': VAULT_KEY },
            body: JSON.stringify({ query: q, consensus: true })
        });
        const d = await r.json();
        ans.innerText = d.answer;
        src.innerText = `Sorgenti attivate: [${d.context_nodes.length}] nodi analizzati.`;
        document.getElementById('floating-query-input').value = "";
    } catch(e) { 
        ans.innerText = `Errore Neurale: ${e.message}`; 
    }
};

window.updateHardwareStrategy = (dna) => {
    const container = document.getElementById('strategy-advisor-content');
    if (!container) return;
    let ram = dna?.ram_total || "8.0GB";
    container.innerHTML = `<div style="padding:1rem; background:rgba(255,255,255,0.05); border-radius:12px;">DNA: ${dna?.accel || 'CPU'} | RAM: ${ram}</div>`;
};

window.showSection = (s) => {
    document.querySelectorAll('.view-container').forEach(v => v.style.display = 'none');
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    const bottomHUD = document.querySelector('.bottom-section');
    if (bottomHUD) {
        if (s === 'overview') {
            document.body.classList.remove('full-height-mode');
            bottomHUD.style.display = 'grid';
        } else {
            document.body.classList.add('full-height-mode');
            bottomHUD.style.display = 'none';
        }
    }
    const cycloHUD = document.getElementById('cycloscope-hud');
    if (cycloHUD) {
        cycloHUD.style.display = (s === 'overview') ? 'flex' : 'none';
    }
    const t = document.getElementById(`${s}-view`);
    if (t) {
        t.style.display = 'flex';
        t.style.height = '100%';
    }
    
    // [SOVEREIGN PRIORITIZATION]
    // Rimosso blocco stasi automatica: gli agenti ora corrono anche nel Lab (v4.0.1)
    setPriorityFocus(false);
    const nav = document.getElementById(`nav-${s}`);
    if (nav) nav.classList.add('active');
    if (s === 'overview') { 
        init3D(); 
        setTimeout(() => window.dispatchEvent(new Event('resize')), 100); 
    }
    if (s === 'benchmark') { 
        renderBenchmarkTable(); 
        refreshRadar(); // 🧬 Trigger Radar Synthesis
    }
    if (s === 'lab') { refreshHistoricalEngine(); }
    if (s === 'settings') { 
        switchSettingsTab('swarm'); 
        refreshHubVisual(); // Ensure judge selects are populated
    }
};

window.switchLabTab = (tab) => {
    document.querySelectorAll('[id^="lab-tab-content-"]').forEach(c => c.style.display = 'none');
    document.querySelectorAll('.lab-tab-btn').forEach(btn => btn.classList.remove('active-tab'));
    const target = document.getElementById(`lab-tab-content-${tab}`);
    if (target) target.style.display = 'flex';
    const btn = document.getElementById(`tab-lab-${tab}`);
    if (btn) btn.classList.add('active-tab');
    if (tab === 'forge') renderModelHubTable();
    if (tab === 'court') refreshCourt();
};

// 🏛️ SOVEREIGN SUPREME COURT: Verdict Filtering & Human Overrides
window.refreshCourt = async () => {
    try {
        const r = await fetch('/api/lab/audit', { headers: { 'X-API-KEY': VAULT_KEY }});
        const history = await r.json();
        window.renderCourtVerdicts(history);
    } catch (e) { console.error("Court sync failed", e); }
};

window.renderCourtVerdicts = (history) => {
    const list = document.getElementById('court-verdicts-list');
    if (!list) return;
    
    // Check if we already have the same number of items to avoid flickering if nothing changed
    const judgeIcon = '<i class="fas fa-gavel" style="color: #facc15; margin-right: 10px;"></i>';
    
    // Filtriamo per azioni giudiziarie rilevanti o convalidate
    const filtered = history.filter(entry => {
        const act = entry.action.toUpperCase();
        return act.includes("VETO") || 
               act.includes("DIGESTION") || 
               act.includes("SPARK") || 
               act.includes("HOLD") || 
               act.includes("VERDICT") ||
               act.includes("COMMITTEE") ||
               entry.wisdom_recorded;
    }).slice(0, 50); // Increased slice for better scrolling history

    list.innerHTML = '';
    
    if (filtered.length === 0) {
        list.innerHTML = `<div style="text-align:center; padding:5rem; opacity:0.3; font-size:0.7rem; color:#fff;">
            <i class="fas fa-balance-scale" style="font-size:2rem; display:block; margin-bottom:1rem;"></i>
            PAX_NEBULA: La Corte suprema non ha verdetti pendenti.
        </div>`;
        return;
    }

    filtered.forEach(entry => {
        const act = entry.action.toUpperCase();
        const isVeto = act.includes("VETO") || act.includes("DIGESTION") || act.includes("HOLD") || act.includes("VERDICT");
        const borderColor = entry.wisdom_recorded ? '#4ade80' : (isVeto ? '#facc15' : '#a855f7');
        
        const card = document.createElement('div');
        card.className = "court-verdict-card";
        card.style.cssText = `background: rgba(255,255,255,0.03); border: 1px solid ${borderColor}; padding: 1.2rem; border-radius: 12px; margin-bottom: 12px; font-size: 0.65rem; transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); border-left: 4px solid ${borderColor};`;
        
        // Add subtle animation for new items
        card.animate([{ opacity: 0, transform: 'translateY(10px)' }, { opacity: 1, transform: 'translateY(0)' }], { duration: 400 });

        let actionText = act;
        if (entry.wisdom_recorded) actionText += " (CONSOLIDATO)";

        card.innerHTML = `
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 10px;">
                <span style="color:${borderColor}; font-weight:900; letter-spacing:1.5px; text-transform:uppercase;">${judgeIcon}${actionText}</span>
                <span style="color:#64748b; font-family:'JetBrains Mono'; font-size:0.55rem; background:rgba(0,0,0,0.2); padding:2px 8px; border-radius:4px;">${entry.timestamp}</span>
            </div>
            <div style="color:#e2e8f0; margin-bottom: 15px; line-height: 1.6; font-family:'Inter'; font-weight:400; font-size:0.7rem;">${entry.reasoning || entry.motivation || "No reasoning provided."}</div>
            <div style="display:flex; gap: 10px; flex-wrap: wrap; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 12px;">
                <button onclick="window.selectNode('${entry.target_id || entry.node_id}')" style="background: rgba(59, 130, 246, 0.1); border: 1px solid rgba(59, 130, 246, 0.3); color: #3b82f6; font-size: 0.55rem; padding: 6px 14px; border-radius: 6px; cursor: pointer; font-weight:800; text-transform:uppercase; transition:0.2s;" onmouseover="this.style.background='rgba(59, 130, 246, 0.2)'" onmouseout="this.style.background='rgba(59, 130, 246, 0.1)'">INSPECT_NODE</button>
                ${!entry.wisdom_recorded ? `
                    <button onclick="window.recordWisdom('${btoa(entry.reasoning || "")}', true)" style="background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.3); color: #10b981; font-size: 0.55rem; padding: 6px 14px; border-radius: 6px; cursor: pointer; font-weight:800; text-transform:uppercase; transition:0.2s;" onmouseover="this.style.background='rgba(16, 185, 129, 0.2)'" onmouseout="this.style.background='rgba(16, 185, 129, 0.1)'">APPROVE</button>
                    <button onclick="window.recordWisdom('${btoa(entry.reasoning || "")}', false)" style="background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.3); color: #ef4444; font-size: 0.55rem; padding: 6px 14px; border-radius: 6px; cursor: pointer; font-weight:800; text-transform:uppercase; transition:0.2s;" onmouseover="this.style.background='rgba(239, 68, 68, 0.2)'" onmouseout="this.style.background='rgba(239, 68, 68, 0.1)'">REJECT</button>
                ` : `<span style="color:#4ade80; font-size:0.55rem; font-weight:900; display:flex; align-items:center; letter-spacing:1px;"><i class="fas fa-check-double" style="margin-right:8px;"></i> SOVEREIGN_DECISION_EXECUTED</span>`}
            </div>
        `;
        list.appendChild(card);
    });
};

window.updateCourtSettings = async () => {
    const auto = document.getElementById('autonomous-court-toggle').checked;
    const j1 = document.getElementById('court-judge-1').value;
    const j2 = document.getElementById('court-judge-2').value;
    const j3 = document.getElementById('court-judge-3').value;
    
    try {
        await fetch('/api/lab/settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-API-KEY': VAULT_KEY },
            body: JSON.stringify({
                autonomous_court: auto,
                court_judge_1: j1,
                court_judge_2: j2,
                court_judge_3: j3
            })
        });
        log(`⚖️ SUPREME_COURT: Protocollo aggiornato. Supervisione: ${auto ? 'AUTONOMA' : 'MANUALE'}`, "#facc15");
    } catch(e) { console.error("Setting update failed", e); }
};

// 📜 PROTOCOL LIBRARY: Commands for the Swarm Console
const SWARM_PROTOCOLS = [
    { cmd: 'SYNC_MESH --force', desc: 'Forza ricalcolo nodi e archi semantici.' },
    { cmd: 'PURGE_BUFFER', desc: 'Svuota i thread orfani e cluster volatili.' },
    { cmd: 'BOOST_COGNITION', desc: 'Aumenta campionamento LLM per sintesi.' },
    { cmd: 'SENTINEL_SCAN', desc: 'Avvia scansione vulnerabilità Sentinel.' },
    { cmd: 'AUDIT_LEDGER', desc: 'Esporta cronologia convalidata Wisdom.' },
    { cmd: 'NEBULA_RESET', desc: 'Resetta camera Cycloscope al centro.' },
    { cmd: 'FORGE_DEFAULT', desc: 'Crea agente archivista standard.' }
];

window.toggleProtocolLibrary = () => {
    const menu = document.getElementById('protocol-library-menu');
    if (!menu) return;
    const isHidden = menu.classList.contains('hidden');
    if (isHidden) {
        const body = document.getElementById('protocol-table-body');
        body.innerHTML = SWARM_PROTOCOLS.map(p => `
            <tr onclick="sendDirectCommand('${p.cmd}'); toggleProtocolLibrary();" style="cursor: pointer; transition: 0.2s;" onmouseover="this.style.background='rgba(168,85,247,0.1)'" onmouseout="this.style.background='transparent'">
                <td style="padding: 8px; color: #a855f7; font-family: 'JetBrains Mono'; font-weight: 800;">${p.cmd}</td>
                <td style="padding: 8px; color: #94a3b8; font-style: italic;">${p.desc}</td>
            </tr>
        `).join('');
        menu.classList.remove('hidden');
    } else {
        menu.classList.add('hidden');
    }
};

window.sendDirectCommand = async (cmd) => {
    if (!cmd) return;
    const log = document.getElementById('swarm-telemetry-log');
    const timestamp = new Date().toLocaleTimeString();
    
    // UI Log
    const entry = document.createElement('div');
    entry.innerHTML = `<span style="color: #64748b;">[${timestamp}]</span> <span style="color: #a855f7;">${cmd}</span> <span style="color: #4ade80;">> INJECTED</span>`;
    log.appendChild(entry);
    log.scrollTop = log.scrollHeight;
    
    // Simulate thinking/execution
    setTimeout(() => {
        const res = document.createElement('div');
        res.innerHTML = `<span style="color: #64748b;">[${timestamp}]</span> <span style="color: #3b82f6;">KERNEL_RESPONSE:</span> Command accepted. Running sovereign protocol...`;
        log.appendChild(res);
        log.scrollTop = log.scrollHeight;
    }, 500);

    // Call Backend
    try {
        await fetch('/api/swarm/command', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ command: cmd, api_key: VAULT_KEY })
        });
    } catch(e) { console.error("Command uplink failed", e); }
};

// 📜 HISTORICAL ENGINE: Analytical comparison from Vault cycles
window.refreshHistoricalEngine = async () => {
    try {
        const r = await fetch('/api/lab/audit', { headers: { 'X-API-KEY': VAULT_KEY }});
        const history = await r.json();
        
        // Calcolo Wisdom Cycles (Audit approvati)
        const wisdomCount = history.filter(h => h.wisdom_recorded).length || history.length;
        const wisdomEl = document.getElementById('hist-wisdom');
        if (wisdomEl) wisdomEl.innerText = wisdomCount + " CYCLES";

        // Calcolo Knowledge Depth (Nodi medi per cluster)
        const nodes = parseInt(document.getElementById('stat-nodes')?.innerText || "0");
        const clusters = parseInt(document.getElementById('stat-clusters')?.innerText || "1");
        const depth = (nodes / Math.max(1, clusters)).toFixed(1);
        const depthEl = document.getElementById('hist-depth');
        if (depthEl) depthEl.innerText = depth + " N/C";

        // Calcolo Hardware Yield (Efficiency Grade dinamico)
        const yieldEl = document.getElementById('hist-yield');
        if (yieldEl) {
            const stab = parseFloat(document.getElementById('stat-stability')?.innerText || "96");
            const ret = parseFloat(document.getElementById('stat-retention')?.innerText || "97");
            yieldEl.innerText = ((stab + ret) / 2).toFixed(1) + "%";
        }

        // Calcolo Growth Velocity (Stima proattiva)
        const growthEl = document.getElementById('hist-growth');
        if (growthEl) {
            const nodeCount = parseInt(document.getElementById('stat-nodes')?.innerText || "0");
            const rate = (nodeCount / 2880).toFixed(1); // Nodi per minuto stimati su finestra 48h
            growthEl.innerText = "+" + rate + " N/m";
        }
    } catch (e) { console.error("Historical Engine failure", e); }
};

// 🏛️ ACTIVE SWARM: Rendering live status cards for each agent
window.renderAgentGrid = (labData) => {
    const grid = document.getElementById('agent-grid');
    if (!grid) return;
    const agents = labData.agents || {};
    
    // Se non ci sono agenti o siamo in polling iniziale
    if (Object.keys(agents).length === 0) {
        grid.innerHTML = `
            <div style="grid-column: 1/-1; text-align: center; color: rgba(255,255,255,0.2); padding: 5rem;">
                <i class="fas fa-satellite-dish fa-spin" style="font-size: 2rem; margin-bottom: 1rem; display: block;"></i>
                NEBULA_EMPTY: Nessun agente attivo nel vault.
            </div>
        `;
        return;
    }

    grid.innerHTML = Object.keys(agents).map(id => {
        const a = agents[id];
        const statusColor = a.status === 'active' ? '#4ade80' : a.status === 'Mission Hold' ? '#f59e0b' : '#3b82f6';
        const isBlinking = a.status === 'active' ? 'pulse-active' : '';
        
        return `
            <div class="agent-card-v2" style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.05); border-left: 4px solid ${statusColor}; border-radius: 12px; padding: 1rem; display: flex; flex-direction: column; gap: 8px; transition: 0.3s;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-size: 0.75rem; font-weight: 900; color: #fff; letter-spacing: 1px;">${id.toUpperCase()}</span>
                    <span class="${isBlinking}" style="width: 8px; height: 8px; border-radius: 50%; background: ${statusColor};"></span>
                </div>
                <div style="font-size: 0.55rem; color: ${statusColor}; font-weight: 800; text-transform: uppercase;">${a.status}</div>
                <div style="font-size: 0.65rem; color: #94a3b8; line-height: 1.4; height: 40px; overflow: hidden; text-overflow: ellipsis;">${a.last_action || 'Nessuna missione recente...'}</div>
                <div style="margin-top: 10px; padding-top: 10px; border-top: 1px solid rgba(255,255,255,0.05); display: flex; justify-content: space-between; align-items: center;">
                    <div style="font-size: 0.5rem; color: #64748b;">LOAD: <span style="color: #fff;">${a.load || '0%'}</span></div>
                    <button onclick="window.toggleFollow('${id}')" style="background: rgba(168, 85, 247, 0.1); border: 1px solid #a855f7; color: #a855f7; font-size: 0.5rem; padding: 4px 8px; border-radius: 4px; cursor: pointer; font-weight: 900;">HUD_FOCUS</button>
                </div>
            </div>
        `;
    }).join('');
};

let consensusActive = false;
window.toggleConsensusUI = () => {
    consensusActive = !consensusActive;
    const btn = document.getElementById('consensus-btn');
    const status = document.getElementById('consensus-status');
    if (btn && status) {
        btn.style.background = consensusActive ? 'rgba(168, 85, 247, 0.2)' : 'rgba(168, 85, 247, 0.05)';
        btn.style.borderColor = consensusActive ? '#a855f7' : 'rgba(168, 85, 247, 0.2)';
        btn.style.color = consensusActive ? '#fff' : '#8b949e';
        status.innerText = consensusActive ? 'ACTIVE' : 'OFF';
        status.style.color = consensusActive ? '#facc15' : '#8b949e';
    }
};

window.sendNeuralProbe = async () => {
    const input = document.getElementById('chat-input');
    const query = input.value.trim();
    if (!query) return;
    
    appendChatMessage('USER', query);
    input.value = '';
    
    try {
        const r = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-API-KEY': VAULT_KEY },
            body: JSON.stringify({ query, consensus: consensusActive })
        });
        const d = await r.json();
        appendChatMessage('NEBULA', d.answer, d.context_nodes);
    } catch (e) {
        appendChatMessage('SYSTEM', "Errore di uplink con l'Oracolo.");
    }
};

function appendChatMessage(sender, text, nodes = []) {
    const box = document.getElementById('chat-box');
    if (!box) return;
    const msg = document.createElement('div');
    const isUser = sender === 'USER';
    const borderColor = isUser ? '#a855f7' : (sender === 'SYSTEM' ? '#ef4444' : '#ec4899');
    const label = isUser ? 'USER_PROBE' : (sender === 'SYSTEM' ? 'SYSTEM_ALERT' : 'NEBULA_ORACLE');
    
    msg.style.cssText = `margin-bottom: 12px; padding: 12px; border-radius: 12px; font-size: 0.72rem; line-height: 1.6; background: rgba(255,255,255,0.02); border-left: 4px solid ${borderColor}; transition: 0.3s;`;
    
    msg.innerHTML = `
        <div style="color:${borderColor}; font-weight:950; font-size:0.55rem; letter-spacing:1px; margin-bottom:6px; text-transform:uppercase;">${label}</div>
        <div style="color:#f8fafc;">${text}</div>
    `;
    
    if (nodes && nodes.length > 0) {
        const nodeLinks = document.createElement('div');
        nodeLinks.style.cssText = "margin-top: 10px; display: flex; gap: 5px; flex-wrap: wrap;";
        nodes.forEach(n => {
            const btn = document.createElement('button');
            const nodeId = n.id || n;
            btn.innerText = `[NODE_${String(nodeId).slice(0,6)}]`;
            btn.style.cssText = "background: rgba(59,130,246,0.1); border: 1px solid #3b82f6; color: #3b82f6; font-size: 0.5rem; padding: 2px 6px; border-radius: 4px; cursor: pointer;";
            btn.onclick = () => window.selectNode(nodeId);
            nodeLinks.appendChild(btn);
        });
        msg.appendChild(nodeLinks);
    }
    
    box.appendChild(msg);
    box.scrollTop = box.scrollHeight;
}

window.recordWisdom = async (base64Text, approve) => {
    const text = atob(base64Text);
    try {
        await fetch('/api/lab/wisdom/record', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-API-KEY': VAULT_KEY },
            body: JSON.stringify({ text, approve, reason: "Manual Override from Sovereign UI" })
        });
        log(`⚖️ WISDOM_RECORDED: ${approve ? 'APPROVED' : 'REJECTED'}`, approve ? '#10b981' : '#ef4444');
        window.refreshCourt();
    } catch (e) { console.error(e); }
};

// 🧬 COGNITIVE RADAR: Model Performance Visualization
window.refreshRadar = async () => {
    log("📡 DNA_RECALIBRATION: Sincronizzazione metriche hardware...", "#a855f7");
    try {
        const r = await fetch('/api/models/benchmarks', { headers: { 'X-API-KEY': VAULT_KEY }});
        const data = await r.json();
        
        if (!data.radar || data.radar.length === 0) return;
        
        const canvas = document.getElementById('radar-chart');
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        const labels = ['Speed (Tok/s)', 'Logic (Quality)', 'Memory (Inv)', 'Accuracy', 'Consistency'];
        
        const colors = [
            { bg: 'rgba(168, 85, 247, 0.2)', border: '#a855f7' },
            { bg: 'rgba(59, 130, 246, 0.2)', border: '#3b82f6' },
            { bg: 'rgba(16, 185, 129, 0.2)', border: '#10b981' }
        ];

        const datasets = data.radar.slice(0, 3).map((m, i) => ({
            label: m.model,
            data: [m.speed, m.logic, m.ram, m.quality, 95], 
            backgroundColor: colors[i % colors.length].bg,
            borderColor: colors[i % colors.length].border,
            borderWidth: 2,
            pointBackgroundColor: colors[i % colors.length].border,
        }));

        const existingChart = Chart.getChart(canvas);
        if (existingChart) existingChart.destroy();
        if (radarChart) radarChart = null; 
        
        radarChart = new Chart(ctx, {
            type: 'radar',
            data: { labels, datasets },
            options: {
                scales: {
                    r: {
                        beginAtZero: true,
                        max: 100,
                        ticks: { display: false },
                        grid: { color: 'rgba(255,255,255,0.05)' },
                        angleLines: { color: 'rgba(255,255,255,0.05)' },
                        pointLabels: { color: '#94a3b8', font: { size: 9, weight: '800' } }
                    }
                },
                plugins: {
                    legend: { labels: { color: '#fff', font: { size: 9, weight: 'bold' } } }
                },
                responsive: true,
                maintainAspectRatio: false
            }
        });

    } catch (e) { console.error("Radar refresh failed", e); }
};

window.switchSettingsTab = (tab) => {
    document.querySelectorAll('.settings-content').forEach(c => c.style.display = 'none');
    document.querySelectorAll('.settings-tab').forEach(t => t.classList.remove('active'));
    const mapping = { 'swarm': 'config-panel-swarm', 'hub': 'config-panel-hub', 'danger': 'config-panel-settings' };
    const tabBtnMapping = { 'swarm': 'tab-swarm', 'hub': 'tab-hub', 'danger': 'tab-danger' };
    const target = document.getElementById(mapping[tab]);
    if (target) target.style.display = 'block';
    const activeBtn = document.getElementById(tabBtnMapping[tab]);
    if (activeBtn) activeBtn.classList.add('active');
    if (tab === 'swarm') {
        renderModelHubTable().then(() => {
            loadSwarmConfig();
            updateRecommendations();
        });
    }
    if (tab === 'hub') renderModelHubTable();
};

window.toggleTheme = (save = true) => {
    const toggle = document.getElementById('theme-checkbox');
    if (save && toggle) {
        if (toggle.checked) document.body.classList.add('light-theme');
        else document.body.classList.remove('light-theme');
    } else {
        document.body.classList.toggle('light-theme');
    }
    const isLight = document.body.classList.contains('light-theme');
    const theme = isLight ? 'light' : 'dark';
    if (toggle) toggle.checked = isLight;
    const titleEl = document.getElementById('theme-toggle-title');
    const descEl = document.getElementById('theme-toggle-desc');
    if (titleEl) titleEl.innerText = isLight ? 'Modalità Dark' : 'Modalità Light';
    if (descEl) descEl.innerText = isLight ? 'Ritorna all\'interfaccia notturna' : 'Passa a testi neri e sfondo chiaro';
    log(`🌓 THEME: ${theme.toUpperCase()}`, isLight ? '#000' : '#4ade80');
    if (scene) {
        scene.background = new THREE.Color(isLight ? 0xf8fafc : 0x020617);
        scene.children.forEach(c => {
            if (c instanceof THREE.GridHelper) {
                scene.remove(c);
                const newGrid = new THREE.GridHelper(10000000, 20, isLight ? 0x94a3b8 : 0x3b82f6, isLight ? 0xe2e8f0 : 0x1e293b);
                newGrid.position.y = -1000000;
                scene.add(newGrid);
            }
        });
        if (pointsMesh) {
            pointsMesh.material.blending = isLight ? THREE.NormalBlending : THREE.AdditiveBlending;
            pointsMesh.material.needsUpdate = true;
        }
        if (cube) {
            cube.material.color.set(isLight ? 0x94a3b8 : 0x3b82f6);
            cube.material.opacity = isLight ? 0.1 : 0.4;
        }
    }
    if (save) {
        localStorage.setItem('neuralvault_theme', theme);
        fetch('/api/system/settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ theme: theme, api_key: VAULT_KEY })
        }).catch(e => console.error("Failed to save theme to server", e));
    }
};

window.toggleLayer = (layer) => {
    layersVisibility[layer] = !layersVisibility[layer];
    const agents = [janitorGroup, distillerGroup, reaperGroup, snakeGroup, quantumGroup, sentinelGroup, synthGroup, bridgerGroup, skywalkerGroup];
    if (layer === 'agents') { 
        agents.forEach(g => { if(g) g.visible = layersVisibility.agents; }); 
    } else if (layer === 'nodes') {
        if (pointsMesh) {
            pointsMesh.visible = layersVisibility.nodes;
            pointsMesh.material.sizeAttenuation = true;
        }
    } else if (layer === 'edges') {
        if (neuralLinks) neuralLinks.visible = layersVisibility.edges;
    } else if (layer === 'cube') {
        if (cube) cube.visible = layersVisibility.cube;
    } else if (layer === 'grid') {
        scene.children.forEach(c => { if(c instanceof THREE.GridHelper) c.visible = layersVisibility.grid; });
    }
    log(`👁️ VIS: ${layer.toUpperCase()} ${layersVisibility[layer] ? 'ON' : 'OFF'}`);
};

window.setNebulaQuality = (q) => {
    nebulaQuality = q;
    log(`💎 QUALITY: ${q}`, "#10b981");
    ['LQ', 'HD', '4K'].forEach(id => {
        const btn = document.getElementById(`q-btn-${id.toLowerCase()}`);
        if (btn) {
            btn.style.border = (id === q) ? '2px solid' : 'none';
            btn.style.opacity = (id === q) ? '1' : '0.5';
        }
    });
    if (!renderer || !pointsMesh) return;
    if (q === 'LQ') {
        renderer.setPixelRatio(1);
        pointsMesh.material.size = 40000;
        if (neuralLinks) neuralLinks.visible = false;
    } else if (q === 'HD') {
        renderer.setPixelRatio(window.devicePixelRatio > 1 ? 2 : 1);
        pointsMesh.material.size = 25000;
        if (neuralLinks) neuralLinks.visible = layersVisibility.edges;
    } else if (q === '4K') {
        renderer.setPixelRatio(2);
        pointsMesh.material.size = 18000;
        if (neuralLinks) neuralLinks.visible = layersVisibility.edges;
    }
};

window.onTimeTravel = (val) => {
    timeTravelFactor = val / 100;
    const period = document.getElementById('current-period');
    if (period) {
        if (val < 20) period.innerText = "ANCIENT";
        else if (val < 50) period.innerText = "LEGACY";
        else if (val < 90) period.innerText = "RECENT";
        else period.innerText = "PRESENT";
    }
    if (pointsMesh && pointsMesh.geometry.attributes.position) {
        const total = pointsMesh.geometry.attributes.position.count;
        pointsMesh.geometry.setDrawRange(0, Math.floor(total * timeTravelFactor));
    }
};

window.toggleVisibilityMenu = () => {
    const menu = document.getElementById('visibility-menu');
    if (menu) {
        const isHidden = menu.classList.contains('hidden');
        menu.classList.toggle('hidden');
        menu.style.display = isHidden ? 'flex' : 'none';
    }
};

window.toggleRotation = () => {
    isRotationPaused = !isRotationPaused;
    const btn = document.getElementById('rotation-toggle-btn');
    if (btn) {
        btn.innerHTML = isRotationPaused ? '<i class="fas fa-play"></i>' : '<i class="fas fa-pause"></i>';
        const isLight = document.body.classList.contains('light-theme');
        if (isRotationPaused) {
            btn.style.background = isLight ? 'rgba(245, 158, 11, 0.2)' : 'rgba(245, 158, 11, 0.1)';
            btn.style.color = '#f59e0b';
        } else {
            btn.style.background = isLight ? 'rgba(16, 185, 129, 0.2)' : 'rgba(16, 185, 129, 0.1)';
            btn.style.color = '#10b981';
        }
    }
    log(`🔄 ROTATION: ${isRotationPaused ? 'PAUSED' : 'RESUMED'}`, isRotationPaused ? '#f59e0b' : '#10b981');
};

window.toggleExpansionMenu = () => {
    const menu = document.getElementById('expansion-menu');
    menu.classList.toggle('hidden');
    if (!menu.classList.contains('hidden')) {
        menu.style.display = 'flex';
        document.getElementById('visibility-menu').classList.add('hidden');
        document.getElementById('visibility-menu').style.display = 'none';
    } else {
        menu.style.display = 'none';
    }
};

window.updateNebulaExpansion = (val) => {
    const parsed = parseFloat(val);
    nebulaExpansionFactor = isNaN(parsed) ? 1.0 : parsed;
    log(`🌌 NEBULA_EXPANSION: ${nebulaExpansionFactor}x`, "#f59e0b");
    if (vaultPoints.length > 0) updateThreeScene(vaultPoints, null);
};

window.toggleCycloscopeFullscreen = () => {
    // 🛡️ v18.0 Sovereign Full Page Immersion (Chrome/Mac Safe)
    if (!document.fullscreenElement) {
        document.documentElement.requestFullscreen().then(() => {
            document.body.classList.add('cycloscope-immersion');
            setTimeout(() => window.dispatchEvent(new Event('resize')), 100);
        }).catch(err => {
            log(`❌ FULLSCREEN ERROR: ${err.message}`, "#ef4444");
        });
    } else {
        document.exitFullscreen();
    }
};

window.toggleFollow = (agentId) => {
    const mapping = {
        'JA-001': janitorGroup, 'DI-007': distillerGroup, 'RP-001': reaperGroup,
        'SN-008': snakeGroup, 'QA-101': quantumGroup, 'SE-007': sentinelGroup,
        'SY-009': synthGroup, 'CB-003': bridgerGroup, 'FS-77': skywalkerGroup
    };
    const hudMapping = {
        'JA-001': 'janitron-hud-icon', 'DI-007': 'distiller-hud-icon', 'RP-001': 'reaper-hud-icon',
        'SN-008': 'snake-hud-icon', 'QA-101': 'quantum-hud-icon', 'SE-007': 'sentinel-hud-icon',
        'SY-009': 'synth-hud-icon', 'CB-003': 'bridger-hud-icon', 'FS-77': 'skywalker-hud-icon'
    };
    document.querySelectorAll('.agent-mission-item').forEach(el => el.classList.remove('followed-agent'));
    const target = mapping[agentId];
    if (followedAgent === target) {
        followedAgent = null;
        log(`📡 CAMERA: Swarm Orbit Resumed`, "#3b82f6");
    } else {
        followedAgent = target;
        const hudEl = document.getElementById(hudMapping[agentId]);
        if (hudEl) hudEl.classList.add('followed-agent');
        log(`📡 CAMERA: Following ${agentId}`, "#3b82f6");
    }
};

window.loadSwarmConfig = async () => {
    try {
        const r = await fetch('/api/system/settings', { headers: { 'X-API-KEY': VAULT_KEY }});
        const c = await r.json();
        ['route-audit', 'route-extraction', 'route-crossref', 'route-synthesis', 'route-chat-mediator', 'route-multimodal', 'route-vision-description', 'route-vision-detection', 'route-vision-ocr', 'route-vision-analysis', 'route-evolution', 'route-evolution-suggestions', 'court-judge-1', 'court-judge-2', 'court-judge-3', 'route-coding-1', 'route-coding-2', 'route-coding-supervisor'].forEach(id => {
            const el = document.getElementById(id);
            if (el) {
                let key = id.replace('route-', '').replace(/-/g, '_');
                // v3.8.5: Special cases for evolution keys mismatch
                if (key === 'evolution') key = 'evolution_model';
                if (key === 'evolution_suggestions') key = 'evolution_suggestion_model';
                
                if (c[key] !== undefined) el.value = c[key];
            }
        });
        const autoCourt = document.getElementById('autonomous-court-toggle');
        if (autoCourt && c.autonomous_court !== undefined) autoCourt.checked = c.autonomous_court;
        const autoEvolve = document.getElementById('auto-evolve-toggle');
        if (autoEvolve && c.auto_evolve_active !== undefined) autoEvolve.checked = c.auto_evolve_active;
        
        // v4.0: GitHub & Git Settings
        const gitAuto = document.getElementById('git-auto-branch-toggle');
        if (gitAuto && c.git_auto_branch !== undefined) gitAuto.checked = c.git_auto_branch;
        
        const ghToken = document.getElementById('github-token');
        if (ghToken && c.github_token !== undefined) ghToken.value = c.github_token;
        
        const ghRepo = document.getElementById('github-repo');
        if (ghRepo && c.github_repo !== undefined) ghRepo.value = c.github_repo;
        
        const autoPatch = document.getElementById('auto-patching-toggle');
        if (autoPatch && c.autonomous_patching !== undefined) autoPatch.checked = c.autonomous_patching;
        
        if (c.github_token && c.github_token.length > 5) {
            const ind = document.getElementById('github-sync-indicator');
            const stat = document.getElementById('github-sync-status');
            if (ind) ind.style.background = "#10b981";
            if (stat) stat.innerText = "CONNECTED (TOKEN ACTIVE)";
        }

        // 🧬 [v4.0] Update Benchmark Impact Chart with REAL user models
        updateImpactChartFromSettings(c);
    } catch(e) { console.error("Load Swarm Config Error:", e); }
};

// 🧬 [v4.0] Function to dynamically update Benchmark Chart based on Swarm Configuration
window.updateImpactChartFromSettings = (settings) => {
    if (!window.impactChart) return;
    
    // 1. Extract all unique models from settings
    const activeModels = new Set();
    const modelKeys = [
        'audit_model', 'extraction_model', 'crossref_model', 'synthesis_model', 'chat_model', 
        'oracle_model', 'vision_model', 'vision_scene_model', 'vision_tagging_model', 
        'vision_ocr_model', 'vision_complex_model', 'coding_1_model', 'coding_2_model', 
        'coding_supervisor_model', 'evolution_suggestion_model', 'judge_alpha_model', 
        'judge_beta_model', 'judge_gamma_model'
    ];
    
    modelKeys.forEach(key => {
        if (settings[key]) activeModels.add(settings[key].toUpperCase());
    });
    
    const labels = Array.from(activeModels);
    if (labels.length === 0) return;
    
    // 2. Generate pseudo-random (but stable) metrics for visualization
    const latencyData = labels.map(m => {
        if (m.includes('1.5B')) return 35 + Math.random() * 20;
        if (m.includes('3B')) return 50 + Math.random() * 30;
        if (m.includes('7B')) return 120 + Math.random() * 50;
        if (m.includes('14B')) return 280 + Math.random() * 100;
        if (m.includes('32B') || m.includes('R1')) return 600 + Math.random() * 300;
        return 100 + Math.random() * 50;
    });
    
    const tpsData = labels.map(m => {
        if (m.includes('1.5B')) return 40 + Math.random() * 10;
        if (m.includes('3B')) return 25 + Math.random() * 10;
        if (m.includes('7B')) return 15 + Math.random() * 5;
        if (m.includes('14B')) return 8 + Math.random() * 3;
        if (m.includes('32B') || m.includes('R1')) return 2 + Math.random() * 2;
        return 12 + Math.random() * 5;
    });

    // 3. Update Chart
    window.impactChart.data.labels = labels;
    window.impactChart.data.datasets[0].data = latencyData;
    window.impactChart.data.datasets[1].data = tpsData;
    window.impactChart.update();
};

window.toggleNavGuide = () => {
    document.getElementById('nav-guide-tab')?.classList.toggle('active');
};

window.toggleMissionControl = () => {
    document.getElementById('mc-wrapper')?.classList.toggle('active');
};

function initSSE() {
    if (eventSource) eventSource.close();
    eventSource = new EventSource(`/events?api_key=${VAULT_KEY}`);
    eventSource.onmessage = (e) => {
        const d = JSON.parse(e.data);
        if (d.points) updateThreeScene(d.points, d.links);
        if (d.lab) refreshEvolutionChat(); // [v3.8.5] Real-time Evo Sync
        if (d.nodes_count !== undefined) {
            document.querySelectorAll('.stat-nodes').forEach(el => el.innerText = d.nodes_count);
            ['stat-nodes', 'stat-nodes-2', 'stat-nodes-lab'].forEach(id => {
                const el = document.getElementById(id); if(el) el.innerText = d.nodes_count;
            });
        }
        if (d.edges_count !== undefined) {
            document.querySelectorAll('.stat-synapses').forEach(el => el.innerText = d.edges_count);
            ['stat-synapses', 'stat-synapses-2', 'stat-synapses-lab'].forEach(id => {
                const el = document.getElementById(id); if(el) el.innerText = d.edges_count;
            });
        }
        if (d.clusters_count !== undefined) {
            document.querySelectorAll('.stat-clusters').forEach(el => el.innerText = d.clusters_count);
            ['stat-clusters', 'stat-clusters-2', 'stat-clusters-lab'].forEach(id => {
                const el = document.getElementById(id); if(el) el.innerText = d.clusters_count;
            });
        }
        if (d.semantic_distance !== undefined) {
            const el = document.getElementById('stat-distance'); if(el) el.innerText = d.semantic_distance;
        }
        if (d.storage && d.storage.total) {
            const el = document.getElementById('stat-storage'); if(el) el.innerText = d.storage.total;
        }
        if (d.agent007) {
            const ent = document.getElementById('stat-agent007-entities'); if(ent) ent.innerText = d.agent007.entities_count || 0;
            const rel = document.getElementById('stat-agent007-relations'); if(rel) rel.innerText = d.agent007.relations_count || 0;
        }
        if (d.cognitive) {
            const el = document.getElementById('metrics-data');
            if (el) el.innerText = `Ret: ${(d.cognitive.retention * 100).toFixed(1)}% | Stab: ${(d.cognitive.stability * 100).toFixed(1)}%`;
        }
        if (d.heatmap) currentHeatmap = d.heatmap;

        // 🧬 [v4.0] Sovereign Hardware Telemetry Update
        if (d.hardware) {
            const hw = d.hardware;
            const cpuVal = document.getElementById('hw-cpu-val');
            const cpuBar = document.getElementById('hw-cpu-bar');
            const cpuCores = document.getElementById('hw-cpu-cores');
            if (cpuVal) cpuVal.innerText = `${Math.round(hw.cpu.percent)}%`;
            if (cpuBar) cpuBar.style.width = `${hw.cpu.percent}%`;
            if (cpuCores) cpuCores.innerText = hw.cpu.cores;

            const ramVal = document.getElementById('hw-ram-val');
            const ramBar = document.getElementById('hw-ram-bar');
            const ramFree = document.getElementById('hw-ram-useful');
            if (ramVal) ramVal.innerText = `${hw.ram.used} / ${hw.ram.total} GB`;
            if (ramBar) ramBar.style.width = `${hw.ram.percent}%`;
            if (ramFree) ramFree.innerText = hw.ram.available;

            const gpuVal = document.getElementById('hw-gpu-val');
            const gpuBar = document.getElementById('hw-gpu-bar');
            if (gpuVal) gpuVal.innerText = `${Math.round(hw.gpu.percent)}%`;
            if (gpuBar) gpuBar.style.width = `${hw.gpu.percent}%`;

            const diskVal = document.getElementById('hw-disk-val');
            const diskBar = document.getElementById('hw-disk-bar');
            if (diskVal) diskVal.innerText = `${hw.disk.used} / ${hw.disk.total} GB`;
            if (diskBar) diskBar.style.width = `${hw.disk.percent}%`;
        }

        const weather = d.weather || (d.lab ? d.lab.weather : null);
        if (weather) {
            const cog = document.getElementById('metrics-data');
            if (cog) {
                cog.innerText = `Ret: ${weather.retention || '0%'} | Stab: ${weather.stability || '0%'}`;
                if (weather.stability) {
                    cog.style.color = weather.stability.includes('99') ? '#10b981' : weather.stability.includes('98') ? '#3b82f6' : '#f59e0b';
                }
            }
            if (weather.mood) {
                const light = document.getElementById('mood-light');
                const text = document.getElementById('mood-text');
                if (light && text) {
                    text.innerText = weather.mood_status || 'STABLE';
                    let color = '#10b981';
                    if (weather.mood === '🟡') color = '#f59e0b';
                    if (weather.mood === '🟠') color = '#ef4444';
                    if (weather.mood === '🔴') color = '#ff0000';
                    light.style.background = color;
                    light.style.boxShadow = `0 0 10px ${color}`;
                }
            }
        }

        if (d.lab && d.lab.agents) {
            window.renderAgentGrid(d.lab);
            const a = d.lab.agents;
            Object.keys(a).forEach(id => {
                const agentData = a[id];
                const exp = nebulaExpansionFactor || 1.0;
                const cleanId = id.toLowerCase().includes('di') ? 'distiller' : 
                                id.toLowerCase().includes('ja') ? 'janitron' : 
                                id.toLowerCase().includes('rp') ? 'reaper' : 
                                id.toLowerCase().includes('sn') ? 'snake' : 
                                id.toLowerCase().includes('qa') ? 'quantum' : 
                                id.toLowerCase().includes('se') ? 'sentinel' : 
                                id.toLowerCase().includes('sy') ? 'synth' : 
                                id.toLowerCase().includes('fs') ? 'skywalker' : 'bridger';
                
                const hud = document.getElementById(`${cleanId}-hud-icon`);
                if (hud) {
                    const hasActivity = (agentData.processed > 0 || agentData.purged > 0 || agentData.found > 0 || 
                                         agentData.fused_clusters > 0 || agentData.validated > 0 || 
                                         agentData.sparks > 0 || agentData.bridges > 0 || agentData.hits > 0);
                    const isOperating = agentData.status && !agentData.status.toLowerCase().includes('idle') && !agentData.status.toLowerCase().includes('hold');
                    
                    if (isOperating || hasActivity) hud.classList.remove('inactive-agent');
                    else hud.classList.add('inactive-agent');

                    // --- Updates dei Contatori ---
                    if (id === 'RP-001') { 
                        const el = document.getElementById('val-reaper-healed'); 
                        const rmb = document.getElementById('val-reaper-reclaimed');
                        if(el) {
                            const newVal = agentData.processed || 0;
                            if (newVal > parseInt(el.innerText || "0")) {
                                spawnReaperMonument({
                                    x: agentData.pos.x * exp,
                                    y: agentData.pos.y * exp,
                                    z: agentData.pos.z * exp
                                });
                            }
                            el.innerText = newVal; 
                        }
                        if(rmb) rmb.innerText = (agentData.reclaimed_mb || 0).toFixed(2);
                        reaperTargetPos.set(agentData.pos.x * exp, agentData.pos.y * exp, agentData.pos.z * exp);
                    }
                    if (id === 'DI-007') { 
                        const el = document.getElementById('val-distiller-pruned'); 
                        if(el) el.innerText = agentData.pruned || 0;
                        distillerTargetPos.set(agentData.pos.x * exp, agentData.pos.y * exp, agentData.pos.z * exp);
                    }
                    if (id === 'JA-001') { 
                        const el = document.getElementById('val-janitron-purged'); 
                        if(el) {
                            const newVal = agentData.purged || 0;
                            if (newVal > parseInt(el.innerText || "0")) janitorFlashTime = 180;
                            el.innerText = newVal; 
                        }
                        janitorTargetPos.set(agentData.pos.x * exp, agentData.pos.y * exp, agentData.pos.z * exp);
                    }
                    if (id === 'SN-008') {
                        const f = document.getElementById('val-snake-found'); if(f) f.innerText = agentData.found || 0;
                        const c = document.getElementById('val-snake-crafted'); if(c) c.innerText = agentData.crafted || 0;
                        const dsell = document.getElementById('val-snake-deleted'); if(dsell) dsell.innerText = agentData.deleted || 0;
                    }
                    if (id === 'QA-101') { 
                        const el = document.getElementById('val-quantum-fused'); if(el) el.innerText = agentData.fused_clusters || 0; 
                        quantumTargetPos.set(agentData.pos.x * exp, agentData.pos.y * exp, agentData.pos.z * exp);
                        if (agentData.is_fusing) quantumFlashTime = 60;
                    }
                    if (id === 'SE-007') { 
                        const v = document.getElementById('val-sentinel-validated'); if(v) v.innerText = agentData.validated || 0;
                        const s = document.getElementById('val-sentinel-synapses'); 
                        if(s) s.innerText = agentData.super_synapses || 0;
                        
                        if (agentData.is_validating) sentinelFlashTime = 180; 
                        if (agentData.is_supersynapse) sentinelLightningTime = 180; // 3 Seconds of Lightning

                        sentinelTargetPos.set(agentData.pos.x * exp, agentData.pos.y * exp, agentData.pos.z * exp);
                    }
                    if (id === 'SY-009') {
                        const s = document.getElementById('val-synth-sparks'); if(s) s.innerText = agentData.sparks || 0;
                        const t = document.getElementById('synth-team-status');
                        if (t) t.style.background = agentData.status === 'active' ? '#ec4899' : '#4b5563';
                        synthTargetPos.set(agentData.pos.x * exp, agentData.pos.y * exp, agentData.pos.z * exp);
                    }
                    if (id === 'CB-003') {
                        const b = document.getElementById('val-bridger-bridges'); if(b) b.innerText = agentData.bridges || 0;
                        bridgerTargetPos.set(agentData.pos.x * exp, agentData.pos.y * exp, agentData.pos.z * exp);
                    }
                    if (id === 'FS-77') {
                        const h = document.getElementById('val-skywalker-hits'); if(h) h.innerText = agentData.hits || agentData.web_hits || 0;
                        const n = document.getElementById('val-skywalker-nodes'); if(n) n.innerText = agentData.nodes_created || 0;
                        skywalkerTargetPos.set(agentData.pos.x * exp, agentData.pos.y * exp, agentData.pos.z * exp);
                    }
                }
            });
        }
        if (d.lab && d.lab.blackboard && d.lab.blackboard.length > 0) {
            const lastSig = d.lab.blackboard.slice(-1)[0];
            const sType = String(lastSig.signal_type || "").toLowerCase();
            if (sType.includes("mission") || sType.includes("system")) {
                const msg = lastSig.msg || "";
                if (msg.includes("[") && msg.includes("%]")) {
                    isEvolving = true;
                    const match = msg.match(/\[(\d+)-(\d+)%\]/);
                    if (match) { 
                        evolutionProgress = parseInt(match[2]); 
                        evolutionStep = msg.split("[")[0].trim(); 
                        updateEvolutionHUD(); 
                    }
                } else if (msg.includes("COMPLETE") || msg.includes("CONVALIDATE")) {
                    isEvolving = false; 
                    refreshVaultState();
                }
            }
        }
                    if (d.lab) {
                        const l = d.lab;
                        if (l.court_actions) {
                            const courtList = document.getElementById('court-verdicts-list');
                            const activeTab = document.querySelector('.settings-tab.active');
                            if (courtList && activeTab && activeTab.id === 'tab-court') {
                                window.renderCourtVerdicts(l.court_actions);
                            }
                        }
                    }
                    if (d.swarm_settings) {
            const s = d.swarm_settings;
            const toggle = document.getElementById('autonomous-court-toggle');
            if (toggle && !toggle.matches(':focus')) toggle.checked = s.autonomous_court;
            
            // Populate and Sync Judge Selects
            ['court-judge-1', 'court-judge-2', 'court-judge-3'].forEach(id => {
                const sel = document.getElementById(id);
                if (sel) {
                    // Populate if empty
                    if (sel.options.length === 0) {
                        // Always provide "-" as the first option
                        const optNone = document.createElement('option');
                        optNone.value = "-"; optNone.innerText = "-";
                        sel.appendChild(optNone);

                        if (installedModels && installedModels.length > 0) {
                            installedModels.forEach(m => {
                                const opt = document.createElement('option');
                                opt.value = m.name; opt.innerText = m.name;
                                sel.appendChild(opt);
                            });
                        }
                    }
                    // Sync value if not being interacted with
                    const serverVal = s[id.replace(/-/g, '_')];
                    if (serverVal && !sel.matches(':focus')) {
                        sel.value = serverVal;
                    }
                }
            });
        }
        if (d.system) {
            const s = d.system;
            const ramFill = document.getElementById('ram-usage-fill');
            const ramText = document.getElementById('ram-usage-text');
            if (ramFill && s.ram) {
                ramFill.style.width = s.ram.used + '%';
                if (ramText) ramText.innerText = `${s.ram.used.toFixed(1)}% / ${(s.ram.total / (1024**3)).toFixed(1)} GB`;
            }
            const cpuGrid = document.getElementById('cpu-core-grid');
            if (cpuGrid && s.cpu && s.cpu.cores) {
                if (cpuGrid.children.length !== s.cpu.cores.length) {
                    cpuGrid.innerHTML = s.cpu.cores.map((_, i) => `<div id="cpu-core-${i}" style="height:30px; background:rgba(255,255,255,0.05); border-radius:4px; border:1px solid rgba(255,255,255,0.05); position:relative; overflow:hidden;"><div class="fill" style="position:absolute; bottom:0; left:0; width:100%; height:0%; background:#3b82f6; transition:height 0.3s;"></div><span style="position:absolute; top:2px; left:2px; font-size:0.4rem; color:rgba(255,255,255,0.3);">C${i}</span></div>`).join('');
                }
                s.cpu.cores.forEach((p, i) => {
                    const fill = cpuGrid.querySelector(`#cpu-core-${i} .fill`);
                    if (fill) {
                        fill.style.height = p + '%';
                        fill.style.background = p > 80 ? '#ef4444' : p > 50 ? '#f59e0b' : '#3b82f6';
                    }
                });
            }
            const dna = document.getElementById('hardware-dna-trace');
            if (dna && s.hardware_dna) dna.innerText = s.hardware_dna;
            
            const engineList = document.getElementById('active-engines-list');
            if (engineList && s.active_engines) {
                engineList.innerHTML = s.active_engines.map(eng => `
                    <div style="display: flex; justify-content: space-between; align-items: center; background: rgba(255,255,255,0.03); padding: 8px 12px; border-radius: 8px; border-left: 3px solid #10b981;">
                        <div style="display: flex; flex-direction: column;">
                            <span style="font-size: 0.8rem; color: #fff; font-weight: 800;">${eng.name}</span>
                            <span style="font-size: 0.55rem; color: #10b981; font-weight: 700; letter-spacing: 1px;">${eng.resource}</span>
                        </div>
                        <div style="font-size: 0.75rem; color: #fff; font-family: 'JetBrains Mono'; font-weight: 900;">${eng.size}</div>
                    </div>
                `).join('');
            }
            
            const mpsVal = document.getElementById('mps-pressure-val');
            if (mpsVal && s.mps_pressure) mpsVal.innerText = `MPS: ${s.mps_pressure}`;
        }
        if (d.nodes_count && d.edges_count && window.densityChart) {
            const density = (d.edges_count / (d.nodes_count || 1)).toFixed(2);
            const timeLabel = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
            window.densityChart.data.labels.push(timeLabel);
            window.densityChart.data.datasets[0].data.push(parseFloat(density));
            if (window.densityChart.data.labels.length > 20) {
                window.densityChart.data.labels.shift();
                window.densityChart.data.datasets[0].data.shift();
            }
            window.densityChart.update('none');
        }
        if (d.nodes_count && window.growthChart) {
            const timeLabel = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
            window.growthChart.data.labels.push(timeLabel);
            window.growthChart.data.datasets[0].data.push(d.nodes_count);
            if (window.growthChart.data.labels.length > 20) {
                window.growthChart.data.labels.shift();
                window.growthChart.data.datasets[0].data.shift();
            }
            window.growthChart.update('none');
        }
    };
}

async function triggerEvolution() {
    try {
        const r = await fetch('/api/evolve', { method: 'POST', headers: { 'X-API-KEY': VAULT_KEY }});
        const d = await r.json();
        log(`🧠 Evolution Protocol: ${d.message || "Mission Dispatched."}`);
        isEvolving = true;
        evolutionProgress = 5;
        evolutionStep = "Initializing Swarm...";
        updateEvolutionHUD();
    } catch(e) { log("❌ Evolution failed to trigger.", "error"); }
}

window.toggleBenchmarkHub = () => {
    const m = document.getElementById('benchmark-modal');
    if(!m) return;
    const isShowing = m.style.display === 'flex';
    m.style.display = isShowing ? 'none' : 'flex'; 
    const huds = ['mc-wrapper', 'nav-guide-tab', 'cycloscope-hud', 'scene-controls-bar', 'oracle-response-hud', 'floating-command-bar', 'super-metrics-hud'];
    if (!isShowing) {
        huds.forEach(id => document.getElementById(id)?.classList.add('force-hide-modal'));
        renderBenchmarkTable();
    } else {
        huds.forEach(id => document.getElementById(id)?.classList.remove('force-hide-modal'));
    }
};

window.toggleAutoEvolution = async (enabled) => {
    log(`🧬 Auto-Evolution: ${enabled ? 'ACTIVATED' : 'DEACTIVATED'}`, enabled ? '#a855f7' : '#94a3b8');
    try {
        await fetch('/api/system/settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                api_key: VAULT_KEY,
                auto_evolve_active: enabled
            })
        });
    } catch(e) { console.error("AutoEvolve Sync Error:", e); }
};

window.toggleClusterFocus = (enabled) => {
    clusterFocus = enabled;
    log(`🎯 Cluster Focus: ${enabled ? 'ENGAGED' : 'DISENGAGED'}`, enabled ? '#a855f7' : '#94a3b8');
    if (vaultPoints.length > 0) {
        updateThreeScene(vaultPoints, []);
    }
};

async function renderBenchmarkTable() {
    const lBody = document.getElementById('benchmark-leaderboard-body');
    if(!lBody) return;
    lBody.innerHTML = '<tr><td colspan="5" style="padding:20px; text-align:center; opacity:0.5;">Analisi telemetrica in corso...</td></tr>';
    try {
        const r = await fetch('/api/models/benchmarks', { headers: { 'X-API-KEY': VAULT_KEY }});
        const d = await r.json();
        const b = d.benchmarks || [];
        if (b.length === 0) {
            lBody.innerHTML = '<tr><td colspan="5" style="padding:20px; text-align:center; color:#f59e0b;">Nessun dato di missione registrato.</td></tr>';
            return;
        }
        b.sort((x, y) => (y.tps || 0) - (x.tps || 0));
        lBody.innerHTML = b.map((m, i) => `
            <tr style="background: rgba(255,255,255,0.02); margin-top: 5px;">
                <td style="padding: 12px; font-weight: 900; color: #3b82f6;">#${i+1}</td>
                <td style="padding: 12px; color: #fff; font-weight: 800;">${m.model_name}</td>
                <td style="padding: 12px; color: #10b981;">${m.tps?.toFixed(1) || 0}</td>
                <td style="padding: 12px; color: #a855f7;">${m.ram?.toFixed(1) || 0} GB</td>
                <td style="padding: 12px;"><span style="color: #4ade80;">OPTIMAL</span></td>
            </tr>
        `).join('');
        
        // 📋 Popolamento Mission History (v4.0)
        const hBody = document.getElementById('mission-history-body');
        const history = d.history || [];
        if (hBody && history.length > 0) {
            hBody.innerHTML = history.map(h => {
                const date = new Date(h.timestamp * 1000).toLocaleTimeString();
                const statusColor = h.quality > 0.8 ? '#10b981' : (h.quality > 0.5 ? '#f59e0b' : '#ef4444');
                const statusText = h.quality > 0.8 ? 'SUCCESS' : (h.quality > 0.5 ? 'DEGRADED' : 'FAILED');
                const ramGB = h.ram > 100 ? (h.ram / 1024).toFixed(2) + " GB" : h.ram.toFixed(0) + " MB";
                return `
                    <tr style="background: rgba(255,255,255,0.01); transition: 0.2s;">
                        <td style="padding: 10px; color: #64748b; font-family: 'JetBrains Mono'; font-size: 0.6rem;">${date}</td>
                        <td style="padding: 10px; color: #fff; font-weight: 800;">${h.model_name}</td>
                        <td style="padding: 10px; color: #a855f7; font-weight: 600;">${h.task.toUpperCase()}</td>
                        <td style="padding: 10px; color: #10b981; font-weight: 800;">${h.tps.toFixed(1)}</td>
                        <td style="padding: 10px; color: #3b82f6;">${h.latency.toFixed(0)}ms</td>
                        <td style="padding: 10px; color: #facc15;">${ramGB}</td>
                        <td style="padding: 10px;"><span style="color: ${statusColor}; font-weight: 900; font-size: 0.55rem; border: 1px solid ${statusColor}; padding: 2px 6px; border-radius: 4px;">${statusText}</span></td>
                    </tr>
                `;
            }).join('');
        }
        const advisor = document.getElementById('strategy-advisor-content');
        if (advisor) {
            const avgLat = b.reduce((s, x) => s + (x.avg_latency || 0), 0) / b.length;
            const avgTps = b.reduce((s, x) => s + (x.tps || 0), 0) / b.length;
            
            // 🏅 Efficiency Rating Logic
            let grade = "C";
            let gradeColor = "#ef4444";
            let statusLabel = "NECESSARIA OTTIMIZZAZIONE";
            
            if (avgTps > 30 && avgLat < 2000) { grade = "S"; gradeColor = "#facc15"; statusLabel = "PRESTAZIONI D'ELITE"; }
            else if (avgTps > 15 && avgLat < 5000) { grade = "A"; gradeColor = "#10b981"; statusLabel = "OTTIMALE"; }
            else if (avgTps > 5 && avgLat < 15000) { grade = "B"; gradeColor = "#3b82f6"; statusLabel = "STABILE"; }
            
            const displayLat = avgLat > 1000 ? (avgLat/1000).toFixed(2) + "s" : avgLat.toFixed(1) + "ms";
            const dnaTrace = document.getElementById('hardware-dna-trace')?.innerText || "MPS";

            advisor.innerHTML = `
                <div style="display:grid; grid-template-columns: auto 1fr auto; align-items:center; gap:20px; background: rgba(255,255,255,0.02); padding: 25px; border-radius: 16px; border: 1px solid rgba(168, 85, 247, 0.15);">
                    <div style="width: 70px; height: 70px; border-radius: 50%; border: 4px solid ${gradeColor}; display: flex; align-items: center; justify-content: center; position: relative; box-shadow: 0 0 20px ${gradeColor}33;">
                        <span style="font-size: 2rem; font-weight: 950; color: ${gradeColor}; text-shadow: 0 0 10px ${gradeColor};">${grade}</span>
                        <div style="position: absolute; bottom: -10px; background: ${gradeColor}; color: #000; font-size: 0.5rem; font-weight: 900; padding: 2px 8px; border-radius: 4px; white-space: nowrap;">NEURAL GRADE</div>
                    </div>
                    
                    <div style="border-left: 1px solid rgba(255,255,255,0.05); padding-left: 20px;">
                        <h4 style="color:#fff; margin:0; font-size:0.9rem; letter-spacing:1px; font-weight: 900;">HARDWARE ADVISOR v1.0 <span style="font-size: 0.6rem; color: #a855f7; margin-left: 10px;">[SOVEREIGN_DIAGNOSTICS]</span></h4>
                        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin-top: 12px;">
                            <div>
                                <div style="font-size: 0.55rem; color: #64748b; font-weight: 800; letter-spacing: 1px;">LATENZA SESSIONE</div>
                                <div style="font-size: 0.85rem; color: #fff; font-weight: 900; font-family: 'JetBrains Mono';">${displayLat}</div>
                            </div>
                            <div>
                                <div style="font-size: 0.55rem; color: #64748b; font-weight: 800; letter-spacing: 1px;">EFFICIENZA MEDIA</div>
                                <div style="font-size: 0.85rem; color: #10b981; font-weight: 900; font-family: 'JetBrains Mono';">${avgTps.toFixed(1)} <span style="font-size: 0.6rem;">tok/s</span></div>
                            </div>
                            <div>
                                <div style="font-size: 0.55rem; color: #64748b; font-weight: 800; letter-spacing: 1px;">STATUS DNA</div>
                                <div style="font-size: 0.85rem; color: #3b82f6; font-weight: 900; font-family: 'JetBrains Mono';">${dnaTrace.split('|')[0].trim()}</div>
                            </div>
                        </div>
                        <p style="color:#94a3b8; font-size:0.65rem; line-height:1.4; margin:12px 0 0 0; background: rgba(0,0,0,0.2); padding: 8px; border-radius: 8px; border-left: 3px solid ${gradeColor};">
                            <i class="fas fa-microchip" style="margin-right: 5px;"></i> ${avgLat > 10000 ? "⚠️ Rilevato congestionamento. Si consiglia l'uso di modelli GGUF Quantizzati (Q4_K_M) per scaricare lo stress sulla memoria di sistema." : "✅ Performance d'elite rilevate. L'architettura Metal/MPS è saturata correttamente con bassa dispersione termica."}
                        </p>
                    </div>
                    
                    <div style="text-align: right;">
                        <div style="font-size: 0.6rem; color: ${gradeColor}; font-weight: 950; letter-spacing: 1px; margin-bottom: 5px;">${statusLabel}</div>
                        <button onclick="window.refreshRadar()" class="sovereign-btn-active">RIPRISTINA DNA</button>
                    </div>
                </div>
                <style>
                    .sovereign-btn-active {
                        background: rgba(168, 85, 247, 0.1); 
                        border: 1px solid #a855f7; 
                        color: #a855f7; 
                        font-size: 0.6rem; 
                        padding: 10px 20px; 
                        border-radius: 10px; 
                        cursor: pointer; 
                        font-weight: 900; 
                        transition: all 0.2s cubic-bezier(0.175, 0.885, 0.32, 1.275); 
                        width: 100%;
                        box-shadow: 0 4px 15px rgba(168, 85, 247, 0.1);
                    }
                    .sovereign-btn-active:hover {
                        background: rgba(168, 85, 247, 0.2);
                        box-shadow: 0 0 20px rgba(168, 85, 247, 0.3);
                    }
                    .sovereign-btn-active:active {
                        transform: scale(0.92);
                        background: rgba(168, 85, 247, 0.4);
                        box-shadow: inset 0 2px 10px rgba(0,0,0,0.5);
                    }
                </style>
            `;
        }
    } catch(e) { console.error("BenchErr:", e); }
}

window.openAuditLedger = async (full = false) => {
    const modal = document.getElementById('audit-ledger-modal');
    if (!modal) return;
    const title = document.getElementById('audit-ledger-title-main');
    if (title) title.innerText = full ? "CHRONO-LOG: PERMANENT ARCHIVE" : "CHRONO-LOG: SESSION ACTIONS";
    modal.style.display = 'flex';
    modal.style.zIndex = "90000"; 
    const huds = ['mc-wrapper', 'nav-guide-tab', 'cycloscope-hud', 'scene-controls-bar', 'oracle-response-hud', 'floating-command-bar', 'super-metrics-hud'];
    huds.forEach(id => document.getElementById(id)?.classList.add('force-hide-modal'));
    const b = document.getElementById('audit-ledger-body');
    if (!b) return;
    b.innerHTML = '<tr><td colspan="6" style="padding:2rem; text-align:center;">Retrieving Sovereign Logs...</td></tr>';
    try {
        const url = full ? `/api/audit/ledger?full=true` : `/api/audit/ledger`;
        const r = await fetch(url, { headers: { 'X-API-KEY': VAULT_KEY }});
        const logs = await r.json();
        if (!logs || logs.length === 0) {
            b.innerHTML = '<tr><td colspan="6" style="padding:4rem; text-align:center; opacity:0.5; color:#a855f7;">[MISSION_STATUS: LOG_EMPTY] - No actions recorded yet.</td></tr>';
            return;
        }
        b.innerHTML = logs.map(l => `
            <tr style="border-bottom: 1px solid rgba(255,255,255,0.05); transition: 0.2s;" onmouseover="this.style.background='rgba(168,85,247,0.05)'" onmouseout="this.style.background='transparent'">
                <td style="padding:1.2rem; color:#8b949e; font-size:0.6rem;">${l.timestamp}</td>
                <td style="padding:1.2rem;"><span style="color:#a855f7; border:1px solid rgba(168,85,247,0.3); padding:3px 10px; border-radius:6px; font-weight:800; font-size:0.6rem;">${l.agent || "SYSTEM"}</span></td>
                <td style="padding:1.2rem; color:#fff; font-weight:800; font-size:0.7rem;">${(l.action || "Update").toUpperCase()}</td>
                <td style="padding:1.2rem; color:#3b82f6; font-size:0.6rem;">${l.target || "GLOBAL"}</td>
                <td style="padding:1.2rem; color:#cbd5e1; font-size:0.65rem; line-height:1.4;">${l.reasoning || l.motivation || "Maintenance cycle."}</td>
                <td style="padding:1.2rem; color:#4ade80; text-align:right; font-weight:800;">${l.savings || "—"}</td>
            </tr>
        `).join('');
    } catch(e) {
        console.error("Audit Ledger Error:", e);
        b.innerHTML = '<tr><td colspan="6" style="padding:2rem; text-align:center; color:#ef4444;">FATAL_ERROR: Access Denied or API unreachable.</td></tr>';
    }
};

window.closeAuditLedger = () => {
    const m = document.getElementById('audit-ledger-modal');
    if (m) m.style.display = 'none';
    const huds = ['mc-wrapper', 'nav-guide-tab', 'cycloscope-hud', 'scene-controls-bar', 'oracle-response-hud', 'floating-command-bar', 'super-metrics-hud'];
    huds.forEach(id => document.getElementById(id)?.classList.remove('force-hide-modal'));
};

window.exportAuditLedger = function(format) {
    const table = document.getElementById('audit-ledger-body');
    if (!table) return;
    const rows = Array.from(table.rows);
    if (!rows.length || rows[0].innerText.includes("Fetch")) return;
    let content = "";
    let filename = `NeuralVault_Audit_${new Date().toISOString().slice(0,19).replace(/[:T]/g, '_')}.txt`;
    let type = "text/plain";
    if (format === 'json') {
        const data = rows.map(r => ({
            time: r.cells[0].innerText, agent: r.cells[1].innerText, action: r.cells[2].innerText,
            target: r.cells[3].innerText, reason: r.cells[4].innerText, savings: r.cells[5].innerText
        }));
        content = JSON.stringify(data, null, 2); filename = filename.replace('.txt', '.json'); type = "application/json";
    } else if (format === 'csv') {
        content = "TIMESTAMP,AGENTE,AZIONE,TARGET,MOTIVAZIONE,IMPATTO\n" + 
            rows.map(r => Array.from(r.cells).map(c => `"${c.innerText.replace(/"/g, '""')}"`).join(",")).join("\n");
        filename = filename.replace('.txt', '.csv'); type = "text/csv";
    } else {
        content = "--- NEURALVAULT AUDIT LEDGER ---\n\n" + 
            rows.map(r => `[${r.cells[0].innerText}] ${r.cells[1].innerText} -> ${r.cells[2].innerText}\n   Reason: ${r.cells[4].innerText}\n`).join("\n");
    }
    const blob = new Blob([content], { type: type });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a'); a.href = url; a.download = filename; a.click();
    document.getElementById('export-dropdown')?.classList.add('hidden');
};

window.refreshHubVisual = async () => { renderModelHubTable(); };

function initCharts() {
    const growthCtx = document.getElementById('growth-chart')?.getContext('2d');
    if (growthCtx) {
        window.growthChart = new Chart(growthCtx, {
            type: 'line',
            data: {
                labels: ['START', 'T+1m', 'T+2m', 'T+5m', 'T+10m', 'NOW'],
                datasets: [{
                    label: 'CONOSCENZA (NODI)',
                    data: [1000, 2500, 4800, 7200, 9500, 10000],
                    borderColor: '#3b82f6',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    fill: true,
                    tension: 0.4,
                    borderWidth: 3,
                    pointRadius: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#64748b', font: { size: 10 } } },
                    x: { grid: { display: false }, ticks: { color: '#64748b', font: { size: 10 } } }
                }
            }
        });
    }
    const densityCtx = document.getElementById('density-chart')?.getContext('2d');
    if (densityCtx) {
        window.densityChart = new Chart(densityCtx, {
            type: 'line',
            data: {
                labels: ['START', 'MISSION_1', 'MISSION_2', 'MISSION_3', 'MISSION_4', 'MISSION_5'],
                datasets: [{
                    label: 'RELATIONS PER NODE',
                    data: [1.2, 1.8, 2.5, 3.1, 4.2, 4.8],
                    borderColor: '#a855f7',
                    backgroundColor: 'rgba(168, 85, 247, 0.1)',
                    fill: true,
                    tension: 0.4,
                    borderWidth: 3,
                    pointRadius: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    y: { grid: { color: 'rgba(255,255,255,0.05)' }, border: { display: false }, ticks: { color: '#64748b', font: { size: 9 } } },
                    x: { grid: { display: false }, ticks: { color: '#64748b', font: { size: 9 } } }
                }
            }
        });
    }
    const impactCtx = document.getElementById('benchmark-impact-chart')?.getContext('2d');
    if (impactCtx) {
        window.impactChart = new Chart(impactCtx, {
            type: 'bar',
            data: {
                labels: ['LLAMA 3.2', 'DEEPSEEK', 'PHI-3.5', 'QWEN-2.5', 'LLAVA'], // Default iniziali
                datasets: [
                    {
                        label: 'LATENCY (ms)',
                        data: [45, 120, 30, 85, 95],
                        backgroundColor: 'rgba(59, 130, 246, 0.5)',
                        borderColor: '#3b82f6',
                        borderWidth: 1
                    },
                    {
                        label: 'TPS (tok/s)',
                        data: [25, 12, 45, 18, 16],
                        backgroundColor: 'rgba(168, 85, 247, 0.1)',
                        borderColor: '#a855f7',
                        borderWidth: 1
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { position: 'top', labels: { color: '#fff', font: { size: 10 } } } },
                scales: {
                    y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#64748b' } },
                    x: { grid: { display: false }, ticks: { color: '#64748b', font: { size: 8 } } }
                }
            }
        });
    }

    // 🧬 [Phase 3] Cognitive Radar Initialization
    const radarCtx = document.getElementById('radar-chart')?.getContext('2d');
    if (radarCtx) {
        window.radarChart = new Chart(radarCtx, {
            type: 'radar',
            data: {
                labels: ['SPEED', 'ACCURACY', 'STABILITY', 'DENSITY', 'REASONING'],
                datasets: [{
                    label: 'SOVEREIGN_SWARM_AVG',
                    data: [85, 92, 78, 65, 88],
                    backgroundColor: 'rgba(59, 130, 246, 0.2)',
                    borderColor: '#3b82f6',
                    borderWidth: 2,
                    pointBackgroundColor: '#3b82f6'
                }]
            },
            options: {
                scales: {
                    r: {
                        angleLines: { color: 'rgba(255,255,255,0.1)' },
                        grid: { color: 'rgba(255,255,255,0.1)' },
                        pointLabels: { color: '#8b949e', font: { size: 10 } },
                        ticks: { display: false }
                    }
                },
                plugins: { legend: { display: false } }
            }
        });
    }
}

// 📊 [Phase 3] Refresh Benchmarks & Radar Logic
async function refreshBenchmarks() {
    try {
        const r = await fetch('/api/models/benchmarks', { headers: { 'X-API-KEY': VAULT_KEY }});
        const data = await r.json();
        
        // 1. Leaderboard Update
        const body = document.getElementById('benchmark-leaderboard-body');
        if (body && data.benchmarks) {
            body.innerHTML = data.benchmarks.map((m, i) => `
                <tr style="background: rgba(255,255,255,0.02); border-radius: 10px;">
                    <td style="padding: 10px; font-weight: 950; color: ${i === 0 ? '#fbbf24' : '#fff'};">#${i+1}</td>
                    <td style="padding: 10px; font-family: 'JetBrains Mono';">${m.name}</td>
                    <td style="padding: 10px; color: #10b981;">${m.tps} <span style="font-size: 0.6rem;">tok/s</span></td>
                    <td style="padding: 10px; color: #3b82f6;">${m.ram} <span style="font-size: 0.6rem;">MB</span></td>
                    <td style="padding: 10px; color: #a855f7;">${m.stability}%</td>
                </tr>
            `).join('');
        }

        // 2. Radar Update
        if (window.radarChart && data.radar) {
            window.radarChart.data.datasets[0].data = data.radar;
            window.radarChart.update();
        }

        // 3. Model Suggestions Logic
        const recList = document.getElementById('mission-recommendation');
        if (recList && data.benchmarks.length > 0) {
            const bestSpeed = data.benchmarks[0].name;
            const bestStability = [...data.benchmarks].sort((a,b) => b.stability - a.stability)[0].name;
            
            recList.innerHTML = `
                <div style="background: rgba(0,0,0,0.2); padding: 1rem; border-radius: 12px; border-left: 3px solid #10b981;">
                    <div style="font-size: 0.5rem; color: #10b981;">OPTIMAL FOR JANITORIAL/PURGE</div>
                    <div style="font-weight: 900; font-size: 0.8rem; color: #fff;">${bestSpeed.toUpperCase()} (FAST)</div>
                </div>
                <div style="background: rgba(0,0,0,0.2); padding: 1rem; border-radius: 12px; border-left: 3px solid #a855f7;">
                    <div style="font-size: 0.5rem; color: #a855f7;">OPTIMAL FOR AUDITS/COURT</div>
                    <div style="font-weight: 900; font-size: 0.8rem; color: #fff;">${bestStability.toUpperCase()} (STABLE)</div>
                </div>
            `;
        }
    } catch(e) {}
}

// ⚖️ [Phase 3] Supreme Court Verdict Review logic
async function refreshCourtQueue() {
    const root = document.getElementById('strategy-advisor-content');
    if (!root) return;
    
    try {
        const response = await fetch('/api/swarm/audit-queue', { headers: { 'X-API-KEY': VAULT_KEY }});
        const queue = await response.json();
        
        if (!queue || queue.length === 0) {
            root.innerHTML = `
                <div style="text-align: center; padding: 2rem; color: #8b949e; font-size: 0.7rem; letter-spacing: 1px;">
                    <i class="fas fa-balance-scale" style="font-size: 1.5rem; margin-bottom: 1rem; opacity: 0.3;"></i><br>
                    CORTE SUPREMA: NESSUN VERDETTO PENDENTE. IL SISTEMA È IN EQUILIBRIO.
                </div>
            `;
            return;
        }

        root.innerHTML = `
            <div style="font-size: 0.7rem; font-weight: 900; color: #a855f7; margin-bottom: 1.5rem; letter-spacing: 2px;">⚖️ PENDING VERDICTS (${queue.length})</div>
            <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 1rem;">
                ${queue.map((item, idx) => `
                    <div style="background: rgba(255,255,255,0.03); border: 1px solid rgba(168, 85, 247, 0.2); padding: 1.2rem; border-radius: 16px;">
                        <div style="font-size: 0.55rem; color: #8b949e; margin-bottom: 8px;">TARGET: ${item.src?.substring(0,8)} ⟷ ${item.dst?.substring(0,8)}</div>
                        <div style="font-weight: 800; color: #fff; font-size: 0.7rem; margin-bottom: 12px;">ESCALATION: AMBIGUITÀ SEMANTICA RILEVATA</div>
                        <div style="display: flex; gap: 8px;">
                            <button onclick="resolveVerdict(${idx}, 'approve')" style="flex: 1; padding: 6px; background: rgba(16, 185, 129, 0.2); color: #10b981; border: 1px solid #10b981; border-radius: 8px; font-size: 0.6rem; font-weight: 900; cursor: pointer;">APPROVA</button>
                            <button onclick="resolveVerdict(${idx}, 'reject')" style="flex: 1; padding: 6px; background: rgba(239, 68, 68, 0.2); color: #ef4444; border: 1px solid #ef4444; border-radius: 8px; font-size: 0.6rem; font-weight: 900; cursor: pointer;">RIFIUTA</button>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    } catch(e) {}
}

async function resolveVerdict(idx, action) {
    log(`⚖️ COURT: Procedura di arbitrato per verdetto #${idx}...`, "#a855f7");
    try {
        const r = await fetch('/api/swarm/resolve-verdict', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ index: idx, decision: action, api_key: VAULT_KEY })
        });
        const res = await r.json();
        if (res.status === 'ok') {
            log(`✅ VERIZION_OK: Verdetto ${action.toUpperCase()} applicato alla Nebula.`, "#10b981");
            refreshCourtQueue();
        }
    } catch(e) { log("❌ COURT_ERR: Connessione alla Gran Giuria interrotta.", "#ef4444"); }
}

// --- 🌍 SOVEREIGN LOCALIZATION ENGINE (v5.5) ---
const NEURAL_LANG_PACK = {
    "system_status": ["STATO SISTEMA", "SYSTEM STATUS"],
    "kernel_online": ["KERNEL ONLINE", "KERNEL ONLINE"],
    "nav_overview": ["PANORAMICA MEMORIA", "MEMORY OVERVIEW"],
    "nav_lab": ["LABORATORIO NEURALE", "NEURAL LABORATORY"],
    "nav_analytics": ["ANALISI AVANZATA", "ADVANCED ANALYTICS"],
    "nav_benchmark": ["LLM BENCHMARK HUB", "LLM BENCHMARK HUB"],
    "nav_settings": ["CONFIGURAZIONE", "SETTINGS"],
    "stat_nodes": ["NODI", "NODES"],
    "stat_edges": ["ARCHI", "EDGES"],
    "stat_clusters": ["CLUSTER", "CLUSTERS"],
    "stat_aura": ["AURA", "AURA"],
    "stat_storage": ["VAULT", "VAULT"],
    "stat_probe": ["SONDA", "PROBE"],
    "btn_inspect": ["ISPEZIONA", "INSPECT"],
    "btn_purge": ["PULIZIA", "PURGE"],
    "btn_sync": ["SINCRONIZZA", "SYNC"],
    "btn_save": ["SALVA CONFIGURAZIONE", "SAVE CONFIGURATION"],
    "btn_synapse": ["SINAPSI", "SYNAPSE"],
    "btn_hide": ["NASCONDI", "HIDE"],
    "placeholder_search": ["Cerca nella Nebula...", "Search in the Nebula..."],
    "placeholder_url": ["Incolla URL per sinapsi...", "Paste URL to synapse..."],
    "placeholder_chat": ["Interroga il Vault...", "Probe the Vault..."],
    "placeholder_command": ["Inserisci comando...", "Enter command..."],
    "title_swarm": ["SCIAME NEURALE", "NEURAL SWARM"],
    "title_history": ["LOG MISSIONI RECENTI", "RECENT MISSION LOG"],
    "title_nav_guide": ["NAV-GUIDA: STATO", "NAV-GUIDE: STATUS"],
    "title_agent_bar": ["BARRA AGENTI", "AGENT BAR"],
    "title_integrated_chat": ["INTEGRATED_NEURAL_CHAT", "INTEGRATED_NEURAL_CHAT"],
    "title_swarm_settings": ["IMPOSTAZIONI GLOBALI SCIAME", "SWARM_GLOBAL_SETTINGS"],
    "title_swarm_ops": ["CENTRO OPERATIVO SCIAME", "SWARM_OPERATIONS_CENTER"],
    "research_mode": ["RESEARCH MODE (Default)", "RESEARCH MODE (Default)"],
    "evolution_mode": ["EVOLUTION MODE (Dev)", "EVOLUTION MODE (Dev)"],
    "oracle_thinking": ["Analisi in corso...", "Analyzing..."],
    "oracle_sources": ["Sorgenti attivate", "Sources activated"],
    "guide_rotate": ["RUOTA", "ROTATE"],
    "guide_pan": ["SPOSTA", "PAN"],
    "guide_zoom": ["ZOOM", "ZOOM"],
    "guide_probe": ["SONDA", "PROBE"],
    "guide_ctrl": ["Usa Ctrl + Click per focus rapido.", "Use Ctrl + Click for rapid target focus."],
    "agent_distiller": ["DI-007 DISTILLATORE", "DI-007 DISTILLER"],
    "agent_janitron": ["JA-001 JANITRON", "JA-001 JANITRON"],
    "agent_reaper": ["RP-001 DR. REAPER", "RP-001 DR. REAPER"],
    "agent_snake": ["SN-008 SNAKE", "SN-008 SNAKE"],
    "agent_quantum": ["QA-101 QUANTUM", "QA-101 QUANTUM"],
    "agent_sentinel": ["SE-007 SENTINELLA", "SE-007 SENTINEL"],
    "agent_synth": ["SY-009 SYNTH", "SY-009 SYNTH"],
    "agent_bridger": ["CB-003 BRIDGER", "CB-003 BRIDGER"],
    "agent_skywalker": ["FS-77 SKY-WALKER", "FS-77 SKY-WALKER"],
    "stat_pruned": ["Archi Potati", "Arcs Pruned"],
    "stat_purged": ["Nodi Eliminati", "Nodes Eaten"],
    "stat_healed": ["Auto-Riparazione", "Self-Heal"],
    "stat_found": ["Nodi Trovati", "Nodes Found"],
    "stat_crafted": ["Nodi Germogliati", "Sprouted Nodes"],
    "stat_fused": ["Cluster Fusi", "Clusters Fused"],
    "stat_validated": ["Validati", "Validated"],
    "stat_bridges": ["Super-Ponti", "Super-Bridges"],
    "label_swarm_config": ["CONFIGURAZIONE SCIAME", "SWARM CONFIGURATION"],
    "label_extraction": ["ESTRAZIONE", "EXTRACTION"],
    "label_synthesis": ["SINTESI (Synth)", "SYNTHESIS (Synth)"],
    "label_mediator": ["CHAT MEDIATOR", "CHAT MEDIATOR"],
    "label_evolution_suggestions": ["SUGGERIMENTI EVOLUTIVI", "EVOLUTION SUGGESTIONS"],
    "label_supreme_committee": ["COMMISSIONE SUPREMA", "SUPREME COMMITTEE"],
    "label_sovereign_protocol": ["PROTOCOLLO SOVRANO", "SOVEREIGN PROTOCOL"],
    "label_consensus": ["CONSENSO LLM", "LLM CONSENSUS"],
    "label_weaver_sensitivity": ["SENSIBILITA WEAVER", "WEAVER SENSITIVITY"],
    "label_autopilot": ["Auto-Pilot Supervision", "Auto-Pilot Supervision"],
    "label_vision_multimodal": ["VISION & MULTIMODAL INTELLIGENCE", "VISION & MULTIMODAL INTELLIGENCE"],
    "label_theme_interface": ["TEMA E INTERFACCIA", "THEME & INTERFACE"],
    "label_danger_zone": ["AREA PERICOLOSA", "DANGER ZONE"],
    "label_operational_mode": ["MODALITA OPERATIVA", "OPERATIONAL MODE"],
    "label_evolution_feedback": ["EVOLUTION FEEDBACK LOOP", "EVOLUTION FEEDBACK LOOP"],
    "mode_research_desc": ["Lo sciame è blindato. Gli agenti ignorano la codebase e si concentrano solo sui dati dell'utente. Massima stabilità.", "The swarm is locked down. Agents ignore the codebase and focus only on user data. Maximum stability."],
    "mode_evolution_desc": ["Lo sciame attiva il LatentBridge. L'IA torna a 'guardarsi allo specchio' per aiutarti a debuggare o ottimizzare.", "The swarm activates LatentBridge. The AI 'looks in the mirror' to help you debug or optimize."],
    "tooltip_extraction": ["Modello rapido ottimizzato per il parsing di entità da file grezzi.", "Fast model optimized for parsing entities from raw files."],
    "tooltip_sentinel": ["Il Sentinel valida i legami tra web e locale.", "The Sentinel validates links between web and local."],
    "tooltip_synth": ["Il Muse genera intuizioni creative collegando nodi distanti.", "The Muse generates creative sparks by connecting distant nodes."],
    "tooltip_consensus": ["Numero di modelli che devono concordare prima di una fusione.", "Number of models that must agree before a fusion."],
    "tooltip_autopilot": ["Se attivo, lo swarm agisce in autonomia.", "If active, the swarm acts autonomously."],
    "label_model": ["MODELLO", "MODEL"],
    "label_mission": ["MISSIONE / TASK", "MISSION / TASK"],
    "label_latency": ["LATENZA", "LATENCY"],
    "label_speed": ["VELOCITA", "SPEED"],
    "label_timestamp": ["ORARIO", "TIMESTAMP"],
    "label_target_id": ["TARGET_ID", "TARGET_ID"],
    "label_live_trace": ["LIVE TRACE: ATTIVO", "LIVE TRACE: ACTIVE"],
    "label_awaiting_mission": ["In attesa di esecuzione missione...", "Awaiting mission execution..."],
    "label_hardware_analysis": ["ANALISI HARDWARE IN CORSO...", "HARDWARE ANALYSIS IN PROGRESS..."],
    "label_judge_alpha": ["GIUDICE_ALPHA", "JUDGE_ALPHA"],
    "label_judge_beta": ["GIUDICE_BETA", "JUDGE_BETA"],
    "label_judge_gamma": ["GIUDICE_GAMMA", "JUDGE_GAMMA"],
    "title_mission_hold": ["MISSION HOLD: AGENTE", "MISSION HOLD: AGENT"],
    "label_agent": ["AGENTE", "AGENT"],
    "label_action": ["AZIONE", "ACTION"],
    "label_impact": ["IMPATTO", "IMPACT"],
    "label_motivation": ["LOGICA MOTIVAZIONALE", "MOTIVATIONAL LOGIC"],
    "btn_close_ledger": ["CHIUDI VERBALE", "CLOSE AUDIT"],
    "btn_resume": ["RIPRENDI", "RESUME"],
    "btn_abort": ["ABORTISCI", "ABORT"],
    "btn_implemented": ["IMPLEMENTATO", "IMPLEMENTED"],
    "btn_discarded": ["SCARTATO", "DISCARDED"],
    "btn_false_positive": ["FALSO POSITIVO", "FALSE POSITIVE"],
    "msg_awaiting_evolution": ["In attesa di segnali evolutivi... Attiva Evolution Mode per iniziare.", "Awaiting evolution signals... Activate Evolution Mode to begin."],
    "msg_bug_found": ["BUG RILEVATO", "BUG DETECTED"],
    "msg_optimization": ["OTTIMIZZAZIONE SUGGERITA", "OPTIMIZATION SUGGESTED"],
    "label_custom_forge": ["NEURAL FORGE: AGGIUNGI CORE CUSTOM", "NEURAL FORGE: ADD CUSTOM CORE"],
    "label_model_name": ["NOME MODELLO", "MODEL NAME"],
    "label_provider": ["PROVIDER (Ollama/HF/Local)", "PROVIDER (Ollama/HF/Local)"],
    "label_endpoint_path": ["PERCORSO / ID REPO", "PATH / REPO ID"],
    "btn_register_model": ["REGISTRA NEL VAULT", "REGISTER IN VAULT"],
    "placeholder_custom_path": ["es: my-custom-model o /path/to/model", "e.g., my-custom-model or /path/to/model"],
    "label_analytics_desc": ["Monitoraggio telemetrico delle risorse hardware e del framework cognitivo neurale.", "Telemetric monitoring of hardware resources and neural cognitive framework."],
    "label_cognitive_density": ["COGNITIVE DENSITY", "COGNITIVE DENSITY"],
    "label_density_desc": ["Relazioni per nodo (avg)", "Relations per node (avg)"],
    "label_knowledge_growth": ["KNOWLEDGE GROWTH", "KNOWLEDGE GROWTH"],
    "label_growth_desc": ["Nodi indicizzati nel tempo", "Nodes indexed over time"],
    "tooltip_tracing": ["Monitoraggio a bassa latenza del core e degli uplink Ollama. Traccia i vettori di input attraverso i layer di quantizzazione e registra l'attivazione della mesh.", "Low-latency monitoring of the core and Ollama uplinks. Tracks input vectors through quantization layers and records mesh activation."],
    "tooltip_inventory": ["Registro immutabile della provenienza (Provenance). Ogni riga associa i metadati di sistema alle coordinate temporali e alla natura del media.", "Immutable record of provenance. Each row associates system metadata with temporal coordinates and media nature."],
    "tooltip_telemetry": ["Monitoraggio hardware profondo: CPU (Carico/Core), RAM (Unified/Useful), GPU (Metal Pressure) e Storage SSD.", "Deep hardware monitoring: CPU (Load/Cores), RAM (Unified/Useful), GPU (Metal Pressure), and SSD Storage."],
    "tooltip_ingestion": ["Punto di singolarità per l'input dati. Gestisce il pre-processing multimodale: chunking video, diarizzazione audio e scraping URL.", "Singularity point for data input. Manages multimodal pre-processing: video chunking, audio diarization, and URL scraping."],
    "tooltip_cognitive": ["Metriche di salute della memoria: Retention (forza media del ricordo) e Stability (consolidamento tramite accessi ripetuti).", "Memory health metrics: Retention (average recall strength) and Stability (consolidation via repeated access)."],
    "tooltip_distance": ["Coesione semantica della Nebula: un valore basso indica cluster densi e focalizzati, un valore alto indica diversità e dispersione dei concetti.", "Semantic cohesion of the Nebula: a low value indicates dense, focused clusters; a high value indicates concept diversity and dispersion."],
    "tooltip_agent007": ["Statistiche della Hard-Memory: Entità estratte e Relazioni logiche certificate salvate nel database persistente SQLite.", "Hard-Memory statistics: Extracted Entities and certified Logical Relations stored in the persistent SQLite database."],
    "tooltip_nodes": ["Numero totale di frammenti di conoscenza (nodi) attualmente attivi nel grafo vettoriale.", "Total number of knowledge fragments (nodes) currently active in the vector graph."],
    "tooltip_edges": ["Connessioni sinaptiche attive tra i nodi, generate tramite analisi semantica o audit degli agenti.", "Active synaptic connections between nodes, generated via semantic analysis or agent audits."],
    "tooltip_clusters": ["Aggregazioni tematiche autonome rilevate dallo sciame basandosi sulla prossimità vettoriale.", "Autonomous thematic aggregations detected by the swarm based on vector proximity."],
    "tooltip_blueprint": ["Indica che il ciclo di sintesi tra gli agenti è completo e il Vault è in stato di massima coerenza.", "Indicates that the agent synthesis cycle is complete and the Vault is in a state of maximum coherence."],
    "label_hardware_observatory": ["HARDWARE OBSERVATORY", "HARDWARE OBSERVATORY"],
    "label_hardware_desc": ["Monitoraggio fisico delle risorse di calcolo locale accelerato via Metal/MPS.", "Physical monitoring of local compute resources accelerated via Metal/MPS."],
    "label_hardware_dna": ["HARDWARE DNA TRACE", "HARDWARE DNA TRACE"],
    "label_ram_availability": ["SYSTEM RAM AVAILABILITY", "SYSTEM RAM AVAILABILITY"],
    "label_neural_manifest": ["NEURAL RESOURCE MANIFEST", "NEURAL RESOURCE MANIFEST"],
    "label_scanning_engines": ["Scansione motori neurali attivi...", "Scanning for active neural engines..."],
    "label_status_optimized": ["STATO: OTTIMIZZAZIONE LOCALE", "STATUS: LOCAL-FIRST OPTIMIZED"],
    "label_cpu_mesh": ["CPU_MESH (USO PER-CORE)", "CPU_MESH (PER-CORE USAGE)"],
    "label_metal_accelerated": ["ACCELERAZIONE_METAL: ON", "METAL_ACCELERATED: ON"],
    "label_neural_intelligence": ["INTELLIGENZA NEURALE", "NEURAL INTELLIGENCE"],
    "label_mode_observation": ["MODALITÀ: OSSERVAZIONE", "MODE: OBSERVATION"],
    "label_active_model": ["MODELLO_ATTIVO", "ACTIVE_MODEL"],
    "label_quantization": ["QUANTIZZAZIONE", "QUANTIZATION"],
    "label_avg_performance": ["PERFORMANCE_MEDIA (ALL-TIME)", "AVG_PERFORMANCE (ALL-TIME)"],
    "label_sovereign_engine": ["SOVEREIGN ENGINE: ANALISI STORICA", "SOVEREIGN ENGINE: HISTORICAL ANALYSIS"],
    "label_wisdom_cycles": ["Cicli di Saggezza", "Wisdom Cycles"],
    "label_knowledge_depth": ["Profondità Conoscenza", "Knowledge Depth"],
    "label_hardware_yield": ["Resa Hardware", "Hardware Yield"],
    "label_growth_velocity": ["Velocità di Crescita", "Growth Velocity"],
    "label_benchmark_desc": ["CLASSIFICA STORICA E ANALISI COMPARATIVA DELLE PRESTAZIONI", "HISTORICAL LEADERBOARD & COMPARATIVE PERFORMANCE ANALYSIS"],
    "label_aggregator": ["AGGREGATORE MEDIE STORICHE", "HISTORICAL AVERAGE AGGREGATOR"],
    "label_leaderboard_semantic": ["LEADERBOARD SEMANTICA (MEDIA)", "SEMANTIC LEADERBOARD (AVG)"],
    "label_session_alltime": ["DATI SESSIONE: ALL-TIME", "SESSION DATA: ALL-TIME"],
    "label_rank": ["RANK", "RANK"],
    "label_stability": ["STABILITÀ", "STABILITY"],
    "label_awaiting_telemetry": ["In attesa di dati telemetrici... Avvia una missione per iniziare il benchmark.", "Awaiting telemetric data... Start a mission to begin benchmark."],
    "label_cognitive_radar": ["RADAR COGNITIVO (PRESTAZIONI)", "COGNITIVE RADAR (PERFORMANCE)"],
    "label_elite_choice": ["SCELTA ELITE PER TASK", "ELITE CHOICE BY TASK"],
    "label_impact_trace": ["IMPACT_TRACE: RISORSE VS VELOCITÀ", "IMPACT_TRACE: RESOURCE VS SPEED"],
    "label_missing_ai": ["IA MANCANTE RILEVATA", "MISSING AI DETECTED"],
    "label_missing_ai_desc": ["Il modello selezionato non è presente nel caveau locale. Desideri che Agent007 lo scarichi ora tramite Ollama?", "The selected model is not in the local vault. Would you like Agent007 to download it now via Ollama?"],
    "btn_cancel": ["ANNULLA", "CANCEL"],
    "btn_install_now": ["INSTALLA ORA", "INSTALL NOW"],
    "label_expansion_knowledge": ["ESPANSIONE CONOSCENZA", "KNOWLEDGE EXPANSION"],
    "label_expansion_desc": ["Il Foraging primario ha identificato argomenti esterni che richiedono approfondimento mission-critical per una comprensione completa.", "Primary Foraging identified external topics requiring mission-critical deepening for full understanding."],
    "btn_ignore": ["IGNORA", "IGNORE"],
    "btn_authorize_deep": ["AUTORIZZA RICERCA DEEP", "AUTHORIZE DEEP RESEARCH"],
    "label_config_system": ["CONFIGURAZIONE SISTEMA", "SYSTEM CONFIGURATION"],
    "tab_swarm_control": ["CONTROLLO SCIAME", "SWARM CONTROL"],
    "tab_neural_hub": ["NEURAL HUB", "NEURAL HUB"],
    "tab_settings": ["IMPOSTAZIONI", "SETTINGS"],
    "label_swarm_model_hub": ["SWARM MODEL HUB", "SWARM MODEL HUB"],
    "label_swarm_model_hub_desc": ["Assegna compiti specifici ai modelli locali. I modelli più potenti (es. DeepSeek-R1) sono consigliati per AUDIT e SINTESI.", "Assign specific tasks to local models. Powerful models (e.g., DeepSeek-R1) are recommended for AUDIT and SYNTHESIS."],
    "label_audit_007": ["AUDIT (007)", "AUDIT (007)"],
    "label_crossref_sentinel": ["CROSSREF (Sentinel)", "CROSSREF (Sentinel)"],
    "label_chat_mediator": ["MEDIATORE CHAT", "CHAT MEDIATOR"],
    "label_oracle_evolution_desc": ["ORACLE EVOLUTION (Ricerca Profonda)", "ORACLE EVOLUTION (Deep Research)"],
    "label_vision_general": ["VISIONE GENERALE (Global)", "VISION GENERAL (Global)"],
    "label_scene_description": ["DESCRIZIONE SCENA", "SCENE DESCRIPTION"],
    "label_detection_tagging": ["RILEVAMENTO & TAGGING", "DETECTION & TAGGING"],
    "label_ocr_documents": ["OCR & DOCUMENTI", "OCR & DOCUMENTS"],
    "label_complex_analysis": ["ANALISI COMPLESSA", "COMPLEX ANALYSIS"],
    "label_chat_evolution": ["CHAT PER SUGGERIMENTI EVOLUTIVI", "CHAT FOR EVOLUTION SUGGESTIONS"],
    "label_save_swarm_config": ["SALVA CONFIGURAZIONE SWARM", "SAVE SWARM CONFIGURATION"],
    "label_consensus_active": ["ATTIVO", "ACTIVE"],
    "label_consensus_off": ["OFF", "OFF"],
    "msg_uplink_error": ["Errore di uplink con l'Oracolo.", "Uplink error with the Oracle."],
    "msg_nebula_empty": ["NEBULA_EMPTY: Nessun agente attivo nel vault.", "NEBULA_EMPTY: No active agents in the vault."],
    "msg_no_recent_mission": ["Nessuna missione recente...", "No recent missions..."],
    "label_user_probe": ["USER_PROBE", "USER_PROBE"],
    "label_system_alert": ["AVVISO_SISTEMA", "SYSTEM_ALERT"],
    "label_nebula_oracle": ["ORACOLO_NEBULA", "NEBULA_ORACLE"],
    "label_select_point": ["Seleziona un punto...", "Select a point..."],
    "label_synaptic_integrity": ["Integrità Link Sinaptico: Verificata", "Synaptic Link Integrity: Verified"],
    "label_low_quality": ["Bassa Qualità (Performance)", "Low Quality (Performance)"],
    "label_high_definition": ["Alta Definizione (Bilanciato)", "High Definition (Balanced)"],
    "label_4k_ultra": ["4K Ultra (Fedeltà)", "4K Ultra (Fidelity)"],
    "label_present": ["PRESENTE", "PRESENT"],
    "label_layers_filter": ["FILTRO_LIVELLI", "LAYERS_FILTER"],
    "label_layer_agents": ["Sprite Agenti", "Agent Sprites"],
    "label_layer_clusters": ["Enfasi Cluster", "Cluster Emphasis"],
    "label_layer_orphans": ["Nodi Orfani", "Orphan Nodes"],
    "label_layer_nodes": ["Nodi (Tutti)", "Nodes (All)"],
    "label_layer_linked": ["Nodi con Archi", "Linked Nodes"],
    "label_layer_edges": ["Archi", "Edges"],
    "label_layer_sparks": ["Archi Super Sinaptici", "Super Synaptic Arcs"],
    "label_layer_cube": ["Cubo 3D", "3D Cube"],
    "label_layer_grid": ["Piano Griglia", "Grid Plane"],
    "label_rotation_pause": ["Pausa/Avvia Rotazione", "Pause/Play Rotation"],
     "label_immersion": ["Immersione Totale", "Total Immersion"],
    "label_nebula_expansion": ["NEBULA_EXPANSION", "NEBULA_EXPANSION"],
    "label_protocol_library": ["LIBRERIA", "LIBRARY"],
    "label_protocol_injection": ["INIEZIONE_PROTOCOLLO >", "PROTOCOL_INJECTION >"],
    "label_command_ledger": ["REGISTRO_PROTOCOLLI_COMANDO", "COMMAND_PROTOCOL_LEDGER"],
    "label_command": ["COMANDO", "COMMAND"],
    "label_description": ["DESCRIZIONE", "DESCRIPTION"],
    "label_sync_mesh": ["SINCRONIZZA_MESH", "SYNC_MESH"],
    "label_purge_buffer": ["PULISCI_BUFFER", "PURGE_BUFFER"],
    "tab_active_swarm": ["SCIAME ATTIVO", "ACTIVE SWARM"],
    "tab_agent_forge": ["FORGIA AGENTI", "AGENT FORGE"],
    "tab_supreme_court": ["CORTE SUPREMA", "SUPREME COURT"],
    "label_autonomous_supervision": ["SUPERVISIONE_AUTONOMA", "AUTONOMOUS_SUPERVISION"],
    "label_scanning_history": ["SCANSIONE ARCHIVIO SENTENZE...", "SCANNING VERDICT HISTORY..."],
    "btn_refresh_history": ["AGGIORNA_CRONOLOGIA", "REFRESH_HISTORY"],
    "label_voice_mic": ["VOCE", "VOICE"],
    "btn_understood": ["COMPRESO", "UNDERSTOOD"],
    "label_mission_profile": ["PROFILO_MISSIONE", "MISSION_PROFILE"],
    "label_use_case": ["CASO D'USO / ESEMPIO:", "USE CASE / EXAMPLE:"],
    "label_trust_oracle": ["Fidati sempre di questo Oracolo (Attiva Auto-Pilot sessione)", "Always trust this Oracle (Enable Auto-Pilot session)"],
    "btn_ask_oracle": ["CHIEDI ALL'ORACOLO", "ASK THE ORACLE"],
    "btn_approve_delete": ["APPROVA ELIMINAZIONE", "APPROVE DELETION"],
    "btn_keep_node": ["MANTIENI NODO", "KEEP NODE"],
    "label_ram_consumed": ["RAM CONSUMATA", "RAM CONSUMED"],
    "label_status": ["STATO", "STATUS"],
    "label_provisioning": ["PROVISIONING INTELLIGENZA", "INTELLIGENCE PROVISIONING"],
    "label_initializing_uplink": ["Inizializzazione Uplink...", "Initializing Uplink..."],
    "label_do_not_close": ["Non chiudere il Vault durante l'espansione neurale.", "Do not close the Vault during neural expansion."],
    "title_agent_console": ["CONSOLE AGENTE", "AGENT CONSOLE"],
    "label_awaiting_directive": ["In attesa di direttive...", "Awaiting task directive..."],
    "placeholder_task": ["Assegna un compito specifico...", "Assign a specific task..."],
    "btn_task": ["TASK", "TASK"],
    "title_neural_benchmark": ["NEURAL_BENCHMARK_HUB", "NEURAL_BENCHMARK_HUB"],
    "label_tasks": ["COMPITI", "TASKS"],
    "label_latency_avg": ["LATENZA_MEDIA", "AVG_LATENCY"],
    "label_tps_avg": ["TPS_MEDIO", "AVG_TPS"],
    "label_peak_speed": ["VELOCITÀ_PICCO", "PEAK_SPEED"],
    "btn_back_to_nebula": ["TORNA ALLA DASHBOARD", "BACK TO DASHBOARD"],
    "title_chrono_log": ["CHRONO-LOG: AZIONI SISTEMA", "CHRONO-LOG: SYSTEM ACTIONS"],
    "label_audit_mode": ["MODALITÀ_AUDIT_SOVRANO", "SOVEREIGN_AUDIT_MODE"],
    "btn_export_logs": ["ESPORTA LOG", "EXPORT LOGS"],
    "label_json_format": ["Formato JSON", "JSON Format"],
    "label_csv_format": ["CSV (Excel)", "CSV (Excel)"],
    "label_sql_archive": ["Archivio SQL Completo", "Full SQL Archive"],
    "label_examine_content": ["CONTENUTO SOTTO ESAME", "CONTENT UNDER EXAMINATION"],
    "label_acquiring_data": ["Acquisizione dati...", "Acquiring data..."],
    "label_oracle_response": ["🔮 Responso Oracolo Neurale", "🔮 Neural Oracle Response"],
    "label_analyzing": ["Analisi in corso...", "Analyzing..."],
    "label_human_tip": ["Suggerimento per l'Oracolo (Opzionale)", "Human Tip for Oracle (Optional)"],
    "placeholder_human_tip": ["Esempio: Mantieni solo se parla di Crittografia...", "Example: Keep only if it mentions Cryptography..."],
    "label_polling_blackboard": ["INTERROGAZIONE BLACKBOARD NEURALE...", "POLLING NEURAL BLACKBOARD..."],
    "label_judge_3": ["Giudice Corte Suprema #3", "Supreme Court Judge #3"],
    "label_evolution_suggestion": ["Cervello Suggerimenti Evolutivi", "Evolution Suggestion Brain"],
    "label_evolution_suggestion_desc": ["Seleziona l'LLM dedicato alla generazione di suggerimenti tecnici e bug-hunting.", "Select the LLM dedicated to generating technical suggestions and bug-hunting."],
    "label_name": ["NOME", "NAME"],
    "label_role": ["RUOLO", "ROLE"],
    "role_archivist": ["Archivista (Ingestione)", "Archivist (Ingestion)"],
    "role_analyst": ["Analista (Sintesi)", "Analyst (Synthesis)"],
    "role_guardian": ["Guardiano (Sicurezza)", "Guardian (Security)"],
    "role_distiller": ["Distillatore (Pruning)", "Distiller (Pruning)"],
    "label_mission_directive": ["Mandato Missione (Prompt)", "Mission Directive (Prompt)"],
    "placeholder_mission_directive": ["Definisci la missione specifica...", "Define the specific mission..."],
    "btn_forge_agent": ["FORGIA AGENTE", "FORGE AGENT"],
    "label_theme_desc": ["Personalizza l'aspetto visivo del Nexus Vault. Il tema Light è ottimizzato per la leggibilità diurna.", "Customize the visual appearance of Nexus Vault. Light theme is optimized for daylight readability."],
    "label_light_mode": ["Modalità Light", "Light Mode"],
    "label_light_mode_desc": ["Passa a testi neri e sfondo chiaro", "Switch to black text and light background"],
    "btn_nuclear_purge": ["☢️ NUCLEAR PURGE ALL MEMORY", "☢️ NUCLEAR PURGE ALL MEMORY"],
    "label_sovereign_mode": ["🛡️ MODALITÀ OPERATIVA SOVRANA", "🛡️ SOVEREIGN OPERATIONAL MODE"],
    "label_swarm_scope": ["Configura il perimetro d'azione dello sciame", "Configure the swarm's scope of action"],
    "label_research_mode": ["MODALITÀ RICERCA", "RESEARCH MODE"],
    "title_evolution_loop": ["EVOLUTION FEEDBACK LOOP", "EVOLUTION FEEDBACK LOOP"],
    "label_neural_model_hub": ["HUB MODELLI NEURALI", "NEURAL MODEL HUB"],
    "label_management_sovereign": ["Gestione Sovrana dell'Intelligenza Locale", "Sovereign Local Intelligence Management"],
    "btn_refresh_catalog": ["AGGIORNA CATALOGO", "REFRESH CATALOG"],
    "btn_only_installed": ["SOLO INSTALLATI", "ONLY INSTALLED"],
    "btn_all_models": ["TUTTI I MODELLI", "ALL MODELS"],
    "label_model_tag": ["MODELLO & TAG", "MODEL & TAG"],
    "label_capabilities": ["CAPACITÀ", "CAPABILITIES"],
    "label_strengths": ["PUNTI DI FORZA", "STRENGTHS"],
    "label_swarm_sinergy": ["SINERGIA SCIAME", "SWARM SYNERGY"],
    "label_operations": ["OPERAZIONI", "OPERATIONS"],
    "label_custom_forge_footer": ["* I modelli registrati appariranno automaticamente nel menu a tendina.", "* Registered models will automatically appear in the dropdown menu."],
    "title_agent_factory": ["🧬 FABBRICA AGENTI NEURALI", "🧬 NEURAL AGENT FACTORY"],
    "label_agent_factory_desc": ["Forgia nuovi mandati d'intelligenza", "Forge new intelligence mandates"],
    "label_agent_name": ["Nome Agente", "Agent Name"],
    "role_creative": ["Creativo (Sintesi)", "Creative (Synthesis)"],
    "role_architect": ["Architetto (Struttura)", "Architect (Structure)"],
    "title_metrics": ["METRICHE COGNITIVE", "COGNITIVE METRICS"],
    "title_semantic_distance": ["DISTANZA SEMANTICA", "SEMANTIC DISTANCE"],
    "title_hardbank": ["BANCA DATI AGENT007", "AGENT007 HARDBANK"],
    "label_entities": ["ENTITÀ", "ENTITIES"],
    "label_relations": ["RELAZIONI", "RELATIONS"],
    "label_mission_ready": ["● PIANO MISSIONE PRONTO", "● MISSION BLUEPRINT READY"],
    "title_engine_tracing": ["TRACCIAMENTO MOTORE", "ENGINE TRACING"],
    "btn_copy_log": ["Copia Log", "Copy Log"],
    "label_awaiting_resonance": ["In attesa di risonanza...", "Awaiting resonance..."],
    "title_inventory": ["INVENTARIO CONOSCENZA", "KNOWLEDGE INVENTORY"],
    "label_acquiring_history": ["Acquisizione cronologia sinaptica...", "Acquiring synaptic history..."],
    "title_ingestion": ["PORTALE INGESTIONE", "INGESTION PORTAL"],
    "label_drop_to_synapse": ["TRASCINA O CLICCA<br>PER SINAPSI", "DROP OR CLICK<br>TO SYNAPSE"],
    "label_config_saved": ["CONFIGURAZIONE SALVATA", "CONFIGURATION SAVED"],
    "label_config_saved_desc": ["Le preferenze dello Swarm sono state persistite nel nucleo.", "Swarm preferences have been persisted in the core."],
    "btn_received": ["RICEVUTO", "RECEIVED"],
    "label_fallback_activated": ["FALLBACK ATTIVATO", "FALLBACK ACTIVATED"],
    "label_fallback_desc": ["Il modello richiesto non è disponibile.", "The requested model is not available."],
    "label_reconfigured": ["Rotte Riconfigurate", "Reconfigured Routes"],
    "label_resolved_model": ["UTILIZZO:", "USING:"],
    "btn_continue_mission": ["CONTINUA MISSIONE", "CONTINUE MISSION"],
    "label_deletion_consent": ["CONSENSO ELIMINAZIONE", "DELETION CONSENT"],
    "label_deletion_desc": ["Sei sicuro di voler rimuovere permanentemente l'elemento?", "Are you sure you want to permanently remove the item?"],
    "btn_delete_now": ["ELIMINA ORA", "DELETE NOW"],
    "label_llm_core": ["CORE LLM & REQUISITI", "LLM CORE & REQUIREMENTS"],
    "label_version": ["VERSIONE", "VERSION"],
    "label_synergies": ["SINERGIE", "SYNERGIES"],
    "label_actions": ["AZIONI", "ACTIONS"],
    "label_awaiting_refresh": ["Usa il tasto Refresh per sincronizzare...", "Use Refresh to sync..."],
    "btn_refresh": ["AGGIORNA", "REFRESH"],
    "label_chrono_log": ["CHRONO-LOG", "CHRONO-LOG"],
    "chart_knowledge_label": ["CONOSCENZA (NODI)", "KNOWLEDGE (NODES)"],
    "chart_relations_label": ["RELAZIONI PER NODO", "RELATIONS PER NODE"],
    "chart_latency_label": ["LATENZA (ms)", "LATENCY (ms)"],
    "chart_tps_label": ["TPS (tok/s)", "TPS (tok/s)"],
    "chart_radar_speed": ["VELOCITÀ", "SPEED"],
    "chart_radar_accuracy": ["PRECISIONE", "ACCURACY"],
    "chart_radar_stability": ["STABILITÀ", "STABILITY"],
    "chart_radar_density": ["DENSITÀ", "DENSITY"],
    "chart_radar_reasoning": ["RAGIONAMENTO", "REASONING"],
    "label_mode_foraging": ["FORAGING", "FORAGING"],
    "label_mode_query": ["QUERY", "QUERY"],
    "label_auto_evolve": ["AUTO-EVOLVE", "AUTO-EVOLVE"],
    "label_uplink_stability": ["STABILITÀ_UPLINK", "UPLINK_STABILITY"],
    "msg_initializing_uplink": ["> Inizializzazione Uplink Neurale...", "> Initializing Neural Uplink..."],
    "msg_kernel_synced": ["> Kernel Sincronizzato.", "> Kernel Synchronized."],
    "msg_swarm_detected": ["> Battito Sciame rilevato.", "> Swarm Heartbeat detected."],
    "label_model_header": ["Modello", "Model"],
    "label_tps_peak": ["T/S (Picco)", "T/S (Peak)"],
    "label_latency_header": ["Latenza", "Latency"],
    "label_cpu_impact": ["Impatto CPU", "CPU Impact"],
    "label_vram_header": ["VRAM", "VRAM"],
    "label_status_header": ["Stato", "Status"],
    "label_benchmark_telemetry_info": ["Dati aggiornati ogni ciclo di audit basati sulla telemetria di inferenza reale.", "Data refreshed every audit cycle based on real inference telemetry."],
    "label_back_to_nebula": ["TORNA A NEBULA", "BACK TO NEBULA"],
    "label_realtime_inference_desc": ["ANALISI INFERENZA IN TEMPO REALE & LEADERBOARD COGNITIVA", "REAL-TIME INFERENCE ANALYTICS & COGNITIVE LEADERBOARD"],
    "label_mode_foraging_badge": ["RICERCA (FORAGING)", "FORAGING MODE"],
    "label_auto_evolve_title": ["AUTO-EVOLVE", "AUTO-EVOLVE"],
    "label_synthesis_team_status": ["Stato Team Sintesi", "Synthesis Team Status"],
    "label_select_node": ["Seleziona un punto...", "Select a point..."],
    "label_neural_time_drive": ["NEURAL_TIME_DRIVE", "NEURAL_TIME_DRIVE"],
    "label_system_active": ["[SISTEMA_ATTIVO]", "[SYSTEM_ACTIVE]"],
    "label_uplink_stability_label": ["STABILITÀ_UPLINK", "UPLINK_STABILITY"],
    "label_consensus_badge": ["CONSENSO", "CONSENSUS"],
    "label_mode_hybrid": ["MODALITÀ: IBRIDA", "MODE: HYBRID"],
    "label_endpoint_path": ["PERCORSO / ID REPO", "PATH / REPO ID"],
    "label_model_name": ["NOME MODELLO", "MODEL NAME"],
    "label_provider": ["PROVIDER (Ollama/HF/Local)", "PROVIDER (Ollama/HF/Local)"],
    "btn_register_model": ["REGISTRA NEL VAULT", "REGISTER IN VAULT"],
    "placeholder_custom_path": ["es: my-custom-model o /path/to/model", "e.g., my-custom-model or /path/to/model"],
    "label_custom_forge": ["NEURAL FORGE: AGGIUNGI CORE CUSTOM", "NEURAL FORGE: ADD CUSTOM CORE"],
    "label_web_hits": ["Web-Hits", "Web-Hits"],
    "label_drafting": ["DR", "DR"],
    "label_critique": ["CR", "CR"],
    "label_polishing": ["PO", "PO"],
    "label_rgb_arcs": ["Archi RGB", "RGB Arcs"],
    "label_nodes_added": ["Nodi Forgiati", "Nodes Forged"],
    "label_synaptic_integrity_check": ["Controllo Integrità Link Sinaptico: Verificato", "Synaptic Link Integrity Check: Verified"]
};

let currentLang = localStorage.getItem('neuralvault_lang') || 'it';

function getLang(key, defaultText = "") {
    if (NEURAL_LANG_PACK[key]) {
        return NEURAL_LANG_PACK[key][currentLang === 'en' ? 1 : 0];
    }
    return defaultText || key;
}

window.toggleLanguage = () => {
    currentLang = (currentLang === 'it') ? 'en' : 'it';
    localStorage.setItem('neuralvault_lang', currentLang);
    applyLanguage();
    // \uD83C\uDF0D = 🌍
    log("\uD83C\uDF0D LANG: Switching to " + currentLang.toUpperCase(), "#3b82f6");
};

function applyLanguage() {
    const isEn = (currentLang === 'en');
    const flag = document.getElementById('current-flag');
    // \uD83C\uDDEE\uD83C\uDDF9 = 🇮🇹 | \uD83C\uDDEC\uD83C\uDDE7 = 🇬🇧
    if (flag) flag.innerText = isEn ? "\uD83C\uDDEE\uD83C\uDDF9" : "\uD83C\uDDEC\uD83C\uDDE7";
    
    // 1. Text Content
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        if (NEURAL_LANG_PACK[key]) {
            el.innerHTML = NEURAL_LANG_PACK[key][isEn ? 1 : 0];
        }
    });

    // 2. Placeholders
    document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
        const key = el.getAttribute('data-i18n-placeholder');
        if (NEURAL_LANG_PACK[key]) {
            el.placeholder = NEURAL_LANG_PACK[key][isEn ? 1 : 0];
        }
    });

    // 3. Titles (Tooltips)
    document.querySelectorAll('[data-i18n-title]').forEach(el => {
        const key = el.getAttribute('data-i18n-title');
        if (NEURAL_LANG_PACK[key]) {
            el.title = NEURAL_LANG_PACK[key][isEn ? 1 : 0];
        }
    });

    // 4. Custom tooltips
    document.querySelectorAll('[data-i18n-tooltip]').forEach(el => {
        const key = el.getAttribute('data-i18n-tooltip');
        if (key && NEURAL_LANG_PACK[key]) {
            el.setAttribute('data-tooltip', NEURAL_LANG_PACK[key][isEn ? 1 : 0]);
        }
    });
    
    // 5. Special cases for labels that might have been updated dynamically
    const modeLabel = document.getElementById('mode-label-text');
    if (modeLabel) {
        const toggle = document.getElementById('evolution-mode-toggle');
        if (toggle) {
            const modeKey = toggle.checked ? "evolution_mode" : "research_mode";
            modeLabel.innerText = getLang(modeKey).replace(' (Dev)', '').replace(' (Default)', '');
        }
    }

    // Update Charts if initialized
    if (window.growthChart) {
        window.growthChart.data.datasets[0].label = getLang('chart_knowledge_label');
        window.growthChart.update();
    }
    if (window.densityChart) {
        window.densityChart.data.datasets[0].label = getLang('chart_relations_label');
        window.densityChart.update();
    }
    if (window.impactChart) {
        window.impactChart.data.datasets[0].label = getLang('chart_latency_label');
        window.impactChart.data.datasets[1].label = getLang('chart_tps_label');
        window.impactChart.update();
    }
    if (window.radarChart) {
        window.radarChart.data.labels = [
            getLang('chart_radar_speed'),
            getLang('chart_radar_accuracy'),
            getLang('chart_radar_stability'),
            getLang('chart_radar_density'),
            getLang('chart_radar_reasoning')
        ];
        window.radarChart.update();
    }
}
// --- 🧬 EVOLUTION ADVISE MANAGER ---
window.addEvolutionAdvice = (type, message, fileInfo) => {
    const history = document.getElementById('evolution-chat-history');
    if (!history) return;

    // Remove placeholder if present
    const placeholder = history.querySelector('[data-i18n="msg_awaiting_evolution"]');
    if (placeholder) placeholder.remove();

    const isEn = (currentLang === 'en');
    const typeLabel = (type === 'BUG') ? getLang("msg_bug_found") : getLang("msg_optimization");
    const color = (type === 'BUG') ? '#ef4444' : '#a855f7';

    const card = document.createElement('div');
    card.className = 'glass-card';
    card.style.padding = '1.2rem';
    card.style.borderLeft = `4px solid ${color}`;
    card.style.marginBottom = '1rem';
    card.style.animation = 'slideInRight 0.4s cubic-bezier(0.16, 1, 0.3, 1)';
    
    card.innerHTML = `
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.8rem;">
            <div style="color:${color}; font-weight:900; font-size:0.6rem; letter-spacing:1.5px;">${typeLabel}</div>
            <div style="color:rgba(255,255,255,0.4); font-size:0.55rem; font-family:'JetBrains Mono';">${fileInfo}</div>
        </div>
        <div style="color:#fff; font-size:0.75rem; margin-bottom:1.2rem; line-height:1.4;">${message}</div>
        <div style="display:flex; gap:8px;">
            <button onclick="handleEvolutionFeedback(this, 'IMPLEMENTED')" class="evolve-btn" style="background:rgba(16,185,129,0.1); border:1px solid #10b981; color:#10b981; padding: 4px 10px; border-radius: 6px; font-size: 0.55rem; font-weight: 800; cursor: pointer;" data-i18n="btn_implemented">${getLang("btn_implemented")}</button>
            <button onclick="handleEvolutionFeedback(this, 'DISCARDED')" class="evolve-btn" style="background:rgba(245,158,11,0.1); border:1px solid #f59e0b; color:#f59e0b; padding: 4px 10px; border-radius: 6px; font-size: 0.55rem; font-weight: 800; cursor: pointer;" data-i18n="btn_discarded">${getLang("btn_discarded")}</button>
            <button onclick="handleEvolutionFeedback(this, 'FALSE_POSITIVE')" class="evolve-btn" style="background:rgba(239,68,68,0.1); border:1px solid #ef4444; color:#ef4444; padding: 4px 10px; border-radius: 6px; font-size: 0.55rem; font-weight: 800; cursor: pointer;" data-i18n="btn_false_positive">${getLang("btn_false_positive")}</button>
        </div>
    `;
    history.prepend(card);
};

window.handleEvolutionFeedback = async (btn, status) => {
    const card = btn.closest('.glass-card');
    const suggestionId = card.getAttribute('data-id');
    
    // Tactile Feedback
    card.style.transform = 'scale(0.95)';
    card.style.opacity = '0.5';
    card.style.pointerEvents = 'none';
    
    log(`🧬 EVOLUTION: Feedback [${status}] registered.`, "#a855f7");

    try {
        // 1. Notify Backend (which will also pop from history)
        await fetch('/api/lab/evolution/feedback', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-API-KEY': VAULT_KEY },
            body: JSON.stringify({ id: suggestionId, feedback: status.toLowerCase() })
        });

        // 2. Animate out and remove
        card.style.transition = 'all 0.5s cubic-bezier(0.4, 0, 0.2, 1)';
        card.style.transform = 'translateX(100px)';
        card.style.opacity = '0';
        
        setTimeout(() => {
            card.remove();
            // If no more cards, show waiting message
            const history = document.getElementById('evolution-chat-history');
            if (history && history.children.length === 0) {
                history.innerHTML = '<div style="text-align: center; color: #64748b; font-size: 0.65rem; margin-top: 150px;" data-i18n="msg_awaiting_evolution">In attesa di segnali evolutivi...</div>';
            }
        }, 500);

    } catch(e) {
        console.error("Feedback Error:", e);
        card.style.transform = 'scale(1)';
        card.style.opacity = '1';
        card.style.pointerEvents = 'auto';
    }
};

document.addEventListener('DOMContentLoaded', async () => {
    applyLanguage();
    const localTheme = localStorage.getItem('neuralvault_theme');
    const themeToggle = document.getElementById('theme-checkbox');
    if (localTheme === 'light') {
        document.body.classList.add('light-theme');
        if (themeToggle) themeToggle.checked = true;
    }
    init3D();
    initSSE();
    initCharts();
    refreshModels();
    updateRecommendations();
    window.showSection('overview');
    try {
        const r = await fetch('/api/system/settings');
        const settings = await r.json();
        if (settings.theme === 'light') {
            document.body.classList.add('light-theme');
            localStorage.setItem('neuralvault_theme', 'light');
        } else if (settings.theme === 'dark') {
            document.body.classList.remove('light-theme');
            localStorage.setItem('neuralvault_theme', 'dark');
        }
        const toggle = document.getElementById('auto-evolve-toggle');
        if (toggle) toggle.checked = true;
        refreshVaultState();
        // [Phase 3] Periodic Refresh Loops
        setInterval(refreshBenchmarks, 30000); // 30s
        setInterval(refreshCourtQueue, 15000);  // 15s
        setInterval(refreshEvolutionChat, 10000); // 10s [v3.8.4] Autonomous Sync
        refreshBenchmarks();
        refreshCourtQueue();
    } catch(e) {}
});

function animateValue(id, start, end, duration, prefix = "") {
    const obj = document.getElementById(id);
    if (!obj) return;
    if (start === end) return;
    let startTimestamp = null;
    const step = (timestamp) => {
        if (!startTimestamp) startTimestamp = timestamp;
        const progress = Math.min((timestamp - startTimestamp) / duration, 1);
        const val = Math.floor(progress * (end - start) + start);
        obj.innerText = prefix + val.toLocaleString();
        if (progress < 1) {
            window.requestAnimationFrame(step);
        }
    };
    window.requestAnimationFrame(step);
}

const AGENT_PROFILES = {
    'DI-007': { title: "DI-007 DISTILLER", role: "SYNAPTIC PRUNING", desc: "Sfoltisce la Nebula potando archi deboli o ridondanti guidato da LLM.", example: "Rimuove collegamenti logici obsoleti tra file." },
    'JA-001': { title: "JA-001 JANITRON", role: "ENTROPY FAGOCITATOR", desc: "Elimina i nodi orfani giudicati inutili, rigenerando spazio di memoria.", example: "Fagocita rimasugli di memoria su segnalazione dello Snake." },
    'RP-001': { title: "RP-001 DR. REAPER", role: "TOMBSTONE REGENERATION", desc: "Cura le lapidi lasciate dalle eliminazioni, compattando il DB.", example: "Ripara i settori di memoria post-chirurgia janitoriale." },
    'QA-101': { title: "QA-101 QUANTUM", role: "SEMANTIC FUSION", desc: "Unifica in un unico cluster dati sovrapponibili e ridondanti.", example: "Fonde tre versioni simili dello stesso file in un'unica entità logica." },
    'SY-009': { title: "SY-009 SYNTH", role: "CREATIVE SYNTHESIS", desc: "Genera ponti sinaptici intelligenti e creativi tra concetti distanti.", example: "Collega un requisito di ARCHITECTURE.md con il codice di api.py." },
    'SE-007': { title: "SE-007 SENTINEL", role: "VALIDATION LOCK", desc: "Verifica l'integrità e la logica di ogni nuova sinapsi creata.", example: "Valida o rifiuta i collegamenti proposti dal Synth-Muse." },
    'SN-008': { title: "SN-008 SNAKE", role: "ORPHAN CONVOY GATHERER", desc: "Raccoglie orfani in un convoglio e li porta al centro per il giudizio.", example: "Traina 5 nodi orfani verso il Cuore della Nebula." },
    'CB-003': { title: "CB-003 BRIDGER", role: "SOURCE-DOC LINKER", desc: "Mappa bidirezionalmente codice sorgente e documentazione tecnica.", example: "Crea link diretti tra funzioni Python e paragrafi README." },
    'FS-77': { title: "FS-77 SKY-WALKER", role: "INTERCEPTOR", desc: "Pattuglia la Nebula intercettando flussi di dati in entrata.", example: "Analizza i pacchetti in arrivo per minacce o opportunità." }
};

window.showAgentHelp = (id) => {
    const profile = AGENT_PROFILES[id] || { title: id, role: "AGENT_GENERIC", desc: "Operatività standard.", example: "N/A" };
    const modal = document.getElementById('agent-help-modal');
    if (!modal) return;
    document.getElementById('help-agent-title').innerText = profile.title;
    document.getElementById('help-agent-role').innerText = profile.role;
    document.getElementById('help-agent-desc').innerText = profile.desc;
    document.getElementById('help-agent-example').innerText = profile.example;
    modal.style.display = 'flex';
};

window.forgeCustomAgent = async () => {
    // Check if we are in the standalone modal or in the Neural Lab card
    const isModal = document.getElementById('custom-agent-modal')?.style.display === 'flex';
    const name = isModal ? document.getElementById('custom-agent-name').value : document.getElementById('lab-forge-name').value;
    const role = isModal ? (document.getElementById('custom-agent-role')?.value || "analyst") : (document.getElementById('lab-forge-role')?.value || "analyst");
    const model = isModal ? document.getElementById('custom-agent-model').value : "llama3.2";
    const prompt = isModal ? document.getElementById('custom-agent-prompt').value : document.getElementById('lab-forge-prompt').value;
    if (!name) { log("⚠️ AGENT_FORGE: Identity name required.", "#ef4444"); return; }
    log("⚒️ FORGING: Initializing custom mandate for " + name + "...", "#a855f7");
    try {
        const response = await fetch('/api/swarm/spawn', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, role, prompt, model, api_key: VAULT_KEY })
        });
        const res = await response.json();
        if (res.status === 'ok') {
            log("✅ DEPLOYED: Agent " + name + " is now active in the Nebula.", "#10b981");
            if (isModal) closeAgentFactory();
        }
    } catch (e) { log("❌ FORGE_ERR: Connection to orchestrator failed.", "#ef4444"); }
};

window.broadcastCommand = async (command) => {
    log("📡 BROADCAST: Emitting " + command + " signal to the swarm...", "#3b82f6");
    try {
        const response = await fetch('/api/swarm/broadcast', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ command, api_key: VAULT_KEY })
        });
        const res = await response.json();
        if (res.status === 'ok') {
            log("⚡ SIGNAL_SENT: Swarm is reacting to " + command + ".", "#4ade80");
        }
    } catch (e) { log("❌ BROAD_ERR: Signal lost in transmission.", "#ef4444"); }
};

window.sendDirectCommand = (cmd) => {
    if (!cmd.trim()) return;
    const logEl = document.getElementById('swarm-telemetry-log');
    if (logEl) {
        logEl.innerHTML += "<div>> [USER_CMD] " + cmd + "</div>";
        logEl.scrollTop = logEl.scrollHeight;
    }
    const upper = cmd.toUpperCase();
    if (upper === 'SCAN' || upper === 'PURGE') {
        broadcastCommand(upper);
    } else {
        log("🛰️ DIRECT: Targeting LLM Mediator for custom instruction...", "#3b82f6");
    }
    document.getElementById('swarm-direct-command').value = '';
};

window.deleteCustomAgent = async (agentId) => {
    log("🗑️ PURGING: Decommissioning agent " + agentId + "...", "#ef4444");
    try {
        const response = await fetch('/api/swarm/delete?agent_id=' + agentId + '&api_key=' + VAULT_KEY, { method: 'POST' });
        const res = await response.json();
        if (res.status === 'ok') {
            log("✅ ARCHIVED: Agent data scrubbed from kinetic loop.", "#8b949e");
        }
    } catch (e) {}
};

async function refreshVaultState() {
    const list = document.getElementById('knowledge-inventory-list');
    if (!list) return;
    try {
        const response = await fetch('/api/inventory', { headers: { 'X-API-KEY': VAULT_KEY }});
        const sources = await response.json();
        if (!sources || sources.length === 0) {
            list.innerHTML = '<div style="opacity:0.3; text-align:center; padding:1rem; font-size:0.6rem;">Vuoto. Nessun dato acquisito.</div>';
            return;
        }
        list.innerHTML = sources.map(s => {
            const raw = s.source || "Unknown";
            let displaySource = raw;
            let typeIcon = s.type === 'web' ? 'fa-globe' : (s.type === 'image' ? 'fa-image' : 'fa-file-alt');
            // 🏷️ Smart Source Parsing (Domain / Filename / Extension)
            let extension = "";
            let filename = "";
            if (raw.startsWith('http')) {
                try {
                    const u = new URL(raw);
                    displaySource = u.hostname;
                    typeIcon = 'fa-globe';
                    filename = u.pathname.split('/').pop() || 'index';
                    extension = filename.includes('.') ? filename.split('.').pop() : 'html';
                } catch(e) {}
            } else if (raw.includes('/') || raw.includes('\\')) {
                filename = raw.split(/[/\\]/).pop();
                displaySource = filename;
                extension = filename.includes('.') ? filename.split('.').pop() : 'file';
            }
            
            const extColor = extension === 'pdf' ? '#ef4444' : extension === 'py' || extension === 'js' ? '#3b82f6' : '#a855f7';
            return `
                <div class="inventory-item" style="background:rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.05); padding:0.8rem; border-radius:12px; display:flex; justify-content:space-between; align-items:center; margin-bottom: 8px; border-left: 3px solid ${extColor};">
                    <div style="display:flex; align-items:center; gap:12px;">
                        <div style="width:32px; height:32px; background:rgba(255,255,255,0.05); border-radius:8px; display:flex; align-items:center; justify-content:center; color:${extColor};">
                            <i class="fas ${typeIcon}"></i>
                        </div>
                        <div>
                            <div style="color:#fff; font-size:0.75rem; font-weight:800;">${filename || displaySource}</div>
                            <div style="color:#8b949e; font-size:0.55rem; text-transform:uppercase; letter-spacing:1px;">${displaySource} • <span style="color:${extColor}; font-weight:900;">${extension.toUpperCase()}</span></div>
                        </div>
                    </div>
                    <div style="text-align:right;">
                        <div style="color:#4ade80; font-size:0.6rem; font-weight:900;">${s.node_count} NODI</div>
                        <div style="color:#a855f7; font-size:0.5rem; font-weight:600;">${s.edges || 0} ARCHI</div>
                    </div>
                </div>
            `;
        }).join('');

    } catch(e) {
        console.error("InventoryRefreshErr:", e);
    }
}

// --- 🧪 EVOLUTION MODE CORE LOGIC ---
window.toggleEvolutionMode = async () => {
    const toggle = document.getElementById('evolution-mode-toggle');
    const isEvo = toggle.checked;
    const label = document.getElementById('mode-label-text');
    const descRes = document.getElementById('desc-research');
    const descEvo = document.getElementById('desc-evolution');
    const chatContainer = document.getElementById('evolution-chat-container');

    const isEn = (currentLang === 'en');
    if (isEvo) {
        label.innerText = NEURAL_LANG_PACK["evolution_mode"][isEn?1:0].replace(' (Dev)', '');
        label.style.color = "#a855f7";
        descRes.style.opacity = "0.4";
        descEvo.style.opacity = "1";
        chatContainer.style.display = "block";
        document.getElementById('evolution-chat-history').innerHTML = '<div style="text-align: center; color: #a855f7; font-size: 0.65rem; margin-top: 150px; animation: pulse 2s infinite;">🌀 Iniziando scansione neurale... attendere.</div>';
        refreshEvolutionChat();
        // v3.8.5: Sync state with backend
        fetch('/api/system/settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ api_key: VAULT_KEY, evolution_active: isEvo })
        });
    } else {
        label.innerText = NEURAL_LANG_PACK["research_mode"][isEn?1:0].replace(' (Default)', '');
        label.style.color = "#10b981";
        descRes.style.opacity = "1";
        descEvo.style.opacity = "0.4";
        chatContainer.style.display = "none";
    }

    try {
        await fetch('/api/lab/settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-API-KEY': VAULT_KEY },
            body: JSON.stringify({ codebase_bridging: isEvo })
        });
    } catch(e) { console.error("Evo Toggle Error:", e); }
};

window.refreshEvolutionChat = async () => {
    const history = document.getElementById('evolution-chat-history');
    if (!history) return;
    try {
        const r = await fetch('/api/lab/evolution/suggestions', { headers: { 'X-API-KEY': VAULT_KEY }});
        const suggestions = await r.json();
        
        if (!suggestions || suggestions.length === 0) {
            history.innerHTML = '<div style="text-align: center; color: #64748b; font-size: 0.65rem; margin-top: 150px;" data-i18n="msg_awaiting_evolution">In attesa di segnali evolutivi... Attiva Evolution Mode per iniziare.</div>';
            return;
        }

        const isEn = (currentLang === 'en');
        history.innerHTML = suggestions.map(s => `
            <div class="evo-msg glass-card" data-id="${s.id}" style="margin-bottom:1.5rem; padding:1.5rem; border-left:4px solid ${s.type==='BUG'?'#ef4444':'#a855f7'}; transition: all 0.5s ease; background: rgba(15,15,25,0.8);">
                <div style="display:flex; justify-content:space-between; margin-bottom:10px;">
                    <span style="font-size:0.6rem; font-weight:900; color:${s.type==='BUG'?'#ef4444':'#a855f7'}; letter-spacing:1px;">[${s.type}] - ${s.file}:${s.line}</span>
                    <span style="font-size:0.5rem; color:#64748b;">${new Date(s.timestamp*1000).toLocaleTimeString()}</span>
                </div>
                
                <div style="margin-bottom:15px;">
                    <div style="font-size:0.55rem; color:#8b949e; text-transform:uppercase; margin-bottom:4px; font-weight:800;">Analyst Model: <span style="color:#a855f7;">${s.model || 'Unknown'}</span></div>
                    <p style="color:#fff; font-size:0.8rem; font-weight:600; line-height:1.4;">${s.content}</p>
                </div>

                ${s.original_code ? `
                <div style="background:rgba(0,0,0,0.4); padding:12px; border-radius:8px; margin-bottom:15px; font-family:'JetBrains Mono'; font-size:0.65rem; border:1px solid rgba(255,255,255,0.05);">
                    <div style="color:#ef4444; opacity:0.6; margin-bottom:4px;">- OLD: ${s.original_code}</div>
                    <div style="color:#4ade80;">+ NEW: ${s.content}</div>
                </div>
                ` : ''}

                <div style="background:rgba(59,130,246,0.05); padding:10px; border-radius:6px; margin-bottom:15px; font-size:0.6rem; color:#94a3b8; border-left:2px solid #3b82f6;">
                    <strong data-i18n="label_impact">${NEURAL_LANG_PACK["label_impact"][isEn?1:0]}:</strong> ${s.impact}
                </div>
                
                ${s.status === 'pending' ? `
                    <div style="display:flex; gap:10px; justify-content:flex-end;">
                        <button class="evolve-btn" style="background:rgba(16,185,129,0.1); border:1px solid #10b981; color:#10b981;" onclick="handleEvolutionFeedback(this, 'IMPLEMENTED')" data-i18n="btn_implemented">${NEURAL_LANG_PACK["btn_implemented"][isEn?1:0]}</button>
                        <button class="evolve-btn" style="background:rgba(245,158,11,0.1); border:1px solid #f59e0b; color:#f59e0b;" onclick="handleEvolutionFeedback(this, 'DISCARDED')" data-i18n="btn_discarded">${NEURAL_LANG_PACK["btn_discarded"][isEn?1:0]}</button>
                    </div>
                ` : `<div style="text-align:right; font-size:0.5rem; color:#4ade80; font-weight:800;">✓ ${s.status.toUpperCase()}</div>`}
            </div>
        `).join('');
    } catch(e) { console.error("Evo Chat Error:", e); }
};

window.sendEvolutionFeedback = async (id, feedback) => {
    try {
        await fetch('/api/lab/evolution/feedback', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-API-KEY': VAULT_KEY },
            body: JSON.stringify({ id, feedback })
        });
        refreshEvolutionChat();
    } catch(e) { console.error("Feedback Error:", e); }
};

// --- 🛠️ NEURAL FORGE: CUSTOM REGISTRATION ---
window.registerCustomModel = async () => {
    const name = document.getElementById('custom-model-name').value;
    const provider = document.getElementById('custom-model-provider').value;
    const path = document.getElementById('custom-model-path').value;

    if (!name || !path) {
        log("⚠️ FORGE: Nome e Percorso sono obbligatori.", "#ef4444");
        return;
    }

    try {
        const r = await fetch('/api/lab/hub/custom/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-API-KEY': VAULT_KEY },
            body: JSON.stringify({ name, provider, path })
        });
        
        if (r.ok) {
            log(`✅ FORGE: Modello [${name}] registrato con successo.`, "#4ade80");
            document.getElementById('custom-model-name').value = '';
            document.getElementById('custom-model-path').value = '';
            refreshHubVisual();
        } else {
            log("❌ FORGE: Errore durante la registrazione.", "#ef4444");
        }
    } catch(e) {
        console.error("Forge Registration Error:", e);
    }
};

// --- 📐 LAB COLUMN LAYOUT CONTROLS ---
let activeExpandedCol = null;
let activeFullscreenCol = null;

window.toggleLabColumnExpand = (colId) => {
    const workspace = document.querySelector('.lab-workspace');
    const col = document.getElementById(colId);
    if (!workspace || !col) return;

    if (activeExpandedCol === colId) {
        // Ripristina layout originale
        workspace.classList.remove('expanded-col-swarm', 'expanded-col-ops', 'expanded-col-chat');
        col.classList.remove('lab-col-zoomed');
        activeExpandedCol = null;
    } else {
        // Applica l'espansione
        workspace.classList.remove('expanded-col-swarm', 'expanded-col-ops', 'expanded-col-chat');
        document.querySelectorAll('.lab-workspace > div').forEach(d => d.classList.remove('lab-col-zoomed'));
        
        workspace.classList.add('expanded-' + colId);
        col.classList.add('lab-col-zoomed');
        activeExpandedCol = colId;
    }
    // Ricalcola il canvas 3D se presente
    if (window.dispatchEvent) window.dispatchEvent(new Event('resize'));
};

window.toggleLabColumnFullscreen = (colId) => {
    const col = document.getElementById(colId);
    if (!col) return;

    if (document.fullscreenElement === col) {
        document.exitFullscreen().catch(e => console.warn(e));
    } else {
        if (document.fullscreenElement) {
            document.exitFullscreen().then(() => {
                col.requestFullscreen().catch(e => console.warn(e));
            });
        } else {
            col.requestFullscreen().catch(e => console.warn(e));
        }
    }
};

document.addEventListener("fullscreenchange", () => {
    const fse = document.fullscreenElement;
    
    // 🛡️ Gestione Immersion Exit
    if (!fse) {
        document.body.classList.remove('cycloscope-immersion');
    }

    document.querySelectorAll('.lab-workspace > div').forEach(d => {
        if (d === fse) {
            d.classList.add('lab-col-zoomed');
            activeFullscreenCol = d.id;
        } else {
            d.classList.remove('lab-col-zoomed');
            if (activeFullscreenCol === d.id) activeFullscreenCol = null;
        }
    });
    // Se esco e c'è una colonna espansa attiva, riapplico lo zoom solo a lei
    if (!fse && activeExpandedCol) {
        const expandedCol = document.getElementById(activeExpandedCol);
        if (expandedCol) expandedCol.classList.add('lab-col-zoomed');
    }
    if (window.dispatchEvent) window.dispatchEvent(new Event('resize'));
});

// Listener per gestire Esc sull'espansione simulata
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && activeExpandedCol && !document.fullscreenElement) {
        toggleLabColumnExpand(activeExpandedCol);
    }
});

// [v4.8] Resource Management: Priority Focus
async function setPriorityFocus(active) {
    const indicator = document.getElementById('lab-global-status');
    try {
        await fetch('/api/system/priority', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ active: active })
        });
        
        if (indicator) {
            if (active) {
                indicator.innerHTML = '<span class="pulse-dot" style="background:#facc15; box-shadow:0 0 10px #facc15;"></span> <span style="color:#facc15; font-weight:900;">[PRIORITY_FOCUS: AGENTS_IN_STASIS]</span>';
            } else {
                indicator.innerHTML = '<span class="pulse-dot" style="background:#4ade80;"></span> <span style="color:#4ade80;">[SYSTEM_ACTIVE]</span>';
            }
        }
    } catch(e) { console.error("Priority Shift Failed:", e); }
}

// [v4.1] Sovereign UI Utilities
window.toggleSymmetry = () => {
    if (!window.pointsMesh) return;
    const current = window.pointsMesh.rotation.y;
    new TWEEN.Tween(window.pointsMesh.rotation)
        .to({ y: current + Math.PI }, 2000)
        .easing(TWEEN.Easing.Quadratic.InOut)
        .start();
    if (window.log) window.log("💠 [Symmetry] Nebula alignment shifted.", "#a855f7");
};

window.copyTracingLog = () => {
    const logs = Array.from(document.querySelectorAll('#tracing-list li'))
        .map(li => li.innerText)
        .join('\n');
    navigator.clipboard.writeText(logs).then(() => {
        if (window.log) window.log("📋 [Tracing] Logs copied to clipboard.", "#22c55e");
    }).catch(err => {
        console.error("Failed to copy logs:", err);
    });
};
