# Park Prototype Think-Tank Review

- Review date: 2026-11-25
- Scope: First Windows-installable Park laboratory prototype
- Review basis: Park acceptance worksheet AP-02-140503, final technical project document, current GitHub source and recorded workflow evidence
- Status: ADVISORY REVIEW. This is a simulated role-based review, not approval by 16 independent human experts.

## Executive decision

**NOT READY FOR PARK PRESENTATION.**

The current Windows branch has useful engineering foundations. It has a local desktop shell, workspace persistence, bounded DR24 retrieval, raw-data inspection and provenance-aware JSON export.

These features do not yet meet the complete Park claims.

The active delivery must include all four worksheet phases:
1. DR24 data, a labelled cohort and feature engineering.
2. Baseline and XGBoost/LightGBM classification.
3. Calibrated uncertainty, abstention, anomaly analysis and validation.
4. Dashboard, reproducible reports, documentation and Windows packaging.

Do not describe the current branch as a complete Park prototype.

## Evidence reviewed

### Repository evidence

- The frozen v0.2.0 benchmark manifest records 150 objects, 15 classes and 42 features.
- The frozen production model artifact is not present in the inspected repository tree or the supplied all-refs Git bundle. A scan of all bundled refs found no production model artifact.
- Issue #282 records that the original model artifact was not found in repository history, release assets, retained CI artifacts, Dropbox or the supplied local audit. A fresh GitHub Releases audit found only Python wheel and source archives in v1.0.1, v1.0.0 and v0.5.0; none contains the model artifact.
- The supplied local audit also reports that the ALeRCE raw-detection cache is absent. It does not include a fresh audit of the current branch.
- The desktop branch contains DR24 raw retrieval and descriptive statistics. The descriptive policy explicitly states DESCRIPTIVE_NOT_CLASSIFICATION.
- The API has model-registry and inference routes. It requires a valid model artifact.
- The repository has feature, model, calibration, conformal, OOD and scientific-anomaly components. Their presence does not prove that a complete Park workflow runs.
- The current desktop UI hides the classification, uncertainty and scientific-validation workspaces.
- The Windows installer uses the English NSIS language resource. The desktop static assets use English and left-to-right layout.
- Exact-head Windows workflow run 45561977822 failed at Ruff formatting. It passed 18 desktop/workspace tests and JavaScript syntax checks. The build, installer and install/uninstall steps were skipped.
- The next Windows workflow run was started after the formatting correction. Its result must be checked against the exact current head.

### Source-document evidence

- The acceptance worksheet defines four phases over six months.
- The technical project document sets a minimum target of 100,000 labelled light curves.
- The technical document describes a targeted subset of several hundred thousand curves. It does not require downloading the full 5.32-billion-curve DR24 release.
- The technical document defines a CPU-first XGBoost/LightGBM workflow, calibration, abstention, anomaly analysis, temporal validation and an installable dashboard.

## Label-source assessment

The data-source assessment is recorded in PARK_LABELLED_DATA_SOURCE_ASSESSMENT_2026-11-25.md.

Key findings:
- ALeRCE 2020 provides a frozen 15-class labelled set through 2020-06-09. Its 868,371-object output file contains predictions for an unlabeled population. Do not use those predictions as ground truth.
- ALeRCE TAP is the current supported access path for public ZTF object, detection, feature, probability and taxonomy tables. Use TAP or the API. Do not use retired direct database connections. Broker probabilities are not independent labels.
- SCoPe provides 170,632 light curves and 85,136 manually reviewed sources. Its multi-label taxonomy differs from ALeRCE. Use it only for a reviewed external evaluation or a separately versioned model.
- The 2025 ALeRCE paper reports 219,792 labelled sources and 16 subclasses, including TDE. The inspected paper does not provide a clear public DOI for the complete labelled-source manifest. Do not add TDE to the frozen 15-class taxonomy.
- No source has yet been accepted as the complete 100,000-labelled-light-curve DR24 cohort.

## Sixteen role reviews

