# Astronomical Data Analysis & Discovery Platform — Product Roadmap

> **2026-11-24 ACTIVE ROADMAP OVERRIDE — COMPLETE PARK WINDOWS PROTOTYPE:** This roadmap is now gated by [the founder-approved scope freeze](../acceptance/PARK_WINDOWS_PRERELEASE_SCOPE_FREEZE_2026-11-24.md). Until the complete Windows-installable Park prototype has passed all four worksheet phases, clean-machine acceptance and Park presentation, only tasks directly required for the worksheet and technical-plan acceptance may execute. All work that does not map to the four Park acceptance phases is inactive backlog. CPVS, CIN runtime, cross-survey expansion, cross-platform packaging and broad platform expansion remain frozen. The previous web-only delivery decision is superseded for this stage. See the [Park requirements traceability matrix](../acceptance/PARK_PROTOTYPE_REQUIREMENTS_TRACEABILITY_2026-11-24.md) and [Issue #158](https://github.com/saeed92m/ztf-classifier/issues/158).

**Selected active milestone — 2026-11-25:** One English-only Windows-installable Park laboratory prototype. All four worksheet phases and the six-month technical roadmap are active as one delivery target: DR24 cohort, features, classification, calibration, abstention, anomaly analysis, SHAP, temporal/external validation, dashboard, reports and Windows packaging. CPVS, CIN, cross-survey expansion, macOS/Linux packaging and unrelated work remain frozen until Park presentation.

Status date: 2026-10-11  
Current immutable software release: v1.0.1  
Product implementation tracker: [Issue #158](https://github.com/saeed92m/ztf-classifier/issues/158)  
Inactive scientific backlog (not a current Park delivery task): [Issue #170](https://github.com/saeed92m/ztf-classifier/issues/170)

## Guiding constraints
- Preserve scientific baseline v0.2.0 and model identity baseline_v0.2.
- Keep the scientific gate fail-closed; missing evidence is never PASS.
- Build CPU-first, reproducible workflows for modest hardware.
- Separate classification, uncertainty/calibration, conformal prediction, OOD, anomaly evidence, catalog context, and explainability.
- Prefer source-backed, versioned adapters over copying datasets into Git.
- Every meaningful change updates its lifecycle record, tests, failure-prevention knowledge, and affected docs.

## Track A — Active Park prototype scientific acceptance work

### A1. CPVS exact-reproduction investigation — INACTIVE / FROZEN UNTIL PARK DELIVERY
- [ ] Trigger heavy workflow on an intended ci/heavy/* ref and verify source-provenance/scientific-gate-readiness executes.
- [ ] Re-run CPVS derivation after PR #173's finite/non-zero magnitude correction.
- [ ] Inspect acquisition report, derived membership, independent VizieR table, and hashes.
- [x] Verify the robust parser reads all 730,184 published ZTF names without duplicates.
- [x] Identify and correct the audit's invalid row-ordinal substitution: official CPVS lightcurve membership uses Table2 `Seq` (bytes 24–29), not physical row order.
- [ ] Rerun derivation and independent membership audit using actual Seq values; previous membership metrics are invalid and superseded.
- [ ] Explain the residual candidate/published membership difference from valid Seq-based evidence and source-backed selection semantics, not tuned thresholds.
- [ ] Require exact independent membership audit before claiming exact reconstruction.
- [ ] Keep Issue #170 open until evidence-based disposition.

### A2. Park prototype product and scientific acceptance — ACTIVE
- [ ] Acquire and pin the DR24 cohort. Meet the 100,000-labelled-curve technical-plan target.
- [ ] Acquire and pin the label sources. Record label provenance and limitations.
- [ ] Validate object identity, duplicates, cross-filter association, preprocessing, schema and failure codes.
- [ ] Build and validate the versioned feature pipeline.
- [ ] Reproduce the approved baseline without changing its frozen artifact, features or class order.
- [ ] Train and evaluate the selected XGBoost or LightGBM model on the pinned Park cohort.
- [ ] Complete object-level, label, temporal and feature leakage audits.
- [ ] Calibrate probabilities and evaluate uncertainty on a separate eligible set.
- [ ] Implement and evaluate abstention. Report Risk–Coverage and selective error.
- [ ] Implement a separate scientific anomaly method. Do not equate OOD with anomaly evidence.
- [ ] Generate reproducible SHAP explanations for eligible predictions.
- [ ] Complete temporal and independent external validation and the transferability report.
- [ ] Generate reproducible reports and exports with complete provenance.
- [ ] Ensure every required scientific gate runs rather than skips on release-candidate refs.

## Track B — Desktop application and user experience

### B1. Architecture foundation
- [ ] Freeze and test Application ↔ Scientific Core boundary.
- [ ] Define stable application-service, ingestion, provenance, configuration, and durable-state contracts.
- [ ] Ensure GUI uses the same service contracts as CLI/API and cannot bypass scientific validation.

### B2. Scientist-facing workflows
- [ ] Desktop shell and dashboard.
- [ ] Data Manager / import / source connection.
- [ ] Object/source explorer and light-curve visualization.
- [ ] Analysis workspace with features, model identity, class scores, calibration, uncertainty, abstention, OOD, anomaly evidence and provenance.
- [ ] SHAP explanation view for eligible predictions.
- [ ] Temporal and external validation reports.
- [ ] Results, visualization, reproducible scientific reports and exports.
- [ ] Discovery candidate workspace with review status and documented ranking limits.
- [ ] Settings, Help, troubleshooting, diagnostics and logs.

### B3. Distribution and usability
- [ ] Windows self-contained installer and first-run smoke test.
- [ ] Keep macOS and Linux packaging inactive until Park presentation.
- [ ] Clean-machine installation without Python/pip/Git/terminal for normal use.
- [ ] CPU-first performance and memory test on modest hardware.
- [ ] Installer integrity, checksums, release provenance and rollback/uninstall behavior.

## Track C — Unrelated capability expansion — INACTIVE UNTIL PARK DELIVERY
- [ ] Cross-survey expansion to Rubin/LSST or other surveys.
- [ ] New image or catalogue adapters that are not required for the Park taxonomy.
- [ ] Live drift-monitoring services beyond the required transferability report.
- [ ] Human feedback and annotation networks. Never silently convert feedback into ground truth.
- [ ] New product services, integrations and commercial features.

## Track D — Reliability, security, and release engineering (only tasks directly required by the Park Windows Pre-release are active)
- [ ] Test fresh installation, upgrade, uninstall, offline/poor-network failure, cache corruption, and missing-data paths.
- [ ] Test dependency locks, supply-chain/security checks, API auth, data handling, and safe export behavior.
- [ ] Preserve deterministic reports, input manifests, checksums, model identity, and audit trails.
- [ ] Every meaningful PR has a validated lifecycle cycle record and regression test.
- [ ] Every release has complete release notes, release description, checksums, provenance, and scientific/engineering gate evidence.

## Milestones and exit criteria

| Milestone | Exit criteria |
|---|---|
| M0 — Data and model readiness | Pinned DR24 cohort, label provenance, feature contract and approved baseline are verified. |
| M1 — Windows foundation | Application/service boundary, local security, workspace and installer are tested. |
| M2 — Classification workflow | Baseline and main model run from the application with leakage-safe evaluation. |
| M3 — Scientific reliability | Calibration, uncertainty, abstention, anomaly, SHAP and transferability evidence pass. |
| M4 — Park prototype acceptance | Dashboard, reports, exports, guides and clean-Windows workflow pass all required gates. |
| M5 — Park presentation | The installed prototype is presented. The result and feedback are recorded. |

No milestone is complete based on code presence alone. Completion requires measured evidence and recorded acceptance.

## Evidence update — 2026-10-11

A deeper source-schema review found that the previous audit mapped published ZTF names to parent row ordinals instead of the explicit CPVS Table2 `Seq` field (bytes 24–29), while lightcurve `SourceID` joins by `Seq`. Thus the 725,101 / 16,686 / 5,083 values from heavy run [#38095650470](https://github.com/saeed92m/ztf-classifier/actions/runs/38095650470) are invalid and superseded. PR [#176](https://github.com/saeed92m/ztf-classifier/pull/176) now reads actual Seq IDs for the derived candidate universe and published-name join. The Seq-based heavy run [#38121913146](https://github.com/saeed92m/ztf-classifier/actions/runs/38121913146) has completed: 741,786 candidates; 730,184 intersection; 11,602 candidate-only; 0 published-only; 0 duplicate and 0 unmapped published names. This is a valid identifier-space comparison, but exact CPVS reproduction remains **UNRESOLVED** because 11,602 candidates remain unexplained. The flag-zero variant yields 736,225 candidates / 724,712 intersection / 5,472 published-only; a magnitude 20.6 diagnostic loses 18,865 published objects. Neither is an acceptable fix. Current-head CI must pass and the residual selection semantics must be resolved or documented from evidence; do not tune thresholds to force cardinality equality. Source: https://cdsarc.cds.unistra.fr/viz-bin/ReadMe/J/ApJS/249/18?format=html&tex=true.
