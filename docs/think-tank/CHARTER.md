# ZTF Classifier — Think Tank Charter and Operating Protocol

**Version:** 1.0.0 | **Date:** 2026-11-12 | **Status:** Canonical operating reference  
**Primary source:** Project Source `تعیین اعضای اتاق فکر.txt` and its 16-expert Master Prompt.  
**Related:** [Master Review](../THINK_TANK_MASTER_REVIEW_2026-11-12.md), [Session Register](SESSION_REGISTER.md).

## 1. Purpose and authority

The Think Tank is the permanent multidisciplinary review structure for ZTF Classifier. It must challenge assumptions and support the evolution of the project into a reliable, cross-platform Astronomical Data Analysis & Discovery Platform.

The 16 seats are simulated specialist perspectives in this working process. This is not a claim that 16 external human experts have been recruited or attended. Simulation supports structured challenge. It does not replace external peer review or expert adjudication.

The Founder / Project Owner is a separate authority role, outside the 16 seats. The Think Tank recommends. The Project Owner retains final authority over strategy, scope, budget, priorities, acceptance, merge authorization where required and release approval. The Think Tank must warn the owner when a request could weaken scientific validity, reliability, security or product integrity.

Every claim must be classified correctly: verified fact, historical evidence, hypothesis, proposed design, unresolved risk, implemented change, tested change, scientifically validated result or released capability. Do not promote a status without evidence.

## 2. The 16 permanent specialist seats

The seat names follow the supplied project source. Aliases in newer repository documents refer to the same seat; they do not create extra roles.

| No. | Seat | Main responsibility |
|---:|---|---|
| 01 | Chief Scientist / Principal Investigator | Scientific direction, research questions, astrophysical interpretation and limits on scientific claims. |
| 02 | ZTF Survey and Data Specialist | ZTF releases, survey systems, photometry, cadence, identifiers, data selection and survey limitations. |
| 03 | Time-Domain Astrophysicist | Variable and transient phenomena, taxonomy, physical interpretation, rare events and unknown classes. |
| 04 | Astronomical Statistics and Time-Series Specialist | Irregular sampling, measurement errors, time-series methods, periodicity, inference and uncertainty. |
| 05 | Astroinformatics and Big Data Engineer | Ingestion, raw-data preservation, pipelines, storage, indexing, incremental processing and provenance. |
| 06 | Catalog Cross-Matching and Source Identity Specialist | Catalog identity, astrometric association, ambiguity, epoch compatibility, aliases and source lineage. |
| 07 | Chief AI / Machine Learning Scientist | Features, model design, fair algorithm comparison, training strategy and ML boundaries. |
| 08 | Scientific Validation and Benchmark Specialist | Benchmark design, leakage, independent evaluation, calibration, temporal validation, OOD and generalization. |
| 09 | Scientific Software Architect | Module boundaries, domain contracts, architecture, versioning, compatibility and migration. |
| 10 | Backend and Platform Engineer | APIs, persistence, job execution, orchestration, transactions, retries and application integration. |
| 11 | MLOps, DevOps and Infrastructure Security Specialist | CI/CD, artifact integrity, security, dependencies, packaging, deployment, backup and restore. |
| 12 | QA and Reliability Engineer | Unit, integration, regression, scientific-contract, E2E, performance, recovery and cross-platform tests. |
| 13 | Scientific UX/UI and Visualization Designer | Researcher workflows, visual analysis, explainability, accessibility and user experience. |
| 14 | Product Manager and Commercialization Strategist | User needs, scope, prioritization, institutional requirements, acceptance and commercialization. |
| 15 | Scientific Documentation and Technical Communication Specialist | Source records, research docs, API guides, model cards, release notes and traceable claims. |
| 16 | Independent Evaluator / Red Team | Adversarial review of science, data, identity, ML, security, reliability, UX and product claims. |

## 3. Session composition

The 16 seats are permanent review capacity. They do not all need to participate in every working session.

| Session type | Seats | Use |
|---|---:|---|
| Decision core | 7–9 | Routine priorities and cross-subsystem decisions. |
| Specialist panel | 3–5 | Focused scientific, statistical, data, architecture or engineering questions. |
| Cross-disciplinary brainstorming | 6–10 | Alternatives, first-principles reasoning and design options. |
| Stage/release-gate review | All 16 | Major scientific, architecture, product and release decisions. |

Record the active roles and why they were selected. Do not claim that all 16 seats contributed when a smaller panel was used. Use all 16 for decisions that affect scientific validity, source identity, benchmark independence, protected baselines, production acceptance, security posture or public scientific claims.

## 4. Evidence ledger

Every material claim must be recorded with: claim ID, claim, evidence, exact revision, status, confidence, evidence gap and next action.

Allowed evidence states:

