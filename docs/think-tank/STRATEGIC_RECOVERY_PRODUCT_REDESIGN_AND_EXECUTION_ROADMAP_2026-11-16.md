# ZTF Classifier — Strategic Recovery, Independent Audit & Product Redesign

**Document ID:** ZTF-TT-STRATEGIC-RECOVERY-2026-11-16  
**Review date:** 2026-11-16  
**Repository snapshot:** main at f681408fae8d8062dd72ff74791872c1590f6ee8  
**Product owner:** Founder / Project Owner  
**Review mode:** 16-role structured review, cross-examination, architecture workshop, data strategy, product strategy and Red Team  
**Status:** Draft for owner review; documentation proposal only  
**Protected scientific baseline:** v0.2.0  
**Software release recorded by repository:** v1.0.1  
**Implementation scope of this document:** No production code, model, dataset, threshold, release, or protected branch was changed.

> The 16 seats in this review are simulated specialist perspectives coordinated by one AI system. They are not 16 independent human experts, external peer reviewers, or a substitute for scientific collaboration. Their dissent is recorded as a structured design review, not as independent human validation.

---

# 1. Executive Summary

## 1.1 Strategic conclusion

ZTF Classifier should evolve into an **Astronomical Data Analysis, Intelligence & Discovery Platform**. ZTF remains the first operational survey and the first validated scientific use case. It is not the product's permanent boundary.

The correct strategy has two connected but separate delivery tracks:

1. **Park MVP:** deliver a bounded, usable, reproducible ZTF DR24 light-curve analysis product. Keep this scope small enough to demonstrate and validate.
2. **Long-term platform:** build common data, provenance, identity, analysis, and workflow infrastructure that can support additional surveys and distinct astronomical modalities through separate adapters and pipelines.

Do not implement all surveys and modalities in the MVP. Do not design the MVP so narrowly that later sources require a rewrite.

## 1.2 Current readiness

| Area | Verified disposition |
|---|---|
| Scientific research foundation | Partial. A frozen benchmark and feature contract are documented. The original production model artifact is not currently recovered. |
| Python software | Implemented. CLI, API, analysis jobs, result persistence, catalog export and report generation exist in the repository. |
| User-facing workbench | Implemented as a browser-based Workbench served by the API. |
| Self-contained desktop application | Not implemented or verified. |
| ZTF DR24 ingestion | Partial. A raw-preserving, bounded HATS adapter exists. It is not yet the default normalized observation source for ordinary analysis. |
| Multi-survey support | Proposed and partially explored. No validated multi-survey product workflow is established. |
| Multi-modality support | Proposed. Image and spectroscopy pipelines are not established as supported product capabilities. |
| Source identity / cross-match | Partial domain contracts exist on a Draft PR. No validated production association engine or persistent identity ledger exists. |
| Scientific discovery | Partial foundations. Classification, calibration, conformal and OOD contracts exist. OOD is not scientific anomaly evidence. |
| CIN | Architecture proposal only. Runtime implementation is not authorized by its existing project record. |
| Commercial readiness | Not demonstrated. Customer, pricing, licensing and support assumptions need validation. |

The repository is therefore more than a collection of scripts: it has a Python package, API, job/result services and a browser Workbench. It is not yet the complete desktop, multi-source, multi-modality discovery product described by the long-term vision.

## 1.3 Main decisions recommended

1. Keep v0.2.0 immutable.
2. Recover and authenticate the original baseline_v0.2 model artifact before claiming production model availability.
3. Make source selection explicit. Never silently switch from DR24 to ALeRCE.
4. Complete one DR24 end-to-end path before expanding source count.
5. Establish astrophysical source identity separately from survey-native object IDs.
6. Adopt a modular monolith with versioned contracts and modality-specific pipelines.
7. Add Gaia DR3 and TESS as the first external scientific validation candidates after the ZTF path is stable.
8. Treat ATLAS and ASAS-SN as external time-series adapters after their access and quality constraints are tested.
9. Use Pan-STARRS, WISE/NEOWISE, SDSS, SIMBAD and VizieR as catalog/context or modality-specific sources, not as interchangeable light-curve feeds.
10. Treat Rubin as a future adapter with data-rights-aware access. Do not assume all Rubin data products are public.
11. Keep CIN optional and separate.
12. Do not claim scientific discovery from an anomaly score alone.

## 1.4 Priority distinction

CPVS is the highest-priority unresolved scientific research problem. It is not the critical path for the DR24-first Park product. Keep the CPVS investigation open and independent. Continue DR24 product engineering without using CPVS as a release dependency.

---

# 2. Original Vision vs Current State

## 2.1 Original project purpose

The supplied Park presentation and project dossier define a six-month prototype centered on:

- Public ZTF DR24 data.
- Variable and transient objects.
- Light-curve retrieval and preprocessing.
- Feature engineering.
- CPU-first classification.
- Class probabilities and uncertainty.
- Explicit abstention when the system is uncertain.
- Anomaly flags.
- A catalog, dashboard, technical report and reproducible research package.

The project dossier also identifies a 90-day execution checkpoint. The six-month plan assumes acceptance, team capacity, data access and resources. It is not evidence that these milestones have been completed.

## 2.2 Current software state

The current main branch contains:

- A Python package with CLI entry points.
- A FastAPI service.
- A browser-based Scientific Analysis Workbench.
- Model registry and inference interfaces.
- A 42-feature native v0.2 feature backend.
- Application services for analysis, jobs, results, catalogs and reports.
- A bounded raw DR24 HATS acquisition adapter.
- A diagnostic-only DR24 epoch quality assessment.
- A local CSV/Parquet import service with explicit size and schema constraints.
- Automated tests and CI workflows.

The standard ObservationService still constructs AlerceDetectionBackend for normalized observations. The DR24 adapter returns source-native data and explicitly does not convert HMJD, apply a production catflags policy, correct photometry, merge OIDs or feed model inference. This separation is scientifically prudent, but it means the complete DR24 analysis path is not yet connected.

## 2.3 Vision gaps

| Target capability | Current evidence | Gap |
|---|---|---|
| Local desktop application | Browser Workbench exists | No verified Windows/macOS/Linux self-contained installer |
| User imports arbitrary astronomy data | CSV/Parquet import contract exists | No general FITS, AVRO, image or spectrum ingestion contract |
| DR24 end-to-end inference | Raw DR24 route exists | No approved native-to-normalized DR24 model-input contract |
| Multi-survey comparison | Research and issue records exist | No validated cross-survey evaluation product |
| Physical source identity | Draft domain contracts exist | No production probabilistic cross-match or persistent identity ledger |
| Image analysis | Product vision only | No validated image pipeline |
| Spectroscopy | Product vision only | No validated spectral pipeline |
| Scientific anomaly detection | Separate design requirement | Must not be inferred from OOD or classifier confidence |
| Reproducible discovery workflow | Jobs, results, provenance foundations exist | Need complete end-to-end run manifest and source-to-report lineage across supported sources |

## 2.4 Important document conflicts

| Source statement | Repository evidence | Required reconciliation |
|---|---|---|
| Park presentation describes zero data and observation cost | No telescope purchase is required, but storage, internet, compute, staff and support still cost money | Say “no telescope acquisition or proprietary observation cost for the public-data MVP”; do not say total project cost is zero |
| Park presentation describes near-zero infrastructure risk | The application depends on remote services, large downloads, storage, source availability and network access | Quantify operational risk and recovery plans |
| Six-month prototype roadmap | Issue #158 also defines 30/60/90-day checkpoints | Preserve six months as the broader target; use 30/60/90 as gated milestones, not guaranteed delivery |
| README describes persisted production model artifacts | Issue #282 says the original production artifact is absent from the repository, release assets and accessible remote storage checked | Mark model availability UNKNOWN until local recovery and independent authentication |
| README says artifact schema 1.1 is backward-compatible with 1.0 | The frozen original artifact is expected to be schema 1.0; the 1.1 lab-smoke artifact is not a valid replacement | Document artifact compatibility separately from artifact identity |
| README and Handbook report v1.0.1; Model Card says software v1.0.0 | Main branch has inconsistent software version metadata | Synchronize Model Card, README, Handbook and release records |
| Product is described as cross-platform | pyproject requires Python >=3.11,<3.12 and package classifiers do not establish tested Windows/macOS installers | Treat OS support as a target until clean-OS install tests pass |
| Public repository, Proprietary project license | pyproject declares Proprietary; no LICENSE file was found on main | Owner must choose and document the source-code license and contribution policy |
| Product vision lists multi-source and multi-modality | Main implementation is ZTF-centered, with DR24 raw retrieval separate from ordinary analysis | Label each source and modality as proposed, partial, implemented or validated |

---

# 3. Complete Project Audit

## 3.1 Source inventory reviewed

The following supplied files were opened and read:

