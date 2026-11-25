# Installation

**Software release:** v1.0.1  
**Supported Python:** >=3.11.5,<3.12  
**Recommended development environment:** Ubuntu or WSL2

## Install the published package

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install ztf-classifier==1.0.1
ztf-classifier --help
```

The package provides CLI and API entry points. It does not include the full ZTF archive, the frozen benchmark data, or the original v0.2.0 production model artifact.

## Start the API and Workbench

```bash
ztf-classifier-api
```

Open `http://127.0.0.1:8000/workbench/` in a browser on the same machine.

## Install DR24 Explorer dependencies from source

The bounded DR24 raw Explorer requires the optional `dr24` dependencies. Use an isolated checkout:

```bash
git clone https://github.com/saeed92m/ztf-classifier.git
cd ztf-classifier
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.lock
python -m pip install -e ".[dr24]"
ztf-classifier-api
```

The DR24 Explorer supports raw light-curve retrieval and inspection. It does not run the frozen v0.2.0 classifier on DR24.

## Model artifact requirement

Production inference requires a trusted, authenticated model artifact. The original `baseline_v0.2` artifact is not included in the v1.0.1 wheel or source archive and has not been recovered from accessible remote sources. See [Issue #282](https://github.com/saeed92m/ztf-classifier/issues/282).

Do not use the schema-1.1 lab-smoke artifact as a production substitute. Do not claim that model inference is ready until the original artifact and its independent provenance are verified.

## Data

Do not download the full multi-terabyte ZTF archive for normal use. Use bounded, documented source adapters. Preserve source release, query, identifiers, schemas, retrieval time, row counts, and hashes.

## Park demonstrator

Follow the [Park Laboratory Demonstrator Runbook](acceptance/PARK_LABORATORY_DEMONSTRATOR_RUNBOOK_2026-11-18.md). A failed or skipped live test is not acceptance.
