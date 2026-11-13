from __future__ import annotations

import httpx
import pytest

from lidar_discovery.sources.download import download_file

PAYLOAD = bytes(range(256)) * 4000  # ~1 MB


def make_client(fail_after: int | None = None):
    seen: list[str | None] = []

    def handler(request: httpx.Request) -> httpx.Response:
        rng = request.headers.get("range")
        seen.append(rng)
        if request.method == "HEAD":
            return httpx.Response(200, headers={"content-length": str(len(PAYLOAD))})
        start = int(rng.split("=")[1].rstrip("-")) if rng else 0
        body = PAYLOAD[start:]
        if fail_after is not None and not rng:
            body = body[:fail_after]  # truncated stream: server hangs up early
            return httpx.Response(200, content=body, headers={"content-length": str(len(PAYLOAD))})
        return httpx.Response(206 if rng else 200, content=body)

    return httpx.Client(transport=httpx.MockTransport(handler)), seen


def test_download_and_idempotent(tmp_path):
    client, seen = make_client()
    dest = tmp_path / "a" / "t.laz"
    assert download_file("https://x.invalid/t.laz", dest, client=client) == dest
    assert dest.read_bytes() == PAYLOAD
    assert not dest.with_name("t.laz.part").exists()
    n = len(seen)
    download_file("https://x.invalid/t.laz", dest, client=client)  # size matches -> skipped
    assert len(seen) == n + 1  # only the HEAD


def test_resume_from_part(tmp_path):
    client, seen = make_client()
    dest = tmp_path / "t.laz"
    dest.with_name("t.laz.part").write_bytes(PAYLOAD[:300_000])
    download_file("https://x.invalid/t.laz", dest, expected_size=len(PAYLOAD), client=client)
    assert dest.read_bytes() == PAYLOAD
    assert "bytes=300000-" in seen


def test_incomplete_download_keeps_part_then_resumes(tmp_path):
    client, _ = make_client(fail_after=1000)
    dest = tmp_path / "t.laz"
    with pytest.raises(OSError, match="incomplete"):
        download_file("https://x.invalid/t.laz", dest, expected_size=len(PAYLOAD), client=client)
    part = dest.with_name("t.laz.part")
    assert part.exists() and part.stat().st_size == 1000 and not dest.exists()
    client2, seen2 = make_client()
    download_file("https://x.invalid/t.laz", dest, expected_size=len(PAYLOAD), client=client2)
    assert dest.read_bytes() == PAYLOAD and "bytes=1000-" in seen2
