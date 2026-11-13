"""Resumable streaming downloads (.part files, HTTP Range)."""

from __future__ import annotations

import os
from collections.abc import Callable
from pathlib import Path

import httpx

from lidar_discovery.config import USER_AGENT


def remote_size(url: str, client: httpx.Client | None = None) -> int | None:
    own = client is None
    client = client or httpx.Client(headers={"User-Agent": USER_AGENT}, follow_redirects=True)
    try:
        r = client.head(url)
        if r.status_code == 200 and "content-length" in r.headers:
            return int(r.headers["content-length"])
    except httpx.HTTPError:
        return None
    finally:
        if own:
            client.close()
    return None


def download_file(
    url: str,
    dest: Path,
    expected_size: int | None = None,
    progress: Callable[[int, int | None], None] | None = None,
    client: httpx.Client | None = None,
    chunk: int = 1 << 20,
) -> Path:
    """Download url to dest. Idempotent: skips if dest exists with the expected size;
    resumes from dest.part when the server supports Range."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    own = client is None
    client = client or httpx.Client(
        headers={"User-Agent": USER_AGENT}, follow_redirects=True, timeout=httpx.Timeout(60.0)
    )
    try:
        if expected_size is None:
            expected_size = remote_size(url, client)
        if dest.exists() and (expected_size is None or dest.stat().st_size == expected_size):
            return dest
        part = dest.with_name(dest.name + ".part")
        for _ in range(2):
            have = part.stat().st_size if part.exists() else 0
            if expected_size is not None and have > expected_size:
                part.unlink()
                have = 0
            headers = {"Range": f"bytes={have}-"} if have else {}
            with client.stream("GET", url, headers=headers) as r:
                if r.status_code == 416:  # range not satisfiable -> restart
                    part.unlink(missing_ok=True)
                    continue
                r.raise_for_status()
                mode = "ab" if (have and r.status_code == 206) else "wb"
                done = have if mode == "ab" else 0
                total = expected_size
                with open(part, mode) as fh:
                    for data in r.iter_bytes(chunk):
                        fh.write(data)
                        done += len(data)
                        if progress:
                            progress(done, total)
            break
        size = part.stat().st_size
        if expected_size is not None and size != expected_size:
            raise OSError(f"incomplete download {size} != {expected_size}; rerun to resume")
        os.replace(part, dest)
        return dest
    finally:
        if own:
            client.close()
