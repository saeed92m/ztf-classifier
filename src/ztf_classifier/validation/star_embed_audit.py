"""Schema and data-quality audit for the raw StarEmbed ZTF_40k Parquet snapshot.

This audit deliberately does not train a model or claim classification accuracy. It
checks the source contract, split boundaries, light-curve array consistency, and
creates a deterministic object-ID sample for a separately validated inference path.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ARTIFACTS = (
    "train-00000-of-00002.parquet",
    "train-00001-of-00002.parquet",
    "validation-00000-of-00001.parquet",
    "test-00000-of-00001.parquet",
    "anom-00000-of-00001.parquet",
)
TOP_LEVEL_COLUMNS = {"sourceid", "bands_data", "period", "class_str", "ra", "dec"}
BANDS = ("g", "r", "i")
BAND_ARRAY_FIELDS = ("target", "past_feat_dynamic_real", "feat_dynamic_real", "mjd")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _finite_number(value: Any) -> bool:
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def _sequence_length(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return len(value)
    except TypeError:
        return None


def audit_star_embed_dataset(
    data_dir: str | Path,
    output_path: str | Path,
    *,
    sample_size: int = 50,
    seed: int = 20261023,
) -> dict[str, Any]:
    """Audit five pinned StarEmbed Parquet artifacts and write a JSON report."""
    root = Path(data_dir)
    output = Path(output_path)
    if sample_size < 1:
        raise ValueError("sample_size must be at least 1")

    split_frames: dict[str, list[pd.DataFrame]] = {
        "train": [],
        "validation": [],
        "test": [],
        "anom": [],
    }
    artifact_reports: list[dict[str, Any]] = []
    errors: list[str] = []

    for filename in ARTIFACTS:
        path = root / filename
        if not path.is_file():
            errors.append(f"missing_artifact:{filename}")
            continue
        frame = pd.read_parquet(path)
        missing = sorted(TOP_LEVEL_COLUMNS - set(frame.columns))
        if missing:
            errors.append(f"missing_columns:{filename}:{','.join(missing)}")
        frame["_source_artifact"] = filename
        split = "train" if filename.startswith("train-") else filename.split("-")[0]
        split_frames[split].append(frame)
        artifact_reports.append(
            {
                "file": filename,
                "sha256": _sha256(path),
                "bytes": path.stat().st_size,
                "rows": len(frame),
                "columns": list(frame.columns),
                "missing_required_columns": missing,
            }
        )

    if errors:
        report = {
            "schema_version": "1.0",
            "benchmark_id": "star_embed_ztf_40k",
            "status": "BLOCKED",
            "errors": errors,
            "artifacts": artifact_reports,
            "sample": {"requested_size": sample_size, "seed": seed, "source_split": "test", "source_ids": []},
        }
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return report

    combined = {name: pd.concat(parts, ignore_index=True) for name, parts in split_frames.items()}
    all_ids: dict[str, set[str]] = {}
    split_reports: dict[str, Any] = {}
    for split, frame in combined.items():
        ids = frame["sourceid"].astype(str)
        all_ids[split] = set(ids)
        duplicate_ids = sorted(ids[ids.duplicated(keep=False)].unique().tolist())
        invalid_periods = int((~frame["period"].map(_finite_number) | (pd.to_numeric(frame["period"], errors="coerce") <= 0)).sum())
        invalid_coordinates = int(
            (~frame["ra"].map(_finite_number)).sum()
            + (~frame["dec"].map(_finite_number)).sum()
            + (pd.to_numeric(frame["ra"], errors="coerce").lt(0) | pd.to_numeric(frame["ra"], errors="coerce").gt(360)).sum()
            + (pd.to_numeric(frame["dec"], errors="coerce").lt(-90) | pd.to_numeric(frame["dec"], errors="coerce").gt(90)).sum()
        )
        class_counts = {str(k): int(v) for k, v in frame["class_str"].astype(str).value_counts().sort_index().items()}
        split_reports[split] = {
            "rows": len(frame),
            "unique_sourceids": int(ids.nunique()),
            "duplicate_sourceid_count": len(duplicate_ids),
            "duplicate_sourceids_sample": duplicate_ids[:20],
            "class_counts": class_counts,
            "invalid_nonpositive_or_nonfinite_periods": invalid_periods,
            "invalid_or_out_of_range_coordinates": invalid_coordinates,
        }

    overlap_reports = {}
    split_names = list(all_ids)
    for i, left in enumerate(split_names):
        for right in split_names[i + 1 :]:
            overlap = sorted(all_ids[left] & all_ids[right])
            overlap_reports[f"{left}__{right}"] = {
                "overlap_count": len(overlap),
                "overlap_sourceids_sample": overlap[:20],
            }

    leakage_findings: list[str] = []
    object_id_issue_details: list[dict[str, Any]] = []
    detail_columns = ["sourceid", "class_str", "period", "ra", "dec", "_source_artifact"]
    for split, split_report in split_reports.items():
        duplicate_count = int(split_report["duplicate_sourceid_count"])
        if duplicate_count:
            leakage_findings.append(
                f"duplicate_sourceids_within_split:{split}:{duplicate_count}"
            )
            frame = combined[split]
            duplicate_ids = set(split_report["duplicate_sourceids_sample"])
            details = frame.loc[frame["sourceid"].astype(str).isin(duplicate_ids), detail_columns]
            for row in details.to_dict("records"):
                object_id_issue_details.append({
                    "issue": "duplicate_within_split",
                    "split": split,
                    "sourceid": str(row["sourceid"]),
                    "class_str": str(row["class_str"]),
                    "period": float(row["period"]) if _finite_number(row["period"]) else None,
                    "ra": float(row["ra"]) if _finite_number(row["ra"]) else None,
                    "dec": float(row["dec"]) if _finite_number(row["dec"]) else None,
                    "source_artifact": str(row["_source_artifact"]),
                })
    for pair, overlap_report in overlap_reports.items():
        overlap_count = int(overlap_report["overlap_count"])
        if overlap_count:
            leakage_findings.append(f"object_id_overlap_between_splits:{pair}:{overlap_count}")
            left, right = pair.split("__", maxsplit=1)
            overlapping_ids = set(overlap_report["overlap_sourceids_sample"])
            for split in (left, right):
                frame = combined[split]
                details = frame.loc[frame["sourceid"].astype(str).isin(overlapping_ids), detail_columns]
                for row in details.to_dict("records"):
                    object_id_issue_details.append({
                        "issue": "cross_split_overlap",
                        "split": split,
                        "sourceid": str(row["sourceid"]),
                        "class_str": str(row["class_str"]),
                        "period": float(row["period"]) if _finite_number(row["period"]) else None,
                        "ra": float(row["ra"]) if _finite_number(row["ra"]) else None,
                        "dec": float(row["dec"]) if _finite_number(row["dec"]) else None,
                        "source_artifact": str(row["_source_artifact"]),
                    })

    array_report = Counter()
    array_examples: list[dict[str, Any]] = []
    for split, frame in combined.items():
        for row_index, row in frame.iterrows():
            bands = row.get("bands_data")
            if not isinstance(bands, dict):
                array_report["invalid_bands_data_struct"] += 1
                if len(array_examples) < 20:
                    array_examples.append({"split": split, "sourceid": str(row.get("sourceid")), "issue": "invalid_bands_data_struct"})
                continue
            for band in BANDS:
                payload = bands.get(band)
                if payload is None:
                    array_report[f"{band}_band_absent"] += 1
                    continue
                if not isinstance(payload, dict):
                    array_report[f"{band}_band_invalid_struct"] += 1
                    continue
                lengths = {field: _sequence_length(payload.get(field)) for field in BAND_ARRAY_FIELDS}
                target_length = lengths["target"]
                if target_length is None:
                    array_report[f"{band}_target_missing_or_not_sequence"] += 1
                for field in ("past_feat_dynamic_real", "mjd"):
                    if target_length is not None and lengths[field] != target_length:
                        array_report[f"{band}_{field}_length_mismatch"] += 1
                if target_length is not None and lengths["feat_dynamic_real"] not in {target_length, max(0, target_length - 1)}:
                    array_report[f"{band}_feat_dynamic_real_length_mismatch"] += 1
                declared_length = payload.get("length")
                if declared_length is not None and target_length is not None:
                    try:
                        if int(declared_length) != target_length:
                            array_report[f"{band}_declared_length_mismatch"] += 1
                    except (TypeError, ValueError):
                        array_report[f"{band}_declared_length_invalid"] += 1
                for field in BAND_ARRAY_FIELDS:
                    values = payload.get(field)
                    if values is not None:
                        try:
                            if not np.isfinite(np.asarray(values, dtype=float)).all():
                                array_report[f"{band}_{field}_nonfinite_values"] += 1
                        except (TypeError, ValueError):
                            array_report[f"{band}_{field}_not_numeric"] += 1
                if len(array_examples) < 20 and any(
                    key.endswith("length_mismatch") and value
                    for key, value in array_report.items()
                ):
                    array_examples.append({
                        "split": split,
                        "sourceid": str(row.get("sourceid")),
                        "band": band,
                        "array_lengths": lengths,
                        "declared_length": declared_length,
                    })

    test_frame = combined["test"].sort_values("sourceid", kind="mergesort")
    sample_n = min(sample_size, len(test_frame))
    if sample_n:
        sample = test_frame.sample(n=sample_n, random_state=seed).sort_values("sourceid", kind="mergesort")
        sample_ids = sample["sourceid"].astype(str).tolist()
    else:
        sample_ids = []

    train_classes = set(combined["train"]["class_str"].astype(str))
    validation_classes = set(combined["validation"]["class_str"].astype(str))
    test_classes = set(combined["test"]["class_str"].astype(str))
    anom_classes = set(combined["anom"]["class_str"].astype(str))
    class_overlap = {
        "train_validation": sorted(train_classes & validation_classes),
        "train_test": sorted(train_classes & test_classes),
        "validation_test": sorted(validation_classes & test_classes),
        "in_distribution_anom": sorted((train_classes | validation_classes | test_classes) & anom_classes),
    }

    report = {
        "schema_version": "1.0",
        "benchmark_id": "star_embed_ztf_40k",
        "status": "BLOCKED" if errors or leakage_findings else "PASS_SCHEMA_AUDIT_WITH_FINDINGS",
        "validation_errors": leakage_findings,
        "object_id_issue_details": object_id_issue_details,
        "interpretation": "Schema and data-quality audit only; no model predictions or scientific classification performance are evaluated.",
        "seed": seed,
        "artifacts": artifact_reports,
        "splits": split_reports,
        "object_id_overlap": overlap_reports,
        "class_taxonomy_overlap": class_overlap,
        "lightcurve_array_quality_counts": dict(sorted(array_report.items())),
        "lightcurve_array_issue_examples": array_examples,
        "sample": {
            "requested_size": sample_size,
            "actual_size": len(sample_ids),
            "seed": seed,
            "source_split": "test",
            "selection_method": "pandas.DataFrame.sample(random_state=seed) after stable sourceid sort",
            "source_ids": sample_ids,
        },
        "limitations": [
            "A deterministic diagnostic sample is not population-level performance evidence.",
            "Class labels are source-provided labels, not independent physical ground truth.",
            "This audit does not generate predictions, train models, evaluate accuracy, or validate OOD performance.",
        ],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, required=True, help="Directory containing the five acquired StarEmbed Parquet files")
    parser.add_argument("--output", type=Path, required=True, help="JSON report output path")
    parser.add_argument("--sample-size", type=int, default=50)
    parser.add_argument("--seed", type=int, default=20261023)
    args = parser.parse_args(argv)
    report = audit_star_embed_dataset(args.data_dir, args.output, sample_size=args.sample_size, seed=args.seed)
    print(f"status={report['status']}")
    print(f"report={args.output}")
    if report["status"] == "BLOCKED":
        print("errors=" + json.dumps(report.get("errors", [])))
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
