# ZTF Classifier Windows Preview 0.1.0-preview.5

## Summary

This preview improves DR24 acquisition diagnostics and makes the scientific release-gate scopes explicit. It does not claim that scientific validation has passed.

## Changes

- Move Workspaces above DR24 Explorer in the Mission Control sidebar.
- Improve the visibility of the DR24 raw JSON + QC export control. The control remains disabled until a successful acquisition provides an exportable payload.
- Keep export disabled when an HTTP-success response contains zero returned records. Preserve export for partial responses with returned records, and retain requested, returned, and missing OID accounting.
- Include pandas distribution metadata in the frozen Windows application so runtime dependency version checks work after packaging.
- Preserve the DR24 API error code and request ID in the Workbench.
- Log the underlying DR24 acquisition exception in the local desktop log. Use the request ID to correlate the on-screen error with the log.
- Record failed DR24 acquisition with an unknown missing-OID set. A failed query does not prove that every requested OID is missing.
- Separate the release-blocking product validation gate from the non-release-blocking historical external-reproduction gate.
- Explain why source acquisition and source reachability do not count as benchmark evaluation.
- Expose product and external-reproduction gate details through the API.

## Scientific status and limitations

- The product scientific gate remains fail-closed.
- Missing immutable evidence manifests, benchmark result reports, required scientific checks, or provenance continue to block a PASS.
- External CPVS reconstruction remains a separate scientific claim. This preview does not resolve the published-membership discrepancy.
- A successful DR24 retrieval does not prove feature compatibility, model validity, or classification performance.
- No model artifact, feature set, taxonomy, class order, benchmark definition, split, scientific threshold, or acceptance criterion is changed.
- A successful Windows build or installer test is not scientific validation.

## Verification

The exact source commit must pass the Windows Desktop Preview workflow, CI, and Scientific Validation contract workflow. The deterministic offline browser contract also covers empty DR24 responses and partial responses with retained OID accounting. The Windows workflow verifies dependency imports and metadata in the frozen runtime, a live DR24 single- and multi-OID HATS smoke test, JavaScript syntax, desktop runtime, frozen application startup, WebView2 GUI smoke, installer creation, silent install, launch, uninstall, and SHA-256 generation. The live smoke report is included in the release assets and checksummed.

The release must include the exact source commit, build manifest, installer checksum, self-test report, GUI smoke reports, dependency manifest, and user documentation.

## Compatibility

- Windows 10/11 x64.
- Python 3.11 runtime is bundled.
- Microsoft Edge WebView2 Runtime is required.
- The installer is unsigned. SHA-256 checksums are provided.
- User data remains in the Windows user-data directory and is not removed by uninstall.

## Manual acceptance required

1. Confirm Workspaces appears before DR24 Explorer.
2. Confirm the raw JSON + QC button is legible in both Light and Dark themes. Confirm it remains disabled until an export is available.
3. Create or open a workspace, select the two tested sample OIDs, and run the DR24 lookup. If it fails, record the displayed diagnostic ID and provide `%LOCALAPPDATA%\\ZTFClassifier\\logs\\desktop.log`. The diagnostic ID must match the log entry.
4. Review the Product validation and External reproduction sections. Do not expect a PASS until the required evidence manifests, benchmark reports, checks, and provenance are present.
5. Check the Windows executable, Desktop shortcut, Start Menu shortcut, taskbar, and Workbench header branding on the target device. Automated shortcut-presence checks do not prove visual icon consistency; see [issue #320](https://github.com/saeed92m/ztf-classifier/issues/320).
