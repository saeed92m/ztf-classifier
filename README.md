# ZTF Classifier

**ZTF Classifier** is a cross-platform, CPU-first **Astronomical Data Analysis & Discovery Platform** built around Zwicky Transient Facility (ZTF) data. Classification is a core scientific capability of the platform, alongside observation acquisition and validation, scientific feature generation, time-series and light-curve analysis, transient and variable-object analysis, anomaly/OOD diagnostics, production inference, persistent analysis jobs, provenance, and discovery-oriented workflows.

The project is designed as a reproducible, extensible scientific-computing foundation: the frozen benchmark and production model remain stable while the surrounding platform can evolve toward broader data sources, richer feature backends, persistent scientific history, catalog/report generation, continuous analysis, and a full Scientific Analysis Workbench.

## Project status

**Software milestone:** `v0.4.0`  
**Scientific baseline:** `v0.2.0` (immutable)  
**Production model:** `baseline_v0.2`  
**Current direction:** Web/API product layer, scientific analysis workflows, persistent jobs, and platform expansion

The `v0.2.0` scientific baseline is immutable. Later releases and platform capabilities do not silently redefine its historical benchmark, feature schema, or model identity.

## Platform capabilities

The current system combines the following capabilities:

- targeted ZTF/ALeRCE light-curve and detection acquisition;
- strict observation validation, normalization, and quality-control diagnostics;
- deterministic scientific feature generation;
- an extensible Scientific Feature Engine boundary;
- time-series and light-curve analysis;
- transient and variable-object analysis;
- multiclass machine-learning classification;
- calibrated class probabilities;
- split-conformal prediction diagnostics;
- out-of-distribution (OOD) and anomaly diagnostics;
- persisted production model artifacts;
- registry-backed model selection and provenance;
- single-object and batch inference;
- versioned HTTP API contracts;
- source-backed end-to-end object analysis;
- durable SQLite-backed analysis jobs and worker execution;
- scientific provenance and reproducibility metadata;
- a Scientific Analysis Workbench presentation layer.

Classification remains a first-class capability, but it is one component of the broader astronomical analysis and discovery platform.

## Scientific workflow

The canonical object-analysis path is:

```text
ZTF / ALeRCE source
        ↓
Acquisition
        ↓
Validation / QC
        ↓
Normalization
        ↓
Scientific Feature Engine
        ↓
ML inference
   ┌────┼───────────────┐
   ↓    ↓               ↓
Class  Conformal       OOD
prob.  diagnostics     diagnostics
   └────┼───────────────┘
        ↓
Unified scientific result
        ↓
API / CLI / Workbench / Jobs
```

The architecture keeps scientific computation independent from HTTP and UI concerns. The same scientific execution boundary can therefore support interactive analysis, CLI workflows, persistent jobs, batch processing, and future schedulers.

## Data strategy

The platform uses targeted and lazy scientific data access rather than requiring the complete ZTF archive to be stored inside the repository.

Current acquisition is source-backed through the ALeRCE adapter and ZTF observations. Normalized observations preserve scientific measurements, quality information, coordinates where available, acquisition context, and provenance.

Large scientific datasets, caches, generated reports, model runs, and local outputs are intentionally kept outside Git. Repository size is therefore decoupled from scientific-data volume.

Future source connectors can implement the same canonical observation contract without changing downstream scientific consumers.

## Benchmark dataset

The controlled `v0.2` benchmark contains:

| Property | Value |
| --- | --- |
| Objects | **150** |
| Classes | **15** |
| Objects per class | **10** |
| Label source | ALeRCE |
| Photometry source | ZTF |
| Bands | g and r where available |
| Dataset identity | `benchmark_v0.2` |
| Label interpretation | Reference/weak labels, not independent ground truth |

Classes:

- SNIa
- SNIbc
- SNII
- SLSN
- QSO
- AGN
- Blazar
- CV/Nova
- YSO
- LPV
- E
- DSCT
- RRL
- CEP
- Periodic-Other

The benchmark is a controlled validation asset. Its measurements must not be interpreted as population-level performance for the full ZTF survey.

