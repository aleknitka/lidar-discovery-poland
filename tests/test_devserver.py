from __future__ import annotations

import socket

from lidar_discovery import devserver


def test_port_in_use_detects_listener():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        s.listen()
        port = s.getsockname()[1]
        assert devserver.port_in_use(port)
    assert not devserver.port_in_use(port)


def test_wait_for_gives_up_when_process_dies():
    # nothing listens on this URL; alive() is False so it returns immediately
    assert devserver.wait_for("http://127.0.0.1:9/", 30, lambda: False) is False


def test_repo_root_has_frontend():
    assert (devserver.REPO_ROOT / "frontend" / "package.json").exists()


def test_run_dev_rejects_missing_frontend(tmp_path):
    assert devserver.run_dev(frontend_dir=tmp_path, open_browser=False) == 2
