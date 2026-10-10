from pathlib import Path

from ztf_classifier.validation.derivation import _qualified_ids


def test_qualified_ids_separates_snr_candidates_from_magnitude_quality(tmp_path: Path):
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

    # The helper preserves raw SNR candidates separately from the valid-magnitude
    # subset; derive_730k must intersect both sets before publishing membership.
    assert selected == {"1", "2", "3"}
    assert quality == {"1", "2"}



def test_derive_intersects_bands_only_after_finite_magnitude_filter(tmp_path: Path):
    from ztf_classifier.validation.derivation import derive_730k

    parent = tmp_path / "parent.tsv"
    parent.write_text("SourceID\n1\n2\n3\n", encoding="utf-8")
    g = tmp_path / "g.tsv"
    g.write_text(
        "SourceID\tgmag\te_gmag\tg_flag\n"
        "1\t18.0\t0.1\t0\n"
        "2\t18.0\t0.1\t0\n"
        "3\t0.0\t0.1\t0\n",
        encoding="utf-8",
    )
    r = tmp_path / "r.tsv"
    r.write_text(
        "SourceID\trmag\te_rmag\tr_flag\n"
        "1\t17.0\t0.1\t0\n"
        "2\t17.0\t0.1\t0\n"
        "3\t17.0\t0.1\t0\n",
        encoding="utf-8",
    )

    result = derive_730k(
        parent,
        g,
        r,
        tmp_path / "selected.tsv",
        expected_parent_rows=3,
        expected_selected_rows=2,
        parent_evidence_sha256="0" * 64,
    )

    assert result.selected_rows == 2
    assert (tmp_path / "selected.tsv").read_text(encoding="utf-8").splitlines() == [
        "SourceID",
        "1",
        "2",
    ]

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


def test_read_vizier_accepts_commented_tsv_header(tmp_path: Path):
    from scripts.audit_cpvs_membership import read_vizier

    path = tmp_path / "table4.dat"
    path.write_text(
        "# ZTF\tID\n"
        "ZTF1\t1\n"
        "ZTF2\t730184\n",
        encoding="utf-8",
    )

    assert read_vizier(path) == {1, 730184}
