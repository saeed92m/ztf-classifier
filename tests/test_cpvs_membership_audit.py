"""Tests for CPVS membership audit with row-level duplicate evidence (issue #184)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from scripts.audit_cpvs_membership import read_selected, read_vizier

_ENV = dict(os.environ)
_ENV["PYTHONPATH"] = "src:." + os.pathsep + _ENV.get("PYTHONPATH", "")


def _vizier_tsv(lines: list[str]) -> str:
    """Build a VizieR TSV export content with header ZTF\tID."""
    header = "# VizieR export\nZTF\tID\n"
    rows = "".join(f"ZTFJ{oid:010d}.00+000000.0\t{oid}\n" for oid in lines)
    return header + rows


def _run_audit(cand: Path, pub: Path, out: Path) -> subprocess.CompletedProcess:
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
