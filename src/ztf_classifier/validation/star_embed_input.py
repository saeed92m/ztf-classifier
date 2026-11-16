"""Run the frozen v0.2 feature-preparation path on an independent StarEmbed input.

This is an input-compatibility diagnostic only. StarEmbed's seven-class taxonomy
is not mapped to the frozen 15-class classifier, and no prediction is produced.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from ztf_classifier.features.pipeline import V0_2_FEATURES, extract_v0_2_features
from ztf_classifier.validation.star_embed_audit import ARTIFACTS

BAND_TO_FID = {"g": 1, "r": 2}
SPLIT_FILES = {
    "train": [name for name in ARTIFACTS if name.startswith("train-")],
    "validation": ["validation-00000-of-00001.parquet"],
    "test": ["test-00000-of-00001.parquet"],
    "anom": ["anom-00000-of-00001.parquet"],
}


def _canonical_feature_rows_sha256(frame: pd.DataFrame) -> str:
    """Hash logical feature rows independently of Parquet container metadata."""
    canonical_rows: list[dict[str, Any]] = []
    for row in frame.to_dict(orient="records"):
        canonical: dict[str, Any] = {}
        for name, value in row.items():
            if value is None:
                canonical[name] = None
            elif isinstance(value, (bool, np.bool_)):
                canonical[name] = bool(value)
            elif isinstance(value, (int, np.integer)):
                canonical[name] = int(value)
            elif isinstance(value, (float, np.floating)):
                numeric = float(value)
                canonical[name] = numeric if np.isfinite(numeric) else None
            elif isinstance(value, str):
                canonical[name] = value
            elif pd.isna(value):
                canonical[name] = None
            else:
                raise TypeError(
                    f"Unsupported feature value for canonical hash: {type(value).__name__}"
                )
        canonical_rows.append(canonical)
    encoded = json.dumps(
        canonical_rows,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def star_embed_row_to_internal_lc(row: dict[str, Any]) -> pd.DataFrame:
    """Map StarEmbed source-native g/r arrays to the frozen internal LC columns.

    StarEmbed documents target=magnitude, past_feat_dynamic_real=mag_err and
    mjd=Modified Julian Date. The mapping is explicit and does not infer time
    conversions, photometric corrections, or object identity.
    """
    bands = row.get("bands_data")
    if not isinstance(bands, dict):
        raise TypeError("bands_data must be a struct/dict")

    records: list[dict[str, Any]] = []
    for band, fid in BAND_TO_FID.items():
        payload = bands.get(band)
        if payload is None:
            continue
        if not isinstance(payload, dict):
            raise TypeError(f"{band} band payload must be a struct/dict")
        required = ("target", "past_feat_dynamic_real", "mjd")
        missing = [name for name in required if payload.get(name) is None]
        if missing:
            raise ValueError(f"{band} band is missing arrays: {missing}")

        magnitudes = list(payload["target"])
        errors = list(payload["past_feat_dynamic_real"])
        epochs = list(payload["mjd"])
        if not (len(magnitudes) == len(errors) == len(epochs)):
            raise ValueError(
                f"{band} array length mismatch: target={len(magnitudes)}, "
                f"mag_err={len(errors)}, mjd={len(epochs)}"
            )
        for mjd, mag, magerr in zip(epochs, magnitudes, errors, strict=True):
            records.append(
                {
                    "mjd": mjd,
                    "fid": fid,
                    "mag": mag,
                    "magerr": magerr,
                }
            )

    return pd.DataFrame.from_records(
        records, columns=["mjd", "fid", "mag", "magerr"]
    )


def _split_id_sets(data_dir: Path) -> tuple[dict[str, set[str]], dict[str, int]]:
    ids: dict[str, set[str]] = {}
    duplicate_counts: dict[str, int] = {}
    for split, filenames in SPLIT_FILES.items():
        values: list[str] = []
        for filename in filenames:
            frame = pd.read_parquet(data_dir / filename, columns=["sourceid"])
            values.extend(frame["sourceid"].astype(str).tolist())
        counts = Counter(values)
        ids[split] = set(values)
        duplicate_counts[split] = sum(count > 1 for count in counts.values())
    return ids, duplicate_counts


def run_star_embed_feature_probe(
    data_dir: str | Path,
    output_dir: str | Path,
    *,
    sample_size: int = 50,
    seed: int = 20261115,
) -> dict[str, Any]:
    """Generate frozen v0.2 feature vectors for a clean deterministic test sample."""
    root = Path(data_dir)
    output = Path(output_dir)
    if sample_size < 1:
        raise ValueError("sample_size must be at least 1")
    missing = [name for name in ARTIFACTS if not (root / name).is_file()]
    if missing:
        raise FileNotFoundError(f"missing StarEmbed artifacts: {missing}")

    split_ids, duplicate_counts = _split_id_sets(root)
    overlap_counts: dict[str, int] = {}
    split_names = list(split_ids)
    for index, left in enumerate(split_names):
        for right in split_names[index + 1 :]:
            overlap_counts[f"{left}__{right}"] = len(split_ids[left] & split_ids[right])

    # Do not evaluate a test object that appears in another split or more than
    # once in the test split. Preserve and report the original source artifacts.
    test_frame = pd.read_parquet(root / "test-00000-of-00001.parquet")
    test_counts = Counter(test_frame["sourceid"].astype(str).tolist())
    other_ids = set().union(
        *(split_ids[name] for name in split_names if name != "test")
    )
    clean_ids = {
        sourceid
        for sourceid, count in test_counts.items()
        if count == 1 and sourceid not in other_ids
    }
    clean_test = test_frame.loc[
        test_frame["sourceid"].astype(str).isin(clean_ids)
    ].copy()
    clean_test = clean_test.sort_values("sourceid", kind="mergesort")
    selected_n = min(sample_size, len(clean_test))
    if selected_n:
        sample = clean_test.sample(n=selected_n, random_state=seed).sort_values(
            "sourceid", kind="mergesort"
        )
    else:
        sample = clean_test.iloc[0:0]

    feature_rows: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []
    for row in sample.to_dict("records"):
        sourceid = str(row["sourceid"])
        try:
            internal = star_embed_row_to_internal_lc(row)
            features = extract_v0_2_features(internal, cutoff_mjd=None)
            if tuple(features) != V0_2_FEATURES:
                raise ValueError("feature vector does not match frozen v0.2 order")
            record: dict[str, Any] = {
                "sourceid": sourceid,
                "class_str": str(row.get("class_str", "")),
                "input_rows_g_r": len(internal),
                "g_n_obs": float(features.get("g_n_obs", np.nan)),
                "r_n_obs": float(features.get("r_n_obs", np.nan)),
                "g_ls_best_period_days": float(
                    features.get("g_ls_best_period_days", np.nan)
                ),
                "r_ls_best_period_days": float(
                    features.get("r_ls_best_period_days", np.nan)
                ),
            }
            record.update({name: float(features[name]) for name in V0_2_FEATURES})
            feature_rows.append(record)
        except (TypeError, ValueError, KeyError) as exc:
            failures.append(
                {
                    "sourceid": sourceid,
                    "error": f"{type(exc).__name__}: {exc}",
                }
            )

    feature_frame = pd.DataFrame(feature_rows)
    output.mkdir(parents=True, exist_ok=True)
    feature_parquet_path = output / "star_embed_v0_2_feature_probe.parquet"
    feature_parquet_sha256: str | None = None
    feature_parquet_bytes: int | None = None
    if not feature_frame.empty:
        feature_frame.to_parquet(feature_parquet_path, index=False)
        feature_parquet_sha256 = hashlib.sha256(
            feature_parquet_path.read_bytes()
        ).hexdigest()
        feature_parquet_bytes = feature_parquet_path.stat().st_size
    feature_rows_sha256 = _canonical_feature_rows_sha256(feature_frame)

    leakage = {
        "within_split_duplicates": duplicate_counts,
        "cross_split_object_id_overlap": overlap_counts,
    }
    has_leakage = any(duplicate_counts.values()) or any(overlap_counts.values())
    sample_complete = selected_n == sample_size
    status = (
        "BLOCKED_SOURCE_SPLIT_INTEGRITY"
        if has_leakage
        else "BLOCKED_INSUFFICIENT_CLEAN_TEST_SAMPLE"
        if not sample_complete
        else "PASS_INPUT_FEATURE_PROBE"
    )
    report = {
        "schema_version": "1.0",
        "benchmark_id": "star_embed_ztf_40k",
        "status": status,
        "feature_path_status": (
            "EXECUTED_WITH_ERRORS" if failures else
            "EXECUTED" if len(feature_rows) == selected_n and selected_n > 0 else
            "NOT_EXECUTED"
        ),
        "seed": seed,
        "requested_sample_size": sample_size,
        "selected_clean_test_objects": selected_n,
        "feature_vectors_generated": len(feature_rows),
        "feature_vector_width": len(V0_2_FEATURES),
        "feature_rows_sha256": feature_rows_sha256,
        "feature_parquet_sha256": feature_parquet_sha256,
        "feature_parquet_bytes": feature_parquet_bytes,
        "feature_names_sha256_ordered": hashlib.sha256(
            "\n".join(V0_2_FEATURES).encode("utf-8")
        ).hexdigest(),
        "sample_source_split": "test",
        "sample_exclusions": {
            "test_objects_overlapping_other_splits": len(
                split_ids["test"] & other_ids
            ),
            "duplicate_test_sourceids": sum(
                count > 1 for count in test_counts.values()
            ),
        },
        "leakage_audit": leakage,
        "failures": failures,
        "interpretation": (
            "The frozen v0.2 feature-preparation path was exercised on a "
            "deterministic clean subset of StarEmbed test objects. This does not "
            "evaluate classifier accuracy: StarEmbed has a seven-class taxonomy "
            "that is not mapped to the frozen 15-class model. Any source split "
            "duplication/overlap blocks benchmark acceptance even when feature "
            "generation succeeds."
        ),
        "limitations": [
            "No class mapping or prediction was performed.",
            "No model was trained or changed.",
            "StarEmbed labels remain source-provided benchmark labels.",
            "The sample is diagnostic, not population-level performance evidence.",
            "No raw source arrays are written to the report; only derived feature rows are emitted.",
        ],
    }
    (output / "star_embed_input_probe.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--sample-size", type=int, default=50)
    parser.add_argument("--seed", type=int, default=20261115)
    args = parser.parse_args(argv)
    report = run_star_embed_feature_probe(
        args.data_dir, args.output_dir, sample_size=args.sample_size, seed=args.seed
    )
    print(f"status={report['status']}")
    print(f"feature_vectors_generated={report['feature_vectors_generated']}")
    print(f"report={args.output_dir / 'star_embed_input_probe.json'}")
    blocked = report["status"] != "PASS_INPUT_FEATURE_PROBE"
    return 2 if blocked or report["failures"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
