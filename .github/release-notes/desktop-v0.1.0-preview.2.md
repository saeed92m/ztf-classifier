# ZTF Classifier Windows Preview 0.1.0-preview.2

This is an evaluation pre-release of the Windows desktop prototype. It adds the startup splash screen and application branding to the prior Windows preview.

## Changes in this preview

- Show the supplied ZTF splash screen before workspace setup and local API startup.
- Report actual startup milestones with an indeterminate progress animation. No fabricated completion percentage is shown.
- Keep startup errors visible, provide a working Close action, and stop the local API if startup fails.
- Keep the splash window out of the always-on-top state so it does not block other applications.
- Use the supplied application icon in the Workbench header, favicon, Windows executable, NSIS installer, and uninstaller. Configure installer icons through the MUI2 icon definitions.
- Verify packaged splash and icon assets during the frozen application self-test.
- Add regression tests for startup order, startup failure handling, asset signatures, splash security policy, and asset path allowlisting.

## Included

- Windows x64 desktop application using pywebview and Microsoft WebView2.
- Local API with an in-memory session token and loopback binding.
- Local workspace creation, opening, operation history, and export persistence.
- Bounded ZTF DR24 raw light-curve retrieval for 1 to 10 OIDs per request.
- Source-native light-curve display, raw epoch inspection, diagnostic QC, descriptive statistics, and provenance.
- Raw JSON + QC export.
- User Manual and Quick Start PDFs.
- Build manifest, dependency inventory, self-test report, and SHA-256 checksum.

## Validation performed

The release is published only after the exact main-branch commit passes the Windows desktop workflow. The workflow builds the frozen application and installer, runs desktop runtime and workspace tests, checks JavaScript syntax and Ruff rules, runs the frozen application self-test, and performs silent install, launch, and uninstall smoke tests. The release attaches evidence from that same workflow run.

The CI install/uninstall test runs on a GitHub-hosted Windows runner. It does not replace clean-machine acceptance on the target Windows laptop.

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
- Splash appearance and transition must still be checked on the target Windows laptop.
- Full Mission Control UI redesign and automatic GitHub updater are not included in this preview.

## Installation

Download the Windows installer and verify it with SHA256SUMS.txt before running it. Read Quick_Start.pdf first. Read User_Manual.pdf for full instructions and troubleshooting.

## Compatibility and upgrade

This is a preview build. Back up workspace exports before replacing or uninstalling it. Uninstall is designed to preserve user data under the Windows user profile. Do not assume that a later preview will migrate every future workspace schema.
