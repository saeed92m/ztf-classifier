# Data Adequacy and OOD Evaluation Contract

**Status:** Descriptive coverage diagnostic implemented; production OOD eligibility policy pending validation  
**Date:** 2026-11-09  
**Scope:** Production inference, persisted OOD diagnostics, API/CLI/batch/job outputs  
**Baseline impact:** None. This document does not change the v0.2.0 classifier, its 42-feature schema, model artifact, class order, or acceptance criteria.

## 1. Decision

Data adequacy and out-of-distribution (OOD) detection are separate concepts and MUST have separate outputs.

- **Data adequacy** describes whether the supplied observations support the requested feature calculations and downstream evaluation.
- **OOD** describes how the model's feature vector compares with a fitted reference distribution.
- A low OOD anomaly score MUST NOT be interpreted as evidence that the input data are complete or scientifically adequate.
- A classifier prediction MUST NOT be silently removed because an optional diagnostic cannot be evaluated.
- OOD scores MUST NOT be presented as calibrated probabilities.

No production coverage threshold is approved by this decision record. A threshold must not be selected from the 150-object benchmark alone, from a correlation with missingness, or from a desired CI outcome.

## 2. Verified implementation facts on the inspected main revision

The following facts were read from the repository source at the revision inspected on 2026-11-09:

1. `features/extraction.py` records `n_valid_total`, `n_g`, `n_r`, `has_g`, `has_r`, and `has_both_bands`.
2. Basic per-band features are generated only when that band's prepared light curve has at least 10 rows.
3. Lomb–Scargle and phase-morphology extraction is entered only when a band has at least 30 rows. The Lomb–Scargle implementation itself requires at least 10 valid rows.
4. Cross-band features are generated only when both bands have at least one row.
5. `XGBoostInferenceEngine.prepare_features` selects the frozen 42-feature schema, converts non-numeric and infinite values to missing values, and rejects a row only when all 42 features are missing.
6. `ProductionInferenceService.predict` passes every remaining row to the persisted OOD model.
7. `OODProductionModel` uses median imputation, robust scaling, and Isolation Forest. Its input validation checks the matrix globally; it does not enforce a per-row feature-coverage rule.
8. The OOD reference anomaly scores are calculated on the same data used to fit the persisted Isolation Forest. They are therefore in-sample reference scores.
9. The OOD percentile and rank are relative to the persisted reference scores. They are not calibrated anomaly probabilities.
10. The current `PredictionResult` carries one request-level `ood_status` and an optional row-aligned `OODResult`. It has no per-row data-adequacy result.
11. The API, CLI, batch, web, and job serializers expose different subsets of diagnostics. The job executor currently exposes only request-level diagnostic status.

These facts describe source behavior. They do not establish a scientifically valid minimum coverage threshold.

## 3. Failure mode

A row with one finite feature and 41 missing features can pass the current global OOD input validation. Median imputation can then create a complete transformed row and Isolation Forest can return a numerical score.

That score is a mathematical output of the current preprocessing and estimator. It is not evidence that the original row contained enough observations or information for a meaningful scientific comparison.

The current behavior can therefore produce a misleading result: a numerical OOD score without an explicit statement about input adequacy.

## 4. Required result model

The target contract should represent these dimensions independently.

### 4.1 Per-object data adequacy

A future `DataAdequacyResult` should be row-aligned with classification results and contain, at minimum:

- `observed_feature_count`
- `missing_feature_count`
- `coverage_fraction`
- `missing_feature_names` or a stable compact representation
- `status`
- `reason_codes`
- `policy_version`

The status vocabulary should distinguish at least:

- `complete`: all required model features are finite.
- `partial`: some model features are missing.
- `insufficient`: an approved, versioned adequacy policy says the row does not support the requested evaluation.
- `not_assessed`: the adequacy assessment could not be made.

The exact status vocabulary and required fields must be finalized with the serialization contract before implementation.

### 4.2 Per-object OOD evaluation state

OOD evaluation needs a row-level state. At minimum:

- `evaluated`
- `not_evaluated_insufficient_data`
- `not_available`

A row that is not evaluated must not receive fabricated score, percentile, rank, label, or anomaly flags. Serialized values should be null for unavailable numerical fields, with the reason carried separately.

### 4.3 Request-level diagnostic availability

Keep the existing request-level `ood_status` for artifact capability and execution availability. Do not overload it with row-level adequacy.

A request can have an available OOD artifact while some individual rows are not eligible for evaluation.

## 5. Scientific policy: what must be established before gating OOD

A production eligibility threshold requires evidence beyond feature count.

The policy investigation must:

1. Identify all 42 frozen features and map each feature to its extraction family and band.
2. Identify the observation requirements and validity rules for each family.
3. Establish whether the production input contains sufficient provenance to distinguish:
   - feature not computable because the observation threshold was not met;
   - feature absent because its band was not observed;
   - feature missing because of malformed or invalid source data;
   - feature missing because of a pipeline or schema defect.
