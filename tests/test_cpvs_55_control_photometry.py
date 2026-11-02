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


def test_finite_float_rejects_nonfinite_and_invalid_values() -> None:
    assert AUDIT.finite_float("1.25") == 1.25
    assert AUDIT.finite_float("nan") is None
    assert AUDIT.finite_float("inf") is None
    assert AUDIT.finite_float("") is None


def test_summarize_band_filters_target_ids_and_applies_threshold(tmp_path: pathlib.Path) -> None:
    source = tmp_path / "g.tsv"
    source.write_text(
        "SourceID\\tgmag\\te_gmag\\tg_flag\\n"
        "101\\t18.0\\t0.20\\t0\\n"
        "101\\t19.0\\t0.60\\t16\\n"
        "101\\t0\\t0.10\\t0\\n"
        "202\\t18.0\\t0.10\\t0\\n",
        encoding="utf-8",
    )
    result = AUDIT.summarize_band(
        source, {"101"}, "e_gmag", "gmag", ("g_flag", "catflags", "flag"), 2.5
    )
    assert result["101"]["row_count"] == 3
    assert result["101"]["valid_photometry_rows"] == 2
    assert result["101"]["qualifying_detections_approximate"] == 1
    assert result["101"]["passes_approximate_snr"] is True
    assert result["101"]["qualifying_flag_counts"] == {"0": 1}


def test_summarize_band_fails_when_no_detection_passes(tmp_path: pathlib.Path) -> None:
    source = tmp_path / "r.tsv"
    source.write_text(
        "SourceID\\trmag\\te_rmag\\tr_flag\\n"
        "101\\t19.0\\t0.80\\t0\\n",
        encoding="utf-8",
    )
    result = AUDIT.summarize_band(
        source, {"101"}, "e_rmag", "rmag", ("r_flag", "catflags", "flag"), 3.0
    )
    assert result["101"]["row_count"] == 1
    assert result["101"]["qualifying_detections_approximate"] == 0
    assert result["101"]["passes_approximate_snr"] is False
