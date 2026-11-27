from __future__ import annotations

import asyncio
import json
import sys
from collections.abc import Callable
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Self

import pytest
from fastapi import FastAPI

from ztf_classifier.api.app import create_app
from ztf_classifier.api.config import ApiSettings
from ztf_classifier.desktop import main as desktop_main
from ztf_classifier.desktop.main import (
    _build_splash_html,
    _get_desktop_asset_path,
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


def test_installed_version_reads_current_user_uninstall_entry() -> None:
    class FakeKey:
        def __enter__(self) -> Self:
            return self

        def __exit__(self, *args: object) -> None:
            return None

    class FakeRegistry:
        HKEY_CURRENT_USER = "HKCU"

        def __init__(self, value: str | None) -> None:
            self.value = value
            self.path = ""

        def OpenKey(self, hive: str, subkey: str) -> FakeKey:
            assert hive == "HKCU"
            self.path = subkey
            if self.value is None:
                raise OSError("Registry value not found")
            return FakeKey()

        def QueryValueEx(self, key: FakeKey, name: str) -> tuple[str, int]:
            assert name == "DisplayVersion"
            return str(self.value), 1

    registry = FakeRegistry("0.1.0-preview.4")
    assert desktop_main._read_installed_version(
        platform_name="nt", registry_module=registry
    ) == "0.1.0-preview.4"
    assert registry.path == (
        r"Software\Microsoft\Windows\CurrentVersion\Uninstall\ZTFClassifier"
    )
    assert desktop_main._read_installed_version(
        platform_name="nt", registry_module=FakeRegistry(None)
    ) is None
    assert desktop_main._read_installed_version(
        platform_name="linux", registry_module=registry
    ) is None


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
            message for message in messages if message["type"] == "http.response.start"
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
    assert 'rel="icon" href="./ztf-logo.svg" type="image/svg+xml"' in html
    assert 'rel="alternate icon" href="./ztf-logo.ico" type="image/x-icon"' in html
    assert 'src="./ztf-logo.svg"' in html
    assert "ZTF CLASSIFIER" in html
    assert "<script>" not in html
    assert 'document.documentElement.lang = "en"' in bootstrap
    assert 'document.documentElement.dir = "ltr"' in bootstrap
    assert "report_frontend_status" in bootstrap
    assert "unhandledrejection" in bootstrap

    for asset_name in ("index.html", "app.js", "desktop-bootstrap.js", "styles.css"):
        asset = (static_dir / asset_name).read_text(encoding="utf-8")
        assert not any("\u0600" <= char <= "\u06ff" for char in asset), asset_name

    css = (static_dir / "styles.css").read_text(encoding="utf-8")
    assert "direction: rtl" not in css

    installer = (
        Path(__file__).resolve().parents[1] / "packaging" / "windows" / "installer.nsi"
    ).read_text(encoding="utf-8")
    assert '!cd "..\\.."' in installer
    assert r'!define MUI_ICON "src\ztf_classifier\web\static\ztf-logo.ico"' in installer
    assert (
        r'!define MUI_UNICON "src\ztf_classifier\web\static\ztf-logo.ico"' in installer
    )
    assert (
        r'CreateShortcut "$DESKTOP\ZTF Classifier.lnk" "$INSTDIR\ZTFClassifier.exe" "" "$INSTDIR\ZTFClassifier.exe" 0'
        in installer
    )
    assert (
        r'CreateShortcut "$SMPROGRAMS\ZTF Classifier\ZTF Classifier.lnk" "$INSTDIR\ZTFClassifier.exe" "" "$INSTDIR\ZTFClassifier.exe" 0'
        in installer
    )
    assert (
        "File /oname=MicrosoftEdgeWebView2Setup.exe "
        '"packaging\\windows\\MicrosoftEdgeWebView2Setup.exe"'
    ) in installer
    assert '!insertmacro MUI_LANGUAGE "English"' in installer
    assert not any("\u0600" <= char <= "\u06ff" for char in installer)


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


def test_desktop_brand_assets_are_present_and_valid() -> None:
    splash_path = _get_desktop_asset_path("ztf-splash.PNG")
    icon_path = _get_desktop_asset_path("ztf-logo.ico")

    assert splash_path.is_file()
    assert icon_path.is_file()
    assert splash_path.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
    assert icon_path.read_bytes().startswith(b"\x00\x00\x01\x00")


def test_splash_placeholder_is_small_and_does_not_embed_assets() -> None:
    html = _build_splash_html()

    assert len(html.encode("utf-8")) < 2 * 1024 * 1024
    assert "data:image/png;base64," not in html
    assert "setSplashImageUrl" not in html
    assert "default-src 'none'" in html
    assert "Starting desktop services" in html


def test_static_splash_page_uses_same_origin_image() -> None:
    path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "ztf_classifier"
        / "web"
        / "static"
        / "desktop-splash.html"
    )
    html = path.read_text(encoding="utf-8")

    assert "img-src 'self'" in html
    assert 'src="ztf-splash.PNG"' in html
    assert "report_splash_status" in html
    assert "data:image/png;base64," not in html
    assert "window.updateStartupStatus" in html
    assert "report_splash_status" in html
    assert 'id="startup-close"' in html
    assert "close_splash" in html
    assert 'aria-live="polite"' in html
    assert "progress-sweep" in html
    assert "100% complete" not in html


