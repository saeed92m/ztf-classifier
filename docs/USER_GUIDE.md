# ZTF Classifier — User Guide v1.0.1

## Product status

ZTF Classifier v1.0.1 is a released Python package with CLI, API, worker, and an API-backed Scientific Analysis Workbench.

The broader cross-platform desktop product is still in development. The current Workbench is not a self-contained Windows, macOS, or Linux desktop application.

## Scientific workflow

Source data → ingestion and quality checks → feature generation → analysis → classification and diagnostics → provenance → reproducible output.

## Frozen model baseline

- Scientific baseline: v0.2.0 (immutable)
- Production model: `baseline_v0.2`
- Model family: XGBoost
- Feature contract: 42 features, `final_feature_set_v0.2`
- Benchmark: 150 objects, 15 ALeRCE classes, 10 objects per class

ALeRCE labels are reference labels. They are not independent astrophysical ground truth. The benchmark does not establish population-level performance across all ZTF objects.

## Command-line inference

Run:

```bash
ztf-classifier --help
```

Single-object inference:

```bash
ztf-classifier predict \
  --artifact PATH_TO_TRUSTED_ARTIFACT \
  --input INPUT.parquet \
  --output OUTPUT.json
```

Batch inference:

```bash
ztf-classifier batch \
  --artifact PATH_TO_TRUSTED_ARTIFACT \
  --input INPUT.parquet \
  --output OUTPUT.parquet
```

You can use a registry instead of a direct artifact. Select exactly one mode:

- `--artifact PATH`
- `--registry-dir PATH --model-version baseline_v0.2`

Do not use both modes together.

## API and Workbench

The FastAPI service exposes versioned contracts under `/v1/`. The Workbench is served at `/workbench/`.

The current Workbench includes API-backed object analysis, light-curve display, classification probabilities, uncertainty/OOD panels, provenance, batch/catalog/report navigation, and a Scientific Validation view. Some product areas remain placeholders or partial workflows.

For API schemas and service configuration, see [API v1](api/API_V1.md) and the repository's `.env.example`.

## Understanding model outputs

The inference result can include:

- predicted class and class probabilities;
- calibrated probabilities when calibration is available;
- conformal prediction set and diagnostics when available;
- OOD score and reference-distribution diagnostics when available;
- model, artifact, feature-schema, software, and provenance metadata.

A low probability or high OOD score does not prove an astrophysical anomaly. The production baseline does not claim to be a validated scientific-anomaly detector. Anomaly evidence remains a separate analysis channel.

## Data import

The application ingestion service currently supports local CSV and Parquet tables with explicit size and schema checks. It records a source identifier, source type, row count, columns, and file SHA-256.

This import contract does not mean that every CSV or Parquet file can be passed directly to the model. Model inputs must match the selected feature schema.

ZTF Alert/AVRO ingestion, cutout handling, and a general TAP backend are not yet accepted product capabilities.

## Scientific validation limits

- The 150-object benchmark is small and balanced.
- ALeRCE provides reference labels, not independent ground truth.
- The BTS-to-DR24 spatial pilot is a coordinate-recovery diagnostic. It does not establish model accuracy or cross-match precision/recall.
- StarEmbed evaluation remains blocked by a reported duplicate-ID and train/test overlap audit.
- The product scientific gate remains fail-closed until its required source-backed evidence and leakage checks pass.

## Export and reproducibility

Use the report and catalog endpoints for outputs supported by the current API. Results should retain object IDs, source context, schema, model identity, hashes, and run metadata. A skipped or unavailable scientific check must remain visible as not verified.

## Known product gaps

The following work remains open:

- self-contained Windows, macOS, and Linux installers;
- complete Data Manager and Object/Source Explorer workflows;
- integrated Help and troubleshooting;
- phase-folded light-curve visualization;
- ZTF AVRO alert ingestion and cutout preservation;
- TAP-backed acquisition;
- validated discovery ranking and human review;
- complete scientific validation and clean-machine acceptance.

Track product completion in [Issue #158](https://github.com/saeed92m/ztf-classifier/issues/158) and [the platform roadmap](roadmap/PLATFORM_EXPANSION_ROADMAP.md).
