"""Compare derived CPVS candidate membership with the published VizieR table.

This is an audit tool, not a release bypass. A mismatch is reported explicitly
and returns a non-zero exit status.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def read_selected(path: Path) -> set[int]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip().lower() != "sourceid":
        raise ValueError("selected file must start with SourceID header")
    return {int(line.strip()) for line in lines[1:] if line.strip()}


def read_vizier(path: Path) -> set[int]:
    """Read either the published fixed-width table or a VizieR TSV export."""
    ids: set[int] = set()
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    header_index: int | None = None
    for index, line in enumerate(lines):
        fields = [field.strip().lower() for field in line.split("\t")]
        if "id" in fields and "ztf" in fields:
            header_index = index
            break
    if header_index is not None:
        fields = [field.strip().lower() for field in lines[header_index].split("\t")]
        id_index = fields.index("id")
        for line in lines[header_index + 1:]:
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            values = line.split("\t")
            if len(values) > id_index and values[id_index].strip().isdigit():
                ids.add(int(values[id_index].strip()))
        return ids
    for line in lines:
        if not line.strip() or line.lstrip().startswith("#") or line.startswith('"'):
            continue
        raw = line[23:29].strip()
        if raw.isdigit():
            ids.add(int(raw))
    return ids


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--published", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    candidate = read_selected(args.candidate)
    published = read_vizier(args.published)
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
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["exact_membership_match"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
