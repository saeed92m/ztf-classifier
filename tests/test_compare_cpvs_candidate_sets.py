from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import pytest

from scripts.compare_cpvs_candidate_sets import compare_candidate_sets


def test_candidate_set_comparison_records_added_removed_ids_and_hashes(
    tmp_path: Path,
) -> None:
    previous = tmp_path / "previous.tsv"
    current = tmp_path / "current.tsv"
    previous.write_text("SourceID\n1\n2\n3\n", encoding="utf-8")
    current.write_text("SourceID\n2\n3\n4\n5\n", encoding="utf-8")

    previous_diagnostic = tmp_path / "previous.diagnostic.json"
    previous_diagnostic.write_text(
        '{"code_version":"previous-code-sha","candidate_count":3}\n',
        encoding="utf-8",
    )
    parent = tmp_path / "parent.csv"
    parent.write_text(
        "SourceID,ID,gmag,rmag,Per_g,Per_r\n"
        "1,ZTF1,15.0,16.0,0.5,0.6\n"
        "2,ZTF2,15.1,16.1,0.7,0.8\n"
        "3,ZTF3,15.2,16.2,0.9,1.0\n"
        "4,ZTF4,15.3,16.3,1.1,1.2\n"
        "5,ZTF5,15.4,16.4,1.3,1.4\n",
        encoding="utf-8",
    )
    published = tmp_path / "published.tsv"
    published.write_text(
        "ID\tZTF\n1001\tZTF1\n1002\tZTF2\n",
        encoding="utf-8",
    )
    output = tmp_path / "comparison"
    result = compare_candidate_sets(
        previous_candidate_ids=previous,
        current_candidate_ids=current,
        previous_source_run_id="38635891449",
        current_source_run_id="40397098709",
        output_dir=output,
        previous_diagnostic=previous_diagnostic,
        parent_metadata=parent,
        published_ids=published,
    )

    assert result["previous_candidate_ids"]["objects"] == 3
    assert result["current_candidate_ids"]["objects"] == 4
    assert result["shared_objects"] == 2
    assert result["added_in_current_ids"] == ["4", "5"]
    assert result["removed_from_current_ids"] == ["1"]
    assert result["set_equal"] is False
    assert result["previous_candidate_ids"]["sha256"] == hashlib.sha256(
        previous.read_bytes()
    ).hexdigest()
    assert result["previous_candidate_diagnostic"]["metadata"]["code_version"] == (
        "previous-code-sha"
    )
    assert result["previous_candidate_diagnostic"]["sha256"] == hashlib.sha256(
        previous_diagnostic.read_bytes()
    ).hexdigest()
    with (output / "cpvs_candidate_set_change.csv").open(
        encoding="utf-8", newline=""
    ) as stream:
        rows = list(csv.DictReader(stream))
    assert [row["SourceID"] for row in rows] == ["4", "5", "1"]
    removed = rows[-1]
    assert removed["change_type"] == "removed_from_current"
    assert removed["parent_record_found"] == "True"
    assert removed["parent_ZTF_name"] == "ZTF1"
    assert removed["published_member"] == "True"
    assert rows[0]["published_member"] == "False"
    assert result["parent_metadata"]["objects"] == 5
    assert result["published_reference"]["objects"] == 2
    summary = json.loads(
        (output / "cpvs_candidate_set_change.json").read_text(encoding="utf-8")
    )
    assert summary["current_source_run_id"] == "40397098709"
    assert summary["change_csv"]["rows"] == 3


def test_candidate_set_comparison_fails_closed_on_duplicate_ids(
    tmp_path: Path,
) -> None:
    previous = tmp_path / "previous.tsv"
    current = tmp_path / "current.tsv"
    previous.write_text("SourceID\n1\n1\n", encoding="utf-8")
    current.write_text("SourceID\n1\n2\n", encoding="utf-8")

    with pytest.raises(ValueError, match="duplicate object IDs"):
        compare_candidate_sets(
            previous_candidate_ids=previous,
            current_candidate_ids=current,
            previous_source_run_id="previous-run",
            current_source_run_id="current-run",
            output_dir=tmp_path / "comparison",
        )
