# Parallel Product Validation and Ecosystem Benchmark Plan

Status date: 2026-10-22
Status: PLAN RECORDED; execution evidence must be recorded separately.
Target product: Astronomical Data Analysis & Discovery Platform
Immutable software release: v1.0.1
Immutable scientific baseline: v0.2.0
Current CPVS exact-membership reconstruction: UNRESOLVED

## Purpose

Move product validation beyond a single historical paper or catalog. CPVS is one claim-specific reproduction investigation, not the definition of the product. The product must be evaluated against independent datasets, independent scientific methods, varied input schemas, and reproducible known-answer tests.

This plan authorizes safe investigation and documentation, not production releases, destructive actions, baseline changes, or relaxation of scientific acceptance criteria.

## Parallel workstreams

### W1 — Core architecture and generality audit
- Inspect the actual public APIs, CLI, data ingestion, schema/feature contracts, analysis modes, result contracts, provenance, and error handling.
- Identify CPVS-specific assumptions that have leaked into general-purpose code.
- Distinguish implemented capability from planned capability and documentation claims.
- Produce file-and-test-level findings with severity, evidence, remediation, and regression-test proposal.

### W2 — Independent dataset and 50-case evaluation
- Select at least one public astronomical dataset that is independent of the CPVS reconstruction.
- Record publisher, DOI/URL, version, retrieval timestamp, license/access constraints, file hashes, schema, identifiers, labels/reference semantics, and preprocessing.
- Define a deterministic, seed-fixed 50-object sample from the full eligible population. Record the sampling algorithm and sample manifest; stratify where labels and population composition make that meaningful.
- Run the product's currently supported workflows without silently adapting the dataset to fit unsupported assumptions.
- Separately evaluate 50 schema/quality cases (valid variants, optional/additional columns, missing values, malformed values, duplicates, empty input, unsupported units/schema, and explicit rejection paths) where feasible.
- Compare numerical outputs to independent known-answer calculations or reference implementations. A successful process exit is not evidence of scientific correctness.
- Do not call 50 cases a population-level performance estimate. Treat it as a diagnostic smoke/regression sample unless a powered statistical design justifies stronger claims.

### W3 — Independent paper/method replication
- Select a second paper/method whose data and selection semantics are independent of the CPVS membership discrepancy.
- Extract the paper's dataset definition, preprocessing, features, exclusions, reference labels, split strategy, metrics, uncertainty treatment, and known limitations.
- Map each requirement to existing code, missing capability, or unsupported input.
- Reproduce only claims for which source data and evaluation protocol are sufficiently available; document irreproducible claims and ambiguities.
- Do not treat a paper's labels as independent ground truth unless the evidence warrants it.

### W4 — CPVS historical reconstruction
- Continue the explicit-Seq/object-name provenance and membership investigation under Issue #170 and its current pull request.
- Preserve the 11,602 candidate-only discrepancy as unresolved until an independently supported selection rule or root cause is established.
- Do not change global input rules, thresholds, feature schemas, or scientific gates merely to match the published count.
- Report historical reproduction separately from product-level validation.

### W5 — GitHub ecosystem and competitor audit
- Search GitHub systematically across ZTF classifiers, light-curve/time-series analysis, astronomical anomaly discovery, survey pipelines, catalog/cross-match, scientific workbenches, uncertainty/OOD, reproducibility, and desktop packaging.
- Record repository URL, license, maintenance/activity, relevant modules/tests/docs, demonstrated capabilities, evidence strength, and applicability to this project.
- Compare implementation evidence rather than stars or README promises alone.
- Create a traceable gap matrix: finding → evidence → project gap → proposed change → cost/risk → acceptance test.
- Never copy code or assets without checking license and attribution obligations. Avoid adding dependencies unless justified.

## Shared protocol and isolation rules

1. Start from a recorded commit and immutable baseline; every experiment records commit SHA, environment, commands, data version/hash, configuration, and outputs.
2. Workstreams may run in parallel but must use separate branches/work directories and avoid concurrent writes to the same file.
3. Use adapters and versioned contracts for dataset-specific differences. Never impose CPVS-specific filters on all datasets.
4. Preserve the frozen v0.2.0 42-feature schema, class order, model artifact, and acceptance rules unless a separately reviewed and validated change explicitly authorizes a new version.
5. Keep OOD, scientific anomaly evidence, classification uncertainty, calibration, conformal predictions, catalog evidence, and explainability semantically separate.
6. External datasets stay out of Git. Commit manifests, hashes, small synthetic fixtures, tests, and reports; respect source licenses and access terms.
7. Record facts, verified findings, supported inferences, hypotheses, and unresolved questions separately.
8. Missing evidence, skipped required tests, or unexecuted validation is NOT PASS.
9. A passing unit/CI suite demonstrates only the contracts it executes; it does not prove astrophysical validity or generality.
10. No release publication, production-data mutation, destructive cleanup, or costly infrastructure action is authorized by this plan.

