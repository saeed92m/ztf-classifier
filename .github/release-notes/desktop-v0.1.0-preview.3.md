# ZTF Classifier Windows Preview 0.1.0-preview.3

This evaluation pre-release repairs the Windows desktop startup and WebView2 handoff defects reported in preview.2. The confirmed primary cause was an oversized splash HTML document: the 1,873,208-byte PNG expanded to 2,497,612 bytes when base64-embedded, exceeding WebView2 NavigateToString's 2 MiB input limit. The application now displays a small inline placeholder first, starts the loopback API, then navigates the splash window to a packaged static HTML page served by that API. The page loads the PNG with a same-origin relative URL. The release also adds real WebView2 GUI validation to the Windows build and installed-application checks.

## Changes in this preview

- Replace splash status updates through `evaluate_js()` with CSP-compatible `run_js()`. The splash CSP remains strict and does not allow `unsafe-eval`. The splash image is no longer embedded in the HTML. It is loaded from the loopback API because WebView2 `NavigateToString` rejects HTML strings larger than 2 MiB.
- Start backend initialization through the documented pywebview background callback. The startup worker waits for the small splash DOM without blocking the GUI loop, then loads the artwork from the loopback API.
- Verify that the embedded splash image decodes in WebView2 before continuing.
- Keep the splash visible until the Workbench reports a ready DOM, a present and visible `#app` root, and non-empty page content.
- Record frontend JavaScript errors and readiness telemetry in `%LOCALAPPDATA%\\ZTFClassifier\\logs\\desktop.log`.
- Add bounded startup timeouts and retain a visible failure state when the splash or Workbench fails to load.
- Add a real WebView2 GUI smoke test for the build output and installed application.
- Set explicit executable icon locations on Desktop and Start Menu shortcuts. Add CI checks for both shortcut targets.
- Preserve the local API loopback binding, session token, navigation guard, user data, and scientific baseline.

## Included

- Windows x64 desktop application using pywebview and Microsoft WebView2.
- Local API with an in-memory session token and loopback binding.
- Local workspace creation, opening, operation history, and export persistence.
- Bounded ZTF DR24 raw light-curve retrieval for 1 to 10 OIDs per request.
- Source-native light-curve display, raw epoch inspection, diagnostic QC, descriptive statistics, and provenance.
- Raw JSON + QC export.
- User Manual and Quick Start PDFs.
- Build manifest, dependency inventory, self-test report, real WebView2 GUI smoke reports, and SHA-256 checksum.

## Verified Windows build evidence

A Windows preview build completed successfully on main commit `cb9481091904e40771c61b17ffd43fc2bfac6b66` in GitHub Actions run [45882456540](https://github.com/saeed92m/ztf-classifier/actions/runs/45882456540).

The Windows job passed the desktop runtime tests, JavaScript syntax checks, Ruff checks, PyInstaller build, frozen self-test, real WebView2 GUI smoke test, PDF generation, NSIS installer build, silent install, installed launch, installed WebView2 GUI smoke test, silent uninstall, build manifest generation, SHA-256 generation, and artifact upload.

The verified artifact was `15148147866` (archive SHA-256: `3034de5b62df120a48008a0318b18af326a2779297e045ccc14be08c0b283b8`). Its manifest records installer SHA-256 `f83ede58f40f6e3e38708018fe4e4e6efb3a4a86960d73c5b279d72531e09edc`. Both build and installed GUI reports record `PASS`, with the splash image loaded, Workbench DOM ready, visible application root, and zero frontend errors.

The original run did not publish the pre-release because its `publish_preview` input was false. The publication workflow must rebuild and verify the exact commit that creates the release. This evidence records the completed preflight build; it does not claim that the GitHub Release has already been published.

## Validation required for this release

The exact main-branch commit must pass:
- Desktop runtime and workspace tests.
- JavaScript syntax and Ruff checks.
- PyInstaller frozen application build and self-test.
- Real WebView2 splash image, Workbench DOM, visible application-root, and frontend-error smoke test.
- NSIS installer build.
- Silent install, installed self-test, installed WebView2 GUI smoke test, shortcut icon-path checks, and silent uninstall.
- Build manifest, SHA-256 checksum, and artifact upload.

A GitHub-hosted Windows runner can verify WebView2 DOM rendering. It cannot verify the target laptop's display scaling, desktop icon cache, graphics driver, or user-profile environment. Manual acceptance on the target Windows device remains required.

## Known limitations

- Preview target: Windows 10/11 x64.
- Installer is unsigned. SHA-256 checksums are provided.
- Internet access is required for live DR24 retrieval.
- Each retrieval request is limited to 1–10 OIDs.
- DR24 values are preserved in source-native form. No production photometry/time transformation or approved QC mask is applied.
- Descriptive statistics are not model features.
- Classification, calibrated probabilities, abstention, anomaly detection, and transferability are not accepted for the Park target population.
- CPVS candidate-membership discrepancy remains an open scientific validation blocker.
- A successful desktop build is not scientific validation.
- Full Mission Control UI redesign and automatic GitHub updater are not included in this preview.

## Installation

Download the Windows installer and verify it with `SHA256SUMS.txt` before running it. Read `Quick_Start.pdf` first. Read `User_Manual.pdf` for full instructions and troubleshooting.

## Compatibility and upgrade

This is a preview build. Back up workspace exports before replacing or uninstalling it. Uninstall is designed to preserve user data under the Windows user profile. Do not assume that a later preview will migrate every future workspace schema.