1. سند پروژه نسخه نهایی.pdf
2. ارائه پارک علم و فناوری نسخه نهایی.pdf
3. ZTF CLASSIFIER — COSMIC INTELLIGENCE NETWORK.txt
4. ایده داده‌سازی جمعی.txt
5. تعیین اعضای اتاق فکر.txt
6. Branch · ... گزارش وضعیت پروژه.txt
7. تایید سیاست همگرایی پروژه.txt

The crowd-data idea file contains the CIN architecture proposal. It is not a separate implemented subsystem. The CPVS status handoff is a CPVS-specific research record and must not be treated as the whole product roadmap.

Repository documents inspected on main include README, pyproject, requirements.lock, CHANGELOG, Data Card, Model Card, API v1 contract, Handbook v2.8, product architecture index and product expansion record. A draft roadmap and master defect register were also read from Draft PR #281. They are not merged main-branch policy.

## 3.2 Repository snapshot

- Repository: saeed92m/ztf-classifier
- Visibility: public
- Default branch: main
- Observed main HEAD: f681408fae8d8062dd72ff74791872c1590f6ee8
- Repository permission in connected GitHub context: admin/push available
- No production or protected-branch write was performed during this audit.

## 3.3 Open pull requests and current evidence

| PR | Scope | Current state | Latest relevant evidence |
|---|---|---|---|
| #291 | Session 09 documentation | Draft, open | Test, runtime smoke and package build passed; Dependency Audit failed because the main-based branch still resolves soupsieve 2.10 |
| #290 | StarEmbed independent input audit | Draft, open | Current associated Scientific Validation job passed its contract; source-backed acquisition/evidence jobs were skipped. Prior test evidence is not a current full-head scientific result |
| #289 | Soup Sieve security update | Draft, open | All eight jobs in run 43536652404 passed; change is not merged into main |
| #285 | CPVS raw SNR and lineage research | Draft, open | CI, CodeQL, Scientific Validation contract and Product Scope Audit passed; separate 100-object raw lineage job failed CRC32 |
| #284 | Bounded DR24/Zubercal acceptance workflows | Draft, open | Recorded CI, CodeQL, Product Scope and Scientific Validation runs passed; does not establish full application integration |
| #283 | Minimum source identity contracts | Draft, open | Domain contract and tests only; no production matcher or identity ledger |

No PR was merged as part of this audit. No release was published.

## 3.4 Current CI findings

### PR #291

The latest CI run was 43818873284.

- Format Check: success.
- Lint: success.
- Cumulative Lifecycle Gate: success.
- Test Suite: success.
- Runtime Smoke Tests: success.
- Build & Verify Package: success.
- Dependency Audit: failure.
- CI Gate: failure.

The dependency audit found three vulnerabilities in soupsieve 2.10. The security fix exists on PR #289, but main has not received it. This is a real dependency-state blocker for a main-based documentation PR, not a failure of the scientific tests.

### PR #285 / CPVS

The 100-object lineage workflow run 43818485826 failed in the raw archive scan:

- Python zipfile raised BadZipFile.
- The failing archive member was ztf2g.
- The error was Bad CRC-32 for the member.
- The trace did not produce accepted coordinate/epoch evidence.

This establishes an archive-integrity failure in that execution. It does not yet prove whether the origin is the remote archive, transfer, cache, or workflow artifact handling. Do not suppress CRC checking. Re-download to a clean temporary location, verify publisher checksums where available, compute SHA-256, validate ZIP member CRC and record exact bytes before retrying the trace.

### PR #290 / StarEmbed

Earlier test evidence reported 712 passed, 13 skipped and zero failures. That result is tied to its own run and is not proof that the current PR head has completed all acquisition and scientific evidence jobs. The current associated source-backed workflow reports several jobs as skipped. The independent benchmark remains unaccepted because source identity and train/test overlap require resolution.

## 3.5 Scientific baseline audit

Documented baseline:

- 150 objects.
- 15 ALeRCE reference classes.
- 10 objects per class.
- 42 frozen features.
- XGBoost baseline_v0.2.
- Historical cutoff MJD 59447.224132.
- Frozen class order.
- Schema and diagnostic compatibility requirements.

The Data Card confirms the benchmark is small, balanced and weakly labelled. ALeRCE labels are not independent astrophysical ground truth.

The original model artifact remains UNKNOWN. Issue #282 records that the repository, release assets, retained CI artifact, Dropbox and Notion searches did not recover the original artifact. The 1.1 lab-smoke artifact is not a substitute. Seven production inference tests were skipped in the cited CI run because the original artifact or shared model inputs were unavailable.

**Audit rule:** do not call the baseline operational until the original artifact is recovered and independently authenticated.

## 3.6 Data and source audit

The DR24 adapter on main:

- Reads the HATS Lightcurves product.
- Limits a request to 10 OIDs.
- Preserves source-native OID, filter, field, readout channel, coordinates, epoch values and payload hash.
- Does not convert HMJD to MJD.
- Does not apply an approved production quality policy.
- Does not merge OIDs.
- Does not feed the model.

The DR24 quality assessment is explicitly diagnostic, not production-approved.

The current ordinary ObservationService constructs AlerceDetectionBackend. The DR24 raw endpoint is separate. This is a deliberate safe boundary, but it blocks the Park MVP's intended DR24-first analysis flow.

## 3.7 Identity audit

ZTF OID is a survey-native identifier, not a guaranteed physical-source identifier. The DR24 HATS documentation states that objects are defined per filter, field and quadrant. One astrophysical source can have multiple OIDs.

PR #283 adds a minimum identity-domain contract on a Draft branch. It does not implement:

- Probabilistic cross-match.
- Proper-motion and epoch propagation.
- Persistent association ledger.
- Reversible merge/split.
- Independent adjudicated identity samples.
- Validated completeness and reliability.

Do not merge OIDs because they are close on the sky alone.

## 3.8 Product audit

The current product is a Python package, CLI, FastAPI API, job/result services and browser Workbench. It is not yet a complete desktop product.

The browser Workbench includes overview, observations, raw DR24 Explorer, features, classification, uncertainty/OOD, provenance, batch jobs, catalog, reports and scientific validation views. The user-facing desktop installers remain tracked as a future product task in Issue #158.

The local import service accepts CSV and Parquet under explicit limits. It does not imply general FITS image, AVRO alert or spectral file support.

---

# 4. Critical Findings

| ID | Finding | Severity | Evidence | Required action |
|---|---|---|---|---|
| F-01 | Original production model artifact unavailable | Critical / P0 | Issue #282 and skipped inference tests | Recover original bytes and independently authenticate hashes |
| F-02 | DR24 is not the default normalized observation source | Critical / P0 | ObservationService uses AlerceDetectionBackend | Add explicit source selection and DR24 normalization contract |
| F-03 | DR24 time/photometry conversion is not approved | Critical / P0 | Adapter preserves HMJD and native values | Define and validate time, photometry, error and color rules |
| F-04 | OID does not represent physical identity | Critical / P0 | Official HATS semantics and incomplete PR #283 | Implement probabilistic AOIC and reversible association ledger |
| F-05 | Current product lacks desktop packaging | High / P1 | API and browser Workbench; no verified installer | Complete desktop packaging after application workflows stabilize |
| F-06 | Benchmark labels are weak reference labels | High / P1 | Data Card and Model Card | Obtain independent references and report label limitations |
| F-07 | StarEmbed source/split overlap risk | High / P1 | Historical issue #210 / PR #211 | Full identity and split audit before benchmark use |
| F-08 | Multi-source validation is incomplete | High / P1 | Issue #188 partial smoke; inference not run | Establish independent, source-pinned validation |
| F-09 | Multi-modality capability is a proposal | High / P2 | No image/spectrum pipeline acceptance | Build separate modality contracts and pilots |
| F-10 | Security fix not merged into main | High / P0 | PR #289 passes; PR #291 dependency audit fails | Review and merge security fix under owner policy |
| F-11 | Source-code licensing is unresolved | High / P1 | Proprietary metadata, no LICENSE file found | Owner/legal decision on license and contribution model |
| F-12 | Documentation version drift | Medium / P1 | Model Card v1.0.0 vs README/Handbook v1.0.1 | Establish one canonical release metadata source |
| F-13 | Rubin access assumptions may be wrong | High / P2 | Current Rubin Data Policy | Implement access-tier and rights-aware adapters |
| F-14 | CPVS archive integrity blocks raw trace | High research blocker | Run 43818485826 CRC failure | Verify clean source download and archive integrity |
| F-15 | “Zero cost” language overstates project economics | Medium / P1 | Park presentation vs real storage/network/staff costs | Reword and quantify actual operating costs |

---

# 5. Target Product Definition

## 5.1 Product statement

A local-first scientific software platform that allows a researcher to discover, import, validate, inspect, analyze, compare and prioritize astronomical data from supported surveys and modalities. Every result must retain its source, identity, units, time system, quality decisions, method, model and provenance.

