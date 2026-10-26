from __future__ import annotations

import csv
import hashlib
import json
import zipfile
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
    assert set(manifest["outputs"]) == {
        "csv",
        "html",
        "object_detail_html",
        "summary_json",
        "markdown",
    }
    for output_record in manifest["outputs"].values():
        generated = output / output_record["path"]
        assert generated.is_file()
        digest = hashlib.sha256(generated.read_bytes()).hexdigest()
        assert digest == output_record["sha256"]
    table = (output / "cpvs_candidate_only_objects.html").read_text(encoding="utf-8")
    assert "href='cpvs_object_detail.html#2'" in table
    detail = (output / "cpvs_object_detail.html").read_text(encoding="utf-8")
    assert "No matching object in this report." in detail
    assert "candidate_only_not_in_published_table4" in detail
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
            source_revision="test-sha",
        )


def test_report_requires_a_recorded_source_revision(tmp_path: Path):
    parent, candidates, published = make_inputs(tmp_path)
    with pytest.raises(ValueError, match="source_revision must identify"):
        build_cpvs_discrepancy_report(
            parent_metadata=parent,
            candidate_ids=candidates,
            published_ids=published,
            output_dir=tmp_path / "out",
            source_revision="UNRECORDED",
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
            source_revision="test-sha",
        )


def test_report_accepts_vizier_tsv_metadata_units_and_separator(tmp_path: Path):
    parent = write_file(
        tmp_path / "parent_vizier.tsv",
        "# VizieR export\n"
        "#Table: J/ApJS/249/18/table2\n"
        "Seq\tPer\tgmag\trmag\tPer-g\tPer-r\n"
        " \td\tmag\tmag\td\td\n"
        "------\t---\t----\t----\t-----\t-----\n"
        "1\t0.5\t15\t16\t0.5\t0.6\n"
        "2\t0.6\t\t16\t0.6\t0.7\n",
    )
    candidates = write_file(tmp_path / "candidates.tsv", "SourceID\n1\n2\n")
    published = write_file(
        tmp_path / "published_vizier.tsv",
        "# Published reference export\n"
        "Name\tSeq\n"
        " \t \n"
        "------\t---\n"
        "ZTFJ000000.00+000000.0\t1\n",
    )
    result = build_cpvs_discrepancy_report(
        parent_metadata=parent,
        candidate_ids=candidates,
        published_ids=published,
        output_dir=tmp_path / "vizier-report",
        source_revision="test-vizier-source",
    )
    assert result["counts"]["parent_metadata_objects"] == 2
    assert result["counts"]["published_reference_objects"] == 1
    assert result["counts"]["candidate_only_objects"] == 1
    assert result["counts"]["published_only_objects"] == 0



def test_published_table4_uses_ztf_name_not_internal_id(tmp_path: Path):
    parent = write_file(
        tmp_path / "parent.tsv",
        "Seq\tID\tgmag\trmag\tPer-g\tPer-r\n"
        "1\tZTFJ000000.00+000000.0\t15\t16\t0.5\t0.6\n"
        "2\tZTFJ000001.00+000001.0\t\t16\t0.5\t0.6\n",
    )
    candidates = write_file(tmp_path / "candidates.tsv", "SourceID\n1\n2\n")
    # Table 4's numeric ID is intentionally unrelated to parent Seq. The ZTF
    # object-name crosswalk is the authoritative membership join.
    published = write_file(
        tmp_path / "table4.tsv",
        "ID\tZTF\n"
        "99999\tZTF J000000.00+000000.0\n",
    )
    result = build_cpvs_discrepancy_report(
        parent_metadata=parent,
        candidate_ids=candidates,
        published_ids=published,
        output_dir=tmp_path / "report",
        source_revision="test-sha",
    )
    assert result["counts"]["intersection_objects"] == 1
    assert result["counts"]["candidate_only_objects"] == 1
    with (tmp_path / "report" / "cpvs_candidate_only_objects.csv").open(
        encoding="utf-8", newline=""
    ) as stream:
        rows = list(csv.DictReader(stream))
    assert [row["SourceID"] for row in rows] == ["2"]


def test_table4_ztf_names_fail_closed_without_parent_name_crosswalk(
    tmp_path: Path,
):
    parent, candidates, _ = make_inputs(tmp_path)
    published = write_file(
        tmp_path / "table4.tsv",
        "ID\tZTF\n99999\tZTFJ000000.00+000000.0\n",
    )
    with pytest.raises(ValueError, match="parent metadata has no object-name column"):
        build_cpvs_discrepancy_report(
            parent_metadata=parent,
            candidate_ids=candidates,
            published_ids=published,
            output_dir=tmp_path / "out",
            source_revision="test-sha",
        )



