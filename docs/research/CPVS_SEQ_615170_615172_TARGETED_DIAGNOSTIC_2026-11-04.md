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

The workflow downloads only the g-band archive. The script verifies the official archive MD5/SHA-256, streams the compressed member without writing the 5 GB extracted file to disk, verifies the extracted member SHA-256 and byte count, and scans the complete data for Seq `615170` and `615172`.

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
- Source checksum and full extracted-file integrity: required by the workflow.
- Scientific gate: unchanged and fail-closed.
- Next step after the report: compare the raw coordinate/HJD evidence, then decide whether to run a separate targeted r-band check.