## Required deliverables

- Validation manifests and machine-readable results in the repository's established evidence location, without committing external source data.
- A dataset-independent evaluation report with known-answer comparisons and explicit scope limitations.
- A 50-case deterministic sample manifest and per-case result/failure ledger.
- A second-paper protocol and reproduction report.
- A repository ecosystem inventory and prioritized gap matrix with license review.
- Core architecture audit with code paths and regression-test proposals.
- Updated handbook, product roadmap, scientific-validation roadmap, README, architectural decisions, and cumulative lifecycle/failure-prevention record.
- Follow-up issues/PRs for confirmed findings, each with acceptance criteria and regression coverage.

## Acceptance criteria

- Every selected dataset and sample is versioned, hash-verified where feasible, and traceable to source identifiers.
- At least one supported analysis is checked against an independent known-answer reference.
- Unsupported inputs fail clearly and do not yield silently misleading scientific outputs.
- CPVS-specific behavior is isolated from generic ingestion and analysis contracts.
- All 50 selected cases have recorded status and failure reason where applicable; no failures are dropped from the report.
- Paper replication claims cite their source protocol and clearly distinguish reproduction, partial reproduction, and non-reproduction.
- Ecosystem recommendations link to inspected source files/tests/docs and include compatibility/license review.
- Required tests execute; skipped or missing required evidence cannot be represented as a pass.
- No frozen baseline or scientific acceptance criteria are silently changed.

## Initial execution order

1. Record current repository commit and inspect canonical code/docs/workflow status.
2. Run W1, W3, W4, and W5 investigations in parallel; W2 starts as soon as a suitable independent dataset and supported input path are confirmed.
3. Produce a read-only gap report before changing core code.
4. Fix only evidence-backed defects, in isolated branches, with regression tests.
5. Re-run affected tests and the independent dataset sample after each accepted change.
6. Review and merge only after CI and scientific acceptance criteria are satisfied. This document does not itself authorize merging.

## Status ledger — 2026-10-22

- Decision: parallel workstreams adopted to reduce elapsed time while preserving isolation.
- Verified repository context: README defines the product as an Astronomical Data Analysis & Discovery Platform; canonical docs include docs/HANDBOOK_UPDATED_v2.8.md, docs/roadmap/PLATFORM_EXPANSION_ROADMAP.md, docs/roadmap/SCIENTIFIC_VALIDATION_ROADMAP.md, docs/ECOSYSTEM_REVIEW_PRODUCT_EXPANSION_2026-10-08.md, and docs/architecture/V1_PRODUCT_ARCHITECTURE.md.
- Current CPVS discrepancy: remains unresolved; do not infer resolution from successful CI or exact intersection alone.
- Dataset choice, paper choice, complete repository inventory, and independent 50-case results: NOT YET VERIFIED.
- No code behavior, frozen baseline, or release was changed by this plan.


## Initial architecture evidence snapshot — 2026-10-22
The initial repository sample and gap matrix are documented in [ECOSYSTEM_GAP_AUDIT_INITIAL_2026-10-22.md](../ECOSYSTEM_GAP_AUDIT_INITIAL_2026-10-22.md). It records only the repositories and files actually inspected and explicitly lists remaining search/inspection gaps.


Read-only inspection of the current main-branch source shows a useful boundary but also a concrete generality gap:

- `src/ztf_classifier/application/ingestion.py` imports local CSV/Parquet tables, checks file size, non-empty content, unique column names, optional required columns, and records SHA-256/source metadata. This establishes generic tabular ingestion, not universal scientific interpretation.
- `src/ztf_classifier/features/engine.py` defaults to `NativeV0_2Backend`, which calls `extract_v0_2_features` and `validate_v0_2_feature_vector`; this intentionally preserves the frozen 42-feature contract.
- `src/ztf_classifier/jobs/executor.py` acquires observations through `ObservationService`, computes a registered feature backend, and predicts using a registered production model. The current end-to-end object-analysis path is therefore not a generic arbitrary-dataset analysis engine.
- `docs/api/API_V1.md` says the production model currently requires its frozen feature schema.

