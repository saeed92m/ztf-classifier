# CPVS 55-control archive identity lead — 2026-11-04

## Verified retained-artifact facts

Source: workflow run 41367972395, artifact 13108147605 (`cpvs-raw-cds-reconciliation`), plus the independent g-band layout artifact 13126290795.

- The 55 objects are all nonmembers of the published Table 4 reference, are not in the reconstructed candidate set, and pass the four-field positive-metadata diagnostic.
- Only 1/55 has g-band rows in the inspected original Zenodo archive; 51/55 have r-band rows. No object has both bands in the retained attachments.
- The full g archive contains 89,697,393 rows, compared with 89,702,309 summed Table 2 `Ng`; 91 Seq values have row-count mismatches.
- 55 Table 2 objects with positive `Ng` have no g-band rows in the inspected archive.
- The g archive contains one unknown Seq, `615172`, with 132 rows. The Table 2 object with Seq `615170` has `Ng=132`, `Nr=113`, and no g or r rows in the inspected archive.

## Specific identity lead

Table 2 Seq `615170` is `ZTFJ202927.75-132516.6`, at RA 307.36563 deg and Dec -13.42128 deg. Its Table 2 photometric summary is `gmag=14.886`, `rmag=14.736`, `Per-g=0.3496071`, `Per-r=0.3496036`, `Ng=132`, and `Nr=113`.

The unknown g-archive Seq `615172` has exactly 132 rows. The count match and two-step identifier difference are a useful lead. They do **not** prove that those rows belong to Seq `615170`. The retained small diagnostic artifact does not include the 132 raw rows, their coordinates, or their timestamps.

## Source integrity

- Zenodo record: https://zenodo.org/records/3886372
- g archive expected MD5: `850fcef561dd7407fbe8e19e99100d7a`
- g archive SHA-256: `47cd1823b3ccdb69fa3085381cf63ff0605f6d841fc3bc37489dce023ddc19b9`
- Extracted `ztf2g` file SHA-256: `366aaf3539f83955bb1e29799df9e63005a9eb682f4f56d0807545a3534b0f16`
- Extracted `ztf2g` size: 5,034,066,142 bytes

The archived ZIP checksum passed in the source-backed workflow. The count mismatch is therefore present in the checksum-verified archive inspected by that run; it is not explained by a failed download checksum.

## Required bounded follow-up

1. Retrieve the checksum-verified original `ztf2g.zip` and extract only rows with first-column Seq `615172`.
2. Compare the rows' RA/Dec and HJD values with the Table 2 coordinates and the time range for Seq `615170`.
3. Search the original r archive for Seq `615170`, Seq `615172`, and orphan IDs around that range.
4. Check whether other unknown Seq values match Table 2 objects by coordinates and row counts.
5. Record exact source file hashes, row counts, coordinates, and timestamps before proposing any mapping correction.

## Scientific boundary

This lead concerns archive-to-Table2 identifier integrity for a small control set. It does not explain the 11,602 candidate-only IDs, establish the publisher's selection rule, or justify changing SNR thresholds, filters, or the production selector. Keep the CPVS blocker open.
