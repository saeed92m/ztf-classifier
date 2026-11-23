# ZTF Classifier — Quick Start

## Goal
Run the released v1.0.1 production inference path with a trusted, compatible v0.2.0 model artifact. This workflow does not acquire or normalize native DR24 light curves.

## 1. Environment
Python 3.11 is required.

    python3.11 -m venv .venv
    source .venv/bin/activate
    python -m pip install --upgrade pip
    python -m pip install ztf-classifier==1.0.1
    ztf-classifier --help

## 2. Prepare a compatible input
Production inference expects a Parquet dataset that follows the frozen final_feature_set_v0.2 contract. The contract has 42 features. Do not rename, reorder, synthesize, or substitute features.

The model artifact is not included in the Python wheel or source distribution. Obtain it through the project's controlled artifact workflow and verify its manifest and hashes before use.

## 3. Run inference
Single prediction:

    ztf-classifier predict --artifact PATH_TO_ARTIFACT --input INPUT.parquet --output OUTPUT.json

Batch prediction:

    ztf-classifier batch --artifact PATH_TO_ARTIFACT --input INPUT.parquet --output OUTPUT.parquet

The alternative registry mode requires both --registry-dir and --model-version baseline_v0.2. Do not combine artifact and registry selection modes.

## 4. Interpret results
Keep predicted class/probabilities, calibration, conformal prediction sets, and OOD diagnostics separate. OOD is not an astrophysical anomaly. A high OOD score alone is not evidence of a new astrophysical object.

ALeRCE labels are benchmark/reference labels, not independent ground truth.

## 5. DR24 status
The native DR24 acquisition adapter is under review in PR #264. It is a raw-data interface, not an accepted normalized DR24-to-feature-to-inference path. Do not send DR24 native measurements into the frozen v0.2.0 model.

## 6. Reproducibility
Retain input files and hashes, object IDs, source/version, feature schema, model version, artifact hash, software version, run configuration, outputs, warnings, and validation status.

The scientific baseline is v0.2.0. The software release is v1.0.1.
