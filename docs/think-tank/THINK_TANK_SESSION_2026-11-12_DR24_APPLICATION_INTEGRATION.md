# Think Tank Session 02 — DR24 Application Integration and Park Source-Product Decision

**Date:** 2026-11-12  
**Status:** Evidence review complete; implementation decision partially blocked  
**Repository baseline reviewed:** `main` at `f681408fae8d8062dd72ff74791872c1590f6ee8`  
**Scope:** Issue #253 (DR24 application integration), Issue #249 (AOIC), Issue #158 (Park MVP)  
**Review method:** 16 simulated specialist roles, followed by a red-team challenge. This is a structured internal review, not a claim that 16 external human experts attended.

## 1. Evidence inspected

- `src/ztf_classifier/application/observations.py`
- `src/ztf_classifier/domain/observations.py`
- `src/ztf_classifier/io/dr24_lightcurve.py`
- `src/ztf_classifier/io/detection_acquisition.py`
- `src/ztf_classifier/jobs/executor.py`
- `tests/test_dr24_observation_service.py`
- `docs/PARK_MVP_DR24_APPLICATION_READINESS_AUDIT_2026-11-04.md`
- `docs/architecture/AOIC_IDENTITY_AND_CROSSMATCH_ARCHITECTURE_v0.1.md`
- Issue #253 history, including the 2026-11-12 updates and bounded DR24 HATS, Workbench, and Zubercal evidence.

## 2. Verified implementation state

1. `ObservationService` constructs `AlerceDetectionBackend` as its normalized observation backend.
2. The same service has a separate `get_dr24_native_lightcurves()` method. It returns source-native HATS payloads and diagnostic QC. It does not normalize to the existing observation model.
3. `SourceBackedAnalysisExecutor` calls `get_observations()`; therefore the ordinary analysis path remains ALeRCE-backed.
4. DR24 HATS raw acquisition, bounded multi-OID API, raw-preserving QC, and Explorer components exist. Their existence does not prove end-to-end DR24 model inference.
5. The DR24 adapter preserves HMJD, native magnitude/error, color coefficient, catflags, OID, filter, field, RCID, and payload hash. It explicitly avoids time conversion, color correction, flag filtering, and OID grouping.
6. The source-product documentation distinguishes DR24 HATS from Zubercal DR20. The products have different semantics and must not be represented as interchangeable.
7. The submitted Park dossier emphasizes Zubercal recalibrated PSF photometry. The current repository plan emphasizes DR24 HATS as the discovery stream and Zubercal as a supplementary comparison stream. The approved Park primary-source decision is not reconciled in the available evidence.

## 3. Sixteen specialist perspectives

| Role | Review finding | Required control |
|---|---|---|
| 01 Chief Scientist / PI | The Park source-product mismatch is a scientific scope decision, not a coding detail. | Do not select a primary product by assumption. |
| 02 ZTF Survey & Data Specialist | HATS is a distinct source-native lightcurve product. | Preserve release, catalog schema/index, OID, filter and partition metadata. |
| 03 Time-Domain Astrophysicist | HMJD must not be silently relabeled MJD. | Keep native time values and define a reviewed time conversion contract. |
| 04 Astronomical Statistics Specialist | Per-filter OIDs and incomplete bands can bias sampling and analysis. | Report band completeness and missingness at object-group level. |
| 05 Astroinformatics Architect | Current raw and normalized service boundaries are not yet unified by explicit source selection. | Add a typed source request and source-specific result contracts. |
| 06 Catalog/Cross-Match Specialist | OID is not a physical-source identity. | Preserve aliases and use explicit confirmed/ambiguous/unmatched states. |
| 07 Chief ML Scientist | Raw HATS measurements are not automatically compatible with frozen v0.2.0 features. | No inference until a versioned mapping passes validation. |
| 08 ML Validation Scientist | Existing benchmark performance cannot validate a new DR24 population. | Use leakage-safe, independently labeled evaluation and report skips. |
| 09 Principal Software Architect | The executor currently depends on the ALeRCE-normalized service method. | Inject a source-selection abstraction; avoid hidden backend selection. |
| 10 Backend Engineer | Native DR24 and normalized observations have different schemas and guarantees. | Keep separate typed pathways; no lossy implicit coercion. |
| 11 DevOps/MLOps/Security | Live source calls must remain bounded and reproducible. | Pin queries, manifests, dependency versions and hashes; no full archive pull. |
| 12 QA/Reliability | A source selector can fail through accidental fallback or partial success. | Test explicit source, unavailable source, partial OID response, retries and no-fallback. |
| 13 UX/Visualization | Users must know which data product and release produced each panel/export. | Display source, release, filter, OID, missing reasons and native units. |
| 14 Product/Commercialization | Park acceptance must match the submitted deliverable and demonstrable user workflow. | Reconcile HATS-versus-Zubercal primary role before locking MVP scope. |
| 15 Scientific Documentation | Existing claims mix raw acquisition, diagnostic QC and model readiness. | Label each evidence stage and preserve historical run scope. |
| 16 Independent Red Team | A successful API smoke or matching epoch count can still hide wrong identity, time basis or photometric semantics. | Require end-to-end pinned-source evidence and independent review before acceptance. |

