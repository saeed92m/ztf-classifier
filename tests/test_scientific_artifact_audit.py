from __future__ import annotations

from pathlib import Path

from scripts.audit_scientific_artifacts import (
    LAB_ARTIFACT,
    PRODUCTION_ARTIFACT,
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

    assert report["production_integration_tests_ready"] is False
    assert report["production_model_artifact"]["exists"] is False
    assert report["lab_smoke_artifact"]["exists"] is True
    assert report["lab_smoke_artifact"]["production_eligible"] is False
    assert report["lab_smoke_artifact"]["status"] == (
        "LAB_SMOKE_ONLY_NOT_A_PRODUCTION_SUBSTITUTE"
    )
    assert any("Do not substitute" in blocker for blocker in report["blockers"])


def test_audit_reports_ready_only_when_all_prerequisites_exist(tmp_path: Path) -> None:
    _write_files(
        tmp_path,
        tuple(str(PRODUCTION_ARTIFACT / name) for name in (
            "model.json",
            "feature_schema.parquet",
            "artifact_manifest.json",
            "model_contract.json",
            "provenance.json",
            "calibration.json",
            "conformal.json",
            "ood.json",
            "ood_model.joblib",
        ))
        + (
            "data/processed/features_v0.2.parquet",
            "reports/tables/final_feature_set_v0.2.parquet",
            "reports/tables/final_model_config_v0.2.json",
            "data/raw/alerce/123_detections.parquet",
            "reports/tables/fold_assignments.parquet",
        ),
    )

    report = audit(tmp_path, hash_data=False)

    assert report["production_integration_tests_ready"] is True
    assert report["production_model_artifact"]["missing_required_files"] == []
    assert report["alerce_raw_detection_cache"]["parquet_file_count"] == 1
    assert report["fold_assignment_files"] == [
        "reports/tables/fold_assignments.parquet"
    ]
    assert report["safety"]["read_only"] is True
    assert report["safety"]["uploads_performed"] is False
