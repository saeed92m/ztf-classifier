"""Tests for scripts/verify_cpvs_four_field_rule.py.

These exercise the DECISIVE-OFFLINE four-field test against SYNTHETIC synthetic
fixed-width fixtures that reproduce the documented CDS byte layout. No
publisher data is present; the numbers here validate parser and set logic only.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

_SCRIPT = (
    Path(__file__).resolve().parents[1] / "scripts" / "verify_cpvs_four_field_rule.py"
)
_spec = importlib.util.spec_from_file_location("verify_cpvs_four_field_rule", _SCRIPT)
assert _spec is not None and _spec.loader is not None
vfr = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(vfr)


@pytest.fixture()
def small_contract(monkeypatch):
    """Shrink the documented row counts so tiny fixtures are admissible."""
    monkeypatch.setattr(vfr, "TABLE2_REQUIRED_ROWS", 4)
    monkeypatch.setattr(vfr, "TABLE4_REQUIRED_ROWS", 2)


def _write(dirpath: Path, table2_rows: list[str], table4_rows: list[str] | None = None):
    t2 = dirpath / "table2.dat"
    t2.write_text("\n".join(table2_rows) + "\n")
    t4 = None
    if table4_rows is not None:
        t4 = dirpath / "table4.dat"
        t4.write_text("\n".join(table4_rows) + "\n")
    return t2, t4


def test_four_field_matches_published_when_all_conditions_align(
    tmp_path, small_contract
):
    t2, t4 = _write(
        tmp_path,
        [
            vfr._make_t2_row("ZTF1aaa", 1, 18.5, 17.2, 12.34, 12.35),
            vfr._make_t2_row("ZTF2bbb", 2, 19.1, 17.9, 5.5, 5.51),
            vfr._make_t2_row("ZTF3ccc", 3, 0.0, 17.0, 8.0, 8.01),
            vfr._make_t2_row("ZTF4ddd", 4, 20.0, 19.0, 0.0, 8.01),
        ],
        [vfr._make_t4_row("ZTF1aaa", 1), vfr._make_t4_row("ZTF2bbb", 2)],
    )
    report = vfr.run(t2, t4, None)
    assert report["counts"]["four_field_count"] == 2
    assert report["counts"]["four_field_only"] == 0
    assert report["counts"]["published_only"] == 0
    assert report["verdict"]["status"] == "EXTENSIONALLY_EQUIVALENT"
    # The caveat must always accompany equivalence.
    assert "not proof of author intent" in report["verdict"]["caveat"]


def test_unpublished_positive_object_refutes_the_rule(tmp_path, small_contract):
    t2, t4 = _write(
        tmp_path,
        [
            vfr._make_t2_row("ZTF1aaa", 1, 18.5, 17.2, 12.34, 12.35),
            vfr._make_t2_row("ZTF2bbb", 2, 19.1, 17.9, 5.5, 5.51),
            vfr._make_t2_row("ZTF3ccc", 3, 18.0, 17.0, 8.0, 8.01),
            vfr._make_t2_row("ZTF4ddd", 4, 20.0, 19.0, 0.0, 8.01),
        ],
        [vfr._make_t4_row("ZTF1aaa", 1), vfr._make_t4_row("ZTF4ddd", 4)],
    )
    report = vfr.run(t2, t4, None)
    assert report["counts"]["four_field_only"] == 2  # seq 2 and 3
    assert report["verdict"]["status"] == "BOTH_DIRECTIONS_FAIL"


def test_published_member_violating_the_rule_means_insufficient(
    tmp_path, small_contract
):
    t2, t4 = _write(
        tmp_path,
        [
            vfr._make_t2_row("ZTF1aaa", 1, 18.5, 17.2, 12.34, 12.35),
            vfr._make_t2_row("ZTF2bbb", 2, 0.0, 17.9, 5.5, 5.51),
            vfr._make_t2_row("ZTF3ccc", 3, 0.0, 17.0, 8.0, 8.01),
            vfr._make_t2_row("ZTF4ddd", 4, 20.0, 19.0, 0.0, 8.01),
        ],
        [vfr._make_t4_row("ZTF1aaa", 1), vfr._make_t4_row("ZTF2bbb", 2)],
    )
    report = vfr.run(t2, t4, None)
    assert report["counts"]["published_only"] == 1
    assert report["verdict"]["status"] == "HYPOTHESIS_INSUFFICIENT"


def test_null_sentinel_is_not_positive(tmp_path, small_contract):
    """`?=0` fields must read as null, never as 0.0 satisfying `> 0`."""
    t2, t4 = _write(
        tmp_path,
        [
            vfr._make_t2_row("ZTF1aaa", 1, 18.5, 17.2, 12.34, 12.35),
            vfr._make_t2_row("ZTF2bbb", 2, 0.0, 0.0, 0.0, 0.0),
            vfr._make_t2_row("ZTF3ccc", 3, 18.0, 17.0, 8.0, 8.01),
            vfr._make_t2_row("ZTF4ddd", 4, 18.0, 17.0, 8.0, 8.01),
        ],
        [vfr._make_t4_row("ZTF1aaa", 1), vfr._make_t4_row("ZTF3ccc", 3)],
    )
    report = vfr.run(t2, t4, None)
    assert report["counts"]["null_per_field"]["gmag"] == 1
    assert report["counts"]["four_field_count"] == 3  # seq 1, 3, 4


def test_truncated_row_aborts_instead_of_being_skipped(tmp_path, small_contract):
    t2, t4 = _write(
        tmp_path,
        [_make_short_row()],
        [vfr._make_t4_row("ZTF1aaa", 1), vfr._make_t4_row("ZTF2bbb", 2)],
    )
    with pytest.raises(vfr.ContractError, match="truncated"):
        vfr.run(t2, t4, None)


def _make_short_row() -> str:
    return vfr._make_t2_row("ZTF1aaa", 1, 18.0, 17.0, 1.0, 1.0)[:100]


def test_wrong_row_count_aborts(tmp_path, small_contract):
    t2, t4 = _write(
        tmp_path,
        [
            vfr._make_t2_row("ZTF1aaa", 1, 18.5, 17.2, 12.34, 12.35),
            vfr._make_t2_row("ZTF2bbb", 2, 19.1, 17.9, 5.5, 5.51),
        ],
        [vfr._make_t4_row("ZTF1aaa", 1), vfr._make_t4_row("ZTF2bbb", 2)],
    )
    with pytest.raises(vfr.ContractError, match="row count mismatch"):
        vfr.run(t2, t4, None)


def test_duplicate_seq_aborts(tmp_path, small_contract):
    t2, t4 = _write(
        tmp_path,
        [
            vfr._make_t2_row("ZTF1aaa", 1, 18.5, 17.2, 12.34, 12.35),
            vfr._make_t2_row("ZTF1aaa", 1, 19.1, 17.9, 5.5, 5.51),
            vfr._make_t2_row("ZTF3ccc", 3, 18.0, 17.0, 8.0, 8.01),
            vfr._make_t2_row("ZTF4ddd", 4, 18.0, 17.0, 8.0, 8.01),
        ],
        [vfr._make_t4_row("ZTF1aaa", 1), vfr._make_t4_row("ZTF3ccc", 3)],
    )
    with pytest.raises(vfr.ContractError, match="duplicate Seq"):
        vfr.run(t2, t4, None)


def test_name_seq_namespace_mismatch_aborts(tmp_path, small_contract):
    """If Table4.ID is not Table2.Seq, refuse to compare sets at all."""
    t2, t4 = _write(
        tmp_path,
        [
            vfr._make_t2_row("ZTF1aaa", 1, 18.5, 17.2, 12.34, 12.35),
            vfr._make_t2_row("ZTF2bbb", 2, 19.1, 17.9, 5.5, 5.51),
            vfr._make_t2_row("ZTF3ccc", 3, 18.0, 17.0, 8.0, 8.01),
            vfr._make_t2_row("ZTF4ddd", 4, 18.0, 17.0, 8.0, 8.01),
        ],
        [vfr._make_t4_row("ZTF9zzz", 1), vfr._make_t4_row("ZTF2bbb", 2)],
    )
    with pytest.raises(vfr.ContractError, match="namespace assumption is refuted"):
        vfr.run(t2, t4, None)


def test_id_outside_documented_range_aborts(tmp_path, small_contract):
    t2, t4 = _write(
        tmp_path,
        [
            vfr._make_t2_row("ZTF1aaa", 1, 18.5, 17.2, 12.34, 12.35),
            vfr._make_t2_row("ZTF2bbb", 2, 19.1, 17.9, 5.5, 5.51),
            vfr._make_t2_row("ZTF3ccc", 3, 18.0, 17.0, 8.0, 8.01),
            vfr._make_t2_row("ZTF4ddd", 781_605, 18.0, 17.0, 8.0, 8.01),
        ],
        [vfr._make_t4_row("ZTF1aaa", 1), vfr._make_t4_row("ZTF2bbb", 2)],
    )
    with pytest.raises(vfr.ContractError, match="outside documented"):
        vfr.run(t2, t4, None)


def test_zenodo_path_joins_on_ztf_name(tmp_path, small_contract):
    t2, _ = _write(
        tmp_path,
        [
            vfr._make_t2_row("ZTF1aaa", 1, 18.5, 17.2, 12.34, 12.35),
            vfr._make_t2_row("ZTF2bbb", 2, 19.1, 17.9, 5.5, 5.51),
            vfr._make_t2_row("ZTF3ccc", 3, 18.0, 17.0, 8.0, 8.01),
            vfr._make_t2_row("ZTF4ddd", 4, 18.0, 17.0, 8.0, 8.01),
        ],
    )
    csv = tmp_path / "1st_layer.csv"
    csv.write_text("ID,SourceID,gmag\nZTF1aaa,X,18.5\nZTF2bbb,Y,19.1\n")
    report = vfr.run(t2, None, csv)
    assert report["counts"]["zenodo_names"] == 2
    assert report["counts"]["published_count"] == 2
    assert report["counts"]["four_field_only"] == 2


def test_zenodo_unmapped_name_aborts(tmp_path, small_contract):
    t2, _ = _write(
        tmp_path,
        [
            vfr._make_t2_row("ZTF1aaa", 1, 18.5, 17.2, 12.34, 12.35),
            vfr._make_t2_row("ZTF2bbb", 2, 19.1, 17.9, 5.5, 5.51),
            vfr._make_t2_row("ZTF3ccc", 3, 18.0, 17.0, 8.0, 8.01),
            vfr._make_t2_row("ZTF4ddd", 4, 18.0, 17.0, 8.0, 8.01),
        ],
    )
    csv = tmp_path / "1st_layer.csv"
    csv.write_text("ID,SourceID\nZTF1aaa,X\nZTF_NOT_IN_TABLE2,Y\n")
    with pytest.raises(vfr.ContractError, match="absent from table2.dat"):
        vfr.run(t2, None, csv)


def test_set_digests_are_present_for_out_of_band_verification(tmp_path, small_contract):
    """Counts alone are insufficient; digests let a third party re-verify."""
    t2, t4 = _write(
        tmp_path,
        [
            vfr._make_t2_row("ZTF1aaa", 1, 18.5, 17.2, 12.34, 12.35),
            vfr._make_t2_row("ZTF2bbb", 2, 19.1, 17.9, 5.5, 5.51),
            vfr._make_t2_row("ZTF3ccc", 3, 18.0, 17.0, 8.0, 8.01),
            vfr._make_t2_row("ZTF4ddd", 4, 18.0, 17.0, 8.0, 8.01),
        ],
        [vfr._make_t4_row("ZTF1aaa", 1), vfr._make_t4_row("ZTF4ddd", 4)],
    )
    report = vfr.run(t2, t4, None)
    for key in (
        "four_field_only_sha256_of_sorted_ids",
        "published_only_sha256_of_sorted_ids",
    ):
        digest = report["counts"][key]
        assert isinstance(digest, str) and len(digest) == 64


def test_seq_gaps_counts_missing_ids_as_positive(tmp_path, small_contract):
    t2, t4 = _write(
        tmp_path,
        [
            vfr._make_t2_row("ZTF1aaa", 1, 18.5, 17.2, 12.34, 12.35),
            vfr._make_t2_row("ZTF2bbb", 2, 19.1, 17.9, 5.5, 5.51),
            vfr._make_t2_row("ZTF4ddd", 4, 20.0, 19.0, 8.0, 8.01),
            vfr._make_t2_row("ZTF5eee", 5, 20.0, 19.0, 8.0, 8.01),
        ],
        [vfr._make_t4_row("ZTF1aaa", 1), vfr._make_t4_row("ZTF2bbb", 2)],
    )
    report = vfr.run(t2, t4, None)
    assert report["counts"]["seq_gaps"] == 1


def test_cli_self_test_passes(capsys):
    assert vfr.main(["--self-test"]) == 0
    out = capsys.readouterr().out
    assert json.loads(out)["self_test"] == "PASS"


def test_cli_contract_violation_exits_2(tmp_path, small_contract, capsys):
    t2, t4 = _write(
        tmp_path,
        [_make_short_row()],
        [vfr._make_t4_row("ZTF1aaa", 1), vfr._make_t4_row("ZTF2bbb", 2)],
    )
    code = vfr.main(
        ["--table2", str(t2), "--table4", str(t4), "--out", str(tmp_path / "r.json")]
    )
    assert code == 2
    assert "CONTRACT VIOLATION" in capsys.readouterr().err
    assert not (tmp_path / "r.json").exists()
