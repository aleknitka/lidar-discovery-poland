"""LiDAR source adapters. Importing this package registers the built-in sources."""

from lidar_discovery.sources import gugik, local, zbgis  # noqa: F401
from lidar_discovery.sources.base import (
    LidarSource,
    TileRef,
    get_source,
    register_source,
    source_ids,
)

__all__ = ["LidarSource", "TileRef", "get_source", "register_source", "source_ids"]