def test_desktop_asset_path_uses_pyinstaller_bundle_root(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)

    assert _get_desktop_asset_path("ztf-splash.PNG") == (
        tmp_path / "ztf_classifier" / "web" / "static" / "ztf-splash.PNG"
    )


def test_splash_asset_validator_rejects_non_png_assets() -> None:
    with pytest.raises(ValueError, match="valid PNG"):
        desktop_main._validate_splash_asset(b"not-an-image")


def test_desktop_asset_path_rejects_unknown_names() -> None:
    with pytest.raises(ValueError, match="Unsupported desktop asset"):
        _get_desktop_asset_path("unexpected.txt")


def test_set_splash_status_uses_run_js_not_eval() -> None:
    calls: list[str] = []

    class FakeWindow:
        def run_js(self, script: str) -> None:
            calls.append(script)

        def evaluate_js(self, script: str) -> None:
            pytest.fail("evaluate_js must not be used under the strict splash CSP")

    desktop_main._set_splash_status(FakeWindow(), "API ready")
    assert len(calls) == 1
    assert "window.updateStartupStatus" in calls[0]
    assert "API ready" in calls[0]


def test_desktop_bridge_reports_frontend_errors(
    caplog: pytest.LogCaptureFixture,
) -> None:
    bridge = desktop_main.DesktopBridge("test-token")
    assert bridge.get_api_token() == "test-token"
    bridge.report_frontend_error("test frontend failure")
    bridge.report_frontend_status(
        {
            "title": "ZTF Classifier — Scientific Workbench",
            "app_root_present": True,
            "app_root_visible": True,
            "body_text_length": 100,
            "frontend_errors": [],
        }
    )
    assert bridge._frontend_status_event.is_set()
    assert bridge._frontend_status["app_root_visible"] is True
    assert "Workbench frontend error: test frontend failure" in caplog.text


def test_splash_bridge_reports_image_decode_status() -> None:
    class FakeWindow:
        destroyed = False

        def destroy(self) -> None:
            self.destroyed = True

    bridge = desktop_main.SplashBridge()
    fake_window = FakeWindow()
    bridge.bind_window(fake_window)
    bridge.close_splash()
    assert fake_window.destroyed

    bridge.report_splash_status(
        {
            "image_loaded": True,
            "natural_width": 1536,
            "natural_height": 864,
        }
    )
    assert bridge._image_status_event.is_set()
    assert bridge._image_status["image_loaded"] is True


