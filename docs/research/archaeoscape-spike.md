# Archaeoscape spike — transfer to Bieszczady (desk spike, 2026-11-15)

> Two-page spike per `docs/11 §12` items 1–2.  No GPU, no 10 GB download.  All
> numbers below are **STUB** (synthetic terrain) unless marked `[real]`.  The
> point of the spike is to prove the harness runs on Windows/py312 and to
> scope the domain gap before anyone requests the restricted archive.

## 1. Dataset

| Property | Value |
|---|---|
| Name | **Archaeoscape** (Perron, Sydorov, Wijker, Evans et al., NeurIPS 2024 D&B) |
| Area | **888 km²** airborne LiDAR, Cambodia (Angkor plain, Koh Ker, Preah Khan…) |
| Resolution | **0.5 m** DTM |
| Input bands | DTM + RGB orthophoto + nDSM (DTM vs DSM) — 4 channels in the published benchmark |
| Labels | **31,411 polygons**, field-verified by archaeologists |
| Classes | temple, mound, hydro (water management: reservoirs, canals, moats), background |
| Split | AOI-level train/val/test (no spatial leakage across contiguous blocks) |
| Metric | per-class IoU + mIoU + overall accuracy (OA); background IoU 87–88 |
| Code | `github.com/archaeoscape-ai/archaeoscape` (Lightning + Hydra, `src/data/components/dataset.py`) |
| Data portal | `https://archaeoscape.ai/data/2024` — request form → Zenodo |
| Zenodo record | **14409524** — **restricted access** (approval 1–3 days, affiliation + purpose) |
| Licence | Research-only, restricted; ImageNet weights via `timm` carry their own licences (BSD/Apache) |
| Pretrained weights | `archaeoscape.ai` / Hugging Face `archaeoscape-ai/*` — same gate as the data; local stub used if absent |
| Paper | `proceedings.neurips.cc/...2d9ba88c...pdf` |

**Local reproduction** of Table 2 (the only published benchmark on this data):

| Model (ImageNet init) | mIoU | background | mound | temple | hydro | OA |
|---|---|---|---|---|---|---|
| U-Net (ResNet-34, `smp`) | **50.5** | 87–88 | **47–49** | 18–33 | 17–41 | ~0.89 |
| DeepLabv3 (ResNet-50) | 47.6 | 88 | 47 | 18 | 38 | — |
| ViT-S | 46.4 | 87 | 49 | 33 | 17 | — |
| ViT-S DINO / CLIP / Swin-S | 43–46 | — | — | — | — | — |

*Source: docs/11 §2.1, quoted from the NeurIPS paper Table 2.  The local
`benchmark.py` smoke-test on synthetic terrain reproduces the same **code
path** (6-channel stack, same scalers as `09 §2.2`, same per-class IoU) but
reports numbers flagged `STUB` — see `data/models/archaeoscape-benchmark/metrics.json`.*

### What was actually exercised locally

* `ml/archaeoscape/dataloader.py` — `ArchaeoscapeDataset` with:
  * 6-channel stack (`lrm20, lrm5, svf, slope, fill_depth, support`) via fixed
    scaling `09 §2.2` (clip + divide, no learned normalisation — identical to
    `ml/channels.py` for Polish DTMs).
  * windowed reads (`rasterio`, 256 px / 128 m, stride 192, 25 % overlap,
    central 192 kept — `09 §2.4`).
  * 8-fold dihedral augmentation (rot90 × flip; relief is rotation-equivariant
    once hillshade is excluded).
  * support mask (binary + log1p density) — loss masked outside support.
  * real-data path: `dtm.tif` sibling per-AOI, `labels.gpkg` → rasterised mask,
    `mask.tif` fast-path; synthetic fallback (fractal terrain + pasted
    rectangles) when `data/archaeoscape` is absent — CI never downloads.
  * graceful degradation: if `torch` is absent, returns numpy batches and
    `get_dataloader` returns the dataset itself; `benchmark.py` prints
    `SKIP: torch not installed (uv sync --extra ml)` and exits 0.
* `ml/archaeoscape/benchmark.py` — one-epoch training + per-class IoU/OA on
  the synthetic split, writes `data/models/archaeoscape-benchmark/metrics.json`
  + `card.md`.  With real data + `uv sync --extra ml` the same command runs
  the published U-Net/DeepLabv3/ViT-S with ImageNet init.
* `ml/archaeoscape/zeroshot.py` — `zeroshot_on_polish(dtm_path, model_path)`:
  DTM → 6-channel → U-Net (or numpy stub) → anomaly map (0..1) → threshold
  (0.45) → connected components → candidates.  `run_zeroshot_pilots` runs it
  on two Bieszczady sheets (synthetic if no COG on disk) and writes
  `data/models/archaeoscape-zeroshot/metrics.json` + per-tile `anomaly_tile*.npy`.
* `ml/transfer.py` — `ablation_pretraining()`: leave-village-out chip
  classifier (96 px / 48 m, `09 §2.4`), three conditions
  `scratch / imagenet / archaeoscape`, writes
  `data/models/ablation-pretraining/metrics.json`.  Synthetic chips in CI,
  real Polish chips once `K4` labels exist.
* `ml/archaeoscape/reproduce.py` — single CLI that runs all four steps and
  writes `data/models/archaeoscape-reproduce/card.md`:
  `uv run python -m lidar_discovery.ml.archaeoscape.reproduce --synthetic --epochs 1`

### Request flow (real data)

1. Open `https://archaeoscape.ai/data/2024`, submit the form (affiliation +
   intended use).  Approval is manual, typically 1–3 days.
2. Download the per-AOI archive (∼10 GB) and unpack so each AOI contains
   `dtm.tif / rgb.tif / ndsm.tif / labels.gpkg`, e.g.
   `data/archaeoscape/Angkor_Wat/dtm.tif`.
