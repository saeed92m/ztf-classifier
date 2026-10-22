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
- Seq values are **not** equal to the contiguous range 1–781,602. The pinned VizieR parent-metadata TSV (SHA-256 `3675b1274f73fcb15d47e7a780f194ef8fa335cd248c6ff53ea4f01559c86591`) identifies the two missing Seq values as **615171 and 615172**. After those gaps, physical row ordinal is offset from Seq by two; row ordinal is therefore not a safe replacement for Seq.

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

## Additional exact-set diagnostic: parent metadata validity

A separate full-dataset diagnostic in heavy run [38635891449](https://github.com/saeed92m/ztf-classifier/actions/runs/38635891449), artifact ID 11935357767, tested the predicate that all four parent Table2 fields are finite and positive: gmag, rmag, Per-g, and Per-r.

Recalculation from the retained artifact confirms:
- Candidate set: 741,786 Seq IDs.
- Candidate IDs with all four parent fields positive: 730,184.
- Candidate-only IDs retained by the four-field predicate: 0.
- Published-only IDs relative to that filtered set: 0, because the unfiltered object-name audit maps all 730,184 published rows into the candidate set.
- Exact set equality: `(candidate ∩ valid(gmag,rmag,Per-g,Per-r)) == published Table4 membership`.

Partition of the 11,602 candidate-only objects:
- 11,580 fail both the two-mean-magnitude validity pair and the two-per-band-period validity pair.
- 17 have both mean magnitudes positive but lack a positive value for at least one per-band period.
- 5 have both per-band periods positive but lack a positive g-band mean magnitude.
- 0 pass all four checks.

The raw-photometry diagnostics also show a strong separation in qualifying g-band detections:
- Candidate-only objects: minimum 1, median 5, 90th percentile 9, 99th percentile 39 qualifying g detections.
- Published members: minimum 11, median 104, 90th percentile 201, 99th percentile 488 qualifying g detections.
- Among candidate-only objects, 11,470 have no positive parent gmag and 11,475 have no positive Per-g. Only 171 have any non-zero qualifying flag in g and 680 in r, so a blanket flag-zero rule is not supported.

This suggests the extras are concentrated among objects for which the parent two-band fit metadata is incomplete, rather than being explained by the tested nonlinear SNR conversion. It still does not establish the publisher's exact acceptance rule: a minimum detection count or metadata-validity condition must not be inferred solely from these distributions.

The diagnostic parent-metadata TSV SHA-256 is `3675b1274f73fcb15d47e7a780f194ef8fa335cd248c6ff53ea4f01559c86591`; the candidate set SHA-256 is `699ff34bcf8dd4b5043eed48384973cb5109fd86ca260f831a502097370238df`; the full diagnostic JSON SHA-256 is `7e763d8804a57d75d1633d0a4089a4a6ac5aa40bb4695964d35e645b67ad5b61`; and the membership audit JSON SHA-256 is `4c1a082569820af26cbca80320a4913a00e1849446b0ca0205fc872b5ce89c5c`.

**Interpretation:** this is an exact membership-recovery predicate, not yet a proven statement of the publisher's selection rule. The official Table2 ReadMe marks gmag, rmag, Per-g, and Per-r as missing when zero, but Chan et al. (2022) explicitly describe the g/r SNR thresholds and do not explicitly state that all four metadata fields must be positive. Preserve this distinction: the residuals are fully explained numerically by missing/invalid parent metadata, while the scientific justification for treating all four fields as required remains open. Do not silently change the production predicate until the source method or author clarification supports it.

## Confirmed defects versus unresolved science

1. **Confirmed identifier-comparison defect:** Table4 catalog-internal IDs and parent SourceIDs are distinct namespaces. The audit must crosswalk by ZTF name.
2. **Confirmed parser defect:** the pinned Table2 Seq values are not a contiguous 1..N row ordinal; substituting row order can mis-map objects.
3. **Confirmed SNR guard defect:** non-finite SNR values could pass the previous comparison guard. Explicit finite/positive checks are now covered by regression tests.
4. **Unresolved scientific discrepancy:** 11,602 candidate-only objects remain after the object-name crosswalk and SNR guard correction. Neither a flag-zero cut, a magnitude cut, nor the nonlinear SNR alternative reproduces the reference membership. Do not force the count by changing thresholds.

## Full candidate-only provenance trace (completed 2026-10-22)

The full per-object g/r trace completed successfully in [run 39737844922](https://github.com/saeed92m/ztf-classifier/actions/runs/39737844922), artifact ID `12408367638`, named `cpvs-100-1000-sample-snr-diagnostics`. It contains one diagnostic record for each of the 11,602 candidate-only Seq/ZTF objects, including g/r source-row counts, valid-error counts, qualifying-row counts, flags, representative HJD/magnitude/error rows, and linear/exact SNR comparisons. The run verified the retained heavy-source artifact SHA-256 `debd55db39be64c5e267af44bc1e486824b3d6d0c0caeac9f04fca254c05410c`.

Full-trace findings:
- All 11,602 candidate-only objects have at least one qualifying source row in both g and r under the SNR-only rule.
- Qualifying g-row count among extras: minimum 1, median 5, 90th percentile 9, 99th percentile 39, maximum 245; 11,435 objects have 10 or fewer qualifying g rows.
- The nonlinear inverse-magnitude-error SNR diagnostic changes zero membership classifications.
- Combined with the parent metadata audit, the extras are numerically accounted for by incomplete/non-positive parent fit metadata. The exact production-method interpretation remains unresolved.

Review the retained per-object trace before proposing any scientific-rule change. If the four-field metadata predicate cannot be supported by the published method or source code, keep the blocker and request author clarification rather than inventing a filter.
