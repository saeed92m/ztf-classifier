from pathlib import Path

from scripts.audit_cpvs_object_identity import audit, read_published_rows


def test_published_id_to_parent_row_name_alignment_is_checked(tmp_path: Path):
    parent = tmp_path / "parent.tsv"
    parent.write_text(
        "ZTFJ000000.01+000001.0 1\n"
        "ZTFJ000000.02+000002.0 2\n"
        "ZTFJ000000.03+000003.0 3\n",
        encoding="utf-8",
    )
    candidate = tmp_path / "selected.tsv"
    candidate.write_text("SourceID\n1\n3\n", encoding="utf-8")
    published = tmp_path / "table4.tsv"
    published.write_text(
        "# ZTF\tID\n"
        "ZTFJ000000.01+000001.0\t1\n"
        "ZTFJ000000.99+000009.0\t9\n",
        encoding="utf-8",
    )

    report = audit(parent, candidate, published)

    assert report["status"] == "ID_TO_NAME_MAPPING_NOT_VALIDATED"
    alignment = report["published_id_to_parent_row_name_alignment"]
    assert alignment["matched_count"] == 1
    assert alignment["mismatched_count"] == 0
    assert alignment["out_of_parent_ordinal_range_count"] == 1
    provisional = report["provisional_name_membership_using_row_ordinal_mapping"]
    assert provisional["interpretable"] is False


def test_published_fixed_width_table_rows_parse_ztf_and_internal_id(tmp_path: Path):
    path = tmp_path / "table4.dat"
    path.write_text(
        f"{'ZTFJ000000.01+000001.0':<22s} {1:6d} CLASS 12.00000 30.00000 0.12345\\n"
        f"{'ZTFJ000000.02+000002.0':<22s} {2:6d} CLASS 13.00000 31.00000 0.23456\\n",
        encoding="utf-8",
    )

    rows = read_published_rows(path)

    assert rows == [
        {"ztf": "ZTFJ000000.01+000001.0", "id": 1},
        {"ztf": "ZTFJ000000.02+000002.0", "id": 2},
    ]
