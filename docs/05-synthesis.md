# 05 - Synthesis: LiDAR discovery of traces of villages emptied in 1944-1951, south-eastern Poland

Status: research synthesis for pipeline design. Written 2026-11-12. Next step: an independent critique (Fable).
Inputs: `docs/bieszczady-lidar-handoff.md` [H], `docs/research/00..04` [N00]-[N04].

## Evidence tags used in this document

| Tag | Meaning |
|---|---|
| **[V\*]** | Verified by me in this synthesis pass (fetched page, Crossref record, PDF text, or live service query). Details in Appendix A. |
| **[V]** | Marked verified (fetched) in a research note. I did not re-check it. Treat figures as probably right. |
| **[U]** | Unverified: search snippet, memory, or a secondary source. A lead, not a fact. |
| **[D]** | Derived: my arithmetic or design proposal. No source. |
| **[ORCH]** | Verified live by the orchestrator before this pass. |

Raw material from my checks is in the session scratchpad (WFS GML dumps, PDF text extractions, LAS header reads). It is not committed.

---

## 1. Executive summary

### 1.1 What we know

1. **The idea is not new for this region. The scale is.** Affek, Wolski, Latocha, Zachwatowicz and Wieczorek have mapped pre-war micro-relief in abandoned Carpathian villages by hand: Caryńskie in the Bieszczady, Borysławka and Posada Rybotycka in the Wiar basin, and Rogóżka in the Sudetes, as a comparison. Their headline result: 38-70% of non-natural parcel boundaries and 65-79% of roads on mid-19th-century cadastral maps are still detectable in LiDAR [V\*, Affek et al. 2022, DOI 10.1002/arp.1846]. I found no systematic, region-wide or automated inventory across the roughly 100+ former villages of the Western Bieszczady [N02 §3.2; my search, §4].
2. **The data is much better than the earlier notes assumed.** The WFS tile index labels every tile near Caryńskie "4 p/m2". But GUGiK also serves a **2023 acquisition** (EVRF2007 service), not only 2012. Reading the LAS headers of the actual files gives about **59-84 points/m² (all returns)** for two 2023 tiles covering Caryńskie, against about 8-13 points/m² for 2012-13 tiles [V\*, §3.3]. This is the most important new fact in this document. The "4 p/m2" attribute is a nominal minimum, not the delivered density. Ground-return density under forest and the leaf-on/leaf-off state of the 2023 flight are **still unknown** until we decompress a tile.
3. **The earlier village coordinates are wrong.** All 8 preset coordinates in [H] are 2.7-11 km from the Wikidata/Wikipedia coordinates (Appendix B). The orchestrator's pilot point (49.195 N, 22.555 E) is about 5 km NW of Caryńskie, which lies at about 49.166 N, 22.618 E [V\*, IALE poster, Wikidata]. Caryńskie is inside **Bieszczady National Park** [V\*, pl.wikipedia]. That limits fieldwork.
4. **"Operation Vistula" is the wrong umbrella label for most Bieszczady villages.** Caryńskie was emptied in late April-May 1946. Wolski states explicitly that Akcja "Wisła" played little role in present-day gmina Lutowiska, because most villages there were already emptied [V\*, Wolski poster]. The regional sequence is: deportation to Soviet Ukraine (1944-46), Operation Vistula (1947), and Operation H-T, the 1951 border exchange, which removed the inhabitants of about 40 more villages in the north-east [V\*, Wolski 2016, DOI 10.7163/GPol.0064]. Cause must be a per-village field with a source.
5. **Polish law on searching changed on 1 May 2025.** The old permit regime (art. 36 ust. 1 pkt 12) and the penalty in art. 109c, both cited in [N04], are **repealed** in the consolidated text. They are replaced by a registration-via-app regime with landowner and possessor consent (art. 36b). Art. 36c bans searching in cemeteries, former cemeteries, war graves and registered or recorded monuments plus a 10 m buffer. Penalties are now in art. 109d-109e [V\*, Dz.U. 2024 poz. 1292]. Three later amendments (2025-2026) were not read. Desk-based LiDAR analysis is not "searching with a device" as written, but this needs a lawyer's confirmation (§8).

### 1.2 What is feasible

- **Feasible now:** a reproducible pipeline that downloads GUGiK point clouds by script, builds 0.5 m DTMs, renders SVF, openness, local-relief and VAT products, and produces ranked candidate features. A human then triages them against an explicit known-check. Every component exists. The WFS gives direct download URLs [ORCH, V\*].
- **Realistic "discoveries":** mostly **feature-level additions to already-known villages**: house platforms, cellars, wells, roads, terraces, cemetery and chapel outlines. Less often, **hamlets, colonies or farmsteads** that are absent from modern gazetteers but drawn on historical maps. Finding a village absent from every source is unlikely. Villages are well documented in archives (§4.3).
- **Not feasible without partners:** field verification inside the National Park, access to AZP (Polish Archaeological Record) site records with coordinates, and authoritative per-village cause-of-depopulation data. All three need institutional contact: WKZ Przemyśl, BdPN, NID, and IGiPZ PAN (Affek and Wolski).
- **Not useful:** NASA products for micro-relief. GEDI and ICESat-2 give footprints, not imagery. G-LiHT has no Poland coverage [V, N01 §3]. The Maya post's "NASA lidar" does not transfer.

### 1.3 The five decisions that matter most

| # | Decision | Recommendation | Why it matters |
|---|---|---|---|
| D1 | Primary data epoch | **2023 EVRF2007 point clouds** as primary; 2012 KRON86 as a second epoch for QA and change. Decide only after a one-tile QA (ground density under forest, flight date from GPS time). | A 5-10x density difference changes what is detectable: cellars and wells versus only terraces and roads. |
| D2 | What counts as a "discovery" | Two-axis rating: anthropogenic confidence A0-A3 × novelty tier T0-T3 (§4.4). The default product is T1 (new features in known villages). | Avoids the HN failure mode: claiming novelty for what is already in the literature. |
| D3 | Detection strategy | Start with **human review of standard visualisations plus simple morphometric candidate rules**, measured on a labelled pilot. Add ML (U-Net or detector) only once ≥300-500 labelled features exist. A VLM is an optional ranker, benchmarked against that baseline. | Published DL precision on rare archaeology is low (0.26 for hillforts). Without labels, ML gives numbers we cannot check. |
| D4 | Python environment | **pixi (conda-forge) with Python 3.12**: PDAL, GDAL, rasterio, laspy+lazrs, numba, rvt vis module. The uv-only Python 3.12 path stays as a fallback. Drop the `>=3.14` pin. | PDAL has no PyPI wheel for Windows. rvt-py declares `<3.12`, but its `rvt.vis` module is GDAL-free (§9). |
| D5 | Disclosure and partnership | Tiered disclosure (§8.4). No public point coordinates for unregistered features, cemeteries or bunkers. Contact WKZ Przemyśl, BdPN and IGiPZ PAN before any public release. | Looting, desecration, UXO and Polish-Ukrainian memory politics. Also the legal duty to notify. |

---

## 2. What the Maya post and the HN thread actually teach us

Source: [N00], plus my own re-fetch of the post [V\*]. I did **not** re-read the HN thread. All HN points below are [N00]-level (partly summarised by a small model).

### 2.1 What the post is

- It is a diary-style blog post, not a method paper. The author is self-described as "not an archaeologist" [V, N00].
- **Data:** "NASA lidar data", about 1,200 km² of strips. No product name is given [V\*]. G-LiHT (Cook et al. 2013) is cited as a reference, which suggests but does not prove that the strips were G-LiHT [V\* that it is cited; the inference is mine, U].
- **Method, verbatim:** "There was no special model or classifier involved: the agents literally looked at the pictures, following a precise guide." [V\*]. The guide is not published [V, N00].
- **Validation:** inspection of the point cloud (ground versus vegetation returns, profiles), then a report to INAH [V, N00].
- **Outcome:** INAH replied that "no registered archaeological site was identified at the location". The site was nevertheless **already published** in Estrada-Belli et al. 2025, which the agents' literature search missed [V\*]. No cost figure is given. The elapsed time was "less than 72 hours" from idea to INAH reply [V\*].

### 2.2 The lessons, stated exactly

1. **The official register can be incomplete while the literature is not.** INAH's register did not contain the site, but a 2025 paper did [V\*]. For us: absence from NID/AZP registers is **weak evidence** of novelty. The known-check must include the scientific literature: Affek, Wolski, theses, BdPN yearbooks, regional journals. It must also include grey and community sources such as Magurycz, local lists and tourist literature.
2. **The pipeline shape is portable; the method is not.** LiDAR, then images, then triage, then external validation, then a report to the authority [N00]. Nothing in the post tells us which visualisations, thresholds or detectors work.
3. **Agents persuade their operators.** The HN critique (nickalaso, per [N00]): an agent swarm should have been run on an exhaustive "has this been found?" task, and LLMs are good at convincing their handler that something is significant [U, HN not re-read]. Design consequence: the novelty verdict must be **produced by a deterministic, logged checklist** (§6), not by an LLM's opinion. An LLM may help retrieve literature, but every match or non-match is recorded with the query and the source.
4. **Experts are needed for "the last 10%"** (sailfast, per [N00]). We plan for archaeologist or conservator review and field checks.
5. **Ranking idea** (y04nn, per [N00]): detect unnatural shapes, cluster them, and rank co-occurrence higher. This fits villages well. A single pit means little; a row of rectangular platforms with pits beside a hollow way along a stream is a farmstead line (§5.3, rule R5).
6. **Coordinates were censored** by the author [N00]. That supports tiered disclosure (§8.4).
7. **Cost and reproducibility were not reported.** We log compute, reviewer minutes per km², and model and prompt versions per candidate (§10.5).

### 2.3 What the post does not teach

It gives no evidence on precision or recall, no false-positive taxonomy, nothing on temperate forest, and nothing on small features of about 5-15 m such as house platforms. In Maya work the targets are pyramids 8-12 m tall. Our targets are cellars about 0.5-2 m deep and platforms a few decimetres high. The detection problem is different in kind.

---

## 3. Data

### 3.1 Sources ranked by usefulness for micro-relief

