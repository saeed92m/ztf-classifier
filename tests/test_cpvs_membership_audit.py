from pathlib import Path

from scripts.audit_cpvs_membership import read_selected, read_vizier


def test_read_selected_uses_sourceid_values(tmp_path: Path):
    path = tmp_path / "selected.tsv"
    path.write_text("SourceID\n1\n3\n5\n", encoding="utf-8")
    assert read_selected(path) == {1, 3, 5}


def test_read_vizier_reads_fixed_width_id_column(tmp_path: Path):
    path = tmp_path / "table4.dat"
    lines = [
        f"{'ZTFJ000000.00+000000.0':<22}{'':1}{1:>6}  EW  0.0  0.0  0.1",
        f"{'ZTFJ000001.00+000000.0':<22}{'':1}{3:>6}  EA  0.0  0.0  0.2",
        f"{'ZTFJ000002.00+000000.0':<22}{'':1}{5:>6}  RR  0.0  0.0  0.3",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    assert read_vizier(path) == {1, 3, 5}
