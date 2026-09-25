# v0.4.0 Complete Upgrade Report

Date: 2026-09-25
Branch: chore/complete-upgrade-v0.4
Baseline commit: 0c615b09813e0f5a8e61a895d371789e3ab1e21f
Final validated commit before documentation closeout: 80557eac1c8964409d3c45772efc8d644a9dfea6

## Summary

The v0.4.0 upgrade specification has been implemented against the v0.3.0 production milestone.

The immutable scientific baseline v0.2.0, benchmark_v0.2 dataset contract, frozen 42-feature schema, baseline_v0.2 model identity, and artifact schemas 1.0/1.1 remain intact.

## Implemented areas

- software version 0.4.0;
- canonical requirements.lock from a verified CI-resolved Python 3.11.16 Ubuntu environment;
- streaming SHA-256 utility;
- artifact manifest hash and additive provenance metadata;
- legacy artifact checksum warning path;
- independent calibration/conformal/OOD diagnostics;
- strict ALeRCE ingestion validation and diagnostics;
- additive CLI and batch provenance/status fields;
- Data Card and Model Card;
- frozen feature provenance and temporal leakage contract;
- security guidance for joblib artifacts;
- hardened CI and package validation.

## Files added

- requirements.lock
- src/ztf_classifier/reproducibility/checksums.py
- tests/test_checksums.py
- tests/test_alerce_ingestion_diagnostics.py
- tests/test_prediction_result_statuses.py
- docs/DATA_CARD.md
- docs/MODEL_CARD.md
- docs/FEATURE_PROVENANCE_CONTRACT.md
- reports/upgrade/baseline_test_status.md

## Important modified components

- pyproject.toml — package milestone/tooling
- .github/workflows/ci.yml — locked install, lint, scoped format gate, coverage, build, wheel validation, audit
- src/ztf_classifier/models/artifact_io.py — checksum/integrity/provenance hardening
- src/ztf_classifier/models/provenance.py — software provenance
- src/ztf_classifier/models/results.py — explicit diagnostic status metadata
- src/ztf_classifier/models/result_builder.py — metadata propagation
- src/ztf_classifier/models/production_inference.py — independent diagnostics and provenance
- src/ztf_classifier/application/batch.py — batch provenance/status propagation
- src/ztf_classifier/cli/main.py — additive output metadata
- src/ztf_classifier/io/alerce.py — validation and ingestion diagnostics
- README.md, CHANGELOG.md, Handbook — documentation/continuity

## Validation

Final PR CI run #138 passed on commit 80557eac1c8964409d3c45772efc8d644a9dfea6.

- Ruff lint: PASS
- scoped Ruff format check: PASS
- pytest: PASS — 364 passed, 4 skipped, 6 warnings
- coverage reporting: PASS — 83% total
- package build: PASS
- wheel install: PASS
- pip check: PASS
- package import: PASS
- pip-audit: PASS with no known third-party vulnerabilities reported

pip-audit reports the local ztf-classifier package as not published on PyPI, so the project itself cannot be audited by that service. This is a tooling limitation, not a vulnerability finding.

## Baseline verification limitation

The repository connector cannot execute arbitrary commands in the user's WSL2 working tree. Therefore the requested pre-change local baseline commands are explicitly marked NOT VERIFIED in reports/upgrade/baseline_test_status.md. No local result is fabricated.

CI is the executable validation authority for this branch.

## Compatibility

- v0.2.0 scientific baseline: preserved
- benchmark_v0.2: preserved
- 42-feature frozen schema: preserved
- baseline_v0.2 model: preserved
- artifact schema 1.0: preserved
- artifact schema 1.1: preserved
- CLI contract: additive changes only

## Known limitations

- The benchmark remains 150 objects / 15 classes and is not population-representative.
- ALeRCE labels remain reference/weak labels.
- Real-world OOD and temporal generalization require independent larger-scale validation.
- External data licensing/ToS must be enforced before publication or commercial redistribution.
- The canonical lock is Linux/Python-3.11 oriented because it was captured from the verified Ubuntu CI environment.

## Rollback

Rollback is safe at the Git level by reverting the v0.4.0 upgrade commits or retaining the v0.3.0 main baseline. The immutable v0.2.0 scientific tag is not modified.

## Reproduction

Use Python 3.11.16 and install the committed requirements.lock, then install the project with --no-deps. Run pip check, Ruff, pytest, build, wheel installation, import verification, and pip-audit as defined by .github/workflows/ci.yml.

## NOT VERIFIED

The following remain explicitly unverified through this connector:
- the user's local WSL2 working-tree status immediately before the upgrade;
- local pyenv/.venv package state outside CI;
- local clean-room reproduction on the user's machine.

No other validation item above is marked NOT VERIFIED because it was executed successfully by GitHub Actions.