| Role | Finding | Required action |
|---|---|---|
| 1. Chief Scientist / PI | The current raw-data workflow is not the claimed classifier. | Keep the release NOT READY until all scientific phases pass. |
| 2. ZTF Data Specialist | DR24 retrieval is bounded and source-native. It is not yet a validated model-input pipeline. | Validate time, photometry, quality flags, filters and identity contracts. |
| 3. Time-Domain Astrophysicist | OID does not prove physical-source identity. | Preserve OIDs and require explicit cross-match evidence before grouping. |
| 4. Statistics Specialist | The 150-object benchmark is too small to support broad population claims. | Use the pinned labelled cohort and leakage-safe evaluation. Report class-level limits. |
| 5. Astroinformatics / Data Engineering | The 100,000-object target needs a reproducible acquisition pipeline. | Build a manifest-first, chunked DR24 acquisition process. Do not download the full catalogue. |
| 6. Feature Engineering Specialist | The frozen 42-feature schema is defined for the v0.2.0 baseline. DR24 parity is not established. | Validate every feature, unit, missing-value rule and input mapping. Do not silently change v0.2.0. |
| 7. Machine Learning Specialist | The original production model artifact is missing. | Recover and authenticate it. If recovery fails, propose a separately versioned new model. Do not call it the original baseline. |
| 8. Model Validation Specialist | Calibration and conformal code exists, but no accepted Park-population evidence is available. | Use separate training, calibration and test sets. Report ECE, MCE, Brier score and Risk–Coverage. |
| 9. Anomaly Specialist | OOD scores and scientific anomaly evidence are different outputs. | Implement and evaluate a separate anomaly method. Keep the two channels separate. |
| 10. Explainability Specialist | SHAP is a dependency and code component, not an accepted user workflow. | Produce reproducible explanations tied to exact model, feature schema and input. |
| 11. Cross-Match Specialist | Cross-filter records must not be grouped by OID alone. | Record identity evidence and preserve unresolved associations. |
| 12. Software Architect | The local desktop shell is a useful base. The scientific application workflow is incomplete. | Integrate one end-to-end workflow. Avoid unrelated architecture changes. |
| 13. Backend / API Engineer | Model routes require a configured model registry. The production artifact is absent. | Add clear readiness and failure states. Do not return placeholder predictions. |
| 14. MLOps / Security Specialist | The installer is unsigned. Runtime security has not passed clean-Windows review. | Complete dependency lock, package audit, local API review, WebView2 tests and signing decision. |
| 15. QA / Reliability Specialist | CI does not prove a working Windows installation. | Test install, launch, restart, data workflow, export, uninstall and data preservation on clean Windows. |
| 16. Product / UX / Red Team | A raw viewer is not the product claimed in the Park documents. | Keep all four phases in scope. Use English-only STE100 text. Reject unsupported claims. |

## Critical blockers

| ID | Blocker | State | Exit evidence |
|---|---|---|---|
| B01 | Original v0.2.0 production model artifact | BLOCKED | Original artifact and independently trusted hashes |
| B02 | ALeRCE labelled/raw source inputs | BLOCKED / PARTIAL | Pinned cohort, label provenance and source-backed acquisition report |
| B03 | DR24-to-feature compatibility | NOT VERIFIED | Feature parity report and regression tests |
| B04 | 100,000 labelled-object cohort | NOT VERIFIED | Complete manifest, count reconciliation and hashes |
| B05 | Main model on Park cohort | NOT VERIFIED | Model artifact and leakage-safe evaluation report |
| B06 | Calibration and abstention | NOT VERIFIED | Separate calibration data, metrics and Risk–Coverage report |
| B07 | Scientific anomaly analysis | NOT VERIFIED | Separate method and evaluated anomaly evidence |
| B08 | SHAP explanations | NOT VERIFIED | Reproducible model-linked explanation output |
| B09 | Temporal and external validation | NOT VERIFIED | Transferability report and failure analysis |
| B10 | Full Windows acceptance | NOT VERIFIED | Exact-head installer and clean-machine evidence |
| B11 | Park evaluation/distribution terms | BLOCKED | Written approval |

## Decisions and controls

1. Keep all four Park phases active as one delivery target.
2. Keep CPVS and the 11,602-object discrepancy frozen until Park presentation.
3. Preserve the v0.2.0 baseline. Do not rebuild or relabel its missing production artifact.
4. If the original artifact cannot be recovered, create a new model version only through a separate, documented and validated workflow. Keep it separate from v0.2.0.
5. Do not use ALeRCE predictions as independent ground truth.
6. Do not present OOD scores as scientific anomaly detections.
7. Keep all user-facing text in English. Use short sentences and active voice. Keep the UI LTR.
8. Keep the installer unsigned status visible until code signing is complete.
9. Do not distribute the installer before written Park evaluation terms are approved.
10. Do not merge or release until exact-head CI, scientific gates and clean-Windows acceptance pass.

## Next execution order

1. Complete the current Windows installer build and resolve all exact-head failures.
2. Verify the English-only UI and installer with automated tests.
3. Audit the full current branch and integration dependencies.
4. Define the Park cohort contract and labelled-source mapping.
5. Resolve the original model artifact blocker or approve a separate new-model plan.
6. Validate DR24 preprocessing and the feature pipeline.
7. Train and evaluate the main model on the pinned labelled cohort.
8. Complete calibration, abstention, anomaly, SHAP and transferability evidence.
9. Integrate the complete scientific workflow into the Windows application.
10. Complete clean-Windows acceptance and the Park handoff package.

The review does not approve the current branch for distribution. It defines the evidence needed for the first Park prototype.
