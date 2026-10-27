from pathlib import Path

from scripts.audit_cpvs_nonfinite_snr import trace


def test_trace_separates_nonfinite_only_ids_from_finite_qualifiers(tmp_path: Path) -> None:
    lightcurve = tmp_path / "g.tsv"
    lightcurve.write_text(
        "SourceID\te_gmag\tgmag\n"
        "1\t0.1\t15.0\n"
        "2\tnan\t15.0\n"
        "3\t0.6\t15.0\n"
        "4\t0.1\t0.0\n",
        encoding="utf-8",
    )

    result = trace(
        lightcurve,
        parent_ids={"1", "2", "3", "4"},
        sigma=2.5,
        band="g",
        member=None,
    )

    assert result["legacy_ids"] == {"1", "2", "4"}
    assert result["finite_ids"] == {"1", "4"}
    assert result["nonfinite_ids"] == {"2"}
    assert result["nonfinite_only_ids"] == {"2"}
    assert result["invalid_magnitude_ids"] == {"4"}
    assert result["nonfinite_snr_rows"] == 1
    assert result["finite_qualifying_rows"] == 2
