from __future__ import annotations

import json
from pathlib import Path

from scripts.audit_cpvs_snr_guard_impact import audit


def _write(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def test_nonfinite_snr_guard_exactly_explains_added_candidate_ids(tmp_path: Path) -> None:
    g_dir = tmp_path / "g"
    r_dir = tmp_path / "r"
    _write(
        g_dir / "g.txt",
        "SourceID\tHJD\tgmag\te_gmag\tg_flag\n"
        "194424\t2450000.1\t18.0\t0.1\t0\n"
        "195452\t2450000.2\t19.0\t0.1\t0\n",
    )
    _write(
        r_dir / "r.txt",
        "SourceID\tHJD\trmag\te_rmag\tr_flag\n"
        "194424\t2450000.1\t18.1\t\t0\n"
        "195452\t2450000.2\t19.1\tNaN\t0\n",
    )
    changes = _write(
        tmp_path / "changes.csv",
        "change_type,SourceID,parent_record_found,parent_ZTF_name,published_member\n"
        "added_in_current,194424,True,ZTFJ111832.86+125702.8,False\n"
        "added_in_current,195452,True,ZTFJ114217.06+145351.4,False\n",
    )
    current = _write(tmp_path / "current.tsv", "SourceID\n194424\n195452\n")
    previous = _write(tmp_path / "previous.tsv", "SourceID\n")
    parent = _write(tmp_path / "Table2.txt.zip", "fixture parent bytes\n")
    output = tmp_path / "out" / "attribution.json"

    result = audit(
        g_dir=g_dir,
        r_dir=r_dir,
        changes_path=changes,
        current_candidates_path=current,
        previous_candidates_path=previous,
        output_path=output,
        source_run_id="current-run",
        previous_run_id="previous-run",
        parent_table2_path=parent,
        raw_g_md5="g-md5",
        raw_r_md5="r-md5",
    )

    assert result["status"] == "CONFIRMED_NONFINITE_SNR_GUARD"
    assert output.is_file()
    persisted = json.loads(output.read_text(encoding="utf-8"))
    assert persisted["changed_object_count"] == 2
    assert all(
        row["current_candidate_list_member"]
        and not row["previous_candidate_list_member"]
        and row["replay_candidate_with_regressed_guard"]
        and not row["replay_candidate_with_finite_guard"]
        and row["finite_snr_guard_explains_membership_change"]
        for row in persisted["objects"]
    )
    assert all(row["r_band"]["nonfinite_snr_rows"] > 0 for row in persisted["objects"])
