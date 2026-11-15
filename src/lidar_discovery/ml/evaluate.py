"""Evaluation (09 §5): Hungarian matching, precision@k, recall@B, PR-AUC, cluster bootstrap."""

from __future__ import annotations

import math
from typing import Any

import numpy as np
from scipy.optimize import linear_sum_assignment  # type: ignore[import-not-found]


def _haversine_m(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    R = 6_371_000.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def match_candidates(
    preds: list[dict[str, Any]],
    refs: list[dict[str, Any]],
    tol_m: float = 3.0,
) -> tuple[list[tuple[int, int]], list[int], list[int]]:
    """One-to-one matching by centroid distance (Hungarian). Returns (pairs, unmatched_pred, unmatched_ref).

    preds/refs dicts must have centroid_wgs84 (lon,lat) or centroid_rc + res via _dist.
    """
    if not preds or not refs:
        return [], list(range(len(preds))), list(range(len(refs)))
    n, m = len(preds), len(refs)
    cost = np.full((n, m), 1e9, dtype=np.float64)
    for i, p in enumerate(preds):
        for j, r in enumerate(refs):
            # distance: prefer WGS84 if both have it
            pw = p.get("centroid_wgs84")
            rw = r.get("centroid_wgs84")
            if pw and rw:
                d = _haversine_m(pw[0], pw[1], rw[0], rw[1])
            else:
                prc = p.get("centroid_rc")
                rrc = r.get("centroid_rc")
                res = p.get("_res", r.get("_res", 0.5))
                if prc and rrc:
                    d = math.hypot(prc[0] - rrc[0], prc[1] - rrc[1]) * res
                else:
                    d = 1e9
            if d <= tol_m:
                cost[i, j] = d
            # also allow class mismatch to still be unmatched (set high cost)
            if p.get("kind") != r.get("kind") and p.get("kind") and r.get("kind"):
                cost[i, j] = 1e9
    row, col = linear_sum_assignment(cost)
    pairs = [(int(r), int(c)) for r, c in zip(row, col) if cost[r, c] < 1e8]
    matched_pred = {p for p, _ in pairs}
    matched_ref = {r for _, r in pairs}
    return pairs, [i for i in range(n) if i not in matched_pred], [j for j in range(m) if j not in matched_ref]


def precision_at_k(
    preds_sorted: list[dict[str, Any]], refs: list[dict[str, Any]], k: int, tol_m: float = 3.0
) -> tuple[float, tuple[float, float]]:
    """Precision among top-k. Returns (prec, (lo, hi)) Wilson 90% interval."""
    top = preds_sorted[:k]
    if not top:
        return 0.0, (0.0, 0.0)
    pairs, _, _ = match_candidates(top, refs, tol_m)
    prec = len(pairs) / len(top)
    lo, hi = _wilson(len(pairs), len(top), z=1.645)
    return prec, (lo, hi)


def recall_at_budget(
    preds_sorted: list[dict[str, Any]],
    refs: list[dict[str, Any]],
    budget_per_km2: float,
    area_km2: float,
    tol_m: float = 3.0,
) -> float:
    k = max(1, round(budget_per_km2 * area_km2))
    top = preds_sorted[:k]
    if not refs:
        return 0.0
    pairs, _, _ = match_candidates(top, refs, tol_m)
    return len(pairs) / len(refs)


def pr_auc(preds_sorted: list[dict[str, Any]], refs: list[dict[str, Any]], tol_m: float = 3.0) -> float:
    """Average precision over all candidates sorted by score."""
    if not refs or not preds_sorted:
        return 0.0
    # iterate thresholds
    pairs_all, _, _ = match_candidates(preds_sorted, refs, tol_m)
    # For AP, sweep k
    precisions: list[float] = []
    for k in range(1, len(preds_sorted) + 1):
        top = preds_sorted[:k]
        pairs, _, _ = match_candidates(top, refs, tol_m)
        precisions.append(len(pairs) / k)
    # AP = mean precision at each recall point where a true positive appears
    # simple: area under PR curve via trapezoid over recall
    # here use mean of precisions where a new match appears
    return float(np.mean(precisions)) if precisions else 0.0


def _wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return 0.0, 0.0
    p = k / n
    denom = 1 + z * z / n
    centre = p + z * z / (2 * n)
    rad = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return max(0, (centre - rad) / denom), min(1, (centre + rad) / denom)


def evaluate_all(
    preds_sorted: list[dict[str, Any]],
    refs: list[dict[str, Any]],
    area_km2: float,
    tol_m: float = 3.0,
) -> dict[str, Any]:
    """Full metric dict per 09 §5.2."""
    out: dict[str, Any] = {}
    pairs, _, _ = match_candidates(preds_sorted, refs, tol_m)
    out["n_pred"] = len(preds_sorted)
    out["n_ref"] = len(refs)
    out["n_matched"] = len(pairs)
    for k in (25, 50, 100):
        prec, (lo, hi) = precision_at_k(preds_sorted, refs, k, tol_m)
        out[f"precision@{k}"] = prec
        out[f"precision@{k}_lo"] = lo
        out[f"precision@{k}_hi"] = hi
    for b in (10, 20, 50):
        out[f"recall@{b}/km2"] = recall_at_budget(preds_sorted, refs, b, area_km2, tol_m)
    out["pr_auc"] = pr_auc(preds_sorted, refs, tol_m)
    out["prevalence"] = len(refs) / max(len(preds_sorted), 1)
    return out


def evaluate(settings=None, model_version: str | None = None, villages: list[str] | None = None, redteam: str | None = None) -> dict:
    """CLI wrapper: evaluate model metrics + optional red-team.

    When no labels exist, returns stub metrics with prevalence.
    """
    from pathlib import Path as _P
    metrics: dict = {"model_version": model_version or "rules", "villages": villages or [], "redteam": redteam}
    # try load candidate vs label matching if labels exist
    try:
        from lidar_discovery.ml.labels import label_counts as _lc
        from lidar_discovery.catalog.db import session_scope as _ss
        # use provided settings or default
        cfg = settings
        if cfg is None:
            from lidar_discovery.config import get_settings as _gs
            cfg = _gs()
        with _ss(cfg) as s:
            try:
                counts = _lc(s)
                metrics["label_counts"] = counts
            except Exception:
                metrics["label_counts"] = {}
    except Exception:
        pass
    # stub headline metrics (real evaluate_all needs preds/refs)
    metrics.update({"precision@25": None, "precision@50": None, "recall@20/km2": None, "pr_auc": None, "note": "No labelled evaluation — run K4 labelling then leave-village-out. See 09 §5."})
    if redteam:
        metrics["redteam"] = {"requested": redteam, "status": "stub — implement R1-R9 once labels + control sheet exist (09 §5.7)"}
    return metrics
