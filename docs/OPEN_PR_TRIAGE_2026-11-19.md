# GitHub PR and Issue Triage — 2026-11-19

**Repository:** `saeed92m/ztf-classifier`  
**Snapshot:** 2026-11-19  
**Open PRs:** 40  
**Open Issues:** 17

## Actions completed in this review

| PR | Action | Result |
|---|---|---|
| #289 | Security dependency fix | Merged into main. Soup Sieve 4.1; main Dependency Audit passed. |
| #283 | Minimum evidence-backed source identity contracts | Merged into main. Adds immutable domain contracts and tests; no matcher or persistence layer. Issue #249 remains open. |
| #296 | Park execution and full-cohort acceptance documentation | Closed as superseded after all five files were copied byte-for-byte and verified on PR #297. No content discarded. |
| #297 | Park documentation and acceptance convergence | Retained as the consolidated Draft PR. Current-head CI before the latest documentation refresh passed; current refresh CI is running. |

## Open PR inventory and disposition

### Park / DR24 delivery

| PR | Scope | Disposition |
|---|---|---|
| #297 | Consolidated Park runbook, full-cohort acceptance, handbook, roadmap, Persian status, and current documentation | P0. Keep Draft until current-head CI and local live/Workbench evidence pass. |
| #284 | Enable bounded DR24 and Zubercal validation workflows on current branch | P0. Retargeted to main. Lifecycle record corrected to BLOCKED pending current-base CI. |
| #270 | Live DR24 API payload parity | Keep. Depends on the already-merged DR24 adapter PR #264; retarget and verify against current main before merge. |
| #269 | Verified DR24 HATS payload evidence | Keep as evidence until the current Park evidence package is reconciled. |
| #268 | Bounded live DR24 payload probe | Keep until its evidence is compared with current source tests. |
| #266 | Park MVP delivery plan and acceptance gates | Keep until unique Persian Park documents and plan details are reconciled with PR #297. |
| #263 | Bounded BTS-to-DR24 recovery tooling | Ready for review, but inspect the code and source boundaries before merge. |
| #227 | Real DR24 light curves through the feature engine | Keep. Feature parity and source semantics are not yet accepted. |

### Identity, architecture, and governance

| PR | Scope | Disposition |
|---|---|---|
| #281 | Unified scientific baseline, project status, think-tank records, defect register, and roadmap | Keep. It contains 27 files and 82 commits. It conflicts with the current consolidated documentation branch and must be reconciled file by file. Do not merge as-is. |
| #294 | External astronomy ecosystem review | Keep as research evidence; extract decisions into the roadmap after review. |
| #292 | Strategic recovery audit and product redesign | Keep until its recommendations are compared with the current master roadmap. |
| #291 | Think-tank remediation and final review session 09 | Keep as historical review evidence; consolidate unique actions. |
| #252 | Cosmic Intelligence Network architecture | Defer from Park critical path. Retain as future architecture work. |
| #247 | v1.0.1 guides and 2026-11-03 status | Compare against the current README/handbook; close only after all unique content is preserved. |
| #211 | Parallel independent validation and ecosystem plan | Keep as research planning until its evidence and decisions are reconciled. |
| #189 | Auditable multi-source validation protocol | Keep; validate its contracts against the current source adapters. |
| #187 | Handbook, roadmap, and ecosystem review alignment | Compare with current docs; do not merge duplicate historical snapshots blindly. |

### Dependencies

| PR | Scope | Disposition |
|---|---|---|
| #288 | FastAPI requirement range | Do not merge yet. Historical CI has failures; rerun on current main and inspect the resolved lock. |
| #287 | LSDB 0.11.1 | Do not merge yet. Historical CI has failures; verify compatibility and rerun. |
| #286 | ALeRCE 2.4.0 | Do not merge yet. Historical Lint/Product Scope checks failed; investigate before updating the dependency. |

### OOD and independent benchmark research

