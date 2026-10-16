"""Audit CPVS object identity by the source's internal ID and ZTF name.

The official Table2 schema contains a Seq/internal SourceID column. This audit
checks that mapping against the independent published Table4 ID/name pairs,
then reports numeric-ID and object-name membership separately. It never changes
selection or scientific acceptance criteria.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from ztf_classifier.validation.derivation import _open_text


def read_parent_rows(path: Path, member: str | None = None) -> list[dict[str, object]]:
    """Read ZTF name, row ordinal, and actual Seq ID where the source exposes it."""
    owner, raw = _open_text(path, member)
    try:
        rows: list[dict[str, object]] = []
        ordinal = 0
        for encoded in raw:
            line = encoded.decode("utf-8", errors="replace").strip()
            if not line:
                continue
            fields = line.split()
            if not fields or not fields[0].upper().startswith("ZTF"):
                continue
            ordinal += 1
            seq = fields[1].strip() if len(fields) > 1 else ""
            if seq.isdigit() and int(seq) > 0:
                source_id = int(seq)
                method = "explicit_seq"
            else:
                source_id = ordinal
                method = "row_ordinal_fallback"
            rows.append(
                {
                    "row_ordinal": ordinal,
                    "source_id": source_id,
                    "ztf": fields[0],
                    "mapping_method": method,
                }
            )
        if not rows:
            raise ValueError(f"No parent ZTF catalog rows could be parsed from {path}")
        return rows
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
        columns = [part.strip().lower() for part in candidate.split("\\t")]
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
            columns = [part.strip() for part in line.split("\\t")]
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
    parent_rows = read_parent_rows(parent_path)
    candidate_ids = read_candidate_ids(candidate_path)
    published_rows = read_published_rows(published_path)

    parent_id_counts = Counter(int(row["source_id"]) for row in parent_rows)
    parent_name_counts = Counter(str(row["ztf"]) for row in parent_rows)
    published_id_counts = Counter(int(row["id"]) for row in published_rows)
    published_name_counts = Counter(str(row["ztf"]) for row in published_rows)
    parent_names_by_id = {
        int(row["source_id"]): str(row["ztf"]) for row in parent_rows
    }
    parent_names_by_ordinal = {
        int(row["row_ordinal"]): str(row["ztf"]) for row in parent_rows
    }
    published_ids = set(published_id_counts)
    published_names = set(published_name_counts)
    parent_ids = set(parent_names_by_id)

    id_name_matches = []
    id_name_mismatches = []
    ids_outside_parent = []
    row_ordinal_mismatches = []
    for row in published_rows:
        catalog_id = int(row["id"])
        ztf_name = str(row["ztf"])
        parent_name = parent_names_by_id.get(catalog_id)
        if parent_name is None:
            ids_outside_parent.append({"id": catalog_id, "ztf": ztf_name})
        elif parent_name == ztf_name:
            id_name_matches.append(catalog_id)
        else:
            id_name_mismatches.append(
                {"id": catalog_id, "published_ztf": ztf_name, "parent_ztf": parent_name}
            )
        ordinal_name = parent_names_by_ordinal.get(catalog_id)
        if ordinal_name is not None and ordinal_name != ztf_name:
            row_ordinal_mismatches.append(
                {"id": catalog_id, "published_ztf": ztf_name, "row_ordinal_ztf": ordinal_name}
            )

    mapping_methods = Counter(str(row["mapping_method"]) for row in parent_rows)
    parent_id_duplicates = sum(count > 1 for count in parent_id_counts.values())
    parent_name_duplicates = sum(count > 1 for count in parent_name_counts.values())
    published_id_duplicates = sum(count > 1 for count in published_id_counts.values())
    published_name_duplicates = sum(count > 1 for count in published_name_counts.values())
    mapping_validated = (
        not ids_outside_parent
        and not id_name_mismatches
        and parent_id_duplicates == 0
        and parent_name_duplicates == 0
        and published_id_duplicates == 0
        and published_name_duplicates == 0
    )

    candidate_names = {
        parent_names_by_id[oid] for oid in candidate_ids if oid in parent_names_by_id
    }
    candidate_ids_outside_parent = sorted(candidate_ids - parent_ids)
    return {
        "schema_version": "1.1",
        "status": "ID_TO_NAME_MAPPING_VALIDATED" if mapping_validated else "ID_TO_NAME_MAPPING_NOT_VALIDATED",
        "identity_basis": "ZTF object name with explicit Table2 Seq/internal SourceID mapping",
        "parent": {
            "row_count": len(parent_rows),
            "unique_source_id_count": len(parent_ids),
            "source_id_min": min(parent_ids),
            "source_id_max": max(parent_ids),
            "source_id_mapping_methods": dict(mapping_methods),
            "duplicate_source_id_count": parent_id_duplicates,
            "duplicate_ztf_name_count": parent_name_duplicates,
            "row_ordinal_vs_source_id_mismatch_count": sum(
                int(row["source_id"]) != int(row["row_ordinal"]) for row in parent_rows
            ),
            "source_id_interpretation": "Table2 Seq column when present; row ordinal fallback only for simplified legacy tables",
        },
        "candidate_numeric_ids": {
            "count": len(candidate_ids),
            "outside_parent_source_id_count": len(candidate_ids_outside_parent),
            "outside_parent_source_id_sample": candidate_ids_outside_parent[:25],
        },
        "published_reference": {
            "row_count": len(published_rows),
            "unique_id_count": len(published_ids),
            "duplicate_id_count": published_id_duplicates,
            "unique_ztf_name_count": len(published_names),
            "duplicate_ztf_name_count": published_name_duplicates,
        },
        "published_id_to_parent_name_alignment": {
            "matched_count": len(id_name_matches),
            "mismatched_count": len(id_name_mismatches),
            "ids_outside_parent_count": len(ids_outside_parent),
            "mismatch_sample": id_name_mismatches[:25],
            "outside_parent_sample": ids_outside_parent[:25],
        },
        "published_id_to_row_ordinal_alignment": {
            "mismatched_count": len(row_ordinal_mismatches),
            "mismatch_sample": row_ordinal_mismatches[:25],
            "note": "Diagnostic comparison only; row ordinals are not treated as internal SourceIDs.",
        },
        "numeric_id_membership": {
            "intersection_count": len(candidate_ids & published_ids),
            "candidate_only_count": len(candidate_ids - published_ids),
            "published_only_count": len(published_ids - candidate_ids),
            "candidate_only_sample": sorted(candidate_ids - published_ids)[:25],
            "published_only_sample": sorted(published_ids - candidate_ids)[:25],
        },
        "object_name_membership": {
            "interpretable": mapping_validated,
            "candidate_name_count": len(candidate_names),
            "published_name_count": len(published_names),
            "intersection_count": len(candidate_names & published_names),
            "candidate_only_count": len(candidate_names - published_names),
            "published_only_count": len(published_names - candidate_names),
            "candidate_only_sample": sorted(candidate_names - published_names)[:25],
            "published_only_sample": sorted(published_names - candidate_names)[:25],
            "warning": "Treat as authoritative only if ID-to-name mapping is validated.",
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
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
