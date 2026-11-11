# ZTF Classifier — Scientific Methodology

**Status snapshot:** 2026-11-12  
**Current repository main at review:** `f681408fae8d8062dd72ff74791872c1590f6ee8`

## Scope

The platform analyzes public ZTF observations with explicit source provenance, schema, time, photometric, identity, leakage, and evidence boundaries. Raw acquisition, normalization, quality control, feature generation, inference, calibration, OOD, anomaly analysis, and scientific confirmation are distinct stages.

## Immutable baseline

The v0.2.0 benchmark contains 150 objects across 15 ALeRCE reference classes, 42 frozen features, and the XGBoost `baseline_v0.2` model. ALeRCE labels are benchmark/reference labels, not independent astrophysical ground truth. The historical cutoff is MJD 59447.224132. The class order and feature contract must not change in this baseline.

The software release v1.0.1 is separate from the scientific baseline version.

## Evidence types

Benchmark performance, external catalogue agreement, source-backed reproduction, calibration, conformal prediction, OOD behavior, scientific anomaly analysis, data adequacy, expert review, and human annotation are distinct evidence types.

A green CI workflow establishes only the behavior of the jobs that ran. A skipped source-backed job is not PASS. Engineering tests do not establish scientific validity.

## Data-source semantics

DR24 HATS and Zubercal DR20 are distinct products. Preserve their source-native identifiers, time scales, photometry, units, error fields, flags, and provenance. Do not treat ZTF OID as canonical astrophysical identity. Do not merge DR24 HMJD and Zubercal MJD(TDB) without a validated transformation.

Do not connect DR24 observations to the frozen 42-feature model until the time, photometry, identity, QC, feature mapping, and leakage contracts pass independent validation.

## Diagnostic semantics

Classification uncertainty, calibration, conformal prediction, OOD, data adequacy, and scientific anomaly are separate concepts. A high OOD score is not automatically an astrophysical anomaly. Missing data is UNKNOWN unless observed evidence supports FAIL.

## CPVS historical membership investigation

The published reference membership is 730,184 objects from a 781,602-object Table 2 parent. The official Table 4 membership is cross-walked to the authoritative Table 2 `Seq` identifiers.

Latest retained historical set comparison reviewed on 2026-11-11:

| Set | Definition | Count |
|---|---|---:|
| P | Published Table 4 membership mapped to Table 2 Seq | 730,184 |
| C | Retained historical candidate set, not freshly re-derived on current main | 741,786 |
| C ∩ P | Shared members | 730,184 |
| C − P | Candidate-only | 11,602 |
| P − C | Published-only | 0 |
| F | Table 2 rows with finite positive gmag, rmag, Per-g, Per-r | 730,239 |
| C ∩ F | Diagnostic intersection | 730,184 |
| F − C | Four-field-positive controls | 55 |

The four-field predicate yields an exact empirical intersection on the retained historical identifiers. It is not established as the publisher's documented selection rule. The paper and Table 4 ReadMe do not explicitly require all four fields to be positive. The diagnostic must not become a production selector without primary-source or author evidence.

The 55-control raw-photometry audit was corrected on 2026-11-11. Missing archive rows are UNKNOWN, not SNR FAIL:

- g band: PASS 1, FAIL 0, UNKNOWN 54.
- r band: PASS 51, FAIL 0, UNKNOWN 4.
- joint g/r: PASS 0, FAIL 0, UNKNOWN 55.

A separate deterministic 1,000-object sample from the complete 51,418 Table 2 nonmember population has been selected. It contains 1,000 unique IDs and zero published members. The raw g/r archive coverage and SNR state for these IDs remain UNKNOWN because the source archives were not included in the evidence package.

The 11,602 residuals remain unexplained. The retained candidate set must be freshly derived on the current code with hash-pinned source inputs. Existing fixed 100-object, stratified 1,000-object, and separate nonmember-control samples must remain distinct. Run raw g/r coverage, finite-SNR, and full-versus-batch object-level checks. Report disagreement only relative to published membership; do not call the reference astrophysical ground truth.

Older workflow records report 11,604 extras. That value belongs to an earlier revision/input state. Do not mix it with the 11,602 retained Seq-based comparison.

Related trackers: [Issue #170](https://github.com/saeed92m/ztf-classifier/issues/170), [Issue #180](https://github.com/saeed92m/ztf-classifier/issues/180), and bounded archive-identity investigation [PR #265](https://github.com/saeed92m/ztf-classifier/pull/265).

**Disposition:** OPEN / UNRESOLVED / DEFERRED RESEARCH. CPVS exact reproduction is not a DR24 Park MVP release gate. Do not change thresholds, membership, production selector, model, feature set, class order, or v0.2.0 baseline to force count equality.

## Reproducibility

Every scientific claim must identify source release/version, retrieval context, exact object IDs, raw and derived hashes where practical, schema, taxonomy/class order, feature definition, filters, time cutoffs, random seeds, code commit, dependency environment, model/calibrator identity, output hashes, warnings, errors, and validation status. A missing input or skipped gate must remain explicit.
