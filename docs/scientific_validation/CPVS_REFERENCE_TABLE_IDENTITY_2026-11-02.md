# CPVS reference-table identity clarification — 2026-11-02

## Status

**Source identity clarified. Membership discrepancy remains unresolved.**

This note prevents a naming collision between two different papers that both contain a Table 4. In this project, the 730,184-object operational reference is the **Table 4 of Chan et al. (2022)**, not the Table 4 of Chen et al. (2020).

## 1. Two different Table 4s

### Chen et al. (2020): original CPVS catalog

- Paper: *The Zwicky Transient Facility Catalog of Periodic Variable Stars*.
- DOI: https://doi.org/10.3847/1538-4365/ab9cae
- CDS catalog: `J/ApJS/249/18`.
- Table 2 / CDS `table2.dat`: the 781,602-object CPVS catalog.
- **This paper's Table 4** is the aggregate variable-purity comparison with other catalogs. It is not an object-level membership list.

### Chan et al. (2022): anomaly-analysis sample

- Paper: *Searching for Anomalies in the ZTF Catalog of Periodic Variable Stars*.
- DOI: https://doi.org/10.3847/1538-4357/ac69d4
- CDS catalog: `J/ApJ/932/118`.
- **This catalog's Table 4 / CDS `table4.dat`** contains 730,184 object-level records ranked by anomaly score in Cartesian latent space.
- CDS documents the fields `ZTF`, `ID`, `Class`, `RAdeg`, `DEdeg`, and `Score`.
- CDS describes the sample as 730,184 of the 781,602 available CPVS light curves, with at least one 2.5-sigma detection in `g` and one 3-sigma detection in `r`, respectively. The paper's Section 2 describes the same preprocessing population.

Therefore, the statement “Table 4 is not an object-level membership table” is true only for **Chen et al. (2020) Table 4**. It is false for **Chan et al. (2022) CDS Table 4**. Always identify the paper and CDS catalog when referring to Table 4.

## 2. Existing project evidence

The independent two-table audit is retained in GitHub Actions:

- Workflow run: https://github.com/saeed92m/ztf-classifier/actions/runs/40953220220
- Artifact: `cpvs-independent-two-table-audit` (artifact ID `12932850414`).
- Table 2 query: VizieR `J/ApJS/249/18/table2`, fields `ID,Seq,gmag,rmag,Per-g,Per-r`.
- Table 4 query: VizieR `J/ApJ/932/118/table4`, fields `ZTF,ID`.

The artifact records:

| Check | Result |
|---|---:|
| Table 2 rows | 781,602 |
| Unique Table 2 `Seq` values | 781,602 |
| Table 2 `Seq` range | 1–781,604 |
| Table 4 rows | 730,184 |
| Unique Table 4 catalogue IDs | 730,184 |
| Table 4 ZTF names unmapped to Table 2 | 0 |
| Published membership IDs after name-to-`Seq` crosswalk | 730,184 |
| Four-field-positive Table 2 rows | 730,239 |
| Four-field-only rows outside Table 4 membership | 55 |
| Table 4-only IDs relative to the four-field set | 0 |

The audit correctly maps Table 4 `ZTF` names to Table 2 `ID`, then to Table 2 `Seq`. It does **not** assume that Table 4 `ID` and Table 2 `Seq` are interchangeable.

### Hashes of the retained VizieR TSV responses

These hashes are for the exact TSV responses used in the independent audit. They are **not** hashes of the original CDS fixed-width `table4.dat` bytes.

| File | SHA-256 |
|---|---|
| `table2.tsv` | `c5422312ca470592d11f5a614ac6558b3665413d7806e55915e96007c90d71f4` |
| `table4.tsv` | `b5453a8659935c5323cab3bca73a92ba71fd3964803ccab9464ec601853f7460` |

The artifact's verdict is that the four-field-positive predicate is **not** the published selection rule: 55 Table 2 objects satisfy all four positivity conditions but are absent from Chan et al. (2022) Table 4.

## 3. Additional residual-population evidence

