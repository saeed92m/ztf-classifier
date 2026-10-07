# ZTF Classifier — Ecosystem Review & Product Expansion Record

Status date: 2026-10-08
Review scope: GitHub repository-search ecosystem review for “Ztf classifier” plus adjacent ZTF/astronomy ML tooling.
Purpose: Preserve reusable lessons and convert them into explicit product, architecture, UX, scientific, and roadmap requirements.

## Executive decision

ZTF Classifier remains an **Astronomical Data Analysis & Discovery Platform**, not merely a classifier.

The immutable v0.2.0 scientific baseline is preserved. New capabilities must be layered around the core through stable contracts rather than by rewriting or weakening the baseline.

## Lessons to retain

### 1. Discovery workbench, not classification-only
The platform should support a complete path:
source data → ingestion → normalization/QC → feature/context generation → analysis modes → uncertainty/calibration/OOD → candidate ranking → evidence/provenance → human/scientific validation → reproducible discovery outputs.

### 2. Anomaly and OOD are distinct
OOD, classification uncertainty, calibration, conformal prediction, scientific anomaly evidence, catalog evidence, and explainability evidence remain separate channels. The system must never label an OOD score as proof of a scientific anomaly.

### 3. Real/Bogus is a separate concern
Artifact/reality screening must be architecturally distinct from scientific object classification. A future real/bogus stage may precede scientific inference without changing the v0.2 scientific benchmark semantics.

### 4. Object/Source Explorer
Every analyzed source should have an inspectable scientific record containing identity, coordinates, observations, light curve, features, classification, probabilities, uncertainty/OOD, anomaly evidence, catalog/cross-match evidence, provenance, and model/artifact identity.

### 5. Cross-match as a first-class capability
Cross-match must produce evidence, not just a boolean match:
catalog/source ID, angular separation, confidence/method, retrieval time/version, and provenance. Candidate integrations include Gaia, SIMBAD, VizieR, NED, ALeRCE, and TNS where licensing/access/contracts permit.

### 6. Human-in-the-loop review
Candidate discovery should support review states such as accept, reject, reclassify, annotate, and defer. Human feedback must be provenance-aware and must not silently become training truth.

### 7. Explainability
Predictions should expose understandable evidence: leading feature contributions, probability/calibration context, conformal set, OOD state, data-quality state, and model/artifact version. Explainability is evidence about the model, not scientific proof.

### 8. Similar-object search
Provide similarity search for scientifically comparable sources, with a transparent similarity definition and reproducible retrieval context.

### 9. Discovery ranking
Introduce a transparent, versioned discovery score/ranking that can combine novelty, anomaly evidence, uncertainty/OOD, data quality, cross-match context, and scientific-interest signals. The score must be explainable and must not be presented as an objective truth.

### 10. Alert/data-stream readiness
Architecture should support offline, batch, and future streaming/alert processing without forcing a later Core rewrite. ZTF Alert/AVRO ingestion should be treated as a supported future input contract.

### 11. Modular feature registry
Feature definitions should be versioned and metadata-rich: name, definition, units, source, version, missing-value policy, valid range, and scientific interpretation. The frozen v0.2 42-feature definition remains immutable.

### 12. Provenance and evidence in the UI
Scientific provenance is not only backend metadata. Users should be able to inspect dataset/source, retrieval context, schema, object ID, model version, feature schema, artifact hash, and evidence lineage from the GUI.

## Product/UX requirements

### Cross-platform desktop application
Target:
- Windows 10/11: self-contained installer
- macOS: signed/notarized application distribution where feasible
- Linux: AppImage as the broad portable baseline; .deb may be added for Debian/Ubuntu users

The user-facing installation path must not require Python, virtual environments, pip, Git, or a terminal.

CLI and API remain available for advanced users.

### Integrated Help Center
Help is a first-class product area, not an external afterthought.

Required sections:
- Getting Started
- Importing ZTF Data
- Object Explorer
- Light Curves & Visualization
- Classification
- Discovery & Anomaly Detection
- Models & Features
- Understanding Results
- Scientific Validation
- Reports & Export
- Settings
- Troubleshooting
- Scientific Methodology
- Data/Privacy
- About

Help must be contextual where practical and error-aware.

### Core GUI areas
Dashboard, Data Manager/Import, Object Explorer, Analysis, Discovery, Results/Visualization, Models, Reports, Help, Settings.

## Roadmap priorities

### P0 — Product foundation
- Cross-platform desktop shell and packaging architecture
- Stable Application/Core API boundary
- Data ingestion abstraction
- Object/Source Explorer
- Integrated Help and Troubleshooting
- Explainability/OOD/uncertainty presentation
- Provenance/Evidence UI
- Discovery/Anomaly workflow

### P1 — Scientific exploration
- Cross-match framework
- Similar-object search
- Human-in-the-loop review and feedback
- Transparent discovery ranking
- Real/Bogus integration boundary
- Additional validated analysis modes

### P2 — Scale and operations
- ZTF Alert/AVRO ingestion
- Offline/batch/streaming execution modes
- Follow-up integrations where scientifically and operationally justified
- Additional models/features only with validation and provenance contracts

## Guardrails

1. v0.2.0 scientific baseline remains immutable.
2. Baseline benchmark labels remain reference labels, not independent ground truth.
3. No large external datasets are committed to Git.
4. Scientific claims remain fail-closed.
5. OOD is not automatically scientific anomaly detection.
6. Human feedback is not silently promoted to ground truth.
7. Discovery ranking is an explainable prioritization mechanism, not a scientific truth score.
8. Every new external catalog/data source requires provenance, version/retrieval evidence, and licensing/access review.
9. Every meaningful implementation change updates affected documentation, cumulative-learning/failure-prevention records, roadmap status, and release notes when release behavior changes.
10. Desktop packaging must not require users to manage Python dependencies manually.

## Ecosystem references used as design inspiration

The review considered patterns from projects/tooling around ZTF and astronomical time-series analysis, including SCoPe, zwad, SkyPortal, ZTF alert schemas, cesium, BRAAI, AMPEL, and AstroLens. These are design references, not dependencies or endorsements.

The project should adopt only patterns that preserve ZTF Classifier's scientific contracts, CPU-first posture, provenance requirements, and reproducibility standards.

## Definition of success

The product should allow a non-developer scientist to:
1. install the application on Windows, macOS, or Linux;
2. import or connect supported ZTF data;
3. inspect sources and light curves;
4. run classification/analysis;
5. understand uncertainty, OOD, evidence, and provenance;
6. discover and rank unusual candidates;
7. review candidates;
8. export reproducible results/reports;
9. access Help without using a terminal.

Advanced users retain CLI/API access.