The platform supports research. It does not replace scientific judgement or independently confirm a discovery.

## 5.2 Primary users

1. Astronomer / researcher: builds a project, selects data, runs scientific analysis and exports a reproducible report.
2. Time-domain analyst: inspects light curves, transient evolution, variability and cross-survey matches.
3. Data scientist: imports compatible data, configures features, models and validation.
4. Research group / institute: runs repeatable workflows on local or institutional infrastructure.
5. Expert reviewer: reviews candidate evidence and annotations.
6. Educator / student: learns data analysis using bounded public examples.

## 5.3 Core user value

- One project workspace for supported astronomical data.
- Clear data-quality and identity diagnostics before analysis.
- Modality-specific analysis, not one generic model.
- Reproducible results and transparent uncertainty.
- Candidate ranking that exposes evidence and limitations.
- Comparison across sources without silently mixing units, time systems or taxonomies.

## 5.4 Product boundaries

The platform must distinguish:

- Detection reality / artifact screening.
- Physical source association.
- Object classification.
- Probability calibration.
- Conformal prediction.
- Data adequacy.
- OOD detection.
- Scientific anomaly analysis.
- Novelty and candidate ranking.
- Expert confirmation.

These outputs have different scientific meanings. They must not be collapsed into one score.

---

# 6. Park MVP Definition

## 6.1 MVP objective

Deliver a credible, usable ZTF DR24 time-series analysis demonstration. Do not attempt a complete all-survey or all-modality platform in the Park MVP.

The project dossier targets a labelled subset of at least 100,000 light curves. Treat this as a delivery target that requires a source manifest, label semantics, eligibility rules and reproducible acquisition. It is not an existing achievement.

## 6.2 Required MVP features

1. Explicit source selection: DR24 HATS or ALeRCE reference source.
2. Bounded object lookup and batch retrieval.
3. Source-native raw data preservation.
4. Object/filter/field/rcid identity display.
5. Time-system and photometry metadata display.
6. Versioned quality assessment with per-epoch reasons.
7. Explicit missing-data and eligibility reporting.
8. Feature generation only after a validated DR24 normalization contract.
9. Baseline model recovery and verified inference.
10. Calibrated probabilities only if calibration evidence is valid for the selected input domain.
11. Abstention and unknown state.
12. OOD output kept separate from scientific anomaly evidence.
13. Object Explorer with light curve, feature, model and provenance views.
14. API and browser Workbench.
15. Deterministic CSV/Parquet catalog and report export.
16. Machine-readable run manifest and offline replay.
17. Reproducible guided demo for 5–10, then 30–50 confirmed astrophysical sources.
18. A separate path to the 100,000-light-curve Park dataset target.

## 6.3 Explicit MVP exclusions

- Full Rubin integration.
- Full public CIN network.
- General-purpose image classification.
- General-purpose spectroscopy.
- Multi-messenger discovery.
- Automatic model retraining from user feedback.
- Full archive download.
- Microservices.
- GPU dependence.
- Claims of novel astrophysical discovery.

## 6.4 MVP acceptance gate

A non-developer researcher must be able to select DR24, retrieve a supported source, inspect native observations and QC, run the validated analysis path, see model and uncertainty evidence, export a report and reproduce the result from a run manifest.

A successful raw-data display alone does not satisfy this gate.

---

# 7. Multi-Source Data Strategy

The following priorities are recommendations, not claims of implemented adapters or formal partnerships.

| Source | Main data and format | Scientific role | Adapter / tests | Priority |
|---|---|---|---|---|
| ZTF DR24 | HATS/Parquet light curves and object table; FITS images through archive services | Primary optical time-domain source | HATS query, native HMJD, filter/field/rcid identity, flags, source hashes, lazy retrieval | P0 |
| ALeRCE | Broker classifications, features and light-curve access | Historical reference labels and live comparison | Separate reference adapter; preserve label provenance and broker version | P0 reference lane |
| Gaia DR3 | Astrometry, photometry, spectra and selected variable-source epoch time series; archive tables and DataLink | Astrometric context, variable-star reference and association | TAP/DataLink adapter; source_id, epoch, TCB, covariance, quality and release metadata | P1 |
| TESS / MAST | FITS light-curve files, target pixel files and full-frame images | Space-based photometry and independent time-series validation | MAST search/download adapter; TIC ID, sector, cadence, quality flags, FITS HDU schema | P1 |
| ATLAS | c/o-band forced photometry, web form and API | External ground-based time-series comparison | Authenticated service adapter; coordinate, request token, filter, flux/magnitude, limits and retrieval policy | P1 |
| ASAS-SN Sky Patrol | Public light curves via pyasassn/API; CSV/Parquet client output | Long-baseline bright-source time series | Sky Patrol adapter; target catalog, blend/crowding flags, filter and client version | P1 |
| Pan-STARRS DR2 | Mean, stack, detection and forced-mean catalogs via MAST API; images | Optical catalog context and cross-match | Catalog adapter; filter, epoch semantics, quality flags and coverage | P2 |
| WISE / NEOWISE | AllWISE catalog, NEOWISE single-exposure catalogs and FITS images via IRSA | Infrared colors and time-domain context | IRSA TAP/Gator and image adapter; W1–W4, epochs, saturation and confusion | P2 |
| SDSS | Optical spectra, imaging, catalogs and FITS files; SkyServer/CAS/SAS | Spectroscopic reference and image context | Spectral/catalog adapters; plate-MJD-fiber identity, wavelength, flux, inverse variance, masks | P2 |
| SIMBAD | Object identifiers, types, aliases and bibliography via TAP | Object context and name resolution | Catalog context adapter; release/ingestion timestamp, alias provenance and service availability | P2 |
| VizieR | Published catalog tables, spectra, time-series and images via TAP/ObsTAP | Curated scientific reference data | Catalog registry and query adapter; table metadata, citations, version and license | P2 |
| Rubin / LSST | Public alert stream and selected public products; access rights differ by product | Future scale and alert-stream validation | Rights-aware alert/catalog adapter; data rights, public/proprietary status, schema version and rate limits | P3 |

## 7.1 Source-specific constraints

### ZTF DR24

The IRSA HATS product provides one row per ZTF object with a nested light curve. Important fields include objectid, filterid, fieldid, rcid, objra, objdec, nepochs and nested hmjd, mag, magerr, clrcoeff and catflags.

The source-native time column is HMJD, defined in the DR24 release notes as HJD minus 2,400,000.5. Do not silently treat it as MJD or BJD. The native magnitude system and color correction must be handled using the release documentation.

### Gaia DR3

Gaia DR3 includes astrometry and broad-band photometry for a very large source population. Its variable-source time-series products are not a universal time series for every Gaia source. Epoch photometry is available for a defined subset through variability tables and DataLink. Preserve Gaia source_id, reference epoch, coordinate uncertainty and TCB time semantics.

### TESS

TESS light curves and target pixel files are FITS products. A target observed in several sectors can have multiple files. Preserve sector, cadence, product type, pipeline version, quality flags and target identity. Do not concatenate sectors without a documented detrending and gap-handling policy.

### ATLAS

The forced-photometry service is publicly accessible but described as experimental. Its server requires registration/token access. Large-volume requests are discouraged without contacting the service operators. Begin with small, user-authorized samples.

### ASAS-SN

The Sky Patrol client supports catalog queries, cone searches and light-curve downloads. The published documentation warns that blending and crowding can affect photometry. The client/service has its own access and request requirements. Preserve the input catalog and target ID.

### Pan-STARRS

Pan-STARRS DR2 offers mean, stack, detection and forced-mean catalog products through MAST. It is useful for optical catalog context and image data. It is not a general replacement for ZTF or TESS time-series data.

### WISE / NEOWISE

Use IRSA catalog and image interfaces. AllWISE is primarily catalog context; NEOWISE time-domain products can provide multi-epoch infrared measurements. Preserve mission, scan/epoch, quality, saturation and confusion information.

### SDSS

SDSS offers spectra, imaging and catalog products through SkyServer/CAS and SAS. Spectra should enter a dedicated spectral data contract. Do not treat a spectrum as a photometric light curve.

### Rubin

The current data policy distinguishes public alerts and prompt products from proprietary data products. Prompt catalogs and alerts may be public, while prompt images and annual data releases have proprietary periods. Access to the Rubin Science Platform is limited to eligible data-rights holders. The adapter must check product-specific rights before query, storage, export or redistribution.

### SIMBAD and VizieR

These are reference/catalog services, not raw survey instruments. As of 9 November 2026, CDS reported degraded service due to a cybersecurity incident and provided mirrors. The platform must support service health reporting, mirror configuration and graceful failure. Never make these services a hard runtime dependency for local analysis.

---

# 8. Multi-Modality Strategy

