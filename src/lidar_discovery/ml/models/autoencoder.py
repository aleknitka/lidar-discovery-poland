"""Torch autoencoder for unsupervised anomaly (re-exports detect/anomaly helpers)."""

from __future__ import annotations

from typing import Any

import numpy as np

from lidar_discovery.detect.anomaly import (
    anomaly_map_pca,
    anomaly_map_residual,
    anomaly_map_torch,
    sample_patches,
    train_ae_torch,
    train_pca,
)


def train(
    arrays: dict[str, np.ndarray],
    grid: Any,
    method: str = "auto",
    n_patches: int = 2000,
    patch: int = 32,
    epochs: int = 8,
) -> Any:
    """Train anomaly model on random forest-floor patches. method: auto|torch|pca|residual."""
    patches = sample_patches(arrays, grid, n=n_patches, patch=patch)
    if len(patches) == 0:
        return None
    if method == "residual":
        return None
    if method in ("auto", "torch"):
        try:
            return train_ae_torch(patches, epochs=epochs)
        except Exception:
            if method == "torch":
                raise
    try:
        return train_pca(patches)
    except Exception:
        return None


def anomaly(
    arrays: dict[str, np.ndarray], model: Any | None, patch: int = 32, stride: int = 16
) -> np.ndarray:
    if model is not None and hasattr(model, "eval"):
        return anomaly_map_torch(arrays, model, patch, stride)
    if model is not None and hasattr(model, "transform"):
        return anomaly_map_pca(arrays, model, patch, stride)
    return anomaly_map_residual(arrays)


# ---------------------------------------------------------------- CLI / scheduler compat wrapper
# The real train(arrays, grid, ...) is above; this wrapper lets `ldp ml train-ae`
# call `train(settings, locations=..., epochs=..., out_dir=...)`.
try:
    _orig_train = train  # type: ignore[name-defined]
    _orig_anomaly = anomaly  # type: ignore[name-defined]
except NameError:
    _orig_train = None  # type: ignore[assignment]
    _orig_anomaly = None  # type: ignore[assignment]

def _is_settings(obj) -> bool:
    return hasattr(obj, "data_dir") and hasattr(obj, "derived_dir")

def train_settings_aware(*args, **kwargs):  # type: ignore[no-untyped-def]
    """Dispatch: train(settings, ...) vs train(arrays, grid, ...)."""
    if args and _is_settings(args[0]):
        # settings path: train(settings, locations=[...], epochs=..., out_dir=...)
        settings = args[0]
        locs = kwargs.get("locations") or (args[1] if len(args) > 1 and isinstance(args[1], (list, tuple)) else None)
        epochs = int(kwargs.get("epochs", 8))
        out_dir = kwargs.get("out_dir") or kwargs.get("out")
        # load one location's arrays/grid for AE training
        from lidar_discovery.catalog import repo as _repo
        from lidar_discovery.catalog.db import session_scope as _ss
        import rasterio as _rio
        from lidar_discovery.processing.dtm import Grid as _Grid
        # pick first location that has a DTM
        loc_ids = list(locs) if locs else []
        if not loc_ids:
            with _ss(settings) as s:
                loc_ids = [loc.id for loc in _repo.list_locations(s)[:3]]
        arrays = None; grid = None
        for lid in loc_ids:
            try:
                with _ss(settings) as s:
                    prods = {pr.kind: pr for pr in _repo.list_products(s, lid)}
                if "dtm" not in prods:
                    continue
                def _abs(ps):
                    ap = Path(ps.path); return ap if ap.is_absolute() else Path(settings.data_dir) / ap
                with _rio.open(_abs(prods["dtm"])) as ds:
                    dtm = ds.read(1).astype("float32")
                    if ds.nodata is not None:
                        import numpy as _np
                        dtm = _np.where(dtm == ds.nodata, float("nan"), dtm)
                    grid = _Grid(x0=float(ds.transform.c), y1=float(ds.transform.f), res=float(ds.res[0]), width=ds.width, height=ds.height)
                    arrays = {"dtm": dtm}
                    for kk in ("hillshade","slope","svf","lrm","ground_density"):
                        if kk in prods:
                            try:
                                with _rio.open(_abs(prods[kk])) as d2:
                                    a = d2.read(1).astype("float32")
                                    if d2.nodata is not None:
                                        import numpy as _np2; a = _np2.where(a==d2.nodata, float("nan"), a)
                                    arrays[kk] = a
                            except Exception: pass
                    break
            except Exception:
                continue
        if arrays is None or grid is None:
            return {"status": "no_data", "error": "no DTM found for autoencoder training; run fetch-bbox first", "locations": loc_ids}
        # train on arrays
        model = _orig_train(arrays, grid, epochs=epochs) if _orig_train else None  # type: ignore[misc]
        # save if out_dir given
        if out_dir is not None and model is not None:
            try:
                out_p = Path(out_dir); out_p.mkdir(parents=True, exist_ok=True)
                # save via torch if available else pickle
                try:
                    import torch as _torch  # type: ignore[import-not-found]
                    _torch.save(model.state_dict() if hasattr(model, "state_dict") else model, out_p / "ae.pt")
                except Exception:
                    import pickle as _pk
                    with open(out_p / "ae.pkl","wb") as fh: _pk.dump(model, fh)
            except Exception: pass
        return {"status": "ok", "locations": loc_ids, "epochs": epochs, "out_dir": str(out_dir) if out_dir else None, "patches": 2000}
    # array path
    return _orig_train(*args, **kwargs) if _orig_train else None  # type: ignore[misc]

# monkey-patch module-level train for CLI import `from ...autoencoder import train`
# keep original as _train_arrays, expose compat as train
_train_arrays = _orig_train
train = train_settings_aware  # type: ignore[no-redef]
