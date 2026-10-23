"""Tests for raw StarEmbed dataset schema and sample audit."""

import json

import pyarrow as pa
import pyarrow.parquet as pq

from ztf_classifier.validation.star_embed_audit import (
    ARTIFACTS,
    audit_star_embed_dataset,
)


def _row(sourceid: str, class_str: str = "EW") -> dict:
    band = {
        "target": [15.1, 15.2, 15.0],
        "past_feat_dynamic_real": [0.1, 0.1, 0.2],
        "feat_dynamic_real": [0.0, 1.0, 1.0],
        "mjd": [60000.0, 60001.0, 60002.0],
        "length": 3,
    }
    return {
        "sourceid": sourceid,
        "bands_data": {"g": band, "r": band, "i": None},
        "period": 0.5,
        "class_str": class_str,
        "ra": 120.0,
        "dec": 20.0,
    }


def test_star_embed_audit_writes_deterministic_test_sample(tmp_path) -> None:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    rows_by_file = {
        ARTIFACTS[0]: [_row("train-a")],
        ARTIFACTS[1]: [_row("train-b")],
        ARTIFACTS[2]: [_row("validation-a")],
        ARTIFACTS[3]: [_row("test-b"), _row("test-a")],
        ARTIFACTS[4]: [_row("anom-a", "Beta_Lyrae")],
    }
    for filename, rows in rows_by_file.items():
        pq.write_table(pa.Table.from_pylist(rows), data_dir / filename)

    output = tmp_path / "report.json"
    report = audit_star_embed_dataset(data_dir, output, sample_size=1, seed=7)

    assert report["status"] == "PASS_SCHEMA_AUDIT_WITH_FINDINGS"
    assert report["splits"]["train"]["rows"] == 2
    assert report["sample"]["actual_size"] == 1
    assert report["sample"]["source_split"] == "test"
    assert output.is_file()
    assert json.loads(output.read_text())["seed"] == 7


def test_star_embed_audit_blocks_duplicate_object_across_splits(tmp_path) -> None:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    rows_by_file = {
        ARTIFACTS[0]: [_row("train-only"), _row("leaked-object")],
        ARTIFACTS[1]: [_row("train-other")],
        ARTIFACTS[2]: [_row("validation-only")],
        ARTIFACTS[3]: [_row("leaked-object")],
        ARTIFACTS[4]: [_row("anom-only", "Beta_Lyrae")],
    }
    for filename, rows in rows_by_file.items():
        pq.write_table(pa.Table.from_pylist(rows), data_dir / filename)

    report = audit_star_embed_dataset(data_dir, tmp_path / "report.json")

    assert report["status"] == "BLOCKED"
    assert report["object_id_overlap"]["train__test"]["overlap_count"] == 1
    assert "object_id_overlap_between_splits:train__test:1" in report["validation_errors"]
    details = [item for item in report["object_id_issue_details"] if item["issue"] == "cross_split_overlap"]
    assert {item["split"] for item in details} == {"train", "test"}
    assert all(item["source_artifact"] for item in details)


def test_star_embed_audit_fails_closed_when_artifact_is_missing(tmp_path) -> None:
    report = audit_star_embed_dataset(tmp_path, tmp_path / "report.json")
    assert report["status"] == "BLOCKED"
    assert any(item.startswith("missing_artifact:") for item in report["errors"])
