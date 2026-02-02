from flask import Flask, send_from_directory
from waitress import serve
import os

app = Flask(__name__)

HTML_CONTENT="""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>3D Flood Twin - Optimized with Search</title>
    <script src="https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.js"></script>
    <link rel="stylesheet" href="https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.css" />
    <script src="https://unpkg.com/@maplibre/maplibre-gl-geocoder@1.5.0/dist/maplibre-gl-geocoder.min.js"></script>
    <link rel="stylesheet" href="https://unpkg.com/@maplibre/maplibre-gl-geocoder@1.5.0/dist/maplibre-gl-geocoder.css" />
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <style>
        * { box-sizing: border-box; }
        body { margin: 0; padding: 0; overflow: hidden; font-family: 'Segoe UI', Arial, sans-serif; }
        #map { width: 100vw; height: 100vh; }

        /* Geocoder positioning */
        .maplibregl-ctrl-geocoder {
            position: absolute;
            top: 20px;
            left: 20px;
            z-index: 1001;
            width: 350px;
        }

        .maplibregl-ctrl-geocoder .maplibregl-ctrl-geocoder--input {
            border-radius: 8px;
            border: 2px solid #3b82f6;
            padding: 12px 16px;
            font-size: 14px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }

        .maplibregl-ctrl-geocoder--suggestion {
            padding: 12px 16px;
            border-bottom: 1px solid #e5e7eb;
            cursor: pointer;
            transition: background 0.2s;
        }

        .maplibregl-ctrl-geocoder--suggestion:hover {
            background: #f0f9ff;
        }

        #legend {
            position: absolute;
            top: 20px;
            right: 20px;
            background: rgba(255,255,255,0.95);
            padding: 16px 20px;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 1000;
            font-size: 12px;
        }
        #legend h3 { margin: 0 0 12px 0; font-size: 16px; color: #1e40af; }
        .legend-item { display: flex; align-items: center; margin: 6px 0; }
        .legend-color { width: 30px; height: 16px; margin-right: 10px; border-radius: 3px; }

        #timelineControls {
            position: absolute;
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(255,255,255,0.95);
            padding: 16px 24px;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 1000;
            min-width: 550px;
        }
        #timelineControls h3 { margin: 0 0 10px 0; text-align: center; font-size: 14px; color: #1e40af; }
        #timeDisplay { text-align: center; font-size: 18px; font-weight: bold; color: #dc2626; margin-bottom: 10px; }
        #timeSlider { width: 100%; height: 8px; margin: 10px 0; border-radius: 4px; -webkit-appearance: none; appearance: none; background: linear-gradient(to right, #3b82f6 0%, #3b82f6 0%, #d1d5db 0%, #d1d5db 100%); cursor: pointer; }
        #timeSlider::-webkit-slider-thumb { -webkit-appearance: none; width: 20px; height: 20px; background: #dc2626; border-radius: 50%; cursor: pointer; box-shadow: 0 2px 6px rgba(0,0,0,0.3); }
        #timeSlider::-moz-range-thumb { width: 20px; height: 20px; background: #dc2626; border-radius: 50%; border: none; cursor: pointer; }

        #sliderButtons { display: flex; gap: 8px; justify-content: center; margin-top: 12px; }
        #sliderButtons button { background: #3b82f6; color: white; border: none; padding: 10px 16px; border-radius: 6px; cursor: pointer; font-size: 12px; font-weight: 600; }
        #sliderButtons button:hover { background: #1e40af; }

        .speed-control { text-align: center; margin-top: 10px; font-size: 11px; }
        .speed-control select { padding: 4px 8px; border-radius: 4px; border: 1px solid #ccc; }

        #loadingStatus { text-align: center; margin-top: 8px; font-size: 10px; color: #059669; font-weight: 600; }

        #loadingOverlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.8); display: flex; align-items: center; justify-content: center; z-index: 10000; flex-direction: column; }
        #loadingOverlay.hidden { display: none; }
        .loader { text-align: center; color: white; }
        .spinner { border: 4px solid rgba(255,255,255,0.3); border-top: 4px solid #3b82f6; border-radius: 50%; width: 40px; height: 40px; animation: spin 1s linear infinite; margin: 0 auto 20px; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }

        #chunkLoadingIndicator {
            position: absolute;
            bottom: 100px;
            right: 20px;
            background: rgba(0,0,0,0.7);
            color: white;
            padding: 12px 16px;
            border-radius: 6px;
            font-size: 11px;
            z-index: 999;
            display: none;
        }
    </style>
</head>
<body>
    <div id="loadingOverlay">
        <div class="loader">
            <div class="spinner"></div>
            <h2 style="margin-top: 20px;">Initializing Flood Visualization...</h2>
            <p id="loadingProgress" style="font-size: 12px; margin-top: 10px;">0% - Loading metadata...</p>
        </div>
    </div>

    <div id="map"></div>

    <div id="chunkLoadingIndicator">
        <span id="chunkLoadingText">Loading timestep data...</span>
    </div>

    <div id="legend">
        <h3>Flood Depth (m)</h3>
        <div class="legend-item"><div class="legend-color" style="background:#bbdefb;"></div><span>&lt; 0.5</span></div>
        <div class="legend-item"><div class="legend-color" style="background:#42a5f5;"></div><span>0.5–1</span></div>
        <div class="legend-item"><div class="legend-color" style="background:#1976d2;"></div><span>1–2</span></div>
        <div class="legend-item"><div class="legend-color" style="background:#0d47a1;"></div><span>&gt; 2</span></div>
    </div>

    <div id="timelineControls">
        <div id="timeDisplay">Time: 00:00:00</div>
        <input type="range" id="timeSlider" min="0" max="336" value="0" step="1">
        <div id="sliderButtons">
            <button id="playBtn">▶️ Play</button>
            <button id="prevBtn">⏮️ Prev</button>
            <button id="nextBtn">⏭️ Next</button>
            <button id="resetBtn">🔄 Reset</button>
        </div>
        <div class="speed-control">
            Speed: <select id="playSpeed">
                <option value="100">Very Fast</option>
                <option value="200">Fast</option>
                <option value="500" selected>Normal</option>
                <option value="1000">Slow</option>
                <option value="2000">Very Slow</option>
            </select>
        </div>
        <div id="loadingStatus">Ready</div>
    </div>

    <script>
        const API_KEY = '3vyFCdEjKRCq9JRv9kWH';

        let map, scene, camera, renderer;
        let modelTransform;
        let currentTimestep = 0;
        let totalTimesteps = 336;
        let isPlaying = false;
        let playInterval = null;
        let playSpeed = 500;
        let depthScale = 1.0;
        let waterMeshes = [];
        
        // Metadata
        let polygonIndex = null;
        let polygonCount = 0;
        let coordinatesBuffer = null;

        // Chunk caching system
        const CHUNK_SIZE = 10;
        const TOTAL_CHUNKS = 34;
        const MAX_CACHED_CHUNKS = 3;
        const chunkCache = new Map();
        let chunkLoadQueue = new Set();
        let isLoadingChunk = false;

        const customLayer = {
            id: '3d-model', type: 'custom', renderingMode: '3d',
            onAdd(m, gl) {
                camera = new THREE.Camera();
                scene = new THREE.Scene();
                waterMeshes = [];
                const light = new THREE.AmbientLight(0xffffff, 0.7);
                scene.add(light);
                const dirLight = new THREE.DirectionalLight(0xffffff, 0.8);
                dirLight.position.set(100, 200, 100);
                scene.add(dirLight);
                renderer = new THREE.WebGLRenderer({ canvas: m.getCanvas(), context: gl, antialias: true });
                renderer.autoClear = false;
            },
            render(gl, matrix) {
                const rx = new THREE.Matrix4().makeRotationAxis(new THREE.Vector3(1,0,0), modelTransform.rotateX);
                const ry = new THREE.Matrix4().makeRotationAxis(new THREE.Vector3(0,1,0), modelTransform.rotateY);
                const rz = new THREE.Matrix4().makeRotationAxis(new THREE.Vector3(0,0,1), modelTransform.rotateZ);
                const m = new THREE.Matrix4().fromArray(matrix);
                const l = new THREE.Matrix4()
                    .makeTranslation(modelTransform.translateX, modelTransform.translateY, modelTransform.translateZ)
                    .scale(new THREE.Vector3(modelTransform.scale, -modelTransform.scale, modelTransform.scale))
                    .multiply(rx).multiply(ry).multiply(rz);
                camera.projectionMatrix = m.multiply(l);
                renderer.resetState();
                renderer.render(scene, camera);
                map.triggerRepaint();
            }
        };

        // Initialize map with geocoder
        map = new maplibregl.Map({
            container: 'map',
            style: `https://api.maptiler.com/maps/streets/style.json?key=${API_KEY}`,
            center: [77.027, 28.448],
            zoom: 14,
            pitch: 60,
            bearing: -20
        });

        // Add Geocoder with custom API
        const geocoderApi = {
            forwardGeocode: async (config) => {
                const features = [];
                try {
                    const request = `https://nominatim.openstreetmap.org/search?q=${config.query}&format=geojson&polygon_geojson=1&addressdetails=1`;
                    const response = await fetch(request);
                    const geojson = await response.json();
                    for (const feature of geojson.features) {
                        const center = [
                            feature.bbox[0] + (feature.bbox[2] - feature.bbox[0]) / 2,
                            feature.bbox[1] + (feature.bbox[3] - feature.bbox[1]) / 2
                        ];
                        features.push({
                            type: 'Feature',
                            geometry: { type: 'Point', coordinates: center },
                            place_name: feature.properties.display_name,
                            properties: feature.properties,
                            text: feature.properties.display_name,
                            place_type: ['place'],
                            center
                        });
                    }
                } catch (e) {
                    console.error(`Failed to forwardGeocode: ${e}`);
                }
                return { features };
            }
        };

        map.addControl(new MaplibreGeocoder(geocoderApi, { maplibregl }), 'top-left');

        map.on('style.load', () => {
            const origin = [77.027, 28.448];
            const coord = maplibregl.MercatorCoordinate.fromLngLat(origin, 0);
            modelTransform = {
                translateX: coord.x, translateY: coord.y, translateZ: coord.z,
                rotateX: Math.PI/2, rotateY: 0, rotateZ: 0,
                scale: coord.meterInMercatorCoordinateUnits()
            };
            map.addLayer(customLayer);
            initializeVisualization();
        });

        async function initializeVisualization() {
            try {
                document.getElementById('loadingProgress').textContent = '10% - Loading metadata...';
                
                const indexRes = await fetch('polygon_index.json');
                if(!indexRes.ok) throw new Error('Index file not found');
                polygonIndex = await indexRes.json();
                polygonCount = polygonIndex.length;
                
                document.getElementById('loadingProgress').textContent = '30% - Loading coordinates...';

                const coordRes = await fetch('coordinates.bin');
                if(!coordRes.ok) throw new Error('Coordinates file not found');
                coordinatesBuffer = await coordRes.arrayBuffer();
                
                document.getElementById('loadingProgress').textContent = '50% - Preloading initial chunks...';

                const chunksToPreload = [0, 1];
                await Promise.all(chunksToPreload.map(idx => loadChunkIfNeeded(idx)));
                
                document.getElementById('loadingProgress').textContent = '100% - Ready!';
                
                setTimeout(() => {
                    document.getElementById('loadingOverlay').classList.add('hidden');
                    updateTimestep(0);
                }, 500);
                
            } catch(err) {
                console.error('Error:', err);
                document.getElementById('loadingProgress').textContent = `Error: ${err.message}`;
            }
        }

        async function getDepthDataForTimestep(timestep) {
            const chunkIdx = Math.floor(timestep / CHUNK_SIZE);
            
            if(!chunkCache.has(chunkIdx)) {
                showChunkLoadingIndicator(true);
                await loadChunkIfNeeded(chunkIdx);
                showChunkLoadingIndicator(false);
            }

            const chunkData = chunkCache.get(chunkIdx);
            return chunkData ? chunkData[timestep] : null;
        }

        async function loadChunkIfNeeded(chunkIdx) {
            if(chunkCache.has(chunkIdx)) return;
            
            if(chunkLoadQueue.has(chunkIdx)) {
                while(chunkLoadQueue.has(chunkIdx)) {
                    await new Promise(r => setTimeout(r, 50));
                }
                return;
            }

            chunkLoadQueue.add(chunkIdx);
            
            try {
                console.log(`Loading chunk ${chunkIdx}/${TOTAL_CHUNKS-1}`);
                
                const chunkFile = `chunks/chunk_${String(chunkIdx).padStart(3, '0')}.bin`;
                const res = await fetch(chunkFile);
                if(!res.ok) throw new Error(`Chunk ${chunkIdx} not found`);
                
                const buffer = await res.arrayBuffer();
                const view = new Float32Array(buffer);
                
                const chunkData = {};
                const startTs = chunkIdx * CHUNK_SIZE;
                const endTs = Math.min(startTs + CHUNK_SIZE, 337);
                
                let idx = 0;
                for(let ts = startTs; ts < endTs; ts++) {
                    chunkData[ts] = view.slice(idx * polygonCount, (idx + 1) * polygonCount);
                    idx++;
                }
                
                chunkCache.set(chunkIdx, chunkData);
                console.log(`✅ Chunk ${chunkIdx} loaded: ${(buffer.byteLength / 1024 / 1024).toFixed(2)} MB`);

                if(chunkCache.size > MAX_CACHED_CHUNKS) {
                    const oldestKey = chunkCache.keys().next().value;
                    chunkCache.delete(oldestKey);
                    console.log(`Cache full - evicted chunk ${oldestKey}`);
                }
                
            } catch(err) {
                console.error('Chunk load error:', err);
            } finally {
                chunkLoadQueue.delete(chunkIdx);
            }
        }

        async function preloadNearbyChunks(currentTimestep) {
            const currentChunk = Math.floor(currentTimestep / CHUNK_SIZE);
            const nextChunk = currentChunk + 1;
            
            if(nextChunk < TOTAL_CHUNKS && !chunkCache.has(nextChunk) && !chunkLoadQueue.has(nextChunk)) {
                loadChunkIfNeeded(nextChunk).catch(err => console.error('Background preload failed:', err));
            }
        }

        function createFloodPolygons(depths) {
            if(!scene || !depths) return;
            
            waterMeshes.forEach(m => {
                scene.remove(m);
                m.geometry?.dispose();
                m.material?.dispose();
            });
            waterMeshes = [];

            const view = new DataView(coordinatesBuffer);
            let offset = 0;

            const floodedPolygons = [];
            for(let p = 0; p < polygonCount; p++) {
                const pointCount = view.getUint32(offset, true);
                offset += 4;
                
                const depth = depths[p];
                if(depth > 0) {
                    floodedPolygons.push({p, depth, startOffset: offset, pointCount});
                }
                
                offset += pointCount * 16;
            }

            if(floodedPolygons.length === 0) return;

            const depthGroups = {};
            floodedPolygons.forEach(poly => {
                let color;
                if(poly.depth < 0.5) color = '0xbbdefb';
                else if(poly.depth < 1.0) color = '0x42a5f5';
                else if(poly.depth < 2.0) color = '0x1976d2';
                else color = '0x0d47a1';

                if(!depthGroups[color]) depthGroups[color] = [];
                depthGroups[color].push(poly);
            });

            Object.entries(depthGroups).forEach(([colorStr, polygons]) => {
                const color = parseInt(colorStr);
                const vertices = [];
                const indices = [];
                let vertexCount = 0;

                polygons.forEach(poly => {
                    const {startOffset, pointCount} = poly;
                    const depth = poly.depth;
                    
                    const coords = [];
                    let readOffset = startOffset;
                    for(let i = 0; i < pointCount; i++) {
                        const lng = view.getFloat64(readOffset, true);
                        readOffset += 8;
                        const lat = view.getFloat64(readOffset, true);
                        readOffset += 8;
                        coords.push({lng, lat});
                    }

                    const bottomVerts = [];
                    const topVerts = [];

                    for(let i = 0; i < coords.length; i++) {
                        const {lng, lat} = coords[i];
                        const m = maplibregl.MercatorCoordinate.fromLngLat([lng, lat]);
                        const x = (m.x - modelTransform.translateX) / modelTransform.scale;
                        const y = (m.y - modelTransform.translateY) / modelTransform.scale;

                        vertices.push(x, 0, y);
                        bottomVerts.push(vertexCount++);

                        vertices.push(x, depth * depthScale, y);
                        topVerts.push(vertexCount++);
                    }

                    if(bottomVerts.length >= 3) {
                        for(let i = 1; i < bottomVerts.length - 1; i++) {
                            indices.push(bottomVerts[0], bottomVerts[i], bottomVerts[i+1]);
                        }
                    }

                    if(topVerts.length >= 3) {
                        for(let i = 1; i < topVerts.length - 1; i++) {
                            indices.push(topVerts[0], topVerts[i+1], topVerts[i]);
                        }
                    }

                    for(let i = 0; i < coords.length; i++) {
                        const j = (i + 1) % coords.length;
                        indices.push(
                            bottomVerts[i], bottomVerts[j], topVerts[i],
                            bottomVerts[j], topVerts[j], topVerts[i]
                        );
                    }
                });

                if(vertices.length > 0) {
                    const geometry = new THREE.BufferGeometry();
                    geometry.setAttribute('position', new THREE.BufferAttribute(new Float32Array(vertices), 3));
                    geometry.setIndex(new THREE.BufferAttribute(new Uint32Array(indices), 1));
                    geometry.computeVertexNormals();

                    const material = new THREE.MeshPhongMaterial({
                        color: color,
                        transparent: true,
                        opacity: 0.85,
                        side: THREE.DoubleSide,
                        flatShading: false
                    });

                    const mesh = new THREE.Mesh(geometry, material);
                    scene.add(mesh);
                    waterMeshes.push(mesh);
                }
            });
        }

        async function updateTimestep(step) {
            step = Math.max(0, Math.min(totalTimesteps, step));
            
            const depths = await getDepthDataForTimestep(step);
            if(!depths) return;

            currentTimestep = step;
            createFloodPolygons(depths);
            preloadNearbyChunks(step);
            updateDisplay();
        }

        function updateDisplay() {
          const baseDate = new Date('2025-07-09T01:55:00');
          const d = new Date(baseDate);
          d.setMinutes(d.getMinutes() + currentTimestep * 5);
            
          const day = String(d.getDate()).padStart(2, '0');
          const monthNames = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
          const month = monthNames[d.getMonth()];
          const year = d.getFullYear();
          const dateStr = `${day}-${month}-${year}`;
          const timeStr = d.toLocaleTimeString('en-US', { hour12: false });
            
          document.getElementById('timeDisplay').textContent = `${dateStr} - ${timeStr}`;
          document.getElementById('timeSlider').value = currentTimestep;
            
          const percentage = (currentTimestep / totalTimesteps) * 100;
          document.getElementById('timeSlider').style.background = `linear-gradient(to right, #3b82f6 0%, #3b82f6 ${percentage}%, #d1d5db ${percentage}%, #d1d5db 100%)`;
        }

        function showChunkLoadingIndicator(show) {
            document.getElementById('chunkLoadingIndicator').style.display = show ? 'block' : 'none';
        }

        document.getElementById('timeSlider').addEventListener('input', e => {
            const newStep = parseInt(e.target.value);
            updateTimestep(newStep);
        });

        document.getElementById('timeSlider').addEventListener('click', e => {
            const slider = e.target;
            const rect = slider.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const percentage = x / rect.width;
            const newStep = Math.round(percentage * totalTimesteps);
            slider.value = Math.max(0, Math.min(totalTimesteps, newStep));
            
            const evt = new Event('input', { bubbles: true });
            slider.dispatchEvent(evt);
        });

        document.getElementById('playBtn').addEventListener('click', () => {
            isPlaying = !isPlaying;
            document.getElementById('playBtn').textContent = isPlaying ? '⏸️ Pause' : '▶️ Play';
            if(isPlaying) {
                playInterval = setInterval(() => {
                    const nextStep = currentTimestep >= totalTimesteps ? 0 : currentTimestep + 1;
                    updateTimestep(nextStep);
                }, playSpeed);
            } else {
                clearInterval(playInterval);
            }
        });

        document.getElementById('prevBtn').addEventListener('click', () => {
            if(currentTimestep > 0) updateTimestep(currentTimestep - 1);
        });

        document.getElementById('nextBtn').addEventListener('click', () => {
            if(currentTimestep < totalTimesteps) updateTimestep(currentTimestep + 1);
        });

        document.getElementById('resetBtn').addEventListener('click', () => {
            if(isPlaying) document.getElementById('playBtn').click();
            updateTimestep(0);
        });

        document.getElementById('playSpeed').addEventListener('change', e => {
            playSpeed = parseInt(e.target.value);
            if(isPlaying) {
                clearInterval(playInterval);
                document.getElementById('playBtn').click();
            }
        });
    </script>
</body>
</html>
"""


@app.route('/')
def home():
    return HTML_CONTENT

# Serve static files (e.g. flood_depth_master_slim.geojson, flood_depths.bin) from the same directory as this script
@app.route('/<path:filename>')
def static_files(filename):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return send_from_directory(base_dir, filename)

if __name__ == '__main__':
    print("Starting FloodTwin server on http://0.0.0.0:9120")
    serve(
        app,
        host='0.0.0.0',
        port=9120,
        threads=8,              # User requested
        channel_timeout=300,    # User requested
        ident='3DFloodTwin',      # Server identity
        connection_limit=500,   # Limit connections for small scale
        cleanup_interval=30     # Cleanup inactive connections
    )

