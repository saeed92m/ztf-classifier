# Production Acceptance Checklist

Current evidence: `reports/acceptance/final-platform-acceptance-2026-09-25.md`

This checklist is the final gate for the Astronomical Data Analysis & Discovery Platform layer.

## Scientific integrity

- [ ] v0.2.0 tag remains immutable.
- [ ] Native v0.2 feature schema remains 42 features and deterministic.
- [ ] Source-backed analysis never fabricates observations.
- [ ] Scientific results retain object, survey, model, schema, provenance, and creation metadata.
- [ ] Reports and catalog exports are derived read-only views.

## Scientific validation

- [ ] Independent labeled benchmark manifest is pinned.
- [ ] Ground-truth provenance and label taxonomy are documented.
- [ ] Object-level train/test leakage checks pass.
- [ ] External benchmark execution succeeds.
- [ ] Per-class classification metrics and confusion matrix are recorded.
- [ ] Calibration/probabilistic diagnostics are recorded where applicable.
- [ ] OOD and explicit failure-case validation are recorded.
- [ ] Independent classifier outputs are separated from ground truth.
- [ ] ZTF source-backed reproduction is pinned to a documented release/subset.
- [ ] Benchmark results are reproducible from the recorded manifest.
- [ ] Scientific regressions are resolved or explicitly dispositioned before release.

## Persistence

- [ ] Job lifecycle is durable and lease-aware.
- [ ] Scientific results are idempotent per job.
- [ ] Conflicting retries are rejected.
- [ ] Incremental checkpoints cannot move backwards.
- [ ] Runtime databases are external to source control.

## API

- [ ] OpenAPI exposes versioned contracts.
- [ ] Stable error codes do not leak internal exception details.
- [ ] Request IDs are generated or propagated.
- [ ] Optional bearer authentication protects versioned endpoints when configured.
- [ ] Catalog pagination and bounded exports are enforced.
- [ ] Feature backend discovery and explicit backend selection are versioned.

## Workbench

- [ ] Observations and durable results are API-backed.
- [ ] No illustrative scientific values are presented as loaded results.
- [ ] Catalog, jobs, report, and analysis views consume API contracts.
- [ ] Report export is read-only and deterministic.
- [ ] Theme changes do not alter scientific semantics.

## CI / packaging

- [x] Ruff lint passes.
- [x] Ruff format checks pass.
- [x] Full pytest suite passes (437 passed; 4 data-dependent modules skipped).
- [x] Coverage is recorded.
- [x] Package build succeeds.
- [x] Built wheel installs and passes pip check.
- [x] Package import succeeds.
- [x] Dependency audit passes.
- [x] No runtime SQLite database or credential is committed.

## Release evidence

The release is accepted only after all gates above have executable evidence in the final merged main commit.
