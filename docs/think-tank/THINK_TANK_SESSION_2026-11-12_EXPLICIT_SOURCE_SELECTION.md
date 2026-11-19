# Think Tank Session 03 — Explicit Source Selection and Native Observation Boundaries

**Date:** 2026-11-12  
**Status:** Design review completed; implementation NOT APPROVED by this session  
**Scope:** Issue #253, Issue #249, source-selection boundary, API compatibility, provenance and model-readiness  
**Baseline:** main `f681408fae8d8062dd72ff74791872c1590f6ee8`; scientific v0.2.0 and software v1.0.1 remain immutable

> This is a structured review performed through 16 simulated specialist roles and an independent Red Team pass. It is not a claim that 16 external people attended or approved the work.

## 1. Inputs inspected

The review consumed Think Tank Session 02 and the current source code and contracts on the inspected main revision:

- `src/ztf_classifier/application/observations.py`
- `src/ztf_classifier/domain/observations.py`
- `src/ztf_classifier/io/detection_acquisition.py`
- `src/ztf_classifier/io/dr24_lightcurve.py`
- `src/ztf_classifier/io/zubercal_dr20.py`
- `src/ztf_classifier/api/schemas.py`
- `src/ztf_classifier/api/app.py`
- `src/ztf_classifier/jobs/store.py`
- `src/ztf_classifier/jobs/executor.py`
- `src/ztf_classifier/jobs/runner.py`
- `docs/architecture/DR24_HATS_VS_ZUBERCAL_SOURCE_CONTRACT_v0.1.md`
- `docs/knowledge/ARCHITECTURAL_DECISIONS.md`
- Issues #158, #249 and #253
- Draft PR #283 (minimum source identity domain contracts) and Draft PR #284 (bounded DR24/Zubercal test workflow activation)

The code findings below describe the inspected revision. PR #283 and PR #284 are separate active changes and must be rechecked before implementation.

## 2. Verified current state

### 2.1 Existing application path

1. `ObservationService.__init__` constructs `AlerceDetectionBackend` as its normalized observation backend.
2. `get_observations()` calls that backend and uses `alerce_to_internal_lc_robust()`.
3. Its `ObservationProvenance.source` is set to `ALeRCE`.
4. `SourceBackedAnalysisExecutor` calls `get_observations()`, computes features and then calls the model registry.
5. The API and worker construct the default service with an ALeRCE client.
6. `ObjectAnalysisRequest` and `AnalysisJobRequest` do not contain a source selector. The persistent job record also has no source-adapter field.

Therefore, the current standard observation and model-analysis path is ALeRCE-backed. This is a code fact, not a recommendation that ALeRCE is independent ground truth.

### 2.2 DR24 HATS path

The DR24 adapter and raw API return source-native records. The adapter preserves HMJD, native magnitude and error, color coefficient, catflags, OID, filter, field, RCID, catalog epoch count and payload hash. It does not perform time conversion, color correction, quality filtering, OID grouping or model inference.

The current Workbench Explorer displays this native data. It is not the normalized observation-to-model path.

### 2.3 Zubercal DR20 path

The separate Zubercal adapter queries around a ZTF OID position. It returns PS1 object IDs and preserves raw rows, MJD(TDB), magnitude, scaled magnitude error, band, field, RCID, flag and info. It preserves all candidate PS1 IDs and reports ambiguity. Its current decision is `NOT_SELECTED`.

A Zubercal PS1 object ID is not a ZTF OID. A single cone search has already returned two PS1 candidates for one tested ZTF position. The adapter cannot claim physical identity.

### 2.4 Domain mismatch

The current normalized `Observation` record uses an MJD field. It does not represent DR24 HMJD as a distinct native time field. It also lacks the full DR24 native photometry and quality semantics.

A generic conversion into this record would hide source-specific meaning. The same risk applies to Zubercal MJD(TDB), scaled errors and PS1-match context.

### 2.5 Identity contract dependency

PR #283 proposes immutable survey-object, catalog-entry, astrophysical-source, association-evidence and association-decision records. It does not implement matching, persistence, source selection or model inference. The application integration must use the final reviewed identity contract; it must not create a parallel identity model.

## 3. Findings from the 16 specialist roles

