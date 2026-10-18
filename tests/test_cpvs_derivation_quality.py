from pathlib import Path

from ztf_classifier.validation.derivation import _qualified_ids


def test_qualified_ids_separates_snr_candidates_from_magnitude_quality(tmp_path: Path):
    path = tmp_path / "g.tsv"
    path.write_text(
        "SourceID\tgmag\te_gmag\tg_flag\n"
        "1\t18.0\t0.1\t0\n"
        "2\t18.0\t0.1\t1\n"
        "3\t0.0\t0.1\t0\n"
        "4\t18.0\t0.5\t0\n"
        "5\t18.0\tnan\t0\n"
        "6\t18.0\t0.0\t0\n"
        "7\t18.0\t-0.1\t0\n",
        encoding="utf-8",
    )

    selected, quality = _qualified_ids(
        path,
        sigma=2.5,
        parent_ids={"1", "2", "3", "4", "5", "6", "7"},
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

    name1 = "ZTF J000000.1+0000"
    name2 = "ZTF J000001.1+0000"

    def parent_row(name: str, seq: int, ra: float) -> str:
        return f"{name:<22} {seq:6d} {ra:9.5f} {45.0:9.5f}"

    parent = tmp_path / "parent.txt"
    parent.write_text(
        parent_row(name1, 10, 123.0) + "\n"
        + parent_row(name2, 30, 124.0) + "\n",
        encoding="utf-8",
    )

    # Table4 has its own internal ID; mapping must use the ZTF name and the
    # parent's real Seq key, not Table4 IDs or row ordinals.
    published = tmp_path / "table4.dat"
    published.write_text(
        "# ZTF ID Class RAdeg DEdeg Score\n"
        + f"{name1:<22} {700:6d} {'Mira':<5} {123.0:9.5f} {45.0:9.5f} {0.9:7.5f}\n"
        + f"{name2:<22} {701:6d} {'SR':<5} {124.0:9.5f} {46.0:9.5f} {0.8:7.5f}\n",
        encoding="utf-8",
    )

    assert read_vizier(published, parent) == {10, 30}


def test_band_diagnostics_keep_flag_policy_separate_from_snr(tmp_path: Path):
    from scripts.diagnose_cpvs_selection import band_metrics

    path = tmp_path / "g.tsv"
    path.write_text(
        "SourceID\te_gmag\tgmag\tg_flag\n"
        "1\t0.1\t18.0\t0\n"
        "1\t0.1\t18.0\t1\n"
        "2\t0.1\t18.0\t1\n"
        "3\tnan\t18.0\t0\n"
        "4\t0.0\t18.0\t0\n",
        encoding="utf-8",
    )
    metrics = band_metrics(path, {1, 2, 3, 4}, "e_gmag", "gmag")
    assert metrics[1]["snr"] is True
    assert metrics[1]["snr_flag0"] is True
    assert metrics[2]["snr"] is True
    assert metrics[2]["snr_flag0"] is False
    assert metrics[3]["snr"] is False
    assert metrics[4]["snr"] is False


def test_derivation_excludes_candidates_without_parent_mean_band_magnitudes(tmp_path: Path):
    from ztf_classifier.validation.derivation import derive_730k

    parent = tmp_path / "Table2.txt"
    rows = [
        ("ZTFJ000000.01+000000.1", 101, 18.0, 17.0, 0.2, 0.2),
        ("ZTFJ000001.01+000000.1", 205, 0.0, 17.0, 0.2, 0.2),
        ("ZTFJ000002.01+000000.1", 309, 18.0, 0.0, 0.2, 0.2),
        # Per-g is absent, but the common Per and both mean magnitudes exist.
        # The paper says to fold both bands with the common Per, so keep this
        # object in the interim set pending explanation of the 17-object residual.
        ("ZTFJ000003.01+000000.1", 412, 18.0, 17.0, 0.0, 0.2),
    ]
    with parent.open("w", encoding="utf-8") as handle:
        for name, sid, gmag, rmag, perg, perr in rows:
            handle.write(
                f"{name:<22} {sid:>6} {0.1:>9.5f} {0.2:>9.5f} {0.3:>11.7f} "
                f"{0.5:>6.3f} {6.0:>5.3f} {58000.0:>13.7f} "
                f"{gmag:>6.3f} {rmag:>6.3f} {perg:>13.7f} {perr:>13.7f} "
                f"{20:>4d} {20:>4d} {0.5:>6.3f} {0.5:>6.3f} "
                f"{6.0:>6.3f} {6.0:>6.3f} {0.8:>6.3f} {0.8:>6.3f} "
                f"{0.1:>5.3f} {0.1:>5.3f} EW 0.0 0.0\n"
            )

    g = tmp_path / "g.tsv"
    g.write_text(
        "SourceID\tgmag\te_gmag\tg_flag\n"
        "101\t18.0\t0.1\t0\n"
        "205\t18.0\t0.1\t0\n"
        "309\t18.0\t0.1\t0\n"
        "412\t18.0\t0.1\t0\n",
        encoding="utf-8",
    )
    r = tmp_path / "r.tsv"
    r.write_text(
        "SourceID\trmag\te_rmag\tr_flag\n"
        "101\t17.0\t0.1\t0\n"
        "205\t17.0\t0.1\t0\n"
        "309\t17.0\t0.1\t0\n"
        "412\t17.0\t0.1\t0\n",
        encoding="utf-8",
    )

    result = derive_730k(
        parent,
        g,
        r,
        tmp_path / "selected.tsv",
        expected_parent_rows=4,
        expected_selected_rows=2,
        parent_evidence_sha256="0" * 64,
    )

    assert result.selected_rows == 2
    assert (tmp_path / "selected.tsv").read_text(encoding="utf-8").splitlines() == [
        "SourceID",
        "101",
        "412",
    ]
