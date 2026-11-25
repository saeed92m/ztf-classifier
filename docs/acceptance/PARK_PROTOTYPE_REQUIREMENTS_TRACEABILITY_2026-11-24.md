# Park Prototype Requirements Traceability Matrix

- Status: Active acceptance reference for the Windows-installable Park prototype
- Acceptance owner: Founder / Project Owner
- Primary tracker: Issue #158
- Scope policy: PARK_WINDOWS_PRERELEASE_SCOPE_FREEZE_2026-11-24.md
- Test plan: PARK_WINDOWS_PRERELEASE_TEST_PLAN.md
- Evidence date for the status table: 2026-11-24

## 1. Source documents and interpretation

This matrix uses the following submitted documents:

1. Park acceptance worksheet: 261007-091750-354.docx, form AP-02-140503.
2. Final technical project document: سند_پروژه_نسخه_نهایی.pdf.
3. Park presentation: ارائه_پارک_علم_و_فناوری_نسخه_نهایی.pdf.

The worksheet defines the product purpose, use cases, technical R&D areas and four delivery phases. The technical project document adds the prototype scope, model and feature plan, evaluation metrics, and the six-month monthly roadmap.

The Windows-installable delivery requirement and the freeze on unrelated work are explicit Founder decisions. Do not describe these decisions as direct quotations from the worksheet.

**Binding Founder decision — 2026-11-25:** The active delivery is one Windows-installable laboratory prototype that implements and validates all four worksheet phases. It is not a raw-data viewer-only preview. The active scope includes DR24 data, a labelled cohort, feature engineering, classification, calibrated uncertainty, abstention, anomaly analysis, explainability, temporal and external validation, a dashboard, reproducible reports and Windows packaging. The preview and installer are English-only and use left-to-right layout.

## 2. Requirements from the acceptance worksheet

| Source | Declared requirement | Testable acceptance evidence |
|---|---|---|
| 2.4 | Analyse public ZTF light curves and classify variable and transient objects | Run the full data-to-prediction workflow on a pinned and versioned population |
| 2.4 | Prioritise candidates and identify unusual objects | Separate ranking and anomaly outputs with documented methods |
| 2.4 | Provide confidence and uncertainty; abstain when evidence is weak | Calibrated probabilities, uncertainty metrics and a tested abstention policy |
| 2.4 | Use a CPU-first architecture | Build and run the supported workflow without a required high-end GPU |
| 2.5.1 | Automatic astronomical data analysis | Run the workflow from the application UI |
| 2.5.2 | Prioritise follow-up candidates | Rank candidates by model output, data quality and uncertainty |
| 2.5.3 | Identify rare and anomalous candidates | Use a defined anomaly method and an evaluated candidate list |
| 2.5.4 | Support research and reporting | Provide inspection, analysis, reports and exports |
| 2.5.6 | Provide installable software and an analytical dashboard | Install and use the Windows application without developer tools |
| 2.6 | Handle irregular, noisy light curves and class imbalance | QC, feature and model tests cover missing data, uneven sampling and class imbalance |
| 2.6 | Prevent overfitting and data leakage | Object-level and time-aware split tests |
| 2.6 | Calibrate probabilities and estimate uncertainty | Calibration evaluation on a separate eligible set |
| 2.6 | Support abstention | Risk–Coverage and selective-error report |
| 2.6 | Detect anomalies and explain outputs | Separate anomaly evaluation and reproducible SHAP output |
| 2.6 | Test generalisation | Temporal and independent external evaluation |
| 2.9–2.10 | Use DR24, preprocessing, feature extraction, XGBoost/LightGBM, uncertainty and anomaly methods | End-to-end workflow with versioned data, features, model and reports |
| 4.1 | Deliver four phases in six months | Evidence for each phase and the final Windows prototype |

## 3. Requirements from the technical project document

### 3.1 Data and cohort

