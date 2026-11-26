# Windows Experimental Desktop — UX and Product Design Brief

**Status:** Draft for implementation review  
**Date:** 2026-11-24  
**Product:** ZTF Classifier — Astronomical Data Analysis & Discovery Platform  
**Target:** First standalone Windows 11 experimental build for the Tabriz Science and Technology Park

## 1. Product decision

The project owner selected a standalone Windows desktop application. A normal evaluator must be able to install and launch it from Windows without Python, pip, Git, a virtual environment, or a terminal.

The Park application form is the source of product claims. The first Windows build must demonstrate useful, real ZTF work. A polished shell with simulated measurements is not an acceptable prototype.

The UI/UX work starts in parallel with API, data, scientific-validation, and packaging work.

## 2. Users and core tasks

Primary user: an astronomer, research student, or technical evaluator who is not expected to use a terminal.

The first-run user must be able to:

1. Open the app and understand its current readiness and data-source status.
2. Search for or enter a supported ZTF object identifier.
3. Retrieve available DR24 light-curve observations through the approved adapter.
4. Inspect observations by filter, light curve, sampling, magnitude statistics, and quality flags.
5. Run only the analysis methods that the selected data and validated contracts support.
6. Understand which outputs are available, diagnostic-only, blocked, or not run.
7. Export a reproducible report and machine-readable evidence bundle.
8. Find Help and understand the limits of the result.

## 3. Information architecture

Use a persistent left navigation with these areas:

| Area | Purpose in the Windows experiment |
|---|---|
| Dashboard | Recent runs, source status, validation state, and a guided first action |
| Data Manager | DR24 query, supported import, query history, and data inventory |
| Object Explorer | Search, identity, coordinates when available, per-filter light curves, and observation table |
| Analysis | Documented preprocessing/QC and approved feature extraction only |
| Results | Descriptive findings and, only when enabled by evidence, prediction results |
| Discovery | Candidate review and anomaly evidence only after the relevant implementation and validation |
| Provenance | Run ID, source, query, IDs, hashes, software/schema/model identity, warnings, and evidence lineage |
| Reports | Export catalog, report, and reproducibility bundle |
| Help | Guided workflow, data-source help, result interpretation, limitations, and troubleshooting |
| Settings | Language, appearance, data paths, cache, and privacy controls |

Do not show disabled future functionality as if it were operational. Use an explicit disabled state with a short reason.

## 4. Main screen composition

### Dashboard
- Header: product name, app version, and local service state.
- Primary action: **Explore a ZTF object**.
- Secondary actions: open a recent project, import supported data, view prior runs.
- Status area: DR24 source availability, cache state, model artifact state, and scientific gate state.
- Recent runs table with run ID, date, input count, status, and export availability.

### Object Explorer
- Search row: identifier, source choice, filter, and retrieval controls.
- Identity panel: submitted OID and catalog identifiers kept distinct; coordinates only when returned by source evidence.
- Main plot: magnitude against source-native time. Do not relabel HMJD as MJD.
- Filter controls: g and r are separate data series and separate records. Do not imply both bands exist when only one exists.
- Observation table: time, magnitude, magnitude error, filter, catflags, and source-native fields.
- Summary panel: counts, time span, sampling interval, magnitude distribution, missing values, and quality diagnostics.
- Provenance drawer: retrieval query, returned IDs, response hashes, timestamps, and warnings.

### Analysis and Results
- Wizard: select input → review source/QC → choose supported operation → run → inspect → export.
- Every method shows its contract/version and its status.
- The model result region must display **NOT RUN** or **BLOCKED** when inference did not run. It must not show sample probabilities, placeholder class names, or invented accuracy.
- Calibrated probabilities, abstention, OOD, anomaly, and explainability are separate result channels. Do not merge them into one confidence score.
- A skipped gate is shown as **SKIPPED / NOT VERIFIED**, never PASS.

### Reports
- Preview a report before export.
- Include Run ID, software commit, source/query, object IDs, filters, counts, source and normalized hashes when available, schema versions, configuration, warnings, skipped stages, and model identity or NOT RUN.
- Exports must use versioned, documented schemas.

## 5. User flows

### Flow A — first successful exploration
Launch → welcome and limitations → choose DR24 → enter supported OID/query → preview returned IDs and filters → retrieve → inspect light curve and observations → view source-native summary and QC → export evidence/report.