| Modality | Canonical input | Dedicated processing | Main outputs | Earliest phase |
|---|---|---|---|---|
| Time-series / light curves | Time, flux or magnitude, uncertainty, band, quality, source identity | Time normalization, quality assessment, sampling analysis, variability, period search, transient evolution | Features, periods, model outputs, diagnostics | MVP |
| Images | FITS image, WCS, exposure, filter, PSF, mask, variance, calibration | FITS validation, WCS validation, background, source detection, image subtraction or cutout, artifact QC | Source detections, cutouts, image quality, morphology and image anomaly candidates | P2 |
| Spectroscopy | FITS or tabular wavelength, flux, uncertainty, mask, resolution and metadata | Wavelength calibration, resampling, continuum handling, line detection, redshift and spectral classification | Spectral features, line measurements, redshift estimate and uncertainty | P3 |
| Astrometry | RA/Dec, reference epoch, proper motion, parallax, covariance | Coordinate frame and epoch propagation, uncertainty propagation, association | Position, motion, parallax and association evidence | P1 |
| Photometric catalogs | Source ID, bands, magnitudes/fluxes, errors, flags and epochs | Unit/band harmonization, catalog QC and cross-match | Color, SED context and source properties | P1 |
| Multi-wavelength | Independent optical/IR/UV/X-ray/radio measurements | Per-source/per-band contracts, epoch-aware association and SED assembly | Multi-wavelength context and derived quantities | P2 |
| Alerts/events | AVRO/JSON packet, detection, forced photometry, cutouts, broker metadata | Schema validation, alert deduplication, event history and stream processing | Event records, real/bogus screening and follow-up candidates | P2 |

## 8.1 Non-negotiable modality rule

Do not create one universal preprocessing pipeline or one model for every modality.

Share identity, provenance, project management, metadata, job execution, reporting and user interface infrastructure. Keep the scientific processing and validation modality-specific.

Multimodal fusion is a later research capability. It requires explicit synchronization, association uncertainty, feature contracts, missing-modality handling and independent validation.

---

# 9. Target Architecture

## 9.1 Architecture choice

Recommended initial architecture: **Modular Monolith + Versioned Contracts + Local-first Storage + Plugin Adapters**.

| Option | Benefit | Cost / risk | Decision |
|---|---|---|---|
| Modular monolith | One installable product, simple local operations, clear module boundaries | Requires discipline to prevent module coupling | Recommended |
| Microservices | Independent deployment and scaling | Network, security, operations and data-consistency costs | Reject for MVP |
| Plugin-first distributed platform | Extensible source ecosystem | Too much lifecycle complexity before stable core contracts | Future extension only |

## 9.2 Logical architecture

USER INTERFACES  
Desktop GUI / Browser Workbench / CLI / API

APPLICATION SERVICES  
Workspace / Project / Data Manager / Job Manager / Report Manager / Settings

CORE CONTRACTS  
Source / Dataset / Observation / Source Identity / Association / Analysis Run / Feature / Model / Result / Provenance

SOURCE LAYER  
ZTF DR24 / ALeRCE / Gaia / TESS / ATLAS / ASAS-SN / Pan-STARRS / WISE / SDSS / SIMBAD / VizieR / Rubin

RAW DATA LAYER  
Immutable source references / cached source bytes / content hashes / original metadata

VALIDATION LAYER  
Schema / units / time system / coordinate frame / flags / missingness / duplicate / source rights / integrity

IDENTITY LAYER  
Survey object IDs / physical source candidates / astrometric propagation / probabilistic associations / ambiguity ledger

MODALITY PIPELINES  
Time-series / images / spectroscopy / astrometry / catalog / alerts

ANALYSIS LAYER  
Statistics / feature registry / model registry / classification / calibration / conformal / OOD / anomaly / similarity / clustering / ranking

EVIDENCE LAYER  
Run manifest / source lineage / diagnostics / uncertainty / explanation / review state / reproducible report

PERSISTENCE AND EXPORT  
Local project database / Parquet / FITS / ECSV / VOTable / CSV / JSON / Markdown / reproducibility bundle

OPTIONAL HUMAN LAYER  
CIN / expert annotation / human-AI disagreement / curated research datasets

## 9.3 Shared versus modality-specific components

Shared:

- Workspace and project management.
- Source registry and adapter lifecycle.
- Dataset manifests and hashes.
- Provenance graph.
- Job orchestration and restart.
- Storage, caching and export.
- Logging, errors and diagnostics.
- Model/feature registries.
- API and GUI contracts.
- Authentication and access policy.

Modality-specific:

- Time and cadence handling.
- Photometry normalization.
- Image calibration and source detection.
- Spectral calibration and line analysis.
- Astrometric epoch propagation.
- Alert schema and event history.
- Modality-specific features, models and evaluation.

## 9.4 Data contracts

Every source adapter must return:

- Source name and release/version.
- Source-native identifiers.
- Retrieval timestamp.
- Exact query and parameters.
- Source schema and schema version.
- Original units, time system and coordinate frame.
- Row/epoch count and missing-data report.
- Raw payload hash or source checksum.
- Access and license metadata.
- Error and retry state.

Every analysis run must preserve:

- Unique Run ID.
- Code commit and software environment.
- Input dataset manifest and object order.
- Transformations and parameters.
- Feature schema and taxonomy version.
- Model, calibrator and artifact hashes.
- Random seed and deterministic settings.
- Output hashes, warnings and exceptions.
- Explicit status for skipped or unmeasured gates.

---

# 10. Scientific and ML Strategy

## 10.1 Reference hierarchy

Do not use one label type as universal truth.

Maintain separate labels and evidence classes:

1. Survey-native detection or object identity.
2. Broker classification.
3. Published catalog membership.
4. Spectroscopic classification.
5. Expert-curated reference.
6. Community annotation.
7. Model prediction.
8. Model-derived novelty or anomaly signal.

Every label must carry source, version, method, date and confidence/limitations.

## 10.2 Baseline protection

- Keep the 150-object/15-class benchmark frozen.
- Keep the 42-feature v0.2 feature contract frozen.
- Keep class order frozen.
- Recover original model bytes before production inference claims.
- Do not rebuild and call a new model the historical model.
- New training runs require a new model version, dataset version, split manifest and model card.

## 10.3 Validation design

- Group splits by physical source, not individual observations.
- Prevent same-source or same-event leakage across train/test.
- Use temporal splits for time-domain generalization.
- Use external-survey tests only when labels, units, time systems and feature semantics are compatible.
- Report class-level precision/recall, Macro-F1, Balanced Accuracy and confusion matrix.
- Evaluate calibration with Brier Score, ECE and reliability diagrams.
- Evaluate selective prediction with risk-coverage.
- Evaluate OOD separately from scientific anomaly detection.
- Report uncertainty and abstention under missingness and domain shift.
- Never report accuracy on an unlabeled user dataset.

## 10.4 Discovery semantics

- Classification answers: which known class best matches the input?
- OOD answers: how unlike the reference model distribution is the input?
- Anomaly analysis answers: what statistically unusual behavior is supported by the declared analysis?
- Novelty search prioritizes objects that merit inspection.
- Discovery requires independent scientific evidence and follow-up.

A ranking score is a triage tool, not a probability of discovery.

---

# 11. CPVS Research Lane

CPVS remains an independent scientific research workstream. It must not block DR24 product development.

Latest evidence reviewed:

- Parent Table 2: 781,602 rows.
- Published membership: 730,184 objects.
- Historical reconstructed candidates: 741,786.
- Candidate-only: 11,602.
- Published-only: 0.
- Four-field diagnostic matches the published membership on retained historical IDs, but is not established as the publisher's documented selection rule.
- MGPR feasibility: 34/34 full fits; 132/136 blocked folds PASS; 4 INSUFFICIENT_DATA. This is computational feasibility, not membership validation.
- The 100-object raw coordinate/epoch lineage run 43818485826 failed with Bad CRC-32 for archive member ztf2g. It did not produce accepted trace evidence.

Required next actions:

1. Re-download the pinned source archive into a clean path.
2. Verify publisher checksum, archive member size, CRC32 and SHA-256.
3. Compare the downloaded bytes with a separately retrieved source copy if possible.
4. Only after archive integrity passes, run the fixed 100-object lineage trace.
5. Preserve the fixed 1,000-object sample and full-parent diagnostics.
6. Keep all hypotheses separate and label them as hypotheses until proven.
7. Keep Issue #170 open. Do not change production filters or thresholds.

---

# 12. CIN Integration Strategy

CIN is a proposed, independent human-annotation subsystem. Its current specification is architecture, not implementation.

Recommended sequence:

- C0: feasibility and governance audit.
- C1: versioned task, annotation, provenance and privacy contracts.
- C2: small controlled light-curve assessment pilot.
- C3: gold tasks, repeated blind reviews, contributor calibration and disagreement preservation.
- C4: human-AI comparison.
- C5: pairwise similarity and novelty tasks.
- C6: image assessment.
- C7: curated research datasets and controlled model experiments.
- C8: community expansion.

