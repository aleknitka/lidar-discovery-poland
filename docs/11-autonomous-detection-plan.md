# 11 — Autonomous LiDAR Man-Made Detection Plan

Status: plan. Written 2026-11-15. Builds on `09-ml-detection-plan.md` (still binding for metrics/splits/ethics) and extends it toward a fully autonomous download → process → detect → tag → map loop for **any man-made vs natural anomaly** (not only house platforms). Sources checked today via web/paper search; tags [C]=primary record read, [A]=abstract only, [S]=search summary.

## 0. Summary

Autonomous does not mean unsupervised discovery. It means **no human in the download/process/inference loop**; a human remains the decision gate before any candidate is published. The system crawls GUGiK, builds relief rasters, scores every tile for geometric regularity, and enqueues ranked `Candidate` chips with image tags for one reviewer.

Staged detectors — rules → GBM re-ranker → CNN chip classifier → U-Net for linears → anomaly autoencoder — share the same terrain-only 6-channel input and the same object-level, leave-village-out evaluation. Transfer from the new large open datasets (Archaeoscape 888 km² / 31k features [C], ADAF 10k+ barrows/ringforts [A]) is the fastest path to bootstrap labels.

## 1. Goal restated

Detect geometrically regular, non-natural earthworks under forest from airborne LiDAR and tag each detection against the visualisations we already serve as image chips:

* **Positives:** house platforms, cellar/well pits, terraces, holloways, field-boundary banks, cemetery/church enclosures, stone mounds, charcoal hearths, WWII dugouts/trenches when distinguishable — any compact or linear form whose plan, profile and slope are inconsistent with natural terrain.
* **Negatives / confusers:** windthrow pits+mounds, suffosion/karst depressions, boar rooting, slash piles, logging roads/skid trails, drainage ditches, quarries, landslides, shell/dugout craters, modern structures, DTM artefacts (strip seams, low-support interpolation).
* **Tagging:** every `Candidate` stores `model_version`, calibrated `model_score`, `low_support` flag, footprint (EPSG:2180 + WGS84), and links to image chips: `hillshade.png`, `svf.png`, `lrm.png`, `slope.png`, `dtm_shaded.png` + optional `orto1944` chip. Frontend renders them in the review queue and on the map.

End product is a **ranked triage queue at fixed review budget B (e.g. 20 candidates/km²)** — see `09 §1` for why pixel IoU/mAP are not headline metrics.

## 2. State of art — what paper search actually yields for "not natural"

### 2.1 Raster-derivative + CNN (dominant paradigm, directly transferable)

All successful archaeology detectors convert the DTM to **illumination-invariant relief visualisations** and train a 2D CNN. Raw elevation/position are never inputs (location leak).

| Method | Data / task | Architecture | Reported result | Relevance to us | Source |
|---|---|---|---|---|---|
| **Archaeoscape** — first open ALS-archaeology dataset (888 km² Cambodia, 31k features: temples, mounds, hydro) | 0.5 m DTM + RGB + nDSM; segmentation | U-Net 50.5 IoU, DeepLabv3 47.6, ViT-S 46.4 (bg 87-88, mounds 47-49, temples 18-33) | 4× larger than prior sets; ImageNet-pretrained encoders transfer; code+weights on `archaeoscape.ai`; our best transfer base | [C] Perron et al., NeurIPS 2024 D&B — `proceedings.neurips.cc/...2d9ba88c...pdf` + `github.com/archaeoscape-ai/archaeoscape` |
| **ADAF** — automatic detection of archaeological features from ALS | 10k+ enclosures/ringforts/barrows | HRNet (segmentation) + Faster R-CNN (detection) | Tool built to be easy-to-use; large per-class sample; shows two-model ensemble works | [A] `sciencedirect.com/science/article/pii/S2352409X26001689` (2026) |
| **Maya broadscale** ConvNeXt hillfort detector | Yucatan G-LiHT LiDAR (published) | ConvNeXt (classification of vignettes) | Prec 0.26 @ Rec 0.71; 148/169 Hesse candidates >0.9 were obvious FP → human verification required | [A/C] Landauer et al. 2025 `10.5334/jcaa.178`; Springer 2025 `10.1007/s10816-025-09741-5` |
| **Białowieża 0.5 m ISOK** — same sensor as ours | Field banks, charcoal hearths, barrows in Polish forest (ISOK 4 p/m²) | U-Net (ResNet-34) on SVF/slope/LRM | Pixel F1 0.58 IoU 0.50 overall; IoU 0.41 for field-system banks | [C] Banasiak et al. 2022 `10.3390/rs14040995` |
| **CarcassonNet** — hollow roads (sunken lanes) | 0.5 m DTM Netherlands | CNN segmentation | MCC 0.47 (unverified number in prior notes) — only automated holloway result found | [C] Verschoof-van der Vaart & Landauer 2021 `10.1016/j.culher.2020.10.009` |
| **WODAN2** | Large random test area | CNN | Did not reach human performance (abstract) | [A] `10.3390/ijgi9050293` | 

