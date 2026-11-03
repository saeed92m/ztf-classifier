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

## 7. Acceptance criteria for the assessment phase

- [x] Canonical CIN source read in full.
- [x] Major repository boundaries inspected at pinned base revision.
- [x] Reusable components separated from missing CIN capabilities.
- [x] Product and scientific independence requirements recorded.
- [x] Registered API routes, shared-key authentication boundary and local persistence modules inspected.
- [ ] Data availability and image-license review.
- [ ] Privacy, consent, retention and threat model.
- [ ] Deployment, backup/restore and multi-user concurrency review.
- [ ] Formal LC-01 pilot protocol reviewed.
- [ ] ADRs and task backlog approved.
- [ ] End-to-end implementation and scientific pilot evidence.

## 8. Status interpretation

This assessment is partially completed architecture work, not implemented, tested or scientifically validated. Documentation and planning do not increase scientific readiness of the existing ZTF model. The v0.2.0 baseline and v1.0.1 release remain unchanged.

**Next action:** complete data availability/licensing, privacy/retention, deployment/recovery and LC-01 protocol reviews. Then freeze the task and contribution contracts before runtime code.
