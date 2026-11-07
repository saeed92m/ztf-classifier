#!/usr/bin/env python3
"""Audit local scientific artifacts without modifying or uploading them.

The frozen production model and the 2026-10-27 lab-smoke artifact are distinct.
This script never treats the lab-smoke artifact as a production substitute.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

PRODUCTION_ARTIFACT = Path("runs/model_baseline_v0.2_production/artifact")
LAB_ARTIFACT = Path("runs/lab-smoke-20261027T104951Z/artifact")

PRODUCTION_FILES = (
    "model.json",
    "feature_schema.parquet",
    "artifact_manifest.json",
    "model_contract.json",
    "provenance.json",
    "calibration.json",
    "conformal.json",
    "ood.json",
    "ood_model.joblib",
)

KNOWN_LAB_HASHES = {
    "model.json": "96bbbd4643d073be574b0bb359062a31219417b2d857ac00e64a8c3f47e21a6c",
    "feature_schema.parquet": "fed07fc291070ecbdc7bbc597fad5aac6a3f4a1746feb12a9f4c2407108af329",
    "calibration.json": "8eaddb70ecaf02c10fe252d03337be484415e68dcce1fdb30f6fbf1fe25fb714",
    "conformal.json": "d45ee30ba564f319d8599f3e18afd6ae9010ea0e41d1a301065acec0c9a6be8b",
}

FEATURE_FILES = (
    Path("data/processed/features_v0.2.parquet"),
    Path("reports/tables/final_feature_set_v0.2.parquet"),
    Path("reports/tables/final_model_config_v0.2.json"),
)

TESTS = (
    "tests/test_feature_pipeline_parity.py",
    "tests/test_raw_dataset_validation_integration.py",
    "tests/test_offline_feature_dataset_reproduction.py",
    "tests/test_model_production_inference.py",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def describe_file(path: Path, *, calculate_hash: bool) -> dict[str, Any]:
    result: dict[str, Any] = {
        "path": str(path),
        "exists": path.is_file(),
    }
    if path.is_file():
        stat = path.stat()
        result["size_bytes"] = stat.st_size
        if calculate_hash:
            result["sha256"] = sha256_file(path)
    return result


def describe_directory(path: Path, *, calculate_hash: bool) -> dict[str, Any]:
    result: dict[str, Any] = {
        "path": str(path),
        "exists": path.is_dir(),
        "files": [],
    }
    if not path.is_dir():
        return result

    files = sorted(item for item in path.iterdir() if item.is_file())
    result["file_count"] = len(files)
    result["total_size_bytes"] = sum(item.stat().st_size for item in files)
    result["files"] = [
        describe_file(item, calculate_hash=calculate_hash) for item in files
    ]
    return result


def find_fold_assignments(root: Path) -> list[str]:
    matches: set[Path] = set()
    for base in (root / "data/processed", root / "reports/tables"):
        if base.is_dir():
            matches.update(
                item
                for item in base.rglob("*")
                if item.is_file() and "fold" in item.name.lower()
            )
    return sorted(str(item.relative_to(root)) for item in matches)


def audit(repo_root: Path, *, hash_data: bool) -> dict[str, Any]:
    production_dir = repo_root / PRODUCTION_ARTIFACT
    lab_dir = repo_root / LAB_ARTIFACT

    production = describe_directory(production_dir, calculate_hash=True)
    production_files = {
        item["path"].split("/")[-1]: item
        for item in production["files"]
    }
    production["required_files"] = {
        name: production_files.get(name, {"path": str(PRODUCTION_ARTIFACT / name), "exists": False})
        for name in PRODUCTION_FILES
    }
    production["missing_required_files"] = [
        name
        for name, item in production["required_files"].items()
        if not item["exists"]
    ]
    production["ready"] = (
        production["exists"] and not production["missing_required_files"]
    )

    lab = describe_directory(lab_dir, calculate_hash=True)
    lab["known_hash_checks"] = {}
    for name, expected in KNOWN_LAB_HASHES.items():
        actual = next(
            (
                item.get("sha256")
                for item in lab.get("files", [])
                if Path(item["path"]).name == name
            ),
            None,
        )
        lab["known_hash_checks"][name] = {
            "expected_sha256": expected,
            "actual_sha256": actual,
            "matches": actual == expected if actual is not None else False,
        }
    lab["production_eligible"] = False
    lab["status"] = "LAB_SMOKE_ONLY_NOT_A_PRODUCTION_SUBSTITUTE"

    feature_data = [
        describe_file(repo_root / path, calculate_hash=hash_data)
        for path in FEATURE_FILES
    ]
    alerce_dir = repo_root / "data/raw/alerce"
    alerce = describe_directory(alerce_dir, calculate_hash=False)
    alerce_parquet = (
        sorted(alerce_dir.rglob("*.parquet")) if alerce_dir.is_dir() else []
    )
    alerce["parquet_file_count"] = len(alerce_parquet)
    alerce["parquet_sample"] = [
        str(item.relative_to(repo_root)) for item in alerce_parquet[:20]
    ]

    test_files = [
        {
            "path": name,
            "exists": (repo_root / name).is_file(),
        }
        for name in TESTS
    ]
    fold_assignments = find_fold_assignments(repo_root)

    blockers: list[str] = []
    if not production["ready"]:
        blockers.append(
            "Frozen production model artifact is missing or incomplete. "
            "Do not substitute the lab-smoke artifact."
        )
    missing_features = [
        item["path"] for item in feature_data if not item["exists"]
    ]
    if missing_features:
        blockers.append(
            "Required feature/config artifacts are missing: "
            + ", ".join(missing_features)
        )
    if not alerce["parquet_file_count"]:
        blockers.append("No ALeRCE raw-detection Parquet cache was found.")
    if not fold_assignments:
        blockers.append("No fold-assignment artifact was found under data/processed or reports/tables.")

    return {
        "schema_version": "ztf-local-scientific-artifact-audit-v1",
        "baseline": {
            "scientific_baseline": "v0.2.0",
            "feature_schema": "final_feature_set_v0.2",
            "feature_count": 42,
            "production_model_path": str(PRODUCTION_ARTIFACT),
        },
        "production_model_artifact": production,
        "lab_smoke_artifact": lab,
        "feature_and_config_artifacts": feature_data,
        "alerce_raw_detection_cache": alerce,
        "fold_assignment_files": fold_assignments,
        "dependent_test_files": test_files,
        "production_integration_tests_ready": (
            production["ready"]
            and not missing_features
            and bool(alerce["parquet_file_count"])
            and bool(fold_assignments)
        ),
        "blockers": blockers,
        "safety": {
            "read_only": True,
            "uploads_performed": False,
            "files_modified": False,
            "lab_artifact_used_as_production": False,
            "large_data_hashing_enabled": hash_data,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("reports/scientific_validation/local_scientific_artifact_audit.json"),
    )
    parser.add_argument(
        "--hash-data",
        action="store_true",
        help="Also calculate SHA-256 for feature datasets. This can take time.",
    )
    args = parser.parse_args()

    repo_root = args.repo_root.expanduser().resolve()
    report = audit(repo_root, hash_data=args.hash_data)
    output = args.output
    if not output.is_absolute():
        output = repo_root / output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "output": str(output),
        "production_integration_tests_ready": report["production_integration_tests_ready"],
        "blockers": report["blockers"],
    }, indent=2))
    return 0 if report["production_integration_tests_ready"] else 2


if __name__ == "__main__":
    sys.exit(main())
