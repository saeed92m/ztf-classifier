"""Tests for traceable ZTF names in CPVS diagnostic records."""

from pathlib import Path

from scripts import diagnose_cpvs_selection as diagnostic


def test_source_id_to_ztf_name_map_reverses_verified_parent_mapping(monkeypatch) -> None:
    parent_mapping = {
        "ZTFJ183105.75+005641.0": 17,
        "ZTFJ204059.52+452553.6": 42,
    }
    monkeypatch.setattr(
        diagnostic,
        "read_parent_name_to_sourceid",
        lambda path: parent_mapping,
    )

    result = diagnostic.source_id_to_ztf_name_map(Path("parent.zip"))

    assert result == {
        17: "ZTFJ183105.75+005641.0",
        42: "ZTFJ204059.52+452553.6",
    }