Non-negotiable controls:

- CIN must remain optional.
- ZTF Classifier must operate without CIN.
- Human consensus is not ground truth.
- Raw contributions and disagreements must be retained.
- Do not contaminate the frozen benchmark.
- No automatic production retraining.
- Contributor skill estimates must be audited for bias.
- Human labels must retain contributor, task, data version, interface version and timestamp provenance.
- Privacy, retention, deletion, attribution and license policies must be approved before a public pilot.

CIN should not enter the Park MVP critical path.

---

# 13. User Experience and GUI

## 13.1 Researcher workflow

1. Install application or open the browser Workbench.
2. Create a local Workspace.
3. Create a Project.
4. Select a supported source.
5. Run a bounded source query or import a supported file.
6. Inspect metadata, schema, units, time system and source rights.
7. Review Data Quality Report.
8. Review identity and cross-match state.
9. Select an analysis mode.
10. Configure supported filters and parameters.
11. Start a reproducible Analysis Run.
12. Inspect progress and warnings.
13. Review object list and individual source record.
14. Inspect raw observations, plots, features and model outputs.
15. Review calibration, uncertainty, OOD and anomaly evidence separately.
16. Inspect candidate ranking and reasons.
17. Export catalog and report.
18. Save the run manifest.
19. Re-run the same pinned analysis offline.

## 13.2 Simple and advanced modes

Simple mode:

- Choose source.
- Search or import.
- Run quality checks.
- Run supported analysis.
- Inspect results.
- Export report.

Advanced mode:

- Explicit source query and release.
- Schema and filter configuration.
- Time/coordinate and photometry settings.
- Feature backend and model selection.
- Validation protocol and split.
- Run manifest and diagnostics.
- Batch and API/CLI execution.

## 13.3 GUI areas

- Home / Workspace.
- Data Manager.
- Source Registry.
- Object / Source Explorer.
- Analysis.
- Discovery.
- Cross-match.
- Models and Features.
- Results and Visualization.
- Reports and Exports.
- Validation.
- Help and Troubleshooting.
- Settings and Data Governance.

Every displayed metric must show its definition, source and status. Do not show an unlabeled confidence percentage as scientific certainty.

---

# 14. Engineering Roadmap

## Phase 0 — Recovery and truth baseline

- Recover and authenticate original model artifact.
- Fix security dependency state.
- Resolve documentation version drift.
- Confirm license policy.
- Establish a single current project status source.
- Keep CPVS research separate from product release.

Exit: no unsupported production model claim; security and documentation state are explicit.

## Phase 1 — DR24 application path

- Add explicit source-selection contract.
- Keep ALeRCE and DR24 separate.
- Normalize DR24 time and photometry under source-backed tests.
- Define QC policy and data-adequacy output.
- Preserve OID/filter/field/rcid.
- Add a source-group association state.
- Run a 5–10 source end-to-end sample, then 30–50.
- Verify API and Workbench parity.
- Add offline replay.

Exit: same pinned DR24 inputs produce reproducible object-level results with complete provenance.

## Phase 2 — Park MVP

- Build and document the labelled DR24 subset.
- Complete baseline and main model evaluation.
- Validate probability calibration and abstention.
- Keep OOD and anomaly separate.
- Deliver dashboard, catalog, report and reproducibility bundle.
- Conduct a non-developer acceptance test.
- Produce the Park demo and technical report.

Exit: all MVP acceptance criteria pass on a clean supported environment.

## Phase 3 — Cross-survey time-series

- Gaia DR3 selected variable-star subset.
- TESS selected sectors and products.
- ATLAS forced photometry.
- ASAS-SN Sky Patrol.
- Cross-survey identity and time alignment.
- Domain-shift evaluation.

Exit: each source adapter passes its own ingestion and QC tests; cross-survey model claims have independent labels and protocol.

## Phase 4 — Catalog and multi-wavelength context

- Pan-STARRS DR2.
- WISE/NEOWISE.
- SIMBAD and VizieR.
- Probabilistic cross-match and evidence ledger.
- SED and contextual analysis.

Exit: association quality and data provenance are measured and ambiguity is visible.

## Phase 5 — Images and spectroscopy

- FITS image ingestion and WCS.
- Image quality and source detection.
- Difference image and cutout workflow.
- SDSS spectrum ingestion.
- Wavelength and flux contracts.
- Spectral features, redshift and classification.

Exit: separate image and spectrum pipelines pass scientific validation.

## Phase 6 — Discovery workbench

- Similar-object search.
- Clustering and population analysis.
- Transparent candidate ranking.
- Scientific anomaly analysis.
- Expert review and reproducible candidate reports.

Exit: candidate ranking is calibrated to a defined task and not presented as discovery truth.

## Phase 7 — Optional CIN

- Controlled annotation pilot.
- Quality and consensus.
- Human-AI disagreement.
- Curated dataset release.
- Controlled model experiment.

Exit: governance and independent evaluation pass.

---

# 15. Testing and Validation Matrix

| Layer | Required tests | Acceptance |
|---|---|---|
| Source adapter | Auth, query, timeout, pagination, source version, schema, hashes | Pinned source response and failure states reproducible |
| Data integrity | Null, NaN, Inf, duplicate, malformed, truncation, CRC, hash mismatch | No corrupt input silently accepted |
| Time | UTC, MJD, HMJD, BJD, TCB, time scale and reference epoch | Explicit conversion with unit tests and independent references |
| Coordinates | ICRS, frame, epoch, proper motion, uncertainty | Propagation and uncertainty independently checked |
| Photometry | Flux/magnitude, zeropoint, color term, negative error, saturation, flags | Native values preserved; normalization contract validated |
| Identity | OID, Gaia source_id, aliases, duplicates, multiple associations | Ambiguity preserved; no forced nearest-neighbor merge |
| Time-series | Irregular cadence, gaps, alias, phase coverage, missing bands | Method-specific tests and uncertainty |
| Image | FITS HDU, WCS, masks, background, PSF, units | Image pipeline has separate acceptance metrics |
| Spectroscopy | Wavelength grid, flux, inverse variance, masks, resolution | Spectral pipeline has separate acceptance metrics |
| ML | Group split, temporal split, leakage, class imbalance, calibration | Reproducible metrics with denominators |
| OOD/anomaly | Shift, missingness, contamination, false positives | Separate evidence and thresholds |
| Cross-survey | Schema and domain shift, source identity, class mapping | No model transfer claim without valid labels |
| Application | Job restart, cache, cancellation, persistence, export | Deterministic replay and failure recovery |
| GUI | Simple user path, errors, accessibility, plot interpretation | Non-developer user completes supported workflow |
| Packaging | Clean Windows/macOS/Linux install, upgrade, uninstall | No manual Python setup for standard user |
| Security | Dependency audit, secret scan, path traversal, unsafe artifacts | Security gate passes; untrusted model files rejected |
| Reproducibility | Manifest, hash, code commit, environment, output comparison | Same pinned run reproduces declared deterministic outputs |

A skipped test is NOT VERIFIED, not PASS. A green CI job does not establish scientific validity unless the required scientific evidence jobs ran.

---

# 16. Security and Data Governance

1. No credentials in Git, logs or reports.
2. Use least-privilege access for external sources.
3. Verify data terms, attribution and redistribution restrictions.
4. Store source metadata, license and access class in the Data Source Registry.
5. Keep raw data separate from derived outputs.
6. Do not commit large scientific datasets to Git.
7. Use immutable manifests and content hashes.
8. Treat model artifacts as executable inputs; verify trusted origin and hashes before loading.
9. Use safe parsing for FITS, AVRO, Parquet and archives.
10. Protect local project files and database backups.
11. Define retention, deletion and export policy.
12. Maintain offline analysis for already acquired data.
13. For Rubin, enforce product-specific data-rights restrictions.
14. For CIN, define participant privacy, annotation rights, retention and consent before public release.
15. Resolve project source-code license and contributor terms before inviting external contributors.

---

# 17. Commercialization Strategy

## 17.1 Customer hypotheses

- University astronomy and physics groups.
- Research institutes and observatories.
- Survey data centers and broker teams.
- Scientific software groups.
- Graduate programs and astronomy data-science training.
- Research consortia that need reproducible screening and prioritization.

These are target segments, not validated paying customers.

## 17.2 Value proposition

- Reproducible source-to-result workflow.
- Local-first analysis for research groups.
- Survey-aware ingestion and quality control.
- Explainable and uncertainty-aware candidate prioritization.
- Cross-survey evidence and scientific reports.
- Extensible modality-specific analysis.

## 17.3 Revenue options

1. Institutional annual license with local deployment.
2. Paid support and maintenance.
3. Custom source adapters and research workflows.
4. Training and workshops.
5. Research contracts and grant-funded development.
6. Optional hosted service only after privacy, data rights, operating cost and customer demand are validated.

