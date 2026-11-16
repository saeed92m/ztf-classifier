# Think Tank Session 09 — CPVS Action and Scientific Revalidation

**Session:** TT-2026-11-16-09  
**Date:** 2026-11-16  
**Scope:** CPVS 11,602-object membership discrepancy; corrective engineering; final evidence plan  
**Review:** 16 simulated specialist seats plus Red Team  
**Status:** Research actions applied; scientific root cause NOT PROVEN  
**Protected baseline:** v0.2.0 unchanged

> This is a simulated multi-disciplinary review. It is not a meeting of 16 external human experts or independent academic peer review.

## 1. Executive decision

The CPVS discrepancy remains **OPEN / NOT RESOLVED**.

The best current explanation is a two-stage **SNR plus downstream complete-case hypothesis**. It explains the observed set difference. It does not yet prove the publisher's complete selection procedure.

| Population | Objects |
|---|---:|
| Table 2 parent | 781,602 |
| Table 4 reference | 730,184 |
| Reconstructed two-band SNR candidates | 741,786 |
| Candidate-only relative to Table 4 | 11,602 |
| Published-only relative to candidates | 0 |
| Four-field-positive within SNR candidates | 730,184 |
| Four-field-only parent controls | 55 |

The four-field predicate is: positive gmag, rmag, Per-g and Per-r. It selects all 730,184 Table 4 objects inside the SNR candidate set, with zero residuals and zero missing reference IDs. Across the full parent it also selects 55 nonmembers. Therefore the exact match is empirical, not proof of publisher intent.

Chan et al. (2022) describes the 730,184 subset as having at least one 2.5-sigma g detection and one 3-sigma r detection. It does not explicitly state the four-field predicate. The paper also uses the two-band mean-magnitude color feature and discusses per-band periods. These facts support a downstream feature-completeness hypothesis, not a documented membership rule.

## 2. Verified CPVS evidence

### 2.1 SNR and membership

