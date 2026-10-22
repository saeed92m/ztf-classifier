import json
import zipfile
from pathlib import Path

from scripts.audit_cpvs_membership import (
    read_parent_catalog,
    read_parent_metadata_fields,
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


def test_read_parent_catalog_maps_one_based_object_row_ordinals(tmp_path: Path):
    path = tmp_path / "Table2.txt"
    path.write_text(
        "metadata ignored\nZTFJ000000.00+000000.0 0.00056 12.0 1.2 EW\n"
        "ZTFJ000001.00+000000.0 0.00061 13.0 2.3 RR\n",
        encoding="utf-8",
    )
    assert read_parent_catalog(path) == {
        1: "ZTFJ000000.00+000000.0",
        2: "ZTFJ000001.00+000000.0",
    }


def test_read_parent_catalog_preserves_explicit_seq_ids(tmp_path: Path):
    path = tmp_path / "Table2-seq.txt"
    path.write_text(
        "ZTFJ000000.00+000000.0 17 12.0 -3.0 1.2 EW\\n"
        "ZTFJ000001.00+000000.0 29 13.0 -4.0 2.3 RR\\n",
        encoding="utf-8",
    )

    assert read_parent_catalog(path) == {
        17: "ZTFJ000000.00+000000.0",
        29: "ZTFJ000001.00+000000.0",
    }


def test_read_parent_metadata_fields_uses_explicit_seq(tmp_path: Path):
    path = tmp_path / "Table2.txt"
    path.write_text(
        "ZTFJ000000.13+620605.8 10 0.00056 62.10163 1.9449979 0.198 5.189 58386.2629478 16.200 15.800 1.100 1.200\\n"
        "ZTFJ000000.14+721413.7 30 0.00061 72.23716 0.2991500 0.263 6.308 58388.2555794 0 15.100 0 0.900\\n",
        encoding="utf-8",
    )

    assert read_parent_metadata_fields(path) == {
        10: {"gmag": "16.200", "rmag": "15.800", "Per-g": "1.100", "Per-r": "1.200"},
        30: {"gmag": "0", "rmag": "15.100", "Per-g": "0", "Per-r": "0.900"},
    }


def test_read_parent_catalog_reads_zip(tmp_path: Path):
    path = tmp_path / "Table2.txt.zip"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(
            "Table2.txt",
            "metadata ignored\nZTFJ000000.00+000000.0 0.00056 12.0 1.2 EW\n"
            "ZTFJ000001.00+000000.0 0.00061 13.0 2.3 RR\n",
        )
    assert read_parent_catalog(path) == {
        1: "ZTFJ000000.00+000000.0",
        2: "ZTFJ000001.00+000000.0",
    }



def test_read_parent_catalog_ignores_metadata_and_uses_object_ordinals(tmp_path: Path):
    path = tmp_path / "Table2.txt"
    path.write_text(
        "Table 2. ZTF Variables Catalog\\n"
        "ZTFJ000000.00+000000.0 0.00056 -3.0 1.2 EW\\n"
        "page footer\\n"
        "ZTFJ000001.00+000000.0 0.00061 -4.0 2.3 RR\\n",
        encoding="utf-8",
    )

    assert read_parent_catalog(path) == {
        1: "ZTFJ000000.00+000000.0",
        2: "ZTFJ000001.00+000000.0",
    }


def test_object_name_crosswalk_compares_parent_sourceids_not_catalog_ids(
    tmp_path: Path, monkeypatch
):
    from scripts import audit_cpvs_membership as audit

    parent = tmp_path / "Table2.txt"
    parent.write_text(
        "ZTFJ000000.00+000000.0 10 0.00056 20 30 EW\n"
        "ZTFJ000001.00+000000.0 20 0.00061 21 31 RR\n"
        "ZTFJ000002.00+000000.0 30 0.00080 22 32 EA\n",
        encoding="utf-8",
    )
    published = tmp_path / "table4.tsv"
    published.write_text(
        "ZTF\tID\n"
        "ZTFJ000001.00+000000.0\t101\n"
        "ZTFJ000002.00+000000.0\t102\n",
        encoding="utf-8",
    )
    candidate = tmp_path / "selected.tsv"
    candidate.write_text("SourceID\n20\n30\n", encoding="utf-8")
    output = tmp_path / "audit.json"
    monkeypatch.setattr(
        "sys.argv",
        [
            "audit_cpvs_membership.py",
            "--candidate", str(candidate),
            "--published", str(published),
            "--parent", str(parent),
            "--output", str(output),
        ],
    )

    assert audit.main() == 0
    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["catalog_internal_id_comparison_is_object_level"] is False
    assert report["object_name_crosswalk_exact_membership_match"] is True
    assert report["object_name_crosswalk_candidate_only_count"] == 0
    assert report["object_name_crosswalk_published_only_count"] == 0
