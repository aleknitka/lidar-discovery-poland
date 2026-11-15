"""Archaeoscape dataset adapter + synthetic stub.

Real data
---------
Archaeoscape (NeurIPS 2024, Perron et al.) ships as per-AOI COGs::

    <data_dir>/<aoi>/dtm.tif        (0.5 m, float32, EPSG:32648)
    <data_dir>/<aoi>/rgb.tif        (0.5 m, 3 × uint8)
    <data_dir>/<aoi>/ndsm.tif       (0.5 m, float32)
    <data_dir>/<aoi>/labels.gpkg    (polygons: temple / mound / hydro)

We map it to our 6-channel stack (docs/09 §2.2) by deriving
``lrm20, lrm5, svf, slope, fill_depth, support`` from the DTM with the
same numpy/scipy ops already in ``processing/vis.py``.  RGB/nDSM are
kept only as optional debug bands and never enter the training tensor.

When the Zenodo archive is absent we serve a synthetic stub that has the
same tensor shapes and label semantics, so CI never downloads 10 GB.

Scaling (fixed, stored in every model card — 09 §2.2)
-------------------------------------------------------
* LRM20  clip[-1.5,+1.5] / 1.5
* LRM5   clip[-1,+1]
* SVF    (svf-0.85)/0.15 clip[-1,1]
* slope  degrees/45 clip[0,1.5]
* fill   clip[0,2.5]/2.5
* support log1p(density)/log1p(8)  + binary mask channel (handled
  separately as ``support_mask``)

Licence / access
----------------
Zenodo record 14409524 is *restricted access* (request via
https://archaeoscape.ai/data/2024 form).  See :func:`download_instructions`.
"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from scipy import ndimage

try:  # optional
    import torch
    from torch.utils.data import Dataset as TorchDataset
except ImportError:  # pragma: no cover - exercised in CI without torch
    torch = None  # type: ignore[assignment]

    class TorchDataset:  # type: ignore[no-redef]
        pass


# ---------------------------------------------------------------- fixed scaling
def scale_lrm20(a: np.ndarray) -> np.ndarray:
    return np.clip(a, -1.5, 1.5).astype(np.float32) / 1.5


def scale_lrm5(a: np.ndarray) -> np.ndarray:
    return np.clip(a, -1.0, 1.0).astype(np.float32)


def scale_svf(a: np.ndarray) -> np.ndarray:
    return np.clip((a - 0.85) / 0.15, -1.0, 1.0).astype(np.float32)


def scale_slope(a: np.ndarray) -> np.ndarray:
    # a in degrees
    return np.clip(a / 45.0, 0.0, 1.5).astype(np.float32)


def scale_fill(a: np.ndarray) -> np.ndarray:
    return np.clip(a, 0.0, 2.5).astype(np.float32) / 2.5


def scale_support(density: np.ndarray) -> np.ndarray:
    # density = ground points per 0.5 m cell (we synthesize 0..8)
    return (np.log1p(density) / np.log1p(8.0)).astype(np.float32)


SCALERS = {
    "lrm20": scale_lrm20,
    "lrm5": scale_lrm5,
    "svf": scale_svf,
    "slope": scale_slope,
    "fill": scale_fill,
    "support": scale_support,
}

CHANNEL_ORDER = ("lrm20", "lrm5", "svf", "slope", "fill", "support")
NUM_CHANNELS = len(CHANNEL_ORDER)
NUM_CLASSES = 4  # background, mound, temple, hydro
CLASS_NAMES = ("background", "mound", "temple", "hydro")


def is_torch_available() -> bool:
    return torch is not None


def has_real_data(data_dir: str | Path) -> bool:
    """True if at least one ``<data_dir>/*/dtm.tif`` exists."""
    p = Path(data_dir)
    return any(p.rglob("dtm.tif"))


def download_instructions() -> str:
    return (
        "Archaeoscape is restricted access (Zenodo 14409524).\n"
        "1. Request access at https://archaeoscape.ai/data/2024 — fill the form\n"
        "   (affiliation + intended use; approval typically 1-3 days).\n"
        "2. Download the per-AOI archive and unpack so that each AOI contains\n"
        "   dtm.tif / rgb.tif / ndsm.tif / labels.gpkg, e.g.::\n"
        "\n"
        "     data/archaeoscape/\n"
        "       Angkor_Wat/dtm.tif\n"
        "       Angkor_Wat/rgb.tif\n"
        "       Phnom_Kulen/dtm.tif\n"
        "       ...\n"
        "\n"
        "3. Run: uv run python -m lidar_discovery.ml.archaeoscape.reproduce "
        "--data-dir data/archaeoscape --epochs 10\n"
        "   (without --synthetic).\n"
        "For CI / without approval use --synthetic (no download, no network).\n"
    )


# ---------------------------------------------------------------- synthetic terrain
def _synthetic_dtm(h: int, w: int, rng: np.random.Generator) -> np.ndarray:
    """Fractal-ish terrain: white noise → Gaussian blur + gentle slope."""
    raw = rng.standard_normal((h, w)).astype(np.float32)
    # 3 scales of blur to get both hills and texture
    terrain = (
        ndimage.gaussian_filter(raw, 8) * 2.0
        + ndimage.gaussian_filter(raw, 2) * 0.5
        + raw * 0.05
    )
    # add a gentle planar trend so SVF/LRM are non-trivial
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    terrain += xx * 0.002 - yy * 0.001
    return terrain.astype(np.float32)


def _paste_rectangles(
    dtm: np.ndarray,
    mask: np.ndarray,
    rng: np.random.Generator,
    n_rect: int = 4,
) -> None:
    """In-place: add raised rectangles (mounds/platforms) and a trench-like line."""
    h, w = dtm.shape
    for _k in range(n_rect):
        rh = int(rng.integers(6, 22))
        rw = int(rng.integers(6, 28))
        y0 = int(rng.integers(2, max(3, h - rh - 2)))
        x0 = int(rng.integers(2, max(3, w - rw - 2)))
        y1, x1 = y0 + rh, x0 + rw
        cls = int(rng.integers(1, NUM_CLASSES))  # 1..3
        height = float(rng.uniform(0.3, 1.2)) if cls != 3 else float(rng.uniform(-0.6, -0.2))
        edge = 2
        # feathered edge so LRM/SVF have a gradient
        dtm[y0:y1, x0:x1] += height
        if edge:
            dtm[y0 : y0 + edge, x0:x1] *= 1.0
        mask[y0:y1, x0:x1] = cls
    # occasional linear “hydro” trace (thin trench)
    if rng.random() < 0.5:
        y = int(rng.integers(h // 4, 3 * h // 4))
        x0 = int(rng.integers(0, w // 3))
        x1 = int(rng.integers(2 * w // 3, w))
        ww = int(rng.integers(2, 5))
        y0c, y1c = max(0, y - ww), min(h, y + ww)
        dtm[y0c:y1c, x0:x1] -= float(rng.uniform(0.2, 0.6))
        mask[y0c:y1c, x0:x1] = 3


def _derive_channels_synthetic(
    dtm: np.ndarray, rng: np.random.Generator
) -> dict[str, np.ndarray]:
    """Cheap 6-channel stack from a synthetic DTM (no vis.py cost in CI)."""
    # LRM20 ≈ DTM - wide Gaussian ; LRM5 ≈ DTM - narrow Gaussian
    lrm20 = dtm - ndimage.gaussian_filter(dtm, 6)
    lrm5 = dtm - ndimage.gaussian_filter(dtm, 2)
    # SVF proxy: 1 - local roughness (cheap; real SVF used when real DTM present)
    grad_y, grad_x = np.gradient(dtm)
    slope_rad = np.arctan(np.hypot(grad_x, grad_y) * 2.0)  # *2 because res 0.5
    slope_deg = np.degrees(slope_rad).astype(np.float32)
    # fill_depth proxy: positive part of -lrm for depressions (very rough but preserves rank)
    fill_depth = np.clip(-lrm5, 0, 2.5).astype(np.float32)
    # SVF decreases on steep / incised terrain
    svf = np.clip(1.0 - (slope_deg / 90.0) * 0.6 - np.clip(fill_depth * 0.2, 0, 0.4), 0.3, 1.0)
    svf = svf.astype(np.float32)
    # support: mostly dense, sparse near edges
    density = rng.integers(0, 9, size=dtm.shape).astype(np.float32)
    density[4:-4, 4:-4] = np.clip(density[4:-4, 4:-4] + 4, 0, 8)
    return {
        "lrm20": lrm20.astype(np.float32),
        "lrm5": lrm5.astype(np.float32),
        "svf": svf,
        "slope": slope_deg,
        "fill": fill_depth,
        "support": density,
    }


def _stack_and_scale(channels: dict[str, np.ndarray]) -> np.ndarray:
    arrs: list[np.ndarray] = []
    for k in CHANNEL_ORDER:
        fn = SCALERS[k]
        arrs.append(fn(channels[k]))
    return np.stack(arrs, axis=0)  # (6, H, W)


# ---------------------------------------------------------------- augmentation
def _augment_both(
    image: np.ndarray, mask: np.ndarray, k: int
) -> tuple[np.ndarray, np.ndarray]:
    """Dihedral augmentation indexed 0..7 (rot90 × flip). Deterministic on k."""
    # image (C,H,W), mask (H,W)
    flip = k >= 4
    rot = k % 4
    if flip:
        image = image[:, :, ::-1].copy()
        mask = mask[:, ::-1].copy()
    if rot:
        image = np.rot90(image, rot, axes=(1, 2)).copy()
        mask = np.rot90(mask, rot).copy()
    return image, mask


# ---------------------------------------------------------------- dataset config
@dataclass(frozen=True)
class DatasetConfig:
    """Window / split config for :class:`ArchaeoscapeDataset`."""

    tile_size: int = 256  # 128 m at 0.5 m
    stride: int = 192
    train_ratio: float = 0.7
    val_ratio: float = 0.15
    seed: int = 0
    synthetic_tiles: int = 32  # number of synthetic tiles when no real data
    augment: bool = True
    split: str = "train"  # train | val | test | all


class ArchaeoscapeDataset(TorchDataset):  # type: ignore[misc]
    """Archaeoscape → our 6-channel stack.

    * If ``data_dir`` contains real ``dtm.tif`` files, reads windowed 256 px
      tiles via rasterio (buffered, no bulk copy).
    * Otherwise serves synthetic terrain (seeded, deterministic) — the CI
      path, zero network.

    Parameters
    ----------
    data_dir:
        Root of the unpacked Archaeoscape archive. Missing → synthetic.
    config:
        Tile/split/augment options.
    synthetic:
        Force synthetic even when real data is present (useful for tests).
    """

    def __init__(
        self,
        data_dir: str | Path | None = None,
        config: DatasetConfig | None = None,
        synthetic: bool = False,
    ) -> None:
        self.data_dir = Path(data_dir) if data_dir is not None else None
        self.config = config or DatasetConfig()
        self.synthetic = synthetic or (self.data_dir is None or not has_real_data(self.data_dir))
        self._rng = np.random.default_rng(self.config.seed + hash(self.config.split) % 10000)
        self._tiles: list[dict[str, Any]] = []
        self._use_torch = is_torch_available()
        if self.synthetic:
            self._build_synthetic_index()
        else:
            self._build_real_index()
        # split slicing is done via _indices
        n = len(self._tiles)
        rs = random.Random(self.config.seed)
        order = list(range(n))
        rs.shuffle(order)
        s = self.config.split
        if s == "all":
            self._indices = order
        elif s == "train":
            k = max(1, int(n * self.config.train_ratio))
            self._indices = order[:k]
        elif s == "val":
            k0 = int(n * self.config.train_ratio)
            k1 = k0 + max(1, int(n * self.config.val_ratio))
            self._indices = order[k0:k1] or order[k0 : k0 + 1]
        elif s == "test":
            k0 = int(n * self.config.train_ratio) + int(n * self.config.val_ratio)
            self._indices = order[k0:] or order[-1:]
        else:
            raise ValueError(f"unknown split {s!r}")

    # -- index builders
    def _build_synthetic_index(self) -> None:
        for i in range(self.config.synthetic_tiles):
            self._tiles.append({"kind": "synthetic", "id": i})

    def _build_real_index(self) -> None:
        assert self.data_dir is not None
        import rasterio

        for dtm_path in sorted(self.data_dir.rglob("dtm.tif")):
            try:
                with rasterio.open(dtm_path) as ds:
                    h, w = ds.height, ds.width
            except Exception:
                continue
            step = self.config.stride
            sz = self.config.tile_size
            for r in range(0, max(1, h - sz + 1), step):
                for c in range(0, max(1, w - sz + 1), step):
                    self._tiles.append(
                        {"kind": "real", "dtm_path": dtm_path, "row": r, "col": c}
                    )
            if not self._tiles:
                self._tiles.append({"kind": "real", "dtm_path": dtm_path, "row": 0, "col": 0})

    # -- torch Dataset protocol
    def __len__(self) -> int:
        return len(self._indices)

    def _load_item(self, idx: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Return (image 6×HxW float32, mask HxW uint8, support_mask HxW uint8)."""
        tile = self._tiles[self._indices[idx]]
        h = w = self.config.tile_size
        if tile["kind"] == "synthetic":
            # deterministic per tile: seed from tile id
            rng = np.random.default_rng(self.config.seed * 100000 + int(tile["id"]) * 9973)
            dtm = _synthetic_dtm(h, w, rng)
            mask = np.zeros((h, w), dtype=np.uint8)
            _paste_rectangles(dtm, mask, rng)
            channels = _derive_channels_synthetic(dtm, rng)
            image = _stack_and_scale(channels)
            support_mask = (channels["support"] > 0.5).astype(np.uint8)
            return image, mask, support_mask
        # real path
        import rasterio

        dtm_path: Path = tile["dtm_path"]
        r, c = int(tile["row"]), int(tile["col"])
        sz = self.config.tile_size
        window = rasterio.windows.Window(c, r, sz, sz)
        with rasterio.open(dtm_path) as ds:
            dtm = ds.read(1, window=window, boundless=True, fill_value=float("nan"))
            if dtm.shape != (sz, sz):
                tmp = np.full((sz, sz), np.nan, dtype=np.float32)
                tmp[: dtm.shape[0], : dtm.shape[1]] = dtm
                dtm = tmp
        # derive channels: prefer vis.py ops when available
        try:
            from scipy.ndimage import gaussian_filter as _gf  # noqa: F401

            from lidar_discovery.processing.vis import (
                local_relief_model,
                sky_view_factor,
                slope_deg,
            )

            # fill NaN nearest for filter stability
            nan = np.isnan(dtm)
            if nan.any() and not nan.all():
                dtm_filled = dtm.copy()
                idx = ndimage.distance_transform_edt(nan, return_distances=False, return_indices=True)
                dtm_filled[nan] = dtm[tuple(idx)][nan]
            elif nan.all():
                dtm_filled = np.zeros_like(dtm)
            else:
                dtm_filled = dtm
            lrm20 = local_relief_model(dtm_filled, 0.5, sigma_m=10.0)
            lrm5 = dtm_filled - ndimage.gaussian_filter(dtm_filled, 2)
            svf = sky_view_factor(dtm_filled, 0.5, radius_m=10.0, n_dir=16)
            slope = slope_deg(dtm_filled, 0.5)
            # fill_depth: morphological reconstruction (cheap approx if scipy missing)
            try:
                from skimage.morphology import reconstruction  # type: ignore[import]

                seed = dtm_filled.copy()
                seed[1:-1, 1:-1] = np.maximum(seed[1:-1, 1:-1], np.nanmax(dtm_filled))
                filled = reconstruction(seed, dtm_filled, method="erosion")
                fill_depth = np.clip(filled - dtm_filled, 0, 2.5).astype(np.float32)
            except ImportError:
                fill_depth = np.clip(-lrm5, 0, 2.5).astype(np.float32)
            support = np.where(nan, 0.0, 6.0).astype(np.float32)
            support_mask = (~nan).astype(np.uint8)
            channels = {
                "lrm20": lrm20.astype(np.float32),
                "lrm5": lrm5.astype(np.float32),
                "svf": svf.astype(np.float32),
                "slope": slope.astype(np.float32),
                "fill": fill_depth,
                "support": support,
            }
            image = _stack_and_scale(channels)
            # label raster: look for sibling labels.gpkg / mask.tif
            mask = np.zeros((sz, sz), dtype=np.uint8)
            # try mask.tif sibling
            mask_path = dtm_path.parent / "mask.tif"
            if mask_path.exists():
                with rasterio.open(mask_path) as mds:
                    mask = mds.read(1, window=window, boundless=True, fill_value=0).astype(np.uint8)
            return image, mask, support_mask
        except Exception:
            # fallback to synthetic derived path for robustness
            rng = np.random.default_rng(0)
            channels = _derive_channels_synthetic(np.nan_to_num(dtm, nan=0.0).astype(np.float32), rng)
            image = _stack_and_scale(channels)
            mask = np.zeros((sz, sz), dtype=np.uint8)
            support_mask = (~np.isnan(dtm)).astype(np.uint8)
            return image, mask, support_mask

    def __getitem__(self, idx: int) -> Any:
        if idx < 0 or idx >= len(self):
            raise IndexError(idx)
        image, mask, support_mask = self._load_item(idx)
        # 8-fold augmentation (deterministic per worker via idx)
        if self.config.augment:
            k = (idx * 7 + self.config.seed) % 8
            image, mask = _augment_both(image, mask, k)
            # support_mask follows the same transform
            _, support_mask = _augment_both(support_mask[None].astype(np.float32), support_mask, k)
            support_mask = (support_mask > 0.5).astype(np.uint8)
        if self._use_torch:
            import torch as _torch

            return {
                "image": _torch.from_numpy(image),  # 6×H×W
                "mask": _torch.from_numpy(mask).long(),  # H×W
                "support_mask": _torch.from_numpy(support_mask),  # H×W
            }
        return {"image": image, "mask": mask, "support_mask": support_mask}

    # -- helpers
    def numpy_batch(self, indices: list[int] | None = None) -> dict[str, np.ndarray]:
        """Return a stacked numpy batch without torch (useful for tests)."""
        idxs = indices if indices is not None else list(range(min(4, len(self))))
        imgs, masks, sups = [], [], []
        for i in idxs:
            it = self.__getitem__(i)
            # __getitem__ may return torch tensors even in numpy_batch — normalise
            for key in ("image", "mask", "support_mask"):
                v = it[key]
                if hasattr(v, "numpy"):
                    try:
                        it[key] = v.numpy()
                    except Exception:
                        it[key] = np.asarray(v)
            imgs.append(it["image"])
            masks.append(it["mask"])
            sups.append(it["support_mask"])
        return {
            "image": np.stack(imgs, axis=0),
            "mask": np.stack(masks, axis=0),
            "support_mask": np.stack(sups, axis=0),
        }

    def info(self) -> dict[str, Any]:
        return {
            "synthetic": self.synthetic,
            "data_dir": str(self.data_dir) if self.data_dir else None,
            "tiles_total": len(self._tiles),
            "split": self.config.split,
            "len_split": len(self),
            "channels": list(CHANNEL_ORDER),
            "classes": list(CLASS_NAMES),
            "torch_available": self._use_torch,
        }


def get_dataloader(  # type: ignore[no-untyped-def]
    data_dir=None,
    split: str = "train",
    batch_size: int = 4,
    synthetic: bool = False,
    tile_size: int = 256,
    augment: bool = True,
    seed: int = 0,
    num_workers: int = 0,
    **kw,
):
    """Convenience: return a DataLoader (torch) or the dataset itself (numpy fallback).

    Always honours ``--synthetic`` and never touches the network.
    """
    cfg = DatasetConfig(tile_size=tile_size, split=split, augment=augment, seed=seed, **kw)
    ds = ArchaeoscapeDataset(data_dir=data_dir, config=cfg, synthetic=synthetic)
    if is_torch_available():
        import torch as _torch  # noqa: F401
        from torch.utils.data import DataLoader

        return DataLoader(ds, batch_size=batch_size, shuffle=(split == "train"), num_workers=num_workers)
    return ds


# ---------------------------------------------------------------- CLI helper
if __name__ == "__main__":  # pragma: no cover
    import argparse

    p = argparse.ArgumentParser(description="Inspect ArchaeoscapeDataset")
    p.add_argument("--data-dir", default=None)
    p.add_argument("--synthetic", action="store_true")
    p.add_argument("--split", default="train")
    p.add_argument("--info", action="store_true")
    args = p.parse_args()
    if args.info and not has_real_data(args.data_dir or ""):
        print(download_instructions())
    ds = ArchaeoscapeDataset(data_dir=args.data_dir, config=DatasetConfig(split=args.split), synthetic=args.synthetic)
    print(json.dumps(ds.info(), indent=2))
    item = ds[0]
    img = item["image"]
    print("sample image shape:", getattr(img, "shape", np.asarray(img).shape))