Supported conclusion: local tabular files can be imported generically, while the existing native feature/model path remains schema-specific. Whether every other module preserves this boundary still requires the planned full code audit and independent dataset test. Do not claim arbitrary-feature analysis is already implemented; treat it as a product capability gap to map and prioritize.


## StarEmbed end-to-end execution gap — 2026-10-23

A follow-up read-only audit of `configs/benchmarks/star_embed_ztf_40k.json`, `src/ztf_classifier/validation/adapters.py`, `src/ztf_classifier/validation/acquisition.py`, `src/ztf_classifier/validation/runner.py`, `src/ztf_classifier/validation/__main__.py`, and `.github/workflows/scientific-validation.yml` found that the existing adapter can acquire the five Parquet source artifacts and resolve/record a Hugging Face revision, but the benchmark runner evaluates an already-prepared prediction table. The runner requires `sourceid`, `class_str`, and `y_pred`; it does not generate predictions from raw StarEmbed light curves. The current heavy workflow acquires StarEmbed and then proceeds into large CPVS g/r archive acquisition/derivation; no StarEmbed raw-light-curve-to-model prediction step was found in the inspected workflow.

Therefore the independent-dataset end-to-end evaluation is **BLOCKED pending an explicit prediction-generation path**. Before running it, inspect actual StarEmbed Parquet schema, units, arrays, split semantics, and preprocessing; define a versioned adapter/feature mapping or separately compatible model; preserve train/validation/test and OOD split boundaries; generate a provenance-backed prediction table; and then run the benchmark evaluator. Do not force the frozen v0.2 42-feature model onto incompatible raw inputs or train on the held-out test sample. A targeted StarEmbed workflow should be separated from large CPVS downloads to avoid unnecessary transfer/runtime. No heavy run was started in this audit.


## Raw StarEmbed schema audit implementation — 2026-10-23

A first executable diagnostic has now been added at `src/ztf_classifier/validation/star_embed_audit.py`, with focused tests in `tests/test_star_embed_audit.py`. Run it after acquiring the five pinned Parquet artifacts:

```bash
python -m ztf_classifier.validation.star_embed_audit \
  --data-dir reports/scientific_validation/ztf_star_embed \
  --output reports/scientific_validation/ztf_star_embed/schema_audit.json \
  --sample-size 50 --seed 20261023
```

The report records each artifact's SHA-256, byte size, row count and columns; split-level counts, duplicate IDs, class counts, invalid period/coordinates; pairwise ID overlap; in-distribution/OOD class overlap; per-band array consistency findings; and a deterministic sample of IDs from the held-out test split. It fails closed if any required source artifact or top-level schema column is missing. It does **not** train, infer, score classification accuracy, or establish astrophysical validity.

**Verified real-data result (CI run 39921499634, 2026-10-23):** all CI jobs passed, and the StarEmbed acquisition/audit steps ran. The uploaded audit artifact records 29,047 train rows (29,046 unique IDs), 4,150 validation rows, 8,301 test rows, and 1,087 anomaly rows. It found a cross-split train/test SourceID overlap `CSS_J051729.2+083846` and one duplicate within train `CSS_J164349.2+401208`. The original audit incorrectly returned `PASS_SCHEMA_AUDIT_WITH_FINDINGS` despite these leakage findings; therefore the result is **not accepted as a clean audit**. A fail-closed regression and row-level provenance report are now committed: duplicate IDs within a split or across split boundaries produce `BLOCKED`, and issue details include the source artifact, class, period, and coordinates. The new CI run must verify this correction. This finding does not establish classifier performance or physical-label validity.

The public StarEmbed dataset card describes top-level columns `sourceid`, `bands_data`, `period`, `class_str`, `ra`, and `dec`; nested per-band fields `target`, `past_feat_dynamic_real`, `feat_dynamic_real`, `mjd`, and `length`; and train/validation/test plus an `anom` OOD split. The audit implements these as observed source-contract checks, not assumptions that every object has every band.

**Current evidence boundary:** code and synthetic-fixture tests have been added to the draft PR branch; the real Parquet artifacts have not yet been acquired/audited in this step, and CI for the new head has not yet been observed. The independent inference/evaluation path remains blocked. Do not treat the presence of this audit tool as completion of the 50-object scientific evaluation.