### Flow B — local supported-data import
Launch → Data Manager → choose a declared CSV/Parquet adapter → inspect schema and file hash → validate → preview rejected/missing rows and reasons → save as a new run → inspect and export.

Do not advertise arbitrary CSV, FITS, or AVRO support unless the corresponding adapter exists and has tests.

### Flow C — model inference
Select dataset → validate data contract → verify authenticated model and feature schema → run only when all required gates pass → show probabilities, calibration, abstention, OOD and anomaly in distinct sections → export evidence.

If any gate fails or is unavailable, stop inference and explain the exact reason. The present production v0.2.0 artifact is not yet authenticated; the UI must therefore not imply production inference is ready.

## 6. Visual design direction

- Scientific workstation, not a consumer dashboard.
- Dark astronomy-inspired default with a fully usable light theme.
- Calm hierarchy: one primary action per page, restrained accent colors, consistent spacing and typography.
- Dense tables and plots may support technical detail, but important status and next steps must remain readable.
- Keep chart axes, units, filter identity, time semantics, data gaps, and uncertainty visible.
- Use distinct visual treatment for observations, warnings, diagnostic outputs, and validated scientific outputs.
- Use accessible contrast, keyboard focus, readable text sizes, and non-color-only status labels.
- Avoid ornamental star fields, excessive glow, animation, and decorative metrics that reduce scientific readability.

## 7. Localization

For the Park demonstration, use Persian as the default UI language. Preserve standard English scientific names and abbreviations next to Persian labels where this reduces ambiguity (for example HMJD, OID, catflags, OOD, Macro-F1).

Store display strings in localization resources. Do not embed Persian-only labels throughout the application logic. Keep the architecture ready for English localization.

## 8. Scientific status language

Use one consistent set of statuses across the app, reports, and logs:

- **READY** — prerequisites for this operation are present.
- **RUNNING** — operation is active.
- **COMPLETE** — operation completed; this does not imply scientific validation.
- **DIAGNOSTIC ONLY** — descriptive or exploratory output only.
- **BLOCKED** — a required prerequisite is missing or a gate failed.
- **NOT RUN** — operation was not executed.
- **SKIPPED / NOT VERIFIED** — a validation stage did not execute.
- **VALIDATED** — use only when the named, versioned validation protocol passed.

Do not use a general green success indicator for an operation that completed without scientific validation.

## 9. First release scope boundary

The minimum useful desktop demonstration is a real, provenance-backed DR24 exploration workflow with separate filter views, descriptive statistics, QC, run history, and reproducible export.

The following features are not to be presented as validated or enabled merely to match the application form:
- production v0.2.0 inference before recovery and independent authentication of the original artifact;
- DR24-to-v0.2 feature generation before the time, photometry, filter, QC, grouping, and 42-feature contracts pass;
- confirmed physical-source cross-match before AOIC evidence exists;
- calibrated probabilities, abstention, OOD or anomaly claims before their respective evaluation gates pass;
- discovery ranking before the score and its scientific interpretation are validated.

The Park application form describes these as product objectives. The software must show actual progress and limitations, not convert planned outputs into current claims.

## 10. UX acceptance tests

- A new user can identify the first action without Help.
- A new user can retrieve and inspect a supported DR24 object without terminal access.
- g/r filters are distinguished and missing bands are explicit.
- Source-native time and magnitude are shown without silent conversion.
- Catflags and missing observations are visible; no hidden row filtering is implied.
- The user can identify the run and reproduce the source query from the report.
- The user can see whether inference actually ran and why it was blocked or skipped.
- Exported JSON and reports pass schema/round-trip checks.
- Keyboard navigation and visible focus work on all primary controls.
- The UI remains usable at common laptop resolutions and Windows display scaling.

## 11. Review

This brief is intended for the project's simulated 16-seat specialist review. It is not external human peer review. Each reviewer must record evidence, risks, dissent, and acceptance conditions. Changes to the claims or release boundary require a recorded owner decision.

## 12. Evidence references

- Owner-approved Park application form and final Park presentation (uploaded project documents).
- `docs/architecture/V1_PRODUCT_ARCHITECTURE.md`
- `docs/ECOSYSTEM_REVIEW_PRODUCT_EXPANSION_2026-10-08.md`
- Issues #158, #253, #249, #282, #293, and #305.