**Takeaway:** hillshade is for humans; models want **SVF (16 dir, r=10 m), SLRM/LRM (r≈20 m), slope, openness, fill-depth** — the stack used in RVT `2.2.1` and in the IALE 2019 Bieszczady poster (SVF 16/10 m). `09 §2.2` already fixes this 6-channel input; no change needed.

### 2.2 Direct point-cloud methods (research track, not stage 1)

| Method | Idea | Fit for "man-made vs natural" |
|---|---|---|
| **Multi-level multi-resolution (MLMR) semantic segmentation** on ALS points — filters vegetation then detects structures directly on points | AI pipeline for both ground filtering and detection | Validates point-direct path, but needs dense labels and GPU; less mature than raster CNNs for cm-relief | [S] `isprs-archives.copernicus.org/.../isprs-archives-XLVI-2-W1-2022-365-2022.pdf` |
| **ForestFormer3D** — unified end-to-end forest LiDAR 3D segmentation (ICCV 2025) | Transformer on forest point clouds; individual tree + semantic | Strong vegetation/ground separation; could replace/enhance our ground filter (class-12 handling in K2) | [S] `openaccess.thecvf.com/...ForestFormer3D...ICCV_2025...pdf` |
| **PointDMM** — deep semantic segmentation for complex forests (1259 scenes, 214B points) | 4-class forest point labelling | Hard-negative mining for tree vs terrain; helps define confuser taxonomy | [A] `mdpi.com/1999-4907/14/12/2276` |
| **Point-cloud metrics for walls vs low vegetation** (ISPRS 2013) — multi-scale roughness s1=5 m, s2=3 m, s3=11 m | Handcrafted roughness separates standing masonry from scrub | Directly inspires our handcrafted features in `morphometrics.py` | [S] `isprs-archives.copernicus.org/.../XL-5-W2-459-2013.pdf` |

**Decision:** stage 1 stays raster. Point-cloud track is a K2 supporting experiment (better ground classification) and a stage-3 option for dense canopy where raster support collapses.

### 2.3 Unsupervised anomaly detection (label-scarce regime)

| Method | Idea | Use here |
|---|---|---|
| **Deep geometric descriptors** (WACV 2023, MVTec/Bergmann) — learn per-point descriptors on clean terrain, flag deviations via kNN distance | No man-made labels needed; flags any geometric regularity | Cold-start detector for new precincts; generates candidates for the labelling queue | [C] `openaccess.thecvf.com/.../Bergmann_Anomaly_Detection_in_3D_Point_Clouds...WACV_2023...pdf` |
| **VAE on 3D point clouds** (`arxiv 2304.03420`) — reconstruct normal patches, high reconstruction error = anomaly | Unsupervised 3D anomaly | Same idea on 2.5D DTM patches (autoencoder on LRM/SVF); cheap on CPU | [A] `arxiv.org/html/2304.03420v1` |
| **Synthetic LiDAR-derived data + DCNN** for cemeteries under forest (`npj Heritage Science 2025`) | Synthesize training cemeteries where labels missing | Pattern to synthesize cellar pits/platforms where 09 requires ≥150 positives/class | [A] `nature.com/articles/s40494-025-01798-5` |

**Decision:** add an **autoencoder anomaly channel** as a parallel candidate generator alongside morphometric rules. It needs no labels and catches the "unknown unknowns" — general man-made vs natural.

### 2.4 Visualization derivatives that matter

