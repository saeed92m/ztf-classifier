#!/usr/bin/env python3
"""Audit original Zenodo g/r photometry for the 55 CPVS control objects."""

from __future__ import annotations

import argparse
import csv
import gzip
import json
import math
import pathlib
import re
from collections import Counter
from datetime import UTC, datetime
from typing import Any

SNR_FACTOR = 1.0857362047581296
LN10_OVER_2P5 = math.log(10.0) / 2.5


def finite_float(value: object) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def read_controls(path: pathlib.Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream, delimiter="\t")
        required = {"SourceID", "ZTF", "Ng", "Nr", "candidate", "Table4_member"}
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise ValueError(f"Control TSV missing columns: {sorted(required)}")
        rows = list(reader)
    if len(rows) != 55 or len({row["SourceID"] for row in rows}) != 55:
        raise ValueError(f"Expected 55 unique controls, got {len(rows)}")
    return rows


def split_fields(line: str) -> list[str]:
    stripped = line.strip()
    if "\t" in stripped:
        return [value.strip() for value in stripped.split("\t")]
    if "," in stripped:
        return [value.strip() for value in next(csv.reader([stripped], delimiter=","))]
    return re.split(r"\s+", stripped)


def iter_photometry_rows(path: pathlib.Path, error_column: str, mag_column: str):
    """Stream original Zenodo files using their documented named columns."""
    candidates = (
        [path]
        if path.is_file()
        else sorted(
            item
            for item in path.rglob("*")
            if item.is_file()
            and item.suffix.lower() in {".csv", ".txt", ".dat", ".gz", ""}
        )
    )
    matched_files = 0
    for candidate in candidates:
        opener = gzip.open if candidate.suffix.lower() == ".gz" else open
        with opener(candidate, "rt", encoding="utf-8", errors="replace", newline="") as stream:
            header = None
            indexes = None
            for line in stream:
                if not line.strip():
                    continue
                header_candidate = line.strip()
                if header_candidate.startswith("#"):
                    header_candidate = header_candidate[1:].strip()
                fields = split_fields(header_candidate)
                normalized = {value.strip().lower(): index for index, value in enumerate(fields)}
                required = {"sourceid", mag_column.lower(), error_column.lower()}
                if required.issubset(normalized):
                    header = fields
                    indexes = normalized
                    break
            if header is None or indexes is None:
                continue
            matched_files += 1
            for line in stream:
                if not line.strip() or line.lstrip().startswith("#"):
                    continue
                values = split_fields(line)
                if len(values) != len(header):
                    continue
                yield {
                    name: values[index]
                    for name, index in indexes.items()
                    if index < len(values)
                }
    if matched_files == 0:
        raise ValueError(
            f"No original photometry file below {path} has SourceID, {mag_column}, and {error_column}"
        )


def summarize_band(
    path: pathlib.Path,
    source_ids: set[str],
    error_column: str,
    mag_column: str,
    flag_columns: tuple[str, ...],
    threshold: float,
) -> dict[str, dict[str, Any]]:
    """Scan all original band files once and retain rows for the 55 controls."""
    result = {
        source_id: {
            "row_count": 0,
            "valid_photometry_rows": 0,
            "qualifying_detections_approximate": 0,
            "qualifying_detections_exact": 0,
            "qualifying_detections_inverse_error": 0,
            "passes_approximate_snr": False,
            "passes_exact_snr": False,
            "passes_inverse_error_snr": False,
            "max_approximate_snr": None,
            "max_exact_snr": None,
            "minimum_magnitude_error": None,
            "qualifying_flag_counts": {},
        }
        for source_id in source_ids
    }
    flags = {source_id: Counter() for source_id in source_ids}
    for row in _iter_rows(
        path, required_columns=("SourceID", error_column, mag_column)
    ):
        source_id = str(row.get("SourceID", "")).strip()
        if source_id not in result:
            continue
        item = result[source_id]
        item["row_count"] += 1
        magnitude = finite_float(row.get(mag_column))
        error = finite_float(row.get(error_column))
        if magnitude is None or magnitude == 0 or error is None or error <= 0:
            continue

        item["valid_photometry_rows"] += 1
        approximate_snr = SNR_FACTOR / error
        try:
            exact_snr = 1.0 / math.expm1(error * LN10_OVER_2P5)
        except (OverflowError, ZeroDivisionError):
            exact_snr = 0.0
        inverse_error_snr = 1.0 / error

        item["max_approximate_snr"] = max(
            approximate_snr,
            item["max_approximate_snr"]
            if item["max_approximate_snr"] is not None
            else approximate_snr,
        )
        item["max_exact_snr"] = max(
            exact_snr,
            item["max_exact_snr"] if item["max_exact_snr"] is not None else exact_snr,
        )
        item["minimum_magnitude_error"] = min(
            error,
            item["minimum_magnitude_error"]
            if item["minimum_magnitude_error"] is not None
            else error,
        )

        if approximate_snr >= threshold:
            item["qualifying_detections_approximate"] += 1
            item["passes_approximate_snr"] = True
            flag_key = next(
                (
                    key
                    for key in row
                    if key.strip().lower() in {name.lower() for name in flag_columns}
                ),
                None,
            )
            if flag_key is not None and str(row[flag_key]).strip():
                flags[source_id][str(row[flag_key]).strip()] += 1
        if exact_snr >= threshold:
            item["qualifying_detections_exact"] += 1
            item["passes_exact_snr"] = True
        if inverse_error_snr >= threshold:
            item["qualifying_detections_inverse_error"] += 1
            item["passes_inverse_error_snr"] = True

    for source_id, item in result.items():
        item["qualifying_flag_counts"] = dict(sorted(flags[source_id].items()))
    return result


