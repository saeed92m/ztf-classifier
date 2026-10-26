#!/usr/bin/env python3
"""Run a bounded real-data DR24 lightcurve -> native feature-engine smoke test.

This is an integration smoke test, not a benchmark or model-accuracy claim.
The DR24 API returns HMJD; it is passed as the internal relative time coordinate
used by the existing feature extractor. No absolute-time cutoff or catalog
membership claim is made.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import requests

from ztf_classifier.features.engine import ScientificFeatureEngine

API_URL = "https://irsa.ipac.caltech.edu/cgi-bin/ZTF/nph_light_curves"
COLLECTION = "ztf_dr24"
TIME_CANDIDATES = ("hmjd", "mjd", "hjd")
FILTER_CANDIDATES = ("filterid", "fid", "filter", "filtercode", "band")
MAG_CANDIDATES = ("mag",)
MAGERR_CANDIDATES = ("magerr", "e_mag")
FLAG_CANDIDATES = ("catflags", "catflag")


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _column(frame: pd.DataFrame, candidates: tuple[str, ...]) -> str | None:
    lookup = {str(name).strip().lower(): str(name) for name in frame.columns}
    return next((lookup[name] for name in candidates if name in lookup), None)


def normalize_api_frame(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Map the documented IRSA DR24 CSV schema to the engine observation contract."""
    if frame.empty:
        raise ValueError("IRSA returned an empty lightcurve table.")
    frame = frame.copy()
    frame.columns = [str(name).strip().lower() for name in frame.columns]

    time_col = _column(frame, TIME_CANDIDATES)
    filter_col = _column(frame, FILTER_CANDIDATES)
    mag_col = _column(frame, MAG_CANDIDATES)
    magerr_col = _column(frame, MAGERR_CANDIDATES)
    flag_col = _column(frame, FLAG_CANDIDATES)
    missing = [
        name for name, value in (
            ("time (hmjd/mjd/hjd)", time_col),
            ("filter id/code", filter_col),
            ("mag", mag_col),
            ("magerr", magerr_col),
        ) if value is None
    ]
    if missing:
        raise ValueError(
            f"IRSA CSV schema missing {missing}; returned columns={list(frame.columns)}"
        )

    filt = frame[filter_col]
    if pd.api.types.is_numeric_dtype(filt):
        fid = pd.to_numeric(filt, errors="coerce")
    else:
        values = filt.astype(str).str.strip().str.lower()
        mapping = {
            "g": 1, "zg": 1, "ztfg": 1, "1": 1,
            "r": 2, "zr": 2, "ztfr": 2, "2": 2,
            "i": 3, "zi": 3, "ztfi": 3, "3": 3,
        }
        fid = values.map(mapping)

    raw_time = pd.to_numeric(frame[time_col], errors="coerce")
    time_semantics = time_col
    if time_col == "hjd":
        raw_time = raw_time - 2400000.5
        time_semantics = "hjd_minus_2400000.5"
    elif time_col == "hmjd":
        time_semantics = "heliocentric_modified_julian_date"

    normalized = pd.DataFrame({
        "mjd": raw_time,
        "fid": pd.to_numeric(fid, errors="coerce"),
        "mag": pd.to_numeric(frame[mag_col], errors="coerce"),
        "magerr": pd.to_numeric(frame[magerr_col], errors="coerce"),
    })
    if flag_col is not None:
        normalized["catflags"] = pd.to_numeric(frame[flag_col], errors="coerce")
    else:
        normalized["catflags"] = np.nan

    raw_rows = len(normalized)
    normalized = normalized.loc[normalized["fid"].isin([1, 2])].copy()
    # Keep bad/non-finite measurements visible to the production preprocessing
    # path; prepare_band_lightcurve is the authority for its current validity rule.
    normalized = normalized.sort_values(["fid", "mjd"], kind="mergesort").reset_index(drop=True)
    meta = {
        "source_time_column": time_col,
        "time_semantics": time_semantics,
        "source_filter_column": filter_col,
        "source_mag_column": mag_col,
        "source_magerr_column": magerr_col,
        "source_flag_column": flag_col,
        "raw_rows": raw_rows,
        "g_rows": int((normalized["fid"] == 1).sum()),
        "r_rows": int((normalized["fid"] == 2).sum()),
        "i_or_other_rows_excluded": raw_rows - len(normalized),
        "catflags_missing_rows": int(normalized["catflags"].isna().sum()),
        "catflags_nonzero_rows": int((normalized["catflags"].fillna(0) != 0).sum()),
    }
    return normalized, meta


