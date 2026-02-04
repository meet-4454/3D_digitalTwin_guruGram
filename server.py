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
<title>3D Flood Twin</title>
<script src="https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.js"></script>
<link rel="stylesheet" href="https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.css" />
<script src="https://unpkg.com/@maplibre/maplibre-gl-geocoder@1.5.0/dist/maplibre-gl-geocoder.min.js"></script>
<link rel="stylesheet" href="https://unpkg.com/@maplibre/maplibre-gl-geocoder@1.5.0/dist/maplibre-gl-geocoder.css" />
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<style>
/* ──────────────────────────── RESET & BASE ──────────────────────── */
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  overflow: hidden;
  font-family: 'Segoe UI', system-ui, sans-serif;
  background: #f8fafc;
  color: #1e293b;
}
#map { width: 100vw; height: 100vh; }

/* ──────────────────────────── SIDEBAR ────────────────────────────── */
#sidebar {
  position: absolute;
  top: 0; left: 0;
  width: 20vw;
  min-width: 320px;
  height: 100vh;
  background: linear-gradient(180deg, #ffffff 0%, #f1f5f9 100%);
  border-right: 2px solid #5298A9;
  z-index: 1000;
  display: flex;
  flex-direction: column;
  transition: transform .30s cubic-bezier(.4,0,.2,1);
  overflow-y: auto;
  overflow-x: hidden;
  scrollbar-width: thin;
  scrollbar-color: #5298A9 transparent;
  box-shadow: 4px 0 12px rgba(82, 152, 169, 0.15);
}
#sidebar.collapsed { transform: translateX(-100%); }

/* scrollbar chrome */
#sidebar::-webkit-scrollbar { width: 8px; }
#sidebar::-webkit-scrollbar-track { background: transparent; }
#sidebar::-webkit-scrollbar-thumb { background: #B1DEE2; border-radius: 4px; }
#sidebar::-webkit-scrollbar-thumb:hover { background: #5298A9; }

/* ── title bar ── */
#titleBar {
  padding: 24px 24px 16px;
  flex-shrink: 0;
  border-bottom: 1px solid #e2e8f0;
}
#titleBar h1 {
  font-size: 24px;
  font-weight: 700;
  color: #5298A9;
  letter-spacing: 0.5px;
  margin: 0;
}

/* ── geocoder strip ── */
#geocoderWrap {
  padding: 20px 24px 16px;
  flex-shrink: 0;
}
/* Override maplibre geocoder internals to match light theme */
.maplibregl-ctrl-geocoder { width: 100% !important; box-shadow: none !important; }
.maplibregl-ctrl-geocoder .maplibregl-ctrl-geocoder--input {
  background: #ffffff !important;
  border: 2px solid #B1DEE2 !important;
  border-radius: 10px !important;
  color: #1e293b !important;
  padding: 16px 20px 16px 52px !important;
  font-size: 16px !important;
  box-shadow: 0 2px 8px rgba(82, 152, 169, 0.1) !important;
  height: 52px !important;
}
.maplibregl-ctrl-geocoder .maplibregl-ctrl-geocoder--input:focus {
  border-color: #5298A9 !important;
  box-shadow: 0 0 0 3px rgba(82, 152, 169, 0.15) !important;
}
.maplibregl-ctrl-geocoder .maplibregl-ctrl-geocoder--icon { 
  filter: none;
  left: 16px !important;
}
.maplibregl-ctrl-geocoder--suggestion {
  background: #ffffff !important;
  color: #1e293b !important;
  border-bottom: 1px solid #e2e8f0 !important;
  font-size: 15px !important;
  padding: 12px 16px !important;
}
.maplibregl-ctrl-geocoder--suggestion:hover { background: #f8fafc !important; }
.maplibregl-ctrl-geocoder .maplibregl-ctrl-geocoder--suggestion-details { 
  color: #64748b !important;
  font-size: 14px !important;
}

/* ── collapse toggle (chevron pill that sits at the right edge) ── */
#collapseBtn {
  position: absolute;
  top: 50%;
  right: -20px;
  transform: translateY(-50%);
  width: 40px; height: 40px;
  background: #ffffff;
  border: 2px solid #5298A9;
  border-radius: 50%;
  color: #5298A9;
  font-size: 20px;
  cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  z-index: 1001;
  transition: background .2s, transform .3s;
  box-shadow: 2px 2px 8px rgba(82, 152, 169, 0.25);
}
#collapseBtn:hover { 
  background: #f1f5f9;
  transform: translateY(-50%) scale(1.05);
}
#sidebar.collapsed #collapseBtn { right: -42px; }

/* ── panel card ── */
.panel {
  margin: 0 24px 12px;
  background: #ffffff;
  border: 2px solid #B1DEE2;
  border-radius: 12px;
  padding: 24px 20px;
  flex-shrink: 0;
  box-shadow: 0 2px 8px rgba(82, 152, 169, 0.08);
}
.panel-header {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 18px;
}
.panel-header-left { display: flex; align-items: center; gap: 12px; }
.panel-icon {
  width: 28px; height: 28px;
  display: flex; align-items: center; justify-content: center;
  color: #5298A9;
  font-size: 20px;
}
.panel-title { 
  font-size: 18px; 
  font-weight: 700; 
  color: #264351; 
  letter-spacing: 0.3px; 
}
.panel-badge {
  font-size: 13px; 
  font-weight: 700;
  background: #B1DEE2;
  color: #264351;
  padding: 4px 12px;
  border-radius: 12px;
  letter-spacing: 0.4px;
}

