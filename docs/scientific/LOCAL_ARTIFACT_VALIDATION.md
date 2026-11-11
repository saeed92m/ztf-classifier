# Local scientific artifact audit and test procedure

## Purpose

The scientific/model integration tests require frozen artifacts that are intentionally not stored in Git. Use this read-only audit before running those tests.

The expected production artifact is:

`runs/model_baseline_v0.2_production/artifact/`

The 2026-10-27 lab-smoke artifact is:

`runs/lab-smoke-20261027T104951Z/artifact/`

**Do not use the lab-smoke artifact as a replacement for the frozen production artifact.** The lab artifact is a separate model run. The frozen production artifact requires artifact schema `1.0`; schema `1.1` lab-smoke artifacts are rejected even if copied into the production path. The audit checks internal manifest/file hash consistency, but it cannot authenticate the original artifact against a trusted external manifest hash that is not currently available.

## Run the audit in WSL

From the original project checkout:

```bash
cd ~/projects/ztf-classifier
python scripts/audit_scientific_artifacts.py
```

The script writes:

`reports/scientific_validation/local_scientific_artifact_audit.json`

It checks:
- all required files under the frozen production artifact;
- the known hashes of selected files in the separate lab-smoke artifact;
- the v0.2 feature dataset and model configuration;
- the ALeRCE raw-detection Parquet cache;
- fold-assignment files;
- the four test modules affected by the 10 skipped tests.

The script does not modify or upload scientific inputs. It writes the JSON audit report. It does not hash large feature datasets unless `--hash-data` is supplied. The readiness field means that required paths exist and the artifact's internal manifest/file hashes are self-consistent. It does not authenticate the artifact against an independently pinned original manifest, validate model contents or feature semantics, or establish scientific performance.

## Run the skipped tests

Run these tests only after the audit reports `integration_prerequisites_present: true`:

```bash
python -m pytest -q \
  tests/test_feature_pipeline_parity.py \
  tests/test_raw_dataset_validation_integration.py \
  tests/test_offline_feature_dataset_reproduction.py \
  tests/test_model_production_inference.py
```

Do not create a symlink from the lab-smoke artifact to the production path. Do not copy lab model weights into the frozen production artifact directory.

## Expected result

The audit report must identify the exact missing paths. If the production artifact is absent, the production-inference tests remain blocked. If feature files or the ALeRCE raw cache are absent, the corresponding integration tests remain blocked.

When sharing the audit report, share the JSON report only. Do not upload raw lightcurves, credentials or large data files.
