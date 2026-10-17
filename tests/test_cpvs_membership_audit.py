from pathlib import Path

from scripts.audit_cpvs_membership import (
    read_parent_name_to_sourceid,
    read_published_ztf_names,
    read_selected,
    read_vizier,
)
from scripts.diagnose_cpvs_selection import membership_by_type, parent_catalog_metadata


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



def test_parent_catalog_metadata_parses_tokenized_table2_columns(tmp_path: Path):
    parent = tmp_path / "Table2.txt"
    fields = [
        "ZTFJ000000.13+620605.8",
        "100",
        "0.00056",
        "62.10163",
        "1.9449979",
        "0.500",
        "3.140",
        "0.0000000",
        "15.000",
        "14.000",
        "1.0000000",
        "1.0000000",
        "11",
        "12",
        "0.500",
        "0.500",
        "0.100",
        "0.100",
        "0.900",
        "0.900",
        "0.100",
        "0.100",
        "-5.000",
        "-5.000",
        "EW",
        "0.000",
        "0.000",
    ]
    parent.write_text(" ".join(fields) + "\n", encoding="utf-8")

    metadata = parent_catalog_metadata(parent)

    assert metadata[100] == {
        "ztf_name": "ZTFJ000000.13+620605.8",
        "type": "EW",
        "ng": 11,
        "nr": 12,
    }
    assert membership_by_type({100}, metadata) == {"EW": 1}


def test_parent_catalog_metadata_parses_split_ztf_name_rows(tmp_path: Path):
    parent = tmp_path / "Table2.txt"
    fields = [
        "ZTF",
        "J000000.14+721413.7",
        "101",
        "0.00061",
        "72.23716",
        "0.2991500",
        "0.500",
        "3.140",
        "0.0000000",
        "15.000",
        "14.000",
        "1.0000000",
        "1.0000000",
        "21",
        "22",
        "0.500",
        "0.500",
        "0.100",
        "0.100",
        "0.900",
        "0.900",
        "0.100",
        "0.100",
        "-5.000",
        "-5.000",
        "BYDra",
        "0.000",
        "0.000",
    ]
    parent.write_text(" ".join(fields) + "\n", encoding="utf-8")

    metadata = parent_catalog_metadata(parent)

    assert metadata[101] == {
        "ztf_name": "ZTFJ000000.14+721413.7",
        "type": "BYDra",
        "ng": 21,
        "nr": 22,
    }



def test_parent_catalog_metadata_uses_fixed_width_offsets_when_verified(tmp_path: Path):
    parent = tmp_path / "Table2.txt"
    row = [" "] * 228

    def put(start: int, end: int, value: str, *, left: bool = False) -> None:
        width = end - start
        text = value.ljust(width) if left else value.rjust(width)
        assert len(text) == width
        row[start:end] = text

    put(0, 22, "ZTFJ000000.15+721413.7", left=True)
    put(23, 29, "102")
    put(30, 39, "0.00061")
    put(40, 49, "72.23716")
    put(50, 61, "0.2991500")
    # Leave phi21 blank to ensure token splitting cannot accidentally shift columns.
    put(75, 88, "0.0000000")
    put(89, 95, "15.000")
    put(96, 102, "14.000")
    put(103, 116, "1.0000000")
    put(117, 130, "1.0000000")
    put(131, 135, "21")
    put(136, 140, "22")
    put(141, 147, "0.500")
    put(148, 154, "0.500")
    put(155, 160, "0.100")
    put(161, 166, "0.100")
    put(167, 173, "0.900")
    put(174, 180, "0.900")
    put(181, 186, "0.100")
    put(187, 192, "0.100")
    put(193, 201, "-5.000")
    put(202, 210, "-5.000")
    put(211, 216, "BYDra", left=True)
    put(217, 222, "0.000")
    put(223, 228, "0.000")
    parent.write_text("".join(row) + "\n", encoding="utf-8")

    metadata = parent_catalog_metadata(parent)

    assert metadata[102] == {
        "ztf_name": "ZTFJ000000.15+721413.7",
        "type": "BYDra",
        "ng": 21,
        "nr": 22,
    }


def test_fixed_stratified_samples_are_reproducible_and_balanced():
    from scripts.diagnose_cpvs_selection import fixed_stratified_samples

    parent = set(range(2000))
    published = set(range(1000))
    first = fixed_stratified_samples(parent, published)
    second = fixed_stratified_samples(parent, published)

    assert first == second
    assert len(first["sample_100"]) == 100
    assert len(first["sample_1000"]) == 1000
    assert set(first["sample_100"]).issubset(first["sample_1000"])
    assert sum(oid in published for oid in first["sample_100"]) == 50
    assert sum(oid not in published for oid in first["sample_100"]) == 50
    assert sum(oid in published for oid in first["sample_1000"]) == 500
    assert sum(oid not in published for oid in first["sample_1000"]) == 500
