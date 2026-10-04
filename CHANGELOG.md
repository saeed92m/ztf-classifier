# Changelog

## Unreleased

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