| Rank | Source | Resolution / density | Coverage of study area | Use | Status |
|---|---|---|---|---|---|
| 1 | **GUGiK ALS point clouds, EVRF2007 service, 2023** | Nominal "4 p/m2" (and "12 p/m2" blocks). **Measured 59-84 pts/m² all returns** on 2 Caryńskie tiles; 32 pts/m² and 8.6 pts/m² elsewhere | 2,387 tiles at "4 p/m2" plus 608 at "12 p/m2" intersect bbox 49.00-49.70 N / 22.10-22.95 E | Primary DTM source | [V\*] counts and headers; ground density and season unknown |
| 2 | GUGiK ALS, EVRF2007, 2025 | "12 p/m2"; measured 27-43 pts/m² on 2 tiles | 608 tiles, same footprint as the 2023 "12 p/m2" block, roughly 49.41-49.59 N, 22.11-22.67 E (Lesko-Ustrzyki Dolne-Bircza belt) | Second epoch for the northern belt | [V\*] |
| 3 | GUGiK ALS, KRON86 service, 2012-2014 | Nominal "4 p/m2"; measured 8.3-13.3 pts/m² on 3 tiles | 2012: 1,385 tiles; 2013: 553; 2014: 711 in bbox | Second epoch; continuity with Affek and Wolski, who used ISOK at 4 p/m2 single strip | [V\*] |
| 4 | GUGiK NMT 1 m grid (WMS/WCS/download) | 1 m | National | Quick look only. Too coarse: ploughing traces and ruts disappear at 1 m [V\*, IALE poster] | [V, N01] |
| 5 | Slovak ZBGIS ALS, cycle 2 | min 15 pts/m², LAZ, CC BY 4.0 | Slovak side of the border | Cross-border context only | [V, N01] |
| 6 | Historical aerial photos (PZGiK scans 1951+, 1960s) | Photo | Unknown per area | "Last built state" evidence, not relief | [U, N04 §2.3] |
| 7 | Copernicus GLO-30, SRTM, EU-DEM | 25-30 m DSM | Global | Not useful | [V/U, N01] |
| 8 | NASA GEDI, ICESat-2 | Footprints of about 17-25 m, sparse tracks | Inside the band | Not useful for micro-relief; vertical QA at most | [U, N01] |
| 9 | NASA G-LiHT | Airborne | No Poland coverage found | Not applicable | [V, N01] |
| - | Ukraine (Lviv oblast) open ALS | None found | - | Gap: Sianki, upper San right bank | [U, negative search] |

### 3.2 The honest NASA answer

NASA has no data that resolves house platforms or cellars in Poland. GEDI and ICESat-2 sample ground elevation in footprints about 17-25 m across along tracks [U]. They cannot make an image. G-LiHT, the NASA airborne lidar the Maya post probably drew on, has no Polish coverage on OpenTopography [V, N01 §3.1]. The Polish national ALS is far better than anything NASA offers here. "Use NASA" should be dropped from the project framing, except as an optional vertical sanity check.

### 3.3 Coverage, density and year in the study area (verified this pass)

Method: WFS 2.0.0 `GetFeature` with `RESULTTYPE=hits` and full feature downloads for bbox 49.00-49.70 N, 22.10-22.95 E (EPSG:4326 lat/lon order) on both services. LAS header range-reads (first 375 bytes) of eight files [V\*].

**Tile counts in the bbox**

| Service | Year layer | Tiles | `char_przestrz` | Project number (`nr_zglosz`) |
|---|---|---|---|---|
| KRON86 | 2010, 2011, 2015-2019 | 0 | - | - |
| KRON86 | 2012 | 1,385 | 4 p/m2 | M-3334-012/11 |
| KRON86 | 2013 | 553 | 4 p/m2 | M-3334-012/11 (230), M-34-014/13/F (323) |
| KRON86 | 2014 | 711 | 4 p/m2 | M-34-013/13/F (707), M-34-014/13/F (4) |
| EVRF2007 | 2018-2022, 2024, 2026 | 0 | - | - |
| EVRF2007 | **2023** | **2,995** | 4 p/m2 (2,387), **12 p/m2 (608)** | GI-FOTO.6202.7.2023; GI-FOTO.6201.11.2023 |
| EVRF2007 | 2025 | 608 | 12 p/m2 | GK-FOTO.6201.8.2025; GK-FOTO.6201.14.2025 |

**Measured density from LAS headers** (point count ÷ header bbox area; all classes, so overlap and noise are included)

| File (sheet) | Layer | Points | Area | **Measured density** | Header notes |
|---|---|---|---|---|---|
| 77932_1392506 M-34-106-A-c-4-4-4 (covers Caryńskie point 49.166/22.618) | 2023 | 85.2 M | 1.446 km² | **58.9 /m²** | LAS 1.2 fmt 1, "VQ-780II", TerraScan; file created 2023 day 240 |
| 77932_1392545 M-34-106-A-d-3-3-3 (adjacent, NE) | 2023 | 122.0 M | 1.447 km² | **84.3 /m²** | 799 MB LAZ |
| 5063_353845 M-34-106-C-a-2-2-2 (KRON86 tile at the same point) | 2012 | 16.8 M | 1.446 km² | 11.6 /m² | LAS 1.2 fmt 3; rewritten by LAStools las2las in 2019, so the header date is not the flight date |
| 5063_354772 M-34-106-C-b-1-2-2 | 2012 | 19.2 M | 1.449 km² | 13.3 /m² | 130 MB |
| 5092_160435 M-34-81-C-c-4-4-3 | 2012 | 11.7 M | 1.414 km² | 8.3 /m² | 64 MB |
| 77514_1351363 M-34-94-A-a-2-1-4 | 2023 | 45.6 M | 1.431 km² | 31.8 /m² | 297 MB |
| 77514_1351342 M-34-82-D-c-3-4-2 | 2023 | 3.5 M | 0.412 km² (partial sheet) | 8.6 /m² | 19.5 MB |
| 82229_1697719 M-34-93-D-a-2-3-3-4 | 2025 | 15.2 M | 0.356 km² | 42.6 /m² | 124 MB |

How to read this:
- `char_przestrz` is the specification minimum, not the delivered density. Delivered density varies by a factor of up to 10 within one layer. It is higher in steep mountain tiles, probably because of strip overlap and terrain [D].
- Totals include class 12 (overlap), class 7 (noise) and all vegetation returns. **Ground (class 2) density under beech and fir forest is the number that matters, and it is unknown.** Affek 2016's dedicated April 2013 leaf-off flight achieved 12 ground pts/m² out of 25 total [V\*]. If the 2023 flight was leaf-on in summer, the ground fraction could be far lower [D]. **The first pipeline task is a one-tile QA:** class histogram, ground points per 0.5 m cell, GPS-time-derived flight dates.
- Header creation dates (2023 day 181 and day 240) are processing dates, not proof of acquisition season [D].
- Horizontal and vertical accuracy attributes: 2012 `blad_sr_wys` 0.15 m, `blad_sr_syt` 0.50 m [ORCH]; 2023 0.15 m and 0.30 m [V\*].

**What is not verified:** coverage south of 49.0 N (Tarnawa Wyżna, Sianki) and east of 22.95 E, though the bbox already reached the border; per-tile ground density; flight months; whether the 2023 and 2025 "12 p/m2" sheets are the same flight republished or a re-flight. Their extents are identical, which is suspicious [V\* extents; interpretation U].

### 3.4 Gaps

1. Ground density under forest in 2023 versus 2012 (decides D1).
2. Leaf state and season of each flight.
3. Ukrainian side (no open ALS) and parts of the Slovak side (not checked).
4. Vertical datum: tiles from KRON86 and EVRF2007 must be harmonised before differencing. [N01] claimed a difference of "a few decimetres to >1 m". **I downgrade that to [U].** My recollection is that the offset is on the order of 1-2 dm and spatially smooth, but I did not verify it. Recommendation: co-register epochs empirically on stable surfaces (paved roads, buildings) rather than relying on a datum constant.
5. Licence text: free for "any purpose" per the Geoportal LiDAR page [V, N01/N04]. The Regulamin was not read.

### 3.5 How to enumerate tiles (verified recipe)

```
Service A: https://mapy.geoportal.gov.pl/wss/service/PZGIK/DanePomiaroweLidarKRON86/WFS/Skorowidze
Service B: https://mapy.geoportal.gov.pl/wss/service/PZGIK/DanePomiaroweLidarEVRF2007/WFS/Skorowidze
GetFeature: SERVICE=WFS&VERSION=2.0.0&REQUEST=GetFeature
            &TYPENAMES=gugik:SkorowidzDanychPomiarowychLIDAR<YYYY>
            &BBOX=<latmin>,<lonmin>,<latmax>,<lonmax>,urn:ogc:def:crs:EPSG::4326
            [&RESULTTYPE=hits] [&COUNT=n]
Output geometry: EPSG:2180 with axis order (northing, easting).
Attributes used: godlo, akt_rok, akt_data (2012 only), char_przestrz, nr_zglosz, uklad_h,
            blad_sr_wys, blad_sr_syt, url_do_pobrania (direct .laz URL), modul_archiwizacji
Download: https://opendata.geoportal.gov.pl/NumDaneWys/DanePomiaroweLAZ/<id>/<id>_<feature>_<godlo>.laz
          supports HTTP Range (used for header reads) [V*]
```

Pipeline rule: store the full WFS GML/GeoJSON response per query, with a timestamp, as provenance. GUGiK republishes data, so the index can change.

### 3.6 Data volume estimates [D]

- Bytes per point in LAZ: 6.5 for 2023, about 5.5-6.7 for 2012 (from the files above).
- **Pilot (Caryńskie, about 17 km² village area [V\*, IALE poster] plus buffer, about 16-20 sheets):** 2023 about 10-16 GB; 2012 about 2-3 GB. Derived 0.5 m float32 rasters are about 16 MB/km² per product uncompressed, so about 0.5 GB for 10 products. Trivial.
- **Whole bbox, 2023 layer:** 2,387 sheets of about 1.45 km² (about 3,460 km², minus clipping) plus 608 sheets of about 0.36 km². At a measured 30-60 pts/m² that is 1-2 × 10^11 points, or **about 0.7-1.4 TB of LAZ**. The 2012 layer is about 0.1-0.15 TB.
- Processing: a 120 M-point tile is heavy in pure Python. Use per-tile ground-only extraction (class 2 plus key points), which may be 10-30% of points, then TIN-grid with a 20-30 m buffer from neighbours. A workstation with 32-64 GB RAM is enough tile by tile.
- Decision: **do not bulk-download the region before the pilot validates D1.**

---

## 4. Prior art

### 4.1 Study table

"Verified?" refers to the specific numbers in the row.

