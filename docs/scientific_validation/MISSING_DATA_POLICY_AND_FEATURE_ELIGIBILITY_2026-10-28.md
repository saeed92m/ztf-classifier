# Missing-data and feature-eligibility policy — 2026-10-28

## Scope and decision

This audit is additive and does not modify the frozen v0.2.0 model, 42-feature order, training data, class order, or historical cutoff. The goal is to distinguish (1) an unavailable measurement, (2) a feature that cannot be estimated from the available observations, and (3) a scientifically invalid object. These are not equivalent states.

**Approved policy:** do not fabricate unavailable source measurements. Do not impute in the source/feature-extraction layer. Keep a source object available for analyses whose requirements it satisfies; mark a feature unavailable when its prerequisites are not met; reject only the specific analysis that requires unavailable information. Any model-level imputation must remain an explicitly versioned, training-fitted preprocessing step with provenance and leakage controls.

## Repository audit (read-only baseline review)

The current native v0.2 pipeline:
- filters each band through prepare_band_lightcurve, which removes rows with non-finite MJD/magnitude/error and non-positive error;
- requires at least 10 valid observations for basic per-band features;
- requires at least 30 valid observations for Lomb–Scargle features;
- emits NaN for features whose declared eligibility threshold is not met;
- computes cross-band color features when both bands have at least one valid observation;
- computes cross-band sample-standard-deviation ratios in the same function, where ddof=1 makes the ratio undefined for a band with only one valid observation.

The last point is a concrete diagnostics gap: color is mathematically defined from one valid magnitude per band, but a sample-standard-deviation-based variability ratio needs at least two observations. The frozen output may retain NaN for that ratio; the application should explain why instead of presenting an undifferentiated missing value. This change does not alter the feature values or thresholds.

The existing validate_v0_2_feature_vector checks feature names/order but does not itself validate the numerical finiteness of each value. That is consistent with the pipeline's intentional use of NaN for ineligible features, but callers must not interpret schema validation as proof that all features are computable.

## Implemented diagnostic helper

diagnose_v0_2_feature_eligibility provides a JSON-safe, non-mutating report with:
- raw and valid observation counts per band;
- rejected-row counts under the existing canonical validity function;
- basic-feature (>=10), periodicity-feature (>=30), and sample-standard-deviation (>=2) eligibility;
- cross-band color and per-band variability-ratio eligibility;
- conservative reasons for non-finite feature values, without imputing or changing them.

The helper is opt-in and is not yet wired into every API/UI response. That integration is a separate compatibility-reviewed task. The report does not apply a new quality cut, declare an object invalid, or alter the frozen v0.2 feature vector.

## Validation scope

The added tests exercise:
1. the difference between color eligibility and sample-standard-deviation eligibility;
2. the basic/periodicity minimum-observation thresholds;
3. invalid-row handling through the canonical preprocessing function;
4. JSON strict serialization and input immutability;
5. fail-closed behavior for missing required input columns.

These tests are regression coverage for the diagnostic helper, not a claim of a full scientific benchmark. They must pass on the PR's current head before this work is accepted.

## CPVS remains a separate reference-reproduction track

The current CPVS comparison is still a reference-membership result, not independent astrophysical truth. Current source-backed counts are 781,602 parent objects, 741,786 candidates, 730,184 published members, 11,602 candidate-only and zero published-only. The four-field diagnostic condition matches the published set on the pinned artifact, but is not proven to be the historical publisher's exact rule. No production CPVS selection rule is changed by this policy work.

## External method references

- ZTF DR24 documentation recommends using catflags to filter epochs affected by image/calibration/source-quality issues; a finite positive magnitude uncertainty alone is not a complete quality assessment: https://irsa.ipac.caltech.edu/data/ZTF/docs/releases/dr24/ztf_release_notes_dr24.pdf
- Chan et al. (2022) describe their specific CPVS sample as having at least one 2.5-sigma g-band and 3-sigma r-band detection, then phase-folding both bands with the common period: https://doi.org/10.3847/1538-4357/ac69d4
- Pruzhinskaya et al. / related anomaly-detection work notes that engineered features may be undefined or unreliable for a substantial fraction of light curves and motivates representation approaches that stay closer to observations: https://academic.oup.com/mnras/article/508/4/5734/6368852

## Explicit limitations

- This audit does not prove why each CPVS Table 2 field is zero.
- It does not establish the publisher's preprocessing code.
- It does not claim that a finite-SNR check alone is a complete ZTF quality policy.
- It does not change production selection, training, or release acceptance criteria.
