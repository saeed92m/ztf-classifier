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
| models/discovery.py | Discovery-candidate domain contract | Candidate may feed CIN after source identity and provenance checks |
| models/analysis_mode.py | Analysis mode definitions | Possible eligibility integration; not a task-definition store |
| results.py | Result persistence/serialization boundaries | Must be assessed for immutable contribution separation before reuse |
| FastAPI and Workbench | Existing API-backed application surfaces | Possible future CIN client/API boundary; not proof of CIN |
| Model provenance and scientific validation | Existing model identity and fail-closed controls | Must remain separate from contribution and annotation provenance |

This is a source-level boundary review, not a complete database migration or runtime audit. Before implementation, inspect current API routes, persistence backends, auth model, job lifecycle, UI routing, deployment and clean-install behavior.

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
| Privacy, retention, consent and attribution | Existing security practices need CIN-specific review | Gap |
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

## 7. Acceptance criteria for the assessment phase

- [x] Canonical CIN source read in full.
- [x] Major repository boundaries inspected at pinned base revision.
- [x] Reusable components separated from missing CIN capabilities.
- [x] Product and scientific independence requirements recorded.
- [ ] Detailed route/storage/authentication audit.
- [ ] Data availability and image-license review.
- [ ] Privacy, consent, retention and threat model.
- [ ] Formal LC-01 pilot protocol reviewed.
- [ ] ADRs and task backlog approved.
- [ ] End-to-end implementation and scientific pilot evidence.

## 8. Status interpretation

This assessment is partially completed architecture work, not implemented, tested or scientifically validated. Documentation and planning do not increase scientific readiness of the existing ZTF model. The v0.2.0 baseline and v1.0.1 release remain unchanged.

**Next action:** complete the detailed storage/API/auth/data/licensing audit, then freeze LC-01 task and contribution contracts before runtime code.
