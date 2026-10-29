"""Tests for the fail-closed Zenodo Table 2 format adapter."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "normalize_cpvs_table2_zenodo.py"
_spec = importlib.util.spec_from_file_location("normalize_cpvs_table2_zenodo", _SCRIPT)
assert _spec is not None and _spec.loader is not None
norm = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(norm)


@pytest.fixture()
def small_source_contract(monkeypatch):
    monkeypatch.setattr(norm, "SEQ_MAX", 5)


def _set(line: list[str], start: int, end: int, value: str) -> None:
    """Write a 1-based inclusive field into a character list."""
    assert len(value) <= end - start + 1
    line[start - 1 : end] = list(value.rjust(end - start + 1))


def _row(seq: int, name: str, gmag: float, rmag: float, per_g: float, per_r: float) -> str:
    line = list(" " * 223)
    _set(line, 1, 22, name)
    _set(line, 24, 29, str(seq))
    _set(line, 90, 95, f"{gmag:6.3f}")
    _set(line, 97, 102, f"{rmag:6.3f}")
    _set(line, 104, 116, f"{per_g:13.7f}")
    _set(line, 117, 129, f"{per_r:13.7f}")
    return "".join(line).rstrip()


def _source(tmp_path: Path) -> tuple[Path, list[str]]:
    rows = [
        _row(1, "ZTFJ000001.00+000001.0", 18.5, 17.2, 12.34, 12.35),
        _row(2, "ZTFJ000002.00+000002.0", 19.1, 17.9, 5.5, 5.51),
        _row(4, "ZTFJ000004.00+000004.0", 20.0, 19.0, 8.0, 8.01),
        _row(5, "ZTFJ000005.00+000005.0", 20.0, 19.0, 8.0, 8.01),
    ]
    source = tmp_path / "Table2.txt"
    source.write_text("Table: test\n----------------\n" + "\n".join(rows) + "\n", encoding="ascii")
    return source, rows


def test_normalization_preserves_fields_and_counts_seq_gaps(tmp_path, small_source_contract):
    source, original_rows = _source(tmp_path)
    output = tmp_path / "table2.dat"
    report_path = tmp_path / "normalization.json"
    report = norm.normalize(
        source, output, report_path,
        expected_source_lines=6, expected_records=4, expected_metadata_lines=2,
    )
    normalized_rows = output.read_text(encoding="ascii").splitlines()
    assert report["status"] == "PASS"
    assert report["recognized_record_count"] == 4
    assert report["seq_gaps"] == 1
    assert len(normalized_rows) == 4
    for original, normalized in zip(original_rows, normalized_rows):
        assert normalized[103:116].strip() == original[103:116].strip()
        assert normalized[117:130].strip() == original[116:129].strip()
        assert normalized[89:95].strip() == original[89:95].strip()
        assert normalized[96:102].strip() == original[96:102].strip()
    assert report["normalized_sha256"]


def test_bad_record_count_fails_closed_and_writes_report(tmp_path, small_source_contract):
    source, _ = _source(tmp_path)
    output = tmp_path / "table2.dat"
    report_path = tmp_path / "normalization.json"
    with pytest.raises(norm.ContractError, match="source contract mismatch"):
        norm.normalize(
            source, output, report_path,
            expected_source_lines=6, expected_records=3, expected_metadata_lines=2,
        )
    assert report_path.exists()
    assert not output.exists()


def test_non_numeric_period_fails_closed(tmp_path, small_source_contract):
    source, rows = _source(tmp_path)
    bad = list(rows)
    chars = list(bad[0])
    chars[116:129] = list("not-a-number".ljust(13))
    bad[0] = "".join(chars)
    source.write_text("Table: test\n----------------\n" + "\n".join(bad) + "\n", encoding="ascii")
    with pytest.raises(norm.ContractError, match="non-numeric per_r"):
        norm.normalize(
            source, tmp_path / "table2.dat", tmp_path / "normalization.json",
            expected_source_lines=6, expected_records=4, expected_metadata_lines=2,
        )