| Study | Location | Data | Method | Validation | Key results | ID / URL | Verified? |
|---|---|---|---|---|---|---|---|
| Affek et al. 2022, *Archaeological Prospection* 29(1):157-173 | 3 post-WWII abandoned villages: 2 Carpathian, 1 Sudetes | National ALS (ISOK) + mid-19th-c. cadastral maps + field survey | Interpretive mapping of boundaries, roads, agriculture, buildings | Cadastral overlay + field | 38-70% of non-natural parcel boundaries and 65-79% of cadastral roads still detectable; customised visualisations beat ready-made shaded DEMs | DOI 10.1002/arp.1846 | **[V\*]** abstract via Crossref; full text not read |
| Wolski, Latocha, Affek, Zachwatowicz, Wieczorek, IALE 2019 poster | Caryńskie (Bieszczady), Borysławka (Przemyśl Foothills), Rogóżka (Śnieżnik) | ISOK LAS 1.2, **4 pts/m² single strip**, scan angle ≤±25°, altitude accuracy ≤0.15 m | DEM **0.5 m, TIN natural neighbour** from Ground + Key points (ArcGIS + LP360); **SVF 16 directions, 10 m radius** (RVT); manual interpretation | Austrian 1:2880 / Prussian 1:5000 cadastre; field GPS mapping; interviews | Feature-class visibility table (roads, terraces, ploughing, boundaries, settlement remnants: ruins, foundations, cellars, wells). Ploughing traces and ruts visible at 0.5 m, not at 1 m. TIN better than IDW. Rule: "pixels per m² should not exceed points per m²". Errors: settlement remains classified as Building, cellars and wells as Low Point, dugouts as low/medium vegetation; "mounds" that were branch piles | igipz.pan.pl/tl_files/igipz/ZSIGiK/news/IALE_2019/poster.pdf | **[V\*]** PDF text extracted; Table 1 layout garbled, values reconstructed |
| Affek 2016, *Geographia Polonica* 89(3):415-424 | 25 km² mapped of 63.5 km² flown, Wiar basin (Posada Rybotycka, Borysławka) | **Dedicated flight, not ISOK:** MGGP Aero, 19 Apr 2013 (leaf-off), Riegl LMS-Q680i, 12 ground pts/m², 25 total; 0.5 m DTM | SVF (main), colour hillshade, LRM (Novák LRM toolbox); iterative manual interpretation; RGB ortho, intensity, post-war cadastres | Field visits, interviews, AZP, cadastre 1852/1965/2010 | Building remains: "elevated flat regular forms, usually rectangles, often with holes (former cellars) or mounds (bread oven, chimney)". Building remains **did not exactly match cadastral positions but stayed within the same parcel**. Zero features on former state-farm land afforested in the 1990s (deep ploughing). Floodplain features erased. Branch piles misread as mounds | DOI 10.7163/GPol.0062; PDF rcin.org.pl/Content/59333 | **[V\*]** PDF text |
| Wolski 2016, *Geographia Polonica* 89(3):371-387 | Western Bieszczady | Conceptual + landscape | Definition and classification of abandoned-village landscapes | - | >100 villages; about 90% of population relocated in 1944-47 and 1951; Operation H-T (1951) removed about 40 villages' inhabitants; return extremely rare | DOI 10.7163/GPol.0064 | **[V\*]** PDF text |
| Wolski (undated poster, IGiPZ) | Caryńskie, gmina Lutowiska | Fieldwork 1996, cadastre 1852 (1:2880, AP Przemyśl and Rzeszów), 1966 updates | Land-use reconstruction 1850-1996; artefact inventory | Field | Caryńskie emptied late Apr-May 1946, buildings levelled soon after. 19 field roads, 11 km, 4.6 km/km². Stone mounds; terraces. Nettle stands match cadastral house sites. **Suffosion funnels** (natural depressions) present. Populations table for about 35 villages (1921/1943/1996) | igipz.pan.pl/.../wolski_poster.pdf | **[V\*]** PDF text |
| Banasiak et al. 2022, *Remote Sensing* 14(4):995 | Białowieża Forest | ISOK ALS | U-Net semantic segmentation (archaeological, natural, modern) | Pixel-wise against ground-truth masks | **Dice/F1 0.58, IoU 0.50** overall; IoU 0.41 field banks, 0.62 plots, 0.62 barrows (after 83 epochs) | DOI 10.3390/rs14040995 | **[V\*]** Crossref abstract |
| Stereńczak et al. 2020, *Remote Sensing* 12(16):2657 | Białowieża | ALS | Interpretation + field | Field | >300 km of possible field boundaries | DOI 10.3390/rs12162657 | metadata [V]; numbers [U] |
| Białowieża feature counts (1,919 flagged, 96% confirmed) | Białowieża | ALS | ? | Field | 96% field confirmation | source unidentified | **[U] do not cite** |
| Słowiński et al. 2026, *ESSD* 18:493-506 | All of Poland (forests) | LiDAR DTM | Manual visual interpretation on a 500 m grid | Field at 7 of 9 sites, >250 features all confirmed | 634,815 relict charcoal hearths; few in mountains | DOI 10.5194/essd-18-493-2026; data 10.5281/zenodo.15630690 | [V] |
| Landauer et al. 2025, *JCAA* 8(1) | England, Hesse, Molise; hillforts | National LiDAR | ConvNeXt (ImageNet) + pseudo-labelling; 579 positive / about 20,000 negative vignettes | Known inventories + expert review | **Precision 0.26, recall 0.71, F1 0.38** (England: 305 predictions, 80 TP, 225 FP, 32 FN). Hesse: 148/169 >90%-confidence candidates obvious FPs. Molise: 85 of top 100 FPs | DOI 10.5334/jcaa.178 | **[V\*]** |
| Verschoof-van der Vaart et al. 2020 (WODAN2.0), *IJGI* 9:293 | Netherlands | AHN LiDAR | Faster R-CNN + Location-Based Ranking | Small non-random vs large random test sets | About 70% (small non-random) vs about 50% barrows, 46% Celtic fields, **18% charcoal kilns** on a large random set; **does not reach human performance** (citizen-science comparison) | DOI 10.3390/ijgi9050293 | **[V\*]** Crossref abstract |
| Peck et al. 2026, *Advances in Archaeological Practice* | Kisatchie NF, Louisiana | LiDAR DEM | Mask R-CNN on procedurally simulated objects | Field survey | High recall, low precision. Field: objects were **not** tar kilns but another historic feature class. Secondary report: 709 post-filter predictions, 686 FP, all 12 targets found | DOI 10.1017/aap.2025.10130 | qualitative **[V\*]** (Crossref abstract); numbers [V, secondary news] |
| Guyot et al. 2021, *JCAA* 4(1) | Morbihan, Brittany | LiDAR | Mask R-CNN, 150 tiles / 195 structures, random split | Random hold-out | mAP@0.5 0.29-0.77 (mean 0.50); augmentation raised 0.64 to 0.75 | DOI 10.5334/jcaa.64 | [V] |
| Bellat et al. 2025 review | Cross-field | - | Review | - | ALS in about 50% of structure-detection cases; 59% (n=31) unsuccessful or partially successful | arXiv 2501.03840 | [V] |
| Trier et al. 2021 (charcoal kilns 90% detected, 38% FP) | Norway | ALS | Faster R-CNN | ? | as stated | DOI not resolved (my guess failed; do not cite) | [U] |
| Guyot et al. 2018 (2,952 TP, 41 FP) | Brittany | LiDAR | RF on multiscale TPI | ? | as stated | mdpi 2072-4292/10/2/225 | [U] |
| Kiarszys et al. 2019, *Antiquity* | W Poland, Cold War warhead sites | ALS + archives + declassified imagery | Interpretation | Archival | Precedent for Cold War features in forest | Cambridge URL in [N02] | [U] |
| Oryński et al., EGU24-8532 | S Poland | ALS + geophysics | U-Net | Field | "Hundreds of sites" (count only) | meetingorganizer EGU24-8532 | [V] (abstract) |
| Majewska 2022, *Prace Geograficzne* 169 | **Bartki, Warmia-Masuria** (not Carpathians) | ISOK | TPI, TRI, openness | ? | Comparable method, different region | - | [U] |

### 4.2 Where we would be novel and where we would duplicate

| Aspect | Duplicative | Plausibly novel |
|---|---|---|
| Caryńskie, Borysławka, Posada Rybotycka feature maps | Yes: published interpretations exist (2016 map, 2019 poster, 2022 paper). Use them as **validation**, not as results. | Only if 2023 dense data reveals feature classes the 2012-13 data could not: cellars, wells, small platforms. |
| Region-wide inventory of the roughly 100+ Western Bieszczady villages (Wolski poster lists about 35 in gmina Lutowiska alone) | No public, georeferenced, feature-level inventory found [N02 §3.2; my search] | **Yes. This is the main contribution.** |
| Use of the 2023 and 2025 acquisitions | All published Bieszczady studies predate them | Yes. It needs the QA in §3.3. |
| Two-epoch (2012 to 2023) comparison | Not found | Yes: detecting post-2012 forestry damage to features is a heritage-monitoring product. |
| Automated or ML detection of house remains in Carpathian forest | Not found for this region (search 2026-11-12) | Yes, but expect modest precision. |
| Open pipeline with provenance, known-check log and per-village cause record | Not found | Yes (method contribution). |

**Duplication risk to manage:** IGiPZ PAN may hold unpublished inventories, for example Wolski's 1996 fieldwork and the PRELUDIUM 2013-16 project. Ask them first. This is both courtesy and the HN lesson.

### 4.3 The known-villages problem: what "discovery" can mean here

- The villages themselves are documented. Wolski's poster tabulates about 35 villages of gmina Lutowiska with populations for 1921, 1943 and 1996 [V\*]. Austrian cadastral maps from 1852 exist at 1:2880 in AP Przemyśl and Rzeszów [V\*, Wolski poster]. PRNG still lists Caryńskie and Nasiczne as official localities of type "osada" [V\*, live PRNG WFS]. Wikidata types most of them as plain "wieś w Polsce", not "former settlement" [V\*]. So **a gazetteer entry does not imply an inhabited village, and a gazetteer query cannot list the emptied villages.**
- What is plausibly unknown, at least in any georeferenced public form:
  (a) the exact positions and count of house platforms, cellars, wells, ovens, roads, terraces, field boundaries, cemeteries and church or chapel outlines in each village;
  (b) small units: hamlets ("przysiółki"), forest colonies, sawmill or railway settlements, shepherd and forestry posts. These appear on WIG 1:100k/1:25k sheets or cadastral maps but not in modern gazetteers;
  (c) features of war and post-war conflict: UPA hideouts and bunkers, military posts, trenches. These are **highly sensitive** (§8);
  (d) post-2012 damage to features (two-epoch).

### 4.4 Discovery tiers and evidence required

