"""Patch/chip sampler with rasterio windowed reads + 8-fold augmentation (09 §2.4)."""

from __future__ import annotations

import random
from pathlib import Path
from typing import Any

import numpy as np


def augment_8fold(chip: np.ndarray, k: int) -> np.ndarray:
    """Rotate/flip a (C,H,W) chip. k in 0..7 covers D4 group."""
    # k: 0..3 = rot90 k times, 4..7 = flip then rot
    # chip is (C,H,W) or (H,W)
    flip = k >= 4
    rot = k % 4
    out = chip
    if flip:
        # horizontal flip (W axis)
        out = np.flip(out, axis=-1).copy()
    if rot:
        # rotate in HW plane (axes -2, -1)
        out = np.rot90(out, k=rot, axes=(-2, -1)).copy()
    return out


class PatchSampler:
    """On-the-fly rasterio windowed patch sampler (no bulk export)."""

    def __init__(
        self,
        cog_paths: dict[str, Path | str],
        patch: int = 256,
        res: float = 0.5,
    ) -> None:
        self.cog_paths = {k: Path(v) for k, v in cog_paths.items()}
        self.patch = patch
        self.res = res

    def read_patch(self, row: int, col: int) -> dict[str, np.ndarray]:
        """Read patch at (row,col) in pixel coords from each COG."""
        import rasterio  # type: ignore[import-not-found]

        out: dict[str, np.ndarray] = {}
        for kind, path in self.cog_paths.items():
            if not path.exists():
                continue
            with rasterio.open(path) as ds:
                win = rasterio.windows.Window(col, row, self.patch, self.patch)
                arr = ds.read(1, window=win, boundless=True, fill_value=float(ds.nodata or -9999))
                arr = np.where(arr == -9999, np.nan, arr).astype(np.float32)
                # pad if near edge
                if arr.shape != (self.patch, self.patch):
                    tmp = np.full((self.patch, self.patch), np.nan, np.float32)
                    h, w = arr.shape
                    tmp[:h, :w] = arr
                    arr = tmp
                out[kind] = arr
        return out

    def random_patches(
        self, n: int, shape: tuple[int, int], seed: int = 0
    ) -> list[dict[str, np.ndarray]]:
        rng = random.Random(seed)
        h, w = shape
        out = []
        for _ in range(n):
            r = rng.randint(0, max(0, h - self.patch))
            c = rng.randint(0, max(0, w - self.patch))
            patch = self.read_patch(r, c)
            # random aug
            k = rng.randint(0, 7)
            patch = {kk: augment_8fold(v[None, :, :], k)[0] if v.ndim == 2 else augment_8fold(v, k) for kk, v in patch.items()}
            out.append(patch)
        return out


def iter_chip_batches(
    cands: list[dict[str, Any]],
    arrays: dict[str, np.ndarray],
    grid: Any,
    chip: int = 96,
    batch: int = 32,
    shuffle: bool = True,
    seed: int = 0,
) -> Any:
    """Yield batches of (B, 6, chip, chip) chips centred on candidates."""
    from lidar_discovery.ml.channels import stack_for_model

    stacked = stack_for_model(arrays)  # (6, H, W)
    _, h, w = stacked.shape
    idxs = list(range(len(cands)))
    if shuffle:
        rng = random.Random(seed)
        rng.shuffle(idxs)
    half = chip // 2
    for i in range(0, len(idxs), batch):
        batch_idxs = idxs[i : i + batch]
        chips = []
        for j in batch_idxs:
            rc = cands[j].get("centroid_rc") or (h // 2, w // 2)
            r, c = int(round(rc[0])), int(round(rc[1]))
            r0, c0 = max(0, r - half), max(0, c - half)
            r1, c1 = r0 + chip, c0 + chip
            # pad if needed
            chip_arr = np.zeros((6, chip, chip), np.float32)
            # copy with clamping
            sr0, sc0 = max(0, r0), max(0, c0)
            sr1, sc1 = min(h, r1), min(w, c1)
            dr0, dc0 = sr0 - r0, sc0 - c0
            dr1, dc1 = dr0 + (sr1 - sr0), dc0 + (sc1 - sc0)
            chip_arr[:, dr0:dr1, dc0:dc1] = stacked[:, sr0:sr1, sc0:sc1]
            chips.append(chip_arr)
        yield np.stack(chips) if chips else np.zeros((0, 6, chip, chip), np.float32)
