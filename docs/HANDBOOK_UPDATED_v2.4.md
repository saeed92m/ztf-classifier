# ZTF Classifier — Project Continuity Handbook v2.3

## 0. Purpose and completion contract

This is the current project-continuity handbook for the **ZTF Classifier / Astronomical Data Analysis & Discovery Platform**.

It has two jobs:

1. preserve the scientific and engineering knowledge accumulated during development;
2. define, in an auditable way, what must be true before the project may be declared **Complete / v1.0 Released**.

The project is **not complete merely because CI is green, a model runs, or a benchmark number looks good**.

### Completion rule

The project may be declared complete only after all required gates below are simultaneously satisfied:

- implementation scope is complete for the declared product release;
- unit, contract, regression, integration and production-E2E tests pass;
- scientific validation and external benchmarking pass their declared evidence contracts;
- leakage/integrity/temporal audits pass;
- provenance and reproducibility evidence is complete;
- production data path works independently of any single benchmark;
- uncertainty/calibration/OOD and failure handling are validated where applicable;
- API/schema/artifact contracts are stable and documented;
- release artifacts are reproducible and checksummed;
- known limitations are documented;
- every release-blocking unresolved item is closed or explicitly excluded from the release scope with scientific justification;
- cumulative-learning review is complete: baseline → evidence → failure/root cause → lesson → prevention rule → regression protection → roadmap update;
- final E2E audit and release-freeze audit pass.

Only then may the project move:

**Validated → Release Candidate → Final Audit → v1.0 Release → Complete.**

---

## 1. Product identity

The target product is an **Astronomical Data Analysis & Discovery Platform**, not merely a classifier.

Canonical flow:

`source data → ingestion → normalization/QC → scientific feature generation → ML/statistical analysis → uncertainty/calibration/OOD → scientific outputs → provenance/evidence`

The platform must support analysis and discovery workflows beyond the frozen historical classifier while preserving scientific lineage.

A benchmark is evidence about the platform; it is not the platform architecture.

---

## 2. Immutable baseline and lineage

The scientific baseline **v0.2.0 is immutable** and must never be rewritten.

Its lineage includes the controlled 150-object benchmark, 15 ALeRCE classes, 10 objects per class, 42 frozen features, XGBoost baseline, calibration/conformal/OOD components and the historical cutoff used by that prototype.

Later work must preserve the distinction between:

- historical baseline;
- current production-oriented implementation;
- new scientific evidence;
- unresolved historical-reproduction claims.

No new benchmark or product requirement may silently rewrite the meaning of v0.2.0.

---

## 3. Cumulative learning is an engineering rule

Every meaningful stage follows:

**AUDIT → RETRIEVE KNOWLEDGE → BASELINE → OBJECTIVE → PLAN → IMPLEMENT → TEST → MEASURE → VALIDATE → ROOT CAUSE → LESSON → RULE/DESIGN CHANGE → REGRESSION → ACCEPT/REVISE → HANDOFF**

A failure is not considered learned until its prevention is encoded where practical:

**Failure → Root Cause → Lesson → Prevention Rule → Regression Test → Architecture/Process Protection**

Required stage evidence:

- prior validated knowledge consumed;
- explicit baseline;
- measured result;
- failures and root causes;
- lessons and knowledge status;
- regression protection;
- affected documentation updated;
- next-stage impact recorded.

This is a permanent lifecycle requirement.

---

## 4. Permanent failure-prevention rules

The following classes of mistakes are now treated as regression-controlled project knowledge and must not be repeated:

