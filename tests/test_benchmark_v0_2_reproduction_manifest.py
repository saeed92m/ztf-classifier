import json
from pathlib import Path

from ztf_classifier.reproducibility.validation import (
    ReproducibilityValidator,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]

MANIFEST_PATH = (
    PROJECT_ROOT
    / "reports"
    / "reproducibility"
    / "benchmark_v0.2-reproduction.json"
)


def test_benchmark_v0_2_reproduction_manifest() -> None:
    assert MANIFEST_PATH.is_file()

    result = ReproducibilityValidator().validate(
        MANIFEST_PATH,
        project_root=PROJECT_ROOT,
        verify_files=True,
    )

    assert result.dataset_sha256 == (
        "53bbe20bf18bbf955d80563200b06dcc20f9aab94edc5553259a54e1ff7e00f5"
    )

    assert result.feature_schema_sha256 == (
        "fed07fc291070ecbdc7bbc597fad5aac6a3f4a1746feb12a9f4c2407108af329"
    )

    manifest = json.loads(
        MANIFEST_PATH.read_text(encoding="utf-8")
    )

    assert manifest["schema_version"] == "1.0"

    assert manifest["project"] == "ZTF Classifier"

    assert manifest["run"]["purpose"] == (
        "offline_v0_2_reproduction"
    )

    assert manifest["source"]["git_commit"] == (
        "866c868a7292294014c81b58ad5880310073a5ec"
    )

    assert manifest["source"]["git_branch"] == "main"
    assert manifest["source"]["git_dirty"] is False

    assert manifest["dataset"]["object_count"] == 150
    assert manifest["dataset"]["feature_count"] == 42
    assert manifest["dataset"]["dataset_version"] == (
        "benchmark_v0.2-reproduction"
    )

    assert manifest["feature_schema"]["version"] == "v0.2"

    configuration = manifest["configuration"]

    assert configuration["backend"] == "ParquetDetectionBackend"
    assert configuration["network_access"] is False
    assert configuration["object_count"] == 150
    assert configuration["feature_count"] == 42

    assert configuration["parity"]["metadata"] == "exact"
    assert configuration["parity"]["features"] == "exact"
    assert (
        configuration["parity"]["artifact_sha256_matches_frozen_v0_2"]
        is True
    )
