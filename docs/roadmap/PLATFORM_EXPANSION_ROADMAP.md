# Astronomical Data Analysis & Discovery Platform — Product Roadmap

Status date: 2026-11-01  
Current immutable software release: v1.0.1  
Product implementation tracker: [Issue #158](https://github.com/saeed92m/ztf-classifier/issues/158)  
Scientific blocker: [Issue #170](https://github.com/saeed92m/ztf-classifier/issues/170)

## Guiding constraints
- Preserve scientific baseline v0.2.0 and model identity baseline_v0.2.
- Keep the scientific gate fail-closed; missing evidence is never PASS.
- Build CPU-first, reproducible workflows for modest hardware.
- Separate classification, uncertainty/calibration, conformal prediction, OOD, anomaly evidence, catalog context, and explainability.
- Prefer source-backed, versioned adapters over copying datasets into Git.
- Every meaningful change updates its lifecycle record, tests, failure-prevention knowledge, and affected docs.

## Track A — Scientific integrity and external evidence

### A1. CPVS exact-reproduction investigation — OPEN / UNRESOLVED
- [ ] Trigger heavy workflow on an intended ci/heavy/* ref and verify source-provenance/scientific-gate-readiness executes.
- [ ] Re-run CPVS derivation after PR #173's finite/non-zero magnitude correction.
- [ ] Inspect acquisition report, derived membership, independent VizieR table, and hashes.
- [x] Verify the robust parser reads all 730,184 published ZTF names without duplicates.
- [x] Identify and correct the audit's invalid row-ordinal substitution: official CPVS lightcurve membership uses Table2 `Seq` (bytes 24–29), not physical row order.
- [ ] Rerun derivation and independent membership audit using actual Seq values; previous membership metrics are invalid and superseded.
- [ ] Explain the 11,602 candidate-only objects from valid Seq-based evidence and source-backed selection semantics, not tuned thresholds.
- [x] Recheck the retained historical artifact and produce fixed 100-object and 1,000-object stratified samples; sample reference labels are explicitly marked inferred because raw Table 4 bytes are absent from the retained artifact.
- [ ] Require exact independent membership audit before claiming exact reconstruction.
- [ ] Keep Issue #170 open until evidence-based disposition.

### A2. Product-level validation — RELEASE-BLOCKING
- [ ] Complete pinned ZTF DR24 source-backed adapter execution. A raw-only indexed HATS adapter and API route are in Draft PR #264; live acquisition and downstream inference are not yet verified.
- [ ] Complete frozen historical ALeRCE reference acquisition/execution and immutable manifests.
- [ ] Complete object-overlap, duplicate, target leakage, temporal leakage, preprocessing, schema, provenance, and failure-code audits.
- [ ] Generate per-release benchmark evidence and show scope limits/known failure cases to users.
- [ ] Ensure required scientific gates run rather than skip on release-candidate refs.

## Track B — Desktop application and user experience

### B1. Architecture foundation
- [ ] Freeze and test Application ↔ Scientific Core boundary.
- [ ] Define stable application-service, ingestion, provenance, configuration, and durable-state contracts.
- [ ] Ensure GUI uses the same service contracts as CLI/API and cannot bypass scientific validation.

### B2. Scientist-facing workflows
- [ ] Desktop shell and dashboard.
- [ ] Data Manager / import / source connection.
- [ ] Object/source explorer and light-curve visualization.
- [ ] Analysis workspace with model identity, uncertainty, calibration, OOD and provenance.
- [ ] Results, visualization, reproducible reports and exports.
- [ ] Discovery candidate workspace with human review and ranking limitations.
- [ ] Settings, Help, troubleshooting, diagnostics and logs.

### B3. Distribution and usability
- [ ] Windows self-contained installer and first-run smoke test.
- [ ] macOS application package and smoke test.
- [ ] Linux AppImage or documented, tested alternative.
- [ ] Clean-machine installation without Python/pip/Git/terminal for normal use.
- [ ] CPU-first performance and memory test on modest hardware.
- [ ] Installer integrity, checksums, release provenance and rollback/uninstall behavior.

## Track C — Scientific capability expansion
- [ ] Independent labeled benchmark and cross-match evidence.
- [ ] Model comparison/ensemble only where labels are comparable and splits are leakage-safe.
- [ ] Dedicated scientific anomaly analysis; do not label OOD as anomaly detection.
- [ ] Drift monitoring separates live-source changes from frozen historical evaluation.
- [ ] Multisurvey/light-curve/image/catalog adapters only after licensing, provenance, schema and validation review.
- [ ] Controlled human feedback; never silently convert review feedback into ground truth.

## Track D — Reliability, security, and release engineering
- [ ] Test fresh installation, upgrade, uninstall, offline/poor-network failure, cache corruption, and missing-data paths.
- [ ] Test dependency locks, supply-chain/security checks, API auth, data handling, and safe export behavior.
- [ ] Preserve deterministic reports, input manifests, checksums, model identity, and audit trails.
- [ ] Every meaningful PR has a validated lifecycle cycle record and regression test.
- [ ] Every release has complete release notes, release description, checksums, provenance, and scientific/engineering gate evidence.

## Milestones and exit criteria

| Milestone | Exit criteria |
|---|---|
| M0 — Scientific recovery | Required heavy jobs execute; CPVS claim is accurately classified; evidence gaps/root causes are recorded. |
| M1 — Desktop foundation | Application/service boundary and ingestion/provenance contracts are tested. |
| M2 — Usable alpha | A non-developer can install, import/connect data, inspect an object/light curve, run analysis, and view evidence. |
| M3 — Scientific workbench | Results, uncertainty/OOD, discovery review, reproducible reports and exports work end-to-end. |
| M4 — Cross-platform beta | Windows/macOS/Linux packaging and clean-machine smoke tests pass. |
| M5 — Scientific product acceptance | Independent benchmark, leakage, provenance, failure analysis and release gates pass for declared scope. |
| M6 — Stable platform release | All M0–M5 criteria pass, docs/help are complete, release notes and evidence are published. |

No milestone is complete based on code presence alone. Completion requires measured evidence and recorded acceptance.

## Evidence update — 2026-11-01

The corrected historical Seq-space comparison remains: 781,602 parent objects; 730,184 published members; 741,786 candidates; 730,184 intersection; 11,602 candidate-only; zero published-only. Earlier row-ordinal comparison metrics remain invalid and superseded.

A retained historical heavy artifact from run [38635891449](https://github.com/saeed92m/ztf-classifier/actions/runs/38635891449) was rechecked without repeating the multi-gigabyte light-curve download. All 11,602 candidate-only objects have `snr_exact=true` in both bands in the retained diagnostics. The four-field metadata condition reproduces the retained membership set, but the paper does not explicitly document both parent mean magnitudes and both band-specific periods as mandatory selection fields. This remains diagnostic evidence, not proof of author intent.

A deterministic 100-object and 1,000-object stratified sample was generated from the full retained parent metadata. The method, hashes, sample counts, results, and limitations are documented in [CPVS_PARENT_SAMPLE_AUDIT_2026-11-01.md](../scientific_validation/CPVS_PARENT_SAMPLE_AUDIT_2026-11-01.md). The sample's published-member labels are inferred from the retained audit because the raw Table 4 bytes are not present in that artifact; a fresh independent join remains required.

PR [#244](https://github.com/saeed92m/ztf-classifier/pull/244) is an open Draft. It adds a candidate-level audit, ZTF-name-to-Seq crosswalk, VizieR mirror fallback, and regression coverage. Review identified and corrected a VizieR column-header format issue. The full heavy source-backed path has not yet been run on the latest PR head. The previous heavy run [#40873746342](https://github.com/saeed92m/ztf-classifier/actions/runs/40873746342) failed to acquire Table 4 from configured CDS endpoints.

**Current disposition:** A1 remains OPEN / UNRESOLVED. Do not merge or claim scientific resolution based only on ordinary CI or historical artifact diagnostics. The next gate is a reviewed, current-head source-backed comparison with pinned raw Table 2 and Table 4/Zenodo bytes, full object-level differences, and documented SNR/detection semantics. Do not modify the production selector, thresholds, v0.2.0 baseline, or acceptance criteria to force a match.

## CPVS evidence refresh — 2026-11-01

The new full Zenodo membership crosswalk completed successfully on PR head `7c73a4a9d2260e080300303e6aac826630369539`. A full comparison against the retained candidate IDs again found 730,184 published members, all present in the 741,786 candidates, plus 11,602 candidate-only IDs and zero published-only IDs. This is stronger source-backed membership evidence, but it is not scientific resolution: raw Table 4 bytes were not used, and the candidate set remains a retained historical derivation. See `docs/scientific_validation/CPVS_FULL_ZENODO_MEMBERSHIP_COMPARISON_2026-11-01.md` for hashes and limitations. Keep Issue #170 open and fail-closed.


## Evidence update — 2026-11-04

### CPVS

The source-backed run [41417144949](https://github.com/saeed92m/ztf-classifier/actions/runs/41417144949), job `125183681255`, completed. It verified the parent/archive acquisition and reproduced **741,786** candidates against the **730,184** published membership reference. Candidate-only remains **11,602**; published-only remains **0**. The finite/nonzero magnitude guard removed zero candidates.

The independent membership audit did not complete. VizieR mirror requests timed out; the fallback parser treated a dashed separator row as a ZTF name and failed the Table 2 name-to-Seq crosswalk. The parser repair and two regression tests are in Draft PR #244. Do not call this audit PASS until current-head tests and the retained-artifact crosswalk pass.

Object-level membership counts relative to the published list are TP=730,184, FP=11,602, FN=0, TN=39,816. These are agreement metrics against published membership, not astrophysical truth or model-performance metrics.

The candidate/reference intersection equals the reference. The candidate ∩ four-field-positive Table 2 set also equals the reference, but the 2022 method describes two-band SNR thresholds and use of the common Table 2 period. It does not document a requirement for all four fields `gmag`, `rmag`, `Per-g`, and `Per-r`. All 11,602 candidate-only IDs have a finite positive common `Per`; missing common period does not explain the difference. Table 2 `Ng`/`Nr` counts also disagree with raw-archive detections for a small subset.

The 100- and 1,000-object fixed samples were independently reproduced exactly using seed `ztf-cpvs-fixed-object-sample-v2`. The 55 four-field-only controls have incomplete archived photometry coverage. One identity lead is under targeted investigation: Table 2 Seq 615170 has `Ng=132` but no g rows; orphan g-archive Seq 615172 has 132 rows. Draft PR #265 checks the checksum-pinned g archive's raw coordinates and HJD. This remains a hypothesis until the scan completes.

No SNR threshold, selector, reference definition, or v0.2.0 artifact was changed. Issue #170 remains OPEN / UNRESOLVED.

### DR24

Draft PR #264 adds a raw-only, bounded, indexed DR24 HATS adapter and API route. It preserves native HMJD, photometry, flags, filter and OID provenance. It does not normalize times, correct color, apply quality masks, merge OIDs, or run inference. Ordinary CI is being verified. Live source-backed acquisition and the 30–50 object end-to-end inference path remain incomplete.

### Release and baseline

The v0.2.0 baseline and v1.0.1 release remain unchanged. No tag or release was created. No draft PR was merged. M0 and all later milestones remain incomplete.


### DR24 ordinary CI update — 2026-11-04

Draft PR #264 head `02d96ce85b58d8a6ce5670a8833b2beb74d70b24` completed ordinary CI:
- Format, lint, lifecycle, runtime smoke, package build/install/import, dependency audit, and final CI Gate passed.
- Test Suite: 649 passed, 10 skipped, 9 warnings, 0 failures.
- Dependency audit reported 0 known vulnerabilities.
- The 10 skips are explicit: 3 feature/raw-data integration tests lack the frozen feature artifact or raw detection cache; 7 production-inference tests lack `runs/model_baseline_v0.2_production/artifact`.
- The skipped artifact-dependent tests are not PASS. CI does not yet verify the frozen v0.2.0 production artifact path.
- DR24/ALeRCE/CPVS source-backed jobs were skipped on this feature branch. This ordinary CI result does not verify live HATS acquisition, DR24 normalization, or end-to-end inference.

The raw DR24 adapter remains Draft PR #264 and is not merged. The baseline and release remain unchanged.
