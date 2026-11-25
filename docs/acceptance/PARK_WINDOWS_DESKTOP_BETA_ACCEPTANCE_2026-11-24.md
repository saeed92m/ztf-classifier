# Park Windows Desktop Experimental Release — Acceptance Contract

**Date:** 2026-11-24  
**Status:** Proposed execution contract; not an acceptance result  
**Owner decision:** Standalone Windows desktop application; English-only Windows experimental preview  
**Primary tracker:** Issue #158  
**Scientific baseline:** Preserve v0.2.0 and all frozen artifacts

## 1. Purpose and acceptance boundary

**Active delivery selection (Founder, 2026-11-25):** The first deliverable is the Windows laboratory preview in Sections 1, 3–7 and its W0–W13 gates. The Full Park MVP in Section 8 is a separate later milestone. It is not part of this preview and must not displace preview acceptance work. The project scope freeze remains active until the preview is installed and tested on clean Windows and presented to the Park.

Deliver the first useful, installable Windows desktop preview for a Science and Technology Park demonstration. It must provide a real and reproducible scientific workflow. A screenshot-only mock-up or an installer that opens a broken web page does not pass.

The submitted Park workbook AP-02-140503 identifies the current product state as a laboratory prototype with no sales. It describes a CPU-first platform for ZTF light-curve analysis and rare-transient discovery. It also states that capabilities which are not implemented or validated remain development objectives. They must not be presented as verified product features.

Keep three deliverables separate:

1. **Windows laboratory preview:** installable, real-data workflow with source inspection, diagnostics, provenance and export.
2. **Full Park MVP:** the wider six-month R&D plan, including a provenance-backed labelled dataset, feature pipeline, model evaluation, uncertainty, anomaly analysis and reproducible technical report.
3. **Long-term platform:** broader discovery workflows and cross-survey support.

Passing the preview does not pass the full Park MVP.

## 2. Requirements derived from the Park workbook

The workbook describes these intended product outcomes:

- Process and analyse public ZTF light curves.
- Classify variable and transient objects when a validated model and compatible input contract are available.
- Prioritise follow-up candidates using documented model output, data quality and uncertainty.
- Investigate unusual and rare-object candidates.
- Support research through inspection, analysis and reporting.
- Provide installable software and an analytical dashboard, with a path to Windows, macOS and Linux.
- Use a CPU-first architecture without a required high-cost GPU.
- Record data, source, model and test versions so results can be traced and reproduced.

The workbook defines a six-month plan with four phases:

| Phase | Workbook output |
|---|---|
| 1 | Development environment, DR24 access, labelled subset and feature set |
| 2 | Baseline and main XGBoost/LightGBM model with initial evaluation |
| 3 | Calibrated uncertainty, abstention, anomaly score and validation report |
| 4 | Live dashboard, documentation and software-registration preparation |

These are planned outcomes, not proof that the work is complete.

## 3. First Windows preview — required user workflow

A non-developer user must be able to:

1. Install the application from a Windows installer.
2. Start it from the Start menu or desktop shortcut.
3. Create or open a local workspace.
4. Select ZTF DR24 HATS explicitly as the data source.
5. Enter or select a known DR24 OID.
6. Retrieve a real light curve and see a clear acquisition status.
7. Inspect the light curve separately by OID and filter.
8. Inspect raw observation values and diagnostic QC.
9. Review source-native descriptive statistics, when the approved change is integrated.
10. Inspect source, schema, identifiers, retrieval time and payload hashes.
11. Export raw records, descriptive summaries and provenance to JSON.
12. Reopen the workspace and identify the last operation and its status.
13. Read help and understand what to do when network access or source retrieval fails.

A helper script, notebook, direct API call or developer-only command does not satisfy this user workflow.

### Required screens

- Welcome and Workspace
- Home
- Data Sources
- DR24 Object Explorer
- Light-Curve Analysis
- Quality and Summary
- Provenance
- Reports and Export
- Settings
- Help and About

Do not expose blocked model and discovery functions as working features.

## 4. Scientific behaviour in this preview

The preview may claim only what is verified:

