# 09 - Machine-learning detection plan

Status: plan, not implemented. Written 2026-11-13. Scope: how (and whether) machine learning should be used to find house platforms, cellar pits, wells, terraces, holloways, field boundaries, cemetery and church sites of the villages emptied in 1944-1951, from GUGiK ALS data, desk-only.

Inputs read: `research/03-detection-methods-tooling.md`, `05-synthesis.md` (§5-7, §10), `06-critique.md` (in full), `07-decisions.md` (desk-only), `08-architecture-contract.md` (framework v0). Where this plan conflicts with 05, the critique (06) and the decisions (07) win.

Evidence tags, as in 06:

- **[C]** checked today (2026-11-13) against a primary record: Crossref metadata/abstract, arXiv, PyPI JSON, or the paper page. Method in brackets.
- **[A]** abstract-level only (Crossref or search summary): the claim is in the abstract; the body was not read.
- **[S]** web-search summary only. A lead.
- **[M]** my domain knowledge. Not checked.
- **[D]** my reasoning or arithmetic.
- **[06]/[05]/[03]** taken from that project document with the tag it carries there.

---

## 0. Summary

1. The realistic product is a **ranked triage queue for one human reviewer**, not an autonomous detector. The unit of work and of evaluation is the **candidate object** (point, polygon or line), not the pixel or the tile.
2. **No ML before the desk-only kill gates K1-K4 and K6 have passed** (§8). The first "model" is a set of morphometric rules plus a gradient-boosted re-ranker on handcrafted features. A CNN is trained only if it beats that baseline on held-out villages at a fixed review budget.
3. Inputs are **terrain-only** relief channels at 0.5 m from the 2023 epoch, with a support mask from ground density. Historical maps, the 1944 orthophoto and the cadastre are **evaluation data, not inputs**, until an ablation earns them a place.
4. Evaluation is **leave-village-out**, reports precision@k and recall at a stated review budget with the prevalence printed beside it, uses object matching with stated tolerances, and compares against **independent denominators** (1921 building counts, 1944 roofs, cadastre symbols).
5. Everything runs on a **CPU-only Windows laptop**: LightGBM in minutes, a small CNN in hours, regional inference in a working day. No GPU is assumed.
6. ML output enters the catalogue as `Candidate` rows with `origin=ml`, `model_version`, a calibrated score, `review_status=proposed`, `reality=unassessed` and `disclosure=restricted`.

---

## 1. Problem framing

### 1.1 What kind of problem this is

| Framing | Fits which classes | Problem here |
|---|---|---|
| Object detection (boxes) | Cellars, wells, platforms, charcoal hearths: compact objects 2-20 m | Boxes describe holloways, terraces and field boundaries badly; the object count per class is small |
| Semantic segmentation (pixels) | Linear and areal classes: holloways, terraces, field-boundary scarps, cemetery enclosures | Pixel scores must still be turned into objects for review; pixel IoU says little about reviewer value (Banasiak et al. 2022 report pixel F1 0.58, IoU 0.50 [C, Crossref abstract, 10.3390/rs14040995]) |
| Classification of candidate chips | Any compact class, given a candidate generator | Recall is capped by the generator |
| **Ranking for review** | All | This is what the reviewer consumes. Every framing above ends here |

The literature supports the ranking view. In the best-documented recent large-area search, a ConvNeXt hillfort detector reached precision 0.26 at recall 0.71, and 148 of 169 Hesse candidates above 90% confidence were obvious false positives; the authors require human verification [05/03, verified there: Landauer et al. 2025, 10.5334/jcaa.178]. WODAN2 on a large random test area did not reach human performance [05, Crossref abstract, 10.3390/ijgi9050293]. Peck et al. 2026 found all 12 targets with 686 false positives among 709 predictions, and the "targets" turned out to be another feature class [05/03]. Nothing suggests our harder targets (decimetre platforms and small pits under old beech-fir forest) will do better.

Therefore: **the system proposes, a person decides**. Its value is the reviewer time it saves at a given recall, measured as in K6 (06 §6): "reviewing ranked candidates is at least twice as fast as scanning tiles at the same recall".

### 1.2 Units

| Unit | Used for | Definition |
|---|---|---|
| **Candidate object** | Review, labels, primary metrics | A point (cellar, well, mound), polygon (platform, enclosure) or line (holloway, terrace edge, boundary) in EPSG:2180, stored in WGS84 in the `Candidate` table |
| Pixel (0.5 m) | Training of segmentation models; loss masking | Internal only. Never reported as a headline metric |
| Patch (256 px = 128 m) | Model input and inference tiling | Internal only |
| Scan cell (100 × 100 m) | Annotation completeness, negatives, review budget | A cell is "exhaustively scanned" or not. Only scanned cells provide true negatives |
| Village (PRG precinct) | Cross-validation fold, recall against denominators | Precinct ID from `ms:A06_Granice_obrebow_ewidencyjnych` |

### 1.3 Base rates (what we are up against)

No measured base rate exists yet (06 problem 4). Working numbers, to be replaced in K6:

- Targets: a village of this size had on the order of 50-150 farmsteads [06, M]. Two pilot precincts of about 15 km² each [06, C for Caryńskie 14.97 km²] might hold 100-300 house sites in total, of which an unknown share has a surviving earthwork (K1 measures this).
- Confusers: closed depressions 0.3-2.5 m deep from windthrow, suffosion, quarrying, shell craters and dugouts may be one to two orders of magnitude more numerous than cellars [06, D]. If a closed-depression rule yields 100-1,000 depressions per km² and a village has 5-10 cellar-like features per km², the prevalence among candidates is **about 0.5-10%** [D].
- Consequence: a random ranking already scores precision@k equal to the prevalence. Every precision figure in this project is printed next to the prevalence of its evaluation area, and next to the rule baseline.
- Review cost: at about 30 s per candidate [D, to be measured in K4/K6], 20 candidates per km² over the 3,000 km² region is 500 reviewer-hours. Exhaustive review of raw depressions is impossible; a ranked budget is the only option.

### 1.4 What the model is asked, and what it is not

The `Candidate` schema separates **reality** (real landform vs DTM artefact), **morphological class**, and **dating evidence** (06 problem 3). ML answers only the first two, and only as a score:

- `p(class = c | relief)` for each target class c, from relief alone.
- It never sets `reality`, never fills `dating_evidence` and never touches `documentation_status`.
- "Is this from the village period?" is not an ML question. LiDAR does not date features (06 problem 3).

