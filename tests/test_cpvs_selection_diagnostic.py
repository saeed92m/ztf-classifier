"""Regression tests for the source-backed CPVS selection diagnostic.

These cover the artifact the heavy validation uploads, not the science of the
730,184 reconstruction. Two things are pinned:

1. the script can run at all (an earlier import change broke it silently, because
   nothing tested it), and
2. its serialized output is standards-compliant JSON, so the artifact can be
   parsed by anything other than Python's permissive default decoder.
"""

from __future__ import annotations

import json
import sys
import zipfile
from pathlib import Path

import pytest

from scripts.audit_cpvs_membership import read_parent_name_map
from scripts.diagnose_cpvs_selection import main


class _Fixture:
    """A miniature CPVS layout: zipped CSV parent, TSV published, CSV photometry.

    ''Seq'' deliberately skips 3, so any code path that substitutes a row ordinal
    for ''Seq'' produces a different answer than one that reads the column.
    """

    PUBLISHED_COUNT = 5
    SEQS = (1, 2, 4, 5, 6, 7, 8, 9)
    NAMES = tuple(f"ZTFJ{i:06d}.00+000000.0" for i in range(1, 9))

    def __init__(self, root: Path) -> None:
        self.names = self.NAMES
        self.seqs = self.SEQS
        self.published_count = self.PUBLISHED_COUNT
        self.root = root
        (root / "g").mkdir(parents=True)
        (root / "r").mkdir(parents=True)

        rows = ["ID,Seq,Per,gmag,rmag"]
        for name, seq in zip(self.names, self.seqs, strict=True):
            rows.append(f"{name},{seq},1.2345678,18.5,18.0")
        self.parent = root / "Table2.txt.zip"
        with zipfile.ZipFile(self.parent, "w") as archive:
            archive.writestr("Table2.txt", "\n".join(rows) + "\n")

        self.published = root / "published_table4.dat"
        published = ["#ZTF\tID", "#---\t---"]
        published += [
            f"{name}\t{seq}"
            for name, seq in list(zip(self.names, self.seqs, strict=True))[
                : self.published_count
            ]
        ]
        self.published.write_text("\n".join(published) + "\n", encoding="utf-8")

        for band in ("g", "r"):
            header = f"SourceID,e_{band}mag,{band}mag"
            body = [header]
            for seq in self.seqs:
                body.extend([f"{seq},0.10,18.0"] * 3)
            (root / band / f"ztf2{band}.csv").write_text(
                "\n".join(body) + "\n", encoding="utf-8"
            )

    def run(self, output: Path) -> int:
        # main() reads sys.argv, so drive it the way the workflow does.
        argv = [
                "--parent", str(self.parent),
                "--g", str(self.root / "g"),
                "--r", str(self.root / "r"),
                "--published", str(self.published),
                "--output", str(output),
            "--expect-parent-count", str(len(self.names)),
        ]  # fmt: skip
        previous = sys.argv
        sys.argv = ["diagnose_cpvs_selection.py", *argv]
        try:
            return main()
        finally:
            sys.argv = previous


def _reject(token: str):  # pragma: no cover - only raises
    raise AssertionError(f"non-standard JSON literal present: {token}")


def test_diagnostic_runs_and_writes_a_report(tmp_path: Path):
    fixture = _Fixture(tmp_path)
    output = tmp_path / "selection_diagnostics.json"
    assert fixture.run(output) == 0
    assert output.is_file()


def test_output_is_strict_rfc8259_json(tmp_path: Path):
    """json.loads must succeed with NaN/Infinity rejected.

    Python's encoder emits bare NaN and Infinity by default, which are not JSON
    literals. Anything parsing this artifact outside Python would reject them, so
    the test parses with parse_constant set to raise.
    """
    fixture = _Fixture(tmp_path)
    output = tmp_path / "selection_diagnostics.json"
    fixture.run(output)
    text = output.read_text(encoding="utf-8")

    payload = json.loads(text, parse_constant=_reject)
    assert set(payload) == {
        "baseline_1p085",
        "baseline_1p0",
        "baseline_plus_mag206",
        "baseline_plus_rmag206",
    }
    for token in ("NaN", "Infinity", "-Infinity"):
        assert token not in text


