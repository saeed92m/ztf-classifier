import pandas as pd

from ztf_classifier.io.alerce import alerce_to_internal_lc_robust


def _row(**overrides):
    row = {
        "mjd": 60000.0,
        "fid": 1,
        "magpsf_corr": 20.0,
        "sigmapsf_corr_ext": 0.1,
        "magpsf": 20.1,
        "sigmapsf": 0.2,
        "ra": 120.0,
        "dec": -20.0,
        "dubious": "false",
        "corrected": "true",
    }
    row.update(overrides)
    return row


def test_alerce_diagnostics_count_invalid_rows_and_fallbacks() -> None:
    detections = pd.DataFrame([
        _row(),
        _row(mjd=-1),
        _row(fid=9),
        _row(magpsf_corr=None, sigmapsf_corr_ext=None),
        _row(magpsf_corr=None, sigmapsf_corr_ext=None, magpsf=20.2, sigmapsf=0.2),
        _row(ra=400),
        _row(),
    ])
    output, diagnostics = alerce_to_internal_lc_robust(
        detections,
        return_diagnostics=True,
    )

    assert len(output) == 3
    assert diagnostics.rows_input == 7
    assert diagnostics.rows_output == 3
    assert diagnostics.invalid_mjd == 1
    assert diagnostics.invalid_fid == 1
    assert diagnostics.invalid_coordinates == 1
    assert diagnostics.raw_fallback_count == 2
    assert diagnostics.corrected_photometry_count == 5
    assert diagnostics.rows_dropped == 4


def test_alerce_diagnostics_remove_exact_duplicates() -> None:
    detections = pd.DataFrame([_row(), _row()])
    output, diagnostics = alerce_to_internal_lc_robust(
        detections,
        return_diagnostics=True,
    )
    assert len(output) == 1
    assert diagnostics.duplicate_rows == 1
