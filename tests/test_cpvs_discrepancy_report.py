from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from ztf_classifier.validation.cpvs_discrepancy_report import (
    build_cpvs_discrepancy_report,
    read_ids,
)


def write_file(path: Path, content: str) -> Path:
    path.write_text(content, encoding="utf-8")
    return path


def make_inputs(tmp_path: Path):
    parent = write_file(
        tmp_path / "parent.tsv",
        "SourceID\tgmag\trmag\tPer-g\tPer-r\n"
        "1\t15\t16\t0.5\t0.6\n"
        "2\t\t16\t0.5\t0.6\n"
        "3\t15\t16\t\t0.6\n"
        "4\t\t\t\t\n",
    )
    candidates = write_file(
        tmp_path / "candidates.tsv", "SourceID\n1\n2\n3\n4\n"
    )
    published = write_file(tmp_path / "published.tsv", "ID\n1\n")
    return parent, candidates, published


def test_report_exports_every_candidate_only_id_and_explicit_unknowns(
    tmp_path: Path,
):
    parent, candidates, published = make_inputs(tmp_path)
    output = tmp_path / "report"
    result = build_cpvs_discrepancy_report(
        parent_metadata=parent,
        candidate_ids=candidates,
        published_ids=published,
        output_dir=output,
        source_revision="test-sha",
    )
    assert result["counts"]["candidate_only_objects"] == 3
    assert result["counts"]["published_only_objects"] == 0
    assert result["source_revision"] == "test-sha"
    with (output / "cpvs_candidate_only_objects.csv").open(
        encoding="utf-8", newline=""
    ) as stream:
        rows = list(csv.DictReader(stream))
    assert {row["SourceID"] for row in rows} == {"2", "3", "4"}
    assert all(row["raw_lightcurve_status"] == "NOT_ASSESSED" for row in rows)
    assert all(
        row["external_crossmatch_status"] == "NOT_ASSESSED" for row in rows
    )
    manifest = json.loads(
        (output / "cpvs_discrepancy_manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["interpretation"]["historical_publisher_rule"] == "UNRESOLVED"
    assert (output / "cpvs_candidate_only_objects.html").exists()
    assert (output / "cpvs_discrepancy_report.md").exists()


def test_report_fails_closed_when_candidate_lacks_parent_provenance(
    tmp_path: Path,
):
    parent, _, published = make_inputs(tmp_path)
    candidates = write_file(tmp_path / "bad.tsv", "SourceID\n999\n")
    with pytest.raises(ValueError, match="lack parent provenance"):
        build_cpvs_discrepancy_report(
            parent_metadata=parent,
            candidate_ids=candidates,
            published_ids=published,
            output_dir=tmp_path / "out",
        )


def test_duplicate_object_ids_are_rejected(tmp_path: Path):
    path = write_file(tmp_path / "duplicates.tsv", "SourceID\n1\n1\n")
    with pytest.raises(ValueError, match="duplicate object IDs"):
        read_ids(path)


def test_required_diagnostic_fields_are_mandatory(tmp_path: Path):
    parent = write_file(tmp_path / "parent.tsv", "SourceID\tgmag\trmag\n1\t15\t16\n")
    candidates = write_file(tmp_path / "candidates.tsv", "SourceID\n1\n")
    published = write_file(tmp_path / "published.tsv", "SourceID\n2\n")
    with pytest.raises(ValueError, match="missing required fields"):
        build_cpvs_discrepancy_report(
            parent_metadata=parent,
            candidate_ids=candidates,
            published_ids=published,
            output_dir=tmp_path / "out",
        )
