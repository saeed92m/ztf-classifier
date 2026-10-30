# CPVS residual-17 audit (2026-10-30)

## Status

**Finding: exact archived membership reconstruction is supported by both set-level comparison and a direct 17-object Zenodo join; author-intent/root-cause semantics remain unresolved.** No production selector or scientific acceptance criterion was changed.

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

### Set-theoretic verification of the reconstruction

The independent two-table audit artifact from workflow run `40953220220` establishes:

- Published membership \(P\): 730,184 unique names, all mapped to Table 2 `Seq`; zero unmapped and zero duplicate published names.
- Original SNR candidate set (C): 741,786 IDs; the historical comparison reports (P \subseteq C) (published-only count 0).
- Four-field parent-metadata set \(F\): 730,239 IDs; the two-table audit reports (P \subseteq F) (published count and intersection both 730,184).
- The local recomputation above establishes (|C \cap F| = 730,184).

Therefore (P \subseteq C \cap F), and (|P| = |C \cap F|); hence **(P = C \cap F)** for these archived inputs. This proves exact object-level membership reconstruction for the audited snapshot, rather than merely matching the final count. It does not establish why the authors' pipeline produced that set or whether the four-field predicate was their intended rule.

The independent two-table artifact records Table 2 SHA-256 `c5422312ca470592d11f5a614ac6558b3665413d7806e55915e96007c90d71f4` and Table 4 SHA-256 `b5453a8659935c5323cab3bca73a92ba71fd3964803ccab9464ec601853f7460`. Its verdict is `HYPOTHESIS_REFUTED` for the proposition that the four-field predicate alone defines published membership: 55 objects satisfy \(F\) but are not in \(P\). The SNR candidate condition is therefore essential to the reconstructed equality.

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

A targeted, direct per-object audit was completed in GitHub Actions run [41091772746](https://github.com/saeed92m/ztf-classifier/actions/runs/41091772746), on commit `c7eec0deb36a1e066295f69b40479a4ae5db811c`. It retrieved the Table 2 crosswalk for exactly the 17 requested `Seq` values, joined each to its ZTF `ID`, and compared those names against the `ID` column of the downloaded Zenodo `1st_layer.csv`.

The Zenodo archive passed the pinned MD5 check: `7fc6562d4208cbfa97366351984810e3`. The direct audit artifact reports **0/17 in reference and 17/17 not in reference**, with 730,184 unique names in the reference. The exact source-file hashes recorded in the JSON artifact are:

- targeted Table 2 response SHA-256: `edd4edae61e59b0d9d6db07465f6cb120ae23d90b00ede14f8c6b947d42a67b8`
- extracted Zenodo `1st_layer.csv` SHA-256: `c235df101bf7a130b5dccdd95b786ac347f2b7ef24fc49ed7ae989aa8625437b`
- uploaded audit ZIP SHA-256: `35bd613c79a5bf0d755cd29b76f3312d9a9244b6d80fc5292f4ee303fce280f1`

The artifact `cpvs-17-object-zenodo-membership-audit` is attached to that run. This is direct evidence that the 17 residual candidates are absent from the frozen Zenodo reference. It does **not** by itself prove the authors' exact intended selection logic or explain all upstream photometry/SNR semantics.

## What the paper actually says

Chan et al. (2022), Section 2.1, states that the 730,184 light curves were selected with at least one 2.5-sigma detection in g and one 3-sigma detection in r. It then says both bands are phase-folded using the **common period** from Table 2 of Chen et al. (2020). It does **not** explicitly state that both band-specific fields `Per-g` and `Per-r` must be positive.

Source: https://doi.org/10.3847/1538-4357/ac69d4; accessible article text also indexed at https://arxiv.org/abs/2112.03306.

Therefore, the 17-object pattern narrows the discrepancy but does not establish the authors' intended selection logic. All 17 have a common period `Per`, so “no common period” is not a valid explanation. The remaining scientific question is why the documented per-band SNR rule, when reconstructed from the available single-exposure photometry, admits 11,602 IDs absent from the published set. Potential differences in exact detection/SNR semantics, photometry eligibility, preprocessing, or an undocumented catalog-membership constraint still need evidence.

## Guardrail

Do not change the production selector, SNR thresholds, benchmark baseline, or scientific acceptance criteria on the basis of this diagnostic alone. The direct 17-object membership check is now verified, but keep the authors' intended selection semantics and upstream SNR/photometry root cause marked **UNRESOLVED** until source-supported evidence establishes them.
