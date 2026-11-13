# Bieszczady LiDAR Finder: Conversation Handoff

Exported from a claude.ai session (3 Nov 2026) to continue in Claude Code.

## Goal

Find traces of abandoned villages in the Bieszczady Mountains (south-eastern Poland) using LiDAR terrain data, which shows the ground under trees and foliage. The user wanted a demo app that drops a pin (random or chosen) in the Bieszczady and shows LiDAR imagery for it.

## What was built

A single-file Leaflet web app, `bieszczady-lidar.html` (full source in the section below). It has:

- A button that drops a random pin inside a Bieszczady bounding box (lat 49.10–49.42, lon 22.20–22.75), plus click-to-pin.
- GUGiK (Polish Surveyor General) 1 m terrain-model shaded relief (NMT, bare earth) via WMS, loading from zoom 12.
- A GUGiK aerial-photo or OpenStreetMap background.
- An opacity slider for the LiDAR layer, to compare the forest canopy with the ground.
- A tile-projection switch (EPSG:3857 / EPSG:4326).
- A preset list of 8 former villages, a "what to look for" checklist, and a copy-coordinates button.

It is a local file, not a hosted page, because hosted artifacts block map tiles from outside servers.

## Known issues and untested parts (read first)

- **Never tested live.** The sandbox could not reach geoportal.gov.pl, so no tile request was verified.
- **Aerial photo URL is unverified.** `ORTO_URL` (`.../PZGIK/ORTO/WMS/StandardResolution`) was written from memory. An older endpoint seen in search results is `https://mapy.geoportal.gov.pl/wss/service/img/guest/ORTO/MapServer/WMSServer` (layer `Raster`, WMS 1.1.1). Check GetCapabilities for both.
- **LiDAR URL and layer name.** The documented example is `https://mapy.geoportal.gov.pl/wss/service/PZGIK/NMT/GRID1/WMS/ShadedRelief` with `LAYERS=Raster`, `VERSION=1.3.0`, `CRS=EPSG:2180`. Whether it accepts EPSG:3857 or 4326 was not verified. If not, use a proj4leaflet EPSG:2180 CRS or a proxy.
- **Village coordinates are approximate.** They came from memory, not a source. Caryńskie, Łopienka and Jaworzec are the least certain. Verify against PRNG or Polish Wikipedia.
- **Standard hillshade is limited.** The research below found custom-processed terrain models show much more than the default online hillshade.

## Conversation

### 1. Request

> I want to use LiDAR imaging to look for abandoned village ruins in south-eastern Poland. Can you make a demo application that puts a pin somewhere in rural south-eastern Poland, in the Bieszczady Mountains, and finds LiDAR imaging for it so I can see what's underneath the trees and foliage?

Claude checked current GUGiK services and built the app. Source material: the GUGiK NMT page (WMS/WMTS/WCS services, shaded-relief example URL).

### 2. Where the village names came from

> Where did you get the names of the abandoned villages?

From Claude's general knowledge, not a lookup. They are well-known former Boyko villages mostly emptied in 1944–1947 (deportations to the USSR, Operation Vistula). Coordinates are estimates. Further candidates not yet added: Zawój, Smolnik, Beniowa, Bukowiec, Tarnawa Wyżna.

### 3. Has anyone done this before?

> Do you know if anybody has done something like this, using LiDAR to look for abandoned villages in the Bieszczady?

Yes. Search results and fetched pages showed:

- **IGiPZ PAN (Polish Academy of Sciences):** Andrzej Affek led a 2013–2016 project (NCN PRELUDIUM grant 2012/05/N/ST10/03520) using airborne LiDAR to find cultural heritage under tree canopy in the upper Wiar River catchment (Przemyśl Foothills), checked by GPS fieldwork and archival maps.
- **Wolski, Latocha, Affek, Zachwatowicz, Wieczorek (IALE 2019 poster):** studied **Caryńskie** (Bieszczady), Borysławka (Przemyśl Foothills) and Rogóżka (Śnieżnik Massif). They built 0.5 m terrain models and sky-view-factor visualisations from national ISOK point clouds and compared them with 19th-century Austrian and Prussian cadastral maps.
  - Roads, terraces, ploughing traces, field boundaries and settlement remains are still detectable under forest.
  - Custom processing showed more than default online products (e.g. ploughing traces only at 0.5 m; TIN interpolation beat IDW).
  - Limits: dense vegetation, classification errors, and false features (e.g. branch piles read as mounds). Field verification is essential.
