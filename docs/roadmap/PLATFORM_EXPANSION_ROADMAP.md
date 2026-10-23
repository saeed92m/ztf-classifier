# Astronomical Data Analysis & Discovery Platform — Product Roadmap

Status date: 2026-10-11  
Current immutable software release: v1.0.1  
Product implementation tracker: [Issue #158](https://github.com/saeed92m/ztf-classifier/issues/158)  
Scientific blocker: [Issue #170](https://github.com/saeed92m/ztf-classifier/issues/170)

## Guiding constraints
- Preserve scientific baseline v0.2.0 and model identity baseline_v0.2.
- Keep the scientific gate fail-closed; missing evidence is never PASS.
- Build CPU-first, reproducible workflows for modest hardware.
- Separate classification, uncertainty/calibration, conformal prediction, OOD, anomaly evidence, catalog context, and explainability.
- Prefer source-backed, versioned adapters over copying datasets into Git.
- Every meaningful change updates its lifecycle record, tests, failure-prevention knowledge, and affected docs.

## Track A — Scientific integrity and external evidence

### A1. CPVS exact-reproduction investigation — OPEN / UNRESOLVED
- [ ] Trigger heavy workflow on an intended ci/heavy/* ref and verify source-provenance/scientific-gate-readiness executes.
- [ ] Re-run CPVS derivation after PR #173's finite/non-zero magnitude correction.
- [ ] Inspect acquisition report, derived membership, independent VizieR table, and hashes.
- [x] Verify the robust parser reads all 730,184 published ZTF names without duplicates.
- [x] Identify and correct the audit's invalid row-ordinal substitution: official CPVS lightcurve membership uses Table2 `Seq` (bytes 24–29), not physical row order.
- [ ] Rerun derivation and independent membership audit using actual Seq values; previous membership metrics are invalid and superseded.
- [ ] Explain the residual candidate/published membership difference from valid Seq-based evidence and source-backed selection semantics, not tuned thresholds.
- [ ] Require exact independent membership audit before claiming exact reconstruction.
- [ ] Keep Issue #170 open until evidence-based disposition.

### A2. Product-level validation — RELEASE-BLOCKING
- [ ] Complete pinned ZTF DR24 source-backed adapter execution.
- [ ] Complete frozen historical ALeRCE reference acquisition/execution and immutable manifests.
- [ ] Complete object-overlap, duplicate, target leakage, temporal leakage, preprocessing, schema, provenance, and failure-code audits.
- [ ] Generate per-release benchmark evidence and show scope limits/known failure cases to users.
- [ ] Ensure required scientific gates run rather than skip on release-candidate refs.

## Track B — Desktop application and user experience

### B1. Architecture foundation
- [ ] Freeze and test Application ↔ Scientific Core boundary.
- [ ] Define stable application-service, ingestion, provenance, configuration, and durable-state contracts.
- [ ] Ensure GUI uses the same service contracts as CLI/API and cannot bypass scientific validation.

### B2. Scientist-facing workflows
- [ ] Desktop shell and dashboard.
- [ ] Data Manager / import / source connection.
- [ ] Object/source explorer and light-curve visualization.
- [ ] Analysis workspace with model identity, uncertainty, calibration, OOD and provenance.
- [ ] Results, visualization, reproducible reports and exports.
- [ ] Discovery candidate workspace with human review and ranking limitations.
- [ ] Settings, Help, troubleshooting, diagnostics and logs.

### B3. Distribution and usability
- [ ] Windows self-contained installer and first-run smoke test.
- [ ] macOS application package and smoke test.
- [ ] Linux AppImage or documented, tested alternative.
- [ ] Clean-machine installation without Python/pip/Git/terminal for normal use.
- [ ] CPU-first performance and memory test on modest hardware.
- [ ] Installer integrity, checksums, release provenance and rollback/uninstall behavior.

## Track C — Scientific capability expansion
- [ ] Independent labeled benchmark and cross-match evidence.
- [ ] Model comparison/ensemble only where labels are comparable and splits are leakage-safe.
- [ ] Dedicated scientific anomaly analysis; do not label OOD as anomaly detection.
- [ ] Drift monitoring separates live-source changes from frozen historical evaluation.
- [ ] Multisurvey/light-curve/image/catalog adapters only after licensing, provenance, schema and validation review.
- [ ] Controlled human feedback; never silently convert review feedback into ground truth.

## Track D — Reliability, security, and release engineering
- [ ] Test fresh installation, upgrade, uninstall, offline/poor-network failure, cache corruption, and missing-data paths.
- [ ] Test dependency locks, supply-chain/security checks, API auth, data handling, and safe export behavior.
- [ ] Preserve deterministic reports, input manifests, checksums, model identity, and audit trails.
- [ ] Every meaningful PR has a validated lifecycle cycle record and regression test.
- [ ] Every release has complete release notes, release description, checksums, provenance, and scientific/engineering gate evidence.

## Milestones and exit criteria

| Milestone | Exit criteria |
|---|---|
| M0 — Scientific recovery | Required heavy jobs execute; CPVS claim is accurately classified; evidence gaps/root causes are recorded. |
| M1 — Desktop foundation | Application/service boundary and ingestion/provenance contracts are tested. |
| M2 — Usable alpha | A non-developer can install, import/connect data, inspect an object/light curve, run analysis, and view evidence. |
| M3 — Scientific workbench | Results, uncertainty/OOD, discovery review, reproducible reports and exports work end-to-end. |
| M4 — Cross-platform beta | Windows/macOS/Linux packaging and clean-machine smoke tests pass. |
| M5 — Scientific product acceptance | Independent benchmark, leakage, provenance, failure analysis and release gates pass for declared scope. |
| M6 — Stable platform release | All M0–M5 criteria pass, docs/help are complete, release notes and evidence are published. |

No milestone is complete based on code presence alone. Completion requires measured evidence and recorded acceptance.

## Evidence update — 2026-10-11

A deeper source-schema review found that the previous audit mapped published ZTF names to parent row ordinals instead of the explicit CPVS Table2 `Seq` field (bytes 24–29), while lightcurve `SourceID` joins by `Seq`. Thus the 725,101 / 16,686 / 5,083 values from heavy run [#38095650470](https://github.com/saeed92m/ztf-classifier/actions/runs/38095650470) are invalid and superseded. PR [#176](https://github.com/saeed92m/ztf-classifier/pull/176) now reads actual Seq IDs for the derived candidate universe and published-name join. The Seq-based heavy run [#38121913146](https://github.com/saeed92m/ztf-classifier/actions/runs/38121913146) has completed: 741,786 candidates; 730,184 intersection; 11,602 candidate-only; 0 published-only; 0 duplicate and 0 unmapped published names. This is a valid identifier-space comparison, but exact CPVS reproduction remains **UNRESOLVED** because 11,602 candidates remain unexplained. The flag-zero variant yields 736,225 candidates / 724,712 intersection / 5,472 published-only; a magnitude 20.6 diagnostic loses 18,865 published objects. Neither is an acceptable fix. Current-head CI must pass and the residual selection semantics must be resolved or documented from evidence; do not tune thresholds to force cardinality equality. Source: https://cdsarc.cds.unistra.fr/viz-bin/ReadMe/J/ApJS/249/18?format=html&tex=true.


## Track C1 — General-purpose light-curve ingestion and cross-survey validation

**Status: NOT IMPLEMENTED / acceptance blocker.** The platform must not assume that every astronomer will provide CPVS or even ZTF data. CPVS is one historical reproduction benchmark, not the product's only input domain. This track is independent of Issue #170 and must proceed regardless of author response.

### Product contract

1. Accept user-selected light-curve tables through an explicit schema-mapping step; never infer that arbitrary column names or units are interchangeable.
2. Normalize supported inputs into a versioned, survey-neutral observation contract: object identifier, observation time and time scale, passband, measurement type (magnitude or flux), value, uncertainty, quality/mask flags, and optional coordinates. Preserve original columns and values.
3. Keep survey-specific metadata and units explicit. Convert units only with a documented, tested transformation; never silently treat magnitude as flux, mix AB/Vega systems, or assume all timestamps share a time scale.
4. Separate **ingestion validity**, **feature computability**, **model compatibility**, and **scientific validity**. A file can import successfully while remaining ineligible for the frozen ZTF model.
5. The v0.2.0 / v1.0.1 ZTF model, its 42-feature schema, class order, calibration, cutoff, and acceptance gates remain unchanged. Unsupported inputs must return actionable diagnostics, not a fabricated prediction.
6. Every run emits a machine-readable report: input hashes, source/survey declaration, mapped schema and units, row/object counts, duplicate and missingness statistics, quality-filter counts, time/band coverage, conversion log, feature availability, model-compatibility decision, warnings, and reason-coded failures.

### Initial public-data validation matrix

These are candidate external validation sources, not claims that adapters already exist or that their labels are interchangeable. Each dataset must be pinned by release/version, license/terms, retrieval date, and checksums before use.

| Dataset family | Representative source | What it tests | Initial acceptance lane |
|---|---|---|---|
| ZTF periodic variables | CPVS parent + published Table 4 | Existing baseline, identifier joins, historical reproducibility | Historical membership and derivation tests; CPVS blocker remains separate |
| ZTF survey data | Official IRSA ZTF DR24 | Raw/public-source ingestion and large tabular schemas | Source adapter + time/band/quality/provenance checks |
| ZTF labeled light curves | StarEmbed ZTF_40k | Split integrity, duplicates, missingness, raw-array handling | Independent dataset audit; no automatic claim of independent ground truth |
| TESS transients | TESS Transients (MAST/MIT) | Text time-series schema, transients, uneven coverage and quality caveats | Import/normalization first; classification only with compatible labels/features |
| TESS extracted light curves | MAST TESS products / TGLC | FITS tables, sector/cadence metadata, flux units and time conventions | FITS adapter and unit/time-scale checks |
| OGLE variable stars | OGLE Collection of Variable Stars | Long baselines, different passbands, catalog labels and text formats | Survey adapter and label-taxonomy mapping audit |
| AAVSO observations | AAVSO International Database | Heterogeneous contributors, visual/CCD observations, mixed quality and passbands | Import and quality/provenance diagnostics; not direct ZTF-model inference |
| ATLAS | Public ATLAS light-curve products / cross-survey retrieval | Different passbands, photometric conventions and cadence | Adapter only after official schema/license review |
| ASAS-SN | Public variable-star/light-curve products | Broad cadence, survey-specific bands and quality flags | Adapter and missingness/cadence stress tests |
| Gaia variability | Gaia DR3 variability products | Catalog-level variability features vs point-level photometry | Separate catalog-feature lane; do not pretend it is a raw light curve |
| PLAsTiCC / ELAsTiCC | Public transient benchmark datasets | Simulated-domain shifts, class imbalance and out-of-domain behavior | Benchmark-only lane with simulation/domain labels explicit |

### Required test ladder — per source and per supported input mode

- **L0 — Readability:** valid/invalid files, supported encodings and formats, empty inputs, malformed rows, duplicate headers, oversized files, and clear error messages.
- **L1 — Schema mapping:** renamed columns, reordered columns, extra columns, missing required fields, ambiguous identifier/time/value fields, and user-confirmed mappings.
- **L2 — Scientific semantics:** magnitude versus flux, uncertainty units, passband mapping, time scale (UTC/BJD/TDB where applicable), sentinel values, non-finite values, upper limits, quality flags, duplicate observations, and unsorted timestamps.
- **L3 — Normalization invariants:** deterministic normalized output, unchanged source values retained, row-count accounting, stable object grouping, and reproducible content hashes.
- **L4 — Feature compatibility:** feature-by-feature availability and missingness; no silent imputation or schema coercion; compare feature output against hand-checked fixtures.
- **L5 — Model compatibility:** only run a model if its declared input schema, units, passbands, training domain, and preprocessing match. Otherwise return `unsupported_model_domain` or an explicit review-required status.
- **L6 — Scientific evaluation:** use independently sourced labels where available, object-disjoint and time-aware splits, per-class precision/recall/F1, confusion matrix, calibration, abstention/coverage, OOD behavior, and failure-case review. Report metrics per dataset and never pool incomparable taxonomies.
- **L7 — Reproducibility/regression:** repeat runs and verify identical normalized hashes/features; record source versions, transformations, dependencies, manifests and results.

### Minimum release gate for a new survey adapter

A source is **supported for import** only after L0–L3 pass. It is **supported for feature analysis** only after L4 passes. It is **supported for prediction** only after L5 passes. It is **scientifically validated for a stated task/domain** only after L6–L7 pass. The UI/CLI/API must display these as distinct statuses and never collapse them into a single green check.

### Execution order

1. Audit and test the existing local CSV/Parquet ingestion boundary against the L0/L1/L3 adversarial fixture matrix.
2. Define a versioned canonical observation schema and explicit mapping/conversion report; add golden fixtures with known magnitude, flux, band, and time-scale cases.
3. Implement one additional real source adapter at a time, beginning with TESS Transients text tables and one MAST FITS product because their input representations and cadence/metadata differ from ZTF. Keep acquisition bounded to small, public, pinned samples.
4. Add OGLE and AAVSO as independent format/quality stress tests; add ATLAS/ASAS-SN/Gaia only after source schema and usage terms are verified.
5. Run the same test ladder for every adapter in CI. Keep source-download tests separately marked and hash-pinned so ordinary CI does not depend on live endpoints.
6. Publish a dataset-by-dataset capability table with evidence links, unsupported cases, and metrics. Do not claim universal compatibility from successful file import.

**Scientific boundary:** one universal ingestion interface is achievable; one universal feature vector or classifier is not assumed. Different surveys have different passbands, calibrations, cadence, time conventions, noise, and label taxonomies. Cross-survey predictions require explicit transformations and independent validation; otherwise the correct behavior is import/analyze with limitations or abstain, not silently classify.


## Platform-wide product contract — reviewed 2026-10-23

The product is an Astronomical Data Analysis & Discovery Platform. ZTF/CPVS is the first scientific domain and an important validation task, not the only allowed user input. The platform must accept astronomer-selected data through supported, explicit source/file contracts and must not assume that a successfully imported file is eligible for the frozen ZTF classifier.

Governing references:
- Product vision, architecture boundaries, capability-state vocabulary and documentation rules: [Project Charter](../PROJECT_CHARTER_AND_SOURCE_OF_TRUTH.md).
- Verified current release/PR/documentation state and blockers: [Project State Register](../PROJECT_STATE_REGISTER.md).

### Capability acceptance states

Track these separately for each input/source and analysis mode:
1. **Import-supported:** format, schema mapping, provenance and row/object accounting pass pinned tests.
2. **Analysis-supported:** declared QC/features/analysis pass deterministic fixtures for that source.
3. **Model-compatible:** exact artifact, schema, preprocessing, units, passbands, taxonomy and domain contract match.
4. **Scientifically validated:** source-backed, leakage-safe evaluation, calibration/failure analysis and reproducibility gates pass for a stated task/domain.

A successful state at one level does not imply the next. Unsupported or unvalidated inputs must return explicit diagnostics/abstention, not a fabricated classification.

### Documentation synchronization rule

Any material change to product scope, architecture, validation criteria, release status, or known blockers must update this roadmap, the current handbook/state register, and relevant user/developer docs in the same change. Update Notion as a revision-stamped mirror after the source commit is known. Preserve historical handbook versions. Do not report Wiki/Pages/Supabase as updated unless access, target identity and the saved result are verified.
