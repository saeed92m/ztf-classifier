# Park MVP Delivery Plan and Acceptance Record

**Status date:** 2026-11-07  
**Delivery tracker:** Issue #158  
**DR24 integration tracker:** Issue #253  
**Scientific baseline:** v0.2.0 — frozen  
**Software release:** v1.0.1 — immutable  
**Disposition:** NOT ACCEPTED — implementation and source-backed demonstration are incomplete.

## 1. Delivery objective
## Institutional dossier reconciliation

The original September 2026 Park presentation and project proposal remain unchanged as submitted records. A Persian technical status addendum dated 2026-11-07 has been prepared to qualify claims about live demonstration, DR24 classification, anomaly detection, dataset scale, staffing and schedule against current evidence: [PARK_TECHNICAL_STATUS_ADDENDUM_2026-11-07.fa.md](acceptance/PARK_TECHNICAL_STATUS_ADDENDUM_2026-11-07.fa.md). Attach this addendum when sharing the original dossier as a current status package. Do not silently replace the submitted PDFs.

Deliver a real, bounded, reproducible ZTF analysis demonstration for the Tabriz Science and Technology Park. The first acceptance target is a working application workflow, not a claim that the complete scientific platform or a production DR24 classifier is finished.

A reviewer must be able to select or load a supported sample, inspect source data and quality, run supported analysis, inspect provenance and limitations, and export results with a reproducibility record.

## 2. Two separate scientific lanes

### Lane A — DR24 exploratory analysis
This lane is for source-native data exploration. It is not validated v0.2.0 model inference.

First demonstration:
- 5–10 objects for smoke testing, then 30–50 objects for the guided demonstration.
- Use bounded indexed DR24 HATS objectid retrieval. Never download the full DR24 archive.
- Begin with g and r where valid source identity and data coverage are established.
- Preserve raw hmjd, mag, magerr, clrcoeff, catflags, objectid, filterid, fieldid, rcid, coordinates, catalog epoch counts, retrieval time, source release, schema identity, and content hashes.
- Keep each ZTF OID separate until an evidence-backed cross-OID mapping exists. A ZTF OID is not automatically an astrophysical-source identifier.
- Display missing rows, malformed records, excluded epochs, and retrieval failures with explicit reasons.
- Export source-native records, QC summaries, plots, object-level analysis, and a run manifest.

The first deliverable may provide descriptive statistics, cadence/coverage diagnostics, light-curve visualization, and versioned exploratory features. It must not claim a DR24 classifier or validated astrophysical discovery.

### Lane B — Frozen v0.2.0 reference inference
This lane uses only the frozen, supported feature contract and its matching model artifact:
- 42 features in final_feature_set_v0.2;
- frozen class order and schema contract;
- production artifact model_baseline_v0.2_production/artifact;
- historical cutoff 59447.224132;
- existing schema 1.1 diagnostics and fail-closed scientific gate.

Do not feed native DR24 measurements into this model unless a separately reviewed and validated mapping proves compatibility. Do not retrain or overwrite the baseline as part of the Park MVP.

ALeRCE labels are benchmark/reference labels. They are not independent astrophysical ground truth.

## 3. Source semantics and QC
The raw acquisition layer must preserve source values. It must not silently:
- relabel HMJD as geocentric MJD;
- apply color correction without source color and the relevant calibration definition;
- equate catflags == 0 with a documented production-quality policy;
- merge OIDs based only on positional proximity;
- substitute ALeRCE when DR24 retrieval fails.

For exploratory QC, report raw catflags distributions, bit-15 (32768) epochs as a separate cloud/moon diagnostic, strict catflags==0 counts separately, non-finite values, non-positive magnitude errors, per-band counts, time coverage, cadence gaps, and missing-band status.

Any exclusion rule must have a version, rationale, and recorded effect on row counts. Raw records must remain recoverable.

