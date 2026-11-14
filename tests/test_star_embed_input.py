"""Regression tests for the independent StarEmbed input path."""
import copy

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from ztf_classifier.validation.star_embed_audit import ARTIFACTS
from ztf_classifier.validation.star_embed_input import (
    run_star_embed_feature_probe,
    star_embed_row_to_internal_lc,
)


def _band(n: int = 40) -> dict:
    mjd = [60000.0 + index * 0.7 for index in range(n)]
    target = [15.0 + 0.1 * np.sin(index * 0.31) for index in range(n)]
    return {
        "target": target,
        "past_feat_dynamic_real": [0.05] * n,
        "feat_dynamic_real": [0.0] + [0.7] * (n - 1),
        "mjd": mjd,
        "length": n,
    }


def _row(sourceid: str, class_str: str = "EW") -> dict:
    return {
        "sourceid": sourceid,
        "bands_data": {
            "g": copy.deepcopy(_band()),
            "r": copy.deepcopy(_band()),
            "i": None,
        },
        "period": 0.5,
        "class_str": class_str,
        "ra": 120.0,
        "dec": 20.0,
    }


def test_star_embed_mapping_preserves_mjd_magnitude_error_and_band_identity() -> None:
    internal = star_embed_row_to_internal_lc(_row("source-1"))
    assert list(internal.columns) == ["mjd", "fid", "mag", "magerr"]
    assert len(internal) == 80
    assert set(internal["fid"]) == {1, 2}
    assert internal.loc[internal["fid"] == 1, "mjd"].iloc[0] == 60000.0
    assert internal.loc[internal["fid"] == 2, "magerr"].iloc[0] == 0.05


def test_star_embed_mapping_rejects_misaligned_arrays() -> None:
    row = _row("source-1")
    row["bands_data"]["g"]["mjd"] = [60000.0]
    with pytest.raises(ValueError, match="array length mismatch"):
        star_embed_row_to_internal_lc(row)


def test_star_embed_feature_probe_uses_clean_test_ids_and_emits_42_features(
    tmp_path,
) -> None:
    data_dir = tmp_path / "data"
    output_dir = tmp_path / "output"
    data_dir.mkdir()
    rows_by_file = {
        ARTIFACTS[0]: [_row("train-1")],
        ARTIFACTS[1]: [_row("train-2")],
        ARTIFACTS[2]: [_row("validation-1")],
        ARTIFACTS[3]: [_row("test-1"), _row("test-2")],
        ARTIFACTS[4]: [_row("anom-1", "Beta_Lyrae")],
    }
    for filename, rows in rows_by_file.items():
        pq.write_table(pa.Table.from_pylist(rows), data_dir / filename)

    report = run_star_embed_feature_probe(
        data_dir, output_dir, sample_size=1, seed=7
    )
    assert report["status"] == "PASS_INPUT_FEATURE_PROBE"
    assert report["feature_vectors_generated"] == 1
    assert report["feature_vector_width"] == 42
    assert (output_dir / "star_embed_v0_2_feature_probe.parquet").is_file()


def test_star_embed_feature_probe_blocks_cross_split_leakage_but_runs_clean_sample(
    tmp_path,
) -> None:
    data_dir = tmp_path / "data"
    output_dir = tmp_path / "output"
    data_dir.mkdir()
    rows_by_file = {
        ARTIFACTS[0]: [_row("train-leak"), _row("train-clean")],
        ARTIFACTS[1]: [_row("train-2")],
        ARTIFACTS[2]: [_row("validation-1")],
        ARTIFACTS[3]: [_row("train-leak"), _row("test-clean")],
        ARTIFACTS[4]: [_row("anom-1", "Beta_Lyrae")],
    }
    for filename, rows in rows_by_file.items():
        pq.write_table(pa.Table.from_pylist(rows), data_dir / filename)

    report = run_star_embed_feature_probe(
        data_dir, output_dir, sample_size=1, seed=7
    )
    assert report["status"] == "BLOCKED_SOURCE_SPLIT_INTEGRITY"
    assert report["sample_exclusions"]["test_objects_overlapping_other_splits"] == 1
    assert report["feature_vectors_generated"] == 1
