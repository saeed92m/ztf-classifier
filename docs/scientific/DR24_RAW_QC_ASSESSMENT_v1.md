# DR24 raw-preserving QC assessment

## Status

Policy: `ztf-dr24-raw-qc-diagnostic-v1`

Status: `DIAGNOSTIC_NOT_PRODUCTION_APPROVED`

This policy reports quality indicators. It does not delete or modify raw DR24 epochs. It does not define the model-input selection policy.

## Rules

- **Catalog likely usable:** `catflags` is a non-negative integer and bit 15 (32768) is not set.
- **Strict clean:** `catflags == 0`.
- **Photometry valid:** `hmjd`, `mag`, and `magerr` are finite numbers, and `magerr >= 0`.
- **Provisional analysis candidate:** catalog-likely-usable AND photometry-valid. This is a diagnostic flag only.

The policy keeps these dimensions separate. For example, an epoch with `catflags=1` is likely usable under the bit-15 rule, but it is not strictly clean. The UI and API must not collapse these two states into one Boolean.

## Raw-data guarantees

- Epoch order is unchanged.
- Epoch values are unchanged.
- Missing values remain missing in the raw record.
- No epoch is filtered from the raw response.
- No color correction is applied.
- HMJD is not relabeled as MJD.
- No feature generation or model inference is performed.

## Source basis

- [ZTF DR24 release notes](https://irsa.ipac.caltech.edu/data/ZTF/docs/releases/dr24/ztf_release_notes_dr24.pdf), section 13.6.
- [IRSA DR24 HATS tutorial](https://caltech-ipac.github.io/irsa-tutorials/ztf-lightcurves/).

The IRSA tutorial demonstrates `catflags == 0` for a strict clean-epoch plot. The DR24 explanatory documentation describes bit 15 (32768) as cloud/moon-related and says values below 32768 are likely usable. Negative `magerr` values are invalid.

## Limitations and next validation

This diagnostic policy is not a scientific acceptance decision. Before model use, the project must validate the policy against independently identified sources, preserve the raw rows, define how each flag affects each feature, and test the impact on temporal and external validation. Calibration uncertainty and source-color uncertainty also remain separate from `magerr`.
