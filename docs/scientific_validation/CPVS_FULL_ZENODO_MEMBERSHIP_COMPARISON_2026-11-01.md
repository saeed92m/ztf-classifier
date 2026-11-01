# CPVS full Zenodo membership comparison — 2026-11-01

## Result

**Status: exact membership reconstruction remains UNRESOLVED.**

A full object-level comparison was completed between the retained historical candidate IDs and a fresh full crosswalk of the frozen Zenodo membership archive to the actual Table 2 `Seq` / light-curve `SourceID` namespace.

| Set | Count |
|---|---:|
| Parent Table 2 objects | 781,602 |
| Frozen Zenodo published membership | 730,184 |
| Historical reconstructed candidates | 741,786 |
| Intersection | 730,184 |
| Candidate-only | 11,602 |
| Published-only | 0 |

All published membership IDs are present in the candidate set. The 11,602 candidate-only IDs remain unexplained. This result does **not** resolve the scientific blocker.

## Source and join provenance

- GitHub Actions run: [41299576448](https://github.com/saeed92m/ztf-classifier/actions/runs/41299576448), completed successfully on PR head `7c73a4a9d2260e080300303e6aac826630369539`.
- Full crosswalk artifact: `cpvs-full-zenodo-membership-crosswalk`.
- Reference archive: Zenodo DOI `10.5281/zenodo.5764899`, `1st_layer.csv`.
- Join: Zenodo ZTF `ID` → Table 2 ZTF `ID` → Table 2 `Seq` (light-curve `SourceID`).
- Table 2 rows mapped: 781,602; unique Seq values: 781,602; Seq range: 1–781,604.
- Published unique names and mapped Seq IDs: 730,184.
- Unmapped published names: 0.
- Raw Table 4 bytes were **not** used. This is a full crosswalk to the frozen Zenodo `1st_layer.csv` membership, not a direct byte-level Table 4 comparison.

## SHA-256 provenance

| Input/output | SHA-256 |
|---|---|
| Table 2 VizieR crosswalk | `d67ed2044ed3889e8056cb2b793670b1e0cc88d5073f20dabb47e5e27e1c7dd4` |
| Zenodo `1st_layer.csv` | `c235df101bf7a130b5dccdd95b786ac347f2b7ef24fc49ed7ae989aa8625437b` |
| Historical candidate file bytes | `699ff34bcf8dd4b5043eed48384973cb5109fd86ca260f831a502097370238df` |
| Sorted candidate IDs | `4e784952ac7a41f08ae78e04415f5b1dc4e5162d38091838c8725212ea7fe9fe` |
| Sorted published membership IDs | `18fba7523a4f66fa2314d017433e3ef8bdbe85f1980557bc1f1e0dc61094774c` |
| Sorted intersection IDs | `18fba7523a4f66fa2314d017433e3ef8bdbe85f1980557bc1f1e0dc61094774c` |
| Sorted candidate-only IDs | `b891e2ef5a79841f08ae78e04415f5b1dc4e5162d38091838c8725212ea7fe9fe` |
| Candidate-only TSV | `895559983a90a08b56d572f8f767fe19df4fd4324177f6e5edc0d92f6f2e03bf` |

The complete candidate-only identifier list is in [CPVS_CANDIDATE_ONLY_11602_2026-11-01.tsv](CPVS_CANDIDATE_ONLY_11602_2026-11-01.tsv).

## Rechecked parent metadata for all 11,602 residual IDs

All 11,602 candidate-only IDs were found in the retained parent metadata table.

| Diagnostic | Count |
|---|---:|
| Missing `gmag` | 11,470 |
| Missing `rmag` | 115 |
| Missing at least one of `gmag` / `rmag` | 11,585 |
| Missing `Per-g` | 11,475 |
| Missing `Per-r` | 122 |
| Both magnitudes present, but at least one band period missing | 17 |
| `Ng = 0` | 13 |
| `Nr = 0` | 1 |

These fields overlap. The counts above are diagnostics, not a statement of the original authors' selection logic. The four-field metadata predicate is not accepted as the production selection rule. Earlier comparison of that predicate still had 55 objects outside the published membership.

## Interpretation and limitations

1. The full Zenodo crosswalk independently confirms the historical set cardinalities and the 11,602 residual IDs in the Table 2 Seq namespace.
2. The zero published-only result does not explain the candidate-only population.
3. The residuals pass the retained exact per-band SNR diagnostics. The metadata patterns above may explain why they differ from the published list, but they do not prove the intended CPVS selection procedure.
4. The full membership crosswalk is a new run result. The candidate set and parent metadata are retained historical artifacts from the earlier heavy run, not a fresh full photometry reconstruction on the current PR head.
5. No production selector, SNR threshold, model, feature set, class order, v0.2.0 baseline, or scientific acceptance criterion was changed.

## Next required work

1. Acquire and hash raw Table 4 bytes or an authoritative publisher-provided equivalent, then independently reproduce the ZTF-name-to-Seq crosswalk.
2. Compare the full raw reference IDs with the candidate set and retain exact per-object provenance for every residual.
3. Establish the published selection and detection/SNR semantics from source documentation or author/publisher evidence.
4. Reproduce the 100- and 1,000-object samples against this fresh membership crosswalk, and label the reference definition explicitly.
5. Keep Issue #170 open and fail-closed until the 11,602 residuals have a source-supported explanation.

**Disposition: CPVS exact reconstruction remains an open scientific validation blocker.**
