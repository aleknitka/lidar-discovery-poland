# 10 - Presentation plan: how we show scans and candidates to people

Status: plan, not implemented. Scope: the internal review workspace (`/explore`), the later public catalogue (`/catalog` and the static public site of 05 §11), and the plug-in folder `frontend/src/presentation/`. Binding constraints: 07-decisions.md (desk-only; nothing is ever "field-confirmed"), 08-architecture-contract.md (API, disclosure, the word "candidate" rather than "discovery"), 05-synthesis.md §4.4 (A/T axes), §8.3-8.4 (sensitivities, tiers P0-P3) and §11 (dissemination).

Evidence tags as in 05: [V\*] checked by me in this pass, [D] my design proposal, [U] unverified.

---

## 1. Teardown of the Maya article's presentation

Source: Pietro Miotti, "My AI Agents (Re)discovered a Maya Site in 72 Hours", https://pietromiotti.com/latest/maya-site/ (fetched 2026-11-13). I downloaded all 11 images and the video poster and viewed them [V\*]. The 360° video (`M2_lidar_360.mp4`) was not played; its poster frame and caption were inspected.

### 1.1 Narrative structure

The post is a dated diary (18, 19, 20, 21 October), then "So what was it?", "What's next", "What I've learned". The visual arc is:

1. **Hook: the reveal.** It opens with a before/after swipe: satellite (unbroken forest) vs bare-earth LiDAR (plaza, pyramid). The payoff comes before any explanation.
2. **Origin story:** two 1912 Bingham photographs (Machu Picchu "discovered" under vegetation). They frame the post as exploration.
3. **Breadth:** a grid of eight flagged sites ("keep an eye on the bottom-left one"). It shows that a search took place and sets up a mystery.
4. **Detail:** a locator map with a zoom box and labelled features.
5. **Immersion:** a 3D 360° turntable.
6. **Evidence:** point-cloud cross-sections (ground vs vegetation returns).
7. **Authority:** the redacted letter to INAH and INAH's highlighted reply.
8. **Imagination:** an AI-generated reconstruction "around AD 700".
9. **Correction:** an "Update (11 November)" notice placed **at the top**, saying that the site was already published (Estrada-Belli et al. 2025).

The sequence runs overview → zoom → 3D → raw evidence → institutional confirmation → story. Each step answers the doubt the previous one raised ("is it real?" → "here are the raw points"). The order follows the reader's scepticism, not the order of the work.

### 1.2 Figure by figure

