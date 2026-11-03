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

**Estimated platform progress: 58%.** This is a weighted product-readiness estimate. It is not a code-completion percentage and it is not a scientific-validation result. The scoring method is below.

The product-level scientific gate remains fail-closed. A successful CI workflow does not prove that all required source-backed scientific checks passed. The exact historical CPVS reconstruction is a separate claim-specific workstream. It is excluded from the product progress score and is not being worked in this status cycle.

## Progress measurement

Each subsystem receives a score from 0 to 100:

- 0: no implementation or evidence;
- 25: design or partial contract only;
- 50: partial implementation with some tests;
- 75: implementation covers the main path, but important end-to-end evidence is missing;
- 100: declared acceptance criteria pass with reproducible evidence.

Scores between these anchors are interpolated from the number and importance of verified sub-criteria. They are engineering estimates. They are not measured scientific metrics.

The overall estimate is the weighted sum of the subsystem scores. The weights reflect the target product: a scientist-facing, cross-platform, scientifically validated application.

| Subsystem | Weight | Score | Evidence and remaining gap |
|---|---:|---:|---|
| Scientific core and model | 18% | 85% | Frozen 42-feature v0.2.0 contract, XGBoost baseline, persisted artifact, calibration, conformal and OOD diagnostics, CLI and batch inference. Independent population-level validation remains incomplete. |
| Data acquisition and ingestion | 10% | 65% | BTS snapshot acquisition, DR24 Objects HATS spatial queries, and indexed Lightcurves HATS availability checks now run with manifests and hashes. Source grouping, quality-aware ingestion, TAP and AVRO alert ingestion remain open. |
| Product scientific validation | 20% | 45% | Fail-closed gate and benchmark registry exist. Independent BTS→DR24 recovery and Lightcurves availability are measured on 100 targets. StarEmbed leakage and DR24 source grouping/photometry-quality validation remain blockers. No independent model-performance claim is established. |
| API and application services | 12% | 80% | FastAPI v1, application services, persisted jobs/results, catalog/report and provenance contracts exist. Full user-path and clean-install acceptance remains open. |
| Workbench and user experience | 12% | 45% | API-backed Workbench and several analysis views exist. Data Manager, complete Object/Source Explorer, integrated Help and full discovery review remain incomplete. |
| Discovery, anomaly and explainability | 8% | 30% | Domain contracts and separate diagnostic channels exist. A validated end-to-end scientific discovery workflow and human review/ranking are not complete. |
| Cross-platform packaging and deployment | 10% | 15% | Python wheel and source distribution are published. No self-contained Windows installer, macOS app, or Linux AppImage has passed clean-machine tests. |
| CI, security and release engineering | 6% | 90% | PR #246 current-head CI, CodeQL, Product Scope Audit, and Scientific Validation contract checks passed. Full CI reported 650 passed, 10 skipped, 9 warnings, and 83% coverage. PR #247 currently fails its lifecycle gate because its documentation-only changes lack a cycle record; this report update adds one. |
| Documentation and operations | 4% | 65% | Installation, user guide, model card, roadmap and status report are being aligned with v1.0.1 and the frozen v0.2.0 baseline. The main handbook and operational acceptance guides still need a full synchronization pass. |

**Weighted total: 57.7%, rounded to 58%.**

## Verified release and engineering evidence

### v1.0.1 release

