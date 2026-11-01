from __future__ import annotations

import importlib.util
import pathlib
import sys

SCRIPT = (
    pathlib.Path(__file__).resolve().parents[1]
    / "scripts"
    / "cpvs_55_control_photometry.py"
)
SPEC = importlib.util.spec_from_file_location("cpvs_55_control_photometry", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
AUDIT = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = AUDIT
SPEC.loader.exec_module(AUDIT)


def test_parse_vizier_tsv_skips_metadata_and_keeps_expected_source() -> None:
    payload = (
        b"# VizieR output\n"
        b"Seq\tRAdeg\tDEdeg\tMJD\tmag\te_mag\tflag\n"
        b"---\t------\t------\t---\t---\t-----\t----\n"
        b"1352\t0.66552\t44.04453\t58653.4\t19.84\t0.12\t0\n"
        b"1352\t0.66552\t44.04453\t58654.4\t20.01\t0.50\t16\n"
        b"9777\t0.10181\t64.36214\t58655.4\t18.40\t0.10\t0\n"
    )
    rows = AUDIT.parse_vizier_tsv(payload, "1352")
    assert len(rows) == 2
    assert {row["Seq"] for row in rows} == {"1352"}
    assert rows[0]["flag"] == "0"


def test_parse_vizier_tsv_rejects_missing_schema() -> None:
    try:
        AUDIT.parse_vizier_tsv(b"# empty response\nNo data found\n", "1352")
    except ValueError as exc:
        assert "no Seq/MJD/mag/e_mag/flag header" in str(exc)
    else:
        raise AssertionError("Expected invalid VizieR response to fail")


def test_band_metrics_applies_per_band_snr_threshold() -> None:
    rows = [
        {"mag": "18.0", "e_mag": "0.20", "flag": "0"},
        {"mag": "19.0", "e_mag": "0.60", "flag": "16"},
        {"mag": "0", "e_mag": "0.10", "flag": "0"},
        {"mag": "18.0", "e_mag": "nan", "flag": "0"},
    ]
    g = AUDIT.band_metrics(rows, 2.5)
    r = AUDIT.band_metrics(rows, 3.0)
    assert g["row_count"] == 4
    assert g["valid_photometry_rows"] == 2
    assert g["qualifying_detections_approximate"] == 1
    assert g["passes_approximate_snr"] is True
    assert r["qualifying_detections_approximate"] == 1
    assert r["passes_approximate_snr"] is True


def test_band_metrics_returns_false_when_no_detection_passes() -> None:
    rows = [{"mag": "19.0", "e_mag": "0.80", "flag": "0"}]
    result = AUDIT.band_metrics(rows, 3.0)
    assert result["valid_photometry_rows"] == 1
    assert result["qualifying_detections_approximate"] == 0
    assert result["passes_approximate_snr"] is False
