# Park Windows Prototype — Acceptance Test Plan

- Status: TEST PLAN. No test result is implied by this document.
- Target version: 0.1.0-preview.1
- Target OS: Windows 10/11 x64
- Tracker: Issue #158
- Acceptance contract: PARK_WINDOWS_DESKTOP_BETA_ACCEPTANCE_2026-11-24.md

Record each test with UTC date, exact commit, software version, test environment, result, log and evidence. Use only these states: PASS, FAIL, BLOCKED, NOT RUN or NOT APPLICABLE.

The Windows preview and installer must be English-only. The UI must use left-to-right layout. Use plain English and short instructions. Do not use Persian text or RTL layout.

## 1. Test inputs

- GitHub Pre-release installer.
- SHA-256 checksum and build manifest.
- Release notes and user guide.
- Pinned DR24 cohort and its manifest.
- Label and taxonomy manifest.
- Feature and model manifests.
- Windows clean-machine test environment.
- Internet access for DR24 retrieval and WebView2 Runtime installation, if needed.

## 2. Preconditions

1. Use a clean Windows x64 machine or VM snapshot.
2. Do not install Python, pip, Git or developer tools.
3. Prefer a standard user without Administrator rights.
4. Record Windows edition, version, build, architecture, RAM, free disk space and WebView2 Runtime version.
5. Verify the installer checksum before installation.
6. Record whether the installer is unsigned. A checksum is not a code signature.
7. Confirm that the Park evaluation and distribution terms are approved in writing before external distribution.

## 3. Installer tests

| ID | Test | Method | PASS criteria |
|---|---|---|---|
| W01 | SHA-256 | Run Get-FileHash on the installer | Hash matches SHA256SUMS.txt |
| W02 | x64 gate | Run installer on Windows x64 | Installation can continue |
| W03 | 32-bit rejection | Test in a 32-bit VM, if available | Installer stops with a clear message |
| W04 | WebView2 present | Install when Runtime exists | Installer does not download Runtime again |
| W05 | WebView2 absent, online | Remove Runtime in a test VM and install | Microsoft-signed bootstrapper installs Runtime |
| W06 | WebView2 absent, offline | Disable network and install | Installer stops. It does not leave a partial installation |
| W07 | Per-user install | Install as a standard user | Install completes under LocalAppData without elevation |
| W08 | Shortcuts | Check Start Menu and desktop shortcuts | Both shortcuts point to the installed executable |
| W09 | Repeat install | Run the same installer again | Installer gives clear, safe behaviour and preserves user data |
| W19 | English-only UI and installer | Inspect all installer pages, errors, finish page and Workbench screens | All user-facing text is English. The UI uses LTR layout. No Persian text or Farsi language resource is required |

WebView2 Evergreen installation requires network access. Offline Runtime installation is not part of this release unless it is separately tested.

## 4. Desktop runtime and security tests

| ID | Test | Method | PASS criteria |
|---|---|---|---|
| W10 | Launch | Start from Start Menu | App window opens. No blank screen appears |
| W11 | Local API binding | Inspect the listening socket | Service binds to loopback only. It does not bind to 0.0.0.0 or a network interface |
| W12 | API authentication | Send requests without a token and with an invalid token. Request /docs, /redoc and /openapi.json | Protected endpoints reject invalid requests. API docs return 404 in desktop mode. Security headers are present |
| W13 | WebView security | Test CSP, external links, new windows and URI schemes | Only local scripts and connections are allowed. External navigation and unknown schemes are blocked |
| W14 | Restart | Close and reopen the app | App starts without a port conflict. Workspace data remains available |
| W15 | No developer tools | Complete the user workflow | User does not need Python, Git, a terminal or developer tools |
| W16 | Uninstall | Remove the application | Executable, shortcuts and install directory are removed |
| W17 | User data preservation | Inspect user data after uninstall | Workspaces, logs and exports remain |
| W18 | Reinstall | Reinstall the same version | Existing user data opens without corruption |

## 5. Data and cohort tests

