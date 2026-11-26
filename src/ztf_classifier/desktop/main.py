"""Windows desktop entry point for the ZTF Classifier Workbench."""

from __future__ import annotations

import base64
import ctypes
import json
import os
import secrets
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from ztf_classifier.api.app import create_app
from ztf_classifier.desktop.runtime import (
    LocalApiServer,
    build_desktop_settings,
    get_user_data_dir,
)


class DesktopBridge:
    """Expose only the session API token to the trusted local Workbench."""

    def __init__(self, api_token: str) -> None:
        self._api_token = api_token

    def get_api_token(self) -> str:
        """Return the in-memory token to the local desktop WebView."""
        return self._api_token


def _get_desktop_asset_path(asset_name: str) -> Path:
    """Return a path to a bundled desktop asset with a fixed allowlist."""
    allowed_assets = {"ztf-splash.PNG", "ztf-logo.ico"}
    if asset_name not in allowed_assets:
        raise ValueError(f"Unsupported desktop asset: {asset_name}")
    return Path(__file__).resolve().parents[1] / "web" / "static" / asset_name


def _build_splash_html(splash_image: bytes) -> str:
    """Build a self-contained splash page with an indeterminate progress bar."""
    png_signature = b"\x89PNG\r\n\x1a\n"
    if not splash_image.startswith(png_signature):
        raise ValueError("The desktop splash asset is not a valid PNG file.")

    encoded_image = base64.b64encode(splash_image).decode("ascii")
    template = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta http-equiv="Content-Security-Policy"
        content="default-src 'none'; img-src data:; style-src 'unsafe-inline'; script-src 'unsafe-inline'; base-uri 'none'; form-action 'none'; object-src 'none'">
  <title>ZTF Classifier — Starting</title>
  <style>
    * { box-sizing: border-box; }
    html, body { width: 100%; height: 100%; margin: 0; overflow: hidden; background: #030b19; }
    body { position: relative; color: #f8fbff; font-family: "Segoe UI", Arial, sans-serif; }
    .mission-art { display: block; width: 100%; height: 100%; object-fit: contain; }
    .startup-panel {
      position: absolute; left: 23.5%; right: 23.5%; top: 51.5%; height: 13%;
      display: flex; flex-direction: column; justify-content: center; gap: 13px;
      padding: 6px 10px; border-radius: 8px;
      background: rgba(2, 10, 27, .94);
    }
    .startup-status {
      min-height: 22px; display: flex; align-items: center; justify-content: center;
      text-align: center; font-size: clamp(11px, 2vw, 16px); line-height: 1.3;
      overflow-wrap: anywhere;
    }
    .progress-track {
      height: 7px; width: 100%; overflow: hidden; border: 1px solid #27b7ef;
      border-radius: 99px; background: #071a35;
    }
    .progress-indicator {
      display: block; width: 28%; height: 100%; border-radius: inherit;
      background: linear-gradient(90deg, #087de0, #31d7ff, #087de0);
      animation: progress-sweep 1.6s ease-in-out infinite alternate;
    }
    .progress-track.failed { border-color: #f87171; }
    .progress-track.failed .progress-indicator { display: none; }
    .startup-hint {
      display: none; color: #fca5a5; font-size: 11px; line-height: 1.35;
      text-align: center;
    }
    .startup-hint.visible { display: block; }
    @keyframes progress-sweep {
      from { transform: translateX(-105%); }
      to { transform: translateX(360%); }
    }
    @media (prefers-reduced-motion: reduce) {
      .progress-indicator { animation: none; transform: translateX(120%); }
    }
  </style>
</head>
<body>
  <img class="mission-art" src="data:image/png;base64,__SPLASH_IMAGE__" alt="">
  <section class="startup-panel" aria-label="Application startup">
    <div id="startup-status" class="startup-status" role="status" aria-live="polite">
      Preparing desktop session…
    </div>
    <div id="startup-progress" class="progress-track" aria-label="Startup in progress">
      <span class="progress-indicator"></span>
    </div>
    <div id="startup-hint" class="startup-hint">
      Close this window and restart ZTF Classifier.
    </div>
  </section>
  <script>
    window.updateStartupStatus = function (message, failed) {
      document.getElementById("startup-status").textContent = String(message);
      document.getElementById("startup-progress").classList.toggle("failed", Boolean(failed));
      document.getElementById("startup-hint").classList.toggle("visible", Boolean(failed));
    };
  </script>
</body>
</html>
"""
    return template.replace("__SPLASH_IMAGE__", encoded_image)


def _set_splash_status(window: Any, message: str, *, failed: bool = False) -> None:
    """Update the splash status without inserting untrusted HTML."""
    status = json.dumps(message)
    failure_state = "true" if failed else "false"
    window.evaluate_js(
        f"window.updateStartupStatus({status}, {failure_state});"
    )


def _show_error(message: str) -> None:
    if os.name == "nt":
        ctypes.windll.user32.MessageBoxW(
            None,
            message,
            "ZTF Classifier",
            0x10,
        )
    else:
        print(message, file=sys.stderr)


def _load_webview() -> Any:
    try:
        import webview
    except ImportError as exc:
        raise RuntimeError(
            "Windows desktop support is not installed. "
            'Install the "desktop-windows" extra and try again.'
        ) from exc
    if not _is_webview2_runtime_installed():
        raise RuntimeError(
            "Microsoft Edge WebView2 Runtime is not installed. "
            "Install the Evergreen Runtime from "
            "https://developer.microsoft.com/microsoft-edge/webview2/ "
            "and restart ZTF Classifier."
        )
    return webview


def _is_trusted_local_url(candidate: str, base_url: str) -> bool:
    """Accept only the exact loopback origin owned by this desktop session."""
    try:
        candidate_parts = urlsplit(candidate)
        base_parts = urlsplit(base_url)
        return (
            base_parts.scheme == "http"
            and base_parts.hostname in {"127.0.0.1", "::1"}
            and candidate_parts.scheme == base_parts.scheme
            and candidate_parts.hostname == base_parts.hostname
            and candidate_parts.port == base_parts.port
            and candidate_parts.username is None
            and candidate_parts.password is None
        )
    except ValueError:
        return False


def _install_navigation_guard(window: Any, base_url: str) -> None:
    """Block non-session navigation at the native WebView2 event boundary."""
    control = getattr(window.native, "webview", None)
    if control is None:
        raise RuntimeError("The native WebView2 control is not available.")

    def block_untrusted_navigation(sender: Any, args: Any) -> None:
        if not _is_trusted_local_url(str(args.Uri), base_url):
            args.Cancel = True

    def block_external_uri_scheme(sender: Any, args: Any) -> None:
        args.Cancel = True

    def block_new_window(sender: Any, args: Any) -> None:
        args.Handled = True

    handlers: list[Callable[..., None]] = [
        block_untrusted_navigation,
        block_external_uri_scheme,
        block_new_window,
    ]

    def attach_core_handlers(core: Any) -> None:
        if core is None:
            raise RuntimeError("The WebView2 core is not initialized.")
        core.FrameNavigationStarting += block_untrusted_navigation
        core.LaunchingExternalUriScheme += block_external_uri_scheme
        core.NewWindowRequested += block_new_window

    def on_core_initialized(sender: Any, args: Any) -> None:
        if args.IsSuccess:
            attach_core_handlers(sender.CoreWebView2)

    control.NavigationStarting += block_untrusted_navigation

    core = control.CoreWebView2
    if core is None:
        control.CoreWebView2InitializationCompleted += on_core_initialized
        handlers.append(on_core_initialized)
    else:
        attach_core_handlers(core)

    # Keep Python delegates alive for the lifetime of the native .NET events.
    window._ztf_navigation_handlers = handlers


def _is_webview2_runtime_installed(
    *,
    platform_name: str | None = None,
    registry_module: Any | None = None,
) -> bool:
    """Check the Evergreen WebView2 Runtime registry values."""
    if (platform_name or os.name) != "nt":
        return False

    if registry_module is None:
        try:
            import winreg as registry_module
        except ImportError:
            return False

    client_id = "{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}"
    locations = (
        (
            registry_module.HKEY_LOCAL_MACHINE,
            rf"SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\{client_id}",
        ),
        (
            registry_module.HKEY_CURRENT_USER,
            rf"Software\Microsoft\EdgeUpdate\Clients\{client_id}",
        ),
    )
    for hive, subkey in locations:
        try:
            with registry_module.OpenKey(hive, subkey) as registry_key:
                version, _ = registry_module.QueryValueEx(registry_key, "pv")
            if isinstance(version, str) and version not in {"", "0.0.0.0"}:
                return True
        except OSError:
            continue
    return False


def _run_self_test() -> None:
    """Verify the frozen app, WebView2 runtime, API and static Workbench."""
    user_data = get_user_data_dir()
    report_path = user_data / "logs" / "desktop-self-test.json"
    checks: dict[str, str] = {}
    error: str | None = None
    runtime: LocalApiServer | None = None

    try:
        webview = _load_webview()
        if not hasattr(webview, "create_window"):
            raise RuntimeError("The packaged pywebview module is incomplete.")
        checks["pywebview_and_webview2_runtime"] = "PASS"

        token = secrets.token_urlsafe(32)
        settings = build_desktop_settings(token, data_dir=user_data)
        registry_dir = settings.scientific_registry_dir
        if not registry_dir.is_dir() or not any(registry_dir.glob("*.json")):
            raise RuntimeError("The packaged benchmark registry is missing.")
        checks["benchmark_registry"] = "PASS"

        runtime = LocalApiServer(create_app(settings=settings, docs_enabled=False))
        base_url = runtime.start()
        checks["local_api_health"] = "PASS"

        for path in (
            "/workbench/",
            "/workbench/app.js",
            "/workbench/desktop-bootstrap.js",
            "/workbench/styles.css",
            "/workbench/ztf-splash.PNG",
            "/workbench/ztf-logo.ico",
        ):
            with urlopen(f"{base_url}{path}", timeout=5) as response:
                if response.status != 200:
                    raise RuntimeError(f"Unexpected HTTP status for {path}.")
                body = response.read()
                if path == "/workbench/" and (
                    b"DR24 Explorer" not in body
                    or b"desktop-bootstrap.js" not in body
                    or b'./ztf-logo.ico' not in body
                    or b"Content-Security-Policy" not in body
                ):
                    raise RuntimeError(
                        "The packaged desktop Workbench HTML is incomplete."
                    )
                if path == "/workbench/app.js" and b"desktop-home" not in body:
                    raise RuntimeError(
                        "The packaged desktop Workbench script is incomplete."
                    )
                if (
                    path == "/workbench/styles.css"
                    and b"data-desktop-preview" not in body
                ):
                    raise RuntimeError(
                        "The packaged desktop Workbench styles are incomplete."
                    )
                if path == "/workbench/ztf-splash.PNG" and not body.startswith(
                    b"\x89PNG\r\n\x1a\n"
                ):
                    raise RuntimeError("The packaged desktop splash image is invalid.")
                if path == "/workbench/ztf-logo.ico" and not body.startswith(
                    b"\x00\x00\x01\x00"
                ):
                    raise RuntimeError("The packaged desktop icon is invalid.")
            checks[f"static:{path}"] = "PASS"

        for path in ("/docs", "/redoc", "/openapi.json"):
            try:
                with urlopen(f"{base_url}{path}", timeout=5):
                    raise RuntimeError(
                        f"Desktop API documentation remained enabled: {path}"
                    )
            except HTTPError as exc:
                if exc.code != 404:
                    raise
            checks[f"api_docs_disabled:{path}"] = "PASS"

        try:
            with urlopen(f"{base_url}/v1/settings", timeout=5):
                raise RuntimeError("The local API accepted a request without a token.")
        except HTTPError as exc:
            if exc.code != 401:
                raise
        checks["api_rejects_missing_token"] = "PASS"

        request = Request(
            f"{base_url}/v1/settings",
            headers={"Authorization": f"Bearer {token}"},
        )
        with urlopen(request, timeout=5) as response:
            if response.status != 200:
                raise RuntimeError("The local API rejected its session token.")
        checks["api_accepts_session_token"] = "PASS"
    except Exception as exc:  # noqa: BLE001 - capture startup failure for the self-test report
        error = f"{type(exc).__name__}: {exc}"
    finally:
        if runtime is not None:
            try:
                runtime.stop()
                checks["local_api_shutdown"] = "PASS"
            except Exception as exc:  # noqa: BLE001 - record shutdown failure in the self-test report
                error = error or f"{type(exc).__name__}: {exc}"
                checks["local_api_shutdown"] = "FAIL"

        report_path.parent.mkdir(parents=True, exist_ok=True)
        report = {
            "schema_version": "ztf-desktop-self-test-v1",
            "status": "FAIL" if error else "PASS",
            "checks": checks,
            "error": error,
        }
        report_path.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    if error:
        raise SystemExit(1)


def main() -> None:
    """Start the private API, then open the standalone Windows window."""
    if os.name != "nt":
        raise SystemExit("The first desktop preview supports Windows only.")
    if "--self-test" in sys.argv[1:]:
        _run_self_test()
        return

    runtime: LocalApiServer | None = None
    try:
        webview = _load_webview()
        webview.settings["ALLOW_DOWNLOADS"] = True
        webview.settings["ALLOW_FILE_URLS"] = False
        webview.settings["OPEN_EXTERNAL_LINKS_IN_BROWSER"] = False
        webview.settings["OPEN_DEVTOOLS_IN_DEBUG"] = False
        webview.settings["REMOTE_DEBUGGING_PORT"] = None

        user_data = get_user_data_dir()
        splash_image = _get_desktop_asset_path("ztf-splash.PNG").read_bytes()
        icon_path = _get_desktop_asset_path("ztf-logo.ico")
        if not icon_path.is_file() or not icon_path.read_bytes().startswith(
            b"\x00\x00\x01\x00"
        ):
            raise RuntimeError(
                "The packaged ZTF Classifier application icon is missing or invalid."
            )

        splash_window = webview.create_window(
            "ZTF Classifier",
            html=_build_splash_html(splash_image),
            width=768,
            height=512,
            min_size=(768, 512),
            resizable=False,
            frameless=True,
            easy_drag=True,
            shadow=True,
            on_top=True,
            background_color="#030b19",
            text_select=False,
            zoomable=False,
        )

        def start_desktop_session(current_window: Any) -> None:
            nonlocal runtime
            try:
                _set_splash_status(
                    splash_window,
                    "Preparing local workspace and application settings…",
                )
                token = secrets.token_urlsafe(32)
                settings = build_desktop_settings(token, data_dir=user_data)
                app = create_app(settings=settings, docs_enabled=False)

                _set_splash_status(
                    splash_window,
                    "Starting the private local API and checking readiness…",
                )
                runtime = LocalApiServer(app)
                base_url = runtime.start()

                _set_splash_status(
                    splash_window,
                    "Local services are ready. Opening the Workbench…",
                )
                window = webview.create_window(
                    "ZTF Classifier — Scientific Workbench",
                    url=f"{base_url}/workbench/?desktop=1",
                    js_api=DesktopBridge(token),
                    width=1360,
                    height=900,
                    min_size=(1024, 700),
                    resizable=True,
                    text_select=True,
                    zoomable=False,
                    hidden=True,
                )
                if window is None:
                    raise RuntimeError("The Workbench window could not be created.")

                window.events.closed += runtime.stop

                def install_navigation_guard(current_window: Any) -> None:
                    _install_navigation_guard(current_window, base_url)

                def dismiss_splash(current_window: Any) -> None:
                    try:
                        splash_window.destroy()
                    except Exception:
                        pass

                window.events.before_show += install_navigation_guard
                window.events.loaded += dismiss_splash
                window.show()
            except Exception as exc:  # noqa: BLE001 - keep startup errors visible in the splash window
                if runtime is not None:
                    try:
                        runtime.stop()
                    except Exception:
                        pass
                    runtime = None
                try:
                    _set_splash_status(
                        splash_window,
                        f"Startup failed: {type(exc).__name__}: {exc}",
                        failed=True,
                    )
                except Exception:
                    pass

        splash_window.events.loaded += start_desktop_session
        webview.start(
            gui="edgechromium",
            debug=False,
            private_mode=True,
            storage_path=str(user_data / "webview"),
        )
    except Exception as exc:
        _show_error(
            "The ZTF Classifier desktop application could not start.\n\n"
            f"{exc}\n\n"
            "Check that Microsoft Edge WebView2 Runtime is installed. "
            "The application did not switch to an external browser."
        )
        raise SystemExit(1) from exc
    finally:
        if runtime is not None:
            runtime.stop()


if __name__ == "__main__":
    main()