- Live retrieval for the tested DR24 HATS workflow.
- Raw source-native observation display.
- Per-OID and per-filter inspection.
- Diagnostic QC under the versioned diagnostic policy.
- Per-OID descriptive statistics, if the current PR #307 change passes integration and validation.
- JSON export with provenance and hashes, after end-to-end verification.

The preview must not claim:

- DR24-to-v0.2.0 feature parity.
- Validated DR24 classification.
- Availability of an authenticated v0.2.0 production model unless its artifact is recovered and verified.
- Calibrated probabilities on an eligible independent evaluation cohort.
- Validated conformal coverage or abstention performance.
- Scientific anomaly discovery from OOD scores.
- Physical-source identity across OIDs without accepted AOIC evidence.
- General model performance across all ZTF sources.
- Completion of the 100,000-light-curve Park cohort.

The existing descriptive summary status is DESCRIPTIVE_NOT_CLASSIFICATION. The current DR24 QC status is diagnostic and not production-approved. Raw values must remain available.

## 5. Desktop requirements

### User experience

- The application opens in its own desktop window. The user must not open a browser manually.
- The user must not need Python, pip, Git, a virtual environment, Docker or a terminal.
- Show clear states for local service, network, acquisition, processing, export and errors.
- Do not show a green connection state when a service is unavailable.
- Distinguish missing records, empty light curves, partial results, rejected records and source errors.
- **Owner amendment (2026-11-25):** The Windows experimental preview is English-only. Persian localization and right-to-left layout are not acceptance requirements for this preview. Consider them for a later product release only. Preserve standard astronomical terms, units and identifiers.
- Plot labels must match the real source time scale. DR24 HMJD must never be labelled MJD.
- Show magnitude units, filter, error bars and missing-data indicators.
- Use accessible contrast, keyboard navigation, visible focus and readable scaling.

### Local runtime and security

The desktop shell must manage local application services as one application lifecycle.

Acceptance requirements:

- Bind local services to loopback only by default.
- Use a dynamically allocated or collision-safe local port; do not assume port 8000 is free.
- Pass the local API endpoint to the desktop shell securely.
- Start and stop child processes cleanly.
- Prevent the UI from using an untrusted remote endpoint as its backend.
- Define a local-origin and request-security policy; test cross-origin and request-forgery cases.
- Store settings, logs, workspace files and caches in documented per-user locations.
- Do not store secrets in plain text or export them.
- Do not upload local files or astronomical data without explicit user action.
- Show where exports and logs are saved.
- Provide a useful recovery message when local service startup fails.

### Candidate packaging strategy

The current Workbench is HTML/CSS/JavaScript. Candidate path:

1. Reuse the current Workbench as the presentation layer.
2. Keep scientific Core and application services separate.
3. Prototype a native Windows shell that embeds the Workbench.
4. Compare pywebview with WebView2 against a PySide6/WebEngine alternative.
5. Build on a native Windows runner.
6. Evaluate PyInstaller onedir before one-file mode.
7. Select an installer after dependency and signing requirements are reviewed.
8. Detect WebView2 at run time and provide an installation path if missing.
9. Test application launch without a network connection. Live DR24 retrieval still requires network access.

This is a candidate architecture, not a final dependency decision. Measure startup, memory, installer size, clean-machine compatibility and failure handling before selecting the framework.

## 6. Data and cohort requirements

Do not download the entire multi-terabyte DR24 collection for the first preview.

Pin a small cohort and record:

- Source release, query and selection rule.
- Requested and returned OIDs.
- OID, filter, field and partition identity.
- Retrieved, missing, empty, partial and rejected records.
- Acquisition timestamp and source metadata.
- Payload and export hashes.
- Schema and software version.
- Label source and label limitations, where labels are used.
- AOIC identity evidence when discussing records as one astrophysical source.

The two previously tested OIDs are separate survey OIDs. Do not present them as one confirmed astrophysical source without independent identity evidence.

Grow the sample in stages: the existing two-OID smoke test, then a predeclared 5–10-object diagnostic set, then a 30–50-object guided demonstration after identity and availability are verified. Do not replace records after reviewing outcomes merely to reach a desired count.

The 100,000-light-curve labelled cohort remains a separate full-Park-MVP target. Process and reconcile the complete eligible cohort under a declared rule.

## 7. Hard acceptance gates

