from pathlib import Path

from ztf_classifier.validation.derivation import _qualified_ids


def test_qualified_ids_reject_nonfinite_snr(tmp_path: Path) -> None:
    lightcurve = tmp_path / "g.tsv"
    lightcurve.write_text(
        "SourceID\te_gmag\tgmag\tg_flag\n"
        "1\t0.1\t15.0\t0\n"
        "2\tnan\t15.0\t0\n"
        "3\t0.6\t15.0\t0\n"
        "4\t0.1\t0.0\t0\n",
        encoding="utf-8",
    )

    selected, valid_magnitude = _qualified_ids(
        lightcurve,
        sigma=2.5,
        parent_ids={"1", "2", "3", "4"},
        member=None,
        error_columns=("e_gmag",),
        flag_columns=("g_flag",),
    )

    assert selected == {"1", "4"}
    assert valid_magnitude == {"1"}
