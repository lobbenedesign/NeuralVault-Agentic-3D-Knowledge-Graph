/**
 * AURA NEXUS MASTER CONTROLLER (v2.8.2 Sovereign - MEDICAL UPDATE)
 */

let scene, camera, renderer, pointsMesh, neuralLinks, cube, raycaster, mouse;
let janitorGroup, janitorTop, janitorBottom, janitorLabel;
let distillerGroup, distillerLabel;
let reaperGroup, reaperLabel; 
let snakeGroup, snakeSegments = [], snakeLabel;
let janitorTargetPos = new THREE.Vector3(200000, 200000, 200000);
let distillerTargetPos = new THREE.Vector3(-200000, 200000, -200000);
let reaperTargetPos = new THREE.Vector3(0, 300000, 0);
let snakeCurrentTarget = new THREE.Vector3(1200000, 0, 0);
let snakeDirection = new THREE.Vector3(1, 0, 0);
let lastSnakeStep = 0;
let lastReaperProcessed = 0, lastJanitorPurged = 0, lastDistillerPruned = 0;
let janitorFlashTime = 0, distillerFlashTime = 0;
let followedAgent = null; 
let medicalCubes = [];
let controls, eventSource, vaultPoints = [], installedModels = [];
let isRotationPaused = false;
let isUserInteracting = false;
let layersVisibility = { agents: true, orphans: true, nodes: true, linked_nodes: true, edges: true, sparks: true, cube: true, grid: true, nav_guide: true };
let snapshots = []; 
let sseCount = 0;
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
    if (!gl) return;

    scene = new THREE.Scene();
    scene.background = new THREE.Color(0x020617);
    const width = container.clientWidth;
    const height = container.clientHeight;
    
    camera = new THREE.PerspectiveCamera(45, width / height, 100, 100000000);
    camera.position.set(1500000, 1500000, 1500000); 
    camera.lookAt(0, 0, 0);

    renderer = new THREE.WebGLRenderer({ 
        canvas, 
        context: gl, 
        antialias: true, 
        alpha: true,
        precision: "highp",
        powerPreference: "high-performance"
    });
    renderer.setSize(width, height);
    renderer.setPixelRatio(window.devicePixelRatio > 1 ? 2 : 1); // Clamp to 2 for performance/quality balance

    scene.add(new THREE.AmbientLight(0xffffff, 1.2));
    const dl = new THREE.DirectionalLight(0xffffff, 1.0);
    dl.position.set(1, 1, 1);
    scene.add(dl);

    // Boundary Cube
    cube = new THREE.Mesh(
        new THREE.BoxGeometry(4000000, 4000000, 4000000),
        new THREE.MeshBasicMaterial({ color: 0x3b82f6, wireframe: true, transparent: true, opacity: 0.15 })
    );
    scene.add(cube);

    const grid = new THREE.GridHelper(10000000, 20, 0x1e293b, 0x0f172a);
    grid.position.y = -1000000;
    scene.add(grid);

    // Points Cloud
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

    controls = new THREE.OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.screenSpacePanning = true;
    controls.enabled = true;
    
    // Explicit mouse mapping: Left Drag = Rotate, Right Drag = Pan, Scroll = Zoom
    controls.mouseButtons = {
        LEFT: THREE.MOUSE.ROTATE,
        MIDDLE: THREE.MOUSE.DOLLY,
        RIGHT: THREE.MOUSE.PAN
    };
    controls.minDistance = 50; 
    controls.maxDistance = 10000000;
    
    // 🖱️ Define explicit mouse bindings
    controls.mouseButtons = {
        LEFT: THREE.MOUSE.ROTATE,
        MIDDLE: THREE.MOUSE.DOLLY,
        RIGHT: THREE.MOUSE.PAN
    };

    controls.addEventListener('start', () => { isUserInteracting = true; });
    controls.addEventListener('end', () => { isUserInteracting = false; });

    raycaster = new THREE.Raycaster();
    raycaster.params.Points.threshold = 15000; // Better click precision
    mouse = new THREE.Vector2();

    container.addEventListener('click', onNebulaClick);
    
    // 🖱️ Fix: Disable Context Menu on Canvas for Pan Interaction
    canvas.addEventListener('contextmenu', e => e.preventDefault());
    
    // 🎯 Fix: Probe Toggle logic (Close on deactivate)
    document.getElementById('probe-toggle').addEventListener('change', (e) => {
        if (!e.target.checked) closeInspector();
    });

    // 🕹️ CUSTOM GESTURES: Vertical Pan via Shift + Scroll
    window.addEventListener('wheel', (e) => {
        if (e.shiftKey && controls.enabled) {
            const panSpeed = controls.target.distanceTo(camera.position) * 0.001;
            const direction = new THREE.Vector3(0, 1, 0).applyQuaternion(camera.quaternion);
            const move = direction.multiplyScalar(-e.deltaY * panSpeed);
            
            camera.position.add(move);
            controls.target.add(move);
            e.preventDefault();
        }
    }, { passive: false });

    provisionAgents();
    animate();
    window.is3DInitialized = true;

    // ⚡ [v2.9] REAL-TIME VIEWPORT CALIBRATION
    window.addEventListener('resize', () => {
        const width = container.clientWidth;
        const height = container.clientHeight;
        if (camera && renderer) {
            camera.aspect = width / height;
            camera.updateProjectionMatrix();
            renderer.setSize(width, height);
            console.log(`📐 [Viewport] Recalibrated: ${width}x${height}`);
        }
    });

    // Handle Fullscreen transitions specifically
    document.addEventListener('fullscreenchange', () => {
        setTimeout(() => window.dispatchEvent(new Event('resize')), 100);
    });
}

