#!/usr/bin/env python3
"""Decisive, offline test of the CPVS "four-field positivity" hypothesis.

Background
----------
Issue #170: the documented CPVS rule (arXiv:2112.03306 §II.1: "at least one
2.5-sigma g and 3-sigma r detection") selects ~741,788 of the 781,602 Table 2
objects, but the published membership (J/ApJ/932/118 Table 4) has 730,184.
An undocumented rule is sometimes asserted to close the gap exactly:

    gmag > 0  and  rmag > 0  and  Per-g > 0  and  Per-r > 0

That rule is a pure function of four *nullable* Table 2 columns. Testing it
therefore needs only two published tables -- no photometry, no 31-minute
derivation, and no access to the 11,604 candidate-only IDs:

    table2.dat  781,602 rows, Lrecl 228   (J/ApJS/249/18)
    table4.dat  730,184 rows, Lrecl  63   (J/ApJ/932/118)

This script decides, falsifiably:

    S4      = { Seq in table2 : all four nullable fields > 0 }
    P       = published membership from table4

    S4_only        > 0  -> the "exact equality" claim is FALSE
    P_only         > 0  -> the four-field rule cannot define membership
    both == 0           -> the rule is extensionally equivalent (NOT proof
                           of author intent -- see the printed caveat)

Byte layout (1-based inclusive, from CDS ReadMe `J/ApJS/249/18`):

    table2.dat   ID 1-22 A22 | Seq 24-29 I6 | gmag 90-95 F6.3 ?
                 rmag 97-102 F6.3 ? | Per-g 104-116 F13.7 ? | Per-r 118-130 F13.7 ?
    table4.dat   ZTF 1-22 A22 | ID 24-29 I6 (catalogue ID; not assumed equal to Seq)

`?=0` is CDS notation for "nullable, null encoded as 0". Those fields are read
as None, never as 0.0.

Fail-closed by design: a short line, a non-numeric field, an unexpected row
count, a duplicate or out-of-range Seq, or a Table4 name/Seq mismatch aborts
with a non-zero exit code. It cannot silently emit a plausible empty result.

Standard library only -- no pip install required.

Usage
-----
    python3 verify_cpvs_four_field_rule.py --self-test
    python3 verify_cpvs_four_field_rule.py --table2 table2.dat --table4 table4.dat
    python3 verify_cpvs_four_field_rule.py --table2 table2.dat --zenodo-csv 1st_layer.csv
    ... add --dump-ids to write the differing Seq lists to disk
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
from pathlib import Path

TABLE2_REQUIRED_ROWS = 781_602
TABLE4_REQUIRED_ROWS = 730_184
SEQ_MAX = 781_604  # documented Seq range is [1/781604]

# 1-based inclusive byte spans -> 0-based half-open Python slices.
S2_NAME = (1, 22)
S2_SEQ = (24, 29)
S2_GMAG = (90, 95)
S2_RMAG = (97, 102)
S2_PERG = (104, 116)
S2_PERR = (118, 130)
S4_NAME = (1, 22)
S4_ID = (24, 29)

MIN_T2_LEN = S2_PERR[1]
MIN_T4_LEN = S4_ID[1]

FIELDS = ("gmag", "rmag", "per_g", "per_r")


class ContractError(RuntimeError):
    """Raised when an input violates a documented structural contract."""


def _span(line: str, span: tuple[int, int]) -> str:
    start, end = span
    return line[start - 1 : end]


def _sha256(path: Path, chunk: int = 1 << 20) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(chunk), b""):
            digest.update(block)
    return digest.hexdigest()


def _nullable_float(raw: str) -> float | None:
    """Parse a CDS `?=0` field. Blank and 0 are null, not 0.0."""
    text = raw.strip()
    if not text:
        return None
    try:
        value = float(text.replace("D", "E").replace("d", "e"))
    except ValueError as exc:  # pragma: no cover - guarded by caller
        raise ValueError(f"non-numeric value {raw!r}") from exc
    if value == 0.0:  # documented null sentinel
        return None
    return value


def _iter_table2(path: Path):
    """Yield (row_no, name, seq, four_values). Fails closed on any deviation."""
    with path.open("rb") as handle:
        for row_no, raw in enumerate(handle, start=1):
            line = raw.decode("utf-8", errors="strict").rstrip("\r\n")
            if not line:
                raise ContractError(f"{path}:{row_no}: blank line inside table2.dat")
            if len(line) < MIN_T2_LEN:
                raise ContractError(
                    f"{path}:{row_no}: truncated row ({len(line)} chars; "
                    f"need >= {MIN_T2_LEN} to reach Per-r at bytes 118-130)"
                )
            name = _span(line, S2_NAME)
            if not name.strip().upper().startswith("ZTF"):
                raise ContractError(
                    f"{path}:{row_no}: ID field at bytes 1-22 is {name!r}, "
                    "expected a ZTF object name"
                )
            seq_text = _span(line, S2_SEQ).strip()
            if not seq_text.isdecimal():
                raise ContractError(
                    f"{path}:{row_no}: Seq at bytes 24-29 is {seq_text!r}"
                )
            seq = int(seq_text)
            if not 1 <= seq <= SEQ_MAX:
                raise ContractError(
                    f"{path}:{row_no}: Seq {seq} outside documented [1/{SEQ_MAX}]"
                )
            values = []
            for span, label in (
                (S2_GMAG, "gmag 90-95"),
                (S2_RMAG, "rmag 97-102"),
                (S2_PERG, "Per-g 104-116"),
                (S2_PERR, "Per-r 118-130"),
            ):
                try:
                    values.append(_nullable_float(_span(line, span)))
                except ValueError:
                    raise ContractError(
                        f"{path}:{row_no}: non-numeric {label}: {_span(line, span)!r}"
                    ) from None
            yield row_no, name.strip(), seq, tuple(values)


def _iter_table4(path: Path):
    with path.open("rb") as handle:
        for row_no, raw in enumerate(handle, start=1):
            line = raw.decode("utf-8", errors="strict").rstrip("\r\n")
            if not line:
                raise ContractError(f"{path}:{row_no}: blank line inside table4.dat")
            if len(line) < MIN_T4_LEN:
                raise ContractError(
                    f"{path}:{row_no}: truncated row ({len(line)} chars; "
                    f"need >= {MIN_T4_LEN} to reach ID at bytes 24-29)"
                )
            id_text = _span(line, S4_ID).strip()
            if not id_text.isdecimal():
                raise ContractError(
                    f"{path}:{row_no}: ID at bytes 24-29 is {id_text!r}"
                )
            yield row_no, _span(line, S4_NAME).strip(), int(id_text)


def _zenodo_names(path: Path) -> set[str]:
    """Read the `ID` column (ZTF catalog name) from Zenodo 1st_layer.csv."""
    import csv as _csv

    names: set[str] = set()
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = _csv.DictReader(handle)
        if not reader.fieldnames or "ID" not in reader.fieldnames:
            raise ContractError(f"{path}: no `ID` column; found {reader.fieldnames!r}")
        for row in reader:
            value = (row.get("ID") or "").strip()
            if value:
                names.add(value)
    if not names:
        raise ContractError(f"{path}: `ID` column yielded zero names")
    return names


def run(table2: Path, table4: Path | None, zenodo_csv: Path | None) -> dict:
    report: dict = {
        "contract": {
            "table2_expected_rows": TABLE2_REQUIRED_ROWS,
            "table4_expected_rows": TABLE4_REQUIRED_ROWS,
            "null_encoding": "0 == null (CDS ?=0)",
        },
        "inputs": {},
        "counts": {},
        "verdict": {},
    }

    print(f"[1/4] hashing {table2} ...", file=sys.stderr)
    report["inputs"]["table2"] = {
        "path": str(table2),
        "bytes": table2.stat().st_size,
        "sha256": _sha256(table2),
    }
    if table4 is not None:
        print(f"[1/4] hashing {table4} ...", file=sys.stderr)
        report["inputs"]["table4"] = {
            "path": str(table4),
            "bytes": table4.stat().st_size,
            "sha256": _sha256(table4),
        }
    if zenodo_csv is not None:
        print(f"[1/4] hashing {zenodo_csv} ...", file=sys.stderr)
        report["inputs"]["zenodo_csv"] = {
            "path": str(zenodo_csv),
            "bytes": zenodo_csv.stat().st_size,
            "sha256": _sha256(zenodo_csv),
        }

    # ---- table2 ---------------------------------------------------------
    print("[2/4] parsing table2.dat ...", file=sys.stderr)
    seq_to_name: dict[int, str] = {}
    name_to_seq: dict[str, int] = {}
    four_field: set[int] = set()
    per_field_null = {f: 0 for f in FIELDS}
    per_field_nonpositive = {f: 0 for f in FIELDS}
    rows = 0
    for row_no, name, seq, values in _iter_table2(table2):
        rows += 1
        if seq in seq_to_name:
            raise ContractError(f"{table2}:{row_no}: duplicate Seq {seq}")
        if name in name_to_seq:
            raise ContractError(f"{table2}:{row_no}: duplicate object name {name!r}")
        seq_to_name[seq] = name
        name_to_seq[name] = seq
        for field, value in zip(FIELDS, values):
            if value is None:
                per_field_null[field] += 1
            elif value <= 0:
                per_field_nonpositive[field] += 1
        if all(value is not None and value > 0 for value in values):
            four_field.add(seq)

    if rows != TABLE2_REQUIRED_ROWS:
        raise ContractError(
            f"table2.dat row count mismatch: expected {TABLE2_REQUIRED_ROWS}, got {rows}"
        )

    report["counts"]["table2_rows"] = rows
    report["counts"]["table2_unique_seq"] = len(seq_to_name)
    report["counts"]["seq_min"] = min(seq_to_name)
    report["counts"]["seq_max"] = max(seq_to_name)
    report["counts"]["seq_gaps"] = (
        max(seq_to_name) - min(seq_to_name) + 1
    ) - len(seq_to_name)
    report["counts"]["four_field_count"] = len(four_field)
    report["counts"]["null_per_field"] = per_field_null
    report["counts"]["nonpositive_nonnull_per_field"] = per_field_nonpositive

    # ---- published membership ------------------------------------------
    if table4 is not None:
        print("[3/4] parsing table4.dat ...", file=sys.stderr)
        published: set[int] = set()
        seen_table4_ids: set[int] = set()
        rows4 = 0
        unmapped_names: list[dict] = []
        for row_no, name, ident in _iter_table4(table4):
            rows4 += 1
            if ident in seen_table4_ids:
                raise ContractError(f"{table4}:{row_no}: duplicate catalogue ID {ident}")
            seen_table4_ids.add(ident)
            seq = name_to_seq.get(name)
            if seq is None:
                if len(unmapped_names) < 10:
                    unmapped_names.append({"row": row_no, "name": name, "catalogue_id": ident})
                continue
            published.add(seq)
        if rows4 != TABLE4_REQUIRED_ROWS:
            raise ContractError(
                f"table4.dat row count mismatch: expected {TABLE4_REQUIRED_ROWS}, got {rows4}"
            )
        report["counts"]["table4_rows"] = rows4
        report["counts"]["table4_unique_catalogue_ids"] = len(seen_table4_ids)
        report["counts"]["table4_unmapped_names_count"] = rows4 - len(published)
        report["counts"]["table4_unmapped_name_examples"] = unmapped_names
        if rows4 - len(published):
            raise ContractError(
                f"{rows4 - len(published)} published Table 4 names could not be mapped "
                "to Table 2 object names; refusing to compare sets."
            )
        report["counts"]["identifier_crosscheck"] = (
            "PASS (published ZTF names mapped to Table 2 Seq; Table4.ID not equated to Seq)"
        )
    elif zenodo_csv is not None:
        print("[3/4] reading Zenodo 1st_layer.csv ...", file=sys.stderr)
        names = _zenodo_names(zenodo_csv)
        by_name = {name: seq for seq, name in seq_to_name.items()}
        unmapped = names - by_name.keys()
        published = {by_name[name] for name in names if name in by_name}
        report["counts"]["zenodo_names"] = len(names)
        report["counts"]["zenodo_unmapped_names"] = len(unmapped)
        report["counts"]["zenodo_unmapped_examples"] = sorted(unmapped)[:5]
        if unmapped:
            raise ContractError(
                f"{len(unmapped)} Zenodo names are absent from table2.dat; the "
                "name join is incomplete, refusing to compare sets."
            )
    else:  # pragma: no cover - argparse enforces this
        raise ContractError("supply --table4 or --zenodo-csv")

    report["counts"]["published_count"] = len(published)

    # ---- set comparison -------------------------------------------------
    print("[4/4] comparing sets ...", file=sys.stderr)
    s4_only = four_field - published
    published_only = published - four_field
    report["counts"]["intersection"] = len(four_field & published)
    report["counts"]["four_field_only"] = len(s4_only)
    report["counts"]["published_only"] = len(published_only)
    report["counts"]["four_field_only_sha256_of_sorted_ids"] = hashlib.sha256(
        "\n".join(str(i) for i in sorted(s4_only)).encode()
    ).hexdigest()
    report["counts"]["published_only_sha256_of_sorted_ids"] = hashlib.sha256(
        "\n".join(str(i) for i in sorted(published_only)).encode()
    ).hexdigest()

    if not s4_only and not published_only:
        status = "EXTENSIONALLY_EQUIVALENT"
        meaning = (
            "The four-field predicate reproduces the published membership exactly. "
            "This is equivalence of sets, NOT evidence of author intent."
        )
    elif s4_only and published_only:
        status = "BOTH_DIRECTIONS_FAIL"
        meaning = (
            f"{len(s4_only)} Table2 objects satisfy all four positivity conditions "
            f"but are unpublished, and {len(published_only)} published members "
            "violate at least one condition. The rule matches membership in "
            "neither direction."
        )
    elif s4_only:
        status = "HYPOTHESIS_REFUTED"
        meaning = (
            f"{len(s4_only)} Table2 objects satisfy all four positivity conditions "
            "yet are not in the published membership, so the four-field rule "
            "cannot be the published selection rule."
        )
    else:
        status = "HYPOTHESIS_INSUFFICIENT"
        meaning = (
            f"{len(published_only)} published members violate at least one of the "
            "four positivity conditions, so the rule cannot define membership."
        )
    report["verdict"] = {"status": status, "meaning": meaning}
    report["verdict"]["caveat"] = (
        "Set equality is not proof of author intent. Only the authors can confirm "
        "the historical rule; see the clarification letter in "
        "docs/scientific_validation/CPVS_INDEPENDENT_AUDIT_2026-10-29.md."
    )
    report["_diff"] = {
        "four_field_only": sorted(s4_only),
        "published_only": sorted(published_only),
    }
    return report


def _place(text: str, start: int, end: int) -> str:
    """Build a fixed-width line with `text` occupying 1-based [start, end]."""
    return " " * (start - 1) + str(text).rjust(end - start + 1)


def _make_t2_row(
    name: str, seq: int, gmag: float, rmag: float, pg: float, pr: float
) -> str:
    line = list(" " * 228)
    for text, (start, end) in (
        (name.ljust(22)[:22], S2_NAME),
        (str(seq).rjust(6), S2_SEQ),
        (f"{gmag:6.3f}", S2_GMAG),
        (f"{rmag:6.3f}", S2_RMAG),
        (f"{pg:13.7f}", S2_PERG),
        (f"{pr:13.7f}", S2_PERR),
    ):
        line[start - 1 : end] = text
    return "".join(line)


def _make_t4_row(name: str, ident: int) -> str:
    line = list(" " * 63)
    for text, (start, end) in (
        (name.ljust(22)[:22], S4_NAME),
        (str(ident).rjust(6), S4_ID),
    ):
        line[start - 1 : end] = text
    return "".join(line)


def self_test() -> int:
    """Prove the parser and the set logic work, on SYNTHETIC fixtures."""
    global TABLE2_REQUIRED_ROWS, TABLE4_REQUIRED_ROWS
    saved = (TABLE2_REQUIRED_ROWS, TABLE4_REQUIRED_ROWS)
    TABLE2_REQUIRED_ROWS, TABLE4_REQUIRED_ROWS = 4, 2
    try:
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = Path(tmp)
            t2 = tmpdir / "table2.dat"
            t4 = tmpdir / "table4.dat"
            # seq 1,2 satisfy all four; 3 and 4 each fail one condition.
            t2.write_text(
                "\n".join(
                    [
                        _make_t2_row("ZTF1aaa", 1, 18.5, 17.2, 12.34, 12.35),
                        _make_t2_row("ZTF2bbb", 2, 19.1, 17.9, 5.5, 5.51),
                        _make_t2_row("ZTF3ccc", 3, 0.0, 17.0, 8.0, 8.01),  # gmag null
                        _make_t2_row("ZTF4ddd", 4, 20.0, 19.0, 0.0, 8.01),  # Per-g null
                    ]
                )
                + "\n"
            )
            # Published = {1,3}: row 3 is published despite a null gmag, so the
            # four-field rule must be reported as HYPOTHESIS_INSUFFICIENT.
            t4.write_text(
                "\n".join([_make_t4_row("ZTF1aaa", 1), _make_t4_row("ZTF3ccc", 3)])
                + "\n"
            )

            report = run(t2, t4, None)
            assert report["counts"]["table2_rows"] == 4, report["counts"]
            assert report["counts"]["four_field_count"] == 2, report["counts"]
            assert report["counts"]["four_field_only"] == 1, report["counts"]  # seq 2
            assert report["counts"]["published_only"] == 1, report["counts"]  # seq 3
            assert report["verdict"]["status"] == "BOTH_DIRECTIONS_FAIL", report[
                "verdict"
            ]

            # An unknown published object name must abort rather than compare sets.
            t4.write_text(
                "\n".join([_make_t4_row("ZTF9zzz", 1), _make_t4_row("ZTF3ccc", 3)])
                + "\n"
            )
            try:
                run(t2, t4, None)
            except ContractError as exc:
                assert "published Table 4 names could not be mapped" in str(exc), exc
            else:
                raise AssertionError("name/Seq mismatch did not abort")

            # Truncation must abort rather than be skipped.
            (tmpdir / "short.dat").write_text(
                _make_t2_row("ZTF1aaa", 1, 18.0, 17.0, 1.0, 1.0)[:100] + "\n"
            )
            try:
                run(tmpdir / "short.dat", None, t4)
            except ContractError as exc:
                assert "truncated" in str(exc), exc
            else:
                raise AssertionError("truncated row did not abort")

        print(json.dumps({"self_test": "PASS", "fixtures": "SYNTHETIC"}, indent=2))
        return 0
    finally:
        TABLE2_REQUIRED_ROWS, TABLE4_REQUIRED_ROWS = saved


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--table2", type=Path, help="J/ApJS/249/18 table2.dat (781,602 rows, Lrecl 228)"
    )
    parser.add_argument(
        "--table4", type=Path, help="J/ApJ/932/118 table4.dat (730,184 rows, Lrecl 63)"
    )
    parser.add_argument(
        "--zenodo-csv", type=Path, help="alternative: Zenodo 5764899 1st_layer.csv"
    )
    parser.add_argument("--out", type=Path, default=Path("cpvs_four_field_report.json"))
    parser.add_argument(
        "--dump-ids", action="store_true", help="also write the differing Seq lists"
    )
    parser.add_argument(
        "--self-test", action="store_true", help="run on SYNTHETIC fixtures and exit"
    )
    args = parser.parse_args(argv)

    if args.self_test:
        return self_test()
    if args.table2 is None:
        parser.error("--table2 is required (or use --self-test)")
    if (args.table4 is None) == (args.zenodo_csv is None):
        parser.error("supply exactly one of --table4 or --zenodo-csv")
    try:
        report = run(args.table2, args.table4, args.zenodo_csv)
    except ContractError as exc:
        print(f"CONTRACT VIOLATION: {exc}", file=sys.stderr)
        return 2

    diff = report.pop("_diff")
    if args.dump_ids:
        Path("cpvs_four_field_only_ids.txt").write_text(
            "\n".join(str(i) for i in diff["four_field_only"]) + "\n"
        )
        Path("cpvs_published_only_ids.txt").write_text(
            "\n".join(str(i) for i in diff["published_only"]) + "\n"
        )
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    print(f"\nfull report written to {args.out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