- **Anna Majewska (Univ. of Łódź, 2022):** same approach for Bartki, an abandoned village in former East Prussia, using ISOK data (about 4 points/m², 2018) and TPI, TRI, hillshade and positive-openness visualisations.

Recommendation: for serious work, download the raw point cloud from Geoportal and make sky-view-factor or local-relief models in QGIS with the Relief Visualization Toolbox (RVT).

### Sources

- [GUGiK: Numeryczny model terenu](https://www.geoportal.gov.pl/pl/dane/numeryczny-model-terenu)
- [IGiPZ PAN: Hidden cultural heritage in the abandoned landscape](https://www.igipz.pan.pl/project_en/events/3_1552.html)
- [IGiPZ PAN: IALE 2019 poster](https://www.igipz.pan.pl/tl_files/igipz/ZSIGiK/news/IALE_2019/poster.pdf)
- [Geographia Polonica 2016, vol. 89, iss. 3](https://geographiapolonica.pl/article/item/10610.html)
- [Majewska 2022, Prace Geograficzne: Bartki village](https://ejournals.eu/en/journal_article_files/full_text/018ecee1-4dc2-7100-8c03-82d585cc395f/download)

## Suggested next steps in Claude Code

1. Run the app locally (`python3 -m http.server`) and confirm the LiDAR and aerial tiles load; fix endpoints and CRS as needed.
2. Replace the approximate village list with verified coordinates (PRNG or Wikipedia) and add more villages.
3. Optionally add a WMTS or WCS source, or a local pipeline: download NMT or the point cloud, then generate sky-view-factor and local-relief tiles with RVT.

## App source: `bieszczady-lidar.html`

```html
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Bieszczady LiDAR Finder</title>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@400;600&display=swap">
<style>
  /* Layout: full-screen map with a side panel (bottom sheet on phones) */
  :root{
    --bg:#1b1f1c; --panel:#232925; --fg:#e6e9e4; --muted:#9aa49c;
    --accent:#d9a441; --line:#38403a;
    --sans:"IBM Plex Sans",system-ui,sans-serif; --mono:"IBM Plex Mono",ui-monospace,monospace;
    color-scheme:dark;
  }
  html,body{height:100%;margin:0;background:var(--bg);color:var(--fg);font:14px/1.45 var(--sans)}
  .app{display:grid;grid-template-columns:320px 1fr;height:100%}
  aside{background:var(--panel);border-right:1px solid var(--line);overflow-y:auto;padding:16px;display:flex;flex-direction:column;gap:16px}
  #map{height:100%;background:#111}
  h1{font-size:18px;margin:0}
  h2{font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);margin:0 0 8px}
  p{margin:0;color:var(--muted)}
  section{display:flex;flex-direction:column;gap:8px}
  button,select{font:inherit;background:var(--bg);color:var(--fg);border:1px solid var(--line);border-radius:6px;padding:8px 10px;cursor:pointer}
  button:hover,select:hover{border-color:var(--accent)}
  button:focus-visible,select:focus-visible,input:focus-visible{outline:2px solid var(--accent);outline-offset:1px}
  .primary{background:var(--accent);color:#1b1f1c;border-color:var(--accent);font-weight:600}
  .row{display:flex;gap:8px;flex-wrap:wrap}
  .row>*{flex:1}
  label{display:flex;justify-content:space-between;font-size:13px}
  input[type=range]{width:100%;accent-color:var(--accent)}
  .coords{font:13px var(--mono);background:var(--bg);border:1px solid var(--line);border-radius:6px;padding:8px;user-select:all;font-variant-numeric:tabular-nums}
  ul{margin:0;padding-left:18px;color:var(--muted)}
  .sites{display:flex;flex-direction:column;gap:4px}
  .sites button{text-align:left;display:flex;justify-content:space-between;gap:8px}
  .sites small{color:var(--muted);font-family:var(--mono)}
  #status{font-size:12px;color:var(--accent);min-height:1em}
  .src{font-size:12px}
  .src a{color:var(--accent)}
  @media (max-width:700px){
    .app{grid-template-columns:1fr;grid-template-rows:55% 45%}
    aside{order:2;border-right:0;border-top:1px solid var(--line)}
  }
</style>
</head>
<body>
<div class="app">
  <aside>
    <div>
      <h1>Bieszczady LiDAR Finder</h1>
      <p>Bare-earth LiDAR relief (trees removed) from Poland's GUGiK. Look for traces of abandoned villages under the forest.</p>
    </div>

    <section>
      <h2>Pin</h2>
      <button class="primary" id="randomBtn">Drop random pin in Bieszczady</button>
      <p>Or click anywhere on the map.</p>
      <div class="coords" id="coords">—</div>
      <div class="row">
        <button id="copyBtn">Copy coordinates</button>
        <button id="zoomBtn">Zoom to pin</button>
      </div>
    </section>

    <section>
      <h2>Layers</h2>
      <label for="lidarOp"><span>LiDAR relief opacity</span><span id="opVal">100%</span></label>
      <input type="range" id="lidarOp" min="0" max="100" value="100">
      <p>Slide down to blend in the aerial photo and compare forest vs. ground.</p>
      <label for="base"><span>Background</span></label>
      <select id="base">
        <option value="orto">Aerial photo (GUGiK)</option>
        <option value="osm">OpenStreetMap</option>
      </select>
      <label for="crs"><span>Tile projection</span></label>
      <select id="crs">
        <option value="3857">Web Mercator (EPSG:3857)</option>
        <option value="4326">WGS84 (EPSG:4326)</option>
      </select>
      <div id="status"></div>
    </section>

    <section>
      <h2>Known abandoned villages</h2>
      <p>Approximate locations. Most were emptied in 1944–1947 (deportations, Operation Vistula).</p>
      <div class="sites" id="sites"></div>
    </section>

    <section>
      <h2>What to look for</h2>
      <ul>
        <li>Rectangular cellar pits and house platforms</li>
        <li>Field terraces and boundary banks on slopes</li>
        <li>Sunken roads (holloways) leading to nothing</li>
        <li>Church or cemetery outlines, often on a small rise</li>
        <li>Straight drainage ditches in flat valley floors</li>
      </ul>
      <p>Best seen at zoom 16–18. The relief layer only loads from about zoom 12.</p>
    </section>

    <p class="src">Data: <a href="https://www.geoportal.gov.pl" target="_blank" rel="noopener">GUGiK Geoportal</a> NMT 1 m (LiDAR), orthophoto; © OpenStreetMap contributors.</p>
  </aside>
  <div id="map"></div>
</div>

<script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js"></script>
<script>
const LIDAR_URL = "https://mapy.geoportal.gov.pl/wss/service/PZGIK/NMT/GRID1/WMS/ShadedRelief";
const ORTO_URL  = "https://mapy.geoportal.gov.pl/wss/service/PZGIK/ORTO/WMS/StandardResolution";

// Approximate positions of former villages (check visually on the relief)
const SITES = [
  ["Krywe",      49.339, 22.437],
  ["Tworylne",   49.347, 22.458],
  ["Hulskie",    49.330, 22.487],
  ["Caryńskie",  49.192, 22.555],
  ["Łopienka",   49.322, 22.360],
  ["Jaworzec",   49.303, 22.392],
  ["Dydiowa",    49.098, 22.722],
  ["Sianki",     49.032, 22.858]
];

// Random pins stay inside this box (Polish Bieszczady, roughly)
const BOX = {latMin:49.10, latMax:49.42, lonMin:22.20, lonMax:22.75};

const map = L.map("map", {zoomControl:true}).setView([49.25, 22.48], 11);

const osm = L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
  {maxZoom:19, attribution:"© OpenStreetMap"});

let orto, lidar, crsCode = "3857";
const status = document.getElementById("status");
let errCount = 0;

function makeWms(url, opts){
  const crs = crsCode === "4326" ? L.CRS.EPSG4326 : L.CRS.EPSG3857;
  const layer = L.tileLayer.wms(url, Object.assign({
    layers:"Raster", format:"image/png", version:"1.3.0",
    crs, tileSize:512, maxZoom:20, attribution:"GUGiK"
  }, opts));
  layer.on("tileerror", () => {
    errCount++;
    if (errCount > 3) status.textContent = "Some tiles failed. Try the other tile projection, or zoom in.";
  });
  layer.on("load", () => { if (errCount <= 3) status.textContent = ""; });
  return layer;
}

function buildLayers(){
  const op = document.getElementById("lidarOp").value / 100;
  const baseSel = document.getElementById("base").value;
  [orto, lidar].forEach(l => l && map.removeLayer(l));
  errCount = 0; status.textContent = "";
  orto  = makeWms(ORTO_URL, {format:"image/jpeg"});
  lidar = makeWms(LIDAR_URL, {minZoom:12, opacity:op, transparent:true});
  if (baseSel === "orto") { map.removeLayer(osm); orto.addTo(map); }
  else { osm.addTo(map); }
  lidar.addTo(map);
}
buildLayers();

document.getElementById("lidarOp").addEventListener("input", e => {
  document.getElementById("opVal").textContent = e.target.value + "%";
  lidar.setOpacity(e.target.value / 100);
});
document.getElementById("base").addEventListener("change", buildLayers);
document.getElementById("crs").addEventListener("change", e => { crsCode = e.target.value; buildLayers(); });

// Pin handling
let pin = null;
const coordsEl = document.getElementById("coords");
function setPin(lat, lon, label){
  if (pin) map.removeLayer(pin);
  pin = L.marker([lat, lon]).addTo(map);
  if (label) pin.bindPopup(label).openPopup();
  coordsEl.textContent = lat.toFixed(5) + ", " + lon.toFixed(5);
}
function flyTo(lat, lon){ map.setView([lat, lon], 16); }

map.on("click", e => setPin(e.latlng.lat, e.latlng.lng));

document.getElementById("randomBtn").addEventListener("click", () => {
  const lat = BOX.latMin + Math.random() * (BOX.latMax - BOX.latMin);
  const lon = BOX.lonMin + Math.random() * (BOX.lonMax - BOX.lonMin);
  setPin(lat, lon, "Random pin");
  flyTo(lat, lon);
});
document.getElementById("zoomBtn").addEventListener("click", () => {
  if (pin) { const p = pin.getLatLng(); flyTo(p.lat, p.lng); }
});
document.getElementById("copyBtn").addEventListener("click", async e => {
  const t = coordsEl.textContent;
  if (t === "—") return;
  try { await navigator.clipboard.writeText(t); e.target.textContent = "Copied"; }
  catch { const r = document.createRange(); r.selectNodeContents(coordsEl); getSelection().removeAllRanges(); getSelection().addRange(r); e.target.textContent = "Selected – press Ctrl+C"; }
  setTimeout(() => e.target.textContent = "Copy coordinates", 1500);
});

// Site list
const sitesEl = document.getElementById("sites");
SITES.forEach(([name, lat, lon]) => {
  const b = document.createElement("button");
  b.innerHTML = `<span>${name}</span><small>${lat.toFixed(3)}, ${lon.toFixed(3)}</small>`;
  b.addEventListener("click", () => { setPin(lat, lon, name + " (approx.)"); flyTo(lat, lon); });
  sitesEl.appendChild(b);
});
</script>
</body>
</html>
```
