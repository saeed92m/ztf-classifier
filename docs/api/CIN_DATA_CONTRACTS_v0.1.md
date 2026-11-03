# CIN Data and API Contracts v0.1

**Status:** Proposed logical contract; not an implemented API or database schema  
**Source:** ZTF-CIN-ARCH-001 v1.0.0  
**Tracking:** [Issue #251](https://github.com/saeed92m/ztf-classifier/issues/251)

## 1. Contract rules

- IDs are opaque UUIDs or stable namespaced IDs; never derive identity from mutable coordinates.
- Every contract has an explicit schema_version.
- Task definitions and policies have independent semantic versions.
- Raw contributions are immutable.
- A retry with the same idempotency key and payload returns the original result. A conflicting payload with the same key is rejected and audited.
- Timestamps are UTC ISO-8601.
- Missing evidence is explicit; do not invent coordinates, epochs, uncertainties, catalog identity or contributor attributes.
- A schema-valid response is not automatically scientifically valid.
- The API namespace below is proposed and is not currently implemented.

## 2. Typed subject reference

A CIN task must identify what is being assessed. It must not use one unqualified string for all subject types.

Example fields:

| Field | Meaning |
|---|---|
| subject_type | object, event, detection, observation or dataset_sample |
| source_system | ZTF or another named source |
| source_release | Exact source release/version |
| source_record_id | Original external/survey identifier |
| canonical_object_id | Optional AOIC ID; null until evidence-backed |
| identity_status | confirmed, provisional, ambiguous or unresolved |
| observation_id | Optional observation reference |
| event_id | Optional event reference |

A canonical object_id may be populated only after AOIC identity contracts are accepted and an evidence-backed identity exists. Until then, preserve source identifiers and unresolved state. A ZTF OID must not be presumed to be a globally unique physical-object identity.

## 3. Task definition

Required logical fields:

- task_type_id (LC-01, IMG-01, PAIR-01, PAT-01, NOV-01, SIM-01);
- task_definition_version;
- schema_version;
- scientific objective;
- supported subject type and source data requirements;
- input/presentation contract;
- response schema and allowed vocabulary;
- confidence and abstention policy;
- assignment policy version;
- QC and consensus policy versions;
- interpretation limits;
- retention and licensing references.

Task definition changes that alter wording, input, presentation or response semantics require a new version.

## 4. Generated task

Required fields include task_id, task_type_id, task_definition_version, subject_ref, dataset_ref, dataset_version, manifest hash, presentation_version, selection_policy_version, selection_stream, machine_assessment_visibility and created_at.

The task must reference immutable source data and a pinned dataset manifest. Machine prediction visibility must be explicit. For blind ordinary annotation, the value should be hidden.

## 5. Contribution submission

Required fields include contribution_id, task_id, task_type_id, task_definition_version, response payload, pseudonymous contributor_ref, presentation_version, submitted_at and idempotency_key.

The response vocabulary is task-specific. Confidence range and interpretation must be declared by the task definition. Confidence must not be called calibrated without evaluation.

## 6. Contribution states

raw_received → schema_validated → quality_assessed → eligible_for_aggregation → aggregated → optionally expert_reviewed → optionally research_ready.

These are not a single mutable status field that overwrites history. Each transition is an append-only event with actor/system, timestamp, policy version and reason. Rejected or deferred responses remain auditable under the retention policy.

## 7. Consensus result

A consensus record must reference task and task-definition version; exact eligible contribution IDs; aggregation algorithm and version; QC policy version; response distribution; disagreement/agreement statistics; uncertainty and ambiguity state; input contribution manifest/hash; execution version and timestamp; and expert-review reference if any.

Never store only the winning label. Preserve all underlying responses and distributions. A numeric score in [0,1] is not called a probability unless calibration is demonstrated.

## 8. Dataset manifest

A release manifest should include dataset ID and semantic version; immutable record list or content-addressed partitions; source dataset/release references; task definition versions; selection/assignment/QC/consensus policy versions; included/excluded counts and reasons; annotation and disagreement statistics; provenance references and checksums; license and redistribution terms; privacy/consent/retention policy version; software commit and environment; release timestamp and parent release.

Corrections create a new release. Published releases are not rewritten.

## 9. Proposed API surface

Namespace: /api/v1/

| Method | Path | Purpose |
|---|---|---|
| GET | /tasks | List eligible tasks |
| GET | /tasks/{task_id} | Retrieve task and presentation contract |
| POST | /tasks/{task_id}/contributions | Submit idempotent contribution |
| GET | /objects/{object_id} | Retrieve permitted object context |
| GET | /objects/{object_id}/assessments | Retrieve assessments with provenance |
| GET | /candidates | List investigation candidates |
| GET | /candidates/{candidate_id} | Retrieve candidate evidence |
| GET | /datasets | List released datasets |
| GET | /datasets/{dataset_id} | Retrieve release metadata/manifest |
| GET | /contributors/me/summary | Privacy-aware personal summary |

Every endpoint requires request/response schemas, authentication and authorization, error semantics, rate limits, audit, tests and versioning before implementation.

## 10. Required contract tests

- valid and invalid task definitions;
- task version immutability;
- typed subject references;
- unresolved identity handling;
- response vocabulary and numeric bounds;
- abstention and confidence semantics;
- idempotent retry;
- conflicting duplicate rejection;
- immutable raw response;
- append-only state transitions;
- deterministic consensus reconstruction;
- disagreement preservation;
- dataset manifest reconstruction and hash verification;
- authorization and data isolation;
- API compatibility and error behavior.

## 11. Compatibility and non-goals

No existing ZTF model input contract, v0.2.0 benchmark or feature schema is modified. No automatic production retraining is introduced. No human consensus is promoted to ground truth. No public contributor network, gamification or external survey adapter is implied. Current API routes are not assumed to implement these proposed endpoints.
