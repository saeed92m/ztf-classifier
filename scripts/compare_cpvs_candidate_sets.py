"""Compare immutable CPVS candidate-ID lists across source-backed workflow runs."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from ztf_classifier.validation.cpvs_discrepancy_report import (
    published_membership_ids,
    read_ids,
    read_parent_metadata,
    sha256_file,
)


def _reject_nonfinite_json_constant(value: str) -> None:
    raise ValueError(f"non-standard JSON constant is not allowed: {value}")


def compare_candidate_sets(
    *,
    previous_candidate_ids: str | Path,
    current_candidate_ids: str | Path,
    previous_source_run_id: str,
    current_source_run_id: str,
    output_dir: str | Path,
    previous_diagnostic: str | Path | None = None,
    parent_metadata: str | Path | None = None,
    published_ids: str | Path | None = None,
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
    if (parent_metadata is None) != (published_ids is None):
        raise ValueError("parent metadata and published IDs must be supplied together")
    parent_rows: list[dict[str, str]] = []
    parent_id_key: str | None = None
    parent_name_key: str | None = None
    published_members: set[str] = set()
    parent_record: dict[str, Any] | None = None
    published_record: dict[str, Any] | None = None
    if parent_metadata is not None and published_ids is not None:
        parent_path = Path(parent_metadata)
        published_path = Path(published_ids)
        parent_rows, parent_id_key = read_parent_metadata(parent_path)
        parent_name_aliases = {
            "id",
            "ztf",
            "ztfname",
            "ztf_name",
            "name",
            "object_name",
        }
        parent_name_key = next(
            (key for key in parent_rows[0] if key.lower() in parent_name_aliases),
            None,
        )
        if parent_name_key is None:
            raise ValueError(
                "parent metadata has no ZTF object-name field for crosswalk"
            )
        published_members = published_membership_ids(
            published_path,
            parent_rows,
            parent_id_key,
        )
        parent_record = {
            "path": str(parent_path),
            "sha256": sha256_file(parent_path),
            "objects": len(parent_rows),
        }
        published_record = {
            "path": str(published_path),
            "sha256": sha256_file(published_path),
            "objects": len(published_members),
        }
    previous_diagnostic_record: dict[str, Any] | None = None
    if previous_diagnostic is not None:
        diagnostic_path = Path(previous_diagnostic)
        if not diagnostic_path.is_file():
            raise ValueError(
                f"previous candidate diagnostic not found: {diagnostic_path}"
            )
        try:
            diagnostic_payload = json.loads(
                diagnostic_path.read_text(encoding="utf-8"),
                parse_constant=_reject_nonfinite_json_constant,
            )
        except (UnicodeDecodeError, ValueError) as exc:
            raise ValueError(
                f"invalid previous candidate diagnostic JSON: {exc}"
            ) from exc
        if not isinstance(diagnostic_payload, dict):
            raise ValueError("previous candidate diagnostic must be a JSON object")
        previous_diagnostic_record = {
            "path": str(diagnostic_path),
            "sha256": sha256_file(diagnostic_path),
            "bytes": diagnostic_path.stat().st_size,
            "metadata": diagnostic_payload,
        }

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    csv_path = out / "cpvs_candidate_set_change.csv"
    def metadata_for(object_id: str, change_type: str) -> dict[str, Any]:
        parent_row = next(
            (
                row
                for row in parent_rows
                if parent_id_key is not None and row.get(parent_id_key) == object_id
            ),
            {},
        )
        values = {key.lower(): value for key, value in parent_row.items()}
        return {
            "change_type": change_type,
            "SourceID": object_id,
            "parent_record_found": bool(parent_row),
            "parent_ZTF_name": (
                parent_row.get(parent_name_key, "") if parent_name_key else ""
            ),
            "published_member": object_id in published_members,
            "gmag": values.get("gmag", ""),
            "rmag": values.get("rmag", ""),
            "Per_g": values.get("per_g", ""),
            "Per_r": values.get("per_r", ""),
        }

    change_rows = [
        metadata_for(object_id, "added_in_current") for object_id in added
    ] + [metadata_for(object_id, "removed_from_current") for object_id in removed]
    with csv_path.open("w", encoding="utf-8", newline="") as stream:
        fieldnames = [
            "change_type",
            "SourceID",
            "parent_record_found",
            "parent_ZTF_name",
            "published_member",
            "gmag",
            "rmag",
            "Per_g",
            "Per_r",
        ]
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(change_rows)

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
        "previous_candidate_diagnostic": previous_diagnostic_record,
        "parent_metadata": parent_record,
        "published_reference": published_record,
        "changed_objects_preview": change_rows[:100],
        "shared_objects": len(shared),
        "added_in_current_count": len(added),
        "removed_from_current_count": len(removed),
        "set_equal": previous == current,
        "added_in_current_ids_preview": added[:100],
        "removed_from_current_ids_preview": removed[:100],
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
    parser.add_argument("--previous-diagnostic", type=Path)
    parser.add_argument("--parent-metadata", type=Path)
    parser.add_argument("--published-ids", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    result = compare_candidate_sets(
        previous_candidate_ids=args.previous_candidate_ids,
        current_candidate_ids=args.current_candidate_ids,
        previous_source_run_id=args.previous_source_run_id,
        current_source_run_id=args.current_source_run_id,
        output_dir=args.output_dir,
        previous_diagnostic=args.previous_diagnostic,
        parent_metadata=args.parent_metadata,
        published_ids=args.published_ids,
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
