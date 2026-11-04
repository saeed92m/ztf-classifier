from __future__ import annotations

import pandas as pd
import pytest

from ztf_classifier.io.dr24_lightcurve import (
    DR24AcquisitionError,
    DR24LightcurveBackend,
    DR24LightcurveRequest,
    _canonical_records,
)


def test_request_is_bounded_and_rejects_invalid_oids() -> None:
    with pytest.raises(ValueError):
        DR24LightcurveRequest(())
    with pytest.raises(ValueError):
        DR24LightcurveRequest((1, 1))
    with pytest.raises(ValueError):
        DR24LightcurveRequest((0,))
    with pytest.raises(ValueError):
        DR24LightcurveRequest(tuple(range(1, 12)))


def test_canonical_payload_preserves_native_columns_and_hashes() -> None:
    frame = pd.DataFrame(
        {
            "hmjd": [60000.1, 60000.2],
            "mag": [18.2, 18.3],
            "magerr": [0.03, 0.04],
            "clrcoeff": [0.1, 0.1],
            "catflags": [0, 32768],
        }
    )
    records, digest = _canonical_records(frame)
    assert records[0]["hmjd"] == 60000.1
    assert records[1]["catflags"] == 32768
    assert len(digest) == 64


def test_canonical_payload_rejects_schema_drift() -> None:
    with pytest.raises(DR24AcquisitionError, match="missing required columns"):
        _canonical_records(pd.DataFrame({"hmjd": [1.0]}))


def test_backend_requires_objectid_index() -> None:
    class Collection:
        all_indexes = {"other": object()}

    class Catalog:
        all_columns = {
            "objectid", "filterid", "fieldid", "rcid", "objra", "objdec",
            "nepochs", "lightcurve",
        }
        hc_collection = Collection()

    backend = DR24LightcurveBackend(lambda *_args, **_kwargs: Catalog())
    with pytest.raises(DR24AcquisitionError, match="no objectid index"):
        backend.acquire(DR24LightcurveRequest((123,)))


def test_backend_reports_missing_oids_and_source_provenance() -> None:
    class Collection:
        all_indexes = {"objectid": object()}

    class Query:
        def compute(self) -> pd.DataFrame:
            return pd.DataFrame(
                [
                    {
                        "objectid": 123,
                        "filterid": 1,
                        "fieldid": 100,
                        "rcid": 4,
                        "objra": 120.0,
                        "objdec": -20.0,
                        "nepochs": 2,
                        "lightcurve": pd.DataFrame(
                            {
                                "hmjd": [60000.1, 60000.2],
                                "mag": [18.2, 18.3],
                                "magerr": [0.03, 0.04],
                                "clrcoeff": [0.1, 0.1],
                                "catflags": [0, 32768],
                            }
                        ),
                    }
                ]
            )

    class Catalog:
        all_columns = {
            "objectid", "filterid", "fieldid", "rcid", "objra", "objdec",
            "nepochs", "lightcurve",
        }
        hc_collection = Collection()

        def id_search(self, *, values: dict[str, list[int]]) -> Query:
            assert values == {"objectid": [123, 456]}
            return Query()

    result = DR24LightcurveBackend(
        lambda *_args, **_kwargs: Catalog()
    ).acquire(DR24LightcurveRequest((123, 456)))

    assert len(result.records) == 1
    assert result.records[0].objectid == 123
    assert result.records[0].catalog_nepochs == 2
    assert result.provenance["missing_oids"] == [456]
    assert result.provenance["interpretation"]["time_column"] == "hmjd"
    assert result.provenance["interpretation"]["quality"].startswith("raw")
    assert result.provenance["epoch_count"] == 2
