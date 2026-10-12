from pathlib import Path

from scripts.audit_cpvs_membership import read_selected, read_vizier


def test_read_selected_uses_sourceid_values(tmp_path: Path):
    path = tmp_path / "selected.tsv"
    path.write_text("SourceID\n1\n3\n5\n", encoding="utf-8")
    assert read_selected(path) == {1, 3, 5}


def test_read_vizier_reads_fixed_width_names_and_maps_to_parent_seq(tmp_path: Path):
    path = tmp_path / "table4.dat"
    names = ["ZTFJ000000.00+000000.0", "ZTFJ000001.00+000000.0", "ZTFJ000002.00+000000.0"]
    lines = [
        f"{name:<22}{'':1}{index:>6}  EW  0.0  0.0  0.1"
        for name, index in zip(names, (1, 3, 5), strict=True)
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    parent = tmp_path / "Table2.txt"
    parent.write_text(
        "ZTFJ000000.00+000000.0 105 0.00056 62.10163 1.9449979 BYDra\n"
        "ZTFJ000001.00+000000.0 309 0.00061 72.23716 0.2991500 EW\n"
        "ZTFJ000002.00+000000.0 811 0.00080 32.14645 0.2870590 EW\n",
        encoding="utf-8",
    )
    assert read_vizier(path, parent) == {105, 309, 811}


def test_read_vizier_reads_tsv_export_and_maps_to_parent_seq(tmp_path: Path):
    path = tmp_path / "table4.tsv"
    path.write_text("# VizieR export\nZTF\tID\nZTFJ000000.00+000000.0\t7\nZTFJ000001.00+000000.0\t9\n", encoding="utf-8")
    parent = tmp_path / "Table2.txt"
    parent.write_text(
        "ZTFJ000000.00+000000.0 105 0.00056 62.10163 1.9449979 BYDra\n"
        "ZTFJ000001.00+000000.0 309 0.00061 72.23716 0.2991500 EW\n",
        encoding="utf-8",
    )
    assert read_vizier(path, parent) == {105, 309}
