import pandas as pd
import pytest

from ztf_classifier.data.source_subset import (
    SourceSubsetValidationError,
    apply_temporal_cutoff,
    normalize_source_subset,
    qc_source_subset,
)


def test_normalization_is_deterministic_and_preserves_source_rows() -> None:
    frame = pd.DataFrame(
        {
            "OID": ["ZTF0002", "ZTF0001"],
            "RA": [20.0, 10.0],
            "DEC": [-10.0, 5.0],
            "NGOODOBSREL": [4, 7],
        }
    )

    result = normalize_source_subset(frame)

    assert result["oid"].tolist() == ["ZTF0001", "ZTF0002"]
    assert result["ngoodobsrel"].tolist() == [7, 4]
    assert qc_source_subset(frame, result).to_dict() == {
        "input_rows": 2,
        "output_rows": 2,
        "dropped_rows": 0,
    }


@pytest.mark.parametrize(
    ("column", "value"),
    [
        ("ra", 361.0),
        ("dec", 91.0),
        ("ngoodobsrel", -1),
    ],
)
def test_normalization_rejects_invalid_quality_values(column: str, value: float) -> None:
    frame = pd.DataFrame(
        {
            "oid": ["ZTF0001"],
            "ra": [10.0],
            "dec": [5.0],
            "ngoodobsrel": [3],
        }
    )
    frame.loc[0, column] = value

    with pytest.raises(SourceSubsetValidationError):
        normalize_source_subset(frame)


def test_normalization_rejects_duplicate_object_ids() -> None:
    frame = pd.DataFrame(
        {
            "oid": ["ZTF0001", "ZTF0001"],
            "ra": [10.0, 10.0],
            "dec": [5.0, 5.0],
            "ngoodobsrel": [3, 4],
        }
    )

    with pytest.raises(SourceSubsetValidationError, match="duplicate"):
        normalize_source_subset(frame)


def test_temporal_cutoff_is_inclusive() -> None:
    frame = pd.DataFrame({"oid": ["a", "b", "c"], "hmjd": [59446.0, 59447.0, 59448.0]})

    result = apply_temporal_cutoff(frame, "hmjd", 59447.0)

    assert result["oid"].tolist() == ["a", "b"]


def test_temporal_control_fails_closed_when_time_is_missing() -> None:
    frame = pd.DataFrame({"oid": ["a"]})

    with pytest.raises(SourceSubsetValidationError, match="observation time column"):
        apply_temporal_cutoff(frame, "hmjd", 59447.0)


def test_temporal_control_rejects_invalid_time_values() -> None:
    frame = pd.DataFrame({"oid": ["a", "b"], "hmjd": [59447.0, None]})

    with pytest.raises(SourceSubsetValidationError, match="null/non-numeric"):
        apply_temporal_cutoff(frame, "hmjd", 59447.0)
