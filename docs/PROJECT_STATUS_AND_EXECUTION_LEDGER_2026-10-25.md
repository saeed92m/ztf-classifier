# Project Status & Execution Ledger — 2026-10-26 (updated)

## Purpose

This document is the dated, evidence-conscious coordination point for the ZTF Classifier project. It does not replace the immutable v0.2.0 scientific baseline, release notes, source manifests, or issue-level evidence. It distinguishes verified repository state from unresolved science and planned work.

## Verified repository state at review time

- Default branch: `main`, at `d88e54a2eb70d5e4531bc950341ef3136c29a5e2`.
- Current immutable software release documented by the repository: `v1.0.1`.
- Frozen scientific baseline: `v0.2.0`; production model: `baseline_v0.2`; preserve the 42-feature `final_feature_set_v0.2`, frozen class order, historical cutoff `59447.224132`, diagnostics schema 1.1, and fail-closed scientific gate.
- Security PR [#223](https://github.com/saeed92m/ztf-classifier/pull/223) merged on 2026-10-26 as `8c2ba057a572b1cd460c47d1e02940e1ba44e366`. The merge refreshed dependency pins; dependent PRs still require current-head CI and dependency-audit verification.
- CPVS report PR [#224](https://github.com/saeed92m/ztf-classifier/pull/224) remains open and draft. Its implementation/tests are not equivalent to a generated, source-backed 11,602-row deliverable; verify current-head checks and independently audit the actual outputs before merge.
- [Issue #170](https://github.com/saeed92m/ztf-classifier/issues/170) remains the scientific membership-reconstruction blocker.
- [Issue #222](https://github.com/saeed92m/ztf-classifier/issues/222) defines a bounded operational behavior test on 100 random object-level inputs; it is not an independent scientific benchmark.

## CPVS discrepancy: what is and is not established

The currently recorded full-set result is:

| Population | Recorded count |
|---|---:|
| CPVS Table 2 parent rows / source objects | 781,602 |
| Published Table 4 reference IDs | 730,184 |
| Seq-based reconstructed candidates | 741,786 |
| Shared IDs | 730,184 |
| Candidate-only IDs | 11,602 |
| Published-only IDs | 0 |

The recorded diagnostic partition of candidate-only IDs is 11,580 failing at least one condition in both the parent mean-magnitude pair and per-band-period pair; 17 with positive mean magnitudes but a missing/nonpositive period; and 5 with both periods but missing/nonpositive `gmag`. The four-field predicate (`gmag > 0`, `rmag > 0`, `Per-g > 0`, `Per-r > 0`) has been recorded as matching Table 4 membership exactly for the source-backed diagnostic artifacts.

**Interpretation boundary:** this establishes a reproducible diagnostic set relation for the recorded artifacts; it does not prove that the four-field predicate is the publisher's historical selection rule, nor that any candidate-only object is a new discovery. Keep Issue #170 open until the source versions, exact publisher semantics, provenance, and independent evidence are resolved. Re-verify artifact hashes, row/object counts, and command provenance before reusing these counts in a release or public scientific claim.

## Workstreams and acceptance criteria

### A. CPVS discrepancy report

1. Re-fetch and freeze the authoritative parent metadata, published Table 4 membership, and Seq-based candidate IDs; record source URLs, retrieval timestamps, row counts, schema, and SHA-256.
2. Run the report builder from PR #224 against those exact inputs. Confirm the CSV has exactly 11,602 unique candidate-only object IDs, every ID maps to an authoritative parent record, and the manifest hashes match the generated files.
3. Review every diagnostic reason; missing and invalid values must remain explicit, never imputed silently.
4. Generate HTML/CSV/Markdown/JSON outputs and verify internal count consistency and deterministic rebuild behavior.
5. Keep raw-light-curve review and external catalog cross-match as `NOT_ASSESSED` until their evidence is actually present.
6. Do not close Issue #170 merely because the report is generated.

### B. 100-random-object operational behavior test

This is a bounded test of how the current program behaves on 100 random object-level inputs, not an independent scientific benchmark and not an accuracy claim.

- Select exactly 100 object-level IDs from a defined parent population using a fixed recorded random seed; record the selection frame, source version, selection command, software revision, configuration, and input hashes.
- Account for all selected objects, including ingestion failures and exclusions; never silently replace difficult cases.
- Per object, record input/schema validation, QC and feature-generation status, inference/analysis completion or failure, output/uncertainty/abstention fields where supported, warnings, errors, and runtime/resource observations if available.
- Evaluate operational behavior: input handling, robustness, reproducibility, traceable outputs, and clarity of failure states. Do not tune model parameters or frozen artifacts using this sample.
- Do not infer accuracy, calibration, novelty, representativeness of all ZTF objects, or independent scientific validity from this test alone.
- Keep this test separate from the frozen 150-object/15-class ALeRCE v0.2 benchmark and CPVS membership reconstruction. ALeRCE labels remain benchmark labels, not independent ground truth.

### C. New ZTF inputs and identity/provenance tests

- Test at least one source-backed ZTF input outside the CPVS reconstruction, using documented object IDs and immutable input hashes.
- Verify the pipeline preserves authoritative source identifiers (including non-contiguous Seq values where applicable), does not substitute row ordinals, handles duplicates/missing values deterministically, and produces stable object-level outputs on rebuild.
- Distinguish a catalog-membership discrepancy from ML classification error and from a genuinely new/previously uncatalogued object.
- Do not extrapolate the CPVS discrepancy rate to unrelated ZTF datasets without measured evidence.

### D. Cross-platform experimental distribution

- Target operating systems: Windows, Ubuntu Linux, and macOS; target remains CPU-first.
- Repository metadata currently declares Python `>=3.11,<3.12`. Do not claim broader Python-version support without updating dependencies and passing the full supported matrix.
- Build a clean-machine matrix covering install, import, CLI/API startup, representative data ingestion, inference, export, and uninstall/reinstall. Record OS version, Python version, dependency lock, architecture, commands, and results.
- Produce platform-specific install instructions and artifacts only for environments actually tested. A source package or Linux CI pass alone does not establish a Windows/macOS installer.
- Preserve the core scientific engine and CLI/API independently of GUI; optional GUI must not fork scientific logic or mutate the frozen baseline.

### E. GUI / UI / UX

- Audit existing API and Workbench routes before building a second interface. The repository documents a FastAPI API and a `/workbench/` view; that is existing UI surface, not proof of a polished desktop GUI.
- Prioritize user journeys: select/import source data; validate schema/provenance; run analysis; inspect classification, confidence/uncertainty/OOD and abstention; inspect light curves/features; browse discrepancies; export a traceable report.
- Provide clear states for missing data, failed analysis, unsupported inputs, and unassessed scientific evidence.
- Add end-to-end UI tests and accessibility/usability checks before describing the GUI as ready for general users.

### F. Company-Platform integration

- Keep ZTF Classifier independently installable and usable. Company-Platform integration is an optional future integration, not a runtime dependency.
- Define a versioned API/export contract, authentication and least-privilege rules, job/result identifiers, provenance fields, error handling, and data-retention boundaries before connecting systems.
- Do not write production database rows or change database schemas until a concrete, versioned integration requirement and migration/test plan exist.

### G. Security, lifecycle and documentation

- PR #223 is merged. Re-check dependent PRs' current CI and dependency audits; do not bypass the audit.
- Re-run PR #224 against the current main base after the dependency refresh and independently verify its generated outputs; do not merge automatically.
- Update README, handbook, roadmap, issue records, and release notes from verified evidence. Do not report workflow success as scientific validation when scientific jobs are skipped.
- Preserve raw scientific data outside Git unless explicitly approved and licensed. Store manifests and small provenance metadata, not large catalogs or credentials.
- Treat GitHub wiki and repository description updates separately from source-doc updates; do not claim they changed unless a write is verified.

## Current blockers

1. Exact historical CPVS selection semantics are not independently proven; Issue #170 remains open.
2. The actual 11,602-row report has not yet been verified as generated from the source-backed artifacts by the current report PR.
3. Raw light-curve inspection and a full external-catalog cross-match have not been established for all 11,602 objects.
4. The 100-random-object operational test has not yet been run and audited; no results are claimed.
5. Windows/macOS clean-machine packaging and a user-ready GUI have not been verified by this review.
6. PR #223 is merged; PR #224 remains open/draft pending current-head CI and source-backed output validation.

## Next execution sequence

1. Verify current branch/PR/workflow state and security audit.
2. Use authoritative source-backed artifacts to generate and audit the CPVS report.
3. Re-run CPVS reporting CI on a base that contains the reviewed dependency remediation.
4. Execute the 100-random-object operational test with a fixed seed, complete per-object accounting, and a reproducible manifest.
5. Implement and test cross-platform packaging and GUI incrementally.
6. Define Company-Platform API integration after the independent product workflows are stable.

No scientific blocker is considered resolved solely by this document.


## Additional artifact inventory — 2026-10-25

GitHub Actions exposes the source-backed diagnostic run [#38635891449](https://github.com/saeed92m/ztf-classifier/actions/runs/38635891449) (branch `ci/heavy/cpvs-parent-metadata-diagnostic-20261012`, commit `d9c6ac40a17cdce7e0b6a65d12e471a3a1dbb175`). Its artifact listing includes:

- `scientific-validation-heavy`, artifact ID `11935357767`, reported size 34,104,786 bytes, GitHub-reported digest `sha256:346cd0a22d1490c9d3c5f6ff290ca2377e1c5458895c0c0d4b616b0708630c36`, expires 2027-01-12.
- `frozen-reference-evidence-ztf_periodic_730k_published`, artifact ID `11929663226`, 439 bytes, digest `sha256:921a7b82881bf0b12827b4036699cf4fb19d56d2818988ccb6f1aa0540e9027c`.
- `scientific-validation-external-source-evidence`, artifact ID `11929070312`, 18,998 bytes, digest `sha256:b89d3f3ea513ecfc5513fb06dc0723ebb4e5f7ee517239cf5f54bb64565aa359`.
- `frozen-reference-evidence-alerce_reference_frozen_20200609`, artifact ID `11928138398`, 487 bytes, digest `sha256:cf69a4da28a20451016f42d555f42d9f3675ec95cd1500392163c384d4d70a6f`.
- `scientific-validation-provenance`, artifact ID `11927184945`, 1,016 bytes, digest `sha256:248f14c9872085aceaa1ecb313c0c7e4e5d3be2dd6e8319b9aafecea09700d94`.

These are artifact-service metadata, not a completed local content audit. The ZIP was fetched into the working file service, but the available execution environment returned errors when attempting to inspect/extract its bytes. Therefore its internal members, source file hashes, and the 11,602-row report have **not** been verified in this turn. Retrieve/materialize the artifact in a functioning local runtime, inspect its manifest and member list, validate archive integrity, and reproduce the report before relying on its contents. Do not let the artifact expire before preserving the necessary provenance evidence.


## Product data-input boundary — clarified 2026-10-25

The standard application distribution does not include a large astronomical data archive for the user. Users select and supply the astronomical data they need. Product work should therefore prioritize supported input formats, schema/quality validation, clear rejection/error messages, provenance and hashes, local processing/privacy defaults, and explicit consent before any upload or disclosure. Small synthetic fixtures or separately licensed test samples may be used in development/CI but are not a bundled scientific dataset or a promise of data delivery.

## CPVS parallel resolution experiment — recorded 2026-10-25

Two independent tracks will be evaluated side by side. Neither track is accepted in advance, and neither may change the immutable v0.2.0 scientific baseline or v1.0.1 release artifacts.

- **Track A — source-backed reconstruction / Jupyter processing:** branch `experiment/cpvs-jupyter-reconstruction-20261025`. Audit the actual notebook/code, source versions and hashes, Table2 `Seq` versus light-curve SourceID mapping, object-level versus row-level grain, joins, filter order, duplicate policy, and missing/non-finite values. Reproduce the current set from identified inputs before testing the four-field diagnostic condition (`gmag > 0`, `rmag > 0`, `Per-g > 0`, `Per-r > 0`) as a hypothesis, not an assumed publisher rule. Record every included/excluded ID and reason, exact set differences, commands/environment, hashes, and deterministic rerun results.
- **Track B — discrepancy reporting:** implementation branch `feature/cpvs-discrepancy-report-20261024`, PR [#224](https://github.com/saeed92m/ztf-classifier/pull/224). Run the report builder against authoritative, hash-identified source artifacts; verify candidate-only IDs, parent provenance, counts across CSV/HTML/Markdown/JSON, deterministic output hashes, and explicit `NOT_ASSESSED` labels for checks not performed. This track makes discrepancies auditable; it does not itself prove the historical rule or eliminate the underlying discrepancy.
- **Shared comparison criteria:** identifier/source integrity; deterministic reproducibility; false inclusion/exclusion against an explicitly defined reference; missing/invalid-value behavior; traceability; and tests on additional independent, source-backed astronomical inputs outside CPVS. A matching count alone is insufficient. Do not choose conditions solely to force 730,184 IDs.
- **Decision rule:** choose a production method only after evidence and regression tests support its scientific meaning and robustness. If the publisher's historical rule cannot be established, retain the uncertainty explicitly and keep discrepancy reporting as a product capability. The exact-reproduction blocker in [Issue #170](https://github.com/saeed92m/ztf-classifier/issues/170) remains open until its evidence criteria are met. The 100-object operational behavior test in [Issue #222](https://github.com/saeed92m/ztf-classifier/issues/222) is separate and does not establish scientific accuracy.
- **Execution state as of 2026-10-25:** experiment branch and plan were recorded; no winner or scientific resolution was claimed.

## Execution update — 2026-10-26

- PR [#223](https://github.com/saeed92m/ztf-classifier/pull/223) was merged as commit `8c2ba057a572b1cd460c47d1e02940e1ba44e366`, refreshing vulnerable dependency pins on `main`.
- A retained-artifact report bundle was generated and checked: 11,602 unique candidate-only IDs; all 11,602 joined to one parent Table 2 row; 781,602 parent rows; CSV/JSON row counts agree; strict JSON parsing and ZIP integrity checks passed. Bundle SHA-256: `9ed3c52555f5ef892bf574f77f981c4955decbae7f134c7b542e2f0434e653bc`. This reuses the prior candidate-only list and does not independently rerun the complete Table 4 join.
- A deterministic stratified 100-object identity/membership spot-check and 1,000-object sample construction audit were recorded. These validate sample/crosswalk construction only; they do not prove raw per-epoch detection semantics or full-vs-batch equivalence.
- PR [#227](https://github.com/saeed92m/ztf-classifier/pull/227) ran a real DR24 smoke test on 12 objects and the 42-feature engine. Model inference was `NOT_RUN`; the sample had g-only data and 23/42 features NaN, so this is ingestion/feature-engine smoke evidence only.
- The previous Dependency Audit failures on PRs [#219](https://github.com/saeed92m/ztf-classifier/pull/219) and #227 were associated with stale `filelock==4.0.3` and `setuptools==84.0.0` pins. The dependency-refresh commit was merged to `main`; both dependent branches have since advanced and their current-head CI/scientific checks must complete before merge.
- **Still blocked:** the historical CPVS selection rule; fresh independent full Table 4 membership comparison; source-backed 1,000-object raw-photometry review and full-vs-batch test; independent Gaia/TESS validation; and supported-OS desktop packaging. Keep Issue #170 open and the scientific gate fail-closed.
