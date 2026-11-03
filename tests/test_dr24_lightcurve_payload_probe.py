import pandas as pd
import pytest

from scripts.probe_ztf_dr24_lightcurve_payload import (
    _nested_frame,
    canonical_payload,
    parse_oids,
    summarize_payload,
)


def _payload():
    return pd.DataFrame(
        {
            "hmjd": [60000.1, 60001.2, 60002.3],
            "mag": [17.1, 17.2, 17.3],
            "magerr": [0.02, 0.03, 0.0],
            "clrcoeff": [-0.1, -0.2, -0.3],
            "catflags": [0, 32768, 0],
        }
    )


def test_parse_oids_is_bounded_unique_and_positive():
    assert parse_oids("101, 102", maximum=2) == [101, 102]
    with pytest.raises(ValueError, match="Duplicate"):
        parse_oids("101,101")
    with pytest.raises(ValueError, match="positive"):
        parse_oids("0")
    with pytest.raises(ValueError, match="limited"):
        parse_oids(",".join(str(value) for value in range(1, 12)))


def test_nested_payload_requires_explicit_dr24_columns():
    frame = _nested_frame(_payload(), 101)
    assert list(frame.columns) == ["hmjd", "mag", "magerr", "clrcoeff", "catflags"]
    with pytest.raises(ValueError, match="missing columns"):
        _nested_frame(pd.DataFrame({"mjd": [1.0]}), 101)


def test_canonical_payload_hash_is_stable():
    first, first_hash = canonical_payload(_payload())
    second, second_hash = canonical_payload(_payload().copy())
    assert first == second
    assert first_hash == second_hash
    assert len(first_hash) == 64


def test_summary_preserves_hmjd_and_quality_flag_counts():
    payload = _payload()
    summary, epochs = summarize_payload(
        101,
        {
            "filterid": 1,
            "fieldid": 123,
            "rcid": 4,
            "objra": 10.0,
            "objdec": -2.0,
            "nepochs": 3,
        },
        payload,
    )
    assert summary["hmjd_min"] == pytest.approx(60000.1)
    assert summary["hmjd_max"] == pytest.approx(60002.3)
    assert summary["clean_catflags_zero_count"] == 2
    assert summary["catflags_counts"] == {"0": 2, "32768": 1}
    assert summary["epoch_count_matches"] is True
    assert epochs[0]["hmjd"] == pytest.approx(60000.1)
    assert summary["photometry_interpretation"].startswith("Raw DR24")


def test_summary_counts_only_finite_numeric_values():
    payload = pd.DataFrame(
        {
            "hmjd": [60000.0, float("inf"), float("nan")],
            "mag": [17.0, float("inf"), float("nan")],
            "magerr": [0.02, float("inf"), -0.1],
            "clrcoeff": [0.1, 0.2, 0.3],
            "catflags": [0, 32768, 32768.5],
        }
    )
    summary, _ = summarize_payload(
        102,
        {
            "filterid": 2,
            "fieldid": 124,
            "rcid": 5,
            "objra": 11.0,
            "objdec": -3.0,
            "nepochs": 3,
        },
        payload,
    )
    assert summary["hmjd_finite_count"] == 1
    assert summary["mag_finite_count"] == 1
    assert summary["magerr_finite_count"] == 2
    assert summary["magerr_positive_count"] == 1
    assert summary["catflags_counts"]["32768.5"] == 1
