"""Compare CPVS candidate membership with published Table 4 via ZTF names."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path


def normalize_name(value: str) -> str:
    """Normalize only case and whitespace for the published object-name join."""
    return "".join(value.split()).upper()


def read_selected(path: Path) -> set[int]:
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    if not lines or lines[0].strip().lower() != "sourceid":
        raise ValueError("selected file must start with SourceID header")
    values = [int(line.strip()) for line in lines[1:] if line.strip()]
    if len(values) != len(set(values)):
        raise ValueError("selected file contains duplicate SourceIDs")
    return set(values)


def read_vizier_names(path: Path) -> set[str]:
    """Read the ZTF object-name column from CDS Table 4 TSV or fixed-width data."""
    lines = path.read_text(encoding="utf-8-sig", errors="replace").splitlines()
    header_index: int | None = None
    name_index: int | None = None
    for index, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue
        candidate = stripped[1:].strip() if stripped.startswith("#") else stripped
        if "\t" not in candidate:
            continue
        columns = [item.strip().lower() for item in candidate.split("\t")]
        possible = [
            i
            for i, column in enumerate(columns)
            if column in {"ztf", "ztf identifier", "ztf_id", "ztf name"}
        ]
        if possible:
            header_index, name_index = index, possible[0]
            break

    raw_names: list[str] = []
    if header_index is not None and name_index is not None:
        for line_number, line in enumerate(
            lines[header_index + 1 :], start=header_index + 2
        ):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            columns = [item.strip() for item in line.split("\t")]
            if name_index >= len(columns):
                raise ValueError(f"{path}:{line_number}: malformed Table 4 row")
            value = columns[name_index]
            if not value or set(value) == {"-"}:
                continue
            raw_names.append(value)
    else:
        # CDS table4.dat has the ZTF identifier in the first fixed-width field.
        for line_number, line in enumerate(lines, start=1):
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            value = line[:23].strip()
            if value.upper().startswith("ZTF"):
                raw_names.append(value)
            elif re.match(r"^-+$", value):
                continue

    names = [normalize_name(value) for value in raw_names]
    if not names:
        raise ValueError(f"{path}: no ZTF object names found in published Table 4")
    duplicates = sorted(name for name, count in Counter(names).items() if count > 1)
    if duplicates:
        raise ValueError(
            f"{path}: duplicate normalized published ZTF names, examples={duplicates[:10]}"
        )
    return set(names)


def read_parent_name_map(path: Path) -> dict[str, int]:
    """Map Table 2 ZTF object names to its stable Seq/SourceID namespace."""
    lines = path.read_text(encoding="utf-8-sig", errors="replace").splitlines()
    header_index: int | None = None
    seq_index: int | None = None
    name_index: int | None = None
    for index, line in enumerate(lines):
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "\t" not in stripped:
            continue
        columns = [item.strip().lower() for item in stripped.split("\t")]
        if "seq" in columns and "id" in columns:
            header_index = index
            seq_index = columns.index("seq")
            name_index = columns.index("id")
            break

    name_to_id: dict[str, int] = {}
    if header_index is not None and seq_index is not None and name_index is not None:
        for line_number, line in enumerate(
            lines[header_index + 1 :], start=header_index + 2
        ):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            columns = [item.strip() for item in line.split("\t")]
            if len(columns) <= max(seq_index, name_index):
                raise ValueError(
                    f"{path}:{line_number}: row has {len(columns)} columns, "
                    f"expected at least {max(seq_index, name_index) + 1}"
                )
            raw_id, raw_name = columns[seq_index], columns[name_index]
            if not raw_id or set(raw_id) == {"-"}:
                continue  # VizieR units/ruler rows
            if not raw_id.isdigit() or not raw_name:
                raise ValueError(
                    f"{path}:{line_number}: invalid Seq/object-name mapping"
                )
            key = normalize_name(raw_name)
            if key in name_to_id:
                raise ValueError(
                    f"{path}:{line_number}: duplicate normalized parent name "
                    f"{raw_name!r} (already maps to Seq {name_to_id[key]})"
                )
            name_to_id[key] = int(raw_id)
    else:
        name_to_id = _read_fixed_width_parent_map(path, lines)

    if not name_to_id:
        raise ValueError(
            f"{path}: cannot build parent name crosswalk; expected a Table 2 TSV export "
            "with 'Seq' and 'ID' columns, or the original fixed-width table2.dat"
        )
    _validate_parent_seq_monotonic(path, name_to_id)
    return name_to_id


# CDS J/ApJS/249/18 table2.dat is fixed width (Lrecl 228). The VizieR ReadMe
# documents `Seq` in columns 24-29 as I6 with the range [1/781604], and the ZTF
# object identifier occupies the leading 23 columns.
_TABLE2_NAME_SLICE = slice(0, 23)
_TABLE2_SEQ_SLICE = slice(23, 29)


def _read_fixed_width_parent_map(path: Path, lines: list[str]) -> dict[str, int]:
    """Map Table 2 object names to the documented ``Seq`` column.

    This deliberately does NOT derive the identifier from the row's position in
    the file. That shortcut was previously used here and it is unsound: the
    catalogue has 781,602 rows while ``Seq`` spans [1/781604], so at least two
    ``Seq`` values are absent. From the first gap onward a row's ordinal is
    strictly lower than its ``Seq``, and every object after it would be assigned
    the wrong parent identifier with no error raised.

    The identifier is therefore read from its documented column and every row is
    validated. Anything that does not look like a real catalogue row is an error
    rather than a silently skipped line.
    """
    name_to_id: dict[str, int] = {}
    for line_number, line in enumerate(lines, start=1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        raw_seq = line[_TABLE2_SEQ_SLICE].strip()
        raw_name = line[_TABLE2_NAME_SLICE].strip()
        if not raw_seq and not raw_name:
            continue
        if not raw_seq.isdigit():
            raise ValueError(
                f"{path}:{line_number}: column 24-29 is not a Seq integer "
                f"({raw_seq!r}); refusing to infer the parent identifier"
            )
        if not raw_name.upper().startswith("ZTF"):
            raise ValueError(
                f"{path}:{line_number}: columns 1-23 do not hold a ZTF object name "
                f"({raw_name!r}); the fixed-width layout does not match the ReadMe"
            )
        key = normalize_name(raw_name)
        if key in name_to_id:
            raise ValueError(
                f"{path}:{line_number}: duplicate normalized parent name "
                f"{raw_name!r} (already maps to Seq {name_to_id[key]})"
            )
        name_to_id[key] = int(raw_seq)
    return name_to_id


def _validate_parent_seq_monotonic(path: Path, name_to_id: dict[str, int]) -> None:
    """Reject a crosswalk whose Seq values repeat.

    A repeated Seq would mean two object names claim the same parent identifier,
    which makes the membership join ambiguous. Gaps are legitimate (the
    catalogue is not dense) and are not rejected.
    """
    seen: dict[int, str] = {}
    for name, seq in name_to_id.items():
        if seq in seen:
            raise ValueError(
                f"{path}: Seq {seq} is claimed by both {seen[seq]!r} and {name!r}"
            )
        seen[seq] = name


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--published", type=Path, required=True)
    parser.add_argument("--parent", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)

    try:
        return _run_audit(args)
    except ValueError as error:
        # An input the audit cannot read is a refusal, not a result. Report it on
        # stderr and fail with a non-zero status so no membership number can be
        # produced from a crosswalk that did not validate. Exit code 1 means
        # "could not evaluate"; exit code 2 means "evaluated, sets differ".
        sys.stderr.write(f"audit_cpvs_membership: {error}\n")
        return 1


def _run_audit(args: argparse.Namespace) -> int:

    candidate = read_selected(args.candidate)
    published_names = read_vizier_names(args.published)
    parent_name_map = read_parent_name_map(args.parent)
    unmapped = sorted(published_names - set(parent_name_map))
    if unmapped:
        raise ValueError(
            f"{len(unmapped)} published Table 4 names are absent from parent Table 2; "
            f"examples={unmapped[:10]}"
        )
    published = {parent_name_map[name] for name in published_names}
    report = {
        "candidate_count": len(candidate),
        "published_count": len(published),
        "intersection_count": len(candidate & published),
        "candidate_only_count": len(candidate - published),
        "published_only_count": len(published - candidate),
        "candidate_only_sample": sorted(candidate - published)[:25],
        "published_only_sample": sorted(published - candidate)[:25],
        "exact_membership_match": candidate == published,
        "published_source": "VizieR J/ApJ/932/118 table4.dat",
        "membership_join_key": "normalized ZTF object name -> parent Table 2 Seq/SourceID",
        "parent_name_mapping_count": len(parent_name_map),
        "published_unmapped_name_count": 0,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["exact_membership_match"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
