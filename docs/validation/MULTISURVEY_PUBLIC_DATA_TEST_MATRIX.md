# Public multi-survey data validation matrix

**Status:** test plan with one implemented source-format adapter; not a claim of multi-survey scientific validation. Large science data stays outside Git; commit only small fixtures and compact manifests.

## Execution states

- **Not started:** no adapter execution or fixture evidence recorded.
- **Format adapter implemented:** documented format parser plus unit tests; does not prove a live file was downloaded or scientific performance validated.
- **Import verified:** pinned real source file retrieved, hashed, parsed, and reconciled with source row/object accounting.
- **Analysis verified:** named source-appropriate analysis completed with deterministic output and checks.
- **Model scientifically validated:** independent, leakage-safe evaluation passes for a declared task/domain.

## Initial source matrix

| Source / project | Data type and format | First bounded experiment | Key risks | Current status |
|---|---|---|---|---|
| TESS Transients (MIT/MAST TICA-derived) | Public transient light curves, whitespace text, BTJD/TDB, counts/s and magnitudes | One documented light curve, flux and magnitude views; retain e_mag=99.9 upper-limit sentinel | Scattered-light systematics, host-galaxy flux, uncertain absolute calibration, upper limits | Format adapter and synthetic fixture tests added in PR #212; live retrieval and checksum reconciliation pending |
| TESS-GAIA Light Curve (TGLC) / TESS SPOC-like products | FITS light curves keyed by Gaia DR3 ID or TIC ID and sector | One FITS light curve plus metadata/sector, with explicit FITS column map | Crowding, sector gaps, cadence, pipeline differences, QUALITY semantics | Generic explicit-schema FITS reader and synthetic TESS-like tests added in PR #212; live file verification pending |
| ZTF DR public light curves / DR24 | Survey-specific light curves and catalog products | Pin a bounded sample and compare source row/object counts to current ZTF adapter | Band conventions, flags, grouping, historical cutoffs | Existing product track; inspect source-backed run per release |
| StarEmbed | ZTF light curves and prepared benchmark data | Reproduce small evaluation after object-level split/duplicate leakage is fixed | Duplicate IDs, train/test object overlap, domain mismatch | Blocked on issue #210 leakage-safe split and dataset audit |
| SNAD flare-classifier | ZTF DR17 flare catalogue and model pipeline | Inspect public catalogue schema; run small non-training catalogue analysis | Flare-specific labels; model not interchangeable with baseline | External comparator; adapter not started |
| SNAD ZTF Real/Bogus classifier | ZTF object features and ONNX model | Verify feature contract and small inference fixture only if compatible | Artifact-vs-real distinction, feature/training provenance, license | External comparator; adapter not started |
| SNAD ZTF anomaly detection (ZWAD) | ZTF DR3 feature matrices and object IDs | Run one bounded feature matrix with documented algorithms | Anomaly is not classification/OOD; human review | External analysis comparator; adapter not started |
| OGLE / AAVSO / ATLAS / ASAS-SN / Gaia variability | Light curves or catalog time series with distinct schemas | One pinned sample per source after format/license/schema is documented | Time scale, passband, units, limits, selection effects | Not started |

## Required record per real-data experiment

1. Source URL/API and product/version; access date; license/citation.
2. Exact file names, byte sizes, SHA-256 checksums and retrieval command.
3. Source schema/version and explicit column/unit/time mapping.
4. Input/output rows, unique objects, duplicate/missing/non-finite counts, and dropped-row accounting.
5. Named transformations and before/after row accounting.
6. Deterministic analysis command, environment versions and random seeds.
7. Output artifact checksums and compact result summary.
8. Failure modes, unsupported semantics, and distinct import, analysis, model-compatibility, and scientific-validation states.

## First execution sequence

1. Validate the TESS Transients parser against a pinned real file and compare its schema and row count with the raw download.
2. Add a TGLC FITS reader as a separate adapter, not as generic CSV.
3. Run a source-backed ZTF sample and a small ZWAD/flare-catalog comparison.
4. Fix StarEmbed object-level split/duplicate leakage before reporting benchmark scores.
5. Build a scientist-facing import → inspect → analyze → report path on the same canonical observation contract.

A source is not supported solely because a synthetic test passes. Import verification requires real-file provenance and reconciliation.