Full-parent workflow [43600721277](https://github.com/saeed92m/ztf-classifier/actions/runs/43600721277) processed all 781,602 Table 2 objects.

For the 11,602 candidate-only objects:
- g SNR PASS: 11,602.
- r SNR PASS: 11,602.
- Two-band SNR PASS: 11,602.
- Approximate, exact magnitude-error and inverse-error diagnostic formulas produced the same membership result in this residual cohort.
- Tested flag policies `flag < 32768` and `flag != 32768` did not change membership.
- Strict `flag == 0` is invalid for reproduction: it removes 5,472 Table 4 members in the full-parent ablation.

Full-parent reference-relative counts:
- SNR alone: TP 730,184; FP 11,602; FN 0; TN 39,816.
- Four-field predicate alone: TP 730,184; FP 55; FN 0; TN 51,363.
- SNR AND four-field predicate: TP 730,184; FP 0; FN 0; TN 51,418.

These metrics compare catalogue membership only. They do not measure astrophysical truth.

### 2.2 The 11,602 residuals

The residuals partition into:
- 11,580 with both field pairs incomplete.
- 17 with both mean magnitudes but one band-specific period missing.
- 5 with both per-band periods but one mean magnitude missing.

Thus 11,585 lack at least one mean magnitude. The 17 period-incomplete objects have substantial raw observations. Their missing-band log(FAP) values are mixed: 10 are zero and 7 are negative. A single FAP threshold does not explain them.

A bounded MGPR feasibility experiment fitted all 17 residuals and 17 matched Table 4 controls. This shows that a missing band-specific period does not necessarily prevent a finite fit when the common period and both raw light curves are available. It does not prove historical Table 4 membership.

### 2.3 Raw archive lineage

The full-parent run found 100 objects with at least one raw archive row-count mismatch against Table 2 Ng/Nr:
- 91 g-band mismatches.
- 25 r-band mismatches.
- Cohorts: 55 four-field-only controls, 14 candidate-only residuals, 26 Table 4 members and 5 other parent objects.

For the 55 four-field-only controls:
- 54/55 have no g raw rows despite positive Table 2 Ng.
- 4/55 have no r raw rows despite positive Table 2 Nr.
- Cross-tab: 51 r-only, 3 neither, 1 g-only, 0 both.
- Their missing-band SNR state is UNKNOWN, not FAIL.

The 14 residual mismatches include 13 objects with Table 2 Ng=0 but positive raw g rows. Three also have r count mismatches. This is a source-lineage question, not proof of an ID mapping defect.

The Zenodo r attachment expands to 109,971,576 rows. The CDS ReadMe lists 89,697,393 for both g and r. The pinned archive/member hashes are recorded in Session 08. This discrepancy remains open.

### 2.4 Quality flags and source limitations

The Zenodo attachments do not contain image-level INFOBITS. The equivalence of Zenodo g_flag/r_flag to Chen et al.'s DR2 catflags is not proven. The tested non-strict flag policies do not remove the residuals. Missing raw rows cannot be classified as SNR failures.

### 2.5 Time scale

Zenodo describes the raw epoch as HJD. CDS describes it as MJD. Chan et al. (2022) defines phase using MJD. The 100-object coordinate/epoch workflow failed in its unit-test stage before scanning data. It produced no accepted time-scale result.

Do not subtract 2,400,000.5 until raw values prove HJD-like input. Do not substitute Table 2 T0 without a source-backed reason. Phase-fold and MGPR results that depend on this conversion remain provisional.

## 3. Engineering actions applied

On research branch `research/cpvs-snr-formula-audit-20261112`:

1. Added observed and expected byte/row counts to the archive integrity error. The check remains fail-closed.
2. Replaced external `unzip -p` subprocess streaming with Python's standard-library `zipfile.open()`. The diagnostic still checks archive SHA-256, member SHA-256, CRC32, expanded bytes and row count.
3. Expanded the synthetic regression test to assert member bytes, row count, SHA-256 and CRC32.
4. Updated Session 08 with the completed MGPR result and the failed 100-object lineage run.
5. Updated Issue #170 with the current evidence and unresolved disposition.

Commits:
- `17024482eb3a42f118b815f5b837c5249f768f7f` — detailed archive-integrity error.
- `4741297ffbf8b56ff742719d4b2662c5c0b790fa` — standard-library ZIP streaming.
- `31e2e3ef246151f378ae4d6dd236987fb4a5744f` — integrity regression assertions.

**Verification boundary:** source changes were fetched and inspected after each write. The latest CI result on commit `31e2e3ef246151f378ae4d6dd236987fb4a5744f` has not been retrieved. The repair is applied, but not yet CI-verified. Previous workflow [43612083641](https://github.com/saeed92m/ztf-classifier/actions/runs/43612083641) failed before the raw-data scan.

## 4. Simulated 16-seat review and Red Team decision

| Discipline | Decision |
|---|---|
| Variable-star astronomy | SNR pass does not prove complete two-band analysis eligibility. |
| Survey photometry | Separate image-level INFOBITS from epoch-level flags. |
| Statistical inference | Keep PASS, FAIL and UNKNOWN distinct. |
| Time-series analysis | Resolve HJD/MJD before accepting phase-fold or GP results. |
| Catalogue curation | Preserve Table 2 Seq, ZTF name and raw SourceID as separate provenance fields. |
| Data engineering | Verify every archive member and count. Never weaken integrity checks. |
| Software testing | Test the exact ZIP stream and all integrity metadata. |
| ML methodology | A successful MGPR fit does not prove catalogue membership. |
| Reproducibility | Pin source bytes, code SHA, commands, seeds and outputs. |
| Cross-match science | Coordinate proximity is a candidate alias, not an identity decision. |
| Quality assurance | The 55 controls are UNKNOWN for missing-band SNR. |
| Scientific governance | No production selector change without primary-source support. |
| Product architecture | Keep CPVS research separate from the DR24 MVP, but retain the scientific blocker. |
| Security/release | No merge, release or production model change in this action. |
| Documentation | Record only verified evidence and limitations. |
| Red Team | The four-field exact match may be post-hoc correlation; it is not proof of publisher intent. |

Red Team objections:
1. The four-field predicate was identified after observing the mismatch. It is not an independently specified rule.
2. Missing raw rows cannot be labelled SNR FAIL.
3. The r-file row count and epoch descriptions conflict across source documentation.
4. A missing per-band period may reflect a failed fit, rejected fit or export omission.
5. A 3-arcsecond nearest-coordinate match is not enough to rewrite object identity.
6. The published SNR description does not specify every upstream quality and fitting stage.

## 5. Corrective work order

### P0 — Validate the repaired 100-object lineage path
- Verify current-head unit tests.
- Re-run the 100-object g/r lineage scan.
- Record actual/expected bytes, rows, SHA-256 and CRC32.
- Correct only the side proven wrong: fixture, metadata or implementation.
- Inspect all 100 objects and all alternate SourceID candidates.

### P0 — Resolve all 100 row-count mismatches
- Compare SourceID, RA, Dec, epoch, magnitude, uncertainty and flag.
- Separate missing-band coverage, count mismatch and duplicate epochs.
- Locate the authoritative definition and source stage for Table 2 Ng/Nr.
- Establish whether the Zenodo attachments are complete and whether they represent the same processing stage.
- Determine why 55 controls lack dual-band raw attachments.

### P0 — Reconstruct Chen et al. upstream selection
- Recover original code or a sufficiently detailed method.
- Verify Zenodo flag-to-catflags mapping.
- Locate image-level INFOBITS or an equivalent pinned DR2 source.
- Reproduce minimum-detection, quality, period-search, one-band acceptance, 1-arcsecond period redetermination, Fourier-fit and alias stages.
- Compare each stage at object level against Table 2 and Table 4.
- Do not replace missing method evidence with the four-field predicate.

### P1 — Resolve the 17 missing per-band periods
Trace the original period-fit inputs and diagnostics. Compare FAP, R-square, amplitude and fit quality with matched Table 4 controls. Distinguish failed fits from zero sentinels and export omissions.

### P1 — Resolve time scale and r archive count
Inspect actual epoch values from pinned members. Reconcile HJD/MJD documentation and the CDS/Zenodo r-file count. Rerun phase-fold and MGPR only after conversion is proven.

### P0 — Final population and sample acceptance
Regenerate current-head 100-object, stratified 1,000-object and separate 1,000-object nonmember samples. Preserve exact IDs, seeds, commands, source hashes and per-object PASS/FAIL/UNKNOWN results. Compare full and batched processing by complete object identity. Report reference-relative TP/FP/FN/UNKNOWN with exact denominators.

## 6. Final disposition

- CPVS root cause: **NOT PROVEN**.
- Table 4 reproduction: **NOT VALIDATED**.
- Issue #170: **OPEN**.
- Issue #180: **OPEN / DEFERRED RESEARCH**.
- PR #285: **DRAFT / OPEN**.
- Production selector, thresholds, model, features, taxonomy, benchmark, class order and v0.2.0 baseline: **UNCHANGED**.
- No merge or release performed.

The next acceptance gate is a successful, checksum-verified 100-object lineage run, followed by a complete row-level explanation for the 100 mismatches and a source-backed reconstruction of the publisher's quality and detection rules. If the original method cannot be recovered, retain the unresolved blocker. Matching a count is not enough.

## Sources

- Chan et al. (2022): https://doi.org/10.3847/1538-4357/ac69d4
- CDS Table 4 ReadMe: https://cdsarc.cds.unistra.fr/viz-bin/ReadMe/J/ApJ/932/118?format=html&tex=true
- Chen et al. (2020) Zenodo record: https://zenodo.org/records/3886372
- Chen et al. (2020) CDS ReadMe: https://cdsarc.cds.unistra.fr/ftp/J/ApJS/249/18/ReadMe
- Official ZTF DR2 quality documentation: https://irsa.ipac.caltech.edu/data/ZTF/docs/releases/dr02/src/dr02.html


---

## 7. Primary-source recovery — Chen et al. (2020), full Section III

The full paper text is now checked directly from arXiv: https://arxiv.org/abs/2005.08662

This adds important upstream constraints that must be tested before accepting the four-field hypothesis:

1. Chen et al. first selected ZTF DR2 objects with at least 20 detections.
2. They excluded poor-quality images and photometry using INFOBITS < 33,554,432 and catflags != 32,768.
3. Period searches were performed in both g and r bands, but a candidate was accepted when the light curve in **one band** met all period-search conditions. Therefore, requiring both Per-g and Per-r to be positive is not a valid assumption about the original Chen catalogue-generation gate.
4. They used Lomb–Scargle periods from 0.025 to 1,000 days and selected periodic candidates with FAP < 0.001.
5. They redetermined periods using photometry within 1 arcsecond of the source position.
6. They fitted fourth-order Fourier functions and excluded poorly fitted light curves using adjusted R-squared. The paper describes the condition as R_g^2 < 0.4 and R_r^2 < 0.4; its exact logical implementation and the correspondence to the published Table 2 R2 fields still need source-level verification.
7. They then excluded some aliases using period versus R-squared or phase-difference criteria.
8. The classification feature set includes the period, Fourier parameters, amplitude, Wesenheit magnitude and adjusted R-squared. The Wesenheit calculation explicitly uses both fitted mean magnitudes.

### Consequence for the 11,602 discrepancy

The 11,585 residuals with at least one missing mean magnitude have a plausible downstream completeness explanation: Chan et al. uses both mean magnitudes to construct the two-band color/Wesenheit-derived feature. This is consistent with the exact empirical four-field intersection, but it still does not prove that the four-field predicate was the actual Table 4 filter.

The remaining 17 residuals are more difficult. They have both mean magnitudes and a common period, but one band-specific period is missing. Chen et al. explicitly allowed a catalogue candidate to pass the original periodicity search when only one band met the period conditions. Chan et al.'s phase-folding method uses the common Table 2 period. Therefore the missing Per-g/Per-r value alone is not a documented reason to exclude these 17 from the Chan pipeline. Their exclusion needs a separate explanation, such as a raw-data quality issue, a failed two-band interpolation, a missing/invalid epoch, or another undocumented complete-case rule.

### New ordered tests

- Verify the Zenodo g_flag/r_flag mapping to DR2 catflags by comparing the exact raw observations against the official DR2 light-curve products for a bounded set of the 100 mismatch objects and controls.
- Recover or query the DR2 image metadata needed to evaluate INFOBITS < 33,554,432. The Zenodo attachments do not contain INFOBITS.
- For all 100 row-count mismatch objects, compare Table 2 Ng/Nr with raw rows after each independently documented quality stage.
- For the 17 period-incomplete residuals, compare raw two-band data and quality-qualified detections with 17 matched Table 4 controls; then rerun the Chan two-band MGPR preparation and interpolation using the proven MJD convention.
- Test the original Chen adjusted-R-squared and alias criteria only after confirming whether the Table 2 R2-g/R2-r fields are the same statistic.
- Do not impose a two-band period requirement at the Chen catalogue-generation stage. Preserve it only as a diagnostic feature-completeness hypothesis if the Chan pipeline requires it.

This primary-source recovery narrows the problem. It does not resolve the 11,602 discrepancy. Root cause remains NOT PROVEN.