| Failure pattern | Permanent prevention |
|---|---|
| Invalid JSON/manifest | Parse/validate every manifest before execution; CI contract test |
| Manifest/executable adapter mismatch | One declared contract; adapter contract test pins schema, columns, prefixes and selection semantics |
| Wrong ALeRCE schema | Source-backed schema verification; current ZTF TAP contract uses `ztf` |
| Duplicate/non-deterministic source rows | Deterministic ordering, explicit deduplication and final exact-shape validation |
| Shell line-continuation corruption | Execute workflow command syntax through CI validation; never introduce escaped continuations that change shell semantics |
| Quality flag accidentally used as CPVS selection criterion | Separate scientific selection predicates from diagnostic metadata; regression tests lock the published detection semantics |
| PASS claimed without real audit | PASS requires generated evidence and completed audit, not code-path existence |
| CPVS exact-membership mismatch hidden by thresholds | Never tune predicates to cardinality; preserve candidate/published/intersection diagnostics and fail closed |
| Historical/live-data drift | Record source version, retrieval time, hashes and evidence manifests; classify live-source claims explicitly |
| Cascade failures | Independent validation jobs and fail-closed boundaries; one benchmark issue must not silently corrupt unrelated product gates |
| Missing cumulative-learning records | Completion checklist requires knowledge/failure/regression updates |
| Lint/CI regression | CI remains release-blocking and every fix receives the appropriate regression coverage |

These rules are part of the architecture and Definition of Done, not optional notes.

---

## 5. Scientific validation architecture

Scientific Validation & External Benchmarking is a permanent **product-level release-blocking gate**.

Required evidence layers include:

1. independent labeled benchmark;
2. catalog/cross-match evidence;
3. independent classifier/reference system;
4. raw/source-backed ZTF reproduction;
5. OOD and failure-case validation;
6. leakage/integrity/temporal audits;
7. reproducibility and provenance evidence.

ALeRCE is an independent reference system for relevant evidence; it is **not absolute ground truth**.

Large scientific datasets must not be committed to Git. Git stores manifests, checksums, contracts, reports and provenance.

---

## 6. CPVS reconstruction: current scientific boundary

The CPVS investigation uses:

- parent population: **781,602**;
- independently published membership: **730,184**.

A prior audit found a candidate set containing all 730,184 published members plus additional candidates. That result is a historical-selection reconstruction finding, not an ML error count.

The project must not introduce a threshold, flag predicate, or arbitrary filter merely to make the reconstructed count equal 730,184.

Exact historical reproduction remains a claim-specific evidence question until the source semantics are independently demonstrated.

### Critical semantic rule

The published selection criterion must be implemented from the source methodology. Quality flags may be retained as diagnostic evidence when appropriate, but must not become selection criteria unless the source evidence explicitly requires them.

---

## 7. Product gate vs historical-reproduction gate

### Product Scientific Gate — release blocking

Validates the actual platform:

- source acquisition;
- normalization/QC;
- feature generation;
- analysis/inference;
- uncertainty/calibration/OOD;
- provenance;
- reproducibility;
- leakage/integrity;
- benchmark evidence;
- production E2E.

### External CPVS Reproduction Gate — claim-specific and fail-closed

Validates only the claim:

> exact historical reproduction of the published CPVS membership.

If unresolved, the evidence must be recorded as **UNRESOLVED**, never silently converted to PASS.

This separation prevents a historical benchmark reconstruction issue from being confused with a product failure, while preserving scientific honesty.

---

## 8. Current live validation status

At the time of this handbook revision:

- Canonical recovery branch: `ci/heavy/fix-scientific-validation-blockers-20260928`
- Canonical PR: **#124**
- Latest completed CodeQL run associated with the prior head: **success**
- Scientific Validation run **#526 / 36756251456** is the latest observed run before the current ALeRCE fix.
- Its contract-validation job passed.
- Its CPVS heavy job had reached CPVS light-curve download/normalization after successfully acquiring the 781k parent and StarEmbed evidence.
- Its independent DR24/ALeRCE evidence job failed on a validator-ordering bug: the query intentionally fetched 1,000 rows for deterministic duplicate resolution while validation incorrectly required 150 rows before truncation.
- The failure is fixed by deterministic sort → deduplicate by object ID → select 150 → final exact-shape validation.
- A regression test now locks this behavior.

