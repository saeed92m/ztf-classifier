# ZTF Classifier — Quick Start

**Software release:** v1.0.1  
**Scientific baseline:** v0.2.0 (immutable)

## 1. Install the package

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install ztf-classifier==1.0.1
ztf-classifier --help
```

## 2. Start the API and Workbench

```bash
ztf-classifier-api
```

Open `http://127.0.0.1:8000/workbench/`.

## 3. DR24 raw-data exploration

For the raw DR24 Explorer, use the source installation procedure in [Installation](INSTALLATION.md) and install the `dr24` extra.

The Explorer can request 1–10 positive DR24 OIDs through the indexed HATS API. It displays source-native epochs, a light curve, diagnostic QC, provenance, and raw JSON export.

The Explorer is an experimental raw-data inspection path. It does not infer physical identity across OIDs, apply an approved production quality mask, convert HMJD or photometry to the frozen v0.2.0 contract, generate the frozen 42-feature vector, or run the frozen v0.2.0 model on DR24.

See [DR24 Explorer](user/DR24_EXPLORER.md) and the [Park runbook](acceptance/PARK_LABORATORY_DEMONSTRATOR_RUNBOOK_2026-11-18.md).

## 4. Production inference

```bash
ztf-classifier predict \
  --artifact PATH_TO_AUTHENTICATED_ARTIFACT \
  --input INPUT.parquet \
  --output OUTPUT.json
```

The input must satisfy the frozen 42-feature schema. Use only a trusted artifact with a verified manifest and independent provenance.

**Important:** the original frozen `baseline_v0.2` production artifact is not available in accessible remote sources. Recovery remains open in [Issue #282](https://github.com/saeed92m/ztf-classifier/issues/282). The published package does not include model weights. Do not use the lab-smoke artifact as a substitute.

## 5. Interpret outputs

Keep predicted class, calibrated probability, conformal prediction, OOD, and scientific-anomaly evidence separate. A raw score is not a calibrated probability. A high OOD score is not proof of an astrophysical anomaly. Missing or unsupported data must produce an explicit blocked state.

## 6. Reproducibility

Retain source identity, release, query, object IDs, schema, feature contract, model version, artifact hash, software version, output files, and evidence manifests. ALeRCE labels are reference/weak labels, not independent astrophysical ground truth.