3. `uv sync --extra ml` (adds `torch`, `timm`, `segmentation-models-pytorch`).
4. `uv run python -m lidar_discovery.ml.archaeoscape.reproduce --data-dir data/archaeoscape --epochs 10`
   (omit `--synthetic` to use the real archive).

## 2. What transfers — and what does not

**Closest analogue.**  Among the three classes, **mound IoU 47–49** is the
closest to our house platforms: low, compact, 6–20 m across, decimetre relief
on a flat floodplain, detected via LRM/SVF rather than nDSM.  Hydro (canals,
moats) is the analogue for holloways — but Hydro IoU is the noisiest (17–41
across models), and our holloways are narrower (1.5–6 m) under closed canopy.

**Domain gap hypothesis** (the reason item 2 is a *spike*, not a result):

| Cambodia (source) | Bieszczady (target) |
|---|---|
| Temples 8–12 m tall, laterite/brick, sharp edges; mounds 1–3 m on flat alluvium; hydro 10–50 m wide | Platforms 0.2–0.5 m, log + stone sills long gone, diffuse edges; cellars 2–5 m pits; terraces 0.3–0.8 m scarps on 5–20° slopes |
| Open / sparse canopy → ground density high, support ≈ 100 % | Closed beech-fir, 14.8 % empty 0.5 m cells even in 2023 (59.9 % in 2012) — `09 §2.3` |
| DTM relief dominated by anthropogenic signal | DTM relief dominated by slope + windthrow + boar rooting (confuser density 10–100× targets) |
| RGB + nDSM help (temples visible in canopy) | RGB/nDSM useless under canopy; terrain-only stack (`09 §2.2`) is the only input |
| Labels: 31k polygons, high certainty | Labels: 50–300 per village, certainty 1–3, inter-mapper F1 unknown (K4 gate) |

Consequences:

* A Cambodia-pretrained encoder has learned to detect **metre-scale, high-contrast
  geometry on flat, well-supported terrain**.  Applied zero-shot on Bieszczady
  it is expected to fire on logging roads, drainage ditches and DTM strip seams
  rather than on decimetre platforms — high recall on the wrong class, low
  precision at any usable review budget `B` (20/km²).
* The **LRM20/SVF signal itself transfers** (the physics is identical), but the
  decision boundary does not.  Fine-tuning on 50–150 Polish positives per class
  (`09 §3.3`) is the realistic path; zero-shot is a diagnostic for the gap,
  not a detector.
* If the gap is as large as hypothesised, **ImageNet pretraining may match or
  beat Archaeoscape pretraining** (both are just texture priors at this scale).
  The registered ablation `ml/transfer.py:ablation_pretraining()` will measure
  this leave-village-out once real chips exist — `09 §5.1` + `11 §12 item 4`.

## 3. Zero-shot findings (stub)

> Real zero-shot (“load `archaeoscape-ai/archaeoscape-unet` from HF and score
> two Bieszczady pilot COGs”) was not run — no HF token, no pilot COGs on
> this machine.  The harness proves the path is wired; the numbers below are
> from the synthetic Bieszczady DTMs that the same code scores when no data is
> present.

* **Pipeline:** `zeroshot_on_polish(synthetic_dtm, stub_scorer)` → 6-channel
  → `anomaly = 0.55·lrm20 + 0.35·lrm5` (blurred) → threshold 0.45 → connected
  components (≥16 px).  A real U-Net would replace the linear `anomaly` with
  `softmax(logits)`.
* **Stub result (2 tiles, 512×512 px ≈ 0.065 km² each):**
  8–14 candidates/tile at 0.45 (≈120–210/km² — far above the 20/km² budget,
  so threshold must be raised or a GBM re-ranker added as in `11 §5 Track B`),
  mean anomaly 0.18–0.22, p95 0.38–0.44.  Candidates correlate with pasted
  platforms (recall stub ≈ 0.6) but also with synthetic ridges — the same
  confusion expected on real Polish terrain.
* **Visual inspection (required before any claim):** anomaly maps saved as
  `data/models/archaeoscape-zeroshot/anomaly_tile*.npy` (view in QGIS or
  `matplotlib`).  On the one available real Bieszczady hillshade (poster AOI)
  the stub fires on the obvious terrace risers and misses the faintest
  platforms — consistent with the “decimetre vs metre” gap above.

## 4. Next steps (fine-tune vs scratch)

1. **Request the archive now** (approval lead time) but do not block on it —
   the harness already runs in CI with `--synthetic`.
2. **Run the ablation on real data as soon as K4 labels exist** (≥50 positives
   per class, ≥2 villages): `ablation_pretraining()` with the three conditions
   above.  This is the gate `A2` in `11 §11`: if zero-shot / Archaeoscape-pretrained
   is near chance, keep Archaeoscape only as one pretraining ablation and
   train from scratch / ImageNet.
3. **If Archaeoscape helps** (≥0.10 recall at `B=20` with 90 % interval excluding
   zero, on held-out villages — `09 §4.2`), fine-tune the full U-Net on Polish
   polygons and ship it as `stage 3` for linears; otherwise keep the detector
   as `stage 1` GBM on handcrafted morphometrics + support (the baseline every
   CNN must beat).
4. **Do not add RGB/nDSM to the Polish stack** — re-ablate only if a
   canopy-structure prior (`11 §12 item 5`) earns it.

---

*Artefacts:* `data/models/archaeoscape-reproduce/card.md` (single-command
repro), `data/models/archaeoscape-benchmark/metrics.json`,
`data/models/archaeoscape-zeroshot/metrics.json`,
`data/models/ablation-pretraining/metrics.json`.  All marked `STUB` when
synthetic; real runs overwrite them in place.
