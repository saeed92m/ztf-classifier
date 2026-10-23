# ZTF Classifier — User Guide

> Product scope: Astronomical Data Analysis & Discovery Platform. ZTF is the first established domain, not the only input. User-supplied data is accepted only through supported formats and explicit schema/semantic checks; import success does not mean the frozen ZTF model is compatible.

See [current handbook](HANDBOOK_CURRENT.md), [glossary](PROJECT_GLOSSARY.md), [product charter](PROJECT_CHARTER_AND_SOURCE_OF_TRUTH.md), and [state register](PROJECT_STATE_REGISTER.md).

## Workflow

source data → ingestion/QC → feature generation → analysis → uncertainty/calibration/OOD → scientific outputs → provenance/evidence

## Baseline

The latest published software release observed on 2026-10-23 is v1.0.1. Check the GitHub release page before installing a different version. The production model is baseline_v0.2 and uses the immutable 42-feature v0.2 contract.

## Inference

Use the predict command for single-object inference and the batch command for batch inference. Select exactly one model source: a trusted artifact or an explicit registry/model-version pair.

## Interpretation

Classification confidence, OOD, and scientific anomaly are separate result channels. A low-confidence or OOD result is not automatically an astrophysical anomaly.

## Discovery

Discovery candidates are versioned scientific results assembled from analysis outputs and evidence. They are not simply low-confidence predictions.