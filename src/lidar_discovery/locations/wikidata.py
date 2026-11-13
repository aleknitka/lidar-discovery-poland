"""Wikidata lookup (API search + entity claims; generic User-Agent, no personal info)."""

from __future__ import annotations

from typing import Any

import httpx

from lidar_discovery.config import USER_AGENT

API = "https://www.wikidata.org/w/api.php"


def search_places(name: str, language: str = "pl", limit: int = 10) -> list[dict[str, Any]]:
    """Return [{qid, label, description, lat, lon, precision_deg}] for entities matching name."""
    with httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=30) as c:
        r = c.get(
            API,
            params={
                "action": "wbsearchentities",
                "search": name,
                "language": language,
                "limit": limit,
                "format": "json",
            },
        )
        r.raise_for_status()
        hits = r.json().get("search", [])
        if not hits:
            return []
        ids = "|".join(h["id"] for h in hits)
        r = c.get(
            API,
            params={
                "action": "wbgetentities",
                "ids": ids,
                "props": "claims|labels|descriptions",
                "format": "json",
            },
        )
        r.raise_for_status()
        ents = r.json().get("entities", {})
    out = []
    for h in hits:
        e = ents.get(h["id"], {})
        p625 = e.get("claims", {}).get("P625")
        if not p625:
            continue
        v = p625[0]["mainsnak"]["datavalue"]["value"]
        out.append(
            {
                "qid": h["id"],
                "label": h.get("label"),
                "description": h.get("description"),
                "lat": v["latitude"],
                "lon": v["longitude"],
                "precision_deg": v.get("precision"),
            }
        )
    return out
