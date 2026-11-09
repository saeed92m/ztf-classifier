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

Issue #170 remains **OPEN / SCIENTIFICALLY UNRESOLVED**. It is a claim-specific research blocker. It does not block the DR24-first Park delivery and it does not authorize changes to the production selector or the frozen v0.2.0 baseline.

The historical Seq-based comparison retained in repository evidence reports:

| Set | Objects |
|---|---:|
| Parent Table 2 | 781,602 |
| Published Table 4 | 730,184 |
| Reconstructed two-band SNR candidates | 741,786 |
| Candidate-only | 11,602 |
| Published-only | 0 |

The published-name to Table 2 Seq crosswalk is documented as 730,184 mapped and zero unmapped names. The 11,602 excess candidates remain unexplained by the published method. Zero published-only IDs does not explain the candidate-only set.

### Corrected 55-control interpretation

The retained raw-photometry archive evidence shows:

- g-band rows exist for only 1 of 55 controls.
- r-band rows exist for 51 of 55 controls.
- No control has both bands represented in the retained attachments.

Therefore, the earlier statement that zero of 55 controls passed both band SNR thresholds is **not supported**. The old per-band failure counters treated absent rows as failed SNR measurements. That interpretation is invalid.

Missing raw photometry is `UNKNOWN`, not `FAIL`. The 55-control raw-photometry audit is PARTIAL. It does not independently validate the two-band SNR predicate for these controls.

### New Master Handoff diagnostics — evidence still required

The user-approved CPVS Master Handoff reports additional diagnostics:

- Four-field-positive set: 730,239 objects.
- Four-field-only relative to the published set: 55 objects.
- Published-only relative to the four-field set: zero.
- A separate `Ng >= 11` and `Nr >= 11` diagnostic: 730,229 candidates.
- That observation-count diagnostic leaves 45 candidate-only objects and removes 11,557 of the 11,602 residuals.
- The 45 residuals are reported in three groups: 17, 4 and 24 objects.
- A separate 1,000-object control sample is required from the complete set of 51,418 parent nonmembers.

These values are **reported by the approved handoff**. This ledger update does not claim that the ID lists, source files, hashes, commands and output artifacts have been independently re-run or verified.

The handoff has an internal set-arithmetic inconsistency that must be resolved from the actual ID lists. It states `|F| = 730,239`, `|F \\ P| = 55` and `|P \\ F| = 0`, but also states `|C ∩ F| = 730,239` while asserting `C ∩ F = P` and `|P| = 730,184`. These statements cannot all be true with the same set definitions. Do not silently choose one number. Preserve the diagnostic as **UNVERIFIED** until the exact sets, definitions and hashes reconcile.

The `Ng/Nr >= 11` test is a diagnostic hypothesis. It is not an approved publisher rule or production threshold. Do not apply it to production membership.

### Other CPVS integrity findings

- PR #244 is open and Draft. Its recorded base SHA is `4f98a06...`; current main is `bc85f6c...`. A current-head pull-request validation after rebase is not verified.
- The fixed stratified 100/1,000 samples were reproduced from retained artifacts. They deliberately oversample discrepancy groups and are not prevalence estimates.
- The separate 1,000-object nonmember control sample from all 51,418 nonmembers still requires its exact ID manifest, seed, sampling method and hashes.
- Full MGPR diagnostics for the published controls, 11,602 candidate-only objects, 45 remaining objects and the defined control groups are not verified.
- The g/r archive per-Seq reconciliation remains incomplete. The 91 g-band count mismatches and 4,916-row total difference remain separate archive-integrity issues.
- Seq 615170 / 615172 remains a strong identity lead, not an approved SourceID remapping. Preserve both identifiers until full raw coordinate, time and band evidence supports a decision.

### Required next evidence

1. Reconcile the exact four-field ID sets and the arithmetic conflict in the Master Handoff.
2. Produce a source-backed, hashed ID list for the `Ng/Nr >= 11` experiment. Record its full parent and reference definitions. Do not promote the rule to production.
3. Generate and hash the separate 1,000-object nonmember control sample from all 51,418 parent nonmembers.
4. Complete object-level raw g/r provenance for the required samples and the 11,602 residuals.
5. Complete per-Seq archive reconciliation and the 615170/615172 identity investigation without automatic ID remapping.
6. Run MGPR with explicit `PASS`, `FAIL`, `UNKNOWN` and `ERROR` states. Missing data and execution errors must not be counted as scientific failures.
7. Rebase/rebuild PR #244 from current main and run CI on its exact final head.
8. Keep the CPVS issue open until a reproducible root cause or a clearly source-supported limitation is established.

No production selector, SNR threshold, model, feature set, class order, reference membership, scientific gate or v0.2.0 artifact is changed by this status correction.

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
## Institutional submission reconciliation

The original 13-page Park presentation and 21-page project proposal were inspected. They remain unchanged as submitted records. A Persian technical status addendum was added at docs/acceptance/PARK_TECHNICAL_STATUS_ADDENDUM_2026-11-07.fa.md. It distinguishes the frozen v0.2.0 inference path from exploratory DR24 raw-data work, separates OOD from scientific anomaly detection, clarifies that the 5.32B figure is release scale rather than processed project volume, and records that the 5–10 and 30–50 object demos remain incomplete. Use the original PDFs with this dated addendum; create a formally revised PDF only as a separately versioned submission.


- Handbook v2.9: this status date and current delivery/science boundaries.
- Park delivery plan: docs/PARK_MVP_DELIVERY_PLAN_2026-11-05.md.
- Product roadmap: docs/roadmap/PLATFORM_EXPANSION_ROADMAP.md.
- Quick Start, User Guide and Installation: v1.0.1 and Python 3.11, with model-artifact and DR24 limitations.
- README: baseline and product boundaries; handbook link.
- Changelog: no release entry is added because this is documentation-only work and no software release is created.
- Notion: update the canonical handbook, project knowledge base, documentation index, CPVS audit and CIN implementation record with this dated checkpoint.

## Decision

Keep the immediate delivery focused on a bounded, honest, reproducible DR24 exploratory workflow. Do not make a production DR24 classifier claim. Do not merge/release solely because CI is green. Do not mix CPVS or CIN research with the Park acceptance path.