* **SLRM / LRM** — DTM minus low-pass (σ≈10 m, radius ≈20 m) isolates decimetre relief independent of slope; Hesse 2010 Local Relief Model; used in every Polish/Czech study above.
* **SVF / openness / sky-view factor** — 16 directions, 10 m radius is the de facto standard for holloways/pits.
* **Slope + fill-depth (morphological reconstruction)** — direct closed-depression signal (cellars/wells vs windthrow).
* **Support / interpolation-distance raster** — distance to nearest ground point; flags unreliable relief (`09 §2.3`). Requested as contract product.

All are implemented numpy/scipy in `processing/vis.py` (no RVT dependency on Windows) and provenanced as COGs.

## 3. Autonomous pipeline — what "autonomous" concretely means

```mermaid
flowchart LR
    Sched[[Scheduler<br/>APScheduler / cron<br/>per-precinct queue]] --> WFS
    WFS[GUGiK WFS<br/>KRON86 + EVRF2007<br/>Skorowidze sheets] --> DL
    DL[Downloader<br/>sources/gugik.py<br/>LAZ cache data/raw<br/>resume .part + Range] --> QAG[QA gate<br/>density + flight date<br/>from LAS header]
    QAG --> DTM[DTM 0.5m<br/>processing/dtm.py<br/>Delaunay TIN<br/>class-2 (+class-12 if K2)]
    DTM --> DER[Derivatives<br/>hillshade slope SVF LRM<br/>ground_density + support<br/>COG EPSG:2180]
    DER --> RULE[Candidate generators<br/>detect/rules.py<br/>closed dep. + LRM blobs<br/>+ linear tracing<br/>+ AE anomaly]
    RULE --> FEAT[morphometrics.py<br/>handcrafted features<br/>per candidate]
    FEAT --> RANK[ML re-ranker<br/>ml/models/gbm.py<br/>or chipnet/unet<br/>calibrated score]
    RANK --> CHIP[Chip export<br/>96px + 256px PNGs<br/>hillshade/SVF/LRM/ortho]
    CHIP --> CAT[(Catalog SQLite<br/>Candidate origin=rule/ml<br/>review_status=proposed<br/>disclosure=restricted)]
    CAT --> UI[/Explore /review<br/>ranked queue<br/>keyboard accept/reject/]
    UI --> LAB[(Label table<br/>target/confuser/unsure<br/>scan_cells)]
    LAB -. retrain .-> RANK
    CAT --> MAP[/Public map /catalog<br/>LDP_PUBLIC_MODE<br/>generalised/aggregated/]
    QAG -. reprocess .-> DTM
    WFS -. new epoch .-> DL
```

**Autonomy contract:**

1. Scheduler enumerates `seeds/locations.yaml` + PRG precincts intersecting the Bieszczady bbox, checks `TileCache` + `Product.provenance` freshness (30 d for WFS caps), and enqueues one `Job(kind=fetch-area)` at a time (existing `jobs.py` ThreadPoolExecutor(1); 2 parallel sheet downloads).
2. `estimate` runs first — if `bytes_to_download` or `area_km2` over `LDP_MAX_FETCH_*`, job waits for operator to raise limits (no silent 4 GB pull).
3. After `process_aoi`, `ml/channels.py` derives `lrm5`, `fill_depth`, `support` as COGs and registers Products.
4. `ml/predict.py` scores every candidate (rules) or runs sliding-window U-Net; writes `Candidate` rows with `origin=ml`, `model_version`, `confidence=model_score` (while `reality=unassessed`), `score_sd`, `low_support`, full provenance (`input Product IDs`, `DTM recipe hash`, `channel spec hash`, `git SHA`). No 2012 model runs on 2023 DTM or vice versa.
5. Image chips are written to `data/chips/<location>/<candidate_id>/` and their relative paths stored in `Candidate.provenance.chips`; tile URLs remain `GET /api/layers/{id}/tiles/{z}/{x}/{y}.png`.
6. Frontend `Data` tab shows job progress (bytes, tiles, step `ground→dtm→density→hillshade→slope→svf→lrm→write`); `Places` tab lists new `area-*` locations automatically.

## 4. Data acquisition — autonomous download

