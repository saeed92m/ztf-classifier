"""Windows desktop entry point for the ZTF Classifier Workbench."""

from __future__ import annotations

import ctypes
import os
import secrets
import sys
from typing import Any

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