---

## 2. Inputs

### 2.1 Epoch

- **Train and predict on 2023 (EVRF2007) only** in all first stages. It has about 6.5 vendor ground points/m² under forest and 14.8% empty 0.5 m forest cells, against 2.2/m² and 59.9% in 2012 [06 §2.1, C].
- **2012 (KRON86) is a different domain.** A 0.5 m DTM there is 60% interpolation under forest. A model trained on 2023 will not transfer to it (06 §7, ML researcher). No 2012 channel enters the model. 2012 is used only for (a) a red-team test (§5.7), and (b) reviewer context in the frontend swipe view.
- **2025 "12 p/m2" blocks** cover only the northern belt. Treat as a third domain; do not mix into training until Q3 in 05 is answered.
- **Class-12 re-classification (K2)** changes the DTM. If K2 adopts it, every model is retrained on the new DTM and the old model cards are marked superseded. A model trained on vendor class 2 is never applied to a re-classified DTM or vice versa. The DTM recipe hash is part of `model_version`.
- Vertical datum offsets (KRON86-EVRF2007, about 14-20 cm [06, S]) do not matter for the channels below, which are all local and detrended. They matter only for two-epoch differencing, which is not an ML input.

### 2.2 Channels

Contract products (08): DTM, hillshade, slope, SVF (16 directions, 10 m radius), LRM (low-pass about 20 m), ground density, all 0.5 m COGs in EPSG:2180. The ML stack uses:

| # | Channel | Source | Why | Fixed scaling (stored in the model card) |
|---|---|---|---|---|
| 1 | LRM 20 m | contract `lrm` | Platforms, terraces, boundary banks, holloways: decimetre relief independent of slope | clip to [-1.5, +1.5] m, divide by 1.5 |
| 2 | LRM 5 m | derived in `ml/channels.py` from the DTM | Small pits and wells (2-6 m) are smoothed out of LRM 20 | clip [-1, +1] m |
| 3 | SVF r10 m | contract `svf` | Standard in the regional literature (IALE 2019 poster used 16 directions, 10 m [05, V\*]); good for holloways and pits | (svf - 0.85) / 0.15, clip [-1, 1] |
| 4 | Slope | contract `slope` | Terrace scarps, holloway walls; also conditions confusers (landslides on steep slopes) | degrees / 45, clip [0, 1.5] |
| 5 | Fill depth | derived: DTM filled by morphological reconstruction minus DTM | Direct closed-depression signal (cellars, wells, craters, windthrow pits) | clip [0, 2.5] m, divide by 2.5 |
| 6 | Support | contract `ground_density` -> log1p(points per 0.5 m cell) / log1p(8), plus a binary mask (§2.3) | Lets the model learn that low support means unreliable relief | as stated |

Not used as model inputs, with reasons:

- **Raw DTM elevation and absolute position.** They encode location, not form. A model given altitude or coordinates learns "valley floor band of known villages", which is the circular prior 06 problem 3 warns against.
- **Hillshade.** Illumination-dependent and redundant given slope and LRM. It stays the main view for human and VLM review.
- **Historical layers** (1852 cadastre, WIG, 1944 orthophoto, PRG precinct membership, distance to village centre). Evaluation-only (§3.5).
- **Canopy-height or first-return layers** (05 §5.3, 06 §7). Possibly useful (old orchard trees mark farmsteads), but they are a location prior for settlement, not evidence of the feature. Candidate for a later ablation, not for stage 1.

Scales follow the targets: a cellar is 2-8 m across, a platform 6-20 × 4-12 m [05 R1-R2, D], a holloway 1.5-6 m wide [05 R3, from Affek 2016]. LRM 5 m and LRM 20 m bracket that range. The 128 m patch shows a platform with its neighbours, which matters because farmsteads occur in rows (05 R5).

### 2.3 Support mask and no-data

- Contract `ground_density` is the count of class-2 points per 0.5 m cell. Single empty cells are normal (14.8% in 2023 forest). The mask is therefore defined on a neighbourhood: **supported = at least 1 ground point in the surrounding 2 × 2 m window (4 × 4 cells)**, computed in `ml/channels.py`. Proposed product for the contract: an interpolation-distance raster (distance to the nearest ground point), which 06 §7 also asks for. Threshold: unsupported where distance > 1.0 m [D, tune on K1 sheets].
- Training: pixels outside support are excluded from the loss (masked), not set to zero.
- Inference: candidates whose footprint is more than 30% unsupported are still emitted, with a flag `low_support` in provenance and a score cap. They are never silently dropped, because 06 problem 3 notes that a real cellar can fail to appear where density is poor.
- Coverage reporting: every metric states the share of the evaluation area that is supported. Recall is reported twice: over all reference features, and over reference features in supported terrain.
- No-data outside the AOI or the tile: zero after scaling plus support = 0. Patches with more than 50% no-data are not sampled for training.

### 2.4 Patches, overlap and edges

- Training patch: **256 × 256 px = 128 × 128 m**, sampled on the fly with rasterio windowed reads from the COGs. No bulk export of overlapping patches to disk (§6.3).
- Classifier chip (stage 2): **96 × 96 px = 48 × 48 m** centred on a candidate. Large enough for a 20 m platform plus surroundings.
- Inference: 256 px windows with a stride of 192 px (25% overlap). Only the central 192 × 192 px of each window is kept (a 32 px = 16 m margin is discarded), so every output pixel sees at least 16 m of context in each direction. SVF (10 m) and LRM (20 m) are computed on buffered tiles upstream (contract `ldp process`), so the channels themselves have no tile-edge artefacts.
- Augmentation: the 8 rotations and flips (relief channels are rotation-equivariant once hillshade is excluded); small elevation-scale jitter (±10%) on LRM and fill depth; no colour jitter; no synthetic object insertion in the first stages (05 §5.4 item 5; 06 cut list).

---

## 3. Labels

### 3.1 Annotation schema

Labels are `Candidate` rows (08) plus an ML label table that the API does not need to serve. Fields:

