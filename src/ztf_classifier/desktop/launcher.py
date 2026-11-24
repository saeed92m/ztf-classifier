"""Standalone Windows desktop launcher for the ZTF Classifier Workbench."""

from __future__ import annotations

import argparse
import json
import os
import platform
import secrets
import socket
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Sequence
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

import uvicorn

LOOPBACK_HOST = "127.0.0.1"
WORKBENCH_PATH = "/workbench/"
STARTUP_TIMEOUT_SECONDS = 20.0
SHUTDOWN_TIMEOUT_SECONDS = 10.0
HEALTH_TIMEOUT_SECONDS = 3.0


def workbench_url(port: int, access_token: str) -> str:
    """Build a local URL; keep the token in the fragment, not the HTTP request."""
    if not 1 <= port <= 65535:
        raise ValueError("port must be between 1 and 65535")
    if not access_token:
        raise ValueError("access_token must not be empty")
    token = quote(access_token, safe="")
    return (
        f"http://{LOOPBACK_HOST}:{port}{WORKBENCH_PATH}"
        f"#desktop-token={token}"
    )


def _application_data_dir() -> Path:
    """Return a per-user writable path outside the installation directory."""
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        return Path(local_app_data) / "ZTFClassifier"
    return Path.home() / "AppData" / "Local" / "ZTFClassifier"


def _configure_environment(data_dir: Path, access_token: str) -> dict[str, str | None]:
    """Configure local storage and a per-process API key before importing the API."""
    data_dir = data_dir.expanduser().resolve()
    paths = {
        "ZTF_API_KEY": access_token,
        "ZTF_API_OBSERVATION_CACHE_DIR": str(data_dir / "cache" / "observations"),
        "ZTF_API_JOB_STORE": str(data_dir / "jobs" / "jobs.sqlite3"),
        "ZTF_API_RESULT_STORE": str(data_dir / "results" / "results.sqlite3"),
        "ZTF_API_STATE_PATH": str(data_dir / "settings.json"),
    }
    previous = {name: os.environ.get(name) for name in paths}
    for path in (
        data_dir,
        data_dir / "cache" / "observations",
        data_dir / "jobs",
        data_dir / "results",
        data_dir / "logs",
    ):
        path.mkdir(parents=True, exist_ok=True)
    os.environ.update(paths)
    return previous


def _restore_environment(previous: dict[str, str | None]) -> None:
    for name, value in previous.items():
        if value is None:
            os.environ.pop(name, None)
        else:
            os.environ[name] = value


@dataclass
class LocalApiServer:
    """Manage a loopback-only Uvicorn server for one desktop session."""

    access_token: str
    data_dir: Path
    server: uvicorn.Server | None = None
    thread: threading.Thread | None = None
    listener: socket.socket | None = None
    port: int | None = None
    previous_environment: dict[str, str | None] | None = None

    def start(self) -> int:
        """Start the API on an available loopback port and wait for readiness."""
        if self.thread is not None:
            raise RuntimeError("The local API server has already been started.")
        if not self.access_token:
            raise ValueError("A desktop API token is required.")

        self.previous_environment = _configure_environment(
            self.data_dir,
            self.access_token,
        )
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listener.bind((LOOPBACK_HOST, 0))
        listener.listen(128)
        listener.set_inheritable(False)
        self.listener = listener
        self.port = int(listener.getsockname()[1])

        config = uvicorn.Config(
            "ztf_classifier.api.app:app",
            host=LOOPBACK_HOST,
            port=self.port,
            log_level="warning",
            access_log=False,
            reload=False,
        )
        self.server = uvicorn.Server(config)
        self.thread = threading.Thread(
            target=self.server.run,
            kwargs={"sockets": [listener]},
            name="ztf-classifier-local-api",
            daemon=True,
        )
        self.thread.start()

        deadline = time.monotonic() + STARTUP_TIMEOUT_SECONDS
        while time.monotonic() < deadline:
            if self.server.started and self.thread.is_alive():
                self._check_health()
                return self.port
            if not self.thread.is_alive():
                self.stop()
                raise RuntimeError(
                    "The local API process stopped before it became ready."
                )
            time.sleep(0.05)

        self.stop()
        raise TimeoutError("The local API did not become ready in time.")

    def _check_health(self) -> None:
        if self.port is None:
            raise RuntimeError("The local API port is unavailable.")
        request = Request(
            f"http://{LOOPBACK_HOST}:{self.port}/health",
            headers={"Accept": "application/json"},
        )
        try:
            with urlopen(request, timeout=HEALTH_TIMEOUT_SECONDS) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (OSError, URLError, ValueError) as exc:
            raise RuntimeError("The local API health check failed.") from exc
        if payload.get("status") != "ok":
            raise RuntimeError("The local API returned an unexpected health state.")

    def stop(self) -> None:
        """Stop the API thread and restore environment variables."""
        if self.server is not None:
            self.server.should_exit = True
        if self.thread is not None:
            self.thread.join(timeout=SHUTDOWN_TIMEOUT_SECONDS)
            if self.thread.is_alive() and self.server is not None:
                self.server.force_exit = True
                self.thread.join(timeout=2.0)
            if self.thread.is_alive():
                raise RuntimeError("The local API did not stop cleanly.")
        if self.listener is not None:
            try:
                self.listener.close()
            except OSError:
                pass
        if self.previous_environment is not None:
            _restore_environment(self.previous_environment)
            self.previous_environment = None


