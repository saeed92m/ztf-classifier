"""Compare CPVS membership with VizieR using catalog IDs and ZTF-name crosswalks."""

from __future__ import annotations

import argparse
import json
import zipfile
from collections import Counter
from pathlib import Path
from typing import Iterable


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
            raw_id, name = columns[id_index], columns[ztf_index]
            if raw_id.isdigit() and name:
                rows[int(raw_id)] = name
        return rows
    # CDS fixed-width table4.dat: ZTF occupies bytes 1-22; ID occupies 24-29.
    for line in materialized:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        raw_name, raw_id = line[0:22].strip(), line[23:29].strip()
        if raw_id.isdigit() and raw_name.startswith("ZTF"):
            rows[int(raw_id)] = raw_name
    return rows


def read_vizier_rows(path: Path) -> dict[int, str]:
    """Return catalog-internal ID -> published ZTF name."""
    return _vizier_rows(path.read_text(encoding="utf-8", errors="replace").splitlines())


def read_vizier(path: Path) -> set[int]:
    """Read VizieR catalog-internal membership IDs."""
    return set(read_vizier_rows(path))


def _catalog_rows(lines: Iterable[str]) -> dict[int, str]:
    """Map explicit Table 2 Seq/SourceID values to ZTF object names.

    CPVS Table2's second field is Seq, the internal source identifier used by
    the single-exposure attachments. Do not substitute catalog row order.
    Decimal second fields are treated as legacy coordinate-only fixtures and
    use row ordinals solely to preserve those older test inputs.
    """
    result: dict[int, str] = {}
    ordinal = 0
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        fields = stripped.split()
        if not fields or not fields[0].upper().startswith("ZTF"):
            continue
        ordinal += 1
        raw_source_id = fields[1] if len(fields) > 1 else ""
        source_id = int(raw_source_id) if raw_source_id.isdigit() else ordinal
        if source_id in result:
            raise ValueError(f"duplicate CPVS Table2 Seq/SourceID: {source_id}")
        result[source_id] = fields[0]
    return result


def read_parent_catalog(path: Path) -> dict[int, str]:
    """Read Table 2 catalog row ordinals and names from plain text or ZIP."""
    if not zipfile.is_zipfile(path):
        with path.open(encoding="utf-8", errors="replace") as handle:
            return _catalog_rows(handle)
    with zipfile.ZipFile(path) as archive:
        for member in (name for name in archive.namelist() if not name.endswith("/")):
            with archive.open(member) as raw:
                rows = _catalog_rows(line.decode("utf-8", errors="replace") for line in raw)
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
    published_internal_ids = set(published_rows)
    report: dict[str, object] = {
        "candidate_count": len(candidate),
        "published_count": len(published_internal_ids),
        "catalog_internal_id_intersection_count": len(candidate & published_internal_ids),
        "catalog_internal_id_candidate_only_count": len(candidate - published_internal_ids),
        "catalog_internal_id_published_only_count": len(published_internal_ids - candidate),
        "catalog_internal_id_comparison_is_object_level": False,
        "published_source": "VizieR J/ApJ/932/118 table4.dat",
        "published_id_semantics": "catalog internal identifier; not assumed to equal parent SourceID",
    }

    if args.parent:
        parent_rows = read_parent_catalog(args.parent)
        parent_names = set(parent_rows.values())
        published_names = set(published_rows.values())
        parent_name_counts = Counter(parent_rows.values())
        published_name_counts = Counter(published_rows.values())
        duplicate_parent_names = sorted(name for name, count in parent_name_counts.items() if count > 1)
        duplicate_published_names = sorted(name for name, count in published_name_counts.items() if count > 1)
        name_to_parent_ids: dict[str, list[int]] = {}
        for parent_id, name in parent_rows.items():
            name_to_parent_ids.setdefault(name, []).append(parent_id)

        # Translate published Table 4 entries to the parent SourceID namespace by
        # astronomical object name. Ambiguous duplicate parent names are not silently
        # assigned to an arbitrary row; they make the crosswalk non-verifiable.
        mapped_published_ids: set[int] = set()
        ambiguous_published_names: list[str] = []
        for name in published_rows.values():
            matches = name_to_parent_ids.get(name, [])
            if len(matches) == 1:
                mapped_published_ids.add(matches[0])
            elif len(matches) > 1:
                ambiguous_published_names.append(name)

        missing_published_names = sorted(published_names - parent_names)
        missing_parent_names = sorted(parent_names - published_names)
        crosswalk_valid = not duplicate_parent_names and not duplicate_published_names and not ambiguous_published_names
        candidate_only = sorted(candidate - mapped_published_ids)
        published_only = sorted(mapped_published_ids - candidate)
        exact_match = crosswalk_valid and not missing_published_names and candidate == mapped_published_ids

        report.update({
            "parent_catalog_row_count": len(parent_rows),
            "parent_unique_ztf_name_count": len(parent_names),
            "published_unique_ztf_name_count": len(published_names),
            "published_names_missing_from_parent_count": len(missing_published_names),
            "published_names_missing_from_parent": missing_published_names[:100],
            "parent_names_missing_from_published_count": len(missing_parent_names),
            "parent_names_missing_from_published_sample": missing_parent_names[:100],
            "duplicate_parent_ztf_name_count": len(duplicate_parent_names),
            "duplicate_parent_ztf_name_sample": duplicate_parent_names[:100],
            "duplicate_published_ztf_name_count": len(duplicate_published_names),
            "duplicate_published_ztf_name_sample": duplicate_published_names[:100],
            "ambiguous_published_name_count": len(set(ambiguous_published_names)),
            "published_id_to_ztf_name_sample": [
                {"catalog_internal_id": object_id, "ztf": published_rows[object_id]}
                for object_id in sorted(published_rows)[:100]
            ],
            "object_name_crosswalk_valid": crosswalk_valid,
            "object_name_crosswalk_exact_membership_match": exact_match,
            "object_name_crosswalk_candidate_only_count": len(candidate_only),
            "object_name_crosswalk_candidate_only_sourceid_sample": candidate_only[:100],
            "object_name_crosswalk_candidate_only_sourceids": candidate_only,
            "object_name_crosswalk_candidate_only_objects": [
                {"SourceID": source_id, "ZTF": parent_rows.get(source_id)}
                for source_id in candidate_only
            ],
            "object_name_crosswalk_published_only_count": len(published_only),
            "object_name_crosswalk_published_only_sourceid_sample": published_only[:100],
            "object_name_crosswalk_published_only_sourceids": published_only,
            "object_name_crosswalk_published_only_objects": [
                {"SourceID": source_id, "ZTF": parent_rows.get(source_id)}
                for source_id in published_only
            ],
            "object_name_crosswalk_candidate_membership_sha256": __import__("hashlib").sha256(
                ("\n".join(map(str, sorted(candidate))) + "\n").encode()
            ).hexdigest(),
            "object_name_crosswalk_published_parent_sourceids_sha256": __import__("hashlib").sha256(
                ("\n".join(map(str, sorted(mapped_published_ids))) + "\n").encode()
            ).hexdigest(),
            "exact_membership_match": exact_match,
            "membership_comparison_basis": "ZTF object-name crosswalk into explicit Table 2 Seq/SourceID values",
            "parent_sourceid_mapping_basis": "Table2 second field Seq/internal source identifier; never inferred from row order for integer Seq rows",
        })
    else:
        report.update({
            "exact_membership_match": candidate == published_internal_ids,
            "membership_comparison_basis": "catalog internal IDs only; not an object-level proof",
        })

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["exact_membership_match"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
