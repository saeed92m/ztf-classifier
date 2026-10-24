import gzip
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
    g.write_text(
        "SourceID\tgmag\te_gmag\nA\t15.0\t0.1\nB\t16.0\t0.8\n", encoding="utf-8"
    )
    r = tmp_path / "r.tsv"
    r.write_text(
        "SourceID\trmag\te_rmag\nA\t15.0\t0.1\nB\t16.0\t0.8\n", encoding="utf-8"
    )
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


def _fixed_width_cpvs_table2_row(name: str, seq: str | int) -> str:
    return f"{name:<22} {seq!s:>6}\n"


def test_cpvs_table_source_ids_use_official_seq_field(tmp_path: Path):
    from ztf_classifier.validation.derivation import _source_ids

    parent = tmp_path / "Table2.txt"
    parent.write_text(
        "Table 2. ZTF Variables Catalog\n"
        + _fixed_width_cpvs_table2_row("ZTFJ000000.13+620605.8", 1)
        + "page 1 footer\n"
        + _fixed_width_cpvs_table2_row("ZTFJ000000.14+721413.7", 2),
        encoding="utf-8",
    )

    assert _source_ids(parent, None) == {"1", "2"}


def test_cpvs_table_source_ids_preserve_authoritative_seq_gaps(tmp_path: Path):
    from ztf_classifier.validation.derivation import _source_ids

    parent = tmp_path / "Table2.txt"
    parent.write_text(
        _fixed_width_cpvs_table2_row("ZTFJ000000.13+620605.8", 1)
        + _fixed_width_cpvs_table2_row("ZTFJ000000.14+721413.7", 3),
        encoding="utf-8",
    )

    # Seq is the source identifier, not the parsed row ordinal. Gaps are valid.
    assert _source_ids(parent, None) == {"1", "3"}


def test_cpvs_table_source_ids_fail_closed_outside_documented_seq_range(
    tmp_path: Path,
):
    from ztf_classifier.validation.derivation import _source_ids

    parent = tmp_path / "Table2.txt"
    parent.write_text(
        _fixed_width_cpvs_table2_row("ZTFJ000000.13+620605.8", 781605),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="outside the documented range"):
        _source_ids(parent, None)


def test_cpvs_table_source_ids_fail_closed_on_duplicate_seq(tmp_path: Path):
    from ztf_classifier.validation.derivation import _source_ids

    parent = tmp_path / "Table2.txt"
    row = _fixed_width_cpvs_table2_row("ZTFJ000000.13+620605.8", 1)
    parent.write_text(
        row + _fixed_width_cpvs_table2_row("ZTFJ000000.14+721413.7", 1),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="duplicate CPVS Table2 Seq"):
        _source_ids(parent, None)


def test_cpvs_table_source_ids_fail_closed_on_missing_seq(tmp_path: Path):
    from ztf_classifier.validation.derivation import _source_ids

    parent = tmp_path / "Table2.txt"
    parent.write_text(
        _fixed_width_cpvs_table2_row("ZTFJ000000.13+620605.8", "bad"),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="invalid CPVS Table2 Seq"):
        _source_ids(parent, None)


def test_cpvs_table_source_ids_fail_closed_on_truncated_row(tmp_path: Path):
    from ztf_classifier.validation.derivation import _source_ids

    parent = tmp_path / "Table2.txt"
    parent.write_text("ZTFJ000000.13+620605.8\n", encoding="utf-8")

    with pytest.raises(ValueError, match="truncated CPVS Table2 row"):
        _source_ids(parent, None)


def test_lightcurve_directory_auto_selects_data_file(tmp_path: Path):
    from ztf_classifier.validation.derivation import _iter_rows

    root = tmp_path / "g"
    root.mkdir()
    (root / "README.txt").write_text("CPVS g-band documentation\n", encoding="utf-8")
    (root / "nested").mkdir()
    (root / "nested" / "ztf2g.txt").write_text(
        "SourceID RAdeg DEdeg HJD gmag e_gmag g_flag\n1 1 2 3 15.0 0.1 0\n",
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


def test_lightcurve_directory_accepts_headerless_cpvs_file(tmp_path: Path):
    from ztf_classifier.validation.derivation import _iter_rows

    root = tmp_path / "g"
    root.mkdir()
    (root / "ztf2g").write_text(
        "1 1.0 2.0 3.0 15.0 0.1 0\n2 1.1 2.1 4.0 16.0 0.2 1\n",
        encoding="utf-8",
    )

    assert list(_iter_rows(root, required_columns=("SourceID", "e_gmag"))) == [
        {
            "SourceID": "1",
            "RAdeg": "1.0",
            "DEdeg": "2.0",
            "HJD": "3.0",
            "gmag": "15.0",
            "e_gmag": "0.1",
            "g_flag": "0",
        },
        {
            "SourceID": "2",
            "RAdeg": "1.1",
            "DEdeg": "2.1",
            "HJD": "4.0",
            "gmag": "16.0",
            "e_gmag": "0.2",
            "g_flag": "1",
        },
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


def test_lightcurve_gzip_accepts_headerless_cpvs_file(tmp_path: Path):
    from ztf_classifier.validation.derivation import _iter_rows

    path = tmp_path / "ztf2g.gz"
    with gzip.open(path, "wt", encoding="utf-8") as handle:
        handle.write("1 1.0 2.0 3.0 15.0 0.1 0\n2 1.1 2.1 4.0 16.0 0.2 1\n")

    assert list(_iter_rows(path, required_columns=("SourceID", "e_gmag"))) == [
        {
            "SourceID": "1",
            "RAdeg": "1.0",
            "DEdeg": "2.0",
            "HJD": "3.0",
            "gmag": "15.0",
            "e_gmag": "0.1",
            "g_flag": "0",
        },
        {
            "SourceID": "2",
            "RAdeg": "1.1",
            "DEdeg": "2.1",
            "HJD": "4.0",
            "gmag": "16.0",
            "e_gmag": "0.2",
            "g_flag": "1",
        },
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
            "# SourceID RAdeg DEdeg HJD gmag e_gmag g_flag\n1 1 2 3 15.0 0.1 0\n",
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
