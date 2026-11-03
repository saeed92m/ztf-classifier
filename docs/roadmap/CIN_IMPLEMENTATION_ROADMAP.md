# Cosmic Intelligence Network — Implementation Roadmap

**Source:** ZTF-CIN-ARCH-001 v1.0.0  
**Tracking:** [Issue #251](https://github.com/saeed92m/ztf-classifier/issues/251)  
**Status:** Proposed; feasibility audit and documentation in progress; no runtime phase is complete.

## Guiding rules

- CIN is optional and logically independent.
- ZTF Classifier remains independently useful without CIN or network access.
- AOIC is the planned identity layer; CIN must preserve source IDs and unresolved identity until AOIC is accepted.
- Protect frozen scientific baseline v0.2.0 and immutable software release v1.0.1.
- Raw contributions are immutable; aggregates and expert decisions are separate.
- Consensus is not ground truth; novelty is not discovery.
- Active learning must retain random audit and representative samples.
- Human annotations never trigger automatic production retraining.
- Do not add paid infrastructure, microservices or broad catalog ingestion without measured need.
- Every milestone requires evidence, tests, documentation and governance review.

## Work packages

| ID | Work package | Deliverables | Exit criteria | State |
|---|---|---|---|---|
| C0 | Repository and scientific feasibility audit | Architecture mapping, source availability, data/license report, risks, reuse assessment | Actual route/storage/auth/job/UI/deployment boundaries inspected | Partial read-only assessment |
| C1 | Architecture and governance foundation | ADRs, formal contracts, task taxonomy, provenance, privacy/retention, threat model | Versioned contracts and governance approved | Proposed |
| C2 | LC-01 controlled MVP | Task generation, assignments, UI, contribution API/storage, audit | End-to-end task and contribution can be reproduced | Proposed |
| C3 | QC and consensus | Controls, repeated assessments, contributor estimates, disagreement, expert review | Consensus reproducible from immutable responses | Proposed |
| C4 | ZTF and human–AI integration | ZTF adapter, model output reference, selection policies, random audit | Blind and representative sampling with selection manifest | Proposed |
| C5 | Advanced annotation experiments | PAIR-01, NOV-01, SIM-01, PAT-01 | Each task family independently evaluated | Proposed |
| C6 | Image-based intelligence | IMG-01, image adapters, science/reference/difference provenance | Image evidence and artifact labels validated | Proposed |
| C7 | Research datasets and model experiments | Immutable releases, manifests, controlled experiments | Leakage-safe independent evaluation and documented value | Proposed |
| C8 | Community and multi-survey expansion | Public campaigns, researcher workspace, external survey adapters | Security, privacy, operational and scientific gates pass | Future |

## Detailed gates

### C0 — Feasibility

- [ ] Inspect API routes, authentication, authorization and current persistence.
- [ ] Inspect job/worker orchestration and idempotency.
- [ ] Inspect Workbench routing and accessible visualization.
- [ ] Map existing observation, discovery, review, model and provenance contracts.
- [ ] Confirm whether storage can isolate immutable raw contributions.
- [ ] Review ZTF light-curve source and presentation requirements.
- [ ] Review image availability, cutout provenance and licensing.
- [ ] Define privacy, consent, retention, deletion and attribution constraints.
- [ ] Confirm offline operation and deployment boundary.
- [ ] Record reuse versus build decisions.

### C1 — Contracts and governance

- [ ] Define typed subject references and AOIC interoperability.
- [ ] Freeze task-definition schema and semantic versioning.
- [ ] Define contribution and idempotency contracts.
- [ ] Define append-only contribution events and state transitions.
- [ ] Define consensus result and disagreement contracts.
- [ ] Define dataset release manifests.
- [ ] Complete threat model, privacy notice, consent and retention policy.
- [ ] Define data and annotation licensing.
- [ ] Create ADR records for adopted decisions.

### C2 — LC-01 MVP

- [ ] Pin source dataset and deterministic sample manifest.
- [ ] Implement task generation and independent assignment.
- [ ] Implement accessible task presentation with confidence/abstention.
- [ ] Implement immutable contribution storage and validation.
- [ ] Implement idempotent retries and duplicate conflict handling.
- [ ] Implement provenance readback and audit.
- [ ] Demonstrate end-to-end reconstruction.

### C3 — Quality and expert review

- [ ] Define independently validated control cases.
- [ ] Measure task-specific contributor performance.
- [ ] Implement repeated independent assessments.
- [ ] Implement response distributions and disagreement.
- [ ] Evaluate initial consensus estimator.
- [ ] Implement separate expert adjudication and rationale.
- [ ] Preserve all raw responses and historical decisions.

### C4 — Human–AI integration

- [ ] Add versioned model prediction references.
- [ ] Hide predictions from ordinary contributors where practical.
- [ ] Add uncertainty, novelty and disagreement streams.
- [ ] Maintain random audit and representative samples.
- [ ] Measure selection bias.
- [ ] Keep production retraining disabled.

### C5–C8 — Expansion

Each additional task family, image workflow, dataset release, model experiment, public campaign or survey adapter requires its own scientific objective, contracts, source/license review, test matrix, independent validation and release gate.

## Milestone rules

A created task or page is not implementation. A green ordinary CI workflow is not scientific validation. A working MVP is not scientific effectiveness. A public network is not required for the first pilot.

Do not publish a CIN release until privacy, security, data rights, reproducibility, scientific validation and recovery requirements pass.

## Relationship to the platform roadmap

CIN extends the discovery and human-review track. It does not replace the core desktop product, AOIC identity work, data acquisition or independent scientific validation. It must remain separately measurable so CIN planning does not inflate readiness estimates for the existing ZTF product.


## Reference specifications

- [Canonical architecture companion](../architecture/COSMIC_INTELLIGENCE_NETWORK_v1.0.0.md)
- [Repository integration assessment](../CIN_INTEGRATION_ASSESSMENT_2026-11-03.md)
- [Task, contribution, consensus and dataset contracts](../api/CIN_DATA_CONTRACTS_v0.1.md)
- [LC-01 scientific pilot protocol](../research/CIN_LC01_PILOT_PROTOCOL_v0.1.md)
- [Participation and contributor experience](../product/CIN_PARTICIPATION_STRATEGY_v0.1.md)
- [Governance, privacy, security and risk](../governance/CIN_GOVERNANCE_AND_RISK_v0.1.md)
- [Proposed decision register](../knowledge/ARCHITECTURAL_DECISIONS.md)
