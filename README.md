# ZTF Classifier

## Latest CPVS source-backed checkpoint — 2026-10-27

The latest inspected heavy source-backed run is [40397098709](https://github.com/saeed92m/ztf-classifier/actions/runs/40397098709), commit `4674d3ad69ff7148a246ccf34f5aa216c3e791fd`. The parent catalog contains 781,602 SourceIDs (SHA-256 `0f3ca5d4e71f674c38b3c08553c12cca0c32d2d31f776166ab29ce80a75cf138`). The derivation logged 741,788 candidates against the expected 730,184 and failed the expected-count check; the independent membership audit recorded 11,604 candidate-only and 0 published-only IDs. The 3.77 GB heavy artifact SHA-256 is `212f4192de530212bafe597d589c67c0778363e0dadc1f64c1b44e8f170eb426`.

**Scientific status remains UNRESOLVED and release-blocking.** This latest 741,788 / 11,604 result supersedes older counts only for this run; it does not explain their difference. PR #182 sampling code currently emits only 100- and 1,000-object samples; the agreed 50-object quick sample, separate 100-object targeted edge-case sample, and 10,000-object parent-population sample have not yet been implemented or run against this pinned evidence. Keep the probability sample separate from targeted edge-case diagnostics. Do not alter selection rules, thresholds, acceptance criteria, or frozen v0.2.0 / v1.0.1 artifacts to force equality. See [Issue #180](https://github.com/saeed92m/ztf-classifier/issues/180) for the verified checkpoint and next actions.


## Verified source-code finding — non-finite SNR predicate (2026-10-27)

The exact heavy-workflow checkout is merge commit `3c91da4` (PR head `4674d3ad69ff7148a246ccf34f5aa216c3e791fd`, base `8c2ba057a572b1cd460c47d1e02940e1ba44e366`). In `src/ztf_classifier/validation/derivation.py` at that revision, the predicate is `if oid not in parent_ids or _snr_from_mag_error(row.get(error_key, "")) < sigma:`. A non-finite SNR can pass this check because `NaN < sigma` is false. The later diagnostic branch `science/cpvs-samples-clean-20261012` explicitly rejects non-finite SNR using `math.isfinite(snr)`.

This confirms a real defect in the executed predicate, but does **not** establish that it explains all 11,604 candidate-only IDs. The same run logged 781,602 parent SourceIDs, 741,788 derived candidates versus 730,184 expected, 11,604 candidate-only and zero published-only. The scientific status remains **UNRESOLVED / release-blocking** until per-object provenance quantifies this predicate's effect and an exact, reproducible membership comparison is produced. Do not change thresholds, use the four-field diagnostic as an assumed publisher rule, or modify the frozen v0.2.0 baseline / v1.0.1 release to force a match. Evidence is tracked in [Issue #180](https://github.com/saeed92m/ztf-classifier/issues/180).


## Status snapshot — 2026-10-27

- Active ALeRCE fix: [PR #231](https://github.com/saeed92m/ztf-classifier/pull/231), open/draft/unmerged, head `4a6ddd786ebb37551253349ef483ca968a8f00ac`.
- Current-head CI, CodeQL, Product Scope Audit, and Scientific Validation workflows completed successfully. Four source-backed/heavy scientific jobs were skipped; this is not full scientific validation.
- The lab artifact is local diagnostic output, not a published release asset. Frozen scientific baseline `v0.2.0` and immutable software release `v1.0.1` remain unchanged.
- The 45-object diagnostic acquisition is distinct from the still-required explicit `fallback_on_empty` selection-policy experiment.
- CPVS exact reconstruction remains **UNRESOLVED**; see [Issue #170](https://github.com/saeed92m/ztf-classifier/issues/170). Do not tune selection rules to force published cardinality.
- Current execution evidence and acceptance steps: [Project Status & Execution Ledger](docs/PROJECT_STATUS_AND_EXECUTION_LEDGER_2026-10-27.md).


A CPU-first Astronomical Data Analysis & Discovery Platform for Zwicky Transient Facility (ZTF) data, scientific feature generation, machine-learning and statistical analysis, uncertainty/OOD diagnostics, provenance, and discovery-oriented workflows.

## Project status

**Version:** v1.0.1
**Release:** `v1.0.1` (immutable)
**Status:** v1.0.1 released and immutable; v1.0.0 remains immutable; Scientific Validation, CI, CodeQL, release publication, and artifact verification passed

The v0.2 core pipeline includes:

* light-curve acquisition and validation;
* feature extraction;
* multiclass classification;
* probability calibration;
* conformal prediction;
* out-of-distribution (OOD) scoring;
* historical and temporal evaluation;
* persisted production model artifacts;
* production inference;
* single-object and batch inference interfaces.

The current benchmark contains **150 ZTF objects across 15 ALeRCE classes**. ALeRCE classifications are used as benchmark labels and are not treated as independent ground truth.

## Product direction

ZTF Classifier is being expanded into a cross-platform **Astronomical Data Analysis & Discovery Platform**.

The planned end-user experience is a self-contained desktop application for Windows, macOS, and Linux. Users should not need to install Python, pip, virtual environments, Git, or use a terminal for normal operation. CLI and API interfaces remain available for advanced users.

The product expansion includes:
- Data Manager and ingestion abstraction;
- Object/Source Explorer;
- light-curve and scientific visualization;
- classification, uncertainty, calibration, conformal prediction, and OOD;
- separate scientific-anomaly and Real/Bogus channels;
- discovery candidate generation and transparent ranking;
- catalog/cross-match evidence;
- similar-object search;
- human-in-the-loop review and feedback;
- explainability and provenance/evidence views;
- integrated Help and Troubleshooting;
- reproducible reports and exports.

See `docs/ECOSYSTEM_REVIEW_PRODUCT_EXPANSION_2026-10-08.md` and `docs/architecture/V1_PRODUCT_ARCHITECTURE.md` for the canonical expansion record.

## Scientific objective

The project investigates whether public ZTF light curves can be used to construct a reproducible CPU-oriented classifier that provides:

* multiclass object classification;
* class probabilities;
* calibrated confidence estimates;
* set-valued predictions through conformal prediction;
* anomaly / out-of-distribution scores;
* reproducible historical and temporal evaluation.

The intended long-term system is designed for scalable transient and variable-source screening without requiring the full ZTF DR24 archive to be downloaded locally.

## Data strategy

The project uses targeted ZTF light-curve retrieval rather than downloading the complete DR24 catalog.

The benchmark dataset was acquired through the ALeRCE ZTF interface and cached locally as per-object Parquet light curves.

The pipeline is designed around targeted and lazy data access so that the full DR24-scale data volume is not required for development or experimentation.

## Benchmark dataset

Current v0.2 benchmark:

* Objects: **150**
* Classes: **15**
* Objects per class: **10**
* Label source: **ALeRCE**
* Light curves: **ZTF**
* Bands: **g and r where available**
* Labels: weak / reference labels, not independent ground truth

Classes:

* SNIa
* SNIbc
* SNII
* SLSN
* QSO
* AGN
* Blazar
* CV/Nova
* YSO
* LPV
* E
* DSCT
* RRL
* CEP
* Periodic-Other

## Feature engineering

The frozen v0.2 model uses **42 features**.

Feature groups:

1. Cross-band features
2. Observation-quality features
3. Periodicity features
4. Photometric-level features

The frozen feature definition is stored in:

```text
reports/tables/final_feature_set_v0.2.parquet
```

## Model and calibration

The production model uses the frozen v0.2 model configuration and persists the complete inference artifact.

The artifact includes:

* model configuration;
* trained classifier;
* preprocessing state;
* feature schema;
* probability calibration;
* provenance information;
* conformal prediction diagnostics;
* OOD diagnostics and production OOD model.

The current artifact schema is **1.1** and remains backward-compatible with schema **1.0** artifacts.

## Conformal prediction

Conformal diagnostics are calibrated from held-out predictions and persisted with the production artifact.

Production inference can expose:

* significance level (`alpha`);
* conformal threshold;
* prediction set;
* prediction-set size.

Conformal outputs are available through both the JSON prediction interface and the batch Parquet interface.

## Out-of-distribution detection

The production OOD pipeline uses:

* median imputation;
* robust scaling;
* Isolation Forest;
* persisted reference anomaly scores.

The OOD contract contains:

* anomaly score;
* normality score;
* anomaly percentile;
* Isolation Forest label;
* anomaly rank;
* top 1%, 5%, and 10% anomaly flags.

The OOD feature contract contains **42 features**, matching the frozen model feature definition.

## Production inference

The production inference layer loads a persisted artifact and performs inference using the stored model, preprocessing, calibration, conformal diagnostics, and OOD configuration.

Production outputs preserve model and diagnostic metadata so that downstream consumers can distinguish the exact artifact contract used for inference.

## Command-line interface

The CLI is available as:

```text
ztf-classifier {predict,batch}
```

### Model selection

Production inference requires exactly one explicit model-selection mode:

**Direct artifact**

```bash
ztf-classifier predict \
  --artifact PATH_TO_ARTIFACT \
  --input INPUT.parquet \
  --output OUTPUT.json
```

**Registry-backed selection**

```bash
ztf-classifier predict \
  --registry-dir PATH_TO_REGISTRY \
  --model-version baseline_v0.2 \
  --input INPUT.parquet \
  --output OUTPUT.json
```

Do not supply `--artifact` together with `--registry-dir` / `--model-version`; ambiguous model selection is rejected.

### Single prediction output

```bash
ztf-classifier predict \
  --artifact PATH_TO_ARTIFACT \
  --input INPUT.parquet \
  --output OUTPUT.json
```

The JSON output uses CLI schema **1.1** and contains:

* model version;
* model family;
* sample count;
* calibration status;
* conformal status;
* OOD status;
* predicted class;
* predicted class index;
* class probabilities;
* conformal diagnostics when available;
* OOD diagnostics when available.

### Batch prediction output

```bash
ztf-classifier batch \
  --artifact PATH_TO_ARTIFACT \
  --input INPUT.parquet \
  --output OUTPUT.parquet
```

Registry-backed batch inference uses the same explicit selection contract:

```bash
ztf-classifier batch \
  --registry-dir PATH_TO_REGISTRY \
  --model-version baseline_v0.2 \
  --input INPUT.parquet \
  --output OUTPUT.parquet
```

Batch output uses schema **1.1**.

The Parquet file contains prediction columns plus metadata including:

* `ztf_classifier.schema_version`
* `ztf_classifier.model_version`
* `ztf_classifier.model_family`
* `ztf_classifier.has_calibration`
* `ztf_classifier.has_conformal`
* `ztf_classifier.has_ood`
* `ztf_classifier.calibration_status`
* `ztf_classifier.conformal_status`
* `ztf_classifier.ood_status`
* `ztf_classifier.artifact_schema_version`
* `ztf_classifier.artifact_hash`
* `ztf_classifier.feature_schema_hash`
* `ztf_classifier.software_version`

Existing output files are not overwritten.

Empty batch outputs are rejected by the application contract.

## Security and artifact handling

The production OOD artifact contains a `joblib` model file. Treat model artifacts as executable-trust-boundary inputs: only load artifacts from trusted sources and verify their manifest/checksum integrity before loading. Do not accept untrusted `joblib` files in a public inference service.

## Reproducibility

The project is managed with Git and uses a pinned Python development environment.

Primary environment:

* Python **3.11.16**
* Ubuntu 26.04 LTS
* WSL2

The repository contains reproducibility, provenance, checksum validation, ingestion diagnostics, and artifact-contract components intended to make model production and inference auditable. CI uses the committed `requirements.lock` environment captured from a verified Python 3.11.16 Ubuntu runner. The CI gate also validates formatting, coverage reporting, package builds, wheel installation, and dependency security auditing.

## Validation status

The production inference and batch-output contracts are covered by focused automated tests.

Current validated areas include:

* model artifact loading and schema compatibility;
* calibration;
* conformal diagnostics;
* OOD diagnostics;
* production inference;
* CLI prediction output;
* batch Parquet output;
* batch metadata contract;
* batch schema and flag validation;
* rejection of empty batch outputs.

The full test suite is the release gate. CI runs installation, dependency verification, Ruff, the complete pytest suite, and package import verification. Registry-backed prediction and batch paths are covered by real subprocess E2E tests.

The immutable scientific baseline is tag `v0.2.0`; the production model artifact remains version `baseline_v0.2` while the current software release is `v1.0.1`.

## Repository structure

```text
src/ztf_classifier/
├── application/       Application and batch inference services
├── cli/               Command-line interface
├── dataset/           Dataset construction and validation
├── features/          Scientific Feature Engine and extensible backends
├── incremental/       Restart-safe incremental analysis checkpoints
├── catalog/            Durable scientific catalog query/export
├── reporting/          Deterministic scientific report generation
├── io/                ZTF / ALeRCE data access and storage
├── models/             Model, calibration, conformal, OOD, and inference
├── pipeline/          Dataset and model pipelines
├── preprocessing/     Light-curve preprocessing
├── reproducibility/   Environment and reproducibility validation
└── uncertainty/       Uncertainty-related components

tests/                  Automated contract and regression tests
reports/                Frozen benchmark specifications and tables
```

## Scope and scientific limitations

This repository is a production-oriented research pipeline and benchmark foundation. It provides validated production inference interfaces, but the benchmark itself remains intentionally limited and is not a claim of population-level ZTF performance.

The benchmark is intentionally small and balanced. Its labels originate from ALeRCE and therefore should not be interpreted as independent astrophysical ground truth.

Performance measured on the current 150-object benchmark should not be interpreted as representative of the full ZTF population.

The system is intended as a reproducible foundation for future scaling, broader validation, and deployment-oriented development. See `docs/DATA_CARD.md` and `docs/MODEL_CARD.md` for the current dataset and model limitations.


## Current platform direction and scientific-validation boundary

The project is evolving from a classifier-centered research pipeline into an **Astronomical Data Analysis & Discovery Platform**. The intended operational flow is:

`ZTF/source data -> ingestion -> normalization/QC -> scientific feature generation -> ML/statistical analysis -> uncertainty/calibration/OOD -> scientific outputs -> provenance/evidence`

A benchmark is evidence about this system; it is not the system's architecture.

### Current CPVS reconstruction finding

| Population | Objects |
|---|---:|
| CPVS parent | 781,602 rows |
| Published membership | 730,184 |
| Current Seq-based candidates | 741,786 |
| Published ∩ candidate | 730,184 |
| Published-only | 0 |
| Candidate-only | 11,602 |
| Duplicate / unmapped published names | 0 / 0 |

The Seq-based heavy run [#38121913146](https://github.com/saeed92m/ztf-classifier/actions/runs/38121913146) has completed derivation and an independent membership audit. All 730,184 published names map to actual Table2 Seq/SourceID values; the candidate set contains all published objects but 11,602 additional objects, so exact reconstruction remains **UNRESOLVED**. Earlier metrics 725,101 / 16,686 / 5,083 were invalid because they mapped names to row ordinals. The official CPVS ReadMe defines Table2 `Seq` at bytes 24–29 as the internal source identifier used by the lightcurve attachments. Source: https://cdsarc.cds.unistra.fr/viz-bin/ReadMe/J/ApJS/249/18?format=html&tex=true

No threshold or predicate is to be introduced solely to force the candidate cardinality to 730,184 without independent scientific evidence.

### Scientific gate architecture

The repository separates:

- **Product Scientific Gate — release blocking:** validates the actual ingestion/analysis/inference product and its declared evidence contracts.
- **External CPVS Reproduction Evidence — claim-specific fail-closed:** exact historical 730,184/781,602 reproduction remains unresolved until source evidence proves the selection semantics.

An unresolved external reproduction claim must not silently become a product failure. Conversely, the project must not claim exact historical reproduction without exact evidence.

### v1.0.1 release state

- Software release: v1.0.1, published and immutable.
- Release infrastructure is event-driven from successful Scientific Validation and no longer depends on manual dispatch.
- Curated release notes are mandatory for every future release.
- The frozen scientific baseline remains v0.2.0 and the production model remains baseline_v0.2.
- Exact CPVS reconstruction remains UNRESOLVED: the current Seq-based run finds 741,786 candidates, all 730,184 published objects, and 11,602 candidate-only objects with zero published-only or unmapped names. Selection semantics for the extra candidates remain under investigation; no threshold or flag rule may be tuned solely to force the published cardinality.
- This reconstruction discrepancy is not an ML or production failure and must not be hidden or forced away by threshold tuning.

The v1.0.1 software release is published and immutable. The broader discovery platform continues through documented product expansion and independent scientific benchmarking.

## Astronomical Data Analysis & Discovery Platform layer



The classifier is being expanded into a unified astronomical analysis application while preserving the frozen scientific v0.2.0 baseline.

Current platform contracts include:

* normalized ALeRCE-backed observation APIs;
* source-backed single-object scientific analysis;
* persistent analysis jobs with leases and stable result references;
* a durable scientific-result repository;
* Workbench views backed by real observations and persisted results;
* paginated scientific catalog queries and deterministic CSV export;
* deterministic Markdown reports derived from persisted scientific results;
* restart-safe incremental result cursors and durable checkpoints;
* an extensible Scientific Feature Engine with explicit backend registration, schema versions, and provenance;
* optional API-key protection for versioned endpoints and generated request IDs.

The native feature backend remains the default and preserves the frozen 42-feature v0.2 contract. New feature backends are versioned independently and do not mutate historical results.

### API and Workbench

The FastAPI service exposes the versioned API contract documented in docs/api/API_V1.md. The Scientific Analysis Workbench is served at /workbench/ and consumes the same API boundaries rather than duplicating scientific logic.

Runtime result/job/checkpoint databases are external runtime state and are intentionally ignored by Git. Deployment configuration is documented in .env.example.


## Discovery-platform contract status

The platform architecture now has executable domain contracts for external catalog/cross-match context, diagnostic separation, discovery candidates and human review, controlled learning feedback, explainability evidence, and explicit light-curve/image/catalog modality declarations. These contracts extend the platform without changing the immutable v0.2.0 scientific baseline or introducing parity-driven GPU, LLM, DVC, or distributed infrastructure.

The current production model explicitly does **not** claim a scientific-anomaly detector: OOD diagnostics and scientific anomaly evidence are separate result channels. Scientific anomaly evidence remains `not_evaluated` until a dedicated analysis mode supplies and versions such evidence.


## Current project roadmap and status (2026-10-11)

- Current immutable software release: **v1.0.1**; frozen scientific baseline: **v0.2.0**.
- Canonical continuity handbook: [HANDBOOK_UPDATED_v2.8.md](docs/HANDBOOK_UPDATED_v2.8.md).
- Canonical cross-platform product roadmap: [PLATFORM_EXPANSION_ROADMAP.md](docs/roadmap/PLATFORM_EXPANSION_ROADMAP.md).
- Scientific validation roadmap: [SCIENTIFIC_VALIDATION_ROADMAP.md](docs/roadmap/SCIENTIFIC_VALIDATION_ROADMAP.md).
- Current CPVS exact-reconstruction blocker: [Issue #170](https://github.com/saeed92m/ztf-classifier/issues/170). Schema review identified that both derivation and audit substituted physical row ordinals for CPVS Table2 Seq / lightcurve SourceID. The 725,101 / 16,686 / 5,083 metrics from run [#38095650470](https://github.com/saeed92m/ztf-classifier/actions/runs/38095650470) are therefore invalid. PR #176 now reads actual Seq IDs and adds non-contiguous-ID regression coverage; updated heavy evidence is required before making membership claims.
- Desktop product acceptance target: [Issue #158](https://github.com/saeed92m/ztf-classifier/issues/158). The platform is not considered complete until clean-machine, non-developer end-to-end workflows and supported-OS packaging are verified.
