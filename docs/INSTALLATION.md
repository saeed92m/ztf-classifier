# Installation

## Supported environment
The released package requires Python 3.11. The current published software release is ztf-classifier==1.0.1.

## Linux / WSL

    python3.11 -m venv .venv
    source .venv/bin/activate
    python -m pip install --upgrade pip
    python -m pip install ztf-classifier==1.0.1
    ztf-classifier --help

## Windows PowerShell

    py -3.11 -m venv .venv
    .\.venv\Scripts\Activate.ps1
    python -m pip install --upgrade pip
    python -m pip install ztf-classifier==1.0.1
    ztf-classifier --help

## macOS

    python3.11 -m venv .venv
    source .venv/bin/activate
    python -m pip install --upgrade pip
    python -m pip install ztf-classifier==1.0.1
    ztf-classifier --help

## Model artifact
The wheel and source distribution do not include the frozen production model artifact. Obtain it through the project's controlled artifact workflow. Verify the manifest and hashes before loading it. Do not load untrusted model files.

## Development installation
Clone the repository, create a Python 3.11 environment, and install the project in editable mode with the documented development dependencies. Use the lock file for reproducible development.

## Important limitations
- The Python package is not a self-contained desktop installer.
- Native DR24 raw acquisition is under review in PR #264. It is not an accepted end-to-end DR24 inference workflow.
- Do not download the complete DR24 archive for installation or first-run setup.
- The frozen v0.2.0 inference path requires its exact 42-feature input contract and matching model artifact.
