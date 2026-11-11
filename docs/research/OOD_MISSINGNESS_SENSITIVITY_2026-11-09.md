# OOD Missingness Sensitivity — 2026-11-09

**Disposition: DIAGNOSTIC ONLY. No production eligibility policy is approved.**

## Purpose

Measure how missing feature values affect the frozen v0.2 production OOD score and its reference-relative percentile.

The experiment uses two types of masking:

1. MCAR masking. It removes random feature values from complete rows.
2. Extraction-aligned masking. It removes feature groups by using the actual v0.2 observation-count rules.

The experiment does not change the model, feature schema, classifier, class order, or v0.2.0 baseline. It does not set a minimum coverage threshold.

## Reproducibility record

| Item | Value |
|---|---|
| Repository | `saeed92m/ztf-classifier` |
| Branch | `science/ood-missingness-experiment-20261109` |
| Experiment commit | `c99410d152530b2e78822b11913117a3286536da` |
| GitHub Actions run | [42698425064](https://github.com/saeed92m/ztf-classifier/actions/runs/42698425064) |
| Artifact ID | `13710761158` |
| Artifact SHA-256 | `bb12f5f6f511e27c4ab2f62c9c76e4825d4a08501ee0e2af96d6c6dc3c26546f` |
| Dataset | `data/processed/features_v0.2.parquet` |
| Dataset SHA-256 | `d08543cffe5db141d6a7e4ee429264acdaa50c6e4fd01f1b0fa2a36aa42a6a85` |
| Feature schema | `reports/tables/final_feature_set_v0.2.parquet` |
| Feature schema SHA-256 | `fed07fc291070ecbdc7bbc597fad5aac6a3f4a1746feb12a9f4c2407108af329` |
| Python | 3.11.16 |
| NumPy / pandas / SciPy | 2.4.6 / 3.0.6 / 1.17.1 |
| scikit-learn | 1.9.1 |

The artifact contains the JSON report, the generated feature-group mapping, and eight CSV/JSON evidence files. GitHub retains the artifact until 2026-12-09.

## Frozen reference input

The dataset has 150 objects, 15 ALeRCE reference classes, and 10 objects per class. The model uses 42 ordered features.

- Feature cells: 6,300.
- Missing cells: 1,612 (25.59%).
- Complete objects: 59.
- Partial objects: 91.

ALeRCE labels are reference labels. They are not independent astrophysical ground truth.

The production OOD configuration uses IsolationForest with 300 estimators, `contamination="auto"`, and random state 42.

The experiment reconstructed `OODProductionModel` by fitting it to the exact frozen feature matrix with the frozen OOD configuration.

**The persisted production artifact was not loaded.** The reconstructed model is not a byte-for-byte replay of `ood_model.joblib`. The repository does not contain a production OOD model artifact.

The reference anomaly scores are in-sample scores. They are not independent test scores.

## Feature-family mapping

The experiment derives the feature groups from the canonical v0.2 extraction functions. It does not maintain a second manual list of feature names.

The generated mapping partitions all 42 features into seven groups:

| Group | Features | Eligibility rule |
|---|---:|---|
| g basic | 13 | At least 10 valid g observations |
| g periodicity | 6 | At least 30 valid g observations |
| r basic | 13 | At least 10 valid r observations |
| r periodicity | 6 | At least 30 valid r observations |
| Cross-band color | 2 | At least 1 valid observation in each band |
| g variability ratio | 1 | Both bands present and at least 2 valid g observations |
| r variability ratio | 1 | Both bands present and at least 2 valid r observations |

The mapping follows these source functions and rules:

- `basic_band_features`
- `lomb_scargle_features`
- `basic_cross_band_features`
- `prepare_band_lightcurve`
- `BASIC_MIN_OBSERVATIONS = 10`
- `LS_MIN_OBSERVATIONS = 30`

The color features need one valid observation in each band. The variability ratios use a sample standard deviation. They need at least two observations in the relevant band. The cross-band function runs only when both bands have observations.

The full generated mapping and its source-column metadata are in `feature_group_mapping.json` in the experiment artifact.

## Natural missingness validation

The experiment compared every row's exact missing-feature set with the extraction-aligned patterns.

<badge color="success">150 / 150 exact matches</badge>

- Exact pattern matches: 150.
- Unmatched rows: 0.
- Ambiguous rows: 0.
- Complete rows: 59.
- Partial rows: 91.

This means that every missing-feature pattern in this frozen 150-object dataset matches the v0.2 extraction eligibility rules. This validates the missingness provenance for this dataset. It does not validate OOD accuracy.

| Natural extraction pattern | Objects | n_g range | n_r range |
|---|---:|---:|---:|
| Complete | 59 | 32–685 | 30–1,045 |
| Both periodicity groups unavailable | 23 | 10–26 | 11–27 |
| g periodicity unavailable | 11 | 15–28 | 30–77 |
| r periodicity unavailable | 11 | 31–144 | 12–27 |
| g has 2–9 observations | 6 | 2–6 | 32–170 |
| r has 2–9 observations; g has 10–29 | 4 | 10–25 | 4–9 |
| g has 2–9 observations; r has 10–29 | 12 | 2–9 | 10–27 |
| No valid g observations | 6 | 0 | 42–78 |
| No valid r observations | 7 | 31–747 | 0 |
| No g observations; r has 10–29 | 2 | 0 | 10–29 |
| No r observations; g has 10–29 | 1 | 20 | 0 |
| Both bands have 2–9 observations | 8 | 2–8 | 2–9 |

The eight objects with 38 missing features have 2–9 valid observations in both bands. They retain only four cross-band features. This pattern matches the extraction rules exactly.

## Method

### MCAR masking

The paired MCAR experiment uses the 59 complete reference rows. It preserves each object's unmasked score as its baseline.

For each row, the experiment selects feature positions uniformly at random and replaces them with NaN. It uses eight masking levels and 20 deterministic replicates per level.

Each level has 1,180 paired evaluations (59 objects × 20 replicates). The experiment has 9,440 MCAR paired evaluations in total.

The levels leave 41, 40, 38, 34, 30, 21, 11, or 1 feature observed.

### Extraction-aligned masking

The second experiment uses 17 deterministic scenarios. Each scenario masks a feature group or a combination of groups that follows the actual v0.2 observation-count rules.

The scenarios include:
- one-band periodicity unavailable;
- both periodicity groups unavailable;
- one band with 2–9 observations;
- one band with one observation;
- one band absent;
- both bands with 2–9 observations;
- mixed low-observation patterns across the two bands.

Each scenario is applied to all 59 complete rows. This gives 1,003 paired evaluations (17 × 59).

The report measures:

- absolute and signed changes in anomaly percentile;
- anomaly-score changes;
- Spearman rank correlation against the unmasked baseline;
- suppression and creation of flags at the existing 90th, 95th, and 99th reference-percentile thresholds.

The 90/95/99 values are existing OOD configuration thresholds. They are not calibrated probabilities. They are not new acceptance thresholds.

## Results

### MCAR masking

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

### Extraction-aligned feature-family masking

| Scenario | Features missing | Coverage | Median absolute shift | Median signed shift | Spearman rank correlation | Suppressed 90th flags | Suppressed 95th flags | Suppressed 99th flags |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| g periodicity unavailable | 6 | 85.7% | 8.00 | -8.00 | 0.928 | 14.3% | 33.3% | 50.0% |
| r periodicity unavailable | 6 | 85.7% | 5.33 | -5.33 | 0.975 | 14.3% | 33.3% | 50.0% |
| Both periodicity groups unavailable | 12 | 71.4% | 12.67 | -12.67 | 0.835 | 21.4% | 33.3% | 50.0% |
| g has 2–9 observations | 19 | 54.8% | 20.00 | -20.00 | 0.882 | 64.3% | 66.7% | 100.0% |
| r has 2–9 observations | 19 | 54.8% | 16.67 | -16.67 | 0.929 | 57.1% | 50.0% | 100.0% |
| g has one observation | 20 | 52.4% | 22.00 | -22.00 | 0.842 | 71.4% | 83.3% | 100.0% |
| r has one observation | 20 | 52.4% | 18.00 | -18.00 | 0.906 | 57.1% | 66.7% | 100.0% |
| g band absent | 23 | 45.2% | 24.67 | -24.67 | 0.796 | 78.6% | 100.0% | 100.0% |
| r band absent | 23 | 45.2% | 20.00 | -20.00 | 0.866 | 85.7% | 83.3% | 100.0% |
| Both bands have 2–9 observations | 38 | 9.5% | 64.67 | -64.67 | 0.553 | 100.0% | 100.0% | 100.0% |
| Both bands have one observation | 40 | 4.8% | 70.67 | -70.67 | 0.381 | 100.0% | 100.0% | 100.0% |
| g has 2–9; r has 10–29 | 25 | 40.5% | 28.00 | -28.00 | 0.805 | 71.4% | 66.7% | 100.0% |
| r has 2–9; g has 10–29 | 25 | 40.5% | 30.67 | -30.67 | 0.803 | 71.4% | 66.7% | 100.0% |
| g has one; r has 10–29 | 26 | 38.1% | 32.00 | -32.00 | 0.762 | 71.4% | 83.3% | 100.0% |
| r has one; g has 10–29 | 26 | 38.1% | 32.67 | -32.67 | 0.797 | 71.4% | 66.7% | 100.0% |
| g absent; r has 10–29 | 29 | 31.0% | 34.67 | -34.67 | 0.731 | 78.6% | 100.0% | 100.0% |
| r absent; g has 10–29 | 29 | 31.0% | 34.67 | -34.67 | 0.786 | 85.7% | 100.0% | 100.0% |

No new anomaly flags were created in these 17 scenarios. The existing baseline flags were either retained or suppressed.

The baseline subset contains 14 objects above the 90th percentile, 6 above the 95th percentile, and 2 above the 99th percentile. The 99th-percentile suppression rates therefore have a small denominator.

### Natural missingness association

On the 150 fitted reference objects:

- Complete rows have a median OOD percentile of 71.33.
- Partial rows have a median OOD percentile of 34.67.
- Missing feature count and OOD percentile have a Spearman correlation of -0.581.

This is a descriptive association. It is confounded by object identity and feature-pattern differences. It is not a causal estimate.

## Main findings

1. Missing features usually reduce the anomaly score and percentile.
2. This effect can hide an object that was flagged with complete data.
3. The effect is present under random MCAR masks and under extraction-aligned masks.
4. The 150-object dataset has no unexplained missing-feature pattern. All 91 partial rows match the extraction eligibility rules.
5. The eight rows with only four features are not random failures. They have 2–9 valid observations in both bands.
6. When both bands have 2–9 observations, all baseline flags at the 90th, 95th, and 99th percentiles are suppressed in the paired experiment.
7. Rank stability alone is not enough to trust a threshold decision. A rank correlation can remain moderate while the absolute percentile moves down.

The suppression rate is calculated only among evaluations that were flagged at the same threshold before masking. It is not the percentage of all rows.

## Limitations

- The paired experiments use 59 complete rows from a 150-object reference dataset.
- The model was reconstructed from the frozen matrix and configuration. The persisted production artifact was not loaded or compared byte-for-byte.
- Reference scores are in-sample.
- MCAR masking does not reproduce every correlated survey failure.
- Extraction-aligned masks reproduce the v0.2 feature eligibility rules. They do not represent every possible source of distribution shift.
- The experiment has no independent astrophysical OOD labels.
- The ALeRCE labels are not independent ground truth.
- The results do not establish OOD precision, recall, calibration, or population-level performance.

## Decision

**Do not use a fixed coverage threshold from this experiment. Do not suppress OOD scores based on an arbitrary rule.**

The evidence shows that missingness can suppress anomaly flags. The current per-row coverage and OOD evaluation-state fields are therefore important.

Keep these states distinct:

- `evaluated_complete_features`
- `evaluated_with_missing_features`
- `evaluated_adequacy_unreported`
- `not_available`

A partial row must not be presented as equivalent to a complete-feature OOD evaluation.

## Required next work

1. Obtain the exact production OOD artifact if it becomes available. Compare its reference scores with the reconstructed model. Do not substitute a lab-smoke artifact.
2. Evaluate with an independent labeled ID/OOD population. Do not use ALeRCE reference labels as ground truth.
3. Assess live and survey-specific missingness patterns. Keep them separate from the frozen historical reference.
4. Only then define and version an OOD eligibility policy. Add regression tests and a fail-closed scientific gate for that policy.

Until these steps pass, OOD eligibility remains a scientific validation blocker. This report does not change the frozen model, features, class order, or v0.2.0 baseline.