4. Reconstruct row-level feature coverage on the exact frozen reference dataset used to fit the OOD artifact.
5. Compare the distribution of coverage in reference data with the distribution in prospective production inputs.
6. Evaluate the effect of missingness on OOD scores using controlled masking experiments. Keep the original row, masked row, mask pattern, seed, and score differences.
7. Stratify the analysis by feature family, band, class label where available, and observation count. Treat benchmark labels as benchmark labels, not independent ground truth.
8. Define the target operating point and acceptable false rejection rate for OOD evaluation.
9. Version the policy and record the evidence, dataset hashes, commands, and reviewer decision.

A single global percentage may be inadequate if feature families have different scientific requirements. Do not assume that 50% coverage, 10/42 features, or any other convenient number is valid without evidence.

## 6. Required tests after policy approval

### Unit tests

- Complete feature row.
- Partially missing row.
- Row with one finite feature.
- Row with all features missing.
- Numeric strings, non-numeric values, positive infinity, and negative infinity.
- Stable reason codes and deterministic coverage counts.
- Input arrays are not mutated.
- Output arrays are immutable where the existing result contract requires immutability.

### Production inference tests

- Classification output is unchanged by the adequacy diagnostic.
- OOD is evaluated only for rows eligible under the approved policy.
- OOD is not evaluated for ineligible rows.
- Eligible-row OOD values map back to the correct original row positions.
- Mixed batches preserve sample order and count.
- No ineligible row receives a numerical OOD result.
- Existing deterministic OOD tests remain valid for rows that satisfy the approved policy.

### Serialization tests

- API response contains row-level adequacy and OOD evaluation state.
- CLI JSON has explicit null values for non-evaluated OOD fields.
- Batch Parquet preserves nullable OOD columns and row-level status.
- Job output exposes the same concepts for a single object.
- Web UI does not display a missing score as zero or as a normal result.
- Schema-version changes are explicit and documented.

### Scientific validation

- Run controlled masking experiments on the exact reference dataset.
- Report score shifts and eligibility changes by feature family and class.
- Test a fixed, reproducible sample from the full parent dataset when available.
- Do not use the same in-sample OOD scores as independent validation evidence.
- Do not claim calibrated OOD performance without an independent evaluation design.

## 7. Compatibility and migration

The current API response, CLI output, batch output, job payload, and result-store payload have independent schema contracts. Additive fields still require compatibility tests.

Before implementation, inspect and record the exact schema versions for every surface. Increment only the contracts whose serialized shape changes. Keep old consumers safe or document a breaking version change.

Do not change the frozen model artifact or its preprocessing state as part of this work. A future OOD model retraining or reference-set change is a separate scientific change with its own provenance and validation.

## 8. Current blockers

- The exact frozen 42-feature schema and feature-family mapping must be read from the binary schema artifact at the local validated checkout or a text export with a verified hash.
- The exact OOD reference training matrix is not available in the public source tree inspected here.
- No empirically validated per-row adequacy threshold has been established.
- The local benchmark audit previously reported missingness patterns, but those results must be re-run against the exact dataset and hash before they can support a production policy.
- The current GitHub Actions environment may skip integration tests when scientific artifacts are not present. A green run with those tests skipped is not scientific validation.

## 9. Implemented non-gating diagnostic

The current feature branch adds a descriptive `DataAdequacyResult` before OOD preprocessing. It reports, for each row:

- observed and missing counts across the 42 frozen features;
- coverage fraction;
- missing feature names;
- `complete` or `partial` status;
- a stable missing-feature reason code.

The diagnostic is computed from the numeric, finite-value mask before median imputation. It is attached to `PredictionResult` and serialized through API, CLI, batch Parquet, object-job payloads, and the web workbench. The API, CLI, batch, and job payload versions are incremented where their serialized contracts changed.

This diagnostic is descriptive only. It does not make a scientific eligibility decision. A one-feature row is explicitly labelled `partial`, but the current OOD model still produces a score for it. This behavior is deliberately visible and remains a production validation blocker until an evidence-based threshold is approved.

Do not implement a production OOD exclusion threshold until Sections 5 and 8 are resolved. Any non-gating diagnostic must not imply that a row is scientifically adequate merely because it has nonzero coverage.

## 10. Acceptance criteria

This work is complete only when:

- the 42-feature schema mapping is verified by hash;
- the adequacy policy has reproducible scientific evidence and a version;
- low-coverage rows cannot receive misleading OOD results under that policy;
- classification output remains unchanged;
- API, CLI, batch, job, and web outputs agree on row-level state;
- regression and scientific validation tests pass;
- skipped tests and artifact dependencies are reported;
- documentation records limitations and migration behavior.

Until then, OOD data adequacy remains an explicit scientific validation blocker.
