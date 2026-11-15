"""U-Net segmentation for linear classes (Stage 3, 09 §4.1 D).

Uses `segmentation-models-pytorch` (smp) with ResNet-18/34 encoder, 6 input
channels, ImageNet init. CPU training ~10-30 h; inference 10-60 s/km².
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np


def _require() -> Any:
    try:
        import segmentation_models_pytorch as smp  # type: ignore[import-not-found]
        import torch  # type: ignore[import-not-found]

        return smp, torch
    except Exception as e:  # pragma: no cover
        raise RuntimeError(
            "segmentation-models-pytorch/torch not installed. Run: uv sync --extra ml"
        ) from e


def build_unet(
    encoder: str = "resnet18", in_chans: int = 6, classes: int = 1, pretrained: bool = True
) -> Any:
    smp, _ = _require()
    model = smp.Unet(
        encoder_name=encoder,
        encoder_weights="imagenet" if pretrained else None,
        in_channels=in_chans,
        classes=classes,
    )
    return model


def train_unet(
    train_patches: np.ndarray,
    train_masks: np.ndarray,
    val_patches: np.ndarray | None = None,
    val_masks: np.ndarray | None = None,
    encoder: str = "resnet18",
    epochs: int = 10,
    out_path: Path | None = None,
) -> Any:
    """Train on (N,6,H,W) patches + (N,H,W) masks. Returns model."""
    smp, torch = _require()

    model = build_unet(encoder, in_chans=6, classes=1, pretrained=True)
    opt = torch.optim.Adam(model.parameters(), lr=1e-4)
    loss_fn = smp.losses.DiceLoss(mode="binary")
    ds = torch.utils.data.TensorDataset(
        torch.from_numpy(train_patches), torch.from_numpy(train_masks.astype(np.float32))
    )
    loader = torch.utils.data.DataLoader(ds, batch_size=4, shuffle=True)
    model.train()
    for _ in range(epochs):
        for xb, yb in loader:
            opt.zero_grad()
            pred = model(xb).squeeze(1)
            loss = loss_fn(pred, yb)
            loss.backward()
            opt.step()
    if out_path is not None:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        torch.save(model.state_dict(), out_path)
    return model


def predict_sliding(
    model: Any,
    stacked: np.ndarray,
    patch: int = 256,
    stride: int = 192,
    device: str = "cpu",
    batch: int = 4,
) -> np.ndarray:
    """Sliding-window inference -> (H,W) float32 probability map (0..1)."""
    _, torch = _require()
    import torch  # type: ignore[import-not-found]

    _, h, w = stacked.shape
    acc = np.zeros((h, w), np.float32)
    cnt = np.zeros((h, w), np.float32)
    model.eval()
    dev = torch.device(device)
    model.to(dev)
    # collect windows
    windows: list[tuple[int, int, np.ndarray]] = []
    for r in range(0, h - patch + 1, stride):
        for c in range(0, w - patch + 1, stride):
            windows.append((r, c, stacked[:, r : r + patch, c : c + patch]))
    # handle remainder edges
    if h % stride != 0 or w % stride != 0:
        for r in [h - patch]:
            for c in [w - patch]:
                if r >= 0 and c >= 0 and (r, c) not in {(x[0], x[1]) for x in windows}:
                    windows.append((r, c, stacked[:, r : r + patch, c : c + patch]))
    with torch.no_grad():
        for i in range(0, len(windows), batch):
            batch_w = windows[i : i + batch]
            xb = torch.from_numpy(np.stack([x[2] for x in batch_w])).to(dev)
            preds = torch.sigmoid(model(xb)).cpu().numpy()  # (B,1,H,W) or (B,H,W)
            if preds.ndim == 4:
                preds = preds[:, 0]
            for (r, c, _), pred in zip(batch_w, preds):
                # keep central 192x192 (16 m margin) if overlapping
                m = 32
                r0, r1 = r + m, r + patch - m
                c0, c1 = c + m, c + patch - m
                # clamp
                r0c, r1c = max(0, r0), min(h, r1)
                c0c, c1c = max(0, c0), min(w, c1)
                pr0, pr1 = r0c - r, r1c - r
                pc0, pc1 = c0c - c, c1c - c
                acc[r0c:r1c, c0c:c1c] += pred[pr0:pr1, pc0:pc1]
                cnt[r0c:r1c, c0c:c1c] += 1
    cnt[cnt == 0] = 1
    return (acc / cnt).astype(np.float32)

def train(*args, **kwargs):  # type: ignore[no-untyped-def]
    return train_unet(*args, **kwargs)

def predict(*args, **kwargs):  # type: ignore[no-untyped-def]
    return predict_sliding(*args, **kwargs)

def load(path, encoder="resnet18", in_chans=6, classes=1, pretrained=False):  # type: ignore[no-untyped-def]
    model = build_unet(encoder=encoder, in_chans=in_chans, classes=classes, pretrained=pretrained)
    import torch  # type: ignore[import-not-found]
    state = torch.load(str(path), map_location="cpu")
    model.load_state_dict(state)
    model.eval()
    return model

def build_model(*args, **kwargs):  # type: ignore[no-untyped-def]
    return build_unet(*args, **kwargs)
