"""Regression tests for VizieR separator rows in CPVS membership tables."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from audit_cpvs_candidate_four_field import read_vizier
from diagnose_cpvs_selection import published_membership


def test_read_vizier_skips_dashed_separator_rows(tmp_path: Path) -> None:
    table = tmp_path / "table4.tsv"
    table.write_text(
        "ZTF\tID\n"
        "----------------------\t----------------------\n"
        "ZTF J123456.78+123456.7\t42\n",
        encoding="utf-8",
    )

    rows = read_vizier(table, ("ZTF", "ID"))

    assert rows == [{"ZTF": "ZTF J123456.78+123456.7", "ID": "42"}]


def test_published_membership_crosswalk_ignores_separator_rows(
    tmp_path: Path,
) -> None:
    table2 = tmp_path / "table2.tsv"
    table4 = tmp_path / "table4.tsv"
    table2.write_text(
        "ID\tSeq\n"
        "ZTF J123456.78+123456.7\t4200\n",
        encoding="utf-8",
    )
    table4.write_text(
        "ZTF\tID\n"
        "----------------------\t----------------------\n"
        "ZTF J123456.78+123456.7\t1\n",
        encoding="utf-8",
    )

    published, crosswalk = published_membership(table2, table4, None)

    assert published == {4200}
    assert crosswalk["published_rows"] == 1
    assert crosswalk["unmapped_published_names"] == 0
