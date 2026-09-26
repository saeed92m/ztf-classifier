import zipfile
from pathlib import Path

import pytest

from ztf_classifier.validation.derivation import (
    DerivationConfig,
    _snr_from_mag_error,
    derive_730k,
)


def test_published_sigma_defaults():
    config = DerivationConfig()
    assert config.g_sigma == 2.5
    assert config.r_sigma == 3.0


def test_snr_from_magnitude_error():
    assert _snr_from_mag_error("0.4342944819") == pytest.approx(2.5, rel=1e-8)
    assert _snr_from_mag_error("0.3619120683") == pytest.approx(3.0, rel=1e-8)
    assert _snr_from_mag_error("bad") != _snr_from_mag_error("bad")


def test_derivation_fails_closed_on_parent_count(tmp_path: Path):
    parent = tmp_path / "parent.tsv"
    parent.write_text("SourceID\nA\nB\n", encoding="utf-8")
    g = tmp_path / "g.tsv"
    g.write_text("SourceID\te_gmag\nA\t0.1\nB\t0.1\n", encoding="utf-8")
    r = tmp_path / "r.tsv"
    r.write_text("SourceID\te_rmag\nA\t0.1\nB\t0.1\n", encoding="utf-8")
    with pytest.raises(ValueError, match="parent row/object count mismatch"):
        derive_730k(parent, g, r, tmp_path / "selected.tsv")


def test_derivation_emits_immutable_evidence_manifest(tmp_path: Path):
    parent = tmp_path / "parent.tsv"
    parent.write_text("SourceID\nA\nB\n", encoding="utf-8")
    g = tmp_path / "g.tsv"
    g.write_text("SourceID\te_gmag\nA\t0.1\nB\t0.8\n", encoding="utf-8")
    r = tmp_path / "r.tsv"
    r.write_text("SourceID\te_rmag\nA\t0.1\nB\t0.8\n", encoding="utf-8")
    result = derive_730k(
        parent,
        g,
        r,
        tmp_path / "selected.tsv",
        expected_parent_rows=2,
        expected_selected_rows=1,
        parent_evidence_sha256="0" * 64,
        code_version="test",
    )
    assert result.selected_rows == 1
    evidence = (tmp_path / "selected.tsv.evidence.json").read_text(encoding="utf-8")
    assert '"parent_evidence_sha256": "' + "0" * 64 in evidence


def test_cpvs_table_parser_skips_metadata_before_sourceid_header(tmp_path: Path):
    from ztf_classifier.validation.derivation import _iter_rows

    parent = tmp_path / "Table2.txt"
    parent.write_text(
        "Table: ZTF variables catalog\n"
        "This metadata line must not become the header.\n"
        "SourceID\tName\n"
        "3\tZTFJ000000.19+320847.2\n",
        encoding="utf-8",
    )

    assert list(_iter_rows(parent)) == [
        {"SourceID": "3", "Name": "ZTFJ000000.19+320847.2"}
    ]


def test_cpvs_table_falls_back_to_ordinal_sourceids(tmp_path: Path):
    from ztf_classifier.validation.derivation import _source_ids

    parent = tmp_path / "Table2.txt"
    parent.write_text(
        "Table 2. ZTF Variables Catalog\n"
        "ID R.A. (J2000) Dec. (J2000) Period Type\n"
        "ZTFJ000000.13+620605.8 0.00056 62.10163 1.9449979 BYDra\n"
        "ZTFJ000000.14+721413.7 0.00061 72.23716 0.2991500 EW\n"
        "ZTFJ000000.19+320847.2 0.00080 32.14645 0.2870590 EW\n"
        "Note: footer must not become a catalog row\n",
        encoding="utf-8",
    )

    assert _source_ids(parent, None) == {"1", "2", "3"}




def test_lightcurve_directory_auto_selects_data_file(tmp_path: Path):
    from ztf_classifier.validation.derivation import _iter_rows

    root = tmp_path / "g"
    root.mkdir()
    (root / "README.txt").write_text("CPVS g-band documentation\n", encoding="utf-8")
    (root / "nested").mkdir()
    (root / "nested" / "ztf2g.txt").write_text(
        "SourceID RAdeg DEdeg HJD gmag e_gmag g_flag\n"
        "1 1 2 3 15.0 0.1 0\n",
        encoding="utf-8",
    )

    assert list(_iter_rows(root, required_columns=("SourceID", "e_gmag"))) == [
        {
            "SourceID": "1",
            "RAdeg": "1",
            "DEdeg": "2",
            "HJD": "3",
            "gmag": "15.0",
            "e_gmag": "0.1",
            "g_flag": "0",
        }
    ]


def test_lightcurve_directory_aggregates_data_files(tmp_path: Path):
    from ztf_classifier.validation.derivation import _iter_rows

    root = tmp_path / "g"
    root.mkdir()
    payload = "SourceID e_gmag\n"
    (root / "part1.txt").write_text(payload + "1 0.1\n", encoding="utf-8")
    (root / "part2.txt").write_text(payload + "2 0.2\n", encoding="utf-8")

    assert list(_iter_rows(root, required_columns=("SourceID", "e_gmag"))) == [
        {"SourceID": "1", "e_gmag": "0.1"},
        {"SourceID": "2", "e_gmag": "0.2"},
    ]


def test_lightcurve_zip_auto_selects_data_member(tmp_path: Path):
    from ztf_classifier.validation.derivation import _iter_rows

    archive = tmp_path / "ztf2g.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("README.txt", "CPVS g-band documentation\n")
        zf.writestr(
            "ztf2g",
            "SourceID\tRAdeg\tDEdeg\tHJD\tgmag\te_gmag\tg_flag\n"
            "1\t1\t2\t3\t15.0\t0.1\t0\n",
        )

    assert list(
        _iter_rows(
            archive,
            required_columns=("SourceID", "e_gmag"),
        )
    ) == [
        {
            "SourceID": "1",
            "RAdeg": "1",
            "DEdeg": "2",
            "HJD": "3",
            "gmag": "15.0",
            "e_gmag": "0.1",
            "g_flag": "0",
        }
    ]


def test_lightcurve_zip_fails_closed_on_ambiguous_members(tmp_path: Path):
    from ztf_classifier.validation.derivation import _iter_rows

    archive = tmp_path / "ambiguous.zip"
    payload = "SourceID\te_gmag\n1\t0.1\n"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("part1", payload)
        zf.writestr("part2", payload)

    with pytest.raises(ValueError, match="multiple members matching required columns"):
        list(_iter_rows(archive, required_columns=("SourceID", "e_gmag")))


def test_lightcurve_zip_accepts_whitespace_delimited_header(tmp_path: Path):
    from ztf_classifier.validation.derivation import _iter_rows

    archive = tmp_path / "ztf2g-whitespace.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("README.txt", "CPVS g-band documentation\n")
        zf.writestr(
            "ztf2g",
            "# SourceID RAdeg DEdeg HJD gmag e_gmag g_flag\n"
            "1 1 2 3 15.0 0.1 0\n",
        )

    assert list(
        _iter_rows(
            archive,
            required_columns=("SourceID", "e_gmag"),
        )
    ) == [
        {
            "SourceID": "1",
            "RAdeg": "1",
            "DEdeg": "2",
            "HJD": "3",
            "gmag": "15.0",
            "e_gmag": "0.1",
            "g_flag": "0",
        }
    ]