| ID | Test | Method | PASS criteria |
|---|---|---|---|
| W20 | Cohort manifest | Verify the pinned DR24 cohort manifest | Source release, query, selection rule, object IDs, filters, labels, timestamps and hashes are recorded |
| W21 | Cohort reconciliation | Compare requested, retrieved, missing, empty, partial and rejected records | Counts reconcile. No silent fallback or silent row removal occurs |
| W22 | Label provenance | Inspect each label source and taxonomy mapping | Every label has a source, version and documented limitation |
| W23 | Object identity | Compare OID and cross-filter records | OIDs remain separate unless approved identity evidence supports grouping |
| W24 | DR24 contract | Test HATS time, photometry, filters, quality flags and missing values | Native values and units are preserved. All transformations are versioned and tested |
| W37 | Zubercal cross-match | Query the supplementary DR20 catalogue for a HATS OID. Include zero, one and multiple-candidate cases | Every candidate is preserved with radius and ambiguity state. No candidate is selected or merged automatically |

## 6. Feature and model tests

| ID | Test | Method | PASS criteria |
|---|---|---|---|
| W25 | Feature schema | Run feature generation on the pinned cohort | Feature names, order, units, schema and missing-value rules match the approved contract |
| W26 | Feature numerical tests | Test finite values, limits, errors and missing data | Results match documented tolerances. Invalid values fail safely |
| W27 | Baseline reproduction | Run the approved baseline with pinned inputs | Baseline metrics and artifact hashes match the approved reference |
| W28 | Main model | Run the selected XGBoost or LightGBM model | Model identity, input schema, taxonomy and outputs are recorded |
| W29 | Leakage checks | Inspect object-level, label, temporal and feature splits | No prohibited overlap or leakage is found |
| W30 | Classification metrics | Generate per-class metrics and confusion matrix | Balanced Accuracy, Macro-F1, precision, recall and valid ROC-AUC/PR-AUC are reported |

## 7. Uncertainty, anomaly and explainability tests

| ID | Test | Method | PASS criteria |
|---|---|---|---|
| W31 | Calibration | Evaluate probabilities on a separate calibration set | ECE, MCE, Brier score and calibration plots are recorded |
| W32 | Abstention | Evaluate the declared abstention policy | Risk–Coverage and selective error are reported. Low-evidence cases are not forced into a class |
| W33 | Anomaly analysis | Run the separate anomaly method | Method, inputs, parameters, scores and validation evidence are recorded. OOD is not labelled as anomaly evidence |
| W34 | Explainability | Generate SHAP output for eligible predictions | Explanation matches the exact model, feature schema and input |
| W35 | Temporal validation | Train on earlier data and test on later data | Split, population and metrics are recorded. No object leakage is found |
| W36 | External validation | Evaluate on the declared independent population | Dataset, taxonomy mapping, limitations and transferability results are reported |

## 8. Application workflow and reproducibility tests

1. Install the application on a clean Windows system.
2. Create a workspace.
3. Select the approved DR24 source and cohort.
4. Retrieve the requested records.
5. Inspect raw light curves, filters and diagnostic QC.
6. Run the approved feature pipeline.
7. Run the baseline and main model.
8. Review calibrated probabilities, uncertainty and abstention.
9. Review anomaly scores and eligible SHAP explanations.
10. Review temporal and external validation reports.
11. Export the scientific report and reproducibility bundle.
12. Close and reopen the workspace.
13. Verify the last operation, report and export.
14. Repeat the run with the same pinned inputs and compare hashes and declared numerical tolerances.

The complete workflow must run from the installed application. A notebook, helper script or direct API call does not pass this test.

## 9. Evidence required for each test

Record:
- Test ID and result.
- UTC date and time.
- Windows edition, version, build and architecture.
- RAM, free disk space and test environment.
- App version, source commit and installer SHA-256.
- WebView2 Runtime version and installation method.
- Dataset, label, feature, model, taxonomy and split versions.
- Logs, screenshots and artifact paths.
- Error details, limits and corrective action.

Do not report NOT RUN or SKIPPED as PASS.

## 10. Distribution limits

- The installer is UNSIGNED until a valid code signature is applied.
- A checksum verifies file integrity. It does not prove publisher identity.
- Do not upload a public installer until written Park evaluation and distribution terms are approved.
- A GitHub Pre-release does not prove scientific validity or Park acceptance.

## 11. Final acceptance

All applicable tests W01–W37 must pass or have a documented, approved NOT APPLICABLE state. No mandatory scientific gate may remain BLOCKED or NOT RUN.

The full workflow must run on a clean Windows system. The report must include installation, launch, data retrieval, features, model output, uncertainty, abstention, anomaly analysis, explainability, validation, export and data preservation.

The Founder / Project Owner must approve the package for Park presentation. Record the presentation and its outcome. Until then, the status remains NOT READY FOR PARK PRESENTATION.
