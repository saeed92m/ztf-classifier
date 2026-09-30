from pathlib import Path

from ztf_classifier.validation.derivation import _qualified_ids


def test_qualified_ids_uses_detection_snr_and_finite_magnitudes_only(tmp_path: Path):
    path = tmp_path / "g.tsv"
    path.write_text(
        "SourceID\tgmag\te_gmag\tg_flag\n"
        "1\t18.0\t0.1\t0\n"
        "2\t18.0\t0.1\t1\n"
        "3\t0.0\t0.1\t0\n"
        "4\t18.0\t0.5\t0\n",
        encoding="utf-8",
    )

    selected, quality = _qualified_ids(
        path,
        sigma=2.5,
        parent_ids={"1", "2", "3", "4"},
        member=None,
        error_columns=("e_gmag",),
        flag_columns=("g_flag", "catflags", "flag"),
    )

    assert selected == {"1", "2", "3"}
    assert quality == {"1"}


def test_qualified_ids_empty_input_returns_two_sets(tmp_path: Path):
    path = tmp_path / "empty.tsv"
    path.write_text("", encoding="utf-8")

    selected, quality = _qualified_ids(
        path,
        sigma=2.5,
        parent_ids=set(),
        member=None,
        error_columns=("e_gmag",),
        flag_columns=("g_flag", "catflags", "flag"),
    )

    assert selected == set()
    assert quality == set()