| Role | Finding |
|---|---|
| 1. Principal Investigator | Source selection must identify the scientific product, not only the transport backend. |
| 2. ZTF Survey Specialist | Preserve DR24 OID, filter, field and RCID. Never treat OID as physical identity. |
| 3. Time-Domain Astrophysicist | Keep HMJD and MJD(TDB) distinct. Do not compare epochs before a validated conversion. |
| 4. Astrostatistician | A source adapter pass is not a model-performance result. Track denominators, missing records and selection effects. |
| 5. Astroinformatics Architect | Use source-specific payload contracts. Avoid a lossy universal observation object. |
| 6. Catalog Cross-Match Specialist | Use PR #283's typed identity boundary after review. Keep unmatched and ambiguous states explicit. |
| 7. ML Scientist | No DR24 or Zubercal values enter the frozen v0.2.0 model without independent feature-parity and leakage evidence. |
| 8. Benchmark and Validation Lead | Keep source acquisition, schema validation, photometry QC, identity, feature parity and model evaluation as separate gates. |
| 9. Software Architect | Separate acquisition, normalization profile, identity association, feature generation and inference. |
| 10. Backend/API Engineer | A request must name the requested source. Persist that choice and the source-contract version. |
| 11. DevOps/MLOps/Security Engineer | Record source, release, query, hashes, code revision, dependency lock and execution status. Never log credentials. |
| 12. QA Engineer | Test explicit selection, unsupported operations, missing OIDs, source failures, retries and no-fallback behavior. |
| 13. UX/Product Designer | Show source name, release, native time system, units, flags, query and exclusions in the Workbench. |
| 14. Product/Commercial Lead | Do not present a source as the accepted Park primary product until the approved dossier and deliverable are reconciled. |
| 15. Scientific Documentation Lead | Label each output as native, normalized, diagnostic, model-ready or not model-ready. |
| 16. Independent Red Team | A generic `source` parameter is unsafe if it silently changes normalization or model behavior. Use explicit operation capabilities and reject unsupported combinations. |

## 4. Joint decisions

### Approved design principles

1. Source selection must be explicit for every new acquisition request.
2. The selected source must be returned in the result and the run manifest.
3. The source release, schema, query, native units, time system, filters, row counts, missing IDs, warnings, hashes and code revision must be retained.
4. A failed or empty selected source must return a source-specific failure or explicit empty result. It must not trigger silent fallback to another source.
5. Keep separate native contracts for ALeRCE, DR24 HATS and Zubercal DR20.
6. Keep source acquisition separate from normalization, source association, feature generation and model inference.
7. Use the reviewed identity types from PR #283 when available. Do not infer physical identity from OID equality or angular proximity alone.
8. Preserve existing v1 API behavior during a versioned migration. Do not silently change the backend of existing analysis routes.
9. A model-analysis operation must reject a source that has no approved normalization, identity, QC and feature contract.
10. Keep all current scientific baselines and acceptance criteria unchanged.

### Not approved by this session

- No choice of HATS or Zubercal as the sole Park primary product.
- No automatic conversion of HMJD to MJD or MJD(TDB).
- No magnitude/color correction or QC filtering policy.
- No OID grouping or crossmatch algorithm.
- No DR24 or Zubercal connection to the frozen v0.2.0 model.
- No new default source for the existing analysis endpoint.
- No inference fallback to ALeRCE when DR24 or Zubercal is selected.

## 5. Proposed API and application contract

This section is a design proposal. It does not describe implemented functionality.

### 5.1 Separate operations and source types

Define explicit, versioned source identifiers:

- `ALERCE_DETECTIONS` — ALeRCE detection service; current normalized path.
- `ZTF_DR24_HATS_NATIVE` — source-native DR24 HATS lightcurves.
- `ZTF_ZUBERCAL_DR20_NATIVE` — source-native Zubercal DR20 matched photometry.

Do not treat these identifiers as interchangeable. Do not use one common payload schema to erase their differences.

A future acquisition request should include:
- source identifier;
- source contract version;
- source-specific query/reference;
- requested operation;
- optional, versioned QC policy identifier;
- explicit identity-association policy, if used.

Source-specific request models should validate the fields required by that source. For example, Zubercal requires a position and ZTF OID context; DR24 HATS requires one or more bounded DR24 OIDs.

### 5.2 Native acquisition result

Return a discriminated source-specific result. The result must carry:

- source identifier and release;
- native schema and time system;
- native identifiers and partition fields;
- raw measurement fields and units;
- exact query or requested IDs;
- returned, missing and rejected IDs;
- source row/epoch counts;
- raw payload hash and hash scope;
- retrieval time and software revision;
- explicit warnings and error states.

Do not force raw HATS or Zubercal measurements into the present normalized `Observation` record.

### 5.3 Model-analysis capability gate

For model analysis, require a registered compatibility profile that names and versions:

- source adapter;
- normalization transform;
- time conversion;
- photometry and error mapping;
- quality policy;
- identity/grouping policy;
- feature schema;
- supported model and training-domain evidence.

At this review point, the standard model-analysis executor is ALeRCE-backed. DR24 HATS and Zubercal are not approved as model-ready inputs.

A request for model inference from an unsupported source must fail with a stable machine-readable error such as `source_not_model_ready`. It must not call the ALeRCE backend as a fallback.

### 5.4 Backward compatibility

Keep current v1 endpoints and worker behavior unchanged until a separate migration proposal is reviewed. A new API version or an explicit versioned acquisition endpoint should require a source value. Do not infer a source from a missing field.

