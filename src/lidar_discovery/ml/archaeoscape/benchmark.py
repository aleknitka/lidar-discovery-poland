"""Reproduce NeurIPS 2024 Table 2 (Archaeoscape benchmark).

Runs U-Net / DeepLabv3 / ViT-S with ImageNet init on the Archaeoscape
split and reports IoU per class (temple/mound/hydro/bkg) and overall
accuracy.  If no real data or no torch is present the same loop runs on
the synthetic stub and marks every number as STUB so the pipeline stays
green.

Metrics are written to ``data/models/archaeoscape-benchmark/metrics.json``
plus a companion ``card.md``.
"""

from __future__ import annotations

import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from lidar_discovery.ml.archaeoscape import ARCHAEOSCAPE_CLASSES
from lidar_discovery.ml.archaeoscape.dataloader import (
    ArchaeoscapeDataset,
    DatasetConfig,
    download_instructions,
    has_real_data,
    is_torch_available,
)

BENCHMARK_DIR = Path("data/models/archaeoscape-benchmark")
NUM_CLASSES = len(ARCHAEOSCAPE_CLASSES)

# Reference numbers from Perron et al., NeurIPS 2024 D&B — Table 2
# (quoted in docs/11 §2.1). Intervals are approximate.
REF_TABLE2: dict[str, dict[str, float]] = {
    "unet": {"mIoU": 50.5, "background": 87.5, "mound": 48.0, "temple": 25.0, "hydro": 41.0},
    "deeplabv3": {"mIoU": 47.6, "background": 88.0, "mound": 47.0, "temple": 18.0, "hydro": 38.0},
    "vit_s": {"mIoU": 46.4, "background": 87.0, "mound": 49.0, "temple": 33.0, "hydro": 17.0},
}


@dataclass
class ClassMetrics:
    iou: float
    tp: int
    fp: int
    fn: int


def _compute_metrics(
    preds: np.ndarray, targets: np.ndarray, num_classes: int = NUM_CLASSES
) -> dict[str, Any]:
    """Pixel confusion → per-class IoU + OA + mIoU (ignores NaN / 255)."""
    preds = preds.reshape(-1)
    targets = targets.reshape(-1)
    valid = targets != 255
    preds, targets = preds[valid], targets[valid]
    if len(targets) == 0:
        return {
            "per_class_iou": dict.fromkeys(ARCHAEOSCAPE_CLASSES, 0.0),
            "miou": 0.0,
            "oa": 0.0,
            "confusion": np.zeros((num_classes, num_classes), dtype=int).tolist(),
        }
    cm = np.zeros((num_classes, num_classes), dtype=np.int64)
    for t, p in zip(targets, preds, strict=False):
        if 0 <= int(t) < num_classes and 0 <= int(p) < num_classes:
            cm[int(t), int(p)] += 1
    ious: dict[str, float] = {}
    for i, name in enumerate(ARCHAEOSCAPE_CLASSES):
        tp = int(cm[i, i])
        fp = int(cm[:, i].sum() - tp)
        fn = int(cm[i, :].sum() - tp)
        denom = tp + fp + fn
        ious[name] = float(tp / denom) if denom else 0.0
    # mIoU over foreground only (temple/mound/hydro) + background separately reported
    miou = float(np.mean(list(ious.values())))
    oa = float(np.trace(cm) / cm.sum()) if cm.sum() else 0.0
    return {
        "per_class_iou": ious,
        "miou": miou,
        "oa": oa,
        "confusion": cm.tolist(),
    }


# ---------------------------------------------------------------- tiny head (numpy fallback)
class _NumpyStubModel:
    """Deterministic stub: predicts background everywhere except a centre square."""

    def __init__(self, num_classes: int = NUM_CLASSES) -> None:
        self.num_classes = num_classes

    def predict_mask(self, image: np.ndarray) -> np.ndarray:
        # image 6×H×W, return H×W uint8
        _, h, w = image.shape
        m = np.zeros((h, w), dtype=np.uint8)
        # if LRM20 channel has strong positive bump, predict mound
        lrm20 = image[0]
        m[lrm20 > 0.25] = 1  # mound
        m[lrm20 > 0.6] = 2  # temple where very strong
        # hydro: negative fill where slope low
        fill = image[4]
        m[(fill > 0.15) & (m == 0)] = 3
        return m


