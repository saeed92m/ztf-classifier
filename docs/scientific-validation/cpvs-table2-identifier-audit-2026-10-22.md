# CPVS Table2 identifier schema and membership audit — 2026-10-22

## Purpose

This record documents the source-backed identifier schema used to reconstruct the published CPVS subset and the unresolved 11,602-object membership discrepancy. It is diagnostic evidence, not scientific sign-off.

## Pinned source and integrity

- Source: Zenodo record 3886372, version v1, *The Zwicky Transient Facility Catalog of Periodic Variable Stars*.
- Official source: https://zenodo.org/records/3886372
- Parent archive: `Table2.txt.zip`
- Expected MD5: `24dd4cf138a2687901d64b2d029cc624` — verified by GitHub Actions.
- SHA-256: `0f3ca5d4e71f674c38b3c08553c12cca0c32d2d31f776166ab29ce80a75cf138`.
- Archive size: 63,989,551 bytes.
- Table2 object rows: 781,602.
- Unique ZTF names: 781,602; duplicate names: 0.
- Explicit Seq identifiers: 781,602 unique values, minimum 1, maximum 781,604.
- Seq values are **not** equal to the contiguous range 1–781,602. Physical object-row ordinal is therefore not a safe replacement for Seq.

The first data rows establish the schema (fields shown in order):

| ZTF identifier | Seq | RA (deg) | Dec (deg) | Period (days) |
|---|---:|---:|---:|---:|
| ZTFJ000000.13+620605.8 | 1 | 0.00056 | 62.10163 | 1.9449979 |
| ZTFJ000000.14+721413.7 | 2 | 0.00061 | 72.23716 | 0.2991500 |
| ZTFJ000000.19+320847.2 | 3 | 0.00080 | 32.14645 | 0.2870590 |

The supplementary-data description states that SourceID joins the g/r single-exposure attachments to Table2; it gives SourceID=3 for ZTFJ000000.19+320847.2. The actual pinned file exposes Seq in the second field, so derivation and auditing must preserve that explicit value. Coordinate-only table fixtures may use ordinal fallback in tests, but the pinned production source must resolve to explicit Seq.

## Identifier namespaces

- Table2 Seq / light-curve SourceID: source identifier for the parent object and its g/r measurements.
- VizieR Table4 catalog-internal ID: a separate namespace. Never compare it directly with the parent SourceID.
- Correct comparison: map each published Table4 row through its ZTF object name into the verified parent Seq namespace, then compare sets.

## Verified full-dataset result

Evidence:
- Full source-backed derivation and crosswalk: https://github.com/saeed92m/ztf-classifier/actions/runs/39699256625
- Audit artifact ID: `12391909327`
- Parent Table2 SHA-256: `0f3ca5d4e71f674c38b3c08553c12cca0c32d2d31f776166ab29ce80a75cf138`
- Published Table4 SHA-256: `cc6b094c9bc38d32cd2ced853d60e74e0924ff3c9819252795f60825972ad46f`
- Candidate-set SHA-256: `699ff34bcf8dd4b5043eed48384973cb5109fd86ca260f831a502097370238df`

| Metric | Verified value |
|---|---:|
| Parent objects | 781,602 |
| Published Table4 objects | 730,184 |
| Reconstructed candidates | 741,786 |
| Intersection | 730,184 |
| Candidate-only | **11,602** |
| Published-only | 0 |
| Published ZTF names missing from parent | 0 |
| Duplicate parent/published ZTF names | 0 |

The object-level membership is **not an exact match**. Zero published-only IDs does not explain the 11,602 candidate-only objects. Keep the scientific validation gate blocked.

## Deterministic sample and SNR diagnostic

The retained-source diagnostic artifact is run 39701473339, artifact ID `12393482824`, named `cpvs-100-1000-sample-snr-diagnostics`.

- Fixed seed: 20261022.
- Full sample: 1,000 objects, stratified as 500 published members and 500 non-members.
- Nested diagnostic: 100 objects, 50 members and 50 non-members.
- 1,000-object sample confusion counts: TP=500, FP=94, FN=0, TN=406.
- The nonlinear inverse magnitude-error/SNR alternative produced the same membership set as the current linear approximation in the full candidate comparison. It does not explain the discrepancy.
- In the sample, 93 of 94 candidate-only objects had at most 10 g-band rows, whereas all 500 sampled published members had at least 13 g-band rows. This is a diagnostic association, not proof of a minimum-row-count rule. The published method describes at least one qualifying detection per band; do not add a row-count cutoff without source-backed evidence.

## Confirmed defects versus unresolved science

1. **Confirmed identifier-comparison defect:** Table4 catalog-internal IDs and parent SourceIDs are distinct namespaces. The audit must crosswalk by ZTF name.
2. **Confirmed parser defect:** the pinned Table2 Seq values are not a contiguous 1..N row ordinal; substituting row order can mis-map objects.
3. **Confirmed SNR guard defect:** non-finite SNR values could pass the previous comparison guard. Explicit finite/positive checks are now covered by regression tests.
4. **Unresolved scientific discrepancy:** 11,602 candidate-only objects remain after the object-name crosswalk and SNR guard correction. Neither a flag-zero cut, a magnitude cut, nor the nonlinear SNR alternative reproduces the reference membership. Do not force the count by changing thresholds.

## Next evidence required

The full per-object g/r provenance trace for all 11,602 candidate-only objects is running against the retained heavy source artifact. It should preserve per-band row counts, valid errors, qualifying rows, flags, representative observations, and input/output hashes. Review that report before proposing a scientific-rule change. If the documented criterion still cannot explain the extras, retain the blocker and request clarification from the publication authors rather than inventing a filter.
