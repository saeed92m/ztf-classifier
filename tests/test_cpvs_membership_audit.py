import json
from pathlib import Path

import pytest

from scripts.audit_cpvs_membership import (
    crosscheck_published_names_against_ids,
    normalize_name,
    read_parent_name_map,
    read_published_table4_ids,
    read_selected,
    read_vizier_names,
)
from scripts.audit_cpvs_membership import (
    main as audit_main,
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


# ---------------------------------------------------------------------------
# Fail-closed guarantees for the Table 2 -> parent-id crosswalk.
#
# The membership result is only meaningful if the crosswalk is one-to-one and
# derived from a documented identifier column. These tests pin the behaviours
# that previously failed silently.
# ---------------------------------------------------------------------------


def _fixed_width_row(name: str, seq: int, period: str = "0.5") -> str:
    """Build one CDS-style table2.dat row: name in cols 1-23, Seq in 24-29."""
    return f"{name:<23}{seq:>6}  {period}  18.0  0.1"


def test_fixed_width_parent_map_reads_seq_column_not_row_ordinal(tmp_path: Path):
    """The parent identifier comes from the Seq column, never from row order.

    Table 2 has 781,602 rows while Seq spans [1/781604], so at least two Seq
    values are absent. Once a gap is passed, a row's ordinal is lower than its
    Seq. An ordinal-derived identifier would therefore mislabel every object
    after the first gap while raising nothing.

    The gap is reproduced here directly: Seq 3 is skipped, so the third data row
    has ordinal 3 but Seq 5.
    """
    path = tmp_path / "table2.dat"
    path.write_text(
        "\n".join(
            [
                _fixed_width_row("ZTFJ000000.00+000000.0", 1),
                _fixed_width_row("ZTFJ000001.00+000000.0", 2),
                # Seq 3 and 4 absent from the catalogue.
                _fixed_width_row("ZTFJ000004.00+000000.0", 5),
                _fixed_width_row("ZTFJ000005.00+000000.0", 6),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    mapping = read_parent_name_map(path)
    assert mapping == {
        "ZTFJ000000.00+000000.0": 1,
        "ZTFJ000001.00+000000.0": 2,
        "ZTFJ000004.00+000000.0": 5,
        "ZTFJ000005.00+000000.0": 6,
    }
    # The ordinal of the third data row is 3, and it must not be used.
    assert mapping["ZTFJ000004.00+000000.0"] != 3


def test_fixed_width_parent_map_rejects_non_integer_seq_column(tmp_path: Path):
    """A shifted layout must fail loudly instead of being read as identifiers."""
    path = tmp_path / "table2.dat"
    bad_row = f"{'ZTFJ000000.00+000000.0':<23}{'XXXXXX':>6}  0.5  18.0  0.1\n"
    path.write_text(bad_row, encoding="utf-8")

    with pytest.raises(ValueError, match="not a Seq integer"):
        read_parent_name_map(path)


def test_fixed_width_parent_map_rejects_non_ztf_name_column(tmp_path: Path):
    """If the name column is not where the ReadMe says, refuse the file."""
    path = tmp_path / "table2.dat"
    bad_row = f"{'not-a-ztf-name':<23}{1:>6}  0.5  18.0  0.1\n"
    path.write_text(bad_row, encoding="utf-8")

    with pytest.raises(ValueError, match="do not hold a ZTF object name"):
        read_parent_name_map(path)


def test_duplicate_normalized_parent_name_is_rejected(tmp_path: Path):
    """Two spellings that normalize to one name make the mapping ambiguous."""
    path = tmp_path / "table2.tsv"
    path.write_text(
        "Seq\tID\tPer\n"
        "1\tZTFJ000000.00+000000.0\t0.5\n"
        "2\tZTF J000000.00+000000.0\t0.7\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="duplicate normalized parent name"):
        read_parent_name_map(path)


def test_duplicate_normalized_published_name_is_rejected(tmp_path: Path):
    """The same ambiguity on the published side must also fail closed."""
    path = tmp_path / "table4.tsv"
    path.write_text(
        "ZTF\tID\nZTFJ000000.00+000000.0\t10\nZTF J000000.00+000000.0\t11\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="duplicate normalized published ZTF names"):
        read_vizier_names(path)


def test_duplicate_seq_is_rejected(tmp_path: Path):
    """One Seq claimed by two names is not a usable crosswalk."""
    path = tmp_path / "table2.tsv"
    path.write_text(
        "Seq\tID\tPer\n"
        "7\tZTFJ000000.00+000000.0\t0.5\n"
        "7\tZTFJ000001.00+000000.0\t0.7\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="is claimed by both"):
        read_parent_name_map(path)


def test_malformed_tsv_row_is_rejected_not_skipped(tmp_path: Path):
    """A short row must not be skipped; that would drop objects silently."""
    path = tmp_path / "table2.tsv"
    path.write_text(
        "Seq\tID\tPer\n1\tZTFJ000000.00+000000.0\t0.5\n2\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="expected at least"):
        read_parent_name_map(path)


def test_empty_parent_file_is_rejected(tmp_path: Path):
    """No rows must be an error, never an empty crosswalk."""
    path = tmp_path / "table2.tsv"
    path.write_text("Seq\tID\tPer\n", encoding="utf-8")

    with pytest.raises(ValueError, match="cannot build parent name crosswalk"):
        read_parent_name_map(path)


def test_published_name_absent_from_parent_is_rejected(tmp_path: Path):
    """An unmapped published object must fail, not be dropped or guessed."""
    parent = tmp_path / "table2.tsv"
    parent.write_text(
        "Seq\tID\tPer\n1\tZTFJ000000.00+000000.0\t0.5\n",
        encoding="utf-8",
    )
    candidate = tmp_path / "selected.tsv"
    candidate.write_text("SourceID\n1\n", encoding="utf-8")
    published = tmp_path / "table4.tsv"
    published.write_text(
        "ZTF\tID\nZTFJ999999.00+000000.0\t42\n",
        encoding="utf-8",
    )
    output = tmp_path / "report.json"

    rc = audit_main(
        [
            "--candidate",
            str(candidate),
            "--published",
            str(published),
            "--parent",
            str(parent),
            "--output",
            str(output),
        ]
    )

    # Exit code 1 means "could not evaluate". It must never be conflated with
    # exit code 2 ("evaluated, the sets differ"), which is a real result.
    assert rc == 1
    assert not output.exists(), "no report may be written from an unmapped join"


def test_end_to_end_audit_maps_by_name_and_reports_both_directions(tmp_path: Path):
    """The audit reports candidate-only and published-only as separate sets."""
    parent = tmp_path / "table2.tsv"
    parent.write_text(
        "Seq\tID\tPer\n"
        "1\tZTFJ000000.00+000000.0\t0.5\n"
        "2\tZTFJ000001.00+000000.0\t0.6\n"
        "3\tZTFJ000002.00+000000.0\t0.7\n",
        encoding="utf-8",
    )
    candidate = tmp_path / "selected.tsv"
    # 1 and 2 are candidates; 3 is not reconstructed.
    candidate.write_text("SourceID\n1\n2\n4\n", encoding="utf-8")
    published = tmp_path / "table4.tsv"
    # Published membership is objects at Seq 1 and 2.
    published.write_text(
        "ZTF\tID\nZTFJ000000.00+000000.0\t500\nZTFJ000001.00+000000.0\t501\n",
        encoding="utf-8",
    )
    output = tmp_path / "report.json"

    rc = audit_main(
        [
            "--candidate",
            str(candidate),
            "--published",
            str(published),
            "--parent",
            str(parent),
            "--output",
            str(output),
        ]
    )

    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["published_count"] == 2
    assert report["intersection_count"] == 2
    assert report["candidate_only_count"] == 1
    assert report["candidate_only_sample"] == [4]
    assert report["published_only_count"] == 0
    assert report["published_unmapped_name_count"] == 0
    assert report["membership_join_key"].startswith("normalized ZTF object name")
    assert report["exact_membership_match"] is False
    # A non-empty difference is reported, and the exit status says so.
    assert rc == 2


# ---------------------------------------------------------------------------
# Independent cross-check of the published membership.
#
# The ReadMes document one shared identifier namespace: published table4.dat has
# "ID [1/781604] Catalog internal identifier" in columns 24-29, and parent
# table2.dat has "Seq [1/781604] Internal source identifier" in the same columns.
# Because table4.dat holds only 730,184 rows, its ID cannot be a row position in
# itself.
#
# That makes a second, independent route to membership available. When both
# routes agree, the crosswalk and the identifier handling are both corroborated.
# When they disagree, the audit must refuse to report a number rather than pick
# the route it prefers.
# ---------------------------------------------------------------------------


def _table4_row(name: str, internal_id: int, klass: str = "EW") -> str:
    """Build one CDS-style table4.dat row (Lrecl 63)."""
    return (
        f"{name:<22} {internal_id:>6} {klass:<5} "
        f"{123.45678:>9.5f} {45.67890:>9.5f} {0.12345:>7.5f}"
    )


def test_read_published_table4_ids_reads_documented_id_column(tmp_path: Path):
    path = tmp_path / "table4.dat"
    path.write_text(
        "\n".join(
            [
                _table4_row("ZTFJ000000.00+000000.0", 1),
                _table4_row("ZTFJ000004.00+000000.0", 5),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    assert read_published_table4_ids(path) == {1, 5}


def test_crosscheck_agrees_when_name_and_id_routes_match(tmp_path: Path):
    parent = tmp_path / "table2.tsv"
    parent.write_text(
        "Seq\tID\tPer\n"
        "1\tZTFJ000000.00+000000.0\t0.5\n"
        "5\tZTFJ000004.00+000000.0\t0.6\n",
        encoding="utf-8",
    )
    published = tmp_path / "table4.dat"
    published.write_text(
        "\n".join(
            [
                _table4_row("ZTFJ000000.00+000000.0", 1),
                _table4_row("ZTFJ000004.00+000000.0", 5),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    parent_map = read_parent_name_map(parent)
    names = read_vizier_names(published)

    result = crosscheck_published_names_against_ids(published, names, parent_map)
    assert result["published_id_crosscheck"] == "AGREE"
    assert result["published_id_count"] == 2
    assert result["published_name_join_count"] == 2


def test_crosscheck_refuses_when_name_and_id_routes_disagree(tmp_path: Path):
    """A shifted or mis-parsed layout must stop the audit, not pick a winner."""
    parent = tmp_path / "table2.tsv"
    parent.write_text(
        "Seq\tID\tPer\n"
        "1\tZTFJ000000.00+000000.0\t0.5\n"
        "5\tZTFJ000004.00+000000.0\t0.6\n",
        encoding="utf-8",
    )
    # The ID column claims 1 and 5, but the names resolve to 1 and 5 as well,
    # so force the disagreement by changing which object the name belongs to.
    published = tmp_path / "table4.dat"
    published.write_text(
        "\n".join(
            [
                _table4_row("ZTFJ000000.00+000000.0", 1),
                _table4_row("ZTFJ000004.00+000000.0", 9),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    parent_map = read_parent_name_map(parent)
    names = read_vizier_names(published)

    with pytest.raises(ValueError, match="inconsistent between the object-name join"):
        crosscheck_published_names_against_ids(published, names, parent_map)


def test_crosscheck_rejects_blank_or_non_numeric_id_field(tmp_path: Path):
    parent = tmp_path / "table2.tsv"
    parent.write_text(
        "Seq\tID\tPer\n1\tZTFJ000000.00+000000.0\t0.5\n", encoding="utf-8"
    )
    published = tmp_path / "table4.dat"
    row = f"{'ZTFJ000000.00+000000.0':<22} {'XXXXXX':>6} EW    123.45678  45.67890 0.12345"
    published.write_text(row + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="not a Table 4 ID"):
        read_published_table4_ids(published)


def test_crosscheck_is_opt_in_and_reported(tmp_path: Path):
    """Without the flag the audit still runs; with it the result is recorded."""
    parent = tmp_path / "table2.tsv"
    parent.write_text(
        "Seq\tID\tPer\n"
        "1\tZTFJ000000.00+000000.0\t0.5\n"
        "5\tZTFJ000004.00+000000.0\t0.6\n",
        encoding="utf-8",
    )
    candidate = tmp_path / "selected.tsv"
    candidate.write_text("SourceID\n1\n5\n", encoding="utf-8")
    published = tmp_path / "table4.dat"
    published.write_text(
        "\n".join(
            [
                _table4_row("ZTFJ000000.00+000000.0", 1),
                _table4_row("ZTFJ000004.00+000000.0", 5),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    output = tmp_path / "report.json"

    rc = audit_main(
        [
            "--candidate",
            str(candidate),
            "--published",
            str(published),
            "--parent",
            str(parent),
            "--output",
            str(output),
            "--crosscheck-published-ids",
        ]
    )

    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["published_id_crosscheck"] == "AGREE"
    assert report["published_count"] == 2
    assert report["published_only_count"] == 0
    assert report["exact_membership_match"] is True
    assert rc == 0
