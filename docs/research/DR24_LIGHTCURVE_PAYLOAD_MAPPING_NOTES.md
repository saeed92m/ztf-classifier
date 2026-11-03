# ZTF DR24 Lightcurve Payload Mapping Notes

**Status:** source-derived engineering notes; not an approved production normalization contract  
**Date:** 2026-11-03  
**Related work:** [Issue #253](https://github.com/saeed92m/ztf-classifier/issues/253), [PR #246](https://github.com/saeed92m/ztf-classifier/pull/246), [PR #255](https://github.com/saeed92m/ztf-classifier/pull/255)

## 1. Confirmed source structure

The official IRSA DR24 HATS tutorial describes the Lightcurves catalog as one row per ZTF object. The nested `lightcurve` value stores a time-series table with:

| Field | Meaning | Engineering handling |
|---|---|---|
| `hmjd` | Heliocentric-based Modified Julian Date, in days | Preserve as HMJD. Do not rename to MJD. |
| `mag` | Calibrated AB magnitude for a source with g-r = 0 | Preserve as source magnitude. Do not assume it equals ALeRCE corrected PSF magnitude. |
| `magerr` | 1-sigma magnitude uncertainty | Preserve separately. Source documentation says this excludes zeropoint uncertainty and possible systematics relative to external catalogs. |
| `clrcoeff` | Linear photometric color coefficient | Preserve separately. A color correction requires an explicit, defensible AB g-r value and a versioned formula. |
| `catflags` | Bit-encoded photometric/image quality flags | Preserve the raw integer. Apply only a documented, versioned quality policy. |

The HATS row also carries object-level metadata. The official tutorial lists `objectid`, `filterid`, `fieldid`, `rcid`, `objra`, `objdec`, `nepochs`, and the nested `lightcurve` value. The `objectid` index supports targeted lookup.

## 2. Identifier and grouping boundary

The official IRSA tutorial states that ZTF object IDs are defined per (filter, field, quadrant). A single astrophysical source can therefore map to multiple OIDs. A source can have up to three filter-level OIDs, and field/quadrant boundaries can create additional OIDs.

Consequences:

- An OID is a survey-record identifier, not a globally unique astrophysical identity.
- Never concatenate or merge OIDs by positional proximity alone.
- Preserve `objectid`, `filterid`, `fieldid`, and `rcid` on every acquired row.
- Any cross-OID source group needs a separate versioned association contract, evidence, and regression tests.
- Do not use the 5-arcsecond BTS recovery radius as an identity rule.

## 3. Time semantics

The DR24 release notes define HMJD as the heliocentric-based modified Julian date derived from HJD - 2400000.5. It corresponds to the middle of the exposure and the approximate object position.

The current canonical feature pipeline requires a column named `mjd`. An HMJD value is not an MJD value. A direct rename would misstate the time scale. The probe therefore retains HMJD and does not feed the values into the v0.2.0 feature pipeline.

Before a production adapter can supply the canonical time field, the project must select and validate one of these approaches:

1. Extend the source-neutral observation contract to represent time scale explicitly and adapt downstream feature calculations without changing the frozen v0.2.0 feature definition; or
2. Convert HMJD to the required time basis using documented coordinates and a validated algorithm, with error bounds and regression fixtures.

Do not choose an approach from convenience alone. Test the impact on baseline days, period estimates, cutoff semantics, and reproducibility.

## 4. Photometry semantics

The DR24 magnitude is calibrated for a source with g-r = 0 in the AB system. The `clrcoeff` field carries a linear color term. The release notes also state that `magerr` excludes the usually small zeropoint uncertainty and possible systematics relative to external catalogs.

The current ALeRCE normalizer selects corrected PSF magnitude/error when available and otherwise uses raw PSF magnitude/error. Those fields do not have an established one-to-one mapping to DR24 `mag` and `magerr`.

Required before model use:

- Define whether the application stores native DR24 calibrated magnitude or computes a color-adjusted value.
- Define the required color source, uncertainty, and missing-color behavior.
- Preserve native values and the applied correction separately.
- Quantify the photometric-system difference against a controlled, object-matched sample.
- Do not silently substitute ALeRCE values or change the frozen feature schema.

## 5. Quality flags

The official tutorial demonstrates `catflags == 0` to retain clean epochs. The DR24 release notes identify bit 15 (decimal 32768) as a cloud/moon-affected flag and describe `catflags` as a bit field.

The tutorial example is a source recommendation, not yet the project's approved production policy. The adapter must preserve raw flags and report exclusions by flag value/bit. A future policy must define whether it requires all flags to be zero or applies a documented bit mask. It must also report the retained and excluded epoch counts per OID and filter.

## 6. Current probe scope

PR #255 adds a manual-only, indexed lookup for at most five OIDs. It records:

- Requested, returned, and missing OIDs.
- Available catalog columns and their column-name hash.
- Object/filter/field/readout-channel metadata.
- Nested payload column names and dtypes.
- Payload row count and comparison with `nepochs`.
- HMJD range and finite-value counts.
- Magnitude/error finite-value counts.
- Raw `catflags` distribution and count with `catflags == 0`.
- Canonical payload hash and output hashes.

The probe does not normalize data, group OIDs, select quality policy, infer physical identity, call the feature engine, or run model inference. It is an evidence collection step only.

## 7. Exit conditions for the next adapter stage

Do not implement or enable a production DR24 observation backend until all items below have evidence:

1. A successful bounded payload probe with retained artifact and hashes.
2. Confirmation of the returned nested payload representation and actual dtypes.
3. Explicit time-scale decision and regression fixtures.
4. Explicit magnitude/color policy and controlled comparison with the existing ALeRCE path.
5. Explicit quality-flag policy and per-flag exclusion diagnostics.
6. Explicit object/filter/field/quadrant grouping policy, separate from OID acquisition.
7. Versioned request/result/provenance contracts and deterministic fixture tests.
8. No silent fallback between DR24 and ALeRCE.
9. An API and Workbench end-to-end run manifest that identifies the actual source.

## 8. Official references

- [IRSA: Access ZTF DR24 Light Curves from HATS Catalog](https://caltech-ipac.github.io/irsa-tutorials/ztf-lightcurves/) — HATS schema, nested payload, indexed OID lookup, clean-epoch example, and per-filter/field/quadrant identity behavior.
- [IRSA: ZTF DR24 Release Notes](https://irsa.ipac.caltech.edu/data/ZTF/docs/releases/dr24/ztf_release_notes_dr24.pdf) — HMJD, magnitude, magnitude uncertainty, color coefficient, and quality-flag semantics.
- [IRSA: Cloud Data Access](https://irsa.ipac.caltech.edu/cloud_access/) — official public DR24 HATS S3 catalog locations.

These notes record source documentation. They do not establish a completed live retrieval or scientific validation.
