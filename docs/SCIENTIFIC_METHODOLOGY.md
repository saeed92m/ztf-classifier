# ZTF Classifier — Scientific Methodology

## Scope

The platform analyzes public ZTF observations with explicit provenance, schema, temporal, leakage, and evidence boundaries.

## Immutable baseline

The v0.2.0 benchmark contains 150 objects across 15 ALeRCE reference classes, 42 frozen features, and an XGBoost baseline model. ALeRCE labels are benchmark/reference labels, not independent astrophysical ground truth.

## Evidence

Benchmark performance, external catalog/reference agreement, source-backed reproduction, OOD behavior, failure analysis, and human/scientific validation are distinct evidence types.

## Diagnostic semantics

Classification uncertainty, calibration, conformal prediction, OOD, and scientific anomaly are separate concepts. A high OOD score is not automatically an astrophysical anomaly.

## CPVS boundary

The immutable published membership contains 730,184 objects from a 781,602-object parent. Current reconstruction contains all published members plus 11,604 additional candidates. Exact historical selection semantics remain unresolved and must not be forced by threshold tuning.

## Reproducibility

Scientific claims require source identity, retrieval/version information, object identifiers, hashes, schemas, taxonomy, temporal/leakage controls, and retained evidence artifacts.