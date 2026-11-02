# Independent ZTF Recovery Validation — BTS and StarEmbed

## Status

Planning and source-contract review only. No BTS-to-DR24 recovery run has been executed yet. This document does not claim any measured recovery rate or identifier multiplicity.

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
- BTS: deterministic 100-object sample, restricted to rows with valid ZTF ID, TNS ID, RA, Dec, and a non-empty classification.

The sampling algorithm, seed, sorted source IDs, and sample SHA-256 must be recorded. Do not silently replace failed sample members.

### Phase 3 — spatial recovery

For every sampled source, query the official ZTF DR24 Objects Table by sky position. Use a 1-arcsecond primary radius and sensitivity checks at 2 and 5 arcseconds. Keep all returned OIDs and their coordinates, filters, and angular separations.

For BTS, coordinate offsets between the transient and its host or reference-image object can occur. A spatial match is therefore an association candidate, not proof of physical identity. Record this limitation.

### Phase 4 — identifier multiplicity analysis

For each external source, report:

- no ZTF OID found;
- exactly one OID found;
- multiple OIDs across different filters;
- multiple OIDs in the same filter;
- multiple OIDs with distinct field/quadrant provenance, where available;
- ambiguous spatial associations;
- nearest angular separation;
- sensitivity to the 1, 2, and 5 arcsecond radii.

Do not call every OID after the first an extra object. Report OID multiplicity separately from astrophysical-source multiplicity.

### Phase 5 — scale-up

Only after the pilot passes data-integrity and matching checks:

- increase to a fixed 1,000-object sample;
- then evaluate the full available source sample if runtime and query load are reasonable.

Do not run a full-catalog cross-match until the pilot establishes query cost and match behavior.

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
