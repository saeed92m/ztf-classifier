#!/usr/bin/env python3
"""Compare the 11,602 CPVS residuals with Chen et al.'s suspected-variable table."""
from __future__ import annotations
import argparse, csv, hashlib, json, math, zipfile, zlib
from collections import Counter
from pathlib import Path
from typing import Any

EXPECTED_TABLE6_MD5 = "fcad26b036c8dbee29f6d868fecc9697"
EXPECTED_TABLE6_ROWS = 1_381_527
EXPECTED_RESIDUALS = 11_602
SKIP_HEADER_LINES = 20


def archive_md5(path: Path) -> str:
    digest = hashlib.md5()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_table6_ids(
    archive_path: Path,
    *,
    expected_md5: str = EXPECTED_TABLE6_MD5,
    expected_rows: int | None = EXPECTED_TABLE6_ROWS,
) -> tuple[set[str], dict[str, Any]]:
    observed_md5 = archive_md5(archive_path)
    if observed_md5 != expected_md5:
        raise ValueError(f"Table 6 archive MD5 mismatch: {observed_md5} != {expected_md5}")
    with zipfile.ZipFile(archive_path) as archive:
        members = [
            info for info in archive.infolist()
            if not info.is_dir() and not info.filename.startswith("__MACOSX/")
        ]
        if len(members) != 1:
            raise ValueError(f"Expected one Table 6 data member, found {[x.filename for x in members]}")
        info = members[0]
        ids: set[str] = set()
        field_counts: Counter[int] = Counter()
        malformed_lines = 0
        rows = 0
        member_sha = hashlib.sha256()
        member_crc = 0
        member_bytes = 0
        with archive.open(info, "r") as stream:
            for line_number, raw in enumerate(stream, start=1):
                member_sha.update(raw)
                member_crc = zlib.crc32(raw, member_crc)
                member_bytes += len(raw)
                if line_number <= SKIP_HEADER_LINES:
                    continue
                line = raw.decode("utf-8", errors="strict").strip()
                if not line or line.startswith("#"):
                    continue
                fields = line.split()
                source_id = fields[0].strip() if fields else ""
                if not source_id.startswith("ZTFJ"):
                    malformed_lines += 1
                    continue
                rows += 1
                field_counts[len(fields)] += 1
                ids.add(source_id)
        crc_hex = f"{member_crc & 0xFFFFFFFF:08x}"
        if member_bytes != info.file_size:
            raise ValueError(f"Table 6 member byte count mismatch: {member_bytes} != {info.file_size}")
        if crc_hex != f"{info.CRC:08x}":
            raise ValueError(f"Table 6 member CRC mismatch: {crc_hex} != {info.CRC:08x}")
        if malformed_lines:
            raise ValueError(f"Table 6 contains {malformed_lines} non-empty rows with invalid IDs")
        if expected_rows is not None and rows != expected_rows:
            raise ValueError(f"Table 6 row count mismatch: {rows} != {expected_rows}")
        if len(ids) != rows:
            raise ValueError(f"Table 6 has duplicate IDs: rows={rows}, unique={len(ids)}")
        if len(field_counts) != 1:
            raise ValueError(f"Inconsistent Table 6 row widths: {dict(field_counts)}")
    return ids, {
        "archive_md5": observed_md5,
        "member_name": info.filename,
        "member_size_bytes": member_bytes,
        "member_sha256": member_sha.hexdigest(),
        "member_crc32": crc_hex,
        "record_count": rows,
        "unique_id_count": len(ids),
        "row_field_counts": dict(field_counts),
        "duplicate_id_count": rows - len(ids),
    }


def is_positive_finite(value: str | None) -> bool:
    try:
        number = float(value) if value is not None else float("nan")
    except (TypeError, ValueError):
        return False
    return math.isfinite(number) and number > 0


def metadata_predicates(row: dict[str, str]) -> dict[str, bool]:
    mean_pair = is_positive_finite(row.get("gmag")) and is_positive_finite(row.get("rmag"))
    period_pair = is_positive_finite(row.get("Per-g")) and is_positive_finite(row.get("Per-r"))
    four_field = mean_pair and period_pair
    recorded_four_field = row.get("four_field_positive", "").strip().lower() == "true"
    if recorded_four_field != four_field:
        raise ValueError(
            f"Four-field flag disagrees with source values for SourceID={row.get('SourceID')}"
        )
    return {
        "both_mean_magnitudes_positive": mean_pair,
        "both_band_periods_positive": period_pair,
        "four_field_positive": four_field,
    }


