# ZTF Classifier — Quick Start

**Software release:** v1.0.1
**Scientific baseline:** v0.2.0 (immutable)

## 1. Install the package

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install ztf-classifier==1.0.1
```

Verify the installation:

```bash
ztf-classifier --help
```

## 2. Start the API and Workbench

```bash
ztf-classifier-api
```

Open `http://127.0.0.1:8000/workbench/`.

## 3. Inspect raw DR24 data

For the bounded DR24 Explorer, install from source with the `dr24` extra as described in [Installation](INSTALLATION.md). The Explorer supports bounded OID requests, raw light-curve inspection, diagnostic QC, acquisition provenance, and JSON export. Follow the [Park Runbook](acceptance/PARK_LABORATORY_DEMONSTRATOR_RUNBOOK_2026-11-18.md).

This path does not establish physical identity across OIDs, an approved production quality mask, conversion to the frozen v0.2.0 feature contract, or classification on DR24. Keep HMJD and native photometry semantics explicit.

## 4. Production inference status

The original `baseline_v0.2` production artifact has not been recovered and authenticated. Production inference therefore remains **BLOCKED**. Do not substitute the lab-smoke artifact. The frozen feature contract remains 42 features; no feature order or scientific baseline was changed by the Park documentation integration.

For a separately authenticated artifact, the documented CLI shape is:

```bash
ztf-classifier predict \
  --artifact PATH_TO_AUTHENTICATED_ARTIFACT \
  --input INPUT.parquet \
  --output OUTPUT.json
```

This example does not imply that the required production artifact is available or that inference passed a scientific gate.

## 5. Interpretation and reproducibility

Do not treat raw scores as calibrated probabilities, OOD as astrophysical anomaly, or ALeRCE reference labels as independent astrophysical truth. Retain source/release, query, OID, schema, feature/model identity where applicable, software revision, output hashes, and provenance manifests.

See [Installation](INSTALLATION.md), [User Guide](USER_GUIDE.md), [Scientific Methodology](SCIENTIFIC_METHODOLOGY.md), [API documentation](api/API_V1.md), [Data Card](DATA_CARD.md), and [Model Card](MODEL_CARD.md).
