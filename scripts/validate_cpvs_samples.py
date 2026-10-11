"""Create reproducible CPVS membership samples and compare object-level full/batch outputs.

This tool is diagnostic only. Published membership is a reference, not independent
astrophysical ground truth. It never changes scientific thresholds or membership.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_ids(path: Path) -> set[str]:
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    if lines and lines[0].strip().lower() in {"sourceid", "source_id", "id"}:
        lines = lines[1:]
    values = {line.strip() for line in lines if line.strip()}
    if not values:
        raise ValueError(f"no IDs found in {path}")
    if any(not value.isdigit() for value in values):
        raise ValueError(f"expected numeric SourceIDs in {path}")
    return values


def read_decisions(path: Path) -> dict[str, bool]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError(f"missing CSV header: {path}")
        normalized = {name.strip().lower(): name for name in reader.fieldnames}
        id_key = next((normalized[k] for k in ("sourceid", "source_id", "id") if k in normalized), None)
        decision_key = next((normalized[k] for k in ("selected", "decision", "member", "is_member") if k in normalized), None)
        if not id_key or not decision_key:
            raise ValueError(f"{path} needs SourceID and selected/decision columns")
        result: dict[str, bool] = {}
        for row in reader:
            oid = (row.get(id_key) or "").strip()
            raw = (row.get(decision_key) or "").strip().lower()
            if not oid:
                continue
            if oid in result:
                raise ValueError(f"duplicate object decision for SourceID {oid} in {path}")
            if raw in {"1", "true", "yes", "selected", "member"}:
                result[oid] = True
            elif raw in {"0", "false", "no", "not_selected", "nonmember"}:
                result[oid] = False
            else:
                raise ValueError(f"unrecognized decision {raw!r} for SourceID {oid}")
        return result


def stratified_sample(parent: set[str], published: set[str], size: int, seed: int) -> tuple[list[str], dict[str, int]]:
    if size > len(parent):
        raise ValueError(f"sample size {size} exceeds parent population {len(parent)}")
    positive = sorted(parent & published, key=int)
    negative = sorted(parent - published, key=int)
    if not positive or not negative:
        raise ValueError("parent catalog must contain both reference-positive and reference-negative IDs")
    rng = random.Random(seed)
    # Proportional allocation with at least one member from each stratum.
    n_pos = round(size * len(positive) / len(parent))
    n_pos = min(len(positive), max(1, min(size - 1, n_pos)))
    n_neg = size - n_pos
    if n_neg > len(negative):
        n_neg = len(negative)
        n_pos = size - n_neg
    chosen = rng.sample(positive, n_pos) + rng.sample(negative, n_neg)
    chosen.sort(key=int)
    return chosen, {"published_reference_member": n_pos, "outside_published_reference": n_neg}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--parent-ids", type=Path, required=True, help="Complete CPVS Table2 Seq/SourceID list")
    parser.add_argument("--published-ids", type=Path, required=True, help="Independent Table4 membership mapped to Table2 Seq")
    parser.add_argument("--candidate-ids", type=Path, required=True, help="Full derivation's selected SourceIDs")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=20261012)
    parser.add_argument("--full-decisions", type=Path, help="Optional CSV: SourceID,selected from full-catalog processing")
    parser.add_argument("--batch-decisions", type=Path, help="Optional CSV: SourceID,selected from object-grouped batch processing")
    args = parser.parse_args()
    if bool(args.full_decisions) != bool(args.batch_decisions):
        parser.error("--full-decisions and --batch-decisions must be supplied together")

    parent = read_ids(args.parent_ids)
    published = read_ids(args.published_ids)
    candidate = read_ids(args.candidate_ids)
    if len(parent) != 781_602:
        raise ValueError(f"expected exactly 781602 unique parent SourceIDs, got {len(parent)}")
    if not published <= parent:
        raise ValueError(f"{len(published - parent)} published IDs do not map to the parent catalog")
    if not candidate <= parent:
        raise ValueError(f"{len(candidate - parent)} candidate IDs are outside the parent catalog")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    input_hashes = {
        "parent_ids_sha256": sha256(args.parent_ids),
        "published_ids_sha256": sha256(args.published_ids),
        "candidate_ids_sha256": sha256(args.candidate_ids),
    }
    manifests = []
    for size in (100, 1000):
        ids, strata = stratified_sample(parent, published, size, args.seed + size)
        path = args.output_dir / f"cpvs_sample_{size}.json"
        manifest = {
            "schema_version": 1,
            "sample_size": size,
            "seed": args.seed + size,
            "method": "Python random.Random.sample, stratified by published-reference membership, sorted by numeric SourceID",
            "population_size": len(parent),
            "population_membership_sha256": input_hashes["parent_ids_sha256"],
            "published_reference_sha256": input_hashes["published_ids_sha256"],
            "candidate_membership_sha256": input_hashes["candidate_ids_sha256"],
            "strata_counts": strata,
            "source_ids": ids,
            "caveat": "Published membership is a comparison reference, not independent astrophysical ground truth.",
        }
        path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        manifests.append({"path": path.name, "sha256": sha256(path), "sample_size": size, "strata_counts": strata})

    fp = sorted(candidate - published, key=int)
    fn = sorted(published - candidate, key=int)
    report = {
        "status": "UNRESOLVED" if fp or fn else "REFERENCE_MEMBERSHIP_MATCH",
        "diagnostic_only": True,
        "selection_policy_changed": False,
        "population": {"parent_count": len(parent), "published_reference_count": len(published), "candidate_count": len(candidate), "intersection_count": len(candidate & published), "candidate_only_count": len(fp), "published_only_count": len(fn)},
        "relative_to_published_reference": {"false_positive_count": len(fp), "false_negative_count": len(fn), "candidate_only_source_ids": fp, "published_only_source_ids": fn},
        "input_sha256": input_hashes,
        "sample_manifests": manifests,
        "seed_base": args.seed,
        "code_note": "Run this script from the exact Git commit under test; record that commit in CI provenance.",
        "full_vs_batch": None,
        "caveat": "Published membership is a reference comparison, not independent astrophysical truth.",
    }
    if args.full_decisions and args.batch_decisions:
        full = read_decisions(args.full_decisions)
        batch = read_decisions(args.batch_decisions)
        if set(full) != parent or set(batch) != parent:
            report["full_vs_batch"] = {
                "status": "INVALID_COVERAGE",
                "full_missing_count": len(parent - set(full)),
                "full_extra_count": len(set(full) - parent),
                "batch_missing_count": len(parent - set(batch)),
                "batch_extra_count": len(set(batch) - parent),
            }
            report["status"] = "UNRESOLVED"
        else:
            disagreements = sorted((oid for oid in parent if full[oid] != batch[oid]), key=int)
            report["full_vs_batch"] = {
                "status": "PASS" if not disagreements else "FAIL",
                "parent_object_count": len(parent),
                "full_selected_count": sum(full.values()),
                "batch_selected_count": sum(batch.values()),
                "disagreement_count": len(disagreements),
                "disagreement_source_ids": disagreements,
                "grouping_key": "complete CPVS SourceID; never light-curve row position",
            }
            if disagreements:
                report["status"] = "UNRESOLVED"
    report_path = args.output_dir / "cpvs_sample_validation_report.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    # Diagnostics are report-producing, not a release gate. The JSON status remains fail-closed.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
