# ZTF Classifier Windows Preview - Quick Start

**Version:** 0.1.0-preview.1

## Install

1. Download ZTFClassifier-0.1.0-preview.1-Setup.exe and SHA256SUMS.txt from the GitHub Pre-release.
2. Verify the installer in PowerShell: Get-FileHash .\ZTFClassifier-0.1.0-preview.1-Setup.exe -Algorithm SHA256
3. Compare the hash with SHA256SUMS.txt.
4. Run the installer.
5. Launch ZTF Classifier from the Desktop shortcut or Start Menu.

The installer is unsigned. The checksum verifies file integrity, not publisher identity.

## First DR24 inspection

1. Wait for API ready.
2. Open Workspaces.
3. Create a workspace named Park demonstration.
4. Open DR24 Explorer (raw).
5. Select Tested sample OIDs or enter 1 to 10 positive, unique ZTF OIDs.
6. Select Load raw light curves.
7. Review the light curve, raw epoch rows, diagnostic QC, descriptive statistics, and acquisition provenance.
8. Select Download raw JSON + QC to save the export to the active workspace and download it.

Built-in sample OIDs:
- 264114400013085
- 264214400000912

## Interpret the output

The preview displays source-native DR24 data. It preserves HMJD, magnitude, magnitude error, colour coefficient, and catalogue flags. HMJD is not MJD.

Descriptive statistics are not machine-learning features. Diagnostic QC is not a production-approved mask.

This preview does not provide validated classification, calibrated probabilities, abstention, or anomaly detection for the Park population. Do not present raw-data summaries as model predictions.

See User_Manual.pdf in the release assets for full instructions and troubleshooting.
