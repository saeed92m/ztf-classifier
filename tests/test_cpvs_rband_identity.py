"""Tests for the targeted CPVS r-band identity discovery scan."""

from __future__ import annotations

import hashlib
import shutil
import sys
import zipfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from diagnose_cpvs_rband_identity import scan_archive


@pytest.mark.skipif(shutil.which("unzip") is None, reason="Info-ZIP is required")
def test_rband_scan_reports_target_orphan_and_spatial_candidates(
    tmp_path: Path,
) -> None:
    rows = [
        f"615172,307.3656934,-13.4214107,{2450000 + index},14.2,0.04,0\n"
        for index in range(113)
    ]
    rows.append("999999,307.36570,-13.42140,2450100,15.1,0.08,0\n")
    data = "".join(rows).encode("utf-8")
    archive_path = tmp_path / "ztf2r.zip"
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("ztf2r", data)

    report = scan_archive(
        archive_path,
        expected_archive_md5=hashlib.md5(archive_path.read_bytes()).hexdigest(),
        expected_data_sha256=hashlib.sha256(data).hexdigest(),
        expected_data_size=len(data),
        expected_total_rows=114,
    )

    assert report["status"] == "DISCOVERY_COMPLETE"
    assert report["validation_errors"] == []
    assert report["scan"]["data_rows"] == 114
    assert report["target_seq_summary"]["row_count"] == 0
    assert report["orphan_seq_summary"]["row_count"] == 113
    assert report["comparison"]["orphan_seq_rows_match_table2_nr"] is True
    assert report["comparison"]["orphan_seq_matches_table2_nr_and_within_one_arcsec"] is True
    assert report["comparison"]["interpretation"] == "STRONG_R_BAND_IDENTITY_LEAD"
    assert {item["source_id"] for item in report["comparison"]["nearby_source_ids"]} == {
        615172,
        999999,
    }
    assert report["extracted_member"]["pinned_integrity_verified"] is True


@pytest.mark.skipif(shutil.which("unzip") is None, reason="Info-ZIP is required")
def test_rband_scan_fails_closed_on_archive_md5_mismatch(tmp_path: Path) -> None:
    data = b"615172,307.3656934,-13.4214107,2450000,14.2,0.04,0\n"
    archive_path = tmp_path / "ztf2r.zip"
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("ztf2r", data)

    report = scan_archive(archive_path, expected_archive_md5="00000000000000000000000000000000")
    assert report["status"] == "FAILED_VALIDATION"
    assert any("MD5 mismatch" in error for error in report["validation_errors"])
