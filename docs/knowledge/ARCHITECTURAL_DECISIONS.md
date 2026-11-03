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
| AOIC-001 | PROPOSED | Maintain a stable internal object identity separately from external catalog and survey identifiers. | Canonical identity and cross-match design; prevent OID/alias conflation. | Identity contracts, catalog adapters, provenance |
| AOIC-002 | PROPOSED | Matching must account for epoch, astrometric uncertainty and competing candidates; ambiguous/unmatched states are explicit. | Nearest-neighbour matching alone cannot establish astrophysical identity. | Match engine, review, scientific validation |
| AOIC-003 | PROPOSED | Identity changes use append-only decisions and merge/split lineage. | Preserve traceability and correction history. | Identity registry, audit, downstream lineage |
| CIN-001 | PROPOSED | CIN is an optional, logically independent human-intelligence subsystem. | ZTF Classifier must remain useful without CIN. | Architecture, API, deployment |
| CIN-002 | PROPOSED | Raw human contributions are immutable; QC, consensus, expert review and research-ready annotations are separate. | Preserve independent evidence and disagreement. | Data model, provenance, research datasets |
| CIN-003 | PROPOSED | Human consensus is not ground truth and cannot automatically trigger production retraining. | Protect benchmark validity and scientific authority boundaries. | Governance, model training, release gates |
| CIN-004 | PROPOSED | Active learning must retain random audits and representative sampling. | Measure selection bias and avoid over-sampling anomalies. | Scheduler, pilot protocol, evaluation |
| CIN-005 | PROPOSED | Begin with a controlled LC-01 pilot before public-network expansion. | Prove information value before scaling. | Roadmap, pilot protocol |

These entries are proposals until individually reviewed and adopted. They do not authorize changes to frozen baselines, model artifacts or production data.
