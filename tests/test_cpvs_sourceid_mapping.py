from pathlib import Path

import pytest

from ztf_classifier.validation.derivation import _source_ids_from_catalog


def test_cpvs_parent_catalog_uses_explicit_seq_not_row_order(tmp_path: Path):
    parent = tmp_path / "Table2.txt"
    parent.write_text(
        "metadata ignored\n"
        "ZTFJ000000.19+320847.2 3 0.0000 32.1464\n"
        "ZTFJ000001.00+000000.0 17 0.0042 0.0000\n",
        encoding="utf-8",
    )

    assert _source_ids_from_catalog(parent, None) == {"3", "17"}


def test_cpvs_parent_catalog_rejects_missing_seq_instead_of_inventing_ordinals(
    tmp_path: Path,
):
    parent = tmp_path / "Table2.txt"
    parent.write_text(
        "ZTFJ000000.19+320847.2 12.5 32.1\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="integer Seq/SourceID"):
        _source_ids_from_catalog(parent, None)


def test_cpvs_parent_catalog_rejects_duplicate_seq(tmp_path: Path):
    parent = tmp_path / "Table2.txt"
    parent.write_text(
        "ZTFJ000000.19+320847.2 3 0.0000 32.1464\n"
        "ZTFJ000001.00+000000.0 3 0.0042 0.0000\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="duplicate CPVS Table2 Seq/SourceID|duplicate CPVS Table2 SourceID/Seq"):
        _source_ids_from_catalog(parent, None)