* **Primary index:** GUGiK WFS 2.0.0 `GetFeature` with `BBOX=minlat,minlon,maxlat,maxlon,urn:ogc:def:crs:EPSG::4326` on
  * `https://mapy.geoportal.gov.pl/wss/service/PZGIK/DanePomiaroweLidarKRON86/WFS/Skorowidze` (layers `gugik:SkorowidzDanychPomiarowychLIDAR2010..2019`)
  * `https://mapy.geoportal.gov.pl/wss/service/PZGIK/DanePomiaroweLidarEVRF2007/WFS/Skorowidze` (2023 + 2025 in study area; enumerate via GetCapabilities) — per `08` contract, verified in box 49.00-49.70 N / 22.10-22.95 E as 2,387 tiles at 4 p/m² + 608 at 12 p/m² [V* in 05]. Attributes: `godlo`, `akt_rok`, `akt_data`, `char_przestrz`, `url_do_pobrania`, `uklad_h`.
* **Ready-made downloader:** `gmbgit/gugik-api` (REST service refactored from QGIS plugin `Pobieracz danych GUGiK`) and `rgugik` R package — inspect for WFS paging quirks, but keep our `sources/wfs.py` as the canonical adapter (`sources/gugik.py` subclasses `GugikWfsSource`). See `github.com/gmbgit/gugik-api` [S] and `plugins.qgis.org/plugins/pobieracz_danych_gugik` [S].
* **Epoch choice:** train/predict on **2023 EVRF2007 only** first (≈6.5 ground pts/m² under forest, 14.8% empty 0.5 m cells vs 2.2/m² 59.9% in 2012 [C in 09]). 2012 is a different domain — used only for red-team R5 and reviewer swipe context.
* **Incremental:** `HEAD` Content-Length cached 30 d in `TileCache`; skip if `data/raw/<source>/<year>/<file>` size matches; `.part` + HTTP Range resume; never refetch a cached sheet.

## 5. Detection methods — implementation track

Three parallel tracks share channels and evaluation; only one ships per class per `09 §4.2` promotion rule (gain ≥0.10 recall at fixed B, 90% cluster-bootstrap interval excludes zero, ≥2 held-out villages).

### Track A — Morphometric rules (stage 0, always on)

Deterministic, no labels, high recall, low precision. Implemented in `detect/rules.py` + `detect/morphometrics.py` (scikit-image `morphological_reconstruction`, `regionprops`).

* **Closed depressions:** `fill_depth = reconstructed(DTM) - DTM`; threshold 0.3-2.5 m, area 3-80 m², compactness, depth/area ratio. Catches cellars, wells, windthrow pits, craters, charcoal hearths.
* **Positive LRM blobs:** LRM20 >0.15 m and LRM5 >0.10 m, rectangularity >0.6, area 20-250 m² for platforms; circularity for mounds.
* **Linear depressions/ridges:** SVF trough + slope ridge tracing (Heipke-style buffer, width 1.5-6 m) for holloways, terraces, field-boundary scarps.
* **AE anomaly (unsupervised):** convolutional autoencoder (3-4 layers, 32-64 ch) trained to reconstruct *random forest-floor patches* (no labels) on the 6-channel stack; `anomaly = ||input - reconstruction||₂` per pixel; threshold → candidates. Flags anything geometrically regular. Runs on CPU in minutes per km².

Output: raw candidates with per-candidate features (depth, area, shape indices, multi-scale LRM/slope stats, support fraction, neighbourhood counts, AE error).

### Track B — Supervised re-ranker (stage 1-2, the baseline every CNN must beat)

* **B1 LightGBM on handcrafted features** (≈100 dims, monotone constraints e.g. score ↑ with rectangularity for platforms). Needs ~50 positives/class/≥2 villages. Trains in <1 min for 20k candidates; scoring is milliseconds/km². This is the `09` gate ML-1.
* **B2 Frozen ImageNet embeddings + LightGBM** — ResNet-18/EfficientNet-B0 from `timm` (first conv adapted to 6 ch, ImageNet weights), forward pass per 96 px chip (48 m) → 512-d embedding concatenated with handcrafted features → LightGBM. Tests whether CNN features help without backprop. Cost: one forward pass/candidate, no GPU needed.
* **B3 Fine-tuned CNN chip classifier** — same encoder, fine-tuned end-to-end on chips (30 epochs, ~1-3 h on 8-core CPU for 5k chips). Only if B2 beats B1.

