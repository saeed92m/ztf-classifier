# Cosmic Intelligence Network (CIN) — Architecture v1.0.0

**Canonical source:** ZTF CLASSIFIER — COSMIC INTELLIGENCE NETWORK  
**Document ID:** ZTF-CIN-ARCH-001  
**Source version:** 1.0.0  
**Status:** Proposed architecture; feasibility and contract design only; no runtime implementation is claimed  
**Tracking:** [Issue #251](https://github.com/saeed92m/ztf-classifier/issues/251)

> This repository document translates the user-supplied canonical source into architecture and implementation boundaries. It does not replace the canonical source, authorize the complete network, or claim that proposed features are implemented.

## 1. Purpose and strategic position

CIN is a human-in-the-loop astronomical intelligence and collaborative annotation subsystem. It converts carefully designed human interactions into structured, measurable, quality-controlled and traceable scientific evidence.

CIN is not a simple voting tool, informal feedback form or gamification layer. Its scientific purpose is to support annotation, comparison, prioritization, anomaly investigation, research dataset construction and controlled evaluation of machine-generated assessments.

The long-term vision is a survey-agnostic human intelligence layer. ZTF is the first planned scientific integration. TESS, Gaia, Rubin/LSST, JWST and other surveys are future adapter opportunities only. No partnership, integration, dataset or capability is implied by listing them.

## 2. Product boundaries

The ecosystem contains three distinct scientific capabilities:

| System | Primary responsibility | Required boundary |
|---|---|---|
| ZTF Classifier | Computational astronomy: ingestion, QC, features, ML/statistics, calibration, uncertainty, OOD, anomaly evidence and reproducible analysis | Useful without CIN or network access |
| AOIC | Canonical astronomical identity, catalog aliases, cross-match evidence, identity decisions and lineage | Does not treat proximity or catalog labels as unquestionable truth |
| CIN | Human tasks, independent annotations, quality control, consensus, expert review, active learning and research datasets | Optional and independently governed |

The systems communicate through versioned contracts. None is an unquestionable source of truth for another.

CIN must not be embedded into the classifier's scientific core. CIN being unavailable must not interrupt local ingestion, analysis, inference, benchmark evaluation or reporting.

Company-Platform may later provide optional discovery, account, institutional or public-portal integration. It is not a runtime dependency of ZTF Classifier or CIN.

## 3. Non-negotiable scientific constraints

- Preserve frozen scientific baseline v0.2.0, its benchmark, 42-feature contract, class order, model artifact and acceptance gates. Verify exact artifacts before repeating baseline details as current facts.
- Preserve v1.0.1 as a separate immutable software release identity.
- Do not add crowdsourced annotations to the protected benchmark.
- Do not modify benchmark labels or retroactively alter model predictions.
- Do not introduce human-derived features into the frozen feature contract.
- Do not trigger production retraining automatically from contributions or consensus.
- Keep original observations, derived features, machine predictions, raw human contributions, aggregates, expert annotations, research datasets, training datasets and frozen evaluation datasets logically separate.
- Keep uncertainty and abstention available. Never force a participant to select a known class.
- Consensus is an aggregate estimate, not ground truth. Expert review is a distinct evidence class, not an overwrite of community data.
- Novelty and anomaly scores are prioritization signals, not discoveries.
- Preserve disagreement and all underlying responses.
- Evaluate selection bias, correlated judgments, leakage, calibration and generalization before using annotations for model experiments.

## 4. Initial architecture

Use a modular monolith with explicit versioned API contracts and independently governed scientific data storage. Do not introduce microservices until measured workload, isolation, scaling or deployment needs justify them.

Core modules:

1. Scientific Data Adapter — references source observations and immutable datasets; validates schema and provenance; prepares task-ready data without unnecessary archive duplication.
2. Task Generation Engine — reproducible task creation from versioned definitions, eligibility rules and policies.
3. Task Allocation Engine — independent repeated assignments, diversity, assignment limits and balanced coverage.
4. Human Interaction Layer — accessible desktop/mobile task presentation, response, optional confidence and abstention.
5. Contribution Ingestion Engine — validation, idempotency, duplicate handling, immutable raw response storage and audit.
6. Consensus Engine — response aggregation, disagreement, uncertainty and expert escalation.
7. Contributor Intelligence Engine — task-family-specific estimates from validated controls; never a universal scientific-authority score.
8. Active Learning Scheduler — uncertainty, novelty, disagreement, relevance and cost, balanced with random audit and representative sampling.
9. Research Dataset Manager — immutable, versioned datasets, manifests, inclusion/exclusion rules, provenance and licensing.
10. Expert Review Module — separate specialist adjudication and rationale.

The scientific adapter must reference the exact source dataset, source record, observation and identity evidence used by each task.

## 5. Task taxonomy

Task IDs and definitions are versioned. These are initial annotation vocabularies, not validated astrophysical class taxonomies.

| Task ID | Name | Purpose | Limitation |
|---|---|---|---|
| LC-01 | Light Curve Assessment | Human assessment of temporal morphology | A morphology label is not an astrophysical class |
| IMG-01 | Image Artifact Assessment | Assess science/reference/difference image evidence | A light curve alone cannot establish image artifact status |
| PAIR-01 | Pairwise Comparison | Relative comparison or ranking of samples | Preference is not an absolute class label |
| PAT-01 | Pattern Recognition | Annotate periodic, quasi-periodic, irregular, flare-like, eclipsing-like, transient-like or complex patterns | Categories require versioned instructions |
| NOV-01 | Novelty Assessment | Prioritize candidates for investigation | Not proof of discovery |
| SIM-01 | Similarity Assessment | Human-guided similarity, clustering and representation research | Similarity depends on task context |

Every task definition must include a unique ID, semantic version, objective, supported input, input schema, response vocabulary, confidence and abstention rules, presentation requirements, QC/assignment/consensus policies, interpretation limits, retention rules and acceptance criteria.

Changes to question wording, visual presentation or response vocabulary require a new task-definition version because they may change annotation meaning.

## 6. Contribution lifecycle and data separation

Each contribution receives a unique ID and records task ID/type/version, typed subject reference, dataset/version, pseudonymous contributor reference, response payload, optional confidence, timestamp, presentation version, QC state and provenance.

Required distinct states:

- raw response;
- schema-validated response;
- quality-assessed response;
- aggregated assessment;
- expert-reviewed annotation;
- research-ready annotation.

Raw responses are immutable. Corrections or adjudications create new linked records. Do not overwrite the original response.

Minimum logical entities:

| Entity | Purpose |
|---|---|
| scientific_subject_refs | Typed references to object, event, detection, observation or dataset records |
| observation_bundles | Immutable source observation references and provenance |
| dataset_sources | Source registry, releases, access and license context |
| task_definitions | Versioned task contracts |
| tasks | Generated scientific tasks |
| task_assignments | Allocation and repeated independent assignment |
| contributions | Immutable raw human responses |
| contribution_events | Append-only submission and audit events |
| gold_standard_items | Independently validated control examples |
| contributor_profiles | Pseudonymous contributor references and consent state |
| contributor_skill_estimates | Task-family-specific estimates and calibration |
| model_predictions | Versioned machine assessments |
| consensus_results | Reproducible aggregates and disagreement statistics |
| expert_reviews | Separate expert assessments and adjudication rationale |
| discovery_candidates | Scientific investigation queue |
| dataset_releases | Immutable research dataset versions |
| dataset_manifests | Composition, source lineage, checksums, license and QC |
| policy_versions | Versioned assignment, selection and quality-control policies |

Physical table names and storage technology remain open until repository, deployment and offline requirements are assessed.

### 6.1 Subject identity and AOIC dependency

A task must use a typed subject reference, not an ambiguous free-text identifier. It may refer to a canonical object_id, a transient event_id, a detection, an observation or a versioned dataset record.

AOIC is a proposed identity subsystem and is not yet an accepted runtime dependency. Until AOIC contracts are reviewed and implemented, CIN must preserve original survey/catalog identifiers and source provenance. It must not fabricate a canonical object identity.

Where a source is unresolved, the task records that state. It must not silently merge multiple survey OIDs or observations into one physical object.

## 7. Quality control and consensus

Quality control combines independently validated control examples, repeated independent assessments, blind presentation where practical, randomized order, task-specific contributor calibration, uncertainty and abstention analysis, response consistency, expert escalation, random audits and representative sampling.

Control examples require documented independent reference evidence. ALeRCE reference labels alone must not be described as independent astrophysical ground truth.

Response time alone is not a quality score. Consensus methods may start with majority vote, response distributions, agreement measurement, confidence aggregation and explicit ambiguity detection. Dawid–Skene, GLAD, hierarchical Bayesian and task-specific latent-class methods are later experiments. Every method requires evaluation against independently adjudicated reference data.

Preserve individual responses, distributions, confidence, contributor-level uncertainty estimates, model disagreement and expert decisions. Consensus must never erase disagreement.

## 8. Active learning and selection bias

Task priority may consider model uncertainty, novelty, disagreement, scientific relevance, sample coverage, annotation cost and expected information value.

Maintain separate streams for uncertainty, novelty, model disagreement, random audit, representative sampling and underrepresented classes.

Do not assume selection factors are independent. Do not allow only unusual or uncertain candidates to dominate the dataset. Evaluate selection policy and selection bias. Human–AI disagreement is a review signal, not an automatic verdict against either source.

Human annotations must not automatically trigger production retraining. Any model experiment requires a separately versioned dataset, leakage-safe splits, a controlled experiment and independent evaluation against protected benchmarks.

## 9. API and integration boundary

Proposed namespace: /api/v1/. Candidate endpoint families (not existing endpoints):

- GET /api/v1/tasks
- GET /api/v1/tasks/{task_id}
- POST /api/v1/tasks/{task_id}/contributions
- GET /api/v1/objects/{object_id}
- GET /api/v1/objects/{object_id}/assessments
- GET /api/v1/candidates
- GET /api/v1/candidates/{candidate_id}
- GET /api/v1/datasets
- GET /api/v1/datasets/{dataset_id}
- GET /api/v1/contributors/me/summary

Each interface requires request/response schemas, authentication and authorization, error semantics, rate limits, idempotency and tests before implementation.

ZTF Classifier may expose stable source references, feature schema, prediction/model/artifact identity, uncertainty, anomaly evidence and observation provenance. CIN must not depend on internal ML implementation details. ZTF Classifier must not depend on CIN for normal operations.

## 10. Privacy, security, licensing and attribution

Participation must be transparent and informed. Explain contribution purpose, telemetry, intended uses, public/private status, retention/deletion, attribution and privacy options.

Collect only purpose-limited telemetry such as task completion, abandonment, optional confidence, presentation version and repeated attempts. Do not collect unrelated browsing behavior, device fingerprints, unnecessary location or sensitive personal data.

Required controls include authentication where needed, role separation, validation, rate limits, abuse controls, idempotency, audit logs, secret management, database access restrictions, backup/restore tests and retention enforcement.

Review rights and licenses for source astronomy data, derived assets, submitted annotations and public dataset releases. Do not assume open source data means unrestricted redistribution of every derivative.

Recognition and gamification are optional. They must not reward speed over quality, guessing, volume-only participation or imply professional credentials. Public attribution must respect consent and publication policy; do not promise authorship to all contributors.

## 11. Deployment and resilience

Avoid premature infrastructure. Initial deployment may use existing compatible Python components, a lightweight API, PostgreSQL-compatible storage, object storage only where necessary, queues only when asynchronous workloads require them, and containers where useful. The exact stack requires repository and infrastructure assessment. No paid infrastructure is assumed for the first prototype.

CIN outage must not affect local ZTF analysis, inference, benchmark evaluation or reporting. Backup and restoration procedures must be tested before production deployment.

## 12. Research datasets and publication

Dataset releases are immutable and versioned. Corrections create a new release. Manifests identify included/excluded records, task and policy versions, QC statistics, source references, checksums, licenses, privacy policy and persistent identifiers where available.

Future outputs may include light-curve annotation, image artifact, anomaly prioritization, pairwise similarity and human–AI evaluation datasets. These are planned outputs, not guaranteed results.

## 13. Validation and release gates

Tests must cover task generation/validation, response validation, consensus, contributor estimates, candidate selection, dataset construction, ZTF/model adapters, persistence, assignment, expert review, API security, duplicate submissions, authorization, data isolation, provenance and end-to-end reconstruction.

Scientific evaluation must measure agreement against independently validated references, inter-annotator agreement, uncertainty, expert adjudication, false positives/negatives, task presentation effects, selection bias, correlated errors, downstream utility and generalization.

A release is blocked by incomplete provenance, lost/modified raw responses, unreproducible datasets, benchmark contamination, incompatible API contracts, critical security failures, irreproducible consensus or claims beyond the evidence.

An operational MVP is not proof of scientific effectiveness. Model improvement requires a separate predeclared validation study and independent evaluation.

## 14. Staged roadmap

| Phase | Scope | Exit evidence |
|---|---|---|
| C0 | Repository and scientific feasibility audit | Architecture compatibility, source/data availability, license, risk and reuse report |
| C1 | Foundation and governance | Versioned contracts, data model, task taxonomy, provenance, privacy/retention, threat model |
| C2 | LC-01 controlled MVP | End-to-end task, contribution, immutable storage, retrieval and provenance |
| C3 | QC and consensus | Validated controls, repeated assessments, reproducible consensus, disagreement and expert review |
| C4 | ZTF and human–AI integration | Versioned adapter, selection manifest, blind/random streams and bias report |
| C5 | PAIR-01, NOV-01, SIM-01 | Separate task experiments and independent usefulness assessment |
| C6 | IMG-01 image intelligence | Image adapters, science/reference/difference provenance and artifact annotation validation |
| C7 | Research datasets and model experiments | Immutable manifests, controlled experiments, baseline comparison and leakage checks |
| C8 | Community and multi-survey expansion | Secure public workflows, researcher tools and separately validated adapters |

Do not implement all modules at once. Prove measurable information value with a controlled LC-01 pilot before investing in large-scale gamification or infrastructure.

## 15. Initial pilot recommendation — LC-01

A controlled pilot should include representative samples and deliberately selected unusual samples, independently validated controls, blind presentation, independent responses, optional confidence and abstention, expert comparison, disagreement preservation, random audits and a predeclared analysis plan.

Do not choose a fixed participant count, annotation count or duration before feasibility and statistical power considerations are assessed.

The pilot question is: **Do human assessments add measurable information beyond the existing machine-learning workflow for the declared task and sample population?**

## 16. Institutional positioning

CIN may be described in proposals as a planned R&D subsystem for structured human participation in astronomical analysis. Do not claim a global network, completed crowdsourced dataset, validated discovery, accuracy improvement, mission integration or institutional partnership unless evidence exists.

## 17. Decision register

The canonical source proposes CIN-ADR-001 through CIN-ADR-015: logical independence; independent ZTF operation; modular architecture; immutable contributions; separation of consensus and expert validation; benchmark protection; versioned annotations; active learning; random audits; approved model retraining only; transparent participation; future survey adapters; optional Company-Platform integration; evidence-based scientific claims; and staged implementation.

These are proposed decisions until reviewed and explicitly adopted in repository ADR records.

## 18. Agent and developer operating rules

Before implementation, inspect repository, branch and working tree, instructions, handbook, architecture, roadmap, tests, release gates and this source. Map each requirement to an existing module or explicit gap.

Preserve the scientific baseline. Keep CIN independent. Avoid premature microservices, dependencies, paid infrastructure and public launch. Do not claim proposed features as implemented. Every accepted implementation change must update impacted architecture, handbook, roadmap, API/data contracts, tests, Model Card impact assessment, changelog and release criteria as appropriate.

If a proposed change conflicts with a frozen baseline, approved ADR, validated contract, security policy or production requirement, stop and document the conflict. This source is a canonical proposal, not authority to override higher-priority controls.

For substantial CIN work, report repository/branch, completed work, remaining work, tests, scientific risks, data governance, documentation sync, integration impact and next action. Distinguish proposed, designed, implemented, tested, validated and released.

## 19. Immediate deliverables

- CIN Integration Assessment.
- Individual ADR records and unresolved design decisions.
- Prioritized implementation backlog.
- Formal task/contribution/consensus/dataset contracts.
- Scientific pilot protocol.
- Documentation synchronization.

## 20. Definition of done

CIN is not complete when a UI or vote counter exists. It is complete only when raw human evidence is immutable and traceable; task definitions and policies are versioned; quality and uncertainty are measured; disagreement and expert review are preserved; selection bias is evaluated; datasets are reproducible and licensed; protected benchmarks remain isolated; human-assisted experiments are independently validated; and the optional subsystem cannot compromise standalone ZTF Classifier operation.

**Final principle:** ZTF Classifier supplies computational analysis. CIN supplies structured human-generated evidence. AOIC supplies traceable identity and cross-match evidence. Together they form a governed human–AI astronomical discovery architecture.
