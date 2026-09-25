# ZTF Classifier

A CPU-oriented machine-learning research pipeline for classification of astronomical transient and variable objects using public Zwicky Transient Facility (ZTF) light-curve data.

## Project status

**Version:** v0.4.0
**Status:** Hardened production-oriented research pipeline with reproducibility, provenance, registry-backed inference, strict ingestion diagnostics, and validated CLI E2E paths

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

The immutable scientific baseline is tag `v0.2.0`; the production model artifact remains version `baseline_v0.2` while the software package milestone is `v0.4.0`.

## Repository structure

```text
src/ztf_classifier/
├── application/       Application and batch inference services
├── cli/               Command-line interface
├── dataset/           Dataset construction and validation
├── features/          Feature engineering
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
