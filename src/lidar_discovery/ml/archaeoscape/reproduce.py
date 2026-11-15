"""One-command reproduction: dataloader + short training + zero-shot → card.md.

Usage::

    uv run python -m lidar_discovery.ml.archaeoscape.reproduce --synthetic --epochs 1
    uv run python -m lidar_discovery.ml.archaeoscape.reproduce --data-dir data/archaeoscape --epochs 10
    uv run python -m lidar_discovery.ml.archaeoscape.reproduce --data-dir data/archaeoscape --synthetic --epochs 2

Always succeeds without torch (numpy fallback) and without network.
Real data is used only when ``--data-dir`` points at an unpacked
Archaeoscape archive (see download_instructions()).
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from lidar_discovery.ml.archaeoscape.benchmark import run_benchmark
from lidar_discovery.ml.archaeoscape.dataloader import (
    ArchaeoscapeDataset,
    DatasetConfig,
    download_instructions,
    has_real_data,
    is_torch_available,
)
from lidar_discovery.ml.archaeoscape.zeroshot import run_zeroshot_pilots
from lidar_discovery.ml.transfer import AblationConfig, ablation_pretraining


def _run_dataloader_smoke(data_dir: str | Path | None, synthetic: bool, seed: int = 0) -> dict:
    cfgs = [
        DatasetConfig(split="train", seed=seed, synthetic_tiles=16, augment=True),
        DatasetConfig(split="test", seed=seed, synthetic_tiles=8, augment=False),
    ]
    infos: list[dict] = []
    for cfg in cfgs:
        ds = ArchaeoscapeDataset(data_dir=data_dir, config=cfg, synthetic=synthetic)
        batch = ds.numpy_batch(indices=list(range(min(2, len(ds)))))
        infos.append(
            {
                "split": cfg.split,
                "len": len(ds),
                "image_shape": list(batch["image"].shape),
                "mask_shape": list(batch["mask"].shape),
                "classes_present": sorted(int(x) for x in set(batch["mask"].reshape(-1).tolist())),
                "channels": list(ds.info()["channels"]),
            }
        )
    return {"dataloader": infos}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Reproduce Archaeoscape spike (synthetic by default).")
    p.add_argument("--data-dir", default=None, help="Unpacked Archaeoscape root (dtm.tif per AOI).")
    p.add_argument("--synthetic", action="store_true", help="Force synthetic stub (no download).")
    p.add_argument("--epochs", type=int, default=2, help="Training epochs for the benchmark stub.")
    p.add_argument("--batch-size", type=int, default=2)
    p.add_argument("--out-dir", default="data/models/archaeoscape-reproduce", help="Where to write card.md/metrics.json.")
    p.add_argument("--seed", type=int, default=0)
    args = p.parse_args(argv)

    synthetic = args.synthetic or (args.data_dir is None or not has_real_data(args.data_dir or ""))
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.perf_counter()

    print(f"[reproduce] synthetic={synthetic}  data_dir={args.data_dir}  epochs={args.epochs}", file=sys.stderr)
    if synthetic:
        print("[reproduce] Using synthetic stub — no network.", file=sys.stderr)
    if not is_torch_available():
        print("SKIP: torch not installed (uv sync --extra ml) — running numpy fallback.", file=sys.stderr)

    results: dict = {
        "synthetic": synthetic,
        "data_dir": args.data_dir,
        "epochs": args.epochs,
        "torch_available": is_torch_available(),
        "steps": {},
    }

    # 1 — dataloader smoke
    try:
        results["steps"]["dataloader"] = _run_dataloader_smoke(args.data_dir, synthetic, seed=args.seed)
        print("[reproduce] dataloader OK", file=sys.stderr)
    except Exception as e:
        results["steps"]["dataloader"] = {"error": str(e)}
        print(f"[reproduce] dataloader failed: {e}", file=sys.stderr)

    # 2 — benchmark (Table 2, short run)
    try:
        bench = run_benchmark(
            data_dir=args.data_dir,
            synthetic=synthetic,
            epochs=args.epochs,
            batch_size=args.batch_size,
            out_dir=str(out / "benchmark"),
            seed=args.seed,
        )
        results["steps"]["benchmark"] = {k: bench.get(k) for k in ("dataset", "synthetic", "models", "elapsed_s")}
        print("[reproduce] benchmark OK", file=sys.stderr)
    except Exception as e:
        results["steps"]["benchmark"] = {"error": str(e)}
        print(f"[reproduce] benchmark failed: {e}", file=sys.stderr)

    # 3 — zero-shot pilots
    try:
        zs = run_zeroshot_pilots(out_dir=str(out / "zeroshot"))
        results["steps"]["zeroshot"] = {"tiles": zs.get("tiles"), "is_stub": zs.get("is_stub")}
        print("[reproduce] zeroshot OK", file=sys.stderr)
    except Exception as e:
        results["steps"]["zeroshot"] = {"error": str(e)}
        print(f"[reproduce] zeroshot failed: {e}", file=sys.stderr)

    # 4 — ablation
    try:
        abl = ablation_pretraining(out_dir=str(out / "ablation"), config=AblationConfig(synthetic=synthetic, seed=args.seed))
        results["steps"]["ablation"] = {"aggregate": abl.get("aggregate")}
        print("[reproduce] ablation OK", file=sys.stderr)
    except Exception as e:
        results["steps"]["ablation"] = {"error": str(e)}
        print(f"[reproduce] ablation failed: {e}", file=sys.stderr)

    results["elapsed_s"] = time.perf_counter() - t0
    results["instructions_real_data"] = download_instructions() if synthetic else "Real data was used."

    # write metrics
    (out / "metrics.json").write_text(json.dumps(results, indent=2), encoding="utf-8")

    # write card.md (the artefact the task requires)
    torch_note = "torch available" if is_torch_available() else "torch NOT installed — numpy fallback (uv sync --extra ml)"
    lines = [
        "# Archaeoscape reproduce — card",
        "",
        f"Mode: **{'synthetic STUB' if synthetic else 'real data'}** | {torch_note} | epochs={args.epochs}",
        f"Elapsed: {results['elapsed_s']:.1f}s",
        "",
        "## 1. Dataloader",
        "",
    ]
    dl = results["steps"].get("dataloader", {})
    if isinstance(dl, dict) and "dataloader" in dl:
        for info in dl["dataloader"]:
            lines.append(f"- split={info['split']} len={info['len']} image={info['image_shape']} mask={info['mask_shape']} classes={info['classes_present']}")
    else:
        lines.append(f"- error: {dl}")

    lines += ["", "## 2. Benchmark (NeurIPS 2024 Table 2, stub)"]
    bench = results["steps"].get("benchmark", {})
    if "models" in bench:
        for name, m in bench["models"].items():
            pc = m.get("per_class_iou", {})
            lines.append(
                f"- {name}: mIoU={m.get('miou', 0):.2f} OA={m.get('oa', 0):.3f} "
                f"bkg={pc.get('background', 0):.2f} mound={pc.get('mound', 0):.2f} "
                f"temple={pc.get('temple', 0):.2f} hydro={pc.get('hydro', 0):.2f} [{m.get('status', '')}]"
            )
        lines.append("")
        lines.append("> STUB numbers are smoke-test only; reference U-Net 50.5 / DeepLabv3 47.6 / ViT-S 46.4 mIoU.")
    else:
        lines.append(f"- error: {bench}")

    lines += ["", "## 3. Zero-shot on Bieszczady pilots (stub)"]
    zs = results["steps"].get("zeroshot", {})
    if "tiles" in zs:
        for t in zs["tiles"]:
            lines.append(f"- tile {t['tile']}: {t['candidates']} cands ({t['candidates_per_km2']:.1f}/km²) mean_anom={t['mean_anomaly']:.3f} p95={t['p95_anomaly']:.3f}")
        lines.append("")
        lines.append("> No labels — visual inspection required. STUB.")
    else:
        lines.append(f"- error: {zs}")

    lines += ["", "## 4. Ablation — ImageNet vs Archaeoscape vs scratch"]
    abl = results["steps"].get("ablation", {})
    if "aggregate" in abl:
        for cond, ag in abl["aggregate"].items():
            lines.append(f"- {cond}: mean macro-F1={ag['mean_macro_f1']:.3f} ± {ag['std_macro_f1']:.3f}")
        lines.append("")
        lines.append("> Synthetic chips — ranking is harness-only.")
    else:
        lines.append(f"- error: {abl}")

    lines += [
        "",
        "## 5. Real-data instructions",
        "",
        "```",
        download_instructions(),
        "```",
        "",
        f"Outputs: `{out}/metrics.json`, `{out}/benchmark/metrics.json`, `{out}/zeroshot/metrics.json`, `{out}/ablation/metrics.json`",
        "",
        "See also: `docs/research/archaeoscape-spike.md` and `docs/11 §12` backlog items 1-2.",
    ]
    (out / "card.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[reproduce] wrote {out / 'card.md'} and {out / 'metrics.json'}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
