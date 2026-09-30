# ZTF Classifier — Project Continuity Handbook v2.3

## Status and purpose

This handbook supersedes v2.2 as the current cumulative project handbook draft for the recovery and product-unblocking stage. It preserves the immutable historical baseline and all validated lifecycle rules while incorporating the latest scientific-validation findings and the architectural separation between the product path and historical external-benchmark reconstruction.

- Repository: `saeed92m/ztf-classifier`
- Product identity: **Astronomical Data Analysis & Discovery Platform**
- Current implementation/recovery PR: #124, `ci/heavy/fix-scientific-validation-blockers-20260928`
- Latest verified PR head at handbook update: `d867349215660ee6f44eb1195781184c6373f75d`
- Immutable scientific baseline: `v0.2.0` — never rewrite
- Product-level Scientific Validation: permanent release gate
- External benchmark reconstruction: evidence layer for its declared historical-reproduction claim
- Current live heavy validation run: Scientific Validation #447 / run `36689743353`

## 1. Product definition

The project is not architecturally limited to a classifier. Its target is a scientific data-analysis and discovery platform that can:

1. acquire astronomical observations from supported sources;
2. normalize and quality-control observations;
3. generate scientifically defined, provenance-aware features;
4. perform ML and statistical analysis;
5. quantify uncertainty and calibration;
6. detect out-of-domain and failure conditions;
7. produce reproducible scientific results and reports;
8. preserve provenance, evidence, model/data versions, and limitations.

Canonical product flow:

`source data -> ingestion -> normalization/QC -> scientific feature generation -> ML/statistical analysis -> uncertainty/calibration/OOD -> scientific outputs -> provenance/evidence`

A benchmark is evidence about this system; a benchmark is not the system itself.

## 2. Immutable baseline and lineage

The validated `v0.2.0` scientific prototype remains immutable. Its historical evidence includes a controlled 150-object ZTF benchmark, 15 ALeRCE classes, 10 objects per class, 42 frozen features, an XGBoost baseline, calibration/conformal/OOD components, and the historical cutoff used by that prototype.

Later work must preserve lineage. New validation or product work must not silently rewrite that baseline or retroactively change its meaning.

## 3. Cumulative learning lifecycle

Every meaningful stage follows:

AUDIT -> RETRIEVE PREVIOUS KNOWLEDGE -> DEFINE OBJECTIVE -> DEFINE BASELINE -> PLAN -> IMPLEMENT -> TEST -> MEASURE -> VALIDATE -> ROOT-CAUSE ANALYSIS -> KNOWLEDGE EXTRACTION -> UPDATE KNOWLEDGE -> UPDATE TESTS/RULES -> COMPARE -> ACCEPT/REVISE -> NEXT STAGE.

Knowledge states are explicit: FACT, VERIFIED, SUPPORTED, HYPOTHESIS, ASSUMPTION, UNRESOLVED, REJECTED.

A failure is considered learned only when its prevention is encoded where practical:

Failure -> Root Cause -> Lesson -> Rule/Design Change -> Regression Test -> Prevention.

## 4. Scientific validation architecture

Scientific acceptance remains release-blocking. Required evidence layers are:

1. independent labeled benchmark;
2. catalog/cross-match evidence;
3. independent classifier/reference system;
4. raw/source-backed ZTF reproduction;
5. OOD and failure-case validation.

ALeRCE is reference-system evidence, not absolute ground truth. External datasets remain outside Git; manifests, hashes, contracts, reports, and provenance remain in Git.

No single accuracy/F1/calibration/OOD number is sufficient for scientific acceptance.

## 5. The CPVS 730k finding — root cause and resolution

The recent blocker was an external benchmark reconstruction problem, not an ML failure and not a failure of the product data-analysis architecture.

The relevant population is the ZTF Catalog of Periodic Variable Stars (CPVS) context:

- parent catalog: 781,602 objects;
- independently published selected membership: 730,184 objects;
- current raw-selection candidate: 741,788 objects;
- exact intersection with the published set: 730,184;
- published-only: 0;
- candidate-only: 11,604.

Therefore every published 730,184 object is contained in the current candidate, while the current predicate admits 11,604 additional parent objects.

The important scientific conclusion is:

**11,604 is a selection-reconstruction discrepancy. It is not 11,604 bad objects, 11,604 ML mistakes, or 11,604 production failures.**

The current predicate reproduces the published set as a subset but has additional candidates. The exact historical selection semantics have not yet been proven equivalent to the current reconstruction. Possible causes include historical quality/flag semantics, source snapshot differences, parsing/join semantics, or undocumented selection details. These remain hypotheses until source evidence confirms them.

### Explicit non-solution

A threshold must not be introduced merely to force 741,788 down to 730,184. In particular, a magnitude cutoff selected because it makes the count match would be scientific overfitting to the expected answer unless independently supported by the source methodology.

## 6. Product gate vs external-reproduction gate

The project now distinguishes two scopes:

### Product Scientific Gate — release blocking