- `VERIFIED`
- `PARTIALLY_VERIFIED`
- `UNVERIFIED`
- `CONTRADICTED`
- `FAILED`
- `BLOCKED`
- `NOT_IMPLEMENTED`
- `NOT_APPLICABLE`

Keep implementation states separate:

- `PROPOSED`
- `DESIGNED`
- `IMPLEMENTED`
- `TESTED`
- `VALIDATED`
- `RELEASED`

A green CI run is engineering evidence, not scientific validation. A skipped test is not a pass. Missing data is not a negative result. An unavailable artifact cannot be replaced by a lab artifact without a validated decision. Never invent tests, data statistics, benchmark metrics, discoveries, external reviews, releases or customer evidence.

## 5. Mandatory 12-stage review process

Apply all 12 stages to a comprehensive project review. For focused work, record the relevant stages and explain why the others are not required.

### Stage 0 — Project recovery and knowledge reconstruction
Reconstruct project history, original objectives, scientific scope, decisions, failures, corrections, assumptions, product vision and immutable decisions.  
**Deliverable:** Project Knowledge Baseline.

### Stage 1 — Scientific foundation review
Review research questions, astrophysical scope, ZTF limitations, taxonomy, identity, data selection, photometry, errors, cadence, feature validity, statistics and reproducibility.  
**Deliverable:** Scientific Foundation Review.

### Stage 2 — Data architecture and pipeline audit
Review acquisition, identifiers, raw preservation, normalization, QC, missing data, duplicates, cross-band/OID links, partitions, cross-match, provenance, storage and recovery.  
**Deliverable:** Data lineage map and data-contract findings.

### Stage 3 — Machine learning and statistical audit
Review features, models, leakage, splits, validation, calibration, conformal prediction, OOD, domain adaptation, drift, external validation and interpretability.  
**Deliverable:** ML and Statistical Validation Review.

### Stage 4 — Software architecture and code audit
Review repository structure, module boundaries, contracts, error handling, logging, configuration, persistence, APIs, concurrency, performance, dependencies, security and technical debt.  
**Deliverable:** Code and Architecture Audit.

### Stage 5 — Product and user-experience review
Review the scientist workflow: dashboard, data manager, source explorer, light curves, analysis, model management, uncertainty, OOD, anomaly, cross-match, candidate management, human review, reports and support. For each proposal state user, purpose, input, output, dependencies, acceptance and scientific limits.  
**Deliverable:** Product Requirements and UX Review.

### Stage 6 — Discovery-science expansion
Assess rare transients, unusual variables, unknown classes, novelty, anomalies, similarity search, catalogs, ranking, human review, backtesting, alert readiness and multi-survey integration. Separate near-term capabilities from long-term research.  
**Deliverable:** Discovery Science Opportunity Review.

### Stage 7 — Independent adversarial review
Red Team must attempt to disprove claims. Investigate identity errors, false matches, selection bias, leakage, benchmark assumptions, misleading probabilities, corruption, feature semantics, invalid conclusions, reproducibility, security, packaging, UX, operations and product claims. Severity: CRITICAL, HIGH, MEDIUM, LOW, INFORMATIONAL. Each defect needs ID, evidence, subsystem, impact, root cause, reproduction, correction, regression test and acceptance criterion.  
**Deliverable:** Severity-ranked Defect Register.

### Stage 8 — Cross-expert brainstorming
Conduct three rounds: scientific excellence; engineering/product excellence; long-term differentiation/discovery. Use first principles, design review, Six Thinking Hats, Devil's Advocate, FMEA, pre-mortem, SWOT, trade-offs and architecture comparison. Preserve disagreement, rejected and deferred proposals, and evidence needed.  
**Deliverable:** Alternatives and Disagreement Record.

### Stage 9 — Final architecture design
Define data sources, adapters, raw preservation, normalization/QC, identity, features, statistics, inference, uncertainty, conformal prediction, OOD, anomaly, Real/Bogus, cross-match, discovery, ranking, human review, provenance, persistence, services, APIs, GUI, CLI, reporting, observability, security, tests and release.  
**Deliverable:** Diagrams, responsibilities, interfaces, contracts, dependencies, failure boundaries, versioning and migration.

### Stage 10 — Product definition and acceptance
Define product identity, users, use cases, functional/non-functional requirements, performance, security, scientific acceptance, platforms, installation, offline operation, docs, licensing, maintenance and packaging. Define COMPLETE exactly. Code existence is not completion.  
**Deliverable:** Product Definition and Acceptance Specification.

### Stage 11 — Execution roadmap
Build a dependency-aware roadmap: P0 critical blockers; P1 scientific foundation; P2 data and architecture; P3 core product; P4 advanced science; P5 cross-platform release; P6 independent scientific acceptance; P7 mature discovery platform. Each task needs ID, purpose, priority, dependencies, responsible role, output, tests, acceptance, risks, complexity and Definition of Done.  
**Deliverable:** Evidence-linked Execution Roadmap.

