# Architectural Decisions Knowledge

| ID | Status | Decision | Evidence / rationale | Propagated to |
|---|---|---|---|---|
| AD-CI-001 | VERIFIED | Scientific validation is a permanent product-level gate. | Registry, executable gate, release fail-closed contract. | Release, roadmap, testing |
| AD-CI-002 | VERIFIED | Ground truth and independent reference agreement remain separate. | Manifest evaluation-role contract and regression tests. | Benchmarks, reports |
| AD-CI-003 | VERIFIED | External scientific datasets are not committed to Git. | Reproducibility and provenance contract. | Benchmark registry |
| AD-CI-004 | VERIFIED | Cumulative learning is a lifecycle control, not documentation-only. | Stage contract, ledger, knowledge layer, and executable validation. | All future stages |
| AD-CI-005 | VERIFIED | Local optimization cannot override scientific validity or release integrity. | Multi-objective quality vector and trade-off rules. | Model, feature, performance, release |
| AD-CI-006 | VERIFIED | Historical external-benchmark reconstruction is a claim-specific evidence scope and is not the product execution path. | CPVS 730k discrepancy analysis and PR #124 recovery architecture. | Scientific validation gate, roadmap, CI |


| AD-PROD-001 | ADOPTED | The product is a cross-platform Astronomical Data Analysis & Discovery Platform, not classifier-only. | Ecosystem review and existing platform architecture. | README, handbook, architecture, roadmap |
| AD-PROD-002 | ADOPTED | Desktop GUI is a product layer over stable scientific Core contracts; CLI/API remain supported. | Prevents GUI-driven scientific-core rewrites and preserves automation. | Architecture, packaging, UX |
| AD-PROD-003 | ADOPTED | Normal users must have self-contained installation on Windows/macOS/Linux without Python/pip/venv/Git/terminal. | User-path review and product usability requirement. | Packaging, release, installation |
| AD-PROD-004 | ADOPTED | Object/Source Explorer and provenance/evidence UI are first-class product capabilities. | Scientific discovery workflows require source-level inspection and reproducibility. | GUI, results, reports |
| AD-PROD-005 | ADOPTED | Cross-match, similar-object search, human review, discovery ranking, and Real/Bogus are explicit architectural boundaries. | Ecosystem review identified these as reusable patterns with clear scientific semantics. | Discovery architecture, analysis modes |
| AD-PROD-006 | ADOPTED | OOD, uncertainty, scientific anomaly, catalog evidence, and explainability remain separate evidence channels. | Prevents semantic overclaiming. | Result contracts, UI, validation |
| AD-PROD-007 | ADOPTED | Future alert/streaming support must be enabled by contracts without weakening deterministic offline/batch workflows. | Preserves reproducibility while allowing operational scaling. | Ingestion, orchestration |


## Proposed architecture decisions — 2026-11-03

| ID | Status | Decision | Evidence / rationale | Propagated to |
|---|---|---|---|---|
| AOIC-001 | PROPOSED | Maintain stable internal object identity separately from external catalog and survey identifiers. | Canonical identity and cross-match design; prevent OID/alias conflation. | Identity contracts, catalog adapters, provenance |
| AOIC-002 | PROPOSED | Matching accounts for epoch, astrometric uncertainty and competing candidates; ambiguous/unmatched states remain explicit. | Nearest-neighbour distance alone cannot establish astrophysical identity. | Match engine, review, validation |
| AOIC-003 | PROPOSED | Identity changes use append-only decisions and merge/split lineage. | Preserve traceability and correction history. | Identity registry, audit, lineage |
| CIN-ADR-001 | PROPOSED | CIN is a logically independent subsystem. | Separate human intelligence from the computational core. | Architecture, deployment |
| CIN-ADR-002 | PROPOSED | ZTF Classifier remains independently functional. | CIN outage must not interrupt local analysis, inference, benchmark evaluation or reports. | Core services, deployment, tests |
| CIN-ADR-003 | PROPOSED | Initial implementation uses modular architecture. | Avoid premature distributed services and infrastructure. | Architecture, operations |
| CIN-ADR-004 | PROPOSED | Raw human contributions are immutable. | Preserve original evidence and audit history. | Data model, ingestion, provenance |
| CIN-ADR-005 | PROPOSED | Consensus and expert validation are separate. | Aggregate judgments do not equal expert adjudication or ground truth. | Consensus, review, datasets |
| CIN-ADR-006 | PROPOSED | Existing benchmark remains protected. | Prevent benchmark contamination and leakage. | Benchmark, training, validation |
| CIN-ADR-007 | PROPOSED | Human annotations are versioned and traceable. | Task, presentation, policy and dataset versions affect annotation semantics. | Contracts, manifests, reports |
| CIN-ADR-008 | PROPOSED | Active learning guides task selection. | Prioritize uncertainty, novelty, disagreement and information value. | Scheduler, selection policy |
| CIN-ADR-009 | PROPOSED | Random audit and representative samples are mandatory. | Detect selection bias and preserve population coverage. | Sampling, pilot, evaluation |
| CIN-ADR-010 | PROPOSED | Model retraining requires independent approval. | Human data cannot automatically change production models. | Model governance, releases |
| CIN-ADR-011 | PROPOSED | Participation and telemetry are transparent and purpose-limited. | Protect consent, privacy and trust. | UX, privacy, retention |
| CIN-ADR-012 | PROPOSED | External survey integrations are future extensions. | Each adapter requires source, license and scientific validation. | Adapters, roadmap |
| CIN-ADR-013 | PROPOSED | Company-Platform integration is optional. | Avoid a hard dependency on a separate company platform. | Deployment, integration |
| CIN-ADR-014 | PROPOSED | Scientific claims require reproducible evidence. | Prevent unsupported claims about discoveries or model improvement. | Validation, publications, releases |
| CIN-ADR-015 | PROPOSED | Implementation follows staged feasibility gates. | Prove value with a controlled LC-01 pilot before network expansion. | Roadmap, lifecycle, release |

These decisions remain proposals until individually reviewed and adopted. They do not authorize changes to frozen baselines, model artifacts or production data.

Canonical CIN source and detailed requirements: [architecture](../architecture/COSMIC_INTELLIGENCE_NETWORK_v1.0.0.md), [participation strategy](../product/CIN_PARTICIPATION_STRATEGY_v0.1.md), [governance and risk](../governance/CIN_GOVERNANCE_AND_RISK_v0.1.md), [Issue #251](https://github.com/saeed92m/ztf-classifier/issues/251).
