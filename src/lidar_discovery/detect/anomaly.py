"""Unsupervised anomaly detector for DTM patches (11 Track A AE, 09 option).

Trains a tiny convolutional autoencoder on random forest-floor patches
(where support>0.5). High reconstruction error => geometrically regular /
man-made. Falls back to PCA or Gaussian residual when torch/sklearn missing.

CPU minutes per km²; no labels required.
"""

from __future__ import annotations

from typing import Any

import numpy as np
from scipy import ndimage

from lidar_discovery.ml.channels import stack_for_model
from lidar_discovery.processing.dtm import Grid


def _has_torch() -> bool:
    try:
        import torch  # noqa: F401  # type: ignore[import-not-found]

        return True
    except Exception:
        return False


def _has_sklearn() -> bool:
    try:
        import sklearn  # noqa: F401  # type: ignore[import-not-found]

        return True
    except Exception:
        return False


# ---------------------------------------------------------------- sampling patches


def sample_patches(
    arrays: dict[str, np.ndarray],
    grid: Grid,
    n: int = 2000,
    patch: int = 32,
    support_thresh: float = 0.5,
    seed: int = 0,
) -> np.ndarray:
    """Sample n random (6, patch, patch) patches where support is adequate.

    Returns (n, 6, patch, patch) float32, scaled via stack_for_model.
    """
    rng = np.random.default_rng(seed)
    h, w = next(iter(arrays.values())).shape
    stacked = stack_for_model(arrays)  # (6, H, W)
    support = arrays.get("support", arrays.get("ground_density"))
    if support is None:
        support_valid = np.ones((h, w), bool)
    else:
        # threshold on raw support before scaling
        sup_raw = support
        support_valid = np.isfinite(sup_raw) & (sup_raw > support_thresh * 0.2)
    patches: list[np.ndarray] = []
    tries = 0
    while len(patches) < n and tries < n * 20:
        tries += 1
        r = int(rng.integers(0, max(1, h - patch)))
        c = int(rng.integers(0, max(1, w - patch)))
        if not support_valid[r : r + patch, c : c + patch].mean() > 0.8:
            continue
        p = stacked[:, r : r + patch, c : c + patch]
        if np.isnan(p).any():
            continue
        patches.append(p)
    if not patches:
        return np.zeros((0, 6, patch, patch), np.float32)
    return np.stack(patches).astype(np.float32)


# ---------------------------------------------------------------- torch autoencoder (optional)


