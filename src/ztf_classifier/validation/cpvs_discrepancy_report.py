"""Traceable CPVS candidate-only reports; never infer discovery or publisher intent."""
from __future__ import annotations

import csv
import hashlib
import html
import json
import math
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REQUIRED_FEATURES = ("gmag", "rmag", "Per-g", "Per-r")
ID_ALIASES = ("sourceid", "source_id", "seq", "id")


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_table(path: str | Path) -> tuple[list[str], list[dict[str, str]]]:
    with Path(path).open("r", encoding="utf-8-sig", newline="") as stream:
        sample = stream.read(8192)
        stream.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters="\t,;")
        except csv.Error:
            dialect = csv.excel_tab
        reader = csv.DictReader(stream, dialect=dialect)
        if not reader.fieldnames:
            raise ValueError(f"{path}: missing header")
        headers = [str(name).strip() for name in reader.fieldnames]
        if len(headers) != len(set(headers)):
            raise ValueError(f"{path}: duplicate headers")
        rows = []
        for line_number, raw in enumerate(reader, start=2):
            if None in raw:
                raise ValueError(f"{path}:{line_number}: extra fields")
            rows.append(
                {
                    key.strip(): (value or "").strip()
                    for key, value in raw.items()
                    if key is not None
                }
            )
        return headers, rows


def id_column(headers: list[str]) -> str:
    normalized = {header.lower(): header for header in headers}
    for alias in ID_ALIASES:
        if alias in normalized:
            return normalized[alias]
    raise ValueError(f"missing identifier column; expected one of {ID_ALIASES}")


def read_ids(path: str | Path) -> set[str]:
    headers, rows = read_table(path)
    key = id_column(headers)
    values = []
    for line_number, row in enumerate(rows, start=2):
        value = row.get(key, "")
        if not value.isdigit():
            raise ValueError(f"{path}:{line_number}: invalid object ID {value!r}")
        values.append(str(int(value)))
    duplicates = sorted(
        value for value, count in Counter(values).items() if count > 1
    )
    if duplicates:
        raise ValueError(f"{path}: duplicate object IDs, examples={duplicates[:10]}")
    return set(values)


def number_status(raw: str | None) -> str:
    if raw is None or not raw.strip():
        return "missing"
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return "invalid"
    if not math.isfinite(value):
        return "non_finite"
    return "positive" if value > 0 else "nonpositive"


