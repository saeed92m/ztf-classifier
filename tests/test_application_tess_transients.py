from __future__ import annotations

import pytest

from ztf_classifier.application.errors import ApplicationInputError
from ztf_classifier.application.tess_transients import load_tess_transient

HEADER = """# reference_flux: 123.45
# BTJD TJD cts_per_s e_cts_per_s mag e_mag bkg bkg_model bkg2 e_bkg2
"""
ROWS = """1000.0 999.9 12.0 1.0 14.2 0.1 2.0 0.1 0.2 0.03
1000.5 1000.4 -1.0 0.5 19.0 99.9 3.0 0.2 0.3 0.04
"""


def test_load_tess_transients_flux_preserves_rows_and_upper_limit_flag(tmp_path):
    path = tmp_path / "lc_2022sfe_cleaned"
    path.write_text(HEADER + ROWS, encoding="utf-8")
    result = load_tess_transient(path, object_id="2022sfe", measurement="flux")
    assert len(result.observations) == 2
    assert result.observations["object_id"].tolist() == ["2022sfe", "2022sfe"]
    assert result.observations["time_value"].tolist() == [1000.0, 1000.5]
    assert result.observations["value"].tolist() == [12.0, -1.0]
    assert result.observations["measurement_type"].tolist() == ["flux", "flux"]
    assert result.observations["quality_flag"].tolist() == [
        "not_marked_as_upper_limit", "magnitude_upper_limit_3sigma",
    ]
    assert result.diagnostics["reference_flux_counts_per_second"] == 123.45
    assert result.diagnostics["source_rows_read"] == 2
    assert result.diagnostics["background_correction_performed"] is False


def test_load_tess_transients_magnitude_keeps_99_9_sentinel(tmp_path):
    path = tmp_path / "lightcurve.txt"
    path.write_text(HEADER + ROWS, encoding="utf-8")
    result = load_tess_transient(path, object_id="SN-test", measurement="magnitude")
    assert result.observations["value"].tolist() == [14.2, 19.0]
    assert result.observations["uncertainty"].tolist() == [0.1, 99.9]
    assert result.diagnostics["magnitude_upper_limit_rows"] == 1


@pytest.mark.parametrize(
    ("content", "message"),
    [
        ("# reference_flux: 1.0\n# wrong columns\n1 2 3\n", "Unexpected TESS Transients columns"),
        ("# no reference flux\n# BTJD TJD cts_per_s e_cts_per_s mag e_mag bkg bkg_model bkg2 e_bkg2\n1 2 3\n", "reference_flux"),
    ],
)
def test_load_tess_transients_rejects_unrecognized_source_schema(tmp_path, content, message):
    path = tmp_path / "bad.txt"
    path.write_text(content, encoding="utf-8")
    with pytest.raises(ApplicationInputError, match=message):
        load_tess_transient(path, object_id="test")


def test_load_tess_transients_requires_explicit_object_id_and_measurement(tmp_path):
    path = tmp_path / "lightcurve.txt"
    path.write_text(HEADER + ROWS, encoding="utf-8")
    with pytest.raises(ApplicationInputError, match="object_id"):
        load_tess_transient(path, object_id=" ")
    with pytest.raises(ApplicationInputError, match="measurement"):
        load_tess_transient(path, object_id="test", measurement="both")