Two independent axes. A candidate is reported as e.g. "A2/T1".

**Axis A: is it an anthropogenic feature of the relevant period?**

| Level | Meaning | Minimum evidence |
|---|---|---|
| A0 | Morphometric candidate | Detector or rule output only |
| A1 | Plausible feature | Reviewer judges it consistent with a feature class on ≥2 visualisations (e.g. SVF + LRM) **and** a profile. Not explained by a known FP class (§7) |
| A2 | Probable period feature | A1 **plus** spatial context: inside a cadastral or WIG settlement area, in a farmstead row or on a road network, **or** visible in both epochs (2012 and 2023, which excludes ephemeral artefacts) |
| A3 | Confirmed | A2 **plus** field verification (photo, GPS, description) by a qualified person with permission, **or** an archival document that locates that specific object |

**Axis T: is it already known?**

| Tier | Meaning | Required checks (all logged, §6) |
|---|---|---|
| T0 | Known and visible: already registered, published or mapped as that feature | Match in NID register, AZP, published maps (Affek, Wolski), OSM, Wikidata, BdPN inventories |
| T1 | Known settlement, newly mapped feature | The settlement is known, but this feature is not in any checked feature-level source |
| T2 | Settlement or hamlet absent from modern gazetteers (PRNG, Wikidata, OSM), present on historical maps | T1 checks **plus** PRNG M1/M2 name and position search, Wikidata, OSM, **and** a positive match on cadastre, WIG or Austrian survey sheets |
| T3 | Not in any source we checked | T2 checks **plus** negative results on historical maps, the literature search (Polish, Ukrainian, English) and an expert query (IGiPZ PAN or WKZ). The default assumption is a check failure, not a discovery |

Reporting rule: **T1 needs ≥A2; T2 or T3 needs A3, or A2 with an expert's written opinion.** No "discovery" wording is used in public for anything below A2/T1.

---

## 5. Detection approach options

### 5.1 Options compared

| Option | What it is | Expected performance (evidence) | Cost | Main risk | Verdict |
|---|---|---|---|---|---|
| O1 Manual visual triage | Experts scan SVF, LRM, VAT tiles on a grid (Słowiński-style 500 m cells) | The de facto standard in all Polish studies [V\*, Affek 2016; V\*, poster; V, Słowiński]. WODAN2 did not reach human (citizen-science) performance [V\*] | About 1-3 reviewer-hours/km² at feature level [D, guess] | Reviewer fatigue and inconsistency; does not scale to 3,000+ km² | **Baseline and ground-truth generator** |
| O2 Classical morphometric rules | LRM/SVF thresholds, closed-depression detection (cellars, wells), rectangle fitting on positive LRM (platforms), linear-feature tracing (hollow ways, terraces), clustering | No direct published metrics for this feature set. Trier & Pilø 2012 (pits, Norway) is a precedent [U]. Guyot 2018 RF on TPI is strong [U] | Cheap, transparent | Many natural confusers (§7) | **First automatic stage: high-recall candidate generator** |
| O3 Supervised DL (U-Net, Mask R-CNN, YOLO) | Trained on labelled features | Banasiak: F1 0.58 pixel-wise in Białowieża [V\*]. Landauer: precision 0.26 at recall 0.71 [V\*]. WODAN2: 18-50% on realistic random tests [V\*]. Peck: high recall, low precision, wrong class identity [V\*]. Bellat: 59% of studies unsuccessful or partial [V] | Needs ≥ several hundred labels, a GPU, careful spatial CV | Overfitting to the pilot valley; illusory scores from random splits [V, N03 §3.1] | **Phase 2, after labels exist** |
| O4 Weak labels from cadastral and WIG maps | Use 1852 building symbols, roads and parcel lines as noisy labels | Affek: building remains are within the parcel but not at the mapped spot [V\*]. Affek 2014 reports systematic ALS-vs-map displacement [U]. Point labels are therefore wrong by metres to tens of metres | Moderate (digitising, georeferencing) | Label noise mistaken for model error | **Use for area-level weak supervision** (multiple-instance: "this parcel contains ≥1 building remain"), and for priors in ranking. Not as pixel masks |
| O5 VLM or LLM-agent triage (the Maya approach) | Show rendered tiles to a VLM with a written guide; ask for features and confidence | **No evaluation found for temperate-forest micro-relief.** Landauer & Klassen 2025 zero-shot claims are [U]. The Maya post gives no metrics and produced a rediscovery [V\*] | Per-tile API cost; time | Confident hallucination; persuasion of the operator; non-reproducibility across model versions | **Optional ranker or second reader**, only after O1/O2 baselines exist, benchmarked on the labelled pilot with fixed prompts and model IDs. Never decides novelty |
| O6 Hybrid (recommended) | O2 generates candidates → known-check → O1 human review (optionally with an O5 second reader) → labels feed O3 → O3 replaces part of O2 | Best supported by the evidence: every high-performing published system keeps humans in the loop (Landauer explicitly requires human verification [V]) | Staged | Process complexity | **Adopt** |

### 5.2 Quantitative evidence, with confidence

| Claim | Number | Confidence |
|---|---|---|
| Cadastral boundaries / roads persisting in LiDAR | 38-70% / 65-79% | High [V\*] |
| DL hillfort precision / recall, national scale | 0.26 / 0.71 | High [V\*] |
| DL hillfort top-confidence FP share (Hesse, >90% confidence) | 148/169 = 88% | High [V\*] |
| U-Net pixel F1 on Polish ALS archaeology | 0.58 (IoU 0.50) | High [V\*] |
| DL on a realistic random test (Netherlands) | 18-50% by class | High [V\*] |
| Simulated-training detector (Louisiana) | 686/709 FP after filtering | Medium [V, secondary] |
| Charcoal kiln DL in Norway: 90% detected, 38% FP | - | Low [U] |
| Manual LiDAR features later confirmed in the field (charcoal) | all of >250 visited | Medium [V] (feature type is easy) |
| Białowieża 96% field confirmation | - | **Do not use** [U] |

Implication [D]: assume a candidate generator plus DL ranking yields **≤0.3 precision at useful recall** in this region at first. Plan reviewer capacity accordingly. At 3,000 km² and an assumed 5-20 candidates/km² after filters, that is 15,000-60,000 candidates. Review must be sampled and ranked, not exhaustive.

### 5.3 Candidate rule set for O2 (design, to be tuned) [D]

Feature signatures come from Affek 2016 Table 2 [V\*] and the poster [V\*]. All thresholds are placeholders.

| Rule | Target | Signature |
|---|---|---|
| R1 Cellar / well | Closed depression | Depth 0.3-2.5 m; area 4-60 m²; compact or rectangular. Wells are smaller and round. Often inside or next to R2 |
| R2 House platform | Flat raised or terraced rectangle | Positive LRM 0.1-1 m; 6-20 × 4-12 m; low internal slope; often an internal pit (cellar) or mound (oven, chimney) |
| R3 Hollow way | Linear depression | Width 1.5-6 m, depth 0.3-3 m, length >50 m; often parallel braids; climbs slopes (Affek: up to 3 m deep, 1.5 m wide) |
| R4 Agricultural terrace / field boundary | Linear break of slope along contours | Repeated parallel scarps 0.3-3 m high; strip pattern perpendicular to the valley ("łanowy" layout) |
| R5 Farmstead row | Cluster | ≥3 R1/R2 within 30-80 m spacing along a valley-floor axis or road (R3). This is the Maya-thread "co-occurrence" idea |
| R6 Church / cemetery | Enclosure | Rectangular bank or ditch 20-80 m; slight rise; often old trees (not visible in a DTM; use the 2023 DSM or first returns) |
| R7 Stone mound | Small mound | 0.3-1 m high, 2-6 m across, at parcel corners (Wolski) |

The 2023 point cloud also allows **non-ground cues**: old orchard trees and house-plantings (sycamore, ash, spruce) mark farmsteads [V\*, Wolski poster]. A canopy-structure layer from first returns may add signal. Untested idea [D].

### 5.4 Labels and training data strategy [D]

1. **Pilot ground truth (hand-labelled):** Caryńskie (about 17 km²) and Borysławka (about 7.9 km²) [V\* areas]. These are the two villages with published interpretations to compare against. Label features as points plus polygons with class, confidence and visualisation used. Two independent labellers on a 20% overlap sample give inter-annotator agreement, which is the realistic ceiling for any model.
2. **Weak labels:** georeference 1852 cadastral sheets (AP Przemyśl Fond 126 scans, §6.2). Derive parcel polygons with "building present" flags. Use them as bag-level labels and as ranking priors (a candidate inside a building parcel scores higher).
3. **Negatives:** explicit confuser samples (§7): windthrow pit-mound pairs, suffosion funnels, landslide scarps, skid trails, slash piles, charcoal hearths. Collect them during the O1 review as a by-product.
4. **Pseudo-labelling:** follow the Landauer approach only after a first model exists [V].
5. **Synthetic insertion:** Peck-style procedural cellars and platforms inserted into real DTMs. Useful for recall, dangerous for class identity [V\*]. Use only for pre-training.
6. **Spatial cross-validation:** **leave-one-village-out** (Caryńskie ↔ Borysławka ↔ a third blind village, e.g. Tworylne or Krywe in the San valley). Within a village, use ≥1 km spatial blocks with a buffer of at least the visualisation radius, since SVF and LRM leak context. Report per-village recall per feature class, precision@k (k = 50, 100, 200), FP/km², and reviewer minutes per confirmed feature. Never report random-split scores alone [V, N03 §4.3].

---

## 6. Novelty / known-check design

### 6.1 Sources to compare against

