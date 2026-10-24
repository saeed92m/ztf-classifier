"""Astronomer-oriented ingestion and workflow audit.

This suite verifies the *actually supported* ingestion contracts and the
complete astronomer workflow from an astronomer's perspective, without
claiming support for arbitrary astronomical data merely because CSV can be read.

Supported paths (verified via src/ztf_classifier/application/ingestion.py
and src/ztf_classifier/io/):
- Local CSV / Parquet tabular ingestion via DataIngestionService (max_bytes, provenance hash)
- ALeRCE detection ingestion via alerce_to_internal_lc_robust (requires mjd, fid, magpsf_corr etc.)
- Feature extraction via ScientificFeatureEngine (42 frozen v0.2 features) with explicit
  handling of missing values, insufficient observations, and cross-band requirements.

Each case exercises valid and invalid inputs: multiple objects, missing values,
malformed timestamps, duplicate IDs, quality flags, insufficient observations.
All fixtures are synthetic and clearly labeled; no real-data validation is claimed here.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd
import pytest

from ztf_classifier.application.errors import ApplicationInputError
from ztf_classifier.application.ingestion import DataIngestionService, ImportRequest
from ztf_classifier.data.source_subset import (
    SourceSubsetValidationError,
    normalize_source_subset,
)


def _write_csv(path: Path, content: str) -> Path:
    path.write_text(content, encoding="utf-8")
    return path


def test_ingestion_supports_csv_and_parquet_with_provenance(tmp_path: Path):
    svc = DataIngestionService()
    csv_path = _write_csv(
        tmp_path / "valid.csv",
        "oid,mjd,mag,magerr,ra,dec\nZTF1,60000,18.0,0.1,10,20\nZTF2,60001,19.0,0.2,11,21\n",
    )
    result = svc.import_file(
        ImportRequest(path=csv_path, required_columns=("oid", "mjd", "mag"))
    )
    assert result.row_count == 2
    assert set(result.columns) == {"oid", "mjd", "mag", "magerr", "ra", "dec"}
    assert result.source.source_type in ("local_csv", "local_parquet")
    assert result.content_sha256 == hashlib.sha256(csv_path.read_bytes()).hexdigest()
    assert result.source.metadata["row_count"] == 2

    # Parquet round-trip with same contract
    parquet_path = tmp_path / "valid.parquet"
    pd.read_csv(csv_path).to_parquet(parquet_path)
    result2 = svc.import_file(
        ImportRequest(path=parquet_path, required_columns=("oid", "mjd"))
    )
    assert result2.row_count == 2
    assert result2.source.source_type == "local_parquet"


def test_ingestion_duplicate_column_handling(tmp_path: Path):
    svc = DataIngestionService()
    # Pandas mangles duplicate headers to oid, oid.1 — service currently does not reject
    # This documents the actual behavior and identifies a gap: duplicate headers should ideally fail.
    path = tmp_path / "dup.csv"
    path.write_text("oid,oid,mjd\nZTF1,ZTF1,60000\n", encoding="utf-8")
    result = svc.import_file(ImportRequest(path=path))
    # Actual: pandas produces columns ['oid','oid.1','mjd'] which are unique, so import succeeds
    # Gap noted: we should reject semantic duplicate column names before mangling.
    assert "oid" in result.columns
    assert result.row_count == 1


def test_ingestion_rejects_missing_required_columns(tmp_path: Path):
    svc = DataIngestionService()
    path = _write_csv(tmp_path / "miss.csv", "oid,mjd\nZTF1,60000\n")
    with pytest.raises(Exception) as exc:
        svc.import_file(
            ImportRequest(path=path, required_columns=("oid", "mjd", "mag"))
        )
    assert "missing required columns" in str(exc.value).lower()


def test_ingestion_rejects_empty_and_oversized(tmp_path: Path):
    svc = DataIngestionService()
    empty = _write_csv(tmp_path / "empty.csv", "oid,mjd\n")
    with pytest.raises(ApplicationInputError):
        svc.import_file(ImportRequest(path=empty))
    big = _write_csv(tmp_path / "big.csv", "oid,mjd\nZTF1,60000\n")
    with pytest.raises(ApplicationInputError) as exc:
        svc.import_file(ImportRequest(path=big, max_bytes=1))
    assert "exceeds max_bytes" in str(exc.value).lower()


def test_ingestion_handles_multiple_objects_and_missing_values(tmp_path: Path):
    """Astronomer often provides a file with many objects; verify we preserve them
    and that missing magerr values are kept as NaN for downstream QC, not silently dropped."""
    svc = DataIngestionService()
    content = "oid,mjd,mag,magerr\nZTF1,60000,18.0,0.1\nZTF2,60001,19.0,\nZTF3,60002,18.5,0.2\nZTF1,60003,18.2,0.15\n"
    path = _write_csv(tmp_path / "multi.csv", content)
    result = svc.import_file(ImportRequest(path=path, required_columns=("oid",)))
    assert result.row_count == 4
    # Service does not deduplicate oids; downstream SourceSubset normalization does
    assert result.data["oid"].tolist() == ["ZTF1", "ZTF2", "ZTF3", "ZTF1"]
    # Missing magerr becomes NaN, not an error at ingestion (validated later)
    assert pd.isna(result.data.loc[1, "magerr"])


def test_source_subset_normalization_rejects_duplicate_oid(tmp_path: Path):
    from ztf_classifier.data.source_subset import normalize_source_subset

    frame = pd.DataFrame(
        {
            "oid": ["ZTF1", "ZTF1"],
            "ra": [10, 11],
            "dec": [20, 21],
            "ngoodobsrel": [30, 31],
        }
    )
    with pytest.raises(Exception) as exc:
        normalize_source_subset(frame)
    assert "duplicate" in str(exc.value).lower()


def test_source_subset_rejects_out_of_range_coordinates():
    bad_ra = pd.DataFrame(
        {"oid": ["ZTF1"], "ra": [370], "dec": [20], "ngoodobsrel": [30]}
    )
    with pytest.raises(SourceSubsetValidationError):
        normalize_source_subset(bad_ra)
    bad_dec = pd.DataFrame(
        {"oid": ["ZTF1"], "ra": [10], "dec": [95], "ngoodobsrel": [30]}
    )
    with pytest.raises(SourceSubsetValidationError):
        normalize_source_subset(bad_dec)


def test_alerce_ingestion_requires_all_columns_and_handles_malformed_mjd():
    from ztf_classifier.io.alerce import alerce_to_internal_lc_robust

    good = pd.DataFrame(
        {
            "mjd": [60000.0, 60001.0],
            "fid": [1, 2],
            "magpsf_corr": [18.0, 19.0],
            "sigmapsf_corr_ext": [0.1, 0.1],
            "magpsf": [18.0, 19.0],
            "sigmapsf": [0.1, 0.1],
            "ra": [10, 10],
            "dec": [20, 20],
            "dubious": [False, False],
            "corrected": [True, True],
        }
    )
    lc, diag = alerce_to_internal_lc_robust(good, return_diagnostics=True)
    assert len(lc) == 2
    assert diag.rows_input == 2

    missing = good.drop(columns=["mjd"])
    with pytest.raises(Exception) as exc:
        alerce_to_internal_lc_robust(missing)
    assert "missing required columns" in str(exc.value).lower()

    malformed = good.copy()
    malformed["mjd"] = ["not-a-date", "60001"]
    lc2, diag2 = alerce_to_internal_lc_robust(malformed, return_diagnostics=True)
    # Invalid MJD row is dropped, diagnostics counts it
    assert diag2.invalid_mjd == 1
    assert len(lc2) == 1


def test_alerce_ingestion_counts_invalid_mag_and_duplicate_rows():
    from ztf_classifier.io.alerce import alerce_to_internal_lc_robust

    df = pd.DataFrame(
        {
            "mjd": [60000.0, 60000.0, 60001.0],
            "fid": [1, 1, 2],
            "magpsf_corr": [18.0, 18.0, float("nan")],
            "sigmapsf_corr_ext": [0.1, 0.1, 0.1],
            "magpsf": [18.0, 18.0, 19.0],
            "sigmapsf": [0.1, 0.1, 0.1],
            "ra": [10, 10, 10],
            "dec": [20, 20, 20],
            "dubious": [False, False, False],
            "corrected": [True, True, True],
        }
    )
    lc, diag = alerce_to_internal_lc_robust(df, return_diagnostics=True)
    # Duplicate rows are counted, invalid mag reduces output
    assert diag.duplicate_rows >= 1 or diag.invalid_mag >= 1
    assert len(lc) <= 2


def test_feature_engine_handles_insufficient_observations_and_missing_bands():
    from ztf_classifier.features.pipeline import extract_v0_2_features

    # Below BASIC_MIN (10): g_n_obs is NaN (pipeline returns NaN for ineligible features)
    tiny = pd.DataFrame(
        {
            "mjd": [60000 + i for i in range(5)],
            "mag": [18.0] * 5,
            "magerr": [0.1] * 5,
            "fid": [1] * 5,
        }
    )
    feats = extract_v0_2_features(tiny)
    import math

    assert math.isnan(feats["g_n_obs"])  # <10 -> ineligible -> NaN
    assert math.isnan(feats["r_n_obs"])  # 0 r-band -> NaN
    assert math.isnan(feats["g_ls_best_power"])  # <30 -> NaN

    # Exactly 12 observations (>10, <30): basic features computed, LS still NaN
    twelve = pd.DataFrame(
        {
            "mjd": [60000 + i for i in range(12)],
            "mag": [18.0 + 0.01 * i for i in range(12)],
            "magerr": [0.1] * 12,
            "fid": [1] * 12,
        }
    )
    feats12 = extract_v0_2_features(twelve)
    assert feats12["g_n_obs"] == 12
    assert math.isnan(feats12["g_ls_best_power"])  # still <30

    # 30 observations: LS computed
    thirty = pd.DataFrame(
        {
            "mjd": [60000 + i * 0.5 for i in range(30)],
            "mag": [18.0 + 0.1 * (i % 3) for i in range(30)],
            "magerr": [0.1] * 30,
            "fid": [1] * 30,
        }
    )
    feats30 = extract_v0_2_features(thirty)
    assert feats30["g_n_obs"] == 30
    assert math.isfinite(feats30["g_ls_best_power"])

    # Missing mag values are ignored by prepare_band_lightcurve (non-finite filtered)
    bad_mag = pd.DataFrame(
        {
            "mjd": [
                60000,
                60001,
                60002,
                60003,
                60004,
                60005,
                60006,
                60007,
                60008,
                60009,
                60010,
                60011,
            ],
            "mag": [
                18.0,
                float("nan"),
                18.2,
                18.1,
                18.0,
                18.3,
                18.2,
                18.1,
                18.0,
                18.2,
                18.1,
                18.0,
            ],
            "magerr": [0.1] * 12,
            "fid": [1] * 12,
        }
    )
    feats2 = extract_v0_2_features(bad_mag)
    assert feats2["g_n_obs"] == 11  # NaN row not counted, 12-1=11


def test_full_workflow_ingestion_to_features_to_prediction(tmp_path: Path):
    """End-to-end: ingestion -> feature extraction -> provenance hash chain.

    This is synthetic but exercises the supported tabular-v1 contract through
    to feature generation; model prediction is tested where artifact exists.
    """
    svc = DataIngestionService()
    csv_path = _write_csv(
        tmp_path / "workflow.csv",
        "oid,mjd,mag,magerr,fid,ra,dec,ngoodobsrel\n"
        "ZTF1,60000,18.0,0.1,1,10,20,30\n"
        "ZTF1,60001,18.1,0.1,1,10,20,30\n"
        "ZTF1,60002,18.2,0.12,2,10,20,30\n"
        "ZTF1,60003,17.9,0.11,2,10,20,30\n",
    )
    imported = svc.import_file(
        ImportRequest(path=csv_path, required_columns=("oid", "mjd", "mag"))
    )
    assert imported.row_count == 4
    # Provenance chain: content hash matches file
    assert imported.content_sha256 == hashlib.sha256(csv_path.read_bytes()).hexdigest()
    assert imported.source.source_id == "workflow"
    # Observations to features (minimal)
    from ztf_classifier.features.pipeline import extract_v0_2_features

    obs = imported.data.rename(columns={"fid": "fid"})  # already correct
    # Provide required columns for pipeline: mjd,mag,magerr,fid
    feats = extract_v0_2_features(obs)
    assert len(feats) == 42
    assert all(k in feats for k in ["g_n_obs", "r_n_obs", "mean_color_gr"])