def is_candidate_only_stratum(value: str | None) -> bool:
    return any(
        label.strip() == "candidate_only"
        for label in (value or "").split(",")
    )


def read_candidate_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream, delimiter="\t")
        required = {
            "SourceID", "ZTF", "strata", "candidate", "Table4_member",
            "gmag", "rmag", "Per-g", "Per-r", "four_field_positive",
        }
        missing = required.difference(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Residual artifact missing columns: {sorted(missing)}")
        rows = [
            row for row in reader
            if is_candidate_only_stratum(row.get("strata"))
        ]
    if len(rows) != EXPECTED_RESIDUALS:
        raise ValueError(f"Expected {EXPECTED_RESIDUALS} candidate-only residuals; found {len(rows)}")
    source_ids = [row["SourceID"].strip() for row in rows]
    ztf_ids = [row["ZTF"].strip() for row in rows]
    if any(not value for value in source_ids + ztf_ids):
        raise ValueError("Residual artifact contains an empty SourceID or ZTF ID")
    if len(set(source_ids)) != len(rows) or len(set(ztf_ids)) != len(rows):
        raise ValueError("Residual artifact contains duplicate object identifiers")
    if any(row["candidate"].strip().lower() != "true" for row in rows):
        raise ValueError("A candidate-only row is not marked as a candidate")
    if any(row["Table4_member"].strip().lower() != "false" for row in rows):
        raise ValueError("A candidate-only row is unexpectedly a Table 4 member")
    for row in rows:
        metadata_predicates(row)
    return rows


def build_report(
    residual_rows: list[dict[str, str]],
    table6_ids: set[str],
    table6_metadata: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    overlap = [row for row in residual_rows if row["ZTF"].strip() in table6_ids]
    predicates = {row["SourceID"]: metadata_predicates(row) for row in residual_rows}
    by_predicate: dict[str, dict[str, int]] = {}
    for field in (
        "both_mean_magnitudes_positive",
        "both_band_periods_positive",
        "four_field_positive",
    ):
        group = [row for row in residual_rows if predicates[row["SourceID"]][field]]
        by_predicate[field] = {
            "residuals_in_group": len(group),
            "table6_overlap": sum(row["ZTF"].strip() in table6_ids for row in group),
        }
    report = {
        "schema_version": "1.0",
        "diagnostic": "CPVS Table 6 suspected-variable overlap",
        "scope": "Read-only comparison; not a membership selector",
        "table6": table6_metadata,
        "residuals": {
            "candidate_only_count": len(residual_rows),
            "unique_source_id_count": len({row["SourceID"].strip() for row in residual_rows}),
            "unique_ztf_id_count": len({row["ZTF"].strip() for row in residual_rows}),
            "table6_overlap_count": len(overlap),
            "table6_non_overlap_count": len(residual_rows) - len(overlap),
            "overlap_fraction": len(overlap) / len(residual_rows),
            "by_metadata_predicate": by_predicate,
        },
        "interpretation_limit": (
            "An overlap or non-overlap with the suspected-variable table does not establish "
            "the historical CPVS or Chan et al. membership rule. It is a cross-catalogue diagnostic only."
        ),
    }
    return report, overlap


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--residuals", type=Path, required=True)
    parser.add_argument("--table6-zip", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    residual_rows = read_candidate_rows(args.residuals)
    table6_ids, table6_metadata = read_table6_ids(args.table6_zip)
    report, overlap = build_report(residual_rows, table6_ids, table6_metadata)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "cpvs_table6_overlap_report.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    with (args.output_dir / "cpvs_table6_residual_overlap.tsv").open(
        "w", encoding="utf-8", newline=""
    ) as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=[
                "SourceID", "ZTF", "Type", "gmag", "rmag", "Per", "Per-g", "Per-r",
                "Ng", "Nr", "mean_magnitude_pair_positive", "band_period_pair_positive",
                "four_field_positive",
            ],
            delimiter="\t",
            extrasaction="ignore",
        )
        writer.writeheader()
        writer.writerows(overlap)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
