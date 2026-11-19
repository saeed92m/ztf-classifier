import sys
from types import SimpleNamespace
from typing import ClassVar

import pandas as pd
import pytest

from scripts import query_ztf_dr24_lightcurve_availability as availability


class _FakeCatalog:
    all_columns: ClassVar[list[str]] = ["objectid", "filterid", "nepochs"]

    def __init__(self, rows, indexes=None):
        self.hc_collection = SimpleNamespace(
            all_indexes={"objectid": object()} if indexes is None else indexes
        )
        self._rows = rows

    def id_search(self, *, values):
        assert values == {"objectid": [101, 102]}
        return SimpleNamespace(
            compute=lambda: pd.DataFrame(self._rows)
        )


def _targets():
    return [
        {"external_id": "BTS_A", "ra": "10", "dec": "20"},
        {"external_id": "BTS_B", "ra": "11", "dec": "21"},
    ]


def _matches():
    return [
        {
            "external_id": "BTS_A",
            "oid": "101",
            "filtercode": "zg",
            "fid": "1",
        },
        {
            "external_id": "BTS_A",
            "oid": "102",
            "filtercode": "zr",
            "fid": "2",
        },
    ]


def test_indexed_lightcurve_lookup_preserves_missing_oids(monkeypatch):
    fake_catalog = _FakeCatalog(
        [{"objectid": 101, "filterid": 1, "nepochs": 44}]
    )
    monkeypatch.setitem(
        sys.modules,
        "lsdb",
        SimpleNamespace(open_catalog=lambda *args, **kwargs: fake_catalog),
    )

    oid_rows, target_rows, metadata = availability.query_lightcurve_availability(
        _targets(), _matches()
    )

    assert len(oid_rows) == 2
    assert oid_rows[0]["lightcurve_row_found"] is True
    assert oid_rows[0]["nepochs"] == 44
    assert oid_rows[0]["filter_metadata_consistent"] is True
    assert oid_rows[1]["lightcurve_row_found"] is False
    assert target_rows[0]["objects_table_oid_count"] == 2
    assert target_rows[0]["lightcurve_row_count"] == 1
    assert target_rows[0]["missing_lightcurve_oid_count"] == 1
    assert target_rows[0]["total_nepochs"] == 44
    assert target_rows[0]["zg_oids"] == 1
    assert target_rows[0]["zr_oids"] == 0
    assert target_rows[1]["objects_table_oid_count"] == 0
    assert metadata["index_search_performed"] is True
    assert metadata["requested_oid_count"] == 2
    assert metadata["found_oid_count"] == 1
    assert metadata["missing_oid_count"] == 1


def test_lightcurve_lookup_fails_closed_without_objectid_index(monkeypatch):
    fake_catalog = _FakeCatalog(
        [{"objectid": 101, "filterid": 1, "nepochs": 44}],
        indexes={"other": object()},
    )
    monkeypatch.setitem(
        sys.modules,
        "lsdb",
        SimpleNamespace(open_catalog=lambda *args, **kwargs: fake_catalog),
    )

    with pytest.raises(ValueError, match="no objectid index"):
        availability.query_lightcurve_availability(_targets(), _matches())


def test_lightcurve_lookup_fails_on_filter_metadata_mismatch(monkeypatch):
    fake_catalog = _FakeCatalog(
        [{"objectid": 101, "filterid": 2, "nepochs": 44}]
    )
    monkeypatch.setitem(
        sys.modules,
        "lsdb",
        SimpleNamespace(open_catalog=lambda *args, **kwargs: fake_catalog),
    )

    with pytest.raises(ValueError, match="filter metadata mismatch"):
        availability.query_lightcurve_availability(_targets(), _matches())
