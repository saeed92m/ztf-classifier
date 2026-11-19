# ZTF Classifier — User Guide

**Software release:** v1.0.1  
**Scientific baseline:** v0.2.0 (immutable)

## Supported workflows

### Raw DR24 Explorer

1. Start the API and Workbench.
2. Open DR24 Explorer.
3. Enter 1–10 unique positive DR24 OIDs.
4. Load the raw light curves.
5. Inspect separate OID panels, native HMJD/magnitude values, raw epoch records, diagnostic QC, and acquisition provenance.
6. Export the raw JSON and retain its hashes.

This is a bounded raw-data inspection workflow. It is not a DR24 classifier. Do not infer physical identity across OIDs or treat diagnostic QC as a production selection policy.

### Frozen v0.2.0 inference

The CLI and API support artifact-backed inference with the frozen 42-feature contract. Inference requires the original trusted model artifact and compatible input data.

The original `baseline_v0.2` production artifact has not been recovered from accessible remote sources. See [Issue #282](https://github.com/saeed92m/ztf-classifier/issues/282). The v1.0.1 package does not contain model weights. Do not substitute the lab-smoke artifact.

## Scientific interpretation

- The frozen benchmark contains 150 ZTF objects across 15 ALeRCE reference classes, with 10 objects per class.
- ALeRCE labels are reference/weak labels, not independent astrophysical truth.
- The 150-object benchmark is not representative of the full ZTF population.
- Classification confidence, calibration, conformal prediction, OOD, and scientific anomaly are separate channels.
- A raw score is not a calibrated probability.
- OOD is not an astrophysical anomaly.
- Missing or unsupported data must remain explicit.

## Park demonstrator

Use the [Park Laboratory Demonstrator Runbook](acceptance/PARK_LABORATORY_DEMONSTRATOR_RUNBOOK_2026-11-18.md). The current demonstrator claim is limited to raw DR24 acquisition, inspection, diagnostic QC, provenance, and export. Full Park MVP acceptance requires the complete predeclared cohort to pass through the normal API and Workbench workflow.
