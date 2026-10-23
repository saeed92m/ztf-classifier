# Project Charter, Product Contract, and Source-of-Truth Policy

**Status:** Current governing document for platform direction; implementation status is tracked separately in [PROJECT_STATE_REGISTER.md](PROJECT_STATE_REGISTER.md).  
**Repository:** [saeed92m/ztf-classifier](https://github.com/saeed92m/ztf-classifier)  
**Last reviewed:** 2026-10-23

## 1. Product identity

The product is an **Astronomical Data Analysis & Discovery Platform**. “ZTF Classifier” is the repository/software name and the first validated scientific implementation, not a restriction that every user must bring ZTF or CPVS data.

The platform is intended to help astronomers bring data, inspect it, run scientifically appropriate analysis, evaluate uncertainty and out-of-domain behavior, discover and prioritize candidates, review evidence, and export reproducible results. It is not merely a single classifier, a CPVS reconstruction script, a broker clone, or a telescope/hardware project.

## 2. Vision and mission

**Vision:** provide a reliable, extensible, CPU-first workbench that makes astronomical data analysis and discovery accessible and reproducible on modest hardware, while preserving scientific limits and provenance.

**Mission:** build a software platform around explicit data contracts, source adapters, quality control, scientific feature/context generation, compatible analysis methods, uncertainty and calibration, OOD/anomaly evidence, cross-match/context evidence, candidate ranking, human/scientific review, and reproducible reports.

**Product promise:** every result must communicate what was analyzed, how it was processed, which method/model was used, what evidence supports it, what uncertainty/limitations apply, and whether the declared scientific validation gate passed. If the system cannot justify a prediction, it must abstain or report an explicit unsupported/unknown status.

## 3. Product principles

1. **Astronomer-selected input:** users may provide their own supported files or select supported public data sources. No assumption that every input is ZTF or CPVS.
2. **One ingestion interface, not one universal classifier:** file readability, schema normalization, feature availability, model compatibility, and scientific validation are separate states.
3. **Explicit semantics:** object identity, observation time format and scale, passband, magnitude/flux type, units, uncertainty, quality flags, coordinates, and source metadata must be declared or validated. Never silently infer scientifically consequential conversions.
4. **Traceability end to end:** retain source-row/object identity and record hashes, source/release, retrieval date, schema mapping, transformations, exclusions, feature version, model artifact, taxonomy, split, configuration, software environment, diagnostics, and outputs.
5. **Scientific honesty:** benchmark/reference/pseudo-labels are not independent ground truth. No performance or compatibility claims without source-backed evaluation.
6. **Fail-closed gates:** missing, skipped, stale, or inconclusive required evidence is not PASS. Do not weaken thresholds to make a workflow green.
7. **Object-level integrity:** split, join, deduplicate, and compare using complete object/source identifiers—not light-curve rows or physical row ordinals.
8. **CPU-first, resource-aware:** target modest machines and bounded data access. Do not download entire survey archives when a pinned sample or lazy query suffices.
9. **Human oversight:** scientific candidate rankings are decision support, not autonomous discoveries. Preserve review history without silently converting feedback into ground truth.
10. **Reproducible change:** every material change includes regression tests, a lifecycle record, updated docs, evidence, known limitations, and rollback/compatibility notes.

## 4. Canonical end-to-end workflow

1. **Choose/import source** — local files, a declared public survey adapter, or a supported catalog/API.
2. **Capture provenance** — source/release/license or terms, retrieval time, checksums, input identifiers, schema and environment.
3. **Normalize and validate** — map columns explicitly; validate units, time convention, bands, identifiers, missingness, quality flags, duplicate rows, and row counts. Preserve originals.
4. **Quality control** — report rather than silently erase invalid or questionable observations; any exclusion rule is named, versioned, tested, and counted.
5. **Generate features/context** — compute only features valid for the source and document missing/inapplicable features and transformation provenance.
6. **Choose analysis mode** — descriptive/statistical analysis, periodicity, classification, calibrated confidence, conformal sets, OOD scoring, scientific anomaly analysis, cross-match/context, or candidate ranking. These are separate capabilities and must not be conflated.
7. **Check compatibility** — verify the requested method’s schema, units, bands, training domain, preprocessing, taxonomy and artifact requirements before execution.
8. **Evaluate/review** — apply leakage-safe object-level and time-aware validation; show class-wise errors, calibration, risk–coverage, OOD limitations, and human review status where relevant.
9. **Export reproducibly** — data products, report, plots, warnings, provenance manifest, hashes, model/config identity, and machine-readable reason codes.

## 5. Capability states and acceptance language

Use these distinct states in CLI/API/GUI, reports, roadmap, and documentation:

- **Planned:** specified but no implementation evidence.
- **Implemented:** code exists; this alone does not establish successful behavior.
- **Import-supported:** declared format/source passes ingestion, schema and provenance checks on pinned fixtures.
- **Analysis-supported:** declared analysis/feature path passes deterministic fixtures and source-specific QC.
- **Model-compatible:** input contract matches the exact model artifact, preprocessing, units/bands, feature schema, taxonomy and domain contract.
- **Scientifically validated:** predeclared, source-backed evaluation and leakage/provenance/failure gates pass for a clearly stated task and domain.
- **Blocked / unresolved:** required evidence is missing, contradictory or fails; the reason and next evidence needed must be recorded.
- **Deprecated:** no longer recommended; replacement and compatibility window documented.

Never collapse these into one “supported” badge or infer scientific validity from successful file import, passing unit tests, or green CI alone.

## 6. Frozen scientific baseline and non-negotiable boundaries

The established v0.2.0 scientific baseline is immutable unless a separately reviewed, validated change explicitly supersedes it. Current recorded baseline: 150 benchmark objects, 15 ALeRCE reference classes, 10 objects per class, 42 features in `final_feature_set_v0.2`, XGBoost artifact `model_baseline_v0.2_production/artifact`, historical cutoff `59447.224132`, artifact/schema 1.1 diagnostics and fail-closed scientific gate. Verify against committed artifacts before relying on a value in a scientific claim.

ALeRCE labels are benchmark/reference labels, not independent ground truth. The historical ALeRCE snapshot (Zenodo record 4279623 through 2020-06-09) is a frozen reference; live ALeRCE data is monitoring/context and must not be substituted for historical benchmark evidence.

CPVS is one important scientific reproduction task, not the whole product. Its membership discrepancy remains a blocker until source-supported resolution: 781,602 parent IDs; 730,184 published IDs; 741,786 reconstructed candidates; 11,602 candidate-only; zero published-only, according to the latest recorded Seq-based audit. These counts must be reverified against current workflow artifacts before being repeated as fresh measurements. Do not force equality by tuning thresholds or silently changing the published scientific rule.

## 7. Architecture boundaries

- **Source adapters:** format/survey-specific retrieval and parsing; versioned and independently tested.
- **Canonical observation contract:** survey-neutral representation retaining source semantics and provenance; it does not erase survey-specific metadata.
- **Scientific core:** deterministic feature/analysis/model code with explicit contracts and no UI-specific assumptions.
- **Application services:** orchestration, user-selected inputs, durable run metadata, diagnostics, and shared behavior across GUI/CLI/API.
- **Presentation:** desktop/web/CLI views display status and evidence but cannot bypass validation gates.
- **Evidence/provenance layer:** immutable or content-addressed records connecting source → transformation → feature → model/analysis → report.
- **Storage:** raw scientific datasets stay out of Git; repository stores code, schemas, manifests, small fixtures, checksums and compact reports. Database/cloud state must have documented ownership, access control, retention, backup/restore and operational responsibilities before production use.

## 8. Product capability map

The intended platform surface includes:
- Data Manager: local import, source connection, schema mapping, preview, QC, provenance and run history.
- Object/Source Explorer: identifiers, source metadata, observations, cross-match evidence and related objects.
- Light-curve and scientific visualization: time series, bands, cadence, uncertainty, quality masks, phase folding where justified, and source metadata.
- Analysis workspace: descriptive statistics, feature computation, periodicity and supported methods.
- Classification and model management: explicit model identity, compatible schemas/taxonomies, probabilities, calibrated confidence, conformal sets and abstention.
- OOD and anomaly workflows: separate OOD score from scientific-anomaly claims; expose evidence and limitations.
- Discovery workflow: candidate generation, transparent ranking, filters, triage, human review and feedback history.
- Reporting/export: CSV/Parquet/FITS as supported, plots, machine-readable results, provenance manifest, hashes and reproducible reports.
- Help/diagnostics: contextual guidance, clear error/recovery instructions, logs, environment checks and support bundle with secrets excluded.
- Distribution: clean-machine desktop install for supported OS targets, CLI/API for advanced workflows, CPU/memory limits, upgrade/rollback and integrity verification.
- Future integrations: streaming alerts, additional surveys/catalogs, image data and Rubin/LSST only after explicit source contracts, legal/usage review and task-specific validation.

These are product requirements, not a claim that every surface is implemented today. The state register and per-feature acceptance evidence control status.

## 9. Multi-survey strategy

Candidate sources include ZTF DR24/CPVS, StarEmbed, TESS/MAST/TGLC and TESS Transients, OGLE, AAVSO, ATLAS, ASAS-SN, Gaia variability products, and PLAsTiCC/ELAsTiCC. Treat this as a validation matrix, not a promise that all adapters exist. Pin versions, terms, retrieval dates, schemas and hashes before use.

For every source, test: readability; explicit schema mapping; time/unit/band/quality semantics; row/object accounting and duplicate behavior; deterministic normalization; feature availability; model compatibility; independent/time-aware scientific evaluation; and reproducible outputs. Start with small public samples. Never treat different taxonomies or simulated labels as interchangeable.

## 10. Source of truth and documentation governance

- **GitHub main + tagged releases:** authoritative for merged code, shipped artifacts, versioned contracts and current release facts.
- **Open PRs:** proposals only; do not describe them as shipped or validated. Link status and checks.
- **GitHub issues/actions/artifacts:** evidence for blockers, workflow status and scientific measurements; record run IDs and commit SHAs.
- **Current handbook/state register/roadmap:** human-readable operational view, updated in the same documentation change as material implementation decisions.
- **Notion:** navigation, durable decisions, and human-readable mirror. Every snapshot records exact Git commit/PR and date. It must not claim to be fresher than GitHub.
- **GitHub Wiki:** supplementary entry point only; link back to canonical documents. If the Wiki is not accessible to the automation connection, report the limitation rather than claiming it was updated.
- **GitHub Pages:** only a published source if repository settings actually enable it and deployment is verified. Do not claim a site exists merely because docs are present.
- **Supabase or other services:** only part of the ZTF project if a matching project/schema/owner is explicitly verified. Do not infer that another company project is this product’s backend.

Every material update must include: what changed; why; exact source revision; status (planned/implemented/tested/validated); evidence links; risks and limitations; next action and owner. Keep historical handbook versions intact; publish a clearly labeled current handbook rather than silently rewriting old snapshots.

## 11. Definition of done

A feature is complete only when:
- the requirement and unsupported cases are explicit;
- implementation is integrated at the correct architecture boundary;
- unit, integration, regression and relevant scientific tests pass and are inspected;
- source-backed fixtures/manifests and deterministic results are retained;
- provenance and user-facing diagnostics are present;
- security, privacy, resource and licensing concerns are reviewed;
- handbook, roadmap, API/user guide, help and release notes are aligned;
- status is verified on the exact commit/release;
- unresolved risks are stated without downgrading acceptance criteria.

A documentation task is complete only when the edited files/pages are fetched back and verified, the canonical links work, mirrors identify the correct revision, and unsupported destinations (Wiki/Pages/services) are explicitly reported.
