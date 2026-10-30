#!/usr/bin/env python3
"""Audit CPVS SNR candidates against Table 2 fields and Table 4 by ZTF name."""
from __future__ import annotations
import argparse, csv, hashlib, json, math
from pathlib import Path


def read_vizier(path: Path, required: tuple[str, ...]) -> list[dict[str, str]]:
    import re

    header: list[str] | None = None
    metadata: dict[int, str] = {}
    rows: list[dict[str, str]] = []
    with path.open(encoding="utf-8-sig", newline="") as stream:
        for raw in stream:
            line = raw.rstrip("\r\n")
            if not line.strip():
                continue
            if line.startswith("#Column"):
                match = re.match(r"^#Column\s+(\d+)\s+(\S+)", line)
                if match:
                    metadata[int(match.group(1))] = match.group(2)
                continue
            if line.startswith("#"):
                continue
            fields = [value.strip() for value in line.split("\t")]
            if header is None and all(k.lower() in {x.lower() for x in fields} for k in required):
                header = fields
                continue
            if header is None and metadata:
                header = [metadata[i] for i in sorted(metadata)]
            if header is None or len(fields) != len(header) or fields == header:
                continue
            rows.append(dict(zip(header, fields)))
    if header is None:
        raise ValueError(f"{path}: missing VizieR column metadata/header {required!r}")
    missing = [key for key in required if key not in header]
    if missing:
        raise ValueError(f"{path}: VizieR schema missing required columns {missing!r}; found {header!r}")
    if not rows:
        raise ValueError(f"{path}: VizieR schema parsed but no data rows were found")
    return rows

def read_candidates(path: Path) -> set[int]:
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.reader(f, delimiter="\t")
        header = next(reader, [])
        if not header or header[0].strip().lower() != "sourceid":
            raise ValueError("candidate file must start with SourceID")
        result = set()
        for n, row in enumerate(reader, 2):
            if not row or not row[0].strip():
                continue
            value = int(row[0])
            if value in result:
                raise ValueError(f"duplicate candidate SourceID {value} at line {n}")
            result.add(value)
        return result


def ids_hash(ids: set[int]) -> str:
    return hashlib.sha256("".join(f"{x}\n" for x in sorted(ids)).encode()).hexdigest()


