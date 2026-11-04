"""Tests for the targeted CPVS orphan-Seq identity diagnostic."""

from __future__ import annotations

import hashlib
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from diagnose_cpvs_seq_identity import scan_archive


def test_orphan_seq_coordinate_match_is_reported_as_identity_lead(
    tmp_path: Path,
) -> None:
    data = "".join(
        f"615172,307.36563,-13.42128,{2450000 + index},14.886,0.05,0\n"
        for index in range(132)
    ).encode("utf-8")
    archive_path = tmp_path / "ztf2g.zip"
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("ztf2g", data)

    report = scan_archive(
        archive_path,
        target_seq=615170,
        orphan_seq=615172,
        expected_archive_md5=hashlib.md5(archive_path.read_bytes()).hexdigest(),
        expected_archive_sha256=hashlib.sha256(archive_path.read_bytes()).hexdigest(),
        expected_data_sha256=hashlib.sha256(data).hexdigest(),
        expected_data_size=len(data),
        expected_ra_deg=307.36563,
        expected_dec_deg=-13.42128,
        expected_gmag=14.886,
        expected_ng=132,
    )

    assert report["target_seq_summary"]["row_count"] == 0
    assert report["orphan_seq_summary"]["row_count"] == 132
    assert report["comparison"]["orphan_median_coordinate_separation_arcsec"] == 0.0
    assert report["comparison"]["strong_coordinate_match_to_table2_target"] is True
    assert report["comparison"]["interpretation"] == "STRONG_IDENTITY_LEAD"
