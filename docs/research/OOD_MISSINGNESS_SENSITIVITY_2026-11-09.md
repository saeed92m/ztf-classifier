# OOD Missingness Sensitivity — 2026-11-09

**Disposition: DIAGNOSTIC ONLY. No production eligibility policy is approved.**

## Purpose

Measure how missing feature values affect the frozen v0.2 production OOD score and reference-relative percentile.

The experiment does not change the model, the feature schema, the classifier, or the v0.2.0 baseline. It does not set a minimum coverage threshold.

## Reproducibility record

| Item | Value |
|---|---|
| Repository | `saeed92m/ztf-classifier` |
| Branch | `science/ood-missingness-experiment-20261109` |
| Experiment commit | `5c0c281c9791f85f0e237580ca5ca90cb8dbd8b5` |
| GitHub Actions run | [42694153530](https://github.com/saeed92m/ztf-classifier/actions/runs/42694153530) |
| Artifact ID | `13708656954` |
| Artifact SHA-256 | `e0c088b27c008fef1eb28da636252e8f31fc48aa933dbd495641c63e3d13e791` |
| Dataset | `data/processed/features_v0.2.parquet` |
| Dataset SHA-256 | `d08543cffe5db141d6a7e4ee429264acdaa50c6e4fd01f1b0fa2a36aa42a6a85` |
| Feature schema | `reports/tables/final_feature_set_v0.2.parquet` |
| Feature schema SHA-256 | `fed07fc291070ecbdc7bbc597fad5aac6a3f4a1746feb12a9f4c2407108af329` |
| Python | 3.11.16 |
| NumPy / pandas / SciPy | 2.4.6 / 3.0.6 / 1.17.1 |
| scikit-learn | 1.9.1 |

The artifact contains the machine-readable JSON report and four CSV outputs. GitHub retains the artifact until 2026-12-09.

## Frozen reference input

The dataset has 150 objects, 15 ALeRCE reference classes, and 10 objects per class. The model uses 42 ordered features.

- Feature cells: 6,300.
- Missing cells: 1,612 (25.59%).
- Complete objects: 59.
- Partial objects: 91.

ALeRCE labels are reference labels. They are not independent astrophysical ground truth.

The production OOD model uses IsolationForest with 300 estimators, `contamination="auto"`, and random state 42. The experiment reconstructed the OOD model by fitting `OODProductionModel` to the exact frozen feature matrix with the frozen OOD configuration.

**The persisted production artifact was not loaded.** This is a deterministic reconstruction from the frozen training matrix. It is not a byte-for-byte replay of `ood_model.joblib`.

The reference anomaly scores are in-sample scores. They are not independent test scores.

## Method

The experiment used only the 59 complete reference rows for paired masking. It preserved each object's unmasked score as its baseline.

For each row, the experiment selected feature positions uniformly at random and replaced them with NaN. This is MCAR masking. It used eight masking levels and 20 deterministic replicates per level.

Each level has 1,180 paired evaluations (59 objects × 20 replicates). The experiment has 9,440 paired evaluations in total.

The levels leave 41, 40, 38, 34, 30, 21, 11, or 1 feature observed.

The report measures:

- absolute and signed changes in anomaly percentile;
- anomaly-score changes;
- Spearman rank correlation against each object's baseline percentile;
- transitions across the existing 90th, 95th, and 99th reference-percentile flags.

The 90/95/99 values are existing OOD configuration thresholds. They are not calibrated probabilities. They are not new acceptance thresholds.

## Results

| Features missing | Coverage | Median absolute percentile shift | Median signed shift | Median Spearman rank correlation | Suppressed 90th-percentile flags | Suppressed 95th-percentile flags | Suppressed 99th-percentile flags |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 97.62% | 0.67 | -0.67 | 0.996 | 8.9% | 11.7% | 37.5% |
| 2 | 95.24% | 1.33 | -0.67 | 0.991 | 10.7% | 20.0% | 55.0% |
| 4 | 90.48% | 2.00 | -1.33 | 0.980 | 12.9% | 30.8% | 65.0% |
| 8 | 80.95% | 3.33 | -3.33 | 0.961 | 27.1% | 40.0% | 95.0% |
| 12 | 71.43% | 5.33 | -5.33 | 0.936 | 37.1% | 50.8% | 100.0% |
| 21 | 50.00% | 17.33 | -17.33 | 0.870 | 67.9% | 82.5% | 100.0% |
| 31 | 26.19% | 42.00 | -42.00 | 0.763 | 92.5% | 100.0% | 100.0% |
| 41 | 2.38% | 69.33 | -69.33 | 0.282 | 100.0% | 100.0% | 100.0% |

A negative percentile shift means that the masked row receives a lower anomaly percentile than its own unmasked baseline.

The suppression rate is calculated only among evaluations that were flagged at the same threshold before masking. It is not the percentage of all rows.

The baseline subset contains 14 objects above the 90th percentile, 6 above the 95th percentile, and 2 above the 99th percentile. Each object is evaluated 20 times. The 99th-percentile suppression rates therefore have a small denominator.

### Main findings

1. Missing features usually reduce the anomaly score and percentile in this experiment.
2. This effect can hide an object that was flagged with complete data.
3. With 4 missing features (90.48% coverage), 65% of the baseline 99th-percentile flags were suppressed.
4. With 8 missing features (80.95% coverage), 95% of the baseline 99th-percentile flags were suppressed.
5. With 12 missing features (71.43% coverage), all baseline 99th-percentile flags were suppressed.
6. With only one feature observed, all baseline flags at the 90th, 95th, and 99th percentiles were suppressed.

The ranking can remain fairly stable while the absolute percentile moves down. For example, at 8 missing features the median Spearman correlation is 0.961, but 95% of baseline 99th-percentile flags are suppressed. Rank stability alone is not enough to trust a threshold decision.

### Natural missingness association

On the 150 fitted reference objects:

- Complete rows have a median OOD percentile of 71.33.
- Partial rows have a median OOD percentile of 34.67.
- Missing feature count and OOD percentile have a Spearman correlation of -0.581.

This is a descriptive association. It is confounded by object identity and feature-missingness patterns. It is not a causal estimate.

## Limitations

- The paired experiment uses 59 complete rows from a 150-object reference dataset.
- MCAR masking does not reproduce correlated survey missingness.
- Feature-family masking was not run. The repository does not yet provide a verified machine-readable feature-family map for this experiment.
- The production OOD artifact was reconstructed. It was not loaded and compared byte-for-byte.
- Reference scores are in-sample.
- The experiment has no independent astrophysical OOD labels.
- The ALeRCE labels are not independent ground truth.
- The results do not establish OOD precision, recall, calibration, or population-level performance.

## Decision

**Do not use a fixed coverage threshold from this experiment. Do not suppress OOD scores based on an arbitrary rule.**

The evidence shows that missingness can suppress anomaly flags. The current per-row coverage and OOD evaluation-state fields are therefore important. Keep the states distinct:

- `evaluated_complete_features`
- `evaluated_with_missing_features`
- `evaluated_adequacy_unreported`
- `not_available`

A partial row must not be presented as equivalent to a complete-feature OOD evaluation.

## Required next work

1. Load the exact persisted `ood_model.joblib` and compare its reference scores with the reconstructed model.
2. Add a verified feature-family mapping. Run g-band, r-band, periodicity, and cross-band block-masking tests where the mapping supports them.
3. Reproduce real missingness patterns from the frozen feature dataset. Separate feature-generation failure, insufficient observations, and unavailable source data.
4. Evaluate with an independent labeled ID/OOD population. Do not use ALeRCE reference labels as ground truth.
5. Only then define and version an OOD eligibility policy. Add regression tests and a fail-closed scientific gate for that policy.

Until these steps pass, OOD eligibility remains a scientific validation blocker. This report does not change the frozen model, features, class order, or v0.2.0 baseline.