- Primary source: ZTF DR24 HATS light curves in g, r and i filters.
- Supplementary calibration source: Zubercal DR20. Keep it separate from HATS and preserve cross-match ambiguity.
- Label sources: ALeRCE and SCoPe. Record each label source and its limits.
- Supplementary data: AllWISE and Gaia only when cross-matching is implemented and validated.
- The technical roadmap sets a minimum of 100,000 labelled light curves in Month 1.
- The technical document also describes a targeted cohort of several hundred thousand curves. Do not download the full 5.32-billion-curve release.
- The exact cohort size above the 100,000 minimum must follow the pinned acquisition plan and available resources.

Data acceptance:
1. Preserve source identifiers and object identifiers.
2. Record release, query, acquisition time, input/output counts and failures.
3. Keep labels and label provenance separate from raw data.
4. Do not silently drop incomplete records. Record the reason for each exclusion.
5. Store manifests and hashes for input and output data.
6. Keep HATS OIDs, ALeRCE OIDs and Zubercal PS1 IDs separate. Group records only when an approved identity record supports it.

### 3.2 Taxonomy and feature engineering

The prototype taxonomy includes transient, stochastic, periodic and eclipsing groups. It also includes Artifact / Unknown / Dubious as a quality-control class. Preserve the approved class definitions and order.

The technical document lists these feature families:
1. Basic statistical features.
2. Quantile features.
3. Periodic and frequency features.
4. Light-curve shape features.
5. Colour and supplementary catalogue features.
6. Quality and validation features.

Each feature must have a definition, unit, schema version, missing-data rule and test. Do not silently alter the frozen v0.2.0 feature contract.

### 3.3 Models and evaluation

The technical document proposes:
- Logistic Regression and k-NN as simple baselines.
- Balanced Random Forest as a baseline.
- XGBoost or LightGBM as the main CPU-first model.
- Isotonic or Platt calibration and conformal prediction for uncertainty.
- Isolation Forest or a suitable semi-supervised method for anomaly analysis.
- SHAP for model explanations.

Required evaluation includes:
- Balanced Accuracy and Macro-F1.
- Per-class precision and recall.
- Confusion matrix.
- ROC-AUC and PR-AUC where valid.
- ECE, MCE and Brier score.
- Risk–Coverage and selective error.
- Temporal split.
- Independent external evaluation.

Use object-level and temporal splits. Check overlap between training, calibration and test populations. ALeRCE labels are benchmark labels. Do not describe them as independent ground truth.

## 4. Six-month delivery plan

| Month | Phase | Main work | Required output |
|---|---|---|---|
| 1 | Infrastructure and data | Environment, DR24, labelled cohort, retrieval and cache | At least 100,000 labelled curves with a data manifest |
| 2 | Features and baseline | Feature families and Balanced Random Forest | Feature report, confusion matrix and baseline |
| 3 | Main model | XGBoost/LightGBM, tuning and SHAP | Main model and baseline comparison |
| 4 | Uncertainty and anomaly | Calibration, conformal prediction, abstention and Isolation Forest | Calibration curves, Risk–Coverage and anomaly candidates |
| 5 | Validation and transferability | Temporal split, external test and error analysis | Comparative validation report |
| 6 | Demonstration and documentation | Dashboard/API, paper draft, Park acceptance file | Live demo, technical package and Park handoff |

The worksheet groups the work into four phases of 2 + 1 + 2 + 1 months. This table provides the monthly detail from the technical project document. It is a plan, not evidence of completion.

## 5. Windows delivery requirements

The Founder requires a GitHub Pre-release that installs on Windows.

Acceptance tests:
- Install on a clean Windows system.
- Launch without Python, pip, Git or a terminal.
- Run the full scientific workflow from the application.
- Retrieve data and show provenance.
- Save and reopen a workspace and its results.
- Test failure handling and restart.
- Uninstall without deleting user data.
- Provide a build manifest, dependency lock, checksum and test report.

The installer is unsigned unless a valid code signature is added. A checksum is not a code signature. Obtain written Park evaluation terms before external distribution.

## 6. Evidence status recorded on 2026-11-24