**F1. Hero swipe: "Lidar: bare ground, 2013" vs "Satellite image today"** (`hero-lidar.jpg`, `hero-satellite.jpg`, both 1200×1090, identical extent)
- *What:* the same hilltop as a colour-by-height bare-earth rendering and as Esri/Maxar imagery that shows only canopy.
- *Construction:* a CSS clip slider (`--pos` custom property). On load it plays **one automatic sweep** (50→85→15→50 % over ~3 s with ease-in-out), stops as soon as the reader touches it, and **respects `prefers-reduced-motion`**. Each side carries a label with its date. The LiDAR side is a hillshade multiplied by a **diverging teal-white-orange/brown ramp** (teal low, rust high), apparently stretched to the local height range. NoData is masked to near-black (#0d1117-ish), so the strip outline is visible. It has a 100 m scale bar in a rounded dark box and an attribution ("NASA G-LiHT lidar, 2013"). There is **no north arrow and no colour legend**.
- *Why it persuades:* the slider makes the reader perform the reveal. The forest "comes off" under their own hand. The dates make an honest point: the ground is from 2013 and the canopy is from today.
- *Issues:* a diverging ramp suggests a meaningful midpoint, but height has none. Without a legend, the reader cannot tell whether the orange is 3 m or 30 m. The local stretch amplifies small relief.

**F2. Bingham 1912 photo pair** (public domain, Wikimedia Commons, credited with links)
- *Construction:* two images in flex proportion, so heights match.
- *Persuasion:* it sets up a romantic discovery narrative. The scare quotes on "discovered" are a nod to the indigenous guide. *Lesson for us:* do not use explorer framing. Our villages were never lost to the people who lived there.

**F3. Grid of eight flagged sites** (`maya-sites.jpg`, 4×2)
- *Construction:* neutral warm-grey **multi-direction hillshade**, the same style in every panel, a dark background, a scale bar per panel, a north arrow badge per panel and a tiny attribution per panel. **Scales differ** (100 m and 200 m panels sit side by side). One panel (bottom right) shows an obvious **interpolation artefact**: a faceted TIN cone over a data void. It is not called out.
- *Persuasion:* abundance ("lots of villages") and a consistent house style make the eight panels read as one dataset. The teaser line creates a hook.
- *Issues:* no false positives are shown, and there is no count of how many flags were rejected. The artefact panel undercuts the claim that the agents filtered noise.

**F4. Locator + zoom with interpretation labels** (`lidar-zoom.jpg`, 1600×2124)
- *Construction:* top: greyscale hillshade of the whole strip, white-boxed labels with thin black leader lines (Cliff, Platform 1-3, **Modern tracks**), and a red rectangle "Civic centre". **Red trapezoid connector lines** link it to the bottom panel. Bottom: zoom with **thin orange contour lines** overlaid on the hillshade, labels (Plaza, Pyramid (8 m+), Raised courtyard, **Reservoir?**) and **dashed red section lines A-A′ and B-B′** that set up F6. North arrows and scale bars (100 m, 50 m) on both panels.
- *Persuasion:* this is the classic cartographic locator-inset. Labels turn shapes into named places. Labelling "Modern tracks" shows that the author separated modern from ancient.
- *Honesty points:* the only explicit uncertainty marker is "?" on Reservoir. "Pyramid (8 m+)" in the figure sits beside "8-12 m" in the text. All other labels read as fact (no confidence levels).

**F5. 3D turntable video** (`M2_lidar_360.mp4`, poster 1080²)
- *Construction:* the DTM as a matte warm-grey solid with an extruded skirt (a "museum block" look) on a near-black background. It rotates 360°. The overlay states "**heights exaggerated ×1.5**". It autoplays when ≥60 % in view (IntersectionObserver), pauses out of view, and is muted and looped. It has an `aria-label`.
- *Persuasion:* physical, object-like and tangible. It is cheap to watch. Stating the exaggeration is good practice.
- *Issue:* a pre-rendered video cannot be interrogated (no scale, no rotation by the user).

**F6. Point-cloud cross-sections** (`point-cloud-profiles.jpg`, two stacked panels)
- *Construction:* A-A′ (west→east) and B-B′ (south→north), matching F4's dashed lines. **Vegetation returns: small, translucent green dots. Ground returns: larger brown dots. Terrain model: black dashed line.** X axis: "metres from a point on the site" (a relative origin, so no coordinates leak). The **vertical axis has no numbers**, only a 10 m scale bar. Red callouts: "**Gap at the top (no ground returns)**", "**Mound tops (no ground returns)**".
- *Vertical exaggeration (my measurement):* in A-A′, 10 m ≈ 95 px vertical vs 50 m ≈ 300 px horizontal, so VE ≈ 1.6×. In B-B′, VE ≈ 1.65×. **The VE is not stated** in the figure, unlike F5.
- *Persuasion:* this is the most scientific figure. It shows the ground surface is supported by actual returns under 10-17 m of canopy. It also **admits where the model interpolates** (the callouts). Using a relative origin is a quiet disclosure control.
- *Lesson:* this is the figure to emulate. Point-level evidence, plus an explicit "here the surface is guessed".

**F7. Redacted letter to INAH and F8. INAH reply** (`report-letter.jpg`, `inah-reply.jpg`)
- *Construction:* page crops with black redaction bars over the municipality and names. The reply has **yellow highlight** on the key sentence. The caption says that "exact coordinates went in a confidential annex".
- *Persuasion:* borrowed institutional authority, plus visible responsible-disclosure behaviour.
- *Issue:* the highlighted sentence ("no registered site at the location") was read as "nobody knew". The update shows that was wrong. A register's silence was presented visually as confirmation of novelty (05 §2.2 lesson 1).

**F9. AI reconstruction "around AD 700"** (`reconstruction.jpg`, Gemini)
- *Construction:* a photoreal aerial view at golden hour: a painted pyramid with a thatched temple, people, smoke, and a pond in the "Reservoir?" hollow. The caption discloses the generator.
- *Persuasion:* very strong. It is the most memorable image.
- *Why it misleads:* it upgrades every hedge in F4 into fact ("Reservoir?" becomes water, "probably houses" become thatched huts) and adds colours, roofs and people for which there is no evidence. Photorealism carries no visual marker of uncertainty. **For us this is a hard "no"** (see §3).

### 1.3 What the article does well, what it omits, and lessons

| Device | Keep / adapt / reject | Our version |
|---|---|---|
| User-driven reveal swipe with one gentle auto-sweep, reduced-motion aware | **Keep** | Canopy DSM ↔ bare-earth swipe (M1) and then-vs-now swipe (M5) |
| Dates on both sides of every comparison | **Keep** | Every layer label carries source + epoch ("GUGiK ALS 2023", "Luftwaffe ortho 1944") |
| Uniform small-multiples grid | **Adapt** | Same scale in all panels by default. Include rejected look-alikes (FP classes, 05 §7) |
| Locator + zoom + labelled interpretation | **Keep** | M6 overlay, with confidence encoded in every label, not only one "?" |
| Section lines on the map that match the profiles | **Keep** | M3: the profile line drawn on the map is the profile tool's input |
| Ground vs vegetation profile with "no ground returns" callouts | **Keep, automate** | M3 marks interpolated spans automatically from ground-point gaps |
| VE stated on 3D | **Keep, extend** | State VE on **every** profile and 3D view; default 1× for public |
| Relative distance origin (no coordinates) | **Keep** | All public profiles and story figures |
| Colour-by-height without legend; diverging ramp | **Reject** | Sequential perceptual ramp + legend in metres (§4) |
| Mixed scales in a grid; unflagged artefact panel | **Reject** | Fixed scale or a scale badge; artefact masks shown |
| Register silence shown as confirmation | **Reject** | Evidence panel lists every check, positive and negative (M8) |
| Photoreal AI reconstruction | **Reject** | At most a schematic, sourced diagram from the cadastre or a 1944 photo (§3.4) |
| Correction at the top of the page | **Keep** | Versioned story pages with a visible change log (M7) |
| Explorer/"discovered" framing | **Reject** | Memory and documentation framing (§3.5) |

Missing from the article, and needed by us: precision/recall or any count of rejected flags; a false-positive gallery; uncertainty on measurements; acquisition season and ground density (the reason a surface is trustworthy); provenance per figure; any voice of descendant communities.

---

## 2. Other reference points (links checked 2026-11-13)

1. **Relief Visualization Toolbox (RVT) and the VAT composite.** Kokalj & Somrak 2019, "Why Not a Single Image? Combining Visualizations to Facilitate Fieldwork and On-Screen Mapping", *Remote Sensing* 11(7):747, doi:10.3390/rs11070747 [V\* via Crossref]. Code: https://github.com/EarthObservation/RVT_py, docs https://rvt-py.readthedocs.io/en/latest/ [V\* 200]. VAT blends hillshade, slope, positive openness and SVF with fixed blend modes and opacities. It is the de facto standard composite for archaeological ALS. Our backend already re-implements the components in numpy (08 §Stack).
2. **Guidance documents.** Historic England, *Using Airborne Lidar in Archaeological Survey: The Light Fantastic* (Crutchley & Crow, 2018), https://historicengland.org.uk/images-books/publications/light-fantastic (in the search index; the site returns 403 to scripted requests) [V via search]. EAC Guidelines 10, *Guidelines for the use of Airborne Laser Scanning (Lidar) in Archaeology* (Bennett & Cowley eds., 2025), doi:10.5281/zenodo.14609210 [V\* via Zenodo API]. Bennett et al. 2012, "A Comparison of Visualization Techniques for Models Created from Airborne Laser Scanned Data", *Archaeological Prospection*, doi:10.1002/arp.1414 [V\* via Crossref]. These sources argue that no single visualisation is sufficient and that each one should be documented with its parameters.
3. **PACUNAM Maya lidar.** Canuto et al. 2018, "Ancient lowland Maya complexity as revealed by airborne laser scanning of northern Guatemala", *Science*, doi:10.1126/science.aau0137 [V\* Crossref]. Popular presentation: https://www.nationalgeographic.com/history/article/maya-laser-lidar-guatemala-pacunam [V\* 200], with canopy-to-bare-earth reveals and annotated 3D. https://www.pacunam.org/ [V\* 200]. The reveal device is the same as F1, at scale.
4. **NLS "Side by Side" historic map viewer** (National Library of Scotland): split screen or swipe between georeferenced historic maps and modern layers, including a LiDAR DTM background, with a transparency slider and linked/unlinked panning. Help page https://maps.nls.uk/geo/explore/side-by-side-old (the site returns 405 to scripted requests; confirmed via search results) [V via search]. This is the model for M5 (then vs now).
5. **Web 3D and point-cloud stacks.** Potree, https://potree.github.io/ [V\* 200] (octree streaming, built-in profile tool, EDL shading). deck.gl `PointCloudLayer` https://deck.gl/docs/api-reference/layers/point-cloud-layer [V\* 200] and loaders.gl `LASLoader` (reads LAS/LAZ in the browser) https://loaders.gl/docs/modules/las/api-reference/las-loader [V\* 200]. COPC (cloud-optimised point cloud) https://copc.io/ [V\* 200]. MapLibre `raster-dem` terrain + hillshade https://maplibre.org/maplibre-gl-js/docs/examples/3d-terrain/ [V\* 200]. `maplibre-gl-compare` swipe https://github.com/maplibre/maplibre-gl-compare [V\* 200]. Scrollytelling with Scrollama https://github.com/russellgoldenberg/scrollama [V\* 200]. Colour maps: Crameri "Scientific colour maps" https://www.fabiocrameri.ch/colourmaps/ [V\* 200]. Iconem terrain viewer split modes (a terrain-specific swipe/split UI) https://terrain-viewer.iconem.com/docs/features/split-modes/ [V\* 200].

---

## 3. Catalogue of presentation modes

Each mode is a plug-in under `frontend/src/presentation/<mode>/` exposing `{id, label, audience: 'review'|'public'|'both', minDisclosure, mount(mapCtx), unmount()}` [D]. Every mode reads the disclosure level of whatever it shows and refuses to render restricted content when `public_mode` is on (the client check duplicates the server check; the server is authoritative).

Cost scale: **S** ≤2 dev-days, **M** 3-7, **L** 8-15, **XL** >15 (one developer, includes tests).

### M1. Colour-by-height with forest-removed reveal (canopy curtain)
- **Purpose:** public story (the hook, like F1) and review (does the feature sit under dense canopy, so that its ground density is suspect?).
- **Data:** `dtm` (bare earth, class 2) and a new `dsm` product (highest return per 0.5 m cell, classes 1-5, excluding 7/12). Optional `chm` = DSM − DTM. The 1944 ortho or current ortho as an alternative "before" side.
- **Technique:** two MapLibre raster sources in two synced maps with `maplibre-gl-compare`, or a single map with a CSS clip (as F1). DTM rendered as a **sequential perceptual ramp** (Crameri `batlow` or `oleron` land half) × multi-hillshade (multiply blend done server-side to avoid client blending limits). DSM rendered with the same ramp and the **same height stretch**, so the curtain compares like with like. One auto-sweep on first view, disabled by `prefers-reduced-motion` and after first touch. Legend in metres a.s.l. (EVRF2007) with the stretch range printed.
- **Endpoints:** extend tiles: `GET /api/layers/{id}/tiles/{z}/{x}/{y}.png?ramp=batlow&rescale=min,max|auto&shade=multidir&vexag=1`. The response header `X-Rescale: 612.4,688.9` lets the legend show the real range. New product kinds `dsm`, `chm` in `ldp process`.
- **Cost:** S (frontend; the swipe already exists) + S (backend ramp params) + S (DSM/CHM products).

### M2. Multi-visualisation composites and small multiples
- **Purpose:** review first (05 §4.4 A1 requires ≥2 visualisations), public second (one VAT image per village story).
- **Data:** `hillshade` (multi-dir), `slope`, `svf`, `lrm`, new `openness_pos`, `openness_neg`, `vat` (composite), `ground_density`.
- **Technique:** (a) a **VAT composite** rendered server-side as a single COG (RVT parameters recorded in provenance; Kokalj & Somrak 2019 defaults for "general" and "flat" terrain); (b) a **linked small-multiples panel** for a candidate: 2×3 chips of SVF / LRM / openness− / hillshade / VAT / ground density, all **at the same scale and extent**, each with a parameter caption ("SVF r=10 m, 16 dir"). Chips are `<img>` tiles from a static-map endpoint, not six live maps (performance). Keyboard 1-6 enlarges a chip.
- **Endpoints:** `GET /api/candidates/{id}/chips?kinds=svf,lrm,...&size=512&pad_m=40` returns PNGs or a JSON of URLs. `GET /api/layers/{id}/static.png?bbox=...&w=&h=` (rio-tiler `part()`). Product kinds `vat`, `openness_pos`, `openness_neg`.
- **Cost:** M (backend VAT + chips), S (frontend panel).

### M3. 2D cross-section profile with ground vs vegetation returns
- **Purpose:** review (the strongest evidence that a feature is in the ground surface and not an artefact of interpolation; F6) and public (one curated profile per story, relative origin).
- **Data:** classified LAZ points in a corridor (default 2 m wide) around a user-drawn line; the DTM sampled along it; per-epoch (2012/2023/2025) for a two-epoch overlay.
- **Technique:** draw a line in MapLibre (reuse the candidate drawing tool). The line is drawn on the map with A/A′ end labels, as in F4. **D3** scatter in an SVG or canvas panel: vegetation (classes 3-5) small translucent green, ground (2) larger brown, unclassified grey, noise hidden; DTM as a dashed line; **spans where ground points are absent for > N m are shaded automatically and labelled "interpolated: no ground returns"**. Axes in metres with **VE stated and adjustable (1×, 2×, 5×)**. Default 1×, and exaggerated profiles carry a badge. Hover-linked: moving along the profile moves a marker on the map. Optional second epoch as a second dashed line, with Δz.
- **Endpoints:** `POST /api/profiles` body `{location_id, source_id, epoch, line: GeoJSON LineString, width_m, classes?, max_points}` → `{distance_m[], z[], cls[], ret[], dtm: {distance_m[], z[]}, gaps: [[d0,d1]], ve_hint, provenance}`. Points are thinned server-side (stratified by class) to ≤50 k. For public mode the origin is relative and no coordinates are returned. Implementation: read the LAZ tiles intersecting the corridor with laspy, filtered by a shapely buffer. Cache by a hash of the request.
- **Cost:** M (backend: tile lookup, corridor clip, thinning; it needs raw LAZ retained or a per-tile ground+veg extract), M (frontend D3 panel + map link).

### M4. 3D point-cloud view (and 3D terrain)
- **Purpose:** review (rotate around an ambiguous mound; separate trees, branch piles (05 §7) and real platforms) and public (an F5-like turntable, but interactive).
- **Data:** a point subset around a candidate (e.g. 150×150 m), classes 2-6, intensity, return number; and/or DTM as terrain-RGB for a lightweight surface view.
- **Technique, two tiers:**
  - *M4a terrain 3D (cheap):* MapLibre `raster-dem` source + `terrain` + `hillshade` layer with our DTM encoded as **terrain-RGB**, pitch up to 60°, `exaggeration` shown in the UI ("heights ×1.0"). Drape SVF/VAT/1944 photo on top. Built into MapLibre, so no new library.
  - *M4b point cloud:* **deck.gl `PointCloudLayer`** in a `MapboxOverlay` over MapLibre, data parsed with **loaders.gl `LASLoader`** from a LAZ subset. Colour by class / height / intensity; toggle "hide vegetation". Eye-dome lighting is not built in. If needed later, move to **Potree** (octree, EDL, built-in profile) as a separate route. Potree needs octree conversion (PotreeConverter, a native binary, which conflicts with the PyPI-only rule of 08). COPC would need PDAL/untwine (the same conflict). So v1 serves **bounded LAZ subsets** written by laspy+lazrs, which needs no octree.
- **Endpoints:** `GET /api/layers/{dtm_id}/terrain/{z}/{x}/{y}.png?encoding=terrarium|mapbox` (rio-tiler render of the DTM to RGB-encoded elevation; buffer the tiles to avoid seams). `GET /api/pointcloud?location_id=&bbox=&epoch=&classes=2,3,4,5&max_points=2e6&format=laz` → `application/vnd.laszip` (LAZ 1.4, offsets relative to the bbox centre for public mode). The size cap is enforced. Restricted polygons are clipped out server-side.
- **Cost:** M4a S-M; M4b M (deck.gl integration, LAZ endpoint), L if Potree.

### M5. Then vs now: 1944 photo / 1852 cadastre / WIG vs LiDAR
- **Purpose:** both. Review: dating evidence (A2 context, D1 validation). Public: the emotional core ("here stood the houses").
- **Data:** georeferenced historical rasters as COG products of kind `historical`: `ortho_1944` (the Luftwaffe orthophoto of southern Podkarpackie on geoportal-krajowy.pl; 06 #19, licence [U]), `cadastre_1852` (AP Przemyśl scans, licence [U], 05 §8.2 q6), `wig_1930s`. Each has georeferencing RMSE and control points in provenance.
- **Technique:** NLS-style **swipe** (reuse the existing compare) plus an **opacity fade** and a "**spyglass**" (circular lens showing layer B under the cursor; one map, clip-path on a canvas copy, or a second map masked by a CSS radial clip). Vector overlay of **digitised cadastral house plots** (polygons, with sheet number) on the LiDAR. Georeferencing error is drawn as a translucent buffer (e.g. ±RMSE ring around each digitised house), because Affek 2016 found building remains "within the same parcel", not at the exact cadastral position. If a WMS source allows CORS, MapLibre can consume it directly as a raster source with a `{bbox-epsg-3857}` template; otherwise the backend proxies and caches.
- **Endpoints:** no new route if historical rasters are ingested as products (`/api/locations/{id}/layers` gains `kind=historical`, `licence`, `attribution`, `georef_rmse_m`). Optional `GET /api/wms-proxy/{source}/{z}/{x}/{y}.png`. New `GET /api/locations/{id}/historical-features` (digitised houses, roads, church; FeatureCollection with source sheet).
- **Cost:** S (frontend modes on the existing swipe), M (backend ingest of georeferenced scans), plus **manual georeferencing and digitising**, which is the real cost (about 0.5-1 day per village).

### M6. Annotated interpretation overlay with uncertainty
- **Purpose:** review (the reviewer's map) and public (curated, generalised labels).
- **Data:** candidates (geometry, `morph_class`, `reality` + `confidence`, A/T rating, `review_status`, `documentation_status`), historical features, known false-positive look-alikes.
- **Technique:** MapLibre GeoJSON layers. **Encoding:** class → icon/shape (not colour alone); certainty → **line style and fill opacity** (A0 dotted outline without fill, A1 dashed, A2 solid + light fill; A3 is not used, per D1); review status → small badge. Labels follow F4 (white box, leader line) but always carry the rating, e.g. "house platform? A1". Natural/artefact rejections can be shown greyed ("rejected: branch pile") on review maps. Collision-aware labels via MapLibre symbol layers. Toggle "show my interpretation / hide all interpretation" so the reader can look at the raw relief first and avoid anchoring (05 §10.4).
- **Endpoints:** existing `/api/candidates`. Add `GET /api/candidates?...&format=public` → generalised geometry (server applies disclosure) and `GET /api/locations/{id}/summary` → counts per class × A-level (P3 aggregates).
- **Cost:** S-M.

### M7. Village story page (scrollytelling, public catalogue)
- **Purpose:** public only. One page per village, co-written with or reviewed by descendant organisations (05 §8.3, §11).
- **Data:** the location record (names pl/uk/historical, depopulation events with sources), the P2/P3 subset, generalised relief tiles, 1944/cadastre layers where licensed, 1-3 curated profiles (relative origin), archival photos with rights, oral-history quotes with consent, a change log.
- **Technique:** a sticky full-height MapLibre map + text steps driven by **Scrollama** (IntersectionObserver). Each step sets `{camera, layers, swipe position, highlighted aggregate}`, declared in a per-village JSON/MDX story file. Suggested arc, adapted from §1.1 but reordered for honesty: (1) the place today (forest, ortho, names); (2) **the people and what happened, with sources** (per-village cause, never a blanket label); (3) 1852/1944 then-vs-now swipe; (4) forest-removed reveal; (5) what the relief shows (aggregate counts, generalised); (6) **how we know / what we don't know** (M8); (7) how to visit respectfully (park rules, cemeteries cared for by named stewards); (8) corrections, sources, change log. All steps also work as a plain linear article without JavaScript (accessibility, print, search).
- **Endpoints:** none new for the public static site (built from P2/P3 exports + PMTiles per 05 §11). In the app, `GET /api/locations/{id}/story` (story JSON) for preview inside `/catalog`.
- **Cost:** L for the framework and first village (Caryńskie); M per additional village, dominated by writing, translation and review.

### M8. "How we know / what we don't know" evidence panel
- **Purpose:** both. It is a side panel in `/explore` for each candidate and a block in each story.
- **Data:** A/T rating with the rule that produced it, `documentation_status` (every source checked, `found` true/false, query, date), visualisations that showed it, profile(s), epochs present, ground-point density at the feature, reviewer count and agreement, model/prompt versions if any (origin), known FP classes considered and why they were rejected.
- **Technique:** a structured card, not prose. Three columns: **Supports** (e.g. "visible in SVF and LRM", "on 1852 parcel 214", "present in 2012 and 2023"), **Against / unknown** (e.g. "ground density 0.4 pts/m² here", "no 1944 photo coverage"), **Not checked** (sources still pending). A coverage bar (05 §10.6 `coverage_score`). Plain-language strongest claim, using the D1 wording: "LiDAR feature consistent with N independent historical sources". Link to every figure used. Public version: the same card with coordinates removed and counts rather than points.
- **Endpoints:** `GET /api/candidates/{id}/evidence` (assembles rating, documentation_status, provenance of layers used, ground density sampled at the geometry). The density sampling is new: `GET /api/layers/{ground_density_id}/stats?geometry=`.
- **Cost:** M (mostly backend assembly), S frontend.

### M9 (supporting). Two-epoch change view
- 2012 vs 2023 difference raster (after empirical co-registration, 05 §3.4) with a **diverging** ramp (this is the one case where diverging is right: zero is meaningful). Swipe plus difference. Endpoint: product kind `dz` with provenance of co-registration. Cost M (backend co-registration). Use: monitoring stories (forestry tracks over platforms), not detection.

### M10 (supporting). False-positive gallery
- A reference small-multiples page of our FP classes (05 §7: suffosion funnels, branch piles, charcoal platforms, skid trails, etc.) in the same rendering as M2. It trains reviewers and gives public readers calibration (the counterpart to F3's missing rejects). Cost S once M2 chips exist.

### Endpoint summary (proposed additions to 08)

| Endpoint | Modes | Notes |
|---|---|---|
| `tiles/...png?ramp=&rescale=&shade=` | M1, M2 | colour ramps; `X-Rescale` header |
| `GET /api/layers/{id}/terrain/{z}/{x}/{y}.png` | M4a, M7 | terrarium or mapbox encoding |
| `GET /api/layers/{id}/static.png?bbox=&w=&h=` | M2, M7, M10 | figure export too |
| `GET /api/candidates/{id}/chips` | M2 | same-scale chips |
| `POST /api/profiles` | M3 | thinned classified points + DTM + gaps |
| `GET /api/pointcloud?...&format=laz` | M4b | capped; restricted polygons clipped |
| `GET /api/candidates/{id}/evidence` | M8 | assembled card |
| `GET /api/layers/{id}/stats?geometry=` | M8 | ground density at the feature |
| `GET /api/locations/{id}/summary` | M6, M7 | P3 aggregates |
| `GET /api/locations/{id}/historical-features` | M5 | digitised cadastre/1944 |
| `GET /api/locations/{id}/story` | M7 | preview only |
| product kinds `dsm, chm, vat, openness_pos/neg, historical, dz` | M1, M2, M5, M9 | `ldp process` additions |

All new endpoints honour `LDP_PUBLIC_MODE`: they return 404 for restricted items, generalise geometry, cap raster resolution (see §4.3), and use a relative origin for profiles and point clouds.

---

## 4. Honesty and ethics in presentation

### 4.1 Show uncertainty everywhere it exists
- Every candidate graphic carries its A/T rating and review status in text, not only as styling.
- Line style encodes certainty (§3 M6). Colour is reserved for class or data.
- Profiles mark interpolated spans. Maps can show a **ground-density mask** (hatched where < 1 ground pt per 0.5 m cell, the 05 §10.6 rule), so readers see where the DTM is guesswork.
- Numbers carry ranges: "platform ~12 × 8 m (±1 m), raised 0.2-0.4 m", never a bare "8 m+".
- Georeferencing error of historical maps is drawn (M5).
- Each figure has a provenance footer: source, epoch, product, parameters, code version (from `provenance`).

### 4.2 Avoid persuasive overclaiming
- No word "discovery" or "discovered" in UI or captions (08). Use "candidate", "feature", "mapped". Public claims follow 05 §4.4: nothing below A2/T1 is presented as a finding.
- **No photoreal reconstructions** (generative or hand-made). If illustration is needed: a schematic line drawing derived only from the cadastre/1944 photo, labelled "schematic, based on the 1852 cadastre sheet X". Every element must trace to a source.
- No auto-playing "reveal" without a static fallback. The swipe starts at 50 % and shows both labels. No dramatic VE by default: profiles and 3D default to 1×, and exaggeration needs a visible badge.
- Show rejects: the FP gallery (M10) and counts of rejected vs accepted candidates per village on the evidence panel.
- Register silence is never shown as novelty. M8 shows each source checked and what it returned.
- Corrections go to the top of the story page with a date, as in the Maya update, and the change log is permanent.

### 4.3 Generalising coordinates in public views (visual techniques)
Server-side rules are in 08 (generalised → 1 km cell centroid; restricted hidden). Visual counterparts:
- **Aggregate hex/square cells (≥1 km², P3):** cells with counts, labelled "12 features mapped in this cell". Cells with < k (e.g. 3) features are merged or suppressed, so a lone count does not reveal the position.
- **Village-level point and "zone" polygon:** a soft, blurred outline (the PRG precinct or a buffered convex hull), never feature points.
- **Relief tiles in public mode:** resolution cap (≥1 m effective, max zoom ~16) and **masks over sensitive polygons** (cemeteries, conflict features) rendered as a neutral flat fill with a note "relief withheld here (burial ground)". A blur is not used, because it invites reconstruction and looks like censorship of something exciting. Flat fill + reason is calmer.
- **Profiles and 3D:** relative origin ("metres from a point in the village"), no lat/lon readout. The north arrow may be kept, because orientation alone does not locate a feature.
- **No copyable coordinates** in public UI; the map's coordinate readout is disabled; `?ll=` URLs are rounded to the cell.
- **Screenshots and exports** inherit the same generalisation (they are rendered from the same public endpoints).

### 4.4 Graves and cemeteries
- Never shown as points, outlines, labels or relief in public views unless already public and protected (05 §8.4). Where a cemetery is publicly known and cared for (e.g. by Magurycz), link to the steward's page rather than mapping it ourselves.
- In `/explore`, restricted features carry a lock badge and are excluded from exports by default.
- Profiles and point-cloud subsets requested over a restricted polygon return 403 in public mode, and in internal mode show a warning banner.

### 4.5 Respectful wording about displaced communities
- **Name the event per village with sources**: "In April-May 1946 the inhabitants were forcibly resettled to the Ukrainian SSR [source]". Never "Operation Vistula villages" as a blanket label. Never "abandoned" for forced displacement (use "emptied", "depopulated", "whose inhabitants were deported/resettled").
- No assignment of blame per village. Where narratives differ, present both with sources (05 §8.3).
- Use the community's own names: the Ukrainian/Lemko/Boyko name of the village, and the church dedication.
- Use no "lost", "hidden" or "forgotten" framing for places that descendants remember; prefer "documented", "remembered", "mapped".
- Each story page has a correction channel and credits reviewers from descendant organisations.

### 4.6 Bilingual and trilingual labels (PL / UK / EN)
- UI strings in `i18n/{pl,uk,en}.json` from day one (react-i18next or a small context). The locale is chosen by URL prefix on public pages (`/pl/`, `/uk/`, `/en/`).
- Village names are shown in **Polish and Ukrainian (Cyrillic) together** regardless of UI language, plus the historical spelling (PRNG `NAZWYHISTORYCZNE`). Example: "Caryńskie / Царинське".
- Fonts must cover Latin Extended-A and Cyrillic (e.g. Noto Sans, Inter). Test label collision with Cyrillic lengths.
- Map labels use MapLibre `text-field` with `["coalesce", ["get","name_uk"], ...]`. Basemap labels in the user's language where the basemap supports it.
- Translations of sensitive text (cause of depopulation) are reviewed by native speakers from the relevant community, not machine-only.

---

## 5. Design system notes

### 5.1 Colour ramps
- **Elevation (sequential):** Crameri `batlow` (or `oleron` land half / `bamako`). Perceptually uniform, colourblind-friendly, readable in greyscale. Never `jet` or rainbow, and no diverging ramp for elevation (the F1 issue).
- **Local relief (LRM), dz (M9):** diverging `vik` or `roma`/`broc`, **centred on 0**, symmetric range, legend in metres.
- **Relief visualisations (hillshade, SVF, openness, VAT):** greyscale, as convention (RVT, Historic England). SVF: dark = enclosed. Document the stretch (e.g. SVF 0.65-1.0).
- **Ground density:** sequential single-hue (`lajolla` or Viridis-like) with a hatched overlay below threshold.
- **Point classes:** vegetation green (#4f9d4f at 40 % opacity, small), ground brown (#7a4a1e, larger), buildings/unclassified grey, noise hidden. These match F6, and the size difference keeps them separable for colour-vision deficiency.
- **Interpretation overlays:** a categorical palette of at most 7 classes (Okabe-Ito) with **shape and dash redundancy**. Rejected = neutral grey.
- Check each palette with a CVD simulator (deuteranopia, protanopia, tritanopia) as part of the plug-in PR checklist.

### 5.2 Vertical exaggeration
- Default **1×** for every public profile and 3D view. Review tools may offer 2× / 5× via a toggle.
- Always print VE on the figure ("vertical ×2"), including on profiles (the omission in F6).
- Profiles show a vertical scale bar *and* axis ticks in metres (relative heights in public mode).
- MapLibre terrain exaggeration is displayed in the UI control.

### 5.3 Scale bars, north arrows, labels, attributions
- Scale bar on every map view and static figure (MapLibre `ScaleControl`, metric). In small multiples, use **the same scale for all panels**; if that is impossible, use a prominent per-panel scale badge.
- North arrow when bearing ≠ 0 or in any static export. MapLibre `NavigationControl` with compass visible.
- Attribution on every map and figure: "Dane: GUGiK (ALS 2023, EVRF2007)", OSM contributors (ODbL), historical sources with archive and signature, "Processing: lidar-discovery-poland vX". Check the GUGiK licence wording (05 §8.2 q5) before public release.
- Layer labels always include epoch: "SVF · ALS 2023" / "Ortofoto 1944".
- Label style: white rounded box, 1 px dark leader line (F4 style). Typography 12-14 px on map, Cyrillic-capable font.

### 5.4 Dark / light
- `/explore` defaults to a **dark UI chrome** (relief imagery reads best on near-black, as in F1/F3/F5, and reviewers work long sessions). The map NoData colour is a neutral #111 rather than pure black.
- `/catalog` and story pages default to light, following `prefers-color-scheme`.
- Design tokens (CSS custom properties) for background, surface, text, accent, and the overlay palette, with dark and light values. Greyscale relief tiles are the same in both themes; only the NoData/background and the UI change.
- Contrast: label text ≥4.5:1 against the label box in both themes.

### 5.5 Motion and accessibility
- One auto-sweep at most, disabled under `prefers-reduced-motion`, stopped on first interaction (F1 practice).
- 3D: no autoplay rotation in review. In public, an optional turntable has a pause control.
- Every swipe and slider is keyboard operable (arrow keys) and has an `aria-label`. Each figure has alt text that states what is and is not shown.

---

## 6. Implementation roadmap

Effort is in developer-days for one developer familiar with the stack. Backend dependencies are named so they can be scheduled with the pipeline work.

### Phase 0 - Foundations inside the v0 frontend (≈4-6 d)
- Plug-in interface in `frontend/src/presentation/` and a shared `MapContext` (map instance, active location, disclosure mode, locale). 1.5 d.
- Design tokens (dark/light), i18n scaffolding (pl/uk/en), legend and scale/north/attribution components, layer labels with epoch. 2 d.
- Provenance footer component reading `layers[].provenance`. 0.5 d.
- Backend: ramp/rescale params on the tile endpoint + `X-Rescale` header. 1 d. **Dependency:** none beyond v0.

### Phase 1 - MVP review tools (≈12-18 d), target: usable during the M1 Caryńskie pilot
1. **M3 profile tool** (backend 4 d, frontend 4 d). **Dependency:** raw or extracted classified LAZ kept on disk for the pilot tiles; tile index by bbox. This is the most important single tool: it decides A1, it exposes interpolation, and nothing else checks the ground density.
2. **M2 small-multiples chips + VAT** (backend 3 d incl. openness and VAT; frontend 1.5 d). **Dependency:** `ldp process` gains `openness_*` and `vat`.
3. **M6 interpretation overlay with certainty styling + M8 evidence panel (internal)** (backend 2 d for `/evidence` and `/stats`; frontend 3 d). **Dependency:** `documentation_status` populated by the known-check (05 §6).

### Phase 2 - Richer review and comparison (≈15-22 d)
4. **M1 canopy curtain** with DSM/CHM products (backend 2 d, frontend 1.5 d; reuse the swipe).
5. **M5 then vs now** (frontend 2 d for swipe/fade/spyglass; backend 2 d to ingest historical COGs with licence and RMSE; **plus about 0.5-1 d per village** of georeferencing and digitising). **Dependency:** licence answers for the 1944 ortho and the cadastre (05 §8.2 q6).
6. **M4a terrain 3D** (backend terrain-RGB 1.5 d, frontend 1.5 d).
7. **M4b point-cloud view** with deck.gl + loaders.gl (backend LAZ subset 2 d, frontend 3-4 d). Defer Potree until reviewers ask for it.
8. **M9 two-epoch dz** (backend co-registration 3-4 d) and **M10 FP gallery** (1 d).

### Phase 3 - Public catalogue and story pages (≈20-30 d + content time)
9. Public-mode hardening: generalised tiles (resolution cap, masks), aggregate cells, coordinate readout off, export through public endpoints, and tests that public endpoints never emit restricted geometry (property tests). 5 d. **Dependency:** sensitive polygons digitised; WKZ notified (05 §8.4).
10. **M7 scrollytelling** framework (Scrollama, story JSON schema, no-JS fallback, print styles). 6-8 d. First story (Caryńskie) with M1/M5/M3/M8 steps. 4 d dev + writing.
11. Public **M8** card and the "method / what we don't know" page. 2 d.
12. Static export to PMTiles + static site (05 §11). 4-6 d. **Dependency:** licence clearance for derived relief.
13. Translation and community review loop: calendar time (weeks), not dev time.

### Build first (and why)
1. **M3 cross-section profile.** This is the evidence that a surface is real (F6 was the article's most credible figure). It is required for A1 (05 §4.4), automates the "no ground returns" honesty, and is the cheapest guard against interpolation artefacts in leaf-on Carpathian data.
2. **M2 multi-visualisation chips (incl. VAT).** A1 needs ≥2 visualisations. Same-scale chips make review fast and comparable, and they underpin the FP gallery and every later public figure.
3. **M6 + M8 interpretation overlay with an evidence panel.** This puts uncertainty and documentation status in front of the reviewer from day one, so the persuasive public modes (curtain, story) are later built on ratings that were honestly recorded rather than retrofitted.

The forest-removed curtain (M1) is the obvious crowd-pleaser and is cheap. It comes in Phase 2, deliberately after the tools that tell us whether what it reveals is real.

### Open questions
- Q-P1: licence of GUGiK-derived relief tiles for public redistribution and of the 1944 orthophoto (05 §8.2 q5-6).
- Q-P2: public relief resolution cap (1 m vs masks only; 05 Q4).
- Q-P3: whether reviewers need Potree-grade point-cloud navigation, or whether profiles + deck.gl subsets suffice (decide after the pilot).
- Q-P4: who signs off story text per village (descendant organisations, IGiPZ PAN).