This validates whether the actual platform can ingest, analyze, validate, and reproduce scientific outputs. It covers product-scope benchmarks and integrity checks such as DR24 source-backed subsets, controlled labeled benchmarks, independent reference evidence, leakage checks, feature determinism, provenance, calibration/OOD, and failure analysis.

### External CPVS Reproduction Evidence — claim-specific fail-closed

The 730k/781k CPVS reconstruction remains fail-closed for the narrower claim:

> exact historical reconstruction of the published CPVS membership.

If exact membership is unresolved, the project records `UNRESOLVED` and retains candidate, diagnostic, and membership-audit evidence. It must not silently claim exact historical reproduction.

This separation prevents a historical benchmark reconstruction issue from blocking unrelated product development while preserving scientific honesty.

## 7. Current CI evidence

As of this handbook update:

- PR #124 is open and mergeable.
- Scientific Validation run #447 is active.
- Source-backed job has successfully completed dependency installation, acquisition of the 781k parent evidence, StarEmbed acquisition, CPVS light-curve download/normalization, and parent-integrity validation.
- It is currently executing the 730k derivation step.
- The benchmark/lifecycle contract job has completed successfully: registry validation, scientific validation contract tests, and cumulative lifecycle tests all passed.


The final heavy source-backed outcome is intentionally not recorded as PASS until the live run completes.

## 8. Current product execution contract

The intended operational product is source-driven rather than benchmark-driven. A supported ZTF release such as DR24 is treated as an input source; the platform acquires a declared subset, records source/version/manifest/checksums, normalizes observations, applies QC and temporal/leakage controls, computes versioned scientific features, runs analysis/inference, quantifies uncertainty and OOD status where applicable, and emits reproducible scientific results with provenance. DR24 is currently the latest public ZTF data release according to IRSA, with Objects and Lightcurves available through archive services and HATS/Parquet interfaces.

The historical CPVS benchmark is therefore an external validation instrument. It is not the definition of the production data path and must not dictate arbitrary product selection thresholds.

## 9. Product roadmap

### P0 — Unblock and stabilize the scientific core
- complete PR #124 validation;
- preserve the CPVS unresolved evidence boundary;
- ensure product-scope validation can execute independently;
- eliminate CI/repository contract regressions;
- update knowledge, failure, and architectural records.

### P1 — Product data path
- pinned ZTF/DR24 source-backed acquisition;
- ingestion contracts;
- normalization and QC;
- deterministic observation model;
- scalable scientific feature generation;
- provenance at observation, feature, model, and result levels.

### P2 — Analysis and inference
- model registry and production inference;
- uncertainty and calibration;
- conformal diagnostics where applicable;
- OOD/failure detection;
- reproducible scientific result store;
- deterministic scientific reports.

### P3 — Scientific validation
- StarEmbed reproducible adapter;
- catalog/cross-match validation;
- ALeRCE independent-reference adapter with immutable evidence strategy;
- DR24 source-backed reproduction subset;
- CPVS historical reconstruction investigation;
- full leakage and temporal-integrity audits;
- benchmark regression suite.

### P4 — Discovery platform
- scientific catalog operations;
- analysis jobs and durable workers;
- Scientific Analysis Workbench;
- experiment/benchmark comparison;
- provenance/evidence browser;
- discovery-oriented workflows beyond classification.

### P5 — Production acceptance and continuous improvement
- release evidence automation;
- visible benchmark scope and limitations;
- cumulative learning ledger;
- failure-to-regression prevention loop;
- resource/performance evidence;
- reproducible release packages.

## 10. Definition of Done

A stage is complete only when:

1. prior knowledge was retrieved and used;
2. baseline is explicit;
3. objective and expected improvement are defined;
4. evidence is measured;
5. tests pass for the change;
6. failures have root causes;
7. lessons are recorded;
8. knowledge status is classified;
9. regression protection exists where practical;
10. architecture/roadmap are updated when affected;
11. unresolved risks are explicit;
12. output is reusable by the next stage;
13. release-gate semantics are preserved.

## 11. Source-of-truth hierarchy

1. GitHub source, merged history, tags, and release records for code and implementation state.
2. Source-backed benchmark manifests and evidence for scientific claims.
3. Notion for durable human-readable project knowledge and navigation.
4. This handbook for lifecycle, architecture, validation semantics, and roadmap continuity.

Notion must never be treated as a substitute for Git history.

## 12. Current open scientific questions

- What exact historical quality/selection semantics account for the 11,604 candidate-only CPVS objects?
- Which CPVS source snapshot and undocumented preprocessing details are required for exact reproduction?
- Which product-scope benchmark will serve as the primary release regression fixture for each analysis mode?
- Which DR24 subset and expected-answer evidence should become the canonical raw-source product fixture?

These are tracked questions, not reasons to stop unrelated product development.

## 13. Permanent engineering rule

Never optimize a benchmark number in isolation. Reproduce the scientific meaning first, preserve provenance, distinguish evidence scopes, and keep the product moving through independently validated stages.

---
Source lineage: repository `saeed92m/ztf-classifier`; handbook v2.2; Scientific Validation roadmap; cumulative-learning roadmap; PR #124 recovery work; current run #447 evidence; IRSA ZTF DR24 documentation.
