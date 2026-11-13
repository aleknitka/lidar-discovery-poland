# 01 - LiDAR / elevation data sources for south-eastern Poland (Operation Vistula / WWII-era village traces)

Tags: [VERIFIED: fetched page] = content retrieved by WebFetch in this session (summaries produced by a small model; re-check exact figures before citing).
[UNVERIFIED: search snippet] = only seen in WebSearch result text. [UNVERIFIED: memory] = not checked in this session.
[DERIVED] = arithmetic/inference from verified facts.

---

## 1. Polish national ALS data (GUGiK / Geoportal)

### 1.1 Product overview
- Point clouds: ALS, XYZ + class, echo, intensity, optional RGB; LAS, with LAZ "almost always" used; classes 0,2,3,4,5,6,7,8,12. [VERIFIED: fetched page] https://geoportal.gov.pl/en/data/lidar-measurements-lidar ; https://www.geoportal.gov.pl/pl/dane/dane-pomiarowe-lidar
- Density stated nationally: "from about 4 pts/m2 up to 20 pts/m2 in cities". [VERIFIED: fetched page] same two URLs.
- "Territory of Poland is covered with ALS data." [VERIFIED: fetched page] https://geoportal.gov.pl/en/data/lidar-measurements-lidar (note: this is a general claim; per-area coverage not checked).
- DTM/NMT: 1 m x 1 m grid "updated systematically from ALS"; secondary 5 m grid from stereo for 25 cm orthophoto production; downloaded NMT files are Arc INFO GRID. [VERIFIED: fetched page] https://www.geoportal.gov.pl/pl/dane/numeryczny-model-terenu-nmt/
- Free download and use "for any purpose" (NMT and LiDAR pages). [VERIFIED: fetched page] same URLs. Page does not name a licence; check Regulamin: https://www.geoportal.gov.pl/pl/o-geoportalu/regulamin/ [VERIFIED: linked from https://www.geoportal.gov.pl/pl/dane/ ; content NOT fetched]. Footer: "(c) 2023 Glowny Urzad Geodezji i Kartografii" [VERIFIED: fetched page https://www.geoportal.gov.pl/pl/dane/].

