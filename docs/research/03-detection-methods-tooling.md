# 03 - Detection methods and tooling (LiDAR archaeology, SE Poland)

Research date: 2026-11-12. Tags: `[VERIFIED: fetched]` = page content opened with WebFetch. `[VERIFIED: local uv resolve]` = checked by `uv pip compile` on this machine (uv 0.7.15, target cp314 win_amd64, `--only-binary :all:`; resolution only, nothing installed). `[UNVERIFIED]` = known only from a search-result snippet or a secondary page; primary page not opened. Blocked (HTTP 403/404) pages are listed under Gaps.

---

## 0. Headline findings

1. **rvt-py cannot be installed on the project's Python 3.14 as published.** PyPI metadata for 2.2.2 and 2.2.3 (latest, 2025-07-04) sets `requires_python <3.12,>=3.6`. `[VERIFIED: fetched]` https://pypi.org/pypi/rvt-py/json . The earlier 1.0.x and 2.0-2.2.1 releases have no upper bound, but there is no 3.12+ release. `[VERIFIED: fetched]` (release table, same URL). Local resolve also fails because its gdal dependency has no usable cp314 win_amd64 wheel. `[VERIFIED: local uv resolve]`
2. **PDAL has no Windows/cp314 wheel.** The latest PyPI release (3.5.5) is an sdist only; classifiers stop at 3.13. `[VERIFIED: fetched]` https://pypi.org/pypi/pdal/json . Local resolve: "all versions of pdal have no usable wheels." `[VERIFIED: local uv resolve]`. Practical route is conda-forge or WSL/Docker, or the PDAL-free path (laspy + own rasterisation). Not verified for conda-forge availability (see Gaps).
3. **The "mainstream" Python stack resolves for cp314 win_amd64:** laspy, rasterio, geopandas, ultralytics, torch, scikit-learn, segmentation-models-pytorch, sahi, pyproj, shapely, open3d resolved; fiona did not (only 0.5 listed). `[VERIFIED: local uv resolve]`. Metadata side: rasterio 1.5.2 declares 3.13 and 3.14 classifiers `[VERIFIED: fetched]` https://pypi.org/pypi/rasterio/json ; ultralytics 8.4.211 declares 3.14 `[VERIFIED: fetched]` https://pypi.org/pypi/ultralytics/json ; laspy 2.7.0 is pure-Python `[VERIFIED: fetched]` https://pypi.org/pypi/laspy/json .
4. **Strongest recent evidence on precision is poor.** In a 2025 deep-learning hillfort search, the top-ranked AI detections in England had 225 false positives out of 305 predictions; in Hesse 148 of 169 candidates above 90% confidence were "obvious false positives"; overall test precision 0.26, recall 0.71, F1 0.38. `[VERIFIED: fetched]` https://journal.caa-international.org/articles/10.5334/jcaa.178 . Human verification of false positives is the authors' explicit requirement. `[VERIFIED: fetched]` (same URL).
5. **Training data is the bottleneck.** A 2025 review of ML in archaeology reports that LiDAR/ALS was used in ~50% of automatic-structure-detection study cases, that results were "mainly reported as unsuccessful or partially successful (59%, n = 31)", and that transfer learning was used in 41% (n = 16). `[VERIFIED: fetched]` https://arxiv.org/html/2501.03840 . A 2020 LiDAR-ML pipeline paper names "a limited amount of training labels" as a constraint. `[VERIFIED: fetched]` https://arxiv.org/abs/2004.02099 .
6. **Simulated training data is a live 2026 option.** Peck et al. (2026) trained Mask R-CNN on simulated tar-kiln shapes inserted into real DEMs; the best model found all 12 known targets but 686 of 709 post-filter predictions were false positives (Kisatchie NF, Louisiana). `[VERIFIED: fetched, secondary news report]` https://archaeologymag.com/2026/08/ai-trained-on-simulated-sites-finds-unknown-features/ ; primary DOI 10.1017/aap.2025.10130 was printed on that page (not opened).
7. **Forest false positives are the main operational risk** (tree-throw mounds, mima mounds, drainage, reservoirs, relict charcoal hearths, windthrow pits). Sources are mostly snippet-level; see section 5.

---

## 1. Visualisation of LiDAR DTMs

