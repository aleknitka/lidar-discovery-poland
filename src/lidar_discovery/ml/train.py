"""Training entry points (gbm/chip/unet/ae). Thin wrappers over models/*."""

from __future__ import annotations

from pathlib import Path

import numpy as np


def train_gbm(
    features: np.ndarray,
    labels: np.ndarray,
    feature_names: list[str],
    out_dir: Path,
) -> Path:
    from lidar_discovery.ml.models import gbm as gbm_model

    out = out_dir / "gbm.txt"
    gbm_model.train(features, labels, feature_names=feature_names, out_path=out)
    return out


def train_chip(
    chips: np.ndarray,
    labels: np.ndarray,
    out_dir: Path,
    epochs: int = 10,
) -> Path:
    from lidar_discovery.ml.models import chipnet

    out = out_dir / "chip.pt"
    chipnet.train_classifier(chips, labels, epochs=epochs, out_path=out)
    return out


def train_unet(
    patches: np.ndarray,
    masks: np.ndarray,
    out_dir: Path,
    epochs: int = 10,
) -> Path:
    from lidar_discovery.ml.models import unet

    out = out_dir / "unet.pt"
    unet.train_unet(patches, masks, epochs=epochs, out_path=out)
    return out