@pytest.mark.parametrize(
    ("api_start_failure", "gui_smoke_test"),
    [(False, False), (True, False), (False, True)],
)
def test_main_starts_backend_from_webview_callback_and_hands_off_after_dom_ready(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    api_start_failure: bool,
    gui_smoke_test: bool,
) -> None:
    events: list[str] = []
    statuses: list[tuple[str, bool]] = []
    errors: list[str] = []

    class FakeEvent:
        def __init__(self) -> None:
            self.callbacks: list[Callable[..., Any]] = []

        def __iadd__(self, callback: Callable[..., Any]) -> Self:
            self.callbacks.append(callback)
            return self

        def fire(self, window: Any) -> None:
            for callback in tuple(self.callbacks):
                callback(window)

    class FakeWindow:
        def __init__(self) -> None:
            self.events = SimpleNamespace(
                closed=FakeEvent(),
                before_show=FakeEvent(),
                loaded=FakeEvent(),
            )
            self.destroyed = False
            self.shown = False
            self.bridge: Any | None = None
            self.scripts: list[str] = []

        def run_js(self, script: str) -> None:
            self.scripts.append(script)

        def load_url(self, url: str) -> None:
            self.loaded_url = url
            events.append("splash-page-loaded")
            if self.bridge is not None:
                self.bridge.report_splash_status(
                    {
                        "image_loaded": True,
                        "natural_width": 1536,
                        "natural_height": 864,
                    }
                )

        def show(self) -> None:
            self.shown = True
            self.events.before_show.fire(self)
            self.events.loaded.fire(self)
            if self.bridge is not None and hasattr(
                self.bridge, "report_frontend_status"
            ):
                self.bridge.report_frontend_status(
                    {
                        "title": "ZTF Classifier — Scientific Workbench",
                        "app_root_present": True,
                        "app_root_visible": True,
                        "body_text_length": 100,
                    }
                )

        def destroy(self) -> None:
            self.destroyed = True
            events.append("window-destroyed")

    class FakeWebview:
        def __init__(self) -> None:
            self.settings: dict[str, Any] = {}
            self.windows: list[FakeWindow] = []
            self.window_arguments: list[tuple[str, dict[str, Any]]] = []
            self.start_callback: Callable[..., Any] | None = None
            self.start_args: tuple[Any, ...] = ()

        def create_window(self, title: str, **kwargs: Any) -> FakeWindow:
            window = FakeWindow()
            window.bridge = kwargs.get("js_api")
            self.windows.append(window)
            self.window_arguments.append((title, kwargs))
            events.append(f"window-created:{title}")
            return window

        def start(
            self, func: Callable[..., Any], args: tuple[Any, ...], **kwargs: Any
        ) -> None:
            self.start_callback = func
            self.start_args = args
            self.start_arguments = kwargs
            splash_window = self.windows[0]
            splash_window.shown = True
            events.append("splash-shown")
            splash_window.events.loaded.fire(splash_window)
            func(*args)

    class FakeRuntime:
        def __init__(self, app: Any) -> None:
            self.app = app
            events.append("api-created")

        def start(self) -> str:
            events.append("api-started")
            if api_start_failure:
                raise RuntimeError("test API startup failed")
            return "http://127.0.0.1:43210"

        def stop(self) -> None:
            events.append("api-stopped")

    splash_asset = tmp_path / "ztf-splash.PNG"
    icon_asset = tmp_path / "ztf-logo.ico"
    splash_asset.write_bytes(bytes.fromhex("89504e470d0a1a0a") + b"fixture")
    icon_asset.write_bytes(bytes.fromhex("00000100") + b"fixture")
    assets = {"ztf-splash.PNG": splash_asset, "ztf-logo.ico": icon_asset}
    webview = FakeWebview()

    monkeypatch.setattr(desktop_main, "os", SimpleNamespace(name="nt"))
    monkeypatch.setattr(
        desktop_main.sys,
        "argv",
        ["ZTFClassifier.exe"] + (["--gui-smoke-test"] if gui_smoke_test else []),
    )
    monkeypatch.setattr(desktop_main, "_load_webview", lambda: webview)
    monkeypatch.setattr(
        desktop_main, "_get_desktop_asset_path", lambda name: assets[name]
    )
    monkeypatch.setattr(
        desktop_main, "get_user_data_dir", lambda: tmp_path / "user-data"
    )

    def fake_configure_logging(path: Path) -> Path:
        log_dir = path / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        return log_dir / "desktop.log"

    monkeypatch.setattr(
        desktop_main,
        "_configure_desktop_logging",
        fake_configure_logging,
    )
    monkeypatch.setattr(
        desktop_main,
        "build_desktop_settings",
        lambda token, data_dir: {"token": token, "data_dir": data_dir},
    )
    monkeypatch.setattr(
        desktop_main, "create_app", lambda settings, docs_enabled: object()
    )
    monkeypatch.setattr(desktop_main, "LocalApiServer", FakeRuntime)
    monkeypatch.setattr(
        desktop_main.secrets, "token_urlsafe", lambda length: "test-api-token"
    )
    monkeypatch.setattr(
        desktop_main,
        "_install_navigation_guard",
        lambda window, base_url: events.append("navigation-guard-installed"),
    )
    monkeypatch.setattr(
        desktop_main,
        "_set_splash_status",
        lambda window, message, failed=False: statuses.append((message, failed)),
    )
    monkeypatch.setattr(
        desktop_main, "_show_error", lambda message: errors.append(message)
    )

    desktop_main.main()

    assert not errors
    assert webview.start_callback is not None
    assert webview.start_args[0] is webview.windows[0]
    assert events.index("splash-shown") < events.index("api-started")
    assert statuses[0][0].startswith("Preparing local workspace")
    assert statuses[1][0].startswith("Starting the private local API")
    assert webview.start_arguments["gui"] == "edgechromium"

    splash_window = webview.windows[0]
    assert webview.window_arguments[0][1]["html"].startswith("<!doctype html>")
    assert webview.window_arguments[0][1]["frameless"] is False
    assert webview.window_arguments[0][1]["on_top"] is False
    assert webview.window_arguments[0][1]["js_api"] is not None

    if api_start_failure:
        assert len(webview.windows) == 1
        assert not splash_window.destroyed
        assert statuses[-1][0].startswith("Startup failed: RuntimeError")
        assert statuses[-1][1] is True
    else:
        assert len(webview.windows) == 2
        main_window = webview.windows[1]
        assert webview.window_arguments[1][1]["hidden"] is True
        assert main_window.shown
        assert splash_window.destroyed
        assert splash_window.loaded_url == (
            "http://127.0.0.1:43210/workbench/desktop-splash.html"
        )
        assert "splash-page-loaded" in events
        assert statuses[-1][0].startswith("Local services are ready")
        assert statuses[-1][1] is False
        if gui_smoke_test:
            assert main_window.destroyed
            report_path = (
                tmp_path / "user-data" / "logs" / "desktop-gui-smoke-test.json"
            )
            report = json.loads(report_path.read_text(encoding="utf-8"))
            assert report["status"] == "PASS"
            assert report["checks"]["splash_image_loaded"] is True
        else:
            assert not main_window.destroyed

    assert events.count("api-stopped") == 1
