from types import SimpleNamespace

import pandas as pd

from scripts import query_ztf_dr24_spatial_recovery as query


class _FakeCatalog:
    all_columns = [
        "oid",
        "ra",
        "dec",
        "filtercode",
        "field",
        "ccdid",
        "qid",
        "rcid",
        "fid",
    ]

    def cone_search(self, *, ra, dec, radius_arcsec):
        assert ra == 10.0
        assert dec == 20.0
        assert radius_arcsec == 5.0
        frame = pd.DataFrame(
            [
                {
                    "oid": 123,
                    "ra": 10.0001,
                    "dec": 20.0,
                    "filtercode": "zg",
                    "field": 100,
                    "ccdid": 2,
                    "qid": 3,
                    "rcid": 7,
                    "fid": 1,
                }
            ]
        )
        return SimpleNamespace(compute=lambda: frame)


def test_query_preserves_available_field_and_quadrant_provenance(monkeypatch):
    fake_lsdb = SimpleNamespace(open_catalog=lambda *args, **kwargs: _FakeCatalog())
    monkeypatch.setitem(__import__("sys").modules, "lsdb", fake_lsdb)

    matches, metadata = query.query_dr24(
        [{"external_id": "BTS_A", "ra": "10", "dec": "20"}],
        radius_arcsec=5.0,
    )

    assert metadata["selected_columns"] == [
        "oid",
        "ra",
        "dec",
        "filtercode",
        "field",
        "ccdid",
        "qid",
        "rcid",
        "fid",
    ]
    assert metadata["provenance_columns"] == [
        "field",
        "ccdid",
        "qid",
        "rcid",
        "fid",
    ]
    assert matches[0]["oid"] == "123"
    assert matches[0]["field"] == 100
    assert matches[0]["rcid"] == 7
    assert matches[0]["fid"] == 1


def test_query_fails_closed_when_required_dr24_columns_are_missing(monkeypatch):
    class IncompleteCatalog:
        all_columns = ["oid", "ra", "dec"]

    fake_lsdb = SimpleNamespace(
        open_catalog=lambda *args, **kwargs: IncompleteCatalog()
    )
    monkeypatch.setitem(__import__("sys").modules, "lsdb", fake_lsdb)

    try:
        query.query_dr24(
            [{"external_id": "BTS_A", "ra": "10", "dec": "20"}],
            radius_arcsec=5.0,
        )
    except ValueError as exc:
        assert "filtercode" in str(exc)
    else:
        raise AssertionError("missing required DR24 columns must fail closed")