See [Data Card](docs/DATA_CARD.md) for dataset identity, provenance, and limitations.

## Scientific Feature Engine

Scientific feature generation is a first-class, extensible subsystem rather than a permanent implementation of the frozen 42-column benchmark.

The initial `native` backend preserves the frozen `v0.2` feature contract. Each engine result records the feature schema, backend identity, backend version, parameters, and a SHA-256 identity of the normalized observation input.

The architecture allows additional scientific feature backends to be introduced without redefining the historical benchmark.

The frozen `v0.2` model uses **42 features**. This number describes the historical production model contract; it is not a ceiling on the platform's future scientific feature space.

See [Scientific Feature Engine](docs/SCIENTIFIC_FEATURE_ENGINE_v0.1.md) and [Feature Provenance Contract](docs/FEATURE_PROVENANCE_CONTRACT.md).

## Production model

The current production model is:

- model version: `baseline_v0.2`;
- model family: XGBoost;
- artifact schema: **1.1**;
- feature schema: frozen `v0.2`;
- classes: **15**;
- calibration: temperature scaling;
- conformal diagnostics: persisted;
- OOD diagnostics: persisted;
- provenance: persisted;
- artifact manifest/checksum: persisted.

Artifact schemas **1.0** and **1.1** remain readable.

See [Model Card](docs/MODEL_CARD.md) for model identity, evaluation context, and limitations.

## Calibration, conformal prediction, and OOD

### Calibration

Production inference can expose calibrated class probabilities when calibration is present in the selected artifact.

### Conformal prediction

Conformal diagnostics are calibrated from held-out predictions and persisted with the production artifact.

Available outputs include:

- significance level (`alpha`);
- conformal threshold;
- prediction set;
- prediction-set size.

### Out-of-distribution detection

The production OOD pipeline uses:

- median imputation;
- robust scaling;
- Isolation Forest;
- persisted reference anomaly scores.

The OOD contract includes:

- anomaly score;
- normality score;
- anomaly percentile;
- Isolation Forest label;
- anomaly rank;
- top 1%, 5%, and 10% anomaly flags.

The OOD feature contract currently follows the frozen 42-feature model contract.

## Production inference and model selection

Production inference requires exactly one explicit model-selection mode.

### Direct artifact

```bash
ztf-classifier predict \
  --artifact PATH_TO_ARTIFACT \
  --input INPUT.parquet \
  --output OUTPUT.json
```

### Registry-backed selection

```bash
ztf-classifier predict \
  --registry-dir PATH_TO_REGISTRY \
  --model-version baseline_v0.2 \
  --input INPUT.parquet \
  --output OUTPUT.json
```

Do not combine `--artifact` with `--registry-dir` / `--model-version`. Ambiguous model selection is rejected.

The same explicit selection contract applies to batch inference:

```bash
ztf-classifier batch \
  --registry-dir PATH_TO_REGISTRY \
  --model-version baseline_v0.2 \
  --input INPUT.parquet \
  --output OUTPUT.parquet
```

Existing output files are not overwritten and empty batch outputs are rejected by the application contract.

## Command-line interface

Available production entry points include:

```text
ztf-classifier
ztf-classifier-api
ztf-classifier-worker
```

The CLI provides production single-object and batch inference. The API and worker entry points expose the platform's service and asynchronous execution boundaries.

## Web/API platform

The HTTP API is an adapter around application and scientific services. FastAPI does not own model loading rules, scientific feature semantics, inference logic, or provenance construction.

