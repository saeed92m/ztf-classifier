import zipfile
from pathlib import Path

from scripts.audit_cpvs_membership import (
    read_parent_catalog,
    read_selected,
    read_vizier,
    read_vizier_rows,
)


def test_read_selected_uses_sourceid_values(tmp_path: Path):
    path = tmp_path / "selected.tsv"
    path.write_text("SourceID\n1\n3\n5\n", encoding="utf-8")
    assert read_selected(path) == {1, 3, 5}


def test_read_vizier_reads_fixed_width_id_and_name(tmp_path: Path):
    path = tmp_path / "table4.dat"
    lines = [
        f"{'ZTFJ000000.00+000000.0':<22}{'':1}{1:>6}  EW  0.0  0.0  0.1",
        f"{'ZTFJ000001.00+000000.0':<22}{'':1}{3:>6}  EA  0.0  0.0  0.2",
        f"{'ZTFJ000002.00+000000.0':<22}{'':1}{5:>6}  RR  0.0  0.0  0.3",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    assert read_vizier(path) == {1, 3, 5}
    assert read_vizier_rows(path) == {
        1: "ZTFJ000000.00+000000.0",
        3: "ZTFJ000001.00+000000.0",
        5: "ZTFJ000002.00+000000.0",
    }


def test_read_vizier_reads_tsv_export(tmp_path: Path):
    path = tmp_path / "table4.tsv"
    path.write_text(
        "# VizieR export\nZTF\tID\nZTFJ000000.00+000000.0\t7\nZTFJ000001.00+000000.0\t9\n",
        encoding="utf-8",
    )
    assert read_vizier(path) == {7, 9}
    assert read_vizier_rows(path) == {
        7: "ZTFJ000000.00+000000.0",
        9: "ZTFJ000001.00+000000.0",
    }


def test_read_parent_catalog_maps_one_based_row_ordinals(tmp_path: Path):
    path = tmp_path / "Table2.txt"
    path.write_text(
        "metadata ignored\nZTFJ000000.00+000000.0 12.0 -3.0\n"
        "ZTFJ000001.00+000000.0 13.0 -4.0\n",
        encoding="utf-8",
    )
    assert read_parent_catalog(path) == {
        1: "ZTFJ000000.00+000000.0",
        2: "ZTFJ000001.00+000000.0",
    }


def test_read_parent_catalog_reads_zip(tmp_path: Path):
    path = tmp_path / "Table2.txt.zip"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(
            "Table2.txt",
            "metadata ignored\nZTFJ000000.00+000000.0 12.0 -3.0\n"
            "ZTFJ000001.00+000000.0 13.0 -4.0\n",
        )
    assert read_parent_catalog(path) == {
        1: "ZTFJ000000.00+000000.0",
        2: "ZTFJ000001.00+000000.0",
    }
