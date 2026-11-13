#!/usr/bin/env python3
"""Phase-fold coverage audit for CPVS residuals and matched Table 4 controls.

This is a research diagnostic only. It does not reproduce MGPR and does not
change or define CPVS catalogue membership.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import statistics
import zipfile
import zlib
from collections import defaultdict
from pathlib import Path
from typing import Any

ARCHIVES = {
    "g": {
        "member": "ztf2g",
        "sha256": "47cd1823b3ccdb69fa3085381cf63ff0605f6d841fc3bc37489dce023ddc19b9",
        "threshold": 2.5,
        "mag_index": 4,
        "err_index": 5,
    },
    "r": {
        "member": "ztf2r",
        "sha256": "48331ba1157afc993a1399e094b97752a82d8d0f736d2fdf63fd7b2a82281b74",
        "threshold": 3.0,
        "mag_index": 4,
        "err_index": 5,
    },
}
LN10_OVER_2P5 = math.log(10.0) / 2.5
HJD_TO_MJD = 2400000.5


def num(value: Any) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def positive(value: Any) -> bool:
    parsed = num(value)
    return parsed is not None and parsed > 0


def parse_tsv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream, delimiter="\t"))


def load_parent(path: Path) -> dict[int, dict[str, str]]:
    result: dict[int, dict[str, str]] = {}
    with path.open("r", encoding="utf-8", newline="") as stream:
        reader = csv.reader(stream, delimiter="\t")
        header: list[str] | None = None
        for row in reader:
            if not row:
                continue
            if row[0].strip() == "Seq":
                header = [x.strip() for x in row]
                continue
            if header is None or not row[0].strip().isdigit():
                continue
            if len(row) != len(header):
                continue
            record = dict(zip(header, (x.strip() for x in row)))
            source_id = int(record["Seq"])
            if source_id in result:
                raise ValueError(f"Duplicate parent Seq: {source_id}")
            result[source_id] = record
    if len(result) != 781602:
        raise ValueError(f"Expected 781602 parent rows, got {len(result)}")
    return result


def choose_targets(parent: dict[int, dict[str, str]], diag: dict[str, Any]) -> list[dict[str, Any]]:
    residual = {int(x["source_id"]) for x in diag["candidate_only_all_objects"]}
    records = [(sid, parent[sid]) for sid in sorted(residual)]
    targets: list[dict[str, Any]] = []

    # All 17 with both mean magnitudes but one missing band-specific period.
    group_17 = [
        (sid, row) for sid, row in records
        if positive(row.get("gmag")) and positive(row.get("rmag"))
        and not (positive(row.get("Per-g")) and positive(row.get("Per-r")))
    ]
    if len(group_17) != 17:
        raise ValueError(f"Expected 17 two-magnitude/incomplete-period objects; got {len(group_17)}")
    targets.extend({"source_id": sid, "cohort": "all_17_both_magnitudes_period_incomplete"} for sid, _ in group_17)

    # All five with both band periods but a missing g-band mean magnitude.
    group_5 = [
        (sid, row) for sid, row in records
        if positive(row.get("Per-g")) and positive(row.get("Per-r"))
        and not (positive(row.get("gmag")) and positive(row.get("rmag")))
    ]
    if len(group_5) != 5:
        raise ValueError(f"Expected 5 two-period/magnitude-incomplete objects; got {len(group_5)}")
    targets.extend({"source_id": sid, "cohort": "all_5_both_periods_magnitude_incomplete"} for sid, _ in group_5)

    # Deterministic fixed sample from the dominant one-band-only fit-output strata.
    only_r_fit = [
        sid for sid, row in records
        if not positive(row.get("gmag")) and not positive(row.get("Per-g"))
        and positive(row.get("rmag")) and positive(row.get("Per-r"))
    ]
    only_g_fit = [
        sid for sid, row in records
        if positive(row.get("gmag")) and positive(row.get("Per-g"))
        and not positive(row.get("rmag")) and not positive(row.get("Per-r"))
    ]
    if len(only_r_fit) != 11465 or len(only_g_fit) != 115:
        raise ValueError(
            f"Unexpected one-band strata sizes: r-only={len(only_r_fit)}, g-only={len(only_g_fit)}"
        )

    def fixed_even_sample(values: list[int], n: int) -> list[int]:
        if len(values) < n:
            raise ValueError("Insufficient members for fixed sample")
        return [values[(i * len(values)) // n] for i in range(n)]

    targets.extend({"source_id": sid, "cohort": "fixed_10_g_fit_missing"} for sid in fixed_even_sample(only_r_fit, 10))
    targets.extend({"source_id": sid, "cohort": "fixed_10_r_fit_missing"} for sid in fixed_even_sample(only_g_fit, 10))

    if len({x["source_id"] for x in targets}) != len(targets):
        raise ValueError("Target cohorts overlap unexpectedly")
    return targets


def choose_controls(
    parent: dict[int, dict[str, str]],
    selected_ids: set[int],
    residual_ids: set[int],
    targets: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    published_ids = selected_ids - residual_ids
    used: set[int] = set()
    controls: list[dict[str, Any]] = []

    features = ("Per", "gmag", "rmag", "Ng", "Nr")
    for target in targets:
        sid = int(target["source_id"])
        tr = parent[sid]
        target_type = tr.get("Type", "")
        target_values = {k: num(tr.get(k)) for k in features}
        candidates: list[tuple[float, int]] = []
        for candidate_id in published_ids:
            if candidate_id in used:
                continue
            row = parent[candidate_id]
            if row.get("Type", "") != target_type:
                continue
            if not all(positive(row.get(k)) for k in ("Per", "gmag", "rmag", "Ng", "Nr")):
                continue
            values = {k: num(row.get(k)) for k in features}
            # Log distance for period and count; magnitude distance in mag units.
            deltas = []
            for key in features:
                a, b = target_values[key], values[key]
                if a is None or b is None or a <= 0 or b <= 0:
                    deltas.append(2.0)
                elif key in {"Per", "Ng", "Nr"}:
                    deltas.append(abs(math.log(b / a)))
                else:
                    deltas.append(abs(b - a) / 0.5)
            score = math.sqrt(sum(x * x for x in deltas))
            candidates.append((score, candidate_id))
        if not candidates:
            raise ValueError(f"No same-type published control for SourceID={sid}, Type={target_type}")
        candidates.sort()
        control_id = candidates[0][1]
        used.add(control_id)
        controls.append({
            "source_id": control_id,
            "cohort": "matched_table4_control",
            "matched_target_source_id": sid,
            "match_distance": candidates[0][0],
        })
    return controls


def parse_line(raw: bytes) -> list[str]:
    text = raw.decode("utf-8", errors="strict").strip()
    if not text or text.startswith("#"):
        return []
    if "\t" in text:
        return [x.strip() for x in text.split("\t")]
    if "," in text:
        return [x.strip() for x in next(csv.reader([text]))]
    return text.split()


def phase_metrics(phases: list[float], bins: int = 160) -> dict[str, Any]:
    if not phases:
        return {
            "n": 0, "unique_phases": 0, "occupied_bins_160": 0,
            "coverage_bins_160": 0.0, "max_circular_phase_gap": None,
            "median_circular_phase_gap": None,
        }
    wrapped = sorted(x % 1.0 for x in phases if math.isfinite(x))
    if not wrapped:
        return {
            "n": 0, "unique_phases": 0, "occupied_bins_160": 0,
            "coverage_bins_160": 0.0, "max_circular_phase_gap": None,
            "median_circular_phase_gap": None,
        }
    unique = sorted(set(round(x, 12) for x in wrapped))
    gaps = [
        unique[i + 1] - unique[i] for i in range(len(unique) - 1)
    ] + [unique[0] + 1.0 - unique[-1]]
    occupied = {min(bins - 1, int(x * bins)) for x in wrapped}
    return {
        "n": len(wrapped),
        "unique_phases": len(unique),
        "occupied_bins_160": len(occupied),
        "coverage_bins_160": len(occupied) / bins,
        "max_circular_phase_gap": max(gaps),
        "median_circular_phase_gap": statistics.median(gaps),
    }


def scan_archive(
    archive_path: Path,
    band: str,
    objects: dict[int, dict[str, Any]],
) -> dict[str, Any]:
    config = ARCHIVES[band]
    digest = hashlib.sha256()
    member_digest = hashlib.sha256()
    member_bytes = 0
    member_crc = 0
    malformed = 0
    rows_total = 0

    observed: dict[int, dict[str, Any]] = {
        sid: {"valid": [], "snr_qualified": [], "flag_lt_32768": [], "flag_zero": [], "raw_rows": 0,
              "flag_counts": defaultdict(int)}
        for sid in objects
    }

    h = hashlib.sha256()
    with archive_path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    if h.hexdigest() != config["sha256"]:
        raise ValueError(f"{band} archive SHA-256 mismatch: {h.hexdigest()}")

    with zipfile.ZipFile(archive_path) as archive:
        members = [name for name in archive.namelist() if Path(name).name == config["member"] and "__MACOSX" not in name]
        if len(members) != 1:
            raise ValueError(f"Expected one {config['member']} member; found {members}")
        member_name = members[0]
        info = archive.getinfo(member_name)
        with archive.open(member_name, "r") as stream:
            for raw in stream:
                member_digest.update(raw)
                member_bytes += len(raw)
                member_crc = zlib.crc32(raw, member_crc)
                try:
                    fields = parse_line(raw)
                except (UnicodeDecodeError, csv.Error):
                    malformed += 1
                    continue
                if not fields:
                    continue
                if len(fields) != 7:
                    malformed += 1
                    continue
                try:
                    sid = int(fields[0])
                except ValueError:
                    # Some files contain column headers. They do not count as data rows.
                    continue
                rows_total += 1
                if sid not in observed:
                    continue
                item = observed[sid]
                item["raw_rows"] += 1
                item["flag_counts"][fields[6]] += 1
                hjd, mag, magerr = num(fields[3]), num(fields[4]), num(fields[5])
                if hjd is None or mag is None or mag == 0 or magerr is None or magerr <= 0:
                    continue
                snr = 1.0 / math.expm1(magerr * LN10_OVER_2P5)
                flag = None
                try:
                    flag = int(fields[6])
                except (TypeError, ValueError):
                    pass
                phase = ((hjd - HJD_TO_MJD) / objects[sid]["period"]) % 1.0
                row = {"phase": phase, "magnitude": mag, "mag_error": magerr, "snr_exact": snr}
                item["valid"].append(row)
                if snr >= config["threshold"]:
                    item["snr_qualified"].append(row)
                if flag is not None and flag < 32768:
                    item["flag_lt_32768"].append(row)
                if flag == 0:
                    item["flag_zero"].append(row)

        member_sha = member_digest.hexdigest()
        if member_bytes != info.file_size:
            raise ValueError(f"{band} member size mismatch: {member_bytes} != {info.file_size}")
        if member_crc & 0xFFFFFFFF != info.CRC:
            raise ValueError(f"{band} member CRC mismatch")
        if malformed:
            raise ValueError(f"{band} archive has {malformed} malformed rows")

    for sid, item in observed.items():
        item["flag_counts"] = dict(sorted(item["flag_counts"].items()))
        for key in ("valid", "snr_qualified", "flag_lt_32768", "flag_zero"):
            item[key] = phase_metrics([x["phase"] for x in item[key]])
    return {
        "archive_sha256": config["sha256"],
        "member_sha256": member_sha,
        "member_bytes": member_bytes,
        "rows_total": rows_total,
        "malformed_rows": malformed,
        "objects": observed,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--g-archive", type=Path, required=True)
    parser.add_argument("--r-archive", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    root = args.input_dir
    data_dir = root / "ztf_periodic_730k"
    parent = load_parent(data_dir / "parent_metadata.tsv")
    diag = json.loads((data_dir / "selection_diagnostics.json").read_text(encoding="utf-8"))
    selected_rows = parse_tsv(data_dir / "selected.tsv")
    selected = {int(x["SourceID"]) for x in selected_rows}
    residual = {int(x["source_id"]) for x in diag["candidate_only_all_objects"]}

    targets = choose_targets(parent, diag)
    controls = choose_controls(parent, selected, residual, targets)
    all_objects = targets + controls
    meta: dict[int, dict[str, Any]] = {}
    for item in all_objects:
        sid = int(item["source_id"])
        row = parent[sid]
        period = num(row.get("Per"))
        if period is None or period <= 0:
            raise ValueError(f"Common period missing for SourceID={sid}")
        meta[sid] = {
            **item,
            "type": row.get("Type"),
            "period": period,
            "gmag": num(row.get("gmag")),
            "rmag": num(row.get("rmag")),
            "period_g": num(row.get("Per-g")),
            "period_r": num(row.get("Per-r")),
            "ng": num(row.get("Ng")),
            "nr": num(row.get("Nr")),
        }

    args.output_dir.mkdir(parents=True, exist_ok=True)
    band_results = {}
    for band, path in (("g", args.g_archive), ("r", args.r_archive)):
        band_results[band] = scan_archive(path, band, meta)

    records: list[dict[str, Any]] = []
    for sid, obj in meta.items():
        g = band_results["g"]["objects"][sid]
        r = band_results["r"]["objects"][sid]
        records.append({
            "SourceID": sid,
            "cohort": obj["cohort"],
            "matched_target_SourceID": obj.get("matched_target_source_id"),
            "Type": obj["type"],
            "Per": obj["period"],
            "gmag": obj["gmag"],
            "rmag": obj["rmag"],
            "Per-g": obj["period_g"],
            "Per-r": obj["period_r"],
            "Ng_Table2": obj["ng"],
            "Nr_Table2": obj["nr"],
            "g_raw_rows": g["raw_rows"],
            "r_raw_rows": r["raw_rows"],
            "g_valid_n": g["valid"]["n"],
            "r_valid_n": r["valid"]["n"],
            "g_snr_qualified_n": g["snr_qualified"]["n"],
            "r_snr_qualified_n": r["snr_qualified"]["n"],
            "g_phase_bins_160": g["valid"]["occupied_bins_160"],
            "r_phase_bins_160": r["valid"]["occupied_bins_160"],
            "g_max_phase_gap": g["valid"]["max_circular_phase_gap"],
            "r_max_phase_gap": r["valid"]["max_circular_phase_gap"],
            "g_median_phase_gap": g["valid"]["median_circular_phase_gap"],
            "r_median_phase_gap": r["valid"]["median_circular_phase_gap"],
            "g_phase_coverage": g["valid"]["coverage_bins_160"],
            "r_phase_coverage": r["valid"]["coverage_bins_160"],
            "g_flag_lt32768_valid_n": g["flag_lt_32768"]["n"],
            "r_flag_lt32768_valid_n": r["flag_lt_32768"]["n"],
            "g_flag_counts": json.dumps(g["flag_counts"], sort_keys=True),
            "r_flag_counts": json.dumps(r["flag_counts"], sort_keys=True),
            "control_match_distance": obj.get("match_distance"),
        })

    records.sort(key=lambda x: (x["cohort"], x["SourceID"]))
    out_tsv = args.output_dir / "cpvs_phasefold_coverage_objects.tsv"
    with out_tsv.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(records[0]), delimiter="\t")
        writer.writeheader()
        writer.writerows(records)

    def group_summary(cohort: str, band: str) -> dict[str, Any]:
        selected_records = [x for x in records if x["cohort"] == cohort]
        key_bins = f"{band}_phase_bins_160"
        key_gap = f"{band}_max_phase_gap"
        key_coverage = f"{band}_phase_coverage"
        values = [x[key_bins] for x in selected_records]
        gaps = [x[key_gap] for x in selected_records if x[key_gap] is not None]
        coverages = [x[key_coverage] for x in selected_records]
        return {
            "n_objects": len(selected_records),
            "phase_bins_160_median": statistics.median(values) if values else None,
            "phase_bins_160_min": min(values) if values else None,
            "max_phase_gap_median": statistics.median(gaps) if gaps else None,
            "max_phase_gap_max": max(gaps) if gaps else None,
            "phase_coverage_median": statistics.median(coverages) if coverages else None,
        }

    cohorts = sorted({x["cohort"] for x in records})
    summary = {
        "status": "PHASE_FOLD_COVERAGE_DIAGNOSTIC_COMPLETE",
        "scientific_validation_status": "NOT_VALIDATED",
        "interpretation": (
            "This tests whether the shared Table 2 Per supports phase-folded g/r inputs. "
            "It does not run MGPR, prove interpolation quality, or reproduce CPVS membership."
        ),
        "source_run": 38635891449,
        "raw_archive_checks": {
            band: {
                "archive_sha256": result["archive_sha256"],
                "member_sha256": result["member_sha256"],
                "member_bytes": result["member_bytes"],
                "rows_total": result["rows_total"],
                "malformed_rows": result["malformed_rows"],
            }
            for band, result in band_results.items()
        },
        "target_counts": {
            "both_magnitudes_period_incomplete": 17,
            "both_periods_magnitude_incomplete": 5,
            "fixed_g_fit_missing_sample": 10,
            "fixed_r_fit_missing_sample": 10,
            "matched_table4_controls": len(controls),
            "total_objects": len(records),
        },
        "target_source_ids": [x["source_id"] for x in targets],
        "control_source_ids": [x["source_id"] for x in controls],
        "cohort_metrics": {
            cohort: {
                "g": group_summary(cohort, "g"),
                "r": group_summary(cohort, "r"),
            }
            for cohort in cohorts
        },
        "row_count_mismatches": [
            {
                "SourceID": x["SourceID"],
                "Ng_Table2": x["Ng_Table2"],
                "Nr_Table2": x["Nr_Table2"],
                "g_raw_rows": x["g_raw_rows"],
                "r_raw_rows": x["r_raw_rows"],
            }
            for x in records
            if x["Ng_Table2"] != x["g_raw_rows"] or x["Nr_Table2"] != x["r_raw_rows"]
        ],
        "limitations": [
            "Zenodo g_flag/r_flag are reported but not assumed to be identical to catflags.",
            "The archive does not contain image-level INFOBITS.",
            "Phase coverage is not MGPR convergence or scientific membership validation.",
            "The original paper's exact GP initialization and optimization bounds are not fully specified in the text.",
            "Controls are nearest same-Type Table 4 members selected by period, magnitudes and observation counts; they are diagnostic matches, not a random control sample.",
        ],
    }
    (args.output_dir / "cpvs_phasefold_coverage_report.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