def build_cpvs_discrepancy_report(
    *,
    parent_metadata: str | Path,
    candidate_ids: str | Path,
    published_ids: str | Path,
    output_dir: str | Path,
    source_revision: str = "UNRECORDED",
) -> dict[str, Any]:
    """Write CSV, strict JSON manifest, searchable HTML and Markdown summary."""
    parent_path, candidate_path, published_path = map(
        Path, (parent_metadata, candidate_ids, published_ids)
    )
    headers, parent_rows = read_table(parent_path)
    id_key = id_column(headers)
    normalized = {header.lower(): header for header in headers}
    absent = [
        field for field in REQUIRED_FEATURES if field.lower() not in normalized
    ]
    if absent:
        raise ValueError(f"parent metadata missing required fields: {absent}")
    feature_keys = {
        field: normalized[field.lower()] for field in REQUIRED_FEATURES
    }

    parent: dict[str, dict[str, str]] = {}
    for line_number, row in enumerate(parent_rows, start=2):
        raw_id = row.get(id_key, "")
        if not raw_id.isdigit():
            raise ValueError(
                f"{parent_path}:{line_number}: invalid authoritative ID {raw_id!r}"
            )
        object_id = str(int(raw_id))
        if object_id in parent:
            raise ValueError(
                f"{parent_path}:{line_number}: duplicate authoritative ID {object_id}"
            )
        parent[object_id] = row

    candidates = read_ids(candidate_path)
    published = read_ids(published_path)
    extras = sorted(candidates - published, key=int)
    if not extras:
        raise ValueError(
            "candidate-only set is empty; refusing to emit an empty discrepancy report"
        )
    missing = sorted(set(extras) - set(parent), key=int)
    if missing:
        raise ValueError(
            f"{len(missing)} candidate-only IDs lack parent provenance: {missing[:10]}"
        )

    records: list[dict[str, Any]] = []
    groups: Counter[str] = Counter()
    for object_id in extras:
        source = parent[object_id]
        states = {
            field: number_status(source.get(key))
            for field, key in feature_keys.items()
        }
        mags_ok = all(states[key] == "positive" for key in ("gmag", "rmag"))
        periods_ok = all(
            states[key] == "positive" for key in ("Per-g", "Per-r")
        )
        if not mags_ok and not periods_ok:
            group = "magnitude_and_period_pair_incomplete"
        elif mags_ok and not periods_ok:
            group = "valid_magnitudes_period_pair_incomplete"
        elif periods_ok and states["gmag"] != "positive":
            group = "valid_periods_gmag_incomplete"
        else:
            group = "other_combination_review_required"
        groups[group] += 1
        reasons = [
            f"{key}:{value}"
            for key, value in states.items()
            if value != "positive"
        ]
        record: dict[str, Any] = dict(source)
        record.update(
            {
                "SourceID": object_id,
                "reference_membership": "candidate_only_not_in_published_table4",
                "diagnostic_group": group,
                "discrepancy_reason": (
                    "; ".join(reasons)
                    if reasons
                    else "none_under_four_field_predicate"
                ),
                **{f"{key}_status": value for key, value in states.items()},
                "raw_lightcurve_status": (
                    source.get("raw_lightcurve_status", "") or "NOT_ASSESSED"
                ),
                "raw_lightcurve_quality": (
                    source.get("raw_lightcurve_quality", "") or "NOT_ASSESSED"
                ),
                "external_crossmatch_status": (
                    source.get("external_crossmatch_status", "") or "NOT_ASSESSED"
                ),
                "external_crossmatch_evidence": (
                    source.get("external_crossmatch_evidence", "") or "NOT_ASSESSED"
                ),
                "scientific_disposition": (
                    source.get("scientific_disposition", "") or "UNREVIEWED"
                ),
                "publisher_rule_interpretation": (
                    "UNRESOLVED: diagnostic predicate reproduces membership, "
                    "historical selection semantics not established"
                ),
            }
        )
        records.append(record)

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    fields = list(dict.fromkeys(key for record in records for key in record))
    csv_path = out / "cpvs_candidate_only_objects.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)

    summary: dict[str, Any] = {
        "report_schema": "cpvs-discrepancy-report/1.0",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "source_revision": source_revision,
        "source_files": {
            name: {
                "path": str(path),
                "sha256": sha256_file(path),
                "bytes": path.stat().st_size,
            }
            for name, path in (
                ("parent_metadata", parent_path),
                ("candidate_ids", candidate_path),
                ("published_ids", published_path),
            )
        },
        "counts": {
            "parent_metadata_objects": len(parent),
            "candidate_objects": len(candidates),
            "published_reference_objects": len(published),
            "intersection_objects": len(candidates & published),
            "candidate_only_objects": len(extras),
            "published_only_objects": len(published - candidates),
            "candidate_only_missing_parent_provenance": 0,
        },
        "diagnostic_group_counts": dict(sorted(groups.items())),
        "interpretation": {
            "reference_definition": "membership in supplied published Table 4 ID list",
            "scientific_ground_truth": False,
            "historical_publisher_rule": "UNRESOLVED",
            "four_field_predicate": "diagnostic only; not a production selection rule",
            "raw_lightcurve_review": (
                "NOT_ASSESSED unless explicit input columns are supplied"
            ),
            "external_crossmatch": (
                "NOT_ASSESSED unless explicit input columns are supplied"
            ),
            "discovery_claim": (
                "none; candidate-only membership does not establish a new discovery"
            ),
        },
    }
    (out / "cpvs_discrepancy_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )

    visible = (
        "SourceID",
        "diagnostic_group",
        "discrepancy_reason",
        "raw_lightcurve_status",
        "external_crossmatch_status",
        "scientific_disposition",
    )
    table_header = "".join(
        f"<th>{html.escape(key)}</th>" for key in visible
    )
    table_rows = []
    for record in records:
        cells = "".join(
            f"<td>{html.escape(str(record.get(key, '')))}</td>"
            for key in visible
        )
        table_rows.append(f"<tr>{cells}</tr>")
    html_path = out / "cpvs_candidate_only_objects.html"
    html_path.write_text(
        "<!doctype html><html lang='en'><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width,initial-scale=1'>"
        "<title>CPVS discrepancy report</title>"
        "<style>body{font:15px system-ui;margin:2rem}input{padding:.6rem;width:min(42rem,90%)}"
        "table{border-collapse:collapse;width:100%;margin-top:1rem}"
        "th,td{border:1px solid #bbb;padding:.4rem;text-align:left}"
        "th{position:sticky;top:0;background:#eee}"
        ".warning{padding:.8rem;border:1px solid #b66;margin:1rem 0}</style>"
        "<h1>CPVS candidate-only discrepancy report</h1>"
        f"<p>Candidate-only records: <strong>{len(records):,}</strong></p>"
        "<p class='warning'>Scientific blocker remains UNRESOLVED. "
        "Candidate-only does not mean a new discovery.</p>"
        "<label for='filter'>Filter records</label><br>"
        "<input id='filter' type='search' placeholder='ID, reason, status…'>"
        f"<table id='records'><thead><tr>{table_header}</tr></thead>"
        f"<tbody>{''.join(table_rows)}</tbody></table>"
        "<script>const f=document.getElementById('filter');"
        "f.addEventListener('input',()=>{const q=f.value.toLowerCase();"
        "for(const r of document.querySelectorAll('#records tbody tr'))"
        "r.hidden=!r.textContent.toLowerCase().includes(q);});</script></html>\n",
        encoding="utf-8",
    )

    markdown = [
        "# CPVS candidate-only discrepancy report",
        "",
        ("**Scientific disposition: UNRESOLVED.** Candidate-only membership is not "
         "astrophysical ground truth or evidence of a new discovery."),
        "",
        "## Counts",
        "",
    ]
    markdown.extend(
        f"- {key.replace('_', ' ')}: {value:,}"
        for key, value in summary["counts"].items()
    )
    markdown.extend(["", "## Diagnostic groups", ""])
    markdown.extend(
        f"- {key}: {value:,}" for key, value in sorted(groups.items())
    )
    markdown.extend(["", "## Input provenance", ""])
    markdown.extend(
        f"- {name} SHA-256: {item['sha256']} ({item['bytes']:,} bytes)"
        for name, item in summary["source_files"].items()
    )
    markdown.extend(
        [
            "",
            "## Limits",
            "",
            "- Four-field predicate is diagnostic only.",
            "- Raw light curves and external cross-matches are NOT_ASSESSED unless explicitly supplied.",
            "- Historical publisher selection semantics remain unresolved.",
            "",
        ]
    )
    md_path = out / "cpvs_discrepancy_report.md"
    md_path.write_text("\n".join(markdown), encoding="utf-8")
    summary["outputs"] = {
        name: {"path": path.name, "sha256": sha256_file(path)}
        for name, path in (
            ("csv", csv_path),
            ("html", html_path),
            ("markdown", md_path),
        )
    }
    (out / "cpvs_discrepancy_manifest.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return summary
