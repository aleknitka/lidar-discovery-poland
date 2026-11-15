"""Archaeoscape transfer spike — adapter for Cambodia ALS dataset (NeurIPS 2024).

See docs/research/archaeoscape-spike.md for the full write-up and
docs/11 §2.1 + §12 items 1-2 for the backlog context.
"""

from __future__ import annotations

__all__ = ["ARCHAEOSCAPE_CLASSES", "ARCHAEOSCAPE_VERSION"]

ARCHAEOSCAPE_CLASSES = ("background", "mound", "temple", "hydro")
ARCHAEOSCAPE_VERSION = "1"