## 4. Required application workflow
1. Select source: DR24 exploratory source or the separately supported frozen-reference path. Show the actual source; no silent fallback.
2. Select sample: curated object/OID manifest with source identity and selection rationale.
3. Acquire: bounded indexed retrieval with timeout, retry, and explicit partial-failure handling.
4. Validate: schema, identity, duplicates, row counts, finite values, filter/partition metadata, and payload hashes.
5. Inspect: searchable object list, per-band light curves, quality diagnostics, and missing-data reasons.
6. Analyze: only transformations/features supported by the selected lane and versioned contract.
7. Review: show model/source identity, uncertainty and OOD only where the matching validated artifact supports them. Do not equate OOD with astrophysical anomaly.
8. Export: CSV/Parquet as applicable, plots, technical report, run manifest, object/OID list, warnings, and hashes.
9. Reproduce: record environment, code revision, configuration, source query, data versions, and output hashes.

## 5. Acceptance gates
| Gate | Required evidence | Status on 2026-11-05 |
|---|---|---|
| G0 — frozen baseline protection | No change to v0.2.0 model, 42-feature contract, class order, or benchmark | PRESERVED by plan; verify each candidate PR |
| G1 — bounded DR24 raw acquisition | Current-head tests plus successful source-backed indexed retrieval and hashes | VERIFIED for bounded retrieval; adapter remains under review |
| G2 — OID identity and grouping | Curated mapping with evidence, ambiguity handling, regression tests | NOT ACCEPTED |
| G3 — photometry/time/QC contract | Versioned transformations, source semantics, fixture tests, retained raw values | NOT ACCEPTED |
| G4 — 5–10 object smoke test | End-to-end API/Workbench run with manifest and per-object status for confirmed sources | PARTIAL; component-level live tests pass, but the accepted 5–10 confirmed-source workflow is not complete |
| G5 — 30–50 object demonstration | Reproducible run, visual inspection, exports, failure log | NOT VERIFIED |
| G6 — scientist-facing workflow | Reviewer completes supported workflow without terminal use | PARTIAL; live browser smoke passes, guided scientist workflow not accepted |
| G7 — scientific performance | Independent labeled evaluation, object-level and temporal leakage checks, metrics and calibration | NOT ACCEPTED |
| G8 — Park handover package | Demo procedure, technical report, limitations, environment, evidence bundle | NOT ACCEPTED |

A green ordinary CI run does not pass a source-backed or scientific gate. Skipped tests remain NOT VERIFIED.

## 6. Execution order

### P0 — establish a reproducible small-sample path
- Review and complete the raw DR24 adapter without expanding its scientific scope.
- Define a curated OID mapping for the first sample. Keep uncertain associations unresolved.
- Pin a small sample and save its exact OID manifest and retrieval evidence.
- Run 5–10 objects through acquisition, QC, visualization, and export.

### P1 — make the application usable
- Add explicit source selection and source identity display.
- Add HMJD-aware axis labels and retain the time-coordinate name in exports.
- Show filter/field/RCID provenance, epoch counts, flag distributions, and exclusions.
- Add object-level success/partial/failure states.
- Add a reproducibility bundle and offline replay from pinned local data.

### P2 — complete the guided demonstration
- Run 30–50 curated objects.
- Review all failed and partial objects.
- Validate deterministic outputs and hashes.
- Rehearse from a clean environment.
- Generate the Park technical report from actual run outputs.

### P3 — expand scientific scope
Build the larger labeled dataset only after licensing, taxonomy, identity, and provenance gates. Perform leakage-safe temporal evaluation. Validate calibration, abstention, OOD, and anomaly methods independently. Treat the 100,000-light-curve target as a future milestone, not a current achievement.

## 7. Work outside this critical path
- CPVS exact membership reproduction remains a separate scientific blocker. Do not weaken criteria or merge exploratory identity hypotheses into the Park demo.
- CIN is a proposed future architecture. No contributor network, annotation corpus, or production consensus system is claimed.
- Cross-platform self-contained installers remain a separate distribution milestone unless the Park requires them.
- Do not add paid infrastructure or download bulk DR24 data for this bounded demonstration.

## 8. Reporting rules
Separate implementation, automated tests, live source-backed evidence, scientific validation, and user-facing acceptance. Do not publish a completion percentage without a defined weighting method and current evidence. Do not claim readiness until G0–G6 pass for the declared demo scope. Do not claim scientific performance until G7 passes.


## 9. Evidence update — 2026-11-07

The evidence below updates the 2026-11-05 planning baseline. It does not change the acceptance definition or the frozen scientific baseline.

### Bounded DR24 source acquisition

