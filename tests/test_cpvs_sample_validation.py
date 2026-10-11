from __future__ import annotations

import csv
import json

from scripts.validate_cpvs_samples import read_decisions, sha256, stratified_sample


def test_stratified_sample_is_deterministic_and_covers_both_strata() -> None:
    parent = {str(value) for value in range(1, 101)}
    published = {str(value) for value in range(1, 21)}
    first, counts = stratified_sample(parent, published, 30, 20261012)
    second, counts_again = stratified_sample(parent, published, 30, 20261012)

    assert first == second
    assert counts == counts_again
    assert len(first) == len(set(first)) == 30
    assert set(first) & published
    assert set(first) - published
    assert counts["published_reference_member"] + counts["outside_published_reference"] == 30


def test_read_decisions_keys_by_complete_source_id_and_detects_duplicates(tmp_path) -> None:
    path = tmp_path / "decisions.csv"
    path.write_text("SourceID,selected\n12,true\n130,false\n", encoding="utf-8")
    assert read_decisions(path) == {"12": True, "130": False}
    assert len(sha256(path)) == 64


def test_decision_csv_rejects_duplicate_source_ids(tmp_path) -> None:
    path = tmp_path / "duplicates.csv"
    path.write_text("SourceID,selected\n12,true\n12,false\n", encoding="utf-8")
    try:
        read_decisions(path)
    except ValueError as exc:
        assert "duplicate object decision" in str(exc)
    else:
        raise AssertionError("duplicate SourceID decisions must fail closed")
