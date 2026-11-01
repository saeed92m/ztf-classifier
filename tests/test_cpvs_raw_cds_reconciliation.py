from __future__ import annotations

import importlib.util
from pathlib import Path

SCRIPT = (
    Path(__file__).resolve().parents[1] / "scripts" / "cpvs_raw_cds_reconciliation.py"
)
SPEC = importlib.util.spec_from_file_location("cpvs_raw_cds_reconciliation", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


def _catalog_row(
    lrecl: int, name: bytes = b"ZTFJ000000.13+620605.8", source_id: bytes = b"000123"
) -> bytes:
    row = bytearray(b" " * lrecl)
    row[:22] = name.ljust(22, b" ")
    row[23:29] = source_id
    return bytes(row)


def test_raw_cds_records_allow_trailing_blank_omission(tmp_path: Path) -> None:
    row = _catalog_row(63).rstrip(b" ")
    source = tmp_path / "table4.dat"
    source.write_bytes(row + b"\n")

    raw, rows, lengths = AUDIT.records(source, 63)

    assert raw == row + b"\n"
    assert rows == [row]
    assert lengths == {len(row): 1}


def test_publisher_mrt_records_allow_one_trailing_pad_byte(tmp_path: Path) -> None:
    row = _catalog_row(63)
    source = tmp_path / "table4.mrt.txt"
    source.write_bytes(row + b" \n")

    _, rows, lengths = AUDIT.records(source, 63, allow_trailing_pad=True)

    assert rows == [row + b" "]
    assert lengths == {64: 1}


def test_raw_cds_rejects_record_longer_than_lrecl(tmp_path: Path) -> None:
    source = tmp_path / "bad.dat"
    source.write_bytes(_catalog_row(63) + b" \n")

    try:
        AUDIT.records(source, 63)
    except ValueError as exc:
        assert "exceeds Lrecl" in str(exc)
    else:
        raise AssertionError("overlength raw CDS record must fail closed")


def test_table2_seq_and_table4_id_are_preserved_as_strings(tmp_path: Path) -> None:
    table2 = tmp_path / "table2.dat"
    table4 = tmp_path / "table4.dat"
    table2.write_bytes(_catalog_row(228) + b"\n")
    table4.write_bytes(_catalog_row(63) + b"\n")

    _, _, _, by_name, by_seq = AUDIT.load_table2(table2)
    _, _, _, parsed_table4 = AUDIT.load_table4(table4)

    assert by_name["ZTFJ000000.13+620605.8"]["SourceID"] == "000123"
    assert by_seq["000123"] == "ZTFJ000000.13+620605.8"
    assert parsed_table4[0]["Table4_ID"] == "000123"


def test_fixed_samples_are_deterministic_and_stratified() -> None:
    groups = {
        "reference_candidate": {f"{i}" for i in range(1, 1001)},
        "candidate_only": {f"{i}" for i in range(1001, 1501)},
        "reference_only": set(),
        "parent_neither": {f"{i}" for i in range(1501, 2001)},
    }

    first = AUDIT.sample_ids(groups, 100, "test-seed")
    second = AUDIT.sample_ids(groups, 100, "test-seed")

    assert first == second
    assert len(first) == 100
    assert len({source_id for source_id, _ in first}) == 100
    assert {name: sum(stratum == name for _, stratum in first) for name in groups} == {
        "reference_candidate": 50,
        "candidate_only": 25,
        "reference_only": 0,
        "parent_neither": 25,
    }