1. **Three-OID direct HATS probe:** [workflow 42061697065](https://github.com/saeed92m/ztf-classifier/actions/runs/42061697065) completed successfully. Three requested OIDs returned 417 epochs (78, 123 and 216). The payload counts matched catalog `nepochs`. Artifact 13432467426 was retained. This is raw-source evidence only.
2. **Four-OID repeatability evidence:** [PR #269](https://github.com/saeed92m/ztf-classifier/pull/269) records two independent runs, 626 epochs across four OIDs, matching per-OID `nepochs`, and matching epoch CSV and summary JSON hashes across the two runs. The raw values were retained; no quality filtering or OID grouping was applied.
3. **FastAPI-to-HATS live smoke:** [workflow 42063653144](https://github.com/saeed92m/ztf-classifier/actions/runs/42063653144) passed one live API test in 70.05 seconds. Artifact 13430999878 was uploaded. This is a bounded route test, not the full application acceptance test.
4. **API failure contracts:** [workflow 42065074402](https://github.com/saeed92m/ztf-classifier/actions/runs/42065074402) passed the failure-contract job.
5. **Workbench browser smoke:** [workflow 42275261463](https://github.com/saeed92m/ztf-classifier/actions/runs/42275261463) passed one browser test in 86.93 seconds. It exercised seven OIDs and 2,183 epochs, including descriptive QC, null-catflags handling, no epoch filtering, JSON export, and export-disabled behavior after missing/source failures. Artifact 13532578108 was retained.

### What these results establish

- Indexed HATS retrieval works for the listed OIDs.
- Catalog epoch counts match returned rows for the tested OIDs.
- Raw payloads and provenance can be retained in bounded artifacts.
- The API route has passed a live smoke test.
- The Workbench has passed a live browser interaction smoke test.
- Descriptive QC and raw export have passed the tested browser assertions.

### What these results do not establish

- The tested OIDs are not all confirmed astrophysical-source identities.
- No cross-OID grouping is accepted.
- No production epoch-selection or quality policy is accepted.
- No HMJD conversion, photometric color correction, DR24 feature contract, or classifier inference is validated.
- The seven-OID browser test is not the 5–10 confirmed-source end-to-end acceptance test.
- The 30–50 confirmed-source guided Park demonstration is not complete.
- No scientific performance, calibration, OOD, anomaly-detection or astrophysical-discovery claim follows from these tests.

### Revised acceptance status

| Gate | Updated status | Evidence / remaining requirement |
|---|---|---|
| G0 — frozen baseline protection | PRESERVED | No model, feature, taxonomy, benchmark or cutoff change in the cited DR24 work. Continue checking each PR. |
| G1 — bounded DR24 raw acquisition | VERIFIED for tested OIDs | Direct HATS, repeatability, API and browser smoke evidence above. This does not imply broad coverage. |
| G2 — OID identity and grouping | NOT ACCEPTED | Curated, evidence-backed crosswalk and ambiguity handling remain required. |
| G3 — photometry/time/QC contract | PARTIAL | Raw fields and descriptive QC are retained. Production transforms and selection policy are not validated. |
| G4 — 5–10 object smoke test | PARTIAL | Component-level tests pass. Still need 5–10 confirmed sources through one complete app workflow and a reproducibility bundle. |
| G5 — 30–50 object demonstration | NOT VERIFIED | Run and review the guided sample after G4 passes. |
| G6 — scientist-facing workflow | PARTIAL | Browser smoke passes. A reviewer-led workflow without terminal use is not accepted. |
| G7 — scientific performance | NOT ACCEPTED | Independent labels, leakage-safe splits, metrics, calibration and uncertainty evaluation are still required. |
| G8 — Park handover package | NOT ACCEPTED | Requires actual demo outputs, limitations, runbook, environment and evidence bundle. |

### Immediate next action

Do not expand the sample yet. First select 5–10 objects with defensible source identity, freeze their OID manifest, run the complete API-to-Workbench-to-QC-to-export workflow, and retain a replayable evidence bundle. Expand to 30–50 objects only after this test passes.

## 10. Immediate acceptance decision
The repository is a useful engineering and scientific baseline. It is not yet an accepted DR24-backed Park demonstrator. The next decisive proof is a successful 5–10 object end-to-end run through the application with source identity, QC, visualization, exports, and a reproducibility manifest. The 30–50 object demonstration follows only after that smoke test passes.