### Track C — Segmentation for linears (stage 3)

* **U-Net with ResNet-18/34 encoder** (`segmentation-models-pytorch`, ImageNet init, 6 ch input, 256 px / 128 m patches, stride 192, masked loss outside support). Training ~10-30 h CPU (128 px patches cut ~4×); inference 10-60 s/km². Reserved for holloways/terraces/boundaries where rules are weakest. Only if it beats rule tracing on length-based completeness/correctness.

### Track D — Point-cloud / foundation auxiliaries (not detectors)

* **SAM 2.1 / remote-sensing FMs as polygon helpers** — point-prompt → platform outline in review UI; benchmark only after K6. Zero-shot SAM on LiDAR is "roughly human" on satellite per Landauer & Klassen 2025 [A] but unproven on 0.5 m temperate micro-relief.
* **VLM triage (K7)** — fixed 300-chip benchmark, fixed prompt/model ID, hard budget; secondary filter hidden until reviewer decides; never sets `reality`.

## 6. Labels, transfer, and synthetic data

Labels are the ceiling. `09 §3` schema (`label`, `confuser_class` 16-way, `certainty 1-3`, `informed_by`, `scan_cell_id`, `split_role`) is kept verbatim. Additions for this plan:

* **Systematic scan first** (K4): exhaustively scan 100 m cells at 1:500-1:1k with SVF+LRM20 side by side, historical overlays off, profile tool for doubts; record `seconds_spent` per decision (feeds K6 "minutes per accepted feature").
* **Cheapest positives:** (a) review rule/AE candidates with keyboard accept/reject/confuser (binary decisions >> drawing), (b) K4 manual scan of two pilots, (c) confuser positives from public sets (BDOT10k/OSM roads+ditches, Słowiński et al. charcoal hearths `10.5194/essd-18-493-2026`), (d) one **no-settlement control sheet** for confuser density.
* **Transfer:** fine-tune Archaeoscape-pretrained encoders (U-Net/DeepLabv3 weights from `archaeoscape.ai`, Zenodo `14409524` [C]) on Polish chips — first experiment before labelling 500 objects. Maya features are pyramids 8-12 m tall vs our decimetre platforms, so expect modest transfer; measure via leave-village-out ablation (with vs without pretraining).
* **Synthetic augmentation (only if label-starved):** paste synthetic pits/platforms into empty forest-floor patches using the same DTM synthesis trick as `npj Heritage Science 2025` for cemeteries; keep synthetic-only evaluation separate.
* **Weak supervision (post-K8):** cadastre/1944 roofs as bag labels (parcel contains ≥1 remain) via multiple-instance learning, never as pixel masks — remains lie inside the parcel, not at the symbol.

Per-class minima before training: **50 positives/≥2 villages for GBM, 150 for any CNN** (`09 §3.3`).

## 7. Model comparison table (what ships when)

| Stage | Inputs | Labels | CPU cost | When to use | Must beat |
|---|---|---|---|---|---|
| 0 rules + AE | LRM20/5, SVF, slope, fill_depth, support | thresholds only | 1-3 min/km² | Candidate generator, always | — |
| 1 GBM re-ranker | 100 handcrafted + support | 50/class | <1 min train | Baseline | rule score at B |
| 2 frozen CNN+GBM | 512-d embedding + handcrafted | 150/class | 5-15 min embed for 20k chips | Cheapest CNN test | stage 1 |
| 2b fine-tuned chip CNN | 6-ch chip | 150/class | 1-3 h | If 2 beats 1 | stage 1 |
| 3 U-Net | 6-ch patch | polygons/lines 150/class | 10-30 h train, 10-60 s/km² infer | Linears only | rule tracing |
| AE anomaly | 6-ch patch | none (self-supervised) | minutes/km² | Cold-start / unknown unknowns | — (parallel generator) |

ImageNet weights via `timm` and `smp` carry their own licences; YOLO (`ultralytics` AGPL-3.0) is avoided unless a BSD detector is chosen.

## 8. Evaluation — unchanged from 09 §5, enforced for every model

