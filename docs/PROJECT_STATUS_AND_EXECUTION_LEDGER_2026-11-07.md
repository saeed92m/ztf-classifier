# ZTF Classifier — Project Status and Execution Ledger

**Status date:** 2026-11-07  
**Primary delivery:** Tabriz Science & Technology Park bounded prototype  
**Delivery tracker:** https://github.com/saeed92m/ztf-classifier/issues/158  
**DR24 integration:** https://github.com/saeed92m/ztf-classifier/issues/253  
**Documentation PR:** https://github.com/saeed92m/ztf-classifier/pull/266 — Draft / open / unmerged  
**Handbook:** HANDBOOK_UPDATED_v2.9.md

## Executive disposition

The project has a published v1.0.1 Python package, an immutable v0.2.0 scientific baseline, production inference contracts, an API-backed Workbench, and bounded live DR24 HATS/API/browser evidence. It does **not** yet have an accepted DR24-backed end-to-end Park demonstration. The immediate target is a complete 5–10 confirmed-source workflow, followed by a 30–50 object guided demonstration.

Do not publish a completion percentage without a defined weighting model. Do not describe the current component smoke tests as product acceptance or scientific validation.

## Protected baseline

- Software release: v1.0.1, immutable.
- Scientific baseline: v0.2.0, immutable.
- Benchmark: 150 ZTF objects, 15 ALeRCE reference classes, 10 objects per class.
- Feature contract: 42 features, final_feature_set_v0.2.
- Production model: baseline_v0.2.
- Historical cutoff: 59447.224132.
- Diagnostic schema: 1.1.
- ALeRCE labels are reference/benchmark labels, not independent ground truth.

## Park delivery evidence

