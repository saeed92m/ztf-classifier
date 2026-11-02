# Independent ZTF Recovery Validation — BTS and StarEmbed

## Status

BTS-to-DR24 spatial pilot completed for a deterministic 100-object sample on 2026-11-02. The run produced measured positional-recovery and OID-multiplicity results; these are reported below. The pilot does not establish object-level precision, recall, or a validated association radius. The separate StarEmbed coordinate-recovery pilot has not yet run. The existing StarEmbed source-acquisition step passed in workflow run 36756251456, but its full 5-artifact package is not reprocessed by this BTS pilot.

CPVS is explicitly outside this workstream. Its open scientific question remains recorded separately; it is not a dependency for this experiment.

## Objective

Test whether an independent catalog object, represented by sky coordinates and an external identifier, maps to zero, one, or multiple ZTF DR24 object identifiers. The experiment must separate:

- an external astrophysical source;
- a catalog row or survey identifier;
- a ZTF DR24 object identifier (`oid`);
- a filter-specific/field-specific ZTF detection stream.

A larger number of ZTF OIDs is not automatically a false positive. The official IRSA DR24 tutorial states that ZTF objects are defined per filter, field, and quadrant. One astrophysical source can therefore map to up to three filter-specific ZTF objects, with further splits near field or quadrant boundaries.

## Independent sources and their roles

### A. StarEmbed ZTF_40k — variable-star classification and OOD

- Source: https://huggingface.co/datasets/StarEmbed/ZTF_40k
- Paper: https://doi.org/10.48550/arXiv.2510.06200
- License shown by the dataset publisher: MIT.
- Published dataset size: 42,585 rows, approximately 560 MB.
- Splits: train, validation, test, and anom.
- In-distribution taxonomy: EW, EA, RRab, RRc, RRd, RS CVn, LPV.
- The anom split contains disjoint classes.
- Source IDs are Catalina Surveys DR1 identifiers (`sourceid`), not ZTF DR24 `oid` values.
- Sky positions (`ra`, `dec`) are available.

Use this source to test classification/OOD behavior and to provide independent source IDs and coordinates for a spatial recovery test. Do not treat `sourceid` as a ZTF identifier. Do not treat the dataset's source labels as a universal taxonomy.

The repository already has a StarEmbed acquisition adapter. The scheduled scientific-validation run on 2026-11-02 reported `acquisition=ACQUIRED`. That confirms acquisition, not classifier performance or recovery accuracy.

### B. ZTF Bright Transient Survey (BTS) — transient recovery and classification

- Official survey page: https://www.ztf.caltech.edu/ztf-bts.html
- Sample explorer: https://sites.astro.caltech.edu/ztf/bts/explorer.php
- Explorer documentation: https://sites.astro.caltech.edu/ztf/bts/explorer_info.html

The BTS explorer provides ZTF 9-character IDs, TNS IDs, coordinates, and spectroscopic classifications. Its sample is updated every few hours. It is not complete for Galactic events or all non-transients. The source snapshot must therefore be acquired, hashed, timestamped, and treated as a time-bounded sample.

BTS is the preferred first transient benchmark because its published sample provides a direct ZTF name, a TNS identifier, coordinates, and a spectroscopic classification. The ZTF name is not assumed to be interchangeable with the DR24 numeric `oid`.

### C. ZTF DR24 Objects Table — recovery target

- Official release: https://www.ztf.caltech.edu/ztf-public-releases.html
- IRSA cloud access: https://irsawebops2.ipac.caltech.edu/cloud_access/index.html
- Official HATS tutorial: https://caltech-ipac.github.io/irsa-tutorials/ztf-lightcurves/

DR24 Objects Table HATS collection:
- Bucket: `ipac-irsa-ztf`
- Prefix: `ztf/enhanced/dr24/objects/hats`
- Object identifier: `oid`
- Coordinates: `ra`, `dec`
- Filter: `filtercode`

Use the official HATS collection for spatial recovery. Keep the source query, release, exact sample, query radius, software versions, returned OIDs, and hashes in the evidence package.

## Experimental protocol

### Phase 1 — contract and acquisition

1. Resolve and record an immutable StarEmbed dataset revision.
2. Acquire the BTS explorer CSV as a dated snapshot. Record the exact request URL, retrieval UTC time, HTTP metadata, row count, schema, and SHA-256.
3. Validate required columns and unique source identifiers.
4. Preserve raw source files. Never overwrite them with normalized files.

### Phase 2 — fixed pilot samples

Run two separate pilots:

- StarEmbed: deterministic 100-object sample, balanced across available source splits where possible.
- BTS recovery: deterministic 100-object sample from rows with valid ZTF ID, TNS ID, RA, and Dec. Do not require a classification label for spatial recovery. The initial sample contains 38 rows with BTS type `-`; these remain valid positional targets but are not labeled classification examples. The full 10,551-row snapshot contains 3,374 rows with type `-`.
- BTS classification: create a separate, deterministic, class-aware sample only from rows with a valid published type. Do not use `-` as a class label. Do not claim that the current spatial sample is class-balanced.

The BTS sample uses ascending SHA-256 of the external ZTF ID as its deterministic ordering; it does not use a random seed. Record the sorted sample IDs and sample SHA-256. Do not silently replace failed sample members.

### Phase 3 — spatial recovery

For every sampled source, query the official ZTF DR24 Objects Table by sky position with a 5-arcsecond outer radius. Recompute angular separations and report sensitivity at 1, 2, and 5 arcseconds. Keep all returned OIDs, coordinates, filters, and separations. Treat 1 arcsecond as a restrictive diagnostic, not an accepted radius. BTS transient coordinates can be offset from DR24 reference-object coordinates.

