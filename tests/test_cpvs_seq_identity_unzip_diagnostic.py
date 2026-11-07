"""Tests for the Info-ZIP based CPVS archive identity diagnostic."""

from __future__ import annotations

import hashlib
import shutil
import struct
import sys
import zipfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from diagnose_cpvs_seq_identity_unzip import scan_archive


@pytest.mark.skipif(shutil.which("unzip") is None, reason="Info-ZIP is required")
def test_unzip_reads_full_member_when_central_directory_crc_is_corrupt(
    tmp_path: Path,
) -> None:
    data = b"".join(
        f"615172,307.36563,-13.42128,{2450000 + i},14.886,0.05,0\n".encode()
        for i in range(132)
    )
    archive_path = tmp_path / "ztf2g.zip"
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("ztf2g", data)

    # Change only the central-directory CRC. The local header and payload remain intact.
    archive_bytes = bytearray(archive_path.read_bytes())
    central_directory = archive_bytes.index(b"PK\x01\x02")
    struct.pack_into("<I", archive_bytes, central_directory + 16, 0x12345678)
    archive_path.write_bytes(archive_bytes)

    archive_bytes = archive_path.read_bytes()
    report = scan_archive(
        archive_path,
        expected_archive_md5=hashlib.md5(archive_bytes).hexdigest(),
        expected_archive_sha256=hashlib.sha256(archive_bytes).hexdigest(),
        expected_data_sha256=hashlib.sha256(data).hexdigest(),
        expected_data_size=len(data),
        expected_total_rows=132,
        expected_ra_deg=307.36563,
        expected_dec_deg=-13.42128,
        expected_gmag=14.886,
        expected_ng=132,
    )

    assert report["scan"]["data_rows"] == 132
    assert report["target_seq_summary"]["row_count"] == 0
    assert report["orphan_seq_summary"]["row_count"] == 132
    assert report["comparison"]["orphan_median_coordinate_separation_arcsec"] == 0.0
    assert report["comparison"]["strong_coordinate_match_to_table2_target"] is True
    assert report["archive"]["zip_crc_verified"] is False
    assert report["extracted_member"]["integrity_verified"] is True
    assert report["validation_errors"] == []
    assert report["status"] == "COMPLETED_WITH_ZIP_CRC_MISMATCH"
