"""Calibration (09 §5.5): isotonic / Platt, reliability diagram, ECE."""

from __future__ import annotations

from typing import Any

import numpy as np


def fit_isotonic(scores: np.ndarray, labels: np.ndarray) -> Any:
    from sklearn.isotonic import IsotonicRegression  # type: ignore[import-not-found]

    ir = IsotonicRegression(out_of_bounds="clip")
    ir.fit(scores, labels)
    return ir


def fit_platt(scores: np.ndarray, labels: np.ndarray) -> Any:
    from sklearn.linear_model import LogisticRegression  # type: ignore[import-not-found]

    lr = LogisticRegression()
    lr.fit(scores.reshape(-1, 1), labels)
    return lr


def calibrate(scores: np.ndarray, calibrator: Any) -> np.ndarray:
    if hasattr(calibrator, "predict"):
        try:
            return np.asarray(calibrator.predict(scores.reshape(-1, 1)), dtype=np.float32)
        except Exception:
            pass
    if hasattr(calibrator, "transform"):
        return np.asarray(calibrator.transform(scores), dtype=np.float32)
    # callable
    return np.asarray(calibrator(scores), dtype=np.float32)


def expected_calibration_error(
    y_true: np.ndarray, y_prob: np.ndarray, n_bins: int = 10
) -> float:
    bins = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    for i in range(n_bins):
        lo, hi = bins[i], bins[i + 1]
        mask = (y_prob >= lo) & (y_prob < hi) if i < n_bins - 1 else (y_prob >= lo) & (y_prob <= hi)
        if not mask.any():
            continue
        acc = float(np.mean(y_true[mask]))
        conf = float(np.mean(y_prob[mask]))
        ece += abs(acc - conf) * (np.sum(mask) / len(y_true))
    return float(ece)