## 4. Joint decision

**APPROVE the architecture direction; BLOCK production source default and DR24-to-model inference pending source-product decision and scientific contracts.**

Approved now:
- Add explicit source selection at the application boundary.
- Keep ALeRCE and DR24 HATS as distinct selectable source adapters.
- Keep Zubercal as a separate adapter/product if included in the approved Park scope.
- Preserve source-native payloads and immutable provenance.
- Make source failure explicit; never silently fall back.
- Keep OID, catalog alias, physical-source group, observation and analysis run as separate entities.
- Keep raw HATS inspection separate from normalized/model-ready observations.
- Preserve the frozen v0.2.0 model, 42-feature set, class order, benchmark and acceptance gates.

Blocked pending evidence/decision:
- Selecting HATS or Zubercal as the primary Park MVP data product.
- A universal HATS↔Zubercal equivalence or automatic substitution.
- Any unapproved HMJD-to-MJD conversion, color correction or catflags production threshold.
- Cross-OID grouping based only on angular proximity.
- DR24-to-v0.2.0 inference without a validated feature mapping and source-identity contract.

## 5. Minimum implementation contract for Issue #253

A source-selection request must identify:
- source enum and product/release;
- exact OID or confirmed source-group reference;
- requested filters and bounded object count;
- normalization profile/version, if and only if an approved profile exists;
- time/photometry policy identifiers, if approved;
- run ID and provenance capture mode.

A result must identify:
- requested, returned and missing IDs;
- native product/release and schema/index identity;
- per-record OID, filter, field, RCID and coordinates where available;
- native time/photometry fields and units;
- epoch counts and exclusion/missing reason codes;
- raw and normalized hashes where applicable;
- warnings/errors and explicit completion state.

The first safe code milestone is source selection plus source-native result routing. It must not create a hidden DR24 normalization or model inference path.

## 6. Red-team challenge and response

**Challenge:** Could a nearby g-band and r-band OID pair be automatically treated as one source and passed into the model?

**Response:** No. Preserve separate OIDs. AOIC may propose a candidate association with astrometric epoch/uncertainty evidence. The state remains ambiguous until a reviewed identity policy and independent validation support confirmation.

**Challenge:** Could a failed DR24 query silently retry ALeRCE and return a result?

**Response:** No. A requested source is part of the scientific provenance. Source failure must remain an explicit failure or partial result. It cannot be replaced by another product.

**Challenge:** Could the existing v0.2.0 feature engine consume HATS fields after a simple column rename?

**Response:** No. Time semantics, native photometry, color treatment, quality flags, filters and source grouping require an approved normalization contract and feature parity evidence.

**Challenge:** Does the four-OID live payload probe prove Park MVP acceptance?

**Response:** No. It proves bounded nested-payload retrieval for those OIDs only. It does not prove confirmed physical identity, normalized features, inference, or a complete API-to-Workbench flow.

## 7. Actions and ownership

| Priority | Action | Tracker | Exit evidence |
|---|---|---|---|
| P0 | Reconcile Park dossier's primary source-product requirement (HATS vs Zubercal) | #158 / #253 | Explicit recorded product decision with source documentation |
| P0 | Define typed source-selection and native result contracts | #253 | ADR, schemas, deterministic fixture tests |
| P0 | Define minimum AOIC alias and association contract | #249 | Confirmed/ambiguous/unmatched behavior and fixture evidence |
| P0 | Route explicit source selection without fallback | #253 | API/service tests for source selection and failure |
| P1 | Approve HMJD, photometry, color and QC policies | #253 | Versioned scientific policy and independent review |
| P1 | Build pinned 5–10 confirmed-source E2E manifest | #158 / #253 | Reproducible API-to-Workbench-to-export evidence |
| P1 | Only then assess DR24 feature compatibility | #158 | Feature parity/leakage report; no baseline mutation |

## 8. Decision status

- Architecture direction: **APPROVED**.
- Source selection contract: **DESIGN REQUIRED**.
- Park primary product: **OPEN — requires dossier reconciliation**.
- DR24 normalized model inference: **BLOCKED**.
- v0.2.0 baseline: **UNCHANGED**.
- CPVS #170/#180: **separate deferred research**.
- CIN #251/#252: **optional future subsystem; not on the Park critical path**.

This session must be consulted before any implementation or PR that changes observation acquisition, source normalization, OID grouping, feature generation, or model inference.
