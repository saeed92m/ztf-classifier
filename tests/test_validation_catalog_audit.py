from __future__ import annotations

import pytest

from ztf_classifier.validation.catalog_audit import audit_event_catalog


def test_event_catalog_audit_preserves_repeated_object_ids(tmp_path):
    path = tmp_path / "events.csv"
    path.write_text(
        "oid,spec_class,energy\n00123,M3,1e32\n00123,M3,\n00456,,2e32\n",
        encoding="utf-8",
    )

    result = audit_event_catalog(path)

    assert result["event_rows"] == 3
    assert result["unique_object_ids"] == 2
    assert result["objects_with_multiple_events"] == 1
    assert result["additional_event_rows_beyond_one_per_object"] == 1
    assert result["event_multiplicity_counts"] == {"2": 1}
    assert result["missing_values_by_column"]["energy"] == 1
    assert result["class_counts"] == {"(missing)": 1, "M3": 2}
    assert result["duplicate_rows_collapsed"] == 0
    assert len(result["sha256"]) == 64


def test_event_catalog_audit_rejects_missing_id_column(tmp_path):
    path = tmp_path / "bad.csv"
    path.write_text("class,value\nM3,1\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Missing object ID"):
        audit_event_catalog(path)


def test_event_catalog_audit_rejects_blank_ids(tmp_path):
    path = tmp_path / "bad.csv"
    path.write_text("oid,value\n,1\n", encoding="utf-8")
    with pytest.raises(ValueError, match="blank"):
        audit_event_catalog(path)