def train_ae_torch(
    patches: np.ndarray,
    epochs: int = 8,
    batch: int = 64,
    lr: float = 1e-3,
    device: str = "cpu",
) -> Any:
    """Train a 4-layer conv AE on patches; returns the model (torch.nn.Module)."""
    import torch  # type: ignore[import-not-found]
    from torch import nn  # type: ignore[import-not-found]

    class TinyAE(nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.enc = nn.Sequential(
                nn.Conv2d(6, 16, 3, 2, 1),
                nn.ReLU(),
                nn.Conv2d(16, 32, 3, 2, 1),
                nn.ReLU(),
                nn.Conv2d(32, 32, 3, 2, 1),
                nn.ReLU(),
            )
            self.dec = nn.Sequential(
                nn.ConvTranspose2d(32, 32, 4, 2, 1),
                nn.ReLU(),
                nn.ConvTranspose2d(32, 16, 4, 2, 1),
                nn.ReLU(),
                nn.ConvTranspose2d(16, 6, 4, 2, 1),
            )

        def forward(self, x):  # type: ignore[no-untyped-def]
            return self.dec(self.enc(x))

    model = TinyAE().to(device)
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    loss_fn = nn.MSELoss()
    ds = torch.utils.data.TensorDataset(torch.from_numpy(patches))
    loader = torch.utils.data.DataLoader(ds, batch_size=batch, shuffle=True)
    model.train()
    for _ in range(epochs):
        for (xb,) in loader:
            xb = xb.to(device)
            opt.zero_grad()
            loss = loss_fn(model(xb), xb)
            loss.backward()
            opt.step()
    return model


def anomaly_map_torch(
    arrays: dict[str, np.ndarray],
    model: Any,
    patch: int = 32,
    stride: int = 16,
    device: str = "cpu",
) -> np.ndarray:
    """Sliding-window reconstruction error -> (H, W) float32 anomaly map."""
    import torch  # type: ignore[import-not-found]

    stacked = stack_for_model(arrays)  # (6, H, W)
    _, h, w = stacked.shape
    acc = np.zeros((h, w), np.float32)
    cnt = np.zeros((h, w), np.float32)
    model.eval()
    with torch.no_grad():
        for r in range(0, h - patch + 1, stride):
            for c in range(0, w - patch + 1, stride):
                p = torch.from_numpy(stacked[:, r : r + patch, c : c + patch]).unsqueeze(0).to(device)
                rec = model(p).cpu().numpy()[0]  # (6, patch, patch)
                err = np.mean((rec - stacked[:, r : r + patch, c : c + patch]) ** 2, axis=0)
                acc[r : r + patch, c : c + patch] += err
                cnt[r : r + patch, c : c + patch] += 1
    cnt[cnt == 0] = 1
    out = (acc / cnt).astype(np.float32)
    # mask NaN regions
    nan_mask = np.isnan(next(iter(arrays.values())))
    out[nan_mask] = np.nan
    return out


# ---------------------------------------------------------------- PCA fallback


def train_pca(patches: np.ndarray, n_components: int = 32) -> Any:
    from sklearn.decomposition import PCA  # type: ignore[import-not-found]

    flat = patches.reshape(len(patches), -1)
    pca = PCA(n_components=min(n_components, len(patches) - 1))
    pca.fit(flat)
    return pca


def anomaly_map_pca(arrays: dict[str, np.ndarray], pca: Any, patch: int = 32, stride: int = 16) -> np.ndarray:
    stacked = stack_for_model(arrays)
    _, h, w = stacked.shape
    acc = np.zeros((h, w), np.float32)
    cnt = np.zeros((h, w), np.float32)
    for r in range(0, h - patch + 1, stride):
        for c in range(0, w - patch + 1, stride):
            p = stacked[:, r : r + patch, c : c + patch].reshape(1, -1)
            rec = pca.inverse_transform(pca.transform(p)).reshape(1, 6, patch, patch)[0]
            err = np.mean((rec - stacked[:, r : r + patch, c : c + patch]) ** 2, axis=0)
            acc[r : r + patch, c : c + patch] += err
            cnt[r : r + patch, c : c + patch] += 1
    cnt[cnt == 0] = 1
    out = (acc / cnt).astype(np.float32)
    out[np.isnan(next(iter(arrays.values())))] = np.nan
    return out


# ---------------------------------------------------------------- Gaussian residual fallback (no deps)


def anomaly_map_residual(arrays: dict[str, np.ndarray]) -> np.ndarray:
    """Cheap anomaly: |DTM - median_filtered DTM| + |LRM| blend.

    No training; good enough to flag regular geometry when torch/sklearn absent.
    """
    dtm = arrays.get("dtm")
    lrm = arrays.get("lrm", arrays.get("lrm20"))
    if dtm is None and lrm is None:
        h, w = next(iter(arrays.values())).shape
        return np.zeros((h, w), np.float32)
    parts: list[np.ndarray] = []
    if dtm is not None:
        filled = np.where(np.isnan(dtm), 0, dtm).astype(np.float32)
        med = ndimage.median_filter(filled, size=7, mode="nearest")
        parts.append(np.abs(filled - med))
    if lrm is not None:
        parts.append(np.abs(np.where(np.isnan(lrm), 0, lrm)))
    out = np.mean(np.stack(parts), axis=0).astype(np.float32)
    out[np.isnan(next(iter(arrays.values())))] = np.nan
    return out


# ---------------------------------------------------------------- high-level helpers


def anomaly_map(
    arrays: dict[str, np.ndarray],
    model: Any | None = None,
    patch: int = 32,
    stride: int = 16,
) -> np.ndarray:
    """Dispatch to the right anomaly backend based on model type."""
    if model is not None:
        # torch model has .eval
        if hasattr(model, "eval"):
            if _has_torch():
                return anomaly_map_torch(arrays, model, patch, stride)
        # sklearn PCA has .transform
        if hasattr(model, "transform"):
            return anomaly_map_pca(arrays, model, patch, stride)
    # no model or unknown -> residual
    return anomaly_map_residual(arrays)


def candidates_from_anomaly(
    amap: np.ndarray,
    grid: Grid,
    thresh: float | None = None,
    min_area_m2: float = 4.0,
    to_wgs84=None,
    support: np.ndarray | None = None,
) -> list[dict[str, Any]]:
    """Threshold anomaly map -> labelled components -> candidates."""
    valid = np.isfinite(amap)
    if not valid.any():
        return []
    if thresh is None:
        # adaptive: mean + 2*std over valid
        vals = amap[valid]
        thresh = float(np.mean(vals) + 2.0 * np.std(vals))
    mask = valid & (amap >= thresh)
    mask = ndimage.binary_opening(mask, structure=np.ones((3, 3)))
    # reuse rules labelling
    try:
        from skimage.measure import label as sk_label  # type: ignore[import-not-found]
        from skimage.measure import regionprops

        lab = sk_label(mask.astype(np.int32), connectivity=2)
        regs = regionprops(lab, intensity_image=np.where(valid, amap, 0))
        out: list[dict[str, Any]] = []
        pix_m2 = grid.res * grid.res
        for reg in regs:
            area_m2 = reg.area * pix_m2
            if area_m2 < min_area_m2:
                continue
            rc = reg.centroid
            from lidar_discovery.detect.rules import _support_fraction as _sf  # local import

            sl = (slice(reg.bbox[0], reg.bbox[2]), slice(reg.bbox[1], reg.bbox[3]))
            frac = _sf(support, sl) if support is not None else 1.0
            out.append(
                {
                    "kind": "other",
                    "centroid_rc": (float(rc[0]), float(rc[1])),
                    "area_m2": float(area_m2),
                    "anomaly_mean": float(np.mean(amap[reg.coords[:, 0], reg.coords[:, 1]])),
                    "low_support": frac < 0.7,
                    "support_fraction": frac,
                    "score": float(np.clip(float(np.mean(amap[reg.coords[:, 0], reg.coords[:, 1]])) / max(thresh, 1), 0, 1)),
                }
            )
        return out
    except Exception:
        lab, _ = ndimage.label(mask, structure=np.ones((3, 3)))
        out2: list[dict[str, Any]] = []
        pix_m2 = grid.res * grid.res
        for lid in range(1, int(lab.max()) + 1):
            idx = np.where(lab == lid)
            area_m2 = len(idx[0]) * pix_m2
            if area_m2 < min_area_m2:
                continue
            rc = (float(np.mean(idx[0])), float(np.mean(idx[1])))
            out2.append({"kind": "other", "centroid_rc": rc, "area_m2": float(area_m2), "score": 0.5})
        return out2
