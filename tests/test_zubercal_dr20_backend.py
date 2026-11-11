from __future__ import annotations

import pytest

from ztf_classifier.io.zubercal_dr20 import (
    MAX_RETURNED_ROWS,
    ZubercalDR20Backend,
    ZubercalDR20Request,
    summarize_zubercal_rows,
)


def test_zubercal_summary_preserves_multiple_ps1_candidates() -> None:
    rows = [
        {
            "objectid": 82251425938786635,
            "mjd": 59000.1,
            "band": "g",
            "mag": 18.2,
            "magerr": 300,
            "fieldid": 100,
            "rcidin": 4,
            "info": 0,
            "flag": 0,
            "objra": 142.59395,
            "objdec": -21.45313,
        },
        {
            "objectid": 82251425941826616,
            "mjd": 59000.2,
            "band": "r",
            "mag": 18.3,
            "magerr": 400,
            "fieldid": 100,
            "rcidin": 4,
            "info": 0,
            "flag": 0,
            "objra": 142.59401,
            "objdec": -21.45314,
        },
    ]
    result = summarize_zubercal_rows(
        rows,
        ztf_objectid=264114400013085,
        ra_deg=142.59396362304688,
        dec_deg=-21.453134536743164,
        radius_arcsec=1.2,
    )
    payload = result.to_dict()

    assert payload["match_state"] == "AMBIGUOUS_MULTIPLE_PS1_IDS"
    assert payload["crossmatch_decision"] == "NOT_SELECTED"
    assert [
        item["ps1_objectid"] for item in payload["candidate_summary"]
    ] == [82251425938786635, 82251425941826616]
    assert payload["provenance"]["row_count"] == 2
    assert payload["raw_rows"][0]["magerr"] == 300
    assert "separation_arcsec" not in payload["raw_rows"][0]
    assert payload["row_annotations"][0]["ps1_objectid"] == 82251425938786635
    assert payload["row_annotations"][0]["separation_arcsec"] > 0
    assert payload["semantics"]["magerr_conversion"] == "magerr_raw / 10000"

    reversed_payload = summarize_zubercal_rows(
        list(reversed(rows)),
        ztf_objectid=264114400013085,
        ra_deg=142.59396362304688,
        dec_deg=-21.453134536743164,
        radius_arcsec=1.2,
    ).to_dict()
    assert (
        payload["provenance"]["payload_sha256"]
        == reversed_payload["provenance"]["payload_sha256"]
    )
    assert reversed_payload["raw_rows"][0]["objectid"] == rows[1]["objectid"]


def test_zubercal_summary_reports_no_match_without_inventing_candidates() -> None:
    result = summarize_zubercal_rows(
        [],
        ztf_objectid=264114400013085,
        ra_deg=142.59396362304688,
        dec_deg=-21.453134536743164,
        radius_arcsec=1.2,
    )
    payload = result.to_dict()
    assert payload["match_state"] == "NO_PS1_MATCH"
    assert payload["candidate_summary"] == []
    assert payload["raw_rows"] == []


@pytest.mark.parametrize(
    "kwargs",
    [
        {"ztf_objectid": 0, "ra_deg": 1.0, "dec_deg": 1.0},
        {"ztf_objectid": 1, "ra_deg": 360.0, "dec_deg": 1.0},
        {"ztf_objectid": 1, "ra_deg": 1.0, "dec_deg": 91.0},
        {"ztf_objectid": 1, "ra_deg": 1.0, "dec_deg": 1.0, "radius_arcsec": 1.21},
    ],
)
def test_zubercal_request_rejects_invalid_bounds(kwargs: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        ZubercalDR20Request(**kwargs)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "value",
    [0, -1, True, False, 1.5, "10", MAX_RETURNED_ROWS + 1],
)
def test_backend_rejects_invalid_returned_row_limits(value: object) -> None:
    with pytest.raises(ValueError, match="max_returned_rows"):
        ZubercalDR20Backend(max_returned_rows=value)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("column", "value"),
    [
        ("objra", float("nan")),
        ("objra", float("inf")),
        ("objra", -0.1),
        ("objra", 360.0),
        ("objra", True),
        ("objra", "142.59395"),
        ("objdec", float("nan")),
        ("objdec", float("-inf")),
        ("objdec", -90.1),
        ("objdec", 90.1),
        ("objdec", False),
    ],
)
def test_zubercal_summary_rejects_invalid_row_coordinates(
    column: str,
    value: object,
) -> None:
    row = {
        "objectid": 82251425938786635,
        "mjd": 59000.1,
        "band": "g",
        "mag": 18.2,
        "magerr": 300,
        "fieldid": 100,
        "rcidin": 4,
        "info": 0,
        "flag": 0,
        "objra": 142.59395,
        "objdec": -21.45313,
    }
    row[column] = value
    expected_exception = TypeError if isinstance(value, (bool, str)) else ValueError
    with pytest.raises(expected_exception):
        summarize_zubercal_rows(
            [row],
            ztf_objectid=264114400013085,
            ra_deg=142.59396362304688,
            dec_deg=-21.453134536743164,
            radius_arcsec=1.2,
        )


def test_zubercal_summary_rejects_invalid_ps1_identity_or_coordinates() -> None:
    base = {
        "mjd": 59000.1,
        "band": "g",
        "mag": 18.2,
        "magerr": 300,
        "fieldid": 100,
        "rcidin": 4,
        "info": 0,
        "flag": 0,
        "objra": 142.59395,
        "objdec": -21.45313,
    }
    with pytest.raises(ValueError, match="PS1 objectid"):
        summarize_zubercal_rows(
            [{**base, "objectid": 0}],
            ztf_objectid=1,
            ra_deg=142.59,
            dec_deg=-21.45,
            radius_arcsec=1.2,
        )
    with pytest.raises(ValueError, match="missing objra/objdec"):
        summarize_zubercal_rows(
            [{**base, "objectid": 123, "objra": None}],
            ztf_objectid=1,
            ra_deg=142.59,
            dec_deg=-21.45,
            radius_arcsec=1.2,
        )
