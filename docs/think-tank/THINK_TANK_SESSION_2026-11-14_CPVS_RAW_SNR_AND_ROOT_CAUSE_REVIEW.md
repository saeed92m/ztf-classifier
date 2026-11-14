# Think Tank Session 08 — CPVS Raw SNR Evidence, Source Semantics and Root-Cause Challenge

**Session ID:** TT-2026-11-14-08  
**Date:** 2026-11-14  
**Scope:** Review the source-backed raw g/r scan of all 11,602 candidate-only CPVS IDs; challenge the current SNR interpretation; determine the next evidence needed for root cause  
**Review form:** 16 simulated specialist seats plus independent Red Team  
**Status:** Raw SNR diagnostic completed; membership discrepancy remains scientifically unresolved  
**Priority:** P0 scientific research; not a DR24-first Park MVP release gate  
**Protected baseline:** v0.2.0 unchanged  
**Execution boundary:** Standard GitHub-hosted `ubuntu-latest`; no paid or self-hosted runner; raw archives remain on runner

> This is a structured simulated 16-seat review. It does not claim that 16 external human experts attended.

## 1. Executive decision

The raw-source scan is complete for the 11,602 candidate-only objects and the fixed 100-/1,000-object samples. It does **not** establish the publisher's complete selection procedure and does **not** resolve the 11,602 discrepancy.

The leading empirical observation is that all 11,602 residual objects pass the diagnostic two-band SNR rule under all three tested formulae, while none passes the four-field-positive metadata predicate. This reproduces the Table 4 membership split for the residual set, but it does not prove that the four-field predicate was the authors' selection rule.

A second important observation is that 14 residual objects have raw archive row counts that differ from Table 2 `Ng`/`Nr`. In 13 cases Table 2 reports `Ng=0` while the g archive has rows; in one case Table 2 reports `Nr=0` while the r archive has rows. The diagnostic currently counts rows with finite, non-zero magnitudes and positive finite magnitude errors, and it reports flags without applying a flag filter. This is a material limitation. The raw archive rows may include measurements that do not qualify as detections under the catalogue's data-quality or selection rules.

**Joint decision: retain NOT_VALIDATED. Do not change the production selector, thresholds, SourceID mapping, model, feature set, taxonomy, benchmark or v0.2.0 baseline.**

## Scope boundary for the wider ZTF project

The submitted science-park proposal and technical/business plan define the product vision and prototype context. The Cosmic Intelligence Network (CIN) and collective data-generation documents define a proposed, separate human-in-the-loop subsystem. They are available as strategic context, but they are not evidence for CPVS membership selection.

For this session:
- CPVS membership and the 11,602 discrepancy are the only scientific investigation target.
- CIN remains a proposed extension; it must not alter the frozen benchmark, production model or CPVS source labels.
- Crowdsourced annotations are not ground truth and must not be used to resolve this catalog discrepancy.
- Product and institutional claims in the proposal do not replace scientific source verification.

## 2. Source-backed execution evidence

### GitHub Actions

