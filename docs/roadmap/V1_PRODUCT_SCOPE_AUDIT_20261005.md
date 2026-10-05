# v1.0 Product-Scope Audit — 2026-10-05

This is the executable pre-freeze gate between v0.5.0 and v1.0.

| Stage | Audited surface |
|---|---|
| P1 | source subset, normalization/QC, temporal controls, replay |
| P2 | feature engine, pipeline, parity, temporal invariance |
| P3 | analysis executor, jobs, durable results, reporting, incremental state |
| P4 | external-source/scientific evidence contracts |
| P5 | API, catalog/report, Workbench |
| P6 | discovery/anomaly semantics and reproducibility |

PASS requires the dedicated workflow, dependency verification, all selected contract/integration tests, declared product-surface checks, retained evidence, and no release-blocking open issue.

The CPVS exact historical reconstruction remains a claim-specific external reproduction question and is not silently promoted to a product failure.

A PASS here does not itself declare v1.0; it authorizes the final release-scope/reproducibility audit and freeze.
