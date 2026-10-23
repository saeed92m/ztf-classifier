"""Reproducible audit for event-level astronomical catalogues."""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

import pandas as pd


def audit_event_catalog(
    path: str | Path,
    *,
    object_id_column: str = "oid",
    class_column: str = "spec_class",
) -> dict[str, object]:
    """Summarize an event catalogue without collapsing repeated object IDs."""
    source = Path(path)
    if not source.is_file():
        raise FileNotFoundError(source)
    raw = source.read_bytes()
    frame = pd.read_csv(source, dtype="string", keep_default_na=False)
    if frame.empty:
        raise ValueError("Catalogue contains no event rows.")
    if not frame.columns.is_unique:
        raise ValueError("Catalogue contains duplicate column names.")
    if object_id_column not in frame.columns:
        raise ValueError(f"Missing object ID column: {object_id_column}")

    ids = frame[object_id_column].astype("string").str.strip()
    if ids.eq("").any():
        raise ValueError("Object IDs contain blank values.")
    multiplicity = Counter(ids.tolist())
    repeated = {key: count for key, count in multiplicity.items() if count > 1}
    missing = {
        column: int(frame[column].astype("string").str.strip().eq("").sum())
        for column in frame.columns
    }
    class_counts: dict[str, int] = {}
    if class_column in frame.columns:
        classes = frame[class_column].astype("string").str.strip().replace("", "(missing)")
        class_counts = {str(key): int(value) for key, value in classes.value_counts().sort_index().items()}

    return {
        "source_file_name": source.name,
        "file_bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "columns": frame.columns.tolist(),
        "event_rows": int(len(frame)),
        "unique_object_ids": int(len(multiplicity)),
        "objects_with_multiple_events": int(len(repeated)),
        "additional_event_rows_beyond_one_per_object": int(len(frame) - len(multiplicity)),
        "event_multiplicity_counts": {
            str(k): int(v) for k, v in sorted(Counter(repeated.values()).items())
        },
        "missing_values_by_column": missing,
        "class_counts": class_counts,
        "duplicate_rows_collapsed": 0,
        "note": (
            "Repeated object IDs are reported as multiple events; rows are not "
            "deduplicated because event-level catalogues may contain multiple "
            "events per object."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("catalogue", type=Path)
    parser.add_argument("--object-id-column", default="oid")
    parser.add_argument("--class-column", default="spec_class")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = audit_event_catalog(
        args.catalogue,
        object_id_column=args.object_id_column,
        class_column=args.class_column,
    )
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
