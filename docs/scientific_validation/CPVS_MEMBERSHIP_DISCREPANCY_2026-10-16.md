# CPVS membership discrepancy — evidence record (2026-10-16)

## Status

**UNRESOLVED — fail-closed.** This record narrows the likely explanation for the 11,602 candidate-only objects, but it does not establish the historical publisher selection rule. No production predicate, threshold, model artifact, or scientific acceptance criterion was changed.

## Pinned evidence

- Heavy Scientific Validation run: [38789483790](https://github.com/saeed92m/ztf-classifier/actions/runs/38789483790), run number 990.
- Source revision recorded by the provenance report: `e505264c736b4c0db1bdf150d55fd36150f40a9a`.
- Artifact: `scientific-validation-heavy.zip`, artifact ID `12004126160`.
- Artifact SHA-256: `28c704671e392fc0e983eee7e8df5ed0f5fd29bce80acd0c2c2cc0218d5da747` (recomputed after download).
- Candidate-only TSV SHA-256: `fc724b5ed77e703b16e272f33e241563dce5c7227ae75484ac8d943689361adc`.
- Epoch-level JSONL SHA-256: `9636a9639358d79ef8fc9030ce9a1165756fa1690257af6e222a11cadfdeeb7d`.
- Parent Table2 archive SHA-256: `0f3ca5d4e71f674c38b3c08553c12cca0c32d2d31f776166ab29ce80a75cf138`.
- Published Table 4 SHA-256: `f7d8ad65644993e3ab25bc560aab32f98601cfb1eb9e78249918039dcf3bfca5`.

## Membership audit

| Set | IDs |
|---|---:|
| CPVS parent | 781,602 |
| Published Table 4 membership | 730,184 |
| Reconstructed rowwise-SNR candidate set | 741,786 |
| Intersection | 730,184 |
| Candidate-only | 11,602 |
| Published-only | 0 |
| Full-vs-batch disagreements across parent | 0 |

Full-vs-batch equality demonstrates implementation consistency only; it does not validate the historical selection rule.

The four-field diagnostic (`gmag`, `rmag`, `Per-g`, `Per-r` all finite and nonzero) selects exactly the published membership when applied to the reconstructed candidate set (0 false positives, 0 false negatives). Applied to the full parent, it retains 730,239 objects, including 55 that do not pass the rowwise SNR predicate. This is an exact discriminator for these pinned artifacts, not proof of the authors' explicit rule.

## New discriminator from the paper's feature definition

Chan et al. (2022), Section 2.3, explicitly add the mean-color feature

`m_gr = <m_g> - <m_r>`

to the anomaly detector, alongside the common period. A source with `gmag=0` or `rmag=0` cannot provide this feature from the Table 2 mean magnitudes without an additional missing-value policy.

The mutually exclusive patterns among the 11,602 candidate-only IDs are:

| Pattern | IDs |
|---|---:|
| `gmag=0` and `Per-g=0` | 11,465 |
| `rmag=0` and `Per-r=0` | 115 |
| `Per-g=0` only | 10 |
| `Per-r=0` only | 7 |
| `gmag=0` only | 5 |
| **Total** | **11,602** |

Therefore, **11,585/11,602 (99.85%)** have a zero g- or r-band mean magnitude. This is a plausible explanation for most exclusions: the paper's published feature definition requires both mean magnitudes. But the paper does not explicitly state that this feature's validity was an upstream membership filter, so the inference remains a hypothesis.

### The residual 17 IDs

The remaining 17 candidate-only IDs have nonzero `gmag` and `rmag`, but one independent per-band period is zero. Every one has a positive common `Per` and at least 50 SNR-qualified, finite/nonzero-magnitude observations in each band. Thus, a simple minimum-observation-count cutoff is not supported by these data.

| SourceID | Zero per-band period | g rows | r rows |
|---:|---|---:|---:|
| 9877 | `Per-r` | 62 | 63 |
| 120746 | `Per-g` | 61 | 71 |
| 127012 | `Per-g` | 96 | 110 |
| 151010 | `Per-g` | 87 | 75 |
| 191955 | `Per-g` | 51 | 50 |
| 281946 | `Per-r` | 245 | 204 |
| 287003 | `Per-g` | 114 | 134 |
| 307249 | `Per-g` | 156 | 156 |
| 378719 | `Per-r` | 156 | 157 |
| 385223 | `Per-r` | 122 | 112 |
| 409233 | `Per-g` | 151 | 175 |
| 429716 | `Per-g` | 171 | 187 |
| 440167 | `Per-g` | 171 | 163 |
| 471637 | `Per-r` | 139 | 145 |
| 518053 | `Per-r` | 168 | 150 |
| 657950 | `Per-r` | 149 | 156 |
| 732333 | `Per-g` | 83 | 77 |

Section 2.1 says both bands are phase-folded using the *common* Table 2 period. The public text therefore does not establish why a zero independent `Per-g`/`Per-r` should exclude these 17 objects. A minimum row-count rule also does not explain them.

## Reproduction

Download `scientific-validation-heavy.zip` from the Artifacts section of [run 38789483790](https://github.com/saeed92m/ztf-classifier/actions/runs/38789483790), then run:

```bash
sha256sum scientific-validation-heavy.zip
```

Expected SHA-256:

```
28c704671e392fc0e983eee7e8df5ed0f5fd29bce80acd0c2c2cc0218d5da747
```

The archived source records and audit JSON are under `ztf_periodic_730k/`; the two provenance ledgers are under `ztf_periodic_730k/provenance/`. The TSV contains one row per candidate-only SourceID and the raw Table 2 record, plus g/r row counts and qualifying-row summaries. Its header has 21 columns; all 11,602 rows parse using Python's tab-delimited `csv.DictReader` with zero malformed rows.

## What would close the blocker

1. Obtain and inspect the authors' preprocessing implementation or an authoritative description of the exact selection operation.
2. Ask the authors whether invalid Table 2 mean magnitudes were excluded because of the `m_gr` feature and why zero per-band periods exclude the residual 17 despite a valid common period and abundant two-band detections.
3. Re-run the full object-level audit against the confirmed rule and preserve source hashes, code revision, FP/FN IDs, and regression coverage.
4. Keep the scientific gate fail-closed until the historical rule is supported by source evidence.

No threshold tuning, flag-based filtering, hardcoded IDs, or baseline changes are authorized by this diagnostic.

## Sources

- Chan et al. (2022), [*Searching for Anomalies in the ZTF Catalog of Periodic Variable Stars*, Sections 2.1 and 2.3](https://doi.org/10.3847/1538-4357/ac69d4).
- Published labeled membership: [Zenodo record 5764899](https://zenodo.org/records/5764899).
- Original CPVS source archive: [Zenodo record 3886372](https://zenodo.org/records/3886372).
- Membership audit and source hashes: [Scientific Validation run 38789483790](https://github.com/saeed92m/ztf-classifier/actions/runs/38789483790).