def test_the_strict_encoder_guard_is_load_bearing():
    """Prove allow_nan=False changes behaviour, rather than being decoration.

    Without it Python writes `Infinity`; with it the write fails. That difference
    is the entire fix.
    """
    payload = {"snr": float("inf")}
    assert "Infinity" in json.dumps(payload)
    with pytest.raises(ValueError, match="Out of range float values"):
        json.dumps(payload, allow_nan=False)


def test_published_membership_uses_names_not_the_internal_id_column(tmp_path: Path):
    """Seq skips 3, so an ordinal-derived join would select the wrong objects.

    Published names are the first five, i.e. Seq {1,2,4,5,6}. Candidate-only must
    therefore be Seq {7,8,9} — three objects. If SourceID were taken from row
    position the mapping would shift and the counts would differ.
    """
    fixture = _Fixture(tmp_path)
    output = tmp_path / "selection_diagnostics.json"
    fixture.run(output)
    payload = json.loads(output.read_text(encoding="utf-8"))

    for name, block in payload.items():
        assert block["count"] == len(fixture.seqs), name
        assert block["published_intersection"] == fixture.published_count, name
        assert block["candidate_only"] == len(fixture.seqs) - fixture.published_count
        assert block["published_only"] == 0


def test_unmapped_published_name_is_refused(tmp_path: Path):
    fixture = _Fixture(tmp_path)
    fixture.published.write_text(
        "#ZTF\tID\n#---\t---\nZTFJ999999.00+000000.0\t1\n", encoding="utf-8"
    )
    with pytest.raises(ValueError, match="absent from the parent"):
        fixture.run(tmp_path / "out.json")


def test_parent_count_guard_is_fail_closed_by_default(tmp_path: Path):
    """The default guard must still be the published 781,602."""
    fixture = _Fixture(tmp_path)
    argv = [
        "--parent", str(fixture.parent),
        "--g", str(fixture.root / "g"),
        "--r", str(fixture.root / "r"),
        "--published", str(fixture.published),
        "--output", str(tmp_path / "out.json"),
    ]  # fmt: skip
    previous = sys.argv
    sys.argv = ["diagnose_cpvs_selection.py", *argv]
    try:
        with pytest.raises(ValueError, match="expected 781602 parent SourceIDs"):
            main()
    finally:
        sys.argv = previous


def test_parent_map_reads_the_zenodo_comma_csv(tmp_path: Path):
    """The heavy validation feeds a comma-separated Zenodo CSV, not a TSV."""
    path = tmp_path / "Table2.csv"
    path.write_text(
        "ID,Seq,Per\nZTFJ000001.00+000000.0,1,1.0\nZTFJ000002.00+000000.0,2,1.0\n",
        encoding="utf-8",
    )
    assert read_parent_name_map(path) == {
        "ZTFJ000001.00+000000.0": 1,
        "ZTFJ000002.00+000000.0": 2,
    }


def test_parent_map_reads_the_vizier_tsv(tmp_path: Path):
    path = tmp_path / "Table2.tsv"
    path.write_text("#ID\tSeq\tPer\nZTFJ000001.00+000000.0\t1\t1.0\n", encoding="utf-8")
    assert read_parent_name_map(path) == {"ZTFJ000001.00+000000.0": 1}


def test_parent_map_reads_a_zip_archive(tmp_path: Path):
    path = tmp_path / "Table2.txt.zip"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("Table2.txt", "ID,Seq\nZTFJ000001.00+000000.0,7\n")
    assert read_parent_name_map(path) == {"ZTFJ000001.00+000000.0": 7}
