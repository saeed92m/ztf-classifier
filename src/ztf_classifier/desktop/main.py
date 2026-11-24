"""Windows desktop entry point for the ZTF Classifier Workbench."""

from __future__ import annotations

import ctypes
import os
import secrets
import sys
from collections.abc import Callable
from typing import Any
from urllib.parse import urlsplit

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


def main() -> None:
    """Start the private API, then open the standalone Windows window."""
    if os.name != "nt":
        raise SystemExit("The first desktop preview supports Windows only.")

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
