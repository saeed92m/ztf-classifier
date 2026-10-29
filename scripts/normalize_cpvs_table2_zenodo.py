#!/usr/bin/env python3
"""Fail-closed normalizer for the Zenodo CPVS Table2.txt alternative source.

The pinned Zenodo file has 34 header/metadata lines and slightly different byte
layout from the CDS table2.dat expected by verify_cpvs_four_field_rule.py. This
tool validates the exact source contract, then inserts one separator before
original byte 117 so Per-r moves from bytes 117-129 to the parser's bytes
118-130. No data values are rewritten.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

EXPECTED_SOURCE_LINES = 781_636
EXPECTED_RECORDS = 781_602
EXPECTED_METADATA_LINES = 34
SEQ_MIN = 1
SEQ_MAX = 781_604


class ContractError(RuntimeError):
    pass


def _number(raw: str, field: str, line_number: int):
    value = raw.strip()
    if not value:
        return None
    try:
        parsed = float(value.replace("D", "E").replace("d", "e"))
    except ValueError as exc:
        raise ContractError(
            f"non-numeric {field} at source line {line_number}: {raw!r}"
        ) from exc
    if not math.isfinite(parsed) or parsed == 0.0:
        return None
    return parsed


def normalize(
    source_path: Path,
    output_path: Path,
    report_path: Path,
    *,
    expected_source_lines: int = EXPECTED_SOURCE_LINES,
    expected_records: int = EXPECTED_RECORDS,
    expected_metadata_lines: int = EXPECTED_METADATA_LINES,
) -> dict:
    raw_bytes = source_path.read_bytes()
    try:
        lines = raw_bytes.decode("ascii").splitlines()
    except UnicodeDecodeError as exc:
        raise ContractError("source is not ASCII; refusing implicit decoding") from exc

    records = []
    metadata = []
    seqs = set()
    names = set()
    null_counts = {"gmag": 0, "rmag": 0, "per_g": 0, "per_r": 0}
    record_lengths = []
    s4_count = 0

    for line_number, line in enumerate(lines, start=1):
        name = line[:22].strip() if len(line) >= 22 else ""
        seq_text = line[23:29].strip() if len(line) >= 29 else ""
        is_record = (
            len(line) >= 129
            and name.upper().startswith("ZTF")
            and seq_text.isdigit()
        )
        if not is_record:
            metadata.append({"line": line_number, "length": len(line), "preview": line[:120]})
            continue

        seq = int(seq_text)
        if not SEQ_MIN <= seq <= SEQ_MAX:
            raise ContractError(f"Seq {seq} at line {line_number} outside [{SEQ_MIN}, {SEQ_MAX}]")
        if seq in seqs:
            raise ContractError(f"duplicate Seq {seq} at source line {line_number}")
        if name in names:
            raise ContractError(f"duplicate ZTF ID {name!r} at source line {line_number}")
        seqs.add(seq)
        names.add(name)
        record_lengths.append(len(line))

        # Source data spans: gmag 90-95, rmag 97-102, Per-g 104-116,
        # Per-r 117-129. Some Per-g values use all 13 bytes despite the
        # header's F12.7 annotation; validate the observed record bytes.
        raw_fields = {
            "gmag": line[89:95],
            "rmag": line[96:102],
            "per_g": line[103:116],
            "per_r": line[116:129],
        }
        parsed = {
            field: _number(value, field, line_number)
            for field, value in raw_fields.items()
        }
        for field, value in parsed.items():
            if value is None:
                null_counts[field] += 1
        if all(parsed[k] is not None and parsed[k] > 0 for k in ("gmag", "rmag", "per_g", "per_r")):
            s4_count += 1

        # Preserve every source character and insert exactly one separator
        # after original byte 116 so the existing CDS-layout parser reads
        # Per-r from bytes 118-130. Verify values before accepting the row.
        normalized = line[:116] + " " + line[116:]
        if normalized[89:95].strip() != raw_fields["gmag"].strip():
            raise ContractError(f"gmag changed during normalization at line {line_number}")
        if normalized[96:102].strip() != raw_fields["rmag"].strip():
            raise ContractError(f"rmag changed during normalization at line {line_number}")
        if normalized[103:116].strip() != raw_fields["per_g"].strip():
            raise ContractError(f"Per-g changed during normalization at line {line_number}")
        if normalized[117:130].strip() != raw_fields["per_r"].strip():
            raise ContractError(f"Per-r changed during normalization at line {line_number}")
        records.append((line_number, normalized))

    metadata_lines = [x["line"] for x in metadata]
    contract_ok = (
        len(lines) == expected_source_lines
        and len(records) == expected_records
        and len(metadata) == expected_metadata_lines
        and metadata_lines == list(range(1, expected_metadata_lines + 1))
        and len(seqs) == expected_records
        and min(seqs, default=None) == SEQ_MIN
        and max(seqs, default=None) == SEQ_MAX
    )
    report = {
        "source_file": source_path.name,
        "source_bytes": len(raw_bytes),
        "source_sha256": hashlib.sha256(raw_bytes).hexdigest(),
        "source_line_count": len(lines),
        "expected_source_line_count": expected_source_lines,
        "recognized_record_count": len(records),
        "expected_record_count": expected_records,
        "metadata_line_count": len(metadata),
        "expected_metadata_line_count": expected_metadata_lines,
        "metadata_lines": metadata,
        "seq_unique_count": len(seqs),
        "seq_min": min(seqs, default=None),
        "seq_max": max(seqs, default=None),
        "seq_gaps": (max(seqs) - min(seqs) + 1 - len(seqs)) if seqs else None,
        "four_field_count": s4_count,
        "null_field_counts": null_counts,
        "record_length_min": min(record_lengths, default=None),
        "record_length_max": max(record_lengths, default=None),
        "normalization": "insert one separator after original byte 116; preserve all source field values; map Per-r 117-129 to CDS parser bytes 118-130",
        "status": "PASS" if contract_ok else "BLOCKED",
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if not contract_ok:
        raise ContractError(
            "source contract mismatch; report written, output not created"
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_bytes = ("\n".join(line for _, line in records) + "\n").encode("ascii")
    output_path.write_bytes(output_bytes)
    report["normalized_file"] = output_path.name
    report["normalized_bytes"] = len(output_bytes)
    report["normalized_sha256"] = hashlib.sha256(output_bytes).hexdigest()
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="Extracted Zenodo Table2.txt")
    parser.add_argument("--output", type=Path, required=True, help="Normalized CDS-layout table2.dat")
    parser.add_argument("--report", type=Path, required=True, help="Normalization evidence JSON")
    args = parser.parse_args(argv)
    try:
        report = normalize(args.input, args.output, args.report)
    except (ContractError, OSError) as exc:
        print(f"CONTRACT VIOLATION: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
