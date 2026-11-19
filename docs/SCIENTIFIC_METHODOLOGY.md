# ZTF Classifier — Scientific Methodology

## Scope

The platform analyzes public ZTF observations with explicit source provenance, schema, temporal, leakage, and evidence boundaries.

## Immutable baseline

The v0.2.0 reference benchmark contains 150 objects across 15 ALeRCE reference classes, 42 frozen features, and the intended XGBoost model identity `baseline_v0.2`. ALeRCE labels are weak/reference labels, not independent astrophysical ground truth.

The original production model artifact has not been recovered or authenticated from accessible remote sources (Issue #282). Do not claim current production inference or substitute the lab-smoke artifact.

## Source roles

- DR24 HATS: primary source-native light-curve stream for the raw Explorer and planned product integration.
- ALeRCE: reference labels and a separate observation service; not independent universal ground truth.
- BTS: spectroscopic labels for a limited transient population; not a benchmark for all 15 v0.2.0 classes.
- Zubercal DR20: separate recalibrated-photometry stream with distinct identifiers, time semantics, and QC.

## DR24 boundaries

Preserve OID, filter, field, RCID, HMJD, mag, magerr, clrcoeff, catflags, source release, query, retrieval time, schema, and hashes. Do not infer physical identity from OID or angular proximity alone. Do not rename HMJD to MJD, apply unapproved color corrections, or impose an unapproved catflags mask.

The DR24 Explorer is raw-data inspection only. It does not run the frozen v0.2.0 model on DR24.

## Diagnostic semantics

Classification uncertainty, calibration, conformal prediction, OOD, scientific anomaly, catalog evidence, and explainability are separate concepts. A high OOD score is not proof of an astrophysical anomaly. A raw score is not a calibrated probability.

## CPVS boundary

The recorded Seq-based comparison reports:
- parent Table 2: 781,602 rows;
- published Table 4 membership: 730,184 objects;
- reconstructed candidates: 741,786 objects;
- intersection: 730,184;
- candidate-only: 11,602;
- published-only: 0.

The 11,602 candidate-only objects remain unexplained. Exact historical reconstruction is UNRESOLVED. Reverify these counts against source artifacts before any new run is described as current. Do not tune thresholds or filters to force the published cardinality. This is a separate historical-reproduction workstream; it does not block DR24 product development.

## Reproducibility

Scientific claims require source identity, retrieval/version information, object IDs, hashes, schemas, taxonomy, temporal/leakage controls, and retained evidence artifacts. A successful CI workflow is not full scientific acceptance when required evidence is skipped or unavailable.