function createTextSprite(text, color) {
    const canvas = document.createElement('canvas');
    canvas.width = 1024; canvas.height = 256;
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, 1024, 256);
    ctx.font = 'Bold 80px JetBrains Mono'; // Double font size for resolution
    ctx.textAlign = 'center';
    ctx.fillStyle = color;
    ctx.fillText(text, 512, 140);
    
    const texture = new THREE.CanvasTexture(canvas);
    texture.minFilter = THREE.LinearFilter;
    texture.magFilter = THREE.LinearFilter;
    texture.anisotropy = 16;
    texture.premultipliedAlpha = false;

    const spriteMaterial = new THREE.SpriteMaterial({ 
        map: texture, 
        transparent: true,
        alphaTest: 0.1,
        depthWrite: false
    });
    const sprite = new THREE.Sprite(spriteMaterial);
    sprite.scale.set(400000, 100000, 1);
    return sprite;
}

function provisionAgents() {
    // JA-001 JANITRON
    janitorGroup = new THREE.Group();
    const jMat = new THREE.MeshLambertMaterial({ color: 0xFFFF00 });
    janitorTop = new THREE.Mesh(new THREE.SphereGeometry(30000, 32, 16, 0, Math.PI*2, 0, Math.PI/2), jMat);
    janitorBottom = new THREE.Mesh(new THREE.SphereGeometry(30000, 32, 16, 0, Math.PI*2, Math.PI/2, Math.PI/2), jMat);
    janitorGroup.add(janitorTop, janitorBottom);
    janitorLabel = createTextSprite("JA-001 JANITRON", "#FFFF00");
    janitorLabel.position.y = 80000;
    janitorGroup.add(janitorLabel);
    scene.add(janitorGroup);

    // DI-007 DISTILLER 
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

    // RP-001 REAPER (3D Voxel)
    reaperGroup = new THREE.Group();
    const mats = [
        null, 
        new THREE.MeshLambertMaterial({ color: 0xffffff }), // 1: Coat
        new THREE.MeshLambertMaterial({ color: 0xffdbac }), // 2: Skin
        new THREE.MeshLambertMaterial({ color: 0x5d4037 }), // 3: Hair
        new THREE.MeshLambertMaterial({ color: 0xef4444 }), // 4: Red Pill
        new THREE.MeshLambertMaterial({ color: 0x2196f3 }), // 5: Blue Pill
        new THREE.MeshLambertMaterial({ color: 0x3e2723 }), // 6: Shoes
        new THREE.MeshLambertMaterial({ color: 0xef4444 })  // 7: Hat
    ];
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

    // SN-008 SNAKE
    snakeGroup = new THREE.Group();
    const sMat = new THREE.MeshLambertMaterial({ color: 0x10b981 });
    snakeGroup.add(new THREE.Mesh(new THREE.BoxGeometry(32500, 32500, 32500), sMat));
    
    snakeLabel = createTextSprite("SN-008 SNAKE", "#10b981");
    snakeLabel.position.y = 80000;
    snakeGroup.add(snakeLabel);
    
    scene.add(snakeGroup);
    snakeSegments = [];
    for(let i=1; i<8; i++) {
        const seg = new THREE.Mesh(new THREE.BoxGeometry(30000 - i*2000, 30000 - i*2000, 30000 - i*2000), sMat);
        seg.position.set(1200000, 0, -i * 35000);
        scene.add(seg);
        snakeSegments.push(seg);
    }
}

