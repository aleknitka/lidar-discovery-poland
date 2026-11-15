"""One-command local development: API (uvicorn) + web app (Vite), started and stopped together."""

from __future__ import annotations

import os
import shutil
import signal
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser
from collections.abc import Callable
from pathlib import Path

import typer

from lidar_discovery.catalog import repo
from lidar_discovery.catalog.db import session_scope
from lidar_discovery.config import get_settings

REPO_ROOT = Path(__file__).resolve().parents[2]
IS_WINDOWS = sys.platform == "win32"


def port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    """True if something already accepts TCP connections on host:port (IPv4 or IPv6 loopback)."""
    for h in {host, "::1"}:
        family = socket.AF_INET6 if ":" in h else socket.AF_INET
        try:
            with socket.socket(family, socket.SOCK_STREAM) as s:
                s.settimeout(0.3)
                if s.connect_ex((h, port)) == 0:
                    return True
        except OSError:
            continue
    return False


def wait_for(url: str, timeout_s: float, alive: Callable[[], bool]) -> bool:
    """Poll url until it answers (any HTTP status); stop on timeout or when alive() is False."""
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline and alive():
        try:
            with urllib.request.urlopen(url, timeout=2):
                return True
        except urllib.error.HTTPError:
            return True  # the server answered
        except (urllib.error.URLError, OSError):
            time.sleep(0.4)
    return False


def _spawn(cmd: list[str], cwd: Path) -> subprocess.Popen:
    kwargs: dict = {"cwd": str(cwd)}
    if IS_WINDOWS:
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        kwargs["start_new_session"] = True
    return subprocess.Popen(cmd, **kwargs)


def _stop(proc: subprocess.Popen) -> None:
    """Terminate a process and its children (npm spawns node; uvicorn may spawn workers)."""
    if proc.poll() is not None:
        return
    try:
        if IS_WINDOWS:
            subprocess.run(
                ["taskkill", "/PID", str(proc.pid), "/T", "/F"],
                capture_output=True,
                check=False,
            )
        else:
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        proc.wait(timeout=8)
    except (subprocess.TimeoutExpired, ProcessLookupError, PermissionError):
        proc.kill()


def run_dev(
    *,
    api_port: int = 8000,
    web_port: int = 5173,
    open_browser: bool = True,
    mock: bool = False,
    frontend_dir: Path | None = None,
) -> int:
    fe = frontend_dir or REPO_ROOT / "frontend"
    if not (fe / "package.json").exists():
        typer.echo(f"Frontend not found at {fe} (run from a repository checkout).", err=True)
        return 2
    npm = shutil.which("npm")
    if npm is None:
        typer.echo("npm not found. Install Node.js 20+ from https://nodejs.org/", err=True)
        return 2

    busy = [p for p in ([] if mock else [api_port]) + [web_port] if port_in_use(p)]
    if busy:
        typer.echo(
            f"Port(s) {', '.join(map(str, busy))} already in use. Is the app already running? "
            "Stop it, or choose other ports with --api-port / --web-port.",
            err=True,
        )
        return 2

    if not (fe / "node_modules").exists():
        typer.echo("Installing frontend packages (first run, one minute)...")
        if subprocess.run([npm, "install"], cwd=fe, check=False).returncode != 0:
            typer.echo("npm install failed.", err=True)
            return 1

    if not mock:
        settings = get_settings()
        settings.ensure_dirs()
        with session_scope(settings) as session:
            empty = not repo.list_locations(session)
        if empty:
            from lidar_discovery.locations.seed import import_seed

            with session_scope(settings) as session:
                locs = import_seed(session, settings.seeds_dir / "locations.yaml")
            typer.echo(f"Loaded {len(locs)} seed locations.")

    procs: list[subprocess.Popen] = []
    web_url = f"http://localhost:{web_port}/explore"
    try:
        api: subprocess.Popen | None = None
        if not mock:
            api = _spawn(
                [
                    sys.executable,
                    "-m",
                    "uvicorn",
                    "lidar_discovery.api.app:create_app",
                    "--factory",
                    "--host",
                    "127.0.0.1",
                    "--port",
                    str(api_port),
                ],
                REPO_ROOT,
            )
            procs.append(api)
            typer.echo(f"Starting API on http://127.0.0.1:{api_port} ...")
            if not wait_for(
                f"http://127.0.0.1:{api_port}/api/health", 60, lambda: api.poll() is None
            ):
                typer.echo("API failed to start (see the error above).", err=True)
                return 1

        script = "dev:mock" if mock else "dev"
        web = _spawn(
            [
                npm,
                "run",
                script,
                "--",
                "--host",
                "127.0.0.1",
                "--port",
                str(web_port),
                "--strictPort",
            ],
            fe,
        )
        procs.append(web)
        typer.echo("Starting web app ...")
        if not wait_for(f"http://127.0.0.1:{web_port}/", 60, lambda: web.poll() is None):
            typer.echo("Web app failed to start (see the error above).", err=True)
            return 1

        web_url = f"http://127.0.0.1:{web_port}/explore"
        typer.echo(f"\nReady: {web_url}" + ("  (mock data)" if mock else ""))
        if not mock:
            typer.echo(f"API docs: http://127.0.0.1:{api_port}/docs")
        typer.echo("Press Ctrl+C to stop both.\n")
        if open_browser:
            webbrowser.open(web_url)

        while all(p.poll() is None for p in procs):
            time.sleep(0.5)
        typer.echo("A process exited; shutting down.", err=True)
        return 1
    except KeyboardInterrupt:
        typer.echo("\nStopping...")
        return 0
    finally:
        for p in reversed(procs):
            _stop(p)