| Field | Values | Notes |
|---|---|---|
| `candidate_id` | FK to `Candidate` | Geometry and `morph_class` live on the Candidate |
| `morph_class` | contract enum: house_platform, cellar_pit, terrace, holloway, field_boundary, cemetery, church_site, other | **Proposed contract additions:** `well`, `stone_mound`. Until then, wells go in `cellar_pit` with `subclass=well` |
| `label` | target / confuser / unsure | Binary target decision for training |
| `confuser_class` | windthrow, charcoal_hearth, dugout_ww2, trench_ww1, logging_road, skid_trail, boar_rooting, quarry_borrow, drainage_ditch, suffosion, landslide, slash_pile, crater, oil_pit, dtm_artefact, modern_structure, other | From 05 §7. Required when `label=confuser` |
| `certainty` | 1 (possible), 2 (probable), 3 (clear) | Annotator's, not the model's |
| `geometry_kind` | point, polygon, line | Cellars and wells as points plus optional polygon; platforms as polygons; linear classes as lines |
| `views_used` | subset of {svf, lrm20, lrm5, slope, hillshade, profile, 2012} | |
| `informed_by` | none, cadastre, wig, ortho1944, published_map, other | **"none" is mandatory for evaluation labels** (§3.5) |
| `label_source` | manual_scan, candidate_review, published_digitised, weak_cadastre, weak_ortho1944 | |
| `annotator_id`, `annotated_at`, `seconds_spent` | | Time per decision feeds the review-budget metric |
| `scan_cell_id` | 100 m cell | Ties the label to an exhaustively scanned cell |
| `split_role` | train, dev, lockbox, eval_only | Assigned per village before labelling starts (§5.1) |
| `sensitive` | bool | Graves, bunkers, hideouts, UXO-suspect. Forces `disclosure=restricted` (§9.2) |

A separate `scan_cells` table records, per 100 m cell: annotator, date, views, minutes, and `complete: bool`. Negatives for training and false positives for evaluation are only defined inside complete cells. Outside them, an unlabelled object is unlabelled, not negative (positive-unlabelled setting [06 §7]; survey: Bekker & Davis 2020, *Machine Learning*, 10.1007/s10994-020-05877-5 [C, Crossref]).

### 3.2 Annotation protocol

1. **Systematic scan first** (this is K4). In QGIS or the frontend, walk 100 m cells in a fixed order at a fixed scale (1:500 to 1:1,000), with SVF and LRM 20 m side by side, a profile tool for anything uncertain, and **all historical overlays switched off**. Mark the cell complete when done.
2. **Class definitions frozen in writing** before the first cell, with 2-3 reference images per class and per confuser, and the decision rules (for example: "pit with an adjacent downslope mound of similar volume, random orientation -> windthrow").
3. **Second, informed pass** (optional, separate layer): the annotator may switch on the 1944 orthophoto and cadastre and add or re-class features, recorded with `informed_by`. These labels may later be used for training but never for evaluation.
4. **Time logging**: every label and every complete cell records seconds spent.
5. **Uncertainty is a label, not a gap**: `unsure` items are kept and excluded from both training and metrics, with their count reported.

### 3.3 The first few hundred labels, cheaply

In order of cost per useful label:

1. **Candidate review instead of drawing.** Run the K6 rules (closed depressions, rectangular positive-LRM blobs, linear depressions) and review their output in the frontend with keyboard accept/reject/confuser buttons. A binary decision on a pre-drawn candidate is several times faster than drawing [D, to be measured]. Caveat: labels obtained this way inherit the rules' recall limits, so they are combined with step 2.
2. **K4 manual scan** of the two pilot villages, which is already in the plan. It provides the only labels with known completeness.
3. **Confuser positives from public datasets**: relict charcoal hearth points (Słowiński et al. 2026, ESSD, 10.5194/essd-18-493-2026; few in mountains [05, V]); forest roads and ditches from BDOT10k/OSM for logging-road and drainage negatives. Each is checked by eye before use.
4. **A no-settlement control sheet** (06 problem 4): one forest sheet with no village history in any source. Everything there that looks like a target is either a confuser or something interesting from another period; it is labelled like any other cell. This sheet supplies the raw confuser density and most hard negatives.
5. **Published interpretations** (Affek et al. 2022 figure maps; the IALE 2019 poster; Affek 2016 map) digitised **only for evaluation**, and only after asking the authors (06 moderate issue 13: the Wolski poster is unpublished).

Per-class minimums before any model is trained for that class [D]: **50 positives from at least 2 villages** for the LightGBM re-ranker; **150 positives from at least 2 villages** for a CNN. Classes below the minimum stay rule-only. 06 problem 4 predicts that roads and terraces will reach these numbers long before cellars and wells.

### 3.4 Negatives strategy

- **Hard negatives are labelled, not assumed.** Every confuser class in 05 §7 gets its own `confuser_class` value. The model is trained target-vs-rest, but metrics are also broken down by confuser class, so we know which confuser is driving false positives.
- **Sampling ratio** for training: per batch about 1/3 target-centred patches, 1/3 confuser-centred, 1/3 random patches from complete scan cells [D]. Random patches keep the model calibrated to background terrain.
- **Sensitive confusers.** WWII dugouts, UPA hideouts, shell craters and suspected graves are labelled with `sensitive=true`. They are useful hard negatives for "cellar" and must never leave the restricted tier (§9.2).
- **Ephemeral confusers** (boar rooting, slash piles, fresh skid trails) can be checked against 2012 where 2012 support is adequate. That is a reviewer aid, not a training signal.

### 3.5 Weak labels and circularity

06 problem 3 and the ML-researcher section are explicit: the cadastre and the 1944 photo should be evaluation data until their value is measured, and the system must not be built to confirm the map. Rules:

1. **Phase 1 (until K8): historical sources are evaluation-only.** 1852 cadastre building symbols, 1944 orthophoto roofs, WIG settlement extents and 1921 building counts are used as independent denominators (§5.4) and to stratify results (inside vs outside mapped settlement). They are not model inputs, not training labels, and not ranking priors.
2. **Evaluation labels are blind.** Only labels with `informed_by=none` count as reference features. The author has read the poster (06 problem 4), so full blindness is impossible; the mitigation is that lockbox-village labels are made before any model output exists for that village, by the second interpreter if one is found, and their file hash is recorded.
3. **Phase 2 (after K8, optional): weak supervision with an ablation.** If historical sources are used for training, use them as **bag labels** ("this cadastral parcel contains at least one building remain"; multiple-instance learning), not as pixel masks, because building remains lie within the parcel but not at the mapped spot [05, Affek 2016]. Keep at least one village where they are never used for training, and report results separately for features **outside** mapped settlement, which is the stratum where the project could add something.
4. **Inputs stay terrain-only** in both phases. A model that cannot see the cadastre cannot be accused of copying it.

