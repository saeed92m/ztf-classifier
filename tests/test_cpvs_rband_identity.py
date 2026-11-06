"""Tests for the targeted CPVS r-band identity and Seq-count reconciliation."""

from __future__ import annotations

import hashlib
import importlib
import shutil
import sys
import zipfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
scan_archive = importlib.import_module("diagnose_cpvs_rband_identity").scan_archive


def _table2_record(seq: int, ra: float, dec: float, rmag: float, nr: int) -> str:
    fields = [" "] * 228
    fields[0:22] = list("ZTFJ" + str(seq).rjust(18))
    fields[23:29] = list(f"{seq:6d}")
    fields[30:39] = list(f"{ra:9.5f}")
    fields[40:49] = list(f"{dec:9.5f}")
    fields[96:102] = list(f"{rmag:6.3f}")
    fields[136:140] = list(f"{nr:4d}")
    return "".join(fields) + "\n"


@pytest.mark.skipif(shutil.which("unzip") is None, reason="Info-ZIP is required")
def test_rband_scan_reconciles_seq_counts_and_cross_band_identity(
    tmp_path: Path,
) -> None:
    rows = [
        f"615172,307.3656702,-13.4214213,{58250 + index},14.7357,0.04,0\n"
        for index in range(113)
    ]
    rows.append("999999,307.36570,-13.42140,58600,15.1,0.08,0\n")
    data = "".join(rows).encode("utf-8")
    archive_path = tmp_path / "ztf2r.zip"
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("ztf2r", data)

    table2_path = tmp_path / "table2.dat"
    table2_path.write_text(
        _table2_record(615170, 307.36563, -13.42128, 14.736, 113)
        + _table2_record(615171, 10.0, 10.0, 15.0, 1),
        encoding="ascii",
    )
    readme_path = tmp_path / "ReadMe"
    readme_path.write_text("ztf2r.dat       75   114    r band data\n", encoding="ascii")
    mismatch_path = tmp_path / "mismatches.tsv"

    archive_bytes = archive_path.read_bytes()
    report = scan_archive(
        archive_path,
        table2_path=table2_path,
        readme_path=readme_path,
        mismatch_output=mismatch_path,
        expected_archive_md5=hashlib.md5(archive_bytes).hexdigest(),
        expected_archive_sha256=hashlib.sha256(archive_bytes).hexdigest(),
        expected_data_sha256=hashlib.sha256(data).hexdigest(),
        expected_data_size=len(data),
        expected_total_rows=114,
        expected_table2_sha256=hashlib.sha256(table2_path.read_bytes()).hexdigest(),
        expected_table2_size=table2_path.stat().st_size,
        expected_table2_records=2,
        expected_readme_sha256=hashlib.sha256(readme_path.read_bytes()).hexdigest(),
        expected_readme_size=readme_path.stat().st_size,
    )

    assert report["validation_errors"] == []
    assert report["status"] == "DISCOVERY_COMPLETE_WITH_SOURCE_DISCREPANCIES"
    assert report["scan"]["data_rows"] == 114
    assert report["target_seq_summary"]["row_count"] == 0
    assert report["orphan_seq_summary"]["row_count"] == 113
    assert report["orphan_seq_summary"]["median_coordinate_separation_arcsec"] < 1.0
    assert report["cross_band_identity_diagnostic"]["interpretation"] == (
        "STRONG_CROSS_BAND_IDENTITY_LEAD"
    )
    reconciliation = report["source_count_reconciliation"]
    assert reconciliation["table2_sum_nr"] == 114
    assert reconciliation["archive_total_rows"] == 114
    assert reconciliation["mismatched_seq_count"] == 2
    assert reconciliation["archive_only_seq_count"] == 2
    assert reconciliation["archive_only_rows"] == 114
    assert "615172" in mismatch_path.read_text(encoding="utf-8")


@pytest.mark.skipif(shutil.which("unzip") is None, reason="Info-ZIP is required")
def test_rband_scan_fails_closed_on_archive_md5_mismatch(tmp_path: Path) -> None:
    data = b"615172,307.3656702,-13.4214213,58250,14.7357,0.04,0\n"
    archive_path = tmp_path / "ztf2r.zip"
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("ztf2r", data)
    table2_path = tmp_path / "table2.dat"
    table2_path.write_text(
        _table2_record(615170, 307.36563, -13.42128, 14.736, 113),
        encoding="ascii",
    )
    readme_path = tmp_path / "ReadMe"
    readme_path.write_text("ztf2r.dat 75 113\n", encoding="ascii")

    report = scan_archive(
        archive_path,
        table2_path=table2_path,
        readme_path=readme_path,
        mismatch_output=tmp_path / "mismatches.tsv",
        expected_archive_md5="00000000000000000000000000000000",
        expected_archive_sha256=None,
        expected_data_sha256=None,
        expected_data_size=None,
        expected_total_rows=None,
        expected_table2_sha256=None,
        expected_table2_size=None,
        expected_table2_records=None,
        expected_readme_sha256=None,
        expected_readme_size=None,
    )
    assert report["status"] == "FAILED_VALIDATION"
    assert any("MD5 mismatch" in error for error in report["validation_errors"])
