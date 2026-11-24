"""Windows desktop entry point for the ZTF Classifier Workbench."""

from __future__ import annotations

import ctypes
import json
import os
import secrets
import sys
from collections.abc import Callable
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

    handlers: list[Callable[..., None]] = [
        block_untrusted_navigation,
        block_external_uri_scheme,
    ]

    def attach_core_handlers(core: Any) -> None:
        if core is None:
            raise RuntimeError("The WebView2 core is not initialized.")
        core.FrameNavigationStarting += block_untrusted_navigation
        core.LaunchingExternalUriScheme += block_external_uri_scheme

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


def _is_webview2_runtime_installed() -> bool:
    """Check the Evergreen WebView2 Runtime registry values."""
    if os.name != "nt":
        return False

    try:
        import winreg
    except ImportError:
        return False

    client_id = "{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}"
    locations = (
        (
            winreg.HKEY_LOCAL_MACHINE,
            rf"SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\{client_id}",
        ),
        (
            winreg.HKEY_CURRENT_USER,
            rf"Software\Microsoft\EdgeUpdate\Clients\{client_id}",
        ),
    )
    for hive, subkey in locations:
        try:
            with winreg.OpenKey(hive, subkey) as registry_key:
                version, _ = winreg.QueryValueEx(registry_key, "pv")
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

        runtime = LocalApiServer(create_app(settings=settings))
        base_url = runtime.start()
        checks["local_api_health"] = "PASS"

        for path in ("/workbench/", "/workbench/app.js", "/workbench/styles.css"):
            with urlopen(f"{base_url}{path}", timeout=5) as response:
                if response.status != 200:
                    raise RuntimeError(f"Unexpected HTTP status for {path}.")
                body = response.read()
                if path == "/workbench/" and b"DR24 Explorer" not in body:
                    raise RuntimeError("The packaged Workbench HTML is incomplete.")
            checks[f"static:{path}"] = "PASS"

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
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
    finally:
        if runtime is not None:
            try:
                runtime.stop()
                checks["local_api_shutdown"] = "PASS"
            except Exception as exc:
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
        token = secrets.token_urlsafe(32)
        user_data = get_user_data_dir()
        settings = build_desktop_settings(token, data_dir=user_data)
        app = create_app(settings=settings)
        runtime = LocalApiServer(app)
        base_url = runtime.start()

        webview.settings["ALLOW_DOWNLOADS"] = True
        webview.settings["ALLOW_FILE_URLS"] = False
        webview.settings["OPEN_EXTERNAL_LINKS_IN_BROWSER"] = False
        webview.settings["OPEN_DEVTOOLS_IN_DEBUG"] = False
        webview.settings["REMOTE_DEBUGGING_PORT"] = None

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
        )
        window.events.closed += runtime.stop

        def install_navigation_guard(current_window: Any) -> None:
            _install_navigation_guard(current_window, base_url)

        window.events.before_show += install_navigation_guard

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
