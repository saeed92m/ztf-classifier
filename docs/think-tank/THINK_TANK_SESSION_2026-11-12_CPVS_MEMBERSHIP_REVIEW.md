# Think Tank Session 04 — CPVS Membership and Raw-SNR Diagnostic Review

**Date:** 2026-11-12  
**Status:** Evidence review completed; source-backed raw-SNR execution remains QUEUED  
**Primary issue:** #170 — CPVS reconstructed membership discrepancy  
**Related PR:** #265 — targeted Seq identity, r-band reconciliation and raw-SNR sample diagnostic  
**Scientific baseline:** v0.2.0 — unchanged

> This is a structured review by 16 simulated specialist roles and a separate Red Team pass. It does not claim participation by 16 external people.

## 1. Review objective

Review the retained CPVS evidence and the new raw-photometry diagnostic before any source-ID correction, membership-rule change or scientific conclusion.

The review must answer four separate questions:

1. What is already verified from retained catalog and archive artifacts?
2. What has the new workflow been designed to measure?
3. What has actually executed against the original Zenodo archives?
4. Which conclusions remain hypotheses?

## 2. Inputs inspected

The review examined:

- Issue #170 and its latest retained-evidence comments.
- Draft PR #265, branch `research/cpvs-seq-identity-20261104`, head `64ed7ec34ee2b2aeae919b228a4423dca7f9fdc9`.
- `scripts/diagnose_cpvs_membership_snr_sample.py`.
- `.github/workflows/cpvs-membership-snr-sample.yml`.
- `scripts/diagnose_cpvs_rband_identity.py`.
- `scripts/diagnose_cpvs_seq_identity_unzip.py`.
- `configs/process/cycles/cpvs-rband-identity-20261107.json`.
- `tests/test_cpvs_membership_snr_sample.py`.
- Existing source-backed workflow comments and retained artifact hashes.
- Current GitHub Actions state for the CPVS workflows.

The code and workflow findings describe PR #265's inspected head. They are not evidence that the workflow completed.

## 3. Verified historical evidence — not a fresh raw-SNR reconstruction

The retained catalog artifacts support these object-level counts:

| Set | Unique IDs |
|---|---:|
| Parent Table 2 | 781,602 |
| Published Table 4 | 730,184 |
| Historical reconstructed candidates | 741,786 |
| Candidate-only residuals | 11,602 |
| Published-only residuals | 0 |
| Four-field-positive Table 2 set | 730,239 |
| Four-field-positive but not reconstructed candidates | 55 |

The retained set relation is:

- `C ∩ F = P` = 730,184.
- `C − P` = 11,602.
- `P − C` = 0.
- `F − C` = 55.

Here `P` is published Table 4 membership, `C` is the historical reconstructed candidate set, and `F` is the positive finite four-field Table 2 set (`gmag`, `rmag`, `Per-g`, `Per-r`).

**Critical limitation:** `C` was reconstructed from the published set plus the retained candidate-only difference list. It was not freshly re-derived from raw g/r photometry in this current workflow. The exact intersection is a diagnostic relationship. It does not prove that the paper authors used a four-field predicate.

The Table 4 to Table 2 name crosswalk has 730,184 rows and zero unmapped names in the retained reparse. The raw table hashes are pinned in prior evidence.

## 4. Raw-photometry diagnostic — what the code does

The new diagnostic is a bounded, source-backed re-derivation for:

- all 11,602 candidate-only residual IDs;
- the fixed 100-object sample;
- the fixed 1,000-object sample;
- all 55 four-field-only controls.

It is not a full 781,602-object reconstruction.

### 4.1 Input provenance

The script verifies the four input TSV files against their retained SHA-256 values and expected byte sizes:

- `candidate_only_11602_object_provenance.tsv`;
- `fixed_sample_100.tsv`;
- `fixed_sample_1000.tsv`;
- `four_field_only_55.tsv`.

It rejects metadata conflicts among those inputs.

The raw data sources are Zenodo record 10.5281/zenodo.3886372:

- g archive MD5 `850fcef561dd7407fbe8e19e99100d7a`;
- g archive SHA-256 `47cd1823b3ccdb69fa3085381cf63ff0605f6d841fc3bc37489dce023ddc19b9`;
- r archive MD5 `daa7bc45c67579253eebe6b1c09dfbd9`;
- r archive SHA-256 `48331ba1157afc993a1399e094b97752a82d8d0f736d2fdf63fd7b2a82281b74`.

The script also pins extracted-member SHA-256, byte count, row count and CRC values for each band.

### 4.2 Selection diagnostic

The script evaluates three SNR calculations for each valid photometry row:

- approximate magnitude-error SNR: `1.0857362047581296 / magerr`;
- exact magnitude-error conversion: `1 / expm1(magerr × ln(10) / 2.5)`;
- inverse magnitude error: `1 / magerr`.

The diagnostic candidate decision currently uses the approximate formula with thresholds:

- g: SNR ≥ 2.5;
- r: SNR ≥ 3.0.

It requires at least one valid, non-zero-magnitude row above threshold in each band. Non-zero flags are recorded; the workflow does not apply a flag filter.