### 3.6 Agreement

- **Second interpreter**: maps 25% of the scan cells of each pilot village (stratified: core, margin, control sheet), blind to the first annotator's layer. Report object-level F1 per class using the matching rules in §5.3, and Cohen's kappa on accept/reject for a shared set of 200 rule candidates.
- **If no second person is available**: intra-rater agreement (the same annotator re-maps 10% of cells after at least 4 weeks, without looking at the first pass). Report it as intra-rater, never as inter-annotator.
- **Gate** (K4): house-related classes with F1 below about 0.5 between mappers mean no automated number will mean anything (06 §6). The agreement level is also the ceiling quoted next to every model score.

### 3.7 Active-learning loop with the frontend

The review tool (08 `/explore`) is the labelling tool. Per review session, the queue for a village mixes:

| Share | Source | Purpose |
|---|---|---|
| 50% | Top of the current ranking | What the reviewer would see in production; estimates precision@k |
| 25% | Score band of maximum uncertainty (calibrated p near 0.3-0.7) | Most informative labels for retraining |
| 25% | Uniform random over all candidates above a low floor | Unbiased estimate of recall and of precision across the score range |

Rules: the reviewer sees no model score until after the decision (anchoring; 05 §10.4); VLM output, if any, is hidden the same way. Active-learning labels are biased towards hard cases, so they are used for training only. Evaluation uses the random slice, complete scan cells, and lockbox villages. Each retraining is a new `model_version`; the label snapshot (hash of the label table) is stored with it.

---

## 4. Model options

### 4.1 Comparison

| Option | Evidence | Labels needed | CPU cost | Verdict |
|---|---|---|---|---|
| **A. Morphometric rules** (fill depth, area, compactness, rectangularity, LRM sign, linear tracing) | De facto first stage in 05 §5.1 (O2); Trier & Pilø 2012 pit detection [03, U] | Thresholds only; tuned on dev village | Minutes per km² | **Stage 0. Candidate generator with high recall** (K6) |
| **B. Gradient boosting / random forest on handcrafted features** (per candidate: depth, area, shape indices, multi-scale LRM and slope statistics, fill-depth profile, support, neighbourhood counts) | Guyot, Hubert-Moy & Lorho 2018, *Remote Sensing* 10(2):225, 10.3390/rs10020225: multi-scale topographic position + Random Forest for Neolithic mounds [C, Crossref abstract; the snippet counts 2,952 TP / 41 FP are not verified, 03] | About 50 positives per class | Seconds to train; milliseconds per candidate | **Stage 1. The baseline every learned model must beat** |
| **C. CNN chip classifier** (ResNet-18/34 or EfficientNet-B0 from `timm`, first conv adapted to 6 channels) re-ranking rule candidates | Somrak, Džeroski & Kokalj 2020, *Remote Sensing* 12(14):2215, CNN on ALS visualisations of Maya structures [C, Crossref title]; Landauer et al. 2025 ConvNeXt on vignettes, precision 0.26 [05, V\*] | About 150 positives per class | Hours on CPU | **Stage 2, if B plateaus** |
| **D. U-Net segmentation** (`segmentation-models-pytorch`, ResNet-18/34 encoder, ImageNet weights, 6 input channels) | Banasiak et al. 2022, Białowieża ISOK data: pixel F1 0.58, IoU 0.50; IoU 0.41 for field-system banks [C, Crossref abstract]; Bundzel et al. 2020 U-Net vs Mask R-CNN on Maya LiDAR [03, U] | Polygons/lines; about 150 objects per class | Hours to a day on CPU | **Stage 3, for linear classes** (holloways, terraces, boundaries) where rules are weakest |
| **E. Object detection** (Faster R-CNN, Mask R-CNN, YOLO) | Trier, Reksten & Løseth 2021, *IJAEOG* 95:102241, 10.1016/j.jag.2020.102241, Faster R-CNN on Norwegian ALS [C, Crossref title; numbers in 03/05 unverified]; WODAN2 [05]; Guyot et al. 2021 Mask R-CNN mAP 0.29-0.77 on a random split [05/03, V]; Peck et al. 2026 [05] | Boxes or masks; hundreds | Heavier than C on CPU | **Not recommended initially.** For compact objects, rules + C is equivalent and cheaper; boxes fit linear classes badly. `ultralytics` (YOLO) is AGPL-3.0 [C, PyPI metadata], a licence decision for an open project; torchvision detectors are BSD |
| **F. Self-supervised pretraining on unlabelled DTM tiles** | Kazimi & Sester 2023, *JCAA* 6:155-173, 10.5334/jcaa.110: pretext tasks predicting relief visualisations from 0.5 m DTMs (200,000 unlabelled patches, Lower Saxony), HRNet; downstream mIoU 63.18 vs 62.64 random init vs 62.85 ImageNet, with about 4,400 labelled objects [C, paper page read; gains about 0.5 mIoU, single runs] | None for pretraining | Days on CPU for a meaningful pretext run | **Deferred.** Published gain is small and was shown with thousands of labels, not tens. Revisit only if stage 2 is label-starved and a GPU is available |
| **G. Foundation models** (SAM-style; remote-sensing FMs) | SAM: Kirillov et al. 2023, arXiv 2304.02643 [C, arXiv]. Landauer & Klassen 2025, *Geomatics* 5(4):52: zero-shot SAM 2.1, GPT-4.1, Gemini 2.0-flash on satellite, LiDAR and drone imagery, claimed "roughly human-expert" level [A, search summary; metrics not read]. Remote-sensing FMs are mostly trained on optical/multispectral satellite imagery at metre to decametre scale [M] | None | SAM ViT-B on CPU: seconds per image [M] | **Not as a detector.** Possible use as a click-to-polygon helper in the review UI (point prompt -> platform outline). Benchmark only after K6 |
| **H. VLM triage** (as in the Maya post) | No evaluation for temperate-forest micro-relief [05]. The Maya post used "no special model or classifier" and produced a rediscovery [05, V\*] | None | API cost per chip | **K7 only:** a fixed 300-chip benchmark with known prevalence, fixed prompt and model ID, hard budget; secondary filter or second reader, hidden from the reviewer until they decide; never decides reality, class or novelty |

### 4.2 Recommended staged path