def audit(table2: Path, table4: Path | None, candidates_file: Path,
          expected_parent: int | None = 781602, expected_published: int | None = 730184,
          zenodo_csv: Path | None = None) -> dict:
    if (table4 is None) == (zenodo_csv is None):
        raise ValueError("supply exactly one of table4 or zenodo_csv")
    t2 = read_vizier(table2, ("ID", "Seq", "gmag", "rmag", "Per-g", "Per-r"))
    t4 = read_vizier(table4, ("ZTF", "ID")) if table4 is not None else None
    name_to_seq, seq_to_name, four = {}, {}, set()
    for row in t2:
        name, seq = row["ID"].strip(), int(row["Seq"])
        if not name or name in name_to_seq or seq in seq_to_name:
            raise ValueError(f"duplicate/empty Table 2 name or Seq: {name!r}/{seq}")
        name_to_seq[name] = seq
        seq_to_name[seq] = name
        try:
            vals = [float(row[k]) for k in ("gmag", "rmag", "Per-g", "Per-r")]
        except (ValueError, KeyError):
            vals = [0.0] * 4
        if all(math.isfinite(v) and v > 0 for v in vals):
            four.add(seq)
    published, seen_names = set(), set()
    if t4 is not None:
        for row in t4:
            name = row["ZTF"].strip()
            if name in seen_names:
                raise ValueError(f"duplicate Table 4 ZTF name: {name}")
            seen_names.add(name)
            if name not in name_to_seq:
                raise ValueError(f"Table 4 name not mapped to Table 2: {name}")
            published.add(name_to_seq[name])  # crosswalk by name; never assume Table4.ID == Seq
    else:
        with zenodo_csv.open(encoding="utf-8", newline="") as stream:
            reader = csv.DictReader(stream)
            if not reader.fieldnames or "ID" not in reader.fieldnames:
                raise ValueError(f"Zenodo CSV must contain ID column; found {reader.fieldnames!r}")
            for row in reader:
                name = (row.get("ID") or "").strip()
                if not name:
                    continue
                if name in seen_names:
                    raise ValueError(f"duplicate Zenodo ZTF name: {name}")
                seen_names.add(name)
                if name not in name_to_seq:
                    raise ValueError(f"Zenodo name not mapped to Table 2: {name}")
                published.add(name_to_seq[name])
    candidates = read_candidates(candidates_file)
    parent = set(seq_to_name)
    if candidates - parent:
        raise ValueError(f"candidate IDs absent from Table 2 Seq: {sorted(candidates-parent)[:10]}")
    if expected_parent is not None and len(parent) != expected_parent:
        raise ValueError(f"parent count expected {expected_parent}, got {len(parent)}")
    if expected_published is not None and len(published) != expected_published:
        raise ValueError(f"published count expected {expected_published}, got {len(published)}")
    candidate_only, published_only = candidates-published, published-candidates
    failed_four, pass_four = candidates-four, candidates&four
    filtered_candidate_only, filtered_published_only = pass_four-published, published-pass_four
    return {
      "counts": {
        "parent":len(parent), "published":len(published), "candidates":len(candidates),
        "candidate_published_intersection":len(candidates&published),
        "candidate_only":len(candidate_only), "published_only":len(published_only),
        "parent_four_field":len(four), "candidate_pass_four_field":len(pass_four),
        "candidate_fail_four_field":len(failed_four), "four_field_parent_only":len(four-published),
        "filtered_candidate_only":len(filtered_candidate_only),
        "filtered_published_only":len(filtered_published_only)
      },
      "sha256_sorted_ids_newline_terminated": {
        "candidate_only":ids_hash(candidate_only), "candidate_fail_four_field":ids_hash(failed_four),
        "four_field_parent_only":ids_hash(four-published),
        "filtered_candidate_only":ids_hash(filtered_candidate_only),
        "filtered_published_only":ids_hash(filtered_published_only)
      },
      "verdict": {
        "exact_membership_match": not candidate_only and not published_only,
        "four_field_intersection_exact_match": not filtered_candidate_only and not filtered_published_only,
        "candidate_excess_equals_four_field_failures": candidate_only == failed_four,
        "author_intent_proven": False
      },
      "inputs": {
        "table2":{"path":str(table2),"bytes":table2.stat().st_size,"sha256":hashlib.sha256(table2.read_bytes()).hexdigest()},
        **({"table4":{"path":str(table4),"bytes":table4.stat().st_size,"sha256":hashlib.sha256(table4.read_bytes()).hexdigest()}} if table4 is not None else {}),
        **({"zenodo_csv":{"path":str(zenodo_csv),"bytes":zenodo_csv.stat().st_size,"sha256":hashlib.sha256(zenodo_csv.read_bytes()).hexdigest()}} if zenodo_csv is not None else {}),
        "published_membership_source": "VizieR J/ApJ/932/118 table4" if table4 is not None else "Zenodo DOI 10.5281/zenodo.5764899 1st_layer.csv",
        "candidates":{"path":str(candidates_file),"bytes":candidates_file.stat().st_size,"sha256":hashlib.sha256(candidates_file.read_bytes()).hexdigest()}
      }
    }


def main() -> int:
    p=argparse.ArgumentParser()
    p.add_argument("--table2",type=Path,required=True)
    p.add_argument("--table4",type=Path)
    p.add_argument("--zenodo-csv",type=Path)
    p.add_argument("--candidates",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    report=audit(a.table2,a.table4,a.candidates,zenodo_csv=a.zenodo_csv)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2,sort_keys=True))
    return 0 if report["verdict"]["four_field_intersection_exact_match"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