| Source | What it holds | Access (as checked) | Join method | Weight |
|---|---|---|---|---|
| NID archaeological register | Registered archaeological sites | **WMS works:** `https://usluga.zabytek.gov.pl/INSPIRE_AMD/Service.svc/get?` layer `Archaeological_Monuments`, EPSG:2180 [V\*]. No WFS found [V\* search] | GetFeatureInfo or visual overlay per candidate. Rate-limit and log | High (T0) |
| NID immovable monuments register | Churches, cemeteries | WMS `INSPIRE_IMD` responds [V\*] (layers not inspected); dane.gov.pl export said to lack coordinates [U, OSM forum] | Overlay + name match | High |
| AZP (Archeologiczne Zdjęcie Polski) | Surface-survey sites by AZP sheet | **Not openly accessible** [U]; probably via WKZ or NID on request. Forest coverage is weak [U] | Request sheet data for pilot AZP areas | High if present; absence is weak evidence |
| Published maps: Affek 2016, Affek et al. 2022, poster, Wolski | Feature maps for 3-4 villages | PDFs (2016, poster: read) [V\*]; 2022 paywalled | Digitise figure maps (georeference) | High (T0 for features) |
| BdPN yearbook inventories (cemeteries, churches) | Cemetery condition | PDFs on archiwum.bdpn.pl [U] | Manual | High |
| PRNG (official names) | Official localities incl. "osada" status for former villages | **WFS works:** `.../PZGiK/PRNG/WFS/GeographicalNames`, layers `ms:M1_UrzedoweNazwyMiejscowosci`, `ms:M2_PozostaleNazwyMiejscowosci`, plus physiographic layers O1-O3; attributes include `RODZAJOBIEKTU`, `NAZWYHISTORYCZNE`, `IDENTYFIKATORSIMC` [V\*] | Name and position within 2 km | Medium (settlement-level T2 test) |
| Wikidata | Villages, cemeteries, non-existent churches with coordinates | SPARQL works; bbox query gives 1,337 items, incl. 19 cemeteries, 11 "była miejscowość", 6 "nieistniejący obiekt budowlany" [V\*] | Spatial query; class-based filters miss most former villages | Medium |
| OSM | Ruins, cemeteries, wayside shrines, tourist "former village" signs | Overpass (not tested) [U]; ODbL | Spatial | Medium |
| Słowiński 2026 charcoal hearth dataset | Hearth points | Zenodo 10.5281/zenodo.15630690 [V] | Spatial (explains mounds) | FP explainer |
| 1852 Franciscan cadastre for Galicia | Buildings, parcels, roads | AP Przemyśl Fond 126 scans (skany.przemysl.ap.gov.pl) via the Gesher Galicia inventory; Gesher stitched maps exist for some villages (e.g. Bystre 1852, Bircza Stara 1852) [U, search results; Bieszczady coverage not checked] | Georeference (Affek: expect displacement) | T2 evidence; A2 context |
| FRANZI (Austria) | Franciscan cadastre protocols, Austria only | Freely accessible; CC0 on Zenodo; only Tyrol georeferenced [V\*] | **Not applicable to Galicia** | - |
| WIG 1:100k / 1:25k (1930s) | Interwar settlement state | Sheet scans exist (e.g. McMaster index, mapywig archive) [U]; "Maps with the Past" suspended [U] | Georeference | T2 evidence |
| Habsburg military surveys (Mapire / Arcanum) | 1780s, 1806-69 | Mapire returned 403 [V, N04]; WMTS claimed [U] | Visual | Context |
| Historical aerial photos 1951+ / 1960s | Last built state | PZGiK ordering [U] | Visual | A2 context |
| Literature search (PL/UA/EN) | Theses, regional journals, Magurycz, tourist guides | Manual + LLM-assisted retrieval with logged queries | Text | **Mandatory** (the HN lesson) |
| Expert query: IGiPZ PAN (Affek, Wolski), WKZ Przemyśl, BdPN | Unpublished knowledge | Email | - | Required for T2/T3 |

### 6.2 Procedure and scoring [D]

For each candidate (or candidate cluster), compute and store:

```
known_hits = [
  {source, source_version_or_date, query, match_type: exact|within_buffer|name|none,
   distance_m, matched_object_id, checked_at, checked_by(human|script|llm+model_id)}
]
```