function animate() {
    requestAnimationFrame(animate);
    const now = Date.now();
    const time = now * 0.001;
    
    if (janitorGroup) {
        janitorGroup.position.lerp(janitorTargetPos, 0.05);
        if (janitorTop) janitorTop.rotation.x = -Math.abs(Math.sin(time * 6)) * 0.6;
        if (janitorBottom) janitorBottom.rotation.x = Math.abs(Math.sin(time * 6)) * 0.6;
        
        // ⚡ ACTION FLASHING
        if (now < janitorFlashTime) {
            janitorGroup.traverse(m => { 
                if(m.isMesh && m.material) {
                    const mats = Array.isArray(m.material) ? m.material : [m.material];
                    mats.forEach(mat => {
                        if (mat.emissive) mat.emissive.setHex(0x00ffff);
                        if (mat.emissiveIntensity !== undefined) mat.emissiveIntensity = 0.5;
                    });
                }
            });
        } else {
            janitorGroup.traverse(m => { 
                if(m.isMesh && m.material) {
                    const mats = Array.isArray(m.material) ? m.material : [m.material];
                    mats.forEach(mat => { if (mat.emissive) mat.emissive.setHex(0x000000); });
                }
            });
        }
    }

    if (distillerGroup) {
        distillerGroup.position.lerp(distillerTargetPos, 0.03);
        distillerGroup.position.y += Math.sin(time * 2) * 800;
        distillerGroup.rotation.y += 0.02;

        // ⚡ ACTION FLASHING
        if (now < distillerFlashTime) {
            distillerGroup.traverse(m => { 
                if(m.isMesh && m.material) {
                    const mats = Array.isArray(m.material) ? m.material : [m.material];
                    mats.forEach(mat => {
                        if (mat.emissive) mat.emissive.setHex(0x00ffff);
                        if (mat.emissiveIntensity !== undefined) mat.emissiveIntensity = 0.5;
                    });
                }
            });
        } else {
            distillerGroup.traverse(m => { 
                if(m.isMesh && m.material) {
                    const mats = Array.isArray(m.material) ? m.material : [m.material];
                    mats.forEach(mat => { if (mat.emissive) mat.emissive.setHex(0x000000); });
                }
            });
        }
    }

    if (reaperGroup) {
        reaperGroup.position.lerp(reaperTargetPos, 0.04);
        // Upright rotation only (facing target on Y axis)
        const ghostTarget = reaperTargetPos.clone();
        ghostTarget.y = reaperGroup.position.y;
        reaperGroup.lookAt(ghostTarget);
        reaperGroup.position.y += Math.cos(time * 1.5) * 500;
    }

    if (snakeGroup && now - lastSnakeStep > 125) { // 🚀 50% Speed Increase (Double Frequency)
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

    medicalCubes.forEach((c, i) => {
        // 🧪 v24.4: Medical Cubes are now PERSISTENT until end of session (no age deletion)
        c.scale.setScalar(0.8 + Math.sin(time * 3) * 0.05); 
        if (c.children[0] && c.children[0].material) {
            c.children[0].material.opacity = 0.85 + Math.sin(time * 2) * 0.1;
        }
    });

    // 🎥 CAMERA FOLLOW LOGIC (Synchronized with OrbitControls)
    if (followedAgent && followedAgent.position && !isUserInteracting) {
        const targetPos = followedAgent.position.clone();
        
        // 🚀 Fix: Only update target if user is not actively panning
        if (controls) {
            controls.target.lerp(targetPos, 0.05); 
        }
    }

    // 🌌 Nebula Rotation (User preferred over Cube rotation)
    if (!isRotationPaused) {
        if (pointsMesh) pointsMesh.rotation.y += 0.001;
        if (neuralLinks) neuralLinks.rotation.y += 0.001;
    }
    
    // Cube is now static for better spatial orientation
    if (controls) controls.update();
    if (renderer) renderer.render(scene, camera);
}

function spawnMedicalCube(x, y, z) {
    const group = new THREE.Group();
    const boxGeo = new THREE.BoxGeometry(45000, 45000, 45000);
    const boxMat = new THREE.MeshLambertMaterial({ color: 0xffffff, transparent: true, opacity: 0.95 });
    const box = new THREE.Mesh(boxGeo, boxMat);
    group.add(box);

    const crossMat = new THREE.MeshBasicMaterial({ color: 0xef4444 });
    const hBar = new THREE.BoxGeometry(35000, 8000, 2000);
    const vBar = new THREE.BoxGeometry(8000, 35000, 2000);
    const faces = [{ pos: [0, 0, 23000], rot: [0, 0, 0] },{ pos: [0, 0, -23000], rot: [0, 0, 0] },{ pos: [23000, 0, 0], rot: [0, Math.PI/2, 0] },{ pos: [-23000, 0, 0], rot: [0, Math.PI/2, 0] },{ pos: [0, 23000, 0], rot: [Math.PI/2, 0, 0] },{ pos: [0, -23000, 0], rot: [Math.PI/2, 0, 0] }];

    faces.forEach(f => {
        const cross = new THREE.Group();
        cross.add(new THREE.Mesh(hBar, crossMat));
        cross.add(new THREE.Mesh(vBar, crossMat));
        cross.position.set(...f.pos);
        cross.rotation.set(...f.rot);
        group.add(cross);
    });

    group.position.set(x, y, z);
    group.userData.createdAt = Date.now();
    scene.add(group);
    medicalCubes.push(group);
}

function updateThreeScene(points, links = []) {
    if (!pointsMesh) return;
    vaultPoints = points || [];
    const count = Math.min(vaultPoints.length, 50000);
    const pos = pointsMesh.geometry.attributes.position.array;
    const col = pointsMesh.geometry.attributes.color.array;
    for (let i = 0; i < count; i++) {
        const p = vaultPoints[i];
        const hasLinks = links.some(l => l.source === p.id || l.target === p.id);
        
        let show = layersVisibility.nodes;
        if (!layersVisibility.orphans && !hasLinks) show = false;
        if (!layersVisibility.linked_nodes && hasLinks) show = false;

        if (show) {
            pos[i*3] = p.x || 0; pos[i*3+1] = p.y || 0; pos[i*3+2] = p.z || 0;
            const color = new THREE.Color(p.color || "#06b6d4");
            col[i*3] = color.r; col[i*3+1] = color.g; col[i*3+2] = color.b;
        } else {
            pos[i*3] = pos[i*3+1] = pos[i*3+2] = 0;
        }
    }
    pointsMesh.geometry.attributes.position.needsUpdate = true;
    pointsMesh.geometry.attributes.color.needsUpdate = true;
    pointsMesh.geometry.setDrawRange(0, count);
    
    // 🧱 CRITICAL: Prevent Frustum Culling when camera moves far
    pointsMesh.geometry.computeBoundingSphere();
    pointsMesh.geometry.computeBoundingBox();

    neuralLinks.clear();
    if (links && links.length > 0) {
        const lineMat = new THREE.LineBasicMaterial({ color: 0x3b82f6, transparent: true, opacity: 0.15 });
        const auraMat = new THREE.LineBasicMaterial({ color: 0xff00ff, transparent: true, opacity: 0.6, linewidth: 2 }); // RGB Sparks Placeholder
        
        links.slice(0, 1500).forEach(l => {
            if (l.source_pos && l.target_pos) {
                const geo = new THREE.BufferGeometry().setFromPoints([
                    new THREE.Vector3(l.source_pos[0], l.source_pos[1], l.source_pos[2]),
                    new THREE.Vector3(l.target_pos[0], l.target_pos[1], l.target_pos[2])
                ]);
                const line = new THREE.Line(geo, l.is_aura ? auraMat : lineMat);
                line.userData.isSpark = !!l.is_aura; // ⚡ Tag for Visibility Menu
                if (l.is_aura) {
                    line.onBeforeRender = (renderer, scene, camera, geometry, material) => {
                        const t = Date.now() * 0.005;
                        material.color.setHSL((t % 1), 1, 0.5); 
                    };
                }
                geo.computeBoundingSphere();
                neuralLinks.add(line);
            }
        });
    }
}

function onNebulaClick(event) {
    const container = document.getElementById('memory-graph-container');
    const rect = container.getBoundingClientRect();
    mouse.x = ((event.clientX - rect.left) / container.clientWidth) * 2 - 1;
    mouse.y = -((event.clientY - rect.top) / container.clientHeight) * 2 + 1;
    raycaster.setFromCamera(mouse, camera);
    const intersects = raycaster.intersectObject(pointsMesh);
    if (intersects.length > 0) {
        // 🕵️‍♂️ Check Probe Toggle state
        if (!document.getElementById('probe-toggle').checked) return;
        selectNode(vaultPoints[intersects[0].index].id);
    }
}

async function selectNode(id) {
    const sidebar = document.getElementById('node-sidebar');
    if (sidebar) { sidebar.classList.remove('hidden'); sidebar.style.display = 'flex'; }
    document.getElementById('node-text').innerText = "Recuperando...";
    try {
        const r = await fetch(`/api/node/${id}`, { headers: { 'X-API-KEY': VAULT_KEY }});
        const d = await r.json();
        document.getElementById('node-text').innerText = d.text || "Vuoto.";
    } catch(e) {}
}

async function refreshModels() {
    try {
        const r = await fetch('/api/models/status', { headers: { 'X-API-KEY': VAULT_KEY }});
        const d = await r.json();
        installedModels = d.installed || [];
    } catch(e) {}
}

async function renderModelHubTable() {
    const tbody = document.getElementById('model-hub-table-body');
    if (!tbody) return;
    try {
        const r = await fetch('/api/models/catalog', { headers: { 'X-API-KEY': VAULT_KEY }});
        const catalog = await r.json();
        tbody.innerHTML = Object.keys(catalog).map(id => {
            const m = catalog[id];
            const isInst = installedModels.some(im => im.name === id);
            return `
                <tr style="background: rgba(255,255,255,0.02); border-bottom: 1px solid rgba(255,255,255,0.05);">
                    <td style="padding: 1rem;"><div style="color:#fff; font-weight:800;">${id}</div></td>
                    <td style="padding: 1rem; color:#4ade80;">${m.forza}</td>
                    <td style="padding: 1rem;">${isInst ? '<span style="color:#10b981;">● ACTIVE</span>' : `<button onclick="installModel('${id}')" style="background:#3b82f6; color:white; border:none; padding:0.3rem 0.6rem; border-radius:4px; font-size:0.6rem; cursor:pointer;">INSTALL</button>`}</td>
                </tr>`;
        }).join('');
    } catch(e) {}
}

function initSSE() {
    if (eventSource) eventSource.close();
    eventSource = new EventSource(`/events?api_key=${VAULT_KEY}`);
    eventSource.onmessage = (e) => {
        const d = JSON.parse(e.data);
        if (d.points) {
            vaultPoints = d.points;
            updateThreeScene(d.points, d.links);
            
            // 🕒 Collect Snapshots for Time Machine Evolution
            sseCount++;
            if (sseCount % 5 === 0 && snapshots.length < 500) {
                snapshots.push({ 
                    points: JSON.parse(JSON.stringify(d.points)), 
                    links: d.links ? JSON.parse(JSON.stringify(d.links)) : [],
                    timestamp: Date.now()
                });
            }
        }
        if (d.nodes_count !== undefined) {
            const el1 = document.getElementById('stat-nodes');
            const el2 = document.getElementById('stat-nodes-2');
            if (el1) el1.innerText = d.nodes_count;
            if (el2) el2.innerText = d.nodes_count;
        }
        if (d.edges_count !== undefined) {
             const el1 = document.getElementById('stat-synapses');
             const el2 = document.getElementById('stat-synapses-2');
             if (el1) el1.innerText = d.edges_count;
             if (el2) el2.innerText = d.edges_count;
        }
        if (d.system && d.system.cpu) {
            const el = document.getElementById('metrics-data');
            if (el) el.innerText = `CPU: ${d.system.cpu.overall.toFixed(1)}% | RAM: ${d.system.ram.used.toFixed(1)}%`;
        }
        if (d.agent007) {
            const ent = document.getElementById('stat-agent007-entities');
            const rel = document.getElementById('stat-agent007-relations');
            if (ent) ent.innerText = d.agent007.entities_count || 0;
            if (rel) rel.innerText = d.agent007.relations_count || 0;
        }
        if (d.storage) {
            const st = document.getElementById('stat-storage');
            if (st) st.innerText = d.storage.total;
        }
        if (d.lab && d.lab.agents) {
            const agents = d.lab.agents;
            if (agents['JA-001']) {
                janitorTargetPos.set(agents['JA-001'].pos.x, agents['JA-001'].pos.y, agents['JA-001'].pos.z);
                const st = document.getElementById('janitron-mission-stat');
                const cur = (agents['JA-001'].purged || 0);
                if (st) st.innerText = `Nodes Eaten: ${cur}`;
                if (cur > lastJanitorPurged) { janitorFlashTime = Date.now() + 2000; lastJanitorPurged = cur; }
            }
            if (agents['DI-007']) {
                distillerTargetPos.set(agents['DI-007'].pos.x, agents['DI-007'].pos.y, agents['DI-007'].pos.z);
                const st = document.getElementById('distiller-mission-stat');
                const cur = (agents['DI-007'].pruned || 0);
                if (st) st.innerText = `Arcs Pruned: ${cur}`;
                if (cur > lastDistillerPruned) { distillerFlashTime = Date.now() + 2000; lastDistillerPruned = cur; }
            }
            if (agents['RP-001']) {
                reaperTargetPos.set(agents['RP-001'].pos.x, agents['RP-001'].pos.y, agents['RP-001'].pos.z);
                const cur = Number(agents['RP-001'].processed || 0);
                const st = document.getElementById('reaper-mission-stat');
                if (st) st.innerText = `Self-Heal: ${cur.toFixed(2)} MB`;
                if (cur > lastReaperProcessed) {
                    spawnMedicalCube(agents['RP-001'].pos.x, agents['RP-001'].pos.y, agents['RP-001'].pos.z);
                    lastReaperProcessed = cur;
                    log(`⚕️ [RP-001] Memoria Sanata: +${cur.toFixed(2)} MB`, "#00ffcc");
                }
            }
            if (agents['SN-008']) {
                snakeCurrentTarget.set(agents['SN-008'].pos.x, agents['SN-008'].pos.y, agents['SN-008'].pos.z);
                const f = document.getElementById('snake-mission-found');
                const s = document.getElementById('snake-mission-stat');
                const p = document.getElementById('snake-mission-processed');
                if (f) f.innerText = `Nodes Found: ${agents['SN-008'].found || 0}`;
                if (s) s.innerText = `Nodes Crafted: ${agents['SN-008'].harvested || 0}`;
                if (p) p.innerText = `Nodes Deleted: ${agents['SN-008'].processed || 0}`;
            }
        }
    };
}

window.toggleFollow = function(agentId) {
    const agentsMap = {
        'JA-001': { group: janitorGroup, icon: 'janitron-hud-icon' },
        'DI-007': { group: distillerGroup, icon: 'distiller-hud-icon' },
        'RP-001': { group: reaperGroup, icon: 'reaper-hud-icon' },
        'SN-008': { group: snakeGroup, icon: 'snake-hud-icon' }
    };

    const target = agentsMap[agentId];
    if (!target) return;

    // Reset all icons
    Object.values(agentsMap).forEach(a => {
        const el = document.getElementById(a.icon);
        if (el) {
            el.classList.add('inactive-agent');
            el.classList.remove('followed-agent');
        }
    });

    if (followedAgent === target.group) {
        followedAgent = null;
        log(`🎥 [Camera] Focus Libero. Modalità Panorama ripristinata.`, "#3b82f6");
    } else {
        followedAgent = target.group;
        const el = document.getElementById(target.icon);
        if (el) {
            el.classList.remove('inactive-agent');
            el.classList.add('followed-agent');
        }
        log(`🎥 [Camera] Aggancio completato su ${agentId}. Tracciamento attivo.`, "#a855f7");
    }
};

window.openAuditLedger = async function(full = false) {
    const modal = document.getElementById('audit-ledger-modal');
    if (modal) modal.style.display = 'flex';
    
    const titleMain = document.getElementById('audit-ledger-title-main');
    if (titleMain) titleMain.innerText = full ? "CHRONO-LOG: FULL HISTORY" : "CHRONO-LOG: SESSION ACTIONS";
    
    const tbody = document.getElementById('audit-ledger-body');
    if (!tbody) return;
    
    tbody.innerHTML = '<tr><td colspan="6" style="text-align:center; padding:2rem;">Acquisizione Kronos-Log in corso...</td></tr>';
    
    try {
        const url = full ? '/api/audit/ledger?full=true' : '/api/audit/ledger';
        const r = await fetch(url, { headers: { 'X-API-KEY': VAULT_KEY }});
        const logs = await r.json();
        
        if (logs && logs.length > 0) {
            const agentColors = { "RP-001": "#ffffff", "JA-001": "#FFFF00", "DI-007": "#a855f7", "SN-008": "#4ade80" };
            tbody.innerHTML = logs.map(l => {
                const aColor = agentColors[l.agent] || "#a855f7";
                return `
                    <tr style="border-bottom: 1px solid rgba(255,255,255,0.05); background: rgba(255,255,255,0.01);">
                        <td style="padding: 1rem; color: #8b949e;">${new Date(l.timestamp * 1000).toLocaleString()}</td>
                        <td style="padding: 1rem;"><span style="color: ${aColor}; font-weight: 800;">${l.agent}</span></td>
                        <td style="padding: 1rem; color: #fff;">${l.action || 'SISTEMAZIONE'}</td>
                        <td style="padding: 1rem; color: #3b82f6;">${l.target || 'GLOBAL'}</td>
                        <td style="padding: 1rem; color: #e2e8f0; font-style: italic;">${l.reason || l.msg || 'Ottimizzazione Neurale'}</td>
                        <td style="padding: 1rem; text-align: right; color: #4ade80;">${l.savings || '+0.03 MB'}</td>
                    </tr>`;
            }).join('');
        } else {
            tbody.innerHTML = '<tr><td colspan="6" style="text-align:center; padding:2rem; color: #8b949e;">Nessun verbale registrato nel ledger corrente.</td></tr>';
        }
    } catch(e) {
        tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; padding:2rem; color: #ef4444;">Errore critico nel recupero verbale: ${e.message}</td></tr>`;
    }
};

window.closeAuditLedger = function() {
    const modal = document.getElementById('audit-ledger-modal');
    if (modal) modal.style.display = 'none';
};

window.onTimeTravel = function(val) {
    if (snapshots.length === 0) return;
    const idx = Math.floor((val / 100) * (snapshots.length - 1));
    const snap = snapshots[idx];
    if (snap) {
        updateThreeScene(snap.points, snap.links);
        document.getElementById('current-period').innerText = val == 100 ? "PRESENT" : new Date(snap.timestamp).toLocaleTimeString();
    }
};

window.closeInspector = function() {
    const s = document.getElementById('node-sidebar');
    if (s) { 
        s.classList.add('hidden'); 
        // ⚡ Immediate closure for responsiveness + clean CSS transition
        setTimeout(() => { s.style.display = 'none'; }, 200); 
    }
};

window.toggleCycloscopeFullscreen = function() {
    // 🛸 Target the CORE 3D container which now correctly houses the Unified HUD
    const container = document.getElementById('memory-graph-container');
    if (!container) return;

    if (!document.fullscreenElement) {
        container.requestFullscreen().then(() => {
            log(`🚀 [Cycloscope] 4K Immersive Mode ACTIVE. Controls Synchronized.`, "#22d3ee");
        }).catch(err => {
            log(`❌ [Fullscreen] Errore: ${err.message}`, "#ef4444");
        });
    } else {
        document.exitFullscreen();
    }
};

window.toggleLegend = function() {
    log(`💡 [Legenda] Archi Bianchi: Legami Standard | Archi Rainbow: Super-Sinapsi`, "#a855f7");
};

window.toggleMissionControl = function() {
    const wrapper = document.getElementById('mc-wrapper');
    const icon = document.getElementById('mc-toggle-icon');
    if (wrapper) {
        wrapper.classList.toggle('active');
        const isActive = wrapper.classList.contains('active');
        if (icon) icon.className = isActive ? 'fas fa-chevron-right' : 'fas fa-chevron-left';
    }
};

window.toggleVisibilityMenu = function() {
    const menu = document.getElementById('visibility-menu');
    if (menu) {
        menu.classList.toggle('hidden');
    }
};

window.toggleNavGuide = function() {
    const tab = document.getElementById('nav-guide-tab');
    const icon = document.getElementById('nav-toggle-icon');
    if (tab) {
        tab.classList.toggle('collapsed');
        const isCollapsed = tab.classList.contains('collapsed');
        if (icon) icon.style.transform = isCollapsed ? 'rotate(0deg)' : 'rotate(180deg)';
    }
};

window.toggleLayer = function(layer) {
    layersVisibility[layer] = !layersVisibility[layer];
    if (layer === 'nav_guide') {
        const nav = document.getElementById('nav-guide-tab');
        if (nav) nav.style.display = layersVisibility[layer] ? 'block' : 'none';
        log(`👁️ [Visibilità] Guida Navigazione ${layersVisibility[layer] ? 'RIPRISTINATA' : 'HIDDEN'}`, "#a855f7");
        return;
    }
    if (layer === 'agents') {
        const setVis = (g, v) => { if(g) g.visible = v; };
        setVis(janitorGroup, layersVisibility.agents);
        setVis(distillerGroup, layersVisibility.agents);
        setVis(reaperGroup, layersVisibility.agents);
        setVis(snakeGroup, layersVisibility.agents);
        medicalCubes.forEach(c => c.visible = layersVisibility.agents);
    }
    if (layer === 'cube' && cube) cube.visible = layersVisibility.cube;
    if (layer === 'grid' && scene) {
        scene.traverse(obj => { if (obj instanceof THREE.GridHelper) obj.visible = layersVisibility.grid; });
    }
    if (layer === 'edges' && neuralLinks) neuralLinks.visible = layersVisibility.edges;
    if (layer === 'sparks' && neuralLinks) {
        neuralLinks.children.forEach(l => {
            if (l.userData.isSpark) l.visible = layersVisibility.sparks;
        });
    }
    if (['nodes', 'orphans', 'linked_nodes'].includes(layer)) {
        updateThreeScene(vaultPoints, []); 
    }
    log(`👁️ [Visibilità] Layer '${layer}' ${layersVisibility[layer] ? 'ATTIVATO' : 'DISATTIVATO'}`, "#a855f7");
};

window.toggleRotation = function() {
    isRotationPaused = !isRotationPaused;
    const btn = document.getElementById('rotation-toggle-btn');
    if (btn) {
        btn.innerHTML = isRotationPaused ? '<i class="fas fa-play"></i>' : '<i class="fas fa-pause"></i>';
        btn.style.color = isRotationPaused ? '#3b82f6' : '#10b981';
        btn.style.background = isRotationPaused ? 'rgba(59,130,246,0.1)' : 'rgba(16, 185, 129, 0.1)';
    }
    log(`🎬 [Rotazione] ${isRotationPaused ? 'IN PAUSA' : 'RIPRISTINATA'}`, isRotationPaused ? "#3b82f6" : "#10b981");
};

window.showSection = (s) => {
    document.querySelectorAll('.view-container').forEach(v => v.style.display = 'none');
    const t = document.getElementById(`${s}-view`);
    if (t) t.style.display = 'flex';
    if (s === 'overview') { init3D(); setTimeout(() => window.dispatchEvent(new Event('resize')), 100); }
};

document.addEventListener('DOMContentLoaded', async () => {
    initSSE();
    await refreshModels();
    await renderModelHubTable();
    window.showSection('overview');
});
