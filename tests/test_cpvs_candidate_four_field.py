from __future__ import annotations

from pathlib import Path

from scripts.audit_cpvs_candidate_four_field import audit


def _write(path: Path, text: str) -> Path:
    path.write_text(text, encoding="utf-8")
    return path


def test_candidate_intersection_crosswalks_table4_by_ztf_name(tmp_path: Path) -> None:
    table2 = _write(
        tmp_path / "table2.tsv",
        "ID\tSeq\tgmag\trmag\tPer-g\tPer-r\n"
        "ZTF1\t1\t18.1\t17.9\t0.4\t0.5\n"
        "ZTF2\t2\t19.1\t18.9\t0.6\t0.7\n"
        "ZTF3\t3\t0\t18.0\t0.8\t0.9\n"
        "ZTF4\t4\t17.1\t16.9\t0.2\t0.3\n"
        "ZTF5\t5\tinf\t16.9\t0.2\t0.3\n"
        "ZTF6\t6\t17.1\t16.9\tnan\t0.3\n",
    )
    # Table 4 numeric IDs deliberately differ from Table 2 Seq. The join must use ZTF.
    table4 = _write(
        tmp_path / "table4.tsv",
        "ZTF\tID\nZTF1\t91\nZTF2\t92\n",
    )
    candidates = _write(
        tmp_path / "selected.tsv",
        "SourceID\n1\n2\n3\n5\n6\n",
    )

    report = audit(table2, table4, candidates, expected_parent=None, expected_published=None)

    assert report["counts"] == {
        "parent": 6,
        "published": 2,
        "candidates": 5,
        "candidate_published_intersection": 2,
        "candidate_only": 3,
        "published_only": 0,
        "parent_four_field": 3,
        "candidate_pass_four_field": 2,
        "candidate_fail_four_field": 3,
        "four_field_parent_only": 1,
        "filtered_candidate_only": 0,
        "filtered_published_only": 0,
    }
    assert report["verdict"]["four_field_intersection_exact_match"] is True
    assert report["verdict"]["candidate_excess_equals_four_field_failures"] is True


def test_zenodo_membership_fallback_joins_by_ztf_name(tmp_path: Path) -> None:
    table2 = _write(
        tmp_path / "table2.tsv",
        "ID\tSeq\tgmag\trmag\tPer-g\tPer-r\n"
        "ZTF1\t1\t18.1\t17.9\t0.4\t0.5\n"
        "ZTF2\t2\t19.1\t18.9\t0.6\t0.7\n"
        "ZTF3\t3\t0\t18.0\t0.8\t0.9\n"
        "ZTF4\t4\t17.1\t16.9\t0.2\t0.3\n",
    )
    zenodo = _write(
        tmp_path / "1st_layer.csv",
        "ID,class\nZTF1,RR\nZTF2,EW\n",
    )
    candidates = _write(tmp_path / "selected.tsv", "SourceID\n1\n2\n3\n")

    report = audit(
        table2, None, candidates, expected_parent=None, expected_published=None,
        zenodo_csv=zenodo,
    )

    assert report["counts"]["published"] == 2
    assert report["counts"]["filtered_candidate_only"] == 0
    assert report["verdict"]["four_field_intersection_exact_match"] is True
    assert report["inputs"]["published_membership_source"].startswith("Zenodo DOI")
