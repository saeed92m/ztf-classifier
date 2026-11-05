# Park MVP Delivery Plan and Acceptance Record

**Status date:** 2026-11-05  
**Delivery tracker:** Issue #158  
**DR24 integration tracker:** Issue #253  
**Scientific baseline:** v0.2.0 — frozen  
**Software release:** v1.0.1 — immutable  
**Disposition:** NOT ACCEPTED — implementation and source-backed demonstration are incomplete.

## 1. Delivery objective
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
| G1 — bounded DR24 raw acquisition | Current-head tests plus successful source-backed indexed retrieval and hashes | PARTIAL; PR #264 is Draft |
| G2 — OID identity and grouping | Curated mapping with evidence, ambiguity handling, regression tests | NOT ACCEPTED |
| G3 — photometry/time/QC contract | Versioned transformations, source semantics, fixture tests, retained raw values | NOT ACCEPTED |
| G4 — 5–10 object smoke test | End-to-end API/Workbench run with manifest and per-object status | NOT VERIFIED |
| G5 — 30–50 object demonstration | Reproducible run, visual inspection, exports, failure log | NOT VERIFIED |
| G6 — scientist-facing workflow | Reviewer completes supported workflow without terminal use | PARTIAL; Workbench exists, guided flow not accepted |
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

## 9. Immediate acceptance decision
The repository is a useful engineering and scientific baseline. It is not yet an accepted DR24-backed Park demonstrator. The next decisive proof is a successful 5–10 object end-to-end run through the application with source identity, QC, visualization, exports, and a reproducibility manifest. The 30–50 object demonstration follows only after that smoke test passes.
