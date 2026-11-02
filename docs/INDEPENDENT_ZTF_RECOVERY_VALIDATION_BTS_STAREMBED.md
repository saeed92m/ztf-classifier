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

The repository already has a StarEmbed acquisition adapter. The scheduled scientific-validation run on 2026-11-02 reported `acquisition=ACQUIRED`. That confirms acquisition, not classifier performance or recovery accuracy. The separate source-integrity audit in Issue [#210](https://github.com/saeed92m/ztf-classifier/issues/210) reports one duplicate `sourceid` within train and one object-ID overlap between train and test. StarEmbed-derived model evaluation remains blocked until those records and the upstream split semantics are resolved.

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

The 2026-11-03 follow-up also queries the DR24 Lightcurves HATS `objectid` index for every recovered Objects Table OID. This records whether a time-series row exists and its `nepochs`. It does not download nested photometry or certify clean epochs.

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

The official BTS CSV request used `subsample=cantrans`, `endpeakmag=19.0`, `quality=y`, and `samprcf=y`. It returned HTTP 200 and 10,551 unique rows for that filtered explorer query; this is not the complete BTS survey catalogue. The verified acquisition manifest records code revision `79fff7d3d557df528c591234c410600d6d3735e6`. The raw response SHA-256 is `af2362275074ff4b6c70523b9db6f2d5991af16fdd8d76ed47520948eb788e82`. The deterministic 100-row sample SHA-256 is `044dc0b3b6a3cf127f50099a7a3f76ae3423df62807564f0c365efb5007bd9a4`.

The spatial query used the official IRSA ZTF DR24 Objects Table HATS collection. It processed all 100 targets and returned 773 OID rows within 5 arcseconds. The audit recomputed great-circle separations and produced the following counts:

| Cone radius | Targets with at least one OID | Unmatched targets | OID rows | Targets with multiple OIDs | Same-filter multiple OIDs | Same-filter multi-OIDs across partitions | Same-filter multi-OIDs within one partition |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 arcsec | 48 | 52 | 160 | 33 | 27 | 27 | 0 |
| 2 arcsec | 78 | 22 | 338 | 69 | 59 | 58 | 15 |
| 5 arcsec | 97 | 3 | 773 | 94 | 88 | 81 | 77 |

At 5 arcseconds, the maximum multiplicity was 22 OIDs for one BTS coordinate. The nearest-match separation statistics were: 1 arcsec radius, median 0.496 arcsec, mean 0.519 arcsec, 90th percentile 0.983 arcsec, maximum 0.998 arcsec; 2 arcsec radius, median 0.831 arcsec, mean 0.873 arcsec, 90th percentile 1.636 arcsec, maximum 1.934 arcsec; 5 arcsec radius, median 1.051 arcsec, mean 1.330 arcsec, 90th percentile 3.322 arcsec, maximum 4.913 arcsec. Across all 773 returned OID rows, the median separation was 2.289 arcseconds, the mean was 2.456 arcseconds, the 90th percentile was 4.436 arcseconds, and the maximum was 4.995 arcseconds. The 22-OID example is BTS source `ZTF19aaklqod` (TNS `SN2020ctr`, type `SN Ia`); it has 9 `zg`, 5 `zi`, and 8 `zr` OIDs within 5 arcseconds, but only one OID within 1 arcsecond. This demonstrates why a 5-arcsecond cone is a candidate-generation radius, not an identity rule. The raw DR24 match CSV SHA-256 is `daf9e8196e475b50442d5fb8fa1d0346aa5b51df060f9ef104135a2c59fbf326`.

The schema-aware evidence artifact is attached to GitHub Actions run [41525750067](https://github.com/saeed92m/ztf-classifier/actions/runs/41525750067). Artifact ID: `13179927852`. ZIP SHA-256: `dbbd39759d11645cfa044538d786960b3bf221d25a9b73b849f136a735e1f830`.

The live Objects Table schema exposed 76 columns. The query selected `field`, `ccdid`, `qid`, and `fid`; `rcid` was not available. The schema-column SHA-256 is `8cb49b5d90cc6df36c306daf08be4aa0402a19de17c2a55058e99064336541f5`. The query used Python 3.11.16, LSDB 0.10.4, and s3fs 2026.9.0. The code revision was `79fff7d3d557df528c591234c410600d6d3735e6`. All 100 targets were processed. The 773 returned OIDs were unique across 97 matched BTS targets; no OID was shared between BTS targets.

The provenance-aware audit shows that all 27 same-filter multi-OID cases at 1 arcsecond span different field/CCD/quadrant partitions. No target has same-filter multi-OIDs within one partition at this radius. At 2 arcseconds, 15 targets have same-filter multi-OIDs within one partition. At 5 arcseconds, 77 targets do. This is strong evidence that the wider cone includes additional nearby Objects Table entries in the same partition. It is not proof that every such entry is a false association. The 1-arcsecond result is consistent with IRSA's guidance that a 1-arcsecond cone can be reasonable for combining ZTF objects, but it is not an accepted identity rule.

The per-match audit contains one row for each of the 773 OIDs and records recomputed angular separation plus field/CCD/quadrant/filter provenance. The raw match CSV SHA-256 is `daf9e8196e475b50442d5fb8fa1d0346aa5b51df060f9ef104135a2c59fbf326`; the per-match audit SHA-256 is `1ffaaeaa32c506d451c0241abf07f8450c1a47de749457f1d582e99de23468c3`; the per-object audit SHA-256 is `be0b248f36f8164f614c65ce8a811cf1c6924db213f3d38304f13377308963fd`.

The official IRSA DR24 tutorial notes that the Objects Table can contain more objects than the Lightcurves Table. An Objects Table OID match therefore does not prove that a time-series row exists. PR #246 now adds an indexed Lightcurves HATS `objectid` lookup. Its source-backed execution is in progress; no availability count is claimed yet.

These results remain positional diagnostics. They do not establish physical identity, cross-match precision/recall, or model accuracy.

The 100-object sample contains 62 rows with a non-placeholder type and 38 rows with type `-`. The full BTS snapshot contains 3,374 unclassified rows. This sample is suitable for the spatial-recovery pilot, not for a class-balanced classification benchmark.

## Relationship to the DR24 feature-engine smoke

The separate real-data feature-engine smoke in Issue [#188](https://github.com/saeed92m/ztf-classifier/issues/188) was reviewed at raw-response level. Its 12 selected OIDs did not represent 12 complete multi-filter sources:

- All 5 failed OIDs had only `filtercode=zi` observations. The g/r feature contract correctly excluded these rows.
- The 7 feature-engine calls that returned results were single-band: 4 r-only and 3 g-only.
- Each partial feature vector had 19 finite values and 23 NaN values out of 42.
- No selected OID had both g and r observations. Model inference was not run.

The filter normalizer is not the root cause. The sample selection uses one OID as the unit, but DR24 OIDs are filter/field/quadrant-specific. The frozen g/r feature contract needs an astrophysical source group that maps constituent OIDs across filters. This PR supplies spatial candidate evidence and an indexed Lightcurves availability check; it does not implement or validate source grouping. Issue #188 now records the root-cause diagnosis and required work.

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