The code also reports per-band exact and inverse-error qualifying counts. However, the combined object-level candidate and confusion summaries currently use the approximate formula only. The output therefore does not yet compare three complete two-band membership sets.

### 4.3 Unknown values

A band with zero raw rows receives a `None` SNR status. The two-band result is also `None` if either band is unknown.

This is correct for missing coverage. Missing photometry is not an SNR failure. The confusion summary puts unknown cases in a separate count instead of false positives or false negatives.

### 4.4 Source integrity and output

The workflow:

1. Runs synthetic tests.
2. Downloads the retained TSV artifact.
3. Downloads the pinned g/r archives.
4. Verifies archive MD5 and SHA-256.
5. Streams archive members with Info-ZIP.
6. Verifies member SHA-256, byte count, row count, CRC and malformed-row count.
7. Re-derives per-object photometry and writes compact JSON/TSV reports.

The workflow has a 120-minute timeout. It uploads only compact reports. It does not upload or commit raw photometry. The workflow is read-only with respect to the CPVS source data.

## 5. Current execution evidence

The workflow run `43097116480` (CPVS Membership Raw SNR Sample Re-derivation) was created on 2026-11-11 at 20:37 UTC for head `64ed7ec`.

At the time of this review:

- Run status: `queued`.
- Conclusion: `null`.
- Jobs created: zero.
- No g/r scan report is available from this run.
- No current raw-SNR result is claimed.

The targeted Seq run `43097116446` and r-band reconciliation run `43097116394` are also still queued with no jobs.

The branch is open and Draft. Compared with current `main`, it is 80 commits ahead and 92 commits behind, with merge base `bc85f6c36b28f3c9ddc2b7b5aa00e0256148441c`. This is a branch-reconciliation risk. Do not merge this PR as-is.

The existing historical Seq 615170/615172 results remain strong identity leads only. They do not authorize rewriting IDs and do not explain the 11,602 membership residuals.

## 6. Findings from the 16 specialist roles

| Role | Review finding |
|---|---|
| 1. Principal Investigator | The four-field intersection is a strong root-cause candidate, not proof of the authors' method. Keep the paper-method question open. |
| 2. ZTF Survey Specialist | Verify each archive checksum, member hash, row count, CRC and per-Seq count. Keep Table 2 Seq and archive Seq distinctions explicit. |
| 3. Time-Domain Astrophysicist | The 615170/615172 coordinate and photometry agreement is a lead. Compare g/r time ranges and source context; do not auto-remap. |
| 4. Astrostatistician | The fixed samples are intentionally stratified. Pooled sample rates are not population prevalence or unbiased performance estimates. Report every stratum separately before interpretation. |
| 5. Astroinformatics Architect | The streaming archive scan is appropriate for large inputs, but preserve full manifests, row counts, malformed rows and per-object provenance. |
| 6. Cross-Match Specialist | An OID/Seq count or positional match does not prove physical identity. Keep candidate, ambiguous and unresolved links distinct. |
| 7. ML Scientist | Do not change the frozen selector, features or model. This diagnostic is a data-method investigation, not model retraining. |
| 8. Benchmark and Validation Lead | Recompute TP/FP/TN/FN only on known labels and known raw outcomes. Retain unknown denominators and report per stratum. |
| 9. Software Architect | Keep raw SNR re-derivation separate from the production CPVS selector and from the v0.2.0 baseline. |
| 10. Backend Engineer | The workflow should be restart-safe, bounded and artifact-driven. Do not create duplicate full-archive runs. |
| 11. DevOps/Security Engineer | Keep token permissions read-only, do not persist raw archives, and record exact run/commit/input hashes. |
| 12. QA Engineer | The synthetic test checks parsing, checksums, no-row unknowns and flags. Full archive execution is still required; one synthetic test is not a source-backed result. |
| 13. Scientific UX Architect | Reports must expose PASS, FAIL, UNKNOWN and ERROR separately, with exact source IDs and archive provenance. |
| 14. Product/Commercial Lead | CPVS research is separate from the immediate Park MVP deliverable. Keep it scientifically active without misrepresenting product readiness. |
| 15. Scientific Documentation Lead | Every count must be labelled retained-artifact, raw-rederived, hypothesized or not measured. |
| 16. Independent Red Team | The current code combines approximate SNR into the candidate decision while also calculating exact and inverse alternatives. It must report full two-band results for all three formulas before the formulas can be compared as candidate-set alternatives. |

## 7. Red Team findings and required improvements

### 7.1 Three formulas are not yet compared at object-membership level

The code calculates per-band qualifying detection counts for approximate, exact and inverse-error SNR. But `build_object_rows()` creates only one combined `rederived_candidate`, based on the approximate formula. The report's confusion matrix also uses that approximate result only.

**Required:** derive separate two-band candidate booleans for all three methods. Compare each method independently to the historical candidate flags and Table 4, with unknowns excluded from FP/FN and reported explicitly. Do not select a method based on which one matches Table 4 best without publisher-method evidence.

### 7.2 Stratified sample summaries need per-stratum output