| Requirement | Recorded state | Evidence and limitation |
|---|---|---|
| DR24 raw acquisition | PARTIAL | Bounded HATS retrieval exists for 1–10 OIDs per request. |
| Descriptive summaries | PARTIAL | Source-native descriptive statistics exist. They are not model features. |
| Windows shell | PARTIAL | PyInstaller one-folder build and frozen self-test passed in an earlier run. |
| Windows installer | BLOCKED / RETESTING | Earlier runs failed at NSIS discovery or language setup. The installer was changed to English-only. Exact-head installer evidence is required. |
| Clean Windows user launch | NOT VERIFIED | A frozen self-test does not prove the complete interactive workflow on a clean device. |
| Windows dependency lock | BLOCKED | A pip freeze output is not a reviewed, reproducible input lock. |
| 100,000 labelled curves | NOT VERIFIED | No complete pinned cohort manifest and acquisition report were accepted in this evidence snapshot. |
| Feature pipeline on Park cohort | NOT ACCEPTED | The frozen feature contract exists. DR24 parity and cohort outputs are not proven. |
| Frozen v0.2.0 production model | BLOCKED | Issue #282 records the artifact-recovery blocker. A lab-smoke artifact is not a substitute. |
| Main XGBoost/LightGBM Park model | NOT VERIFIED | No accepted Park-population model and independent report were verified. |
| SHAP explanations | NOT VERIFIED | No accepted end-to-end SHAP path for the Park cohort was verified. |
| Calibration / conformal / abstention | NOT VERIFIED for Park population | Requires an authenticated model and separate eligible evaluation sets. |
| Anomaly detection | NOT VERIFIED | OOD diagnostics alone do not prove anomaly detection. |
| Temporal / external validation | NOT VERIFIED | No final Park-population transferability report was verified. |
| Scientific reports and exports | PARTIAL | Raw JSON export exists. The full scientific report and catalogue are not accepted. |
| Guided demonstration | NOT ACCEPTED | A 30–50-object end-to-end demo is not yet accepted. Current retrieval is limited to 1–10 OIDs per request. |
| Park handoff | NOT STARTED | No accepted Windows installer or presentation record exists. |

These states are historical evidence from the stated date. Refresh them from exact commits and workflow runs before a release decision.

## 7. Active execution path

All four worksheet phases are active because they form one Park prototype acceptance target.

1. Complete DR24 data, identity, cohort and provenance contracts.
2. Complete and validate the feature pipeline on the pinned cohort.
3. Resolve the approved model-artifact and input-compatibility blockers.
4. Reproduce the baseline and evaluate the main model.
5. Implement calibration, uncertainty and abstention with separate evaluation evidence.
6. Implement anomaly analysis separately from OOD diagnostics.
7. Implement SHAP explanations and reproducible technical reports.
8. Complete temporal and independent external validation.
9. Integrate the complete workflow into the English-only Windows application.
10. Complete installer, clean-machine tests, documentation and Park handoff.

Do not present a blocked capability as complete. The Park prototype is NOT READY until every mandatory gate passes.

## 8. Frozen workstreams

The following work remains outside the active delivery:
- CPVS reconstruction and the 11,602-object discrepancy.
- Independent CPVS diagnostics, retrieval and code changes.
- Cosmic Intelligence Network implementation.
- macOS/Linux packaging.
- Cross-survey expansion and unrelated platform work.

The CPVS discrepancy remains unresolved. This scope decision does not resolve it. Keep its historical evidence intact. Do not run CPVS workflows before Park presentation.

## 9. Final readiness definition

The prototype is ready for presentation only when:
1. Every required worksheet and technical-plan item has a tested implementation and evidence.
2. The UI and reports do not overstate any capability.
3. The full workflow passes from the installed application on clean Windows.
4. Data, feature, model, split, output and provenance manifests are complete.
5. The GitHub Pre-release and installation documents are ready.
6. The prototype is presented to the Park and the result is recorded.

Until then, the status remains **NOT READY FOR PARK PRESENTATION**.
