"""Synthetic regression tests for the CPVS raw SNR sample audit."""

from __future__ import annotations

import csv
import hashlib
import importlib
import shutil
import zipfile
import zlib
from pathlib import Path

import pytest

audit = importlib.import_module("diagnose_cpvs_membership_snr_sample")


def _archive(
    path: Path,
    member: str,
    data: bytes,
    band: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(member, data)
    monkeypatch.setitem(audit.ARCHIVES, band, {
        "member": member,
        "md5": hashlib.md5(path.read_bytes()).hexdigest(),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "member_sha256": hashlib.sha256(data).hexdigest(),
        "member_size": len(data),
        "member_rows": len(data.splitlines()),
        "member_crc32": f"{zlib.crc32(data) & 0xFFFFFFFF:08x}",
        "threshold": 2.5 if band == "g" else 3.0,
    })


def _write_tsv(path: Path, rows: list[dict[str, str]]) -> None:
    fields = list(rows[0])
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


@pytest.mark.skipif(shutil.which("unzip") is None, reason="Info-ZIP is required")
def test_raw_snr_sample_rederivation_and_four_field_gate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    g_data = (
        b"1,10,10,59000,15.0,0.30,0\n"
        b"2,11,11,59001,16.0,0.30,0\n"
        b"3,12,12,59002,17.0,0.60,0\n"
    )
    r_data = (
        b"1,10,10,59000,14.0,0.30,0\n"
        b"2,11,11,59001,15.0,0.50,4096\n"
        b"3,12,12,59002,16.0,0.30,0\n"
    )
    g_archive = tmp_path / "ztf2g.zip"
    r_archive = tmp_path / "ztf2r.zip"
    _archive(g_archive, "ztf2g", g_data, "g", monkeypatch)
    _archive(r_archive, "ztf2r", r_data, "r", monkeypatch)

    candidate_only = tmp_path / "candidate_only.tsv"
    _write_tsv(
        candidate_only,
        [
            {
                "SourceID": "2",
                "ZTF": "ZTF_TEST_2",
                "gmag": "16.0",
                "rmag": "15.0",
                "Per": "1.0",
                "Per-g": "1.0",
                "Per-r": "nan",
                "Ng": "1",
                "Nr": "1",
                "candidate": "True",
                "Table4_member": "False",
                "four_field_positive": "False",
                "g_snr": "True",
                "r_snr": "True",
                "g_qualifying_detections": "1",
                "r_qualifying_detections": "1",
            }
        ],
    )
    sample_100 = tmp_path / "sample_100.tsv"
    _write_tsv(
        sample_100,
        [
            {
                "SourceID": "1",
                "ZTF": "ZTF_TEST_1",
                "stratum": "published_member",
                "gmag": "15.0",
                "rmag": "14.0",
                "Per-g": "1.0",
                "Per-r": "1.0",
                "Ng": "1",
                "Nr": "1",
                "candidate": "True",
                "Table4_member": "True",
                "four_field_positive": "True",
            }
        ],
    )
    sample_1000 = tmp_path / "sample_1000.tsv"
    _write_tsv(
        sample_1000,
        [
            {
                "SourceID": "1",
                "ZTF": "ZTF_TEST_1",
                "stratum": "published_member",
                "gmag": "15.0",
                "rmag": "14.0",
                "Per-g": "1.0",
                "Per-r": "1.0",
                "Ng": "1",
                "Nr": "1",
                "candidate": "True",
                "Table4_member": "True",
                "four_field_positive": "True",
            },
            {
                "SourceID": "2",
                "ZTF": "ZTF_TEST_2",
                "stratum": "candidate_only",
                "gmag": "16.0",
                "rmag": "15.0",
                "Per-g": "1.0",
                "Per-r": "nan",
                "Ng": "1",
                "Nr": "1",
                "candidate": "True",
                "Table4_member": "False",
                "four_field_positive": "False",
            },
            {
                "SourceID": "3",
                "ZTF": "ZTF_TEST_3",
                "stratum": "parent_neither",
                "gmag": "0",
                "rmag": "16.0",
                "Per-g": "1.0",
                "Per-r": "1.0",
                "Ng": "1",
                "Nr": "1",
                "candidate": "False",
                "Table4_member": "False",
                "four_field_positive": "False",
            },
        ],
    )

    four_field_only = tmp_path / "four_field_only.tsv"
    _write_tsv(
        four_field_only,
        [
            {
                "SourceID": "4",
                "ZTF": "ZTF_TEST_4",
                "gmag": "15.5",
                "rmag": "14.5",
                "Per-g": "1.2",
                "Per-r": "1.3",
                "Per": "1.2",
                "Ng": "1",
                "Nr": "1",
                "candidate": "False",
                "Table4_member": "False",
                "four_field_positive": "True",
            }
        ],
    )

    metadata, input_report = audit.load_metadata(
        candidate_only, sample_100, sample_1000, four_field_only
    )
    assert input_report["metadata_conflicts"] == []
    source_ids = set(metadata)
    assert source_ids == {1, 2, 3, 4}
    assert metadata[4]["four_field_only"] is True
    assert audit.parse_photometry_line(
        b'4,10,10,59000,15.5,0.2,"flag,with,commas"\n'
    )[-1] == "flag,with,commas"

    g_report, g_metrics = audit.scan_band_archive(g_archive, "g", source_ids)
    r_report, r_metrics = audit.scan_band_archive(r_archive, "r", source_ids)
    assert g_report["validation_errors"] == []
    assert r_report["validation_errors"] == []

    objects = audit.build_object_rows(metadata, g_metrics, r_metrics)
    by_id = {row["source_id"]: row for row in objects}
    assert by_id[1]["rederived_candidate"] is True
    assert by_id[2]["rederived_candidate"] is False
    assert by_id[3]["rederived_candidate"] is False
    assert by_id[4]["rederived_candidate"] is None
    assert by_id[4]["g"]["passes_approximate_snr"] is None
    assert by_id[4]["r"]["passes_approximate_snr"] is None
    assert by_id[4]["matches_historical_candidate"] is None
    assert by_id[4]["matches_table4_with_four_field_gate"] is None
    assert by_id[2]["matches_historical_candidate"] is False
    assert by_id[1]["matches_table4_with_four_field_gate"] is True
    assert by_id[2]["matches_table4_with_four_field_gate"] is True
    assert by_id[3]["matches_table4_with_four_field_gate"] is True
    assert by_id[2]["r"]["qualifying_detections_approximate"] == 0
    assert by_id[2]["r"]["qualifying_flag_counts"] == {}
    assert by_id[2]["r"]["all_flag_counts"] == {"4096": 1}

    summary = audit.summarize_group(objects)
    assert summary["both_snr_pass"] == 1
    assert summary["both_snr_unknown"] == 1
    assert summary["both_snr_and_four_field"] == 1
    assert summary["both_snr_and_four_field_unknown"] == 1
    assert summary["g_snr_unknown"] == 1
    assert summary["r_snr_unknown"] == 1
    assert summary["table4_members"] == 1


def test_two_band_candidate_membership_is_reported_for_each_snr_formula() -> None:
    metadata = {
        10: {
            "source_id": 10,
            "strata": {"candidate_only"},
            "four_field_positive": True,
            "candidate": True,
            "table4_member": True,
            "table2_ng": 2,
            "table2_nr": 2,
        }
    }
    g_metrics = {
        10: {
            "raw_row_count": 2,
            "passes_approximate_snr": True,
            "passes_exact_snr": False,
            "passes_inverse_error_snr": True,
        }
    }
    r_metrics = {
        10: {
            "raw_row_count": 2,
            "passes_approximate_snr": True,
            "passes_exact_snr": True,
            "passes_inverse_error_snr": False,
        }
    }

    rows = audit.build_object_rows(metadata, g_metrics, r_metrics)
    row = rows[0]
    assert row["rederived_candidate_approximate"] is True
    assert row["rederived_candidate_exact"] is False
    assert row["rederived_candidate_inverse_error"] is False

    summary = audit.summarize_group(rows)
    formulas = summary["snr_formulae"]
    assert formulas["approximate"]["both_snr_pass"] == 1
    assert formulas["exact"]["both_snr_fail"] == 1
    assert formulas["inverse_error"]["both_snr_fail"] == 1
    assert formulas["approximate"]["candidate_rederived_vs_table4"]["true_positive"] == 1
    assert formulas["exact"]["candidate_rederived_vs_table4"]["false_negative"] == 1
    assert formulas["inverse_error"]["candidate_rederived_vs_table4"]["false_negative"] == 1


def test_load_metadata_reports_within_file_duplicates_and_cross_file_overlaps(
    tmp_path: Path,
) -> None:
    base = {
        "SourceID": "10",
        "ZTF": "ZTF_TEST_10",
        "gmag": "15.0",
        "rmag": "14.0",
        "Per-g": "1.0",
        "Per-r": "1.0",
        "Per": "1.0",
        "Ng": "2",
        "Nr": "2",
        "candidate": "True",
        "Table4_member": "True",
        "four_field_positive": "True",
    }
    candidate_only = tmp_path / "candidate_only.tsv"
    _write_tsv(candidate_only, [base, dict(base)])
    sample_100 = tmp_path / "sample_100.tsv"
    _write_tsv(sample_100, [{**base, "stratum": "reference_candidate"}])
    sample_1000 = tmp_path / "sample_1000.tsv"
    _write_tsv(sample_1000, [{**base, "stratum": "reference_candidate"}])
    four_field_only = tmp_path / "four_field_only.tsv"
    _write_tsv(
        four_field_only,
        [{**base, "SourceID": "20", "ZTF": "ZTF_TEST_20"}],
    )

    _, report = audit.load_metadata(
        candidate_only, sample_100, sample_1000, four_field_only
    )
    assert report["within_file_duplicate_rows"]["candidate_only"] == 1
    assert report["within_file_duplicate_source_ids"]["candidate_only"]["examples"] == [10]
    assert report["cross_file_overlaps"]["candidate_only__sample_100"]["count"] == 1
    assert report["cross_file_overlaps"]["candidate_only__sample_1000"]["count"] == 1
    assert report["cross_file_overlaps"]["sample_100__sample_1000"]["count"] == 1
