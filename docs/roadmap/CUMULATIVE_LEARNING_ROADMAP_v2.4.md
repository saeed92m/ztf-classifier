# Cumulative Learning & Product Roadmap — v2.4

## 0. Roadmap authority

This roadmap is the finite execution plan for completing the ZTF Classifier as an **Astronomical Data Analysis & Discovery Platform**.

It uses evidence-based status only:

**Planned → In Progress → Implemented → Validated → Completed**

Code existing in the repository is not sufficient for Completed.

The roadmap ends only at:

**Final Audit → Release Freeze → v1.0 → Complete**

---

## 1. P0 — Scientific validation recovery

**Current state: Completed (2026-10-04)**

- [x] Product-vs-external-reproduction scopes separated.
- [x] CPVS unresolved state represented explicitly.
- [x] CPVS diagnostic/audit evidence retained.
- [x] Benchmark/lifecycle contract tests present.
- [x] ALeRCE manifest JSON validity enforced.
- [x] ALeRCE ZTF schema contract pinned to `ztf`.
- [x] Deterministic duplicate-resolution design specified.
- [x] Regression test added for ALeRCE duplicate-version handling.
- [x] Real ALeRCE source-backed evidence run passes after the validator-ordering fix.
- [x] CPVS heavy source-backed derivation completes.
- [x] Independent 730,184 membership audit completes; exact historical membership remains correctly classified as UNRESOLVED where it does not match the independent published set.
- [x] Scientific gate classifies the final evidence correctly.
- [x] Final release-gate behavior verified by a completed heavy run.

**Exit:** scientific validation run completed; every release-blocking evidence contract is PASS, or any explicitly unresolved claim is outside the release scope and documented as such.

---

## 2. P1 — Operational astronomical data platform

**Goal:** real source data enters through a deterministic, auditable pipeline.

- [ ] ZTF/DR24 source adapter.
- [ ] acquisition manifests and checksums.
- [ ] source version/retrieval-date evidence.
- [ ] schema normalization.
- [ ] observation/QC contract.
- [ ] duplicate/invalid-observation handling.
- [ ] temporal cutoff support.
- [ ] provenance graph.
- [ ] reproducible subset materialization.
- [ ] replay test from manifest.

**Exit:** a pinned source subset can be acquired, normalized, validated and replayed from its manifest with identical declared semantics.

---

## 3. P2 — Scientific Feature Engine

**Goal:** scientific feature generation is a first-class extensible subsystem.

- [ ] feature-family registry.
- [ ] deterministic feature computation.
- [ ] missing-data semantics.
- [ ] feature provenance.
- [ ] quality/validity flags.
- [ ] performance evidence.
- [ ] schema/version compatibility.
- [ ] extensible backends beyond the historical 42-feature baseline.
- [ ] cross-backend regression tests.

**Exit:** feature outputs are deterministic, versioned, provenance-aware and scientifically validated.

---

## 4. P3 — Analysis & Inference

**Goal:** provide a general scientific analysis layer, not only classifier inference.

- [ ] model registry.
- [ ] production inference.
- [ ] probability calibration.
- [ ] conformal uncertainty where applicable.
- [ ] OOD detection.
- [ ] failure taxonomy.
- [ ] reproducible result repository.
- [ ] deterministic report generation.
- [ ] analysis job orchestration.
- [ ] production E2E.

**Exit:** an analysis request produces a versioned scientific result with diagnostics and provenance through a stable interface.

---

## 5. P4 — External Scientific Validation

**Goal:** independently substantiate scientific claims.

- [ ] independent labeled benchmark.
- [ ] catalog/cross-match evidence.
- [ ] ALeRCE independent-reference evidence.
- [ ] StarEmbed reproducible fixture.
- [ ] raw/source-backed ZTF/DR24 fixture.
- [ ] leakage audit.
- [ ] temporal/future-data audit.
- [ ] benchmark-trained-artifact audit.
- [ ] OOD/failure suite.
- [ ] CPVS historical reconstruction investigation.
- [ ] benchmark regression suite.

**Exit:** every scientific claim included in the release has a corresponding reproducible evidence contract.

**CPVS rule:** exact historical reconstruction remains fail-closed unless independently proven. No predicate may be tuned merely to match the published cardinality.

---

