"""LightGBM re-ranker (Stage 1, 09 §4.1 B). Monotone constraints where sensible."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np


def _require_lgbm() -> Any:
    try:
        import lightgbm as lgb  # type: ignore[import-not-found]

        return lgb
    except Exception as e:  # pragma: no cover
        raise RuntimeError(
            "lightgbm not installed. Run: uv sync --extra ml  (or pip install lightgbm)"
        ) from e


def train(
    X: np.ndarray,
    y: np.ndarray,
    feature_names: list[str] | None = None,
    monotone: dict[str, int] | None = None,
    params: dict[str, Any] | None = None,
    out_path: Path | None = None,
) -> Any:
    """Train a binary LightGBM. Returns the Booster."""
    lgb = _require_lgbm()
    # monotone: feature_name -> 1 (increasing) or -1
    mc = None
    if monotone and feature_names:
        mc = [monotone.get(fn, 0) for fn in feature_names]
    ds = lgb.Dataset(X, label=y, feature_name=feature_names or "auto")
    p = {
        "objective": "binary",
        "metric": "auc",
        "verbosity": -1,
        "boosting_type": "gbdt",
        "num_leaves": 31,
        "learning_rate": 0.05,
        "feature_fraction": 0.8,
        "bagging_fraction": 0.8,
        "bagging_freq": 1,
        **(params or {}),
    }
    if mc is not None:
        p["monotone_constraints"] = mc
    booster = lgb.train(p, ds, num_boost_round=200)
    if out_path is not None:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        booster.save_model(str(out_path))
    return booster


def predict_proba(model: Any, X: np.ndarray) -> np.ndarray:
    return np.asarray(model.predict(X), dtype=np.float32)


def predict(model: Any, X: np.ndarray) -> np.ndarray:
    """Alias for predict_proba (kept for uniform train/predict/load contract)."""
    return predict_proba(model, X)


def load(path: Path) -> Any:
    lgb = _require_lgbm()
    return lgb.Booster(model_file=str(path))
