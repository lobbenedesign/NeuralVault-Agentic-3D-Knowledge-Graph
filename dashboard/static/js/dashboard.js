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
let quantumFlashTime = 0, synthFlashTime = 0;
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

    const glOptions = { antialias: false, depth: true, alpha: true };
    let gl = canvas.getContext('webgl2', glOptions) || canvas.getContext('webgl', glOptions);
    if (!gl) {
        log("❌ WebGL Context Failure", "#ef4444");
        return;
    }
    log("🚀 WebGL Context Initialized", "#10b981");

    scene = new THREE.Scene();
    const isLight = document.body.classList.contains('light-theme');
    scene.background = new THREE.Color(isLight ? 0xf8fafc : 0x020617);
    const width = container.clientWidth;
    const height = container.clientHeight;
    
    camera = new THREE.PerspectiveCamera(75, container.clientWidth / container.clientHeight, 10, 50000000);
    camera.position.set(5000000, 5000000, 5000000); 
    camera.lookAt(0, 0, 0);

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
    scene.add(cube);

    const grid = new THREE.GridHelper(10000000, 20, isLight ? 0x94a3b8 : 0x3b82f6, isLight ? 0xe2e8f0 : 0x1e293b);
    grid.position.y = -1000000;
    scene.add(grid);

    // [v16.0] Cluster Visualization Layer
    clusterNodesGroup = new THREE.Group();
    scene.add(clusterNodesGroup);

    window.is3DInitialized = true;
    const MAX_POINTS = 50000;
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.BufferAttribute(new Float32Array(MAX_POINTS * 3), 3));
    geometry.setAttribute('color', new THREE.BufferAttribute(new Float32Array(MAX_POINTS * 3), 3));
    
    pointsMesh = new THREE.Points(geometry, new THREE.PointsMaterial({
        size: 25000, vertexColors: true, transparent: true, opacity: 0.9,
        sizeAttenuation: true, blending: THREE.AdditiveBlending, depthWrite: false
    }));
    scene.add(pointsMesh);

    neuralLinks = new THREE.Group();
    scene.add(neuralLinks);

    if (typeof THREE.OrbitControls === 'function') {
        controls = new THREE.OrbitControls(camera, renderer.domElement);
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
    raycaster.params.Points.threshold = 15000;
    mouse = new THREE.Vector2();

    container.addEventListener('click', (e) => window.onNebulaClick(e));
    canvas.addEventListener('contextmenu', e => e.preventDefault());
    
    const probeToggle = document.getElementById('probe-toggle');
    if (probeToggle) {
        probeToggle.addEventListener('change', (e) => {
            if (!e.target.checked) window.closeInspector();
        });
    }

    provisionAgents();
    animate();
    window.is3DInitialized = true;
    log("🌌 Neural Cycloscope Active", "#3b82f6");

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
    reaperCubes.push({ mesh: cube, expiry: Date.now() + 300000 }); // 5 minutes
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
    // JANITRON Body
    const jBodyGeo = new THREE.BoxGeometry(60000, 60000, 60000);
    const jBodyMat = new THREE.MeshPhongMaterial({ color: 0x4ade80 });
    const jBody = new THREE.Mesh(jBodyGeo, jBodyMat);
    janitorGroup.add(jBody);

    // MOUTH (Always Black)
    const mouthGeo = new THREE.BoxGeometry(40000, 20000, 10000);
    const mouthMat = new THREE.MeshBasicMaterial({ color: 0x000000 });
    const mouth = new THREE.Mesh(mouthGeo, mouthMat);
    mouth.position.z = 30001;
    mouth.userData.isMouth = true;
    janitorGroup.add(mouth);
    janitorLabel = createTextSprite("JA-001 JANITRON", "#FFFF00");
    janitorLabel.position.y = 80000;
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

    // SE-007 SENTINEL
    sentinelGroup = new THREE.Group();
    const seMat = new THREE.MeshPhongMaterial({ color: 0xef4444, emissive: 0x991b1b, transparent: true, opacity: 0.9 });
    sentinelShield = new THREE.Mesh(new THREE.CylinderGeometry(30000, 30000, 80000, 6), seMat);
    sentinelGroup.add(sentinelShield);
    sentinelLabel = createTextSprite("SE-007 SENTINEL", "#ef4444");
    sentinelLabel.position.y = 100000;
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
    fuseNose.rotation.x = -Math.PI / 2;
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
        const time = Date.now() * 0.005;
        const radius = 200000 + 50000 * Math.sin(time * 0.5);
        quantumTargetPos.set(Math.cos(time) * radius, Math.sin(time * 0.7) * 100000, Math.sin(time) * radius);
        synthTargetPos.set(Math.cos(time + Math.PI) * radius, Math.sin(time * 0.7 + Math.PI) * 100000, Math.sin(time + Math.PI) * radius);
    } else {
        updateAgentPhysics();
    }

    // 🧹 [JANITRON] Logic (Always Patrolling + Colored Body)
    const jColor = janitorFlashTime > 0 ? 0x3b82f6 : 0x4ade80;
    if (janitorGroup) {
        janitorGroup.children.forEach(c => {
            if (c.userData.isMouth) c.material.color.set(0x000000); // Always Black Mouth
            else if (c.material) c.material.color.set(jColor);
        });
        if (janitorFlashTime > 0) janitorFlashTime--;
        
        // Persistent Patrol even if idle: orbit the base target
        const time = Date.now() * 0.001;
        const orbitX = Math.cos(time * 0.5) * 50000;
        const orbitZ = Math.sin(time * 0.5) * 50000;
        janitorGroup.position.x += (janitorTargetPos.x + orbitX - janitorGroup.position.x) * 0.05;
        janitorGroup.position.y += (janitorTargetPos.y - janitorGroup.position.y) * 0.05;
        janitorGroup.position.z += (janitorTargetPos.z + orbitZ - janitorGroup.position.z) * 0.05;
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
        if (now > c.expiry) {
            scene.remove(c.mesh);
            return false;
        }
        // Subtle Pulse for the red crosses
        c.mesh.scale.setScalar(1 + Math.sin(now * 0.005) * 0.05);
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
        let prevPos = snakeGroup.position.clone();
        const diff = snakeCurrentTarget.clone().sub(snakeGroup.position);
        if (diff.length() < 100000) snakeCurrentTarget.set((Math.random()-0.5)*2000000, (Math.random()-0.5)*1000000, (Math.random()-0.5)*2000000);
        if (Math.abs(diff.x) > Math.abs(diff.y) && Math.abs(diff.x) > Math.abs(diff.z)) snakeDirection.set(Math.sign(diff.x), 0, 0);
        else if (Math.abs(diff.y) > Math.abs(diff.z)) snakeDirection.set(0, Math.sign(diff.y), 0);
        else snakeDirection.set(0, 0, Math.sign(diff.z));
        snakeGroup.position.add(snakeDirection.clone().multiplyScalar(32500));
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
        sentinelShield.rotation.y += 0.05;
        sentinelGroup.position.y += Math.sin(time * 3) * 300;
    }

    if (synthGroup) {
        synthGroup.position.lerp(synthTargetPos, 0.05);
        const isActive = (synthFlashTime > 0);
        const subPulse = Math.sin(time * 15) * 0.5 + 0.5;
        synthSubAgents.forEach((sub, i) => {
            const orbitSpeed = 2.0;
            const orbitRadius = 65000;
            const angle = (time * orbitSpeed) + (i * Math.PI * 2 / 3);
            sub.position.set(Math.cos(angle) * orbitRadius, Math.sin(angle) * orbitRadius, Math.sin(angle * 0.5) * 20000);
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
        // High-Altitude Periphery Patrol (Outer Guard)
        const patrolOrbit = 1100000 + Math.sin(time * 0.2) * 200000; // Orbiting at the edge
        const patrolSpeed = time * 0.15; // Slower, more majestic patrol
        const tx = Math.cos(patrolSpeed) * patrolOrbit;
        const tz = Math.sin(patrolSpeed) * patrolOrbit;
        const ty = Math.sin(time * 0.4) * 600000; // High vertical clearance
        
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
    }

    if (!isRotationPaused) {
        if (pointsMesh) pointsMesh.rotation.y += 0.001;
        if (neuralLinks) {
            neuralLinks.rotation.y += 0.001;
            const isLight = document.body.classList.contains('light-theme');
            neuralLinks.children.forEach(link => {
                const now = Date.now();
                if (link.isSpark) {
                    link.material.color.setHSL((time * 0.4) % 1, 1, isLight ? 0.4 : 0.6);
                    link.material.opacity = isLight ? 0.8 : 0.6 + Math.sin(time * 10) * 0.3;
                    link.material.blending = isLight ? THREE.NormalBlending : THREE.AdditiveBlending;
                } else if (link.isNew) {
                    function updateLinkMaterial(link, isSuper) {
                        if (isSuper) {
                            const timeInit = link.userData.createdAt || Date.now();
                            const age = Date.now() - timeInit;
                            const color = new THREE.Color();
                            const hue = (Date.now() * 0.0002) % 1;
                            color.setHSL(hue, 0.8, 0.5);
                            link.material.color.copy(color);
                            
                            // Aura LED Pulse
                            if (age < superSynapseAuraDuration) {
                                const pulse = 0.5 + Math.sin(Date.now() * 0.01) * 0.5;
                                link.material.emissive = color;
                                link.material.emissiveIntensity = 2.0 * pulse;
                                link.material.opacity = 0.8 + 0.2 * pulse;
                            } else {
                                link.material.emissiveIntensity = 0;
                                link.material.opacity = 0.6;
                            }
                        }
                    }
                    updateLinkMaterial(link, true);
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

function updateThreeScene(points, links = []) {
    if (!pointsMesh || !neuralLinks) return;
    vaultPoints = points || [];
    const count = Math.min(vaultPoints.length, 50000);
    const pos = pointsMesh.geometry.attributes.position.array;
    const col = pointsMesh.geometry.attributes.color.array;
    const pastelPalette = ["#FFB7B2", "#FFDAC1", "#E2F0CB", "#B5EAD7", "#C7CEEA", "#FF9AA2", "#B2E2F2", "#D5AAFF"];
    const isLight = document.body.classList.contains('light-theme');

    for (let i = 0; i < count; i++) {
        const p = vaultPoints[i];
        pos[i*3] = p.x || 0; pos[i*3+1] = p.y || 0; pos[i*3+2] = p.z || 0;
        let displayColor = p.color || "#06b6d4";
        if (isLight && (displayColor === "#06b6d4" || displayColor === "#ffffff")) {
            displayColor = pastelPalette[i % pastelPalette.length];
        }
        if (!clusterFocus) {
            displayColor = isLight ? "#94a3b8" : "#475569";
        }
        const color = new THREE.Color(displayColor);
        col[i*3] = color.r; col[i*3+1] = color.g; col[i*3+2] = color.b;
    }
    pointsMesh.geometry.attributes.position.needsUpdate = true;
    pointsMesh.geometry.attributes.color.needsUpdate = true;
    renderClusters(vaultPoints);
    const drawCount = Math.floor(count * timeTravelFactor);
    pointsMesh.geometry.setDrawRange(0, drawCount);
    neuralLinks.clear();
    const now = Date.now();
    if (layersVisibility.edges && links && links.length > 0) {
        links.slice(0, 1500).forEach(l => {
            if (l.source_pos && l.target_pos) {
                const geo = new THREE.BufferGeometry().setFromPoints([
                    new THREE.Vector3(l.source_pos[0], l.source_pos[1], l.source_pos[2]),
                    new THREE.Vector3(l.target_pos[0], l.target_pos[1], l.target_pos[2])
                ]);
                const isSpark = l.is_aura === true;
                const isNew = (now - (l.created_at * 1000) < 6000);
                let edgeColor = isLight ? 0x475569 : 0xffffff;
                let opacity = 0.15;
                if (isSpark) {
                    edgeColor = 0xa855f7; 
                    opacity = 0.6;
                } else if (isNew) {
                    edgeColor = 0x00ffff;
                    opacity = 0.8;
                }
                const mat = new THREE.LineBasicMaterial({ 
                    color: edgeColor, 
                    transparent: true, 
                    opacity: opacity,
                    blending: isLight ? THREE.NormalBlending : ((isSpark || isNew) ? THREE.AdditiveBlending : THREE.NormalBlending)
                });
                const line = new THREE.Line(geo, mat);
                line.isSpark = isSpark;
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
            hex.rotation.x = Math.PI / 2;
            hex.onBeforeRender = (renderer, scene, camera, geometry, material) => {
                const clock = Date.now() * 0.002;
                material.color.setHSL((clock + avgX * 0.00001) % 1, 0.8, isLight ? 0.4 : 0.6);
                material.emissive.setHSL((clock * 1.5) % 1, 1, 0.2);
            };
            hex.position.set(avgX, avgY, avgZ);
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

async function selectNode(id) {
    const sidebar = document.getElementById('node-sidebar');
    const txtEl = document.getElementById('node-text');
    if (sidebar) { sidebar.classList.remove('hidden'); sidebar.style.display = 'flex'; }
    if (txtEl) txtEl.innerText = "Caricamento...";
    try {
        const r = await fetch(`/api/node/${id}`, { headers: { 'X-API-KEY': VAULT_KEY }});
        const d = await r.json();
        if (txtEl) txtEl.innerText = d.text || "Vuoto";
        const metaEl = document.getElementById('node-meta');
        if (metaEl && d.connections) {
            const reasons = d.connections
                .filter(c => c.reason)
                .map(c => `<div style="border-left:2px solid #a855f7; padding-left:10px; margin-bottom:10px; color:#4ade80; font-family:'Inter'; font-size:0.75rem;">
                    <strong style="color:#a855f7; font-size:0.6rem;">[NEURAL_INSIGHT]</strong><br/>${c.reason}
                </div>`)
                .join('');
            metaEl.innerHTML = reasons || `<div style="opacity:0.5; font-size:0.6rem;">Analisi strutturale completata. Connessione meccanica certificata.</div>`;
        }
    } catch(e) { if (txtEl) txtEl.innerText = "Errore."; }
}

async function refreshModels() {
    try {
        const r = await fetch('/api/models/status', { headers: { 'X-API-KEY': VAULT_KEY }});
        const d = await r.json();
        installedModels = d.installed || []; return d;
    } catch(e) { return {installed:[], available:[]}; }
}

async function renderModelHubTable() {
    const bodies = [document.getElementById('model-hub-table-body'), document.getElementById('settings-hub-table-body')];
    try {
        const r = await fetch('/api/models/status', { headers: { 'X-API-KEY': VAULT_KEY }});
        const d = await r.json();
        const models = d.installed || [];
        
        const html = models.map(m => {
            const row = `
            <tr style="border-bottom:1px solid rgba(255,255,255,0.05); transition: background 0.3s;" onmouseover="this.style.background='rgba(168,85,247,0.02)'" onmouseout="this.style.background='transparent'">
                <td style="padding:1.2rem;">
                    <div style="font-weight:900; color:#fff; font-size:1.1rem; letter-spacing:1px;">
                        ${m.name.split(':')[0].toUpperCase()} 
                        <span style="font-size:0.7rem; color:#a855f7; margin-left:8px; font-weight:400;">v${m.name.split(':')[1] || 'latest'}</span>
                    </div>
                    <div style="font-family:'JetBrains Mono'; font-size:0.5rem; color:#4ade80; margin-top:6px; background:rgba(74,222,128,0.05); padding:4px 8px; border-radius:4px; display:inline-block;">
                        <i class="fas fa-memory"></i> ${m.ram || '8GB RAM'} | <i class="fas fa-microchip"></i> ${m.cpu || 'Multi-Core'} ${m.vram ? `| <i class="fas fa-video" style="color:#f59e0b;"></i> ${m.vram}` : ''}
                    </div>
                </td>
                <td style="padding:1.2rem; font-size:0.8rem; color:#fff; font-family:'JetBrains Mono';">${m.size}</td>
                <td style="padding:1.2rem;">
                    <span style="font-size:0.55rem; color:${m.status === 'INSTALLED' ? '#4ade80' : '#8b949e'}; font-weight:800; text-transform:uppercase; letter-spacing:1px;">
                        <span class="pulse-dot" style="display:${m.status === 'INSTALLED' ? 'inline-block' : 'none'}; vertical-align:middle; margin-right:5px;"></span>
                        ${m.status}
                    </span>
                </td>
                <td style="padding:1.2rem; font-size:0.7rem; color:#8b949e; line-height:1.5; max-width:250px;">
                    <strong style="color:#fff; display:block; margin-bottom:4px;">${m.strengths}</strong>
                    <span style="font-style:italic;">${m.pros}</span>
                </td>
                <td style="padding:1.2rem;">
                    <div style="display:flex; flex-wrap:wrap; gap:4px; margin-bottom:6px;">
                        ${(Array.isArray(m.synergy) && m.synergy[0] !== 'None') ? m.synergy.map(s => `<span class="badge-synergy" style="font-size:0.5rem; padding:2px 8px;">${s}</span>`).join('') : '<span class="badge-synergy" style="opacity:0.5;">SOLO MODE</span>'}
                    </div>
                    <div style="font-size:0.5rem; color:#a855f7; font-weight:800; text-transform:uppercase; letter-spacing:1px; background:rgba(168,85,247,0.05); padding:2px 6px; border-radius:4px; display:inline-block;">
                        <i class="fas fa-project-diagram"></i> OPTIMIZED: ${m.task || 'GENERAL'}
                    </div>
                </td>
                <td style="padding:1.2rem; text-align:right;">
                    <div style="display:flex; align-items:center; justify-content:flex-end; gap:10px;">
                        ${m.status === 'INSTALLED' ? 
                            `<button onclick="window.deleteModel('${m.name}')" style="background:rgba(239, 68, 68, 0.1); border:1px solid #ef4444; color:#ef4444; padding:6px 16px; border-radius:8px; font-size:0.6rem; font-weight:900; cursor:pointer; transition:0.3s;" onmouseover="this.style.background='#ef4444'; this.style.color='white'">DELETE</button>` :
                            `<button onclick="window.deployModel('${m.name}')" style="background:rgba(74, 222, 128, 0.1); border:1px solid #4ade80; color:#4ade80; padding:6px 16px; border-radius:8px; font-size:0.6rem; font-weight:900; cursor:pointer; transition:0.3s;" onmouseover="this.style.background='#4ade80'; this.style.color='white'">DEPLOY</button>`
                        }
                    </div>
                </td>
            </tr>`;
            return row;
        }).join('');
        
        bodies.forEach(b => { if(b) b.innerHTML = html; });
        populateSwarmSelects(models);
    } catch(e) {
        console.error("Hub Sync Error:", e);
    }
}

function populateSwarmSelects(models) {
    const selects = ['route-audit', 'route-extraction', 'route-crossref', 'route-synthesis', 'route-chat-mediator', 'route-multimodal', 'route-evolution'];
    const installed = models.filter(m => m.status === 'INSTALLED');
    
    selects.forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            const currentVal = el.value;
            el.innerHTML = installed.map(m => `<option value="${m.name}">${m.name}</option>`).join('');
            if (currentVal && installed.find(m => m.name === currentVal)) {
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
        'evolution_model': document.getElementById('route-evolution').value,
        'consensus_threshold': parseInt(document.getElementById('consensus-threshold').value || 2),
        'weaver_sensitivity': parseFloat(document.getElementById('weaver-sensitivity').value || 0.82),
        'auto_evolve_active': document.getElementById('auto-evolve-toggle')?.checked || false
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
    const modal = document.getElementById('delete-confirm-modal');
    const targetSpan = document.getElementById('delete-target-id');
    const confirmBtn = document.getElementById('btn-confirm-delete');
    if (!modal || !targetSpan || !confirmBtn) return;
    targetSpan.innerText = id;
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
window.closeInspector = () => { if (document.getElementById('node-sidebar')) document.getElementById('node-sidebar').classList.add('hidden'); };
window.onNebulaClick = (event) => {
    const container = document.getElementById('memory-graph-container');
    const rect = container.getBoundingClientRect();
    mouse.x = ((event.clientX - rect.left) / container.clientWidth) * 2 - 1;
    mouse.y = -((event.clientY - rect.top) / container.clientHeight) * 2 + 1;
    raycaster.setFromCamera(mouse, camera);
    const intersects = raycaster.intersectObject(pointsMesh);
    if (intersects.length > 0) {
        if (!document.getElementById('probe-toggle').checked) return;
        selectNode(vaultPoints[intersects[0].index].id);
    }
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
    const t = document.getElementById(`${s}-view`);
    if (t) {
        t.style.display = 'flex';
        t.style.height = '100%';
    }
    const nav = document.getElementById(`nav-${s}`);
    if (nav) nav.classList.add('active');
    if (s === 'overview') { 
        init3D(); 
        setTimeout(() => window.dispatchEvent(new Event('resize')), 100); 
    }
    if (s === 'benchmark') { renderBenchmarkTable(); }
    if (s === 'settings') { switchSettingsTab('swarm'); }
};

window.switchLabTab = (tab) => {
    document.querySelectorAll('[id^="lab-tab-content-"]').forEach(c => c.style.display = 'none');
    document.querySelectorAll('.lab-tab-btn').forEach(btn => btn.classList.remove('active-tab'));
    const target = document.getElementById(`lab-tab-content-${tab}`);
    if (target) target.style.display = (tab === 'active') ? 'flex' : 'block';
    const btn = document.getElementById(`tab-lab-${tab}`);
    if (btn) btn.classList.add('active-tab');
    if (tab === 'forge') renderModelHubTable();
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

window.toggleCycloscopeFullscreen = () => {
    const container = document.getElementById('memory-graph-container');
    if (!document.fullscreenElement) {
        container.requestFullscreen().catch(err => {
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
        ['route-audit', 'route-extraction', 'route-crossref', 'route-synthesis', 'route-chat-mediator', 'route-multimodal'].forEach(id => {
            const el = document.getElementById(id);
            if (el) {
                const key = id.replace('route-', '').replace('-', '_');
                el.value = c[key] || el.value;
            }
        });
    } catch(e) {}
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
        const weather = d.weather || (d.lab ? d.lab.weather : null);
        if (weather) {
            const cog = document.getElementById('metrics-data');
            if (cog) {
                cog.innerText = `Ret: ${weather.retention || '0%'} | Stab: ${weather.stability || '0%'}`;
                if (weather.stability) {
                    cog.style.color = weather.stability.includes('99') ? '#10b981' : weather.stability.includes('98') ? '#3b82f6' : '#f59e0b';
                }
            }
        }
        if (d.lab && d.lab.agents) {
            const a = d.lab.agents;
            Object.keys(a).forEach(id => {
                const agentData = a[id];
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
                    const isActive = agentData.status && !agentData.status.toLowerCase().includes('idle');
                    if (isActive) hud.classList.remove('inactive-agent');
                    else hud.classList.add('inactive-agent');
                    if (id === 'RP-001') { 
                        const el = document.getElementById('val-reaper-healed'); 
                        if(el) {
                            const newVal = agentData.processed || 0;
                            const oldVal = parseInt(el.innerText);
                            if (newVal > oldVal) {
                                spawnReaperMonument(agentData.pos);
                            }
                            el.innerText = newVal; 
                        }
                    }
                    if (id === 'DI-007') { 
                        const el = document.getElementById('val-distiller-pruned'); 
                        if(el) {
                            const newVal = agentData.pruned || 0;
                            if (newVal > parseInt(el.innerText)) distillerFlashTime = 240; // 4s at 60fps
                            el.innerText = newVal; 
                        }
                    }
                    if (id === 'JA-001') { 
                        const el = document.getElementById('val-janitron-purged'); 
                        if(el) {
                            const newVal = agentData.purged || 0;
                            if (newVal > parseInt(el.innerText)) janitorFlashTime = 240; // 4s
                            el.innerText = newVal; 
                        }
                    }
                    if (id === 'SN-008') {
                        const f = document.getElementById('val-snake-found'); if(f) f.innerText = agentData.found || 0;
                        const c = document.getElementById('val-snake-crafted'); if(c) c.innerText = agentData.crafted || 0;
                        const d_el = document.getElementById('val-snake-deleted'); if(d_el) d_el.innerText = agentData.deleted || 0;
                        if (agentData.attached_nodes) syncSnakeTail(agentData.attached_nodes.length);
                    }
                    if (id === 'QA-101') { 
                        const el = document.getElementById('val-quantum-fused'); if(el) el.innerText = agentData.fused_clusters || 0; 
                        quantumTargetPos.set(agentData.pos.x, agentData.pos.y, agentData.pos.z);
                        if (agentData.is_fusing) quantumFlashTime = 60;
                    }
                    if (id === 'SE-007') { 
                        const v = document.getElementById('val-sentinel-validated'); if(v) v.innerText = agentData.validated || 0;
                        const s = document.getElementById('val-sentinel-synapses'); if(s) s.innerText = agentData.synapses || 0;
                        sentinelTargetPos.set(agentData.pos.x, agentData.pos.y, agentData.pos.z);
                    }
                    if (id === 'SY-009') { 
                        const el = document.getElementById('val-synth-sparks'); if(el) el.innerText = agentData.sparks || 0; 
                        synthTargetPos.set(agentData.pos.x, agentData.pos.y, agentData.pos.z);
                    }
                    if (id === 'CB-003') { 
                        const el = document.getElementById('val-bridger-bridges'); if(el) el.innerText = agentData.bridges || 0; 
                        bridgerTargetPos.set(agentData.pos.x, agentData.pos.y, agentData.pos.z);
                        if (agentData.status && agentData.status.includes('Sincronizzazione')) bridgerPulseTime = 180;
                    }
                    if (id === 'FS-77') {
                        const el = document.getElementById('val-skywalker-hits'); if(el) el.innerText = agentData.web_hits || 0;
                        skywalkerTargetPos.set(agentData.pos.x, agentData.pos.y, agentData.pos.z);
                        if (agentData.laser_active) spawnSkywalkerLaser();
                    }
                    if (id === 'JA-001') janitorTargetPos.set(agentData.pos.x, agentData.pos.y, agentData.pos.z);
                    if (id === 'DI-007') distillerTargetPos.set(agentData.pos.x, agentData.pos.y, agentData.pos.z);
                    if (id === 'RP-001') reaperTargetPos.set(agentData.pos.x, agentData.pos.y, agentData.pos.z);
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
            const aiModel = document.getElementById('ai-model-name');
            if (aiModel && s.ai_intelligence) aiModel.innerText = s.ai_intelligence.model;
            const aiQuant = document.getElementById('ai-model-quant');
            if (aiQuant && s.ai_intelligence) aiQuant.innerText = s.ai_intelligence.quantization;
            const aiSpeed = document.getElementById('ai-inference-speed');
            if (aiSpeed && s.ai_intelligence) aiSpeed.innerText = s.ai_intelligence.inference_speed;
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
        const bestFast = b[0];
        const bestSmart = b.find(m => m.model_name.includes('llama3.1') || m.model_name.includes('mistral')) || b[0];
        const recContainer = document.getElementById('mission-recommendation');
        if (recContainer && bestFast) {
            recContainer.innerHTML = `
                <div style="background: rgba(16, 185, 129, 0.1); padding: 1.2rem; border-radius: 12px; border-left: 4px solid #10b981;">
                    <div style="font-size: 0.6rem; color: #10b981; font-weight: 900; margin-bottom: 5px;">ELITE CHOICE: DEEP_FORAGING</div>
                    <div style="font-size: 0.8rem; font-weight: 700; color: #fff;">${bestFast.model_name.toUpperCase()}</div>
                    <div style="font-size: 0.6rem; color: #64748b; margin-top: 5px;">Consigliato per velocità di scansione (${bestFast.tps.toFixed(1)} T/S).</div>
                </div>
                <div style="background: rgba(59, 130, 246, 0.1); padding: 1.2rem; border-radius: 12px; border-left: 4px solid #3b82f6;">
                    <div style="font-size: 0.6rem; color: #3b82f6; font-weight: 900; margin-bottom: 5px;">ELITE CHOICE: SYNTHESIS</div>
                    <div style="font-size: 0.8rem; font-weight: 700; color: #fff;">${bestSmart.model_name.toUpperCase()}</div>
                    <div style="font-size: 0.6rem; color: #64748b; margin-top: 5px;">Consigliato per densità sinaptica e ragionamento critico.</div>
                </div>
            `;
        }
        const advisor = document.getElementById('strategy-advisor-content');
        if (advisor) {
            const avgLat = b.reduce((s, x) => s + (x.avg_latency || 0), 0) / b.length;
            advisor.innerHTML = `
                <div style="display:flex; align-items:center; gap:20px;">
                    <div style="background:rgba(168,85,247,0.1); padding:20px; border-radius:50%; border:2px solid #a855f7;">
                        <i class="fas fa-brain" style="color:#a855f7; font-size:1.5rem;"></i>
                    </div>
                    <div>
                        <h4 style="color:#fff; margin:0; font-size:0.8rem; letter-spacing:1px;">HARDWARE ADVISOR v0.9</h4>
                        <p style="color:#94a3b8; font-size:0.65rem; line-height:1.4; margin:5px 0;">
                            Latenza media di sessione: <span style="color:#a855f7;">${avgLat.toFixed(1)}ms</span>. 
                            ${avgLat > 100 ? "Si consiglia di ridurre i parametri di 'context window' per migliorare la fluidità." : "Performance termiche eccellenti. Pronto per missioni di estrazione massiva."}
                        </p>
                    </div>
                </div>
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
                    y: { grid: { color: 'rgba(255,255,255,0.05)' }, border: { display: false }, ticks: { color: '#64748b', font: { size: 9 } } },
                    x: { grid: { display: false }, ticks: { color: '#64748b', font: { size: 9 } } }
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
                labels: ['LLAMA 3.2', 'MISTRAL-7B', 'PHI-3', 'QWEN-2', 'GEMMA-2'],
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
                        backgroundColor: 'rgba(168, 85, 247, 0.5)',
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
                    x: { grid: { display: false }, ticks: { color: '#64748b' } }
                }
            }
        });
    }
}

document.addEventListener('DOMContentLoaded', async () => {
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
        if (settings.auto_evolve_active) {
            const toggle = document.getElementById('auto-evolve-toggle');
            if (toggle) toggle.checked = true;
        }
        refreshVaultState();
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

window.createCustomAgent = async () => {
    const isModal = !!document.getElementById('af-agent-name');
    const name = isModal ? document.getElementById('af-agent-name').value : document.getElementById('lab-forge-name').value;
    const role = isModal ? document.getElementById('af-agent-role').value : "analyst";
    const model = isModal ? document.getElementById('af-agent-model').value : "llama3.2";
    const prompt = isModal ? document.getElementById('af-agent-prompt').value : "";
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
