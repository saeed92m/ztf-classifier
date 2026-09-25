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

## Scientific Validation — permanent Product-Level Gate

- [x] Benchmark Registry exists under `configs/benchmarks/`.
- [x] Versioned manifest contract records source/version/DOI-or-authoritative-unassigned-state, retrieval date, IDs, hashes, schema, taxonomy, mapping, splits, leakage exclusions, preprocessing/input contract, and provenance.
- [x] Ground truth and independent reference predictions are explicitly separated.
- [x] ALeRCE is represented as an independent reference system, not ground truth.
- [x] Reproducible table benchmark runner produces JSON/Markdown evidence and hashes its input.
- [x] Regression comparison is executable and release-blocking.
- [x] Registry contract is exercised by GitHub Actions.
- [ ] All five source-backed benchmark adapters are implemented and executed with immutable evidence.
- [ ] All required leakage checks are PASS for the release candidate.
- [ ] Full scientific validation across ingestion -> normalization -> QC -> feature generation -> inference -> calibration/OOD -> provenance is PASS.
- [x] Scientific Validation Dashboard/Report is integrated into the Workbench via the versioned API and Workbench validation view.
- [ ] No unresolved benchmark regression remains.

The scientific gate remains **NOT VERIFIED** until the unchecked source-backed and leakage/evidence items above are completed. Engineering CI success alone cannot satisfy this gate.

## Definition of Done — Scientific Validation Gate

A product release is scientifically complete only when all applicable conditions below have executable evidence:

- every affected benchmark is identified by a versioned registry manifest;
- benchmark source/version/retrieval date/DOI-or-authoritative-unassigned-state, object IDs, hashes, schema, taxonomy, class mapping, split, leakage exclusions, preprocessing contract, input contract, and provenance are recorded;
- independent ground truth is kept distinct from classifier/reference agreement;
- all applicable leakage checks are PASS, with no unresolved NOT_EXECUTED release blockers;
- the complete scientific chain from ingestion through reproducible inference has been validated;
- classification, calibration, OOD, coverage/rejection, QC, determinism, schema, provenance, and failure-code metrics are reported where applicable;
- any benchmark regression has an explicit scientific disposition before release;
- benchmark evidence is reproducible from source-backed immutable inputs or explicitly documented external-source limitations;
- the Scientific Validation report/dashboard identifies population, version, results, regressions, scope limits, and known failure cases;
- the release workflow records an explicit Scientific Validation Gate result.

A benchmark passing is evidence for its declared scope, not proof of universal correctness.

## Cumulative Learning & Continuous Improvement — permanent product process gate

- [x] Cumulative-learning principle is documented as a lifecycle requirement.
- [x] Mandatory lifecycle includes Audit, Previous Knowledge Retrieval, Baseline, Implementation, Test, Measure, Validate, Root Cause, Knowledge Extraction, Knowledge Update, Regression Update, Baseline Comparison, and Accept/Revise.
- [x] Operational Knowledge Layer exists under `docs/knowledge/`.
- [x] Cumulative Improvement Ledger exists and is version-controlled.
- [x] Knowledge statuses are explicitly classified as FACT, VERIFIED, SUPPORTED, HYPOTHESIS, ASSUMPTION, UNRESOLVED, or REJECTED.
- [x] Executable lifecycle contract exists in `ztf_classifier.lifecycle`.
- [x] Lifecycle contract has regression tests.
- [x] Multi-objective quality vector is defined for relevant changes.
- [x] Performance baseline dimensions are defined and NOT_MEASURED is allowed when evidence is unavailable or not applicable.
- [x] Local optimization cannot override scientific validity, reproducibility, or release integrity.
- [x] Every meaningful pull request must carry a validated machine-readable cycle record under `configs/process/cycles/`.
- [x] CI validates all cycle records and includes the cumulative lifecycle gate in the merge gate.
- [ ] Every future product stage has a completed cumulative cycle record and measured evidence.
- [ ] Process-performance trends are measured over enough cycles to establish a meaningful baseline.

The cumulative-learning gate is complementary to the permanent Scientific Validation Product-Level Gate and cannot downgrade or bypass scientific blockers.