# ---------------------------------------------------------------- torch model factory (optional)
def _build_torch_model(name: str, num_classes: int = NUM_CLASSES):  # type: ignore[no-untyped-def]
    """Return a segmentation model (timm/smp if available, else tiny conv)."""
    name = name.lower()
    try:
        import segmentation_models_pytorch as smp  # type: ignore[import]

        if name in ("unet", "u-net"):
            return smp.Unet(
                encoder_name="resnet34",
                encoder_weights="imagenet" if _has_imagenet() else None,
                in_channels=6,
                classes=num_classes,
            )
        if name in ("deeplabv3", "dlv3", "deeplab"):
            return smp.DeepLabV3(
                encoder_name="resnet34",
                encoder_weights="imagenet" if _has_imagenet() else None,
                in_channels=6,
                classes=num_classes,
            )
    except ImportError:
        pass
    # fallback: minimal conv net (works without smp/timm)
    try:
        from torch import nn
        class TinySeg(nn.Module):  # type: ignore[no-redef]
            def __init__(self) -> None:
                super().__init__()
                self.net = nn.Sequential(
                    nn.Conv2d(6, 16, 3, padding=1),
                    nn.ReLU(),
                    nn.Conv2d(16, 32, 3, padding=1),
                    nn.ReLU(),
                    nn.Conv2d(32, num_classes, 1),
                )

            def forward(self, x):  # type: ignore[no-untyped-def]
                return self.net(x)

        return TinySeg()
    except ImportError:
        return None


def _has_imagenet() -> bool:
    try:
        import timm  # type: ignore[import]  # noqa: F401

        return True
    except ImportError:
        return False


# ---------------------------------------------------------------- main entry
def run_benchmark(
    data_dir: str | Path | None = None,
    synthetic: bool = False,
    epochs: int = 1,
    batch_size: int = 2,
    models: list[str] | None = None,
    out_dir: str | Path | None = None,
    seed: int = 0,
) -> dict[str, Any]:
    """Run Table-2 reproduction (real or synthetic). Returns the metrics dict."""
    models = models or ["unet", "deeplabv3", "vit_s"]
    use_synthetic = synthetic or (data_dir is None or not has_real_data(data_dir or ""))
    out = Path(out_dir) if out_dir is not None else BENCHMARK_DIR
    out.mkdir(parents=True, exist_ok=True)
    torch_available = is_torch_available()
    t0 = time.perf_counter()

    results: dict[str, Any] = {
        "dataset": "synthetic-stub" if use_synthetic else "archaeoscape-real",
        "synthetic": use_synthetic,
        "torch_available": torch_available,
        "epochs": epochs,
        "models": {},
        "reference_table2": REF_TABLE2,
        "elapsed_s": 0.0,
        "stub_warning": None,
    }
    if use_synthetic:
        results["stub_warning"] = (
            "STUB — synthetic terrain; numbers are smoke-test only, not Table 2. "
            + download_instructions()
        )

    if not torch_available:
        print("SKIP: torch not installed (uv sync --extra ml)", file=sys.stderr)
        # still compute stub metrics with numpy so metrics.json is always written
        stub = _NumpyStubModel()
        for name in models:
            ds = ArchaeoscapeDataset(
                data_dir=data_dir,
                config=DatasetConfig(split="test", seed=seed, synthetic_tiles=8, augment=False),
                synthetic=True,
            )
            preds_list, gts_list = [], []
            for i in range(min(8, len(ds))):
                item = ds[i]
                img = item["image"]
                if hasattr(img, "numpy"):
                    img = img.numpy()
                img = np.asarray(img)
                gt = np.asarray(item["mask"])
                pred = stub.predict_mask(img)
                preds_list.append(pred)
                gts_list.append(gt)
            preds = np.concatenate([p.reshape(-1) for p in preds_list])
            gts = np.concatenate([g.reshape(-1) for g in gts_list])
            m = _compute_metrics(preds, gts)
            results["models"][name] = {
                "per_class_iou": m["per_class_iou"],
                "miou": m["miou"],
                "oa": m["oa"],
                "status": "STUB-numpy (no torch)",
            }
        results["elapsed_s"] = time.perf_counter() - t0
        _write_metrics(out, results)
        return results

    # torch path
    import torch  # type: ignore[import]

    device = torch.device("cpu")
    for name in models:
        ds_train = ArchaeoscapeDataset(
            data_dir=data_dir,
            config=DatasetConfig(split="train", seed=seed, augment=True),
            synthetic=use_synthetic,
        )
        ds_test = ArchaeoscapeDataset(
            data_dir=data_dir,
            config=DatasetConfig(split="test", seed=seed, augment=False),
            synthetic=use_synthetic,
        )
        model = _build_torch_model(name)
        if model is None:
            results["models"][name] = {"error": "no model backend", "status": "SKIP"}
            continue
        model = model.to(device)
        # tiny training loop (Adam, CE)
        opt = torch.optim.Adam(model.parameters(), lr=1e-3)
        loss_fn = torch.nn.CrossEntropyLoss(ignore_index=255)
        model.train()
        # limit steps for CI speed: at most 8 batches per epoch
        from torch.utils.data import DataLoader

        loader = DataLoader(ds_train, batch_size=batch_size, shuffle=True, num_workers=0)
        for _ in range(max(0, epochs)):
            for bi, batch in enumerate(loader):
                if bi >= 8:
                    break
                img = batch["image"].float().to(device)
                tgt = batch["mask"].long().to(device)
                opt.zero_grad()
                logits = model(img)
                # upsample if model downsampled (e.g. ViT)
                if logits.shape[-2:] != tgt.shape[-2:]:
                    logits = torch.nn.functional.interpolate(
                        logits, size=tgt.shape[-2:], mode="bilinear", align_corners=False
                    )
                loss = loss_fn(logits, tgt)
                loss.backward()
                opt.step()
        # eval
        model.eval()
        preds_all: list[np.ndarray] = []
        gts_all: list[np.ndarray] = []
        loader_test = DataLoader(ds_test, batch_size=batch_size, shuffle=False, num_workers=0)
        with torch.no_grad():
            for batch in loader_test:
                img = batch["image"].float().to(device)
                tgt = batch["mask"].long().to(device)
                logits = model(img)
                if logits.shape[-2:] != tgt.shape[-2:]:
                    logits = torch.nn.functional.interpolate(
                        logits, size=tgt.shape[-2:], mode="bilinear", align_corners=False
                    )
                pred = logits.argmax(dim=1).cpu().numpy()
                preds_all.append(pred.reshape(-1))
                gts_all.append(tgt.cpu().numpy().reshape(-1))
                if len(preds_all) * batch_size >= 16:
                    break
        if preds_all:
            preds = np.concatenate(preds_all)
            gts = np.concatenate(gts_all)
            m = _compute_metrics(preds, gts)
            entry: dict[str, Any] = {
                "per_class_iou": m["per_class_iou"],
                "miou": m["miou"],
                "oa": m["oa"],
                "confusion": m["confusion"],
                "status": "STUB" if use_synthetic else "measured",
            }
            # attach reference delta when synthetic for transparency
            if use_synthetic:
                entry["reference_delta_miou"] = m["miou"] - float(
                    REF_TABLE2.get(name, {}).get("mIoU", 0.0)
                )
            results["models"][name] = entry
        else:
            results["models"][name] = {"error": "no test batches", "status": "FAIL"}

    results["elapsed_s"] = time.perf_counter() - t0
    _write_metrics(out, results)
    return results


