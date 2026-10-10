"""Compare CPVS candidate membership with the published table using ZTF names."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from zipfile import ZipFile


def read_selected(path: Path) -> set[int]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip().lower() != "sourceid":
        raise ValueError("selected file must start with SourceID header")
    return {int(line.strip()) for line in lines[1:] if line.strip()}


def read_published_ztf_names(path: Path) -> list[str]:
    """Read published ZTF object names from VizieR TSV or fixed-width Table 4."""
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    header_index: int | None = None
    ztf_index: int | None = None

    for index, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue
        candidate = stripped[1:].strip() if stripped.startswith("#") else stripped
        columns = [item.strip().lower() for item in candidate.split("\t")]
        if "ztf" in columns or "ztf identifier" in columns:
            header_index = index
            ztf_index = columns.index("ztf" if "ztf" in columns else "ztf identifier")
            break

    names: list[str] = []
    if header_index is not None and ztf_index is not None:
        for line in lines[header_index + 1:]:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            columns = [item.strip() for item in line.split("\t")]
            if ztf_index < len(columns):
                name = columns[ztf_index].strip()
                if name.upper().startswith("ZTF"):
                    names.append(name.upper())
        return names

    # CDS fixed-width Table 4: ZTF name is the first 22 characters;
    # the adjacent ID column is an internal catalog identifier, not SourceID.
    for line in lines:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        name = line[:22].strip()
        if name.upper().startswith("ZTF"):
            names.append(name.upper())
    if not names:
        raise ValueError(f"could not parse any published ZTF names from {path}")
    return names


def _iter_parent_lines(path: Path):
    """Yield parent catalog lines, selecting the unique member with ZTF rows."""
    if path.suffix.lower() == ".zip":
        with ZipFile(path) as archive:
            members = [name for name in archive.namelist() if not name.endswith("/")]
            candidates: list[str] = []
            for member in members:
                with archive.open(member) as raw:
                    for encoded in raw:
                        line = encoded.decode("utf-8", errors="replace").strip()
                        if line and line.split()[0].upper().startswith("ZTF"):
                            candidates.append(member)
                            break
            if len(candidates) != 1:
                raise ValueError(
                    f"expected one parent catalog member with ZTF rows in {path}, "
                    f"found {len(candidates)}: {candidates[:10]}"
                )
            with archive.open(candidates[0]) as raw:
                for encoded in raw:
                    yield encoded.decode("utf-8", errors="replace")
        return

    with path.open("r", encoding="utf-8", errors="replace") as handle:
        yield from handle


def read_parent_name_to_sourceid(path: Path) -> dict[str, int]:
    """Map each parent-table ZTF name to its one-based catalog-row SourceID."""
    mapping: dict[str, int] = {}
    ordinal = 0
    for line in _iter_parent_lines(path):
        stripped = line.strip()
        if not stripped:
            continue
        fields = stripped.split()
        name = fields[0]
        if not name.upper().startswith("ZTF") or len(fields) < 2:
            continue
        normalized = name.upper()
        if normalized in mapping:
            raise ValueError(f"duplicate ZTF name in parent catalog: {normalized}")
        ordinal += 1
        mapping[normalized] = ordinal
    if not mapping:
        raise ValueError(f"no ZTF rows found in parent catalog: {path}")
    return mapping


def read_vizier(path: Path, parent_path: Path) -> set[int]:
    """Map published Table 4 ZTF names to parent SourceIDs; never compare Table 4 ID directly."""
    names = read_published_ztf_names(path)
    parent_mapping = read_parent_name_to_sourceid(parent_path)
    return {parent_mapping[name] for name in names if name in parent_mapping}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--published", type=Path, required=True)
    parser.add_argument("--parent", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    candidate = read_selected(args.candidate)
    published_names = read_published_ztf_names(args.published)
    parent_mapping = read_parent_name_to_sourceid(args.parent)
    unmapped_names = sorted(set(published_names) - set(parent_mapping))
    duplicate_name_count = len(published_names) - len(set(published_names))
    published = {parent_mapping[name] for name in published_names if name in parent_mapping}

    report = {
        "candidate_count": len(candidate),
        "published_count": len(published_names),
        "published_mapped_sourceid_count": len(published),
        "published_unmapped_name_count": len(unmapped_names),
        "published_unmapped_name_sample": unmapped_names[:25],
        "published_duplicate_name_count": duplicate_name_count,
        "parent_name_mapping_count": len(parent_mapping),
        "intersection_count": len(candidate & published),
        "candidate_only_count": len(candidate - published),
        "published_only_count": len(published - candidate),
        "candidate_only_sample": sorted(candidate - published)[:25],
        "published_only_sample": sorted(published - candidate)[:25],
        "exact_membership_match": (
            candidate == published and not unmapped_names and duplicate_name_count == 0
        ),
        "published_source": "VizieR J/ApJ/932/118 table4.dat",
        "membership_join_key": "normalized ZTF object name mapped to one-based parent Table2 row SourceID",
        "note": "Table 4 ID is a catalog-internal identifier and is not compared directly with parent SourceID.",
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
