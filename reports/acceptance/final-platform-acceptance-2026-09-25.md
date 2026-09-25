# Final Platform Acceptance Evidence

Date: 2026-09-25
Audited main commit: ce36c5ddd2f86776b3d0b2abdda5b5f93efeb4b4
Software version: 0.4.0
Scientific baseline: v0.2.0
Production model: baseline_v0.2

## Purpose

This record separates executable engineering evidence from data-dependent scientific evidence. It is not a substitute for the mandatory scientific-validation gate.

## Current engineering evidence

- Main contains the integrated API, source-backed object analysis, durable jobs/results, catalog/reporting, incremental checkpoints, unified Scientific Feature Engine, Workbench, artifact provenance, and CI/security hardening layers.
- The latest main CI run (#403) reached 444 passed, 4 skipped, 1 failed. The sole failure is a test-contract mismatch in `tests/test_model_artifact_io_diagnostics.py::test_diagnostic_artifact_rejects_path_escape`: the loader emits the more specific message `Artifact ood_model path escapes artifact directory.` while the test expected the generic phrase. This is being corrected without weakening the path-containment check.
- Lint, format, build/package verification, and dependency audit passed on that run; the CI gate failed only because the test job failed.
- CodeQL remains part of the repository security gate.

## Acceptance matrix

| Area | Status | Evidence / limitation |
|---|---|---|
| v0.2.0 scientific baseline | VERIFIED | Immutable baseline retained. |
| Frozen 42-feature schema | VERIFIED | Contract and parity tests remain present. |
| Source-backed object analysis | VERIFIED | API/application contract tests are present and CI-covered. |
| Durable jobs/results/checkpoints | VERIFIED | Lifecycle, idempotency, lease, and monotonicity tests are present. |
| Versioned API + Workbench | VERIFIED | API and Workbench contract tests are present. |
| Catalog/reporting | VERIFIED | Deterministic bounded query/export/report paths are implemented. |
| Scientific Feature Engine | VERIFIED | Backend registration, selection, schema and provenance contracts are implemented. |
| Artifact schema 1.0/1.1 | VERIFIED | Compatibility and diagnostic separation tests are present. |
| CI/package/security hardening | BLOCKED | Current main has the single deterministic test failure described above. |
| Historical raw-cache reproduction | NOT VERIFIED | Immutable historical raw cache is unavailable; current ALeRCE data has drifted. |
| Exact frozen feature reproduction from raw cache | NOT VERIFIED | Depends on the unavailable historical raw snapshot. |
| Offline raw-feature reproduction | NOT VERIFIED | Depends on the unavailable historical raw snapshot. |
| Clean-room local WSL2 execution | NOT VERIFIED | Repository connector cannot execute arbitrary commands in the user's local WSL2 environment. |

## External scientific validation

On 2026-09-25, a dedicated validation run acquired all 150 canonical benchmark OIDs from the current ALeRCE backend. Acquisition succeeded, but strict comparison against the frozen historical raw-cache contract failed because the live service has drifted:

- detection-row mean: frozen `189.63333333333333`; live `189.88666666666666`;
- corrected-true count: frozen `27379`; live `27417`.

Other observed structural checks remained consistent, including the 150 canonical objects, no missing canonical OIDs, schemas, ordering, and FID distributions.

This is recorded as external-source drift, not as a software validation pass. The strict frozen assertions remain strict. Tracking issue: #51.

## Release posture

- Published `v0.2.0`, `v0.3.0`, and `v0.4.0` release milestones remain unchanged.
- `v0.2.0` remains the immutable scientific baseline.
- The next release/acceptance milestone must not be declared scientifically complete until the engineering CI gate is green and the mandatory external-data validation evidence is satisfied or formally dispositioned with the required immutable evidence.
