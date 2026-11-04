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
- Candidate-only objects: 11,602. All have qualifying finite-SNR detections in both bands in the retained diagnostics. All 11,602 also have a finite positive common `Per` value in Table 2. However, only 132 have positive `gmag`, 11,487 have positive `rmag`, 127 have positive `Per-g`, and 11,480 have positive `Per-r`. The parent metadata fields are incomplete for every one of these objects: 11,580 lack both positive mean-magnitude and per-band-period pairs; 17 have both mean magnitudes but incomplete band periods; 5 have both per-band periods but incomplete mean magnitudes. Table 2 also reports `Ng=0` for 13 and `Nr=0` for 1 of these candidate-only objects, despite the retained raw-archive diagnostic finding qualifying SNR detections in both bands. This count mismatch needs source-level reconciliation.
- Published-only objects: zero.
- The later paper *Searching for Anomalies in the ZTF Catalog of Periodic Variable Stars* (DOI: https://doi.org/10.3847/1538-4357/ac69d4), Section 2.1, states that it extracted 730,184 of 781,602 objects using at least one 2.5σ g-band and 3σ r-band detection, then phase-folded both bands using the common period from Table 2. The accessible method text does not state that all four Table 2 fields `gmag`, `rmag`, `Per-g`, and `Per-r` must be positive. It specifically says the common period from Table 2 is used for phase folding; all 11,602 candidate-only objects have that common period as a finite positive value. This is not the same as requiring both per-band period fields `Per-g` and `Per-r`. The exact intersection with the four-field condition is therefore diagnostic evidence, not proof of author intent or an established selection rule. The original preprocessing implementation or author clarification is still needed.

## Evidence and limitations

- Full parent/reference reconciliation and hashes: workflow run 41367972395, artifact 13108147605.
- Fresh source-backed candidate derivation: workflow run 41417144949, job 125183681255, which again returned 741,786 candidates against the expected 730,184 count.
- The independent membership audit in the fresh run failed on a dashed VizieR separator row; its audit result is not a successful current-head reproduction.
- The 100/1,000-object stratified samples were independently reproduced exactly; see `CPVS_FIXED_SAMPLE_REPRODUCTION_2026-11-04.md`.

## Decision

Keep the CPVS membership blocker open. Do not alter SNR thresholds, add the four-field condition to the production selector, or change v0.2.0. The next steps are to complete the bounded parser/crosswalk tests and investigate the original archive-to-Table2 identifier/row-coverage mismatches.


## Table 2 / lightcurve archive schema cross-check

The original CDS `table2.ReadMe` defines:
- `Per`: the common period.
- `Per-g` and `Per-r`: periods determined separately in each band; zero means unknown.
- `gmag` and `rmag`: mean band magnitudes; zero means unknown.
- `Ng` and `Nr`: number of detections in the g and r bands.

The same ReadMe lists 89,697,393 rows for each of `ztf2g.dat` and `ztf2r.dat`. The retained Table 2 `Ng` sum is 89,702,309, which differs from the g archive row count by 4,916. The full g-band Seq reconciliation identifies 91 per-object count mismatches: 56 deficits and 35 surpluses. The net per-Seq delta is -5,048; the orphan Seq 615172 adds 132 rows, giving the observed total deficit of 4,916.

This is a source-level count/identifier integrity issue. The ReadMe's definition of `Per` also confirms that common period and per-band periods are distinct. Since all 11,602 candidate-only objects have a positive common `Per`, missing common period is not a supported explanation for the membership difference.