The 100- and 1,000-object samples were deliberately stratified. The current report emits pooled summaries for each sample and stores stratum membership at object level. It does not provide an explicit summary table per stratum.

**Required:** report count, label availability, g/r PASS/FAIL/UNKNOWN and confusion counts for each stratum. Label pooled figures as stratified diagnostic counts, not prevalence estimates or generalization metrics. Do not compute a population accuracy from unweighted pooled strata.

### 7.3 Duplicate and overlap audit needs to be explicit

The loader merges identical SourceIDs from input TSVs and detects field-value conflicts. It does not emit an explicit within-file duplicate count and cross-file overlap matrix.

**Required:** record unique IDs, duplicate IDs within each file, expected overlap between the fixed 100- and 1,000-object samples, overlap with the residual list and overlap with the 55 controls. Reject conflicting records and report legitimate repeated memberships as strata, not duplicate objects.

### 7.4 Flag semantics remain unresolved

The diagnostic reports all flags and flags for qualifying detections, but it does not apply any flag filter. This is useful as a raw comparison, but it does not prove the publisher ignored flags.

**Required:** retain the unfiltered result as one explicitly named diagnostic. Add separate flag-policy comparisons only when the publisher's policy or an authoritative source is established. Do not tune flags until Table 4 matches.

### 7.5 Full-set scope remains limited

Even a complete run of the current workflow would rederive raw SNR for 11,602 residual IDs, the fixed samples and 55 controls. It would not reconstruct the candidate set for all 781,602 parent IDs.

**Required:** after the bounded diagnostic passes, run an independently specified full object-level reconstruction if source data, provenance and compute resources allow. Compare the complete resulting ID set to Table 4 and the retained candidate set. Keep all inputs and outputs hashed.

### 7.6 r-band archive count residual remains open

The retained r-band archive scan reports 109,971,576 rows, while the Table 2 sum of `Nr` is 109,970,858 (difference +718), and the CDS ReadMe reports 89,697,393. The targeted Seq scan is not a substitute for all-Seq count reconciliation.

**Required:** complete the per-Seq r-band Table 2 comparison, inspect every mismatch, and explain the total residual. Keep the ReadMe conflict separate.

## 8. Joint decisions

1. Keep Issue #170 OPEN and UNRESOLVED.
2. Treat the four-field completeness predicate as the strongest current root-cause candidate, not an accepted publisher rule.
3. Do not change CPVS selector, SNR thresholds, SourceID mapping, benchmark, features, taxonomy, model or v0.2.0 artifact.
4. Keep zero-row bands as UNKNOWN, never as FAIL.
5. Keep the 100-/1,000-object samples stratified. Do not claim population-level metrics from pooled strata.
6. Require exact per-object lineage from every residual and sample result to the retained input TSV and archive row IDs.
7. Keep the g/r archive count mismatch and the 718-row r-band residual as separate audit findings.
8. Do not treat Seq 615170/615172 identity as resolved.
9. Do not merge PR #265 until it is reconciled with current main and its source-backed jobs complete.
10. Do not rerun the 1.6 GB archive workflow merely to create a fresh run while the existing workflow remains queued.

## 9. Acceptance gates

| Gate | Evidence required | Current state |
|---|---|---|
| Synthetic diagnostic tests | parser, integrity, tri-state, row and flag regression tests | Defined in PR; current-head CI not verified |
| Raw g/r archive integrity | archive and member hashes, byte count, CRC, row count, no malformed rows | Not run in current queued workflow |
| 11,602 raw residual scan | object-level g/r results, formula alternatives, row counts, flags and unknowns | Not run |
| Fixed sample diagnostics | 100 and 1,000 sample results, per-stratum metrics and explicit overlap audit | Not run |
| 55 controls | g/r tri-state raw coverage with unknown denominators | Not rederived in current workflow |
| r-band all-Seq reconciliation | per-Seq `Nr` comparison, all mismatches, explain +718 | Not complete |
| Seq 615170/615172 | independent g/r identity evidence and source-ID lineage | Strong lead, unresolved |
| Publisher-method verification | paper, supplement, code or authoritative method proving actual selection steps | Not established |
| Full parent reconstruction | all 781,602 IDs, source hashes and object-level set comparison | Not run |
| Scientific closure | reproducible root cause and regression tests | BLOCKED |

## 10. Final session decision

**Decision: APPROVE THE DIAGNOSTIC DESIGN WITH REQUIRED RED-TEAM AMENDMENTS; KEEP SCIENTIFIC CONCLUSION BLOCKED.**

The new workflow is appropriately bounded, read-only, hash-pinned and explicit about missing data. It can provide useful raw-photometry evidence for the 11,602 residuals and fixed samples once it runs.

However, the present code does not yet compare all three SNR formulas at the combined two-band object level, does not summarize the fixed samples by stratum, and does not report a complete duplicate/overlap matrix. Even after those improvements, the workflow is not a full 781,602-object candidate reconstruction and cannot prove the publisher's selection rule by itself.

No CPVS source ID, membership criterion, threshold, v0.2.0 artifact, feature schema, taxonomy, model or scientific acceptance criterion was changed during this session.
