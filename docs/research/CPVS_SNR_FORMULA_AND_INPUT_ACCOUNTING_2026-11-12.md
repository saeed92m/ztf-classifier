# CPVS Raw SNR Formula and Input Accounting — 2026-11-12

**Think Tank source:** [TT-2026-11-12-07](../think-tank/THINK_TANK_SESSION_2026-11-12_CPVS_PRIORITY_AND_EVIDENCE_RECHECK.md)  
**Base:** `main@f681408fae8d8062dd72ff74791872c1590f6ee8`  
**Scope:** Isolate and correct the retained CPVS raw-SNR diagnostic before any multi-gigabyte source run.

## 1. Why this branch exists

The old research branch `research/cpvs-seq-identity-20261104` contains 80 commits and 14 changed files. Its base snapshot predates current `main`. This branch starts from current main and carries only the bounded raw-SNR sample diagnostic and its synthetic tests.

The original script computes three per-band SNR variants:

1. Approximate: `1.0857362047581296 / magnitude_error`.
2. Exact magnitude-error conversion: `1 / expm1(magnitude_error * ln(10) / 2.5)`.
3. Inverse error: `1 / magnitude_error`.

Before this correction, the script calculated all three per-band detection counts but constructed the two-band object candidate set and Table 4 confusion summary from the approximate formula only. This hid the membership differences between the three alternatives.

## 2. Changes in this branch

### Separate two-band candidate sets

The diagnostic now creates independent object-level candidate states for:

- `approximate`
- `exact`
- `inverse_error`

For each formula, it reports:
- g-band PASS / FAIL / UNKNOWN;
- r-band PASS / FAIL / UNKNOWN;
- two-band candidate PASS / FAIL / UNKNOWN;
- candidate plus four-field diagnostic;
- confusion counts against Table 4 membership;
- agreement/disagreement with the retained historical candidate flag.

The old top-level fields remain as explicit aliases for the approximate formula to preserve downstream compatibility. The full per-formula result is in `snr_formulae`.

The inverse-error formula is a diagnostic alternative. It is not represented as physically equivalent to the exact SNR conversion.

### Explicit input duplicate and overlap accounting

The loader now reports:
- record count per TSV;
- unique SourceID count per TSV;
- duplicate rows and duplicate SourceIDs within each individual TSV;
- pairwise cross-file overlap counts, deterministic sorted-ID hashes and bounded examples;
- metadata conflicts across repeated SourceIDs.

Cross-file overlaps are expected because the fixed samples intentionally draw from the candidate-only and four-field-control cohorts. They are reported, not treated as duplicate source records. Any duplicate SourceID within a single input file now fails closed before raw archive scanning.

### Output

The JSON report contains all formula summaries for each sample stratum. The per-object TSV includes all three g/r formula states and all three two-band candidate results. Missing raw observations remain UNKNOWN.

## 3. Inputs and execution boundary

The script verifies the retained 4 compact input TSVs against the pinned SHA-256 and byte-size manifest from artifact 13108147605. It then scans the checksum-pinned Zenodo g/r archives.

The raw archive members expand to more than 11.2 GB combined. **This branch does not download or scan those archives during ordinary CI.** CI runs only synthetic regression tests. A source-backed run requires a separate explicit compute/cost decision.

## 4. Scientific boundaries

- Table 4 membership is a published membership reference, not independent astrophysical truth.
- Approximate, exact and inverse-error formulas are diagnostics; none is automatically the publisher's full selection method.
- Four-field positivity remains diagnostic only.
- Missing raw rows remain UNKNOWN.
- The fixed samples are stratified diagnostic samples, not prevalence estimators.
- No Seq remapping is authorized.
- No selector, threshold, model, feature, taxonomy, benchmark, v0.2.0 baseline or v1.0.1 release changes.
- No MGPR execution is included.
- This branch does not resolve the 11,602 residuals.

## 5. Required validation

Before this branch can be considered engineering-ready:
1. Ruff format and lint pass.
2. Synthetic tests verify distinct approximate/exact/inverse-error two-band candidate sets.
3. Synthetic tests verify per-band and two-band UNKNOWN behavior.
4. Synthetic tests verify within-file duplicate detection.
5. Synthetic tests verify expected cross-file overlap accounting.
6. Full repository CI and lifecycle validation pass.

A separate raw source-backed execution must verify archive checksums, extracted-member hashes, row counts, malformed-row counts, per-formula results, per-stratum results and output hashes. Do not claim scientific validation from synthetic tests.
