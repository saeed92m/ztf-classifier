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

The workflow file was changed to upload only five explicit evidence files. That artifact-boundary change has not yet been verified by a new raw-SNR run. The existing run 43463184881 artifact contains unrelated historical reports and tables because it uploaded the entire `reports/` directory. Raw g/r archives were not included.
The flag-policy scan [run 43525513465](https://github.com/saeed92m/ztf-classifier/actions/runs/43525513465) completed successfully. Setup, synthetic regression tests, pinned-input retrieval, both checksum-pinned archive downloads, raw scan and artifact upload all passed. Its artifact (ID 14085318178, SHA-256 `198ad0becaae7cc752e34fd34ae6e269ae49a73b255afc6a3773d651f26e6088`) contains exactly five allowlisted files; no unrelated reports or raw archives were uploaded. The artifact contains 7,074,893 uncompressed bytes and expires 2026-11-27.

## 13. Joint decision and current status

- Raw archive integrity: **VERIFIED**.
- Raw SNR scan for 11,602 residual IDs: **COMPLETED**.
- SNR formula disagreement in residual cohort: **NONE**.
- Four-field predicate as empirical discriminator: **VERIFIED FOR THIS RESIDUAL COHORT**.
- Four-field predicate as publisher's documented rule: **NOT ESTABLISHED**.
- Raw row count agreement: **14 OBJECTS HAVE AT LEAST ONE MISMATCH**.
- Flag-based detection semantics: **NOT YET TESTED**.
- Identifier namespace equivalence: **REQUIRES EXPLICIT VERIFICATION**.
- Full 781,602-object reconstruction in this workflow: **NOT PERFORMED**.
- MGPR analysis: **NOT PERFORMED**.
- Scientific validation: **NOT_VALIDATED**.
- Production selector and v0.2.0 baseline: **UNCHANGED**.
- Issue #170: **KEEP OPEN**.
- PR #285: **KEEP DRAFT; DO NOT MERGE ON THIS EVIDENCE ALONE**.

**Root-cause conclusion:** not yet established. The strongest current lead is incomplete two-band fit metadata: positive `gmag` and `rmag` remove 11,585 residuals; the remaining 17 all have one missing band-specific period while retaining a common period. The tested `flag < 32768` diagnostic leaves all 11,602 residuals unchanged, and strict zero-flag filtering removes 5,472 published members. The next work must explain why the Chan et al. pipeline requires both mean magnitudes and, for the remaining 17, both band-specific periods, or identify another rule that yields the same partition. The 14 raw/Table 2 row-count mismatches remain a separate provenance/quality investigation.
