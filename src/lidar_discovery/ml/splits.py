"""Village folds + buffers + lockbox registry (09 §5.1)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

LOCKBOX_VERSION = 1


def leave_village_out_folds(
    village_ids: list[str], buffer_m: float = 250
) -> list[dict[str, Any]]:
    """One fold per village: {held_out: id, train: [..]}."""
    return [{"held_out": v, "train": [x for x in village_ids if x != v]} for v in village_ids]


def lockbox_registry(
    village_ids: list[str], lockbox_ids: list[str], path: Path | None = None
) -> dict[str, Any]:
    """Create or validate lockbox assignment. Refuses to mutate once labels exist."""
    for lid in lockbox_ids:
        if lid not in village_ids:
            raise ValueError(f"lockbox {lid!r} not in village_ids {village_ids}")
    reg: dict[str, Any] = {
        "version": LOCKBOX_VERSION,
        "villages": village_ids,
        "lockbox": sorted(lockbox_ids),
        "train": sorted(set(village_ids) - set(lockbox_ids)),
    }
    reg["hash"] = hashlib.sha256(json.dumps(reg, sort_keys=True).encode()).hexdigest()[:16]
    if path is not None:
        if path.exists():
            existing = json.loads(path.read_text())
            if existing.get("lockbox") != reg["lockbox"]:
                raise ValueError(
                    f"lockbox mismatch: existing {existing.get('lockbox')} vs new {reg['lockbox']}; "
                    "refusing to change a lockbox once assigned"
                )
        path.write_text(json.dumps(reg, indent=2))
    return reg