```
Stage 0  rules (A)                       -> candidates, recall vs K4 labels        [K6]
Stage 1  LightGBM re-ranker (B)          -> must beat rule score at fixed budget   [ML-1]
Stage 2  CNN chip re-ranker (C),          -> must beat stage 1                      [ML-2]
         or frozen-CNN embeddings + LightGBM (cheaper variant of C)
Stage 3  U-Net for linear classes (D)    -> must beat rule tracing                 [ML-3]
Side     VLM benchmark (H)               -> must beat stage-1 ranking at equal time [K7]
Later    weak supervision, SSL, FMs      -> only after K8, each with an ablation
```

Why this order:

- The candidate generator decides recall; re-rankers decide precision at the top. Separating them makes each measurable.
- Stage 1 features are interpretable (a reviewer can see "depth 1.1 m, rectangularity 0.8") and need few labels. Gradient boosting with monotone constraints (e.g. score not decreasing with rectangularity for platforms) limits overfitting on small data [D].
- A frozen ImageNet encoder producing a 512-d embedding per chip, fed to LightGBM with the handcrafted features, costs one forward pass per candidate and no backpropagation. It is the cheapest test of whether CNN features help at all [D].
- U-Net is reserved for linear classes because rule-based tracing of holloways and terraces across 7-8 overlapping strips is fragile (06 moderate issue 6), and because the one automated result for hollow roads is a CNN (CarcassonNet: Verschoof-van der Vaart & Landauer 2021, *J. Cultural Heritage* 47:143-154, 10.1016/j.culher.2020.10.009 [C, Crossref title]; MCC 0.47 from 03, unverified).

**Promotion rule:** a stage replaces the previous one only if, on leave-village-out evaluation, its recall at the fixed review budget (§5.2) is higher by at least 0.10 absolute **and** the 90% cluster-bootstrap interval of the difference excludes zero, in at least 2 held-out villages [D]. Otherwise the simpler stage stays.

---

## 5. Evaluation

### 5.1 Splits

- **Primary: leave-village-out.** Each fold holds out one whole PRG precinct plus a 250 m buffer around it (no training patch may overlap the buffer). Rationale: random splits overstate performance on unseen areas (Roberts et al. 2017, *Ecography* 40:913-929, 10.1111/ecog.02881 [C, Crossref abstract]; Ploton et al. 2020, *Nature Communications*, 10.1038/s41467-020-18321-y [C, Crossref title]). Guyot 2021 used random splits, a known weakness [03, V].
- **Within-village blocks** (500 m blocks, 128 m buffers) are used only for hyperparameter choice inside the training villages, never for reported results.
- **Lockbox villages.** Before any model is trained, assign 2 of the K8 villages as lockbox: labelled blind, hashed, and opened once, after the protocol and thresholds are frozen in writing (06 §7: "freeze the protocol in writing before K8").
- **Thresholds and calibration are never tuned on a test village** (06 §7).
- With 2-3 pilot villages there are 2-3 numbers. They are reported **per village**, not averaged, and no pooled interval is claimed from them (06 problem 4).

### 5.2 Metrics

Reported per class, per village, with the prevalence and the support share of the area:

| Metric | Definition | Why |
|---|---|---|
| **Recall at review budget B** | Share of reference features (complete cells, `informed_by=none`) matched within the top B candidates per km². B fixed in advance, e.g. 10, 20, 50 per km² | The operational question: what does a reviewer catch for a given effort |
| **Precision@k** | Matched candidates among the top k (k = 25, 50, 100 per village), with a Wilson 90% interval | Comparable to Landauer et al.'s top-k reporting [03, V] |
| PR-AUC (average precision) | Over all candidates in complete cells | Threshold-free summary; always shown next to prevalence, which is its chance level |
| FP per km² by confuser class | Unmatched top-B candidates broken down by the reviewer's confuser label | Shows which confuser to fix |
| Reviewer minutes per accepted feature | From logged `seconds_spent` | K6 criterion (at least 2× faster than tile scanning at equal recall) |
| Calibration | Reliability diagram and expected calibration error on dev villages | §5.5 |

Not reported as headlines: pixel IoU, mAP alone (it hid FP rates in prior work [03]), accuracy (meaningless at 1-10% prevalence), any random-split score.

### 5.3 Object matching

One-to-one matching (Hungarian assignment on distance) between candidates and reference features of the same class [D]:

| Class | Match if | Tolerance rationale |
|---|---|---|
| Cellar pit, well, stone mound | Centroid distance ≤ 3 m | Objects 2-8 m across; annotator digitising error about 1 m |
| House platform | Candidate centroid inside the reference polygon buffered by 3 m, **or** IoU ≥ 0.25 | Platform edges are diffuse |
| Church site, cemetery | IoU ≥ 0.25 or centroid inside the polygon | Large, diffuse |
| Holloway, terrace, field boundary | Length-based: completeness = reference length within 3 m of a prediction ÷ reference length; correctness = predicted length within 3 m of reference ÷ predicted length | Standard buffer method for linear-feature extraction [M: Heipke et al. 1997, road extraction; verify before citing] |

Fiorucci et al. 2022 propose centroid-based and pixel-based measures for archaeological object detection on LiDAR and show they track archaeologists' semi-automatic assessment [C, Crossref abstract, *Remote Sensing* 14(7):1694, 10.3390/rs14071694]. The tolerances above are a starting point to be fixed in the frozen protocol, not tuned on results.

### 5.4 Independent denominators

Model recall against our own labels measures the model. It does not measure what fraction of the village we find. Three numbers are reported side by side per village (06 problem 4):

```
(a) visibility ceiling   = house-related LiDAR features mapped by hand  ÷  houses known to have existed
(b) model recall         = (a)-features found within budget B           ÷  (a)-features
(c) end-to-end recall    = (a) × (b)
```

with "houses known to have existed" taken separately from **(i) the 1921 census building count for the locality, (ii) building symbols on the 1852 cadastre (expected to undercount the 1939 state, 06 moderate issue 3), (iii) roofs counted on the 1944 orthophoto** (licence to be checked, 06 problem 5). Disagreement among the three is reported, not resolved. Where the 1944 photo can be georeferenced well enough, (a) can also be computed per roof (matched within 20 m) rather than per count.

Stratification: every recall and precision figure is also given **inside vs outside** mapped settlement (cadastre/WIG/1944 extent). A model that only works inside the mapped band reproduces the map; the outside stratum is where the project's added value would lie (06 problem 3).

### 5.5 Calibration and confidence

