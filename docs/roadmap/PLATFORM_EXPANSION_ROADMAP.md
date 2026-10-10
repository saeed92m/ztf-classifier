# Astronomical Data Analysis & Discovery Platform — Product Roadmap

Status date: 2026-10-11  
Current immutable software release: v1.0.1  
Product implementation tracker: [Issue #158](https://github.com/saeed92m/ztf-classifier/issues/158)  
Scientific blocker: [Issue #170](https://github.com/saeed92m/ztf-classifier/issues/170)

## Guiding constraints
- Preserve scientific baseline v0.2.0 and model identity baseline_v0.2.
- Keep the scientific gate fail-closed; missing evidence is never PASS.
- Build CPU-first, reproducible workflows for modest hardware.
- Separate classification, uncertainty/calibration, conformal prediction, OOD, anomaly evidence, catalog context, and explainability.
- Prefer source-backed, versioned adapters over copying datasets into Git.
- Every meaningful change updates its lifecycle record, tests, failure-prevention knowledge, and affected docs.

## Track A — Scientific integrity and external evidence

### A1. CPVS exact-reproduction investigation — OPEN / UNRESOLVED
- [ ] Trigger heavy workflow on an intended ci/heavy/* ref and verify source-provenance/scientific-gate-readiness executes.
- [ ] Re-run CPVS derivation after PR #173's finite/non-zero magnitude correction.
- [ ] Inspect acquisition report, derived membership, independent VizieR table, and hashes.
- [ ] Verify Table 4 internal ID ↔ ZTF name ↔ parent-row mapping; investigate IDs 781603/781604 and representative candidate-only IDs.
- [ ] Explain the remaining candidate-only population using published selection semantics, not tuned thresholds.
- [ ] Require exact independent membership audit before claiming exact reconstruction.
- [ ] Keep Issue #170 open until evidence-based disposition.

### A2. Product-level validation — RELEASE-BLOCKING
- [ ] Complete pinned ZTF DR24 source-backed adapter execution.
- [ ] Complete frozen historical ALeRCE reference acquisition/execution and immutable manifests.
- [ ] Complete object-overlap, duplicate, target leakage, temporal leakage, preprocessing, schema, provenance, and failure-code audits.
- [ ] Generate per-release benchmark evidence and show scope limits/known failure cases to users.
- [ ] Ensure required scientific gates run rather than skip on release-candidate refs.

## Track B — Desktop application and user experience

### B1. Architecture foundation
- [ ] Freeze and test Application ↔ Scientific Core boundary.
- [ ] Define stable application-service, ingestion, provenance, configuration, and durable-state contracts.
- [ ] Ensure GUI uses the same service contracts as CLI/API and cannot bypass scientific validation.

### B2. Scientist-facing workflows
- [ ] Desktop shell and dashboard.
- [ ] Data Manager / import / source connection.
- [ ] Object/source explorer and light-curve visualization.
- [ ] Analysis workspace with model identity, uncertainty, calibration, OOD and provenance.
- [ ] Results, visualization, reproducible reports and exports.
- [ ] Discovery candidate workspace with human review and ranking limitations.
- [ ] Settings, Help, troubleshooting, diagnostics and logs.

### B3. Distribution and usability
- [ ] Windows self-contained installer and first-run smoke test.
- [ ] macOS application package and smoke test.
- [ ] Linux AppImage or documented, tested alternative.
- [ ] Clean-machine installation without Python/pip/Git/terminal for normal use.
- [ ] CPU-first performance and memory test on modest hardware.
- [ ] Installer integrity, checksums, release provenance and rollback/uninstall behavior.

## Track C — Scientific capability expansion
- [ ] Independent labeled benchmark and cross-match evidence.
- [ ] Model comparison/ensemble only where labels are comparable and splits are leakage-safe.
- [ ] Dedicated scientific anomaly analysis; do not label OOD as anomaly detection.
- [ ] Drift monitoring separates live-source changes from frozen historical evaluation.
- [ ] Multisurvey/light-curve/image/catalog adapters only after licensing, provenance, schema and validation review.
- [ ] Controlled human feedback; never silently convert review feedback into ground truth.

## Track D — Reliability, security, and release engineering
- [ ] Test fresh installation, upgrade, uninstall, offline/poor-network failure, cache corruption, and missing-data paths.
- [ ] Test dependency locks, supply-chain/security checks, API auth, data handling, and safe export behavior.
- [ ] Preserve deterministic reports, input manifests, checksums, model identity, and audit trails.
- [ ] Every meaningful PR has a validated lifecycle cycle record and regression test.
- [ ] Every release has complete release notes, release description, checksums, provenance, and scientific/engineering gate evidence.

## Milestones and exit criteria

| Milestone | Exit criteria |
|---|---|
| M0 — Scientific recovery | Required heavy jobs execute; CPVS claim is accurately classified; evidence gaps/root causes are recorded. |
| M1 — Desktop foundation | Application/service boundary and ingestion/provenance contracts are tested. |
| M2 — Usable alpha | A non-developer can install, import/connect data, inspect an object/light curve, run analysis, and view evidence. |
| M3 — Scientific workbench | Results, uncertainty/OOD, discovery review, reproducible reports and exports work end-to-end. |
| M4 — Cross-platform beta | Windows/macOS/Linux packaging and clean-machine smoke tests pass. |
| M5 — Scientific product acceptance | Independent benchmark, leakage, provenance, failure analysis and release gates pass for declared scope. |
| M6 — Stable platform release | All M0–M5 criteria pass, docs/help are complete, release notes and evidence are published. |

No milestone is complete based on code presence alone. Completion requires measured evidence and recorded acceptance.
