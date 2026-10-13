"""Compare derived CPVS candidate membership with the published VizieR table.

The audit deliberately reports row-level cardinality and duplicate IDs as well as
set membership. A set-only comparison can hide duplicate rows and make the
source-table parser appear healthier than it is.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path


def read_selected_rows(path: Path) -> list[int]:
    """Read candidate SourceID rows without discarding duplicates."""
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip().lower() != "sourceid":
        raise ValueError("selected file must start with SourceID header")
    rows: list[int] = []
    for line_number, line in enumerate(lines[1:], start=2):
        value = line.strip()
        if not value:
            continue
        if not value.isdigit():
            raise ValueError(f"invalid SourceID at line {line_number}: {value!r}")
        rows.append(int(value))
    return rows


def read_selected(path: Path) -> set[int]:
    """Compatibility helper returning unique candidate SourceIDs."""
    return set(read_selected_rows(path))


def read_vizier_rows(path: Path) -> tuple[list[int], str]:
    """Read VizieR TSV/fixed-width membership IDs, preserving duplicate rows."""
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    header_index: int | None = None
    id_index: int | None = None

    for index, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue
        candidate = stripped[1:].strip() if stripped.startswith("#") else stripped
        columns = [item.strip().lower() for item in candidate.split("\\t")]
        if "id" in columns and ("ztf" in columns or "ztf identifier" in columns):
            header_index = index
            id_index = columns.index("id")
            break

    rows: list[int] = []
    if header_index is not None and id_index is not None:
        for line in lines[header_index + 1:]:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            columns = [item.strip() for item in line.split("\\t")]
            if id_index < len(columns):
                raw = columns[id_index]
                if raw.isdigit():
                    rows.append(int(raw))
        return rows, "tsv"

    # CDS fixed-width table4.dat fallback: ID occupies bytes 24-29.
    for line in lines:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        raw = line[23:29].strip()
        if raw.isdigit():
            rows.append(int(raw))
    return rows, "fixed_width"


def read_vizier(path: Path) -> set[int]:
    """Compatibility helper returning unique published IDs."""
    rows, _ = read_vizier_rows(path)
    return set(rows)


def duplicate_summary(rows: list[int]) -> dict[str, object]:
    counts = Counter(rows)
    duplicated = sorted(value for value, count in counts.items() if count > 1)
    return {
        "row_count": len(rows),
        "unique_count": len(counts),
        "duplicate_id_count": len(duplicated),
        "duplicate_row_count": sum(counts[value] - 1 for value in duplicated),
        "duplicate_id_sample": duplicated[:25],
    }


def ids_sha256(ids: set[int]) -> str:
    canonical = "".join(f"{value}\n" for value in sorted(ids)).encode("ascii")
    return hashlib.sha256(canonical).hexdigest()


def rows_sha256(rows: list[int]) -> str:
    canonical = "".join(f"{value}\n" for value in rows).encode("ascii")
    return hashlib.sha256(canonical).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--published", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    candidate_rows = read_selected_rows(args.candidate)
    published_rows, published_parser = read_vizier_rows(args.published)
    candidate = set(candidate_rows)
    published = set(published_rows)
    candidate_only = candidate - published
    published_only = published - candidate

    report = {
        "candidate": duplicate_summary(candidate_rows),
        "published": duplicate_summary(published_rows),
        "candidate_row_sha256": rows_sha256(candidate_rows),
        "published_row_sha256": rows_sha256(published_rows),
        "candidate_unique_ids_sha256": ids_sha256(candidate),
        "published_unique_ids_sha256": ids_sha256(published),
        "published_parser": published_parser,
        "candidate_count": len(candidate),
        "published_count": len(published),
        "intersection_count": len(candidate & published),
        "candidate_only_count": len(candidate_only),
        "published_only_count": len(published_only),
        "candidate_only_sample": sorted(candidate_only)[:25],
        "published_only_sample": sorted(published_only)[:25],
        "exact_membership_match": candidate == published,
        "exact_row_multiset_match": Counter(candidate_rows) == Counter(published_rows),
        "published_source": "VizieR J/ApJ/932/118 table4.dat",
        "interpretation": (
            "Membership equality compares unique IDs; row-multiset equality also "
            "requires matching duplicate multiplicities. Neither result alone "
            "establishes that the scientific selection predicate is correct."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["exact_membership_match"] and report["exact_row_multiset_match"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
