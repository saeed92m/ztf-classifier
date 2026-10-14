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
        "4\t0.0\t18.0\t0\n"
        "5\t0.4\t18.0\t0\n",
        encoding="utf-8",
    )
    metrics = band_metrics(path, {1, 2, 3, 4, 5}, "e_gmag", "gmag")
    assert metrics[1]["snr"] is True
    assert metrics[1]["snr_flag0"] is True
    assert metrics[2]["snr"] is True
    assert metrics[2]["snr_flag0"] is False
    assert metrics[3]["snr"] is False
    assert metrics[4]["snr"] is False
    # For a 0.4-mag uncertainty, the linear approximation exceeds 2.5σ,
    # but the exact inverse magnitude-error transform does not.
    assert metrics[5]["snr"] is True
    assert metrics[5]["snr_exact"] is False


def test_parent_catalog_metadata_reports_type_and_published_detection_counts(
    tmp_path: Path,
):
    from scripts.diagnose_cpvs_selection import parent_catalog_metadata

    def table2_row(
        name: str, source_id: int, variable_type: str, ng: int, nr: int
    ) -> str:
        row = [" "] * 228
        row[0:22] = list(f"{name:<22}")
        row[23:29] = list(f"{source_id:6d}")
        row[30:39] = list(f"{123.45678:9.5f}")
        row[89:95] = list(f"{17.5:6.2f}")
        row[96:102] = list(f"{18.2:6.2f}")
        row[131:135] = list(f"{ng:4d}")
        row[136:140] = list(f"{nr:4d}")
        row[211:216] = list(f"{variable_type:<5}")
        return "".join(row)

    parent = tmp_path / "parent_table2.txt"
    parent.write_text(
        table2_row("ZTFJ000000.00+000000.0", 100, "Mira", 25, 30)
        + "\n"
        + table2_row("ZTFJ000001.00+000000.0", 102, "EW", 0, 12)
        + "\n",
        encoding="utf-8",
    )

    metadata = parent_catalog_metadata(parent)
    assert set(metadata) == {100, 102}
    assert {
        source_id: {
            key: metadata[source_id][key]
            for key in ("type", "ng", "nr", "gmag", "rmag")
        }
        for source_id in metadata
    } == {
        100: {"type": "Mira", "ng": 25, "nr": 30, "gmag": 17.5, "rmag": 18.2},
        102: {"type": "EW", "ng": 0, "nr": 12, "gmag": 17.5, "rmag": 18.2},
    }
    # Extended diagnostic fields may be unavailable in minimal synthetic rows,
    # but their absence must not erase the published metadata above.


def test_parent_catalog_metadata_uses_named_column_vizier_tsv(tmp_path: Path):
    from scripts.diagnose_cpvs_selection import parent_catalog_metadata

    parent = tmp_path / "parent-mirror.txt"
    parent.write_text("metadata supplied separately\\n", encoding="utf-8")
    metadata_tsv = tmp_path / "parent-metadata.tsv"
    metadata_tsv.write_text(
        "#Seq\\tgmag\\trmag\\tNg\\tNr\\tType\\n"
        "100\\t17.5\\t18.2\\t25\\t30\\tMira\\n"
        "102\\t0\\t18.1\\t0\\t12\\tEW\\n",
        encoding="utf-8",
    )

    metadata = parent_catalog_metadata(parent, metadata_tsv)
    assert metadata[100]["gmag"] == 17.5
    assert metadata[100]["rmag"] == 18.2
    assert metadata[100]["ng"] == 25
    assert metadata[100]["nr"] == 30
    assert metadata[100]["type"] == "Mira"
    assert metadata[102]["gmag"] == 0
    assert metadata[102]["ng"] == 0
    assert metadata[102]["type"] == "EW"