## 6. Required contribution from each active expert

Each active role must provide: initial assessment; strongest arguments; problems and risks; missing information; proposed improvements; evidence required; trade-offs; specific recommendation.

Experts must challenge one another. The coordinator must preserve meaningful disagreement.

## 7. Mandatory session record

Every substantial session must record:

1. Session ID, date, scope and status.
2. Exact repository branch and commit SHA reviewed.
3. Baseline, data, model and schema versions.
4. Issues, PRs, source files and artifacts inspected.
5. Active roles and meeting type.
6. Evidence ledger.
7. Role-by-role findings.
8. Disagreements and alternatives.
9. Red-Team challenges.
10. Recommendation and rationale.
11. Implementation tasks.
12. Tests and acceptance evidence.
13. Open questions and blockers.
14. Related GitHub issues, PRs and documents.
15. Project Owner approval status where required.

Use stable IDs such as `TT-2026-11-12-05`. Do not invent attendees, owners, approvals or consensus.

## 8. Decision and implementation controls

Recommendation states: `APPROVE`, `APPROVE_WITH_CONDITIONS`, `REVISE`, `BLOCK`, `DEFER`.

Implementation states: `NOT_STARTED`, `IN_PROGRESS`, `IMPLEMENTED`, `TESTED`, `VALIDATED`, `RELEASED`.

A recommendation is not authorization. A design is not implementation. Passing tests do not prove astrophysical validity.

Do not modify protected baselines, merge PRs, create releases, delete artifacts, change scientific acceptance criteria, weaken validation or alter production data without the required authority.

## 9. Mandatory cross-reference for engineering work

Every material PR, issue update, architecture change, scientific experiment or release decision must link to the Think Tank Session ID, source/prior decision, responsible specialist role(s), exact evidence/revision, test and acceptance gate, and unresolved objection or risk.

Routine low-risk changes may use a 3–5 role panel. Cross-cutting changes should use a 7–9 role core and Red Team. Major scientific, benchmark, security, product-acceptance and release gates require all 16 roles.

## 10. Protected project principles

- Scientific correctness comes before feature count or speed.
- Keep survey OIDs, observations, astrophysical sources and catalog aliases distinct.
- Never merge OIDs only because of positional proximity.
- Keep raw acquisition separate from normalized model-ready data.
- Keep ALeRCE, DR24 HATS and Zubercal DR20 semantics distinct.
- Do not silently fall back between selected sources.
- Keep classification, calibration, conformal prediction, OOD, anomaly, novelty and discovery ranking separate.
- Preserve uncertainty and unknown states.
- Prevent source-level and object-level leakage.
- Preserve provenance, hashes, manifests and replayable evidence.
- Protect scientific baselines and production artifacts.
- Do not claim scientific discovery or validation without the required gates.
- CIN remains a logically independent proposed subsystem. It must not change the standalone operation of ZTF Classifier.

## 11. Project Source register

| Project source or conversation | Governing use |
|---|---|
| `تعیین اعضای اتاق فکر.txt` (both supplied copies) | 16 seats, meeting composition, owner authority, Master Prompt and 12-stage process. |
| Project chat `تعیین اعضای اتاق فکر` | Original charter and adversarial review request. |
| `تایید سیاست همگرایی پروژه.txt` | CPVS-specific raw-data, fixed-sample, root-cause and regression rules. |
| `Branch · ... · گزارش وضعیت پروژه ... .txt` | Historical CPVS handoff. Reverify counts and status. |
| `ZTF CLASSIFIER — COSMIC INTELLIGENCE NETWORK.txt` | Canonical proposed CIN architecture and governance. It is not implementation authorization. |
| `ایده داده‌سازی جمعی.txt` | Original human-contribution concept; CIN canonical source governs detailed CIN conflicts. |
| `ارائه پارک علم و فناوری نسخه نهایی.pdf` | Submitted Park proposal. Preserve as historical source; use dated addenda. |
| `سند پروژه نسخه نهایی.pdf` | Submitted technical project document. Verify claims against current implementation. |
| Repository master review, defect register, roadmap and dated sessions | Current version-controlled synthesis and evidence. They do not override original scientific sources. |
| Project chats `ZTF - 01`, `Continue The Job` and status follow-ups | Conversation history, not proof of completed actions. |

Source precedence: (1) immutable external scientific source bytes and independently verified artifacts; (2) approved scientific baseline, validated data contracts and decisions; (3) current implementation and reproducible workflow evidence; (4) current approved Think Tank decisions; (5) historical reports; (6) proposals and hypotheses. Record conflicts. Do not silently replace the source of truth.

## 12. Current session records

See [SESSION_REGISTER.md](SESSION_REGISTER.md). Add each new material session to that register before relying on its conclusions as continuing project instructions.
