# ADR-001: Windows desktop shell for the Park experimental release

**Status:** Proposed — technical spike required  
**Date:** 2026-11-24  
**Decision owner:** Project owner

## Context

The repository currently contains a FastAPI application and an HTML/CSS/JavaScript Workbench served as static assets. The API server entry point binds to `127.0.0.1:8000`. This is a local web application, not yet an independent Windows desktop program.

The Park owner has selected an independent Windows desktop application. The packaged application must not require a separately installed Python environment, command-line tools, or a manually started browser.

The application must preserve the existing Application/Core boundary. The GUI must not access model artifacts or scientific state directly.

## Candidate approaches

| Candidate | Advantages | Main risks for this product |
|---|---|---|
| pywebview + existing FastAPI + current web UI | Reuses the current front end and Python services; small desktop-shell layer; local application can be packaged with Python | WebView2/.NET runtime detection; PyInstaller hooks and data collection; child-process lifecycle; local HTTP security; native dialog support |
| PySide6 + Qt WebEngine | Mature native widgets and embedded Chromium; broad GUI controls | Larger runtime and package; new Qt dependency; possible UI rewrite; packaging complexity |
| Tauri shell | Native-feeling desktop application; controlled webview; small shell | Rust toolchain and frontend build integration; new inter-process boundary; Python service lifecycle and installer integration require separate design |

## Proposed path

Run a short, isolated engineering spike with **pywebview + the existing FastAPI services** as the first candidate. Do not add it to the production dependency set until the spike passes.

Why this candidate:
1. It reuses the current API and static Workbench rather than replacing the scientific application layer.
2. It can present a real standalone desktop window rather than opening the system browser.
3. It avoids introducing a second backend runtime for the first Windows target.

This is a provisional implementation choice, not yet an accepted architecture. If the spike fails on packaging reliability, startup/shutdown, runtime availability, security, or resource use, compare PySide6 and Tauri again before committing to the shell.

## Required spike tests

1. Start the API as a managed child process without a fixed-port assumption.
2. Bind only to loopback; select an available port; do not listen on all interfaces.
3. Pass the selected local origin to the desktop window without exposing secrets in logs or URLs.
4. Wait for a health/readiness endpoint before creating the window.
5. Open only the expected local application origin inside the WebView.
6. Reject or externally open untrusted navigation and new-window requests.
7. Shut down the API process on normal close, startup failure, and forced close.
8. Detect the WebView2 Runtime and show a clear actionable message if unavailable.
9. Package the app with a frozen Python runtime and all required application/static assets.
10. Test an offline launch and a live DR24 retrieval separately.
11. Test clean Windows 11 installation, upgrade, uninstall, Windows Defender interaction, and user-data retention.
12. Measure startup time, idle RAM, package size, and query memory on the actual Park laptop.

## Runtime and installer strategy

- Prefer WebView2 Evergreen when available, because Microsoft documents it as the normal distribution mode and includes it in Windows 11. The installer and app must still detect runtime availability.
- Do not bundle a Fixed Version WebView2 runtime unless offline or controlled-runtime requirements justify its substantial additional size and update burden.
- Use PyInstaller **one-folder** output for the first internal test build. It is easier to inspect and diagnose than a one-file executable. A signed installer can wrap the tested folder later.
- Do not claim the first build is self-contained until Python dependencies and all required native libraries are bundled and a clean-machine test passes.
- Keep cache, user projects, logs, and exports outside the installation directory, with documented paths and retention rules.

## Local service security requirements

- Bind to `127.0.0.1` or `::1` only.
- Never bind to `0.0.0.0` or a LAN address for the desktop mode.
- Prefer an ephemeral available port; do not assume port 8000 is free.
- Use a per-process random token or equivalent request protection for local control endpoints, stored outside public assets.
- Disable permissive CORS in desktop mode.
- Reject external navigation in the embedded view by default.
- Do not expose interactive API documentation in the packaged production build unless explicitly needed.
- Stop child processes and release sockets on application exit.

## Consequences

Positive:
- The scientific API and service layer can remain the same.
- The first Windows shell can reuse the Workbench while UX design improves it.
- Future macOS/Linux shells can be considered after the Windows acceptance path stabilizes.

Costs and limitations:
- It is still a web-rendered interface inside a native desktop window.
- WebView2 runtime and packaging must be tested.
- PyInstaller may need explicit hidden imports, native binaries, and static-data configuration.
- This ADR does not prove the approach will work on the target device.

## References

- Microsoft: [Distribute your app and the WebView2 Runtime](https://learn.microsoft.com/en-us/microsoft-edge/webview2/concepts/distribution)
- Microsoft: [Evergreen vs. Fixed Version WebView2 Runtime](https://learn.microsoft.com/en-us/microsoft-edge/webview2/concepts/evergreen-vs-fixed-version)
- pywebview: [Installation and platform dependencies](https://pywebview.idepy.com/en/guide/installation)
- pywebview: [Web engine selection](https://pywebview.idepy.com/en/guide/web_engine)
- PyInstaller: [Operating modes](https://pyinstaller.org/en/stable/operating-mode.html)
- PyInstaller: [Spec files and bundled data](https://pyinstaller.org/en/stable/spec-files.html)

