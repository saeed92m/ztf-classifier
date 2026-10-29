# CPVS residual-17 audit (2026-10-30)

## Status

**Finding: strong empirical reconstruction rule; scientific root cause remains unresolved.** This report uses existing historical workflow artifacts. It does not claim the paper's authors explicitly used the metadata predicate below.

## Inputs and provenance

Historical artifact: `historical-cpvs-scientific-validation-heavy.zip`.

| Input | SHA-256 | Rows/IDs |
|---|---|---:|
| `ztf_periodic_730k/selected.tsv` | `699ff34bcf8dd4b5043eed48384973cb5109fd86ca260f831a502097370238df` | 741,786 candidate IDs |
| `ztf_periodic_730k/parent_metadata.tsv` | `3675b1274f73fcb15d47e7a780f194ef8fa335cd248c6ff53ea4f01559c86591` | 781,602 parent rows |
| `ztf_periodic_730k/membership_audit.json` | `4c1a082569820af26cbca80320a4913a00e1849446b0ca0205fc872b5ce89c5c` | Historical reference comparison |
| `ztf_periodic_730k/selection_diagnostics.json` | `7e763d8804a57d75d1633d0a4089a4a6ac5aa40bb4695964d35e645b67ad5b61` | Candidate residual diagnostics |

The reference membership in the historical audit is 730,184 objects. The original audit joined published ZTF names to Table 2 `Seq`; it did not equate Table 4's internal `ID` with `Seq`.

## Full candidate-set recomputation

The existing 741,786 candidate IDs were re-evaluated against all 781,602 rows of the archived parent metadata:

| Predicate applied to candidate IDs | Remaining | Removed at this step |
|---|---:|---:|
| Baseline reconstructed SNR rule: g >= 2.5 and r >= 3.0, finite/nonzero light-curve magnitudes | 741,786 | — |
| Additionally require parent mean `gmag != 0` and `rmag != 0` | 730,201 | 11,585 |
| Additionally require positive `Per-g` and `Per-r` | 730,184 | 17 |

The final 730,184 set equals the historical published membership under the audited ID crosswalk: intersection 730,184, candidate-only 0 after filtering, published-only 0. This is a reproducible set match. It is **not proof** that the authors defined membership by requiring all four metadata fields to be positive.

## The 17 residual objects

All have nonzero parent mean magnitudes and a positive common period `Per`. Each is missing one band-specific period field: 10 lack `Per-g`; 7 lack `Per-r`. They also have nonzero detection counts in both bands.

| SourceID | Type | Per (common) | gmag | rmag | Per-g | Per-r | Ng | Nr |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 9877 | RR | 0.4997498 | 16.127 | 15.856 | 0.4997498 | missing | 62 | 63 |
| 120746 | SR | 431.6131819 | 15.484 | 13.406 | missing | 431.6131819 | 61 | 71 |
| 127012 | SR | 476.4920949 | 16.712 | 14.901 | missing | 476.4920949 | 96 | 110 |
| 151010 | SR | 78.7717874 | 14.878 | 12.767 | missing | 78.7717874 | 87 | 75 |
| 191955 | SR | 149.7153742 | 19.412 | 19.118 | missing | 149.7153742 | 51 | 50 |
| 281946 | SR | 124.8894923 | 17.932 | 17.751 | 124.8894923 | missing | 245 | 204 |
| 287003 | SR | 239.1335439 | 19.826 | 16.740 | missing | 239.1335439 | 114 | 134 |
| 307249 | SR | 156.6939036 | 17.519 | 15.282 | missing | 156.6939036 | 156 | 156 |
| 378719 | BYDra | 3.0957918 | 18.772 | 17.491 | 3.0957918 | missing | 156 | 157 |
| 385223 | SR | 162.2483663 | 17.795 | 14.855 | 162.2483663 | missing | 122 | 112 |
| 409233 | SR | 106.7609377 | 18.197 | 14.745 | missing | 106.7609377 | 151 | 175 |
| 429716 | SR | 49.0058583 | 17.117 | 15.849 | missing | 49.0058583 | 171 | 187 |
| 440167 | SR | 75.7029163 | 18.231 | 15.603 | missing | 75.7029163 | 171 | 163 |
| 471637 | SR | 120.5594061 | 17.865 | 15.290 | 120.5594061 | missing | 139 | 145 |
| 518053 | SR | 29.7867349 | 18.312 | 15.815 | 29.7867349 | missing | 168 | 150 |
| 657950 | SR | 157.6106282 | 17.278 | 16.801 | 157.6106282 | missing | 149 | 156 |
| 732333 | SR | 128.1092097 | 16.405 | 13.497 | missing | 128.1092097 | 83 | 77 |

SHA-256 of the sorted SourceID list, one ID per line with trailing newline: `5d3f1673adfcc6206ee8feb4827ae3776894c68ebf1d535bca4680ad71f44507`.

## Alternate Zenodo membership

Zenodo record [10.5281/zenodo.5764899](https://zenodo.org/records/5764899) describes a CSV with 730,184 periodic transients. The existing independent audit of `1st_layer.csv` reports 730,184 unique names, zero unmapped names, all 730,184 names in the four-field Table 2 set, and 55 Table 2 four-field objects outside that reference set.

Because these 17 objects each lack either `Per-g` or `Per-r`, they fail that four-field predicate. Given the audited set inclusion, the set-based result is that **none of these 17 belongs to the Zenodo reference membership**. A direct per-name join is still desirable as an explicit per-object artifact; a targeted CI job was added to the draft PR, but its execution has not yet been verified.

## What the paper actually says

Chan et al. (2022), Section 2.1, states that the 730,184 light curves were selected with at least one 2.5-sigma detection in g and one 3-sigma detection in r. It then says both bands are phase-folded using the **common period** from Table 2 of Chen et al. (2020). It does **not** explicitly state that both band-specific fields `Per-g` and `Per-r` must be positive.

Source: https://doi.org/10.3847/1538-4357/ac69d4; accessible article text also indexed at https://arxiv.org/abs/2112.03306.

Therefore, the 17-object pattern narrows the discrepancy but does not establish the authors' intended selection logic. All 17 have a common period `Per`, so “no common period” is not a valid explanation. The remaining scientific question is why the documented per-band SNR rule, when reconstructed from the available single-exposure photometry, admits 11,602 IDs absent from the published set. Potential differences in exact detection/SNR semantics, photometry eligibility, preprocessing, or an undocumented catalog-membership constraint still need evidence.

## Guardrail

Do not change the production selector, SNR thresholds, benchmark baseline, or scientific acceptance criteria on the basis of this diagnostic alone. Keep CPVS exact reproduction marked **UNRESOLVED** until the direct Zenodo ID-level artifact and a source-supported root cause are verified.
