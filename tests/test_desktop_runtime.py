from __future__ import annotations

import asyncio
from collections.abc import Callable
from pathlib import Path
from typing import Any, Self

import pytest
from fastapi import FastAPI

from ztf_classifier.api.app import create_app
from ztf_classifier.api.config import ApiSettings
from ztf_classifier.desktop.main import (
    _install_navigation_guard,
    _is_trusted_local_url,
    _is_webview2_runtime_installed,
)
from ztf_classifier.desktop.runtime import (
    DesktopRuntimeError,
    LocalApiServer,
    build_desktop_settings,
    get_user_data_dir,
)
from ztf_classifier.validation.runner import _peak_rss_mb


def test_user_data_directory_uses_explicit_windows_location(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))

    assert get_user_data_dir(platform_name="nt") == tmp_path / "ZTFClassifier"


def test_webview2_runtime_detection_checks_machine_and_user_registry() -> None:
    class FakeKey:
        def __init__(self, value: str) -> None:
            self.value = value

        def __enter__(self) -> Self:
            return self

        def __exit__(self, *args: object) -> None:
            return None

    class FakeRegistry:
        HKEY_LOCAL_MACHINE = "HKLM"
        HKEY_CURRENT_USER = "HKCU"

        def __init__(self, values: dict[tuple[str, str], str]) -> None:
            self.values = values

        def OpenKey(self, hive: str, subkey: str) -> FakeKey:
            try:
                return FakeKey(self.values[(hive, subkey)])
            except KeyError as exc:
                raise OSError("Registry value not found") from exc

        @staticmethod
        def QueryValueEx(key: FakeKey, name: str) -> tuple[str, int]:
            assert name == "pv"
            return key.value, 1

    client_id = "{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}"
    user_key = rf"Software\Microsoft\EdgeUpdate\Clients\{client_id}"
    installed = FakeRegistry({("HKCU", user_key): "126.0.0.0"})
    missing = FakeRegistry({})

    assert _is_webview2_runtime_installed(platform_name="nt", registry_module=installed)
    assert not _is_webview2_runtime_installed(
        platform_name="nt", registry_module=missing
    )
    assert not _is_webview2_runtime_installed(
        platform_name="linux", registry_module=installed
    )


def test_build_desktop_settings_uses_per_user_storage(
    tmp_path: Path,
) -> None:
    token = "test-only-session-token"
    base = ApiSettings(
        observation_cache_dir=Path("old-cache"),
        job_store_path=Path("old-jobs.sqlite3"),
        result_store_path=Path("old-results.sqlite3"),
        application_state_path=Path("old-settings.json"),
        scientific_evidence_dir=Path("old-reports"),
    )

    settings = build_desktop_settings(
        token,
        data_dir=tmp_path / "user-data",
        base_settings=base,
    )

    assert settings.api_key == token
    assert settings.observation_cache_dir == tmp_path / "user-data/cache/observations"
    assert settings.job_store_path == tmp_path / "user-data/jobs/jobs.sqlite3"
    assert settings.result_store_path == tmp_path / "user-data/results/results.sqlite3"
    assert (
        settings.application_state_path == tmp_path / "user-data/settings/settings.json"
    )
    assert settings.scientific_evidence_dir == (
        tmp_path / "user-data/reports/scientific_validation"
    )
    assert all(
        path.exists()
        for path in (
            settings.observation_cache_dir,
            settings.job_store_path.parent,
            settings.result_store_path.parent,
            settings.application_state_path.parent,
            settings.scientific_evidence_dir,
        )
    )


def test_build_desktop_settings_requires_a_token(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="token"):
        build_desktop_settings("", data_dir=tmp_path)