def acquire_lightcurve(session: requests.Session, oid: str, timeout: float) -> tuple[pd.DataFrame, bytes]:
    response = session.get(
        API_URL,
        params={"ID": oid, "COLLECTION": COLLECTION, "FORMAT": "CSV"},
        timeout=timeout,
    )
    response.raise_for_status()
    payload = response.content
    if not payload or b"<html" in payload[:1000].lower():
        raise ValueError(f"IRSA returned empty/HTML content for oid={oid}")
    try:
        frame = pd.read_csv(io.BytesIO(payload), comment="#")
    except Exception as exc:
        raise ValueError(f"Could not parse IRSA CSV for oid={oid}: {exc}") from exc
    if frame.empty:
        raise ValueError(f"IRSA returned no photometry rows for oid={oid}")
    return frame, payload


def valid_band_counts(observations: pd.DataFrame) -> dict[str, int]:
    valid = (
        np.isfinite(pd.to_numeric(observations["mjd"], errors="coerce"))
        & np.isfinite(pd.to_numeric(observations["mag"], errors="coerce"))
        & np.isfinite(pd.to_numeric(observations["magerr"], errors="coerce"))
        & (pd.to_numeric(observations["magerr"], errors="coerce") > 0)
    )
    return {
        "g_valid": int((valid & (observations["fid"] == 1)).sum()),
        "r_valid": int((valid & (observations["fid"] == 2)).sum()),
    }



DR24_SMOKE_SAMPLE_SEED = "DR24-LIGHTCURVE-SMOKE-v1"


