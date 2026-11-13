"""Repository functions + (de)serialisation between rows and GeoJSON."""

from __future__ import annotations

import json
import uuid
from datetime import UTC
from typing import Any

from sqlmodel import Session, select

from lidar_discovery.catalog.disclosure import default_disclosure
from lidar_discovery.catalog.models import (
    DISCLOSURES,
    MORPH_CLASSES,
    ORIGINS,
    REALITY,
    REVIEW_STATUSES,
    Candidate,
    Location,
    Product,
    TileCache,
    dumps,
    utcnow,
)


class ValidationError(ValueError):
    pass


# ---------------------------------------------------------------- locations
def upsert_location(session: Session, loc: Location) -> Location:
    existing = session.get(Location, loc.id)
    if existing:
        for k, v in loc.model_dump().items():
            setattr(existing, k, v)
        loc = existing
    session.add(loc)
    session.commit()
    session.refresh(loc)
    return loc


def get_location(session: Session, loc_id: str) -> Location | None:
    return session.get(Location, loc_id)


def list_locations(session: Session) -> list[Location]:
    return list(session.exec(select(Location).order_by(Location.id)))


def location_to_feature(loc: Location, has_products: bool | None = None) -> dict[str, Any]:
    geom = {"type": "Point", "coordinates": [loc.lon, loc.lat]}
    props: dict[str, Any] = {
        "id": loc.id,
        "names": json.loads(loc.names),
        "depopulation": json.loads(loc.depopulation),
        "provenance": json.loads(loc.provenance),
        "disclosure": loc.disclosure,
        "aoi_buffer_m": loc.aoi_buffer_m,
        "polygon": json.loads(loc.polygon) if loc.polygon else None,
        "notes": loc.notes,
    }
    if has_products is not None:
        props["has_products"] = has_products
    return {"type": "Feature", "id": loc.id, "geometry": geom, "properties": props}


# ----------------------------------------------------------------- products
def add_product(session: Session, prod: Product) -> Product:
    existing = session.get(Product, prod.id)
    if existing:
        session.delete(existing)
        session.commit()
    session.add(prod)
    session.commit()
    session.refresh(prod)
    return prod


def list_products(session: Session, location_id: str | None = None) -> list[Product]:
    q = select(Product).order_by(Product.epoch, Product.kind)
    if location_id:
        q = q.where(Product.location_id == location_id)
    return list(session.exec(q))


def get_product(session: Session, pid: str) -> Product | None:
    return session.get(Product, pid)


def product_to_layer(p: Product) -> dict[str, Any]:
    return {
        "id": p.id,
        "location_id": p.location_id,
        "kind": p.kind,
        "epoch": p.epoch,
        "source_id": p.source_id,
        "resolution_m": p.resolution_m,
        "crs_h": p.crs_h,
        "bounds": json.loads(p.bounds_wgs84),
        "tile_url": f"/api/layers/{p.id}/tiles/{{z}}/{{x}}/{{y}}.png",
        "provenance": json.loads(p.provenance),
        "created_at": p.created_at.isoformat(),
    }


# --------------------------------------------------------------- candidates
def _check(name: str, value: str, allowed: tuple[str, ...]) -> None:
    if value not in allowed:
        raise ValidationError(f"{name} must be one of {list(allowed)}, got {value!r}")


_ENUM_FIELDS: dict[str, tuple[str, ...] | None] = {
    "location_id": None,
    "morph_class": MORPH_CLASSES,
    "reality": REALITY,
    "origin": ORIGINS,
    "review_status": REVIEW_STATUSES,
    "disclosure": DISCLOSURES,
    "model_version": None,
    "reviewer_notes": None,
}


def candidate_from_feature(
    feature: dict[str, Any], existing: Candidate | None = None, partial: bool = False
) -> Candidate:
    """Build/update a Candidate from a GeoJSON Feature (or partial Feature for PATCH)."""
    props = dict(feature.get("properties") or {})
    cand = existing or Candidate(id=str(feature.get("id") or uuid.uuid4().hex[:12]), geometry="")
    geom = feature.get("geometry")
    if geom is not None:
        if not isinstance(geom, dict) or "type" not in geom or "coordinates" not in geom:
            raise ValidationError("geometry must be a GeoJSON geometry")
        cand.geometry = dumps(geom)
    elif existing is None and not partial:
        raise ValidationError("geometry is required")
    for key, allowed in _ENUM_FIELDS.items():
        if key in props:
            if allowed:
                _check(key, props[key], allowed)
            setattr(cand, key, props[key])
    if "reality_confidence" in props:
        c = props["reality_confidence"]
        if isinstance(c, bool) or not isinstance(c, int | float) or not 0 <= c <= 1:
            raise ValidationError("reality_confidence must be within 0..1")
        cand.reality_confidence = float(c)
    if "dating_evidence" in props:
        cand.dating_evidence = dumps(props["dating_evidence"])
    if "documentation_status" in props:
        ds = props["documentation_status"]
        if not isinstance(ds, list):
            raise ValidationError("documentation_status must be a list")
        cand.documentation_status = dumps(ds)
    if existing is None and "disclosure" not in props:
        cand.disclosure = default_disclosure(cand.morph_class)
    cand.updated_at = utcnow()
    return cand


def candidate_to_feature(c: Candidate) -> dict[str, Any]:
    return {
        "type": "Feature",
        "id": c.id,
        "geometry": json.loads(c.geometry),
        "properties": {
            "id": c.id,
            "location_id": c.location_id,
            "morph_class": c.morph_class,
            "reality": c.reality,
            "reality_confidence": c.reality_confidence,
            "dating_evidence": json.loads(c.dating_evidence),
            "documentation_status": json.loads(c.documentation_status),
            "origin": c.origin,
            "model_version": c.model_version,
            "review_status": c.review_status,
            "reviewer_notes": c.reviewer_notes,
            "disclosure": c.disclosure,
            "created_at": c.created_at.isoformat(),
            "updated_at": c.updated_at.isoformat(),
        },
    }


def list_candidates(
    session: Session, location_id: str | None = None, review_status: str | None = None
) -> list[Candidate]:
    q = select(Candidate).order_by(Candidate.created_at)
    if location_id:
        q = q.where(Candidate.location_id == location_id)
    if review_status:
        q = q.where(Candidate.review_status == review_status)
    return list(session.exec(q))


# -------------------------------------------------------------------- cache
def cache_get(session: Session, key: str, max_age_s: float | None = None) -> str | None:
    row = session.get(TileCache, key)
    if row is None:
        return None
    if (
        max_age_s is not None
        and (utcnow() - row.fetched_at.replace(tzinfo=row.fetched_at.tzinfo or UTC)).total_seconds()
        > max_age_s
    ):
        return None
    return row.payload


def cache_put(session: Session, key: str, payload: str) -> None:
    row = session.get(TileCache, key) or TileCache(key=key, payload=payload)
    row.payload = payload
    row.fetched_at = utcnow()
    session.add(row)
    session.commit()
