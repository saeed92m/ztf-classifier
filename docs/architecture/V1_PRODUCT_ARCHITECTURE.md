# ZTF Classifier — v1.0 Product Architecture Index

Canonical product: **Astronomical Data Analysis & Discovery Platform**.

## Scientific Core

Runtime flow:

source data → ingestion → normalization/QC → scientific feature/context layers → analysis modes → uncertainty/calibration/conformal/OOD → candidate ranking → evidence/provenance → human/scientific validation → reproducible discovery outputs.

The v0.2.0 scientific baseline remains immutable. Classification uncertainty, calibration, conformal prediction, OOD, scientific anomaly evidence, catalog evidence, and explainability evidence are separate channels.

Scientific Validation is release-blocking at product level. Exact historical CPVS reconstruction is a separate claim-specific external evidence lane and remains unresolved.

## Product architecture

The desktop product is layered over the scientific Core:

Desktop GUI / CLI / API
→ Application Services
→ Stable Core Contracts
→ Scientific Core
→ Models / Features / Data adapters.

The GUI must not directly mutate scientific model artifacts or bypass validation/provenance contracts.

## Cross-platform delivery

Primary user-facing targets:
- Windows 10/11: self-contained installer
- macOS: application distribution with signing/notarization where feasible
- Linux: AppImage baseline; .deb may be added for Debian/Ubuntu users

End users should not need Python, pip, virtual environments, Git, or a terminal.

CLI/API remain supported for advanced users and automation.

## Data and analysis layer

The platform must support a data-ingestion abstraction capable of evolving across:
- targeted ZTF light curves;
- ZTF Alert/AVRO;
- CSV/Parquet/FITS and other explicitly supported formats;
- future catalog and external-source adapters.

Data adapters must preserve source identity, retrieval/provenance, schema/version, QC state, and object-level lineage.

## Scientific discovery layer

First-class capabilities:
- classification;
- calibration and uncertainty;
- conformal prediction;
- OOD detection;
- scientific anomaly evidence;
- Real/Bogus as a separate architectural stage;
- discovery candidate generation and transparent ranking;
- cross-match evidence;
- similar-object search;
- human-in-the-loop review and feedback;
- explainability evidence;
- reproducible reports.

## Object/Source Explorer

Every source should be inspectable through a unified record containing, where available:
identity, coordinates, observations, light curve, features, model prediction, probabilities, uncertainty, conformal set, OOD state, anomaly evidence, catalog/cross-match evidence, provenance, and model/artifact identity.

## Evidence and provenance

User-visible evidence should include:
- dataset/source;
- retrieval context;
- schema/version;
- object ID;
- model version;
- feature schema;
- artifact identity/hash;
- external catalog/source identity;
- evidence lineage.

Discovery ranking is a versioned prioritization mechanism, not a scientific truth score.

## UX and Help

Core GUI areas:
Dashboard, Data Manager/Import, Object/Source Explorer, Analysis, Discovery, Results/Visualization, Models, Reports, Help, Settings.

Help is a first-class subsystem with contextual Getting Started, data import, analysis, discovery, models/features, results interpretation, scientific validation, reports, settings, troubleshooting, methodology, data/privacy, and about content.

## Scale and operations

Architecture must preserve a path for:
- offline processing;
- batch processing;
- future alert-stream/streaming processing;
- future follow-up integrations.

Streaming support is a future execution mode, not a requirement to weaken current deterministic/offline scientific workflows.

## Guardrails

1. v0.2.0 remains immutable.
2. No dataset leakage or benchmark contamination.
3. OOD is not automatically scientific anomaly detection.
4. Human feedback is not silently promoted to ground truth.
5. External-source claims require provenance and access/licensing review.
6. New analysis modes require explicit contracts, tests, provenance, and scientific validation before being treated as validated capability.


## Generality boundary — 2026-10-22

Generic local CSV/Parquet import is not equivalent to arbitrary scientific analysis. The current importer records schema and SHA-256 provenance, while the default NativeV0_2Backend deliberately preserves the frozen v0.2 42-feature schema and the source-backed production inference path requires a compatible registered model. New datasets and feature sets must use explicit, versioned adapters/backends and declare units, missing-value policy, identifiers, feature schema, provenance, and validation scope. Unsupported combinations must fail explicitly rather than silently reusing CPVS or v0.2 assumptions.

The staged generality audit and independent-dataset/50-case/second-method validation are tracked in [the parallel validation plan](../roadmap/PARALLEL_VALIDATION_AND_ECOSYSTEM_PLAN_2026-10-22.md) and [Issue #210](https://github.com/saeed92m/ztf-classifier/issues/210). CPVS exact reproduction remains a separate unresolved historical claim; no baseline or scientific gate is changed by this architecture note.
