"""Ablation: ImageNet vs Archaeoscape pretraining vs scratch.

Experiment per docs/11 §12 item 4.

Design
------
* Task: chip classifier on Polish chips (house_platform / cellar / background).
  Leave-village-out (2 villages) so the number measures *transfer* not
  memorisation.
* Conditions (3):
    1. ``imagenet`` — timm encoder with ImageNet weights, fine-tuned.
    2. ``archaeoscape`` — same encoder initialised from Archaeoscape
       U-Net / segmentation weights, then fine-tuned.
    3. ``scratch`` — random init.
* With real Polish labels + real Archaeoscape weights the ranking
  answers backlog question A2.  Without them (CI) the whole experiment
  runs on synthetic chips and synthetic "pretraining" (a seeded
  perturbation of the random init) so the harness is exercised and all
  numbers are flagged STUB.

No network, no 10 GB download.  Missing torch/timm degrades to a
numpy stub that still writes a valid card.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from lidar_discovery.ml.archaeoscape.dataloader import (
    is_torch_available,
)

ABLATION_DIR = Path("data/models/ablation-pretraining")


@dataclass(frozen=True)
class AblationConfig:
    villages: tuple[str, ...] = ("village-a", "village-b")
    chips_per_village: int = 64
    chip_size: int = 96  # 48 m at 0.5 m — per 09 §2.4
    epochs: int = 2
    batch_size: int = 8
    seed: int = 0
    synthetic: bool = True


# ---------------------------------------------------------------- synthetic Polish chips
def _synthetic_chip(rng: np.random.Generator, label: int, size: int = 96) -> np.ndarray:
    """6×size×size chip.

    label 0 = background (random terrain),
          1 = platform (raised rectangle),
          2 = cellar (pit).
    Scaled with the same fixed scalers as the real stack.
    """
    from scipy import ndimage as _nd

    from lidar_discovery.ml.archaeoscape.dataloader import (
        _derive_channels_synthetic,
        _stack_and_scale,
    )

    raw = rng.standard_normal((size, size)).astype(np.float32)
    dtm = _nd.gaussian_filter(raw, 4) * 0.8 + _nd.gaussian_filter(raw, 1) * 0.2 + raw * 0.04
    if label == 1:
        rh, rw = int(rng.integers(10, 22)), int(rng.integers(12, 26))
        y0, x0 = (size - rh) // 2 + int(rng.integers(-6, 7)), (size - rw) // 2 + int(rng.integers(-6, 7))
        y0, x0 = max(1, y0), max(1, x0)
        dtm[y0 : y0 + rh, x0 : x0 + rw] += float(rng.uniform(0.25, 0.55))
        dtm = _nd.gaussian_filter(dtm, 0.6)
    elif label == 2:
        rh, rw = int(rng.integers(6, 14)), int(rng.integers(6, 14))
        y0, x0 = (size - rh) // 2 + int(rng.integers(-5, 6)), (size - rw) // 2 + int(rng.integers(-5, 6))
        y0, x0 = max(1, y0), max(1, x0)
        dtm[y0 : y0 + rh, x0 : x0 + rw] -= float(rng.uniform(0.35, 0.9))
    channels = _derive_channels_synthetic(dtm, rng)
    return _stack_and_scale(channels)


def _make_synthetic_folds(cfg: AblationConfig) -> dict[str, list[tuple[np.ndarray, int]]]:
    """Return {village: [(chip, label), ...]} synthetic."""
    rng = np.random.default_rng(cfg.seed)
    folds: dict[str, list[tuple[np.ndarray, int]]] = {}
    for v in cfg.villages:
        items: list[tuple[np.ndarray, int]] = []
        n = cfg.chips_per_village
        for _i in range(n):
            r = rng.random()
            label = 0 if r < 0.40 else (1 if r < 0.75 else 2)
            chip = _synthetic_chip(rng, label, size=cfg.chip_size)
            items.append((chip, label))
        folds[v] = items
    return folds


# ---------------------------------------------------------------- tiny classifier (numpy + optional torch)
class _NumpyChipClassifier:
    """Nearest-centroid stub — deterministic, no torch needed."""

    def __init__(self, seed: int = 0) -> None:
        self.centroids: dict[int, np.ndarray] | None = None
        self.seed = seed

    def fit(self, chips: np.ndarray, labels: np.ndarray) -> None:
        # chips N×6×H×W → mean per channel as feature (6-d)
        feats = chips.mean(axis=(2, 3))  # N×6
        cents: dict[int, np.ndarray] = {}
        for c in (0, 1, 2):
            m = feats[labels == c]
            cents[c] = m.mean(axis=0) if len(m) else np.zeros(6, dtype=np.float32)
        # "pretraining" effect: perturb centroids slightly by seed/condition
        self.centroids = cents

    def predict(self, chips: np.ndarray) -> np.ndarray:
        assert self.centroids is not None
        feats = chips.mean(axis=(2, 3))
        # stack centroids 3×6
        C = np.stack([self.centroids[c] for c in (0, 1, 2)], axis=0)
        # L2 to centroids
        dists = ((feats[:, None, :] - C[None, :, :]) ** 2).sum(axis=2)
        return np.argmin(dists, axis=1).astype(np.int64)

    def predict_proba(self, chips: np.ndarray) -> np.ndarray:
        preds = self.predict(chips)
        proba = np.zeros((len(preds), 3), dtype=np.float32)
        proba[np.arange(len(preds)), preds] = 0.85
        proba[proba == 0] = 0.075
        return proba


def _evaluate_fold(
    train_chips: np.ndarray,
    train_labels: np.ndarray,
    test_chips: np.ndarray,
    test_labels: np.ndarray,
    condition: str,
    seed: int,
) -> dict[str, Any]:
    """Train one condition on one leave-village-out fold, return metrics."""
    # condition perturbs the classifier so the three numbers are not identical
    # (still stub — flagged as such)
    perturb = {"scratch": 0.0, "imagenet": 0.04, "archaeoscape": 0.07}.get(condition, 0.0)
    rng = np.random.default_rng(seed + hash(condition) % 10000)
    # apply a tiny additive bias to simulate pretraining benefit
    bias = rng.standard_normal(6).astype(np.float32) * perturb

    if not is_torch_available():
        clf = _NumpyChipClassifier(seed=seed)
        # inject bias into training chips' mean so centroids shift
        tr = train_chips.copy()
        tr[:, 0, :, :] += bias[0] * 0.1
        clf.fit(tr, train_labels)
        preds = clf.predict(test_chips)
        acc = float((preds == test_labels).mean()) if len(test_labels) else 0.0
        # per-class F1
        f1s: dict[str, float] = {}
        for c, name in enumerate(("background", "platform", "cellar")):
            tp = int(((preds == c) & (test_labels == c)).sum())
            fp = int(((preds == c) & (test_labels != c)).sum())
            fn = int(((preds != c) & (test_labels == c)).sum())
            prec = tp / (tp + fp) if (tp + fp) else 0.0
            rec = tp / (tp + fn) if (tp + fn) else 0.0
            f1s[name] = float(2 * prec * rec / (prec + rec)) if (prec + rec) else 0.0
        m_f1 = float(np.mean(list(f1s.values())))
        return {
            "condition": condition,
            "accuracy": acc,
            "per_class_f1": f1s,
            "macro_f1": m_f1,
            "n_train": len(train_labels),
            "n_test": len(test_labels),
            "status": "STUB-numpy",
        }

    # torch path — tiny CNN
    import torch
    from torch import nn

    class ChipNet(nn.Module):  # type: ignore[no-redef]
        def __init__(self) -> None:
            super().__init__()
            self.feat = nn.Sequential(
                nn.Conv2d(6, 16, 3, padding=1),
                nn.ReLU(),
                nn.MaxPool2d(2),
                nn.Conv2d(16, 32, 3, padding=1),
                nn.ReLU(),
                nn.AdaptiveAvgPool2d(1),
            )
            self.head = nn.Linear(32, 3)

        def forward(self, x):  # type: ignore[no-untyped-def]
            f = self.feat(x).flatten(1)
            return self.head(f)

    device = torch.device("cpu")
    model = ChipNet().to(device)
    # simulate pretraining by scaling init
    if condition == "imagenet":
        with torch.no_grad():
            for p in model.feat.parameters():
                p.add_(torch.randn_like(p) * 0.02)
    elif condition == "archaeoscape":
        with torch.no_grad():
            for p in model.feat.parameters():
                p.add_(torch.randn_like(p) * 0.01)
            for p in model.head.parameters():
                p.mul_(1.05)

    opt = torch.optim.Adam(model.parameters(), lr=2e-3)
    loss_fn = nn.CrossEntropyLoss()
    # build loaders as tensors
    tr_t = torch.from_numpy(train_chips).float()
    tr_l = torch.from_numpy(train_labels).long()
    te_t = torch.from_numpy(test_chips).float()
    model.train()
    for _ in range(2):  # 2 epochs is enough for the stub
        perm = torch.randperm(len(tr_t))
        for i in range(0, len(tr_t), 8):
            idx = perm[i : i + 8]
            opt.zero_grad()
            logits = model(tr_t[idx].to(device))
            loss = loss_fn(logits, tr_l[idx].to(device))
            loss.backward()
            opt.step()
    model.eval()
    with torch.no_grad():
        logits = model(te_t.to(device))
        preds = logits.argmax(dim=1).cpu().numpy()
    acc = float((preds == test_labels).mean()) if len(test_labels) else 0.0
    f1s: dict[str, float] = {}
    for c, name in enumerate(("background", "platform", "cellar")):
        tp = int(((preds == c) & (test_labels == c)).sum())
        fp = int(((preds == c) & (test_labels != c)).sum())
        fn = int(((preds != c) & (test_labels == c)).sum())
        prec = tp / (tp + fp) if (tp + fp) else 0.0
        rec = tp / (tp + fn) if (tp + fn) else 0.0
        f1s[name] = float(2 * prec * rec / (prec + rec)) if (prec + rec) else 0.0
    return {
        "condition": condition,
        "accuracy": acc,
        "per_class_f1": f1s,
        "macro_f1": float(np.mean(list(f1s.values()))),
        "n_train": len(train_labels),
        "n_test": len(test_labels),
        "status": "STUB-torch" if True else "measured",
    }


def ablation_pretraining(
    data_dir: str | Path | None = None,
    out_dir: str | Path | None = None,
    config: AblationConfig | None = None,
) -> dict[str, Any]:
    """Compare ImageNet vs Archaeoscape pretraining vs scratch.

    Leave-village-out on Polish chips (synthetic if no real labels).
    Writes ``<out_dir>/metrics.json`` + ``card.md`` and returns the dict.

    Never downloads, never requires torch (degrades to numpy stub).
    """
    cfg = config or AblationConfig()
    # if a real Polish chip dataset existed we would load it here;
    # for now we always use synthetic and flag it
    _ = data_dir  # reserved for future real-data loader
    use_synthetic = True
    out = Path(out_dir) if out_dir is not None else ABLATION_DIR
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.perf_counter()

    # build folds
    folds = _make_synthetic_folds(cfg)
    villages = list(folds.keys())
    conditions = ("scratch", "imagenet", "archaeoscape")

    # leave-village-out: each village is test once
    fold_results: list[dict[str, Any]] = []
    summary: dict[str, list[float]] = {c: [] for c in conditions}

    for test_village in villages:
        train_items: list[tuple[np.ndarray, int]] = []
        for v, items in folds.items():
            if v != test_village:
                train_items.extend(items)
        test_items = folds[test_village]
        tr_chips = np.stack([c for c, _ in train_items], axis=0) if train_items else np.zeros((0, 6, cfg.chip_size, cfg.chip_size), dtype=np.float32)
        tr_labels = np.array([lbl for _, lbl in train_items], dtype=np.int64)
        te_chips = np.stack([c for c, _ in test_items], axis=0)
        te_labels = np.array([lbl for _, lbl in test_items], dtype=np.int64)
        for cond in conditions:
            res = _evaluate_fold(tr_chips, tr_labels, te_chips, te_labels, condition=cond, seed=cfg.seed)
            res["fold"] = {"train_villages": [v for v in villages if v != test_village], "test_village": test_village}
            fold_results.append(res)
            summary[cond].append(float(res["macro_f1"]))

    # aggregate
    agg: dict[str, dict[str, float]] = {}
    for cond in conditions:
        vals = summary[cond]
        agg[cond] = {
            "mean_macro_f1": float(np.mean(vals)) if vals else 0.0,
            "std_macro_f1": float(np.std(vals)) if vals else 0.0,
            "folds": vals,
        }

    result: dict[str, Any] = {
        "experiment": "ablation_pretraining — ImageNet vs Archaeoscape vs scratch (chip classifier, leave-village-out)",
        "config": {
            "villages": list(cfg.villages),
            "chips_per_village": cfg.chips_per_village,
            "chip_size": cfg.chip_size,
            "epochs": cfg.epochs,
            "seed": cfg.seed,
            "synthetic": use_synthetic,
        },
        "folds": fold_results,
        "aggregate": agg,
        "elapsed_s": time.perf_counter() - t0,
        "stub_warning": "STUB — synthetic Polish chips; ranking is harness-only, not evidence for transfer." if use_synthetic else None,
        "interpretation": (
            "On synthetic data the ranking is meaningless (all conditions see the same synthetic distribution). "
            "With real labels, expect Archaeoscape ≥ ImageNet > scratch if mound texture transfers; "
            "otherwise all three collapse (domain gap — Cambodia temples 8-12 m vs Bieszczady 0.2-0.4 m)."
        ),
        "next_step": "Re-run with real chips once K4 labels exist; keep ImageNet vs Archaeoscape as the registered ablation (09 §5.1).",
    }

    (out / "metrics.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    # card.md
    lines = [
        "# Ablation — pretraining for chip classifier",
        "",
        f"Leave-village-out on {len(villages)} villages × {cfg.chips_per_village} chips (synthetic={use_synthetic}).",
        "",
        "| condition | mean macro-F1 | fold F1s |",
        "|---|---|---|",
    ]
    for cond in conditions:
        a = agg[cond]
        lines.append(f"| {cond} | {a['mean_macro_f1']:.3f} ± {a['std_macro_f1']:.3f} | {', '.join(f'{v:.3f}' for v in a['folds'])} |")
    if use_synthetic:
        lines += ["", "> STUB — synthetic chips; do not quote as transfer evidence."]
    lines += ["", result["interpretation"]]
    (out / "card.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":  # pragma: no cover
    import argparse

    p = argparse.ArgumentParser(description="Ablation: ImageNet vs Archaeoscape vs scratch.")
    p.add_argument("--data-dir", default=None)
    p.add_argument("--out-dir", default=str(ABLATION_DIR))
    args = p.parse_args()
    res = ablation_pretraining(data_dir=args.data_dir, out_dir=args.out_dir)
    print(json.dumps(res, indent=2))
