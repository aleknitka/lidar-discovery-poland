"""CNN chip classifier / embedding extractor (Stage 2, 09 §4.1 C).

Uses `timm` (ResNet-18/34, EfficientNet-B0) with first conv adapted to 6 channels.
Gracefully errors if timm/torch missing.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np


def _require_torch() -> Any:
    try:
        import torch  # type: ignore[import-not-found]

        return torch
    except Exception as e:  # pragma: no cover
        raise RuntimeError("torch not installed. Run: uv sync --extra ml") from e


def _require_timm() -> Any:
    try:
        import timm  # type: ignore[import-not-found]

        return timm
    except Exception as e:  # pragma: no cover
        raise RuntimeError("timm not installed. Run: uv sync --extra ml") from e


def build_encoder(name: str = "resnet18", in_chans: int = 6, pretrained: bool = True) -> Any:
    _require_torch()
    timm = _require_timm()

    model = timm.create_model(name, pretrained=pretrained, in_chans=in_chans, num_classes=0, global_pool="avg")
    return model


def embed_chips(
    model: Any, chips: np.ndarray, batch: int = 32, device: str = "cpu"
) -> np.ndarray:
    """Forward pass -> (N, D) embeddings. Chips: (N, 6, H, W) float32."""
    import torch  # type: ignore[import-not-found]

    model.eval()
    dev = torch.device(device)
    model.to(dev)
    out: list[np.ndarray] = []
    with torch.no_grad():
        for i in range(0, len(chips), batch):
            batch_arr = torch.from_numpy(chips[i : i + batch]).to(dev)
            emb = model(batch_arr)
            out.append(emb.cpu().numpy())
    return np.concatenate(out, axis=0) if out else np.zeros((0, 0), np.float32)


def train_classifier(
    train_chips: np.ndarray,
    train_y: np.ndarray,
    val_chips: np.ndarray | None = None,
    val_y: np.ndarray | None = None,
    name: str = "resnet18",
    epochs: int = 10,
    lr: float = 1e-4,
    out_path: Path | None = None,
) -> Any:
    """Fine-tune a timm encoder + linear head for binary classification. Returns model."""
    import torch  # type: ignore[import-not-found]
    from torch import nn  # type: ignore[import-not-found]

    torch_model = build_encoder(name, in_chans=6, pretrained=True)
    # add head
    dim = int(torch_model.num_features) if hasattr(torch_model, "num_features") else 512
    head = nn.Linear(dim, 1)

    class Full(nn.Module):
        def __init__(self, enc, head):  # type: ignore[no-untyped-def]
            super().__init__()
            self.enc = enc
            self.head = head

        def forward(self, x):  # type: ignore[no-untyped-def]
            return self.head(self.enc(x)).squeeze(1)

    model = Full(torch_model, head)
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    loss_fn = nn.BCEWithLogitsLoss()
    # tiny dataloader
    ds = torch.utils.data.TensorDataset(torch.from_numpy(train_chips), torch.from_numpy(train_y.astype(np.float32)))
    loader = torch.utils.data.DataLoader(ds, batch_size=32, shuffle=True)
    model.train()
    for _ in range(epochs):
        for xb, yb in loader:
            opt.zero_grad()
            loss = loss_fn(model(xb), yb)
            loss.backward()
            opt.step()
    if out_path is not None:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        torch.save(model.state_dict(), out_path)
    return model

def train(*args, **kwargs):  # type: ignore[no-untyped-def]
    """Alias for train_classifier (uniform contract)."""
    return train_classifier(*args, **kwargs)


def _predict_logits(model, chips, batch=32, device="cpu"):  # type: ignore[no-untyped-def]
    import torch  # type: ignore[import-not-found]
    model.eval()
    dev = torch.device(device)
    model.to(dev)
    out: list = []
    import numpy as _np
    with torch.no_grad():
        for i in range(0, len(chips), batch):
            xb = torch.from_numpy(chips[i : i + batch]).to(dev)
            logits = model(xb)
            if logits.ndim > 1:
                logits = logits.squeeze(1)
            probs = torch.sigmoid(logits).cpu().numpy()
            out.append(_np.asarray(probs, dtype=_np.float32))
    return _np.concatenate(out) if out else _np.zeros(0, dtype=_np.float32)


def predict(model, chips, batch=32, device="cpu"):  # type: ignore[no-untyped-def]
    return _predict_logits(model, chips, batch=batch, device=device)


def load(path, name="resnet18", device="cpu"):  # type: ignore[no-untyped-def]
    import torch  # type: ignore[import-not-found]
    from torch import nn  # type: ignore[import-not-found]
    torch_model = build_encoder(name, in_chans=6, pretrained=False)
    dim = int(torch_model.num_features) if hasattr(torch_model, "num_features") else 512
    head = nn.Linear(dim, 1)
    class Full(nn.Module):  # type: ignore[no-redef]
        def __init__(self, enc, head):  # type: ignore[no-untyped-def]
            super().__init__()
            self.enc = enc
            self.head = head
        def forward(self, x):  # type: ignore[no-untyped-def]
            return self.head(self.enc(x)).squeeze(1)
    model = Full(torch_model, head)
    state = torch.load(str(path), map_location=device)
    model.load_state_dict(state)
    model.eval()
    return model


def build_model(*args, **kwargs):  # type: ignore[no-untyped-def]
    return build_encoder(*args, **kwargs)

