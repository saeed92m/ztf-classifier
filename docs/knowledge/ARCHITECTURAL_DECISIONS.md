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



| AD-VAL-001 | ADOPTED | CPVS is a claim-specific historical reproduction benchmark, not the definition of the general product. | Parallel validation plan; independent dataset and second-method workstreams. | Product architecture, validation roadmap, handbook |
| AD-VAL-002 | ADOPTED | General ingestion and analysis must not inherit dataset-specific selection rules without an explicit versioned adapter contract. | Prevents CPVS selection assumptions from contaminating unrelated inputs. | Ingestion, feature engine, adapters, tests |
| AD-VAL-003 | ADOPTED | A deterministic 50-object sample is diagnostic evidence, not a population-level performance claim by itself. | Sample-size scope and known-answer validation protocol. | Benchmark reports, scientific claims |
| AD-VAL-004 | ADOPTED | Ecosystem recommendations require implementation evidence, license review, and a project-specific acceptance test. | Systematic GitHub comparison and gap matrix. | Architecture, dependencies, roadmap |