The retained historical heavy-run artifact (run [38635891449](https://github.com/saeed92m/ztf-classifier/actions/runs/38635891449)) provides additional diagnostics for the 11,602 candidate-only objects:

| Diagnostic | Candidate-only (11,602) | Published ∩ candidate (730,184) |
|---|---:|---:|
| Qualifying `g`-band detections per object, minimum | 1 | 11 |
| Qualifying `g`-band detections per object, median | 5 | 104 |
| Qualifying `g`-band detections per object, 90th percentile | 9 | 201 |
| Qualifying `r`-band detections per object, minimum | 1 | 4 |
| Qualifying `r`-band detections per object, median | 118 | 132 |

The same historical diagnostics report that 11,585 of the 11,602 candidate-only objects lack at least one Table 2 mean magnitude (`gmag` or `rmag`); the remaining 17 have both mean magnitudes but lack at least one per-band period (`Per-g` or `Per-r`). These are overlapping field diagnostics, not independent counts to add.

This pattern is consistent with an additional two-band data-completeness or fit-quality constraint in the Chan et al. (2022) preprocessing pipeline. It does **not** prove such a rule. The paper states the two-band detection thresholds but does not provide executable selection code or a complete per-object exclusion trace. Do not convert the observed field pattern into a production selector without source evidence.

## 4. Interpretation boundaries

1. Chan et al. (2022) Table 4 is the correct 730,184-row object-level reference used in this project's historical membership comparison.
2. Chen et al. (2020) Table 2 is the 781,602-row parent catalog.
3. Chan et al. (2022)'s 730,184-object preprocessing sample is not the same thing as the full original CPVS membership. It is a downstream sample selected for the two-band anomaly-analysis workflow.
4. The four-field-positive predicate is not the published selection rule. The 55-object counterexample refutes that hypothesis.
5. The historical 741,786-versus-730,184 candidate comparison and its 11,602 candidate-only IDs remain unresolved. This clarification does not explain those residuals.
6. A successful ZTF-name-to-`Seq` crosswalk validates identifier mapping. It does not prove that the local candidate derivation implements every preprocessing detail used by Chan et al. (2022).

## 5. Raw CDS acquisition and byte-level verification

The original CDS fixed-width files were acquired from the official NAOJ VizieR mirror. The primary CDS host timed out from the execution environment. The mirror archive was decompressed without changing the payload bytes. The raw files and all hashes are retained in GitHub Actions artifact `cpvs-raw-cds-reconciliation`.

- Workflow run: https://github.com/saeed92m/ztf-classifier/actions/runs/41359313403
- Artifact ID: `13104278760`
- Artifact size: 177,432,977 bytes
- Artifact contains the raw `.dat` files, compressed archives, ReadMe files, full crosswalk, residual provenance, and fixed samples.

| Source file | Bytes | SHA-256 |
|---|---:|---|
| `table2.dat` | 178,986,858 | `2c77c5b6c14811f6abab6e1442ce82c6fb54dbdcfc141954165704fecfcb3881` |
| `table4.dat` | 46,650,697 | `4fa96379d47f851db7ecd80a83986d82201e8718f12ab727b5348a3914374e7d` |
| Table 2 ReadMe | 12,990 | `e57991d9e086155b9da14eaca7a6abc46a876a2dce58b397a90c915ec309e24a` |
| Table 4 ReadMe | 7,924 | `0a7ec0dac13b155fdd63322dc9b0230de42fd05169e0e02c70f68fce0bc67d6a` |
| `table2.dat.gz` | 64,811,721 | `56dc09d5e874c3acedea887d8f928accb4c344c4f354c274edb1af6f9a62e074` |
| `table4.dat.gz` | 18,593,901 | `58a6fc4e0bc769b72ce106b3d6c7e7a26e70a580e348c8258912992390112baf` |

Sources:

- [CDS Table 2](https://cdsarc.cds.unistra.fr/ftp/cats/J/ApJS/249/18/table2.dat)
- [NAOJ mirror Table 2 archive](http://vizier.nao.ac.jp/ftp/cats/J/ApJS/249/18/table2.dat.gz)
- [CDS Table 4](https://cdsarc.cds.unistra.fr/ftp/cats/J/ApJ/932/118/table4.dat)
- [NAOJ mirror Table 4 archive](http://vizier.nao.ac.jp/ftp/cats/J/ApJ/932/118/table4.dat.gz)

The SHA-256 values are checksums calculated for this investigation. They are not publisher-supplied checksums.

### Publisher-file cross-check

The original IOP/AAS machine-readable tables were also retained and compared row by row with the CDS files:

| Comparison | Exact rows | Mismatches |
|---|---:|---:|
| Table 2 CDS vs publisher MRT | 781,602 | 0 |
| Table 4 CDS vs publisher MRT | 730,184 | 0 |

The publisher MRT records contain one extra trailing space. Some CDS Table 4 records omit trailing blank bytes. For comparison only, the in-memory CDS record was right-padded with ASCII spaces to the documented Lrecl. The source files were not changed.

- Publisher Table 2 MRT SHA-256: `58848bee4c62f5bd930787b76045e40bb695b171cc8149b4336b00b55e28d5fa`
- Publisher Table 4 MRT SHA-256: `3cb9e22c42ab19ce89346dd3773c82921d852432b4617f4ff52ce4aea2c8c7d0`

The raw Table 2 file has 781,602 records, each 228 bytes. The raw Table 4 file has 730,184 records. Its record lengths range from 59 to 63 bytes because trailing spaces are omitted. The documented Table 4 Lrecl is 63 bytes.

## 6. Verified object-level identifier crosswalk

The raw files confirm the following:

1. Table 2 has 781,602 unique ZTF names and 781,602 unique `Seq` values.
2. The documented `Seq` range is 1–781,604. The only gaps are `615171` and `615172`. These are identifier gaps, not missing catalog rows.
3. Table 4 has 730,184 unique ZTF names.
4. All 730,184 Table 4 ZTF names map to Table 2 `ID`.
5. All 730,184 Table 4 `ID` values equal the mapped Table 2 `Seq` values.
6. There are zero unmapped names and zero direct ID/Seq mismatches.

The sorted Table 4 `Seq` set has SHA-256:

`18fba7523a4f66fa2314d017433e3ef8bdbe85f1980557bc1f1e0dc61094774c`

The sorted Zenodo `1st_layer.csv` `SourceID` set has the same SHA-256. The full sets are exactly equal:

| Comparison | Count |
|---|---:|
| Table 4 membership | 730,184 |
| Zenodo membership | 730,184 |
| Table 4 only | 0 |
| Zenodo only | 0 |

This verifies the reference identity and the complete ZTF-name → Table 2 ID → Table 2 Seq crosswalk. It does not validate the candidate derivation.

## 7. Candidate comparison and fixed object samples

The raw CDS Table 4 set was compared directly with the retained historical candidate set from workflow run [38635891449](https://github.com/saeed92m/ztf-classifier/actions/runs/38635891449).

| Set | Objects |
|---|---:|
| Raw Table 4 reference | 730,184 |
| Historical reconstructed candidates | 741,786 |
| Intersection | 730,184 |
| Candidate-only | 11,602 |
| Reference-only | 0 |
| Parent neither reference nor candidate | 39,816 |

Sorted-ID hashes:

- Table 4 / Zenodo reference: `18fba7523a4f66fa2314d017433e3ef8bdbe85f1980557bc1f1e0dc61094774c`
- Historical candidate set: `4e784952ac7a41f08ae78e04415f5b1dc4e5162d38091838c8725212ea7fe9fe`
- Candidate-only residual set: `b891e2ef5a79841f23a7d4c8f5d45087280ba5de515d3f39463d9c1465286643`
- Reference-only empty set: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`

The audit generated two deterministic, stratified samples. It uses SHA-256 ranking within each stratum. It does not use a random-number generator.

| Sample | Reference and candidate | Candidate-only | Parent neither |
|---|---:|---:|---:|
| 100 objects | 50 | 25 | 25 |
| 1,000 objects | 500 | 250 | 250 |

The samples are diagnostic samples. They are not population-representative random samples.

Output files and SHA-256:

| File | Bytes | SHA-256 |
|---|---:|---|
| `table4_to_table2_seq_crosswalk.tsv` | 30,455,719 | `89d353b3b8ce24b60ab69df3e119a8e7b7832c3271fcad950cbbd743921349aa` |
| `candidate_only_11602_object_provenance.tsv` | 1,544,130 | `ea97fe7348b74a24621437f9e3bcf9b01a56c9852c64f2ebb6f0a266a4a3761a` |
| `fixed_sample_100.tsv` | 10,809 | `1f12e7674479ac8b984781f82754458acbdfd41588a84281becc122c61a64056` |
| `fixed_sample_1000.tsv` | 107,625 | `60f1514d31d8105c04725eceff95dc20d26c39748cf6c5c09764c8e42d86d9bb` |

The residual file contains all 11,602 candidate-only IDs. It includes the original ZTF name, Table 2 fields, per-band qualifying detection counts, implemented SNR results, flag diagnostics, and parent metadata. The audit reports zero missing or extra residual diagnostic records.

## 8. What the 11,602 residuals show

The historical reconstruction diagnostics report:

- All 11,602 residuals pass the implemented `g`- and `r`-band SNR checks.
- 11,470 have missing `gmag`.
- 115 have missing `rmag`.
- 11,475 have missing `Per-g`.
- 122 have missing `Per-r`.
- 17 have both mean magnitudes. All 17 lack at least one per-band period.
- 5 have both per-band periods but lack at least one mean magnitude.
- 171 have a nonzero qualifying `g`-band flag OR; 680 have a nonzero qualifying `r`-band flag OR.
- 13 have `Ng=0`; 1 has `Nr=0`.

The per-object qualifying-detection distributions are:

| Band | Minimum | Median | 90th percentile | Maximum |
|---|---:|---:|---:|---:|
| `g` | 1 | 5 | 9 | 245 |
| `r` | 1 | 118 | 180 | 1,078 |

These results do not prove the authors' selection rule. They show that the implemented two-band SNR checks alone do not explain the published 730,184-object sample.

A simple minimum of 11 qualifying `g` detections also does not explain the full residual set: 167 candidate-only objects have at least 11 qualifying `g` detections. The 55-object four-field counterexample remains. The four-field predicate is not an established published rule.

The residual pattern is consistent with an additional data-completeness, period-fit, or preprocessing constraint. This is a hypothesis, not a root-cause finding.

## 9. Remaining scientific blocker and next action

**The reference files and identifier crosswalk are now verified. Exact candidate reproduction is not.**

The remaining work is to:

1. Reproduce the candidate set from the exact 89,697,393-row-per-band light-curve inputs or the exact inputs used by Chan et al. (2022).
2. Record the source DOI, file hashes, schema, retrieval date, and processing provenance for each light-curve input.
3. Trace every candidate-only ID through the original per-band records and every selection stage.
4. Compare detection counts, photometric errors, flags, mean magnitudes, period fields, fit-quality measures, and data-availability conditions.
5. Determine the source-supported reason for each of the 11,602 exclusions.
6. Repeat the fixed 100-object and 1,000-object diagnostics against the fresh derivation.
7. Add regression tests after the root cause and exact rule are established.

Do not change the production selector, SNR thresholds, features, model, class order, or acceptance criteria before this work is complete.

Issue [#170](https://github.com/saeed92m/ztf-classifier/issues/170) remains open. PR [#244](https://github.com/saeed92m/ztf-classifier/pull/244) remains a draft. Do not merge it as a scientific fix.

## Primary sources

- Chen et al. (2020), original CPVS paper: https://doi.org/10.3847/1538-4365/ab9cae
- CDS ReadMe for original CPVS, `J/ApJS/249/18`: https://cdsarc.cds.unistra.fr/ftp/cats/J/ApJS/249/18/ReadMe
- Chan et al. (2022), anomaly-analysis paper: https://doi.org/10.3847/1538-4357/ac69d4
- CDS ReadMe for anomaly-analysis catalog, `J/ApJ/932/118`: https://cdsarc.cds.unistra.fr/viz-bin/ReadMe/J/ApJ/932/118?format=html&tex=true
- CDS fixed-width Table 4: https://cdsarc.cds.unistra.fr/ftp/cats/J/ApJ/932/118/table4.dat

**Disposition: source-table identity is clarified; exact CPVS anomaly-sample reproduction is still UNRESOLVED / BLOCKED.**