- The `confidence` written to a Candidate is a **calibrated score**: isotonic regression (or Platt scaling when fewer than about 200 labelled candidates) fitted on dev villages only [D; background: Guo et al. 2017, "On calibration of modern neural networks", arXiv 1706.04599 [C, arXiv]].
- A probability calibrated in one village is valid only at that village's prevalence. The model card states the calibration villages and their prevalence; the UI labels the number "score (calibrated on Caryńskie + X)", not "probability".
- Uncertainty of the score: train 5 models (fold or seed ensemble); store the mean as the score and the spread as `score_sd` in provenance. Large spread is a reason to send a candidate to the uncertainty slice of the review queue.

### 5.6 Reporting uncertainty

- Precision@k: Wilson interval (binomial, k trials).
- Recall and PR-AUC: **cluster bootstrap over 250 m blocks** within a village (features in one block are not independent), 1,000 resamples, 90% interval.
- Across villages: show the per-village points; do not compute a cross-village interval from 2-3 villages.
- Every result table carries: model_version, label snapshot hash, DTM recipe hash, evaluation villages, prevalence, support share, agreement ceiling, date.

### 5.7 Red-team tests (run before any result is quoted)

| # | Test | Pass condition [D] |
|---|---|---|
| R1 | **Control sheet** with no settlement history: predictions per km² above the operating threshold | At most about a quarter of the rate inside villages; everything above threshold is reviewed and its confuser classes reported |
| R2 | **Label permutation**: retrain with shuffled labels | Leave-village-out PR-AUC falls to prevalence. If not, there is leakage |
| R3 | **Location-only model**: LightGBM on slope, altitude, distance to stream and support only (no relief form) | Must score clearly below the real model. If it nearly matches, the model is learning "where villages are", not "what features look like" |
| R4 | **Inside/outside mapped settlement** (§5.4) | Precision outside is reported; a collapse outside is a finding, not something to hide |
| R5 | **Epoch swap**: apply the 2023 model to the 2012 DTM of the same village | Expected to degrade; quantify it, and never ship 2012 predictions without a 2012-specific evaluation |
| R6 | **Artefact sheet**: a sheet with strip seams and dense young conifers (low support) | No more than the control-sheet FP rate in supported terrain; low-support candidates correctly flagged |
| R7 | **Known-negative challenge set**: charcoal hearths from the Słowiński dataset, mapped forest roads, ditches | Report the share ranked in the top B; this is the hard-negative recall of the confuser filter |
| R8 | **Rotation and flip consistency**: score the same candidate under 8 orientations | Score spread small compared with the decision margin |
| R9 | **Known-check red team** (06 problem 2), shared with the non-ML pipeline: 50 certainly known features | Not an ML test, but ML candidates are never released before it passes |

---

## 6. Hardware and compute

### 6.1 Assumptions

Windows 11 laptop, 8-16 CPU threads, 16-32 GB RAM, no CUDA GPU. Python 3.12 via `uv` (08). All packages below have Windows wheels for Python 3.12 on PyPI [C, PyPI JSON 2026-11-13]:

| Package | Version seen | Wheel |
|---|---|---|
| torch | 2.15.0 | cp312 win_amd64 |
| timm | 1.0.31 | py3-none-any |
| segmentation-models-pytorch | 0.6.0 | py3-none-any |
| scikit-learn | 1.9.1 | cp312 win_amd64 |
| lightgbm | 4.7.0 | py3-none-win_amd64 |
| rasterio | 1.5.2 | cp312 win_amd64 |

Plus `scikit-image` (morphological reconstruction, regionprops) and `scipy` for the rules and features [M: wheels not re-checked today]. The PyPI Windows build of torch is the CPU build; CUDA builds come from PyTorch's own index [M]. ML packages go in an optional dependency group (`uv sync --extra ml`) so the core framework stays light. Pin exact versions in `uv.lock`; the model card records them.

### 6.2 Data volumes [D]

- 0.5 m grid: 4 M pixels per km². Six float32 channels: 96 MB/km² uncompressed; the contract COGs (deflate, float32) are probably 30-60% of that.
- Pilot (two precincts plus buffers plus one control sheet, about 40 km²): about 4 GB of channels uncompressed, less as COGs. The two derived channels (LRM 5 m, fill depth) are written as COGs alongside the contract products.
- Training patches are read on the fly with windowed reads; no patch store. An optional cache of chips (96 × 96 × 6, float16 = 110 KB each) for 20,000 candidates is about 2.2 GB.
- Region (3,000 km² of 2023 data): about 290 GB uncompressed channels; on the order of 100 GB as COGs. This does not fit a laptop disk comfortably and is not needed before K8. Process and predict per precinct, keep only candidates.

### 6.3 Runtimes [D, rough; measure in ML-1]

| Task | Size | Estimate on an 8-core laptop |
|---|---|---|
| Rule candidates + handcrafted features | 1 km² | 1-3 min (scikit-image, scipy) |
| LightGBM training | 20,000 candidates × 100 features | Under 1 min |
| LightGBM scoring | 1 km² | Seconds |
| Frozen ResNet-18 embeddings for chips | 20,000 chips of 96 px | 5-15 min |
| CNN chip classifier fine-tuning (ResNet-18) | 5,000 chips × 30 epochs | 1-3 h |
| U-Net (ResNet-18 encoder) training | 4,000 patches of 256 px × 40 epochs | 10-30 h; run overnight, or use 128 px patches and a ResNet-18 encoder to cut this by about 4× |
| U-Net inference | 1 km² ≈ 110 windows of 256 px at 25% overlap | 10-60 s |
| U-Net inference, whole region | 3,000 km² | 8-50 h; per-precinct batches only after K8 |

If stage 3 needs more than one overnight run per experiment, rent a GPU for the training step only; inference stays local. This is a cost decision for the owner, not a design requirement.

---

## 7. Integration with the framework

### 7.1 Module layout

