"""Compare derived CPVS membership with VizieR and cross-check catalog identity."""

from __future__ import annotations

import argparse
import json
import zipfile
from pathlib import Path
from typing import Iterable, TextIO


def read_selected(path: Path) -> set[int]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip().lower() != "sourceid":
        raise ValueError("selected file must start with SourceID header")
    return {int(line.strip()) for line in lines[1:] if line.strip()}


def _vizier_rows(lines: Iterable[str]) -> dict[int, str]:
    materialized = list(lines)
    header_index: int | None = None
    ztf_index: int | None = None
    id_index: int | None = None

    for index, line in enumerate(materialized):
        stripped = line.strip()
        if not stripped:
            continue
        candidate = stripped[1:].strip() if stripped.startswith("#") else stripped
        columns = [item.strip().lower() for item in candidate.split("\t")]
        if "id" in columns and "ztf" in columns:
            header_index = index
            ztf_index = columns.index("ztf")
            id_index = columns.index("id")
            break

    rows: dict[int, str] = {}
    if header_index is not None and ztf_index is not None and id_index is not None:
        for line in materialized[header_index + 1:]:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            columns = [item.strip() for item in line.split("\t")]
            if max(ztf_index, id_index) >= len(columns):
                continue
            raw_id = columns[id_index]
            name = columns[ztf_index]
            if raw_id.isdigit() and name:
                rows[int(raw_id)] = name
        return rows

    # CDS fixed-width table4.dat: ZTF occupies bytes 1-22; ID occupies 24-29.
    for line in materialized:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        raw_name = line[0:22].strip()
        raw_id = line[23:29].strip()
        if raw_id.isdigit() and raw_name.startswith("ZTF"):
            rows[int(raw_id)] = raw_name
    return rows


def read_vizier_rows(path: Path) -> dict[int, str]:
    """Return catalog-internal ID -> published ZTF name from TSV or fixed-width data."""
    return _vizier_rows(path.read_text(encoding="utf-8", errors="replace").splitlines())


def read_vizier(path: Path) -> set[int]:
    """Read VizieR catalog-internal membership IDs from TSV/fixed-width data."""
    return set(read_vizier_rows(path))


def _catalog_rows(lines: Iterable[str]) -> dict[int, str]:
    """Map one-based Table 2 row ordinal to its ZTF identifier."""
    result: dict[int, str] = {}
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        fields = stripped.split()
        if fields and fields[0].upper().startswith("ZTF"):
            result[len(result) + 1] = fields[0]
    return result


def read_parent_catalog(path: Path) -> dict[int, str]:
    """Read Table 2 catalog row ordinals and names from plain text or ZIP."""
    if not zipfile.is_zipfile(path):
        with path.open(encoding="utf-8", errors="replace") as handle:
            return _catalog_rows(handle)

    with zipfile.ZipFile(path) as archive:
        candidates = [name for name in archive.namelist() if not name.endswith("/")]
        for member in candidates:
            with archive.open(member) as raw:
                lines = (line.decode("utf-8", errors="replace") for line in raw)
                rows = _catalog_rows(lines)
            if rows:
                return rows
    raise ValueError(f"no ZTF catalog rows found in parent evidence: {path}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--published", type=Path, required=True)
    parser.add_argument("--parent", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    candidate = read_selected(args.candidate)
    published_rows = read_vizier_rows(args.published)
    published = set(published_rows)
    report: dict[str, object] = {
        "candidate_count": len(candidate),
        "published_count": len(published),
        "intersection_count": len(candidate & published),
        "candidate_only_count": len(candidate - published),
        "published_only_count": len(published - candidate),
        "candidate_only_sample": sorted(candidate - published)[:25],
        "published_only_sample": sorted(published - candidate)[:25],
        "exact_membership_match": candidate == published,
        "published_source": "VizieR J/ApJ/932/118 table4.dat",
        "published_id_semantics": "catalog internal identifier; Table 4 bytes 24-29 / VizieR column ID",
    }

    if args.parent:
        parent_rows = read_parent_catalog(args.parent)
        outside_parent = sorted(object_id for object_id in published if object_id not in parent_rows)
        identity_mismatches = sorted(
            object_id
            for object_id in (published & set(parent_rows))
            if published_rows[object_id] != parent_rows[object_id]
        )
        report.update({
            "parent_catalog_count": len(parent_rows),
            "published_ids_outside_parent_count": len(outside_parent),
            "published_ids_outside_parent": [
                {"id": object_id, "ztf": published_rows[object_id]}
                for object_id in outside_parent[:100]
            ],
            "published_parent_identity_mismatch_count": len(identity_mismatches),
            "published_parent_identity_mismatch_sample": [
                {
                    "id": object_id,
                    "published_ztf": published_rows[object_id],
                    "parent_ztf": parent_rows[object_id],
                }
                for object_id in identity_mismatches[:100]
            ],
        })

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["exact_membership_match"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
