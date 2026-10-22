from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from scripts.verify_cpvs_metadata_predicate import main


def _write_inputs(
    tmp_path: Path,
    *,
    second_object_metadata: tuple[str, str, str, str] = ("15.0", "14.0", "1.2", "1.3"),
) -> tuple[Path, Path, Path, Path]:
    parent = tmp_path / "parent_metadata.tsv"
    parent.write_text(
        "# VizieR metadata export\n"
        "Seq\tgmag\trmag\tPer-g\tPer-r\n"
        "------\t------\t------\t------\t------\n"
        f"10\t16.0\t15.0\t1.0\t1.1\n"
        f"20\t{second_object_metadata[0]}\t{second_object_metadata[1]}\t"
        f"{second_object_metadata[2]}\t{second_object_metadata[3]}\n"
        "30\t0\t14.0\t0\t1.4\n",
        encoding="utf-8",
    )
    candidates = tmp_path / "selected.tsv"
    candidates.write_text("SourceID\n10\n20\n30\n", encoding="utf-8")
    selection = tmp_path / "selection_diagnostics.json"
    selection.write_text(
        json.dumps({"candidate_only_all_objects": [{"source_id": 30}]}),
        encoding="utf-8",
    )
    audit = tmp_path / "membership_audit.json"
    audit.write_text(
        json.dumps(
            {
                "candidate_count": 3,
                "published_count": 2,
                "candidate_only_count": 1,
                "published_only_count": 0,
            }
        ),
        encoding="utf-8",
    )
    return parent, candidates, selection, audit


def test_metadata_predicate_verifier_reproduces_exact_diagnostic_set(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    parent, candidates, selection, audit = _write_inputs(tmp_path)
    output_json = tmp_path / "out" / "report.json"
    output_csv = tmp_path / "out" / "candidate_only.csv"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "verify_cpvs_metadata_predicate.py",
            "--parent-metadata",
            str(parent),
            "--candidates",
            str(candidates),
            "--selection-diagnostics",
            str(selection),
            "--membership-audit",
            str(audit),
            "--output-json",
            str(output_json),
            "--output-csv",
            str(output_csv),
        ],
    )

    assert main() == 0
    report = json.loads(output_json.read_text(encoding="utf-8"))
    assert report["four_field_filtered_set_equals_published_reference"] is True
    assert report["four_field_filtered_candidate_count"] == 2
    assert report["four_field_filtered_candidate_only_count"] == 0
    assert report["candidate_only_partition"] == {"both_pairs_incomplete": 1}
    assert output_csv.is_file()


def test_metadata_predicate_verifier_fails_if_diagnostic_does_not_match_reference(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    parent, candidates, selection, audit = _write_inputs(
        tmp_path, second_object_metadata=("0", "14.0", "0", "1.3")
    )
    output_json = tmp_path / "out" / "report.json"
    output_csv = tmp_path / "out" / "candidate_only.csv"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "verify_cpvs_metadata_predicate.py",
            "--parent-metadata",
            str(parent),
            "--candidates",
            str(candidates),
            "--selection-diagnostics",
            str(selection),
            "--membership-audit",
            str(audit),
            "--output-json",
            str(output_json),
            "--output-csv",
            str(output_csv),
        ],
    )

    with pytest.raises(ValueError, match="does not equal"):
        main()