**Therefore Scientific Validation is not declared PASS yet.**

The next CI run must validate the fix against the real ALeRCE source and complete the remaining scientific gate.

---

## 9. Production architecture

The production path is source-driven and benchmark-independent:

`source → acquisition manifest/checksum → normalized observations → QC → versioned feature engine → analysis/inference → uncertainty/OOD → scientific result → provenance/evidence`

Required properties:

- deterministic behavior;
- explicit schemas;
- versioned contracts;
- provenance at data/feature/model/result levels;
- restart-safe jobs where applicable;
- reproducible reports;
- stable API boundaries;
- no hidden benchmark-only behavior.

The frozen 42-feature v0.2 contract remains available as a historical/native backend. New feature backends must be versioned independently.

---

## 10. Definition of Done — stage and project level

### Stage DoD

A stage is complete only when:

- [ ] prior knowledge reviewed;
- [ ] baseline recorded;
- [ ] objective defined;
- [ ] implementation complete;
- [ ] tests complete;
- [ ] evidence measured;
- [ ] root causes recorded for failures;
- [ ] lessons captured;
- [ ] prevention/regression added;
- [ ] architecture/docs/roadmap updated;
- [ ] unresolved risks explicitly classified;
- [ ] next-stage handoff complete.

### Final Project DoD

All stage requirements above, plus:

- [ ] product scope complete;
- [ ] full production E2E path validated;
- [ ] scientific release gate PASS;
- [ ] independent external benchmark evidence PASS for all release claims;
- [ ] leakage/integrity/temporal audit PASS;
- [ ] OOD/failure validation PASS where applicable;
- [ ] reproducibility bundle PASS;
- [ ] provenance completeness PASS;
- [ ] release artifact/checksum verification PASS;
- [ ] API/schema compatibility PASS;
- [ ] security/reliability acceptance PASS;
- [ ] documentation and limitations complete;
- [ ] cumulative-learning/failure-prevention audit PASS;
- [ ] final clean-room/replay audit PASS;
- [ ] release freeze applied;
- [ ] v1.0 tag/release created only after all blocking checks pass.

**Until every release-blocking item is checked, the project is not Complete.**

---

## 11. Roadmap completion path

The final path is deliberately finite:

**P0 Scientific Recovery → P1 Operational Data Platform → P2 Scientific Feature Engine → P3 Analysis & Inference → P4 External Scientific Validation → P5 Analysis Workbench → P6 Discovery & Continuous Improvement → Final Audit → Release Freeze → v1.0 → Complete**

A roadmap item progresses:

**Planned → In Progress → Implemented → Validated → Completed**

Code existence alone never changes an item to Completed.

---

## 12. Source-of-truth hierarchy

1. Git source/history/tags/releases: implementation truth.
2. Source-backed evidence/manifests/reports: scientific-claim truth.
3. Notion: durable human-readable project knowledge/navigation.
4. This handbook: lifecycle, completion, architecture and continuity contract.

Notion cannot override Git history or scientific evidence.

---

## 13. Final completion certificate

When the project is actually finished, the repository must contain a final evidence bundle identifying:

- exact release commit/tag;
- software version;
- immutable baseline lineage;
- source datasets and versions;
- benchmark manifests and hashes;
- validation reports;
- leakage/integrity reports;
- OOD/failure reports;
- API/schema contracts;
- reproducibility environment;
- artifact checksums;
- known limitations;
- unresolved items explicitly declared none for the release scope;
- cumulative-learning and failure-prevention review;
- final E2E/replay result.

The final Handbook must then be updated from **RC → Released/Complete** with links to that evidence bundle.

This is how the project is considered finished: **not by elapsed work, but by an auditable evidence-backed release state.**

---

## 14. Current roadmap linkage

Canonical roadmap:

`docs/roadmap/CUMULATIVE_LEARNING_ROADMAP_v2.3.md`

