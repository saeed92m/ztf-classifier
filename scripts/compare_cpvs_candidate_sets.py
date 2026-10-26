"""Compare immutable CPVS candidate-ID lists across source-backed workflow runs."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from ztf_classifier.validation.cpvs_discrepancy_report import read_ids, sha256_file


def compare_candidate_sets(
    *,
    previous_candidate_ids: str | Path,
    current_candidate_ids: str | Path,
    previous_source_run_id: str,
    current_source_run_id: str,
    output_dir: str | Path,
) -> dict[str, Any]:
    previous_path = Path(previous_candidate_ids)
    current_path = Path(current_candidate_ids)
    if not previous_source_run_id.strip() or not current_source_run_id.strip():
        raise ValueError("both source run IDs are required")
    previous = read_ids(previous_path)
    current = read_ids(current_path)
    added = sorted(current - previous, key=int)
    removed = sorted(previous - current, key=int)
    shared = previous & current

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    csv_path = out / "cpvs_candidate_set_change.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["change_type", "SourceID"])
        writer.writeheader()
        writer.writerows(
            [{"change_type": "added_in_current", "SourceID": object_id} for object_id in added]
            + [{"change_type": "removed_from_current", "SourceID": object_id} for object_id in removed]
        )

    result: dict[str, Any] = {
        "comparison_schema": "cpvs-candidate-set-diff/1.0",
        "previous_source_run_id": previous_source_run_id,
        "current_source_run_id": current_source_run_id,
        "previous_candidate_ids": {
            "path": str(previous_path),
            "sha256": sha256_file(previous_path),
            "objects": len(previous),
        },
        "current_candidate_ids": {
            "path": str(current_path),
            "sha256": sha256_file(current_path),
            "objects": len(current),
        },
        "shared_objects": len(shared),
        "added_in_current_count": len(added),
        "removed_from_current_count": len(removed),
        "set_equal": previous == current,
        "added_in_current_ids": added,
        "removed_from_current_ids": removed,
        "change_csv": {
            "path": csv_path.name,
            "sha256": sha256_file(csv_path),
            "rows": len(added) + len(removed),
        },
    }
    (out / "cpvs_candidate_set_change.json").write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--previous-candidate-ids", type=Path, required=True)
    parser.add_argument("--current-candidate-ids", type=Path, required=True)
    parser.add_argument("--previous-source-run-id", required=True)
    parser.add_argument("--current-source-run-id", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    result = compare_candidate_sets(
        previous_candidate_ids=args.previous_candidate_ids,
        current_candidate_ids=args.current_candidate_ids,
        previous_source_run_id=args.previous_source_run_id,
        current_source_run_id=args.current_source_run_id,
        output_dir=args.output_dir,
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