Do not prioritize SaaS before the local product, security, backup and support model are proven.

## 17.4 Commercial risks

- Strong free/open research ecosystem.
- Limited institutional budgets.
- Scientific credibility takes time.
- Data rights and source availability differ.
- Small initial customer population.
- Long sales and procurement cycles.
- Maintenance cost across many data sources and OS targets.

The first commercial validation action should be structured interviews with 5–10 target users and a workflow-based pilot. Do not infer market demand from the technology alone.

---

# 18. Prioritized Backlog

Priority definitions: P0 = critical blocker; P1 = required for Park MVP; P2 = expanded product; P3 = long-term.

| ID | Task | Subsystem | Priority | Scientific impact | Effort | Dependencies | Acceptance criteria | Status |
|---|---|---|---|---|---|---|---|---|
| SR-001 | Recover and authenticate v0.2 production model | Model governance | P0 | Critical | Medium | Owner local artifact | Original hashes and dependent inference tests pass | Blocked / Unknown |
| SR-002 | Resolve security dependency on main | Security | P0 | High | Low | PR #289 review | Security patch merged and main CI passes | Open PR |
| SR-003 | Explicit DR24/ALeRCE source selection | Ingestion | P0 | Critical | Medium | #253 | User-selected source is explicit; no fallback | Open |
| SR-004 | DR24 HMJD/photometry normalization contract | Time-series | P0 | Critical | High | Source docs, fixtures | Independent tests for time and photometry | Not complete |
| SR-005 | ZTF OID to physical-source association | Identity | P0 | Critical | High | #249/#283 | Probabilistic association and reversible ledger | Partial contract |
| SR-006 | DR24 5–10 source end-to-end run | MVP | P0 | High | Medium | SR-003/004/005 | API, Workbench, manifest and offline replay | Not accepted |
| SR-007 | 30–50 source guided demo | MVP | P1 | High | Medium | SR-006 | Reproducible guided workflow | Not started |
| SR-008 | 100k labelled DR24 subset | Data | P1 | High | High | Source/label contract | Manifest, label semantics, hashes, QC report | Target only |
| SR-009 | Independent temporal benchmark | Validation | P1 | Critical | High | Model artifact, labels | Group/time leakage checks and full metrics | Incomplete |
| SR-010 | Probability calibration and abstention audit | ML | P1 | High | Medium | SR-001/009 | Brier, ECE, risk-coverage and policy | Not accepted |
| SR-011 | OOD/anomaly semantic separation in UI | Discovery | P1 | High | Medium | API/UI | Separate scores, explanations and status | Partial |
| SR-012 | Cross-platform packaging | Product | P1 | Medium | High | Stable API and app | Clean install tests on target OS | Not implemented |
| SR-013 | Data Source Registry | Data platform | P1 | High | Medium | Source metadata contract | Source/version/license/health metadata | Design |
| SR-014 | Multi-source Gaia pilot | External validation | P2 | High | Medium | ZTF MVP stable | Pinned Gaia DR3 sample and independent tests | Proposed |
| SR-015 | TESS MAST adapter | External validation | P2 | High | Medium | Time-series contracts | Sector-aware FITS ingestion and tests | Proposed |
| SR-016 | ATLAS and ASAS-SN adapters | External time-series | P2 | High | Medium | Source access approval | Bounded source-backed parity tests | Proposed |
| SR-017 | Pan-STARRS/WISE context | Catalog | P2 | Medium | Medium | AOIC | Provenance-backed cross-match | Proposed |
| SR-018 | SDSS spectroscopy pipeline | Spectroscopy | P2 | High | High | Spectral contract | FITS ingestion and spectral metrics | Proposed |
| SR-019 | FITS image analysis | Imaging | P2 | High | High | Image contract | WCS/QC/source-detection benchmark | Proposed |
| SR-020 | Discovery ranking and similar-object search | Discovery | P2 | High | High | Validated analysis evidence | Transparent reproducible ranking | Proposed |
| SR-021 | Rubin alert adapter | Alert stream | P3 | High | High | Data-rights policy | Public-product compliance and schema tests | Proposed |
| SR-022 | CIN LC-01 controlled pilot | Human review | P3 | Medium | Medium | Governance and privacy | Blind repeated annotation protocol | Proposed |
| SR-023 | Public CIN network | Community | P3 | Medium | Very high | CIN pilot evidence | Independent quality and privacy acceptance | Not authorized |
| SR-024 | Documentation/license synchronization | Governance | P1 | High | Low | Owner license decision | Consistent README, Model Card, Handbook, LICENSE | Open |

---

# 19. Risk Register

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| Original model artifact cannot be recovered | Medium | Critical | Search local/offline backups; preserve UNKNOWN; never recreate and mislabel |
| DR24 photometry/time conversion is wrong | Medium | Critical | Preserve native data; use source-backed conversion and independent tests |
| Multiple OIDs merged into one false source | High | Critical | Probabilistic identity and ambiguity states |
| Weak labels mistaken for ground truth | High | Critical | Label hierarchy and independent reference |
| Cross-survey domain shift invalidates model | High | High | Source-specific evaluation and calibration |
| Image/spectrum expansion delays MVP | High | High | Separate modality roadmap |
| Rubin data rights misunderstood | Medium | High | Rights-aware adapter and access checks |
| External service outage | Medium | Medium | Cache, mirror and graceful failure |
| Security vulnerability remains in main | Medium | High | Review PR #289 and re-run main gates |
| Public repo licensing is ambiguous | High | High | Owner/legal license decision |
| Desktop packaging fails on clean OS | Medium | High | Automated clean-OS install tests |
| CIN annotations contaminate benchmark | Medium | Critical | Data-domain separation and no auto-retraining |
| Resource constraints cause poor user experience | Medium | Medium | Lazy loading, bounded jobs, profiling and local-first design |
| Market demand is overestimated | Medium | High | User interviews and paid pilot before SaaS |

---

# 20. Decision Register

| Decision | Recommendation | Reason | Consequence |
|---|---|---|---|
| D-001 Product identity | Astronomical Data Analysis, Intelligence & Discovery Platform | Matches long-term user vision | Product architecture extends beyond classifier |
| D-002 MVP source | ZTF DR24 HATS first | Current product and Park source | Other surveys remain later |
| D-003 ALeRCE role | Reference/broker source, not truth | Label provenance | Keep reference lane distinct |
| D-004 Architecture | Modular monolith | Lower operating complexity | No microservices in MVP |
| D-005 Source selection | Explicit per run | Prevent silent data substitution | Source and provenance visible |
| D-006 Identity | Separate survey OID and physical source | Multiple OIDs may represent one source | AOIC is a first-class subsystem |
| D-007 Baseline | Freeze v0.2.0 | Reproducibility and compatibility | New models get new versions |
| D-008 Model recovery | Recover original artifact before production claims | Avoid false historical identity | Model readiness remains UNKNOWN |
| D-009 Anomaly semantics | Separate OOD, anomaly and novelty | Different scientific questions | Separate UI and API outputs |
| D-010 Multi-modality | Separate pipelines | Different physical data and units | No universal preprocessing |
| D-011 CIN | Optional and later | Governance and MVP focus | No runtime dependency |
| D-012 Desktop | After DR24 workflow is stable | Avoid packaging unstable behavior | Web/API demo first |
| D-013 Licensing | Owner decision required | Public repository and proprietary metadata conflict | No open-source claim until resolved |
| D-014 Rubin | Rights-aware later adapter | Not all data are public | Product-level data policy required |

---

# 21. 30 / 60 / 90-Day Execution Plan

The clock starts only after owner approval, team availability and required resources. These are target checkpoints, not delivery guarantees.

## Days 1–30: Restore scientific and product truth

- Recover model artifact and audit report.
- Resolve security dependency.
- Approve license and source governance.
- Define source-selection contract.
- Finish DR24 raw integrity, time and photometry contracts.
- Define OID/source-group identity states.
- Run 5–10 source DR24 workflow end-to-end.
- Record all failures and replay.

Exit: one supported DR24 workflow runs reproducibly with complete provenance; model artifact status is resolved or explicitly unrecoverable.

## Days 31–60: Validate the Park scientific workflow

- Build bounded labelled DR24 dataset.
- Audit labels and identity.
- Complete feature and model evaluation.
- Measure calibration and abstention.
- Evaluate OOD separately.
- Run temporal validation and error analysis.
- Complete API/Workbench parity.
- Run 30–50 source guided demonstration.

Exit: the Park demo has measured metrics, explicit limitations and a reproducibility bundle.

## Days 61–90: Product acceptance and external validation readiness

- Run non-developer acceptance tests.
- Complete report and catalog export.
- Verify install and recovery on supported target environment.
- Prepare Park technical report and demo.
- Finalize data source registry.
- Approve Gaia/TESS validation plans.
- Conduct 5–10 customer/user interviews.