Current API surface:

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/health` | Liveness |
| GET | `/ready` | Model-registry readiness |
| GET | `/v1/model` | Model metadata |
| POST | `/v1/predict` | Synchronous inference |
| POST | `/v1/batch` | Synchronous multi-row inference |
| GET | `/v1/objects/{oid}` | Object summary |
| GET | `/v1/objects/{oid}/observations` | Normalized observations |
| POST | `/v1/objects/{oid}/analysis` | Complete source-backed analysis |
| POST | `/v1/objects/{oid}/jobs` | Create durable analysis job |
| GET | `/v1/jobs/{job_id}` | Retrieve durable job state |

The API preserves model identity, diagnostic status, prediction results, conformal/OOD diagnostics, warnings, and provenance while preventing internal filesystem paths from becoming public API data.

See [API v1 Contract](docs/api/API_V1.md).

## Persistent analysis jobs

Long-running object analysis can be persisted as durable jobs.

Current implementation:

- SQLite-backed job store;
- lifecycle: `queued → running → succeeded / failed`;
- atomic queue claiming with SQLite `BEGIN IMMEDIATE`;
- dependency-injected scientific execution boundary;
- source-backed executor;
- persisted observations, features, prediction diagnostics, and provenance;
- stable public failure codes;
- protected execution boundary for expected scientific failures;
- preservation of unexpected programmer failures;
- production worker entry point: `ztf-classifier-worker`;
- scheduler-safe non-zero worker exit when drained jobs fail.

The worker connects the durable job layer to the same scientific path used by direct object analysis:

```text
Job
 ↓
ALeRCE acquisition
 ↓
Normalization / QC
 ↓
Scientific Feature Engine
 ↓
Registered model inference
 ↓
Scientific result + provenance
```

See [Persistent Analysis Job Worker](docs/api/ANALYSIS_JOB_WORKER.md).

## Scientific Analysis Workbench

The project includes a presentation-layer Scientific Analysis Workbench served at:

```text
/workbench/
```

The Workbench is designed around scientific inspection rather than generic administration. Its current presentation surfaces include:

- object analysis;
- light-curve visualization;
- classification probabilities;
- scientific metadata and provenance;
- analysis state;
- batch/catalog/report navigation;
- responsive layouts;
- appearance preferences.

The Workbench consumes API contracts and does not embed scientific inference logic.

The current presentation system supports:

- **Auto** — default, follows local clock;
- **System** — follows OS/browser appearance;
- **Deep Space** — dark scientific/observatory theme;
- **Alpha Theme** — Alpha Team brand theme;
- **Light** — light research-lab theme.

Scientific chart palettes remain separate from UI branding.

See [Scientific Analysis Workbench UI Contract](docs/ui/SCIENTIFIC_WORKBENCH_UI_v0.1.md).

## Reproducibility and provenance

Reproducibility is a system-level concern.

The project maintains:

- pinned Python environment;
- committed `requirements.lock`;
- SHA-256 checksum utilities;
- artifact manifest hashing;
- software, dataset, feature, and model provenance;
- ingestion diagnostics;
- feature provenance contracts;
- dataset and model cards;
- CI validation;
- package build and wheel-install verification.

Primary development environment:

- Python **3.11.16**;
- Ubuntu **26.04 LTS**;
- WSL2;
- pyenv + `.venv`.

For a locked environment matching CI:

```bash
python -m pip install -r requirements.lock
python -m pip install -e . --no-deps
python -m pip check
```

## Validation and CI

The full test suite is the release gate.

CI validates:

1. Python 3.11.16 environment;
2. locked dependency installation;
3. package installation;
4. dependency consistency with `pip check`;
5. Ruff linting;
6. formatting of protected upgrade modules;
7. complete pytest suite with coverage;
8. source distribution/wheel build;
9. built-wheel installation;
10. package import;
11. dependency security auditing with `pip-audit`.

Real subprocess E2E paths cover registry-backed prediction and batch inference.

The current repository state also contains contract tests for observation acquisition, scientific feature generation, production inference, the API boundary, persistent jobs, source-backed execution, and worker lifecycle semantics.

## Security and artifact handling

Production model artifacts can contain serialized `joblib` objects. Treat model artifacts as executable-trust-boundary inputs.

Only load model artifacts from trusted sources and validate their manifest/checksum integrity before loading. Do not accept untrusted `joblib` files in a public inference service.

The public API is designed to avoid accepting arbitrary server filesystem paths and to avoid exposing internal paths through public provenance.

## Repository architecture

```text
src/ztf_classifier/
├── domain/             Scientific/domain contracts
├── application/        Application services and inference orchestration
├── api/                Versioned HTTP boundary
├── cli/                Command-line interfaces
├── dataset/             Dataset construction and validation
├── features/            Scientific feature generation and engine
├── io/                  ZTF / ALeRCE acquisition and storage adapters
├── models/              Model, calibration, conformal, OOD, inference
├── pipeline/            Dataset and model pipelines
├── preprocessing/      Light-curve preprocessing
├── reproducibility/    Checksums and reproducibility validation
├── uncertainty/        Uncertainty-related components
├── jobs/               Persistent analysis jobs and worker execution
└── web/                Scientific Workbench presentation assets

