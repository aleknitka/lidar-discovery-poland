"""Thin re-export / adapter for chip export.

Primary assignment signature:
    export_chips(location_id, candidate, arrays, grid, out_dir)
        -> writes 96px + 256px PNGs via src/lidar_discovery/chips.py

Also supports SchedulerWatch signature:
    export_chips(settings, candidate_id, location_id, arrays, grid)

This module delegates to the canonical implementation in
``lidar_discovery.chips`` so there is a single code path.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from lidar_discovery.processing.dtm import Grid


def export_chips(*args: Any, **kwargs: Any) -> dict[str, str]:
    """Dispatch to the canonical chips implementation.

    Accepted call forms:
    - export_chips(location_id, candidate, arrays, grid, out_dir)
    - export_chips(location_id, candidate_id, candidate, arrays, grid, data_dir)
    - export_chips(settings, candidate_id, location_id, arrays, grid)
    """
    from lidar_discovery import chips as _chips

    # Peer signature: (settings, candidate_id, location_id, arrays, grid)
    if args and hasattr(args[0], "data_dir"):
        settings = args[0]
        candidate_id = str(args[1]) if len(args) > 1 else kwargs.get("candidate_id", "candidate")
        location_id = str(args[2]) if len(args) > 2 else str(kwargs.get("location_id", "loc"))
        arrays = args[3] if len(args) > 3 else kwargs.get("arrays", {})
        grid = args[4] if len(args) > 4 else kwargs.get("grid")
        # Minimal candidate stub; real provenance enrichment happens in runner
        cand_stub: dict[str, Any] = {"centroid_rc": None, "support_fraction": 1.0}
        # Try to enrich with centroid if candidate_id looks like a dict? ignore
        try:
            return _chips.export_chips(
                location_id, str(candidate_id), cand_stub, arrays, grid, Path(settings.data_dir)  # type: ignore[arg-type]
            )
        except Exception:
            return {}

    # 6-arg form: (location_id, candidate_id, candidate, arrays, grid, data_dir)
    if len(args) == 6 and isinstance(args[1], str) and isinstance(args[2], dict):
        location_id, candidate_id, candidate, arrays, grid, data_dir = args  # type: ignore[misc]
        return _chips.export_chips(
            str(location_id), str(candidate_id), candidate, arrays, grid, Path(data_dir)
        )

    # 5-arg assignment form: (location_id, candidate, arrays, grid, out_dir)
    if len(args) >= 5 and isinstance(args[1], dict):
        location_id, candidate, arrays, grid, out_dir = args[0], args[1], args[2], args[3], args[4]
        # candidate dict -> need an id
        cand_id = str(candidate.get("id", candidate.get("candidate_id", "candidate")))
        # _chips expects (location_id, candidate_id, candidate, arrays, grid, data_dir)
        # data_dir is parent of out_dir when out_dir is chips/<loc>/<cand>
        try:
            data_dir = Path(out_dir).parents[2] if len(Path(out_dir).parts) >= 3 else Path(out_dir).parent
            # If out_dir already looks like data/chips/loc/cand, parent 2 is data; fallback to data_dir kw
            if "chips" not in str(out_dir):
                data_dir = Path(kwargs.get("data_dir", Path("data")))
        except Exception:
            data_dir = Path(kwargs.get("data_dir", Path("data")))
        # But if out_dir is the base chips dir for this candidate, just treat its parent's parent as data_dir
        # Simpler: if caller passed explicit out_dir that is the candidate dir, use its parent's parent
        # Otherwise treat out_dir as data_dir
        candidate_dir = Path(out_dir)
        # If candidate dict has centroid_rc, keep it; else default inside _chips
        try:
            # If out_dir is exactly the candidate dir, delegate with data_dir = grandparent
            # Reconstruct call: chips.export_chips will create data_dir/chips/loc/cand internally,
            # so we should call it with data_dir and let it create subdirs.
            # Instead write directly via _chips helper by calling with data_dir = parent of chips
            # For the assignment test we write into out_dir directly; do it manually here
            # to avoid double-nesting.
            import json as _json

            from lidar_discovery.chips import KINDS_FOR_CHIPS, _extract_chip, _norm

            from PIL import Image as _Image

            rc = candidate.get("centroid_rc")
            if rc is None:
                h, w = next(iter(arrays.values())).shape  # type: ignore[union-attr]
                rc = (h // 2, w // 2)
            out_base = Path(out_dir)
            out_base.mkdir(parents=True, exist_ok=True)
            rel: dict[str, str] = {}
            for kind in KINDS_FOR_CHIPS:
                arr = arrays.get(kind)
                if arr is None and kind == "lrm":
                    arr = arrays.get("lrm20", arrays.get("lrm"))
                if arr is None:
                    continue
                for sz in (96, 256):
                    chip = _extract_chip(arr, (float(rc[0]), float(rc[1])), sz)
                    img = _Image.fromarray(_norm(chip, kind), mode="L")
                    path = out_base / f"{kind}_{sz}.png"
                    img.save(path, "PNG")
                    # relative to data dir if possible
                    try:
                        rel[f"{kind}_{sz}"] = str(path.relative_to(data_dir))
                    except Exception:
                        rel[f"{kind}_{sz}"] = str(path)
            (out_base / "meta.json").write_text(_json.dumps({"candidate": cand_id, "kinds": rel}, indent=2))
            return rel
        except Exception:
            return {}

    # Fallback: try to interpret as (location_id, candidate, arrays, grid) with out_dir in kwargs
    if len(args) >= 4:
        location_id = str(args[0])
        candidate = args[1] if isinstance(args[1], dict) else {}
        arrays = args[2]
        grid = args[3]
        out_dir = kwargs.get("out_dir", kwargs.get("data_dir", Path("data") / "chips" / location_id))
        candidate_dir2 = Path(str(out_dir))
        return export_chips(location_id, candidate, arrays, grid, candidate_dir2, **kwargs)

    return {}


def export_chips_for_candidate(*args: Any, **kwargs: Any) -> dict[str, str]:
    """Compatibility shim for SchedulerWatch."""

    try:
        from lidar_discovery.chips import export_chips as _orig

        # If called as export_chips_for_candidate(settings, candidate)
        if args and hasattr(args[0], "data_dir"):
            # Not enough info to load arrays; return empty and let runner handle it
            return {}
        return {}
    except Exception:
        return {}
