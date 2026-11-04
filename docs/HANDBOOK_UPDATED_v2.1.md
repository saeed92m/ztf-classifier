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


## 2026-11-04 — DR24 raw acquisition and CPVS validation update

This section supplements the existing v2.1 process controls. It does not change the frozen v0.2.0 scientific baseline.

### Native ZTF DR24 acquisition

The development branch adds an optional, bounded raw-data adapter for the official IRSA ZTF DR24 Lightcurves HATS catalog.

- API: \`GET /v1/dr24/objects/{objectid}/lightcurve\`.
- Optional installation: \`python -m pip install "ztf-classifier[dr24]"\`.
- Backend request limit: 10 unique positive OIDs.
- Lookup: indexed \`objectid\` search only; no full-catalog scan.
- Provenance: requested/returned/missing OIDs, schema-column SHA-256, per-OID payload SHA-256, source metadata, and retrieval timestamp.
- Failure behavior: explicit acquisition error; no ALeRCE fallback.

The endpoint returns native DR24 data. It is not the normalized observation stream used by the frozen v0.2.0 feature and inference path.

### Source semantics and scientific limits

- \`hmjd\` is heliocentric Modified Julian Date (\`HJD - 2400000.5\`) at the exposure midpoint. Do not relabel it as geocentric MJD.
- \`mag\` uses the native ZTF calibration with zero AB color (\`g-r=0\`) assumed.
- \`magerr\` is the reported magnitude uncertainty and does not include all calibration/systematic terms.
- \`clrcoeff\` is the native linear color term. No color correction is applied by the raw adapter.
- \`catflags\` is preserved without a quality mask. Bit 15 (32768) marks cloud/moon-affected epochs; any production mask requires a versioned scientific contract.
- \`filterid\` maps 1/2/3 to g/r/i.
- A ZTF OID is defined per filter, field, and quadrant. One astrophysical source may have multiple OIDs. The adapter does not group or cross-match them.

IRSA source documentation: https://caltech-ipac.github.io/irsa-tutorials/ztf-lightcurves/

### DR24 acceptance status

The raw adapter, API route, unit tests, and API/research documentation are present on the development branch. PR #264 is Draft and is not merged.

Not yet verified:
- live indexed HATS acquisition on a bounded 30–50 OID sample;
- complete source-backed payload/schema/hash regression on a clean environment;
- time-coordinate and photometric normalization policy;
- versioned quality-flag policy;
- AOIC cross-OID identity and cross-match policy;
- normalized DR24-to-feature-to-inference execution;
- independent benchmark, calibration, abstention, and OOD validation.

A passing ordinary CI run is necessary but does not establish these scientific properties.

### CPVS membership validation blocker

The historical comparison remains:
- Parent Table 2: 781,602 unique IDs.
- Published reference: 730,184 unique IDs.
- Reconstructed candidates: 741,786 IDs.
- Candidate-only: 11,602.
- Published-only: 0.

Against published membership only, the object-level counts are TP=730,184, FP=11,602, FN=0, TN=39,816. These are membership-agreement metrics, not astrophysical ground-truth or model-performance metrics.

The candidate/reference intersection equals the reference. The candidate ∩ four-field-positive Table 2 set also equals the reference, but the published method describes the two-band SNR threshold and common period from Table 2. It does not document the four-field-positive condition. All 11,602 candidate-only objects have a finite positive common `Per` value, so missing common period does not explain their exclusion. Table 2 reports `Ng=0` for 13 and `Nr=0` for 1 of these objects, despite qualifying raw-archive detections in both bands; this is another source-level count mismatch. Do not treat the four-field coincidence as the root cause.

The 100- and 1,000-object diagnostic samples were independently reproduced exactly with the fixed SHA-256 seed. The 55 four-field-only controls have incomplete archived lightcurve coverage. A possible Seq 615170/615172 mismatch remains a hypothesis pending raw coordinate/time comparison.

Research notes:
- \`docs/research/CPVS_MEMBERSHIP_CONFUSION_MATRIX_2026-11-04.md\`
- \`docs/research/CPVS_FIXED_SAMPLE_REPRODUCTION_2026-11-04.md\`
- \`docs/research/CPVS_55_CONTROL_ARCHIVE_IDENTITY_LEAD_2026-11-04.md\`
- \`docs/research/CPVS_VIZIER_SEPARATOR_PARSER_DIAGNOSTIC_2026-11-04.md\`

Keep the CPVS blocker open until the parser regression passes, the independent membership crosswalk completes, and the 11,602 residuals have a reproducible source-level explanation.

### Baseline and release controls

- v0.2.0 feature, model, class order, and benchmark remain immutable.
- ALeRCE labels remain benchmark/reference labels, not independent ground truth.
- No release or tag was created.
- PR #264 remains Draft. PR #244 remains Draft.
- Do not merge or publish until current-head CI passes and the required scientific evidence is complete.
