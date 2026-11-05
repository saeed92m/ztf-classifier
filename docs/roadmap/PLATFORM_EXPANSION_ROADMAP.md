# Astronomical Data Analysis & Discovery Platform — Product Roadmap

**Status date:** 2026-11-05  
**Software release:** v1.0.1 (immutable)  
**Park delivery tracker:** Issue #158  
**DR24 application integration:** Issue #253  
**CPVS scientific blocker:** Issue #170

## Executive status
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

1. Review the raw DR24 adapter in PR #264 and verify current-head checks.
2. Define a curated, evidence-backed OID mapping for the demo sample. Keep ambiguous identities separate.
3. Complete source-aware acquisition behind the application service boundary. Keep ALeRCE as a separate source; never silently fall back.
4. Define a versioned DR24 raw/QC contract. Preserve HMJD and native photometry; do not invent color correction or OID grouping.
5. Complete a 5–10-object smoke test with per-object status, hashes, QC, plots, and manifest.
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
| M1 — raw DR24 adapter | Bounded indexed acquisition, schema and payload hashes | PARTIAL; PR #264 Draft |
| M2 — normalized exploratory data | Versioned QC and identity policy, fixture tests | NOT ACCEPTED |
| M3 — smoke test | 5–10 objects end-to-end with manifest | NOT VERIFIED |
| M4 — guided demo | 30–50 objects, Workbench, exports, offline replay | NOT VERIFIED |
| M5 — scientific model expansion | Labeled dataset and leakage-safe independent evaluation | NOT ACCEPTED |
| M6 — distribution | Clean-machine platform packaging | NOT ACCEPTED |

No milestone is complete because code exists. Require the stated evidence and recorded acceptance.

## Next concrete action
Complete PR #264 review and build the smallest end-to-end DR24 exploratory path. The first measurable proof is the 5–10-object smoke test. Do not start with bulk data acquisition, CIN runtime, or a new model.