If the job model later stores source selection, use an additive SQLite migration and test old database files. Persist the source identifier, adapter version and request hash with the job. Do not change the frozen model version or feature contract.

## 6. Required regression and acceptance tests

Before application implementation can be accepted:

1. ALeRCE selection calls only the ALeRCE adapter.
2. DR24 HATS selection calls only the DR24 adapter and preserves each OID independently.
3. Zubercal selection calls only the Zubercal adapter and preserves every PS1 candidate and ambiguity state.
4. A missing DR24 OID remains missing; it does not cause an ALeRCE retry.
5. A source timeout, schema failure or empty response does not invoke a different adapter.
6. Unsupported source/operation combinations return a stable error before feature generation.
7. The raw result contains the exact selected source, release, schema, query, IDs and hashes.
8. A job retry uses the original source request; it does not silently switch source.
9. Existing v1 analysis tests remain unchanged and continue to verify backward compatibility.
10. Old SQLite job-store files migrate without data loss; new source fields remain deterministic.
11. Source-specific time, units and quality fields remain intact through API serialization and offline replay.
12. No native DR24 or Zubercal input reaches the frozen v0.2.0 feature/model path without a separately approved compatibility profile.

The final Park acceptance test remains a pinned 5–10 confirmed astrophysical sources through the full API-to-Workbench acquisition, identity review, QC, visualization, export and offline-replay path. This test must not be substituted by an OID-only raw retrieval smoke test.

## 7. Park product decision

The technical architecture proposal recommends DR24 HATS for broad native discovery coverage and Zubercal DR20 as a supplementary PS1-matched stream. The submitted Park dossier emphasizes recalibrated Zubercal photometry. These statements are not yet reconciled by an approved acceptance decision.

Therefore:
- keep `AD-DATA-001` in PROPOSED status;
- keep HATS and Zubercal separate;
- do not describe one as the approved Park primary product;
- record the final product decision against the signed/approved deliverable before implementation changes the default path.

## 8. Red Team challenges

| Challenge | Required control |
|---|---|
| Missing source selector silently uses ALeRCE | New source-specific operations require a source value; unsupported values fail closed. |
| DR24 HMJD stored as ordinary MJD | Preserve native HMJD and its time-system label; conversion is a separately versioned transform. |
| PS1 ID treated as ZTF OID | Use typed, source-scoped identifiers and preserve all candidates. |
| Ambiguous PS1 candidates reduced to one | Preserve all candidates; no automatic selection. |
| Raw diagnostic QC becomes a filter | Keep diagnostics separate from a versioned, approved production selection policy. |
| Source error causes silent retry from another survey | No cross-source fallback. |
| DR24 native photometry reaches v0.2.0 | Block unless source-to-feature/model compatibility is independently validated. |
| Old API behavior changes without versioning | Keep v1 compatibility and add a separately reviewed migration. |
| Run manifests omit data-source identity | Persist source, release, contract version, query, hashes and exact input IDs. |

## 9. Unresolved blockers and next actions

| Priority | Action | Acceptance evidence |
|---|---|---|
| P0 | Complete review of PR #283 identity contract | Evidence-to-entity linkage tests; clean current-head CI; API compatibility review |
| P0 | Confirm Park source-product requirement | Recorded decision against approved technical/business dossier |
| P0 | Approve source-native API contract | Versioned request/result schemas and no-fallback tests |
| P0 | Implement explicit source selection at application boundary | Tests prove each adapter is called only when selected |
| P0 | Keep native data separate from inference | Unsupported source/model combinations fail closed |
| P1 | Implement minimum identity association integration | Adjudicated, versioned source sample and ambiguity-preserving results |
| P1 | Complete native time/photometry/QC contracts | Scientific references, transforms, units, error budgets and regression fixtures |
| P1 | Run 5–10 confirmed-source E2E acceptance | Full replayable API-to-Workbench artifacts |
| P1 | Expand to 30–50 source demonstration | Run manifest, report and reviewed exclusions |

The full AOIC registry, persistent source graph, merge/split lineage and broad multi-survey expansion remain staged work. The minimum source-identity boundary remains P0.

## 10. Final session decision

**Decision: APPROVE DESIGN PRINCIPLES; BLOCK APPLICATION IMPLEMENTATION THAT WOULD NORMALIZE OR INFER FROM DR24/ZUBERCAL.**

The code review confirms the standard application analysis path is still ALeRCE-backed, while DR24 and Zubercal are separate native acquisition paths. The project may prepare explicit source-selection interfaces and tests, but it must not select a Park primary product, silently fall back, group OIDs, transform native time/photometry, or connect the raw DR24/Zubercal products to the frozen v0.2.0 model before the listed gates pass.

No runtime code, model, data, feature, taxonomy, benchmark, threshold, release or scientific acceptance criterion was changed by this session.