Scientific validation details:

`docs/roadmap/SCIENTIFIC_VALIDATION_ROADMAP.md`

Production acceptance:

`docs/PRODUCTION_ACCEPTANCE_CHECKLIST.md`

Cumulative improvement policy:

`docs/RELEASE_CUMULATIVE_IMPROVEMENT_POLICY.md`

---

**Status:** Recovery / validation in progress.  
**Completion:** NOT YET DECLARED.  
**Immutable baseline:** v0.2.0 preserved.  
**Next completion authority:** the final release evidence bundle and final audit.


---

## 15. Frozen historical reference architecture — added 2026-10-04

The public ZTF/ALeRCE ecosystem review produced a concrete resolution for the historical-reproduction blockers.

### ALeRCE historical reference

- **Frozen reference:** Zenodo record **4279623**, DOI **10.5281/zenodo.4279623**.
- Scope: historical ALeRCE light-curve-classifier data through **2020-06-09**.
- Role: **historical reference-system evidence**, not ground truth.
- Live ALeRCE API/TAP remains a **current-source drift/reference lane**, not the immutable historical benchmark.
- Required verification: archive checksum, member inventory, schema, object IDs, feature columns, classifier-output schema, provenance.

### CPVS historical references

- **Parent catalog:** Zenodo **3886372**, 781,602-object ZTF CPVS parent.
- **Published membership:** Zenodo **5764899**, the published **730,184-object** quality-selected population.
- The 730,184 published membership is the authoritative immutable membership benchmark for the historical release.
- Re-running selection predicates against current light curves is retained as a **diagnostic reconstruction experiment** only.
- Cardinality must never be forced by changing thresholds or adding unsupported quality predicates.

### Evidence rule

Published immutable membership and current-source reconstruction are separate evidence lanes:

`published membership -> historical benchmark`
`current-source derivation -> reconstruction diagnostic`

A mismatch between those lanes is evidence about source/selection semantics; it is not permission to weaken the gate.

### Acquisition rule

Large archives remain outside Git. The repository stores:

- source URL/DOI;
- release/version;
- retrieval date;
- expected MD5/SHA-256;
- archive/member contract;
- object-ID/schema/taxonomy contract;
- leakage exclusions;
- preprocessing contract;
- generated evidence manifest and validation report.

The acquisition helper is `scripts/acquire_frozen_reference_evidence.py`.

### Ecosystem lessons adopted

The comparison with public ZTF/ALeRCE repositories confirms and reinforces:

- explicit preprocessing/feature lineage;
- versioned/frozen dataset releases;
- checksum-backed data acquisition;
- source-specific feature-name mappings;
- cross-match/catalog context as a first-class future layer;
- strict separation of uncertainty, OOD and scientific anomaly;
- future human-in-the-loop discovery and explainability contracts;
- image/multimodal readiness as an architecture boundary, not a reason to add unnecessary GPU infrastructure.

### Completion consequence

Issues **#51** and **#63** remain open until the immutable archives are actually acquired/verified and the resulting evidence is consumed by the scientific validation runner. The new contracts are implementation support, not evidence by themselves.

**Status:** historical-reference architecture implemented; archive verification and final scientific gate remain release-blocking work.

## 16. Current completion status — 2026-10-04

The project is **not yet Complete/v1.0**.

Completed:
- public ecosystem review and gap analysis;
- immutable historical reference contracts;
- fail-closed archive acquisition utility;
- live-vs-frozen source separation;
- provenance/hash requirements.

Remaining release blockers:
1. acquire and verify Zenodo 4279623;
2. acquire and verify Zenodo 5764899 and parent 3886372 as required by the final benchmark runner;
3. execute the frozen-reference adapters end-to-end;
4. close #51/#63 with evidence;
5. run the complete scientific release gate;
6. perform final E2E/replay/reproducibility audit;
7. freeze and tag v1.0 only after all blockers are PASS.
