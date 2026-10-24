# Installation

## Supported platforms

The product targets Windows, macOS and Ubuntu. The **verified** state is
narrower than the target, and is stated here per platform rather than implied.

| Platform | Install path | Status |
|---|---|---|
| Ubuntu (x86-64) | `requirements.lock` (hermetic) or `pip install -e .` | **Verified** — CI `Test Suite`, `Build & Verify Package` |
| macOS | `pip install -e ".[dev]"` from `pyproject.toml` | **Measured by CI** — job `Cross-platform (macos-latest)`. See `docs/README.md` §5 for the current result. |
| Windows | `pip install -e ".[dev]"` from `pyproject.toml` | **Measured by CI** — job `Cross-platform (windows-latest)`. See `docs/README.md` §5. |

`requirements.lock` is a **Linux/x86-64 freeze**. It pins `nvidia-nccl-cu12`,
`jeepney` and `SecretStorage`, which have no macOS or Windows distributions, so
`pip install -r requirements.lock` **fails** on those platforms. Use
`pip install -e .[dev]` instead.

## Requirements

- Python **3.11** (the only version with a verified CI run; the package declares
  `>=3.11,<3.12`)
- CPU-first. No GPU is required; `xgboost` may pull CUDA libraries on Linux
  because they ship in the same wheel.

## Installing a released version

**`ztf-classifier` is not published on PyPI.** Verified 2026-10-24:
`https://pypi.org/pypi/ztf-classifier/json` returns HTTP 404, so
`pip install ztf-classifier` will fail. Do not use that command.

Releases are distributed as build assets attached to GitHub Releases:

    # Latest release assets
    #   ztf_classifier-1.0.1-py3-none-any.whl
    #   ztf_classifier-1.0.1.tar.gz
    # https://github.com/saeed92m/ztf-classifier/releases/latest

    python -m venv .venv
    # Linux / macOS
    source .venv/bin/activate
    # Windows (PowerShell)
    # .venv\Scripts\Activate.ps1

    python -m pip install --upgrade pip
    python -m pip install "https://github.com/saeed92m/ztf-classifier/releases/download/v1.0.1/ztf_classifier-1.0.1-py3-none-any.whl"

Verify:

    ztf-classifier --help

## Installing from source

    git clone https://github.com/saeed92m/ztf-classifier.git
    cd ztf-classifier
    python -m venv .venv
    source .venv/bin/activate          # Windows: .venv\Scripts\Activate.ps1
    python -m pip install --upgrade pip==26.2 setuptools==84.1.0 wheel==0.48.0

    # Portable install path (all platforms)
    python -m pip install -e ".[dev]"

    # Reproducible, hermetic install (Linux x86-64 only)
    python -m pip install -r requirements.lock
    python -m pip install -e . --no-deps

Verify:

    python -m pip check
    python -m pytest -q
    ztf-classifier --help

## Data

The software does not require the complete ZTF archive to be stored locally. Use
the documented acquisition and source contracts for targeted data retrieval.
Runtime configuration lives in `.env.example`; copy it to `.env` and fill the
values. `.env` is git-ignored — never commit credentials.

## Next step

Continue with [`QUICK_START.md`](QUICK_START.md) and the API/Workbench
documentation in [`api/API_V1.md`](api/API_V1.md).
