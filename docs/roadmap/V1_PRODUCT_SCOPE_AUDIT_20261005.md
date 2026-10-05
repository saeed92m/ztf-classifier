# v1.0 Product-Scope Audit — 2026-10-05

## Purpose

This audit is the executable gate between the published v0.5.0 scientific release and the v1.0 release freeze.

The audit does not infer completion from the existence of source files. It requires executable contract/integration tests across the declared P1-P6 product surfaces and a retained GitHub Actions evidence artifact.

## Scope

| Stage | Audit surface | Evidence |
|---|---|---|
| P1 | source subset manifest, normalization/QC, temporal controls, replay | source-subset and raw-dataset test contracts |
| P2 | feature engine, feature pipeline, parity, temporal invariance | feature-engine/pipeline contract tests |
| P3 | analysis executor, jobs, durable results, reports, incremental state | jobs/result/report/incremental tests |
| P4 | scientific validation and external-source evidence | existing scientific-validation release gate + external-source tests |
| P5 | API, catalog/report contracts, Workbench | API and Workbench contract tests |
| P6 | discovery/anomaly semantics, reproducibility, cumulative lifecycle | discovery/anomaly/reproducibility contracts |

## Release-boundary rule

The CPVS exact historical reconstruction remains a claim-specific external reproduction question. It is not silently promoted to a product failure by this audit.

## Acceptance

PASS requires:

1. locked dependencies install and pip check succeeds;
2. every selected P1-P6 contract/integration test succeeds;
3. all declared product surfaces exist at the audited commit;
4. an immutable audit record identifies the exact commit and workflow run;
5. no release-blocking issue is open.

After PASS, the next step is the final release-scope/reproducibility audit and release freeze. v1.0 is not declared by this document alone.
