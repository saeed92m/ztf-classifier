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
- [x] Verify the robust parser reads all 730,184 published ZTF names without duplicates.
- [x] Identify and correct the audit's invalid row-ordinal substitution: official CPVS lightcurve membership uses Table2 `Seq` (bytes 24–29), not physical row order.
- [ ] Rerun derivation and independent membership audit using actual Seq values; previous membership metrics are invalid and superseded.
- [ ] Explain the residual candidate/published membership difference from valid Seq-based evidence and source-backed selection semantics, not tuned thresholds.
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

## Evidence update — 2026-10-11

A deeper source-schema review found that the previous audit mapped published ZTF names to parent row ordinals instead of the explicit CPVS Table2 `Seq` field (bytes 24–29), while lightcurve `SourceID` joins by `Seq`. Thus the 725,101 / 16,686 / 5,083 values from heavy run [#38095650470](https://github.com/saeed92m/ztf-classifier/actions/runs/38095650470) are invalid and superseded. PR [#176](https://github.com/saeed92m/ztf-classifier/pull/176) now reads actual Seq IDs for the derived candidate universe and published-name join. The Seq-based heavy run [#38121913146](https://github.com/saeed92m/ztf-classifier/actions/runs/38121913146) has completed: 741,786 candidates; 730,184 intersection; 11,602 candidate-only; 0 published-only; 0 duplicate and 0 unmapped published names. This is a valid identifier-space comparison, but exact CPVS reproduction remains **UNRESOLVED** because 11,602 candidates remain unexplained. The flag-zero variant yields 736,225 candidates / 724,712 intersection / 5,472 published-only; a magnitude 20.6 diagnostic loses 18,865 published objects. Neither is an acceptable fix. Current-head CI must pass and the residual selection semantics must be resolved or documented from evidence; do not tune thresholds to force cardinality equality. Source: https://cdsarc.cds.unistra.fr/viz-bin/ReadMe/J/ApJS/249/18?format=html&tex=true.


## Status refresh — 2026-10-25

The following items are explicit current workstreams; this refresh does not change the immutable v0.2.0 scientific baseline or assert that the work is complete.

- **CPVS discrepancy:** Issue [#170](https://github.com/saeed92m/ztf-classifier/issues/170) remains open. The recorded Seq-based comparison is 781,602 parent objects, 730,184 published members, 741,786 reconstructed candidates, 11,602 candidate-only IDs, and zero published-only IDs. The four-field diagnostic predicate matches the recorded membership artifacts, but the publisher's historical selection semantics remain unproven. Do not tune thresholds merely to force cardinality.
- **Object-level discrepancy report:** [PR #224](https://github.com/saeed92m/ztf-classifier/pull/224) is open/draft. The implementation must be run against hash-identified authoritative source files and its 11,602-row output verified before calling the deliverable complete. Raw-light-curve review and external cross-match remain unassessed unless separately evidenced.
- **Dependency security:** [PR #223](https://github.com/saeed92m/ztf-classifier/pull/223) is open/unmerged. Its last recorded CI and dependency audit succeeded. Re-check current runs and follow normal review; do not auto-merge.
- **Independent benchmark:** Issue [#222](https://github.com/saeed92m/ztf-classifier/issues/222) tracks a separate 100-object benchmark with raw/source-level data, independent reference analyses, provenance, and leakage checks. It must not be conflated with the ALeRCE benchmark or CPVS reconstruction.
- **Cross-platform product:** target Windows, Ubuntu, and macOS on a CPU-first basis. The declared Python constraint is currently `>=3.11,<3.12`; supported OS/Python claims require clean-machine build and end-to-end test evidence for each target.
- **GUI and integration:** audit and extend the documented FastAPI/`/workbench/` interface before creating duplicate scientific logic. Company-Platform integration remains optional and must use a versioned API/export contract; it must not become a hard runtime dependency.
- **Release and evidence discipline:** a successful CI workflow is not proof of scientific validity when scientific jobs are skipped. Keep blockers open until their specific acceptance criteria pass.

The detailed acceptance criteria and current evidence boundary are maintained in [Project Status & Execution Ledger](../PROJECT_STATUS_AND_EXECUTION_LEDGER_2026-10-25.md).