def select_candidate_objects(
    objects: pd.DataFrame,
    max_objects: int,
    minimum_good_observations: int = 30,
) -> tuple[pd.DataFrame, int]:
    """Choose a deterministic hash-ranked sample from the pinned object subset.

    Ranking by ngoodobsrel alone repeatedly selected the same top objects and
    could hide input diversity. This stable hash ranking is reproducible across
    Python/pandas versions; the eligible-pool size is returned for provenance.
    It does not make the upstream 150-row DR24 source subset representative.
    """
    required = {"oid", "ngoodobsrel"}
    if not required.issubset(objects.columns):
        raise ValueError(f"Objects table missing required columns: {sorted(required - set(objects.columns))}")
    frame = objects.copy()
    frame["oid"] = frame["oid"].astype(str).str.strip()
    if frame["oid"].eq("").any() or frame["oid"].duplicated().any():
        raise ValueError("Objects table contains blank or duplicate OIDs")
    frame["ngoodobsrel"] = pd.to_numeric(frame["ngoodobsrel"], errors="coerce")
    frame = frame.loc[frame["ngoodobsrel"] >= minimum_good_observations].copy()
    eligible_count = len(frame)
    frame["_sample_rank"] = frame["oid"].map(
        lambda oid: hashlib.sha256(f"{DR24_SMOKE_SAMPLE_SEED}:{oid}".encode("utf-8")).hexdigest()
    )
    frame = frame.sort_values(["_sample_rank", "oid"], kind="mergesort").head(max_objects)
    return frame.drop(columns=["_sample_rank"]).reset_index(drop=True), eligible_count


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--objects-tsv", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--max-objects", type=int, default=12)
    parser.add_argument("--timeout", type=float, default=60.0)
    args = parser.parse_args()
    if args.max_objects < 1 or args.max_objects > 30:
        raise SystemExit("--max-objects must be between 1 and 30")

    payload = args.objects_tsv.read_bytes()
    objects = pd.read_csv(io.BytesIO(payload), sep="\t")
    objects.columns = [str(c).strip().lower() for c in objects.columns]
    required = {"oid", "ngoodobsrel"}
    if not required.issubset(objects.columns):
        raise SystemExit(f"Objects TSV missing {sorted(required - set(objects.columns))}")
    try:
        objects, eligible_pool_objects = select_candidate_objects(
            objects, args.max_objects, minimum_good_observations=30
        )
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    if objects.empty:
        raise SystemExit("No deterministic DR24 object candidates have ngoodobsrel >= 30.")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    raw_dir = args.output_dir / "raw"
    raw_dir.mkdir(exist_ok=True)
    engine = ScientificFeatureEngine()
    session = requests.Session()
    feature_rows: list[dict[str, Any]] = []
    observations_all: list[pd.DataFrame] = []
    records: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []

    for row in objects.itertuples(index=False):
        oid = str(row.oid)
        try:
            raw_frame, raw_bytes = acquire_lightcurve(session, oid, args.timeout)
            raw_path = raw_dir / f"{oid}.csv"
            raw_path.write_bytes(raw_bytes)
            normalized, metadata = normalize_api_frame(raw_frame)
            if normalized.empty:
                raise ValueError("No g/r-band rows remained after filter normalization.")
            counts = valid_band_counts(normalized)
            result = engine.compute(normalized[["mjd", "fid", "mag", "magerr"]])
            feature_record: dict[str, Any] = {
                "oid": oid,
                "ngoodobsrel": int(row.ngoodobsrel),
                **counts,
                "input_rows": len(normalized),
                "finite_feature_count": int(np.isfinite(np.asarray(list(result.values.values()), dtype=float)).sum()),
                "nan_feature_count": int(np.isnan(np.asarray(list(result.values.values()), dtype=float)).sum()),
                "feature_schema_version": result.feature_schema_version,
                "backend": result.provenance.backend,
                "backend_version": result.provenance.software_version,
                "normalized_observation_sha256": result.provenance.input_observation_sha256,
                "raw_response_sha256": sha256_bytes(raw_bytes),
                "raw_response_path": str(raw_path.relative_to(args.output_dir)),
                "feature_values": result.values,
            }
            feature_rows.append(feature_record)
            observations_all.append(normalized.assign(oid=oid))
            records.append({
                "oid": oid,
                "ngoodobsrel": int(row.ngoodobsrel),
                **metadata,
                **counts,
                "raw_response_sha256": sha256_bytes(raw_bytes),
                "raw_response_path": str(raw_path.relative_to(args.output_dir)),
                "feature_schema_version": result.feature_schema_version,
                "backend": result.provenance.backend,
                "backend_version": result.provenance.software_version,
                "normalized_observation_sha256": result.provenance.input_observation_sha256,
                "feature_finite_count": feature_record["finite_feature_count"],
                "feature_nan_count": feature_record["nan_feature_count"],
            })
        except Exception as exc:
            failures.append({"oid": oid, "error": f"{type(exc).__name__}: {exc}"})
        time.sleep(0.15)

    if not feature_rows:
        raise SystemExit(f"All DR24 lightcurve requests failed: {failures[:5]}")

    feature_columns = [
        "oid", "ngoodobsrel", "g_valid", "r_valid", "input_rows",
        "finite_feature_count", "nan_feature_count", "feature_schema_version",
        "backend", "backend_version", "normalized_observation_sha256",
        "raw_response_sha256", "raw_response_path",
    ]
    pd.DataFrame([{k: r[k] for k in feature_columns} for r in feature_rows]).to_csv(
        args.output_dir / "feature_run_summary.tsv", sep="\t", index=False
    )
    # Preserve the complete feature vectors in JSON (including NaN as null).
    serializable_features = []
    for record in feature_rows:
        serializable_features.append({
            **{k: v for k, v in record.items() if k != "feature_values"},
            "feature_values": {
                key: (float(value) if np.isfinite(float(value)) else None)
                for key, value in record["feature_values"].items()
            },
        })
    report = {
        "status": "PASS_SMOKE_ONLY",
        "scientific_claim": "NOT_A_BENCHMARK_OR_MODEL_ACCURACY_RESULT",
        "source": "IRSA ZTF DR24 Lightcurve API",
        "release": COLLECTION,
        "source_url": API_URL,
        "objects_tsv_sha256": sha256_bytes(payload),
        "objects_tsv_rows": int(len(pd.read_csv(io.BytesIO(payload), sep="\t"))),
        "candidate_objects": int(len(objects)),
        "candidate_selection": {
            "method": "sha256_ranked_within_pinned_objects_table_subset",
            "seed": DR24_SMOKE_SAMPLE_SEED,
            "minimum_ngoodobsrel": 30,
            "eligible_pool_objects": int(eligible_pool_objects),
            "scope_note": "Selection is from the pinned 150-row DR24 object subset, not a representative survey-wide sample.",
        },
        "successful_objects": len(feature_rows),
        "failed_objects": failures,
        "objects": records,
        "feature_results": serializable_features,
        "feature_engine": {
            "backend": "native",
            "feature_schema_version": "v0.2",
            "feature_count": 42,
            "time_note": "IRSA HMJD is passed as the internal relative time coordinate; no absolute-time cutoff is applied in this smoke test.",
            "quality_note": "No catflags mask is applied here because this smoke test exercises the existing production feature path. Flag counts are recorded; this is not a scientific-quality acceptance claim.",
        },
        "model_inference": {
            "status": "NOT_RUN",
            "reason": "The frozen model artifact is not part of the public repository/CI checkout. This run verifies real DR24 acquisition and feature generation only.",
        },
    }
    report_path = args.output_dir / "dr24_lightcurve_smoke_report.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": report["status"],
        "candidate_objects": report["candidate_objects"],
        "successful_objects": report["successful_objects"],
        "failed_objects": len(failures),
        "objects_with_30plus_valid_points_per_band": sum(
            r["g_valid"] >= 30 and r["r_valid"] >= 30 for r in records
        ),
        "feature_schema": "v0.2",
        "features_per_object": 42,
        "model_inference": "NOT_RUN",
        "report": str(report_path),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
