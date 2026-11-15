"""Minimal WFS 2.0 client: GetCapabilities, GetFeature with paging, GML parsing, file cache."""

from __future__ import annotations

import hashlib
import re
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import httpx

from lidar_discovery.config import USER_AGENT

NS = {
    "wfs": "http://www.opengis.net/wfs/2.0",
    "gml": "http://www.opengis.net/gml/3.2",
    "ows": "http://www.opengis.net/ows/1.1",
    "wfs11": "http://www.opengis.net/wfs",
}


@dataclass
class WfsFeature:
    """A parsed WFS member: flat attributes plus a footprint in EPSG:2180 (x=E, y=N)."""

    gml_id: str
    attrs: dict[str, str]
    rings: list[list[tuple[float, float]]] = field(default_factory=list)  # exteriors
    bbox: tuple[float, float, float, float] | None = None  # minE, minN, maxE, maxN


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _pairs(text: str, swap: bool) -> list[tuple[float, float]]:
    nums = [float(v) for v in text.split()]
    pts = list(zip(nums[0::2], nums[1::2], strict=False))
    # urn:ogc:def:crs:EPSG::2180 axis order is northing, easting -> swap to (E, N)
    return [(b, a) for a, b in pts] if swap else pts


def _swap_needed(srs: str | None) -> bool:
    return bool(srs) and "urn:ogc:def:crs:EPSG" in srs and srs.rstrip("/").endswith("2180")


def parse_capabilities(xml_text: str) -> list[str]:
    """Return feature type names (e.g. 'gugik:SkorowidzDanychPomiarowychLIDAR2012')."""
    root = ET.fromstring(xml_text)
    names = [el.text.strip() for el in root.iter() if _local(el.tag) == "Name" and el.text]
    return [n for n in names if ":" in n]


def parse_feature_collection(xml_text: str) -> tuple[list[WfsFeature], str | None]:
    """Parse a GML 3.2 FeatureCollection. Returns (features, next_page_url)."""
    root = ET.fromstring(xml_text)
    if _local(root.tag) == "ExceptionReport":
        msg = " ".join(
            (e.text or "").strip() for e in root.iter() if _local(e.tag) == "ExceptionText"
        )
        raise RuntimeError(f"WFS exception: {msg}")
    next_url = root.attrib.get("next")
    feats: list[WfsFeature] = []
    for member in root:
        if _local(member.tag) not in ("member", "featureMember"):
            continue
        for ft in member:
            gml_id = ft.attrib.get(f"{{{NS['gml']}}}id", "")
            attrs: dict[str, str] = {}
            rings: list[list[tuple[float, float]]] = []
            bbox = None
            for child in ft:
                name = _local(child.tag)
                if name == "boundedBy":
                    env = next((e for e in child.iter() if _local(e.tag) == "Envelope"), None)
                    if env is not None:
                        sw = _swap_needed(env.attrib.get("srsName"))
                        lc = next(e for e in env if _local(e.tag) == "lowerCorner")
                        uc = next(e for e in env if _local(e.tag) == "upperCorner")
                        (x0, y0), (x1, y1) = (
                            _pairs(lc.text or "", sw)[0],
                            _pairs(uc.text or "", sw)[0],
                        )
                        bbox = (min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1))
                    continue
                geoms = [e for e in child.iter() if _local(e.tag) == "Polygon"]
                if geoms:
                    for poly in geoms:
                        sw = _swap_needed(poly.attrib.get("srsName"))
                        for ext in (e for e in poly if _local(e.tag) == "exterior"):
                            pl = next((e for e in ext.iter() if _local(e.tag) == "posList"), None)
                            if pl is not None and pl.text:
                                rings.append(_pairs(pl.text, sw))
                    continue
                # plain attribute (possibly with a nested gml:timePosition etc.)
                text = (child.text or "").strip()
                if not text:
                    text = " ".join(
                        (e.text or "").strip() for e in child.iter() if e is not child and e.text
                    ).strip()
                attrs[name] = text
            feats.append(WfsFeature(gml_id=gml_id, attrs=attrs, rings=rings, bbox=bbox))
    return feats, next_url


class WfsClient:
    """Thin httpx wrapper with an on-disk response cache."""

    def __init__(
        self,
        base_url: str,
        cache_dir: Path | None = None,
        timeout: float = 60.0,
        cache_ttl_s: float = 7 * 86400,
        client: httpx.Client | None = None,
    ) -> None:
        self.base_url = base_url
        self.cache_dir = cache_dir
        self.cache_ttl_s = cache_ttl_s
        self._client = client or httpx.Client(
            headers={"User-Agent": USER_AGENT}, timeout=timeout, follow_redirects=True
        )

    def _get(self, params: dict[str, Any] | None = None, url: str | None = None) -> str:
        target = url or self.base_url
        key = hashlib.sha256(
            (
                target + "?" + "&".join(f"{k}={v}" for k, v in sorted((params or {}).items()))
            ).encode()
        ).hexdigest()[:32]
        path = self.cache_dir / f"{key}.xml" if self.cache_dir else None
        if path and path.exists() and time.time() - path.stat().st_mtime < self.cache_ttl_s:
            return path.read_text(encoding="utf-8")
        last: Exception | None = None
        for attempt in range(3):
            try:
                r = self._client.get(target, params=None if url else params)
                r.raise_for_status()
                text = r.text
                break
            except httpx.HTTPError as e:  # retry transient errors
                last = e
                time.sleep(1.5 * (attempt + 1))
        else:
            raise RuntimeError(f"WFS request failed: {last}") from last
        if path:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        return text

    def feature_types(self) -> list[str]:
        text = self._get({"service": "WFS", "version": "2.0.0", "request": "GetCapabilities"})
        return parse_capabilities(text)

    def get_features(
        self,
        type_name: str,
        bbox: str | None = None,
        extra: dict[str, str] | None = None,
        page_size: int = 500,
        max_pages: int = 50,
        cql: str | None = None,
    ) -> list[WfsFeature]:
        params: dict[str, Any] = {
            "service": "WFS",
            "version": "2.0.0",
            "request": "GetFeature",
            "typeNames": type_name,
            "count": page_size,
        }
        if bbox:
            params["BBOX"] = bbox
        if cql:
            params["CQL_FILTER"] = cql
        params.update(extra or {})
        out: list[WfsFeature] = []
        text = self._get(params)
        for _ in range(max_pages):
            feats, nxt = parse_feature_collection(text)
            out.extend(feats)
            if not nxt or len(feats) < page_size:
                break
            text = self._get(url=nxt)
        return out


def year_from_type_name(name: str) -> int | None:
    m = re.search(r"(\d{4})$", name)
    return int(m.group(1)) if m else None
