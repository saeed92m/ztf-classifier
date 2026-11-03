# CIN Integration Assessment — 2026-11-03

**Source:** ZTF CLASSIFIER — COSMIC INTELLIGENCE NETWORK, ZTF-CIN-ARCH-001, v1.0.0  
**Assessment base:** main at 764ed5d9dcf43693f5c2e5a278afe326b432d578  
**Status:** Read-only architecture assessment; no runtime implementation  
**Tracking:** [Issue #251](https://github.com/saeed92m/ztf-classifier/issues/251)

## 1. Executive finding

The repository already has parts of the surrounding discovery architecture: scientific observations, catalog context, discovery candidates, human-review/feedback contracts, model provenance, API services, a Workbench and scientific validation controls.

These are useful integration points. They do not establish that CIN exists.

The current source tree does not yet show a complete CIN task lifecycle, immutable human contribution store, contributor calibration, consensus service, active-learning task scheduler, expert adjudication workflow or reproducible human-annotation dataset release process.

Build on stable existing contracts while keeping CIN optional and separately governed. The first deliverable is a controlled LC-01 pilot, not a public community network.

## 2. Existing architecture evidence

Read-only inspection of main at the assessment base identified:

| Existing component | Current role | CIN implication |
|---|---|---|
| models/catalog_context.py | CatalogMatch / CatalogContext preserve contextual cross-match evidence | Useful source context, but not a canonical identity registry |
| catalog/service.py | Queries and exports persisted scientific results | Not a human task or annotation service |
| domain/observations.py | Observation and object-observation summary contracts using survey IDs | Can supply observation references; not CIN task identity |
| models/discovery.py | DiscoveryCandidate, HumanReview and LearningFeedback dataclass contracts | Candidate/review concepts exist, but no CIN workflow or persistence |
| models/analysis_mode.py | Analysis mode definitions | Possible eligibility integration; not a task-definition store |
| results/store.py | SQLite-backed scientific-result persistence | Not a human contribution ledger; result identity and lifecycle semantics differ |
| api/app.py and web/static | FastAPI routes and static Workbench | Possible future CIN client/API boundary; no CIN route or verified CIN interaction flow |
| models/provenance.py and scientific validation | Model identity/provenance and fail-closed controls | Must remain separate from contribution and annotation provenance |

### 2.1 Detailed API, authentication and persistence audit

The following source-level inspection was completed against the pinned `main` revision above:

**HTTP surface — `src/ztf_classifier/api/app.py`**

The existing FastAPI application exposes health/readiness, application settings, scientific validation, feature-backend and model metadata, prediction/batch inference, object summary/observations/analysis, durable analysis jobs, scientific results, reports and catalog query/export routes.

No CIN task, task-assignment, contribution-submission, consensus, contributor-profile, expert-adjudication or dataset-release endpoint was found among the registered routes.

The application mounts the existing static Workbench at `/workbench`. This establishes a presentation surface, not an implemented CIN task interface.

**Authentication — `api/app.py` and `api/config.py`**

- `ZTF_API_KEY` is optional.
- When configured, middleware checks a shared Bearer credential for paths beginning with `/v1/`.
- The health and readiness routes remain outside that `/v1/` check.
- The inspected API boundary does not establish per-contributor identities, roles, task-level authorization, consent records or contributor-specific access control.
- A shared API key is not sufficient as the complete public CIN participant-authentication and authorization model.

**Persistence — `jobs/store.py`, `results/store.py`, `application/state.py`**

- Analysis jobs are stored in a local SQLite database. The job lifecycle has `queued`, `running`, `succeeded` and `failed` states.
- Scientific analysis results are stored in a separate local SQLite database. A result is keyed by job ID and conflicting retries for the same job are rejected.
- Application preferences are stored separately as local JSON state.
- These stores support the existing single-application analysis workflow. They do not provide CIN-specific task assignments, immutable raw contribution events, contributor identity separation, consensus reconstruction, expert adjudication or research dataset release manifests.
- The result store's idempotency behavior must not be mistaken for an append-only, tamper-evident human-contribution ledger. No such CIN ledger was identified in the inspected code.

**Existing human-review contracts — `models/discovery.py`**

Repository code search found `HumanReview` and `LearningFeedback` in the domain contract module, the discovery architecture document and contract tests. The inspected source defines dataclasses and validation rules. It does not establish a persisted review service, contributor workflow, API lifecycle or a controlled human-generated training dataset.

**Identity and provenance**

- Current observation and discovery contracts use survey object identifiers such as `oid`.
- `DataSourceRef` can carry a locator, schema version and optional content hash.
- These contracts provide useful provenance building blocks, but they do not provide a complete typed CIN subject reference, pinned task observation bundle or AOIC-backed canonical identity decision.
- Until AOIC is accepted and implemented, preserve original survey identifiers and unresolved identity explicitly. Do not infer physical identity from an OID or positional cross-match alone.

**Dependency and deployment boundary**

- The package currently targets Python `>=3.11,<3.12`.
- The inspected API configuration defaults to local filesystem paths and SQLite stores.
- This audit does not establish production-grade multi-user concurrency, public-network abuse protection, backup/restore, retention enforcement or independent CIN deployment.
- No new dependency, paid service or infrastructure requirement is justified by this source-level review.

This is a source-level audit of registered routes and inspected modules. It is not a penetration test, load test, database recovery test, deployment audit or proof of production security.

## 3. Gap matrix

| CIN capability | Repository evidence at base | Assessment |
|---|---|---|
| Source/observation provenance | Existing observation and catalog-context contracts | Partial foundation |
| Canonical subject identity | AOIC is proposed separately; current survey OIDs remain | Gap |
| Task taxonomy and versioned definitions | No complete CIN task-definition lifecycle identified | Gap |
| Deterministic task generation | No CIN task-generation service identified | Gap |
| Task allocation and independent assignment | No CIN assignment workflow identified | Gap |
| Human task UI | Workbench exists, but no verified CIN interaction flow | Gap |
| Immutable raw contributions | No CIN contribution ledger identified | Gap |
| Idempotent contribution ingestion | Not verified for CIN | Gap |
| Gold-standard controls | Not verified | Gap |
| Contributor/task-specific calibration | Not verified | Gap |
| Consensus and disagreement | No CIN consensus pipeline identified | Gap |
| Expert adjudication | Human-review contracts may be reusable, but not a full CIN workflow | Partial / gap |
| Active-learning scheduler | Not verified | Gap |
| Research dataset releases | Benchmark/provenance patterns may be reusable | Partial / gap |
| Privacy, retention, consent and attribution | Shared API-key protection exists; CIN-specific controls are absent from inspected code | Gap |
| CIN API and independent deployment | Existing FastAPI surface is not proof of a separate CIN contract | Gap |
| Offline resilience | ZTF core is intended to remain independent; CIN outage isolation needs tests | Gap |
| Public community / gamification | Not implemented or authorized | Future phase |

## 4. Required boundaries

1. Do not place CIN contribution logic inside the frozen classifier or model inference path.
2. Do not reuse object_id for an unverified survey OID. CIN subject references must be typed and preserve original identifiers.
3. AOIC canonical identity is not yet an implemented dependency. Preserve unresolved identity until AOIC contracts are accepted.
4. Keep raw responses, QC decisions, aggregates, expert decisions, research datasets, training datasets and frozen benchmarks separate.
5. Hide model predictions from ordinary contributors where practical.
6. Keep random audit and representative selection alongside active-learning selection.
7. CIN is optional; its outage must not break local ZTF analysis or benchmark evaluation.
8. Human annotations cannot trigger production retraining.
9. Do not add third-party dependencies or paid infrastructure before feasibility and load evidence.

## 5. Recommended first implementation boundary

Start with a controlled LC-01 light-curve morphology assessment pilot.

The smallest end-to-end slice should include a versioned LC-01 task definition; source-backed immutable observation reference; typed subject reference and unresolved-identity state; deterministic task generation from a pinned sample manifest; blind presentation where practical; repeated independent assignment; confidence and abstention; immutable, idempotent contribution ingestion; schema and audit validation; response distribution and disagreement report; independent reference/adjudication protocol; and reproducible dataset export manifest.

Do not start with contributor rankings, gamification, large-scale public access, advanced consensus models, all-sky image downloads or automatic retraining.

## 6. Decisions still required

- Separate package/module or separately deployed process.
- Which storage and authentication components are safe to reuse.
- Pseudonymous contributor IDs, consent, deletion and retention.
- Observation representation and visualization scientifically sufficient for LC-01.
- Independent control examples and leakage prevention.
- Pilot sample size, assignment count and stopping rule.
- Consensus estimator after pilot data exist.
- AOIC subject identity integration after AOIC validation.
- Backup/restore, operational ownership and public deployment boundary.

## 6.1 External source availability and rights review

Public documentation was checked on 2026-11-03. This is a documentation review, not a live bulk-download or redistribution test.

**ZTF DR24 availability**

- The official ZTF release page identifies DR24 as published on 2026-01-22 and describes the release as covering March 2018 through October 2025. The public-survey portion extends through 2025-10-22; the release also includes proprietary-survey observations before 2024-07-22.
- The ZTF-3 schedule states that public images are released on a 60-day sliding window, light curves are recalculated every 12 months, and alerts/forced photometry remain available in real time. Proprietary products follow a 550-day release delay.
- IRSA documents both API access to light curves and image products/cutouts. Its access-control documentation states that proprietary data require credentials.
- IRSA Cloud Access documents DR24 Objects Table and Lightcurves as Parquet/HATS collections in the `ipac-irsa-ztf` S3 bucket. This establishes a documented public acquisition route for DR24 products, but does not prove that the current ZTF Classifier application has integrated that route.
- The repository has a separate open P0 item, [Issue #253](https://github.com/saeed92m/ztf-classifier/issues/253), for connecting provenance-backed DR24 Lightcurves acquisition to the application. CIN must reuse that accepted source-acquisition boundary rather than create a competing, undocumented data path.

**Use restrictions and attribution**

- IRSA's general terms distinguish public, proprietary/exclusive and copyrighted datasets. IRSA states that most public data it serves have no usage restrictions; proprietary/exclusive datasets require explicit access rights; and appropriate acknowledgements/citations are best practice.
- The ZTF API documentation explicitly distinguishes public from proprietary data and describes authenticated access for proprietary products.
- Therefore, CIN must select data whose release/access state is verified as public at retrieval time. It must not use a user's ability to query IRSA as evidence that every returned record is unrestricted.
- Each task must retain release identifier, source locator, retrieval time, source record/observation identity, schema/version metadata, and a content checksum where feasible. Dataset manifests must preserve the relevant ZTF and IRSA acknowledgement/citation information.
- For IMG-01, retain the original image product identity and cutout parameters (center, size, product type, observation epoch, filter and processing version). Do not redistribute or publish a derived image bundle until its source-specific terms and intended redistribution/display use have been reviewed.

**ALeRCE historical dataset**

- Zenodo record [10.5281/zenodo.4279623](https://doi.org/10.5281/zenodo.4279623) describes the labeled ZTF alert-stream set through 2020-06-09 and lists a 1.1 GB archive.
- The record is marked as an open dataset, but the retrieved metadata does not show an identified license value. Open access is not, by itself, a clear redistribution license.
- Do not bundle, mirror, republish or include the ALeRCE archive in a public CIN dataset release until its license/redistribution terms are confirmed with the record maintainers or rights holders. Preserve the DOI and required scientific citation in internal provenance meanwhile.
- ALeRCE labels remain reference/benchmark labels, not independently established astrophysical ground truth. They must not be used as the sole independent control or adjudication source for the LC-01 pilot.

**Pilot consequence**

For the first LC-01 feasibility slice, prefer a pinned, explicitly public DR24 light-curve sample obtained through the approved DR24 acquisition path. Keep the pilot object-level disjoint from the protected v0.2.0 benchmark and its frozen evaluation records. Use independently adjudicated control cases; do not treat ALeRCE labels as independent truth. The current source-level review does not yet establish the sample manifest, exact public-access flags, sample size, image rights, or actual acquisition success.

**External references**

- [ZTF Public Data Releases](https://www.ztf.caltech.edu/ztf-public-releases.html)
- [IRSA ZTF mission and data services](https://irsa.ipac.caltech.edu/Missions/ztf.html)
- [IRSA ZTF API and proprietary-data access](https://irsa.ipac.caltech.edu/docs/program_interface/ztf_api.html)
- [IRSA Cloud Access — DR24 Objects and Lightcurves](https://irsa.ipac.caltech.edu/cloud_access/)
- [IRSA Terms of Use](https://irsa.ipac.caltech.edu/data_use_terms.html)
- [ALeRCE historical dataset — Zenodo](https://doi.org/10.5281/zenodo.4279623)

## 7. Acceptance criteria for the assessment phase

- [x] Canonical CIN source read in full.
- [x] Major repository boundaries inspected at pinned base revision.
- [x] Reusable components separated from missing CIN capabilities.
- [x] Product and scientific independence requirements recorded.
- [x] Registered API routes, shared-key authentication boundary and local persistence modules inspected.
- [x] DR24 public-data availability, IRSA access boundaries and general IRSA terms reviewed from official documentation.
- [ ] ALeRCE Zenodo license/redistribution terms confirmed.
- [ ] IMG-01 source-specific redistribution, cutout and derived-image display terms confirmed.
- [ ] Actual DR24 acquisition and public-access filtering demonstrated with a pinned sample manifest.
- [x] Initial repository privacy/authentication boundary and proposed CIN threat model documented.
- [ ] Participant consent, retention, deletion and jurisdiction-specific privacy review approved.
- [ ] Deployment, backup/restore and multi-user concurrency review.
- [ ] Formal LC-01 pilot protocol reviewed.
- [ ] ADRs and task backlog approved.
- [ ] End-to-end implementation and scientific pilot evidence.

## 8. Status interpretation

This assessment is partially completed architecture work, not implemented, tested or scientifically validated. Documentation and planning do not increase scientific readiness of the existing ZTF model. The v0.2.0 baseline and v1.0.1 release remain unchanged.

**Next action:** resolve the ALeRCE license and IMG-01 image-use terms; demonstrate public-only DR24 retrieval with a pinned object-level sample; then complete privacy/retention, deployment/recovery and LC-01 protocol reviews before freezing the task and contribution contracts.
