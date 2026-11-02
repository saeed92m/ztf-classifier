# ZTF Classifier — Project Status Report

**Status date:** 2026-11-03  
**Main branch:** `4f98a06bde95b08a54a8844995b7717d6281ca33`  
**Current software release:** `v1.0.1` (published, immutable)  
**Scientific baseline:** `v0.2.0` (frozen)  
**Production model:** `baseline_v0.2`  
**Active independent-validation PR:** [#246](https://github.com/saeed92m/ztf-classifier/pull/246) — Draft

## Executive status

The v1.0.1 Python package is released. The frozen v0.2.0 classifier has a 42-feature contract, a persisted XGBoost artifact, calibration/conformal/OOD diagnostics, CLI inference, and batch inference.

The broader product is not complete. The current application has a FastAPI service and an API-backed web Workbench. It does not yet have self-contained Windows, macOS, or Linux desktop installers. Independent scientific validation is also incomplete.

**Estimated platform progress: 56%.** This is a weighted product-readiness estimate. It is not a code-completion percentage and it is not a scientific-validation result. The scoring method is below.

The product-level scientific gate remains fail-closed. A successful CI workflow does not prove that all required source-backed scientific checks passed. The exact historical CPVS reconstruction is a separate claim-specific workstream. It is excluded from the product progress score and is not being worked in this status cycle.

## Progress measurement

Each subsystem receives a score from 0 to 100:

- 0: no implementation or evidence;
- 25: design or partial contract only;
- 50: partial implementation with some tests;
- 75: implementation exists, but important end-to-end evidence is missing;
- 100: declared acceptance criteria pass with reproducible evidence.

The overall estimate is the weighted sum of the subsystem scores. The weights reflect the target product: a scientist-facing, cross-platform, scientifically validated application.

| Subsystem | Weight | Score | Evidence and remaining gap |
|---|---:|---:|---|
| Scientific core and model | 18% | 85% | Frozen 42-feature v0.2.0 contract, XGBoost baseline, persisted artifact, calibration, conformal and OOD diagnostics, CLI and batch inference. Independent population-level validation remains incomplete. |
| Data acquisition and ingestion | 10% | 55% | Local CSV/Parquet and ALeRCE paths exist. A bounded DR24 light-curve smoke test processed 7/12 objects; 5 failed filter normalization. TAP and AVRO alert ingestion remain open. |
| Product scientific validation | 20% | 40% | Versioned benchmark registry, provenance manifests and fail-closed gate exist. StarEmbed leakage audit is blocked. DR24 feature-engine validation is partial. No independent model-performance claim is established. |
| API and application services | 12% | 80% | FastAPI v1, application services, persisted jobs/results, catalog/report and provenance contracts exist. Full user-path and clean-install acceptance remains open. |
| Workbench and user experience | 12% | 45% | API-backed Workbench and several analysis views exist. Data Manager, complete Object/Source Explorer, integrated Help and full discovery review remain incomplete. |
| Discovery, anomaly and explainability | 8% | 30% | Domain contracts and separate diagnostic channels exist. A validated end-to-end scientific discovery workflow and human review/ranking are not complete. |
| Cross-platform packaging and deployment | 10% | 15% | Python wheel and source distribution are published. No self-contained Windows installer, macOS app, or Linux AppImage has passed clean-machine tests. |
| CI, security and release engineering | 6% | 90% | A recent full CI run passed 645 tests, skipped 10, and reported 9 warnings. CodeQL and dependency audit passed; the audited lock environment reported no known vulnerabilities. Latest PR checks are being rerun after a lint correction. |
| Documentation and operations | 4% | 60% | Architecture, API, roadmap, model and user documentation exist. Several guides still state v1.0.0, the main handbook is dated 2026-10-11, and operational acceptance guides need synchronization. |

**Weighted total: 55.5%, rounded to 56%.**

## Verified release and engineering evidence

### v1.0.1 release

Release [v1.0.1](https://github.com/saeed92m/ztf-classifier/releases/tag/v1.0.1) was published on 2026-10-07. It contains:

- `ztf_classifier-1.0.1-py3-none-any.whl` — SHA-256 `b4ba6342d4973031bfec073c55eb56f592dc4e812a0b77f6f2f142df9786d743`;
- `ztf_classifier-1.0.1.tar.gz` — SHA-256 `da855e526df057db943756cab0286f707711e81fce0c8cb992b6f0b5384d4789`.

This is a Python package release. It is not a desktop installer release.

### Full CI evidence

CI run [41493244584](https://github.com/saeed92m/ztf-classifier/actions/runs/41493244584) completed with all eight jobs successful. The full test suite reported:

- 645 passed;
- 10 skipped;
- 9 warnings;
- 98.59 seconds for the pytest run.

The dependency audit reported no known vulnerabilities for the audited environment. CodeQL, Product Scope Audit and Scientific Validation contract checks passed on the associated PR head. The source-backed scientific jobs were skipped in the ordinary PR event. The 10 skipped tests remain visible; their detailed reasons must be reviewed before a release-readiness claim.

### Frozen scientific baseline

The repository manifests and reproduction report confirm:

- 150 benchmark objects;
- 15 ALeRCE reference classes;
- 10 objects per class;
- 42 frozen features in `final_feature_set_v0.2`;
- XGBoost `baseline_v0.2`;
- historical cutoff 59447.224132.

The reproduced feature dataset and model artifact match the frozen v0.2 reference. ALeRCE labels remain reference/weak labels, not independent astrophysical ground truth.

## Independent BTS → ZTF DR24 recovery pilot

PR [#246](https://github.com/saeed92m/ztf-classifier/pull/246) adds a reproducible BTS snapshot acquisition, a 100-object sample, an official DR24 Objects Table HATS query, an OID multiplicity audit, tests, and a dedicated workflow.

### Source scope

The BTS explorer request uses `subsample=cantrans`, `endpeakmag=19.0`, `quality=y`, and `samprcf=y`. The 10,551-row snapshot is the result of that filtered request. It is not the complete BTS catalogue. The BTS documentation says the sample is not complete for Galactic events and non-transients.

### Initial measured result

Source-backed workflow [41488299913](https://github.com/saeed92m/ztf-classifier/actions/runs/41488299913) processed 100 targets and returned 773 DR24 OID rows within 5 arcseconds.

| Cone radius | Targets with at least one OID | Unmatched targets | Targets with multiple OIDs | Same-filter multiple OIDs |
|---:|---:|---:|---:|---:|
| 1 arcsec | 48/100 | 52 | 33 | 27 |
| 2 arcsec | 78/100 | 22 | 69 | 59 |
| 5 arcsec | 97/100 | 3 | 94 | 88 |

The maximum was 22 OIDs for one BTS coordinate at 5 arcseconds. For that source, only one OID was within 1 arcsecond. Recomputed nearest-match separations for the 97 targets matched within 5 arcseconds had a median of 1.051 arcseconds, a mean of 1.330 arcseconds, a 90th percentile of 3.322 arcseconds, and a maximum of 4.913 arcseconds.

These are positional candidate-recovery results. They do not establish physical identity, cross-match precision/recall, or model accuracy. ZTF objects are partitioned by filter and field/quadrant. Multiple OIDs can therefore be valid catalog records for one astrophysical source. The schema-aware audit now separates same-filter OIDs across field/CCD/quadrant partitions from same-partition multiplicity:

| Radius | Same-filter multi-OID targets | Across partitions | Within the same partition |
|---:|---:|---:|---:|
| 1 arcsec | 27 | 27 | 0 |
| 2 arcsec | 59 | 58 | 15 |
| 5 arcsec | 88 | 81 | 77 |

At 1 arcsec, every same-filter multiple-OID case in this sample spans different partitions. At 5 arcsec, 77 targets have same-filter multiple OIDs within at least one field/CCD/quadrant partition. This is consistent with a wider cone including nearby catalog objects. It is not, by itself, a false-positive classification. The per-match audit contains all 773 OIDs and their recomputed separations. The 773 OIDs are unique across the 97 matched BTS targets; no OID was shared by two BTS targets in this sample.

The 100-object spatial query is complete. The follow-up workflow [41527459598](https://github.com/saeed92m/ztf-classifier/actions/runs/41527459598) has passed its 17 contract tests and is running the indexed `objectid` lookup against DR24 Lightcurves HATS for the recovered OIDs. Its availability artifact is not yet verified. An Objects Table match alone does not prove that a time series is available.

### Updated schema-aware execution

The updated query records the DR24 schema columns and hash, code revision, Python/LSDB/s3fs versions, and available field/quadrant provenance. The latest source-backed push run is [41525750067](https://github.com/saeed92m/ztf-classifier/actions/runs/41525750067). At the time of this report, its DR24 query step is still running. Its new artifact has not yet been inspected. Do not replace the initial measured counts with unverified estimates.

The independent recovery contract job passed 14 tests on the same push run. A later test-style correction is awaiting the latest PR CI checks.

## Scientific validation blockers

### StarEmbed

Issue [#210](https://github.com/saeed92m/ztf-classifier/issues/210) records a fail-closed source audit:

- one duplicate `sourceid` within the train split;
- one object-ID overlap between train and test.

StarEmbed-derived model metrics are not independent evaluation evidence until the implicated records, upstream split semantics, and object-level grouping are resolved. No split is changed and no record is silently removed.

### Real DR24 light-curve processing

Issue [#188](https://github.com/saeed92m/ztf-classifier/issues/188) records a bounded source-backed smoke test. I inspected the raw responses in artifact `12691138935`:

- 12 candidate OIDs came from a pinned DR24 subset;
- 5 failed OIDs contain only `filtercode=zi` rows. The g/r feature contract correctly excludes them;
- 7 feature-engine executions returned partial vectors. All 7 were single-band: 4 r-only and 3 g-only;
- each partial vector had 19 finite values and 23 NaN values out of 42;
- 0/12 had both g and r observations;
- model inference was not run.

The normalizer is not the root cause. The smoke sample is selected per OID, but DR24 OIDs are filter/field/quadrant-specific. The feature engine needs an astrophysical source group with constituent OIDs across filters. The existing `ngoodobsrel >= 30` criterion does not guarantee g/r coverage. Issue #188 now records this root-cause diagnosis and the required source-group design. This is an ingestion/feature-engine smoke test, not model validation.

### 100-object operational test

Issue [#222](https://github.com/saeed92m/ztf-classifier/issues/222) remains open. Its required 100-object run must account for every selected object and record ingestion, QC, features, inference, uncertainty, errors and provenance. The earlier 100-object BTS coordinate sample is not a substitute for this test.

### Product work still open

- [#158](https://github.com/saeed92m/ztf-classifier/issues/158): complete cross-platform desktop product.
- [#196](https://github.com/saeed92m/ztf-classifier/issues/196): strict JSON serialization for diagnostic artifacts.
- [#216](https://github.com/saeed92m/ztf-classifier/issues/216): TAP acquisition backend.
- [#217](https://github.com/saeed92m/ztf-classifier/issues/217): AVRO alert ingestion and cutout preservation.
- [#218](https://github.com/saeed92m/ztf-classifier/issues/218): phase-fold visualization.

## CPVS boundary

The exact historical CPVS reconstruction remains a separate external-reproduction claim tracked by [Issue #170](https://github.com/saeed92m/ztf-classifier/issues/170). It is not part of the product progress score in this report. No CPVS investigation or code change was performed in this status cycle.

## Immediate next actions

1. Inspect the indexed DR24 Lightcurves HATS result for the 773 recovered OIDs. Record missing rows, filter IDs and epoch counts.
2. Design and test astrophysical source grouping across filter/field/quadrant OIDs. Do not change the frozen 42-feature schema.
3. Build combined g/r observation groups with complete OID provenance and explicit ambiguity handling.
4. Re-run feature generation on grouped sources. Require g/r coverage and report valid epochs before inference.
5. Review the latest PR CI after the new Lightcurves tests. Require all checks to complete on the current PR head.
6. Resolve the StarEmbed duplicate/overlap evidence before using its metrics.
7. Complete the 100-object operational test as a separate end-to-end application test.
8. Finish desktop workflows, help, clean-machine installation and Windows/macOS/Linux packaging.
9. Synchronize README, handbook, roadmap, installation guide, user guide and model card. Keep all unresolved evidence visible.

## Decision

**The v1.0.1 software package is released. The broader platform is in active development at an estimated 56% readiness. Scientific product acceptance and cross-platform desktop acceptance are not complete.**

No release, merge, or scientific-validation claim is authorized by this report.
