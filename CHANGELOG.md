# Changelog

## [0.3.0] — Production inference milestone

This release advances the project from the immutable v0.2.0 scientific baseline to a production-oriented inference milestone.

### Added
- Filesystem-backed model registry for immutable production artifacts.
- Registry-backed single-object prediction.
- Registry-backed batch inference.
- Explicit CLI model-selection contract.
- Production validation hardening for external boolean fields and model feature schemas.
- Registry-backed end-to-end tests for both predict and batch CLI paths.
- Artifact schema 1.1 support with calibration, conformal diagnostics, OOD diagnostics, and provenance.

### Validated
- 150-object benchmark dataset across 15 classes.
- 42-feature production inference contract.
- JSON prediction output schema 1.1.
- Batch Parquet output schema 1.1.
- Registry → artifact → inference → CLI → output end-to-end path.
- CI dependency, lint, test, and import checks.

### Compatibility
- The `v0.2.0` tag remains the immutable scientific baseline.
- The production artifact model version remains `baseline_v0.2`.
- Artifact schema 1.0 remains supported alongside 1.1.

### Scope
This release does not claim that the 150-object benchmark is representative of the full ZTF population. ALeRCE labels remain reference/weak labels rather than independent astrophysical ground truth.