def test_desktop_api_requires_session_bearer_token(tmp_path: Path) -> None:
    token = "desktop-test-session-token"
    settings = ApiSettings(
        observation_cache_dir=tmp_path / "cache",
        job_store_path=tmp_path / "jobs.sqlite3",
        result_store_path=tmp_path / "results.sqlite3",
        application_state_path=tmp_path / "settings.json",
        api_key=token,
        scientific_registry_dir=tmp_path / "benchmarks",
        scientific_evidence_dir=tmp_path / "evidence",
    )
    app = create_app(settings=settings, docs_enabled=False)

    async def get_response(
        path: str,
        authorization: str | None = None,
    ) -> tuple[int, dict[str, str]]:
        messages: list[dict[str, Any]] = []
        request_headers = (
            [(b"authorization", authorization.encode("ascii"))] if authorization else []
        )

        request_sent = False

        async def receive() -> dict[str, Any]:
            nonlocal request_sent
            if not request_sent:
                request_sent = True
                return {"type": "http.request", "body": b"", "more_body": False}
            return {"type": "http.disconnect"}

        async def send(message: dict[str, Any]) -> None:
            messages.append(message)

        scope = {
            "type": "http",
            "asgi": {"version": "3.0"},
            "http_version": "1.1",
            "method": "GET",
            "scheme": "http",
            "path": path,
            "raw_path": path.encode("ascii"),
            "query_string": b"",
            "root_path": "",
            "headers": request_headers,
            "client": ("127.0.0.1", 12345),
            "server": ("127.0.0.1", 43127),
        }
        await app(scope, receive, send)
        start = next(
            message
            for message in messages
            if message["type"] == "http.response.start"
        )
        response_headers = {
            key.decode("latin-1").lower(): value.decode("latin-1")
            for key, value in start["headers"]
        }
        return start["status"], response_headers

    health_status, health_headers = asyncio.run(get_response("/health"))
    assert health_status == 200
    assert health_headers["x-content-type-options"] == "nosniff"
    assert health_headers["referrer-policy"] == "no-referrer"
    assert health_headers["x-frame-options"] == "DENY"

    assert asyncio.run(get_response("/docs"))[0] == 404
    assert asyncio.run(get_response("/redoc"))[0] == 404
    assert asyncio.run(get_response("/openapi.json"))[0] == 404

    assert asyncio.run(get_response("/v1/settings"))[0] == 401
    assert asyncio.run(get_response("/v1/settings", f"Bearer {token}"))[0] == 200


def test_api_docs_remain_enabled_by_default(tmp_path: Path) -> None:
    settings = ApiSettings(
        observation_cache_dir=tmp_path / "cache",
        job_store_path=tmp_path / "jobs.sqlite3",
        result_store_path=tmp_path / "results.sqlite3",
        application_state_path=tmp_path / "settings.json",
        scientific_registry_dir=tmp_path / "benchmarks",
        scientific_evidence_dir=tmp_path / "evidence",
    )
    app = create_app(settings=settings)
    route_paths = {getattr(route, "path", None) for route in app.routes}

    assert {"/docs", "/redoc", "/openapi.json"} <= route_paths


def test_desktop_workbench_uses_external_bootstrap_and_csp() -> None:
    static_dir = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "ztf_classifier"
        / "web"
        / "static"
    )
    html = (static_dir / "index.html").read_text(encoding="utf-8")
    bootstrap = (static_dir / "desktop-bootstrap.js").read_text(encoding="utf-8")

    assert "Content-Security-Policy" in html
    assert "script-src 'self'" in html
    assert "connect-src 'self'" in html
    assert 'src="./desktop-bootstrap.js"' in html
    assert "<script>" not in html
    assert 'document.documentElement.dir = "rtl"' in bootstrap


def test_validation_runner_peak_memory_measurement_is_portable() -> None:
    assert _peak_rss_mb() > 0.0


def test_local_api_rejects_non_loopback_host() -> None:
    with pytest.raises(ValueError, match="loopback"):
        LocalApiServer(FastAPI(), host="0.0.0.0")


def test_local_api_starts_on_dynamic_loopback_port_and_stops() -> None:
    app = FastAPI()

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    runtime = LocalApiServer(app, startup_timeout=5, shutdown_timeout=5)
    base_url = runtime.start()

    try:
        assert runtime.is_running
        assert base_url.startswith("http://127.0.0.1:")
        assert 0 < runtime.port < 65536
    finally:
        runtime.stop()

    assert not runtime.is_running


