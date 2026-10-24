"""Compare derived CPVS candidate membership with the published VizieR table.

Row-level evidence is preserved (issue #184): raw ordered rows are kept
before set conversion so duplicate IDs and duplicate-row counts are
reported. Both unique-membership equality and row-multiset equality are
required for a successful audit exit.
"""

from __future__ import annotations

import argparse
import hashlib
from collections import Counter
from pathlib import Path

from ztf_classifier.validation.json_utils import dumps_strict


def read_selected(path: Path) -> dict:
    """Read a SourceID-selected file, preserving ordered rows and duplicates.

    Returns a dict with:
      - rows: ordered list of int IDs (may contain duplicates)
      - unique: set of unique int IDs
      - row_count: total number of data rows
      - unique_count: number of unique IDs
      - duplicate_ids: sorted list of IDs appearing more than once
      - duplicate_row_count: total rows minus unique rows
      - ordered_rows_sha256: SHA-256 of the ordered row list
      - unique_ids_sha256: SHA-256 of the sorted unique ID list
      - parser_mode: 'tsv'
    """
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip().lower() != "sourceid":
        raise ValueError("selected file must start with SourceID header")

    rows: list[int] = []
    for line in lines[1:]:
        stripped = line.strip()
        if stripped:
            rows.append(int(stripped))

    unique = set(rows)
    row_count = len(rows)
    unique_count = len(unique)
    id_counts = Counter(rows)
    duplicate_ids = sorted([oid for oid, c in id_counts.items() if c > 1])
    duplicate_row_count = row_count - unique_count

    ordered_bytes = "\n".join(str(oid) for oid in rows).encode("utf-8")
    unique_bytes = "\n".join(str(oid) for oid in sorted(unique)).encode("utf-8")

    return {
        "rows": rows,
        "unique": unique,
        "row_count": row_count,
        "unique_count": unique_count,
        "duplicate_ids": duplicate_ids,
        "duplicate_row_count": duplicate_row_count,
        "ordered_rows_sha256": hashlib.sha256(ordered_bytes).hexdigest(),
        "unique_ids_sha256": hashlib.sha256(unique_bytes).hexdigest(),
        "parser_mode": "tsv",
    }


def read_vizier(path: Path) -> dict:
    """Read VizieR TSV/fixed-width membership IDs, preserving ordered rows.

    Returns the same dict shape as read_selected.
    """
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    rows: list[int] = []
    header_index: int | None = None
    id_index: int | None = None
    parser_mode = "fixed-width"

    for index, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue
        candidate = stripped[1:].strip() if stripped.startswith("#") else stripped
        columns = [item.strip().lower() for item in candidate.split("\t")]
        if "id" in columns and ("ztf" in columns or "ztf identifier" in columns):
            header_index = index
            id_index = columns.index("id")
            parser_mode = "tsv"
            break

    if header_index is not None and id_index is not None:
        for line in lines[header_index + 1 :]:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            columns = [item.strip() for item in line.split("\t")]
            if id_index < len(columns):
                raw = columns[id_index]
                if raw.isdigit():
                    rows.append(int(raw))
    else:
        # CDS fixed-width table4.dat fallback: ID occupies bytes 24-29.
        for line in lines:
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            raw = line[23:29].strip()
            if raw.isdigit():
                rows.append(int(raw))

    unique = set(rows)
    row_count = len(rows)
    unique_count = len(unique)
    id_counts = Counter(rows)
    duplicate_ids = sorted([oid for oid, c in id_counts.items() if c > 1])
    duplicate_row_count = row_count - unique_count

    ordered_bytes = "\n".join(str(oid) for oid in rows).encode("utf-8")
    unique_bytes = "\n".join(str(oid) for oid in sorted(unique)).encode("utf-8")

    return {
        "rows": rows,
        "unique": unique,
        "row_count": row_count,
        "unique_count": unique_count,
        "duplicate_ids": duplicate_ids,
        "duplicate_row_count": duplicate_row_count,
        "ordered_rows_sha256": hashlib.sha256(ordered_bytes).hexdigest(),
        "unique_ids_sha256": hashlib.sha256(unique_bytes).hexdigest(),
        "parser_mode": parser_mode,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--published", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    candidate = read_selected(args.candidate)
    published = read_vizier(args.published)

    candidate_unique = candidate["unique"]
    published_unique = published["unique"]

    candidate_only = candidate_unique - published_unique
    published_only = published_unique - candidate_unique

    # Row-multiset equality: same multiset of IDs (same rows with same duplicates)
    row_multiset_equal = (
        candidate["row_count"] == published["row_count"]
        and candidate["unique_ids_sha256"] == published["unique_ids_sha256"]
        and candidate["duplicate_ids"] == published["duplicate_ids"]
        and candidate["duplicate_row_count"] == published["duplicate_row_count"]
    )

    unique_membership_equal = candidate_unique == published_unique

    report = {
        "candidate": {
            "row_count": candidate["row_count"],
            "unique_count": candidate["unique_count"],
            "duplicate_row_count": candidate["duplicate_row_count"],
            "duplicate_ids": candidate["duplicate_ids"],
            "ordered_rows_sha256": candidate["ordered_rows_sha256"],
            "unique_ids_sha256": candidate["unique_ids_sha256"],
            "parser_mode": candidate["parser_mode"],
        },
        "published": {
            "row_count": published["row_count"],
            "unique_count": published["unique_count"],
            "duplicate_row_count": published["duplicate_row_count"],
            "duplicate_ids": published["duplicate_ids"],
            "ordered_rows_sha256": published["ordered_rows_sha256"],
            "unique_ids_sha256": published["unique_ids_sha256"],
            "parser_mode": published["parser_mode"],
        },
        "comparison": {
            "candidate_count": candidate["unique_count"],
            "published_count": published["unique_count"],
            "intersection_count": len(candidate_unique & published_unique),
            "candidate_only_count": len(candidate_only),
            "published_only_count": len(published_only),
            "candidate_only_sample": sorted(candidate_only)[:25],
            "published_only_sample": sorted(published_only)[:25],
            "unique_membership_equal": unique_membership_equal,
            "row_multiset_equal": row_multiset_equal,
            "exact_match": unique_membership_equal and row_multiset_equal,
        },
        "published_source": "VizieR J/ApJ/932/118 table4.dat",
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        dumps_strict(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(dumps_strict(report, indent=2, sort_keys=True))

    # Exit 0 only if both unique membership AND row-multiset equality match.
    if report["comparison"]["exact_match"]:
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
