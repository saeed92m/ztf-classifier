# ZTF DR24 Explorer

## Purpose

The DR24 Explorer provides a bounded, raw-data view of ZTF DR24 light curves.

It uses the indexed `objectid` lookup. It does not scan the full DR24 catalog.

The view is experimental. It is a data-inspection tool, not a DR24 classifier.

## Lookup

1. Start the Workbench by using the documented application launch procedure.
2. Open **DR24 Explorer**.
3. Enter 1–10 unique positive ZTF DR24 `objectid` values. Separate values with commas or spaces.
4. Select **Load raw light curves**.

The Workbench sends one bounded batch request to `POST /v1/dr24/lightcurves`. The backend requires the indexed `objectid` index. It rejects invalid, duplicate, or unrequested IDs. It also checks each catalog epoch count against the returned payload row count. Missing OIDs remain explicit in provenance.

## Chart and raw records

The chart uses native DR24 values:

- X axis: HMJD, which is HJD - 2400000.5.
- Y axis: native ZTF magnitude.
- Vertical bars: reported `magerr`, when it is finite and non-negative.
- Blue points: bit 15 of `catflags` is not set.
- Amber points: bit 15 is set.
- Gray points: `catflags` is missing or invalid.

Only numeric, finite HMJD/magnitude pairs appear in the chart. Missing values such as JSON `null` do not become zero-valued points. Negative or missing `magerr` does not produce an error bar. No source row is removed from the raw table or JSON export. The chart does not remove flagged epochs.

The raw table displays `hmjd`, `mag`, `magerr`, `clrcoeff`, and `catflags`. It displays up to 50 rows. The chart uses all finite HMJD/magnitude points returned by the source.

## Raw QC summary: `dr24-raw-qc-v0.1`

The summary reports descriptive counts:

- Total epochs.
- Finite HMJD, magnitude, and magnitude-error values.
- Positive, zero, negative, and non-finite `magerr` values.
- Valid, missing, and invalid `catflags` values.
- Bit-15-set and bit-15-not-set counts.
- `catflags == 0` count.
- Other non-zero flags when bit 15 is not set.
- `epochs_excluded`.
- `filtering_applied`.

The current contract reports `epochs_excluded = 0` and `filtering_applied = false`.

**This is not a quality-selection policy.** It does not define a threshold or approve an epoch mask. It does not mark an object as scientifically valid. Keep all raw values.

## JSON export: `ztf-dr24-raw-export-v0.2`

After a successful batch lookup, select **Download raw JSON + QC**.

The file contains:

- The complete raw API response for every returned OID.
- Source and query provenance, including requested/returned/missing OIDs.
- Catalog schema and per-OID payload hashes.
- The `dr24-raw-qc-v0.1` summary.
- Export schema version and export timestamp.

The export button remains disabled when the source lookup fails or returns no catalog row.

Keep the exported file with the analysis record. Do not edit the raw payload.

## Source and provenance

The view displays acquisition provenance. It includes the source, query index, requested and returned OIDs, missing OIDs, schema hash, and payload hashes.

The payload hash identifies the canonical raw response for the OID. Keep the hash with any exported file or downstream analysis.

## Scientific limits

The DR24 Explorer does not:

- Convert HMJD to geocentric MJD.
- Apply color correction.
- Convert native DR24 magnitudes to another photometric system.
- Apply a `catflags` quality mask.
- Remove negative or zero `magerr` values.
- Group OIDs into physical sources.
- Generate the frozen v0.2.0 features.
- Run the frozen v0.2.0 model.
- Estimate calibrated class probabilities.
- Perform OOD or anomaly validation.

A ZTF `objectid` is not guaranteed to represent one unique astrophysical source across filters, fields, or quadrants. Do not merge OIDs by positional proximity alone.

The file `configs/samples/dr24_park_raw_candidate_sample_v0.1.json` contains five BTS-associated spatial candidate identifiers and seven OIDs. The associations are candidates only. They are not confirmed physical identities, training labels, or independent ground truth. The manifest does not authorize OID grouping.

The frozen v0.2.0 model, its 42-feature schema, class order, benchmark, and scientific gates remain unchanged.

## Park demonstration status

A seven-OID raw Workbench browser smoke passed for 2,183 epochs. Four OIDs had independent HATS payload-hash references. Three OIDs had availability evidence but no independent payload-hash reference.

This result verifies raw retrieval and display. It does not satisfy the 5–10 object application acceptance test or the 30–50 object guided Park demonstration. Descriptive QC, JSON export, and source provenance are available in this view, but validated source identity, production QC selection, DR24 feature generation, inference, and scientific performance evaluation remain separate work.


## Multi-OID batch lookup

The Explorer accepts 1–10 unique positive DR24 OIDs in one request. Separate OID records remain separate. The interface calls `POST /v1/dr24/lightcurves`, displays each returned record, and reports missing OIDs from provenance. It does not infer astrophysical identity across OIDs.

The export contains the raw source payload and the separate server-side diagnostic QC assessments. The QC policy is `DIAGNOSTIC_NOT_PRODUCTION_APPROVED`; no epoch is removed or modified.