```
src/lidar_discovery/
  detect/                     # non-ML, shared with K6 (could also live in processing/)
    rules.py                  # closed depressions, positive-LRM blobs, linear depressions -> raw candidates
    morphometrics.py          # per-candidate handcrafted features
  ml/
    __init__.py
    channels.py               # read contract COGs, derive lrm5 + fill_depth + support mask, fixed scaling
    labels.py                 # label table + scan_cells table (SQLModel), snapshots and hashes
    splits.py                 # village folds, buffers, lockbox registry
    sampling.py               # on-the-fly patch/chip sampler (rasterio windows), augmentation
    models/
      gbm.py                  # LightGBM re-ranker (stage 1)
      chipnet.py              # timm encoder chip classifier / embedding extractor (stage 2)
      unet.py                 # smp U-Net for linear classes (stage 3)
    train.py
    predict.py                # sliding window / chip scoring -> objects -> Candidate rows
    postprocess.py            # pixel probabilities -> polygons/lines, NMS, support flags
    evaluate.py               # matching, metrics, bootstrap, red-team runners
    calibrate.py
    registry.py               # model store, model cards, provenance
    vlm.py                    # K7 benchmark only; disabled unless configured with a budget
data/models/<model_version>/  # weights, card.json, card.md, metrics/, label_snapshot.sha256
```

### 7.2 CLI (`ldp ml ...`)

| Command | Does |
|---|---|
| `ldp ml channels <location> --epoch 2023` | Derive LRM 5 m, fill depth and the support mask as COGs; registers them as Products (`kind=lrm5|filldepth|support`) |
| `ldp ml export-patches --locations a,b --kind chips|patches --out ...` | Optional cache of chips/patches with a manifest (CRS, transform, channel spec hash). Normally training reads on the fly |
| `ldp ml splits --assign` | Write the village fold and lockbox registry; refuses to change a lockbox once labels exist |
| `ldp ml train --stage gbm|chip|unet --classes cellar_pit,house_platform --folds leave-village-out` | Train one model per fold plus a final model; writes `data/models/<model_version>/` |
| `ldp ml predict <location> --model <model_version> [--budget 20]` | Score candidates or run sliding-window inference; insert Candidates (§7.3); refuses lockbox villages unless `--open-lockbox` with a protocol hash |
| `ldp ml evaluate --model <model_version> --villages ... [--redteam all]` | Metrics of §5 with intervals; writes `metrics/*.json` and a markdown report |
| `ldp ml card <model_version>` | Render the model card |

### 7.3 Outputs as Candidates

Each ML output becomes a `Candidate` (08) with:

- `origin = ml`, `model_version = <stage>-<yyyymmdd>-<shorthash>`
- `morph_class` = argmax class; per-class scores in provenance
- `reality = unassessed` (the reviewer sets it), `review_status = proposed`
- `confidence` = calibrated score (§5.5). **Contract note:** in 08 the confidence belongs to `reality`, which is a reviewer judgement. Mixing a model score into it is ambiguous. **Proposed contract change:** add `model_score` (0-1) and `model_rank` (per location) to Candidate and keep `confidence` for the reviewer. Until 08 is changed, the score goes into `confidence` only while `reality = unassessed`, and is also stored in provenance.
- `disclosure = restricted` by default for every ML candidate until reviewed (§9.2)
- `documentation_status` empty; filled by the known-check, never by the model
- provenance JSON: run ID, model_version, input Product IDs and hashes, DTM recipe hash, channel spec hash, support fraction, `low_support` flag, `score_sd`, git SHA

Duplicates across runs: a new candidate within the matching tolerance (§5.3) of an existing candidate of the same class is linked to it, not duplicated, so review history is kept. This is the minimal form of the "stable feature ID" that 06 cut for the pilot.

### 7.4 Model cards and provenance

`card.json` + `card.md` per model_version: intended use ("ranking for human review; not a detector; not for dating or novelty claims"); training villages and label snapshot hash; per-class label counts; channels and scaling constants; DTM recipe and epoch; leave-village-out metrics per village with intervals, prevalence and support share; agreement ceiling; red-team results R1-R8; known failure modes (top confuser classes); package versions; compute used; licence of inputs (GUGiK) and of any third-party weights (ImageNet weights via `timm` carry their own terms [M; check per weight]).

---

## 8. Milestones and kill criteria (desk-only)

The non-ML gates come from 06 §6, adjusted by 07 (no field step). **No ML work starts until K1, K2, K3, K4 and K6 have passed.**

| Gate | Question | Desk-only form | Stop or pivot if |
|---|---|---|---|
| K1 | Can a person see house-scale features in 2023? | As 06 | Fewer than about half of 1944/poster house positions show any earthwork: the target is roads and terraces; ML for platforms/cellars is dropped |
| K2 | Does class 12 help? | As 06 | Decides the DTM recipe that all models are tied to |
| K3 | What is already known? | As 06; also gives the denominators (§5.4) | Existing sources place every house within about 20 m: the contribution is a condition survey and ML adds little |
| K4 | Is manual mapping reliable? | As 06, with a second interpreter or (weaker) intra-rater agreement; produces the first labels and scan cells | House-class F1 between mappers below about 0.5: no ML |
| **K5'** (replaces field K5) | Are mapped features plausibly real? | Blind second-interpreter review of a stratified random sample of 100 mapped features; for house classes, consistency with the 1944 photo and cadastre; profile check against strip seams | Less than about half of house-class features survive the blind review: tighten class definitions before any model. Note: this is a plausibility check, not field truth; no output may say "confirmed" (07) |
| K6 | Do rules save reviewer time? | As 06, plus the control-sheet confuser density | Ranked review not at least 2× faster than scanning at equal recall: drop automation, scale by people |
| **ML-0** | Are there enough labels? | Count per class (§3.3) | Below 50 positives in 2 villages for every class: no learned model; stay with rules |
| **ML-1** | Does a LightGBM re-ranker beat the rule score? | Leave-village-out, promotion rule §4.2 | No gain: rules stay; stop ML for that class |
| **ML-2** | Do CNN features add to ML-1? | Frozen embeddings first, then fine-tuning | No gain over ML-1: stop CNN work |
| **ML-3** | Does U-Net beat rule tracing for linear classes? | Length-based completeness/correctness | No gain: keep rules for linear classes |
| K7 | Does a VLM add anything? | 300-chip benchmark (06 §6) | No gain over the ML-1 ranking at equal reviewer time: drop |
| K8 | Does it transfer? | 8-10 precincts chosen by density and land-use history; frozen protocol; lockbox villages opened once | Recall against the independent denominators collapses outside the pilot: no regional run; publish the negative result |

Only after K8: weak supervision (§3.5 phase 2), SSL, any regional inference, and any public aggregate derived from ML output.

---

## 9. Risks, ethics and open questions

### 9.1 Risks

