# v0.4.0 Complete Upgrade Report

Date: 2026-09-25
Current audited main commit: 43f4082369e0f2f0bd6614668ca99bff90818a1c
Scientific baseline: v0.2.0
Production model: baseline_v0.2

## Summary

The v0.4.0 production-oriented upgrade has been implemented without mutating the immutable v0.2.0 scientific baseline, the benchmark_v0.2 dataset contract, or the frozen 42-feature schema.

The platform now includes reproducibility/provenance controls, artifact integrity validation, independent calibration/conformal/OOD diagnostics, strict ALeRCE ingestion diagnostics, temporal leakage controls, durable analysis services, catalog/report/export contracts, an extensible Scientific Feature Engine, API/Workbench integration, registry-backed inference, and hardened CI/security/release automation.

PR #54 (`fix: decouple production diagnostic artifacts`) is merged into `main` at the audited commit above.

## Implemented areas

- software version 0.4.0;
- canonical requirements.lock from the verified CI environment;
- streaming SHA-256 checksum utility;
- artifact manifest hashing and provenance metadata;
- explicit legacy integrity warnings;
- independent calibration, conformal, and OOD diagnostics;
- strict ALeRCE validation and ingestion diagnostics;
- additive CLI and batch provenance/status metadata;
- Data Card and Model Card;
- frozen feature provenance and temporal leakage validation;
- durable jobs, scientific results, checkpoints, catalog, reports, and Workbench contracts;
- extensible Scientific Feature Engine backend registration/selection;
- optional API-key protection and request-ID observability;
- CodeQL and Dependabot;
- package/build/dependency quality gates.

## Important compatibility guarantees

- `v0.2.0` scientific baseline remains immutable.
- `benchmark_v0.2` remains unchanged.
- Frozen feature schema remains 42 features.
- Production model identity remains `baseline_v0.2`.
- Artifact schemas 1.0 and 1.1 remain readable.
- Existing CLI/output fields remain available; new diagnostic metadata is additive.
- Runtime SQLite state and credentials are not committed.

## Validation

Pre-merge validation for PR #54 passed the full repository quality gate before merge.

Post-merge CI run #387 and the corresponding CodeQL run for commit `43f4082369e0f2f0bd6614668ca99bff90818a1c` were still running when this report was refreshed. Their final conclusions and test count are intentionally not guessed.

Previously merged CI evidence already establishes successful execution of:

- Ruff lint;
- Ruff format;
- pytest;
- coverage reporting;
- package build;
- wheel installation;
- pip check;
- package import;
- dependency audit;
- CodeQL.

## Scientific validation boundary

A dedicated 2026-09-25 GitHub Actions validation run acquired all 150 canonical benchmark OIDs from the current ALeRCE detection backend.

Acquisition succeeded for all 150 objects, but strict frozen raw-cache validation detected mutable-source drift:

- frozen detection-row mean: 189.63333333333333
- live detection-row mean: 189.88666666666666
- frozen corrected_true count: 27379
- live corrected_true count: 27417

The strict frozen assertions remain strict. This is external-data drift, not evidence to weaken the benchmark contract.

Tracking issue: #51.

The following therefore remain `NOT VERIFIED` until the historical immutable raw snapshot is available:

- exact raw-cache reproduction;
- exact frozen raw-feature parity;
- offline feature-dataset reproduction from the historical raw snapshot;
- raw-artifact-backed production inference integration.

## Benchmark

The frozen v0.2 benchmark contains:

- 150 objects;
- 15 ALeRCE reference/weak-label classes;
- 10 objects per class;
- ZTF light curves;
- g/r observations where available;
- 42 frozen features.

This report does not claim a new benchmark score or population-level performance.

## Reproducibility

Canonical development environment:

- Python 3.11.16;
- Ubuntu 26.04 LTS;
- WSL2.

The repository contains the lockfile, checksum utilities, provenance manifests, compatibility tests, deterministic reports, and CI build/install verification.

A local clean-room run on the user's WSL2 environment is `NOT VERIFIED` because this connector cannot execute arbitrary commands in that environment.

## Known limitations

- The 150-object benchmark is not population-representative.
- ALeRCE labels are not independent astrophysical ground truth.
- OOD and temporal generalization require larger independent datasets.
- External-source licensing and attribution remain applicable.
- The historical raw cache needed for exact frozen reproduction is not committed to Git.

## Rollback

Rollback application changes by reverting the relevant merged commit(s). Do not rewrite or force-update the immutable `v0.2.0` tag.

For deployment rollback, pin the package to a previously validated commit and retain the production model identity `baseline_v0.2`.

## Reproduction commands

```bash
python -m ruff check src tests
python -m ruff format --check src tests
python -m pytest -q
python -m build
python -m pip install --force-reinstall dist/*.whl
python -m pip check
python -c "import ztf_classifier; print(ztf_classifier.__file__)"
ztf-classifier --help
```

For frozen scientific reproduction, use tag `v0.2.0` and the documented immutable benchmark/data contracts. Never rewrite that tag.

## Release posture

The package milestone is v0.4.0. Software release metadata and the scientific baseline are intentionally separate.

The release workflow is tag-driven. A release must preserve the distinction between repository/CI validation and the data-dependent scientific validations listed above.

## Acceptance rule

CI success is sufficient for repository/software acceptance gates but is not sufficient to claim exact historical raw-data reproduction. The explicit `NOT VERIFIED` scientific boundary must remain visible until the required immutable raw snapshot is available and validated.
