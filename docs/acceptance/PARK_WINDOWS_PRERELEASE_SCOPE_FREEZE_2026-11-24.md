# Park Windows Prototype — Binding Scope Freeze

- Decision date: 2026-11-25
- Status: ACTIVE / FOUNDER-APPROVED
- Owner: Founder / Project Owner
- Delivery tracker: Issue #158
- Primary acceptance contract: PARK_WINDOWS_DESKTOP_BETA_ACCEPTANCE_2026-11-24.md
- Source documents: Park acceptance worksheet AP-02-140503 and the final technical project document

## 1. Binding decision

The only active project objective is to deliver the first useful, Windows-installable Park laboratory prototype.

The prototype must implement and validate the four phases in the submitted acceptance worksheet:

1. Infrastructure, DR24 data, a labelled cohort and feature engineering.
2. Baseline and main XGBoost or LightGBM classification with initial evaluation.
3. Calibrated uncertainty, abstention, anomaly analysis and validation.
4. Dashboard, documentation, reproducible reports and software-registration preparation.

A raw-data viewer, a desktop shell or a successful installer alone does not meet the Park claims.

The final technical project document sets a minimum target of 100,000 labelled light curves for the first six-month roadmap. The acceptance worksheet does not state this number. Treat it as a technical-plan requirement, not as a quotation from the worksheet.

The preview and installer must be English-only. Use plain, direct English. Use short sentences and familiar terms. Keep standard astronomical terms, units, identifiers and scientific labels unchanged. The UI must use left-to-right layout. Do not add Persian text or RTL layout to this delivery.

The scope freeze remains active until:
- all required scientific and product gates pass;
- the exact Windows installer passes clean-machine tests;
- the complete workflow runs from the installed application;
- the package and evidence are presented to the Park; and
- the presentation result is recorded.

## 2. Source and decision hierarchy

The active scope uses these sources:

1. Park acceptance worksheet 261007-091750-354.docx, form AP-02-140503:
   - Section 2.4: product purpose and scientific claims.
   - Section 2.5: product use cases and installable software.
   - Section 2.6: R&D complexity.
   - Sections 2.9–2.10: architecture, data, features, models, uncertainty, anomaly analysis, validation and delivery.
   - Section 4.1: four phases and the six-month schedule.
2. Final technical project document:
   - prototype scope and taxonomy;
   - the 100,000-labelled-light-curve minimum;
   - feature families, model plan and evaluation metrics;
   - six-month roadmap and measurable outputs.
3. Founder decisions in this project:
   - deliver a Windows-installable prototype;
   - use English only for this experimental release;
   - keep CPVS and the 11,602-object discrepancy outside the active work;
   - stop all work that does not directly support Park acceptance.

If a summary conflicts with the source documents, use the source documents and this current Founder decision. Do not describe a Founder decision as a direct quotation from the worksheet.

## 3. Active work

Only the following work is authorised.

### Phase 1 — Infrastructure, data and features

- Build and test the Windows desktop shell and local service lifecycle.
- Acquire the declared ZTF DR24 data.
- Build a pinned labelled cohort. The technical-plan target is at least 100,000 light curves.
- Record source, release, query, object IDs, filters, labels, schemas, hashes and acquisition times.
- Validate object identity and cross-filter grouping.
- Define and test the photometry, time, quality and missing-data contracts.
- Build the versioned feature pipeline.
- Record feature definitions, units, software versions and failure states.

### Phase 2 — Baseline and main model

- Reproduce the approved baseline.
- Train and evaluate the selected CPU-first XGBoost or LightGBM model.
- Use object-level and time-aware data splits.
- Prevent object, label, temporal and feature leakage.
- Report per-class metrics, Balanced Accuracy, Macro-F1, precision, recall, confusion matrix, ROC-AUC and PR-AUC where valid.
- Record the model artifact, taxonomy, feature set, split, configuration and hashes.

### Phase 3 — Uncertainty, anomaly and validation

- Calibrate probabilities on a separate calibration set.
- Evaluate calibration with ECE, MCE and Brier score.
- Implement and evaluate the abstention policy.
- Report Risk–Coverage and selective error.
- Implement a separate anomaly-analysis path. Do not treat OOD scores as anomaly evidence.
- Add SHAP explanations for eligible model outputs.
- Run temporal validation and an independent external evaluation.
- Produce a transferability report with population limits and failure cases.

### Phase 4 — Product and handoff

- Integrate the full workflow into the Windows application.
- Provide a dashboard for data, features, model outputs, uncertainty, abstention, anomalies and reports.
- Provide reproducible exports and run manifests.
- Complete user and installation guides.
- Complete release notes, known limitations and the Park demo script.
- Build the Windows installer and verify it on a clean Windows system.
- Present the installed prototype and record Park feedback.

