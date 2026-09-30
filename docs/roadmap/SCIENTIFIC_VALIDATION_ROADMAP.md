# Scientific Validation Roadmap

Scientific validation is a permanent Product-Level Gate for the final Astronomical Data Analysis & Discovery Platform. Historical external-benchmark reconstruction is a separate evidence scope and must not be conflated with the product execution path.

## Stage V0 — Registry foundation

- [x] Versioned Benchmark Registry
- [x] Machine-readable benchmark manifests
- [x] Deterministic table runner
- [x] JSON + Markdown validation reports
- [x] SHA-256 input evidence
- [x] Explicit ground-truth/reference separation
- [x] Release-blocking regression comparison

## Stage V1 — Benchmark adapters

- [ ] StarEmbed ZTF_40k adapter and reproducible subset retrieval
- [ ] ZTF periodic-variable classification release (~730k) adapter
- [x] historical ZTF periodic-variable catalog (~781k) adapter
- [ ] pinned ZTF DR24 source-backed adapter
- [ ] ALeRCE API/TAP independent-reference adapter

Each adapter must preserve source/version/DOI/retrieval date/object IDs/hashes/schema/taxonomy/split/leakage/preprocessing/provenance.

## Stage V2 — Leakage and scientific integrity

- [ ] object overlap and duplicate-object audits across all benchmark populations
- [ ] target-leakage audit
- [ ] future-data/temporal leakage audit
- [ ] benchmark-trained-artifact audit
- [ ] preprocessing compatibility audit
- [ ] deterministic feature-generation audit
- [ ] schema compatibility audit
- [ ] provenance completeness audit
- [ ] failure-code correctness audit

Any unresolved required check blocks release.

## Stage V3 — Full metric and failure analysis

For applicable benchmarks (engine support implemented; execution/evidence remains release-gated):

- [x] accuracy and balanced accuracy
- [x] macro/weighted precision, recall, F1
- [x] per-class metrics and confusion matrix
- [x] log loss and Brier score
- [x] calibration/reliability diagnostics
- [x] OOD metrics
- [x] coverage/rejection
- [x] false-accept/false-reject analysis
- [x] QC acceptance rate
- [x] inference reproducibility
- [x] resource/latency evidence where relevant

## Stage V4 — Product integration

- [x] validation service integrated with the application layer
- [ ] Benchmark Registry exposed through scientific operations APIs
- [x] Scientific Validation Dashboard/Report integrated into Workbench
- [ ] release evidence generated automatically
- [ ] benchmark regression status visible per release
- [ ] out-of-domain scope and known failure cases visible to users

## Stage V5 — CI/release operations

- [x] registry contract validation in ordinary CI
- [x] scheduled heavy benchmark execution
- [x] manual release-candidate benchmark execution
- [x] regression artifacts retained as release evidence
- [x] release workflow consumes scientific validation status
- [x] no final release can bypass the scientific gate

## Permanent change-trigger policy

Relevant benchmarks must rerun after changes to:

- feature generation;
- preprocessing;
- model or model artifact;
- inference;
- calibration;
- conformal prediction;
- OOD/anomaly handling;
- normalization;
- scientific API contracts.

Benchmark regressions are release-blocking until reviewed and dispositioned.

## Initial source registry

The permanent source set is:

1. StarEmbed ZTF_40k
2. ZTF periodic-variable classification release (~730k objects)
3. historical ZTF periodic-variable catalog (~781k objects)
4. pinned ZTF DR24 source-backed subset
5. ALeRCE API/TAP as an independent reference system

The benchmark source data remains external to Git; Git stores the contracts, manifests, hashes, configurations, and reports.


## Cumulative Learning overlay — permanent lifecycle control

Every Scientific Validation stage is cumulative and must consume validated knowledge from previous stages.

Required stage record:
- Previous knowledge consumed
- Baseline inherited
- Expected improvement
- Metrics and evidence
- New knowledge generated
- New risks discovered
- Regression status
- Lessons learned
- Knowledge carried forward

The lifecycle is:
AUDIT -> RETRIEVE PREVIOUS KNOWLEDGE -> DEFINE OBJECTIVE -> DEFINE BASELINE -> PLAN -> IMPLEMENT -> TEST -> MEASURE -> VALIDATE -> FAILURE/ROOT-CAUSE ANALYSIS -> KNOWLEDGE EXTRACTION -> UPDATE KNOWLEDGE BASE -> UPDATE TESTS/RULES -> COMPARE AGAINST PREVIOUS BASELINE -> ACCEPT/REVISE -> NEXT STAGE.

Knowledge Extraction is mandatory. Knowledge status must be FACT, VERIFIED, SUPPORTED, HYPOTHESIS, ASSUMPTION, UNRESOLVED, or REJECTED. Unverified findings must not silently become inherited facts.

### Scientific multi-objective quality

Relevant iterations evaluate a contextual quality vector:

Accuracy, Correctness, Speed, Efficiency, Reliability, Robustness, Coverage, Reproducibility, Scientific Validity.

A local improvement that weakens scientific validity, correctness, reproducibility, or release integrity is not an accepted improvement. Trade-offs must be measured and recorded.

### Benchmark-to-knowledge loop

Each benchmark execution should produce:
- result evidence;
- failure patterns;
- class-specific weaknesses;
- data-quality findings;
- leakage findings;
- calibration findings;
- OOD findings;
- provenance findings;
- reproducibility findings;
- reusable regression protection.

These outputs feed the project knowledge layer and subsequent benchmark planning.

### Performance evidence

Where relevant, validation records runtime, throughput, latency, memory, CPU/GPU utilization, I/O, batch efficiency, feature-generation time, and inference time. Missing measurements are recorded as NOT_MEASURED, never fabricated.

This overlay does not relax the permanent Scientific Validation Product-Level Gate.


## Recovery architecture — CPVS exact-membership reconstruction

The CPVS 730k reconstruction is now explicitly split from the product gate.

Observed evidence:
- parent CPVS: 781,602
- published membership: 730,184
- current candidate: 741,788
- exact intersection: 730,184
- published-only: 0
- candidate-only: 11,604

Interpretation: the current selection predicate contains the complete published membership but also admits 11,604 additional parent objects. This is an unresolved historical-selection reconstruction discrepancy, not an ML error.

Policy:
1. Do not introduce a threshold solely to force the candidate count to 730,184.
2. Preserve candidate, diagnostic, and membership-audit evidence.
3. Mark exact historical CPVS reproduction `UNRESOLVED` until source semantics are independently established.
4. Do not let this claim-specific unresolved state block unrelated product ingestion, feature, analysis, or product-scope validation work.
5. Keep the product Scientific Gate release-blocking for its own declared evidence scope.

### Product-scope validation path

The release-blocking product path must continue independently through:
source acquisition -> ingestion -> normalization/QC -> feature generation -> analysis/inference -> calibration/OOD -> scientific result/provenance -> known-answer/external validation.

### External-reproduction path

The CPVS path remains responsible for proving the narrower claim of exact historical reproduction. It is fail-closed for that claim.
