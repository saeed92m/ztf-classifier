"""Diagnose CPVS SNR selection against published membership by ZTF-name crosswalk."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
from typing import Any

try:
    from .audit_cpvs_candidate_four_field import read_vizier
except ImportError:  # direct script execution
    from audit_cpvs_candidate_four_field import read_vizier

from ztf_classifier.validation.derivation import _iter_rows, _source_ids


def band_metrics(path: Path, parent: set[int], error_key: str, mag_key: str):
    metrics = {
        oid: {"snr": False, "snr1": False, "mag206": False, "mag206_only": False}
        for oid in parent
    }
    threshold = 2.5 if error_key == "e_gmag" else 3.0
    for row in _iter_rows(path, required_columns=("SourceID", error_key, mag_key)):
        raw_oid = row.get("SourceID", "").strip()
        try:
            oid = int(raw_oid)
        except (TypeError, ValueError):
            continue
        if oid not in metrics:
            continue
        try:
            err = float(row.get(error_key, ""))
            mag = float(row.get(mag_key, ""))
        except (TypeError, ValueError):
            continue
        if not math.isfinite(err) or err <= 0 or not math.isfinite(mag) or mag == 0:
            continue
        snr = 1.0857362047581296 / err
        snr1 = 1.0 / err
        metrics[oid]["snr"] |= snr >= threshold
        metrics[oid]["snr1"] |= snr1 >= threshold
        metrics[oid]["mag206"] |= mag <= 20.6 and snr >= threshold
        metrics[oid]["mag206_only"] |= mag <= 20.6
    return metrics


def ids_hash(ids: set[int]) -> str:
    payload = "".join(f"{value}\n" for value in sorted(ids)).encode("ascii")
    return hashlib.sha256(payload).hexdigest()


def _json_safe(value: Any) -> Any:
    """Convert non-finite floats to JSON null without altering finite values."""
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return value


def published_membership(
    table2_path: Path,
    table4_path: Path | None,
    zenodo_csv: Path | None,
) -> tuple[set[int], dict[str, Any]]:
    if (table4_path is None) == (zenodo_csv is None):
        raise ValueError("supply exactly one of table4_path or zenodo_csv")
    table2 = read_vizier(table2_path, ("ID", "Seq"))
    name_to_seq: dict[str, int] = {}
    seq_to_name: dict[int, str] = {}
    for row in table2:
        name = row["ID"].strip()
        seq = int(row["Seq"])
        if not name or name in name_to_seq or seq in seq_to_name:
            raise ValueError(f"duplicate/empty Table 2 ZTF name or Seq: {name!r}/{seq}")
        name_to_seq[name] = seq
        seq_to_name[seq] = name

    if table4_path is not None:
        table4 = read_vizier(table4_path, ("ZTF", "ID"))
        names = [row["ZTF"].strip() for row in table4]
        source_name = "VizieR J/ApJ/932/118 table4"
        reference_path = table4_path
    else:
        assert zenodo_csv is not None
        with zenodo_csv.open(encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream)
            if not reader.fieldnames or "ID" not in reader.fieldnames:
                raise ValueError(
                    f"Zenodo CSV must contain ID column; found {reader.fieldnames!r}"
                )
            names = [(row.get("ID") or "").strip() for row in reader]
        source_name = "Zenodo 10.5281/zenodo.5764899 1st_layer.csv"
        reference_path = zenodo_csv

    published: set[int] = set()
    seen_names: set[str] = set()
    for name in names:
        if not name or name in seen_names:
            raise ValueError(f"duplicate/empty published ZTF name: {name!r}")
        seen_names.add(name)
        if name not in name_to_seq:
            raise ValueError(f"published ZTF name not mapped to Table 2: {name}")
        published.add(name_to_seq[name])

    return published, {
        "source": source_name,
        "join_key": "published ZTF name -> Table 2 ID -> Table 2 Seq (SourceID)",
        "table2_rows": len(table2),
        "table2_unique_seq": len(seq_to_name),
        "published_rows": len(names),
        "published_unique_ztf_names": len(seen_names),
        "unmapped_published_names": 0,
        "table2_sha256": hashlib.sha256(table2_path.read_bytes()).hexdigest(),
        "published_sha256": hashlib.sha256(reference_path.read_bytes()).hexdigest(),
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--parent", type=Path, required=True)
    p.add_argument("--g", type=Path, required=True)
    p.add_argument("--r", type=Path, required=True)
    p.add_argument("--table2", type=Path, required=True)
    p.add_argument("--published", type=Path)
    p.add_argument("--zenodo-csv", type=Path)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()

    published, crosswalk = published_membership(a.table2, a.published, a.zenodo_csv)
    parent = {int(source_id) for source_id in _source_ids(a.parent, None)}
    if len(parent) != 781_602:
        raise ValueError(f"expected 781602 parent SourceIDs, got {len(parent)}")
    if not published.issubset(parent):
        raise ValueError(
            f"published membership contains {len(published - parent)} IDs absent from parent"
        )
    g = band_metrics(a.g, parent, "e_gmag", "gmag")
    r = band_metrics(a.r, parent, "e_rmag", "rmag")
    predicates = {
        "baseline_1p085": {o for o in parent if g[o]["snr"] and r[o]["snr"]},
        "baseline_1p0": {o for o in parent if g[o]["snr1"] and r[o]["snr1"]},
        "baseline_plus_mag206": {
            o for o in parent if g[o]["mag206"] and r[o]["mag206"]
        },
        "baseline_plus_rmag206": {
            o for o in parent if g[o]["snr"] and r[o]["snr"] and r[o]["mag206_only"]
        },
    }
    report: dict[str, Any] = {
        "status": "COMPLETED",
        "reference": crosswalk["source"],
        "crosswalk": crosswalk,
        "parent_count": len(parent),
        "published_count": len(published),
        "published_ids_sha256": ids_hash(published),
        "author_intent_proven": False,
        "predicates": {},
    }
    for name, ids in predicates.items():
        candidate_only = ids - published
        published_only = published - ids
        report["predicates"][name] = {
            "count": len(ids),
            "published_intersection": len(ids & published),
            "candidate_only": len(candidate_only),
            "published_only": len(published_only),
            "candidate_ids_sha256": ids_hash(ids),
            "candidate_only_ids_sha256": ids_hash(candidate_only),
            "published_only_ids_sha256": ids_hash(published_only),
            "candidate_only_ids": sorted(candidate_only),
            "published_only_ids": sorted(published_only),
        }
    a.output.parent.mkdir(parents=True, exist_ok=True)
    report_json = json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n"
    a.output.write_text(report_json, encoding="utf-8")
    print(report_json, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
