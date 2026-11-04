# CPVS candidate/reference membership confusion matrix — 2026-11-04

## Definition

This comparison treats the published Table 4 / independently crosswalked Zenodo membership (730,184 unique IDs) as the reference label and the historical reconstructed candidate set (741,786 unique IDs) as the prediction. It is a membership comparison, not an independent astrophysical truth assessment.

Parent population: 781,602 unique Table 2 Seq IDs.

## Object-level counts

| | Published member | Published nonmember | Total predicted |
|---|---:|---:|---:|
| Reconstructed candidate | TP 730,184 | FP 11,602 | 741,786 |
| Not reconstructed candidate | FN 0 | TN 39,816 | 39,816 |
| Total reference | 730,184 | 51,418 | 781,602 |

## Derived membership metrics

- Precision: 730,184 / 741,786 = 98.4359%.
- Recall: 730,184 / 730,184 = 100%.
- Specificity: 39,816 / 51,418 = 77.4359%.
- Accuracy: (730,184 + 39,816) / 781,602 = 98.5156%.
- False-positive rate: 11,602 / 51,418 = 22.5641%.

These values describe agreement with the published membership list only. They must not be presented as classifier performance or astrophysical false-positive/false-negative rates.

## Additional diagnostics

- The candidate ∩ four-field-positive metadata set has 730,184 IDs and matches the published reference exactly.
- The four-field-positive parent set contains 730,239 IDs, including 55 noncandidate/nonmember controls.
- Candidate-only objects: 11,602. All have qualifying finite-SNR detections in both bands in the retained diagnostics. The parent metadata fields are incomplete for every one of these objects: 11,580 lack both positive mean-magnitude and period pairs; 17 have both mean magnitudes but incomplete band periods; 5 have both periods but incomplete mean magnitudes.
- Published-only objects: zero.
- The paper's stated two-band SNR rule does not document the four-field-positive Table 2 condition. The exact intersection is therefore diagnostic evidence, not proof of author intent.

## Evidence and limitations

- Full parent/reference reconciliation and hashes: workflow run 41367972395, artifact 13108147605.
- Fresh source-backed candidate derivation: workflow run 41417144949, job 125183681255, which again returned 741,786 candidates against the expected 730,184 count.
- The independent membership audit in the fresh run failed on a dashed VizieR separator row; its audit result is not a successful current-head reproduction.
- The 100/1,000-object stratified samples were independently reproduced exactly; see `CPVS_FIXED_SAMPLE_REPRODUCTION_2026-11-04.md`.

## Decision

Keep the CPVS membership blocker open. Do not alter SNR thresholds, add the four-field condition to the production selector, or change v0.2.0. The next steps are to complete the bounded parser/crosswalk tests and investigate the original archive-to-Table2 identifier/row-coverage mismatches.
