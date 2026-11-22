# Installation

**Software release:** v1.0.1
**Supported Python:** >=3.11.5,<3.12
**Recommended development environment:** Ubuntu or WSL2

## Install the package

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install ztf-classifier==1.0.1
ztf-classifier --help
```

This installation command is documentation; a clean-machine installation was not verified by the Park integration checks. The package does not include the full ZTF archive, frozen benchmark data, or the original v0.2.0 production model artifact. Distribution remains subject to the project's license and release gates.

## Start the API and Workbench

```bash
ztf-classifier-api
```

Open `http://127.0.0.1:8000/workbench/` in a browser on the same machine. Runtime and browser behavior for the combined integration HEAD have not been verified locally in this documentation task.

## Install DR24 Explorer dependencies from source

The bounded DR24 raw Explorer uses the optional `dr24` dependencies:

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

This source-install procedure has not been verified on a clean machine in this task. The Explorer is for bounded, raw DR24 light-curve retrieval and inspection. It does not run the frozen v0.2.0 classifier on DR24.

## Model artifact and data

Production inference requires a trusted, authenticated model artifact. The original `baseline_v0.2` artifact is not included in the v1.0.1 package and remains unrecovered in the audit evidence available to this project. Do not use the schema-1.1 lab-smoke artifact as a substitute. Production inference remains **BLOCKED** until the original artifact is authenticated or a separately approved model passes its own scientific gate.

Do not download the full ZTF archive for normal use. Preserve source release, query, identifiers, schemas, retrieval time, row counts, and hashes for bounded acquisitions.

## Park demonstrator

Follow the [Park Laboratory Demonstrator Runbook](acceptance/PARK_LABORATORY_DEMONSTRATOR_RUNBOOK_2026-11-18.md). PR-associated CI evidence is distinct from a local run on the combined integration HEAD. A failed or skipped live test is not acceptance.

See also [Quick Start](QUICK_START.md), [User Guide](USER_GUIDE.md), [API documentation](api/API_V1.md), and [Model Card](MODEL_CARD.md).
