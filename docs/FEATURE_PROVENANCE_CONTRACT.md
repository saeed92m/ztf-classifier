# Frozen Feature Provenance Contract

## Purpose

This document defines the provenance fields required for every production feature manifest. It applies to the frozen v0.2 feature schema without changing that schema.

## Required fields

| Field | Meaning |
| --- | --- |
| feature | Canonical feature name |
| order | Stable feature order, 1 through 42 for v0.2 |
| group | Feature family/group |
| source_columns | Source observation columns used |
| min_observations | Minimum observations required by the feature |
| uses_future_observations | Whether values depend on observations after a declared cutoff |
| cutoff_compatible | Whether the feature can be computed without future observations |
| missing_behavior | Explicit behavior for insufficient/missing input |
| units | Physical/statistical units or dimensionless |

## v0.2 compatibility rule

The frozen production schema remains exactly 42 features. This document does not authorize adding, removing, renaming, or reordering v0.2 features.

The canonical source remains reports/tables/final_feature_set_v0.2.parquet. A future machine-readable feature manifest must be generated from that source rather than maintaining a second hand-edited list.

## Temporal leakage policy

For any future model/schema version, a temporal validation must construct features using only observations at or before the declared cutoff. Features marked uses_future_observations=true or cutoff_compatible=false must not enter a strict historical/online feature contract unless the feature computation explicitly defines a causal window.

## Provenance and reproducibility

Feature manifests should be persisted beside the dataset/model artifact with:

- feature-schema version;
- feature-schema SHA-256;
- software version;
- source dataset version;
- Git commit;
- creation timestamp;
- missingness/eligibility policy.

No new feature is permitted to silently enter the frozen v0.2 model. New scientific features require a new feature-schema version and a separately versioned model artifact.
