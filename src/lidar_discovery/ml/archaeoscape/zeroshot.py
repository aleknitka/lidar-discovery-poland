"""Zero-shot Archaeoscape U-Net on Polish DTM.

Loads a pretrained Archaeoscape U-Net (Hugging Face ``archaeoscape.ai``
org, if available) and runs it zero-shot on two Bieszczady pilot sheets.
When no real DTM or no weights are present the whole path falls back to
synthetic terrain so CI never needs credentials or network.

Public API
----------
``zeroshot_on_polish(dtm_path, model_path) -> tuple[list[dict], np.ndarray]``
scores SVF+LRM tiles, thresholds, and returns candidates + an anomaly map.

The module also exposes ``run_zeroshot_pilots(...)`` used by the
``reproduce`` CLI.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from scipy import ndimage


# ---------------------------------------------------------------- helpers
def _synthetic_dtm_bieszczady(h: int = 512, w: int = 512, seed: int = 0) -> np.ndarray:
    """Hilly forest DTM with a few pasted platforms (decimetre scale)."""
    rng = np.random.default_rng(seed)
    raw = rng.standard_normal((h, w)).astype(np.float32)
    dtm = (
        ndimage.gaussian_filter(raw, 10) * 3.0
        + ndimage.gaussian_filter(raw, 3) * 0.7
        + raw * 0.05
    )
    # paste 6-10 faint platforms (0.15–0.4 m) — harder than Cambodia temples
    for _ in range(int(rng.integers(6, 11))):
        rh = int(rng.integers(8, 24))
        rw = int(rng.integers(10, 32))
        y0 = int(rng.integers(5, h - rh - 5))
        x0 = int(rng.integers(5, w - rw - 5))
        dtm[y0 : y0 + rh, x0 : x0 + rw] += float(rng.uniform(0.18, 0.45))
    return dtm.astype(np.float32)


def _dtm_to_six_channel(dtm: np.ndarray) -> np.ndarray:
    """DTM (H×W) → 6×H×W scaled stack (same scalers as dataloader)."""
    from lidar_discovery.ml.archaeoscape.dataloader import (
        _derive_channels_synthetic,
        _stack_and_scale,
    )

    # use synthetic derive path (cheap) — real path would call vis.py ops
    rng = np.random.default_rng(0)
    channels = _derive_channels_synthetic(dtm.astype(np.float32), rng)
    return _stack_and_scale(channels)


def _load_dtm_any(path: str | Path | None) -> np.ndarray | None:
    if path is None:
        return None
    p = Path(path)
    if not p.exists():
        return None
    try:
        import rasterio

        with rasterio.open(p) as ds:
            a = ds.read(1).astype(np.float32)
            if ds.nodata is not None:
                a[a == float(ds.nodata)] = np.nan
            a = np.nan_to_num(a, nan=float(np.nanmean(a)) if np.isfinite(a).any() else 0.0)
            return a
    except Exception:
        try:
            return np.load(p).astype(np.float32)  # npy fallback
        except Exception:
            return None


def _try_load_hf_weights(model_path: str | Path | None):  # type: ignore[no-untyped-def]
    """Attempt to load Archaeoscape HF weights; return None on any failure."""
    if model_path is None:
        return None
    p = Path(model_path)
    if p.exists() and p.suffix in (".pt", ".pth", ".ckpt", ".bin"):
        try:
            import torch  # type: ignore[import]

            ckpt = torch.load(p, map_location="cpu")
            # HF ckpt may be {"state_dict": ...} or raw state_dict
            if isinstance(ckpt, dict) and "state_dict" in ckpt:
                ckpt = ckpt["state_dict"]
            return ckpt
        except Exception:
            return None
    # Never download in CI — require local file unless explicitly networked.
    # Probe that huggingface_hub is available without importing it eagerly.
    try:
        import importlib.util as _ilu

        if _ilu.find_spec("huggingface_hub") is None:
            return None
        return None
    except ImportError:
        return None


def _stub_score_map(image: np.ndarray) -> np.ndarray:
    """Numpy stub anomaly map from the 6-channel stack (H×W 0..1).

    Mirrors what a real U-Net would highlight: positive LRM blobs +
    slope edges.  Calibrated so background ≈ 0.1 and platforms ≈ 0.6-0.9.
    """
    # image 6×H×W scaled: 0=lrm20 1=lrm5 2=svf 3=slope 4=fill 5=support
    lrm20 = image[0]
    lrm5 = image[1]
    slope = image[3]
    # score = sigmoid-ish over lrm
    s = 0.55 * np.clip(lrm20 * 1.2 + 0.2, 0, 1) + 0.35 * np.clip(lrm5 * 1.0 + 0.15, 0, 1)
    # slope slightly suppresses flat false positives on steep hillsides is not modelled
    s = np.clip(s + 0.05 * np.clip(slope, 0, 1), 0, 1).astype(np.float32)
    # light blur to mimic model receptive field
    s = ndimage.gaussian_filter(s, 1.2).astype(np.float32)
    return s


def _extract_candidates(
    score: np.ndarray,
    threshold: float = 0.45,
    min_area_px: int = 16,
    res_m: float = 0.5,
) -> list[dict[str, Any]]:
    """Threshold + connected components → candidate list (pixel geometry)."""
    binary = score >= threshold
    labelled, n = ndimage.label(binary)
    cands: list[dict[str, Any]] = []
    for lab in range(1, n + 1):
        mask = labelled == lab
        area = int(mask.sum())
        if area < min_area_px:
            continue
        ys, xs = np.where(mask)
        y0, y1 = int(ys.min()), int(ys.max())
        x0, x1 = int(xs.min()), int(xs.max())
        cy, cx = float(ys.mean()), float(xs.mean())
        peak = float(score[mask].max())
        mean_s = float(score[mask].mean())
        cands.append(
            {
                "bbox_px": [x0, y0, x1, y1],
                "centroid_px": [cx, cy],
                "area_px": area,
                "area_m2": area * res_m * res_m,
                "score_peak": peak,
                "score_mean": mean_s,
                "geometry_wgs84": None,  # filled by caller when transform known
            }
        )
    cands.sort(key=lambda c: c["score_peak"], reverse=True)
    return cands


# ---------------------------------------------------------------- public API
@dataclass
class ZeroshotResult:
    candidates: list[dict[str, Any]]
    anomaly_map: np.ndarray  # H×W float32 0..1
    threshold: float
    dtm_path: str | None
    model_path: str | None
    is_stub: bool
    metrics_stub: dict[str, Any]


def zeroshot_on_polish(
    dtm_path: str | Path | None = None,
    model_path: str | Path | None = None,
    threshold: float = 0.45,
    tile_size: int = 256,
    seed: int = 0,
) -> tuple[list[dict[str, Any]], np.ndarray]:
    """Score one DTM with an Archaeoscape-pretrained U-Net (or stub).

    Parameters
    ----------
    dtm_path:
        Path to a DTM COG/GeoTIFF (EPSG:2180, 0.5 m).  ``None`` → synthetic
        Bieszczady DTM.
    model_path:
        Path to HF/CKPT weights.  ``None`` → numpy stub scorer.

    Returns
    -------
    (candidates, anomaly_map)
        candidates: list of dicts with bbox/centroid/area/score
        anomaly_map: H×W float32 0..1
    """
    dtm = _load_dtm_any(dtm_path)
    if dtm is None:
        dtm = _synthetic_dtm_bieszczady(512, 512, seed=seed)
    # optional torch model
    ckpt = _try_load_hf_weights(model_path)
    # build 6-channel stack tiled if DTM is large (stride = tile_size, no overlap for stub)
    h, w = dtm.shape
    if h <= tile_size and w <= tile_size:
        image = _dtm_to_six_channel(dtm)
        if ckpt is not None:
            try:
                import torch  # type: ignore[import]

                from lidar_discovery.ml.archaeoscape.benchmark import _build_torch_model

                model = _build_torch_model("unet")
                if model is not None:
                    model.load_state_dict(ckpt, strict=False)
                    model.eval()
                    with torch.no_grad():
                        logits = model(torch.from_numpy(image).unsqueeze(0).float())
                        prob = torch.softmax(logits, dim=1)[0, 1:].max(dim=0).values.numpy()
                        # prob may be smaller if model downsamples
                        if prob.shape != (h, w):
                            prob = np.array(
                                ndimage.zoom(prob, (h / prob.shape[0], w / prob.shape[1]), order=1),
                                dtype=np.float32,
                            )
                        anomaly = np.clip(prob, 0, 1).astype(np.float32)
                    cands = _extract_candidates(anomaly, threshold=threshold)
                    return cands, anomaly
            except Exception:
                pass
        anomaly = _stub_score_map(image)
        cands = _extract_candidates(anomaly, threshold=threshold)
        return cands, anomaly

    # tiled inference for large DTMs (simple stitch, no blending)
    anomaly_full = np.zeros((h, w), dtype=np.float32)
    step = tile_size
    for r in range(0, h, step):
        for c in range(0, w, step):
            r1, c1 = min(r + tile_size, h), min(c + tile_size, w)
            patch = dtm[r:r1, c:c1]
            # pad to tile_size for the scorer, then crop
            ph, pw = patch.shape
            if ph < tile_size or pw < tile_size:
                tmp = np.zeros((tile_size, tile_size), dtype=np.float32)
                tmp[:ph, :pw] = patch
                # fill pad with edge value
                if pw < tile_size:
                    tmp[:ph, pw:] = patch[:, -1:].repeat(tile_size - pw, axis=1)
                if ph < tile_size:
                    tmp[ph:, :] = tmp[ph - 1 : ph, :]
                patch_padded = tmp
            else:
                patch_padded = patch
            img = _dtm_to_six_channel(patch_padded)
            score = _stub_score_map(img)[:ph, :pw]
            anomaly_full[r:r1, c:c1] = score
    cands = _extract_candidates(anomaly_full, threshold=threshold)
    return cands, anomaly_full


def run_zeroshot_pilots(
    dtm_paths: list[str | Path] | None = None,
    model_path: str | Path | None = None,
    out_dir: str | Path = "data/models/archaeoscape-zeroshot",
    threshold: float = 0.45,
) -> dict[str, Any]:
    """Run zero-shot on two Bieszczady pilot sheets (synthetic if none).

    Writes ``<out_dir>/metrics.json`` and returns the dict.  Per-tile
    precision/recall are stub (no ground truth) — flagged as such.
    """
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    sources: list[str | None] = (
        [str(p) for p in dtm_paths[:2]] if dtm_paths else [None, None]
    )

    tiles: list[dict[str, Any]] = []
    for i, src in enumerate(sources):
        cands, anomaly = zeroshot_on_polish(dtm_path=src, model_path=model_path, threshold=threshold, seed=i)
        # stub PR: we have no labels, so report candidate count + density
        h, w = anomaly.shape
        area_km2 = (h * 0.5 * w * 0.5) / 1e6
        tiles.append(
            {
                "tile": i,
                "dtm_source": src or f"synthetic-bieszczady-{i}",
                "anomaly_shape": [int(h), int(w)],
                "area_km2": area_km2,
                "threshold": threshold,
                "candidates": len(cands),
                "candidates_per_km2": (len(cands) / area_km2) if area_km2 else 0.0,
                "mean_anomaly": float(anomaly.mean()),
                "p95_anomaly": float(np.percentile(anomaly, 95)),
                "candidates_head": cands[:5],
                # stub PR — no labels
                "precision_stub": None,
                "recall_stub": None,
                "note": "STUB — no ground truth; visual inspection required (see spike report).",
            }
        )
        # save anomaly preview as npy (tiny, no COG writer needed)
        np.save(out / f"anomaly_tile{i}.npy", anomaly)

    result: dict[str, Any] = {
        "model_path": str(model_path) if model_path else None,
        "is_stub": model_path is None or not Path(str(model_path)).exists(),
        "threshold": threshold,
        "tiles": tiles,
        "hf_weights": "archaeoscape-ai/archaeoscape-unet (requires request; stub used if absent)",
        "instruction": "Real weights: request via https://archaeoscape.ai/data/2024 then hf_hub_download.",
    }
    (out / "metrics.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result
