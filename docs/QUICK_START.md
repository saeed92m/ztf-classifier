# ZTF Classifier — Quick Start

## Goal

Run the released v1.0.0 production inference path without downloading the complete ZTF archive.

## 1. Create an environment

Python 3.11 is required.

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install ztf-classifier==1.0.0
```

Verify the installation:

```bash
ztf-classifier --help
```

## 2. Prepare a Parquet input

Production inference expects a Parquet dataset containing the frozen v0.2 feature schema.

For the baseline model, the feature contract is the immutable 42-feature definition. Do not rename, reorder, synthesize, or silently substitute features.

## 3. Run single-object/batch-style JSON inference

Use a trusted production artifact:

```bash
ztf-classifier predict \
  --artifact PATH_TO_ARTIFACT \
  --input INPUT.parquet \
  --output OUTPUT.json
```

Or use the explicit registry contract:

```bash
ztf-classifier predict \
  --registry-dir PATH_TO_REGISTRY \
  --model-version baseline_v0.2 \
  --input INPUT.parquet \
  --output OUTPUT.json
```

Never provide both model-selection modes.

## 4. Run Parquet batch inference

```bash
ztf-classifier batch \
  --artifact PATH_TO_ARTIFACT \
  --input INPUT.parquet \
  --output OUTPUT.parquet
```

The output contains prediction columns and versioned metadata for the model, feature schema, artifact, software, calibration, conformal diagnostics, and OOD diagnostics.

Existing output files are intentionally not overwritten.

## 5. Interpret the result correctly

The production result has separate channels:

- classification/predicted class;
- calibrated probabilities;
- conformal prediction sets;
- OOD diagnostics.

OOD is not the same as an astrophysical anomaly. A scientifically anomalous-object claim requires dedicated scientific-anomaly evidence and is not implied by a high OOD score.

## 6. Reproducibility

For a reproducible analysis, retain:

- input/source identity;
- retrieval/version information;
- object identifiers;
- feature-schema identity;
- model version;
- artifact hash;
- software version;
- output artifact;
- relevant provenance/evidence manifests.

The immutable scientific baseline is v0.2.0 and the production model identity is baseline_v0.2. The software release is v1.0.0.

## 7. Continue to the full workflows

- Installation: `docs/INSTALLATION.md`
- User workflow: `docs/USER_GUIDE.md`
- Scientific methodology: `docs/SCIENTIFIC_METHODOLOGY.md`
- API v1: `docs/api/API_V1.md`
- Data limitations: `docs/DATA_CARD.md`
- Model limitations: `docs/MODEL_CARD.md`

The platform is designed for targeted source acquisition and scientific analysis; a full ZTF archive download is not required for the baseline workflow.