### 1.1 Tools and techniques
- **RVT / rvt-py** (Relief Visualization Toolbox, Python). Apache-2.0. Implements: hillshade (single and multidirectional), slope, simple local relief model, multi-scale relief model, sky illumination, sky-view factor (SVF), anisotropic SVF, positive/negative openness, local dominance, multi-scale topographic position, VAT, Combined VAT (CVAT), e4MSTP. RRIM is not in its list. `[VERIFIED: fetched]` https://github.com/EarthObservation/RVT_py . Docs: https://rvt-py.readthedocs.io/en/latest/ . Its docs say "The default settings therefore assume working with high resolution digital elevation models" but give no numeric defaults. `[VERIFIED: fetched]` (same docs URL). Required citations listed on the repo: Zakšek et al. 2011 (RS 3:398-415), Kokalj et al. 2011 (Antiquity 85:263-273), Kokalj & Somrak 2019 (RS 11(7):747). `[VERIFIED: fetched]` https://github.com/EarthObservation/RVT_py
- **Sky-view factor (Zakšek, Oštir & Kokalj 2011).** Computes the horizon elevation angle γ_i in n directions out to radius R. Examples on the project page: 16 directions / 300 m radius (Grand Canyon); 60 directions / 50 m radius at 1 m resolution (Karst dolines); n = 8 in the method figure. `[VERIFIED: fetched]` https://iaps.zrc-sazu.si/en/svf . The page says parameters "were moved to a new RVT page", and no recommended values are stated there.
- **Kokalj & Somrak 2019 (Remote Sensing 11(7):747).** Argues for combining visualisations into image blends rather than relying on one product; evaluates five blend modes (normal, screen, multiply, overlay, luminosity) for recognising small features; provides a "recipe" and tool. `[UNVERIFIED]` (search summary) https://mdpi.com/2072-4292/11/7/747 . MDPI page returned 403 when fetched.
- **VAT (Visualisation for Archaeological Topography).** Fuses four layers into one image: hillshade, slope, positive openness, SVF. Two presets: general terrain ("a diverse landscape with high mountains and plains") and flat terrain (makes structures "very distinct" but can oversaturate steep slopes). CVAT blends both and is recommended in place of hillshading. Blend modes and numeric parameters are not stated on that page. `[VERIFIED: fetched]` https://rvt-py.readthedocs.io/en/latest/listofvis_VAT.html

### 1.2 Recommended composite (working recipe for this project)
- Base: CVAT (or VAT general + flat) plus positive openness and SVF as separate panels, following Kokalj & Somrak's argument for multi-visualisation review. `[VERIFIED: fetched]` https://rvt-py.readthedocs.io/en/latest/listofvis_VAT.html ; `[UNVERIFIED]` for the blend-mode details.
- Field-view products: hillshade multi-direction and local relief model at small radius.
- Parameters: NOT settled by this research. Must be fixed empirically (SVF radius and direction count trade detail against terrain context; the SVF examples above range from 50 m to 5 km radius, which is not a useful default for a 1 m DTM). `[VERIFIED: fetched]` https://iaps.zrc-sazu.si/en/svf

