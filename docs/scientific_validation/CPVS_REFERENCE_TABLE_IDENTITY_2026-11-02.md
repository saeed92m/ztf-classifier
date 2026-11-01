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

## 5. Required next audit

1. Acquire the original CDS fixed-width `table4.dat` for `J/ApJ/932/118` and preserve its downloaded bytes.
2. Record its byte count, retrieval URL/date, and SHA-256. Compare the physical row count with the CDS ReadMe's 730,184 records.
3. Parse the raw `ZTF` and `ID` fields according to the CDS byte schema. Keep identifiers as strings.
4. Crosswalk `ZTF` to Chen et al. (2020) Table 2 `ID`, then to Table 2 `Seq`. Validate all rows and uniqueness.
5. Compare the resulting Table 4 `Seq` set directly with the frozen Zenodo `1st_layer.csv` `SourceID` set. Do not assume equal cardinality means equal membership.
6. Compare the verified Table 4 set with a fresh candidate derivation from the exact source light curves. Retain per-object provenance for every residual.
7. Re-run the fixed 100-object and 1,000-object diagnostics after the source identities and input hashes are frozen.
8. Keep Issue #170 fail-closed until the 11,602 residuals have a source-supported explanation.

## Primary sources

- Chen et al. (2020), original CPVS paper: https://doi.org/10.3847/1538-4365/ab9cae
- CDS ReadMe for original CPVS, `J/ApJS/249/18`: https://cdsarc.cds.unistra.fr/ftp/cats/J/ApJS/249/18/ReadMe
- Chan et al. (2022), anomaly-analysis paper: https://doi.org/10.3847/1538-4357/ac69d4
- CDS ReadMe for anomaly-analysis catalog, `J/ApJ/932/118`: https://cdsarc.cds.unistra.fr/viz-bin/ReadMe/J/ApJ/932/118?format=html&tex=true
- CDS fixed-width Table 4: https://cdsarc.cds.unistra.fr/ftp/cats/J/ApJ/932/118/table4.dat

**Disposition: source-table identity is clarified; exact CPVS anomaly-sample reproduction is still UNRESOLVED / BLOCKED.**
