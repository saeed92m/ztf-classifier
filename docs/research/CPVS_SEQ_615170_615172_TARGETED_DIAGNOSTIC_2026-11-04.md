# CPVS targeted Seq 615170 / 615172 identity diagnostic — 2026-11-04

## Question

Does the 132-row g-band archive group stored under orphan Seq `615172` belong to Table 2 control Seq `615170`?

This is a targeted archive-to-Table2 identity check. It does not attempt to reproduce the full 741,786 candidate set.

## Retained evidence

- Zenodo source record: https://zenodo.org/records/3886372
- g archive: `ztf2g.zip`, expected size 753.7 MB.
- Expected archive MD5: `850fcef561dd7407fbe8e19e99100d7a`.
- Expected archive SHA-256: `47cd1823b3ccdb69fa3085381cf63ff0605f6d841fc3bc37489dce023ddc19b9`.
- Extracted `ztf2g` SHA-256: `366aaf3539f83955bb1e29799df9e63005a9eb682f4f56d0807545a3534b0f16`.
- Extracted `ztf2g` size: 5,034,066,142 bytes.
- Expected total g rows from the retained layout audit: 89,697,393.
- Table 2 Seq `615170`: `ZTFJ202927.75-132516.6`, RA 307.36563 deg, Dec -13.42128 deg, `gmag=14.886`, `Ng=132`, `Nr=113`.
- Retained archive audit: Seq `615170` has zero g and r rows; orphan Seq `615172` has 132 g rows.

Seq `615170` is one of the 55 four-field-positive noncandidate controls. The 132-row count match is a hypothesis lead only.

## Diagnostic method

The workflow downloads only the g-band archive. The first scanner run verified the official archive MD5/SHA-256 but Python `ZipExtFile` yielded only 739,098,846 bytes and 13,517,255 rows. The expected uncompressed member is 5,034,066,142 bytes and 89,697,393 rows. The observed partial member SHA-256 was `9ffbb54896a4c0676f421ca281a7c53f48fca7047a535cfeff6628ec8db0d3b2`; it did not match the retained full-member SHA-256. The revised scanner uses Info-ZIP `unzip -p`, the extraction path used by the earlier full-layout audit, and verifies the uncompressed member SHA-256, byte count, and row count independently. It also records the ZIP central-directory CRC separately. A CRC mismatch is never ignored; it is reported separately from the independent byte-level checks. A synthetic test changes only the central-directory CRC and verifies that Info-ZIP still returns the complete payload with the expected SHA-256 and size.

For each target Seq, it records row count, coordinate ranges and medians, HJD range, magnitude/error ranges, and flag counts. It computes the angular separation between the orphan rows' median coordinates and the Table 2 coordinates for Seq `615170`.

A coordinate separation of at most one arcsecond and a row count of 132 is reported as `STRONG_IDENTITY_LEAD`. This is not an automatic correction to the source IDs. The raw evidence and independent checks must be reviewed first.

Only the small JSON diagnostic is uploaded as a GitHub Actions artifact. The raw archive and extracted photometry are not committed or uploaded.

## Limitations

- This workflow checks only the g-band archive.
- It does not explain the 11,602 candidate-only IDs.
- It does not establish the publisher's selection rule.
- It does not modify the CPVS selector, SNR thresholds, or v0.2.0 baseline.
- The r-band archive and other orphan/mismatched Seq values require separate evidence.

## Current disposition

- Identity hypothesis: NOT VERIFIED.
- Run 7 (42061358291) confirmed the archive MD5/SHA-256 but the Python reader stopped at 739,098,846 bytes. It produced no valid identity comparison.
- The revised scanner uses Info-ZIP and has a synthetic regression test for a central-directory CRC-only discrepancy.
- Run 8 (42062460017) is testing the revised scanner against the full checksum-pinned source archive. Its result is pending.
- Scientific gate: unchanged and fail-closed.
- Next step after a successful full-member integrity check: compare the raw coordinate/HJD evidence, then decide whether to run a separate targeted r-band check.


## Verified source-backed result — 2026-11-05/06

The corrected Info-ZIP scanner completed against the checksum-pinned Zenodo g-band archive in workflow [42063847111](https://github.com/saeed92m/ztf-classifier/actions/runs/42063847111), artifact `13432972969`. The downloaded artifact was independently inspected.

### Integrity

- Archive: `ztf2g.zip`, Zenodo DOI `10.5281/zenodo.3886372`.
- Archive MD5: `850fcef561dd7407fbe8e19e99100d7a` — matched.
- Archive SHA-256: `47cd1823b3ccdb69fa3085381cf63ff0605f6d841fc3bc37489dce023ddc19b9` — matched.
- ZIP member CRC-32: expected and actual `d2f33aa0` — matched.
- Extracted member size: `5,034,066,142` bytes — matched.
- Extracted member SHA-256: `366aaf3539f83955bb1e29799df9e63005a9eb682f4f56d0807545a3534b0f16` — matched.
- Full scan: `89,697,393` data rows; zero malformed rows; all rows had seven fields.

### Targeted identity lead

- Table 2 Seq `615170`: RA 307.36563°, Dec −13.42128°, `gmag=14.886`, `Ng=132`, `Nr=113`.
- Seq `615170`: zero g-band rows in the scanned archive.
- Orphan Seq `615172`: 132 g-band rows.
- Median orphan coordinates: RA 307.3656934°, Dec −13.4214107°.
- Median angular separation from Table 2 Seq 615170: **0.5202627 arcsec**.
- Orphan mean g magnitude: 14.88604545; difference from Table 2 `gmag`: **+0.00004545 mag**.
- Orphan HJD range: 58254.44022–58657.48608.
- g-flag counts: 130 rows with flag 0; 2 rows with flag 1.

The result is a **STRONG_IDENTITY_LEAD**, not a confirmed ID correction. The scan covers only the g archive. It does not establish the r-band counterpart, explain the 11,602 candidate-only membership residuals, prove the publisher's selection rule, or resolve the 91 Seq-level g-band count mismatches and the 4,916-row Table 2/archive total difference.

### Required next checks

1. Inspect the r-band archive independently for Seq 615170, Seq 615172, and any coordinate-matched orphan rows. The Zenodo record lists `ztf2r.zip` (881.5 MB; MD5 `daa7bc45c67579253eebe6b1c09dfbd9`); its extracted content hash and row count must be measured, not assumed.
2. Reconcile all r-band Seq counts against Table 2 `Nr`, as was done for the g archive.
3. Investigate all 91 g-band per-Seq count mismatches, not only this one object.
4. Keep the 11,602 membership residuals and the publisher-method interpretation open until a reproducible source-level explanation is established.

The CPVS selector, SNR thresholds, published reference, model, features, class order, and frozen v0.2.0 baseline remain unchanged. The scientific gate remains fail-closed.