Allowed states: PASS, FAIL, BLOCKED, NOT RUN, NOT APPLICABLE.

| Gate | Acceptance requirement | Minimum evidence |
|---|---|---|
| W0 Scope | UI and release claims match actual features | Approved scope and claim audit |
| W1 Baseline | Frozen v0.2.0 remains unchanged | Hash and manifest comparison |
| W2 Source | DR24 release, units, time scale and identifiers are explicit | Contract tests and source metadata |
| W3 Acquisition | Requests and results reconcile; no silent fallback | Live API and Workbench evidence |
| W4 Identity | OIDs are not confused with physical sources | AOIC record; ambiguity retained |
| W5 QC | Raw data preserved; diagnostic status is visible | Unit, integration and schema tests |
| W6 Export | Export includes records, provenance, schema and hashes | Export and hash verification |
| W7 Desktop | Managed local service opens in desktop window | Startup, shutdown, port and error tests |
| W8 Installer | Clean Windows 11 install and uninstall pass | Retained clean-machine evidence |
| W9 UX | Non-developer completes the required workflow | Task-based user test |
| W10 Security | Local API, files, dependencies and package are reviewed | Security checklist and dependency audit |
| W11 Legal | Written Park evaluation/demo terms approved | Approved license and third-party rights review |
| W12 Reproducibility | Pinned input can be repeated and reconciled | Run manifest, IDs, hashes and tolerances |
| W13 Handoff | Park package and limitations are complete | Guide, demo script, sample export and limitations |

Skipped jobs are not PASS. A CI browser test does not prove a clean Windows installation. An API query does not prove source identity or model validity.

## 8. Full Park MVP remains a separate gate

The full Park MVP requires:

- Provenance-backed labelled DR24 cohort, target at least 100,000 light curves.
- Explicit source identity and cross-filter grouping.
- Versioned preprocessing and feature pipeline.
- Baseline and main CPU-first model.
- Object-level and temporal leakage-safe evaluation.
- Per-class metrics on eligible labelled data.
- Calibration, uncertainty and abstention evaluation.
- Scientific anomaly outputs separate from OOD diagnostics.
- Independent evaluation with population and taxonomy limits.
- Reproducible technical report and catalog export.
- Environment and run manifests.
- Complete workflow through the application, not scripts alone.

Do not mark the full Park MVP accepted when only the Windows preview passes.

## 9. Release deliverables

- Windows installer and signing status.
- SHA-256 checksum.
- Software version and exact source commit.
- Reproducible Windows build record.
- Dependency manifest or SBOM.
- Install, uninstall and quick-start guides.
- User guide and Park demo script.
- Known limitations and scientific claim boundary.
- Sample JSON export with provenance.
- Test summary, including skipped tests.
- Security and licensing status.
- Support and issue-reporting instructions.
- Data and model provenance notices.

Reconcile desktop versioning with the existing Python package version before tagging. Do not overwrite or relabel release v1.0.1.

## 10. Stop conditions

Do not publish or distribute the installer until:

1. The exact candidate commit passes required CI and package tests.
2. Desktop lifecycle and local API security tests pass.
3. Clean Windows 11 acceptance passes.
4. DR24 retrieval and JSON export pass on the target machine.
5. Park demo license terms are approved in writing.
6. No unsupported classification or discovery claim appears in the UI, report or presentation.

Issue #293 records a proprietary ownership direction. That decision does not itself create an approved Park evaluation license.

## 11. Current disposition

At draft time:

- Main has an API and browser Workbench, but no verified standalone Windows installer.
- The API entry point binds to 127.0.0.1:8000. Desktop lifecycle and safe port handling are not implemented there.
- Python package requires Python 3.11.5 and has no desktop shell or installer dependency in its package metadata.
- PR #307 is draft; its current exact-head CI is not yet green.
- Remote DR24 tests cover a small pinned sample. Local Windows acceptance remains unverified.
- Original production model authentication and DR24 feature compatibility remain blockers for classification.
- Written Park evaluation terms remain a legal blocker.

**Disposition: NOT READY FOR DISTRIBUTION.** Next: stabilise DR24 integration, prototype desktop shell, build Windows package, and complete clean-machine acceptance.
