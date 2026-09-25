# Scientific Validation Architecture

## Product role

Scientific Validation & External Benchmarking is a permanent product-level gate of the Astronomical Data Analysis & Discovery Platform. It is part of development, regression control, release acceptance, and scientific reporting.

The architecture validates the complete scientific chain:

`ingestion -> normalization -> QC -> scientific feature generation -> classification -> probability/calibration -> OOD/anomaly -> provenance -> reproducible inference`

A successful benchmark is not proof of global correctness. It is quantitative, reproducible evidence for the declared population, source versions, labels, preprocessing, and evaluation conditions.

## Components

### Benchmark Registry

Versioned manifests live under `configs/benchmarks/`. Each manifest records:

- benchmark identity and source/version;
- retrieval date, source URL, DOI/license;
- object IDs and hashes when applicable;
- schema and label taxonomy;
- class mapping;
- split definition;
- leakage exclusions;
- preprocessing and input contracts;
- ground-truth provenance;
- independent reference-system provenance;
- benchmark code version.

Large scientific datasets are never committed to Git.

### Benchmark Runner

`ztf_classifier.validation.runner` provides a deterministic table benchmark execution path. It computes classification, probabilistic, calibration, OOD/coverage, and confusion diagnostics where the manifest supplies the required evidence.

The runner hashes its input and writes both machine-readable JSON and human-readable Markdown evidence.

### Reference adapters

Reference systems are adapters, not truth providers. ALeRCE API/TAP is explicitly represented as an independent reference system. Its predictions must remain separate from ground truth.

Planned adapters:

1. StarEmbed ZTF_40k
2. ZTF periodic-variable classification release (~730k)
3. historical ZTF periodic-variable catalog (~781k)
4. pinned ZTF DR24 source-backed subset
5. ALeRCE API/TAP

### Leakage gate

The release contract requires:

- object overlap detection;
- duplicate-object detection across splits;
- target-leakage audit;
- future-data leakage audit;
- benchmark-trained-artifact exclusion;
- preprocessing consistency audit.

Checks that a generic table runner cannot infer are deliberately reported as `NOT_EXECUTED` and therefore block scientific acceptance.

### Regression tracking

`ztf_classifier.validation.regression` compares frozen benchmark reports against current results using versioned tolerances. A regression remains release-blocking until scientifically investigated and dispositioned.

## Validation layers

| Layer | Evidence | Ground truth? |
|---|---|---|
| Independent labeled benchmark | external labels | only where source provenance supports that interpretation |
| Catalog/cross-match | catalog identity/labels | documented evidence, not universal truth |
| Independent classifier | ALeRCE/reference predictions | **No** |
| Raw/source-backed ZTF | pinned source observations | source-backed evidence |
| OOD/failure cases | explicit edge populations | diagnostic evidence |

Ground truth and model agreement are never conflated.

## Release integration

Normal CI validates benchmark manifests and the validation code without requiring large downloads.

Scheduled/manual scientific validation executes source-backed benchmark adapters. Release publication remains fail-closed until the Production Acceptance Checklist contains no unresolved scientific-validation blocker.

Any change affecting feature generation, preprocessing, model, inference, calibration, conformal prediction, OOD, normalization, or scientific API contracts must trigger the relevant benchmark regression suite.

## Scientific Validation Dashboard / Report layer

Every release validation package is expected to expose:

- benchmark IDs and versions;
- evaluated population;
- metric results;
- regressions and disposition;
- out-of-domain scope;
- known failure cases;
- provenance completeness;
- scientific gate status.

The current runner writes the foundational report artifacts; the Workbench/dashboard surface is the next product integration slice.

### Evaluation role contract

Every benchmark manifest declares an `evaluation_role`:

- `ground_truth`: the label column is an independently sourced evaluation label and requires documented ground-truth provenance.
- `reference_system`: the label column contains an independent classifier/reference output and requires reference-system provenance, but is never treated as ground truth.

Runner reports preserve this role explicitly. Agreement with a reference system can be reported as a validation signal, but cannot satisfy the independent-ground-truth requirement.


## Release-gate execution

The scientific validation architecture is fail-closed at release time. The executable gate is implemented by `ztf_classifier.validation.gate` and evaluates all five permanent benchmark registrations, their immutable evidence reports, required leakage checks, provenance completeness, and source/object hashes.

The gate has two distinct operational modes:

- ordinary CI validates the registry/contract and deterministic runner without requiring multi-gigabyte external datasets;
- release validation requires complete source-backed evidence for every required benchmark and exits non-zero while any benchmark remains `NOT_VERIFIED`, `BLOCKED`, or missing.

This separation prevents expensive external acquisition from contaminating ordinary unit-test feedback while preserving a hard scientific release boundary.


## Cumulative learning integration

Scientific validation is both a gate and a knowledge generator. Every execution produces evidence that must be consumed by later iterations.

The lifecycle is:
AUDIT -> RETRIEVE PREVIOUS KNOWLEDGE -> DEFINE OBJECTIVE -> DEFINE BASELINE -> PLAN -> IMPLEMENT -> TEST -> MEASURE -> VALIDATE -> FAILURE/ROOT-CAUSE ANALYSIS -> KNOWLEDGE EXTRACTION -> UPDATE KNOWLEDGE BASE -> UPDATE TESTS/RULES -> COMPARE AGAINST PREVIOUS BASELINE -> ACCEPT/REVISE -> NEXT STAGE.

The cumulative quality vector is contextual: Accuracy, Correctness, Speed, Efficiency, Reliability, Robustness, Coverage, Reproducibility, and Scientific Validity. Scientific validity and release integrity take precedence over local optimization.

Benchmark evidence is propagated through the operational knowledge layer at docs/knowledge/. Important failures must become root-cause records and executable regression protection where possible. The cumulative improvement ledger at docs/knowledge/CUMULATIVE_IMPROVEMENT_LEDGER.md records baseline, change, evidence, regression, knowledge IDs, tests, decision, and next-stage impact.

Changes to feature generation, preprocessing, model, inference, calibration, conformal prediction, OOD, normalization, or scientific APIs must carry forward the relevant prior benchmark lessons and produce updated evidence where applicable.