* **Splits:** leave-village-out with 250 m buffer, no training patch overlapping it; 500 m blocks for hyperparams; 2 lockbox villages labelled blind, hashed, opened once after protocol freeze. No thresholds tuned on test villages.
* **Matching (Hungarian, one-to-one, same class):** pits/wells ≤3 m centroid; platforms buffered polygon or IoU ≥0.25; linears length-based completeness/correctness at 3 m buffer (Heipke-style).
* **Headline metrics (per class, per village, with prevalence + support share):** recall at B (10/20/50 per km²), precision@k (25/50/100, Wilson 90% interval), PR-AUC vs prevalence (=chance), FP/km² by confuser class, reviewer minutes per accepted feature (K6 needs ≥2× faster than tile scanning at equal recall), calibration (isotonic/Platt + reliability diagram + ensemble `score_sd` from 5 seeds).
* **Red-team R1-R9** (`09 §5.7`) run before any number is quoted: control-sheet FP rate, label-permutation (PR-AUC → prevalence), location-only GBM (must lose), inside/outside mapped settlement, epoch swap (2023→2012, expect drop), strip-seam sheet, charcoal-hearth/road challenge set, 8-orientation consistency, known-check 50 certainly known features.

Independent denominators `09 §5.4` (1921 census building count, 1852 cadastre symbols, 1944 roof counts) give visibility ceiling (a) and end-to-end recall (a×b); reported inside vs outside mapped settlement.

## 9. Module layout and CLI (extends 08)

```
src/lidar_discovery/
  detect/                 # non-ML candidate generators (shared with K6)
    rules.py              # closed depression, LRM blobs, linear tracing
    anomaly.py            # autoencoder anomaly generator
    morphometrics.py      # per-candidate features
  ml/
    channels.py           # derive lrm5 + fill_depth + support, fixed scaling
    labels.py             # label + scan_cells tables, snapshots/hashes
    splits.py             # village folds, buffers, lockbox registry
    sampling.py           # rasterio windowed patch/chip sampler, aug
    models/
      gbm.py              # LightGBM re-ranker
      chipnet.py          # timm encoder chip classifier / embedder
      unet.py             # smp U-Net
      autoencoder.py      # unsupervised DTM autoencoder
    train.py  predict.py  postprocess.py  evaluate.py  calibrate.py  registry.py
    vlm.py                # K7 benchmark only
data/models/<model_version>/  weights, card.json/md, metrics/, label_snapshot.sha256
data/chips/<location>/<candidate_id>/  hillshade.png svf.png lrm.png slope.png dtm.png ortho.png
```

| Command | Effect |
|---|---|
| `ldp ml channels <loc> --epoch 2023` | Derive lrm5/fill_depth/support COGs; register Products |
| `ldp ml train-ae --locations ...` | Train autoencoder on random forest-floor patches (no labels) |
| `ldp ml splits --assign` | Write fold/lockbox registry; refuses to mutate lockbox after labels exist |
| `ldp ml train --stage gbm|chip|unet --classes ... --folds leave-village-out` | Train per-fold + final; write `data/models/<version>/` |
| `ldp ml predict <loc> --model <ver> [--budget 20]` | Score candidates / sliding window → Candidates (refuses lockbox without --open-lockbox) |
| `ldp ml evaluate --model <ver> --villages ... [--redteam all]` | Metrics + intervals + markdown report |
| `ldp ml card <ver>` | Render model card (intended use, training villages, per-village metrics, red-team, failure modes, package versions, licence) |
| `ldp fetch-bbox W S E N [--source ...] [--year ...] [--layers ...] --auto-detect` | Existing area job plus immediate predict when DTM ready (autonomous shorthand) |

All outputs enter `Candidate` as `origin=ml`, `model_version`, calibrated `model_score`+`model_rank` (proposed contract change — keep `confidence` for reviewer; until changed score lives in `confidence` while `reality=unassessed` and in provenance), `disclosure=restricted`.

## 10. Running it autonomously

