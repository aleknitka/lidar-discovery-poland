"""Model registry + model cards (09 §7.4, 11 §9)."""

from __future__ import annotations

import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from lidar_discovery.processing.pipeline import PIPELINE_VERSION, code_version


def git_sha() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
            cwd=Path(__file__).parent,
        ).stdout.strip()
    except Exception:
        return ""


def new_model_version(stage: str) -> str:
    sha = git_sha()[:7] or "nogit"
    ts = datetime.now(UTC).strftime("%Y%m%d")
    return f"{stage}-{ts}-{sha}"


def write_card(
    out_dir: Path,
    model_version: str,
    stage: str,
    metrics: dict[str, Any],
    label_hash: str,
    extra: dict[str, Any] | None = None,
) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    card = {
        "model_version": model_version,
        "stage": stage,
        "created_at": datetime.now(UTC).isoformat(),
        "code_version": code_version(),
        "pipeline_version": PIPELINE_VERSION,
        "git_sha": git_sha(),
        "label_snapshot": label_hash,
        "metrics": metrics,
        **(extra or {}),
    }
    (out_dir / "card.json").write_text(json.dumps(card, indent=2))
    md = [
        f"# Model card — {model_version}",
        "",
        f"- Stage: {stage}",
        f"- Created: {card['created_at']}",
        f"- Code: {card['code_version']}",
        f"- Pipeline: {PIPELINE_VERSION}",
        f"- Label snapshot: `{label_hash}`",
        "",
        "## Intended use",
        "Ranking for human review; not a detector; not for dating or novelty claims.",
        "",
        "## Metrics",
        "```json",
        json.dumps(metrics, indent=2),
        "```",
    ]
    if extra:
        md += ["", "## Extra", "```json", json.dumps(extra, indent=2), "```"]
    (out_dir / "card.md").write_text("\n".join(md))
    return out_dir / "card.json"


def list_models(models_root: Path = Path("data/models")) -> list[str]:
    if not models_root.exists():
        return []
    return sorted(p.name for p in models_root.iterdir() if p.is_dir())


def render_card(settings=None, version: str | None = None, *args, **kwargs) -> dict:
    """Render model card — alias for CLI ``ldp ml card <version>``.

    Accepts ``render_card(settings, version)`` or ``render_card(version)``.
    """
    # sniff args: render_card(version) was called with version as first positional
    if version is None and settings is not None and isinstance(settings, str):
        version = settings
        settings = None
    if version is None and args:
        version = str(args[0])
    if version is None:
        raise ValueError("render_card requires a version")
    from pathlib import Path as _P
    # resolve settings for path
    cfg = settings
    if cfg is None or isinstance(cfg, str):
        try:
            from lidar_discovery.config import get_settings as _gs
            cfg = _gs()
        except Exception:
            cfg = None
    roots = []
    if cfg is not None:
        try: roots.append(_P(cfg.data_dir) / "models" / version)
        except Exception: pass
    roots.append(_P("data") / "models" / version)
    for root in roots:
        cj = root / "card.json"
        md = root / "card.md"
        if cj.exists():
            try:
                data = __import__("json").loads(cj.read_text())
                # include markdown if present
                if md.exists():
                    data["_card_md_path"] = str(md)
                return data
            except Exception:
                return {"version": version, "card_json": str(cj), "error": "failed to read card.json"}
        if md.exists():
            return {"version": version, "card_md": md.read_text()[:4000], "card_path": str(md)}
    return {"version": version, "error": "model card not found", "searched": [str(r) for r in roots]}