### 1.2 Point density per scanning standard (ISOK)
- Standard I: >= 4 pts/m2 for a single strip; Standard II: >= 12 pts/m2 (two independent flights, each >= 6 pts/m2) [UNVERIFIED: search snippet, quoting an ISOK-related table; source https://www.igipz.pan.pl/tl_files/igipz/ZSIGiK/news/ISOK/ISOK_szkolenia.pdf was returned as binary and NOT readable by WebFetch].
- Urban standard for cities >50,000 inhabitants: 12 pts/m2; rest of area: 4 pts/m2 (basic). [UNVERIFIED: search snippet] https://geoforum.pl/wydanie/1051/artykul/241/archiwum-geodety/wydanie/193.pdf (not fetched) ; a Koszalin study cites standard II at 12 pts/m2 for an urbanised city [UNVERIFIED: search snippet].
- Another snippet (Przeglad Geologiczny) describes ISOK blocks at 4-12 pts/m2 [UNVERIFIED: search snippet] https://geojournals.pgi.gov.pl/pg/article/download/27182/18899/41289 (not fetched).
- Tile/module sizes: ~550x550 m (urban, ~12 pts/m2) and ~1100x1100 m (other, 6-8 pts/m2) [UNVERIFIED: search snippet; source https://sparrow.up.poznan.pl/kul/sites/default/files/przedmioty/geomatyka_rozsz_wyklad_8_2025_konspekt.pdf not fetched]. Another snippet: "tiles ~550x550 m urban, ~1100x1100 m other" [UNVERIFIED: search snippet, https://yadda.icm.edu.pl/... Zawieska PDF].
- **Standards III and IV (the 1 and 2 pts/m2 tiers the brief refers to): NOT CONFIRMED.** No source found in this session states them. Treat as unverified until the GUGiK ALS technical specification is located.
- Podkarpackie / Bieszczady / Beskid Niski point density and standard: **NOT CONFIRMED.** One search snippet mentioned a 2021 campaign with 4 / 12 pts/m2 but for a different voivodeship (Drezdenko context) [UNVERIFIED: search snippet, do not apply to Podkarpackie].
- Bieszczady-specific LiDAR use (DTM for naturalness, channel heads): mentioned in search snippets only [UNVERIFIED: search snippet] https://archiwum.bdpn.pl/dokumenty/roczniki/rb23/art05.pdf (binary, NOT readable) ; channel-head LiDAR dataset (Bieszczady, multiple LiDAR resolutions) [UNVERIFIED: search snippet] https://bvbvf1.bib-bvb.de/... (not fetched).

### 1.3 Years of acquisition
- WFS indexes: KRON86 = 2010-2019 (layers "Skorowidz danych pomiarowych LIDAR 2010" ... "2019"); the page says the index is split "by year of data currency". [VERIFIED: fetched GetCapabilities] https://mapy.geoportal.gov.pl/wss/service/PZGIK/DanePomiaroweLidarKRON86/WFS/Skorowidze?SERVICE=WFS&REQUEST=GetCapabilities
- EVRF2007: indexes "2018-2025" per one fetch [VERIFIED: fetched page https://www.geoportal.gov.pl/pl/dane/dane-pomiarowe-lidar] but "2018-2020" per another fetch [VERIFIED: fetched page https://geoportal.gov.pl/en/data/lidar-measurements-lidar]. **Conflict - check the EVRF2007 WFS GetCapabilities directly.** The English page also gives KRON86 "2011-2019", conflicting with the 2010-2019 WFS layer list. The Polish page says the KRON86 WFS index covers 2010-2019 (the layer list above is the authoritative item).
- NMT pages: KRON86 index 2000-2019; EVRF2007 from 2018 [VERIFIED: fetched page https://www.geoportal.gov.pl/pl/dane/numeryczny-model-terenu-nmt/].
- **Per-sheet acquisition year is in the WFS/WMS attributes, not checked for Podkarpackie** (no feature query performed).

### 1.4 CRS and vertical datum
- EPSG:2180 (PL-1992) is the default CRS of the LiDAR skorowidze WFS. [VERIFIED: fetched GetCapabilities, DanePomiaroweLidarKRON86 WFS] ; EPSG:2180 used in NMT WMS. [VERIFIED: fetched page https://www.geoportal.gov.pl/pl/dane/numeryczny-model-terenu-nmt/]
- Other CRS offered by that WFS: EPSG:4326, EPSG:3857 [VERIFIED: fetched GetCapabilities].
- 2000 zones (EPSG:2176-2179) are offered by the NMT WMS [VERIFIED: fetched GetCapabilities https://mapy.geoportal.gov.pl/wss/service/PZGIK/NMT/GRID1/WMS/ShadedRelief?SERVICE=WMS&REQUEST=GetCapabilities]. Which zone covers Bieszczady (zone 2000 numbering) is NOT verified here: [UNVERIFIED: memory] EPSG:2178 = zone 7 (19 deg E central meridian), EPSG:2179 = zone 8 (22 deg E). Podkarpacie is roughly 21-24 deg E, so zone 7-8 are the candidates; confirm before use.
- Vertical datums: PL-KRON86-NH and PL-EVRF2007-NH [VERIFIED: fetched pages].
- NOTE: the KRON86 vs EVRF2007 difference is a few decimetres to >1 m locally in Poland, so check which datum a given tile uses before comparing with other sources [UNVERIFIED: memory].

### 1.5 Formats and bulk download
- Downloads: LAZ tiles (point cloud); ARC INFO GRID for NMT. [VERIFIED: fetched pages]
- Methods [VERIFIED: fetched pages]:
  1. "Pobierz dane" module: https://mapy.geoportal.gov.pl/imapnext/imap/index.html?moduleId=modulPD (listed on https://www.geoportal.gov.pl/pl/dane/). Under "Dane do pobrania" > "Chmura punktow" layers.
  2. WMS GetFeatureInfo returns a LAZ download link: https://mapy.geoportal.gov.pl/wss/service/PZGIK/DanePomNMT/WMS/SkorowidzeWUkladzieKRON86 and .../SkorowidzeWUkladzieEVRF2007 (one fetch) ; a different fetch gave https://mapy.geoportal.gov.pl/wss/service/PZGIK/DanePomiaroweNMT/WMS/SkorowidzeUkladKRON86 and .../SkorowidzeUkladEVRF2007. **The two WMS path sets conflict - neither confirmed by GetCapabilities.**
  3. WFS skorowidze, then "Link do pobrania" from object info: https://mapy.geoportal.gov.pl/wss/service/PZGIK/DanePomiaroweLidarKRON86/WFS/Skorowidze (VERIFIED GetCapabilities; 10 feature types 2010-2019, typenames e.g. gugik:SkorowidzDanychPomiarowychLIDAR2012) ; EVRF2007 equivalent https://mapy.geoportal.gov.pl/wss/service/PZGIK/DanePomiaroweLidarEVRF2007/WFS/Skorowidze [UNVERIFIED: not fetched; cited by 2 fetched pages].
  4. WCS for NMT: "Pobierz dane z uslugi WCS" tool, limit "maksymalnie 7 km2" per request [VERIFIED: fetched page].
- Suggested bulk approach [DERIVED]: query the WFS skorowidz with WFS GetFeature (typename gugik:SkorowidzDanychPomiarowychLIDAR<year>, bbox in EPSG:2180, outputFormat GML) to get the "Link do pobrania" per sheet, then wget the links. Not yet tested; the GetFeature call and attribute name for the download link are UNVERIFIED.
- Geoportal service list (WMS/WMTS, WFS, WCS, ATOM, OGC API Features, API, CSW): https://www.geoportal.gov.pl/pl/usluga/wykaz-uslug/ [VERIFIED: fetched link list, page itself not fetched]. ATOM client: https://www.geoportal.gov.pl/pl/aplikacje/do-pobrania/ [VERIFIED: link list].
- dane.gov.pl: NOT checked in this session. [UNVERIFIED: memory] open-data catalogue for GUGiK datasets exists; confirm.
- Viewers (free): CloudCompare, Fugro Viewer, LiMON Viewer (listed on the Geoportal page) [VERIFIED: fetched page].

### 1.6 Coverage of the target area
- Bieszczady / Beskidy / Roztocze / Lubaczow: NOT CONFIRMED tile-by-tile. Only the national "covered" statement is verified (see 1.1). Run the WFS skorowidz per year to check.

---

## 2. Orthophoto and WMS/WMTS layers (current)

- Orthophoto WMS (Polska): service title "Usluga przegladania (WMS) ortofotomap dla obszaru Polski", WMS 1.3.0. Endpoint https://mapy.geoportal.gov.pl/wss/service/PZGIK/ORTO/WMS/StandardResolution?SERVICE=WMS&REQUEST=GetCapabilities [VERIFIED: fetched GetCapabilities; the "StandardResolution" path was named in a search snippet and the fetch succeeded]. Single named layer: "Raster" (Title "Raster"); top-level "Ortofotomapy dla Polski", nested "ORTOFOTOMAPA". CRS: EPSG:4326, 2180, 2176-2179, 3857 (plus CRS:84). Formats: png, tiff, jpeg, png8/24/32, gif, bmp, svg+xml. **No time dimension, no historical layers in this capabilities document.** [VERIFIED: fetched]
- HighResolution ORTO endpoint: named in a search snippet [UNVERIFIED: search snippet]. Not fetched.
- Shaded relief (NMT cieniowanie): https://mapy.geoportal.gov.pl/wss/service/PZGIK/NMT/GRID1/WMS/ShadedRelief?SERVICE=WMS&REQUEST=GetCapabilities ; service title "Numeryczny Model Terenu - Cieniowanie", WMS 1.3.0; layer Name "Raster" (Title "Cieniowanie w siatce 1m x 1m"); CRS EPSG:4326, 2180, 2176-2179, CRS:84; output image/jpeg, tiff, png (+ others). [VERIFIED: fetched GetCapabilities]. Note: the first attempt returned HTTP 503; the retry succeeded. Service may be intermittently unavailable.
- Geoportal "Dane archiwalne" layer group (archival data, WMS/WMTS) [UNVERIFIED: search snippet, source Geoportal help doc not fetched].
- Historical / wartime aerial photos: Geoportal reports GUGiK is digitising archival aerial photos ("Smart Geoportal" project) [UNVERIFIED: search snippet, source not fetched]. A wartime-era orthophoto series ("Ortolub 1944") exists in university teaching materials [UNVERIFIED: search snippet, https://phavi.umcs.pl/at/attachments/2021/0714/140042-instrukcja-ortolub-1944-qgis.pdf not fetched]. **No verified WMS endpoint for 1945-1955 imagery.**
- Mapa zasadnicza WMS: NOT checked in this session. Geoportal "Mapa zasadnicza" is a known product [UNVERIFIED: memory].
- Public PRG (topographic database) WFS: https://www.geoportal.gov.pl/pl/dane/ mentions PRG with WFS and "Pobieranie danych poprzez geoportal.gov.pl" [VERIFIED: fetched page, endpoint not fetched].
- Geoportal service pages (WMS/WMTS, WFS, WCS, OGC API Features): https://www.geoportal.gov.pl/pl/usluga/uslugi-przegladania-wms-i-wmts/ , https://www.geoportal.gov.pl/pl/usluga/uslugi-pobierania-wfs/ , https://www.geoportal.gov.pl/pl/usluga/uslugi-pobierania-wcs/ , https://www.geoportal.gov.pl/pl/usluga/uslugi-ogc-api-features/ [VERIFIED: link list only, not fetched].

---

## 3. NASA and other global / regional sources

### 3.1 NASA GEDI / ICESat-2 / G-LiHT
- GEDI: orbit band about 51.6 N to 51.6 S (ISS-mounted). Bieszczady (~49 N) is inside the band. [UNVERIFIED: search snippet, https://www.earthdata.nasa.gov/es/data/catalog/lpcloud-gedi01-b-003?page=6%2C0 - the search result for GEDI01_B; not fetched directly]. 
- GEDI footprint average 25 m (diameter), discrete footprints, not wall-to-wall [UNVERIFIED: search snippet, https://www.earthdata.nasa.gov/fr/data/catalog/lpcloud-gedi02-b-002?page=1].
- Coverage comparison GEDI vs ICESat-2 (Pronk et al., 2024, Remote Sensing, DOI 10.3390/rs16132259) [UNVERIFIED: search snippet, https://doaj.org/article/7fb7f2523ce24218b9fadabdb476d25c]: combined altimetry DEM ~500 m resolution globally.
- ICESat-2: ~17 m footprint, ~0.7 m along-track sampling, 6 beams [UNVERIFIED: memory - verify with NASA ICESat-2 docs before use].
- Use case: a GEDI/ICESat-2 footprint is a point sample of ground elevation, not an image. It cannot resolve house platforms or cellars at 1-3 m scale. **Assessment: not useful for micro-relief.** Possible use: validating a DTM vertically (e.g. a Bieszczady transect), or regional context. [DERIVED from above]
- G-LiHT: NASA airborne LiDAR; OpenTopography lists G-LiHT only as a collector/filter (Yucatan 2013 dataset) [VERIFIED: fetched https://portal.opentopography.org/datasets and https://www.opentopography.org/]. No G-LiHT coverage of Poland found.

### 3.2 OpenTopography
- Dataset list includes global/regional DEMs: "COP 30m & 90m", "EU_DTM", "AW3D30", "SRTM_GL1 & GL3", "SRTM15Plus", "GEDTM30", "GMRT", "GEBCOIceTopo", "NASADEM", "GEDI_L3", "ANADEM", "USGS 1m/10m/30m" [VERIFIED: fetched https://portal.opentopography.org/datasets].
- High-resolution location filter list does NOT include Poland (includes Finland, France, Greece, Iceland, Italy, Norway, Slovenia, Spain, Switzerland, UK) [VERIFIED: fetched https://portal.opentopography.org/datasets].
- July 2026 release news: new country-wide DEMs for Norway, Finland, Switzerland, Liechtenstein at 0.5-2 m; "new coverage across Europe, Central America and the US" [VERIFIED: fetched https://www.opentopography.org/news/ocean-satellite-data-now-available-opentopography]. Poland not named.
- Conclusion: OpenTopography does not appear to host Polish ALS; use GUGiK directly. [DERIVED]

### 3.3 Copernicus DEM GLO-30 / GLO-90
- GLO-30 30 m, GLO-90 90 m; global; EGM2008 heights (EPSG:3855); **a DSM (surface model incl. vegetation and buildings)** [VERIFIED: fetched https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM].
- Absolute vertical < 4 m (90% linear); relative < 2 m (slopes <= 20%) [VERIFIED: same page].
- Licence: free worldwide, attribution to DLR/Airbus; registration required; available via Copernicus Browser, API, S3/OData bulk [VERIFIED: same page].
- Usefulness for micro-relief: **not useful** (30 m grid, +/-4 m vertical, DSM). [DERIVED]

### 3.4 SRTM, EU-DEM
- SRTM 1 arc-second (30 m) and EU-DEM 25 m: NOT verified in this session (fetch of EEA/CLMS pages failed or redirected). [UNVERIFIED: memory] EU-DEM v1.1 is a DSM at 25 m, EGM96 heights, ETRS89-LAEA; SRTM is a 2000 radar DSM at 30 m. Both lack micro-relief resolution. Verify before citing.

### 3.5 Slovakia (ZBGIS / ULGK SR)
- Cycle 1 ALS (DTM 5.0): 2017-2023; 42 lots of 900-1,800 km2; minimum density 5 pts/m2 last-reflection; DTM 1x1 m raster (ASC, ESRI GRID, TIFF). [VERIFIED: fetched https://www.skgeodesy.sk/geoportal-en/zbgis/als and https://www.skgeodesy.sk/geoportal-en/zbgis/als/1st-cycle]
- Cycle 1 achieved density: 15-52 pts/m2 [UNVERIFIED: search snippet, https://www.skgeodesy.sk/geoportal-en/zbgis/als/1st-cycle snippet, not fully fetched].
- Cycle 2 (DTM 6.0 / DSM 2.0): 2022-2026; 73 lots of 500-900 km2; min 15 pts/m2; LAZ point clouds; footprints in SHP/GDB [VERIFIED: fetched https://www.skgeodesy.sk/geoportal-en/zbgis/als].
- Free download from opendata.skgeodesy.sk (footprint ZIPs 3-480 MB); licence CC BY 4.0 [VERIFIED: fetched https://www.skgeodesy.sk/geoportal-en/zbgis/als]. Note: this is the most usable open ALS for the Slovak side of the Beskid Niski / Bieszczady border.
- CRS: S-JTSK (JTSK03) with Bpv heights; ETRS89-TM34 with hETRS89 heights [VERIFIED: fetched 1st-cycle page].
- Eastern lots 37, 38, 40, 41, 42 were affected by the war in Ukraine; some areas scanned until 30 June 2022; some lots 40-42 supplemented by National Forest Centre data 2018-2023 [VERIFIED: fetched 1st-cycle page]. Which lot covers the Svidnik/Medzilaborce/Snina (border) area: NOT CONFIRMED.
- Density of ZBGIS DMR 4 (older model): NOT confirmed.

### 3.6 Ukraine side (Lviv oblast / Sian headwaters / Sianki area)
- No open national airborne LiDAR found. [UNVERIFIED: search only, negative result] Searches returned: ICESat-2 DEM validation for Ukrainian Carpathians (flood study); GEDI old-growth forest study; plans by the State Forestry Agency to scan forests with drones [UNVERIFIED: search snippets, https://ecopolitic.com.ua/en/news/3d-model-of-ukrainian-forests-state-forestry-agency-plans-to-use-lidar-scanning-technology/].
- Ukrainian State Geocadastre open LiDAR: NOT confirmed. Check directly.

### 3.7 Other notes
- Lidar from national/regional projects in Czech Republic and Germany are out of scope for this brief; not searched.

---

## 4. Practical

- Data volume per km2 [DERIVED]: at 4 pts/m2 = 4,000,000 points per km2; at 12 pts/m2 = 12,000,000. Raw LAS (point format 1.4, 30 bytes/point) would be ~120 MB/km2 (standard II) or ~40 MB/km2 (standard I) before compression; LAZ compression ratio is not verified here.
- Tile size [UNVERIFIED: search snippet]: ~1100 m x 1100 m (rural, ~1.21 km2) and ~550 m x 550 m (urban). A 50 km2 forest block is therefore ~40 rural tiles, roughly 1-3 GB as LAZ (estimate; unverified).
- Standard I vs II for Bieszczady: NOT CONFIRMED. Expected rural = standard I (4 pts/m2) by ISOK logic [UNVERIFIED: memory and snippets]. Check the sheet metadata (year, density) in the WFS skorowidz or in LAS headers (Point Density).
- Ground classification in forest: NOT researched in this session. (Expect low ground-return fraction under dense spruce/beech canopy at 4 pts/m2; treat as a gap.)
- Newer scans: Geoportal index lists updated years to 2025 for EVRF2007 (one fetch) [VERIFIED: fetched page, conflicting]. 
- Recommend checking: EVRF2007 WFS GetCapabilities; LAS header for density; Bieszczady sheet list in WFS.

---

## 5. Items I could not confirm (open list)

1. ISOK standards III and IV (1 and 2 pts/m2 tiers) - not found in any readable source. ISOK PDF (igipz.pan.pl) returned as binary.
2. Point density / acquisition year for Podkarpackie, Bieszczady, Beskid Niski, Roztocze, Lubaczow.
3. Working EVRF2007 WFS and WMS skorowidz endpoints (two conflicting WMS path sets; EVRF2007 WFS not fetched).
4. Correct EPSG 2000 zone for each target area (zones 7 or 8 candidates, unverified).
5. dane.gov.pl entries for GUGiK LiDAR.
6. Geoportal Regulamin content (licence text) - linked, not fetched.
7. Historical aerial photography WMS for 1945-1955 - not found.
8. Mapa zasadnicza WMS - not checked.
9. HighResolution ORTO endpoint - named but not fetched.
10. Ukraine open LiDAR - negative search only.
11. SRTM and EU-DEM specifics - not verified.
12. Forest ground-classification quality on Polish ALS - not researched.
13. ICESat-2 footprint/spacing figures - memory only.
14. Slovak lot covering Bieszczady-border area - not confirmed.
15. GEDI 51.6 deg band and 25 m footprint - from search snippets, not fetched from NASA docs.

Source URLs in this file were all fetched or returned by search in this session. No endpoint was invented; unfetched endpoints are marked as such.

## 6. Orchestrator live verification (2026-11-12) [VERIFIED: queried directly]
WFS `.../DanePomiaroweLidarKRON86/WFS/Skorowidze`, WFS 2.0.0, layers `gugik:SkorowidzDanychPomiarowychLIDAR2010..2019`.
Bbox query (EPSG:4326, lat/lon order) around Carynskie (49.19-49.20 N, 22.55-22.56 E): tiles only in the **2012** layer (none in 2010-11, 2013-19).
Example tile attributes: `godlo` M-34-106-A-c-3-2-4, `akt_data` 2012-10-19, `char_przestrz` **4 p/m2**, `format` LAS (served as LAZ), `blad_sr_wys` 0.15 m, `blad_sr_syt` 0.50 m, `uklad_xy` PL-1992, `uklad_h` PL-KRON86-NH, `url_do_pobrania` = direct download, pattern `https://opendata.geoportal.gov.pl/NumDaneWys/DanePomiaroweLAZ/<id>/<id>_<feature>_<godlo>.laz`. Tile ~1.2 x 1.2 km.
Consequence: Bieszczady near Carynskie is 4 p/m2 (ISOK standard I), 2012 vintage. Enough for ~0.5 m DTM per the literature but near the lower limit; terrain/leaf-off conditions of the 2012 acquisition are unknown. Bulk acquisition can be fully scripted from the WFS. Not yet checked: other parts of the study area, and whether newer (2019+) layers exist outside the KRON86 service (EVRF2007 service).
