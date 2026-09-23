from __future__ import annotations

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORT = (
    PROJECT_ROOT
    / "reports/validation/raw_dataset_benchmark_v0.2.json"
)

EXPECTED_DATASET_SHA256 = (
    "53bbe20bf18bbf955d80563200b06dcc20f9aab94edc5553259a54e1ff7e00f5"
)

EXPECTED_MANIFEST_SHA256 = (
    "9e1bb86b497d068420aabaee2e974dce0e63a02f64349cc628a901e3d36e829b"
)

EXPECTED_FEATURE_SCHEMA_SHA256 = (
    "fed07fc291070ecbdc7bbc597fad5aac6a3f4a1746feb12a9f4c2407108af329"
)

EXPECTED_COMMIT = (
    "c98bb371bedfc73fc6796d16adb659597d05b188"
)


def test_benchmark_v0_2_raw_validation_report() -> None:
    assert REPORT.is_file()

    report = json.loads(REPORT.read_text(encoding="utf-8"))

    assert report["schema_version"] == "1.0"
    assert report["report_type"] == "raw_dataset_validation"
    assert report["status"] == "PASS"

    assert report["run"]["git_commit"] == EXPECTED_COMMIT
    assert report["run"]["git_branch"] == "main"
    assert report["run"]["git_dirty"] is True

    source = report["source"]

    assert source["canonical_dataset"] == (
        "data/processed/benchmark_v0.2/features.parquet"
    )
    assert source["canonical_dataset_sha256"] == EXPECTED_DATASET_SHA256

    assert source["canonical_dataset_manifest"] == (
        "data/processed/benchmark_v0.2/dataset_manifest.json"
    )
    assert source["canonical_dataset_manifest_sha256"] == (
        EXPECTED_MANIFEST_SHA256
    )

    assert source["feature_schema"] == (
        "reports/tables/final_feature_set_v0.2.parquet"
    )
    assert source["feature_schema_sha256"] == (
        EXPECTED_FEATURE_SCHEMA_SHA256
    )

    assert source["raw_cache"] == "data/raw/alerce"

    validation = report["validation"]

    assert validation["status"] == "PASS"
    assert validation["canonical_objects"] == 150
    assert validation["cache_objects"] == 151

    assert validation["missing_oids"] == []
    assert validation["extra_oids"] == ["ZTF18aauelee"]
    assert validation["incomplete_pairs"] == []
    assert validation["schema_mismatches"] == []
    assert validation["invalid_required_values"] == []

    assert validation["fid_distribution"] == {
        "1": 142,
        "2": 142,
        "3": 44,
    }

    assert validation["fid_set_distribution"] == {
        "1": 6,
        "1,2": 94,
        "1,2,3": 40,
        "1,3": 2,
        "2": 6,
        "2,3": 2,
    }

    assert validation["ordering"] == {
        "detections_sorted_by_mjd": True,
        "non_detections_sorted_by_mjd": True,
        "detection_ordering_failures": [],
        "non_detection_ordering_failures": [],
    }

    assert validation["detection_row_statistics"] == {
        "count": 150,
        "min": 4,
        "median": 74.0,
        "max": 1732,
        "mean": 189.63333333333333,
    }

    assert validation["non_detection_row_statistics"] == {
        "count": 150,
        "min": 6,
        "median": 210.5,
        "max": 1918,
        "mean": 313.4266666666667,
    }

    assert len(validation["low_observation_objects_lt10"]) == 1
    assert len(validation["low_observation_objects_lt30"]) == 31

    assert validation["corrected_statistics"] == {
        "corrected_true": 27379,
        "corrected_false": 1066,
    }
