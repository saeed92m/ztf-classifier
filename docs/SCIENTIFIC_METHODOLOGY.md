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

The immutable published membership reference contains 730,184 objects from a parent table with 781,602 rows. The latest recorded Seq-based heavy audit reports 741,786 candidates, all 730,184 published members in the candidate set, 11,602 candidate-only objects, and zero published-only or unmapped published names (run [#38121913146](https://github.com/saeed92m/ztf-classifier/actions/runs/38121913146); see [Issue #170](https://github.com/saeed92m/ztf-classifier/issues/170)). These are recorded diagnostic results and should be revalidated against the primary artifact hashes before new scientific claims. The four-field predicate reproduces the membership set diagnostically, but its identity with the publisher's historical rule is not established. Exact historical selection semantics remain unresolved; do not force cardinality by threshold tuning.

## Reproducibility

Scientific claims require source identity, retrieval/version information, object identifiers, hashes, schemas, taxonomy, temporal/leakage controls, and retained evidence artifacts.

## CPVS parallel experiment decision

The project compares (A) source-backed reconstruction/Jupyter processing and (B) provenance-rich discrepancy reporting. Neither is preselected. A matching count alone is insufficient; compare identifier integrity, reproducibility, per-object inclusion/exclusion reasons, false inclusion/exclusion against an explicit reference, invalid-value handling, and independent source-backed astronomical inputs. See [the experiment plan](https://github.com/saeed92m/ztf-classifier/blob/experiment/cpvs-jupyter-reconstruction-20261025/docs/experiments/CPVS_PARALLEL_RESOLUTION_EXPERIMENT_PLAN_2026-10-25.md).