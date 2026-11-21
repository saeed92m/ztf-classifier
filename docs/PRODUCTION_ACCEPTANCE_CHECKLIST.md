# Production Acceptance Checklist — Current Status

**Status date:** 2026-11-19  
**Main revision reviewed:** `dcedccf50ae5a4541ababc29cfc7471a7d0ea14a`

## Current disposition

**Engineering CI:** PASS  
**Bounded raw DR24 demonstrator:** NOT YET VERIFIED for this handoff  
**Park MVP:** NOT ACCEPTED  
**Validated DR24 classifier:** NOT ESTABLISHED  
**Final product:** IN DEVELOPMENT

Main CI #44515762167 passed with 702 tests passed, 13 skipped, and 9 warnings. Format, lint, runtime smoke, package build, dependency audit, and CI gate passed.

Scientific Validation #44515762163 completed five jobs. It acquired a 150-row DR24 Objects Table response, a separate 150-row live ALeRCE response, and the frozen ALeRCE reference manifest. The two live 150-row responses are not cross-matched. They do not form a labeled DR24 evaluation cohort.

The original v0.2.0 production model artifact is not available in the accessible repository, release assets, or retained CI reports (Issue #282). At least seven production-inference tests remain skipped because the original artifact or shared inputs are unavailable.

## Acceptance gates

| Gate | Requirement | Current status | Evidence required to close |
|---|---|---|---|
| G0 | Preserve v0.2.0 baseline, 42 features, class order, cutoff, and taxonomy | PASS for current reviewed revision | Repeat baseline integrity checks after any scientific change |
| G1 | Bounded DR24 HATS acquisition and raw payload parity | PARTIAL | Current pinned two-OID live test passes; retain response counts and hashes |
| G2 | Physical-source identity and OID association | NOT ACCEPTED | AOIC identity ledger with evidence and ambiguity states |
| G3 | Time, photometry, flags, and QC semantics | NOT ACCEPTED | Approved source-specific contracts and regression tests |
| G4 | DR24 source selection through the normal application service | PARTIAL | End-to-end API/Workbench source selection; no silent fallback |
| G5 | Complete predeclared Park cohort | NOT ACCEPTED | Immutable cohort manifest, all records acquired or explained |
| G6 | Feature mapping and model readiness | BLOCKED | Authenticated original model artifact or separately versioned validated model |
| G7 | Calibration, conformal, OOD, and anomaly semantics | NOT ACCEPTED | Independent held-out evidence; separate result channels |
| G8 | Full Workbench workflow | NOT ACCEPTED | Full cohort completes through normal UI and exports a run manifest |
| G9 | Repeatability and independent evaluation | NOT ACCEPTED | Full rerun hash comparison and appropriate independent reference evaluation |
| G10 | Clean installation, security, backup, restore, and handover | NOT ACCEPTED | Clean-machine evidence, license decision, backup/restore test, user guide |

## Laboratory demonstrator gate

The current raw Explorer may demonstrate only:
- bounded public DR24 HATS retrieval;
- source-native light-curve display;
- diagnostic QC;
- acquisition provenance;
- raw JSON export.

The pinned two-OID live parity test and local Workbench procedure must pass before the demonstrator is marked READY WITH LIMITATIONS.

The previous seven-OID Workbench smoke with 2,183 epochs is historical raw retrieval/display evidence. It does not close the current pinned test or full-cohort acceptance.

## Product-level scientific gate

A green engineering CI run is not scientific acceptance. Source-backed jobs must acquire and validate the intended evidence. Skipped tests are not PASS. The current 150-row DR24 and ALeRCE snapshots are separate, unpaired evidence sets.

## Frozen model gate

The original `baseline_v0.2` artifact is not available in accessible remote sources. Do not substitute the schema-1.1 lab-smoke artifact. Keep production inference BLOCKED until the original artifact and trusted hashes are recovered or a new model is separately versioned and validated.

## CPVS research gate — separate from Park

Issue #170 remains UNRESOLVED. The recorded Seq-based comparison has 11,602 candidate-only objects and zero published-only objects. Reverify source artifacts before describing the numbers as a fresh result. Do not tune thresholds to force equality. CPVS is not a blocker for the raw DR24 demonstrator.

## Definition of done

A gate is closed only when the required evidence is retained and reviewed. A code path, a successful small sample, or a green workflow with skipped required evidence does not close a product or scientific gate.
