"""Audit CPVS object identity by ZTF name, separately from numeric catalog IDs.

The parent catalog's row-ordinal SourceID mapping is treated as a hypothesis and
is explicitly tested against the published Table 4 ID-to-ZTF-name mapping.
This diagnostic never changes selection or scientific acceptance criteria.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from ztf_classifier.validation.derivation import _open_text


def read_parent_names(path: Path, member: str | None = None) -> dict[int, str]:
    """Return the provisional one-based catalog-row ordinal -> ZTF name mapping."""
    owner, raw = _open_text(path, member)
    try:
        result: dict[int, str] = {}
        ordinal = 0
        for encoded in raw:
            line = encoded.decode("utf-8", errors="replace").strip()
            if not line:
                continue
            first = line.split()[0]
            if not first.upper().startswith("ZTF"):
                continue
            ordinal += 1
            result[ordinal] = first
        return result
    finally:
        raw.close()
        if owner is not None:
            owner.close()


def read_published_rows(path: Path) -> list[dict[str, object]]:
    """Read published VizieR TSV or CDS fixed-width Table 4 rows."""
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    header_index = None
    ztf_index = None
    id_index = None
    for index, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue
        candidate = stripped[1:].strip() if stripped.startswith("#") else stripped
        columns = [part.strip().lower() for part in candidate.split("\t")]
        if "id" in columns and ("ztf" in columns or "ztf identifier" in columns):
            header_index = index
            ztf_index = columns.index("ztf") if "ztf" in columns else columns.index("ztf identifier")
            id_index = columns.index("id")
            break

    rows: list[dict[str, object]] = []
    if header_index is not None and ztf_index is not None and id_index is not None:
        for line in lines[header_index + 1 :]:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            columns = [part.strip() for part in line.split("\t")]
            if max(ztf_index, id_index) >= len(columns):
                continue
            name = columns[ztf_index]
            raw_id = columns[id_index]
            if name.upper().startswith("ZTF") and raw_id.isdigit():
                rows.append({"ztf": name, "id": int(raw_id)})
        if rows:
            return rows

    # Official CDS byte layout: ZTF bytes 1-22; internal ID bytes 24-29.
    for line in lines:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        name = line[:22].strip()
        raw_id = line[23:29].strip()
        if name.upper().startswith("ZTF") and raw_id.isdigit():
            rows.append({"ztf": name, "id": int(raw_id)})
    if not rows:
        raise ValueError(f"No published ZTF/ID rows could be parsed from {path}")
    return rows


def read_candidate_ids(path: Path) -> set[int]:
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    if not lines or lines[0].strip().lower() != "sourceid":
        raise ValueError("candidate file must start with SourceID header")
    result: set[int] = set()
    for line in lines[1:]:
        value = line.strip()
        if value:
            if not value.isdigit():
                raise ValueError(f"invalid SourceID in candidate file: {value!r}")
            result.add(int(value))
    return result


def audit(parent_path: Path, candidate_path: Path, published_path: Path) -> dict[str, object]:
    parent_names = read_parent_names(parent_path)
    candidate_ids = read_candidate_ids(candidate_path)
    published_rows = read_published_rows(published_path)
    published_id_counts = Counter(int(row["id"]) for row in published_rows)
    published_name_counts = Counter(str(row["ztf"]) for row in published_rows)
    published_ids = set(published_id_counts)
    published_names = set(published_name_counts)

    id_name_matches = []
    id_name_mismatches = []
    out_of_range = []
    for row in published_rows:
        catalog_id = int(row["id"])
        ztf_name = str(row["ztf"])
        parent_name = parent_names.get(catalog_id)
        if parent_name is None:
            out_of_range.append({"id": catalog_id, "ztf": ztf_name})
        elif parent_name == ztf_name:
            id_name_matches.append(catalog_id)
        else:
            id_name_mismatches.append(
                {"id": catalog_id, "published_ztf": ztf_name, "parent_row_ztf": parent_name}
            )

    parent_name_counts = Counter(parent_names.values())
    published_name_counts = Counter(published_names)
    candidate_ids_outside_parent = sorted(candidate_ids - set(parent_names))
    candidate_names_provisional = {
        parent_names[oid] for oid in candidate_ids if oid in parent_names
    }
    name_mapping_validated = (
        not out_of_range
        and not id_name_mismatches
        and not any(count > 1 for count in published_id_counts.values())
        and not any(count > 1 for count in published_name_counts.values())
        and not any(count > 1 for count in parent_name_counts.values())
    )

    return {
        "schema_version": "1.0",
        "status": "ID_TO_NAME_MAPPING_VALIDATED" if name_mapping_validated else "ID_TO_NAME_MAPPING_NOT_VALIDATED",
        "identity_basis": "ZTF object name",
        "parent": {
            "row_count": len(parent_names),
            "first_row_names": {str(k): v for k, v in list(parent_names.items())[:3]},
            "duplicate_ztf_name_count": sum(count > 1 for count in parent_name_counts.values()),
            "source_id_interpretation": "provisional one-based row ordinal; must be validated against published ID-to-name pairs",
        },
        "candidate_numeric_ids": {
            "count": len(candidate_ids),
            "outside_parent_row_ordinal_range_count": len(candidate_ids_outside_parent),
            "outside_parent_row_ordinal_range_sample": candidate_ids_outside_parent[:25],
        },
        "published_reference": {
            "row_count": len(published_rows),
            "unique_id_count": len(published_ids),
            "duplicate_id_count": sum(count > 1 for count in published_id_counts.values()),
            "unique_ztf_name_count": len(published_names),
            "duplicate_ztf_name_count": sum(count > 1 for count in published_name_counts.values()),
        },
        "published_id_to_parent_row_name_alignment": {
            "matched_count": len(id_name_matches),
            "mismatched_count": len(id_name_mismatches),
            "out_of_parent_ordinal_range_count": len(out_of_range),
            "mismatch_sample": id_name_mismatches[:25],
            "out_of_range_sample": out_of_range[:25],
        },
        "numeric_id_membership": {
            "intersection_count": len(candidate_ids & published_ids),
            "candidate_only_count": len(candidate_ids - published_ids),
            "published_only_count": len(published_ids - candidate_ids),
            "candidate_only_sample": sorted(candidate_ids - published_ids)[:25],
            "published_only_sample": sorted(published_ids - candidate_ids)[:25],
        },
        "provisional_name_membership_using_row_ordinal_mapping": {
            "interpretable": name_mapping_validated,
            "candidate_name_count": len(candidate_names_provisional),
            "published_name_count": len(published_names),
            "intersection_count": len(candidate_names_provisional & published_names),
            "candidate_only_count": len(candidate_names_provisional - published_names),
            "published_only_count": len(published_names - candidate_names_provisional),
            "candidate_only_sample": sorted(candidate_names_provisional - published_names)[:25],
            "published_only_sample": sorted(published_names - candidate_names_provisional)[:25],
            "warning": "Do not interpret name-membership counts as authoritative unless ID-to-name mapping is validated.",
        },
        "scientific_disposition": "DIAGNOSTIC_ONLY; selection thresholds and acceptance criteria unchanged",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--parent", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--published", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = audit(args.parent, args.candidate, args.published)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
