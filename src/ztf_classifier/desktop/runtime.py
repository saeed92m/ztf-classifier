"""Managed loopback API runtime for the Windows desktop shell.

This module does not launch a browser or import pywebview. It can be tested
independently from the Windows GUI runtime.
"""

from __future__ import annotations

import os
import socket
import sys
import threading
import time
from dataclasses import replace
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import urlopen

import uvicorn

from ztf_classifier.api.config import ApiSettings


class DesktopRuntimeError(RuntimeError):
    """Raised when the managed local API cannot start or stop safely."""


def get_user_data_dir(app_name: str = "ZTFClassifier") -> Path:
    """Return the per-user application data directory."""
    if os.name == "nt":
        root = os.environ.get("LOCALAPPDATA") or (Path.home() / "AppData" / "Local")
        return Path(root).expanduser() / app_name

    root = os.environ.get("XDG_DATA_HOME")
    if root:
        return Path(root).expanduser() / app_name
    return Path.home() / ".local" / "share" / app_name


def get_application_resource_dir() -> Path:
    """Return the bundled resource root or the source checkout root."""
    bundle_root = getattr(sys, "_MEIPASS", None)
    if bundle_root:
        return Path(bundle_root).resolve()
    return Path(__file__).resolve().parents[3]


def build_desktop_settings(
    api_token: str,
    *,
    data_dir: Path | None = None,
    base_settings: ApiSettings | None = None,
) -> ApiSettings:
    """Create isolated, authenticated settings for a desktop session."""
    if not api_token or not api_token.strip():
        raise ValueError("A non-empty desktop API token is required.")

    root = (data_dir or get_user_data_dir()).expanduser().resolve()
    directories = {
        "cache": root / "cache" / "observations",
        "jobs": root / "jobs",
        "results": root / "results",
        "state": root / "settings",
        "reports": root / "reports" / "scientific_validation",
    }
    for directory in directories.values():
        directory.mkdir(parents=True, exist_ok=True)

    base = base_settings or ApiSettings.from_environment()
    benchmark_registry = get_application_resource_dir() / "configs" / "benchmarks"
    registry_dir = (
        benchmark_registry
        if benchmark_registry.is_dir()
        else base.scientific_registry_dir
    )

    return replace(
        base,
        observation_cache_dir=directories["cache"],
        job_store_path=directories["jobs"] / "jobs.sqlite3",
        result_store_path=directories["results"] / "results.sqlite3",
        application_state_path=directories["state"] / "settings.json",
        api_key=api_token,
        scientific_registry_dir=registry_dir,
        scientific_evidence_dir=directories["reports"],
    )


class LocalApiServer:
    """Run the FastAPI application on a private, dynamically selected port."""

    def __init__(
        self,
        app: Any,
        *,
        host: str = "127.0.0.1",
        startup_timeout: float = 15.0,
        shutdown_timeout: float = 10.0,
    ) -> None:
        if host not in {"127.0.0.1", "::1"}:
            raise ValueError("Desktop API must bind to a loopback address.")
        if startup_timeout <= 0 or shutdown_timeout <= 0:
            raise ValueError("Runtime timeouts must be positive.")

        self._app = app
        self._host = host
        self._startup_timeout = startup_timeout
        self._shutdown_timeout = shutdown_timeout
        self._socket: socket.socket | None = None
        self._server: uvicorn.Server | None = None
        self._thread: threading.Thread | None = None
        self._thread_error: BaseException | None = None
        self._lock = threading.RLock()
        self._port: int | None = None

    @property
    def host(self) -> str:
        return self._host

    @property
    def port(self) -> int:
        if self._port is None:
            raise DesktopRuntimeError("Local API has not started.")
        return self._port

    @property
    def base_url(self) -> str:
        return f"http://{self._host}:{self.port}"

    @property
    def is_running(self) -> bool:
        return bool(self._thread and self._thread.is_alive())

    def start(self) -> str:
        """Bind a local socket, start Uvicorn and wait for /health."""
        with self._lock:
            if self.is_running:
                return self.base_url

            self._thread_error = None
            local_socket = socket.socket(
                socket.AF_INET6 if ":" in self._host else socket.AF_INET,
                socket.SOCK_STREAM,
            )
            try:
                if os.name == "nt" and hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
                    local_socket.setsockopt(
                        socket.SOL_SOCKET,
                        socket.SO_EXCLUSIVEADDRUSE,
                        1,
                    )
                local_socket.bind((self._host, 0))
                local_socket.listen(socket.SOMAXCONN)
                self._port = int(local_socket.getsockname()[1])

                config = uvicorn.Config(
                    self._app,
                    host=self._host,
                    port=self._port,
                    log_level="warning",
                    access_log=False,
                    lifespan="on",
                )
                server = uvicorn.Server(config)
                self._socket = local_socket
                self._server = server

                def serve() -> None:
                    try:
                        server.run(sockets=[local_socket])
                    except Exception as exc:  # captured for the controlling thread
                        self._thread_error = exc

                self._thread = threading.Thread(
                    target=serve,
                    name="ztf-classifier-local-api",
                    daemon=True,
                )
                self._thread.start()
            except Exception:
                local_socket.close()
                self._socket = None
                self._server = None
                self._thread = None
                self._port = None
                raise

        deadline = time.monotonic() + self._startup_timeout
        health_url = f"{self.base_url}/health"
        last_error: Exception | None = None
        while time.monotonic() < deadline:
            if not self.is_running:
                error = self._thread_error
                self.stop()
                raise DesktopRuntimeError(
                    "Local API process stopped before it became ready."
                ) from error
            try:
                with urlopen(health_url, timeout=0.5) as response:
                    if response.status == 200:
                        return self.base_url
                    last_error = DesktopRuntimeError(
                        f"Unexpected health status: {response.status}"
                    )
            except (OSError, URLError) as exc:
                last_error = exc
            time.sleep(0.1)

        self.stop()
        raise DesktopRuntimeError(
            f"Local API did not become ready within {self._startup_timeout:g}s."
        ) from last_error

    def stop(self) -> None:
        """Ask Uvicorn to stop, join its thread and release the socket."""
        with self._lock:
            server = self._server
            thread = self._thread
            local_socket = self._socket

            if server is not None:
                server.should_exit = True

        if thread is not None and thread.is_alive():
            thread.join(timeout=self._shutdown_timeout)
            if thread.is_alive() and server is not None:
                server.force_exit = True
                thread.join(timeout=2.0)

        if thread is not None and thread.is_alive():
            raise DesktopRuntimeError(
                "Local API did not stop cleanly; its worker thread is still active."
            )

        if local_socket is not None:
            try:
                local_socket.close()
            except OSError:
                pass

        with self._lock:
            self._socket = None
            self._server = None
            self._thread = None
            self._port = None