Exit: MVP acceptance decision is based on evidence; expansion backlog is costed and ordered.

---

# 22. One-Year and Three-Year Roadmap

## One year

- Stable DR24-first application.
- Local-first cross-platform distribution.
- Gaia and TESS external time-series validation.
- ATLAS and ASAS-SN adapters where access is approved.
- Catalog context from Pan-STARRS and WISE/NEOWISE.
- Probabilistic cross-match.
- Versioned candidate ranking.
- Similar-object search.
- Reproducible scientific reports.
- First controlled image or spectroscopy pilot if a clear user need exists.

## Three years

- Mature multi-survey time-domain analysis.
- Separate image and spectroscopy workbenches.
- Multi-wavelength context and source association.
- Alert/event processing where justified.
- Scientific candidate campaigns and expert review.
- Optional CIN with independently evaluated annotation quality.
- Institutional deployments and support contracts.
- Public research datasets and methods papers where licenses and scientific evidence permit.

The three-year vision does not imply that all listed capabilities will be funded or scientifically justified. Each modality requires a separate acceptance gate.

---

# 23. Final Red Team Verdict and Owner Actions

## 23.1 Independent Red Team verdict

**Current state: NOT READY as the complete multi-source, multi-modality discovery platform.**

The repository has meaningful engineering foundations. It has a Python package, API, browser Workbench, job/result infrastructure, feature engine, provenance elements and bounded DR24 raw retrieval.

It does not yet demonstrate:

- Authenticated production model artifact.
- Complete DR24 normalized analysis and inference path.
- Validated physical-source identity and cross-match.
- Independent multi-survey scientific validation.
- Image and spectroscopy pipelines.
- Self-contained desktop distribution.
- Full user-facing product acceptance.
- Commercial customer validation.

## 23.2 What could cause project failure

1. Continuing to add features before the DR24 data path and model artifact are trustworthy.
2. Treating survey object IDs as physical identities.
3. Treating broker labels as ground truth.
4. Mixing time systems or photometric systems without validation.
5. Treating OOD as scientific anomaly.
6. Building a large multi-modality UI without validated pipelines.
7. Releasing a desktop installer before the application workflow is stable.
8. Leaving license and data rights unclear.
9. Claiming scientific validation from green CI while evidence jobs are skipped.
10. Failing to validate demand with real researchers.

## 23.3 If rebuilding from today's state

Keep the v0.2.0 baseline as a historical reference. Rebuild the product architecture around explicit source selection, raw data preservation, a provenance graph, a source-identity layer, modality-specific pipelines, and reproducible analysis runs. Deliver the DR24 MVP first. Add other sources through independently tested adapters. Do not rewrite the scientific baseline to fit new sources.

## 23.4 Decisions required from the owner

1. Confirm the long-term product name and scope: Astronomical Data Analysis, Intelligence & Discovery Platform.
2. Confirm DR24-first Park MVP remains the immediate product delivery.
3. Decide whether source code remains proprietary or receives an explicit open-source license.
4. Identify the original storage location of the v0.2.0 model artifact, if it exists locally.
5. Approve a bounded DR24 5–10 source end-to-end test after source and time contracts are ready.
6. Approve Gaia DR3 and TESS as the first external validation sources after DR24.
7. Keep CIN implementation deferred until the core MVP is accepted.
8. Confirm the budget and supported OS targets before desktop packaging.

---

# Appendix A — Sixteen Specialist Seat Reviews

The following are independent structured perspectives, not separate human reports. Each seat records strengths, risks, opportunities and its recommendation.

## Seat 1 — Chief Scientist / Principal Investigator

**Strengths**
- Clear time-domain astronomy starting point.
- Public data reduces telescope dependency.
- Uncertainty and abstention are central product concepts.

**Risks**
- Product claims can exceed scientific evidence.
- Benchmark labels are weak references.
- Discovery terminology can overstate candidate ranking.

**Opportunities**
- Rare transient prioritization.
- Cross-survey population studies.
- Reproducible candidate dossiers.

**Recommendation:** define a small number of scientific use cases and require a reference, selection function and validation protocol for each.

## Seat 2 — ZTF Survey & Data Specialist

**Strengths**
- DR24 HATS provides scalable source-native light curves.
- Raw-preserving adapter exists.
- ZTF is a suitable initial survey.

**Risks**
- HMJD can be confused with MJD.
- Native photometry requires documented color handling.
- OID is filter/field/quadrant specific.
- catflags policies can remove valid data if misunderstood.
- HATS and Zubercal are distinct products.

**Opportunities**
- Lazy HATS queries.
- Alert AVRO adapter.
- Source-native QC and provenance.

**Recommendation:** finish DR24 source-to-model contracts before claiming a working DR24 inference path.

## Seat 3 — Variable and Transient Astrophysicist

**Strengths**
- Useful variable/transient taxonomy starting point.
- Time-series analysis has real scientific use.
- Unknown/abstention can prevent forced labels.

**Risks**
- Classes overlap physically.
- Selection effects alter observed populations.
- Rare classes have limited reference labels.
- Survey cadence changes detectability.
- Artifact/reality screening is not astrophysical classification.

**Opportunities**
- Transient evolution features.
- Population and rare-object studies.
- Follow-up prioritization.

**Recommendation:** define taxonomy hierarchy and intended scientific question before model design.

## Seat 4 — Astrostatistics and Time-Series Scientist

**Strengths**
- Irregular time-series methods are recognized.
- Temporal validation is a stated requirement.
- Uncertainty is part of the product concept.

**Risks**
- Aliasing and cadence effects.
- Time-system conversion errors.
- Heteroscedastic errors and non-detections.
- Data leakage across repeated observations.
- Poorly calibrated probabilities under domain shift.

**Opportunities**
- Bayesian periodicity.
- Model comparison and posterior diagnostics.
- Phase coverage and sampling adequacy.

**Recommendation:** separate measurement uncertainty, model uncertainty, calibration and data adequacy.

## Seat 5 — Astroinformatics / Big Data Engineer

**Strengths**
- HATS and Parquet support lazy access.
- CPU-first architecture is appropriate.
- Existing jobs and result persistence provide foundations.

**Risks**
- Large archive transfers can fail or repeat.
- Local storage can grow without retention policy.
- Nested data can be normalized incorrectly.
- Object-level joins can be expensive.
- Remote service availability can interrupt jobs.

**Opportunities**
- Partition-aware query planning.
- Local content-addressed cache.
- Bounded and restart-safe acquisition.

**Recommendation:** build source registry, query planner, artifact cache and run manifest before broad ingestion.

## Seat 6 — Catalog and Cross-Matching Specialist

**Strengths**
- Gaia, SIMBAD, VizieR and Pan-STARRS provide useful context.
- The project recognizes OID is not physical identity.
- Draft identity contracts exist.

**Risks**
- Proper motion changes positions by epoch.
- Crowded fields create ambiguous matches.
- Coordinate uncertainty varies by catalog.
- Aliases and catalog identifiers are not interchangeable.
- Nearest-neighbor matches can be false.

**Opportunities**
- Probabilistic cross-match.
- Source association graph.
- Multi-epoch astrometric propagation.

**Recommendation:** build AOIC as a separate evidence subsystem with ambiguity states and reversible associations.

## Seat 7 — Chief AI / ML Scientist

**Strengths**
- Frozen feature baseline offers a controlled starting point.
- Tree models are resource-efficient.
- Calibration, conformal and OOD are already represented in architecture.

**Risks**
- Weak labels limit scientific claims.
- Missingness can become a hidden shortcut.
- Cross-survey feature shift can invalidate predictions.
- One model cannot solve all modalities.
- Active learning can bias the reviewed sample.

**Opportunities**
- Model ensembles.
- Self-supervised representations.
- Similar-object search.
- Domain adaptation after evaluation.

**Recommendation:** preserve baseline; add new model families only after independent source-specific evaluation.

## Seat 8 — Independent Scientific Validation Lead

**Strengths**
- Fail-closed gate is a sound principle.
- Benchmark limitations are documented.
- CPVS is separated from the Park MVP.

**Risks**
- Small benchmark is not population representative.
- External data can share source identities with training.
- CI skips can hide missing evidence.
- Calibration can fail under distribution shift.
- Broker labels are not independent truth.

**Opportunities**
- Group-aware splits.
- Temporal and cross-survey benchmarks.
- Independent adjudicated subsets.

**Recommendation:** require a validation protocol and source lineage before every performance claim.

## Seat 9 — Scientific Software Architect

**Strengths**
- API, application services and scientific core are separated.
- Feature backend registry exists.
- Versioned contracts are already used.

**Risks**
- Source logic can leak into application defaults.
- Modality contracts are not defined.
- Identity and provenance are incomplete.
- Documentation and code can drift.
- Premature microservices increase operational risk.

