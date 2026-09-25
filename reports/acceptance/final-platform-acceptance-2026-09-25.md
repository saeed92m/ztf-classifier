# Final Platform Acceptance Evidence

Date: 2026-09-25
Main commit audited: acc9bafaa15016196c09ec286428aba21c6593a9
Software version: 0.4.0
Scientific baseline: v0.2.0
Production model: baseline_v0.2

## Purpose

This document records the executable evidence available on the merged `main`
commit for the Astronomical Data Analysis & Discovery Platform layer. It does
not convert unavailable data-dependent validation into a success claim.

## Current CI evidence

The latest merged `main` CI run completed successfully:

- Ruff lint: PASS
- Ruff format check: PASS
- pytest: PASS — 437 passed, 4 skipped, 7 warnings
- package build: PASS
- wheel installation: PASS
- pip check: PASS
- package import: PASS
- pip-audit/dependency audit: PASS
- CodeQL: PASS

The repository has no open pull requests at the time of this audit.

## Acceptance matrix

| Area | Status | Evidence / limitation |
|---|---|---|
| v0.2.0 scientific baseline | VERIFIED | Existing immutable baseline contract and regression tests remain in repository. |
| Frozen v0.2 feature schema | VERIFIED | 42-feature schema and parity/contract tests are present and CI-green. |
| Source-backed scientific results | VERIFIED | API/application contracts and source-backed executor tests are CI-green. |
| Durable job lifecycle | VERIFIED | Job store/worker tests, including transition hardening, are CI-green. |
| Idempotent scientific results | VERIFIED | Scientific result store integration tests are CI-green. |
| Monotonic incremental checkpoints | VERIFIED | Checkpoint regression/idempotency tests are CI-green. |
| Versioned API contracts | VERIFIED | FastAPI v1 routes and schema tests are CI-green. |
| Stable API error boundary | VERIFIED | Contract error and unexpected-error handlers are tested. |
| Request IDs / optional bearer auth | VERIFIED | API middleware and authentication tests are CI-green. |
| Bounded catalog/export | VERIFIED | Catalog and API tests are CI-green. |
| Feature backend discovery/selection | VERIFIED | Feature engine and job persistence tests are CI-green. |
| API-backed Workbench | VERIFIED | Workbench/API tests are CI-green. |
| Deterministic report export | VERIFIED | Reporting tests are CI-green. |
| Runtime DB exclusion | VERIFIED | SQLite runtime paths are ignored by Git and persistence tests are CI-green. |
| CI/package gates | VERIFIED | Latest main CI is fully green. |
| Code security analysis | VERIFIED | Latest main CodeQL run is green. |
| Artifact schema 1.0 compatibility | VERIFIED | Loader compatibility tests are present and CI-green. |
| Artifact schema 1.1 compatibility | VERIFIED | Diagnostic artifact compatibility tests are present and CI-green where fixture-backed. |
| Calibration/conformal/OOD separation | VERIFIED | Independent diagnostic paths and status contracts are tested. |
| Ingestion validation | VERIFIED | ALeRCE validation/diagnostic test suite is CI-green. |
| Data Card / Model Card | VERIFIED | Both documents are present on main. |
| Temporal leakage controls | VERIFIED | Temporal audit artifacts and validation tests are present and CI-green. |
| Real raw-detection feature parity | NOT VERIFIED | Requires a raw detection cache intentionally excluded from Git. |
| Raw-dataset validation integration | NOT VERIFIED | Requires the external/raw benchmark cache, intentionally excluded from Git. |
| Offline raw-feature reproduction | NOT VERIFIED | Requires the raw benchmark cache, intentionally excluded from Git. |
| Local WSL2 clean-room reproduction | NOT VERIFIED | This connector cannot execute arbitrary commands in the user's local WSL2 environment. |

## Skipped CI tests

The four skipped modules are data-dependent integration suites:

- `tests/test_feature_pipeline_parity.py`
- `tests/test_raw_dataset_validation_integration.py`
- `tests/test_offline_feature_dataset_reproduction.py`
- `tests/test_model_production_inference.py`

The skips are conditional on raw caches or a legacy production artifact that are
not committed to the repository. They are therefore recorded as
`NOT VERIFIED`, not as passes.

## Scientific limitations

- benchmark_v0.2 contains 150 objects across 15 classes and is not population-representative;
- ALeRCE labels are reference/weak labels rather than independent astrophysical ground truth;
- real-world OOD behavior and temporal generalization require independent larger-scale datasets;
- external-source licensing, attribution, and terms of use remain required for future publication or redistribution.

## Release posture

The package metadata is already at 0.4.0 and the release workflow is tag-driven.
A release tag should only be created after the remaining data-dependent
validation requirements are deliberately accepted or executed with the required
raw/source environment.

## Decision rule

This evidence report does not declare the entire platform scientifically
complete while the explicitly listed data-dependent validations remain
`NOT VERIFIED`. It establishes the exact boundary between executable
repository evidence and environment/data-dependent evidence.