tests/                   Automated contract, integration, and regression tests
docs/                    Architecture, API, scientific, UI, and continuity documentation
reports/                 Frozen benchmark specifications and validation reports
```

The important architectural boundary is:

```text
Presentation / API / CLI
          ↓
Application services
          ↓
Domain + scientific execution
          ↓
Infrastructure / external sources
```

Scientific logic remains reusable across interfaces.

## Scientific limitations

The current benchmark is deliberately small:

- 150 objects;
- 15 classes;
- 10 objects per class;
- ALeRCE reference labels;
- frozen 42-feature model contract.

The benchmark is not representative of the full ZTF population, and ALeRCE labels are not independent astrophysical ground truth.

The current production implementation should therefore be understood as a validated research and product foundation, not as a claim of survey-scale scientific performance.

Future scientific validation must expand dataset size and diversity, evaluate label quality and uncertainty, test temporal and historical generalization, examine class imbalance and selection effects, and validate performance on independently curated data.

## Product direction

The platform is being developed toward a broader astronomical analysis and discovery system while preserving the validated scientific core.

The intended evolution is:

```text
Scientific data sources
        ↓
Ingestion / QC / normalization
        ↓
Scientific Feature Engine
        ↓
Analysis + ML + uncertainty
        ↓
Persistent scientific results
        ↓
Catalogs / reports / API
        ↓
Scientific Analysis Workbench
        ↓
Continuous and incremental discovery workflows
```

Planned expansion areas include:

- additional astronomical data-source connectors;
- richer scientific feature backends;
- scalable feature computation;
- persistent scientific-result storage;
- durable retry and lease semantics;
- catalog and report generation;
- batch and continuous/incremental analysis;
- cross-match and enrichment workflows;
- production observability and deployment;
- larger-scale scientific validation;
- future ML model generations beyond the frozen `baseline_v0.2` contract.

The frozen `v0.2.0` scientific baseline remains the reference point while these capabilities evolve around it.

## Versioning and releases

Important project identities are intentionally separated:

| Identity | Current value |
| --- | --- |
| Software milestone | `v0.4.0` |
| Immutable scientific baseline | `v0.2.0` |
| Dataset contract | `benchmark_v0.2` |
| Production model | `baseline_v0.2` |
| Artifact schema | `1.1` |
| CLI/output schema | `1.1` |

This separation prevents platform evolution from silently changing the scientific benchmark or production model contract.

See [CHANGELOG](CHANGELOG.md) for release history.

## Documentation

Key project documents:

- [Data Card](docs/DATA_CARD.md)
- [Model Card](docs/MODEL_CARD.md)
- [Scientific Feature Engine](docs/SCIENTIFIC_FEATURE_ENGINE_v0.1.md)
- [Feature Provenance Contract](docs/FEATURE_PROVENANCE_CONTRACT.md)
- [API v1 Contract](docs/api/API_V1.md)
- [Persistent Analysis Job Worker](docs/api/ANALYSIS_JOB_WORKER.md)
- [Scientific Analysis Workbench UI](docs/ui/SCIENTIFIC_WORKBENCH_UI_v0.1.md)
- [Project Continuity Handbook](docs/HANDBOOK_UPDATED_v1.9.md)
- [Changelog](CHANGELOG.md)

## Project identity

**ZTF Classifier**  
*Astronomical Data Analysis & Discovery Platform*

The name reflects the project's origin in ZTF object classification; the platform architecture now provides a broader scientific analysis and discovery foundation around that core capability.
