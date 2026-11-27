# ZTF Classifier Windows Preview 0.1.0-preview.4

## Summary

This preview improves the Windows Scientific Workbench interface and update experience.

## Changes

- Complete Light theme coverage for Mission Control panels, navigation, tables, forms, charts and update controls.
- Keep the desktop sidebar visible while the main work area scrolls independently.
- Compare the installed Windows version with the latest published Stable or Preview release.
- Preserve the authenticated local update API and SHA-256 verification for installer downloads.
- Display an explicit warning when the installed version cannot be read or version comparison cannot be completed.

## Verification

The exact source commit must pass the Windows Desktop Preview workflow. This includes desktop runtime tests, JavaScript syntax checks, Ruff checks, frozen application self-test, WebView2 GUI smoke tests, installer build, silent install, launch, uninstall, and checksum generation.

## Compatibility

- Windows 10/11 x64.
- Python 3.11 runtime is bundled.
- Microsoft Edge WebView2 Runtime is required.
- The installer is unsigned. SHA-256 checksums are provided.
- User data remains in the Windows user-data directory and is not removed by uninstall.

## Scientific status and limitations

- This is an engineering preview, not a scientific production release.
- A successful installer build does not establish scientific validation.
- The scientific release gate remains fail-closed.
- No model, dataset, feature schema, taxonomy, class order, benchmark definition, threshold, or scientific acceptance criterion is changed.
- Full scientific validation remains a separate task and is not claimed by this release.

## Manual acceptance required

Install this preview on the target Windows device. Check Light and Dark themes, all navigation pages, long-page scrolling, version comparison, download checksum verification, application restart, and user-data preservation.