## 6. P5 — Scientific Analysis Workbench

- [ ] source/data selection.
- [ ] feature selection.
- [ ] model/analysis selection.
- [ ] uncertainty/OOD inspection.
- [ ] catalog/cross-match views.
- [ ] experiment comparison.
- [ ] provenance/evidence view.
- [ ] exportable reports.

**Exit:** a user can execute a complete supported analysis workflow through the application without bypassing scientific service contracts.

---

## 7. P6 — Discovery & Continuous Improvement

- [ ] cumulative knowledge ledger.
- [ ] failure knowledge base.
- [ ] benchmark lessons.
- [ ] automated regression fixtures.
- [ ] release evidence bundle.
- [ ] performance/resource trend tracking.
- [ ] controlled feedback/retraining loop.
- [ ] discovery workflows beyond predefined classification.

**Exit:** new evidence and failures can be incorporated without losing historical lineage or reopening solved failure modes.

---

## 8. Permanent failure-prevention gate

Every phase must explicitly check the known failure classes before completion:

- invalid manifests;
- manifest/adapter contract mismatch;
- wrong source schema;
- duplicate/non-deterministic source results;
- shell execution errors;
- scientific predicate contamination by diagnostic fields;
- PASS without evidence;
- exact-membership mismatch;
- source drift;
- cascade failures;
- missing cumulative-learning records;
- lint/CI regressions.

For every newly discovered failure:

**Failure → Root Cause → Lesson → Rule → Regression → Architecture/Process update**

A phase cannot be Completed while a known failure has no prevention mechanism when one is reasonably implementable.

---

## 9. Release gates

### Gate A — Engineering

- [ ] tests;
- [ ] lint/type/static checks as applicable;
- [ ] package/build;
- [ ] security;
- [ ] API/schema compatibility;
- [ ] production E2E.

### Gate B — Scientific

- [ ] independent benchmark evidence;
- [ ] leakage/integrity audit;
- [ ] temporal correctness;
- [ ] provenance;
- [ ] reproducibility;
- [ ] calibration/OOD/failure evidence where applicable;
- [ ] external source-backed evidence.

### Gate C — Product

- [ ] source-driven end-to-end workflow;
- [ ] stable application/API boundary;
- [ ] durable scientific results;
- [ ] deterministic reporting;
- [ ] documented limitations;
- [ ] observability/reliability acceptance.

### Gate D — Final audit

- [ ] clean release candidate;
- [ ] complete evidence bundle;
- [ ] replay/verification;
- [ ] cumulative-learning review;
- [ ] no release-blocking unresolved issue;
- [ ] release freeze;
- [ ] v1.0 tag/release.

---

## 10. Definition of Complete

The project is **Complete** only when:

1. all declared product capabilities are implemented;
2. all declared capabilities are validated;
3. all release-blocking scientific gates pass;
4. all included scientific claims have adequate independent evidence;
5. leakage/integrity/temporal controls pass;
6. production E2E passes;
7. provenance and reproducibility are complete;
8. release artifacts are reproducible/checksummed;
9. documentation and limitations are complete;
10. known failures have prevention/regression protection;
11. cumulative-learning review passes;
12. final audit and release freeze pass;
13. v1.0 is tagged/released.

Until then, the project remains **In Progress**, even if individual components are production-ready.

---

## 11. Final execution path

**P0 Recovery  
→ P1 Data Platform  
→ P2 Feature Engine  
→ P3 Analysis & Inference  
→ P4 External Scientific Validation  
→ P5 Workbench  
→ P6 Discovery/Continuous Improvement  
→ Final Audit  
→ Release Freeze  
→ v1.0  
→ Complete**

No hidden phase remains after v1.0. Post-release work is a new lifecycle/release cycle, not unfinished v1.0 work.

---

**Current status:** P0 Completed.  
**Current blocker:** none in the former scientific-validation recovery scope.  
**Next:** release-scope audit → release freeze → publication of the currently declared software release. v1.0 remains gated by the complete product-scope audit.


## 12. Release publication lesson — 2026-10-05

The immutable-release failure is closed and regression-protected. Release publication is now a finite, validated step rather than a manual retry loop. The workflow must never mutate an immutable release; it must verify an already-complete immutable release or select a fresh deterministic release tag for a new publication.