* **Scheduler (v0):** `APScheduler` `BackgroundScheduler` started in the FastAPI lifespan (or a `typer` daemon `ldp watch --bbox ... --interval 24h`) that polls `list_tiles` per source, diffs against `Product` provenance, and enqueues `fetch-area` jobs sequentially. Later: systemd timer / Windows Task Scheduler. One job at a time (existing `ThreadPoolExecutor(1)`); progress persisted every 0.5 s; `cancel` is cooperative.
* **Watch mode for demos:** `ldp dev --watch` — on every new `area-*` location, run `channels → predict → chips` automatically and push a toast in `/explore`.
* **Resource caps:** `LDP_MAX_FETCH_AREA_KM2` (default 6) and `LDP_MAX_FETCH_BYTES` (4 GB) gate the scheduler; jobs over limit stay `queued` with `over_limit` reason. Region (3,000 km², ~100 GB COGs) is processed **per precinct sequentially**, keeping only candidates — not a bulk 3,000 km² COG store on a laptop.
* **Reproducibility:** every Candidate provenance stores `run ID`, `input Product IDs+hashes`, `DTM recipe hash`, `channel spec hash`, `model_version`, `git SHA`, `package versions`. `PIPELINE_VERSION` bump invalidates the area cache key.

## 11. Milestones & kill criteria (desk-only; 09 §8 + autonomous gates)

No ML before K1-K4+K6 pass.

| Gate | Question | Stop/pivot if |
|---|---|---|
| K1 | Can a person see house-scale features in 2023? | <~half of 1944/poster house positions show earthwork → roads/terraces only; drop platform/cellar ML |
| K2 | Does class-12 help? | Decides DTM recipe all models are pinned to |
| K3 | What is already known? | Every house within ~20 m already placed → contribution is condition survey; ML adds little |
| K4 | Is manual mapping reliable? | House-class F1 <~0.5 between mappers → no ML |
| K5' | Are mapped features plausibly real? (blind second interpreter, stratified 100, profile vs seams) | <~half survive → tighten definitions |
| K6 | Do rules/AE save reviewer time? | Ranked review not ≥2× faster than scanning at equal recall → drop automation |
| ML-0 | Enough labels? | <50/≥2 villages for every class → stay rule-only |
| ML-1 | GBM beats rules? | No gain at B (≥0.10 recall, interval excludes 0, ≥2 villages) → rules stay |
| ML-2 | CNN features beat GBM? | No → stop CNN |
| ML-3 | U-Net beats rule tracing? | No → keep rules for linears |
| K7 | VLM beats GBM at equal reviewer time? | No → drop (300-chip fixed benchmark) |
| K8 | Transfer? (8-10 precincts, frozen protocol, lockbox opened once) | Recall vs independent denominators collapses outside pilot → no regional run; publish negative result |
| **A1** | Autonomous loop stable? | Jobs fail/interrupt without resuming from `.part`, or WFS caps change → fix `sources/wfs.py` paging before scaling |
| **A2** | Transfer from Archaeoscape helps? | Zero-shot Archaeoscape U-Net on Polish LRM/SVF scores near chance inside forest → train from scratch; keep Archaeoscape only for pretraining ablation |

## 12. Research backlog (ordered, with owner)

1. **Reproduce Archaeoscape benchmark locally** (1 GPU-day if rented, else CPU overnight on 128 px patches) — verify their dataloader + `archaeoscape` repo runs on Windows/py312; record IoUs on their Cambodia split. Gives a known-good training loop.
2. **Zero-shot Archaeoscape U-Net on two Bieszczady pilot sheets** — no fine-tuning; score SVF+LRM tiles; visually inspect. Quantifies domain gap.
3. **AE anomaly on one pilot precinct** — train on 10k random forest-floor patches; threshold via control sheet; add to candidate generators.
4. **Ablation: ImageNet vs Archaeoscape pretraining vs scratch** for chip classifier — leave-village-out on pilots once labels exist.
5. **Canopy-structure prior (post-K8):** test whether canopy-height / first-return texture (old orchards) improves platform recall outside mapped settlement — ablation only, never as sole signal.

## 13. Risks (additions to 09 §9)