/* divider between panels */
.panel-divider { 
  height: 2px; 
  background: linear-gradient(to right, transparent, #B1DEE2, transparent);
  margin: 8px 24px; 
  flex-shrink: 0; 
}

/* ── timeline current‑time box ── */
#timeBox {
  background: #f8fafc;
  border: 2px solid #B1DEE2;
  border-radius: 10px;
  padding: 14px 18px;
  text-align: center;
  margin-bottom: 18px;
}
#timeBoxLabel { 
  font-size: 13px; 
  color: #64748b; 
  text-transform: uppercase; 
  letter-spacing: 1px; 
  margin-bottom: 6px;
  font-weight: 600;
}
#timeDisplay { 
  font-size: 20px; 
  font-weight: 700; 
  color: #264351; 
  font-variant-numeric: tabular-nums; 
}

/* ── time slider ── */
#sliderRow { position: relative; margin-bottom: 8px; }
#sliderLabels { 
  display: flex; 
  justify-content: space-between; 
  font-size: 13px; 
  color: #64748b; 
  margin-bottom: 6px;
  font-weight: 600;
}
#timeSlider {
  -webkit-appearance: none; appearance: none;
  width: 100%; height: 8px;
  border-radius: 4px;
  background: #e2e8f0;
  outline: none; cursor: pointer;
}
#timeSlider::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 22px; height: 22px;
  background: #5298A9;
  border: 3px solid #ffffff;
  border-radius: 50%;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(82, 152, 169, 0.4);
}
#timeSlider::-moz-range-thumb {
  width: 22px; height: 22px;
  background: #5298A9;
  border: 3px solid #ffffff;
  border-radius: 50%;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(82, 152, 169, 0.4);
}

/* ── transport buttons ── */
#transportBtns {
  display: flex; gap: 12px; justify-content: center;
  margin-top: 18px;
}
.tbtn {
  width: 48px; height: 48px;
  border-radius: 50%;
  background: #ffffff;
  border: 2px solid #B1DEE2;
  color: #5298A9;
  font-size: 20px;
  cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  transition: all .2s;
  box-shadow: 0 2px 6px rgba(82, 152, 169, 0.1);
}
.tbtn:hover {
  background: #f8fafc;
  border-color: #5298A9;
  transform: scale(1.05);
  box-shadow: 0 4px 12px rgba(82, 152, 169, 0.2);
}
.tbtn.active {
  background: #5298A9;
  border-color: #5298A9;
  color: #ffffff;
  box-shadow: 0 4px 12px rgba(82, 152, 169, 0.3);
}

/* ── speed pills ── */
#speedPills { display: flex; gap: 8px; }
.speed-pill {
  flex: 1;
  padding: 12px 0;
  border-radius: 8px;
  background: #ffffff;
  border: 2px solid #B1DEE2;
  color: #5298A9;
  font-size: 15px; 
  font-weight: 700;
  text-align: center;
  cursor: pointer;
  transition: all .2s;
}
.speed-pill:hover { 
  border-color: #5298A9; 
  background: #f8fafc;
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(82, 152, 169, 0.15);
}
.speed-pill.active {
  background: #5298A9;
  border-color: #5298A9;
  color: #ffffff;
  box-shadow: 0 4px 12px rgba(82, 152, 169, 0.3);
}

/* ── opacity row ── */
.opacity-row {
  display: flex; align-items: center; margin-bottom: 16px;
}
.opacity-row:last-child { margin-bottom: 0; }
.opacity-dot { 
  width: 14px; 
  height: 14px; 
  border-radius: 50%; 
  margin-right: 12px; 
  flex-shrink: 0;
  border: 2px solid #5298A9;
}
.opacity-label { 
  font-size: 16px; 
  color: #264351; 
  flex: 1;
  font-weight: 600;
}
.opacity-value { 
  font-size: 15px; 
  color: #5298A9; 
  font-weight: 700; 
  width: 48px; 
  text-align: right; 
  margin-left: 10px; 
}
.opacity-slider-wrap { width: 100%; margin-top: 8px; }
.opacity-slider {
  -webkit-appearance: none; appearance: none;
  width: 100%; height: 6px;
  border-radius: 3px;
  background: #e2e8f0;
  outline: none; cursor: pointer;
}
.opacity-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 20px; height: 20px;
  background: #5298A9;
  border: 3px solid #ffffff;
  border-radius: 50%;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(82, 152, 169, 0.4);
}
.opacity-slider::-moz-range-thumb {
  width: 20px; height: 20px;
  background: #5298A9;
  border: 3px solid #ffffff;
  border-radius: 50%;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(82, 152, 169, 0.4);
}

/* ──────────────────────── LEGEND CARD (top-right) ──────────────── */
#legend {
  position: absolute;
  top: 28px; right: 28px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(8px);
  border: 2px solid #5298A9;
  border-radius: 14px;
  padding: 24px 28px;
  z-index: 999;
  min-width: 240px;
  box-shadow: 0 4px 20px rgba(82, 152, 169, 0.2);
}
.legend-header {
  display: flex; align-items: center; gap: 12px;
  margin-bottom: 20px;
}
.legend-icon { 
  color: #5298A9; 
  font-size: 22px; 
}
.legend-title { 
  font-size: 19px; 
  font-weight: 700; 
  color: #264351;
  letter-spacing: 0.3px;
}
.legend-row {
  display: flex; 
  align-items: center;
  margin-bottom: 14px;
  gap: 14px;
}
.legend-row:last-child { margin-bottom: 0; }
.legend-swatch {
  width: 48px; 
  height: 24px;
  border-radius: 6px;
  flex-shrink: 0;
  border: 1px solid #B1DEE2;
}
.legend-range { 
  font-size: 16px; 
  color: #264351; 
  flex: 1;
  font-weight: 600;
  min-width: 80px;
}
.legend-severity { 
  font-size: 14px; 
  font-weight: 700; 
  color: #5298A9; 
  text-transform: uppercase; 
  letter-spacing: 0.5px;
  min-width: 85px;
  text-align: right;
}

