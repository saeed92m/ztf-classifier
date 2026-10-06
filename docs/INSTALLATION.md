# Installation

## Requirements

Python 3.11 is the supported release environment. A Linux/WSL environment is recommended for scientific workflows.

## Install

Create a virtual environment and install the published package:

    python -m venv .venv
    source .venv/bin/activate
    python -m pip install --upgrade pip
    python -m pip install ztf-classifier==1.0.0

Verify:

    ztf-classifier --help

## Source installation

Clone the repository, create the environment, and install the project in editable mode when developing or extending the platform.

## Data

The software does not require the complete ZTF archive to be stored locally. Use the documented acquisition and source contracts for targeted data retrieval.

## Next step

Continue with the Quick Start and API/Workbench documentation.
