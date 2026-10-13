from pathlib import Path

from scripts.audit_cpvs_membership import (
    duplicate_summary,
    read_selected,
    read_selected_rows,
    read_vizier,
    read_vizier_rows,
)


def test_read_selected_uses_sourceid_values(tmp_path: Path):
    path = tmp_path / "selected.tsv"
    path.write_text("SourceID\n1\n3\n5\n", encoding="utf-8")
    assert read_selected(path) == {1, 3, 5}


def test_read_selected_preserves_duplicate_rows_for_audit(tmp_path: Path):
    path = tmp_path / "selected.tsv"
    path.write_text("SourceID\n1\n3\n3\n5\n", encoding="utf-8")
    rows = read_selected_rows(path)
    assert rows == [1, 3, 3, 5]
    assert duplicate_summary(rows) == {
        "row_count": 4,
        "unique_count": 3,
        "duplicate_id_count": 1,
        "duplicate_row_count": 1,
        "duplicate_id_sample": [3],
    }


def test_read_vizier_reads_fixed_width_id_column(tmp_path: Path):
    path = tmp_path / "table4.dat"
    lines = [
        f"{'ZTFJ000000.00+000000.0':<22}{'':1}{1:>6}  EW  0.0  0.0  0.1",
        f"{'ZTFJ000001.00+000000.0':<22}{'':1}{3:>6}  EA  0.0  0.0  0.2",
        f"{'ZTFJ000002.00+000000.0':<22}{'':1}{5:>6}  RR  0.0  0.0  0.3",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    rows, parser = read_vizier_rows(path)
    assert parser == "fixed_width"
    assert rows == [1, 3, 5]
    assert read_vizier(path) == {1, 3, 5}


def test_read_vizier_preserves_duplicate_rows(tmp_path: Path):
    path = tmp_path / "table4.tsv"
    path.write_text(
        "# VizieR export\nZTF\tID\nZTFJ000000.00+000000.0\t7\n"
        "ZTFJ000001.00+000000.0\t7\nZTFJ000002.00+000000.0\t9\n",
        encoding="utf-8",
    )
    rows, parser = read_vizier_rows(path)
    assert parser == "tsv"
    assert rows == [7, 7, 9]
    assert read_vizier(path) == {7, 9}
    assert duplicate_summary(rows)["duplicate_row_count"] == 1


def test_read_vizier_reads_tsv_export(tmp_path: Path):
    path = tmp_path / "table4.tsv"
    path.write_text(
        "# VizieR export\nZTF\tID\n"
        "ZTFJ000000.00+000000.0\t7\nZTFJ000001.00+000000.0\t9\n",
        encoding="utf-8",
    )
    assert read_vizier(path) == {7, 9}
