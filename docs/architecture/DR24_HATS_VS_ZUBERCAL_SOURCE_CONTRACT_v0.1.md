# DR24 HATS and Zubercal source-product contract v0.1

**Status:** Proposed architecture; Park primary-product acceptance requires confirmation  
**Issue:** [#253](https://github.com/saeed92m/ztf-classifier/issues/253)  
**Baseline:** software v1.0.1; scientific baseline v0.2.0 (immutable)

## 1. Problem

The current DR24 adapter reads the IRSA ZTF DR24 Lightcurves HATS collection:

`s3://ipac-irsa-ztf/ztf/enhanced/dr24/lc/hats`

The project dossier and presentation also refer to Zubercal/recalibrated photometry. These are distinct data products. The implementation must not label HATS native photometry as Zubercal.

## 2. Verified source facts

### DR24 Lightcurves HATS

- One row per ZTF OID, with nested epoch arrays.
- Epoch columns include `hmjd`, `mag`, `magerr`, `clrcoeff`, and `catflags`.
- OIDs are defined per filter, field and quadrant. They are not canonical astrophysical source IDs.
- DR24 native magnitudes assume AB color g-r=0. Color correction requires source color and the epoch color coefficient.
- `HMJD` is heliocentric time (HJD - 2400000.5); it is not the same time scale as Zubercal MJD(TDB).

### Zubercal DR20

- IRSA lists Zubercal separately as recalibrated PSF photometry.
- The available LSDB HATS endpoint is `https://data.lsdb.io/hats/ztf_dr20/zubercal/`.
- The catalog `objectid` is a PS1 object ID, not a ZTF OID.
- The catalog provides `mjd` in TDB, `mag`, `magerr`, `band`, `fieldid`, `rcidin`, `info`, and `flag`.
- The stored Zubercal `magerr` is an integer scaled by 10,000. A derived magnitude error requires division by 10,000. Preserve the stored value in provenance.
- Zubercal `flag` and `info` have their own definitions. They are not interchangeable with DR24 `catflags`.
- The bulk DR20 product is approximately 10 TB. The HATS endpoint may support bounded remote queries, but query cost and latency still require measurement.
- Zubercal matches ZTF detections to PS1 objects within a 1.2-arcsecond limit. Sources without a suitable PS1 match are not represented. This is a material limitation for transient discovery.

## 3. Recommended architecture

Use **both products as separate streams**.

### Track A — DR24 HATS (primary discovery and raw time-series stream)

Use HATS for broad ZTF lightcurve coverage, including objects without a suitable PS1 counterpart. Preserve native epoch values, OID metadata and source provenance. Keep the raw path independent of any Zubercal match.

### Track B — Zubercal DR20 (supplementary calibration stream)

Use Zubercal for objects with a valid PS1 association. Query it through the LSDB HATS service where bounded access is practical. Keep PS1 IDs, match distance, band, MJD(TDB), magnitude, scaled error, `flag` and `info` separate from DR24 fields.

A Zubercal match must be represented as a cross-reference with match method, radius, candidate count and ambiguity state. Do not equate PS1 `objectid` with ZTF OID. Do not discard DR24 sources that have no Zubercal counterpart.

## 4. Time and photometry contract

- Keep DR24 HMJD and Zubercal MJD(TDB) as separate source-native fields.
- Do not compare or merge epochs until a validated time conversion is implemented. A simple numeric offset is not sufficient.
- Keep DR24 native magnitudes and Zubercal PS1-calibrated magnitudes in separate fields.
- Preserve Zubercal raw `magerr`; derive physical magnitude error only through an explicit unit conversion.
- Keep DR24 `catflags` and Zubercal `flag`/`info` separate.
- Calibration uncertainty and PS1 matching uncertainty must not be hidden inside the per-epoch measurement error.
- No cross-source data may enter the frozen v0.2.0 model until feature parity and leakage tests pass.

## 5. Acceptance decision

The recommended technical option is **Option C**: DR24 HATS is the primary discovery stream and Zubercal is a supplementary calibration stream.

The Park acceptance authority must still confirm that this interpretation satisfies the approved dossier. If Zubercal is mandatory as the only primary stream, the project must document that PS1-unmatched transients are outside its coverage. That restriction is not acceptable for the platform's full transient-discovery objective.

## 6. Non-negotiable scientific constraints

- Do not change the frozen v0.2.0 baseline or its 42-feature schema.
- Do not feed DR24 HATS or Zubercal values to the frozen model without an independently validated feature mapping and parity evidence.
- Do not infer astrophysical identity from OID equality or coordinate proximity alone.
- Preserve source release, schema, query, hashes, units and calibration semantics.
- Keep source-native records immutable.

## 7. References

- [IRSA DR24 HATS Lightcurves tutorial](https://caltech-ipac.github.io/irsa-tutorials/ztf-lightcurves/)
- [IRSA ZTF data products](https://irsa.ipac.caltech.edu/Missions/ztf.html)
- [ZTF DR24 release notes](https://irsa.ipac.caltech.edu/data/ZTF/docs/releases/dr24/ztf_release_notes_dr24.pdf)
- [Zubercal overview](https://irsa.ipac.caltech.edu/data/ZTF/zubercal/overview.pdf)
- [LSDB Zubercal/PS1 tutorial](https://docs.lsdb.io/en/stable/tutorials/pre_executed/zubercal-ps1-snad.html)
- [Zubercal DR20 HATS service](https://data.lsdb.io/hats/ztf_dr20/zubercal/)


## 8. Bounded live Zubercal DR20 probe

A bounded remote cone query was executed through the LSDB HATS endpoint.

Evidence:
- Workflow: [42350687356](https://github.com/saeed92m/ztf-classifier/actions/runs/42350687356)
- Artifact: [zubercal-dr20-bounded-probe](https://github.com/saeed92m/ztf-classifier/actions/runs/42350687356/artifacts/13564968687)
- ZTF OID: `264114400013085`
- DR24 center: RA 142.59396362304688 deg, Dec -21.453134536743164 deg
- Search radius: 1.2 arcsec
- Returned Zubercal rows: 123
- Bands: g and r
- Candidate PS1 IDs: `82251425938786635`, `82251425941826616`
- Maximum returned detection separation: 1.1841390371676082 arcsec
- Match state: `AMBIGUOUS_MULTIPLE_PS1_IDS`
- Canonical payload SHA-256: `4d59d7f90d8ced26a97b171d14a1271cf5adf04329b502df219b0fb531c74d4f`

This probe verifies remote HATS access and the returned schema for one bounded query. It does **not** establish which PS1 ID is the correct astrophysical counterpart. The adapter must preserve both candidate IDs and report ambiguity. It must not select one candidate automatically.

The probe also confirms that a 1.2-arcsecond cone can return more than one PS1 object ID for a single ZTF OID. Cross-match ambiguity is therefore a real observed condition, not only a theoretical risk.
