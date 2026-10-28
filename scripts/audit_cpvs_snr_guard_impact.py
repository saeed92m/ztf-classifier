"""Trace changed CPVS candidate IDs to raw rows and compare SNR guard semantics."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
from typing import Any

from ztf_classifier.validation.derivation import _iter_rows

SNR_FACTOR = 1.0857362047581296
FILE_SUFFIXES = {".csv", ".txt", ".dat", ".json", ".gz", ""}


def _key(row: dict[str, str], aliases: tuple[str, ...]) -> str:
    normalized = {key.strip().lower(): key for key in row}
    for alias in aliases:
        if alias.lower() in normalized:
            return normalized[alias.lower()]
    raise ValueError(f"none of {aliases!r} found; columns={tuple(row)}")


def _snr(raw_error: str) -> float:
    try:
        error = float(raw_error)
    except (TypeError, ValueError):
        return float("nan")
    if not math.isfinite(error) or error <= 0:
        return float("nan")
    return SNR_FACTOR / error


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_ids(path: Path) -> set[str]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream, delimiter="\t")
        if not reader.fieldnames or "SourceID" not in reader.fieldnames:
            raise ValueError(f"{path}: expected a SourceID TSV column")
        ids = [str(int(row["SourceID"])) for row in reader if row.get("SourceID", "").strip()]
    if len(ids) != len(set(ids)):
        raise ValueError(f"{path}: duplicate SourceID values")
    return set(ids)


def _read_changes(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    required = {"change_type", "SourceID"}
    if not rows or not required.issubset(rows[0]):
        raise ValueError(f"{path}: expected changed-object rows with {sorted(required)}")
    changed = [row for row in rows if row["change_type"] in {"added_in_current", "removed_from_current"}]
    for row in changed:
        if not row["SourceID"].isdigit():
            raise ValueError(f"{path}: invalid SourceID {row['SourceID']!r}")
    return changed


def _audit_band(root: Path, target_ids: set[str], band: str, threshold: float) -> dict[str, dict[str, Any]]:
    error_key_name = "e_gmag" if band == "g" else "e_rmag"
    mag_key_name = f"{band}mag"
    error_aliases = (error_key_name, "magerr", "mag_err", "error")
    results: dict[str, dict[str, Any]] = {
        oid: {
            "raw_rows_seen": 0,
            "invalid_error_rows": 0,
            "nonfinite_snr_rows": 0,
            "regressed_guard_qualifying_rows": 0,
            "finite_guard_qualifying_rows": 0,
            "regressed_guard_valid_magnitude_rows": 0,
            "finite_guard_valid_magnitude_rows": 0,
            "source_files": [],
            "examples": [],
        }
        for oid in target_ids
    }

    for path in sorted(item for item in root.rglob("*") if item.is_file() and item.suffix.lower() in FILE_SUFFIXES):
        try:
            iterator = _iter_rows(path, required_columns=("SourceID", error_key_name, mag_key_name))
            first = next(iterator, None)
            if first is None:
                continue
            id_key = _key(first, ("SourceID", "sourceid", "oid", "ztf_id"))
            err_key = _key(first, error_aliases)
            mag_key = _key(first, (mag_key_name,))
            try:
                flag_key = _key(first, (f"{band}_flag", "catflags", "flag"))
            except ValueError:
                flag_key = None
            try:
                time_key = _key(first, ("HJD", "MJD", "JD", "time"))
            except ValueError:
                time_key = None
            file_hits: set[str] = set()
            for record_index, row in enumerate(iter((first,)), start=1):
                del record_index, row
            for record_index, row in enumerate(_iter_rows(path, required_columns=("SourceID", error_key_name, mag_key_name)), start=1):
                oid_raw = row.get(id_key, "").strip()
                if not oid_raw.isdigit():
                    continue
                oid = str(int(oid_raw))
                if oid not in target_ids:
                    continue
                file_hits.add(oid)
                result = results[oid]
                result["raw_rows_seen"] += 1
                raw_error = row.get(err_key, "").strip()
                raw_mag = row.get(mag_key, "").strip()
                snr = _snr(raw_error)
                finite_error = math.isfinite(snr)
                if not finite_error:
                    result["invalid_error_rows"] += 1
                    result["nonfinite_snr_rows"] += 1
                regressed_qualifies = not (snr < threshold)
                finite_qualifies = finite_error and snr >= threshold
                if regressed_qualifies:
                    result["regressed_guard_qualifying_rows"] += 1
                if finite_qualifies:
                    result["finite_guard_qualifying_rows"] += 1
                try:
                    magnitude = float(raw_mag)
                except (TypeError, ValueError):
                    magnitude = float("nan")
                valid_magnitude = math.isfinite(magnitude) and magnitude != 0.0
                if regressed_qualifies and valid_magnitude:
                    result["regressed_guard_valid_magnitude_rows"] += 1
                if finite_qualifies and valid_magnitude:
                    result["finite_guard_valid_magnitude_rows"] += 1
                if len(result["examples"]) < 5:
                    result["examples"].append({
                        "source_file": str(path.relative_to(root)),
                        "record_index": record_index,
                        "time": row.get(time_key, "") if time_key else "",
                        "magnitude": raw_mag,
                        "magnitude_error": raw_error,
                        "snr": snr if math.isfinite(snr) else "NONFINITE",
                        "flag": row.get(flag_key, "") if flag_key else "",
                        "regressed_guard_qualifies": regressed_qualifies,
                        "finite_guard_qualifies": finite_qualifies,
                    })
            if file_hits:
                file_record = {
                    "path": str(path.relative_to(root)),
                    "sha256": _sha256(path),
                    "target_ids_found": sorted(file_hits, key=int),
                }
                for oid in file_hits:
                    results[oid]["source_files"].append(file_record)
        except (OSError, UnicodeError, ValueError, csv.Error):
            continue

    for result in results.values():
        unique_files: dict[str, dict[str, Any]] = {}
        for record in result["source_files"]:
            unique_files[record["path"]] = record
        result["source_files"] = list(unique_files.values())
    return results


def audit(
    *,
    g_dir: Path,
    r_dir: Path,
    changes_path: Path,
    current_candidates_path: Path,
    previous_candidates_path: Path,
    output_path: Path,
    source_run_id: str,
    previous_run_id: str,
    parent_sha256: str,
    current_candidate_sha256: str,
    previous_candidate_sha256: str,
    raw_g_md5: str,
    raw_r_md5: str,
) -> dict[str, Any]:
    changes = _read_changes(changes_path)
    target_ids = {str(int(row["SourceID"])) for row in changes}
    current_ids = _read_ids(current_candidates_path)
    previous_ids = _read_ids(previous_candidates_path)
    g = _audit_band(g_dir, target_ids, "g", 2.5)
    r = _audit_band(r_dir, target_ids, "r", 3.0)

    objects: list[dict[str, Any]] = []
    for change in changes:
        oid = str(int(change["SourceID"]))
        current_candidate = oid in current_ids
        previous_candidate = oid in previous_ids
        current_replay = (
            g[oid]["regressed_guard_valid_magnitude_rows"] > 0
            and r[oid]["regressed_guard_valid_magnitude_rows"] > 0
        )
        finite_replay = (
            g[oid]["finite_guard_valid_magnitude_rows"] > 0
            and r[oid]["finite_guard_valid_magnitude_rows"] > 0
        )
        guard_explains = (
            change["change_type"] == "added_in_current"
            and current_candidate
            and not previous_candidate
            and current_replay
            and not finite_replay
            and (
                g[oid]["regressed_guard_valid_magnitude_rows"] > g[oid]["finite_guard_valid_magnitude_rows"]
                or r[oid]["regressed_guard_valid_magnitude_rows"] > r[oid]["finite_guard_valid_magnitude_rows"]
            )
        )
        objects.append({
            "SourceID": oid,
            "change_type": change["change_type"],
            "published_member": change.get("published_member", ""),
            "parent_ZTF_name": change.get("parent_ZTF_name", ""),
            "current_candidate_list_member": current_candidate,
            "previous_candidate_list_member": previous_candidate,
            "replay_candidate_with_regressed_guard": current_replay,
            "replay_candidate_with_finite_guard": finite_replay,
            "finite_snr_guard_explains_membership_change": guard_explains,
            "g_band": g[oid],
            "r_band": r[oid],
        })

    all_explained = bool(objects) and all(
        obj["finite_snr_guard_explains_membership_change"] for obj in objects
    )
    payload: dict[str, Any] = {
        "schema": "cpvs-snr-guard-attribution/1.0",
        "status": "CONFIRMED_NONFINITE_SNR_GUARD" if all_explained else "NOT_CONFIRMED",
        "scope": "cross-run candidate-set changes only; does not resolve the full CPVS membership discrepancy",
        "source_run_id": source_run_id,
        "previous_source_run_id": previous_run_id,
        "parent_table2_sha256": parent_sha256,
        "current_candidate_ids_sha256": current_candidate_sha256,
        "previous_candidate_ids_sha256": previous_candidate_sha256,
        "changed_ids_csv_sha256": _sha256(changes_path),
        "raw_archive_md5": {"ztf2g": raw_g_md5, "ztf2r": raw_r_md5},
        "changed_object_count": len(objects),
        "objects": objects,
        "limitations": [
            "The finite-SNR guard attribution applies only to the changed candidate IDs in these two runs.",
            "The 11,604 candidate-only CPVS membership discrepancy remains unresolved.",
            "A successful guard attribution does not establish the publisher's historical selection rule or astrophysical ground truth."
        ],
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--g-dir", type=Path, required=True)
    parser.add_argument("--r-dir", type=Path, required=True)
    parser.add_argument("--changes", type=Path, required=True)
    parser.add_argument("--current-candidates", type=Path, required=True)
    parser.add_argument("--previous-candidates", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source-run-id", required=True)
    parser.add_argument("--previous-run-id", required=True)
    parser.add_argument("--parent-sha256", required=True)
    parser.add_argument("--current-candidate-sha256", required=True)
    parser.add_argument("--previous-candidate-sha256", required=True)
    parser.add_argument("--raw-g-md5", required=True)
    parser.add_argument("--raw-r-md5", required=True)
    args = parser.parse_args()
    result = audit(
        g_dir=args.g_dir,
        r_dir=args.r_dir,
        changes_path=args.changes,
        current_candidates_path=args.current_candidates,
        previous_candidates_path=args.previous_candidates,
        output_path=args.output,
        source_run_id=args.source_run_id,
        previous_run_id=args.previous_run_id,
        parent_sha256=args.parent_sha256,
        current_candidate_sha256=args.current_candidate_sha256,
        previous_candidate_sha256=args.previous_candidate_sha256,
        raw_g_md5=args.raw_g_md5,
        raw_r_md5=args.raw_r_md5,
    )
    print(json.dumps({key: value for key, value in result.items() if key != "objects"}, indent=2, sort_keys=True))
    for obj in result["objects"]:
        print(json.dumps({
            "SourceID": obj["SourceID"],
            "change_type": obj["change_type"],
            "current_candidate_list_member": obj["current_candidate_list_member"],
            "previous_candidate_list_member": obj["previous_candidate_list_member"],
            "replay_candidate_with_regressed_guard": obj["replay_candidate_with_regressed_guard"],
            "replay_candidate_with_finite_guard": obj["replay_candidate_with_finite_guard"],
            "finite_snr_guard_explains_membership_change": obj["finite_snr_guard_explains_membership_change"],
        }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
