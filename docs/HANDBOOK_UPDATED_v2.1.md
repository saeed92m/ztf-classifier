# ZTF Classifier — Project Continuity Handbook v2.1

## Status

This document is the cumulative-learning successor to Handbook v2.0. It preserves v2.0 and adds the mandatory Cumulative Learning & Continuous Improvement lifecycle. It is authoritative for the process controls introduced by this change; historical release facts remain governed by the immutable Git history and release records.

- Repository: saeed92m/ztf-classifier
- Default branch: main
- Immutable scientific baseline: v0.2.0
- Product scope: Astronomical Data Analysis & Discovery Platform
- Scientific Validation & External Benchmarking: permanent Product-Level Gate
- Current external scientific blocker: Issue #51, historical ALeRCE raw-cache/source drift

## 1. Cumulative Learning & Continuous Improvement Principle

Every iteration must consume all validated and relevant knowledge from earlier iterations and improve the inherited baseline where applicable.

An iteration is not considered an improvement merely because the codebase grows or one metric increases. Improvement is assessed against evidence across the dimensions relevant to the change:

Accuracy, Correctness, Speed, Efficiency, Reliability, Robustness, Coverage, Reproducibility, Scientific Validity.

Trade-offs are allowed when technically or scientifically justified, explicitly measured, regression-checked, and recorded. Scientific correctness, reproducibility, and release integrity cannot be sacrificed for local optimization.

## 2. Mandatory lifecycle

Every meaningful Stage, PR, benchmark cycle, model iteration, feature-engine change, performance optimization, or release hardening cycle follows:

AUDIT
-> RETRIEVE PREVIOUS KNOWLEDGE
-> DEFINE OBJECTIVE
-> DEFINE BASELINE
-> PLAN
-> IMPLEMENT
-> TEST
-> MEASURE
-> VALIDATE
-> FAILURE / ROOT-CAUSE ANALYSIS
-> KNOWLEDGE EXTRACTION
-> UPDATE KNOWLEDGE BASE
-> UPDATE TESTS / RULES
-> COMPARE AGAINST PREVIOUS BASELINE
-> ACCEPT / REVISE
-> NEXT STAGE

Knowledge Extraction is mandatory.

## 3. Executable process contract

Cumulative lifecycle records are validated by ztf_classifier.lifecycle. The contract requires:

- stage identifier and objective;
- previous knowledge consumed;
- inherited baseline;
- expected improvement;
- measurement/evidence;
- validation evidence;
- failure/root-cause status;
- knowledge extraction with an allowed evidence status;
- regression status;
- decision;
- knowledge carried forward.

Allowed knowledge statuses:

FACT, VERIFIED, SUPPORTED, HYPOTHESIS, ASSUMPTION, UNRESOLVED, REJECTED.

Unverified knowledge must not silently become an inherited fact.

## 4. Operational Knowledge Layer

The operational memory is version-controlled under docs/knowledge/:

- PROJECT_KNOWLEDGE_BASE.md
- ARCHITECTURAL_DECISIONS.md
- SCIENTIFIC_FINDINGS.md
- FAILURE_DATABASE.md
- BENCHMARK_LESSONS.md
- PERFORMANCE_LESSONS.md
- TESTING_LESSONS.md
- DATA_QUALITY_FINDINGS.md
- MODEL_FINDINGS.md
- RELEASE_LESSONS.md
- CUMULATIVE_IMPROVEMENT_LEDGER.md

The knowledge layer is part of the engineering lifecycle, not decorative documentation.

## 5. Failure -> Knowledge -> Prevention

Every important failure follows:

Failure -> Root Cause -> Lesson -> Rule / Design Change -> Regression Test -> Future Prevention.

A failure is not fully learned until its prevention is encoded where technically possible.

The historical ALeRCE drift in Issue #51 is an explicit example: live service data cannot replace immutable historical evidence, and frozen assertions must not be weakened to make mutable live data pass.

## 6. Performance and process measurement

Where relevant, iterations record before/after:

- runtime
- throughput
- latency
- memory
- CPU/GPU utilization
- I/O
- batch efficiency
- feature-generation time
- inference time

Process metrics may include audit time, implementation time, debugging time, regression-fix time, rework count, repeated-failure count, PR cycle time, and test execution efficiency.

If a measurement is not applicable or unavailable, record NOT_MEASURED rather than inventing a value.

## 7. Feature Engine and model lifecycle

Scientific Feature Generation must track feature quality, determinism, runtime, missing-data robustness, schema compatibility, provenance, and scientific validity.

Model iterations must compare the previous model and new model through relevant benchmark metrics, calibration, OOD, failure analysis, reproducibility, and inference performance. No single metric establishes improvement.

## 8. Scientific Validation remains release-blocking

The cumulative-learning process strengthens, but never relaxes, the permanent Scientific Validation Product-Level Gate.

The five required evidence layers remain:

1. Independent labeled benchmark
2. Catalog / cross-match evidence
3. Independent classifier/reference system
4. Raw/source-backed ZTF reproduction
5. OOD / failure-case validation

Ground truth remains separate from model agreement. ALeRCE is independent reference evidence, not absolute ground truth.

Large scientific datasets remain outside Git. Git stores manifests, checksums, configurations, contracts, reports, and code.

A benchmark passing is evidence for its declared scope, population, source/version, labels, preprocessing, and evaluation conditions; it is not proof of universal correctness.

## 9. Definition of Done — cumulative stage

A stage is Done only when:

1. previous relevant knowledge was retrieved and used;
2. inherited baseline is explicit;
3. expected improvement or justified trade-off is defined;
4. measurements/evidence are recorded;
5. tests and validation are complete for the change;
6. failures have root-cause analysis;
7. lessons learned are recorded;
8. new knowledge is classified and stored;
9. regression protection is added where possible;
10. roadmap/architecture are updated when the change affects them;
11. no important unresolved regression is silently accepted;
12. the output is reusable by the next stage;
13. scientific-gate requirements remain satisfied or explicitly blocked by the existing release gate.

## 10. Source of truth and immutability

GitHub main, immutable tags, and merged history are the source of truth for source code. v0.2.0 must never be rewritten.

Scientific evidence must be source-backed, reproducible, and provenance-complete. External-source drift is recorded as evidence, not hidden by relaxing tests.

## 11. Canonical project documents

- v2.0 historical continuity: docs/HANDBOOK_UPDATED_v2.0.md
- this cumulative successor: docs/HANDBOOK_UPDATED_v2.1.md
- cumulative architecture: docs/architecture/CUMULATIVE_LEARNING_ARCHITECTURE.md
- scientific validation architecture: docs/architecture/SCIENTIFIC_VALIDATION_ARCHITECTURE.md
- cumulative roadmap: docs/roadmap/CUMULATIVE_LEARNING_ROADMAP.md
- scientific validation roadmap: docs/roadmap/SCIENTIFIC_VALIDATION_ROADMAP.md
- production acceptance: docs/PRODUCTION_ACCEPTANCE_CHECKLIST.md
- operational knowledge: docs/knowledge/

## 12. Permanent engineering rule

No future Stage is allowed to start from a clean conceptual slate when relevant validated knowledge already exists. The inherited baseline, prior failures, benchmark lessons, regression history, and architectural decisions are inputs to the next Stage.
