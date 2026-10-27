# ZTF Classifier — Project Continuity Handbook v2.8

## Current status snapshot — 2026-10-27

PR #231 is open/draft/unmerged at `4a6ddd786ebb37551253349ef483ca968a8f00ac`. CI, CodeQL, Product Scope Audit, and Scientific Validation completed successfully, but four source-backed scientific jobs were skipped. This is not full scientific validation. The local lab artifact is not a release artifact; local test skip reasons are still being verified. The explicit `fallback_on_empty` acquisition and CPVS exact reconstruction remain open. See [the current execution ledger](PROJECT_STATUS_AND_EXECUTION_LEDGER_2026-10-27.md).


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
CPVS parent: 781,602 rows. Published membership: 730,184 objects. Prior candidate and membership reports are historical diagnostics only. Source-schema review found the audit converted published ZTF names to the parent table's physical row ordinal instead of Table2's documented `Seq` value. The official CPVS ReadMe specifies Table2 `Seq` in bytes 24–29 and the lightcurve attachment's `Seq` as its running SourceID; Table2 has 781,602 rows but Seq values span 1..781,604. Therefore, the comparison in run #38095650470 (725,101 intersection, 16,686 candidate-only, 5,083 published-only) is invalid and superseded. The Seq-based heavy run [#38121913146](https://github.com/saeed92m/ztf-classifier/actions/runs/38121913146) now reports 741,786 candidates, 730,184 intersection, 11,602 candidate-only, 0 published-only, 0 duplicate published names, and 0 unmapped names. Exact reconstruction remains UNRESOLVED because the candidate set still contains 11,602 extras. Do not tune thresholds or flag policy to force cardinality equality. Source: https://cdsarc.cds.unistra.fr/viz-bin/ReadMe/J/ApJS/249/18?format=html&tex=true

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
- The parser reads all 730,184 published names without duplicates; however, the previous mapping to row ordinals was semantically wrong. The membership comparison is not valid as a SourceID-space audit until it uses the documented CPVS Table2 Seq column.
- Heavy run [#38095650470](https://github.com/saeed92m/ztf-classifier/actions/runs/38095650470) did not produce a valid membership comparison: it mapped object names to physical parent row ordinals, not the catalog's SourceID. The 725,101 / 16,686 / 5,083 metrics are invalid and superseded. A fresh Seq-based derivation and independent membership audit is required.
- The follow-up CI found one stale test calling `read_vizier()` without its required parent path. It was fixed in commit [6416958](https://github.com/saeed92m/ztf-classifier/commit/641695863195edccb4305cb4884aac727baa30e1). Fresh CI [#38097993359](https://github.com/saeed92m/ztf-classifier/actions/runs/38097993359) and heavy Scientific Validation [#38097993346](https://github.com/saeed92m/ztf-classifier/actions/runs/38097993346) are running. Keep Issue #170 open until the mismatch is explained and required checks pass.

### Desktop product: active implementation
Issue [#158](https://github.com/saeed92m/ztf-classifier/issues/158) is the tracked target for a complete scientist-facing desktop product: dashboard, Data Manager, Object/Source Explorer, analysis/discovery workspaces, visualization, reproducible reports, integrated Help, and self-contained Windows/macOS/Linux packaging. The exit criterion is successful end-to-end use by a non-developer on a clean supported OS without Python, pip, Git, or terminal use for normal operation.

### Documentation synchronization
The documentation update is under review in [PR #175](https://github.com/saeed92m/ztf-classifier/pull/175). It adds a canonical product roadmap, updates the scientific-validation roadmap and troubleshooting, links the handbook/roadmap from README, and records this stage in the cumulative lifecycle ledger.

**Immutable constraints:** v1.0.1 remains unchanged; scientific baseline v0.2.0 remains frozen; scientific validation stays fail-closed; OOD is not represented as scientific anomaly detection.