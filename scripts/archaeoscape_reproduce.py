"""Thin wrapper so `python scripts/archaeoscape_reproduce.py` works as well as -m."""

from lidar_discovery.ml.archaeoscape.reproduce import main

if __name__ == "__main__":
    raise SystemExit(main())