def test_local_api_surfaces_unexpected_worker_exception(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FailingServer:
        def __init__(self, config: object) -> None:
            self.should_exit = False
            self.force_exit = False

        def run(self, sockets: list[object]) -> None:
            raise KeyError("unexpected worker failure")

    monkeypatch.setattr(
        "ztf_classifier.desktop.runtime.uvicorn.Server",
        FailingServer,
    )
    runtime = LocalApiServer(FastAPI(), startup_timeout=2, shutdown_timeout=1)

    with pytest.raises(DesktopRuntimeError) as error:
        runtime.start()

    assert isinstance(error.value.__cause__, KeyError)
    assert not runtime.is_running


def test_trusted_local_url_requires_exact_loopback_origin() -> None:
    base_url = "http://127.0.0.1:43127"

    assert _is_trusted_local_url(f"{base_url}/workbench/", base_url)
    assert _is_trusted_local_url(f"{base_url}/v1/settings?x=1", base_url)
    assert not _is_trusted_local_url("https://127.0.0.1:43127/workbench/", base_url)
    assert not _is_trusted_local_url("http://localhost:43127/workbench/", base_url)
    assert not _is_trusted_local_url("http://127.0.0.1:43128/workbench/", base_url)
    assert not _is_trusted_local_url("http://127.0.0.1.evil.test:43127/", base_url)
    assert not _is_trusted_local_url("http://user@127.0.0.1:43127/", base_url)
    assert not _is_trusted_local_url("http://127.0.0.1:bad/", base_url)


def test_native_navigation_guard_blocks_external_navigation() -> None:
    class FakeEvent:
        def __init__(self) -> None:
            self.handlers: list[Callable[..., None]] = []

        def __iadd__(self, handler: Callable[..., None]) -> Self:
            self.handlers.append(handler)
            return self

        def fire(self, sender: Any, args: Any) -> None:
            for handler in self.handlers:
                handler(sender, args)

    class FakeCore:
        def __init__(self) -> None:
            self.FrameNavigationStarting = FakeEvent()
            self.LaunchingExternalUriScheme = FakeEvent()
            self.NewWindowRequested = FakeEvent()

    class FakeControl:
        def __init__(self) -> None:
            self.NavigationStarting = FakeEvent()
            self.CoreWebView2InitializationCompleted = FakeEvent()
            self.CoreWebView2 = None

    class FakeWindow:
        def __init__(self) -> None:
            self.native = type("Native", (), {"webview": FakeControl()})()

    window = FakeWindow()
    base_url = "http://127.0.0.1:43127"
    _install_navigation_guard(window, base_url)

    allowed = type("Args", (), {"Uri": f"{base_url}/workbench/", "Cancel": False})()
    window.native.webview.NavigationStarting.fire(window.native.webview, allowed)
    assert allowed.Cancel is False

    blocked = type("Args", (), {"Uri": "https://example.com/", "Cancel": False})()
    window.native.webview.NavigationStarting.fire(window.native.webview, blocked)
    assert blocked.Cancel is True

    core = FakeCore()
    window.native.webview.CoreWebView2 = core
    initialized = type("InitArgs", (), {"IsSuccess": True})()
    window.native.webview.CoreWebView2InitializationCompleted.fire(
        window.native.webview,
        initialized,
    )

    frame = type("Args", (), {"Uri": "https://example.com/frame", "Cancel": False})()
    core.FrameNavigationStarting.fire(core, frame)
    assert frame.Cancel is True

    external_scheme = type(
        "Args", (), {"Uri": "mailto:test@example.com", "Cancel": False}
    )()
    core.LaunchingExternalUriScheme.fire(core, external_scheme)
    assert external_scheme.Cancel is True

    new_window = type(
        "Args", (), {"Uri": "https://example.com/new-window", "Handled": False}
    )()
    core.NewWindowRequested.fire(core, new_window)
    assert new_window.Handled is True
    assert len(window._ztf_navigation_handlers) == 4


def test_local_api_requires_ready_health_endpoint() -> None:
    app = FastAPI()

    @app.get("/not-health")
    def not_health() -> dict[str, str]:
        return {"status": "ok"}

    runtime = LocalApiServer(app, startup_timeout=0.25, shutdown_timeout=5)
    with pytest.raises(DesktopRuntimeError, match="did not become ready"):
        runtime.start()
    assert not runtime.is_running