- Buffers: feature-level sources 15 m (plus the source's positional uncertainty); settlement-level sources 500 m inside the cadastral village extent, or 2 km for name-only sources.
- `T = T0` if any feature-level source matches; `T1` if only settlement-level sources match; `T2` if no modern gazetteer matches but a historical map does; `T3` otherwise.
- `coverage_score` = sum of weights of sources actually checked ÷ sum of all weights. **A tier is only valid if coverage_score ≥ 0.8.** Otherwise the tier is "unresolved". This makes "we didn't look" visible.
- An LLM may propose literature hits. A human confirms each hit or non-hit. The LLM's absence-of-evidence is never recorded as "none".

### 6.3 Addressing the HN lesson explicitly

The Maya failure had two parts. The agents' literature search missed a 2025 paper, and the official register also lacked the site [V\*]. Our design answers both: (1) the literature check is a mandatory, logged step with human confirmation; (2) register absence carries low weight; (3) we query experts before any T2/T3 claim; (4) the default public framing is "newly mapped features of a known village" (T1), which is true even when we miss a source.

---

## 7. Candidate false-positive taxonomy for Carpathian forest

| Class | Looks like | Distinguishing cues | Source |
|---|---|---|---|
| Windthrow pit-mound pairs | Cellar (pit) and platform or mound | Paired pit + mound on the downslope or downwind side; random orientation and spacing; no cluster on a road axis | Affek 2016 "fallen tree pits" [V\*]; Forest Research note [U] |
| Slash or branch piles | Mounds, platforms | Not in the 2012 epoch, or changed between epochs; near skid trails; first returns above the "ground" | Affek 2016, poster [V\*] |
| Suffosion funnels (piping, Krosno beds) | Cellars or wells | Round, often in rows along subsurface drainage, on slopes; no rectangular form | Wolski poster [V\*] |
| Landslides, scarps, ravines, abandoned channels | Terraces, hollow ways | Arcuate scarps, lobes; follow geology and streams rather than parcel strips | Affek 2016 [V\*] |
| Logging roads, skid trails, forest vistas ("linie oddziałowe") | Hollow ways | Straight compartment lines about 4 m wide (Affek lists forest vistas as a pre-war class too); modern skid trails are wider, with machine-track ruts and fresh in 2023 vs 2012 | Affek 2016 [V\*]; Landauer (forest paths) [V\*] |
| Post-war collective-farm features (PGR, sheep folds 1960s-70s) | Platforms, enclosures | Mapped on 1965/1966 cadastre updates; concrete; larger regular forms | Affek 2016, Wolski poster [V\*] |
| Deep-ploughed afforestation (1990s) | Destroys or creates linear ridges | Regular parallel furrows over large blocks | Affek 2016 [V\*] |
| Relict charcoal hearths | Platforms (flat, round) | Round 8-15 m flat platforms with a ditch; check the Słowiński dataset | Słowiński [V] |
| Quarries, borrow pits | Pits | Irregular, deep, at outcrops or roadside | Landauer (quarries) [V\*]; IALE table (mining) [V\*] |
| WWI trenches and positions (1914-15 Carpathian front), WWI cemeteries | Linear ditches, enclosures | Zigzag trenches on ridges and passes; documented WWI cemeteries (e.g. near Użok) | [U, domain knowledge; one WWI cemetery near Uzhok in Wikidata, V\*] |
| WWII and 1944-47 features: front lines, dugouts, UPA hideouts, KBW/WOP posts | Pits, platforms | Small rectangular pits in remote forest, on slopes, outside cadastral settlement areas. **Sensitive; may hold human remains or UXO** | Poster lists "dugouts" misclassified as vegetation [V\*]; UXO finds near Otryt [U, N04] |
| Cold War border infrastructure | Linear, platforms | Along the state border strip | [U] |
| Shell and bomb craters, UXO | Cellars or wells | Round, raised rim, clustered | [U]; a safety issue too |
| Wild boar rooting | Surface roughness | Usually sub-resolution and ephemeral; differs between epochs | [U] |
| Beaver dams and ponds | Linear banks in valleys | On streams, water-filled; recent | [U] |
| 19th-20th c. oil pits ("kopanki", Ustrzyki and Lesko area) | Rows of pits | Clusters on the oil belt, spoil heaps | [U, domain knowledge] |
| Forest narrow-gauge railway (Bieszczady forest railway) embankments | Roads, terraces | Constant gradient, long curves | [U] |
| DTM artefacts: misclassified ground, TIN slivers under dense young conifers | Any small form | Low ground-point density mask; not reproducible between epochs | Poster (classification errors) [V\*]; Affek 2016 (no pulses through young conifers) [V\*] |
| Tourist infrastructure: shelters (e.g. Koliba at Przysłup), trails, ski | Platforms, roads | Mapped in OSM | Wolski poster [V\*] |

Mitigations [D]: a ground-density mask (refuse candidates where ground points per cell are below a threshold); two-epoch persistence as an A2 cue; an explicit confuser class in labels; OSM and BDOT10k overlays for modern features.

---

## 8. Legal, ethical and sensitivity framework

### 8.1 What the consolidated Monuments Act says (Dz.U. 2024 poz. 1292, read via api.sejm.gov.pl) [V\*]

- **Art. 35:** archaeological monuments that are discovered, found by chance, found through searches (art. 36b) or obtained through archaeological research are owned by the State Treasury.
- **Art. 32:** whoever, during building or earthworks, discovers an object presumed to be a monument must stop work, secure it, and notify the WKZ (or the mayor or wójt).
- **Art. 36 ust. 1 pkt 5:** archaeological research requires a WKZ permit. **Pkt 12** (searching with electronic or technical devices) is **repealed**. In the text it is marked as valid until the 2023 amendment entered into force, and the 2023 amendment entered into force on **1 May 2025**.
- **Art. 36b** (new): an adult may search for hidden or abandoned movable monuments with electronic or technical devices **with consent of the property owner and possessor and after registering the search** in the ministry's mobile application. The registration gives the dates and area.
- **Art. 36c** (new): searching is **prohibited** in registered or recorded ("ewidencja") monuments and within 10 m of them; in historic monuments; in cultural parks; at UNESCO sites; at European Heritage Label sites; in **cemeteries, former cemeteries, war graves and places of execution**; at Holocaust memorials; and in areas under an archaeological permit application. Ust. 3: the searcher must **stop and notify** on finding human remains or dangerous items, especially explosives.
- **Art. 109c is repealed. Art. 109d** (searching contrary to art. 36c) **and 109e** (searching without registration) carry a fine, restriction of liberty, or up to 2 years' imprisonment.
- Not read: amendments Dz.U. 2025 poz. 1168, 2025 poz. 1673 (in force 2026-06-03 per the ELI API), and 2026 poz. 483. **They may change the above.**

### 8.2 Points that MUST be confirmed with a lawyer and/or the WKZ

1. Desk-based analysis of public LiDAR: does it fall under "poszukiwania" (art. 36b) or "badania archeologiczne" (art. 36 ust. 1 pkt 5)? My reading is no, because no device is used in the field. This is unverified.
2. Whether a field visit for **visual inspection and GPS photography only**, with no detector and no probing, is lawful in (a) state forests, (b) Bieszczady National Park, (c) Park Krajobrazowy Doliny Sanu, and (d) Natura 2000 sites. National park off-trail rules come from the Nature Conservation Act and the park's regulations. I did not read them; [N04] could not read the BdPN Regulamin.
3. Whether there is a **duty to notify the WKZ** of a remotely identified probable archaeological site. Art. 32 covers discovery during works. Is there a general duty for remote identification? Also whether the planned "notify WKZ before publication" practice suffices.
4. Whether publishing coordinates of unregistered sites, or of former cemeteries (where searching is banned under art. 36c), creates liability or conflicts with conservation policy.
5. Licence of GUGiK derived products (DTM, visualisations) for public redistribution: the Regulamin and the Prawo geodezyjne provisions.
6. Database rights and licences for the cadastral scans (AP Przemyśl), Gesher Galicia stitched maps, WIG scans and Mapire.
7. Effects of the 2025-2026 amendments listed in §8.1.
8. Rules for handling found human remains or UXO: police, sappers, Border Guard advisories [U, N04].
9. GDPR-type concerns if publishing interviews or family names of former inhabitants.

### 8.3 Community and political sensitivities

- **Cause of depopulation is contested and plural.** Record per village, with sources: 1939-41 Soviet border actions; 1944-46 "evacuation" to the Ukrainian SSR; 1946 forced expulsions (Caryńskie: Apr-May 1946 [V\*]); 1947 Operation Vistula; 1951 Operation H-T (about 40 villages [V\*]); destruction by fighting or burning; later depopulation. Never label the whole map "Operation Vistula villages".
- Narratives differ: Ukrainian and Lemko descendants vs Polish (UPA-violence framing) [V, N04 §7 via lemko.org and Wikipedia]. The site should describe events with sources, not assign blame per village.
- **Graves and cemeteries:** Greek Catholic, Orthodox, Jewish, Roman Catholic and military. Exact locations stay non-public unless already public and protected. Coordinate with Magurycz and similar stewards [U].
- **UPA hideouts and 1944-47 conflict features:** they may contain human remains and are politically charged. Treat them as tier-3 (non-public) by default.
- Jewish heritage: Jewish communities of the Bieszczady were murdered in 1942 [V\*, Wolski 2016]. Jewish cemeteries in Lutowiska, Cisna, Baligród and elsewhere appear in Wikidata [V\*]. They carry religious-law sensitivities about disturbance.
- The descendant communities (Ukrainian, Lemko, Boyko diaspora) are stakeholders. Plan consultation and a correction channel.

### 8.4 Tiered disclosure (refines [N04 §8]) [D]

| Tier | Audience | Content |
|---|---|---|
| P0 internal | Project team | Everything, incl. raw candidates and exact coordinates |
| P1 partners (agreement) | WKZ Przemyśl, NID, BdPN, IGiPZ PAN | Exact coordinates, A/T ratings, evidence packets. **WKZ notified before any public release** |
| P2 public, village level | Everyone | Village points already public (Wikipedia, PRNG, published papers), cause records with sources, generalised relief imagery (see §11) |
| P3 public, aggregated features | Everyone | Counts of features per village or per hex cell (e.g. ≥1 km² cells); no feature points. Exceptions: features already public and protected (e.g. registered church ruins) |
| Never public | - | Cemeteries and graves not already public; conflict features (bunkers, hideouts); UXO-risk sites; any A3 site the WKZ asks to withhold |

Relief imagery itself reveals features at full resolution. Public tiles should be (a) capped at about 1 m effective resolution or (b) masked inside sensitive polygons. This trades scientific openness against protection. Open question Q4.

---

## 9. Tooling and stack (Windows, Python)

### 9.1 Facts

| Item | Fact | Tag |
|---|---|---|
| rvt-py on PyPI | 2.2.3, `requires_python <3.12,>=3.6`; deps numpy, scipy, gdal, matplotlib, pandas, geopandas, jupyter, rasterio | [V\*] |
| rvt-py source | GitHub master active (commits Aug 2026). `rvt/__init__.py` is empty. **`rvt/vis.py` imports only numpy and scipy** (SVF, openness, SLRM, MSRM, MSTP, local dominance, sky illumination, hillshade). `rvt/default.py` and `rvt/tile.py` import `osgeo.gdal`. Licence Apache-2.0 | [V\*] |
| PDAL on PyPI | 3.5.5 sdist only, no Windows wheel | [V, N03] |
| PDAL on conda-forge | `pdal` 2.10.2 has win-64. **`python-pdal` 3.5.5 has win-64 builds for py310-py315** | [V\*] |
| lazrs (LAZ backend for laspy) | 0.8.2 wheels cp39-cp314 | [V\*] |
| laspy, rasterio, geopandas, torch, ultralytics, sklearn | Resolve for cp314 win_amd64 (resolution only) | [V, N03] |
| fiona | Did not resolve for cp314; use pyogrio | [V, N03] |
| numba on 3.14 | Not checked | [U] |
| PDAL `writers.gdal` | No TIN output (min, max, mean, idw, count, stdev) | [V, N03] |
| TIN beats IDW for 0.5 m relief visualisation | Poster Fig. 4 | [V\*] |

### 9.2 Recommendation

**Primary: pixi workspace (conda-forge), Python 3.12, Windows native.**
- Why: one lockfile; PDAL, GDAL and PROJ binaries from conda-forge; PyPI packages via pixi's uv integration; reproducible on Windows and Linux. Python 3.12 is the conservative choice where numba, torch, rasterio and python-pdal are all mature [D; per-package 3.12 builds probable but not each verified].
- conda-forge: `python=3.12 pdal python-pdal gdal rasterio pyogrio geopandas pyproj shapely laspy lazrs-python numba scipy scikit-image duckdb pyarrow`. Verify the `lazrs-python` package name on conda-forge, or use pip `lazrs`.
- PyPI: `rvt-py` **installed from the git tag with `--no-deps`**, importing only `rvt.vis` and `rvt.blend_func`; or vendor `vis.py` under Apache-2.0 with attribution. `torch` (CUDA wheel index), `segmentation-models-pytorch` and `ultralytics` in a separate optional `ml` feature.
- Change `pyproject.toml` `requires-python` from `>=3.14` to `>=3.12,<3.14` (or manage Python through pixi). The 3.14 pin is a stub [ORCH] with no dependency need.

**Fallback: uv-only, Python 3.12, no PDAL.** laspy+lazrs for reading. Ground class from the vendor classification (class 2). TIN gridding with `scipy.spatial.Delaunay` + `LinearNDInterpolator` per tile with buffers. rasterio for COG output. Vendored `rvt.vis`. This loses SMRF/CSF re-classification. That is acceptable if the vendor ground class proves good in QA.

**Alternative: WSL2 Ubuntu + conda-forge.** Use it if Windows PDAL proves painful. Data then lives on the Linux filesystem; cross-filesystem IO is slow [U].

### 9.3 Implement ourselves (small, testable) [D]

- Per-tile buffered processing (neighbour-tile ground points within 30 m) to avoid edge artefacts in SVF and LRM.
- Ground-density raster (class 2 points per cell) as a mandatory QA mask.
- TIN gridding of ground points to 0.5 m: PDAL `filters.delaunay` + `filters.faceraster` if available in the conda build (not verified), else scipy.
- Two-epoch co-registration: vertical offset and tilt fit on stable surfaces; output a difference raster.
- Fast SVF and openness: `rvt.vis` first. If too slow on 0.5 m tiles of about 1.2 km (about 5.8 M px), use a numba kernel (16 directions × R = 10 m = 20 px is cheap).
- Simple LRM (Hesse-style): Gaussian or mean low-pass difference with purged break-lines. MSRM from rvt.
- Candidate extraction (R1-R7) with scikit-image (regionprops, `morphology.h_minima`) and shapely.
- WFS client, downloader with HTTP Range resume and SHA-256, provenance writer.

---

## 10. Proposed pipeline architecture

### 10.1 Stages

| Stage | Input | Output (format) | Notes |
|---|---|---|---|
| S0 AOI + config | `config/*.yaml` | Resolved config with hash | Pydantic schema; every run records the config hash |
| S1 Tile index | AOI polygon | `catalog/tiles.parquet` (GeoParquet: godlo, layer, year, url, nominal density, datum, WFS response hash) + raw GML archive | Both services, all year layers |
| S2 Download | tiles.parquet | `raw/laz/<service>/<year>/<godlo>.laz` + `.sha256` | Range-resume; never modify raw |
| S3 Point-cloud QA | LAZ | `qa/<tile>.json` (class histogram, ground density stats, GPS-time range converted to dates, return stats) + `qa/<tile>_gdens.tif` | Decides D1; flags low-density tiles |
| S4 Ground DTM | LAZ + neighbours | `dtm/<epoch>/<godlo>_0p5m.tif` (COG, float32, EPSG:2180, explicit vertical datum tag) | Vendor class 2 (+ optional SMRF/CSF re-run); TIN |
| S4b Epoch harmonisation | Two DTMs | `dtm/diff/<godlo>.tif`, `coreg/<godlo>.json` | KRON86 → EVRF2007 empirical |
| S5 Visualisations | DTM | `vis/<product>/<godlo>.tif` (SVF r10 d16, positive/negative openness, SLRM r10/r20, MSRM, multi-hillshade, VAT/CVAT) as COG + 8-bit previews | Parameters in config. Start with the poster's SVF (16 directions, 10 m) [V\*] |
| S6 Candidates | Vis + DTM | `candidates/raw.parquet` (point + polygon WKB, rule ID, morphometrics, scores) | O2 rules; later O3 model inference |
| S7 Context features | Candidates + layers | Enriched candidates (inside cadastral village? distance to hollow way? cluster ID? epoch persistence? ground density) | Cadastral layers once georeferenced |
| S8 Known-check | Candidates + sources | `knowncheck/hits.parquet`, tier per candidate + coverage_score | §6; external queries cached with timestamps |
| S9 Review | Ranked queue | `review/labels.parquet` (labeler, time spent, A-level, class, notes, screenshots) | Simple local web UI (§10.4) |
| S10 Training (phase 2) | Labels + vis | Model artefacts + metrics per spatial fold | Leave-one-village-out |
| S11 Export | Reviewed candidates | Tiered GeoJSON/PMTiles for P1/P2/P3 | Applies disclosure rules automatically |

### 10.2 Storage layout

```
data/                       (gitignored; may live on a separate drive)
  raw/wfs/<date>/<service>_<year>_<bboxhash>.gml
  raw/laz/<service>/<year>/<godlo>.laz(.sha256)
  interim/qa/ dtm/ vis/ diff/
  sources/ cadastre/ wig/ prng/ wikidata/ osm/ nid/   (each with fetch-date folder + README)
catalog/  tiles.parquet  runs.duckdb
outputs/  candidates/ knowncheck/ review/ exports/<tier>/
config/   aoi/*.geojson  pipeline.yaml  rules.yaml  sources.yaml
src/lidar_discovery/  (wfs.py, download.py, qa.py, dtm.py, vis.py, candidates.py, knowncheck.py, review_app/, export.py)
```

### 10.3 Resumability and provenance

- Each per-tile task is idempotent. Its output carries a sidecar `*.prov.json`: stage, code version (git SHA), config hash, input file hashes, library versions, wall time. A task re-runs only if an input hash or config hash changes (make-like). A small custom runner is enough. Snakemake is an option but adds Windows friction [U].
- **Candidate ID** = hash(epoch, godlo, rule, rounded centroid to 0.5 m, run ID). A separate **stable feature ID** links candidates across runs and epochs by spatial matching, so re-runs do not lose review history.
- Every candidate record holds its full lineage: tile URLs and dates, DTM parameters, visualisation parameters, detector version or model checkpoint hash, known-check log, every review action (who, when, what), and the disclosure tier decision with its reason.
- `catalog/runs.duckdb` indexes runs and lets us query "all A2+ cellars detected with SVF params X in 2023 data".

### 10.4 Review tool (minimal) [D]

A local web page (FastAPI, or a static page with a small server) with: side-by-side SVF / LRM / openness / hillshade / ortho chips; a profile line; a 2012-vs-2023 toggle; class buttons including "FP: <class>"; A-level selection; known-check panel. Keyboard-driven, with time per decision logged. Optional "VLM second opinion" button that stores model ID, prompt hash and output, hidden from the reviewer until they have decided, to avoid anchoring.

### 10.5 Minimal first milestone (M1): Caryńskie pilot

Scope:
1. AOI: Caryńskie village area (about 17 km² [V\*]), centred about 49.166 N, 22.618 E, plus a 300 m buffer. Note: inside BdPN, so no field checks without park permission.
2. S1-S5 on **both** 2012 and 2023 epochs.
3. **QA gate:** report ground density per epoch under forest. If 2023 ground density is no better than about 2× that of 2012, revisit D1.
4. Hand-label ground truth in the village core (target ≥300 features over all classes) using O1, blind to the published maps. Then compare with the poster's features and the Wolski inventory (19 roads, 11 km [V\*]).
5. Run the O2 rules. Measure recall per class against the labels, precision@k, FP/km².
6. Known-check dry run: compute tiers for all labelled features using the sources in §6.1 that are available now (NID WMS, PRNG, Wikidata, OSM, published figures).
7. Write a pilot report (methods, numbers, failure cases) and send it to IGiPZ PAN for comment.

Then **M2:** Borysławka (outside the High Bieszczady, 2012-14 and 2023 coverage; Affek 2016 map for comparison) as the leave-one-village-out test. Then **M3:** a blind village with no published LiDAR map (e.g. Tworylne or Krywe in Park Krajobrazowy Doliny Sanu, where field access is less restricted [U]).

### 10.6 Success metrics

| Metric | M1 target (tentative) [D] |
|---|---|
| Ground pts per 0.5 m cell under forest (median, 2023) | ≥1 (poster rule: pixels ≤ points) |
| Recall of hand-labelled cellars and house platforms by O2 rules | ≥0.7 |
| Recall of hollow ways (length-weighted) | ≥0.8 vs the Wolski 11 km |
| Precision@100 of ranked candidates | ≥0.3 (published DL reality ≈0.26) |
| FP per km² after the ground-density mask | Report; aim to halve with two-epoch persistence |
| Reviewer minutes per km² | Report (drives scaling feasibility) |
| Inter-annotator agreement (Cohen's κ or F1 between labellers) | Report. This is the ceiling for any model |
| Known-check coverage_score per candidate | ≥0.8 for all reported candidates |
| Fully reproducible re-run from raw | Yes (hash-identical DTM) |

---

## 11. Dissemination stage outline

- **Stack [D]:** static site (Astro or plain Vite) + **MapLibre GL JS** + **PMTiles** on static hosting (object storage or GitHub Pages). Vector layers in PMTiles; relief in raster PMTiles or COG via a tile function. No server-side database for the public site.
- **Layers by disclosure tier (§8.4):**
  - Village points (P2) with a card: names (Polish, Ukrainian, historical German or Austrian spelling from PRNG `NAZWYHISTORYCZNE` where present), population 1921/1943 where sourced (Wolski poster), cause and date of emptying with source citations, what survives (e.g. Caryńskie: church foundation outline, chapel walls [V\*, pl.wikipedia]), protected-area status, visitor rules.
  - Aggregated feature counts per village or per ≥1 km² hex (P3): "Caryńskie: N house platforms, M km of hollow ways mapped (A2+)".
  - Relief viewer: generalised (≥1 m) SVF/VAT tiles with masked sensitive polygons; a 2012/2023 swipe for monitoring stories.
  - Historical map overlays where licences permit (1852 cadastre, WIG).
- **Content:** method page (incl. tier definitions and known-check, with honest limitations); per-village story pages co-written with or reviewed by descendant organisations; a corrections and feedback form; bilingual Polish + Ukrainian, plus English.
- **Data release:** P2/P3 GeoJSON with a DOI (Zenodo) and licence (attribution to GUGiK; ODbL compliance if OSM-derived). Full P1 data to WKZ, NID and IGiPZ PAN.
- **Not shown:** exact coordinates of new features, cemeteries, conflict features; full-resolution relief inside masks.

---

## 12. Risk register and open questions (ranked)

| # | Risk / question | Likelihood | Impact | Mitigation / next action |
|---|---|---|---|---|
| R1 | 2023 flight was leaf-on, so ground density under beech and fir is no better than 2012 | Medium | High (D1, recall of small features) | One-tile QA (S3) first; fuse epochs; ground-density mask |
| R2 | Claiming novelty for known features (the HN failure) | High without design | High (credibility) | §6 logged known-check; T1 default framing; ask IGiPZ PAN early |
| R3 | Low precision floods reviewers | High | High | Ranking, cluster rules (R5), two-epoch persistence, sampling; measure reviewer minutes/km² in M1 |
| R4 | Legal misstep (field visits in the National Park, searching bans in former cemeteries, notification duty) | Medium | High | Lawyer + WKZ + BdPN before any field step; desk-only until then |
| R5 | Publishing enables looting or desecration, or inflames memory politics | Medium | High | Tiered disclosure; consultation; never publish conflict or grave features |
| R6 | UXO and human remains during fieldwork | Low-medium | Very high (safety) | No ground disturbance; notify police/sappers; field protocol; never alone |
| R7 | Cadastral georeferencing error makes weak labels useless | High | Medium | Area-level (parcel) labels; local rubber-sheeting on persistent roads and boundaries |
| R8 | Overfitting to Caryńskie; random-split optimism | High if careless | Medium | Leave-one-village-out; blind M3 village |
| R9 | Data volume (about 1 TB) and processing time on one Windows machine | Medium | Medium | Pilot first; process per tile, keep only derived COGs; external drive |
| R10 | GUGiK service changes (index, URLs, republishing) | Medium | Low-medium | Archive WFS responses; checksum files; store URL + date |
| R11 | VLM triage adds cost and non-reproducible judgements | Medium | Medium | Optional, benchmarked, logged with model ID; never decides novelty |
| R12 | Duplicating IGiPZ PAN's unpublished work, or upsetting the original researchers | Medium | Medium | Contact first; offer collaboration and co-authorship |
| R13 | Mis-attributing cause of depopulation | High if using "Vistula" broadly | Medium-high | Per-village cause field with citation; review by historians and descendants |
| R14 | Licence ambiguity for derived DTMs and historical map scans | Low-medium | Medium | Read the Regulamin; ask the archives; attribute |

Open questions:
- Q1: What is class-2 density under forest in 2012 vs 2023 at Caryńskie? (QA)
- Q2: What months were the 2012 (M-3334-012/11) and 2023 (GI-FOTO.6202.7.2023) flights? (GPS time)
- Q3: Are the 2023 and 2025 "12 p/m2" blocks the same data? (compare headers and GPS time)
- Q4: How much relief resolution may be public? (conservator opinion)
- Q5: Does IGiPZ PAN hold digitised feature inventories or georeferenced cadastres for Bieszczady villages?
- Q6: Is AZP data for the pilot AZP sheets obtainable, and under what terms?
- Q7: Which Bieszczady villages are in AP Przemyśl Fond 126 scans? (Gesher Galicia inventory PDF not read)
- Q8: How large is the KRON86-EVRF2007 offset locally, and is it spatially uniform?
- Q9: What do the 2025-2026 Monuments Act amendments change?
- Q10: Are the BdPN rules compatible with any field verification by non-staff?

---

## 13. Appendix

### Appendix A: What I verified in this pass (2026-11-12)

| # | Claim checked | Result | How |
|---|---|---|---|
| 1 | Affek et al. 2022 results (38-70%, 65-79%) | **Confirmed**: 3 villages (2 Carpathian, 1 Sudetes), national LiDAR + cadastral maps + field | Crossref abstract for 10.1002/arp.1846 |
| 2 | Banasiak 2022 metrics (missing in notes) | **Found**: F1 0.58, IoU 0.50; per class 0.41/0.62/0.62; authors confirmed | Crossref abstract for 10.3390/rs14040995 |
| 3 | Hillfort CNN precision 0.26 | **Confirmed** with full table (England 305/80/225/32; Hesse 148/169; Molise 85/100), training counts, FP sources | Fetched jcaa.178 |
| 4 | rvt-py Python limit | **Confirmed** `<3.12` (2.2.3). **New:** `rvt.vis` is numpy/scipy-only; repo active Aug 2026 | PyPI JSON; GitHub raw sources |
| 5 | PDAL availability | **New:** conda-forge `python-pdal` 3.5.5 win-64 for py310-py315; `pdal` 2.10.2 win-64 | anaconda.org API |
| 6 | FRANZI / Franciscan cadastre access | Austria-only; Tyrol georeferenced; CC0 on Zenodo; **no Galicia**. Galician 1852 maps: AP Przemyśl Fond 126 scans and Gesher Galicia (search-level only) | Fetched kulturpool.at; WebSearch |
| 7 | Legal article numbers (36.1.12, 109c, 35) | **Corrected**: 36.1.12 and 109c repealed (2023 amendment in force 1 May 2025); new 36b, 36c, 109d, 109e; art. 35 confirmed | Consolidated text Dz.U. 2024 poz. 1292 via api.sejm.gov.pl; ELI metadata |
| 8 | IALE 2019 poster (unreadable in notes) | **Read**: ISOK 4 p/m², 0.5 m TIN DEM, SVF 16 dir / 10 m, feature visibility table, error types, Caryńskie coordinates and area | curl + pdftotext |
| 9 | Affek 2016 data and specs (unreadable in notes) | **Read**: dedicated 2013 Riegl flight (not ISOK), 12 ground pts/m², feature signatures, preservation findings | curl + pdftotext |
| 10 | Wolski 2016 + Wolski poster; the "Vistula" framing | **Read**: >100 villages; 90%; Operation H-T 1951 (about 40 villages); Caryńskie emptied Apr-May 1946; Wisła minor in gmina Lutowiska | curl + pdftotext |
| 11 | Coverage beyond 2012 near Caryńskie | **New**: EVRF2007 2023 (2,995 tiles in bbox) and 2025 (608) | WFS hits + GetFeature |
| 12 | Actual point density | **New**: 2023 Caryńskie tiles 59-84 pts/m² all returns; 2012 8-13 | LAS header range reads |
| 13 | Caryńskie location, protected status | 49.1664 N, 22.6183 E (poster, Wikidata); 49.1508 N, 22.6439 E (pl.wikipedia). Inside BdPN | Fetched pl.wikipedia; Wikidata SPARQL |
| 14 | PRNG as a gazetteer | WFS works; Caryńskie and Nasiczne are official "osada" | Live WFS |
| 15 | NID register services | `INSPIRE_AMD` WMS, layer `Archaeological_Monuments`; `INSPIRE_IMD` WMS responds. No WFS found | Live GetCapabilities |
| 16 | Maya post claims | Confirmed: "NASA lidar" unnamed; "no special model" quote; Estrada-Belli 2025 rediscovery; INAH register also lacked the site; no cost | Fetched post |
| 17 | WODAN2 figures | Confirmed (about 70% vs 50/46/18%; below human performance) | Crossref abstract |
| 18 | Peck et al. 2026 | Confirmed qualitatively (high recall, low precision, wrong class identity) | Crossref abstract |

**Could not verify:**
- the HN thread (not re-read);
- Trier 2021 numbers (my DOI guess resolved to an unrelated paper and is not cited);
- the Białowieża 96% figure;
- Guyot 2018 numbers;
- the KRON86-EVRF2007 offset;
- the 2025-2026 law amendments;
- BdPN regulations;
- AZP access;
- WIG or Mapire endpoints;
- Gesher Galicia coverage of specific Bieszczady villages;
- leaf state and ground density of the 2023 data;
- numba on Python 3.14;
- the conda-forge `lazrs-python` package name.

### Appendix B: Corrections and downgrades of earlier claims

| # | Earlier claim (where) | Correction |
|---|---|---|
| 1 | Village presets (handoff [H]) | All wrong. Distances to Wikidata coordinates: Krywe 49.339/22.437 → 49.2506/22.5219 (about 11.6 km); Tworylne 49.347/22.458 → 49.2678/22.4772 (about 8.9 km); Hulskie 49.330/22.487 → 49.245/22.5367 (about 10.2 km); Caryńskie 49.192/22.555 → 49.1664/22.6183 (about 5.4 km); Łopienka 49.322/22.360 → 49.265/22.3647 (about 6.3 km); Jaworzec 49.303/22.392 → 49.2236/22.4428 (about 9.6 km); Dydiowa 49.098/22.722 → 49.185/22.7461 (about 9.8 km); Sianki 49.032/22.858 → 49.0192/22.8897 (Polish-side entry, about 2.7 km). Distances [D], approximate |
| 2 | "Near Caryńskie only 2012 tiles" ([ORCH], [N01 §6]) | True for KRON86 only. EVRF2007 has 2023 coverage. Also, 49.195/22.555 is not Caryńskie |
| 3 | "Bieszczady is 4 p/m² (ISOK standard I)" ([N01 §6]) | The 4 p/m² is nominal. Measured all-return density is 8-13 (2012) and 59-84 (2023, Caryńskie) per m². Ground density unknown |
| 4 | Affek 2016 used ISOK; "1.57 billion points, ~12 pts/m²" ([N02 §1.2], [U]) | Dedicated MGGP Aero flight, 19 Apr 2013, Riegl LMS-Q680i; 12 ground / 25 total pts/m² [V\*]. The 1.57 billion figure was not found in the extracted text |
| 5 | Art. 36 ust. 1 pkt 12 permit; art. 109c penalty ([N04 §0, §4]) | Repealed from 1 May 2025; replaced by art. 36b/36c and 109d/109e |
| 6 | 0.5 m DTM recommendation "unverified" ([N03 §1.3]) | Verified for 4 pts/m² ISOK data (poster), with the pixels ≤ points rule; ploughing traces lost at 1 m |
| 7 | RVT SVF parameters "not settled" ([N03 §1.2]) | Poster used 16 directions, 10 m radius, no noise reduction. A starting point, not an optimum |
| 8 | Banasiak 2022 "metrics NOT obtained" ([N02 §2.1]) | F1 0.58, IoU 0.50 [V\*] |
| 9 | FRANZI as a cadastral source ([N03 §4.1]) | Not applicable to Galicia; use AP Przemyśl / Gesher Galicia |
| 10 | Wikidata class query for former villages ([N04 §1.3]) | Most former villages are typed "wieś w Polsce"; class filters miss them. Build the list manually from Wolski's table, the korsokolbuszowskie seed list, Wikipedia and PRNG |
| 11 | "Village missing from gazetteers" as a discovery criterion | PRNG keeps former villages as official "osada"; gazetteer presence ≠ inhabited. Tier T2 redefined (§4.4) |
| 12 | KRON86-EVRF2007 "few dm to >1 m" ([N01 §1.4]) | Downgraded to [U]; co-register empirically |
| 13 | "Operation Vistula villages" framing ([H], app text) | Wrong for many villages: Caryńskie 1946; gmina Lutowiska mostly pre-1947; Operation H-T 1951 |
| 14 | Majewska Bartki "Carpathian" ([H]) | Warmia-Masuria [ORCH; N02] |
| 15 | Davis "Mississippi", Kazimi "Maya" (brief) | South Carolina; Harz [ORCH; N03] |
| 16 | "~1,500 villages" | Unsourced; do not use [ORCH; N04]. Sourced: ">100 villages" in the Western Bieszczady (Wolski 2016) |
| 17 | IGiPZ project "in Kraków" (one search summary this pass) | IGiPZ PAN is in Warsaw (poster affiliations) [V\*] |

### Appendix C: Source list

Verified this pass [V\*]:
- Affek et al. 2022, Archaeological Prospection: https://api.crossref.org/works/10.1002/arp.1846
- Banasiak et al. 2022: https://api.crossref.org/works/10.3390/rs14040995
- Affek 2016 PDF: https://rcin.org.pl//Content/59333/PDF/WA51_79176_r2016-t89-no3_G-Polonica-Affek1.pdf (DOI 10.7163/GPol.0062)
- Wolski 2016 PDF: https://rcin.org.pl//Content/59798/PDF/WA51_79555_r2016-t89-no3_G-Polonica-Wolski.pdf (DOI 10.7163/GPol.0064)
- IALE 2019 poster: https://www.igipz.pan.pl/tl_files/igipz/ZSIGiK/news/IALE_2019/poster.pdf
- Wolski poster: https://www.igipz.pan.pl/tl_files/igipz/ZGiK/osoby/wolski/niepublikowane/wolski_poster.pdf
- Landauer et al. 2025: https://journal.caa-international.org/articles/10.5334/jcaa.178
- WODAN2.0: https://api.crossref.org/works/10.3390/ijgi9050293
- Peck et al. 2026: https://api.crossref.org/works/10.1017/aap.2025.10130
- Maya post: https://pietromiotti.com/latest/maya-site
- rvt-py: https://pypi.org/pypi/rvt-py/json ; https://github.com/EarthObservation/RVT_py
- conda-forge: https://api.anaconda.org/package/conda-forge/python-pdal ; https://api.anaconda.org/package/conda-forge/pdal
- lazrs: https://pypi.org/pypi/lazrs/json
- FRANZI: https://kulturpool.at/en/content/franciscan-cadastre
- Monuments Act consolidated text: https://api.sejm.gov.pl/eli/acts/DU/2024/1292/text.html ; amendment metadata https://api.sejm.gov.pl/eli/acts/DU/2025/1673
- GUGiK WFS: https://mapy.geoportal.gov.pl/wss/service/PZGIK/DanePomiaroweLidarKRON86/WFS/Skorowidze ; https://mapy.geoportal.gov.pl/wss/service/PZGIK/DanePomiaroweLidarEVRF2007/WFS/Skorowidze
- PRNG WFS: https://mapy.geoportal.gov.pl/wss/service/PZGiK/PRNG/WFS/GeographicalNames
- NID WMS: https://usluga.zabytek.gov.pl/INSPIRE_AMD/Service.svc/get? ; https://usluga.zabytek.gov.pl/INSPIRE_IMD/Service.svc/get?
- Caryńskie: https://pl.wikipedia.org/wiki/Cary%C5%84skie ; Wikidata SPARQL https://query.wikidata.org/sparql

From the notes, verified there [V] (not re-checked): ESSD charcoal hearths https://essd.copernicus.org/articles/18/493/2026/ ; Guyot 2021 https://journal.caa-international.org/articles/10.5334/jcaa.64 ; Bellat 2025 https://arxiv.org/html/2501.03840 ; Geoportal LiDAR pages https://www.geoportal.gov.pl/pl/dane/dane-pomiarowe-lidar ; Slovak ALS https://www.skgeodesy.sk/geoportal-en/zbgis/als ; OpenTopography https://portal.opentopography.org/datasets ; Copernicus DEM page; Operation Vistula (EN and PL Wikipedia); lemko.org oral history; Stereńczak 2020 Crossref; EGU24-8532.

Search-level leads [U]: Gesher Galicia inventory https://www.geshergalicia.org/?p=8628 and Fond 126 PDF https://www.geshergalicia.org/wp-content/uploads/2015/01/Cadastral-Maps_Records-in-Fond-126-in-the-Polish-State-Archives-Przemyśl.pdf ; Gesher stitched maps (e.g. https://maps.geshergalicia.org/cadastral/bystre-1852) ; korsokolbuszowskie.pl village list ; BdPN yearbooks ; Straż Graniczna UXO advisories ; Kiarszys 2019 Antiquity ; Trier 2012/2021 ; Guyot 2018 ; Landauer & Klassen 2025 ; Mapire/Arcanum ; WIG archives ; INSPIRE records for NID registers.