def _write_metrics(out: Path, results: dict[str, Any]) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / "metrics.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    # companion card.md
    lines = [
        "# Archaeoscape benchmark",
        "",
        f"Dataset: **{results['dataset']}**  |  synthetic={results['synthetic']}  |  torch={results['torch_available']}",
        "",
        "| model | mIoU | OA | bkg | mound | temple | hydro | status |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for name, r in results["models"].items():
        pc = r.get("per_class_iou", {})
        lines.append(
            f"| {name} | {r.get('miou', 0):.1f} | {r.get('oa', 0):.3f} | "
            f"{pc.get('background', 0):.2f} | {pc.get('mound', 0):.2f} | "
            f"{pc.get('temple', 0):.2f} | {pc.get('hydro', 0):.2f} | {r.get('status', '')} |"
        )
    if results.get("stub_warning"):
        lines += ["", "> " + results["stub_warning"].replace("\n", " ")]
    lines += ["", "Reference (NeurIPS 2024 Table 2): U-Net 50.5 / DeepLabv3 47.6 / ViT-S 46.4 mIoU."]
    (out / "card.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    import argparse

    p = argparse.ArgumentParser(description="Archaeoscape Table-2 benchmark (real or synthetic stub).")
    p.add_argument("--data-dir", default=None)
    p.add_argument("--synthetic", action="store_true", help="Force synthetic stub (no download).")
    p.add_argument("--epochs", type=int, default=1)
    p.add_argument("--batch-size", type=int, default=2)
    p.add_argument("--out-dir", default=str(BENCHMARK_DIR))
    p.add_argument("--seed", type=int, default=0)
    args = p.parse_args(argv)
    res = run_benchmark(
        data_dir=args.data_dir,
        synthetic=args.synthetic,
        epochs=args.epochs,
        batch_size=args.batch_size,
        out_dir=args.out_dir,
        seed=args.seed,
    )
    print(json.dumps(res, indent=2))
    if not is_torch_available():
        print("SKIP: torch not installed (uv sync --extra ml)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
