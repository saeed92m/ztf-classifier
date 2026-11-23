# ZTF Classifier — User Guide

**Software release:** v1.0.1
**Scientific baseline:** v0.2.0 (immutable)

## Supported Park demonstrator workflow

1. Start the API and Workbench using [Installation](INSTALLATION.md).
2. Open the raw DR24 Explorer and enter 1–10 unique positive DR24 OIDs.
3. Load the raw light curves and inspect separate OID panels, source-native HMJD/magnitude values, raw epoch records, diagnostic QC, and acquisition provenance.
4. Export raw JSON and retain its hash with the run record.

Follow the [Park Laboratory Demonstrator Runbook](acceptance/PARK_LABORATORY_DEMONSTRATOR_RUNBOOK_2026-11-18.md). This is a bounded raw-data inspection workflow, not a DR24 classifier. Do not infer physical identity across OIDs or treat diagnostic QC as a production selection policy. Documented epoch counts and payload hashes are expected reference values until recomputed from retained raw payloads.

## Model and interpretation limits

The frozen v0.2.0 benchmark contract has 150 objects, 15 ALeRCE reference classes, 10 objects per class, and 42 features. ALeRCE labels are reference labels, not independent astrophysical ground truth. These historical benchmark details do not establish DR24 model performance.

The original `baseline_v0.2` production artifact has not been recovered and authenticated; the package does not include model weights. Production inference is **BLOCKED**. Do not substitute the schema-1.1 lab-smoke artifact. The DR24 Explorer does not generate frozen v0.2 features or predictions. Do not present calibration, conformal coverage, OOD, or anomaly claims for these raw records.

## Reproducibility

Retain source/release, query, OID, retrieval time, native schema, epoch accounting, provenance, software revision, output file, and recomputed SHA-256. CI results must be identified by the PR commit they tested; they do not validate the combined integration HEAD unless that exact SHA ran.