def _request_status(url: str, token: str | None = None) -> int:
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(url, headers=headers)
    try:
        with urlopen(request, timeout=HEALTH_TIMEOUT_SECONDS) as response:
            return int(response.status)
    except HTTPError as exc:
        return int(exc.code)
    except (OSError, URLError) as exc:
        raise RuntimeError(f"Local request failed: {url}") from exc


def run_smoke_test() -> int:
    """Check local binding, token enforcement, and packaged Workbench assets."""
    token = secrets.token_urlsafe(32)
    with TemporaryDirectory(prefix="ztf-classifier-desktop-") as directory:
        api = LocalApiServer(access_token=token, data_dir=Path(directory))
        try:
            port = api.start()
            base = f"http://{LOOPBACK_HOST}:{port}"
            if _request_status(f"{base}/health") != 200:
                raise RuntimeError("The health endpoint did not return HTTP 200.")
            if _request_status(f"{base}/v1/settings") != 401:
                raise RuntimeError("The API accepted an unauthenticated settings request.")
            if _request_status(f"{base}/v1/settings", token) != 200:
                raise RuntimeError("The API rejected the desktop session token.")
            if _request_status(f"{base}{WORKBENCH_PATH}") != 200:
                raise RuntimeError("The Workbench static page is unavailable.")
            print("Windows desktop shell smoke test passed.")
            return 0
        finally:
            api.stop()


def _show_startup_error(message: str) -> None:
    """Show an error dialog in a windowed build; print during development."""
    if platform.system() == "Windows":
        try:
            import ctypes

            ctypes.windll.user32.MessageBoxW(  # type: ignore[attr-defined]
                None,
                message,
                "ZTF Classifier",
                0x10,
            )
            return
        except (AttributeError, OSError):
            pass
    print(message, file=sys.stderr)


def run_desktop() -> int:
    """Launch the standalone Windows window and its private local API."""
    if platform.system() != "Windows":
        raise RuntimeError("The standalone desktop shell currently targets Windows.")

    try:
        import webview
    except ImportError as exc:
        raise RuntimeError(
            "Desktop components are missing. Reinstall the Windows desktop package."
        ) from exc

    token = secrets.token_urlsafe(32)
    api = LocalApiServer(access_token=token, data_dir=_application_data_dir())
    try:
        port = api.start()
        webview.create_window(
            title="ZTF Classifier",
            url=workbench_url(port, token),
            width=1440,
            height=900,
            min_size=(1024, 720),
            text_select=True,
        )
        webview.start(gui="edgechromium", debug=False)
        return 0
    finally:
        api.stop()


def main(argv: Sequence[str] | None = None) -> int:
    """Command-line entry point for the desktop app and Windows smoke test."""
    parser = argparse.ArgumentParser(prog="ztf-classifier-desktop")
    parser.add_argument(
        "--smoke-test",
        action="store_true",
        help="check loopback API, session-token enforcement, and Workbench assets",
    )
    args = parser.parse_args(argv)
    try:
        return run_smoke_test() if args.smoke_test else run_desktop()
    except Exception as exc:
        _show_startup_error(str(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
