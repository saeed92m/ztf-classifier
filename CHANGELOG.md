# Changelog

## [1.0.0] — Stable product release — 2026-10-06

### Added
- Stable software release of the Astronomical Data Analysis & Discovery Platform.
- Event-driven release publication bound to the successful Scientific Validation workflow commit.
- Immutable-safe release handling with final tag/asset verification.
- Curated release notes as a mandatory release contract for future versions.

### Changed
- Software package version is 1.0.0.
- The frozen scientific baseline remains v0.2.0.
- The production model remains baseline_v0.2.
- Release publication no longer depends on manual dispatch.
- Scientific validation evidence is restored from workflow artifacts without requiring large external datasets in Git.

### Scientific status
- Product Scientific Gate: PASS.
- Latest source-backed Scientific Validation: PASS.
- Historical ALeRCE and CPVS references are immutable evidence lanes.
- Exact historical CPVS reconstruction remains UNRESOLVED / claim-specific: current candidate 741,787 vs published membership 730,184, with all 730,184 published members contained in the candidate set.
- This unresolved reconstruction claim is not presented as an ML or production failure.

### Release artifacts
- ztf_classifier-1.0.0-py3-none-any.whl
- ztf_classifier-1.0.0.tar.gz

## [0.5.0] — Scientific validation and immutable release

### Added
- Immutable-safe release-tag resolution and final asset verification.
- Source-backed DR24 and ALeRCE scientific-validation evidence contracts and immutable historical publisher references.
- Heavy release-candidate validation and executable cumulative lifecycle evidence.
- Explicit separation of product release-blocking validation from claim-specific historical external reproduction.

### Changed
- Release certification requires scientific gate, lifecycle contracts, package checks, and reproducibility evidence.

### Scientific status
- CPVS parent evidence: 781,602 rows verified.
- Published CPVS membership reference: 730,184 objects retained as immutable external reference.
- Exact CPVS reconstruction remains explicitly unresolved.

## [0.4.0] — Reproducibility and production hardening

### Added
- Streaming SHA-256 checksum utility.
- Explicit production calibration, conformal, and OOD status fields.
- Artifact manifest hashing and integrity warnings.
- Strict ALeRCE ingestion diagnostics.
- Data Card and Model Card.
- CI format, coverage, package-build, wheel-install, and dependency-audit gates.

### Changed
- Production diagnostic execution is independent: missing conformal data no longer disables OOD evaluation and vice versa.
- Package metadata advances independently from the immutable scientific baseline.

### Compatibility
- v0.2.0 scientific baseline remains immutable.
- Dataset contract benchmark_v0.2 remains unchanged.
- Frozen v0.2 feature schema remains 42 features.
- Artifact schemas 1.0 and 1.1 remain readable.