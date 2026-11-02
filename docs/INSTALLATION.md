# Installation — ZTF Classifier v1.0.1

## Scope

The published v1.0.1 release is a Python package. It provides the CLI, API, worker, and scientific inference services.

**It is not yet a self-contained desktop installer.** The project does not yet publish a Windows installer, macOS application, or Linux AppImage. A normal desktop user still needs a supported Python environment.

## Requirements

- Python 3.11.x
- pip
- A trusted model artifact or an explicit model registry for production inference
- A supported input table that matches the selected feature schema

The frozen production model uses the v0.2.0 scientific baseline and 42 features.

## Windows — PowerShell

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install ztf-classifier==1.0.1
ztf-classifier --help
```

If PowerShell blocks script activation, use the documented Windows Python activation policy for your environment. Do not disable system security controls globally.

## Linux and macOS

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install ztf-classifier==1.0.1
ztf-classifier --help
```

## Source installation

For development:

```bash
git clone https://github.com/saeed92m/ztf-classifier.git
cd ztf-classifier
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.lock
python -m pip install -e .
```

On Windows, create and activate the virtual environment with the PowerShell commands above.

## Supported inference commands

The package exposes:

- `ztf-classifier predict` for single-object inference.
- `ztf-classifier batch` for batch Parquet inference.
- `ztf-classifier-api` for the FastAPI service.
- `ztf-classifier-worker` for the job worker.

Use an explicit artifact path or an explicit registry/model-version pair. Do not provide both selection modes in one request.

## Data and provenance

The package does not require a local copy of the complete ZTF archive. It supports targeted source access and local CSV/Parquet import through the application ingestion contract. Local imports record source identity, row count, schema, and SHA-256.

The scientific inference input must still satisfy the declared feature schema. A generic CSV or Parquet file is not automatically a valid model input.

## Desktop product status

The API-backed Scientific Analysis Workbench is available at `/workbench/` when the API service is running. It is an early web workbench, not a native desktop application. Clean-machine tests and self-contained installers for Windows, macOS, and Linux remain open product requirements tracked in [Issue #158](https://github.com/saeed92m/ztf-classifier/issues/158).

## Next references

- [User Guide](USER_GUIDE.md)
- [API v1](api/API_V1.md)
- [Product Architecture](architecture/V1_PRODUCT_ARCHITECTURE.md)
- [Platform Roadmap](roadmap/PLATFORM_EXPANSION_ROADMAP.md)
