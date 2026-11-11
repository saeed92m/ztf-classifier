from __future__ import annotations

import hashlib
import json
from pathlib import Path

from scripts.audit_scientific_artifacts import (
    LAB_ARTIFACT,
    PRODUCTION_ARTIFACT,
    TESTS,
    audit,
)


def _write_files(root: Path, relative_paths: tuple[str, ...]) -> None:
    for relative in relative_paths:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"test-artifact")


def test_lab_smoke_artifact_never_substitutes_for_production(tmp_path: Path) -> None:
    _write_files(
        tmp_path,
        (
            str(LAB_ARTIFACT / "model.json"),
            str(LAB_ARTIFACT / "feature_schema.parquet"),
        ),
    )

    report = audit(tmp_path, hash_data=False)

    assert report["integration_prerequisites_present"] is False
    assert report["production_model_artifact"]["exists"] is False
    assert report["lab_smoke_artifact"]["exists"] is True
    assert report["lab_smoke_artifact"]["production_eligible"] is False
    assert report["lab_smoke_artifact"]["status"] == (
        "LAB_SMOKE_ONLY_NOT_A_PRODUCTION_SUBSTITUTE"
    )
    assert any("Do not substitute" in blocker for blocker in report["blockers"])


def _write_schema_1_0_production_manifest(
    root: Path, *, schema_version: str = "1.0"
) -> None:
    artifact = root / PRODUCTION_ARTIFACT
    files = {
        "model": "model.json",
        "model_contract": "model_contract.json",
        "feature_schema": "feature_schema.parquet",
        "provenance": "provenance.json",
        "calibration": "calibration.json",
    }
    manifest_files = {}
    for key, filename in files.items():
        path = artifact / filename
        manifest_files[key] = {
            "path": filename,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }
    manifest = {
        "artifact_schema_version": schema_version,
        "model_version": "baseline_v0.2",
        "feature_count": 42,
        "files": manifest_files,
    }
    (artifact / "artifact_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True),
        encoding="utf-8",
    )

def test_audit_reports_ready_for_schema_1_0_without_optional_diagnostics(
    tmp_path: Path,
) -> None:
    required_production_files = (
        "model.json",
        "feature_schema.parquet",
        "artifact_manifest.json",
        "model_contract.json",
        "provenance.json",
        "calibration.json",
    )
    _write_files(
        tmp_path,
        tuple(str(PRODUCTION_ARTIFACT / name) for name in required_production_files)
        + (
            "data/processed/features_v0.2.parquet",
            "reports/tables/final_feature_set_v0.2.parquet",
            "reports/tables/final_model_config_v0.2.json",
            "data/raw/alerce/123_detections.parquet",
            "reports/tables/fold_assignments.parquet",
        )
        + TESTS,
    )
    _write_schema_1_0_production_manifest(tmp_path)

    report = audit(tmp_path, hash_data=False)

    assert report["integration_prerequisites_present"] is True
    artifact = report["production_model_artifact"]
    assert artifact["missing_required_files"] == []
    assert artifact["manifest_validation"]["status"] == "PASS"
    assert artifact["artifact_schema_version"] == "1.0"
    assert artifact["optional_diagnostic_files"]["conformal.json"]["exists"] is False
    assert artifact["optional_diagnostic_files"]["ood.json"]["exists"] is False
    assert artifact["optional_diagnostic_files"]["ood_model.joblib"]["exists"] is False
    assert report["alerce_raw_detection_cache"]["parquet_file_count"] == 1
    assert report["fold_assignment_files"] == [
        "reports/tables/fold_assignments.parquet"
    ]
    assert report["safety"]["read_only"] is True
    assert report["safety"]["uploads_performed"] is False
    assert report["missing_dependent_test_files"] == []


def test_audit_rejects_schema_1_1_lab_smoke_as_production(tmp_path: Path) -> None:
    required_production_files = (
        "model.json",
        "feature_schema.parquet",
        "artifact_manifest.json",
        "model_contract.json",
        "provenance.json",
        "calibration.json",
    )
    _write_files(
        tmp_path,
        tuple(str(PRODUCTION_ARTIFACT / name) for name in required_production_files)
        + (
            "data/processed/features_v0.2.parquet",
            "reports/tables/final_feature_set_v0.2.parquet",
            "reports/tables/final_model_config_v0.2.json",
            "data/raw/alerce/123_detections.parquet",
            "reports/tables/fold_assignments.parquet",
        )
        + TESTS,
    )
    _write_schema_1_0_production_manifest(tmp_path, schema_version="1.1")

    report = audit(tmp_path, hash_data=False)

    assert report["integration_prerequisites_present"] is False
    artifact = report["production_model_artifact"]
    assert artifact["manifest_validation"]["status"] == "FAIL"
    assert artifact["ready"] is False
    assert any(
        "requires schema 1.0" in error
        for error in artifact["manifest_validation"]["errors"]
    )


def test_audit_blocks_manifest_hash_mismatch(tmp_path: Path) -> None:
    required_production_files = (
        "model.json",
        "feature_schema.parquet",
        "artifact_manifest.json",
        "model_contract.json",
        "provenance.json",
        "calibration.json",
    )
    _write_files(
        tmp_path,
        tuple(str(PRODUCTION_ARTIFACT / name) for name in required_production_files)
        + (
            "data/processed/features_v0.2.parquet",
            "reports/tables/final_feature_set_v0.2.parquet",
            "reports/tables/final_model_config_v0.2.json",
            "data/raw/alerce/123_detections.parquet",
            "reports/tables/fold_assignments.parquet",
        )
        + TESTS,
    )
    _write_schema_1_0_production_manifest(tmp_path)
    manifest_path = tmp_path / PRODUCTION_ARTIFACT / "artifact_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["files"]["model"]["sha256"] = "0" * 64
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    report = audit(tmp_path, hash_data=False)

    assert report["integration_prerequisites_present"] is False
    assert report["production_model_artifact"]["manifest_validation"]["status"] == "FAIL"
    assert any(
        "SHA-256 mismatch" in item
        for item in report["production_model_artifact"]["manifest_validation"]["errors"]
    )
