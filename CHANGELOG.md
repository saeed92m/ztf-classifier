# Changelog

## [0.5.0] — Scientific validation release candidate

### Added
- Source-backed DR24 and ALeRCE scientific-validation evidence contracts and immutable historical publisher references.
- Heavy release-candidate validation and executable cumulative lifecycle evidence.
- Explicit separation of product release-blocking validation from claim-specific historical external reproduction.

### Changed
- Release certification now requires the release candidate to satisfy the scientific gate, lifecycle contracts, package checks, and reproducibility evidence.

### Scientific status
- CPVS parent evidence: 781,602 rows verified.
- Published CPVS membership reference: 730,184 objects retained as immutable external reference.
- Exact CPVS reconstruction remains explicitly unresolved and does not block the product gate unless exact reconstruction is part of the declared release claim.


## Unreleased

- Post-v0.5.0 documentation alignment and ecosystem-derived platform guidance.

- Frozen historical ALeRCE and CPVS publisher-reference contracts.
- Immutable archive acquisition with MD5/SHA-256 evidence manifests.
- Frozen/live separation for historical reproduction versus current-source drift monitoring.
- Heavy source-backed scientific-validation evidence and lifecycle-gate correction.
- Scientific-validation completion record for 2026-10-04.

## [0.4.0] — Reproducibility and production hardening

### Added
- Streaming SHA-256 checksum utility for reproducibility and artifact validation.
- Explicit production calibration, conformal, and OOD status fields.
- Artifact manifest hashing and explicit legacy integrity warnings.
- Strict ALeRCE ingestion diagnostics for invalid observations, coordinates, bands, duplicates, and photometry fallback.
- Data card and model card documentation.
- CI format, coverage, package-build, wheel-install, and dependency-audit gates.
- Upgrade baseline and verification report structure.

### Changed
- Production diagnostic execution is independent: missing conformal data no longer disables OOD evaluation and vice versa.
- Package metadata advances to software version 0.4.0 while the scientific baseline remains v0.2.0 and the production model remains baseline_v0.2.
- ALeRCE normalization preserves the existing default DataFrame API while offering an additive diagnostics return mode.

### Compatibility
- The v0.2.0 scientific baseline remains immutable.
- Dataset contract benchmark_v0.2 remains unchanged.
- The frozen v0.2 feature schema remains 42 features.
- Artifact schemas 1.0 and 1.1 remain readable.
- Existing CLI output fields remain available; new diagnostic/provenance fields are additive.

### Limitations
- The 150-object benchmark is small and is not representative of the full ZTF population.
- ALeRCE labels are reference/weak labels rather than independent astrophysical ground truth.
- Source-data licensing and attribution requirements remain applicable to future ingestion and publication.
