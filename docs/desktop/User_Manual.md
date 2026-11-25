# ZTF Classifier Windows Preview - User Manual

**Version:** 0.1.0-preview.1

## Purpose

This is a Windows desktop prototype for bounded inspection of public ZTF DR24 light curves from the IRSA HATS indexed source.

Supported functions:
- Create and open local workspaces.
- Retrieve 1 to 10 positive, unique ZTF object IDs per request.
- Display source-native HMJD and magnitude light curves.
- Inspect raw epoch records, diagnostic QC, descriptive statistics, and provenance.
- Save and restore raw JSON exports with QC and provenance.

This is a data-inspection prototype. It is not a scientifically accepted classifier for the Park target population.

## Install

1. Download the installer and SHA256SUMS.txt from the GitHub Pre-release.
2. In PowerShell, run: Get-FileHash .\ZTFClassifier-0.1.0-preview.1-Setup.exe -Algorithm SHA256
3. Compare the hash with SHA256SUMS.txt.
4. Run the installer.
5. Start ZTF Classifier from the Desktop shortcut or Start Menu.

The installer is unsigned. A checksum confirms file integrity. It does not provide a publisher signature. Windows 10/11 x64 and Microsoft Edge WebView2 Runtime are required. The installer can install the Microsoft-signed Evergreen WebView2 bootstrapper when required.

## First launch

1. Wait for the API ready indicator.
2. Open Workspaces.
3. Enter a workspace name, such as Park demonstration.
4. Select Create workspace.
5. Confirm that the workspace is active.

Create or open a workspace before retrieval. Workspace manifests, operation history, logs, and exports are stored under the current Windows user's application-data directory.

## Retrieve DR24 data

1. Open DR24 Explorer (raw).
2. Enter 1 to 10 positive integer OIDs. Separate IDs with commas, spaces, or new lines.
3. Or select Tested sample OIDs. The built-in sample IDs are 264114400013085 and 264214400000912.
4. Select Load raw light curves.
5. Wait for the request to finish.
6. Review the status and returned records.

The application queries the indexed DR24 source. It does not scan the full catalogue. Separate OIDs remain separate records.

## Read the result

Each record can show the filter, field ID, rcid, epoch count, payload SHA-256, a light-curve plot, descriptive statistics, the first 50 raw epochs, and raw-preserving QC output.

The plot uses source-native HMJD and magnitude values. It shows reported magnitude errors when they are finite and non-negative. HMJD means HJD minus 2,400,000.5. It is not MJD.

The plot omits rows without finite numeric HMJD/magnitude pairs. Those rows remain in the raw payload and export. Descriptive statistics include all finite HMJD/magnitude pairs regardless of catalogue flags. No epoch filtering is applied.

Descriptive statistics are not model features. Diagnostic QC is not a production-approved quality mask.

## Provenance and export

Review Acquisition provenance for source, release, requested/returned/missing OIDs, query details, schema information, and payload hashes.

After a successful retrieval, select Download raw JSON + QC. The application saves the export to the active workspace and downloads a JSON file. The export contains the raw source payload, QC output, descriptive summaries, and provenance.

To restore the latest export, open Workspaces and select Restore export. Then open Reports and exports and download the restored JSON.

## Limitations

- Internet access is required for live DR24 retrieval.
- Each request is limited to 1–10 OIDs.
- No HMJD-to-MJD conversion, magnitude conversion, epoch filtering, production quality mask, frozen model feature generation, or cross-OID source grouping is performed.
- Classification, calibrated probabilities, abstention, anomaly detection, and transferability are not accepted for the Park target population.
- Do not present raw summaries as model predictions.
- A ZTF OID is a catalogue identifier. It does not prove physical-source identity.
- CPVS candidate-membership discrepancy remains an open scientific validation blocker.
- A successful desktop build is not scientific validation.

## Troubleshooting

- API not ready: close and restart the application. Keep logs if the problem continues.
- Retrieval fails: check internet access and retry with one known OID.
- Workspace required: create or open a workspace.
- OID rejected: use positive integers and no more than 10 unique IDs.
- No plot points: inspect raw rows and the JSON export. The source may have no finite HMJD/magnitude pairs.
- Export fails: confirm retrieval succeeded and a workspace is active.
- WebView2 error: install or repair Microsoft Edge WebView2 Runtime.
- Windows blocks installer: verify the checksum. Continue only if it matches and you trust the source.

## Scientific status

This preview demonstrates desktop packaging, local workspace handling, bounded DR24 raw-data retrieval, diagnostic QC, descriptive summaries, and provenance-aware export. It does not complete the four-phase Park scientific acceptance plan. Model authentication, DR24-to-feature compatibility, labelled cohort verification, calibrated classification, abstention, anomaly detection, explainability, and independent/temporal validation remain separate acceptance requirements.