| Evidence | Verified result | Boundary |
|---|---|---|
| HATS direct probe, [run 42061697065](https://github.com/saeed92m/ztf-classifier/actions/runs/42061697065) | 3 OIDs, 417 epochs; catalog nepochs matched; artifact 13432467426 | Raw acquisition only |
| Repeatability evidence, [PR #269](https://github.com/saeed92m/ztf-classifier/pull/269) | Two four-OID runs, 626 epochs; matching epoch CSV and summary JSON hashes | Repeatability of bounded retrieval |
| FastAPI HATS smoke, [run 42063653144](https://github.com/saeed92m/ztf-classifier/actions/runs/42063653144) | One live test passed; artifact 13430999878 | Component API path |
| API failure contracts, [run 42065074402](https://github.com/saeed92m/ztf-classifier/actions/runs/42065074402) | Passed | Failure-contract tests |
| Workbench browser smoke, [run 42275261463](https://github.com/saeed92m/ztf-classifier/actions/runs/42275261463) | One test passed; 7 OIDs, 2,183 epochs; artifact 13532578108 | Browser interaction and raw-data presentation |

These results do not establish physical-source identity, cross-OID grouping, production QC, validated HMJD/photometric transformations, DR24 feature mapping, classifier inference, scientific performance, or Park acceptance.

## Acceptance gates

| Gate | Status | Required next evidence |
|---|---|---|
| G0 — protect frozen baseline | PRESERVED; verify per PR | Baseline/model/schema integrity |
| G1 — bounded raw DR24 acquisition | VERIFIED for tested OIDs; PR #264 under review | Current-head adapter review and acceptance |
| G2 — OID identity/grouping | NOT ACCEPTED | Curated, evidence-backed identity map; ambiguous IDs stay separate |
| G3 — photometry/time/QC | NOT ACCEPTED | Versioned transformations, raw preservation, QC policy and tests |
| G4 — 5–10 confirmed-source smoke | PARTIAL | Full acquisition→identity→QC→visualization→export→manifest→offline replay |
| G5 — 30–50 guided demonstration | NOT VERIFIED | Reproducible run, object status, exports, failure log and rehearsal |
| G6 — scientist-facing workflow | PARTIAL | Reviewer completes workflow without terminal |
| G7 — scientific performance | NOT ACCEPTED | Independent labels, leakage-safe evaluation, calibration/abstention/OOD/anomaly metrics |
| G8 — Park handover | NOT ACCEPTED | Report from actual artifacts, demo procedure, environment, limitations and evidence bundle |

## Critical execution sequence

1. Review and accept the bounded raw adapter only after current-head tests, schema, identity and provenance review.
2. Pin a 5–10 object sample. Record each OID, source metadata, selection rationale and unresolved identity ambiguity.
3. Run the same sample through the application service and Workbench. Preserve native HMJD, photometry, flags, filter/field/RCID, retrieval metadata and hashes.
4. Implement only explicitly versioned exploratory transformations. Do not invent color corrections or map HMJD to another time basis.
5. Add per-object success/partial/failure states and explain every missing or excluded epoch.
6. Export raw data, QC, plots, report, object/OID list, configuration, environment, commit and output hashes.
7. Replay offline from the pinned inputs and compare deterministic outputs.
8. Expand to 30–50 objects, review every failure and partial result, then rehearse from a clean environment.
9. Produce the Park handover report from the real run artifacts.

No bulk DR24 download is required. Do not feed raw DR24 measurements into the frozen v0.2.0 model without a separately validated mapping.

## CPVS research lane — separate from Park delivery

Issue #170 remains OPEN / UNRESOLVED. A retained full object-level audit reports 781,602 parent IDs, 730,184 published IDs, 741,786 reconstructed two-band SNR candidates, 11,602 candidate-only IDs and zero published-only IDs. Intersecting the candidate set with positive Table 2 gmag, rmag, Per-g and Per-r yields exactly the 730,184 published members. All 11,602 candidate-only IDs fail at least one of those four metadata fields. The independent 55-control raw-photometry audit found zero controls passing both band thresholds.

This is a strong root-cause candidate, not proof of author intent. The published paper does not explicitly state the four-field gate. The 17 objects with complete mean magnitudes but incomplete band periods remain unexplained. Raw-photometry re-derivation and verification against author preprocessing semantics are required. See PR #265. Do not change production criteria or the frozen baseline.

## CIN workstream

CIN remains a proposed, separately governed human-in-the-loop subsystem, tracked by Issue #251 and PR #252. It is not on the Park MVP critical path. No production contributor network, annotation corpus, consensus engine or model improvement is claimed. Consensus is not ground truth; raw contributions must be immutable; no automatic production retraining.

## CI and scientific-validation interpretation

Park documentation branch delivery/park-mvp-readiness-20261105:
- CI 42312909047: all jobs passed, including format, lint, lifecycle, tests, runtime smoke, package build and dependency audit.
- CodeQL 42312909023: passed.
- Product Scope Audit 42312909026: passed.
- Scientific Validation 42312909027: contract job passed; four independent/source-backed jobs were skipped.

Therefore, engineering CI is green for that documentation branch. Full source-backed scientific validation is not established. PR #266 is still Draft/open/unmerged.

## Documentation synchronization

- Handbook v2.9: this status date and current delivery/science boundaries.
- Park delivery plan: docs/PARK_MVP_DELIVERY_PLAN_2026-11-05.md.
- Product roadmap: docs/roadmap/PLATFORM_EXPANSION_ROADMAP.md.
- Quick Start, User Guide and Installation: v1.0.1 and Python 3.11, with model-artifact and DR24 limitations.
- README: baseline and product boundaries; handbook link.
- Changelog: no release entry is added because this is documentation-only work and no software release is created.
- Notion: update the canonical handbook, project knowledge base, documentation index, CPVS audit and CIN implementation record with this dated checkpoint.

## Decision

Keep the immediate delivery focused on a bounded, honest, reproducible DR24 exploratory workflow. Do not make a production DR24 classifier claim. Do not merge/release solely because CI is green. Do not mix CPVS or CIN research with the Park acceptance path.