| # | Risk | Mitigation |
|---|---|---|
| M1 | Too few positives for the valuable classes (cellars, wells, platforms) | Per-class minimums; classes below them stay rule-only; report it |
| M2 | The annotator is the ceiling, and the ceiling is unknown (06 problem 4) | Second interpreter; agreement reported beside every score |
| M3 | Circularity: model learns the settlement band | Terrain-only inputs; R3 location-only test; inside/outside stratification |
| M4 | Optimistic metrics from spatial leakage | Leave-village-out with buffers; lockbox; no thresholds tuned on tests |
| M5 | Domain shift between epochs, DTM recipes and density blocks | Model tied to epoch + DTM recipe hash; R5; no cross-domain prediction without evaluation |
| M6 | Active learning biases the evaluation set | Random slice and lockbox only for metrics |
| M7 | Strip seams and low support produce false linear features | Support mask; R6; per-strip checks from K2 |
| M8 | CPU training too slow for U-Net iteration | Smaller patches and encoder; frozen-encoder variant; rent a GPU for training only |
| M9 | Precision too low to be useful anywhere (the published norm) | The plan treats this as a valid outcome; K6/ML-1 kill criteria end the ML track cheaply |
| M10 | Persuasion by scores and VLM text | Scores and VLM output hidden until the reviewer decides; "score", not "probability", in the UI |

### 9.2 Ethics and sensitivity

- **Restricted by default.** Every ML candidate is `disclosure=restricted` until reviewed. Classes `cemetery` and `church_site`, and any label with `sensitive=true` (suspected graves, war graves, execution sites, UPA bunkers and hideouts, WWII dugouts, UXO-suspect craters), stay restricted after review unless already public and protected (08; 05 §8.4).
- **No probability rasters leave the machine.** A score map is a looting map. Public outputs, after K8, are aggregates per village or per ≥1 km² cell, as in 06 §9 and 05 §8.4; and no visible masks around sensitive places (06 moderate issue 8).
- **Training chips are not published** for restricted classes. A benchmark release (06 §9) uses only features already published by others, with their permission.
- **Named authorities.** Suspected war graves or execution sites go to the voivode and the IPN; Jewish cemeteries to the Rabbinical Commission for Cemeteries (06 moderate issue 9, [M] there; verify contacts before use). ML does not change this; it only makes such candidates more frequent.
- **Language.** No "discovery", "unknown" or "confirmed" in any ML output, card or report (06 problem 2; 07). The strongest statement is "LiDAR feature consistent with N independent historical sources".
- **Descendant communities.** ML-derived counts per village are part of the village story and are shared with descendant organisations before publication (06 §9).
- **Damage monitoring** (two-epoch) is not part of this plan; if ML is ever used for it, the results go to State Forests and the park first (06 moderate issue 10).

### 9.3 Open questions

1. Who is the second interpreter, and how many hours can they give? (K4, K5', lockbox labelling.)
2. Which villages are train, dev and lockbox? This must be fixed before labelling starts.
3. Contract changes: add `well` and `stone_mound` to `morph_class`, a label/confuser table, `model_score`/`model_rank` on Candidate, and an interpolation-distance (support) product.
4. 1944 orthophoto: licence and georeferencing quality decide whether it can serve as a per-roof denominator.
5. Can the published Caryńskie interpretations be digitised for evaluation with the authors' permission?
6. Is a rented GPU acceptable for stage 3 training, or is CPU-only a hard constraint?
7. Is YOLO (AGPL-3.0) acceptable if object detection is ever needed, or are BSD/Apache tools required?
8. Should canopy-structure features (old fruit trees, house plantings) be tested as an ablation after K8, given they are a settlement prior?

---

## 10. Sources used in this plan

Checked today [C]:

- Banasiak et al. 2022, *Remote Sensing* 14(4):995, 10.3390/rs14040995 (Crossref abstract)
- Guyot, Hubert-Moy & Lorho 2018, *Remote Sensing* 10(2):225, 10.3390/rs10020225 (Crossref abstract)
- Somrak, Džeroski & Kokalj 2020, *Remote Sensing* 12(14):2215, 10.3390/rs12142215 (Crossref title)
- Kokalj et al. 2023, "Machine learning-ready remote sensing data for Maya archaeology", *Scientific Data* 10:558, 10.1038/s41597-023-02455-x (Crossref abstract; a public annotated ALS dataset, useful as a pipeline test, not as training data for this region)
- Kazimi & Sester 2023, *JCAA* 6:155-173, 10.5334/jcaa.110 (paper page)
- Fiorucci et al. 2022, *Remote Sensing* 14(7):1694, 10.3390/rs14071694 (Crossref abstract)
- Trier, Reksten & Løseth 2021, *IJAEOG* 95:102241, 10.1016/j.jag.2020.102241 (Crossref title only; 03's DOI guess was wrong, this is the right one)
- Verschoof-van der Vaart & Landauer 2021, *J. Cultural Heritage* 47:143-154, 10.1016/j.culher.2020.10.009 (Crossref title only)
- Roberts et al. 2017, *Ecography* 40:913-929, 10.1111/ecog.02881 (Crossref abstract)
- Ploton et al. 2020, *Nature Communications*, 10.1038/s41467-020-18321-y (Crossref title)
- Bekker & Davis 2020, *Machine Learning*, 10.1007/s10994-020-05877-5 (Crossref title)
- Kirillov et al. 2023, "Segment Anything", arXiv 2304.02643; Guo et al. 2017, "On calibration of modern neural networks", arXiv 1706.04599 (arXiv API titles)
- PyPI JSON for torch, timm, segmentation-models-pytorch, scikit-learn, lightgbm, rasterio, ultralytics (versions, wheels, licence)

Abstract or search level [A/S]: Landauer & Klassen 2025, *Geomatics* 5(4):52 (zero-shot VFMs; metrics not read).

Taken from 03/05/06 with their tags: Landauer et al. 2025 (10.5334/jcaa.178); WODAN2 (10.3390/ijgi9050293); Peck et al. 2026 (10.1017/aap.2025.10130); Guyot et al. 2021 (10.5334/jcaa.64); Słowiński et al. 2026 (10.5194/essd-18-493-2026); Affek 2016 and Affek et al. 2022; the IALE 2019 poster; the one-tile QA in 06 §2.1.

Not verified, do not cite as fact: Trier 2021 and CarcassonNet performance numbers; Heipke et al. 1997 buffer metrics; remote-sensing foundation-model training data; the CPU runtimes in §6.3 (estimates to be measured).