### 1.3 Resolution
- Repo/docs example file name is "dem_05m" (`[VERIFIED: fetched]` https://rvt-py.readthedocs.io/en/latest/listofvis_VAT.html), but no document fetched recommends 0.5 m for 4-12 pts/m2. The 0.5 m figure in the brief is therefore `[UNVERIFIED]`.

---

## 2. Ground filtering and DTM generation

### 2.1 Point density of Polish ALS (ISOK / Geoportal)
- Geoportal: coverage "of various density ranging from 4 points per m2 to as many as 20 points per m2 (in cities)". Classes: 2 ground; 3 low veg 0-0.40 m; 4 medium veg 0.40-2.00 m; 5 high veg >2 m; 6 buildings; 7 noise; 8 water; 12 overlap. Data offered as LAZ. Two elevation layers: NMT-PL-KRON86-NH and NMT-PL-EVRF2007-NH; no grid size stated. `[VERIFIED: fetched]` https://geoportal.gov.pl/en/data/lidar-measurements-lidar
- Urban standard 12 pts/m2 and ordinary 4 pts/m2: `[UNVERIFIED]` https://isprs-archives.copernicus.org/articles/XLVIII-1-W3-2023/227/2023/isprs-archives-XLVIII-1-W3-2023-227-2023.pdf (search snippet; PDF not decodable by WebFetch in this session).
- INSPIRE record gives a 1 m grid for the ISOK elevation dataset `[UNVERIFIED]` (search snippet; no URL opened).
- Implication: at 4 pts/m2 a 0.5 m cell has ~1 return/cell on average; 1 m cells are safer for ground DTMs in forest. This is reasoning, not a sourced claim.

### 2.2 Filters (algorithms)
- **PMF** (Zhang et al. 2003, IEEE TGRS 41(4):872-882). `[UNVERIFIED]` https://ieeexplore.ieee.org/document/1202973 (search snippet).
  - PDAL `filters.pmf` defaults: max_window_size 33; slope 1.0; initial_distance 0.15; cell_size 1; max_distance 2.5; exponential growth on by default. The PDAL page says `filters.smrf` "performs much better" and should be preferred in most cases. `[VERIFIED: fetched]` https://pdal.io/en/stable/stages/filters.pmf.html
- **SMRF** (Pingel, Clarke & McBride 2013, ISPRS JPRS 77:21-30). PDAL defaults: cell 1.0; slope 0.15; window 18.0; threshold 0.5; scalar 1.25; ground_class 2; enabled by default. Paper's "optimised" set: scalar 1.2, slope 0.2, threshold 0.45, window 16.0. `[VERIFIED: fetched]` https://pdal.io/en/stable/stages/filters.smrf.html
- **CSF** (Zhang et al. 2016, Remote Sensing 8(6):501). Cloth simulation; "only needs a few easy-to-set integer and Boolean parameters". `[UNVERIFIED]` https://www.mdpi.com/2072-4292/8/6/501 (search snippet; MDPI not fetched). PDAL's filter pages checked did not mention CSF.
- **lidR** (R): classify_ground / rasterize_terrain. Not verified: docs URLs returned 404 (Gaps).
- **WhiteboxTools**: not verified (manual URL returned 404).
- **LAStools**: not checked (commercial; not searched in this pass).
- No head-to-head accuracy comparison of CSF vs PMF/SMRF was found in this pass. `[UNVERIFIED]` (absence of finding).

### 2.3 Interpolation (TIN vs IDW)
- PDAL `writers.gdal` requires `resolution` (no default). `output_type` values: min, max, mean, idw, count, stdev, all (default all). It does **not** list TIN. Radius defaults to resolution x sqrt(2); IDW power default 1.0; window_size default 0. `[VERIFIED: fetched]` https://pdal.io/en/stable/stages/writers.gdal.html
- Therefore: in PDAL, the ground DTM is effectively a gridded min/mean/IDW product. A TIN surface needs another tool (lidR `tin`, WhiteboxTools TIN gridding, or a QGIS TIN) - not verified here.
- Archaeological practice: IDW/mean gridding is sufficient for 1 m DTM; TIN preserves breaks better on steep banks. Not sourced in this pass.

---

## 3. Automated detection in the literature

Figures marked `[UNVERIFIED]` come from search snippets; primary pages were blocked or PDFs were not decodable.

| Study | Region / target | Method | Training size | Reported performance | Tag / URL |
|---|---|---|---|---|---|
| Trier & Pilø 2012 | Oppland, Norway; iron-production pits | Circular-pit detection in ALS height data; decision-tree confidence | - | Automatic beats visual for small pits; DOI 10.1002/arp.1421; "at least five pulses per square metre" | `[UNVERIFIED]` https://doi.org/10.1002/arp.1421 |
| Trier et al. 2018 (ARP 10.1002/arp.1731) | Norway; CNN for ALS | CNN, transfer learning | - | Not read (publisher page blocked) | Gap |
| Trier et al. 2021 (IJAEOG) | Norway; charcoal kilns, grave mounds, pitfall traps; Faster R-CNN | Faster R-CNN | - | Charcoal kilns: 90% detected, 38% false positives in 937 km2 (Øvre Eiker) | `[UNVERIFIED]` https://doaj.org/article/2a34fea1eb4540f3a58b5c5c9df2c9bf (DOAJ returned 403) |
| Somrak, Džeroski & Kokalj 2020 | Maya (per snippet); CNN on ALS visualisations | CNN | - | Numbers not read | `[UNVERIFIED]` https://mdpi-res.com/d_attachment/remotesensing/remotesensing-12-02215/article_deploy/remotesensing-12-02215.pdf (MDPI and PDF not readable) |
| Albrecht et al. 2020 (IBM) | LiDAR pipeline on geospatial platform | ANN + segmentation | "limited amount of training labels" | No metrics reported | `[VERIFIED: fetched]` https://arxiv.org/abs/2004.02099 |
| Bundzel et al. 2020 (RS 12:3685) | Pacunam LiDAR, Maya lowlands, Guatemala | U-Net and Mask R-CNN semantic segmentation; labelling decision-support | - | Not read | `[UNVERIFIED]` https://www.mdpi.com/2072-4292/12/22/3685 |
| Guyot, Hubert-Moy & Lorho 2018 (RS 10:225) | Brittany, France; Neolithic mounds | Multiscale topographic-position features + Random Forest | - | Snippet reports 2,952 TP, 41 FP, 46 FN; field check confirmed a new mound near Carnac | `[UNVERIFIED]` https://mdpi.com/2072-4292/10/2/225/html (403 on fetch) |
| Guyot et al. 2021 (JCAA 4(1)) | Southern Morbihan, Brittany, ~200 km2 | Mask R-CNN (ResNet-101, COCO), head-only fine-tuning | 150 tiles of 512x512 px, 195 structures; split 110/20/20 | mAP@IoU0.5 0.29-0.77 across 110 configs (mean 0.50); augmentation raised 0.64 to 0.75; no precision/recall reported; split is random, not spatial | `[VERIFIED: fetched]` https://journal.caa-international.org/articles/10.5334/jcaa.64 |
| Verschoof-van der Vaart & Lambers 2019 (JCAA 2(1):31-40) | Central Netherlands; barrows, Celtic fields | Faster R-CNN (WODAN) | - | Snippet only | `[UNVERIFIED]` https://scholarlypublications.universiteitleiden.nl/access/item%3A2977987/view |
| WODAN2 (Verschoof-van der Vaart et al. 2020, ISPRS IJGI 9:293) | Netherlands, random test set | Faster R-CNN + Location-Based Ranking | - | Snippet: ~50% barrows, 46% Celtic fields, 18% charcoal kilns recall-type figures on large random set; small non-random test ~70% | `[UNVERIFIED]` https://doi.org/10.3390/ijgi9050293 (403 on fetch) |
| Verschoof-van der Vaart et al. CarcassonNet (JCH 2020/21; DOI 10.1016/j.culher.2020.10.009) | Netherlands to Germany and Slovenia; hollow roads | CNN on road sections | - | MCC 0.47 (snippet); precision/recall not seen | `[UNVERIFIED]` https://doi.org/10.1016/j.culher.2020.10.009 |
| Landauer et al. 2025 (JCAA 8(1)) | England, Hesse (DE), Molise (IT); ~180,000 km2 hillforts | ConvNeXt (ImageNet pretrained), fast.ai, pseudo-labelling | 579 hillfort + ~20,000 negative vignettes; then 505 + 15,156 after pseudo-labelling | England test: 305 predictions, 225 FP, 80 TP, 32 FN; overall precision 0.26, recall 0.71, F1 0.38; Hesse 148/169 obvious FP at >90% confidence; Molise 85 of top 100 FP | `[VERIFIED: fetched]` https://journal.caa-international.org/articles/10.5334/jcaa.178 |
| Davis, Sanger & Lipo 2019 (JASREP 23:166-177) | Beaufort County, South Carolina; shell rings and mounds | Four OBIA methods incl. template matching; combined method best | - | Snippet; note: **not Mississippi** | `[UNVERIFIED]` https://d-davis.github.io/publications/Davis_etal_2019_JASREP.pdf |
| Davis, "deep learning rare features" (SEG) | Coastal South Carolina; shell rings | Deep learning; negatives used to reduce false positives | Very small | Snippet only | `[UNVERIFIED]` https://d-davis.github.io/publications/Davis_etal_SEG.pdf |
| Kazimi (dissertation 2021) | Harz, Lower Saxony (DE); charcoal kilns, mounds, mining holes, bomb craters | Deep learning, semi-supervised (Kazimi & Sester) | - | Snippet only; **not Maya** | `[UNVERIFIED]` https://researchconnect.suny.edu/en/publications/a-comparison-of-automated-object-extraction-methods-for-mound-and/ (unrelated index page) - no primary URL seen |
| Orengo et al. 2020 (PNAS 117:18240-18250; DOI 10.1073/pnas.2005583117) | Cholistan, Pakistan; mounds | Random Forest on multisensor, multitemporal satellite data (not LiDAR, not CNN) | Known mound locations | Probability map ~36,000 km2 | `[UNVERIFIED]` https://www.geo3bcn.csic.es/?p=2221 |
| Yolo on Maya (arXiv 2403.05773) | Maya (Puuc / HNT) | YOLOv8 segmentation | - | Snippet: slightly lower on separate site | `[UNVERIFIED]` https://arxiv.org/html/2403.05773v1 |
| Peck et al. 2026 (AAP 14(2); DOI 10.1017/aap.2025.10130) | Kisatchie NF, Louisiana; tar-kiln-like mounds | Mask R-CNN trained on simulated objects in real DEMs | Not stated | Model 2: 2,032 predictions -> 709 after filters; all 12 targets found; 686 FP; Model 3 (real SC kilns) 11/12 | `[VERIFIED: fetched, secondary]` https://archaeologymag.com/2026/08/ai-trained-on-simulated-sites-finds-unknown-features/ |
| Landauer & Klassen 2025 (Geomatics; preprint Aug 2025) | Zero-shot visual foundation models (SAM 2.1, GPT-4.1, Gemini 2.0-flash) on aerial LiDAR and drone video | Zero-shot, no fine-tuning | 0 | Snippet claim: "comparable to human experts" - numbers not read | `[UNVERIFIED]` https://www.mdpi.com/2673-7418/5/4/52 (403 on fetch) |
| Hattula et al. 2025 (ISPRS Archives XLVIII-M-7) | Forest building segmentation (not archaeology) | SAM + LiDAR DSM | - | SAM struggles with occlusion in dense forest | `[UNVERIFIED]` https://isprs-archives.copernicus.org/articles/XLVIII-M-7-2025/13/2025/isprs-archives-XLVIII-M-7-2025-13-2025.pdf |
| Bellat et al. 2025 review (arXiv 2501.03840) | Cross-field review | - | - | ALS/LiDAR in 50% of structure-detection cases; 59% (n=31) unsuccessful or partial; transfer learning 41% (n=16) | `[VERIFIED: fetched]` https://arxiv.org/html/2501.03840 |

### 3.1 Patterns across the literature (what the evidence supports)
- **Recall is reported; precision usually is not.** Guyot 2021 gives mAP only; Landauer 2025 gives precision 0.26. Use precision@top-k and FP per km2 as the headline metric in this project. `[VERIFIED: fetched]` (rows above)
- **Transfer learning is common** (41% of reviewed structure-detection studies per Bellat et al.). `[VERIFIED: fetched]` https://arxiv.org/html/2501.03840 . Landauer et al. used ImageNet pretraining and then pseudo-labelling to bootstrap from 579 positives. `[VERIFIED: fetched]` https://journal.caa-international.org/articles/10.5334/jcaa.178
- **Random splits are the norm**, so reported scores overstate performance on unseen areas (Guyot 2021 used a random split repeated 10 times). `[VERIFIED: fetched]` https://journal.caa-international.org/articles/10.5334/jcaa.64
- **Negatives matter.** Davis et al. (SEG) and the shipwreck study both report that adding background/negative examples reduces FPs. Source for Davis SEG is `[UNVERIFIED]` (above); the shipwreck claim is `[UNVERIFIED]` (search snippet, https://doi.org/10.3390/rs13091759).
- **Liberal thresholds with field verification** is one explicit strategy in the literature (snippet). `[UNVERIFIED]` https://doi.org/10.3390/rs13091759 ; the Landauer paper instead uses a 90% cutoff and says humans must validate FPs. `[VERIFIED: fetched]` https://journal.caa-international.org/articles/10.5334/jcaa.178

### 3.2 Foundation models / SAM / YOLO / U-Net / VLM / LLM agents (2024-2026)
- SAM applied to LiDAR archaeology: only zero-shot preprint evidence found (Landauer & Klassen 2025). Numbers not verified. `[UNVERIFIED]` https://www.mdpi.com/2673-7418/5/4/52
- YOLOv8 and Mask R-CNN dominate Maya LiDAR work. `[UNVERIFIED]` https://arxiv.org/html/2403.05773v1 ; Bundzel et al. U-Net vs Mask R-CNN. `[UNVERIFIED]` https://www.mdpi.com/2072-4292/12/22/3685
- **LLM agents running LiDAR pipelines for Maya: no paper found.** The 2025 zero-shot study tested GPT-4.1 and Gemini 2.0-flash as detectors, not as pipeline agents. `[UNVERIFIED]` https://www.mdpi.com/2673-7418/5/4/52 . Treat the "recent Maya LLM-agent trend" as unsupported by this research.

---

## 4. Training sets from historical maps; evaluation

### 4.1 Historical sources
- **Franziszeischer Kataster (Austria, 1817-1861).** Digitised parcel protocols: "over 20,000" for all of Austria; georeferenced parcel data complete only for Tyrol (~750,000 parcels). Platform: FRANZI (geschichte-franzi.uibk.ac.at). `[VERIFIED: fetched]` https://kulturpool.at/en/content/franciscan-cadastre . Relevant to this project only as a method reference: the user's Poland study area is not in the Habsburg cadastre except the Galician part (not verified here).
- **Mapire** is a Habsburg military-survey and Hungarian cadastral platform, not the Austrian Franciscan cadastre. `[UNVERIFIED]` https://www.vi-mm.eu/?p=29454 (search snippet). Its listed cadastral maps appear Hungarian. `[UNVERIFIED]`
- **WIG maps (Polish Military Geographical Institute).** 1:100,000 tactical sheets achieved full country coverage, with ~50% of sheets revised in the 1930s. `[UNVERIFIED]` https://phavi.umcs.pl/at/attachments/2024/0722/104300-kuna-panecki-zawadzki-2024-ijgi-13-00249.pdf . The "Maps with the Past" geoportal that hosted georeferenced WIG sheets was suspended in 2022. `[UNVERIFIED]` (same source). MapyWIG archive (1924-1939) and the interwar gazetteer *Skorowidz Miejscowości* are listed. `[UNVERIFIED]` https://rohatyndrg.org/home/topic/maps
- **Heritage registers.** Archaeological monuments are in a separate register book kept by voivodeship conservators; nationwide over 7,600 immovable archaeological monuments (figure from snippet). `[UNVERIFIED]` NID publishes regional archaeological register layers and an AZP-grid WMS on the INSPIRE geoportal (e.g. Opolskie record). `[UNVERIFIED]` https://inspire-geoportal.ec.europa.eu/srv/api/records/4b24be64-7f8c-463d-b6cc-621f6c5b8428 . zabytek.pl: an old count of "more than 84 thousand" monuments; search tool for AZP not confirmed. `[UNVERIFIED]` https://scienceinpoland.pl/aktualnosci/news%2C413170%2Cmore-than-84-thousand-polish-monuments-on-an-interactive-online-map.html

### 4.2 Label construction (proposed; design, not sourced)
1. Positives: village/farm footprints on WIG 1:100,000 / 1:25,000 sheets (1930s) that still survive as forest ruins, matched to NID register entries and to the interwar gazetteer for names. Must be verified in the field or by LiDAR cross-check: many villages on maps are gone or displaced.
2. Negatives: (a) LiDAR tiles with no mapped settlement; (b) confusers listed in section 5 (tree-throw, charcoal hearths, drainage, roads), explicitly, because Davis and the shipwreck study both show negatives reduce FPs (see section 3.1).
3. Weak labels: heuristics on DTM (e.g. local relief threshold) generate candidate pseudo-labels; expert review on a sample; then Landauer-style pseudo-labelling. `[VERIFIED: fetched]` https://journal.caa-international.org/articles/10.5334/jcaa.178
4. Synthetic augmentation: simulated objects inserted into real DEMs (Peck et al. 2026). `[VERIFIED: fetched, secondary]` https://archaeologymag.com/2026/08/ai-trained-on-simulated-sites-finds-unknown-features/ . Augmentation alone raised Guyot 2021 mAP from 0.64 to 0.75. `[VERIFIED: fetched]` https://journal.caa-international.org/articles/10.5334/jcaa.64
5. Self-supervised pretraining on DTM tiles: no source found in this pass (Gap).

### 4.3 Evaluation
- **Spatial cross-validation (block or leave-one-region-out)** is required; the reviewed papers mostly used random splits, which is a known weakness. `[VERIFIED: fetched]` https://journal.caa-international.org/articles/10.5334/jcaa.64 . Method reference for spatial CV: not searched (Gap).
- **Hold-out villages**: evaluate on whole villages withheld from training; report recall per village, not per pixel.
- **Precision at top-k** (k = 50, 100, 200 etc.) plus false positives per km2 is the most directly comparable metric to the Landauer numbers. `[VERIFIED: fetched]` https://journal.caa-international.org/articles/10.5334/jcaa.178 (they report top-100 FP counts)
- Report mAP@0.5 only alongside precision/recall; mAP alone masked FP rates in the reviewed work. `[VERIFIED: fetched]`

---

## 5. Candidate ranking, discovery-vs-known scoring, false positives

### 5.1 Known false-positive sources (forest)
- **Tree-throw mounds and pits (windthrow):** Forest Research notes a small mound produced by modern tree-throw being mistaken for an earthwork. `[UNVERIFIED]` https://cdn.forestresearch.gov.uk/2008/02/lidar_fc_note_web_2008.pdf . A Polish thesis describes windthrow pit-mound pairs and tuning thresholds to reduce FPs. `[UNVERIFIED]` https://www.bip.us.edu.pl/sites/default/files/2026-03/Rozprawa_doktorska.pdf
- **Mima mounds, reservoirs, drainage features:** main FP sources in Peck et al. 2026. `[VERIFIED: fetched, secondary]` https://archaeologymag.com/2026/08/ai-trained-on-simulated-sites-finds-unknown-features/
- **Relict charcoal hearths and stone walls:** natural and anthropogenic structures misread as walls or hearths in a northeastern US forest study. `[UNVERIFIED]` https://gsa.confex.com/gsa/2023SE/webprogram/Paper386125.html
- **Forest paths/roads and terrain:** main FP sources in the Hesse/England hillfort search. `[VERIFIED: fetched]` https://journal.caa-international.org/articles/10.5334/jcaa.178
- **Vegetation residue in ground DTM:** unfiltered vegetation bumps trigger many FPs in a mound model. `[UNVERIFIED]` (search summary, no URL with confidence). Mitigation: stricter ground classification (section 2).
- **Modern structures confused with monuments (mounds, pits)**: location and land use help separate. `[UNVERIFIED]` https://link.springer.com/article/10.1007/s42489-020-00049-w
- **WWII trenches, UXO craters, boar rooting, beaver dams, logging roads**: no source found in this pass (Gap). The 2026 Louisiana case concerned a former WWII training site (Peck et al.), which is a relevant analogue `[VERIFIED: fetched, secondary]` https://archaeologymag.com/2026/08/ai-trained-on-simulated-sites-finds-unknown-features/ ; Polish-specific WWII/UXO sources not searched.

### 5.2 Discovery-vs-known protocol (proposed)
1. Match each candidate against: NID register and AZP grid (section 4.1); WIG sheets; interwar gazetteer names. Known -> "re-detection"; no match -> "candidate".
2. Field check candidates with a fixed protocol (e.g. auger, surface survey, photos, GPS). The Peck et al. team used augers on 2 of 11 visited targets and found none of the expected anthropogenic deposits. `[VERIFIED: fetched, secondary]` https://archaeologymag.com/2026/08/ai-trained-on-simulated-sites-finds-unknown-features/ This shows that field checks can overturn a plausible detection.
3. Score: detector confidence x shape fit x cluster context (count of mounds within a village footprint) x absence from historical maps. Weights are not sourced; treat as design.

---

## 6. Reproducible Python stack (cp314 check)

| Package | PyPI metadata (fetched) | Local uv resolve, cp314 win_amd64, binary-only | Note |
|---|---|---|---|
| rvt-py 2.2.3 | requires_python `<3.12,>=3.6` (2025-07-04) `[VERIFIED: fetched]` | FAIL (gdal has no usable wheels) `[VERIFIED: local uv resolve]` | Blocked on 3.14. Options: separate Python 3.11 env to produce VAT/SVF rasters, or reimplement SVF/openness with numpy |
| pdal 3.5.5 | sdist only; no cp314 wheel `[VERIFIED: fetched]` https://pypi.org/pypi/pdal/json | FAIL `[VERIFIED: local uv resolve]` | Use conda-forge (not verified) or WSL |
| laspy 2.7.0 | pure-Python wheel; requires >=3.10 `[VERIFIED: fetched]` https://pypi.org/pypi/laspy/json | OK | Reads LAZ only with a backend (lazrs/laszip) - not verified |
| rasterio | 1.5.2 classifiers 3.13, 3.14; requires >=3.12 `[VERIFIED: fetched]` https://pypi.org/pypi/rasterio/json | OK | |
| geopandas, pyproj, shapely (numpy 2.5.4), open3d | resolved | OK `[VERIFIED: local uv resolve]` | fiona FAIL (only 0.5 listed) `[VERIFIED: local uv resolve]` - use pyogrio instead (not verified) |
| ultralytics 8.4.211 | requires >=3.8; 3.14 classifier `[VERIFIED: fetched]` https://pypi.org/pypi/ultralytics/json | OK | |
| torch 2.15.0 | requires >=3.11; 3.13/3.14 classifiers `[VERIFIED: fetched]` https://pypi.org/pypi/torch/json | OK | Verify CUDA wheel index before use |
| scikit-learn, segmentation-models-pytorch, sahi | not fetched individually | OK `[VERIFIED: local uv resolve]` | |
| whitebox | not fetched | OK `[VERIFIED: local uv resolve]` | Docs 404 |

Project: `pyproject.toml` pins `requires-python = ">=3.14"` with no dependencies (`[VERIFIED: local file]` C:\Users\alekn\orca\projects\lidar-discovery-poland\pyproject.toml). Wheel checks are resolution-only; no installation was tested.

Recommendation: keep the core pipeline on 3.14 (laspy, rasterio, geopandas, torch, ultralytics, sklearn, sahi). Isolate rvt-py and PDAL in a separate environment (3.11 or conda) and exchange GeoTIFFs.

---

## Gaps (not verified)

- Primary text for Kokalj & Somrak 2019 (MDPI 403). Blend modes and parameters unverified.
- Primary text for Trier 2012 (DOI shown in snippet), Trier 2018 (ARP 10.1002/arp.1731, blocked), Trier 2021 IJAEOG (DOAJ 403), Somrak 2020 (MDPI and PDF unreadable), Bundzel 2020 (not fetched), Guyot 2018 (MDPI 403), WODAN2 (MDPI 403), Landauer & Klassen 2025 (MDPI 403), Orengo 2020 (PNAS not fetched).
- Character et al., Gallwey et al.: not found in search. Meyer (Germany): not searched.
- Davis "Mississippi" claim in brief: not found; Davis's work located is South Carolina. Thiel/Kazimi "Maya": not found; Kazimi's work located is Harz, Germany.
- RVT default parameters (radius, directions) for SVF/openness/LRM: not in fetched docs; rvt-py docs say defaults are "for high-resolution DEMs" only.
- lidR and WhiteboxTools documentation: all tested URLs returned 404. CSF/PMF comparisons beyond snippets: not found.
- TIN gridding tool and interpolation guidance for 4-12 pts/m2: not found.
- 0.5 m DTM resolution recommendation: no fetched source. The only 0.5 m hint is a file name in RVT docs.
- ISOK DTM grid size: not confirmed (INSPIRE snippet says 1 m; Geoportal page gave no size).
- Polish register data access (zabytek.pl search, AZP digital layer): unconfirmed.
- Mapire vs FRANZI for the user's Polish study area: Polish-specific cadastral historical source for villages not found; Austrian Galicia coverage unverified.
- WWII/UXO, boar rooting, beaver dams, logging-road FP sources: not searched in depth.
- Spatial CV and precision@k methodology sources: not searched.
- Self-supervised DTM pretraining: no source.
- LLM-agent Maya pipelines: none found (section 3.2).
- conda-forge availability of pdal and rvt-py for 3.14: not checked.
- Trier/Pilø 2012 "template matching" wording: the snippet did not confirm it.
- The uv resolve check uses binary-only resolution; a real install was not performed.
