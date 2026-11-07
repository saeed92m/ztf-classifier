from __future__ import annotations

from ztf_classifier.validation.dr24_quality import (
    CATFLAGS_BIT_15,
    QC_POLICY_ID,
    assess_dr24_epochs,
)


def test_dr24_qc_assessment_preserves_raw_epochs_and_separates_flag_policies() -> None:
    raw = [
        {"hmjd": 60000.1, "mag": 18.2, "magerr": 0.03, "clrcoeff": 0.1, "catflags": 0},
        {"hmjd": 60000.2, "mag": 18.3, "magerr": 0.04, "clrcoeff": 0.1, "catflags": 1},
        {"hmjd": 60000.3, "mag": 18.4, "magerr": 0.05, "clrcoeff": 0.1, "catflags": CATFLAGS_BIT_15},
    ]
    before = [dict(epoch) for epoch in raw]

    result = assess_dr24_epochs(raw)

    assert raw == before
    assert result["policy_id"] == QC_POLICY_ID
    assert result["policy_status"] == "DIAGNOSTIC_NOT_PRODUCTION_APPROVED"
    assert result["raw_data_mutated"] is False
    assert result["counts"] == {
        "total_epochs": 3,
        "likely_usable_epochs": 2,
        "strict_clean_epochs": 1,
        "photometry_valid_epochs": 3,
        "provisional_analysis_candidates": 2,
        "bit_15_flagged_epochs": 1,
        "invalid_catflags_epochs": 0,
        "invalid_photometry_epochs": 0,
    }
    assert result["epochs"][0]["strict_clean"] is True
    assert result["epochs"][1]["catalog_likely_usable"] is True
    assert result["epochs"][1]["strict_clean"] is False
    assert result["epochs"][2]["bit_15_flagged"] is True
    assert result["epochs"][2]["provisional_analysis_candidate"] is False


def test_dr24_qc_assessment_flags_invalid_photometry_and_catflags() -> None:
    result = assess_dr24_epochs(
        [
            {"hmjd": 60000.1, "mag": 18.2, "magerr": -0.1, "catflags": 0},
            {"hmjd": float("nan"), "mag": None, "magerr": 0.1, "catflags": None},
            {"hmjd": 60000.2, "mag": 18.3, "magerr": 0.1, "catflags": -1},
        ]
    )

    assert result["counts"]["invalid_photometry_epochs"] == 2
    assert result["counts"]["invalid_catflags_epochs"] == 2
    assert "negative_magerr" in result["epochs"][0]["reasons"]
    assert "invalid_hmjd" in result["epochs"][1]["reasons"]
    assert "missing_or_invalid_catflags" in result["epochs"][1]["reasons"]
    assert result["epochs"][2]["catalog_likely_usable"] is False


def test_dr24_qc_assessment_does_not_require_color_coefficient() -> None:
    result = assess_dr24_epochs(
        [{"hmjd": 60000.1, "mag": 18.2, "magerr": 0.03, "clrcoeff": None, "catflags": 0}]
    )
    assert result["counts"]["provisional_analysis_candidates"] == 1
