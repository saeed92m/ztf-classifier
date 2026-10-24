"""Tests for CPVS membership audit with row-level duplicate evidence (issue #184)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.audit_cpvs_membership import (
    _canonical_multiset_digest,
    read_selected,
    read_vizier,
)

_ENV = dict(os.environ)
_ENV["PYTHONPATH"] = "src:." + os.pathsep + _ENV.get("PYTHONPATH", "")


def _fixed_width(name: str, ident: str) -> str:
    """Build a CDS table4.dat record: 22-char name, 1 space, 6-wide ID.

    The ID must land in the documented ``[23:29]`` slice.
    """
    return f"{name:<22}{'':1}{ident:>6}  EW  0.0  0.0  0.1"


def _vizier_tsv(lines: list[str]) -> str:
    """Build a VizieR TSV export content with header ZTF\tID."""
    header = "# VizieR export\nZTF\tID\n"
    rows = "".join(f"ZTFJ{oid:010d}.00+000000.0\t{oid}\n" for oid in lines)
    return header + rows


def _run_audit(
    cand: Path, pub: Path, out: Path, extra_args: list[str] | None = None
) -> subprocess.CompletedProcess:
    return subprocess.run(
        [
            sys.executable,
            "scripts/audit_cpvs_membership.py",
            "--candidate",
            str(cand),
            "--published",
            str(pub),
            "--output",
            str(out),
            *(extra_args or []),
        ],
        capture_output=True,
        text=True,
        check=False,
        env=_ENV,
    )


def test_read_selected_returns_row_evidence(tmp_path: Path):
    path = tmp_path / "selected.tsv"
    path.write_text("SourceID\n1\n3\n5\n", encoding="utf-8")
    result = read_selected(path)
    assert result["unique"] == {1, 3, 5}
    assert result["rows"] == [1, 3, 5]
    assert result["row_count"] == 3
    assert result["unique_count"] == 3
    assert result["duplicate_ids"] == []
    assert result["duplicate_row_count"] == 0
    assert result["parser_mode"] == "tsv"
    assert isinstance(result["ordered_rows_sha256"], str)
    assert isinstance(result["unique_ids_sha256"], str)
    assert len(result["ordered_rows_sha256"]) == 64
    assert len(result["unique_ids_sha256"]) == 64


def test_read_selected_preserves_duplicate_rows(tmp_path: Path):
    """Duplicate rows are preserved in ordered rows and counted."""
    path = tmp_path / "selected.tsv"
    path.write_text("SourceID\n1\n3\n3\n5\n5\n5\n", encoding="utf-8")
    result = read_selected(path)
    assert result["rows"] == [1, 3, 3, 5, 5, 5]
    assert result["unique"] == {1, 3, 5}
    assert result["row_count"] == 6
    assert result["unique_count"] == 3
    assert result["duplicate_ids"] == [3, 5]
    assert result["duplicate_row_count"] == 3


def test_read_selected_rejects_missing_header(tmp_path: Path):
    path = tmp_path / "bad.tsv"
    path.write_text("ID\n1\n3\n5\n", encoding="utf-8")
    try:
        read_selected(path)
        assert False, "should raise ValueError for missing SourceID header"
    except ValueError:
        pass


def test_read_vizier_reads_fixed_width_id_column(tmp_path: Path):
    path = tmp_path / "table4.dat"
    lines = [
        f"{'ZTFJ000000.00+000000.0':<22}{'':1}{1:>6}  EW  0.0  0.0  0.1",
        f"{'ZTFJ000001.00+000000.0':<22}{'':1}{3:>6}  EA  0.0  0.0  0.2",
        f"{'ZTFJ000002.00+000000.0':<22}{'':1}{5:>6}  RR  0.0  0.0  0.3",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    result = read_vizier(path)
    assert result["unique"] == {1, 3, 5}
    assert result["row_count"] == 3
    assert result["unique_count"] == 3
    assert result["duplicate_ids"] == []
    assert result["parser_mode"] == "fixed-width"


def test_read_vizier_reads_tsv_export(tmp_path: Path):
    path = tmp_path / "table4.tsv"
    path.write_text(
        "# VizieR export\nZTF\tID\nZTFJ000000.00+000000.0\t7\nZTFJ000001.00+000000.0\t9\n",
        encoding="utf-8",
    )
    result = read_vizier(path)
    assert result["unique"] == {7, 9}
    assert result["row_count"] == 2
    assert result["parser_mode"] == "tsv"


def test_read_vizier_preserves_duplicate_rows_tsv(tmp_path: Path):
    """Duplicate rows in VizieR TSV are preserved and counted."""
    path = tmp_path / "table4.tsv"
    path.write_text(
        "# VizieR export\nZTF\tID\nZTFJ000000.00+000000.0\t7\n"
        "ZTFJ000001.00+000000.0\t7\n"
        "ZTFJ000002.00+000000.0\t9\n",
        encoding="utf-8",
    )
    result = read_vizier(path)
    assert result["rows"] == [7, 7, 9]
    assert result["unique"] == {7, 9}
    assert result["row_count"] == 3
    assert result["unique_count"] == 2
    assert result["duplicate_ids"] == [7]
    assert result["duplicate_row_count"] == 1


def test_row_multiset_equality_when_identical(tmp_path: Path):
    """Two files with identical rows (including duplicates) pass exact match."""
    cand = tmp_path / "candidate.tsv"
    cand.write_text("SourceID\n1\n2\n2\n3\n", encoding="utf-8")
    pub = tmp_path / "published.tsv"
    pub.write_text(_vizier_tsv([1, 2, 2, 3]), encoding="utf-8")

    out = tmp_path / "report.json"
    result = _run_audit(cand, pub, out)
    assert result.returncode == 0, (
        f"expected exit 0, got {result.returncode}: {result.stderr}"
    )

    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["comparison"]["unique_membership_equal"] is True
    assert report["comparison"]["row_multiset_equal"] is True
    assert report["comparison"]["exact_match"] is True


def test_row_multiset_inequality_when_duplicates_differ(tmp_path: Path):
    """Same unique IDs but different duplicate counts fails exact match."""
    cand = tmp_path / "candidate.tsv"
    cand.write_text("SourceID\n1\n2\n3\n", encoding="utf-8")
    pub = tmp_path / "published.tsv"
    pub.write_text(_vizier_tsv([1, 2, 2, 3]), encoding="utf-8")

    out = tmp_path / "report.json"
    result = _run_audit(cand, pub, out)
    assert result.returncode == 2, f"expected exit 2, got {result.returncode}"

    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["comparison"]["unique_membership_equal"] is True
    assert report["comparison"]["row_multiset_equal"] is False
    assert report["comparison"]["exact_match"] is False


def test_row_multiset_inequality_when_unique_differ(tmp_path: Path):
    """Different unique IDs fails exact match regardless of duplicates."""
    cand = tmp_path / "candidate.tsv"
    cand.write_text("SourceID\n1\n2\n3\n", encoding="utf-8")
    pub = tmp_path / "published.tsv"
    pub.write_text(_vizier_tsv([1, 2, 4]), encoding="utf-8")

    out = tmp_path / "report.json"
    result = _run_audit(cand, pub, out)
    assert result.returncode == 2, f"expected exit 2, got {result.returncode}"

    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["comparison"]["unique_membership_equal"] is False
    assert report["comparison"]["exact_match"] is False


def test_report_contains_sha256_digests(tmp_path: Path):
    """Report includes SHA-256 digests for ordered rows and unique IDs."""
    cand = tmp_path / "candidate.tsv"
    cand.write_text("SourceID\n1\n2\n3\n", encoding="utf-8")
    pub = tmp_path / "published.tsv"
    pub.write_text(_vizier_tsv([1, 2, 3]), encoding="utf-8")

    out = tmp_path / "report.json"
    result = _run_audit(cand, pub, out)
    assert result.returncode == 0, f"expected exit 0, got {result.returncode}"

    report = json.loads(out.read_text(encoding="utf-8"))
    assert len(report["candidate"]["ordered_rows_sha256"]) == 64
    assert len(report["candidate"]["unique_ids_sha256"]) == 64
    assert len(report["published"]["ordered_rows_sha256"]) == 64
    assert len(report["published"]["unique_ids_sha256"]) == 64
    # Identical files → identical digests
    assert (
        report["candidate"]["ordered_rows_sha256"]
        == report["published"]["ordered_rows_sha256"]
    )
    assert (
        report["candidate"]["unique_ids_sha256"]
        == report["published"]["unique_ids_sha256"]
    )


# ---------------------------------------------------------------------------
# Exact row-multiset equality (follow-up review item 1)
#
# Regression: comparing row_count, unique-ID digest, duplicate-ID list and
# duplicate_row_count only is NOT a multiset comparison. The two sequences
# below agree on every one of those aggregates while being different
# multisets, so the previous implementation reported a false exact match.
# ---------------------------------------------------------------------------


_AMBIGUOUS_A = [1, 1, 2, 2, 2, 3]
_AMBIGUOUS_B = [1, 1, 1, 2, 2, 3]


def test_per_id_multiplicity_difference_fails_exact_match(tmp_path: Path):
    """[1,1,2,2,2,3] vs [1,1,1,2,2,3] must fail; only the per-ID counts differ."""
    cand = tmp_path / "candidate.tsv"
    cand.write_text(
        "SourceID\n" + "".join(f"{oid}\n" for oid in _AMBIGUOUS_A), encoding="utf-8"
    )
    pub = tmp_path / "published.tsv"
    pub.write_text(_vizier_tsv(_AMBIGUOUS_B), encoding="utf-8")

    out = tmp_path / "report.json"
    result = _run_audit(cand, pub, out)
    assert result.returncode == 2, (
        f"expected exit 2 for differing per-ID multiplicities, "
        f"got {result.returncode}: {result.stderr}"
    )

    report = json.loads(out.read_text(encoding="utf-8"))
    comparison = report["comparison"]

    # The unique ID set is identical, so unique-membership equality is True.
    assert comparison["unique_membership_equal"] is True
    # ... but the exact row multiset differs.
    assert comparison["row_multiset_equal"] is False
    assert comparison["row_multiset_digest_equal"] is False
    assert comparison["exact_match"] is False

    # Guard the regression itself: every aggregate used by the old (buggy)
    # check is equal, proving the old predicate would have said "equal".
    cand_block, pub_block = report["candidate"], report["published"]
    assert cand_block["row_count"] == pub_block["row_count"] == 6
    assert cand_block["unique_count"] == pub_block["unique_count"] == 3
    assert cand_block["unique_ids_sha256"] == pub_block["unique_ids_sha256"]
    assert cand_block["duplicate_ids"] == pub_block["duplicate_ids"] == [1, 2]
    assert cand_block["duplicate_row_count"] == pub_block["duplicate_row_count"] == 3

    # The distinguishing evidence is the per-ID multiplicity.
    assert cand_block["duplicate_id_counts"] == {"1": 2, "2": 3}
    assert pub_block["duplicate_id_counts"] == {"1": 3, "2": 2}
    assert cand_block["multiplicity_histogram"] == {"1": 1, "2": 1, "3": 1}
    assert pub_block["multiplicity_histogram"] == {"1": 1, "2": 1, "3": 1}
    assert cand_block["row_multiset_sha256"] != pub_block["row_multiset_sha256"]


def test_multiset_difference_sample_reports_both_directions(tmp_path: Path):
    """The report names which IDs have which multiplicity on each side."""
    cand = tmp_path / "candidate.tsv"
    cand.write_text(
        "SourceID\n" + "".join(f"{oid}\n" for oid in _AMBIGUOUS_A), encoding="utf-8"
    )
    pub = tmp_path / "published.tsv"
    pub.write_text(_vizier_tsv(_AMBIGUOUS_B), encoding="utf-8")

    out = tmp_path / "report.json"
    assert _run_audit(cand, pub, out).returncode == 2

    comparison = json.loads(out.read_text(encoding="utf-8"))["comparison"]
    assert comparison["multiplicity_difference_count"] == 2
    assert comparison["multiplicity_difference_sample"] == [
        {"id": 1, "candidate": 2, "published": 3},
        {"id": 2, "candidate": 3, "published": 2},
    ]


def test_canonical_multiset_digest_is_multiplicity_sensitive():
    """Digest of sorted (ID, count) pairs distinguishes multiplicity swaps."""
    from collections import Counter

    digest_a = _canonical_multiset_digest(Counter(_AMBIGUOUS_A))
    digest_b = _canonical_multiset_digest(Counter(_AMBIGUOUS_B))
    assert digest_a != digest_b
    assert len(digest_a) == 64


def test_canonical_multiset_digest_is_order_independent():
    """The canonical digest must not depend on row order."""
    from collections import Counter

    assert _canonical_multiset_digest(Counter([1, 2, 3])) == _canonical_multiset_digest(
        Counter([3, 2, 1])
    )


def test_row_order_difference_is_not_a_multiset_difference(tmp_path: Path):
    """Same IDs in a different order: multisets equal, ordered digests differ."""
    cand = tmp_path / "candidate.tsv"
    cand.write_text("SourceID\n1\n2\n3\n", encoding="utf-8")
    pub = tmp_path / "published.tsv"
    pub.write_text(_vizier_tsv([3, 2, 1]), encoding="utf-8")

    out = tmp_path / "report.json"
    result = _run_audit(cand, pub, out)
    assert result.returncode == 0, f"expected exit 0, got {result.returncode}"

    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["comparison"]["row_multiset_equal"] is True
    assert report["comparison"]["exact_match"] is True
    # Ordered digests stay separate evidence of the original row order.
    assert (
        report["candidate"]["ordered_rows_sha256"]
        != report["published"]["ordered_rows_sha256"]
    )
    assert (
        report["candidate"]["row_multiset_sha256"]
        == report["published"]["row_multiset_sha256"]
    )


# ---------------------------------------------------------------------------
# Fail-closed VizieR parsing (follow-up review item 2)
# ---------------------------------------------------------------------------


def test_read_vizier_rejects_invalid_utf8(tmp_path: Path):
    path = tmp_path / "bad_encoding.tsv"
    path.write_bytes(
        b"# VizieR export\nZTF\tID\nZTFJ000000.00+000000.0\t1\nZTFJ\xff\xfe\t2\n"
    )
    with pytest.raises(ValueError, match="invalid UTF-8"):
        read_vizier(path)


def test_read_vizier_rejects_non_numeric_tsv_id(tmp_path: Path):
    path = tmp_path / "nonnumeric.tsv"
    path.write_text(
        "# VizieR export\nZTF\tID\nZTFJ000000.00+000000.0\t1\nZTFJ000001.00+000000.0\tABC\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="non-numeric ID field"):
        read_vizier(path)


def test_read_vizier_rejects_unicode_digit_tsv_id(tmp_path: Path):
    """Non-ASCII digits are not valid IDs even though str.isdigit() accepts them."""
    path = tmp_path / "unicode_digit.tsv"
    path.write_text(
        "# VizieR export\nZTF\tID\nZTFJ000000.00+000000.0\t\u0663\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="non-numeric ID field"):
        read_vizier(path)


def test_read_vizier_rejects_empty_tsv_id(tmp_path: Path):
    path = tmp_path / "empty_id.tsv"
    path.write_text(
        "# VizieR export\nZTF\tID\nZTFJ000000.00+000000.0\t1\nZTFJ1\t\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="empty ID field"):
        read_vizier(path)


def test_read_vizier_rejects_truncated_tsv_row(tmp_path: Path):
    """A row missing the ID column is an error, not a silently skipped row."""
    path = tmp_path / "truncated.tsv"
    path.write_text(
        "# VizieR export\nZTF\tID\nZTFJ000000.00+000000.0\t1\nZTFJ000001.00+000000.0\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="ID column 1 is missing"):
        read_vizier(path)


def test_read_vizier_rejects_malformed_fixed_width_id(tmp_path: Path):
    path = tmp_path / "fw_bad_id.dat"
    path.write_text(
        _fixed_width("ZTFJ000000.00+000000.0", "1")
        + "\n"
        + _fixed_width("ZTFJ000001.00+000000.0", "ABCDEF")
        + "\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="non-numeric ID field 'ABCDEF'"):
        read_vizier(path)


def test_read_vizier_rejects_missing_fixed_width_id(tmp_path: Path):
    path = tmp_path / "fw_missing_id.dat"
    path.write_text(
        _fixed_width("ZTFJ000000.00+000000.0", "1")
        + "\n"
        + _fixed_width("ZTFJ000001.00+000000.0", "")
        + "\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="empty ID field"):
        read_vizier(path)


def test_read_vizier_rejects_truncated_fixed_width_record(tmp_path: Path):
    path = tmp_path / "fw_truncated.dat"
    path.write_text(
        _fixed_width("ZTFJ000000.00+000000.0", "1") + "\nZTFJ000001.\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="empty ID field"):
        read_vizier(path)


def test_read_vizier_accepts_preamble_metadata_but_not_data_rows(tmp_path: Path):
    """Header/units/separator lines are metadata; data rows must still parse."""
    path = tmp_path / "fw_preamble.dat"
    path.write_text(
        "# CDS table4.dat\n"
        "ZTF                     ID     Type\n"
        "---                     ---    ----\n"
        + _fixed_width("ZTFJ000000.00+000000.0", "1")
        + "\n"
        + _fixed_width("ZTFJ000001.00+000000.0", "3")
        + "\n",
        encoding="utf-8",
    )
    result = read_vizier(path)
    assert result["rows"] == [1, 3]
    assert result["parser_mode"] == "fixed-width"
    assert result["metadata_line_count"] == 3


def test_read_vizier_rejects_unknown_row_after_data_started(tmp_path: Path):
    """Once data has begun, an unparseable non-metadata line must fail closed."""
    path = tmp_path / "fw_garbage.dat"
    path.write_text(
        _fixed_width("ZTFJ000000.00+000000.0", "1") + "\nGARBAGE NOT A RECORD\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="empty ID field"):
        read_vizier(path)


# ---------------------------------------------------------------------------
# Fail-closed selected-file parsing
# ---------------------------------------------------------------------------


def test_read_selected_rejects_invalid_utf8(tmp_path: Path):
    path = tmp_path / "selected_bad_encoding.tsv"
    path.write_bytes(b"SourceID\n1\n\xff\n")
    with pytest.raises(ValueError, match="invalid UTF-8"):
        read_selected(path)


def test_read_selected_rejects_non_numeric_row(tmp_path: Path):
    path = tmp_path / "selected_bad_row.tsv"
    path.write_text("SourceID\n1\nnot-an-id\n", encoding="utf-8")
    with pytest.raises(ValueError, match="non-numeric ID field"):
        read_selected(path)


# ---------------------------------------------------------------------------
# CLI contract: parse failure exits 3 and writes no report (no partial audit)
# ---------------------------------------------------------------------------


def test_cli_parse_error_exits_3_and_writes_no_report(tmp_path: Path):
    cand = tmp_path / "candidate.tsv"
    cand.write_text("SourceID\n1\n2\n", encoding="utf-8")
    pub = tmp_path / "published.tsv"
    pub.write_text("# VizieR export\nZTF\tID\nZTFJ1\t1\nZTFJ2\tBAD\n", encoding="utf-8")

    out = tmp_path / "report.json"
    result = _run_audit(cand, pub, out)

    assert result.returncode == 3, (
        f"expected exit 3 on parse failure, got {result.returncode}"
    )
    assert "input error" in result.stderr
    assert "non-numeric ID field" in result.stderr
    # Fail closed: no report may be produced from a partially parsed table.
    assert not out.exists()
    # ... and no report content leaked onto stdout.
    assert "row_multiset_equal" not in result.stdout


def test_cli_exit_nonzero_when_unique_membership_alone_differs(tmp_path: Path):
    cand = tmp_path / "candidate.tsv"
    cand.write_text("SourceID\n1\n2\n3\n", encoding="utf-8")
    pub = tmp_path / "published.tsv"
    pub.write_text(_vizier_tsv([1, 2, 3, 4]), encoding="utf-8")

    out = tmp_path / "report.json"
    assert _run_audit(cand, pub, out).returncode == 2
    comparison = json.loads(out.read_text(encoding="utf-8"))["comparison"]
    assert comparison["unique_membership_equal"] is False
    assert comparison["row_multiset_equal"] is False
    assert comparison["exact_match"] is False


# ---------------------------------------------------------------------------
# Report evidence preservation (follow-up review item 3)
# ---------------------------------------------------------------------------


def test_report_preserves_source_hashes_and_parser_mode(tmp_path: Path):
    import hashlib

    cand = tmp_path / "candidate.tsv"
    cand.write_text("SourceID\n1\n2\n3\n", encoding="utf-8")
    pub = tmp_path / "published.tsv"
    pub.write_text(_vizier_tsv([1, 2, 3]), encoding="utf-8")

    out = tmp_path / "report.json"
    assert _run_audit(cand, pub, out).returncode == 0
    report = json.loads(out.read_text(encoding="utf-8"))

    assert (
        report["candidate"]["source_sha256"]
        == hashlib.sha256(cand.read_bytes()).hexdigest()
    )
    assert (
        report["published"]["source_sha256"]
        == hashlib.sha256(pub.read_bytes()).hexdigest()
    )
    assert report["candidate"]["parser_mode"] == "tsv"
    assert report["published"]["parser_mode"] == "tsv"
    assert report["candidate"]["row_count"] == 3
    assert report["published"]["row_count"] == 3
    assert report["candidate"]["metadata_line_count"] == 1
    assert report["published"]["metadata_line_count"] == 2


def test_report_preserves_full_per_id_multiplicities_when_requested(tmp_path: Path):
    cand = tmp_path / "candidate.tsv"
    cand.write_text(
        "SourceID\n" + "".join(f"{oid}\n" for oid in _AMBIGUOUS_A), encoding="utf-8"
    )
    pub = tmp_path / "published.tsv"
    pub.write_text(_vizier_tsv(_AMBIGUOUS_A), encoding="utf-8")

    out = tmp_path / "report.json"
    result = _run_audit(cand, pub, out, ["--include-full-multiplicities"])
    assert result.returncode == 0, result.stderr

    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["candidate"]["all_id_multiplicities_included"] is True
    assert report["candidate"]["all_id_multiplicities"] == {"1": 2, "2": 3, "3": 1}
    assert report["published"]["all_id_multiplicities"] == {"1": 2, "2": 3, "3": 1}
    # Digest, per-ID counts and histogram all agree.
    assert (
        report["candidate"]["row_multiset_sha256"]
        == report["published"]["row_multiset_sha256"]
    )


def test_report_omits_full_multiplicities_by_default(tmp_path: Path):
    """The default report stays compact but still carries the exact digest."""
    cand = tmp_path / "candidate.tsv"
    cand.write_text("SourceID\n1\n1\n2\n", encoding="utf-8")
    pub = tmp_path / "published.tsv"
    pub.write_text(_vizier_tsv([1, 1, 2]), encoding="utf-8")

    out = tmp_path / "report.json"
    assert _run_audit(cand, pub, out).returncode == 0
    report = json.loads(out.read_text(encoding="utf-8"))

    assert report["candidate"]["all_id_multiplicities_included"] is False
    assert "all_id_multiplicities" not in report["candidate"]
    assert report["candidate"]["duplicate_id_counts"] == {"1": 2}
    assert report["candidate"]["multiplicity_histogram"] == {"1": 1, "2": 1}
    assert len(report["candidate"]["row_multiset_sha256"]) == 64


def test_report_exposes_exact_membership_match_alias(tmp_path: Path):
    """The heavy workflow gates on a top-level alias that must agree exactly.

    ``scientific-validation.yml`` reads ``exact_membership_match`` from the
    report; it must be true only when unique membership AND the exact row
    multiset hold, and must never disagree with ``comparison.exact_match``.
    """
    cand = tmp_path / "candidate.tsv"
    pub = tmp_path / "published.tsv"
    out = tmp_path / "report.json"

    # Matching case.
    cand.write_text("SourceID\n1\n1\n2\n3\n", encoding="utf-8")
    pub.write_text(_vizier_tsv([1, 1, 2, 3]), encoding="utf-8")
    assert _run_audit(cand, pub, out).returncode == 0
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["exact_membership_match"] is True
    assert report["exact_membership_match"] == report["comparison"]["exact_match"]

    # Multiplicity-only mismatch must not be promoted to an exact match.
    pub.write_text(_vizier_tsv(_AMBIGUOUS_B), encoding="utf-8")
    cand.write_text(
        "SourceID\n" + "".join(f"{oid}\n" for oid in _AMBIGUOUS_A), encoding="utf-8"
    )
    assert _run_audit(cand, pub, out).returncode == 2
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["exact_membership_match"] is False
    assert report["exact_membership_match"] == report["comparison"]["exact_match"]
