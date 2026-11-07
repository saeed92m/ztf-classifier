# DR24 HATS and Zubercal source-product contract v0.1

**Status:** Proposed; requires confirmation against the approved Park deliverable  
**Issue:** [#253](https://github.com/saeed92m/ztf-classifier/issues/253)  
**Baseline:** software v1.0.1; scientific baseline v0.2.0 (immutable)

## 1. Problem

The current DR24 adapter reads the IRSA ZTF DR24 Lightcurves HATS collection:

`s3://ipac-irsa-ztf/ztf/enhanced/dr24/lc/hats`

The project dossier and presentation also refer to Zubercal/recalibrated photometry. These are distinct data products. The implementation must not label HATS native photometry as Zubercal.

## 2. Verified source facts

1. IRSA's DR24 HATS tutorial identifies separate HATS collections for DR24 Lightcurves and the Objects Table.
2. The DR24 Lightcurves HATS collection contains one row per ZTF OID and nested epoch data with `hmjd`, `mag`, `magerr`, `clrcoeff`, and `catflags`.
3. IRSA describes Zubercal separately as a bulk download of recalibrated PSF photometry from ZTF science images.
4. ZTF OIDs are defined per filter, field, and quadrant. One astrophysical source can therefore map to multiple OIDs.
5. The HATS tutorial demonstrates indexed lookup by OID and `catflags == 0` for strict clean-epoch plotting.

## 3. Proposed product split

### Track A — DR24 HATS (primary raw lightcurve adapter)

Use the HATS collection for bounded, indexed native-lightcurve acquisition and reproducible raw-data exploration. Preserve raw epoch values and source provenance. Keep its time and photometry semantics explicit.

### Track B — Zubercal (separate calibration-comparison adapter)

Treat Zubercal as a separate product and adapter. Do not merge it into the HATS record schema without an explicit mapping and provenance contract. Evaluate it as an independent recalibration/comparison source. If the Park deliverable requires Zubercal-derived lightcurves as the primary product, implement and validate a dedicated reconstruction path from the relevant per-exposure PSF-photometry product.

## 4. Acceptance decision required

The current source evidence does not establish that DR24 HATS is an equivalent substitute for the Zubercal output named in the project dossier.

Before the final Park acceptance baseline is frozen, confirm one of these contractual interpretations:

- **Option A:** DR24 HATS is accepted as the primary raw time-series product; Zubercal is an optional comparison stream.
- **Option B:** Zubercal is mandatory for the primary science workflow; a dedicated Zubercal adapter and time-series reconstruction are required.
- **Option C:** both products are required and must be compared using a frozen source/version and photometric validation protocol.

Until that decision is recorded, the implementation must expose product identity and must not claim that the Zubercal deliverable is complete.

## 5. Non-negotiable scientific constraints

- Do not change the frozen v0.2.0 baseline or its 42-feature schema.
- Do not feed DR24 HATS or Zubercal values to the frozen model without an independently validated feature mapping and parity evidence.
- Do not infer astrophysical identity from OID equality or coordinate proximity alone.
- Preserve source-native values, source release, schema, query, hashes, and calibration semantics.
- Treat photometric calibration uncertainty separately from per-epoch `magerr`.

## 6. References

- [IRSA DR24 HATS Lightcurves tutorial](https://caltech-ipac.github.io/irsa-tutorials/ztf-lightcurves/)
- [IRSA ZTF data products](https://irsa.ipac.caltech.edu/Missions/ztf.html)
- [ZTF DR24 release notes](https://irsa.ipac.caltech.edu/data/ZTF/docs/releases/dr24/ztf_release_notes_dr24.pdf)