For BTS, coordinate offsets between the transient and its host or reference-image object can occur. A spatial match is therefore an association candidate, not proof of physical identity. Record this limitation.

### Phase 4 — identifier multiplicity analysis

For each external source, report:

- no ZTF OID found;
- exactly one OID found;
- multiple OIDs across different filters;
- multiple OIDs in the same filter;
- multiple OIDs with distinct field/quadrant provenance, where available;
- same-filter multiple OIDs that remain within one field/quadrant, where provenance is available;
- ambiguous spatial associations;
- nearest angular separation;
- sensitivity to the 1, 2, and 5 arcsecond radii.

Do not call every OID after the first an extra object. Report OID multiplicity separately from astrophysical-source multiplicity.

### Phase 5 — scale-up

Only after the pilot passes data-integrity and matching checks:

- increase to a fixed 1,000-object sample;
- then evaluate the full available source sample if runtime and query load are reasonable.

Do not run a full-catalog cross-match until the pilot establishes query cost and match behavior.

## BTS pilot results — 2026-11-02

The official BTS CSV endpoint returned HTTP 200 and 10,551 rows. The raw response SHA-256 is `af2362275074ff4b6c70523b9db6f2d5991af16fdd8d76ed47520948eb788e82`. The deterministic 100-row sample SHA-256 is `044dc0b3b6a3cf127f50099a7a3f76ae3423df62807564f0c365efb5007bd9a4`.

The spatial query used the official IRSA ZTF DR24 Objects Table HATS collection. It processed all 100 targets and returned 773 OID rows within 5 arcseconds. The audit recomputed great-circle separations and produced the following counts:

| Cone radius | Targets with at least one OID | Unmatched targets | Targets with multiple OIDs | Same-filter multiple OIDs |
|---:|---:|---:|---:|---:|
| 1 arcsec | 48 | 52 | 33 | 27 |
| 2 arcsec | 78 | 22 | 69 | 59 |
| 5 arcsec | 97 | 3 | 94 | 88 |

At 5 arcseconds, the maximum multiplicity was 22 OIDs for one BTS coordinate. At 1 arcsecond, the 48 matched targets had 160 OID rows. For the 97 targets with at least one match inside 5 arcseconds, the nearest-match separation had a median of 1.051 arcseconds, a mean of 1.330 arcseconds, a 90th percentile of 3.193 arcseconds, and a maximum of 4.913 arcseconds. Across all 773 returned OID rows, the median separation was 2.289 arcseconds. The 22-OID example is BTS source `ZTF19aaklqod` (TNS `SN2020ctr`, type `SN Ia`); it has 9 `zg`, 5 `zi`, and 8 `zr` OIDs within 5 arcseconds, but only one OID within 1 arcsecond. This demonstrates why a 5-arcsecond cone is a candidate-generation radius, not an identity rule. The raw DR24 match CSV SHA-256 is `32221405752ac3424054832c797ea502a6c19739b3201b87c7dbb397d04ce5f6`.

The complete evidence artifact is attached to GitHub Actions run [41488299913](https://github.com/saeed92m/ztf-classifier/actions/runs/41488299913). Artifact ID: `13163452038`. ZIP SHA-256: `4e83841123920cdad7feaf72ffc2e1cddc47b276fb5f6cc7faa544c77d233844`.

The initial match artifact contains OID, RA, Dec, and filter code, but no field/quadrant identifiers. Therefore, its same-filter multiplicity counts are descriptive only. They cannot distinguish field/quadrant boundary splits from other close neighbors. The updated query now introspects the DR24 HATS schema and requests `field`, `ccdid`, `qid`, `rcid`, and `fid` when available. The updated auditor writes a per-match CSV with recomputed angular separation and partitions OIDs by field/readout channel when the metadata is complete. These changes are committed, and 12 contract tests, Ruff format, and Ruff lint pass. The updated source-backed query has not yet been verified against a new DR24 artifact. Until then, the initial counts remain the only measured results. The 5-arcsecond result is a broad candidate set, not a validated cross-match. The 1-arcsecond result is more restrictive but does not prove identity for transient sources. No precision, recall, or false-positive rate is claimed.

The 100-object sample contains 62 rows with a non-placeholder type and 38 rows with type `-`. The full BTS snapshot contains 3,374 unclassified rows. This sample is suitable for the spatial-recovery pilot, not for a class-balanced classification benchmark.

## Acceptance criteria

The pilot is complete only when:

1. both source snapshots have immutable evidence manifests;
2. all sampled source IDs and coordinates are traceable;
3. every spatial query is reproducible from the recorded parameters;
4. every returned ZTF OID is retained with its filter and separation;
5. no-match, single-match, multi-filter, and same-filter multiplicity are reported separately;
6. synthetic tests verify the multiplicity calculations;
7. the report makes no claim that a multiple OID is a false positive without further evidence.

This experiment is independent of the CPVS paper-membership reconstruction. It must not change the v0.2.0 model, feature set, class order, production selector, or existing scientific acceptance criteria.

## Source facts and limitations

- The BTS sample explorer documentation says the sample is automatically updated every few hours and explains its incompleteness for Galactic events and non-transients.
- The IRSA DR24 HATS tutorial states that ZTF objects are defined per filter, field, and quadrant. It says one astrophysical source can be represented by up to three filter-specific objects, with further splits near field/quadrant boundaries.
- The StarEmbed dataset page lists 42,585 rows, four splits, Catalina source IDs, coordinates, seven in-distribution classes, and a disjoint anomaly split.

These source facts motivate the experiment. They are not results of the experiment.
