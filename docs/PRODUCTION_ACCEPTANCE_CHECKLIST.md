# Production Acceptance Checklist

Current evidence: `reports/acceptance/final-platform-acceptance-2026-09-25.md` (audited against current `main`)

This checklist is the final gate for the Astronomical Data Analysis & Discovery Platform layer.

## Scientific integrity

- [x] v0.2.0 tag remains immutable.
- [x] Current `main` scientific-validation gate is documented and release-blocking.
- [x] Native v0.2 feature schema remains 42 features and deterministic.
- [x] Source-backed analysis never fabricates observations.
- [x] Scientific results retain object, survey, model, schema, provenance, and creation metadata.
- [x] Reports and catalog exports are derived read-only views.

## Persistence

- [x] Job lifecycle is durable and lease-aware.
- [x] Scientific results are idempotent per job.
- [x] Conflicting retries are rejected.
- [x] Incremental checkpoints cannot move backwards.
- [x] Runtime databases are external to source control.

## API

- [x] OpenAPI exposes versioned contracts.
- [x] Stable error codes do not leak internal exception details.
- [x] Request IDs are generated or propagated.
- [x] Optional bearer authentication protects versioned endpoints when configured.
- [x] Catalog pagination and bounded exports are enforced.
- [x] Feature backend discovery and explicit backend selection are versioned.

## Workbench

- [x] Observations and durable results are API-backed.
- [x] No illustrative scientific values are presented as loaded results.
- [x] Catalog, jobs, report, and analysis views consume API contracts.
- [x] Report export is read-only and deterministic.
- [x] Theme changes do not alter scientific semantics.

## CI / packaging

- [x] Ruff lint passes.
- [x] Ruff format checks pass.
- [x] Full pytest suite passes on current `main` CI; four data-dependent modules remain explicitly skipped when their immutable raw inputs are unavailable.
- [x] Coverage is recorded.
- [x] Package build succeeds.
- [x] Built wheel installs and passes pip check.
- [x] Package import succeeds.
- [x] Dependency audit passes.
- [x] No runtime SQLite database or credential is committed.

## Scientific validation status

The engineering/platform gates are implemented and CI-covered. The independent scientific-validation gate is intentionally **NOT VERIFIED** until the pinned external benchmarks and immutable historical raw-data evidence are executed. See `docs/SCIENTIFIC_VALIDATION_BENCHMARK.md` and issue #51.

## Release evidence

The release is accepted only after all engineering gates and the mandatory scientific-validation gate have executable evidence. CI success alone does not satisfy the scientific-validation gate. The release workflow enforces this boundary and must fail closed while any required scientific-validation item remains `NOT VERIFIED`.