**Opportunities**
- Modular monolith.
- Stable plugin adapter interface.
- Provenance graph and schema registry.

**Recommendation:** freeze core contracts and use one modular application with explicit boundaries.

## Seat 10 — Backend and Platform Engineer

**Strengths**
- FastAPI and CLI are available.
- Durable jobs and results exist.
- Workbench consumes API contracts.

**Risks**
- DR24 raw endpoint is separate from normal observation retrieval.
- User file import is limited to CSV/Parquet.
- Long jobs need reliable cancellation/retry.
- Runtime data retention needs policy.
- Multi-source selection needs API-level support.

**Opportunities**
- Explicit source strategy per run.
- Data Manager service.
- Background workflow and replay.

**Recommendation:** complete the source-selected DR24 path before expanding backend features.

## Seat 11 — MLOps / DevOps / Security

**Strengths**
- CI, CodeQL, dependency audit and package checks exist.
- Artifact hashes and model registry concepts exist.
- Security PR has a passing branch run.

**Risks**
- Security fix is not merged.
- Model artifact chain of custody is incomplete.
- Python support matrix is narrow.
- No verified desktop release pipeline.
- License and provenance metadata are inconsistent.

**Opportunities**
- SBOM and signed release artifacts.
- Reproducible installers.
- Backup/restore acceptance.

**Recommendation:** resolve security, artifact and license gates before distribution expansion.

## Seat 12 — QA / Reliability Engineer

**Strengths**
- Test suite and regression tests are substantial.
- Workflow gates distinguish several validation stages.
- Source-backed tests can run separately.

**Risks**
- Some source-backed jobs are skipped.
- Live data workflows can fail before analysis.
- No clean-OS installer acceptance.
- Time and identity edge cases remain.
- End-to-end tests do not yet prove scientific validity.

**Opportunities**
- Fault injection.
- Offline replay tests.
- Cross-platform matrix.
- Data corruption recovery tests.

**Recommendation:** test the complete user journey and every failure state, not only modules.

## Seat 13 — Scientific UX/UI Designer

**Strengths**
- Workbench exists.
- Scientific sections are separated.
- Provenance and diagnostics have UI concepts.

**Risks**
- Workbench is not a packaged desktop product.
- Technical diagnostics can overwhelm new users.
- Probability may be misread as certainty.
- Candidate ranking may be misread as discovery.
- Missing-data reasons need clear presentation.

**Opportunities**
- Guided workflow.
- Simple and advanced modes.
- Object evidence dossier.
- Integrated help and interpretation.

**Recommendation:** design around a project workflow and source record, not a collection of technical dashboards.

## Seat 14 — Product Manager / Commercialization

**Strengths**
- Park MVP is clearly defined.
- Institutional user segments are identified.
- CPU-first and local-first offer a practical differentiator.

**Risks**
- Market demand is not independently validated.
- Product scope can expand too quickly.
- SaaS is premature.
- License is unclear.
- Support and data costs are under-specified.

**Opportunities**
- Paid institutional pilot.
- Custom data adapters.
- Research workflow support.
- Training and consulting.

**Recommendation:** validate one paid research workflow before committing to a hosted commercial platform.

## Seat 15 — Scientific Documentation Lead

**Strengths**
- README, Data Card, Model Card and architecture documents exist.
- CPVS evidence is extensively recorded.
- Product roadmap records exist on draft branches.

**Risks**
- Main and Draft PR documents disagree.
- Model Card version differs from README.
- Some roadmap documents are not merged.
- Status summaries can become stale.
- Product claims need a single evidence index.

**Opportunities**
- Canonical source registry.
- Versioned status and decision records.
- Automatic documentation consistency checks.

**Recommendation:** maintain one dated canonical status report and link all historical reports rather than rewriting them.

## Seat 16 — Independent Red Team

**Strengths**
- The project has a real software package.
- The API and Workbench are functional foundations.
- Scientific boundaries are increasingly explicit.

**Risks**
- Model artifact is unavailable.
- DR24 is not connected to the default analysis path.
- Identity is unresolved.
- Desktop packaging is absent.
- Multi-survey and multi-modality claims exceed current implementation.

**Opportunities**
- Narrow DR24 MVP.
- Reproducible source-to-result contract.
- External validation ladder.
- Modular modality architecture.

**Recommendation:** stop describing the current state as a complete discovery platform. Describe it as a ZTF-focused scientific software foundation under product expansion.

---

# Appendix B — Cross-Examination Findings

1. **Scientist vs Product Manager:** the broad discovery vision is valid, but the Park MVP must remain small. The MVP should not be delayed by image, spectroscopy or CIN work.
2. **ML Scientist vs Validation Lead:** new model complexity is not justified until independent labels, group splits and temporal validation exist.
3. **ZTF Specialist vs Cross-Match Specialist:** OID grouping must be an evidence-backed association, not a convenience join.
4. **Data Engineer vs Software Architect:** lazy data access is essential, but adapters must return stable contracts and never expose source-specific nested payloads directly to the feature engine.
5. **UX Designer vs QA:** the interface should hide unnecessary complexity but must expose warnings, missingness and validation status.
6. **MLOps vs Scientific Lead:** a green CI is only engineering evidence for jobs that ran. Skipped source-backed validation must remain visible.
7. **CIN vs Scientific Validation:** human annotation can prioritize investigation and create research data, but it cannot silently become benchmark truth.
8. **Red Team vs all seats:** the long-term architecture is directionally sound; the present product is not yet at the maturity implied by the full vision.

## Final consensus

- Preserve the scientific baseline.
- Build the DR24-first MVP.
- Add explicit source and identity contracts.
- Use a modular monolith.
- Separate modality pipelines.
- Validate sources independently.
- Keep CIN optional.
- Do not claim discovery without independent evidence.

## Dissent

There is no technical basis to prioritize a public CIN network, full multi-modality UI or microservices before the DR24 MVP and original model artifact are resolved. These are deferred, not rejected.

---

# Appendix C — Evidence Sources

## User-provided documents

- Final Park presentation.
- Final project dossier.
- ZTF Classifier — Cosmic Intelligence Network.
- Crowd data generation / CIN source.
- Think-tank seat definitions.
- CPVS convergence policy and research handoff.
- Previous CPVS status report.

## Repository sources

- README.md
- pyproject.toml
- requirements.lock
- CHANGELOG.md
- docs/DATA_CARD.md
- docs/MODEL_CARD.md
- docs/api/API_V1.md
- docs/HANDBOOK_UPDATED_v2.8.md
- docs/architecture/V1_PRODUCT_ARCHITECTURE.md
- docs/ECOSYSTEM_REVIEW_PRODUCT_EXPANSION_2026-10-08.md
- src/ztf_classifier/application/observations.py
- src/ztf_classifier/application/ingestion.py
- src/ztf_classifier/io/dr24_lightcurve.py
- src/ztf_classifier/validation/dr24_quality.py
- src/ztf_classifier/features/engine.py
- Issues #157, #158, #170, #188, #251, #253 and #282.
- Draft PRs #283, #284, #285, #289, #290 and #291.
- Draft PR #281 contains the 2026-11-12 master roadmap, defect register and architecture review; these are not merged main-branch policy.

## External source references

- IRSA ZTF mission and DR24 services: https://irsa.ipac.caltech.edu/Missions/ztf.html
- ZTF DR24 HATS tutorial: https://caltech-ipac.github.io/irsa-tutorials/ztf-lightcurves/
- IRSA cloud access and DR24 HATS products: https://irsa.ipac.caltech.edu/cloud_access/
- Gaia DR3 documentation: https://gea.esac.esa.int/archive/documentation/GDR3/
- Gaia DR3 variability content: https://doi.org/10.1051/0004-6361/202243940
- TESS data products: https://heasarc.gsfc.nasa.gov/docs/tess/data-products.html
- Pan-STARRS MAST catalog API: https://catalogs.mast.stsci.edu/docs/panstarrs.html
- ATLAS forced photometry announcement: https://www.wis-tns.org/node/97546
- ASAS-SN Sky Patrol: https://asas-sn.github.io/skypatrol/
- SDSS DR18 data access: https://www.sdss.org/dr18/data_access/
- IRSA catalog API: https://irsa.ipac.caltech.edu/onlinehelp/catalogs/catalogs/api.html
- Rubin data policy: https://rubinobservatory.org/for-scientists/data-policy
- Rubin data access: https://rubinobservatory.org/for-scientists/data-products/data-access
- SIMBAD/CDS service status: https://simbad.cds.unistra.fr/

---

**End of draft strategic recovery report.**

**Review status:** Draft for project-owner review.  
**Scientific status:** No new scientific validation claim is made.  
**Code status:** No production code or baseline artifact was changed.  
**Next gate:** Owner review of the product decisions and backlog priorities, followed by a separate implementation plan for the approved P0/P1 tasks.