| # | Risk | Mitigation |
|---|---|---|
| A1 | WFS caps / `char_przestrz` lies (nominal vs delivered) | Read LAS headers for truth; cache GetCapabilities; retry with paging; log every `godlo` |
| A2 | Large LAZ download dominates runtime, not model | Scheduler throttles; layer selection does not save bytes (warned in UI); keep raw cache; estimate before fetch |
| A3 | Model learns settlement band, not form | Terrain-only inputs; R3 location-only test; inside/outside stratification mandatory |
| A4 | Leakage via overlapping patches | 250 m buffer around held-out precinct; lockbox; label-permutation test |
| A5 | Score maps as looting maps | No raster leaves machine; public outputs are village or ≥1 km² aggregates; chips for restricted classes never published |
| A6 | Language | No "discovery/confirmed/unknown" in any output; strongest claim = "LiDAR feature consistent with N independent historical sources" |

## 14. Hardware / packages

Windows 11 laptop, 8-16 threads, 16-32 GB, no CUDA assumed. All wheels exist for py312 today: `torch 2.15.0` (CPU win_amd64), `timm 1.0.31`, `segmentation-models-pytorch 0.6.0`, `lightgbm 4.7.0`, `scikit-learn 1.9.1`, `rasterio 1.5.2`, `scikit-image`, `scipy` [C, PyPI JSON 2026-11-13 in 09]. ML deps go in `[dependency-groups].ml` (`uv sync --extra ml`); pin in `uv.lock`; model card records versions. Rent a GPU for U-Net training only if one overnight run is insufficient — inference stays CPU.

## 15. References (checked 2026-11-15)

* Perron, Sydorov, Wijker, Evans et al. **Archaeoscape: Bringing Aerial Laser Scanning Archaeology to the Deep Learning Era**, NeurIPS 2024 D&B — dataset 888 km² / 31k features, benchmarks U-Net/DeepLabv3/ViT — `proceedings.neurips.cc/...2d9ba88c...pdf`, code `github.com/archaeoscape-ai/archaeoscape`, data `archaeoscape.ai/data/2024`, Zenodo `14409524`.
* **Broadscale deep learning model for archaeological feature detection across the Maya area**, `sciencedirect.com/science/article/abs/pii/S0305440324000906` (2024); follow-up **Evaluating Broadscale Deep Learning for Maya Settlement Detection in G-LiHT LiDAR**, `link.springer.com/article/10.1007/s10816-025-09741-5`.
* **Automatic detection of archaeological features from ALS using deep learning: ADAF**, HRNet + Faster R-CNN, 10k+ samples, `sciencedirect.com/science/article/pii/S2352409X26001689` (2026).
* **Semantic Segmentation of Airborne LiDAR Data in Maya Archaeology**, `mdpi.com/2072-4292/12/22/3685` (2020).
* Banasiak et al. **Białowieża ISOK 0.5 m**, pixel F1 0.58 IoU 0.50, `10.3390/rs14040995` [C].
* Verschoof-van der Vaart & Landauer 2021 **CarcassonNet** hollow roads, `10.1016/j.culher.2020.10.009` [C].
* **Seeing among foliage with LiDAR and ML: transferable pipeline** (MLMR + vegetation filtering on points), `isprs-archives.copernicus.org/.../XLVI-2-W1-2022-365-2022.pdf`.
* ForestFormer3D (ICCV 2025), PointDMM (`10.3390/f14122276`), standing-remains vs low vegetation metrics (`isprs-archives/.../XL-5-W2-459-2013.pdf`).
* Bergmann et al. **Anomaly Detection in 3D Point Clouds Using Deep Geometric Descriptors**, WACV 2023 — unsupervised anomaly via descriptors; VAE variant `arxiv.org/abs/2304.03420`.
* Cemetery synthesis `nature.com/articles/s40494-025-01798-5` (synthetic LiDAR-derived data + DCNN under forest).
* RVT derivatives (hillshade, SVF 16/10 m, SLRM 20 m, openness) — `isprs-archives/.../XLVIII-M-9-2025/821/2025.pdf` + Highest Gradient Model evaluation `10.3390/rs9020120`.
* GUGiK download: `gmbgit/gugik-api` (`github.com/gmbgit/gugik-api`), QGIS plugin `pobieracz_danych_gugik`, `rgugik` (`10.21105/joss.02948`), WFS `mapy.geoportal.gov.pl/wss/service/PZGIK/DanePomiaroweLidar*/WFS/Skorowidze`.
