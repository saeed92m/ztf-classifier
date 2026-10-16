from pathlib import Path

from scripts.audit_cpvs_object_identity import audit, read_published_rows


def test_published_id_to_parent_source_id_name_alignment_is_checked(tmp_path: Path):
    parent = tmp_path / "parent.tsv"
    parent.write_text(
        "ZTFJ000000.01+000001.0 1 10.0 20.0\n"
        "ZTFJ000000.02+000002.0 2 11.0 21.0\n"
        "ZTFJ000000.03+000003.0 3 12.0 22.0\n",
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
    alignment = report["published_id_to_parent_name_alignment"]
    assert alignment["matched_count"] == 1
    assert alignment["mismatched_count"] == 0
    assert alignment["ids_outside_parent_count"] == 1
    assert report["object_name_membership"]["interpretable"] is False


def test_parent_mapping_uses_explicit_seq_not_row_ordinal(tmp_path: Path):
    parent = tmp_path / "Table2.txt"
    parent.write_text(
        f"{'ZTFJ000000.01+000001.0':<22s} {10:6d} 12.0 20.0\n"
        f"{'ZTFJ000000.02+000002.0':<22s} {12:6d} 13.0 21.0\n",
        encoding="utf-8",
    )
    candidate = tmp_path / "selected.tsv"
    candidate.write_text("SourceID\n10\n12\n", encoding="utf-8")
    published = tmp_path / "table4.tsv"
    published.write_text(
        "# ZTF\tID\n"
        "ZTFJ000000.01+000001.0\t10\n"
        "ZTFJ000000.02+000002.0\t12\n",
        encoding="utf-8",
    )

    report = audit(parent, candidate, published)

    assert report["status"] == "ID_TO_NAME_MAPPING_VALIDATED"
    assert report["parent"]["source_id_mapping_methods"] == {"explicit_seq": 2}
    assert report["parent"]["row_ordinal_vs_source_id_mismatch_count"] == 2
    assert report["object_name_membership"]["intersection_count"] == 2


def test_published_fixed_width_table_rows_parse_ztf_and_internal_id(tmp_path: Path):
    path = tmp_path / "table4.dat"
    path.write_text(
        f"{'ZTFJ000000.01+000001.0':<22s} {1:6d} CLASS 12.00000 30.00000 0.12345\n"
        f"{'ZTFJ000000.02+000002.0':<22s} {2:6d} CLASS 13.00000 31.00000 0.23456\n",
        encoding="utf-8",
    )

    rows = read_published_rows(path)

    assert rows == [
        {"ztf": "ZTFJ000000.01+000001.0", "id": 1},
        {"ztf": "ZTFJ000000.02+000002.0", "id": 2},
    ]
