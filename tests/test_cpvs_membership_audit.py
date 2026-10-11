from pathlib import Path

from scripts.audit_cpvs_membership import (
    read_parent_name_to_sourceid,
    read_published_ztf_names,
    read_selected,
    read_vizier,
)


def test_read_selected_uses_sourceid_values(tmp_path: Path):
    path = tmp_path / "selected.tsv"
    path.write_text("SourceID\n1\n3\n5\n", encoding="utf-8")
    assert read_selected(path) == {1, 3, 5}


def test_parent_name_mapping_uses_published_seq_sourceids(tmp_path: Path):
    parent = tmp_path / "parent.txt"
    parent.write_text(
        "ZTFJ000000.00+000000.0 100 200\n"
        "ZTFJ000001.00+000000.0 101 201\n"
        "ZTFJ000002.00+000000.0 102 202\n",
        encoding="utf-8",
    )
    assert read_parent_name_to_sourceid(parent) == {
        "ZTFJ000000.00+000000.0": 100,
        "ZTFJ000001.00+000000.0": 101,
        "ZTFJ000002.00+000000.0": 102,
    }


def test_read_vizier_maps_fixed_width_ztf_names_not_internal_ids(tmp_path: Path):
    parent = tmp_path / "parent.txt"
    names = [
        "ZTFJ000000.00+000000.0",
        "ZTFJ000001.00+000000.0",
        "ZTFJ000002.00+000000.0",
    ]
    parent.write_text(
        "".join(f"{name} {100 + i} {200 + i}\n" for i, name in enumerate(names)),
        encoding="utf-8",
    )
    published = tmp_path / "table4.dat"
    # Internal Table 4 IDs intentionally do not match the parent row ordinals.
    lines = [
        f"{names[0]:<22}{'':1}{777:>6}  EW  0.0  0.0  0.1",
        f"{names[2]:<22}{'':1}{999:>6}  RR  0.0  0.0  0.3",
    ]
    published.write_text("\n".join(lines) + "\n", encoding="utf-8")
    assert read_vizier(published, parent) == {100, 102}


def test_read_vizier_maps_tsv_names_to_parent_sourceids(tmp_path: Path):
    parent = tmp_path / "parent.txt"
    parent.write_text(
        "ZTFJ000000.00+000000.0 100 200\n"
        "ZTFJ000001.00+000000.0 101 201\n",
        encoding="utf-8",
    )
    published = tmp_path / "table4.tsv"
    published.write_text(
        "# VizieR export\n"
        "ZTF\tID\n"
        "ZTFJ000000.00+000000.0\t7\n"
        "ZTFJ000001.00+000000.0\t9\n",
        encoding="utf-8",
    )
    assert read_published_ztf_names(published) == [
        "ZTFJ000000.00+000000.0",
        "ZTFJ000001.00+000000.0",
    ]
    assert read_vizier(published, parent) == {100, 101}

def test_read_published_names_from_whitespace_vizier_output(tmp_path: Path):
    published = tmp_path / "table4.dat"
    published.write_text(
        "#Table J/ApJ/932/118/table4\n"
        "recno ZTF ID\n"
        "1 ZTFJ000000.00+000000.0 781603\n"
        "2 ZTFJ000001.00+000000.0 781604\n",
        encoding="utf-8",
    )
    assert read_published_ztf_names(published) == [
        "ZTFJ000000.00+000000.0",
        "ZTFJ000001.00+000000.0",
    ]