Every task, issue, pull request, commit and workflow must map to one of these acceptance items.

## 4. Frozen workstreams

The following work must not run before Park presentation:

- CPVS reconstruction, the 11,602-object discrepancy, CPVS diagnostics, data retrieval or code changes.
- Cosmic Intelligence Network implementation.
- Cross-survey expansion to Rubin/LSST or other surveys.
- macOS or Linux desktop packaging.
- New platform services, user networks or unrelated integrations.
- New models or datasets that do not support the stated Park taxonomy and acceptance claims.
- Broad refactoring or dependency changes without a direct acceptance need.
- Commercial features that are not required for the Park prototype.
- Persian localization or right-to-left layout.

CPVS remains an unresolved scientific issue. This freeze does not resolve it. Do not change its status or claim that it is fixed. Keep its historical evidence intact. Do not run its workflows during this delivery stage.

The v0.2.0 scientific baseline remains protected. Do not change its model, features, class order, benchmark, cutoff or acceptance criteria without a separate evidence-based review and written approval. Use the approved baseline where it supports the Park workflow.

## 5. Mandatory scope gate

Before starting work, answer this question:

> Does this task directly implement, test, document or unblock one of the four Park phases or a required Windows acceptance gate?

- Yes: the task may proceed. Define its acceptance test and evidence first.
- No: do not start the task. Keep it in the inactive backlog.
- Unclear: stop and clarify the link to an acceptance item.
- Scope changes require a new written Founder decision.

An existing issue, pull request, scheduled workflow, CI job or think-tank suggestion is not permission to expand scope.

## 6. Acceptance gates

Use only these states: PASS, FAIL, BLOCKED, NOT RUN or NOT APPLICABLE.

| Gate | Required result |
|---|---|
| G1 — Scope | Every UI claim maps to a requirement and an acceptance test. |
| G2 — Data | DR24 cohort, labels, identity and provenance are pinned and reconciled. |
| G3 — Features | The versioned feature pipeline passes schema, numerical and regression tests. |
| G4 — Baseline | The approved baseline is reproduced without changes to frozen artifacts. |
| G5 — Main model | XGBoost or LightGBM evaluation passes leakage-safe tests. |
| G6 — Calibration | Calibration metrics and plots are produced on a separate eligible set. |
| G7 — Abstention | Risk–Coverage and selective error are measured. |
| G8 — Anomaly | Anomaly results use a separate validated method and evidence. |
| G9 — Explainability | SHAP output is reproducible and tied to the exact model and input. |
| G10 — Transferability | Temporal and external evaluation reports are complete. |
| G11 — Desktop | The full workflow runs from the installed Windows application. |
| G12 — Security | Local API, WebView, file access and dependencies pass review. |
| G13 — Installer | Clean Windows install, launch, restart, update/uninstall and data preservation pass. |
| G14 — Reproducibility | Inputs, code, features, model, split, outputs and hashes are recorded. |
| G15 — Handoff | Guides, limitations, demo script, release notes and evidence are complete. |
| G16 — Park delivery | The prototype is presented and the result is recorded. |

A skipped test is not PASS. A green CI workflow does not prove scientific validity. A successful installer does not prove the scientific workflow.

## 7. English and STE100 requirement

All user-facing preview content must be in English:
- installer pages and error messages;
- desktop navigation and screens;
- status messages and validation errors;
- plots, tables, labels and tooltips;
- help, about, export labels and report headings.

Use short sentences. Use one instruction per sentence. Prefer active voice. Use consistent terms. Do not use Persian characters or RTL layout in preview assets.

Add automated tests that fail if Persian text or RTL settings return to the preview UI.

## 8. Think-tank oversight

The 16 think-tank roles provide simulated specialist reviews. They are not 16 independent human approvals.

The review must cover:
- scientific correctness and claim limits;
- ZTF data and astrophysical identity;
- statistics, feature engineering and leakage;
- model quality, calibration and abstention;
- anomaly evidence and explainability;
- independent and temporal validation;
- application architecture and Windows runtime;
- security, QA, usability and reproducibility;
- documentation and Park handoff.

Each review must identify evidence, risks, blockers and the next acceptance test. No role may expand the scope without written Founder approval.

## 9. End of freeze

The Founder / Project Owner is the only authority who can end this freeze.

The freeze ends only after all four conditions pass:
1. All required worksheet and technical-plan gates pass.
2. The Windows installer and complete workflow pass on a clean Windows system.
3. The prototype is presented to the Park.
4. The result and any required follow-up actions are recorded.

Until then, no inactive workstream may start.
