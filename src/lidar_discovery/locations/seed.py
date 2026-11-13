"""Seed YAML -> Location rows."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml
from sqlmodel import Session

from lidar_discovery.catalog.models import Location, dumps
from lidar_discovery.catalog.repo import upsert_location


def load_seed(path: Path) -> list[dict[str, Any]]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return list(data.get("locations", []))


def location_from_seed(entry: dict[str, Any]) -> Location:
    pt = entry["point"]
    dep = entry.get("depopulation") or {}
    dep = {"year": dep.get("year"), "cause": dep.get("cause"), "source_url": dep.get("source_url")}
    return Location(
        id=entry["id"],
        names=dumps(entry.get("names") or {}),
        lon=float(pt["lon"]),
        lat=float(pt["lat"]),
        polygon=dumps(entry["polygon"]) if entry.get("polygon") else None,
        aoi_buffer_m=float(entry.get("aoi_buffer_m", 1000.0)),
        depopulation=dumps(dep),
        provenance=dumps(entry.get("provenance") or []),
        disclosure=entry.get("disclosure", "public"),
        notes=entry.get("notes"),
    )


def import_seed(session: Session, path: Path) -> list[Location]:
    out = []
    for entry in load_seed(path):
        new = location_from_seed(entry)
        old = session.get(Location, new.id)
        if old and old.polygon and not new.polygon:  # keep a previously fetched precinct
            new.polygon = old.polygon
            new.provenance = dumps(
                json.loads(new.provenance)
                + [p for p in json.loads(old.provenance) if p.get("provider") == "prg-wfs"]
            )
        out.append(upsert_location(session, new))
    return out
