# ZTF Classifier — User Guide

## Product status
The software release is v1.0.1. The project has an API-backed Workbench and a frozen scientific inference baseline. The complete guided DR24 application workflow is still under development.

## Supported baseline workflow
Source data → compatible 42-feature input → v0.2.0 inference → diagnostics → provenance and export.

The production model is baseline_v0.2. Its input must follow the frozen final_feature_set_v0.2 schema and class order. Use only a trusted model artifact with a verified manifest.

## DR24 exploratory workflow — not yet accepted
The project is integrating native ZTF DR24 Lightcurves acquisition. PR #264 is Draft and exposes raw source data only. It does not yet provide an accepted source-selectable Workbench workflow or a validated DR24 feature/inference path.

DR24 records must retain HMJD as a heliocentric time coordinate, native photometry, raw quality flags, and per-OID/filter/field/readout provenance. Do not silently merge OIDs, apply color corrections, relabel HMJD as MJD, or use the frozen v0.2.0 model on unvalidated DR24 features.

## Interpretation
Classification, calibration, conformal prediction, OOD, and scientific anomaly analysis are separate concepts. A low-confidence or OOD result is not automatically an astrophysical anomaly.

ALeRCE labels are benchmark/reference labels, not independent ground truth. Report scientific performance only against a declared labeled reference and a leakage-safe evaluation.

## Reproducibility
Each accepted analysis must retain the source and version, exact object/OID list, retrieval timestamp, schema identity, run configuration, code revision, environment, model identity where used, data/output hashes, warnings, exclusions, and validation status.

See docs/QUICK_START.md, docs/INSTALLATION.md, docs/api/API_V1.md, docs/SCIENTIFIC_METHODOLOGY.md, and docs/PARK_MVP_DELIVERY_PLAN_2026-11-05.md.
