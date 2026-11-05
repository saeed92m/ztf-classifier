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


| AD-ECO-001 | ADOPTED | Split, sample, compare and report scientific data at complete object identity, not observation/row level. | Cross-repository leakage patterns and CPVS Seq-vs-row-ordinal failure; validate with object-overlap and full-vs-batch tests. | Data split, CPVS, batch processing, benchmarks |
| AD-ECO-002 | ADOPTED | Label roles must explicitly distinguish independent ground truth, reference labels and pseudo-labels; held-out label use is release-blocking leakage. | External classifier audits; labels derived from another model or threshold are not independent truth. | Benchmark manifests, training, evaluation |
| AD-ECO-003 | ADOPTED | Real/Bogus, classification, uncertainty, calibration, conformal prediction, OOD, anomaly evidence and explainability are separate channels. | Avoids semantic overclaiming and preserves interpretation. | Core contracts, UI, reports |
| AD-ECO-004 | ADOPTED | Full-vs-batch equivalence and data-quality edge cases require deterministic regression coverage. | External pipeline patterns and current CPVS validation requirements. | Ingestion, QC, batch inference, CI |
| AD-ECO-005 | DEFERRED | Gnuastro is not a mandatory dependency absent a demonstrated FITS/image/catalog need and comparative test. | Reduce dependency/platform burden; evaluate on a scoped prototype only. | Optional adapters, packaging |
| AD-ECO-006 | DEFERRED | mcp-stargazing is an optional future observational-planning interface, not part of the ZTF classifier scientific core. | Its documented scope differs from light-curve classification and CPVS reconstruction. | Optional MCP/product integrations |
| AD-ECO-007 | VERIFIED | External repository patterns are inspiration, not scientific evidence for our own model or membership rules. | Different data, label semantics, splits, task scope, maintenance and compute assumptions. | All model/tool adoption decisions |
