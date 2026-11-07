# ZTF Classifier — Project Continuity Handbook v2.9

Status date: 2026-11-07
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

---

## Current delivery and scientific status — 2026-11-07

**Primary delivery objective:** a bounded, reproducible DR24 exploratory prototype for the Tabriz Science and Technology Park. The product delivery track is Issue [#158](https://github.com/saeed92m/ztf-classifier/issues/158); DR24 application integration is Issue [#253](https://github.com/saeed92m/ztf-classifier/issues/253). The exact acceptance plan is `docs/PARK_MVP_DELIVERY_PLAN_2026-11-05.md`.

### Immutable scientific and release baseline

- Software release: `v1.0.1`, published and immutable.
- Scientific baseline: `v0.2.0`, immutable.
- Benchmark: 150 ZTF objects, 15 ALeRCE reference classes, 10 objects per class.
- Frozen feature contract: 42 features, `final_feature_set_v0.2`.
- Production model identity: `baseline_v0.2`.
- Historical cutoff: `59447.224132`.
- Diagnostic schema: 1.1.
- ALeRCE labels are benchmark/reference labels, not independent astrophysical ground truth.
- Do not send native DR24 measurements to the frozen v0.2.0 model without a separately validated mapping.

### Park MVP: evidence and remaining acceptance work

Verified component evidence, limited to the tested OIDs:

- Direct DR24 HATS probe [run 42061697065](https://github.com/saeed92m/ztf-classifier/actions/runs/42061697065): 3 OIDs, 417 epochs; returned epoch counts matched catalog `nepochs`; artifact 13432467426.
- Repeatability evidence [PR #269](https://github.com/saeed92m/ztf-classifier/pull/269): two four-OID runs, 626 epochs, matching epoch CSV and summary JSON hashes.
- FastAPI-to-HATS live smoke [run 42063653144](https://github.com/saeed92m/ztf-classifier/actions/runs/42063653144): one test passed; artifact 13430999878.
- API failure-contract run [42065074402](https://github.com/saeed92m/ztf-classifier/actions/runs/42065074402): passed.
- Workbench browser smoke [run 42275261463](https://github.com/saeed92m/ztf-classifier/actions/runs/42275261463): one test passed; 7 OIDs and 2,183 epochs; artifact 13532578108.

These results establish bounded retrieval and component-level API/UI behavior. They do **not** establish physical-source identity, cross-OID grouping, production QC, validated time/photometric transformations, DR24 feature mapping, classifier inference, scientific performance, or Park acceptance.

Current delivery disposition:

| Gate | Status |
|---|---|
| G0 — frozen baseline protection | PRESERVED; verify each candidate change |
| G1 — bounded raw DR24 acquisition | VERIFIED for tested OIDs; adapter PR #264 remains under review |
| G2 — OID identity and grouping | NOT ACCEPTED |
| G3 — photometry/time/QC contract | NOT ACCEPTED |
| G4 — 5–10 confirmed-source end-to-end smoke | PARTIAL; full acceptance workflow not verified |
| G5 — 30–50 object guided demonstration | NOT VERIFIED |
| G6 — scientist-facing guided workflow | PARTIAL |
| G7 — independent scientific performance | NOT ACCEPTED |
| G8 — Park handover package | NOT ACCEPTED |

Next critical action: complete a pinned 5–10 confirmed-source workflow through acquisition, identity review, raw-preserving QC, visualization, export, manifest, hashes and offline replay. Then complete the 30–50 object demonstration and generate the handover report from actual run outputs. Do not expand to bulk DR24 ingestion or claim a DR24 classifier.

### CPVS membership investigation — separate research lane

Issue [#170](https://github.com/saeed92m/ztf-classifier/issues/170) remains **OPEN / UNRESOLVED** and is not part of the Park MVP release gate.

A full object-level audit of retained artifacts found:
- Parent Table 2: 781,602 IDs.
- Published Table 4: 730,184 IDs.
- Reconstructed two-band SNR candidates: 741,786 IDs.
- Candidate-only residual: 11,602; published-only: zero.
- Intersecting reconstructed candidates with positive `gmag`, `rmag`, `Per-g`, and `Per-r` values yields exactly 730,184 IDs.
- The 11,602 candidate-only IDs fail at least one of those four fields. The 55 four-field-positive noncandidate controls all fail at least one raw two-band SNR threshold in the retained independent control audit.

This is a strong empirical root-cause candidate, not proof of the historical authors' exact selection procedure. The paper describes two-band SNR selection and common-period phase folding; it does not explicitly document the four-field completeness gate. The 17 objects with complete mean magnitudes but incomplete per-band periods remain a specific unresolved case. Fresh raw-photometry re-derivation and verification against author preprocessing semantics are still required.

See [research PR #265](https://github.com/saeed92m/ztf-classifier/pull/265) and [Issue #170](https://github.com/saeed92m/ztf-classifier/issues/170). Do not change the production selector, frozen baseline, or reference definition to force a match.

### Cosmic Intelligence Network (CIN)

CIN is a proposed, separately governed human-in-the-loop subsystem. Its canonical architecture is recorded in Notion and GitHub [PR #252](https://github.com/saeed92m/ztf-classifier/pull/252), [Issue #251](https://github.com/saeed92m/ztf-classifier/issues/251). It is not on the Park MVP critical path. No production contributor network, annotation corpus, validated consensus engine, or model improvement is claimed. Keep raw contributions immutable; consensus is not ground truth; never automatically retrain the production model from contributions.

### Current GitHub workflow interpretation

For the Park documentation branch `delivery/park-mvp-readiness-20261105`, CI run [42312909047](https://github.com/saeed92m/ztf-classifier/actions/runs/42312909047), CodeQL [42312909023](https://github.com/saeed92m/ztf-classifier/actions/runs/42312909023), Product Scope Audit [42312909026](https://github.com/saeed92m/ztf-classifier/actions/runs/42312909026), and the Scientific Validation contract workflow [42312909027](https://github.com/saeed92m/ztf-classifier/actions/runs/42312909027) completed successfully. CI jobs passed. The Scientific Validation contract passed, but the four source-backed/independent scientific jobs were skipped. This is not full scientific validation.

The documentation update remains Draft/open in [PR #266](https://github.com/saeed92m/ztf-classifier/pull/266) until review and merge. Do not describe it as merged.

### Status vocabulary

Use these terms precisely:
- **Designed / Proposed:** architecture or requirement exists; runtime implementation is not implied.
- **Implemented:** code exists on a named branch or merged revision.
- **Tested:** specified automated or manual tests actually ran.
- **Source-backed:** actual external data were retrieved and provenance recorded.
- **Validated:** the relevant scientific or product acceptance criteria passed.
- **Released:** an immutable release artifact was published.

A green workflow, skipped test, matching count, or component smoke test must not be promoted to a broader acceptance claim.
