# Astronomical Data Analysis & Discovery Platform — Product Roadmap

**Status date:** 2026-11-10  
**Software release:** v1.0.1 (immutable)  
**Park delivery tracker:** Issue #158  
**DR24 application integration:** Issue #253  
**CPVS scientific blocker:** Issue #170

**Current continuity record:** [Handbook v3.0](../HANDBOOK_UPDATED_v3.0.md) · [Project Status & Execution Ledger — 2026-11-07](../PROJECT_STATUS_AND_EXECUTION_LEDGER_2026-11-07.md) · [Park MVP delivery plan](../PARK_MVP_DELIVERY_PLAN_2026-11-05.md)

## Evidence refresh — 2026-11-10

**Park prototype status:** bounded raw ZTF DR24 HATS sample retrieved and packaged for offline inspection. The standalone v0.3 demo contains 30 OID records and 4,046 epochs. All 30 records are g-band records from one HATS field/rcid sample. They are not confirmed unique physical sources. The complete 150-row metadata snapshot file is not in the downloaded evidence bundle.

**Current acceptance boundary:** this is a raw-data explorer, not a DR24 classifier. It does not run v0.2.0 inference, derive the frozen 42 features from DR24, or validate DR24 classification/calibration/OOD performance.

**Latest live UI evidence:** the 30-OID Workbench test predicate was corrected at commit `82f0812d07005dd521361f127f3e9f7d493060af`. Live workflow [#42830475350](https://github.com/saeed92m/ztf-classifier/actions/runs/42830475350) completed successfully. It passed 10-OID repeatability, 30-OID source retrieval in three batches and the 30-OID Workbench/browser walkthrough in three batches; no console/page errors. This is an OID-level UI acceptance on the delivery branch, not proof of 30 distinct physical sources or scientific inference.

**Progress scoring — 2026-11-10:** active project 48%; raw-data demo v0.3 82%; Park MVP acceptance gates 33%. These are equal-weight evidence-completion scores, not time estimates or historical trends. See [Park Pilot Readiness Report](../acceptance/PARK_PILOT_READINESS_2026-11-10.fa.md), [Acceptance Form Reconciliation](../acceptance/PARK_ACCEPTANCE_FORM_RECONCILIATION_2026-11-10.fa.md), [Handbook v3.0](../HANDBOOK_UPDATED_v3.0.md), and [Execution Ledger — 2026-11-10](../PROJECT_STATUS_AND_EXECUTION_LEDGER_2026-11-10.md).

The immutable v0.2.0 baseline is unchanged. CPVS remains a separate unresolved research workstream. CIN remains proposed and is not on the Park demo critical path.

---

## Executive status
Institutional submission claims are reconciled in the Persian [Park Technical Status Addendum — 2026-11-07](../acceptance/PARK_TECHNICAL_STATUS_ADDENDUM_2026-11-07.fa.md). The original submitted PDFs remain unchanged; use the addendum when presenting current status.

The repository has a released Python package, a frozen v0.2.0 scientific baseline, production inference interfaces, an API-backed Workbench, and bounded DR24 research evidence. It does not yet have an accepted DR24-backed 30–50-object end-to-end Park demonstration.

Do not use an old readiness percentage as a current completion measure. A new percentage requires a defined weighting method and current evidence for every scored item.

## Non-negotiable constraints
- Preserve the v0.2.0 model, 42-feature schema, class order, benchmark, historical cutoff, and fail-closed scientific gate.
- Keep ALeRCE labels as benchmark/reference labels, not independent ground truth.
- Do not treat OOD as astrophysical anomaly detection.
- Preserve raw data, source identity, time basis, quality flags, and provenance.
- Do not download the full multi-terabyte DR24 archive.
- Skipped scientific tests are NOT VERIFIED, not PASS.
- No merge, release, or scientific acceptance based only on ordinary CI.

## P0 — Park MVP: DR24-backed exploratory workflow
Acceptance target: a scientist can run a bounded, reproducible demonstration without terminal use for the normal workflow.

1. Review the raw DR24 adapter in PR #264. Its current-head CI passed; keep the PR unmerged until review and dependencies are resolved.
2. Define a curated, evidence-backed OID mapping for the demo sample. Keep ambiguous identities separate.
3. Complete source-aware acquisition behind the application service boundary. Keep ALeRCE as a separate source; never silently fall back.
4. Define a versioned DR24 raw/QC contract. Preserve HMJD and native photometry; do not invent color correction or OID grouping.
5. Complete a 5–10-object smoke test with confirmed source identity, per-object status, hashes, QC, plots, and manifest. Component-level API and browser smoke tests pass, but this full acceptance test remains open.
6. Integrate source selection, provenance, QC, missing-data reasons, and exports into the Workbench.
7. Complete a 30–50-object guided demonstration and offline replay.
8. Generate the Park report from actual run artifacts.

The first DR24 lane is exploratory. It is not the frozen v0.2.0 classifier and must not claim validated DR24 classification performance.

## P1 — Frozen baseline demonstration
- Verify the local production artifact and its manifest/hashes.
- Run inference only on inputs that match the frozen 42-feature schema.
- Preserve class order, cutoff, calibration/conformal/OOD artifact identities.
- Record all missing artifact or data dependencies as blockers.
- Do not retrain or alter the baseline.

## P2 — Scientific expansion
- Build the 100,000-light-curve labeled subset only after source identity, taxonomy, licensing, and provenance gates.
- Use object-level and temporal leakage-safe splits.
- Report per-class metrics, calibration, abstention, and external validation only when supported by labeled data.
- Evaluate anomaly detection separately from OOD.
- Keep the 150-object v0.2.0 benchmark distinct from the Park dataset.

## Parallel workstreams outside the Park critical path
### CPVS
Issue #170 remains unresolved. The previously reported comparison has 11,602 candidate-only IDs and zero published-only IDs. The root cause is not established. Keep all thresholds and scientific criteria unchanged. Do not allow this workstream to block the bounded DR24 application demo.

### Cosmic Intelligence Network
CIN remains a proposed architecture. It has no verified production contributor network or annotation corpus. Defer runtime implementation until after the Park MVP.

### Distribution
The published v1.0.1 package is not a self-contained desktop installer. Windows/macOS/Linux installers and clean-machine acceptance remain a separate milestone unless the Park requires them for the initial demonstration.

## Evidence-based milestone gates
| Gate | Exit evidence | Current status |
|---|---|---|
| M0 — frozen baseline | Artifact/schema/class-order integrity | Baseline definition preserved; local artifact verification still required |
| M1 — raw DR24 adapter | Bounded indexed acquisition, schema and payload hashes | VERIFIED for tested OIDs; PR #264 remains under review |
| M2 — normalized exploratory data | Versioned QC and identity policy, fixture tests | PARTIAL; descriptive QC/export pass, production selection and identity policy not accepted |
| M3 — smoke test | 5–10 confirmed sources end-to-end with manifest | PARTIAL; component tests pass, complete acceptance workflow not verified |
| M4 — guided demo | 30–50 objects, Workbench, exports, offline replay | PARTIAL; 30 OID UI run passed, but source identity and full 30–50 guided acceptance remain open |
| M5 — scientific model expansion | Labeled dataset and leakage-safe independent evaluation | NOT ACCEPTED |
| M6 — distribution | Clean-machine platform packaging | NOT ACCEPTED |

No milestone is complete because code exists. Require the stated evidence and recorded acceptance.


## Evidence update — 2026-11-07

The following component-level results are verified for the tested OIDs:

- [Direct HATS probe](https://github.com/saeed92m/ztf-classifier/actions/runs/42061697065): 3 OIDs and 417 epochs; catalog `nepochs` matched returned rows; artifact 13432467426.
- [Repeatability evidence, PR #269](https://github.com/saeed92m/ztf-classifier/pull/269): two four-OID runs, 626 epochs, matching epoch CSV and summary JSON hashes.
- [FastAPI-to-HATS smoke](https://github.com/saeed92m/ztf-classifier/actions/runs/42063653144): one live test passed in 70.05 seconds; artifact 13430999878.
- [API failure contracts](https://github.com/saeed92m/ztf-classifier/actions/runs/42065074402): passed.
- [Workbench browser smoke](https://github.com/saeed92m/ztf-classifier/actions/runs/42275261463): one test passed in 86.93 seconds; seven OIDs, 2,183 epochs; artifact 13532578108.

These tests establish bounded acquisition, API connectivity, raw-data display, descriptive QC and JSON export for their tested cases. They do not establish physical-source identity, cross-OID grouping, production QC selection, HMJD/photometric transformations, DR24 features, classifier inference or scientific validity.

The seven-OID and 30-OID browser tests are not a 5–10 confirmed-physical-source end-to-end acceptance test. The 30-OID OID-level UI is now verified, but the 30–50 physical-source guided demonstration remains PARTIAL until identity/cross-match and a broader user session are accepted. Keep the next milestone focused on a complete, replayable 5–10 confirmed-source run.

## Next concrete action
Complete PR #264 review and build the smallest end-to-end DR24 exploratory path. The first measurable proof is the 5–10-object smoke test. Do not start with bulk data acquisition, CIN runtime, or a new model.