/* ──────────────────────── LOADING OVERLAY ──────────────────────── */
#loadingOverlay {
  position: fixed; inset: 0;
  background: rgba(255, 255, 255, 0.95);
  display: flex; align-items: center; justify-content: center;
  z-index: 10000; flex-direction: column;
}
#loadingOverlay.hidden { display: none; }
.spinner {
  border: 5px solid #e2e8f0;
  border-top: 5px solid #5298A9;
  border-radius: 50%;
  width: 50px; height: 50px;
  animation: spin .8s linear infinite;
  margin: 0 auto 24px;
}
@keyframes spin { to { transform: rotate(360deg); } }
.loader { text-align: center; color: #264351; }
.loader h2 { font-size: 26px; margin-top: 20px; font-weight: 700; }
#loadingProgress { font-size: 16px; color: #64748b; margin-top: 10px; font-weight: 600; }

/* ──────────────────────── CHUNK LOADING TOAST ────────────────── */
#chunkLoadingIndicator {
  position: absolute; bottom: 70px; right: 28px;
  background: rgba(255, 255, 255, 0.95);
  border: 2px solid #5298A9;
  color: #5298A9;
  padding: 12px 20px; 
  border-radius: 10px;
  font-size: 15px; 
  z-index: 999;
  display: none;
  backdrop-filter: blur(6px);
  font-weight: 600;
  box-shadow: 0 4px 12px rgba(82, 152, 169, 0.2);
}

/* ──────────────────────── HIDE DEFAULT MAPLIBRE CONTROLS ────── */
.maplibregl-ctrl-attrib { display: none !important; }

/* ── ensure Marker DOM layer paints ABOVE the WebGL canvas ── */
.maplibregl-markers { z-index: 2 !important; position: relative !important; }

/* ── hamburger: fully hidden when sidebar is open so it doesn't
       overlap the geocoder search icon ── */
#hamburgerBtn.open { opacity: 0; pointer-events: none; transition: opacity .25s; }

/* ──────────────────────── HAMBURGER BUTTON ─────────────────────── */
#hamburgerBtn {
  position: fixed;
  top: 22px; left: 22px;
  width: 48px; height: 48px;
  z-index: 1002;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(6px);
  border: 2px solid #5298A9;
  border-radius: 12px;
  cursor: pointer;
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  gap: 6px;
  transition: all .2s;
  box-shadow: 0 3px 12px rgba(82, 152, 169, 0.25);
}
#hamburgerBtn:hover {
  background: #f8fafc;
  border-color: #49879A;
  transform: scale(1.05);
}
#hamburgerBtn span {
  display: block;
  width: 24px; height: 3px;
  background: #5298A9;
  border-radius: 2px;
  transition: transform .25s, opacity .25s;
}
/* animate to ✕ when sidebar is open */
#hamburgerBtn.open span:nth-child(1){ transform: translateY(9px) rotate(45deg); }
#hamburgerBtn.open span:nth-child(2){ opacity: 0; }
#hamburgerBtn.open span:nth-child(3){ transform: translateY(-9px) rotate(-45deg); }

