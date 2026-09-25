# Final Platform Acceptance Evidence

Date: 2026-09-25
Audited main commit: 0e3c3af6a78d2d63bd79dcef2851eed474757150
Software version: 0.4.0
Scientific baseline: v0.2.0
Production model: baseline_v0.2

## Purpose

This record separates executable engineering evidence from data-dependent scientific evidence. It is not a substitute for the mandatory scientific-validation gate.

## Current engineering evidence

- Main contains the integrated API, source-backed object analysis, durable jobs/results, catalog/reporting, incremental checkpoints, unified Scientific Feature Engine, Workbench, artifact provenance, and CI/security hardening layers.
- Post-merge main CI run #420 is green. It completed the full suite successfully with 444 passed and 4 skipped; lint, format, build/package verification, dependency audit, and the CI gate all passed.
- Post-merge CodeQL run #47 is green.
- The earlier path-escape test-contract failure on run #403 was fixed without weakening the artifact path-containment check.
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
| CI/package/security hardening | VERIFIED | Post-merge CI #420 and CodeQL #47 are green. |
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