| PR | Scope | Disposition |
|---|---|---|
| #290 | Frozen v0.2 feature input on StarEmbed light curves | Keep blocked until duplicate and train/test SourceID overlap findings are resolved. |
| #280 | v0.2 OOD sensitivity to missing features | Keep as research; do not change production thresholds without evidence. |
| #279 | Per-row data adequacy and OOD basis | Keep; review semantics and integration separately. |
| #221 | Portable peak-memory diagnostics | Keep for review; verify Windows/Linux behavior before merge. |

### CPVS historical reconstruction

| PR | Scope | Disposition |
|---|---|---|
| #295 | Independent raw archive CRC verification | Keep; depends on #285 and must retain original source hashes. |
| #285 | Raw SNR and two-band fit completeness | Keep; research only until source artifacts and method are verified. |
| #265 | CPVS Seq archive identity | Keep; preserve evidence for the 11,602 candidate-only discrepancy. |
| #240 | Independent CPVS artifact recheck | Ready for review; compare its artifact evidence with the current published reference before merge. |
| #235 | Non-finite SNR attribution | Keep; no threshold changes without source-backed evidence. |
| #230 | CPVS report from authoritative Table 2 | Keep; verify row-level provenance and exact report lineage. |
| #229 | CPVS report name crosswalk requirements | Ready for review; check that the contract remains compatible with the authoritative ID audit. |
| #206 | Invalid SNR and parent identity audit | Keep; review together with #204/#201. |
| #204 | Scope residual membership counts to parent catalog | Keep; branch is chained to #201. |
| #201 | Retain CPVS residual epoch provenance | Keep; preserve raw row-level evidence. |
| #199 | CPVS lifecycle record validation | Keep; review the process fix with its dependent heavy-validation branch. |
| #184 | Preserve row-level membership evidence | Keep; compare with the current strict audit before merge. |
| #182 | Deterministic 100/1,000 CPVS samples and full-vs-batch tooling | Ready for review; required for the separate CPVS research track. |
| #179 | Parent metadata for candidate-only diagnosis | Ready for review; preserve provenance and avoid declaring a root cause. |
| #177 | Extra-member diagnostics and artifact trimming | Ready for review; keep as evidence, not a fix for the discrepancy. |
| #176 | CPVS membership by ZTF name and heavy readiness | Ready for review; verify against current authoritative membership and tests. |

## Open Issues

All 17 issues remain open. They represent active requirements, blockers, or research questions; none is closed in this review.

| Issue | Scope | Disposition |
|---|---|---|
| #293 | Repository license and distribution policy | Owner decision required before wider distribution. |
| #282 | Recover and authenticate frozen v0.2.0 model artifact | P0 blocker for production inference. |
| #253 | DR24 acquisition through the application | P0 blocker for normal application integration. |
| #251 | CIN integration | Deferred; not on Park critical path. |
| #249 | Canonical source identity and cross-match | Open; PR #283 adds domain contracts only. |
| #222 | 100 random object-level behavior tests | Keep as validation work. |
| #218 | Phase-fold visualization | Product capability; sequence after data/identity contracts. |
| #217 | AVRO alert ingestion | Future ingestion capability. |
| #216 | TAP backend parity | Future source adapter. |
| #210 | Parallel independent-dataset and ecosystem validation | Active scientific validation umbrella. |
| #196 | Standards-compliant JSON diagnostics | Keep until verified fixed. |
| #195 | CPVS candidate-only triage | Research; do not alter published membership. |
| #188 | Fully traceable multi-source validation | Active scientific requirement. |
| #180 | Deterministic CPVS 100/1,000 samples | Separate CPVS research. |
| #170 | CPVS 730k reconstruction discrepancy | UNRESOLVED; 11,602 candidate-only IDs. |
| #158 | Cross-platform Park MVP | P0 product delivery tracker. |
| #157 | Cross-platform desktop discovery platform | Long-term product roadmap. |

## Rules for closing

- Do not close an issue that still represents an active blocker or research question.
- Do not close a PR only because it is old, Draft, or based on an older branch.
- Close a PR as superseded only after its unique content and evidence are copied and verified elsewhere.
- Merge code only after current-base CI passes and scientific/engineering scope is reviewed.
- A Ready-for-review label is not proof that all required scientific gates passed.
- Keep CPVS unresolved until the object-level discrepancy has a reproducible root cause.
