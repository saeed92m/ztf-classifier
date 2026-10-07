# Changelog

All notable changes to the ZTF Classifier platform are documented here.

## [1.0.1] — 2026-10-07

### Fixed
- Made the FastAPI and Uvicorn runtime dependencies part of the standard package installation because `ztf-classifier-api` is a published production entrypoint.
- Kept optional `web` dependencies limited to presentation-only packages (`plotly` and `streamlit`).
- Preserved the v0.2 scientific baseline and `baseline_v0.2` model identity; this is a packaging/productization patch, not a scientific-model change.

### Verification
- Existing API test coverage exercises health/readiness, OpenAPI, prediction, authentication, durable jobs/results, catalog export, feature backends, and fail-closed scientific validation.
- Release v1.0.1 requires the same CI, CodeQL, scientific-validation, and curated-release-note gates.

## [1.0.0] — 2026-10-06

### Release identity
- Software release: `v1.0.0`
- Scientific baseline: immutable `v0.2.0`
- Production model identity: `baseline_v0.2`

### Highlights
- Promoted the repository to the Astronomical Data Analysis & Discovery Platform product identity.
- Added production inference, diagnostics, provenance, API/workbench foundations, durable analysis jobs and scientific result persistence.
- Added canonical installation, quick-start, user, scientific-methodology, troubleshooting, model-card and architecture documentation.
- Release automation now validates source-backed scientific evidence and requires curated release notes.

### Scientific validation
- Source-backed DR24/ALeRCE evidence and immutable historical reference checks pass the scientific gate.
- CPVS historical reconstruction boundary remains explicitly documented and claim-specific.

### Scope
- v1.0.0 is a production software release; it does not change the immutable v0.2 scientific benchmark or baseline model identity.