- Raw scan workflow: [run 43463184881](https://github.com/saeed92m/ztf-classifier/actions/runs/43463184881) — completed successfully.
- Workflow revision: `479a03dbd7e39df5ff5b46d73e8cbc8fa4afc589`.
- Standard hosted runner: `ubuntu-latest`; the workflow manifest states no larger or self-hosted runner.
- The scan downloaded the pinned Zenodo archives on the runner and streamed the expanded members. It did not upload the raw archives.
- Diagnostic status in the JSON: `RAW_SNR_SAMPLE_REDERIVATION_COMPLETE`.
- Scientific status in the JSON: `NOT_VALIDATED`.

### Raw archive integrity

| Archive | Compressed bytes | SHA-256 | Expanded rows | Expanded bytes |
|---|---:|---|---:|---:|
| `ztf2g.zip` | 753,721,838 | `47cd1823b3ccdb69fa3085381cf63ff0605f6d841fc3bc37489dce023ddc19b9` | 89,697,393 | 5,034,066,142 |
| `ztf2r.zip` | 881,495,303 | `48331ba1157afc993a1399e094b97752a82d8d0f736d2fdf63fd7b2a82281b74` | 109,971,576 | 6,175,667,360 |

Both archive MD5 values, SHA-256 values, member SHA-256 values, CRC32 values, member sizes and row counts matched the pinned expectations. All parsed data rows had seven fields. No malformed rows were reported.

### Input artifact integrity

The diagnostic verified the four pinned input TSVs against the reference artifact manifest. There were:
- 11,602 candidate-only records and 11,602 unique IDs;
- 100 fixed-sample records and 100 unique IDs;
- 1,000 fixed-sample records and 1,000 unique IDs;
- 55 four-field-only controls and 55 unique IDs;
- zero within-file duplicate IDs;
- zero metadata conflicts.

Cross-file overlap is intentional because the fixed samples contain stratified objects from the candidate-only and control cohorts. It is reported separately and is not treated as a within-file duplicate.

## 3. Raw SNR results

Diagnostic thresholds:
- g band: SNR >= 2.5
- r band: SNR >= 3.0
- At least one qualifying row in each band.
- The current diagnostic requires a finite, non-zero magnitude and a positive finite magnitude error.
- Flags are counted and reported, but are **not filtered**.

Formulae evaluated independently:
1. Approximate: `1.0857362047581296 / magnitude_error`.
2. Exact magnitude-error conversion: `1 / expm1(magnitude_error * ln(10) / 2.5)`.
3. Inverse-error alternative: `1 / magnitude_error`; diagnostic only, not a physically equivalent SNR definition.

For the 11,602 candidate-only objects:
- g SNR PASS: 11,602; FAIL: 0; UNKNOWN: 0.
- r SNR PASS: 11,602; FAIL: 0; UNKNOWN: 0.
- Two-band SNR PASS: 11,602; FAIL: 0; UNKNOWN: 0.
- No formula disagreements.
- SNR-only comparison with Table 4: 11,602 false positives, 0 false negatives.
- Adding the four-field-positive diagnostic gate: 11,602 true negatives, 0 false positives, 0 false negatives in this residual-only cohort.

The approximate, exact and inverse-error formulae produced the same membership outcome for this residual cohort. This does not establish equivalence of the formulae in general.

## 4. Four-field metadata pattern

The diagnostic predicate is:

`gmag > 0 AND rmag > 0 AND Per-g > 0 AND Per-r > 0`

None of the 11,602 residual objects passes all four conditions. All 11,602 are rejected by this predicate. The 22 specifically reported cross-condition cases comprise:
- 17 objects with both mean magnitudes positive but an incomplete per-band period pair;
- 5 objects with both per-band periods positive but an incomplete mean-magnitude pair.

This is an exact empirical discriminator for this residual cohort. It is **not** evidence that Chan et al. or Chen et al. prescribed this as the membership rule. Do not convert this diagnostic into a production selector.

## 5. Historical selection ablations and the strongest new lead

The pinned heavy-run artifact `scientific-validation-heavy` from run 38635891449 contains independent ablations over the full 781,602-object parent set. These are diagnostic results, not production changes.

| Diagnostic | Candidate count | Candidate-only | Published intersection | Published-only |
|---|---:|---:|---:|---:|
| Baseline rowwise SNR | 741,786 | 11,602 | 730,184 | 0 |
| Flag < 32,768 in each band | 741,786 | 11,602 | 730,184 | 0 |
| Flag == 0 in each band | 736,225 | 11,513 | 724,712 | 5,472 |
| Add positive parent gmag and rmag | 730,201 | 17 | 730,184 | 0 |
| Exact magnitude-error SNR + positive gmag/rmag | 730,201 | 17 | 730,184 | 0 |
| Positive gmag, rmag, Per-g and Per-r | 730,184 intersection | 0 residual after intersection | 730,184 | 0 |

Full parent-set confusion counts:
- SNR candidate set alone: TP 730,184; FP 11,602; FN 0; TN 39,816.
- Four-field metadata gate alone: TP 730,184; FP 55; FN 0; TN 51,363.
- SNR candidate set AND four-field metadata gate: TP 730,184; FP 0; FN 0; TN 51,418.
The 55 four-field-only controls are UNKNOWN for two-band SNR, not FAIL. Therefore, the exact intersection is informative, but the four-field gate alone is not a sufficient membership rule.

Interpretation:
- The tested `flag < 32768` policy does not reduce the 11,602 residuals. This argues against that flag rule as the root cause.
- The completed flag-policy re-scan [run 43525513465](https://github.com/saeed92m/ztf-classifier/actions/runs/43525513465) confirms:
  - all 11,602 residuals pass under both `flag < 32768` and the literal `flag != 32768` rule;
  - no raw row in the candidate-only scan has flag value 32,768; all observed values are below 32,768;
  - in the 11,602 residual cohort, g contains 67,682 rows with flag values only 0, 1, 16, 32, 256, 4096 and 4128; r contains 1,503,643 rows with flag values only 0, 1, 4, 8, 16, 32, 48, 256, 516, 532, 4096, 4097, 4112 and 4128. The maximum observed value is 4128. Nonzero flags occur in 171 objects in g and 680 in r.
  - strict `flag == 0` leaves 11,513 residuals and rejects 89, but it is not the documented usable-epoch rule and the full-parent ablation loses 5,472 published members;
  - row-count matches remain 11,588 in g and 11,599 in r under both non-strict policies, so flags do not explain the 14 row-count mismatches;
  - the 14 mismatching objects have raw flag values 0, except SourceID 265675 with 4096; none has 32,768.
- The 55 four-field-only controls remain UNKNOWN for the two-band SNR decision: 54 have no qualifying g evidence, 4 have no qualifying r evidence, and no object is classified as a two-band SNR FAIL. Do not convert UNKNOWN to FAIL.
- Observation-count hypotheses are also insufficient on their own:
  - `Ng < 11`: 11,443 residuals.
  - `Nr < 11`: 114 residuals.
  - At least one band has fewer than 11 detections: 11,557 residuals; 45 have at least 11 in both bands.
  - At least one band has fewer than 20 detections: 11,581 residuals; 21 have at least 20 in both bands.
  - Only one residual has `Ng + Nr < 20`: SourceID `266897` (4 g + 12 r = 16). Thus Chen et al.'s stated minimum of 20 detections, if interpreted as total detections, explains at most one of the 11,602.
  A minimum of 11 or 20 points per band is not documented by the paper and does not reproduce the full split.
- The Table 2 `R2-g`/`R2-r` fields do not reproduce Table 4 membership when used as a direct global gate:
  - requiring both `R2 >= 0.4` leaves 6 candidate-only objects but excludes 204,462 published members;
  - requiring both `R2 < 0.4` selects 346 candidate-only objects and includes 20,053 published members;
  - requiring either band `R2 < 0.4` leaves 11,596 candidate-only objects but excludes 204,462 published members;
  - requiring both `R2 > 0` leaves 17 candidate-only objects and excludes 805 published members.
  The R² rule in Chen et al. (2020) therefore does not reproduce Table 4 when applied directly to these Table 2 fields as a simple membership selector. Important schema caveat: the Table 2 ReadMe labels `R2-g`/`R2-r` as R-square, while Chen et al.'s prose calls the fit statistic adjusted R². We have not established that these are the same statistic. The source-stage meaning, exact formula and logical interpretation require further investigation.
- The strict `flag == 0` policy is not acceptable: it removes 5,472 published members. Do not use it.
- Requiring both parent mean magnitudes to be positive removes 11,585 of the 11,602 residuals and leaves only 17. The published intersection remains complete.
- The exact candidate-only partition is: 11,580 objects have both field pairs incomplete; 17 have both mean magnitudes but one per-band period missing; 5 have both per-band periods but one mean magnitude missing.
- The remaining 17 have both mean magnitudes, but one of `Per-g` or `Per-r` is missing. In the original Table 2 rows, the missing band's `Per-g` or `Per-r` is the zero sentinel. Its `log(FAP)` is not uniform: 10 of the 17 have `log(FAP)=0.0`, while 7 have negative values from -2.497 to -23.842. Therefore, a missing per-band period cannot be explained by a single FAP threshold; the period-fit rejection or output rule needs investigation. The other band supplies the common `Per`. Their per-band observation counts are substantial (approximately 50–245), so simple low-count rejection does not explain these 17.
- The 17 SourceIDs are: `9877, 120746, 127012, 151010, 191955, 281946, 287003, 307249, 378719, 385223, 409233, 429716, 440167, 471637, 518053, 657950, 732333`. Each has a common `Per`, but one band-specific period is absent. The missing band's `log(FAP)` varies: 10 are 0.0 and 7 are negative (-2.497 to -23.842).
- In the missing band, the Table 2 `R2-g`/`R2-r` field is below 0.4 for 11 objects and at least 0.4 for 6. Since the ReadMe calls these R-square values and the Chen paper refers to adjusted R², this is diagnostic only; it shows that a simple 0.4 threshold on the Table 2 field does not explain all 17.
- All 17 have a common period `Per`; the missing value is the band-specific period.

The Chan et al. (2022) paper explicitly uses the color feature `m_gr = <m_g> - <m_r>` in its Isolation Forest input. This requires both mean magnitudes. Its Table 1 also lists `tau_g` and `tau_r` among the features used in the correlation analysis. This provides a source-backed reason that missing per-band mean magnitudes matter to the downstream analysis, but it does not by itself prove the full four-field gate was the authors' membership selector.

**Strongest current explanation:** the 11,602 residuals are not explained by the numeric SNR threshold or by the tested flag rule. They are strongly associated with incomplete two-band fit products in Table 2. Both mean magnitudes account for 11,585 residuals; the remaining 17 also lack one band-specific period. This is the leading mechanism, not yet a fully documented publisher rule.

## 6. Fixed sample results

| Cohort | Objects | Both-band SNR PASS | Both-band UNKNOWN | Four-field + SNR PASS |
|---|---:|---:|---:|---:|
| Fixed sample 100 | 100 | 75 | 25 | 50 |
| Fixed sample 1,000 | 1,000 | 750 | 250 | 500 |
| Four-field-only controls | 55 | 0 | 55 | 0 |

The fixed samples are stratified diagnostic samples. Pooled rates are not population prevalence estimates. Missing raw rows remain UNKNOWN, not FAIL.

## 7. New source-row-count discrepancies

The raw archive row counts were compared with Table 2 `Ng` and `Nr` for each candidate-only object. Fourteen IDs have at least one mismatch:

| SourceID | Table2 Ng/Nr | Raw g/r rows | Mismatch |
|---:|---:|---:|---|
| 153780 | 0 / 63 | 26 / 63 | g |
| 243734 | 0 / 85 | 31 / 86 | g, r |
| 245898 | 0 / 55 | 11 / 83 | g, r |
| 249760 | 0 / 54 | 12 / 54 | g |
| 255393 | 0 / 58 | 3 / 58 | g |
| 258869 | 0 / 61 | 10 / 61 | g |
| 265675 | 0 / 61 | 25 / 61 | g |
| 291558 | 0 / 50 | 17 / 50 | g |
| 312376 | 0 / 68 | 2 / 68 | g |
| 323977 | 0 / 43 | 11 / 43 | g |
| 324393 | 0 / 72 | 10 / 72 | g |
| 335151 | 0 / 55 | 9 / 55 | g |
| 339262 | 83 / 0 | 85 / 93 | g, r |
| 362478 | 0 / 87 | 12 / 87 | g |

Interpretation:
- 13 objects have `Ng=0` in Table 2 but one or more rows in the raw g archive.
- 1 object has `Nr=0` in Table 2 but 93 rows in the raw r archive.
- Several other mismatches are small count differences.
- These counts alone do not establish an identifier error. Table 2 counts may reflect a selected/quality-filtered definition, while the Zenodo files are single-exposure photometry. This must be tested against the exact source-generation and flag semantics.
- The earlier per-object heavy-run diagnostics report qualifying-row flag OR values of 0 or 4096 in g for these 14 IDs and 0 in r; none reports 32768. If the archived flag field is the same as `catflags`, this is further evidence against `catflags != 32768` explaining these particular mismatches. The flag-field equivalence is still unverified.

This is now a high-priority investigation branch. It may reveal a quality-filtering or data-lineage difference that the current SNR-only scan does not capture.

## 8. Primary-source constraints

Chen et al. (2020), Section III, describes the parent-catalogue processing: at least 20 detections; poor-quality images and photometry excluded using `INFOBITS < 33,554,432` and `catflags != 32,768`; and periodic candidates accepted if the light curve in one band met all period-search conditions. It also describes later period redetermination using photometry within 1 arcsecond of the source position.

Chan et al. (2022), Section 2.1, states that the 730,184 selected light curves contain at least one 2.5σ detection in g and one 3σ detection in r, and that both bands are phase-folded using the common period in Table 2. Section 2.3 also adds the color feature `m_gr = <m_g> - <m_r>` to the Isolation Forest input; this requires both mean magnitudes. Table 1 lists the per-band periods `tau_g` and `tau_r` among the features used for its correlation analysis. The paper does not provide a full row-level formula for the detection or explicitly state that all four Table 2 fields must be positive.

The Zenodo record for Chen et al. (2020) identifies `ztf2g` and `ztf2r` as single-exposure photometry files, with columns:
- g: `SourceID, RAdeg, DEdeg, HJD, gmag, e_gmag, g_flag`
- r: `SourceID, RAdeg, DEdeg, HJD, rmag, e_rmag, r_flag`

The same Zenodo record explicitly states that `SourceID` is the internal source identifier that joins these attachments to Table 2, and gives the example ZTFJ000000.19+320847.2 with `SourceID=3`. This makes a wholesale identifier-namespace mismatch less likely, although the project must still validate its full object-level join.
The CDS Table 4 ReadMe describes 730,184 records as all periodic variables ranked by Cartesian latent-space anomaly score. Table 4 contains only ZTF name, internal ID, class, coordinates and score; it does not publish the feature values used to select or score each object. Its stated selection description is the two-band 2.5σ/3σ detection condition. This is why the exact four-field rule must be treated as an inferred downstream completeness condition, not a directly documented Table 4 filter.

The pinned source-reconciliation report provides the full crosswalk evidence:
- Table 2: 781,602 unique `Seq` values and 781,602 unique ZTF names.
- Table 4: 730,184 unique ZTF names; zero unmapped names.
- Table 4 internal ID equals Table 2 parent `Seq` for all 730,184 records; zero mismatches.
- Table 4 and the Zenodo published-membership set match exactly; zero Table4-only and zero Zenodo-only IDs.
- The sequence range 1–781,604 has two missing values (`615171`, `615172`); this is a sequence gap, not a duplicate or a membership mismatch.
- Sorted candidate-only ID SHA-256: `b891e2ef5a79841f23a7d4c8f5d45087280ba5de515d3f39463d9c1465286643`.
- Sorted full candidate ID SHA-256: `4e784952ac7a41f08ae78e04415f5b1dc4e5162d38091838c8725212ea7fe9fe`.

The original Table 2 ReadMe marks `gmag`, `rmag`, `Per-g` and `Per-r` with `?=0`, so zero is the catalogue's missing-value sentinel for these fields. It defines `log(FAP-g)` and `log(FAP-r)` on a range ending at 0; a reported value of 0.0 is `log(FAP)=0` (FAP=1), not a zero false-alarm probability. The 17-object missing-period cohort includes both zero and negative log-FAP values. VizieR defines `Ng` and `Nr` as the number of detections in each band. The current scan counts all rows with valid magnitude/error and reports flags without filtering. It therefore does not yet reproduce Chen et al.'s stated quality cuts. The `INFOBITS` field is not present in the Zenodo archive. The exact equivalence of Zenodo `g_flag`/`r_flag` to the `catflags` named in Chen et al. must be verified before applying that criterion as a faithful reproduction. The official ZTF DR2 release notes distinguish image-level `INFOBITS < 33,554,432` from light-curve epoch-level `catflags < 32,768`; they describe `catflags=0` as a stricter, perfectly-clean extraction. Chen et al.'s literal `catflags != 32,768` is not identical to the official `catflags < 32,768` rule. The 14 Table 2/raw-row count mismatches may require image-level INFOBITS, which the Zenodo archive does not contain.

Primary sources:
- Chan et al. 2022, Section 2.1: https://doi.org/10.3847/1538-4357/ac69d4
- Chan et al. 2021 arXiv full text (same anomaly-detection methodology): https://arxiv.org/abs/2112.03306 — Sections II.1–II.3 and Table 1 describe two-band MGPR, `m_gr`, common period, and the `tau_g`/`tau_r` correlation features.
- CDS ReadMe for Chan et al. Table 4: https://cdsarc.cds.unistra.fr/viz-bin/ReadMe/J/ApJ/932/118?format=html&tex=true
- Chen et al. 2020 ZTF CPVS Zenodo record and raw-file schema: https://zenodo.org/records/3886372
- Official ZTF DR2 quality filtering: https://irsa.ipac.caltech.edu/data/ZTF/docs/releases/dr02/src/dr02.html
- VizieR Table 2 field metadata: https://vizier.cfa.harvard.edu/viz-bin/VizieR-3?-source=J%2FApJS%2F249%2F18%2Ftable2

## 9. Sixteen-seat review

| Seat | Review finding | Required action |
|---|---|---|
| 01 Chief Scientist / PI | The 11,602 discrepancy remains open. Numerical equality is not method reproduction. | Keep scientific status NOT_VALIDATED. |
| 02 ZTF survey/data specialist | The raw archives contain single-exposure measurements; Table 2 reports detection counts. Their row semantics may differ. | Establish exact archive-to-catalogue data lineage. |
| 03 Variable-star astrophysicist | A non-zero measurement is not automatically a scientifically usable detection. | Examine flags, bad measurements and period validity. |
| 04 Time-series statistician | “At least one detection” depends on the detection predicate, not just a numerical SNR threshold. | Define and test candidate row-level predicates. |
| 05 Astroinformatics engineer | The 14 count mismatches expose an untested join/quality/data-version assumption. | Produce a full per-ID row and field audit. |
| 06 Cross-match specialist | Zenodo explicitly documents SourceID as the internal identifier joining the single-exposure files to Table 2. | Preserve the documented mapping and verify it across the complete object set. |
| 07 ML scientist | No production model change is justified by this diagnostic. | Keep model and feature contract frozen. |
| 08 Scientific validation lead | The residual cohort is fully explained by the four-field predicate empirically, but not by published methodology. | Require independent full-set reconstruction. |
| 09 Software architect | Diagnostic and production selectors must remain separate. | Preserve diagnostic-only outputs and schemas. |
| 10 Backend/data pipeline engineer | The current raw scan is bounded and auditable, but its row-level evidence is too compressed for flag attribution. | Add per-ID flag and rejection summaries. |
| 11 MLOps/security lead | The raw archives were not uploaded, but the artifact included unrelated pre-existing reports because the earlier upload path targeted the whole reports directory. | Keep only five explicit evidence files in the workflow artifact. |
| 12 QA/reliability engineer | Synthetic tests validate mechanics, not the scientific interpretation of flags or the full parent set. | Add flag, row-count, UNKNOWN and identity regression tests. |
| 13 Scientific UX/documentation lead | Reports must label the raw SNR result as diagnostic and surface the 14 count mismatches. | Update the evidence report and provenance record. |
| 14 Product manager | CPVS remains a research workstream and must not block the DR24-first product MVP. | Keep research and product acceptance gates separate. |
| 15 Technical documentation lead | The exact run, hashes, formulas, caveats and next experiments must be preserved. | Maintain this session and Issue #170. |
| 16 Independent Red Team | The current script can overcount detections if flags define usability; it also assumes the candidate IDs map directly to raw archive SourceID. | Challenge both assumptions before any conclusion. |

## 10. Red Team objections

1. **Detection semantics:** The first raw SNR scan did not filter `g_flag`/`r_flag`. The expanded diagnostic now tests three candidate policies separately. None is a confirmed source rule until the field mapping to Chen et al.'s `catflags` is established.
2. **Identity semantics:** Zenodo documents SourceID as the internal identifier joining the raw attachments to Table 2. Confirm that the candidate provenance file uses this same identifier and verify the complete join; do not invent a remapping.
3. **Table 2 counts:** The 14 mismatches mean raw row count cannot be treated as equivalent to `Ng`/`Nr` without understanding the source filters.
4. **Metadata gate:** Four-field positivity exactly separates the residual cohort, but this remains a diagnostic correlation.
5. **Sample design:** The 100 and 1,000 samples are stratified and overlapping; do not interpret pooled metrics as random population estimates.
6. **Flags and errors:** The current calculation uses magnitude error and magnitude validity. It does not apply any quality-flag policy.
7. **R² semantics:** Chen et al.'s Section III refers to adjusted R², but the Table 2 ReadMe labels `R2-g`/`R2-r` as R-square. The direct field ablation does not reproduce Table 4; verify the exact statistic and processing stage before drawing a conclusion or applying a filter.
8. **Formula interpretation:** The inverse-error formula is only a diagnostic comparator. It must not be presented as an alternate physical SNR definition.
9. **Scientific independence:** Table 4 is a published membership reference, not independent astrophysical ground truth.

## 11. Required next experiments

### P0-A — Establish raw row eligibility

For each of the 14 row-count mismatch IDs and a matched control set:
- extract all raw rows for both bands;
- tabulate exact flag values and bit patterns;
- test `flag != 32768`, `flag < 32768`, and `flag == 0` as separate diagnostics;
- verify whether Zenodo `g_flag`/`r_flag` are exactly the `catflags` field described by Chen et al.;
- record that `INFOBITS < 33,554,432` cannot be tested from the current Zenodo archive because INFOBITS is not included;
- calculate SNR before and after each diagnostic flag policy;
- report positive/zero/negative/non-finite magnitude and error counts;
- compare eligible raw-row counts with Table 2 `Ng`/`Nr`;
- do not assume a flag policy is the complete published method.

### P0-B — Prove identifier semantics

- inspect the original Table 2 ReadMe and raw Zenodo schema;
- establish whether the raw `SourceID`, Table 2 `ID`/sequence and project `SourceID` are the same identifier namespace;
- verify exact equality for a broad set, including all 14 mismatches, fixed samples, and randomly selected controls;
- if any mapping is required, create a complete, hashed crosswalk with collision and missing-ID reports.

### P0-C — Reconstruct detection membership

- implement candidate row predicates as separate named diagnostics;
- compute object membership with explicit PASS/FAIL/UNKNOWN;
- compare each predicate to the 730,184 Table 4 IDs;
- quantify false positives, false negatives and unknowns;
- test the 55 four-field-only controls;
- preserve all 11,602 residual IDs.

### P0-D — Investigate the 17 remaining objects

- inspect all 17 records against the original Table 2 bytes and ReadMe;
- confirm the missing `Per-g`/`Per-r` zero sentinel and inspect the full range of missing-band `log(FAP)` values;
- determine whether the 17 were excluded because a valid per-band period was required, because MGPR failed, or because of another fit-quality condition;
- check the role of `tau_g`/`tau_r` in the published correlation analysis and whether complete-case filtering was applied before Table 4 generation;
- verify the requirement for `m_gr` using the two mean magnitudes;
- seek the authors' source code or supplementary processing details; if none exist, document the method gap rather than infer a rule.

### P0-E — Full parent reconstruction

Only after the row-eligibility and 17-object questions are resolved:
- reconstruct the complete 781,602 parent membership from pinned sources;
- compare object-level IDs with Table 4;
- verify duplicate handling, identifier mapping, source hashes and full confusion counts;
- record exact commands and intermediate artifacts.

### P0-F — MGPR readiness, separate from membership

Do not infer MGPR readiness from catalogue membership. Evaluate the common period, per-band coverage, usable measurements, phase coverage, error behavior, numerical conditioning and convergence in a separate gate.

## 12. Workflow and CI note

A later push produced standard CI run [43474444378](https://github.com/saeed92m/ztf-classifier/actions/runs/43474444378), not a fresh raw-SNR scan. Six engineering jobs passed. Dependency Audit failed because `soupsieve 2.10` was reported with three vulnerabilities (CVE-2026-126190, CVE-2026-126193, CVE-2026-126191); the CI Gate therefore failed. This is a separate dependency-security issue, not evidence against the raw-SNR result.

The first raw-SNR run 43463184881 uploaded the entire `reports/` directory and included unrelated historical reports and tables; it did not upload raw g/r archives. The workflow now uses a five-file allowlist, and the completed follow-up run 43525513465 verifies that boundary.
The flag-policy scan [run 43525513465](https://github.com/saeed92m/ztf-classifier/actions/runs/43525513465) completed successfully. Setup, synthetic regression tests, pinned-input retrieval, both checksum-pinned archive downloads, raw scan and artifact upload all passed. Its artifact (ID 14085318178, SHA-256 `198ad0becaae7cc752e34fd34ae6e269ae49a73b255afc6a3773d651f26e6088`) contains exactly five allowlisted files; no unrelated reports or raw archives were uploaded. The artifact contains 7,074,893 uncompressed bytes and expires 2026-11-27.
On the current documentation head `e40ed37`, standard CI (runs 43527887971 and 43527880965), Scientific Validation (43527887940), CodeQL (43527888110) and Product Scope Audit (43527887953) are in progress. No fresh green CI result is claimed.

## 13. Joint decision and current status

### Verified
- Parent Table 2: **781,602 unique Seq values and 781,602 unique ZTF names**. The range 1–781,604 has only two absent sequence values (615171 and 615172); there are no duplicate Seq values.
- Table 4: **730,184 unique ZTF names**. All map to Table 2; zero unmapped names and zero duplicate names.
- Table 4's internal ID equals the matched Table 2 Seq for all 730,184 records. The published Table 4 membership and the retained Zenodo membership reference agree exactly.
- Historical full-parent comparison: 741,786 reconstructed candidates; 730,184 intersection; 11,602 candidate-only; zero published-only.
- Exact four-field diagnostic conjunction `gmag>0 AND rmag>0 AND Per-g>0 AND Per-r>0` reproduces the Table 4 split on the retained historical parent artifact. This establishes an empirical discriminator for that pinned revision, not the publisher's documented selector.
- Residual partition: **11,580** fail both the two-mean-magnitude pair and the two-band-period pair; **17** have both mean magnitudes but one missing band-specific period; **5** have both band-specific periods but a missing g-band mean magnitude. None passes all four conditions.
- For the 17 objects, all retain the common `Per` used by Chan et al. to phase-fold both bands. Their missing-band `log(FAP)` values are mixed: 10 are 0.0 and 7 are negative. One FAP threshold does not explain these missing periods.
- Both `gmag` and `rmag` are required to calculate Chan et al.'s `m_gr` colour feature. The paper uses the common period `Per` for two-band phase folding. The paper does not explicitly say that both band-specific periods `Per-g` and `Per-r` were membership gates.
- A minimum detection count is not the root cause: 45 residual objects have `Ng,Nr>=11`; 21 have at least 20 in each band; only one has fewer than 20 detections in total.
- The Table 2 fields `R2-g` and `R2-r` cannot be used as direct membership gates. Their published ReadMe labels them R-square, while Chen et al. describe an adjusted-R² criterion. The attempted direct Table 2 ablations also remove many published members.
- The broad ID/Seq/Table 4 crosswalk is verified. A general identifier namespace mismatch is not a credible explanation for the 11,602 residuals.

### Fresh raw-source flag-policy scan
- GitHub Actions run: [43525513465](https://github.com/saeed92m/ztf-classifier/actions/runs/43525513465).
- Runner: standard GitHub-hosted `ubuntu-latest`; no paid, larger or self-hosted runner.
- Commit: `451680f94a06303f99b6ea9fd92bda95a784a6d5`.
- Both checksum-pinned Zenodo raw archives passed archive/member hashes, CRC, size and row-count validation.
- All 11,602 residual IDs passed the two-band SNR test under the approximate, exact and inverse-error diagnostic calculations.
- The `flag < 32768` and literal `flag != 32768` policies did not change the residual membership: 11,602 remained two-band PASS.
- The stricter `flag == 0` policy reduced the residual PASS count to 11,513 (89 residual IDs removed). In the full-parent ablation, this strict rule also excluded 5,472 published Table 4 members. It is therefore not a valid reconstruction rule.
- The Zenodo columns are named `g_flag` and `r_flag`. Their exact equivalence to Chen et al.'s `catflags` field has not been proven. ZTF DR2 documentation defines `catflags<32768` as the ordinary epoch-quality condition and `catflags=0` as stricter. Do not silently equate the Zenodo field names with `catflags`.
- The raw archive row counts disagree with Table 2 `Ng/Nr` for 14 residual IDs: 13 have Table 2 `Ng=0` but raw g rows; one has `Nr=0` but raw r rows. These rows have tested flag values below 32768, so the tested flag policies do not explain the mismatch. Image-level `INFOBITS` is not present in the Zenodo attachment files.
- The artifact boundary is verified. Artifact ID `14085318178` has exactly five allowlisted evidence files (runner manifest, archive sizes, archive hashes, JSON report and object-level TSV), 937,297 compressed bytes and no raw archives or unrelated reports. Artifact SHA-256: `198ad0becaae7cc752e34fd34ae6e269ae49a73b255afc6a3773d651f26e6088`. It expires 2026-11-27.

### Interpretation
The strongest explanation is now a **downstream two-band fit/feature-completeness condition**. The reconstructed residuals do not fail the tested SNR thresholds. The vast majority lack one or more required fitted metadata values. Both mean magnitudes are needed for the published colour feature. The remaining 17 lack one per-band period output, but keep the common period.

This is a strong, source-consistent explanation of the observed partition. It is not yet proof of the authors' complete processing logic. The paper's short Section 2.1 description does not state the full four-field conjunction. The 17-object exclusion mechanism is still unexplained. The 14 row-count mismatches are a separate data-lineage and quality question.

### Current state
- Raw archive integrity: **VERIFIED**.
- 11,602-object raw SNR scan: **COMPLETED**.
- Tested flag-policy ablation: **COMPLETED; no explanation for the main residual cohort**.
- Five-file artifact allowlist: **VERIFIED**.
- Exact Table 2 / Table 4 / Zenodo membership crosswalk: **VERIFIED**.
- Four-field diagnostic as an empirical discriminator: **VERIFIED ON THE PINNED HISTORICAL PARENT ARTIFACT**.
- Four-field conjunction as the publisher's documented membership rule: **NOT ESTABLISHED**.
- 14 raw archive / Table 2 row-count discrepancies: **OPEN**.
- Exact `g_flag/r_flag` to `catflags` equivalence and image-level `INFOBITS` attribution: **OPEN**.
- 17-object exclusion mechanism: **OPEN**.
- Independent reproduction of the full Chan et al. preprocessing and MGPR output: **NOT PERFORMED**.
- Scientific validation: **NOT_VALIDATED**.
- Production selector, thresholds, model, features, taxonomy, benchmark and v0.2.0 baseline: **UNCHANGED**.
- Issue #170: **KEEP OPEN**.
- PR #285: **KEEP DRAFT; DO NOT MERGE ON THIS EVIDENCE ALONE**.

## 14. Next experiments — priority order

### P0-A — Reproduce the 17-object path
- Use the 17 fixed SourceIDs listed in Section 5.
- Retrieve their exact two-band raw observations and use the common Table 2 `Per` to phase-fold both bands, as Chan et al. describe.
- Run the published MGPR form and generate both 160-point interpolated bands.
- Compare convergence, covariance conditioning, phase coverage, finite outputs and physical plausibility against matched Table 4 members of the same variable types and similar magnitude/cadence.
- Determine whether the 17 fail MGPR or whether they can be processed normally. A successful MGPR run would reject MGPR failure as their explanation.
- Keep MGPR readiness separate from CPVS membership.

### P0-B — Reconstruct the missing two-band fit products
- For the 11,580 objects that fail both metadata pairs and the 5 objects with both periods but missing g mean magnitude, compare `Ng/Nr`, `R2-g/R2-r`, amplitudes, `log(FAP-g/r)`, period values and raw observation coverage.
- Verify the precise definitions of zero sentinels, fit failures and adjusted R² in the original Chen et al. Table 2 bytes and ReadMe.
- Do not use Table 2 R² values as a proxy for adjusted R² until the equations and processing stage match.

### P0-C — Resolve the 14 row-count mismatches
- Preserve the 14 SourceIDs in the audit report.
- Verify the lineage of `g_flag/r_flag`, `catflags`, and image-level `INFOBITS`.
- If required, resolve the raw exposures to the official DR2 image metadata. The Zenodo attachments alone do not contain `INFOBITS`.
- Compare row eligibility and counts with Table 2 `Ng/Nr` without inventing missing values or remapping IDs.

### P0-D — Obtain independent method evidence
- Search for a public author implementation or supplementary processing notes.
- If no implementation is available, request clarification from the authors on the 730,184 sample construction and the reason for the 17 omissions.
- If the historical rule cannot be confirmed, document the exact method gap. Do not convert an empirical match into a claimed reproduction.

### P0-E — Final scientific acceptance
- Reconstruct the complete 781,602 parent set from pinned source inputs after row eligibility and two-band fit requirements are specified.
- Compare all object-level IDs to the exact Table 4 IDs. Report false positives, false negatives and UNKNOWN objects.
- Retain the fixed 100-object and 1,000-object diagnostics and the 55 four-field-only controls.
- Add regression tests for the verified rule only after independent evidence establishes it.
- Keep all production and v0.2.0 artifacts unchanged until scientific acceptance passes.


## 15. Primary-source method reconciliation and current ordered decision — 2026-11-14

### Primary-source facts now checked

**Chen et al. (2020), Section III** states that their original CPVS discovery pipeline:
1. starts with objects with at least 20 detections;
2. filters image quality with `INFOBITS < 33,554,432` and epoch photometry with `catflags != 32,768`;
3. performs initial period searches on observations associated with the same internal product ID;
4. accepts a periodic candidate when the light curve in **one** band meets all period-search conditions;
5. redetermines the period using photometry within 1 arcsecond of the source position;
6. fits a fourth-order Fourier model;
7. excludes poorly fitted light curves using the adjusted-R² condition stated as `R_g^2 < 0.4` and `R_r^2 < 0.4`;
8. applies additional alias exclusions.

Source: https://arxiv.org/abs/2005.08662

**Chan et al. (2022), Section 2.1** states that the 730,184 selected light curves have at least one 2.5σ g-band detection and one 3σ r-band detection. Both bands are phase-folded with the common Table 2 period. The paper then applies multivariate Gaussian-process regression in normalized phase/wavelength space.

Source: https://doi.org/10.3847/1538-4357/ac69d4

The Chan paper's stated two-band SNR condition is therefore not a complete description of the original Chen catalogue-construction pipeline. The papers describe different processing stages. Do not merge the two stages into one undocumented selector.

### Important diagnostic correction: the R² rule

The Chen text describes rejection when **both** band-specific adjusted-R² values are below 0.4. The direct Table 2 ablation was re-evaluated with that logical interpretation:

- Retain objects unless both Table 2 `R2-g` and `R2-r` are below 0.4.
- Result: 721,387 reconstructed candidates; 11,256 candidate-only; 20,053 published-only.

This does not reproduce Table 4 membership. The Table 2 ReadMe calls the fields “R-square”, while Chen et al. call the fitted statistic “adjusted R²”. Their exact mathematical equivalence and processing stage remain unverified. Do not treat these columns as a faithful adjusted-R² implementation until the formula is established.

The simple 20-detection threshold also does not explain the residual cohort: 21 residual objects have at least 20 detections in each band; only one has fewer than 20 detections in total.

### Current best interpretation

The 11,602 excess objects are not explained by:
- the tested approximate or exact magnitude-error-to-SNR formula;
- the tested `flag < 32768` or literal `flag != 32768` rule on the Zenodo flag values;
- a simple 11-per-band or 20-per-band observation-count threshold;
- a broad Table 2 Seq / Table 4 ID crosswalk error.

The strongest empirical separator remains the two-band metadata-completeness conjunction. Both mean magnitudes explain 11,585 residuals; the remaining 17 have both mean magnitudes and the common period, but lack one band-specific period. Five more objects have both band-specific periods but lack a mean magnitude. This points to a downstream fit/feature-completeness difference, but the papers do not explicitly prescribe the four-field conjunction as Table 4 membership logic.

The 14 raw-archive/Table 2 `Ng/Nr` mismatches remain separate. The Zenodo attachment's `g_flag/r_flag` names have not been proven identical to `catflags`, and image-level `INFOBITS` is absent from those attachments. The tested flag values are all below 32,768; no raw row had value 32,768. This does not test the image-level quality cut.

### Ordered Think Tank decision

1. **Lock the historical reference and source semantics.** Keep the exact Table 2, Table 4, Zenodo and current candidate hashes. Maintain the validated ID crosswalk. Do not regenerate or remap IDs.
2. **Reconstruct the original Chen pipeline in order.** Test the 20-detection rule after quality eligibility; establish the field mapping for `catflags`; resolve image `INFOBITS`; reproduce same-product-ID period search, one-band acceptance, 1-arcsecond period redetermination, fourth-order Fourier fitting, the exact adjusted-R² formula/logic and alias cuts. Record membership after every stage.
3. **Resolve raw-row provenance.** Explain all 14 `Ng/Nr` mismatches and test raw-row eligibility for the full residual list, not only these 14 examples. Preserve missing image metadata as UNKNOWN.
4. **Investigate the 42-object diagnostic cohort.** It contains all 17 two-mean-magnitude/period-incomplete objects, all 5 two-period/magnitude-incomplete objects, 10 fixed objects from each dominant one-band fit-output stratum, and 42 nearest same-Type Table 4 controls. Compare shared-period phase coverage, point counts and quality/SNR distributions in each band.
5. **Run MGPR only after the phase-fold audit passes.** Use the Chan paper's common period in both bands. Compare all residual cases with matched Table 4 controls. Record optimizer convergence, kernel/hyperparameter values, covariance conditioning, phase coverage and 160-point outputs. MGPR success or failure is not itself catalogue-membership proof.
6. **Perform the full 781,602-object reconstruction.** Compare object IDs against the pinned 730,184 Table 4 set at every source-backed processing stage. Report TP, FP, FN, UNKNOWN, duplicates, missing IDs and stage-level hashes.
7. **Change production only after independent method evidence.** If the historical logic cannot be established from public sources or an author implementation, preserve the method gap. Do not infer a filter from a matching count. Keep issue #170 open and PR #285 Draft.

### New diagnostic implementation and CI state

- Added `scripts/diagnose_cpvs_phasefold_coverage.py` and `tests/test_cpvs_phasefold_coverage.py`.
- Added workflow `.github/workflows/cpvs-17-phasefold-coverage.yml`, restricted to standard `ubuntu-latest`; no paid or self-hosted runner.
- The three historical inputs are now SHA-256 pinned:
  - parent metadata: `3675b1274f73fcb15d47e7a780f194ef8fa335cd248c6ff53ea4f01559c86591`;
  - selected IDs: `699ff34bcf8dd4b5043eed48384973cb5109fd86ca260f831a502097370238df`;
  - selection diagnostics: `7e763d8804a57d75d1633d0a4089a4a6ac5aa40bb4695964d35e645b67ad5b61`.
- The first test run was blocked by a historical-artifact download credential error. The subsequent run retrieved the artifact and began the raw Zenodo archive download. That earlier attempt used a flawed circular-phase test fixture and is not accepted as a successful diagnostic.
- The fixture was corrected. The workflow now uses `github.token` with `actions: read`. Corrected run [43530167582](https://github.com/saeed92m/ztf-classifier/actions/runs/43530167582) is queued behind the earlier attempt. No phase-coverage result or MGPR result is accepted yet.
- On current PR head `737b387ec62726f0ec78898b80d416a62e65dedd`, CodeQL and Product Scope Audit passed. Standard CI and Scientific Validation are still running. The separate earlier Dependency Audit failure involving `soupsieve 2.10` remains to be checked on the latest head.

### Current decision

**ROOT CAUSE: NOT PROVEN. SCIENTIFIC VALIDATION: NOT_VALIDATED.**

Leading explanation: a difference in the completeness/eligibility of two-band fitted products or later feature preparation, beyond the published two-band SNR statement. The next action is the ordered source-pipeline reconstruction above, beginning with the exact Chen quality/period/Fourier stages and the 14 raw-row mismatches. The 42-object shared-period phase-fold diagnostic is a supporting test, not a substitute for that reconstruction.

No production selector, thresholds, ID mapping, model, feature schema, taxonomy, benchmark, release artifact or v0.2.0 baseline has changed.


## 16. Zenodo flag schema, official ZTF quality levels, and phase-fold repair — 2026-11-14

### Source-backed field definitions

The Zenodo record for the CPVS supplementary data explicitly says that the two raw attachments contain:

- `ztf2g`: `SourceID, RAdeg, DEdeg, HJD, gmag, e_gmag, g_flag`;
- `ztf2r`: `SourceID, RAdeg, DEdeg, HJD, rmag, e_rmag, r_flag`.

It also states that `SourceID` joins these files to Table 2. The record does **not** define `g_flag/r_flag` as the ZTF DR2 `catflags` field. Therefore the field-name similarity is not evidence of exact semantic equivalence.

Source: https://zenodo.org/records/3886372

The official ZTF DR2 documentation distinguishes two quality levels:

- `INFOBITS < 33,554,432`: image/catalog-level quality, stored in archive image metadata;
- `catflags < 32,768`: epoch-level light-curve quality;
- `catflags = 0`: a stricter optional requirement for perfectly clean measurements.

The Chen paper's literal `catflags != 32,768` condition is not identical to the official documentation's `catflags < 32,768` recommendation. Keep the paper's stated predicate and the archive's recommended predicate as separate tests until the source implementation is reproduced.

Source: https://irsa.ipac.caltech.edu/data/ZTF/docs/releases/dr02/src/dr02.html

### Consequences for the 11,602 residuals

1. The checksum-pinned Zenodo supplement supplies per-epoch flag columns, but it does not supply image-level `INFOBITS`.
2. The raw scan found no flag value equal to 32,768, and every observed flag value was below 32,768. This means the tested `< 32768` and `!= 32768` predicates produce the same result on the scanned values. It does **not** prove that the Zenodo fields are `catflags`.
3. The scan cannot validate the image-level `INFOBITS` cut. A row-level flag test cannot replace it.
4. The 14 raw-archive/`Ng/Nr` count mismatches remain unresolved. Their investigation requires a trace from each `SourceID` and epoch (`HJD`, position, filter and photometry) to the historical DR2 image/catalog metadata. Preserve missing image metadata as UNKNOWN.

### Phase-fold workflow repair

The earlier phase-fold workflow failed while Python's `ZipExtFile` checked the CRC for the multi-gigabyte `ztf2g` ZIP64 member. The same immutable archives had already passed the complete repository raw scan through Info-ZIP streaming and independent byte-level integrity checks.

The phase-fold scanner now uses the same streaming approach:

- read the archive with `unzip -p`;
- verify the archive SHA-256;
- verify the member SHA-256, decompressed byte count, row count, central-directory CRC and streamed CRC;
- reject malformed rows and non-zero extractor exit codes;
- add a deterministic small-ZIP regression test for stream extraction and integrity checks.

The scanner remains diagnostic only. It does not run MGPR and does not change CPVS membership.

Latest relevant evidence:
- the previous raw SNR evidence workflow passed on run [43525513465](https://github.com/saeed92m/ztf-classifier/actions/runs/43525513465);
- phase-fold code repair is committed on the research branch;
- the first rerun using the new streaming code is still in progress; no phase-coverage report has been accepted;
- the test suite's first post-repair CI run found one unused test import. That import was removed. The rerun on commit `fe76e90f8b0ea44f8b56ed14275deba7f4c07f1b` is still in progress;
- CodeQL, Product Scope Audit and the Scientific Validation contract passed on the earlier current branch head. Those checks do not validate phase coverage or resolve the scientific discrepancy.

### Decision carried forward

**The CPVS root cause remains NOT PROVEN.** Do not interpret the four-field metadata match as the publisher's rule. Do not apply a new flag or image-quality filter to production. Next, finish the 42-object phase-coverage diagnostic, then decide whether MGPR is warranted. In parallel, map the Zenodo flags to original DR2 `catflags` and recover image-level `INFOBITS` for the 14 count-mismatch objects. Keep PR #285 Draft, issue #170 open, and v0.2.0 unchanged.


## 17. Shared-period phase coverage and Table 6 overlap results — 2026-11-14

### Phase-fold coverage diagnostic

Workflow run [43535760220](https://github.com/saeed92m/ztf-classifier/actions/runs/43535760220) completed successfully on revision `2d31d08e9d12ad6535ab49ca26008dcc0d630fc1`. The report covers 42 candidate-only residual objects (all 17 both-magnitude / incomplete-band-period cases, all 5 both-period / missing-magnitude cases, and two fixed 10-object strata) plus 42 matched Table 4 controls. It uses the common Table 2 period, separately folds g and r, counts occupied bins on a 160-bin phase grid, and records circular phase gaps.

Verified archive checks in the report:
- g archive SHA-256: `47cd1823b3ccdb69fa3085381cf63ff0605f6d841fc3bc37489dce023ddc19b9`; member SHA-256: `366aaf3539f83955bb1e29799df9e63005a9eb682f4f56d0807545a3534b0f16`; 89,697,393 rows.
- r archive SHA-256: `48331ba1157afc993a1399e094b97752a82d8d0f736d2fdf63fd7b2a82281b74`; member SHA-256: `78df6d0b22099a7e5c6e74b897682c6ab94f90d5f9e887d4b0b3b152514e50fe`; 109,971,576 rows.
- The report records zero raw/Table 2 count mismatches among these 84 selected objects. This is not a full-residual count reconciliation.

Cohort-level medians:
- 17 residuals with both g/r mean magnitudes but at least one missing band-specific period: g 92/160 bins (57.5%); r 91/160 (56.9%). Their g/r median largest circular gaps are 0.0587 and 0.0756.
- 5 residuals with both band-specific periods but incomplete mean-magnitude pair: g 9/160 bins (5.6%); r 77/160 (48.1%). Their median g/r largest gaps are 0.3326 and 0.0679.
- Fixed 10-object g-fit-missing stratum: median g 4.5/160 bins (2.8%) versus r 82/160 (51.3%).
- Fixed 10-object r-fit-missing stratum: median r 4/160 bins (2.5%) versus g 35.5/160 (22.2%).
- The 42 matched controls have median g 43/160 bins (26.9%) and r 76.5/160 (47.8%). They are same-Type nearest matches on period, magnitudes and observation counts, not a random control sample.

Interpretation:
1. The 5 objects with incomplete mean magnitudes have very sparse g-band phase coverage (6–12 valid g observations; median 11). This supports a band-specific data-completeness explanation for those objects.
2. The fixed 10-object missing-fit strata also have very sparse phase coverage in the corresponding band. This supports the same mechanism for those sampled objects.
3. The 17 objects with both mean magnitudes and a missing `Per-g` or `Per-r` have substantial shared-period coverage in both bands. Their median coverage is close to that of their 17 matched Table 4 controls. Sparse shared-period coverage is therefore not a sufficient explanation for this 17-object subgroup.
4. The phase-fold run did not execute MGPR. Phase coverage does not prove Gaussian-process convergence, interpolation quality, original CPVS membership, or the historical selection rule.

The compact report has SHA-256 `6094a9fcee0d37c3cbf42e7b6d97aee5f791cd5adea81fa67d38553295ebd47a`; the object-level TSV has SHA-256 `a6f6f83be18809b8c3d3cc1068f4ef6463ec84771bd30883505de0c91a800bb6`. The downloaded evidence archive is SHA-256 `424f5bd03a0a4f43956901459209527eaa03be0611acf77657c3caf71267b76d`.

A rerun on the corrected streaming-scanner revision remains in progress. Do not treat that pending run as an additional validation result. The completed report remains bounded to the stated 84 objects.

### Table 6 suspected-variable catalogue overlap

Workflow run [43538253256](https://github.com/saeed92m/ztf-classifier/actions/runs/43538253256) completed successfully on revision `ddd4f12e78da805d915792e49ac687aa870030b0`.

Input and integrity evidence:
- Zenodo archive `Table6.txt.zip` MD5: `fcad26b036c8dbee29f6d868fecc9697`.
- Decompressed member `Table6.txt`: 167,166,038 bytes; SHA-256 `f1b51a6be353d8712eba626e12c57bb3c5b0900c2435210f088d65f9db32c6af`; CRC32 `4f18f13d`.
- 1,381,527 records, 1,381,527 unique IDs, 13 fields per record, zero duplicate IDs.
- The pinned residual evidence artifact came from run `43525513465` and has SHA-256 `198ad0becaae7cc752e34fd34ae6e269ae49a73b255afc6a3773d651f26e6088`.

Object-level result:
- 11,602 candidate-only residuals, 11,602 unique SourceIDs and 11,602 unique ZTF names.
- Table 6 overlap: **0**.
- Table 6 non-overlap: **11,602**.
- Overlap fraction: **0.0**.
- The overlap TSV contains only its header; no residual ID matched Table 6.
- The overlap result is also zero within each tested metadata stratum: the 17 both-magnitude objects, the 5 both-period objects, and the 11,580 objects failing both pairs.

Interpretation:
- The residual set is not explained by these objects being listed in the published suspected-variable catalogue.
- Table 6 is a separate catalogue, not the primary Table 2 variables membership list. Zero overlap rules out this specific cross-catalogue explanation only.
- Do not use Table 6 as a production membership filter. The original Chen/Chan selection stages remain to be reconstructed.

The report JSON has SHA-256 `b5a1eafd7b99d95dc31b627f9132a775d0ef9fc71efd62052a5b74b64ab2c28e`; the overlap TSV has SHA-256 `b3fb177880fb8530a1188c79474ca163725d52dca89158aba87b55de7bdad13d`; the downloaded evidence archive has SHA-256 `687dde745d22212dfe74e05cf604b16738aeb566aa356ee69eb186a19b0ec743`.

### Current decisions

- **CPVS root cause remains NOT PROVEN.** The Table 6 hypothesis is rejected for the 11,602 residuals. The phase-fold results support per-band data sparsity for some strata but do not explain the 17 objects with both mean magnitudes and good shared-period coverage.
- Next scientific experiment: obtain the exact MGPR implementation details and run a bounded, deterministic MGPR diagnostic on the 17-object subgroup and matched Table 4 controls. Record convergence, hyperparameters, covariance conditioning, optimizer behavior and output-grid stability. Do not infer catalogue membership from a successful fit alone.
- Continue resolving Zenodo `g_flag/r_flag` to original DR2 `catflags`, recover image-level `INFOBITS`, and trace the 14 raw/Table 2 count mismatches.
- Complete the full 781,602-parent reconstruction and the TP/FP/FN/UNKNOWN comparison only after all selector stages are source-backed.
- Preserve PR #285 Draft, issue #170 Open and v0.2.0. No production selector, model or release change is authorized by these diagnostic results.


## 18. MGPR feasibility experiment — method reconstruction and execution plan (2026-11-14)

### Primary-source method recovered

The published Chan et al. (2022) Section 2.1 gives a sufficiently detailed mathematical and procedural description to design a bounded feasibility experiment. It does not provide a complete executable reference implementation or all numerical optimizer settings.

Source: [Chan et al. 2022, ApJ 932, 118](https://doi.org/10.3847/1538-4357/ac69d4), also [arXiv:2112.03306](https://arxiv.org/abs/2112.03306).

The paper specifies:
1. Use the common period from Chen et al. Table 2 to phase-fold both g and r observations: \(\phi=(t/\tau)-\lfloor t/\tau\rfloor\).
2. Normalize wavelength to a two-filter coordinate.
3. Use a zero mean function.
4. Use a separable radial-basis covariance in phase and wavelength, multiplied by a constant amplitude, plus diagonal white noise:
   \[
   K(\mathbf r,\mathbf r') =
   C\exp\left(-\frac{(\Delta\phi)^2}{l_\phi^2}\right)
   \exp\left(-\frac{(\Delta\lambda)^2}{l_\lambda^2}\right)
   +\delta\,\mathbb{1}_{\mathbf r=\mathbf r'}.
   \]
5. Optimize \(l_\phi,l_\lambda,C,\delta\) against the negative log likelihood using SciPy L-BFGS-B and George.
6. Repeat the phase-folded observations twice, producing phase coordinates over [0,3], then use the [2,3] interval as the periodic output.
7. Generate 160 evenly spaced values per band.
8. Standardize each band independently and scale its magnitude errors by the same standard deviation.

The article does not state the exact George version, optimizer bounds, initial parameter values, or full treatment of measurement uncertainties in the likelihood. We must not invent these as published facts.

### Why the next cohort is 17 + 17

The 17 residuals with both positive mean magnitudes but one missing band-specific period have:
- common Table 2 period available for all 17;
- median phase coverage of 92/160 bins in g and 91/160 in r;
- phase coverage close to their 17 matched Table 4 controls.

This makes them a useful cohort for testing whether the missing per-band period prevents the downstream common-period MGPR interpolation. It does not imply that Chan used Per-g or Per-r as eligibility requirements.

### Bounded diagnostic implementation

The research-only implementation is:
- scripts/diagnose_cpvs_mgpr.py
- tests/test_cpvs_mgpr.py
- .github/workflows/cpvs-mgpr-feasibility.yml
- lifecycle record configs/process/cycles/cpvs-mgpr-feasibility-20261114.json

It uses:
- all 17 residuals and their 17 deterministic same-Type Table 4 controls;
- the pinned raw Zenodo g/r archives and historical parent artifact;
- george==0.4.4 in an isolated GitHub-hosted research runner only; this is not added to production dependencies;
- common Table 2 period, phase repetition over three cycles, normalized two-filter coordinate (g=0, r=1), zero mean, separable RBF, constant amplitude and fitted diagonal white noise;
- per-band StandardScaler-style normalization and scaled measurement errors;
- two deterministic optimizer starts and explicit log-space bounds.

The starts and bounds are analyst-selected reproducibility controls because the paper does not publish those values. The script records them in the report. It also records optimizer status, negative log likelihood, fitted kernel parameters, white-noise variance, covariance condition number, predictive uncertainty and the fraction of predictions outside the observed magnitude range.

No flag predicate is assumed in this MGPR feasibility run. Zenodo g_flag/r_flag has not been proven equivalent to original DR2 catflags. The input uses rows that pass the explicit numeric validity checks in the scanner. This is a feasibility test, not an exact reconstruction of the publisher's pipeline.

### Acceptance and interpretation rules

- A finite GP prediction is not a membership decision.
- Optimizer success alone is not enough. Check likelihood, fitted parameters, covariance conditioning, uncertainty and physical plausibility.
- Compare residuals with matched controls under the same implementation and input policy.
- If results depend strongly on starts or bounds, report instability. Do not select a favorable run.
- If MGPR works for the 17 residuals, this only shows that a missing band-specific Fourier period is not, by itself, a computational barrier to the Chan preprocessing.
- If MGPR fails for the residuals but succeeds for matched controls, investigate data/flag eligibility and numerical conditioning. This still does not prove the official selection rule.
- Keep the 11,602-object CPVS discrepancy NOT PROVEN until original selector stages and full-parent object-level comparison are reconstructed.

### Current execution status

The MGPR workflow and regression tests have been committed to the research branch. CI and the bounded scientific run are pending. No MGPR result is claimed yet.


## 18. MGPR feasibility execution and CI repair — 2026-11-14

### First MGPR attempt

Workflow run [43598133000](https://github.com/saeed92m/ztf-classifier/actions/runs/43598133000) completed with failure after:
- Pinned research runtime installation passed.
- Full-parent evidence download passed.
- Both raw Zenodo archive downloads and SHA-256 checks passed.
- MGPR preparation unit tests passed.
- The scientific fit did not start. The script failed at import time with `ModuleNotFoundError: No module named 'scripts'`.

This is an execution/import-path defect, not an MGPR numerical result. No object-level fit or interpolation result was produced. The run is not evidence for or against MGPR feasibility.

### Corrective change

Commit `589f23b234a041f64ad3a32e26ed6c8079b65f7e` updates the research-only MGPR script to support both package-relative import (unit tests) and direct script execution (GitHub Actions). It does not change the kernel, input selection, optimizer, thresholds or scientific baseline.

The corrected MGPR workflow run `43598776355` is pending. The earlier run `43598692569` was created before the import-path correction and must not be counted as validation of the corrected script.

### CI lint repair

The first CI run on commit `0db1079555b8cd719b4089813d37769b2bbe6f9b` failed Ruff lint because `tests/test_cpvs_mgpr.py` created an unused RNG variable. Commit `9576a5ad1da317c35d80a440b3e59eb3517b5617` removes that unused variable. The format check passed on the earlier attempt; its later CI run was cancelled by a newer push before the remaining gates completed.

The corrected CI run on commit `589f23b234a041f64ad3a32e26ed6c8079b65f7e` is pending. No complete CI pass is claimed.

### Current gate and decision

- MGPR feasibility: **PENDING** on corrected import-path revision; previous attempt failed before fitting.
- CI: **PENDING** on corrected lint/import revision; full gate has not passed.
- CPVS membership root cause: **NOT PROVEN**.
- No production selector, model, feature schema, benchmark, taxonomy or v0.2.0 baseline change.
- PR #285 remains Draft and issue #170 remains Open.

Next actions:
1. Complete the corrected MGPR workflow. Inspect all 34 object-level results, including optimizer status, finite likelihoods, covariance conditioning, uncertainty and output-grid stability. Preserve explicit failures per object.
2. If runtime or memory limits fail, profile the 34-object diagnostic and design a bounded, deterministic numerical strategy without changing the scientific method or silently downsampling observations.
3. Complete the full CI gate on the latest commit.
4. Only after MGPR results, continue reconstructing the original Chen pipeline, including INFOBITS/catflags semantics, same-product period search, Fourier-fit stage and alias exclusions.
5. Keep the full-parent 781,602-object comparison as the final membership validation gate.


## 19. Full Table2 feature completeness and the 55 raw-photometry controls — 2026-11-14

### Full-parent metadata recheck

The pinned historical artifact was downloaded again and its ZIP digest was verified:
- artifact: `scientific-validation-heavy`, run `38635891449`;
- ZIP SHA-256: `346cd0a22d1490c9d3c5f6ff290ca2377e1c5458895c0c0d4b616b0708630c36`;
- parent metadata SHA-256: `3675b1274f73fcb15d47e7a780f194ef8fa335cd248c6ff53ea4f01559c86591`;
- parent rows: 781,602 unique SourceIDs.

The original Table2 file and Table4 crosswalk were also verified from artifact `cpvs-raw-cds-reconciliation`, run `41367972395`, ZIP SHA-256 `130f3db65827afd83f5050e7eb91eb1cf7f6432e85456fd16586c8000a9aa6be`.

Verified object sets:
- Table4 reference: 730,184 IDs.
- Reconstructed SNR candidate set: 741,786 IDs.
- Candidate-only residuals: 11,602 IDs.
- Four-field-only controls: 55 IDs.
- Parent objects outside candidate and 55 controls: 39,761 IDs.

Across all 781,602 parent objects, the four-field predicate (positive gmag, rmag, Per-g and Per-r) selects 730,239 objects. It contains every Table4 member and 55 additional parent objects. Inside the reconstructed candidate set, the same predicate selects exactly 730,184 objects: 730,184 Table4 members, zero residuals, zero false negatives.

Adding positive gAmp and rAmp does not change this 730,239 parent-wide set. Adding positive Ng and Nr also does not change it. The 55 additional objects have all six of these Table2 values positive.

The Table2 ReadMe explicitly marks gmag, rmag, Per-g, Per-r, gAmp and rAmp as missing when zero. It does not mark R2 or log(FAP) zero as missing. In the Table4 reference, R2-g includes 28 zeros and 768 negative values; R2-r includes 9 negative values. log(FAP-g/r) includes zero and negative values. Therefore a positive-R2 or positive-FAP rule would be scientifically invalid.

**Publisher-source boundary:** the checksum-pinned Table4 ReadMe (SHA-256 `0a7ec0dac13b155fdd63322dc9b0230de42fd05169e0e02c70f68fce0bc67d6a`) describes the 730,184 objects using the two-band detection criterion: at least one 2.5σ g detection and one 3σ r detection. It does not state the four-field complete-case predicate. The checksum-pinned Table2 ReadMe (SHA-256 `e57991d9e086155b9da14eaca7a6abc46a876a2dce58b397a90c915ec309e24a`) marks gmag, rmag, Per-g, Per-r, gAmp and rAmp as missing when zero. Therefore the complete-case explanation remains an evidence-based hypothesis about downstream feature availability, not a published membership rule.

This strengthens the complete-case feature hypothesis for the 11,602 residuals: the missing Table2 values align with per-band feature fields used downstream. It remains a hypothesis about publisher intent, not a documented official membership rule.

### Recovered raw-photometry audit for the 55 controls

The earlier raw-control artifact was recovered and re-hashed:
- artifact `cpvs-raw-cds-reconciliation`, run `41367972395`;
- `four_field_only_55.tsv`: SHA-256 `b7f712910467616919f616dfd5f9ddb94a4c6b819f973469eeeb704fae0e1ab6`;
- `per_band_snr_metrics.tsv`: SHA-256 `5388d4f2b8bae524dbc0f96ccf1d74b4a0ef08e6ce0a7e52d0dd0eb0fdfb7002`;
- `per_object_snr_metrics.json`: SHA-256 `c04e319f293ea937695558ba6ae1b304e9785156dcc164b861f188ee62eb2a51`;
- `report.json`: SHA-256 `1d42f55dc1c8f01f289ec697a8af4465aef8ea64e8d5f9fb43c2c96ea2e7cf57`.

The report status is PARTIAL. It records:
- only 1 of 55 controls has g-band raw rows;
- 51 of 55 have r-band raw rows;
- the band-presence cross-tab is 51 r-only, 3 neither, 1 g-only, and zero with both bands;
- raw row counts match Table2 Ng for 1 object and Nr for 51 objects;
- no control is reconstructed as a two-band SNR candidate.

The report itself warns that row-count mismatches must be resolved before interpreting SNR. Therefore these 55 are **not proven low-SNR objects**. Their retained Zenodo raw attachments do not contain both bands for any of them, despite positive Table2 Ng and Nr. This points to a data-stage, attachment-completeness, image-quality or SourceID-mapping question.

### Revised leading hypothesis

The evidence now supports a two-part reconstruction hypothesis:
1. The 11,602 residuals pass the raw two-band SNR test but lack at least one Table2 feature field required for a complete downstream feature vector.
2. The 55 parent controls pass the Table2 completeness test but lack dual-band raw rows in the retained Zenodo attachments, so they do not enter the reconstructed two-band SNR candidate set.

The exact intersection of the reconstructed SNR candidate set and the four-field complete-case predicate equals Table4. This is strong empirical evidence, but it does not prove the original authors used this exact sequence.

### Full-parent experiment started

The new research-only full-parent workflow:
- scans all 89,697,393 g rows and 109,971,576 r rows;
- verifies archive SHA-256, decompressed member SHA-256, byte count, row count and CRC;
- records raw and numeric-valid row counts for every Table2 SourceID;
- evaluates approximate, exact and inverse-error SNR formulas;
- evaluates Zenodo flag comparators `!=32768`, `<32768` and `==0` without assuming these fields are DR2 catflags;
- compares raw row counts with Table2 Ng/Nr by Table4, residual, 55-control and other-parent cohorts;
- emits a full 781,602-object reconciliation TSV and a row-count mismatch TSV.

Implementation:
- `scripts/diagnose_cpvs_full_parent_reconstruction.py`
- `tests/test_cpvs_full_parent_reconstruction.py`
- `.github/workflows/cpvs-full-parent-reconstruction.yml`
- `configs/process/cycles/cpvs-full-parent-raw-row-reconciliation-20261114.json`

The full-parent scan is pending. Until it completes, the 55-control raw-data discrepancy and all-parent count reconciliation remain unresolved. No production selector or v0.2.0 change is authorized.