/* ──────────────────────── CRITICAL ASSETS PANEL ────────────────── */
/* toggle-pill grid */
#assetGrid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 8px;
}
.asset-pill {
  display: flex; 
  align-items: center; 
  gap: 12px;
  padding: 12px 16px;
  border-radius: 10px;
  background: #ffffff;
  border: 2px solid #B1DEE2;
  cursor: pointer;
  transition: all .2s;
  user-select: none;
  min-height: 48px;
}
.asset-pill:hover { 
  border-color: #5298A9;
  background: #f8fafc;
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(82, 152, 169, 0.15);
}
.asset-pill.on {
  border-color: var(--pill-accent);
  background: color-mix(in srgb, var(--pill-accent) 8%, #ffffff);
  box-shadow: 0 0 12px color-mix(in srgb, var(--pill-accent) 20%, transparent);
}
.asset-pill .pill-icon {
  font-size: 18px;
  flex-shrink: 0;
  width: 24px; 
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.asset-pill .pill-label {
  font-size: 13px; 
  font-weight: 700;
  color: #5298A9;
  white-space: nowrap; 
  overflow: hidden; 
  text-overflow: ellipsis;
  transition: color .18s;
  flex: 1;
  line-height: 1.2;
}
.asset-pill.on .pill-label { color: #264351; }

/* tiny count badge that appears next to label when markers exist */
.asset-pill .pill-count {
  margin-left: auto;
  font-size: 11px; 
  font-weight: 700;
  background: #B1DEE2;
  color: #264351;
  padding: 3px 9px;
  border-radius: 10px;
  flex-shrink: 0;
  display: none;
  min-width: 24px;
  text-align: center;
}
.asset-pill.on .pill-count { display: block; }

/* skeleton pulse while OSM data loads */
@keyframes skel { 0%,100%{ opacity:.25 } 50%{ opacity:.5 } }
.asset-skel {
  height: 48px; 
  border-radius: 10px;
  background: #e2e8f0;
  animation: skel 1.4s ease infinite;
}

/* ──────────────────────── OSM MAP MARKERS ──────────────────────── */
.osm-marker {
  width: 32px; height: 32px;
  border-radius: 50% 50% 50% 4px;
  border: 3px solid #fff;
  display: flex; align-items: center; justify-content: center;
  font-size: 16px;
  cursor: pointer;
  box-shadow: 0 4px 10px rgba(0,0,0,.35);
  transform: translate(-50%, -100%);
  transition: transform .15s;
  -webkit-user-select: none;
}
.osm-marker:hover { transform: translate(-50%, -100%) scale(1.15); }

/* popup that appears on marker click */
.osm-popup .maplibregl-popup-content {
  background: rgba(255, 255, 255, 0.98) !important;
  border: 2px solid #5298A9 !important;
  border-radius: 12px !important;
  color: #264351 !important;
  padding: 14px 16px !important;
  font-size: 15px !important;
  box-shadow: 0 4px 20px rgba(82, 152, 169, 0.3) !important;
  max-width: 220px !important;
}
.osm-popup .maplibregl-popup-close {
  color: #64748b !important;
  font-size: 20px !important;
  top: 6px !important; right: 8px !important;
}
.osm-popup .maplibregl-popup-close:hover { color: #264351 !important; }
.popup-name { font-weight: 700; color: #264351; margin-bottom: 4px; font-size: 16px; }
.popup-type { font-size: 13px; color: #5298A9; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 700; }
.popup-addr { font-size: 13px; color: #64748b; margin-top: 6px; padding-top: 6px; border-top: 2px solid #e2e8f0; }
</style>
</head>
<body>

<!-- ── hamburger toggle (always visible) ── -->
<button id="hamburgerBtn" class="open" aria-label="Toggle sidebar">
  <span></span><span></span><span></span>
</button>

<!-- ── loading screen ── -->
<div id="loadingOverlay">
  <div class="loader">
    <div class="spinner"></div>
    <h2>Initializing Flood Visualization…</h2>
    <p id="loadingProgress">0% – Loading metadata…</p>
  </div>
</div>

<!-- ── map canvas ── -->
<div id="map"></div>

<!-- ── chunk‑loading toast ── -->
<div id="chunkLoadingIndicator">Loading timestep data…</div>

<!-- ══════════════════════ SIDEBAR ══════════════════════════════ -->
<div id="sidebar">
  <button id="collapseBtn" title="Toggle sidebar">‹</button>

  <!-- title bar -->
  <div id="titleBar">
    <h1>Flood Twin</h1>
  </div>

  <!-- geocoder -->
  <div id="geocoderWrap"></div>

  <!-- ── Time Control panel ── -->
  <div class="panel">
    <div class="panel-header">
      <div class="panel-header-left">
        <div class="panel-icon">🕐</div>
        <span class="panel-title">Time Control</span>
      </div>      
    </div>

    <div id="timeBox">
      <div id="timeBoxLabel">Current Time</div>
      <div id="timeDisplay">09-July-2025 00:00:00</div>
    </div>

    <div id="sliderRow">
      <input type="range" id="timeSlider" min="0" max="336" value="0" step="1">
    </div>

    <div id="transportBtns">
      <button class="tbtn" id="resetBtn" title="Reset">↺</button>
      <button class="tbtn" id="prevBtn" title="Previous">⏮</button>
      <button class="tbtn" id="playBtn" title="Play">▶</button>
      <button class="tbtn" id="nextBtn" title="Next">⏭</button>
    </div>
  </div>

  <div class="panel-divider"></div>

  <!-- ── Playback Speed panel ── -->
  <div class="panel">
    <div class="panel-header">
      <div class="panel-header-left">
        <div class="panel-icon">🔄</div>
        <span class="panel-title">Playback Speed</span>
      </div>
    </div>
    <div id="speedPills">
      <div class="speed-pill" data-speed="1000">0.5x</div>
      <div class="speed-pill active" data-speed="500">Normal</div>
      <div class="speed-pill" data-speed="250">2x</div>
      <div class="speed-pill" data-speed="125">4x</div>
    </div>
  </div>

  <div class="panel-divider"></div>

  <!-- ── Layer Opacity panel (Flood Layer only) ── -->
  <div class="panel">
    <div class="panel-header">
      <div class="panel-header-left">
        <div class="panel-icon">☰</div>
        <span class="panel-title">Layer Opacity</span>
      </div>
    </div>
    <div class="opacity-row">
      <div class="opacity-dot" style="background:#5298A9;"></div>
      <span class="opacity-label">Flood Layer</span>
      <span class="opacity-value" id="floodOpVal">70%</span>
    </div>
    <div class="opacity-slider-wrap">
      <input type="range" class="opacity-slider" id="floodOpSlider" min="0" max="100" value="70">
    </div>
  </div>

  <div class="panel-divider"></div>

  <!-- ── Critical Assets panel ── -->
  <div class="panel" style="margin-bottom:32px;">
    <div class="panel-header">
      <div class="panel-header-left">
        <div class="panel-icon">📍</div>
        <span class="panel-title">Critical Assets</span>
      </div>
      <span class="panel-badge" id="assetBadge">Loading…</span>
    </div>
    <!-- skeleton shown while OSM fetches; replaced by pills on success -->
    <div id="assetGrid">
      <div class="asset-skel"></div>
      <div class="asset-skel"></div>
      <div class="asset-skel"></div>
      <div class="asset-skel"></div>
      <div class="asset-skel"></div>
      <div class="asset-skel"></div>
      <div class="asset-skel"></div>
      <div class="asset-skel"></div>
    </div>
  </div>
</div>

<!-- ══════════════════════ LEGEND ══════════════════════════════ -->
<div id="legend">
  <div class="legend-header">
    <span class="legend-icon">💧</span>
    <span class="legend-title">Flood Depth</span>
  </div>
  <div class="legend-row">
    <div class="legend-swatch" style="background:linear-gradient(135deg,#B1DEE2,#6BC3D2);"></div>
    <span class="legend-range">&lt; 0.5m</span>
    <span class="legend-severity">Low</span>
  </div>
  <div class="legend-row">
    <div class="legend-swatch" style="background:linear-gradient(135deg,#64B8C1,#5298A9);"></div>
    <span class="legend-range">0.5–1m</span>
    <span class="legend-severity">Moderate</span>
  </div>
  <div class="legend-row">
    <div class="legend-swatch" style="background:linear-gradient(135deg,#5298A9,#49879A);"></div>
    <span class="legend-range">1–2m</span>
    <span class="legend-severity">High</span>
  </div>
  <div class="legend-row">
    <div class="legend-swatch" style="background:linear-gradient(135deg,#49879A,#264351);"></div>
    <span class="legend-range">&gt; 2m</span>
    <span class="legend-severity">Severe</span>
  </div>
</div>

<!-- ═══════════════════════ SCRIPT ════════════════════════════ -->
<script>
(function(){
  /* ─── config ─── */
  const API_KEY = '3vyFCdEjKRCq9JRv9kWH';
  const CHUNK_SIZE    = 10;
  const TOTAL_CHUNKS  = 34;
  const MAX_CACHED    = 3;
  let   totalTimesteps = 336;

  /* ─── state ─── */
  let map, scene, camera, renderer, modelTransform;
  let currentTimestep = 0;
  let isPlaying       = false;
  let playInterval    = null;
  let playSpeed       = 500;
  let depthScale      = 1.0;
  let floodOpacity    = 0.70;
  let waterMeshes     = [];

  let polygonIndex    = null;
  let polygonCount    = 0;
  let coordinatesBuffer = null;

  const chunkCache    = new Map();
  const chunkLoadQueue = new Set();

  /* ─── three.js custom layer ─── */
  const customLayer = {
    id:'3d-model', type:'custom', renderingMode:'3d',
    onAdd(m, gl){
      camera   = new THREE.Camera();
      scene    = new THREE.Scene();
      waterMeshes = [];
      scene.add(new THREE.AmbientLight(0xffffff, 0.7));
      const d  = new THREE.DirectionalLight(0xffffff, 0.8);
      d.position.set(100,200,100);
      scene.add(d);
      renderer = new THREE.WebGLRenderer({ canvas: m.getCanvas(), context: gl, antialias: true });
      renderer.autoClear = false;
    },
    render(gl, matrix){
      const rx = new THREE.Matrix4().makeRotationAxis(new THREE.Vector3(1,0,0), modelTransform.rotateX);
      const ry = new THREE.Matrix4().makeRotationAxis(new THREE.Vector3(0,1,0), modelTransform.rotateY);
      const rz = new THREE.Matrix4().makeRotationAxis(new THREE.Vector3(0,0,1), modelTransform.rotateZ);
      const m  = new THREE.Matrix4().fromArray(matrix);
      const l  = new THREE.Matrix4()
        .makeTranslation(modelTransform.translateX, modelTransform.translateY, modelTransform.translateZ)
        .scale(new THREE.Vector3(modelTransform.scale, -modelTransform.scale, modelTransform.scale))
        .multiply(rx).multiply(ry).multiply(rz);
      camera.projectionMatrix = m.multiply(l);
      renderer.resetState();
      renderer.render(scene, camera);
      map.triggerRepaint();
    }
  };

  /* ─── map init ─── */
  map = new maplibregl.Map({
    container:'map',
    style: `https://api.maptiler.com/maps/streets/style.json?key=${API_KEY}`,
    center:[77.027,28.448], zoom:14, pitch:60, bearing:-20
  });

  /* ─── geocoder (light‑themed, mounted inside sidebar) ─── */
  const geocoderApi = {
    forwardGeocode: async (config) => {
      const features = [];
      try {
        const res = await fetch(
          `https://nominatim.openstreetmap.org/search?q=${config.query}&format=geojson&polygon_geojson=1&addressdetails=1`
        );
        const geojson = await res.json();
        for(const f of geojson.features){
          const center = [
            f.bbox[0]+(f.bbox[2]-f.bbox[0])/2,
            f.bbox[1]+(f.bbox[3]-f.bbox[1])/2
          ];
          features.push({
            type:'Feature',
            geometry:{ type:'Point', coordinates:center },
            place_name: f.properties.display_name,
            properties: f.properties,
            text: f.properties.display_name,
            place_type:['place'],
            center
          });
        }
      } catch(e){ console.error(e); }
      return { features };
    }
  };

  /* Mount geocoder into sidebar div instead of map control */
  const geocoder = new MaplibreGeocoder(geocoderApi, { maplibregl, placeholder:'Search location…' });
  map.addControl(geocoder, 'top-left');
  setTimeout(() => {
    const el = document.querySelector('.maplibregl-ctrl-geocoder');
    if(el) document.getElementById('geocoderWrap').appendChild(el);
  }, 200);

  /* ─── style.load → bootstrap three layer + data ─── */
  map.on('style.load', () => {
    const origin = [77.027,28.448];
    const coord  = maplibregl.MercatorCoordinate.fromLngLat(origin,0);
    modelTransform = {
      translateX: coord.x, translateY: coord.y, translateZ: coord.z,
      rotateX: Math.PI/2, rotateY: 0, rotateZ: 0,
      scale: coord.meterInMercatorCoordinateUnits()
    };
    map.addLayer(customLayer);
    initializeVisualization();
    loadAllAssets();
  });

  /* ─── data loading ─── */
  async function initializeVisualization(){
    try {
      setStatus('10% – Loading metadata…');
      const idxRes = await fetch('polygon_index.json');
      if(!idxRes.ok) throw new Error('Index file not found');
      polygonIndex = await idxRes.json();
      polygonCount = polygonIndex.length;

      setStatus('30% – Loading coordinates…');
      const cRes = await fetch('coordinates.bin');
      if(!cRes.ok) throw new Error('Coordinates file not found');
      coordinatesBuffer = await cRes.arrayBuffer();

      setStatus('50% – Preloading initial chunks…');
      await Promise.all([loadChunkIfNeeded(0), loadChunkIfNeeded(1)]);

      setStatus('100% – Ready!');
      setTimeout(() => {
        document.getElementById('loadingOverlay').classList.add('hidden');
        updateTimestep(0);
      }, 500);
    } catch(err){
      console.error(err);
      setStatus('Error: ' + err.message);
    }
  }

  function setStatus(txt){
    document.getElementById('loadingProgress').textContent = txt;
  }

  /* ─── chunk management ─── */
  async function loadChunkIfNeeded(idx){
    if(chunkCache.has(idx)) return;
    if(chunkLoadQueue.has(idx)){
      while(chunkLoadQueue.has(idx)) await new Promise(r=>setTimeout(r,50));
      return;
    }
    chunkLoadQueue.add(idx);
    try {
      const res = await fetch(`chunks/chunk_${String(idx).padStart(3,'0')}.bin`);
      if(!res.ok) throw new Error(`Chunk ${idx} not found`);
      const buf  = await res.arrayBuffer();
      const view = new Float32Array(buf);
      const data = {};
      const start = idx * CHUNK_SIZE;
      const end   = Math.min(start + CHUNK_SIZE, 337);
      let i = 0;
      for(let ts = start; ts < end; ts++, i++)
        data[ts] = view.slice(i*polygonCount, (i+1)*polygonCount);
      chunkCache.set(idx, data);
      if(chunkCache.size > MAX_CACHED){
        chunkCache.delete(chunkCache.keys().next().value);
      }
    } catch(e){ console.error(e); }
    finally { chunkLoadQueue.delete(idx); }
  }

  async function getDepthDataForTimestep(ts){
    const ci = Math.floor(ts/CHUNK_SIZE);
    if(!chunkCache.has(ci)){
      showChunkToast(true);
      await loadChunkIfNeeded(ci);
      showChunkToast(false);
    }
    const c = chunkCache.get(ci);
    return c ? c[ts] : null;
  }

  function preloadNearbyChunks(ts){
    const next = Math.floor(ts/CHUNK_SIZE)+1;
    if(next < TOTAL_CHUNKS && !chunkCache.has(next) && !chunkLoadQueue.has(next))
      loadChunkIfNeeded(next).catch(()=>{});
  }

  function showChunkToast(show){
    document.getElementById('chunkLoadingIndicator').style.display = show?'block':'none';
  }

  /* ─── flood polygon rendering ─── */
  function createFloodPolygons(depths){
    if(!scene || !depths) return;
    waterMeshes.forEach(m=>{ scene.remove(m); m.geometry?.dispose(); m.material?.dispose(); });
    waterMeshes = [];

    const dv     = new DataView(coordinatesBuffer);
    let   offset = 0;
    const flooded = [];

    for(let p = 0; p < polygonCount; p++){
      const pc = dv.getUint32(offset, true);
      offset += 4;
      if(depths[p] > 0) flooded.push({ p, depth: depths[p], startOffset: offset, pointCount: pc });
      offset += pc * 16;
    }
    if(!flooded.length) return;

    const groups = {};
    flooded.forEach(poly => {
      const c = poly.depth < 0.5 ? '0xB1DEE2'
              : poly.depth < 1.0 ? '0x5298A9'
              : poly.depth < 2.0 ? '0x49879A'
              :                    '0x264351';
      (groups[c] = groups[c] || []).push(poly);
    });

    Object.entries(groups).forEach(([colStr, polys]) => {
      const color    = parseInt(colStr);
      const verts    = [];
      const indices  = [];
      let   vc       = 0;

      polys.forEach(poly => {
        const coords = [];
        let ro = poly.startOffset;
        for(let i = 0; i < poly.pointCount; i++){
          coords.push({ lng: dv.getFloat64(ro,true), lat: dv.getFloat64(ro+8,true) });
          ro += 16;
        }
        const bot = [], top = [];
        coords.forEach(({ lng, lat }) => {
          const m = maplibregl.MercatorCoordinate.fromLngLat([lng,lat]);
          const x = (m.x - modelTransform.translateX) / modelTransform.scale;
          const y = (m.y - modelTransform.translateY) / modelTransform.scale;
          verts.push(x, 0, y);               bot.push(vc++);
          verts.push(x, poly.depth*depthScale, y); top.push(vc++);
        });
        for(let i=1; i<bot.length-1; i++) indices.push(bot[0], bot[i], bot[i+1]);
        for(let i=1; i<top.length-1; i++) indices.push(top[0], top[i+1], top[i]);
        for(let i=0; i<coords.length; i++){
          const j=(i+1)%coords.length;
          indices.push(bot[i], bot[j], top[i], bot[j], top[j], top[i]);
        }
      });

      if(!verts.length) return;
      const geo  = new THREE.BufferGeometry();
      geo.setAttribute('position', new THREE.BufferAttribute(new Float32Array(verts),3));
      geo.setIndex(new THREE.BufferAttribute(new Uint32Array(indices),1));
      geo.computeVertexNormals();

      const mat  = new THREE.MeshPhongMaterial({
        color, transparent:true, opacity: floodOpacity,
        side: THREE.DoubleSide, flatShading: false
      });
      const mesh = new THREE.Mesh(geo, mat);
      scene.add(mesh);
      waterMeshes.push(mesh);
    });
  }

  /* ─── timestep update ─── */
  async function updateTimestep(step){
    step = Math.max(0, Math.min(totalTimesteps, step));
    const depths = await getDepthDataForTimestep(step);
    if(!depths) return;
    currentTimestep = step;
    createFloodPolygons(depths);
    preloadNearbyChunks(step);
    updateDisplay();
  }

  /* ─── display helpers ─── */
  function updateDisplay(){
    const base = new Date('2025-07-09T01:55:00');
    base.setMinutes(base.getMinutes() + currentTimestep*5);
    const dd  = String(base.getDate()).padStart(2,'0');
    const mon = ['January','February','March','April','May','June','July','August','September','October','November','December'][base.getMonth()];
    const yyyy= base.getFullYear();
    const hh  = String(base.getHours()).padStart(2,'0');
    const mm  = String(base.getMinutes()).padStart(2,'0');
    const ss  = String(base.getSeconds()).padStart(2,'0');

    document.getElementById('timeDisplay').textContent = `${dd}-${mon}-${yyyy} ${hh}:${mm}:${ss}`;

    const slider = document.getElementById('timeSlider');
    slider.value = currentTimestep;
    const pct = (currentTimestep/totalTimesteps)*100;
    slider.style.background = `linear-gradient(to right, #5298A9 0%, #5298A9 ${pct}%, #e2e8f0 ${pct}%, #e2e8f0 100%)`;
  }

  /* ──────────────── UI EVENT WIRING ──────────────── */

  function toggleSidebar(){
    const sb  = document.getElementById('sidebar');
    const ham = document.getElementById('hamburgerBtn');
    const chv = document.getElementById('collapseBtn');
    const isNowCollapsed = sb.classList.toggle('collapsed');
    ham.classList.toggle('open', !isNowCollapsed);
    chv.innerHTML = isNowCollapsed ? '›' : '‹';
  }
  document.getElementById('hamburgerBtn').addEventListener('click', toggleSidebar);
  document.getElementById('collapseBtn').addEventListener('click', toggleSidebar);

  document.getElementById('timeSlider').addEventListener('input', e => updateTimestep(+e.target.value));

  document.getElementById('playBtn').addEventListener('click', () => {
    isPlaying = !isPlaying;
    document.getElementById('playBtn').classList.toggle('active', isPlaying);
    document.getElementById('playBtn').innerHTML = isPlaying ? '⏸' : '▶';
    if(isPlaying){
      playInterval = setInterval(() => {
        updateTimestep(currentTimestep >= totalTimesteps ? 0 : currentTimestep+1);
      }, playSpeed);
    } else { clearInterval(playInterval); }
  });
  document.getElementById('prevBtn').addEventListener('click', () => { if(currentTimestep>0) updateTimestep(currentTimestep-1); });
  document.getElementById('nextBtn').addEventListener('click', () => { if(currentTimestep<totalTimesteps) updateTimestep(currentTimestep+1); });
  document.getElementById('resetBtn').addEventListener('click', () => {
    if(isPlaying) document.getElementById('playBtn').click();
    updateTimestep(0);
  });

  document.querySelectorAll('.speed-pill').forEach(pill => {
    pill.addEventListener('click', () => {
      document.querySelectorAll('.speed-pill').forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
      playSpeed = +pill.dataset.speed;
      if(isPlaying){ clearInterval(playInterval); document.getElementById('playBtn').click(); }
    });
  });

  document.getElementById('floodOpSlider').addEventListener('input', e => {
    floodOpacity = +e.target.value / 100;
    document.getElementById('floodOpVal').textContent = e.target.value + '%';
    waterMeshes.forEach(m => { if(m.material) m.material.opacity = floodOpacity; });
  });

  /* ═══════════════════════════════════════════════════════════════════
     CRITICAL ASSETS  —  OSM Overpass fetch · map markers · toggle pills
     ═══════════════════════════════════════════════════════════════════ */

  const ASSET_CATS = [
    { key:'hospital',     icon:'🏥', label:'Hospitals',      accent:'#ef4444', tags:'["amenity"="hospital"]' },
    { key:'school',       icon:'🏫', label:'Schools',        accent:'#10b981', tags:'["amenity"="school"]' },
    { key:'college',      icon:'🎓', label:'Colleges',       accent:'#06b6d4', tags:'(["amenity"="university"];["amenity"="college"];)' },
    { key:'fire_station', icon:'🚒', label:'Fire Stations',  accent:'#f43f5e', tags:'["amenity"="fire_station"]' },
    { key:'police',       icon:'🚔', label:'Police',         accent:'#6366f1', tags:'["amenity"="police"]' },
    { key:'pharmacy',     icon:'💊', label:'Pharmacies',     accent:'#14b8a6', tags:'["amenity"="pharmacy"]' }
  ];

  const catMarkers  = {};
  const catEnabled  = {};
  const catFeatures = {};
  ASSET_CATS.forEach(c => { catMarkers[c.key]=[]; catEnabled[c.key]=false; });

  function renderAssetPills(){
    const grid = document.getElementById('assetGrid');
    grid.innerHTML = ASSET_CATS.map(c => `
      <div class="asset-pill" data-cat="${c.key}" style="--pill-accent:${c.accent}">
        <span class="pill-icon">${c.icon}</span>
        <span class="pill-label">${c.label}</span>
        <span class="pill-count" id="cnt-${c.key}">0</span>
      </div>
    `).join('');

    grid.querySelectorAll('.asset-pill').forEach(pill => {
      pill.addEventListener('click', () => {
        const key = pill.dataset.cat;
        catEnabled[key] = !catEnabled[key];
        pill.classList.toggle('on', catEnabled[key]);
        catEnabled[key] ? showMarkers(key) : hideMarkers(key);
      });
    });
  }

  function showMarkers(key){
    if(catFeatures[key] && catFeatures[key].length > 0){ 
      addMarkers(key, catFeatures[key]); 
      return; 
    }
    fetchCategory(key).then(f => { 
      catFeatures[key]=f; 
      if(f.length > 0) addMarkers(key,f); 
    });
  }
  
  function hideMarkers(key){
    catMarkers[key].forEach(m => m.remove());
    catMarkers[key] = [];
  }

  function addMarkers(key, features){
    hideMarkers(key);
    const cat = ASSET_CATS.find(c => c.key===key);
    features.forEach(f => {
      const p = f.properties;
      const name = p.name || p['name:en'] || p['name:hi'] || p.operator || p.brand || 'Unnamed';
      const addrParts = [
        p['addr:housename'],
        p['addr:housenumber'],
        p['addr:street'] || p['addr:place'],
        p['addr:city']   || p['addr:district'],
        p['addr:state']
      ].filter(Boolean);
      const addrLine = addrParts.join(', ');

      const el = document.createElement('div');
      el.className = 'osm-marker';
      el.style.background = cat.accent;
      el.innerHTML = cat.icon;

      const marker = new maplibregl.Marker({ element: el })
        .setLngLat(f.geometry.coordinates)
        .addTo(map);

      el.addEventListener('click', e => {
        e.stopPropagation();
        new maplibregl.Popup({ className:'osm-popup', closeButton:true, closeOnClick:true, maxWidth:'220px' })
          .setLngLat(f.geometry.coordinates)
          .setHTML(
            `<div class="popup-name">${name}</div>` +
            `<div class="popup-type">${cat.label}</div>` +
            (addrLine ? `<div class="popup-addr">${addrLine}</div>` : '')
          )
          .addTo(map);
      });
      catMarkers[key].push(marker);
    });
    const badge = document.getElementById('cnt-'+key);
    if(badge) badge.textContent = features.length;
  }

  const sleep = ms => new Promise(r => setTimeout(r, ms));

  async function fetchCategory(key){
    const cat = ASSET_CATS.find(c => c.key===key);
    if(!cat) return [];

    const bbox = '28.20,76.70,28.60,77.30';

    let ql;
    const t = cat.tags;
    if(t.startsWith('(')){
      const inner = t.slice(1, t.lastIndexOf(')'));
      const stmts = inner.split(';').filter(Boolean);
      ql = '[out:json];(' + stmts.map(s => `node${s}(${bbox});way${s}(${bbox});`).join('') + ');out center;';
    } else {
      ql = `[out:json];(node${t}(${bbox});way${t}(${bbox}););out center;`;
    }

    const url = 'https://overpass-api.de/api/interpreter?data=' + encodeURIComponent(ql);

    for(let attempt = 1; attempt <= 3; attempt++){
      try {
        const res = await fetch(url);

        if(res.status === 429){
          console.warn(`Overpass 429 for "${key}" – attempt ${attempt}/3, waiting…`);
          await sleep(attempt * 2000);
          continue;
        }
        if(!res.ok){
          console.warn(`Overpass HTTP ${res.status} for "${key}"`);
          return [];
        }

        const json = await res.json();
        const elements = (json.elements || [])
          .filter(el => (el.lat!=null && el.lon!=null) || el.center)
          .map(el => ({
            type:'Feature',
            geometry:{ type:'Point', coordinates:[ el.lon??el.center.lon, el.lat??el.center.lat ] },
            properties: el.tags || {}
          }));
        
        console.log(`Fetched ${elements.length} items for ${key}`);
        return elements;

      } catch(e){
        console.warn(`Overpass fetch error for "${key}" attempt ${attempt}:`, e);
        if(attempt < 3) await sleep(1500);
      }
    }
    return [];
  }

  async function loadAllAssets(){
    renderAssetPills();

    for(let i = 0; i < ASSET_CATS.length; i++){
      const c        = ASSET_CATS[i];
      const features = await fetchCategory(c.key);
      catFeatures[c.key] = features;

      const badge = document.getElementById('cnt-'+c.key);
      if(badge) badge.textContent = features.length;

      if(i < ASSET_CATS.length - 1) await sleep(1000);
    }

    const ab = document.getElementById('assetBadge');
    ab.textContent = 'Ready';
    ab.style.background = '#B1DEE2';
    ab.style.color = '#264351';
  }

})();
</script>
</body>
</html>"""


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

