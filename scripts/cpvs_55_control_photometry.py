#!/usr/bin/env python3
"""Retrieve original CPVS g/r photometry for the 55 four-field-only controls."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import pathlib
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from datetime import UTC, datetime
from typing import Any

VIZIER_URL = "https://vizier.nao.ac.jp/viz-bin/asu-tsv"
SNR_FACTOR = 1.0857362047581296
LN10_OVER_2P5 = math.log(10.0) / 2.5
USER_AGENT = "ztf-classifier-cpvs-control-audit/1.0"


def parse_vizier_tsv(payload: bytes, expected_seq: str) -> list[dict[str, str]]:
    """Parse one VizieR TSV response while ignoring units/type/separator rows."""
    text = payload.decode("utf-8-sig", errors="strict")
    lines = [
        line.rstrip("\r\n")
        for line in text.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    header_index = None
    header: list[str] = []
    for index, line in enumerate(lines):
        fields = next(csv.reader([line], delimiter="\t"))
        normalized = [field.strip() for field in fields]
        if {"Seq", "MJD", "mag", "e_mag", "flag"}.issubset(normalized):
            header_index = index
            header = normalized
            break
    if header_index is None:
        raise ValueError("VizieR response has no Seq/MJD/mag/e_mag/flag header")
    result: list[dict[str, str]] = []
    for line in lines[header_index + 1 :]:
        fields = next(csv.reader([line], delimiter="\t"))
        if len(fields) != len(header):
            continue
        row = dict(zip(header, (value.strip() for value in fields), strict=True))
        seq = row.get("Seq", "")
        if not seq.isdecimal():
            continue
        if seq != expected_seq:
            continue
        result.append(row)
    return result


def finite_float(value: object) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def band_metrics(rows: list[dict[str, str]], threshold: float) -> dict[str, Any]:
    """Apply the historical magnitude-error SNR rule and retain alternatives."""
    valid = []
    qualifying = []
    exact_qualifying = []
    inverse_error_qualifying = []
    flags: Counter[str] = Counter()
    for row in rows:
        magnitude = finite_float(row.get("mag"))
        error = finite_float(row.get("e_mag"))
        if magnitude is None or magnitude == 0 or error is None or error <= 0:
            continue
        approximate_snr = SNR_FACTOR / error
        try:
            exact_snr = 1.0 / math.expm1(error * LN10_OVER_2P5)
        except (OverflowError, ZeroDivisionError):
            exact_snr = 0.0
        inverse_error_snr = 1.0 / error
        item = {
            "magnitude": magnitude,
            "error": error,
            "approximate_snr": approximate_snr,
            "exact_snr": exact_snr,
            "inverse_error_snr": inverse_error_snr,
        }
        valid.append(item)
        if approximate_snr >= threshold:
            qualifying.append(item)
        if exact_snr >= threshold:
            exact_qualifying.append(item)
        if inverse_error_snr >= threshold:
            inverse_error_qualifying.append(item)
        raw_flag = row.get("flag", "").strip()
        if raw_flag:
            flags[raw_flag] += 1

    return {
        "row_count": len(rows),
        "valid_photometry_rows": len(valid),
        "qualifying_detections_approximate": len(qualifying),
        "qualifying_detections_exact": len(exact_qualifying),
        "qualifying_detections_inverse_error": len(inverse_error_qualifying),
        "passes_approximate_snr": bool(qualifying),
        "passes_exact_snr": bool(exact_qualifying),
        "passes_inverse_error_snr": bool(inverse_error_qualifying),
        "max_approximate_snr": max(
            (item["approximate_snr"] for item in valid), default=None
        ),
        "max_exact_snr": max((item["exact_snr"] for item in valid), default=None),
        "minimum_magnitude_error": min(
            (item["error"] for item in valid), default=None
        ),
        "qualifying_flag_counts": dict(sorted(flags.items())),
    }


def request_rows(
    seq: str, band: str, raw_dir: pathlib.Path, retries: int = 3
) -> tuple[list[dict[str, str]], dict[str, Any]]:
    table = f"ztf2{band}"
    params = {
        "-source": f"J/ApJS/249/18/{table}",
        "-out": "Seq,MJD,mag,e_mag,flag",
        "-out.max": "10000",
        "Seq": seq,
    }
    url = VIZIER_URL + "?" + urllib.parse.urlencode(params)
    raw_dir.mkdir(parents=True, exist_ok=True)
    raw_path = raw_dir / f"{table}_seq_{seq}.tsv"
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            request = urllib.request.Request(
                url, headers={"User-Agent": USER_AGENT, "Accept": "text/tab-separated-values"}
            )
            with urllib.request.urlopen(request, timeout=60) as response:
                payload = response.read()
                status = response.status
            raw_path.write_bytes(payload)
            rows = parse_vizier_tsv(payload, seq)
            return rows, {
                "status": "OK",
                "http_status": status,
                "url": url,
                "response_bytes": len(payload),
                "response_sha256": hashlib.sha256(payload).hexdigest(),
                "response_file": raw_path.name,
                "rows_returned": len(rows),
                "attempts": attempt,
            }
        except (
            urllib.error.URLError,
            TimeoutError,
            UnicodeDecodeError,
            ValueError,
        ) as exc:
            last_error = f"{type(exc).__name__}: {exc}"
            time.sleep(min(2**attempt, 8))
    return [], {
        "status": "ERROR",
        "url": url,
        "error": last_error or "unknown request error",
        "attempts": retries,
    }


def read_controls(path: pathlib.Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream, delimiter="\t")
        required = {"SourceID", "ZTF", "Ng", "Nr", "candidate", "Table4_member"}
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise ValueError(
                f"Control TSV missing required columns: {sorted(required)}"
            )
        rows = list(reader)
    if len(rows) != 55:
        raise ValueError(f"Expected 55 four-field-only controls, got {len(rows)}")
    if len({row["SourceID"] for row in rows}) != 55:
        raise ValueError("Control TSV contains duplicate SourceIDs")
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--controls", type=pathlib.Path, required=True)
    parser.add_argument("--output", type=pathlib.Path, required=True)
    parser.add_argument("--delay-seconds", type=float, default=0.25)
    args = parser.parse_args()

    controls = read_controls(args.controls)
    args.output.mkdir(parents=True, exist_ok=True)
    raw_dir = args.output / "raw_queries"
    query_manifest: list[dict[str, Any]] = []
    object_results: list[dict[str, Any]] = []
    per_band_fields = [
        "SourceID",
        "ZTF",
        "band",
        "table2_expected_rows",
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
        "query_status",
        "response_sha256",
        "response_bytes",
        "error",
    ]
    per_band_rows: list[dict[str, Any]] = []

    for index, control in enumerate(controls):
        seq = control["SourceID"].strip()
        per_object: dict[str, Any] = {
            "SourceID": seq,
            "ZTF": control["ZTF"],
            "historical_candidate_member": control["candidate"].lower() == "true",
            "Table4_member": control["Table4_member"].lower() == "true",
            "Table2_Ng": int(float(control["Ng"])),
            "Table2_Nr": int(float(control["Nr"])),
            "bands": {},
        }
        for band, threshold, count_key in (
            ("g", 2.5, "Ng"),
            ("r", 3.0, "Nr"),
        ):
            rows, query = request_rows(seq, band, raw_dir)
            query_manifest.append(
                {"SourceID": seq, "ZTF": control["ZTF"], "band": band, **query}
            )
            metrics = band_metrics(rows, threshold) if query["status"] == "OK" else {}
            per_object["bands"][band] = {
                "query_status": query["status"],
                **metrics,
            }
            per_band_rows.append(
                {
                    "SourceID": seq,
                    "ZTF": control["ZTF"],
                    "band": band,
                    "table2_expected_rows": control[count_key],
                    "row_count": len(rows),
                    "valid_photometry_rows": metrics.get("valid_photometry_rows"),
                    "qualifying_detections_approximate": metrics.get(
                        "qualifying_detections_approximate"
                    ),
                    "qualifying_detections_exact": metrics.get(
                        "qualifying_detections_exact"
                    ),
                    "qualifying_detections_inverse_error": metrics.get(
                        "qualifying_detections_inverse_error"
                    ),
                    "passes_approximate_snr": metrics.get("passes_approximate_snr"),
                    "passes_exact_snr": metrics.get("passes_exact_snr"),
                    "passes_inverse_error_snr": metrics.get(
                        "passes_inverse_error_snr"
                    ),
                    "max_approximate_snr": metrics.get("max_approximate_snr"),
                    "max_exact_snr": metrics.get("max_exact_snr"),
                    "minimum_magnitude_error": metrics.get(
                        "minimum_magnitude_error"
                    ),
                    "query_status": query["status"],
                    "response_sha256": query.get("response_sha256"),
                    "response_bytes": query.get("response_bytes"),
                    "error": query.get("error"),
                }
            )
            time.sleep(max(0.0, args.delay_seconds))
        g = per_object["bands"]["g"]
        r = per_object["bands"]["r"]
        per_object["historical_candidate_reconstructed"] = (
            g.get("passes_approximate_snr") is True
            and r.get("passes_approximate_snr") is True
        )
        per_object["failed_approximate_snr_bands"] = [
            band
            for band, metrics in (("g", g), ("r", r))
            if metrics.get("query_status") != "OK"
            or metrics.get("passes_approximate_snr") is not True
        ]
        per_object["query_complete"] = all(
            per_object["bands"][band].get("query_status") == "OK"
            for band in ("g", "r")
        )
        object_results.append(per_object)
        if (index + 1) % 10 == 0:
            print(f"Queried {index + 1}/{len(controls)} control objects", flush=True)

    with (args.output / "per_band_snr_metrics.tsv").open(
        "w", encoding="utf-8", newline=""
    ) as stream:
        writer = csv.DictWriter(
            stream, fieldnames=per_band_fields, delimiter="\t", lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(per_band_rows)

    (args.output / "per_object_snr_metrics.json").write_text(
        json.dumps(object_results, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    (args.output / "query_manifest.json").write_text(
        json.dumps(query_manifest, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    successful_queries = sum(item["status"] == "OK" for item in query_manifest)
    reconstructed_candidates = [
        item
        for item in object_results
        if item.get("historical_candidate_reconstructed") is True
    ]
    report = {
        "status": "COMPLETE" if successful_queries == 110 else "PARTIAL",
        "source": "VizieR J/ApJS/249/18 ztf2g and ztf2r",
        "retrieved_utc": datetime.now(UTC).isoformat(),
        "control_count": len(controls),
        "query_count": len(query_manifest),
        "successful_queries": successful_queries,
        "failed_queries": 110 - successful_queries,
        "historical_candidate_controls": 0,
        "controls_reconstructed_as_two_band_snr_candidates": len(
            reconstructed_candidates
        ),
        "candidate_reconstruction_contradictions": [
            item["SourceID"] for item in reconstructed_candidates
        ],
        "all_controls_have_no_table4_membership": all(
            item["Table4_member"] is False for item in object_results
        ),
        "all_controls_have_no_historical_candidate_membership": all(
            item["historical_candidate_member"] is False for item in object_results
        ),
        "all_successful_queries_have_raw_response_hashes": all(
            item.get("response_sha256")
            for item in query_manifest
            if item["status"] == "OK"
        ),
        "limitations": [
            "The queried rows are the original CDS CPVS ztf2g/ztf2r tables, not current ZTF DR24 lightcurves.",
            "This audit tests the historical per-band SNR predicate only; it does not establish author intent for the four-field metadata condition.",
            "A query error or empty table result must be distinguished using query_manifest.json and the retained raw response bytes.",
        ],
    }
    (args.output / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
