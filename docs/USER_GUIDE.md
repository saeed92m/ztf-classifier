# ZTF Classifier — User Guide

## Workflow

source data → ingestion/QC → feature generation → analysis → uncertainty/calibration/OOD → scientific outputs → provenance/evidence

## Baseline

The software release is v1.0.0. The production model is baseline_v0.2 and uses the immutable 42-feature v0.2 contract.

## Inference

Use the predict command for single-object inference and the batch command for batch inference. Select exactly one model source: a trusted artifact or an explicit registry/model-version pair.

## Interpretation

Classification confidence, OOD, and scientific anomaly are separate result channels. A low-confidence or OOD result is not automatically an astrophysical anomaly.

## Discovery

Discovery candidates are versioned scientific results assembled from analysis outputs and evidence. They are not simply low-confidence predictions.