from __future__ import annotations

from scripts.audit_cpvs_residual_epochs import metrics, read_vizier


def test_metrics_applies_band_specific_snr_thresholds() -> None:
    g_row = {
        "SourceID": "123",
        "gmag": "17.2",
        "e_gmag": "0.4",
        "g_flag": "0",
    }
    r_row = {
        "SourceID": "123",
        "rmag": "16.8",
        "e_rmag": "0.3",
        "r_flag": "0",
    }

    assert metrics(g_row, "g") == (123, 17.2, 1.0857362047581296 / 0.4, True)
    assert metrics(r_row, "r") == (123, 16.8, 1.0857362047581296 / 0.3, True)


def test_metrics_rejects_zero_or_invalid_magnitude_and_error() -> None:
    assert metrics({"SourceID": "7", "gmag": "0", "e_gmag": "0.2"}, "g") == (
        7,
        0.0,
        None,
        False,
    )
    assert metrics({"SourceID": "8", "gmag": "17", "e_gmag": "0"}, "g") == (
        8,
        17.0,
        None,
        False,
    )
    assert metrics({"SourceID": "bad", "gmag": "17", "e_gmag": "0.2"}, "g") == (
        None,
        None,
        None,
        False,
    )


def test_read_vizier_maps_ztf_names_to_parent_sourceids(tmp_path) -> None:
    names = [
        "ZTFJ000000.00+000000.0",
        "ZTFJ000001.00+000000.0",
        "ZTFJ000002.00+000000.0",
    ]
    parent_catalog = {
        100 + i: {"catalog_object_name": name}
        for i, name in enumerate(names)
    }
    source = tmp_path / "table4.tsv"
    # The Table 4 internal IDs deliberately differ from parent SourceIDs.
    source.write_text(
        "# VizieR export\\n"
        "ZTF\\tID\\n"
        f"{names[0]}\\t777\\n"
        f"{names[2]}\\t999\\n",
        encoding="utf-8",
    )

    assert read_vizier(source, parent_catalog) == {100, 102}
