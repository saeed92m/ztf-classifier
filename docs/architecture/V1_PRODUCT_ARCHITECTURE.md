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
