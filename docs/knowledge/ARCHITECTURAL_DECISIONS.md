# Architectural Decisions Knowledge

| ID | Status | Decision | Evidence / rationale | Propagated to |
|---|---|---|---|---|
| AD-CI-001 | VERIFIED | Scientific validation is a permanent product-level gate. | Registry, executable gate, release fail-closed contract. | Release, roadmap, testing |
| AD-CI-002 | VERIFIED | Ground truth and independent reference agreement remain separate. | Manifest evaluation-role contract and regression tests. | Benchmarks, reports |
| AD-CI-003 | VERIFIED | External scientific datasets are not committed to Git. | Reproducibility and provenance contract. | Benchmark registry |
| AD-CI-004 | VERIFIED | Cumulative learning is a lifecycle control, not documentation-only. | Stage contract, ledger, knowledge layer, and executable validation. | All future stages |
| AD-CI-005 | VERIFIED | Local optimization cannot override scientific validity or release integrity. | Multi-objective quality vector and trade-off rules. | Model, feature, performance, release |
| AD-CI-006 | VERIFIED | Historical external-benchmark reconstruction is a claim-specific evidence scope and is not the product execution path. | CPVS 730k discrepancy analysis and PR #124 recovery architecture. | Scientific validation gate, roadmap, CI |
