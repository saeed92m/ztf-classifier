from pathlib import Path

from scripts.audit_cpvs_membership import (
    normalize_name,
    read_parent_name_map,
    read_selected,
    read_vizier_names,
)


def test_read_selected_uses_sourceid_values(tmp_path: Path):
    path = tmp_path / "selected.tsv"
    path.write_text("SourceID\n1\n3\n5\n", encoding="utf-8")
    assert read_selected(path) == {1, 3, 5}


def test_read_vizier_reads_fixed_width_object_names(tmp_path: Path):
    path = tmp_path / "table4.dat"
    lines = [
        f"{'ZTFJ000000.00+000000.0':<22}{'':1}{999:>6}  EW  0.0  0.0  0.1",
        f"{'ZTFJ000001.00+000000.0':<22}{'':1}{777:>6}  EA  0.0  0.0  0.2",
        f"{'ZTFJ000002.00+000000.0':<22}{'':1}{555:>6}  RR  0.0  0.0  0.3",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    assert read_vizier_names(path) == {
        "ZTFJ000000.00+000000.0",
        "ZTFJ000001.00+000000.0",
        "ZTFJ000002.00+000000.0",
    }


def test_read_vizier_reads_tsv_object_name_not_internal_id(tmp_path: Path):
    path = tmp_path / "table4.tsv"
    path.write_text(
        "# VizieR export\nZTF\tID\n"
        "ZTFJ000000.00+000000.0\t700007\n"
        "ZTFJ000001.00+000000.0\t900009\n",
        encoding="utf-8",
    )
    assert read_vizier_names(path) == {
        "ZTFJ000000.00+000000.0",
        "ZTFJ000001.00+000000.0",
    }


def test_parent_name_crosswalk_maps_z_tf_name_to_seq(tmp_path: Path):
    path = tmp_path / "table2.tsv"
    path.write_text(
        "# VizieR export\n"
        "Seq\tID\tPer\n"
        " \t \td\n"
        "------\t----------------------\t---\n"
        "1\tZTFJ000000.00+000000.0\t0.5\n"
        "3\tZTF J000001.00+000000.0\t0.7\n",
        encoding="utf-8",
    )
    mapping = read_parent_name_map(path)
    assert mapping == {
        "ZTFJ000000.00+000000.0": 1,
        "ZTFJ000001.00+000000.0": 3,
    }
    assert normalize_name(" ZTF J000001.00+000000.0 ") == "ZTFJ000001.00+000000.0"


def test_membership_join_does_not_use_table4_internal_id(tmp_path: Path):
    parent = tmp_path / "table2.tsv"
    parent.write_text(
        "Seq\tID\tPer\n"
        "1\tZTFJ000000.00+000000.0\t0.5\n"
        "3\tZTFJ000001.00+000000.0\t0.7\n",
        encoding="utf-8",
    )
    published = tmp_path / "table4.tsv"
    published.write_text(
        "ZTF\tID\nZTFJ000000.00+000000.0\t900001\n",
        encoding="utf-8",
    )
    parent_map = read_parent_name_map(parent)
    published_names = read_vizier_names(published)
    published_ids = {parent_map[name] for name in published_names}
    assert published_ids == {1}
    assert 900001 not in published_ids