def run_audit(
    controls_path: pathlib.Path,
    g_path: pathlib.Path,
    r_path: pathlib.Path,
    output: pathlib.Path,
) -> dict[str, Any]:
    controls = read_controls(controls_path)
    ids = {row["SourceID"].strip() for row in controls}
    g = summarize_band(
        g_path, ids, "e_gmag", "gmag", ("g_flag", "catflags", "flag"), 2.5
    )
    r = summarize_band(
        r_path, ids, "e_rmag", "rmag", ("r_flag", "catflags", "flag"), 3.0
    )
    output.mkdir(parents=True, exist_ok=True)

    per_object = []
    for control in controls:
        source_id = control["SourceID"].strip()
        g_item, r_item = g[source_id], r[source_id]
        per_object.append(
            {
                "SourceID": source_id,
                "ZTF": control["ZTF"],
                "Table2_Ng": int(float(control["Ng"])),
                "Table2_Nr": int(float(control["Nr"])),
                "historical_candidate_member": control["candidate"].lower() == "true",
                "Table4_member": control["Table4_member"].lower() == "true",
                "g": g_item,
                "r": r_item,
                "g_row_count_matches_table2_Ng": g_item["row_count"]
                == int(float(control["Ng"])),
                "r_row_count_matches_table2_Nr": r_item["row_count"]
                == int(float(control["Nr"])),
                "reconstructed_two_band_snr_candidate": (
                    g_item["passes_approximate_snr"]
                    and r_item["passes_approximate_snr"]
                ),
                "failed_approximate_snr_bands": [
                    band
                    for band, metrics in (("g", g_item), ("r", r_item))
                    if not metrics["passes_approximate_snr"]
                ],
            }
        )

    per_band_rows = []
    for band, values in (("g", g), ("r", r)):
        for source_id, item in sorted(values.items(), key=lambda pair: int(pair[0])):
            per_band_rows.append(
                {
                    "SourceID": source_id,
                    "band": band,
                    **{
                        key: item[key]
                        for key in (
                            "row_count",
                            "valid_photometry_rows",
                            "qualifying_detections_approximate",
                            "qualifying_detections_exact",
                            "qualifying_detections_inverse_error",
                            "passes_approximate_snr",
                            "passes_exact_snr",
                            "passes_inverse_error_snr",
                            "max_approximate_snr",
                            "max_exact_snr",
                            "minimum_magnitude_error",
                        )
                    },
                }
            )
    with (output / "per_band_snr_metrics.tsv").open(
        "w", encoding="utf-8", newline=""
    ) as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=list(per_band_rows[0]),
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(per_band_rows)

    (output / "per_object_snr_metrics.json").write_text(
        json.dumps(per_object, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    complete = all(
        item["g"]["row_count"] > 0 and item["r"]["row_count"] > 0 for item in per_object
    )
    report = {
        "status": "COMPLETE" if complete else "PARTIAL",
        "source": "Zenodo 10.5281/zenodo.3886372 original ztf2g.zip and ztf2r.zip",
        "retrieved_utc": datetime.now(UTC).isoformat(),
        "control_count": len(controls),
        "g_objects_with_photometry": sum(item["row_count"] > 0 for item in g.values()),
        "r_objects_with_photometry": sum(item["row_count"] > 0 for item in r.values()),
        "g_row_counts_match_Table2_Ng": sum(
            item["g_row_count_matches_table2_Ng"] for item in per_object
        ),
        "r_row_counts_match_Table2_Nr": sum(
            item["r_row_count_matches_table2_Nr"] for item in per_object
        ),
        "reconstructed_as_two_band_snr_candidates": sum(
            item["reconstructed_two_band_snr_candidate"] for item in per_object
        ),
        "controls_reconstructed_as_candidates": [
            item["SourceID"]
            for item in per_object
            if item["reconstructed_two_band_snr_candidate"]
        ],
        "failed_g_snr": sum(
            "g" in item["failed_approximate_snr_bands"] for item in per_object
        ),
        "failed_r_snr": sum(
            "r" in item["failed_approximate_snr_bands"] for item in per_object
        ),
        "all_controls_are_nonmembers": all(
            not item["historical_candidate_member"] and not item["Table4_member"]
            for item in per_object
        ),
        "limitations": [
            "This re-evaluates the historical per-band SNR predicate on the original archived light curves.",
            "It does not establish author intent for the four-field Table 2 metadata condition.",
            "A mismatch between row_count and Table2 Ng/Nr must be investigated before interpreting SNR results.",
        ],
    }
    (output / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--controls", type=pathlib.Path, required=True)
    parser.add_argument("--g", type=pathlib.Path, required=True)
    parser.add_argument("--r", type=pathlib.Path, required=True)
    parser.add_argument("--output", type=pathlib.Path, required=True)
    args = parser.parse_args()
    run_audit(args.controls, args.g, args.r, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
