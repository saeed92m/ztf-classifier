# ZTF Classifier — Project Continuity Handbook v2.8

Status date: 2026-10-11
Software release: v1.0.1
Scientific baseline: v0.2.0 (immutable)
Production model: baseline_v0.2

## Current state
v1.0.1 is published and immutable. v1.0.0 remains immutable. Scientific Validation, CI, CodeQL, release asset verification, and release publication gates passed for v1.0.1.

The project is now in Platform Expansion: documentation alignment, cross-platform desktop UX, user-facing workflows, independent scientific benchmarking, and controlled discovery-platform expansion.

## Product identity
The canonical product is an Astronomical Data Analysis & Discovery Platform, not merely a classifier.

Canonical flow:
source data → ingestion → normalization/QC → scientific feature/context layers → analysis modes → uncertainty/calibration/OOD → candidate ranking → evidence/provenance → human/scientific validation → reproducible discovery outputs

## Immutable baseline
v0.2.0 remains immutable: 150 ZTF objects, 15 ALeRCE benchmark classes, 42 frozen features, XGBoost baseline_v0.2, historical cutoff 59447.224132.

## Scientific boundary
CPVS parent: 781,602. Published membership: 730,184. The pre-fix source-backed run reported 741,787 candidates, intersection 730,182, 11,605 candidate-only IDs and two published-only IDs (781603 and 781604). A later code inspection found a real defect in which finite, non-zero magnitude qualification was not applied to the final g/r intersection; PR #173 corrected this and added a regression test. Independent diagnostics that already applied finite/non-zero magnitude filtering still reported 741,785 candidates, so exact reconstruction remains claim-specific UNRESOLVED pending a fresh source-backed rerun and independent membership audit. No predicate or threshold may be changed merely to force cardinality equality.

## Diagnostic semantics
Classification uncertainty, calibration, conformal prediction, OOD, scientific anomaly evidence, catalog evidence, and explainability evidence remain separate channels. The current production model does not claim a scientific-anomaly detector.

## Release rule
Every future release must have curated .github/release-notes/<tag>.md before publication. Immutable releases are never mutated.

## Ecosystem review and product expansion
The 2026-10-08 ecosystem review is recorded in `docs/ECOSYSTEM_REVIEW_PRODUCT_EXPANSION_2026-10-08.md`.

New product requirements are now canonical:
- cross-platform desktop application for Windows, macOS, and Linux;
- self-contained installation without requiring Python/pip/venv/Git/terminal;
- integrated contextual Help and Troubleshooting;
- Object/Source Explorer;
- data-ingestion abstraction;
- explainable classification, uncertainty, calibration, conformal and OOD presentation;
- first-class anomaly/discovery workflows;
- provenance/evidence UI;
- cross-match framework;
- similar-object search;
- human-in-the-loop review/feedback;
- transparent discovery ranking;
- separate Real/Bogus architecture boundary;
- future ZTF Alert/AVRO and offline/batch/streaming readiness.

These additions are layered around the immutable v0.2.0 scientific baseline and must not weaken scientific validation or provenance contracts.

## Next work
1. Complete documentation alignment for v1.0.1 and the platform-expansion requirements.
2. Establish the desktop Application/Core API boundary and cross-platform packaging architecture.
3. Implement the user-facing Data Manager and Object/Source Explorer.
4. Integrate Help/Troubleshooting into the GUI.
5. Perform clean-room/replay and real user-path verification on supported operating systems.
6. Establish independent labeled/cross-match scientific validation evidence.
7. Expand discovery workflows only where contracts and evidence are ready.
8. Maintain cumulative learning, failure-prevention, roadmap, and release-note records for every meaningful change.

## Completion definition
v1.0.0 is complete as a published software milestone. The broader scientific/product platform is not declared scientifically complete merely because v1.0.0 is published.

Every meaningful change must update affected documentation, cumulative-learning records, failure-prevention knowledge, roadmap status, and release notes when release behavior changes.

Current status: v1.0.1 Released / Platform Expansion Active.


## Current scientific status — 2026-10-11

### CPVS exact reconstruction: unresolved
- Issue [#170](https://github.com/saeed92m/ztf-classifier/issues/170) remains open.
- PR [#171](https://github.com/saeed92m/ztf-classifier/pull/171) ensures missing or failed membership-audit evidence cannot default to PASS.
- PR [#173](https://github.com/saeed92m/ztf-classifier/pull/173) corrected a genuine derivation defect but did not establish exact membership.
- Source-backed run [#38005546758](https://github.com/saeed92m/ztf-classifier/actions/runs/38005546758) completed successfully at workflow level but skipped source-provenance/scientific-gate-readiness. A green workflow with a skipped required job is not scientific release readiness.
- A concrete audit defect has been identified in the comparison code: it read Table 4's catalog-internal ID and compared it directly with SourceID values derived from Table2 row order. The source ReadMe describes Table 4 ID as an internal catalog identifier, so the defensible join is by ZTF object name. PR #176 implements this name-based join and adds tests; CI and source-backed results are pending.
- This likely explains the two anomalous published-only IDs (781603/781604), but it does not explain the remaining ~11k candidate-only objects. That residual discrepancy must be measured after the corrected audit runs.
- Next: trigger the heavy workflow on a ci/heavy/* branch after the correction; inspect source acquisition/derivation artifacts; verify unmapped/duplicate names and candidate-only objects; keep the exact-reproduction claim UNRESOLVED until supported by evidence.

### Desktop product: active implementation
Issue [#158](https://github.com/saeed92m/ztf-classifier/issues/158) is the tracked target for a complete scientist-facing desktop product: dashboard, Data Manager, Object/Source Explorer, analysis/discovery workspaces, visualization, reproducible reports, integrated Help, and self-contained Windows/macOS/Linux packaging. The exit criterion is successful end-to-end use by a non-developer on a clean supported OS without Python, pip, Git, or terminal use for normal operation.

### Documentation synchronization
The documentation update is under review in [PR #175](https://github.com/saeed92m/ztf-classifier/pull/175). It adds a canonical product roadmap, updates the scientific-validation roadmap and troubleshooting, links the handbook/roadmap from README, and records this stage in the cumulative lifecycle ledger.

**Immutable constraints:** v1.0.1 remains unchanged; scientific baseline v0.2.0 remains frozen; scientific validation stays fail-closed; OOD is not represented as scientific anomaly detection.