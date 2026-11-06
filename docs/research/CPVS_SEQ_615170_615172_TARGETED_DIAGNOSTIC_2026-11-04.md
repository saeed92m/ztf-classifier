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


## Independent r-band archive scan — 2026-11-07

The g-band result is a strong identity lead only. The next diagnostic is deliberately separate and reads the original `ztf2r.zip` archive from Zenodo record [3886372](https://zenodo.org/records/3886372).

### Source contract

- Archive: `ztf2r.zip`.
- Zenodo-published MD5: `daa7bc45c67579253eebe6b1c09dfbd9`.
- Table 2 target: Seq `615170`, `Nr=113`, RA 307.36563°, Dec −13.42128°.
- Suspected orphan: Seq `615172`.
- Expected r-band schema: `SourceID, RAdeg, DEdeg, HJD, rmag, e_rmag, r_flag`.

### Diagnostic behavior

- Verify the downloaded archive against the published MD5.
- Stream the extracted member with Info-ZIP and calculate its SHA-256, byte count, row count, field-count distribution, malformed-row count and ZIP CRC.
- Summarize Seq 615170 and Seq 615172 independently.
- Search for all SourceIDs with rows within 2 arcseconds of the Table 2 coordinates. This radius only retrieves candidates; it is not an identity rule.
- Preserve HJD, r magnitude, magnitude error and flags in aggregate summaries.
- Upload only a small JSON report. Do not upload or commit raw photometry.
- The first run is a discovery run. It does not claim independent member integrity until the observed member SHA-256, size and row count are reviewed and pinned in a second run.

### Scientific boundaries

- No automatic SourceID remapping.
- No proximity-only identity decision.
- No full r-band Table 2 reconciliation in this targeted diagnostic.
- No explanation of the 11,602 candidate-only membership residuals.
- No change to the CPVS selector, SNR thresholds, published reference, model, features, taxonomy or frozen v0.2.0 baseline.

### Acceptance sequence

1. Pass synthetic regression tests.
2. Complete the source-backed r archive scan with matching Zenodo archive MD5 and zero malformed rows.
3. Review the extracted-member SHA-256, byte count, row count, CRC, Seq summaries and nearby SourceIDs.
4. Pin the reviewed member SHA-256, size and row count.
5. Rerun and verify those pinned values.
6. Perform full r-band SourceID-to-Table2 `Nr` reconciliation in a separate bounded workflow.

The CPVS scientific blocker remains open until the full membership residual is explained.


## r-band archive result and ReadMe discrepancy — 2026-11-07

The first source-backed r-band scan completed in [workflow 42311975704](https://github.com/saeed92m/ztf-classifier/actions/runs/42311975704), artifact 13550020720. The artifact ZIP SHA-256 is \`0d64d338998fc62694d0cc4527ed9cf95544bda5156168ab642ca3731602c80b\`; the extracted JSON SHA-256 is \`2c31b258dffddc3eff0cd6cdc70bb7bf743e180608004b4b808ec06d6710f3e8\`.

### Archive and extracted-member evidence

- Zenodo archive: \`ztf2r.zip\`, DOI \`10.5281/zenodo.3886372\`.
- Published archive MD5: \`daa7bc45c67579253eebe6b1c09dfbd9\`; observed value matched.
- Observed archive SHA-256: \`48331ba1157afc993a1399e094b97752a82d8d0f736d2fdf63fd7b2a82281b74\`.
- ZIP member CRC-32 expected and actual: \`225495a0\`; matched.
- Info-ZIP streamed member size: \`6,175,667,360\` bytes.
- Streamed member SHA-256: \`78df6d0b22099a7e5c6e74b897682c6ab94f90d5f9e887d4b0b3b152514e50fe\`.
- Streamed rows: \`109,971,576\`; zero malformed rows; all rows had seven fields.
- The central-directory 32-bit size value was \`1,880,700,064\`, which equals the streamed size modulo \(2^{32}\). The same modulo pattern exists in the g archive. The full stream reached EOF and the CRC matched; do not interpret the 32-bit size field as the full uncompressed size.

The extracted-member SHA-256, byte count and row count are pinned to this first run as internal reproducibility references. They are not Zenodo-published member checksums. The next run must reproduce them.

### Seq 615170 / 615172 cross-band identity evidence

- Table 2 Seq \`615170\`: \`Nr=113\`, \`rmag=14.736\`, RA 307.36563°, Dec −13.42128°.
- r-band rows under Seq \`615170\`: zero.
- r-band rows under orphan Seq \`615172\`: 113.
- Median coordinates for Seq 615172: RA 307.3656702°, Dec −13.4214213°.
- Median-coordinate separation from Table 2: **0.5277981 arcsec**.
- Closest individual r epoch separation: 0.4953828 arcsec.
- Mean r magnitude: 14.7357168; delta from Table 2: **−0.0002832 mag**.
- r HJD range: 58247.47634–58660.48647.
- r flags: all 113 rows have flag 0.
- g/r median-coordinate separation: **0.0897550 arcsec**.
- The g-band archive independently has 132 rows under Seq 615172, equal to Table 2 \`Ng=132\`, and zero rows under Seq 615170.

Disposition: **STRONG_CROSS_BAND_IDENTITY_LEAD**. The g and r archive records under Seq 615172 have matching per-band counts, sub-arcsecond positions, nearly identical mean magnitudes to Table 2, and overlapping time coverage. This is strong evidence of an archive SourceID mismatch for this one Table 2 object. It is not an automatic SourceID correction.

### Newly identified r-band record-count discrepancy

The authoritative [CDS ReadMe for J/ApJS/249/18](https://cdsarc.cds.unistra.fr/viz-bin/ReadMe/J/ApJS/249/18?format=html&tex=true) lists 89,697,393 records for both \`ztf2g.dat\` and \`ztf2r.dat\` (File Summary, lines 60–70). The checksum-pinned Zenodo r archive stream contains 109,971,576 rows.

The independently hash-verified CDS \`table2.dat\` artifact from workflow 41367972395 has 781,602 unique Seq rows and a summed \`Nr\` of **109,970,858**. Therefore:

- r archive rows minus Table 2 sum \`Nr\`: **+718**.
- Table 2 sum \`Nr\` minus CDS ReadMe r row count: **+20,273,465**.
- r archive rows minus CDS ReadMe r row count: **+20,274,183**.

This indicates a ReadMe-versus-data count inconsistency for the r band. It does not yet establish whether the 718-row residual is caused by per-Seq deficits/surpluses, extra SourceIDs, or duplicates. The full per-Seq comparison is required.

### Full r-band Seq reconciliation added

The updated workflow downloads the checksum-pinned CDS Table 2 and ReadMe, verifies their hashes and sizes, then compares every r-band SourceID count with Table 2 \`Nr\`. It records matched, deficit, surplus and missing Seq counts, total deficit and surplus rows, archive-only Seq IDs, net row differences, and a complete TSV of all mismatches.

The first scan is not the full reconciliation. The pinned second scan must pass before we accept its reproducibility. No raw photometry is uploaded.

### Scientific boundaries

- No automatic SourceID remapping.
- No proximity-only identity decision.
- No claim that the 11,602 candidate-only membership residuals are resolved.
- No change to the CPVS selector, thresholds, published reference, model, features, taxonomy or frozen v0.2.0 baseline.
- The CPVS scientific gate remains fail-closed.
