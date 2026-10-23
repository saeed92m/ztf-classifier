# Installation

> The latest published package observed on 2026-10-23 is v1.0.1. Verify the [GitHub release](https://github.com/saeed92m/ztf-classifier/releases) for current assets and checksums. The broader desktop installer is a separate roadmap item; these instructions describe the Python package.

See [current handbook](HANDBOOK_CURRENT.md) and [project state register](PROJECT_STATE_REGISTER.md).

## Requirements

Python 3.11 is the supported release environment. A Linux/WSL environment is recommended for scientific workflows.

## Install

Create a virtual environment and install the published package:

    python -m venv .venv
    source .venv/bin/activate
    python -m pip install --upgrade pip
    python -m pip install ztf-classifier==1.0.1

Verify:

    ztf-classifier --help

## Source installation

Clone the repository, create the environment, and install the project in editable mode when developing or extending the platform.

## Data

The software does not require the complete ZTF archive to be stored locally. User-provided and other-survey inputs must use a supported format and explicit schema mapping; do not assume every imported dataset is compatible with the frozen ZTF model. Use documented source contracts for targeted retrieval.

## Next step

Continue with the Quick Start and API/Workbench documentation.