Release [v1.0.1](https://github.com/saeed92m/ztf-classifier/releases/tag/v1.0.1) was published on 2026-10-07. It contains:

- `ztf_classifier-1.0.1-py3-none-any.whl` — SHA-256 `b4ba6342d4973031bfec073c55eb56f592dc4e812a0b77f6f2f142df9786d743`;
- `ztf_classifier-1.0.1.tar.gz` — SHA-256 `da855e526df057db943756cab0286f707711e81fce0c8cb992b6f0b5384d4789`.

This is a Python package release. It is not a desktop installer release.

### Full CI evidence

Current PR-head CI run [41528271371](https://github.com/saeed92m/ztf-classifier/actions/runs/41528271371) completed successfully:

- 650 passed;
- 10 skipped;
- 9 warnings;
- 83% total test coverage.

Format, lint, cumulative lifecycle validation, the test suite, and runtime smoke tests passed. The run completed with success. This is engineering evidence, not scientific product acceptance.

The 10 skipped tests are gated on optional source-backed inputs. The relevant test modules require raw ZTF data roots, frozen diagnostic feature inputs, or legacy production-model test artifacts. The CI log does not print a per-test skip list. These tests are not counted as passed scientific validation.

The 9 warnings include a Starlette/FastAPI test-client deprecation and numerical warnings from NumPy, Astropy Lomb–Scargle, and a single-label scikit-learn diagnostic. They did not fail the test suite, but they need review.

Earlier full CI run 41493244584 completed with all eight jobs successful. Its dependency audit reported no known vulnerabilities for the audited environment. CodeQL, Product Scope Audit and Scientific Validation contract checks passed on the associated PR head. The source-backed scientific jobs were skipped in the ordinary PR event.

## Frozen scientific baseline

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

The source-backed follow-up workflow [41527459598](https://github.com/saeed92m/ztf-classifier/actions/runs/41527459598) completed successfully. Its indexed `objectid` lookup queried all 773 recovered OIDs in the official DR24 Lightcurves HATS catalog. The final artifact was downloaded and inspected (artifact ID `13184608092`; ZIP SHA-256 `84548734b39fa5e1639e6b06ed54d0630c23603b4c6a803b3e7c0935966de7e3`).

| Lightcurves availability metric | Result |
|---|---:|
| Objects Table OIDs queried | 773 |
| OIDs with a Lightcurves row | 714 |
| OIDs without a Lightcurves row | 59 |
| Filter metadata pairs consistent | 773/773 |
| BTS targets with at least one g and one r Lightcurves OID | 87/100 |
| BTS targets with at least one Lightcurves OID | 96/100 |
| BTS targets with all recovered OIDs present in Lightcurves | 60/100 |

Missing Lightcurves rows by Objects Table filter: `zg` 25, `zr` 23, and `zi` 11. The 714 found OIDs have 1–1,850 epochs (median 56.5). Row presence does not certify clean epochs, cadence, or scientific usability. The artifact records the Lightcurves HATS 13-column schema, `objectid` index, runtime versions, and input/output hashes.

### Updated schema-aware execution

The schema-aware source-backed run [41525750067](https://github.com/saeed92m/ztf-classifier/actions/runs/41525750067) completed 100/100 targets and returned 773 OID rows. The later run [41527459598](https://github.com/saeed92m/ztf-classifier/actions/runs/41527459598) repeated the source-backed query and added the Lightcurves index check. The latest artifact is the evidence source for the availability counts above.

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

1. Audit photometric quality flags, valid epochs, cadence, and time coverage for a stratified sample of the 714 OIDs with Lightcurves rows.
2. Design and test astrophysical source grouping across filter/field/quadrant OIDs. Do not change the frozen 42-feature schema.
3. Build combined g/r observation groups with complete OID provenance and explicit ambiguity handling.
4. Re-run feature generation on grouped sources. Require g/r coverage and report valid epochs before inference.
5. Resolve the StarEmbed duplicate/overlap evidence before using its metrics.
6. Complete the 100-object operational test as a separate end-to-end application test.
7. Finish desktop workflows, help, clean-machine installation and Windows/macOS/Linux packaging.
8. Synchronize the main handbook and operational acceptance guides. Keep all unresolved evidence visible.

## Decision

**The v1.0.1 software package is released. The broader platform is in active development at an estimated 56% readiness. Scientific product acceptance and cross-platform desktop acceptance are not complete.**

No release, merge, or scientific-validation claim is authorized by this report.


## Cosmic Intelligence Network (CIN) — new proposed workstream

On 2026-11-03, the canonical user-supplied source **ZTF CLASSIFIER — COSMIC INTELLIGENCE NETWORK**, Document ID ZTF-CIN-ARCH-001, version 1.0.0, was read in full and translated into a proposed repository architecture workstream.

- GitHub tracking: [Issue #251](https://github.com/saeed92m/ztf-classifier/issues/251).
- Proposed subsystem: independent, optional human-in-the-loop annotation, quality control, consensus, expert review, active learning and research dataset infrastructure.
- Proposed initial pilot: LC-01 light-curve morphology assessment, with independent controls, blind presentation where practical, repeated assessments, abstention, preserved disagreement and a predeclared evaluation plan.
- Architecture companion, data/API contracts, pilot protocol and staged roadmap are being proposed in a dedicated documentation branch/PR.
- Current repository inspection found reusable observation, catalog-context, discovery-candidate, human-review, model-provenance, API and Workbench boundaries. It did not establish a complete CIN task lifecycle, immutable contribution store, consensus pipeline, active-learning scheduler or human-annotation dataset release system.

**Implementation status: NOT IMPLEMENTED.** This documentation and planning work does not increase the 57.7% platform-readiness estimate and does not establish scientific effectiveness. No human data were collected, no pilot was run, no model was retrained, and no production data or baseline artifacts were changed.

CIN must remain independent of ZTF Classifier and optional at runtime. AOIC is a separate proposed identity subsystem; CIN must preserve original source IDs and unresolved identity until canonical identity contracts are accepted. The v0.2.0 scientific baseline, v1.0.1 software release, benchmark, feature schema and release gates remain unchanged.

CPVS investigation is outside this CIN workstream.