def test_report_reads_authoritative_fixed_width_table2_zip(tmp_path: Path) -> None:
    def fixed_row(
        name: str, seq: int, gmag: str, rmag: str, per_g: str, per_r: str
    ) -> str:
        row = [" "] * 130
        row[0:22] = list(name.ljust(22)[:22])
        row[23:29] = list(str(seq).rjust(6))
        row[89:95] = list(gmag.rjust(6)[:6])
        row[96:102] = list(rmag.rjust(6)[:6])
        row[103:116] = list(per_g.rjust(13)[:13])
        row[117:130] = list(per_r.rjust(13)[:13])
        return "".join(row) + "\n"

    names = [
        "ZTFJ000000.00+000000.0",
        "ZTFJ000001.00+000001.0",
        "ZTFJ000002.00+000002.0",
    ]
    parent_archive = tmp_path / "Table2.txt.zip"
    table_text = "Table 2 metadata\n" + "".join(
        [
            fixed_row(names[0], 1, "15.0", "16.0", "0.5", "0.6"),
            fixed_row(names[1], 2, "15.1", "16.1", "0.7", "0.8"),
            fixed_row(names[2], 4, "", "17.0", "0.9", "1.0"),
        ]
    )
    with zipfile.ZipFile(
        parent_archive, "w", compression=zipfile.ZIP_DEFLATED
    ) as archive:
        archive.writestr("Table2.txt", table_text)

    parent_evidence = write_file(
        tmp_path / "Table2.txt.zip.evidence.json", '{"sha256":"fixture-parent"}\n'
    )
    candidates = write_file(tmp_path / "candidates.tsv", "SourceID\n1\n2\n4\n")
    candidate_evidence = write_file(
        tmp_path / "candidates.tsv.evidence.json", '{"sha256":"fixture-candidate"}\n'
    )
    # Table 4 internal IDs are intentionally unrelated; join by the ZTF name.
    published = write_file(
        tmp_path / "table4.tsv",
        "ID\tZTF\n9001\tZTFJ000000.00+000000.0\n"
        "9002\tZTFJ000001.00+000001.0\n",
    )
    output = tmp_path / "report"
    result = build_cpvs_discrepancy_report(
        parent_metadata=parent_archive,
        candidate_ids=candidates,
        published_ids=published,
        output_dir=output,
        source_revision="fixed-width-test-revision",
        report_code_revision="report-code-test-revision",
        parent_evidence=parent_evidence,
        candidate_evidence=candidate_evidence,
        expected_parent_count=3,
    )

    assert result["counts"] == {
        "parent_metadata_objects": 3,
        "candidate_objects": 3,
        "published_reference_objects": 2,
        "intersection_objects": 2,
        "candidate_only_objects": 1,
        "published_only_objects": 0,
        "candidate_only_missing_parent_provenance": 0,
    }
    assert result["diagnostic_group_counts"] == {
        "valid_periods_gmag_incomplete": 1
    }
    assert result["report_code_revision"] == "report-code-test-revision"
    assert set(result["source_evidence_files"]) == {"parent_evidence", "candidate_evidence"}
    assert result["source_evidence_files"]["parent_evidence"]["sha256"] == hashlib.sha256(
        parent_evidence.read_bytes()
    ).hexdigest()
    assert result["source_context"]["parent_metadata"]["identifier_field"] == "Seq"
    assert result["source_context"]["published_ids"]["membership_join"] == (
        "normalized ZTF object name crosswalk to Table 2 Seq"
    )
    assert result["source_files"]["parent_metadata"]["sha256"] == hashlib.sha256(
        parent_archive.read_bytes()
    ).hexdigest()

    from ztf_classifier.validation.cpvs_discrepancy_report import read_parent_metadata

    invalid_seq_archive = tmp_path / "invalid-seq.zip"
    with zipfile.ZipFile(invalid_seq_archive, "w") as archive:
        archive.writestr(
            "Table2.txt",
            fixed_row(names[0], 781605, "15.0", "16.0", "0.5", "0.6"),
        )
    with pytest.raises(ValueError, match="outside the documented range"):
        read_parent_metadata(invalid_seq_archive, expected_parent_count=1)

    duplicate_seq_archive = tmp_path / "duplicate-seq.zip"
    with zipfile.ZipFile(duplicate_seq_archive, "w") as archive:
        archive.writestr(
            "Table2.txt",
            fixed_row(names[0], 1, "15.0", "16.0", "0.5", "0.6")
            + fixed_row(names[1], 1, "15.1", "16.1", "0.7", "0.8"),
        )
    with pytest.raises(ValueError, match="duplicate authoritative Seq"):
        read_parent_metadata(duplicate_seq_archive, expected_parent_count=2)
