# ZTF Classifier

A CPU-first Astronomical Data Analysis & Discovery Platform for Zwicky Transient Facility (ZTF) data, scientific feature generation, machine-learning and statistical analysis, uncertainty/OOD diagnostics, provenance, and discovery-oriented workflows.

## Current project documentation
- [Persian Park technical status addendum — 2026-11-07](docs/acceptance/PARK_TECHNICAL_STATUS_ADDENDUM_2026-11-07.fa.md)

- [Project Continuity Handbook v3.0](docs/HANDBOOK_UPDATED_v3.0.md)
- [Project Status & Execution Ledger — 2026-11-07](docs/PROJECT_STATUS_AND_EXECUTION_LEDGER_2026-11-07.md)
- [Park MVP Delivery Plan](docs/PARK_MVP_DELIVERY_PLAN_2026-11-05.md)
- [Platform Expansion Roadmap](docs/roadmap/PLATFORM_EXPANSION_ROADMAP.md)

- [Project Continuity Handbook v3.0](docs/HANDBOOK_UPDATED_v3.0.md)
- [Project Status & Execution Ledger — 2026-11-10](docs/PROJECT_STATUS_AND_EXECUTION_LEDGER_2026-11-10.md)
- [Park Pilot Readiness Report — 2026-11-10 (Persian)](docs/acceptance/PARK_PILOT_READINESS_2026-11-10.fa.md)
- [Park Acceptance Form Reconciliation — 2026-11-10 (Persian)](docs/acceptance/PARK_ACCEPTANCE_FORM_RECONCILIATION_2026-11-10.fa.md)

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


## Current project roadmap and status (2026-11-10)

- Current immutable software release: **v1.0.1**.
- Frozen scientific baseline: **v0.2.0**.
- Production model identity: **baseline_v0.2**.
- Benchmark: 150 ZTF objects, 15 ALeRCE reference classes, 10 objects per class.
- Frozen feature contract: 42 features in `final_feature_set_v0.2`.
- Historical cutoff: `59447.224132`.
- Current continuity handbook: [HANDBOOK_UPDATED_v2.9.md](docs/HANDBOOK_UPDATED_v2.9.md).
- Current project execution ledger: [PROJECT_STATUS_AND_EXECUTION_LEDGER_2026-11-07.md](docs/PROJECT_STATUS_AND_EXECUTION_LEDGER_2026-11-07.md).
- Current Park delivery plan: [PARK_MVP_DELIVERY_PLAN_2026-11-05.md](docs/PARK_MVP_DELIVERY_PLAN_2026-11-05.md).
- Full integrity audit and remediation record: [PROJECT_AUDIT_AND_REMEDIATION_2026-11-10.md](docs/PROJECT_AUDIT_AND_REMEDIATION_2026-11-10.md).

### Product delivery boundary

The current `main` application observation service uses ALeRCE by default. DR24 HATS acquisition, multi-OID API work, raw-preserving QC diagnostics, Workbench exploration and the HATS/Zubercal source decision remain in open pull requests. They are not yet an accepted end-to-end DR24 production path.

The latest scheduled source-backed workflow on main, [run 42611080798](https://github.com/saeed92m/ztf-classifier/actions/runs/42611080798), successfully acquired bounded DR24 and ALeRCE source evidence, the frozen historical ALeRCE reference manifest and the independent StarEmbed source package. These results verify source acquisition and evidence contracts for their declared scope. They do not establish DR24 model performance, a 100,000-light-curve dataset, a completed 5–10 object workflow, a 30–50 object demo, or Park acceptance.

The original v0.2.0 production artifact at `runs/model_baseline_v0.2_production/artifact` is not present in the repository tree or the published wheel. Its current status is **UNRECOVERED**, not proven destroyed. A separate lab-smoke artifact is not an approved replacement. Large model and raw-data artifacts must remain outside Git and must be supplied through a controlled, hash-verified source.

Do not publish a completion percentage unless the weighting method and current evidence are defined. Do not describe component smoke tests or skipped scientific jobs as scientific product acceptance.

### CPVS historical reconstruction boundary

[Issue #170](https://github.com/saeed92m/ztf-classifier/issues/170) remains **OPEN / UNRESOLVED**. The retained Seq-based comparison reports 781,602 parent objects, 730,184 published reference members, 741,786 reconstructed candidates, 11,602 candidate-only and zero published-only objects.

The four-field-positive and `Ng/Nr >= 11` results in the approved CPVS Master Handoff are diagnostic hypotheses. Their source ID lists and hashes still require reconciliation. The handoff contains an internal set-arithmetic inconsistency for the four-field intersection. Missing photometry is `UNKNOWN`, not SNR `FAIL`. No production predicate or threshold may be changed to force cardinality equality.

CPVS remains a separate historical-research lane. It does not block the DR24-first product delivery and it is not resolved by product CI.

### Separate architecture workstreams

- AOIC: proposed canonical identity and cross-match architecture, tracked by [Issue #249](https://github.com/saeed92m/ztf-classifier/issues/249). A complete canonical identity registry is not yet merged.
- CIN: optional human-in-the-loop architecture and staged plan, tracked by [Issue #251](https://github.com/saeed92m/ztf-classifier/issues/251) and [PR #252](https://github.com/saeed92m/ztf-classifier/pull/252). No production contributor network, annotation corpus or controlled pilot is claimed.
- Cross-platform desktop installers: not yet verified on clean Windows, macOS and Linux machines. Release v1.0.1 is a Python package, not a self-contained installer.

### Active delivery trackers

- [Issue #158 — Park prototype and product delivery](https://github.com/saeed92m/ztf-classifier/issues/158)
- [Issue #253 — DR24 application acquisition adapter](https://github.com/saeed92m/ztf-classifier/issues/253)
- [Issue #170 — CPVS exact historical reconstruction](https://github.com/saeed92m/ztf-classifier/issues/170)
- [PR #266 — Park plan, handbook and status synchronization](https://github.com/saeed92m/ztf-classifier/pull/266)

