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


def _reject_nonfinite_json_constant(value: str) -> None:
    raise ValueError(f"non-standard JSON constant is not allowed: {value}")


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_table(path: str | Path) -> tuple[list[str], list[dict[str, str]]]:
    # VizieR TSV exports include a multi-line comment preamble, a units row,
    # and a dashed separator before the actual records. Remove those structural
    # lines while retaining original line numbers for actionable errors.
    source_lines = Path(path).read_text(encoding="utf-8-sig").splitlines()
    numbered_lines = [
        (line_number, line)
        for line_number, line in enumerate(source_lines, start=1)
        if line.strip() and not line.lstrip().startswith("#")
    ]
    if not numbered_lines:
        raise ValueError(f"{path}: missing header")
    sample = "\n".join(line for _, line in numbered_lines[:20])
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters="\t,;")
    except csv.Error:
        dialect = csv.excel_tab
    parsed = csv.reader((line for _, line in numbered_lines), dialect=dialect)
    headers = [str(name).strip() for name in next(parsed, [])]
    if not headers or any(not header for header in headers):
        raise ValueError(f"{path}: missing or blank header")
    if len(headers) != len(set(headers)):
        raise ValueError(f"{path}: duplicate headers")

    rows: list[dict[str, str]] = []
    for (line_number, _), raw in zip(numbered_lines[1:], parsed):
        cells = [(value or "").strip() for value in raw]
        # Skip VizieR's units row (blank first field) and dashed ruler row.
        if cells and not cells[0] and any(cells[1:]):
            continue
        if cells and all(not cell or set(cell) == {"-"} for cell in cells):
            continue
        if len(cells) > len(headers):
            raise ValueError(f"{path}:{line_number}: extra fields")
        cells.extend([""] * (len(headers) - len(cells)))
        rows.append(dict(zip(headers, cells, strict=True)))
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


def normalize_object_name(raw: str) -> str:
    """Normalize whitespace/case only for a conservative object-name crosswalk."""
    return "".join(raw.split()).upper()


def published_membership_ids(
    published_path: Path,
    parent_rows: list[dict[str, str]],
    parent_id_key: str,
) -> set[str]:
    """Return published membership in the parent ID namespace.

    A CDS Table 4 export can contain both an internal numeric ID and the
    actual ZTF object-name column. If a ZTF-name column is present, always use
    the name crosswalk; never silently compare Table 4's internal ID to Seq.
    """
    headers, rows = read_table(published_path)
    normalized_headers = {header.lower(): header for header in headers}
    name_key = next(
        (normalized_headers[key] for key in ("ztf", "ztfname", "ztf_name") if key in normalized_headers),
        None,
    )
    if name_key is None:
        # Already-mapped membership inputs are allowed, but their identifier
        # namespace must match the candidate and parent ID namespace.
        return read_ids(published_path)

    normalized_headers_parent = {header.lower(): header for header in parent_rows[0]} if parent_rows else {}
    parent_name_key = next(
        (normalized_headers_parent[key] for key in ("id", "ztf", "ztfname", "ztf_name", "name", "object_name") if key in normalized_headers_parent),
        None,
    )
    if parent_name_key is None:
        raise ValueError(
            "published Table 4 contains ZTF object names but parent metadata has no object-name column; "
            "include the Table 2 ID/ZTF name crosswalk instead of using Table 4's internal ID"
        )

    parent_name_to_id: dict[str, str] = {}
    for line_number, row in enumerate(parent_rows, start=2):
        raw_name = row.get(parent_name_key, "").strip()
        raw_id = row.get(parent_id_key, "").strip()
        if not raw_name:
            raise ValueError(f"parent metadata row {line_number} has a blank object name")
        if not raw_id.isdigit():
            raise ValueError(f"parent metadata row {line_number} has an invalid parent ID {raw_id!r}")
        normalized_name = normalize_object_name(raw_name)
        if normalized_name in parent_name_to_id:
            raise ValueError(
                f"parent object-name normalization collision at row {line_number}: {raw_name!r}"
            )
        parent_name_to_id[normalized_name] = str(int(raw_id))

    published_names: list[str] = []
    for line_number, row in enumerate(rows, start=2):
        raw_name = row.get(name_key, "").strip()
        if not raw_name:
            raise ValueError(f"{published_path}:{line_number}: blank published ZTF object name")
        published_names.append(normalize_object_name(raw_name))
    duplicates = sorted(name for name, count in Counter(published_names).items() if count > 1)
    if duplicates:
        raise ValueError(f"{published_path}: duplicate published ZTF names, examples={duplicates[:10]}")
    unmapped = sorted(set(published_names) - set(parent_name_to_id))
    if unmapped:
        raise ValueError(
            f"{len(unmapped)} published ZTF names do not map to parent metadata; examples={unmapped[:10]}"
        )
    return {parent_name_to_id[name] for name in published_names}


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


def read_parent_metadata(
    path: str | Path, *, expected_parent_count: int = 781_602
) -> tuple[list[str], list[dict[str, str]]]:
    """Read normalized parent tables or the authoritative fixed-width CPVS Table 2 ZIP.

    The official Table 2 layout places the ZTF name in bytes 1–22, Seq in
    bytes 24–29, gmag in 90–95, rmag in 97–102, Per-g in 104–116, and Per-r
    in 118–130. Seq is the source identifier; the row ordinal is never used.
    """
    import zipfile

    source = Path(path)
    if not zipfile.is_zipfile(source):
        # Preserve support for already-normalized CSV/TSV metadata inputs.
        try:
            headers, rows = read_table(source)
            normalized = {header.lower() for header in headers}
            if {"gmag", "rmag", "per-g", "per-r"}.issubset(normalized):
                id_column(headers)
                return headers, rows
        except (UnicodeDecodeError, csv.Error):
            pass
        raise ValueError(
            "parent metadata must be a normalized CSV/TSV table or the official "
            "fixed-width CPVS Table 2 ZIP archive"
        )

    headers = ["ID", "Seq", "gmag", "rmag", "Per-g", "Per-r"]
    with zipfile.ZipFile(source) as archive:
        members = [name for name in archive.namelist() if not name.endswith("/")]
        members.sort(
            key=lambda name: (
                0 if "table2" in Path(name).name.lower() else 1,
                name.lower(),
            )
        )
        for member in members:
            rows: list[dict[str, str]] = []
            try:
                with archive.open(member) as stream:
                    for line_number, raw in enumerate(stream, start=1):
                        line = raw.decode("utf-8", errors="strict").rstrip("\r\n")
                        if not line[:22].strip().upper().startswith("ZTF"):
                            continue
                        if len(line) < 130:
                            raise ValueError(
                                f"{source}:{member}:{line_number}: truncated Table 2 row "
                                f"({len(line)} characters; expected at least 130)"
                            )
                        seq = line[23:29].strip()
                        if not seq.isascii() or not seq.isdecimal():
                            raise ValueError(
                                f"{source}:{member}:{line_number}: invalid authoritative Seq {seq!r}"
                            )
                        seq_value = int(seq)
                        if not 1 <= seq_value <= 781_604:
                            raise ValueError(
                                f"{source}:{member}:{line_number}: authoritative Seq "
                                f"{seq_value} is outside the documented range 1..781604"
                            )
                        rows.append(
                            {
                                "ID": line[:22].strip(),
                                "Seq": str(seq_value),
                                "gmag": line[89:95].strip(),
                                "rmag": line[96:102].strip(),
                                "Per-g": line[103:116].strip(),
                                "Per-r": line[117:130].strip(),
                            }
                        )
            except UnicodeDecodeError:
                continue
            if rows:
                ids = [row["Seq"] for row in rows]
                if len(ids) != len(set(ids)):
                    raise ValueError(f"{source}:{member}: duplicate authoritative Seq values")
                if len(rows) != expected_parent_count:
                    raise ValueError(
                        f"{source}:{member}: expected {expected_parent_count} Table 2 rows, "
                        f"found {len(rows)}"
                    )
                return headers, rows
    raise ValueError(f"{source}: no fixed-width CPVS Table 2 rows with ZTF IDs were found")


def build_cpvs_discrepancy_report(
    *,
    parent_metadata: str | Path,
    candidate_ids: str | Path,
    published_ids: str | Path,
    output_dir: str | Path,
    source_revision: str,
    report_code_revision: str = "UNRECORDED",
    parent_evidence: str | Path | None = None,
    candidate_evidence: str | Path | None = None,
    candidate_diagnostic: str | Path | None = None,
    expected_parent_count: int = 781_602,
) -> dict[str, Any]:
    """Write CSV, strict JSON manifest, searchable HTML and Markdown summary."""
    if (
        not source_revision.strip()
        or source_revision.strip().upper() == "UNRECORDED"
    ):
        raise ValueError(
            "source_revision must identify the revision that produced the inputs"
        )
    parent_path, candidate_path, published_path = map(
        Path, (parent_metadata, candidate_ids, published_ids)
    )
    headers, parent_rows = read_parent_metadata(
        parent_path, expected_parent_count=expected_parent_count
    )
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

    if candidate_evidence is not None and candidate_diagnostic is not None:
        raise ValueError("provide candidate evidence or candidate diagnostic, not both")
    evidence_files: dict[str, dict[str, Any]] = {}
    evidence_metadata: dict[str, dict[str, Any]] = {}
    for name, evidence_path in (
        ("parent_evidence", parent_evidence),
        ("candidate_evidence", candidate_evidence),
        ("candidate_diagnostic", candidate_diagnostic),
    ):
        if evidence_path is None:
            continue
        evidence_file = Path(evidence_path)
        if not evidence_file.is_file():
            raise ValueError(
                f"missing source evidence sidecar for {name}: {evidence_file}"
            )
        try:
            parsed_evidence = json.loads(
                evidence_file.read_text(encoding="utf-8"),
                parse_constant=_reject_nonfinite_json_constant,
            )
        except (UnicodeDecodeError, ValueError) as exc:
            raise ValueError(
                f"invalid strict JSON in source sidecar {name}: {exc}"
            ) from exc
        if not isinstance(parsed_evidence, dict):
            raise TypeError(f"source sidecar {name} must contain a JSON object")
        evidence_files[name] = {
            "path": str(evidence_file),
            "sha256": sha256_file(evidence_file),
            "bytes": evidence_file.stat().st_size,
        }
        evidence_metadata[name] = parsed_evidence

    candidates = read_ids(candidate_path)
    if candidate_diagnostic is not None:
        diagnostic = evidence_metadata["candidate_diagnostic"]
        observed_count = diagnostic.get("observed_selected_rows")
        candidate_digest = diagnostic.get("candidate_sha256")
        if diagnostic.get("status") != "COUNT_MISMATCH":
            raise ValueError("candidate diagnostic status is not COUNT_MISMATCH")
        if observed_count != len(candidates):
            raise ValueError(
                "candidate diagnostic count does not match the candidate ID file"
            )
        if candidate_digest != sha256_file(candidate_path):
            raise ValueError(
                "candidate diagnostic SHA-256 does not match the candidate ID file"
            )
    published = published_membership_ids(published_path, parent_rows, id_key)
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
        "report_code_revision": report_code_revision,
        "source_evidence_files": evidence_files,
        "source_evidence_metadata": evidence_metadata,
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
        "source_context": {
            "parent_metadata": {
                "catalogue": "ZTF Catalog of Periodic Variable Stars, Table 2",
                "source_url": "https://zenodo.org/records/3886372",
                "identifier_field": "Seq",
            },
            "candidate_ids": {
                "method": "source-backed reconstruction output; see scientific-validation workflow diagnostics",
                "source_revision": source_revision,
                "evidence_kind": (
                    "diagnostic"
                    if candidate_diagnostic is not None
                    else "successful_derivation"
                    if candidate_evidence is not None
                    else "not_provided"
                ),
                "photometry_source_url": "https://zenodo.org/records/3886372",
            },
            "published_ids": {
                "catalogue": "Chan et al. (2022), J/ApJ/932/118, Table 4",
                "source_url": "https://vizier.cds.unistra.fr/viz-bin/asu-tsv?-source=J/ApJ/932/118/table4&-out=ZTF,ID&-out.max=1000000",
                "membership_join": "normalized ZTF object name crosswalk to Table 2 Seq",
            },
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
        cells = []
        for key in visible:
            value = str(record.get(key, ""))
            if key == "SourceID":
                safe_id = html.escape(value, quote=True)
                cells.append(
                    f"<td><a href='cpvs_object_detail.html#{safe_id}'>{safe_id}</a></td>"
                )
            else:
                cells.append(f"<td>{html.escape(value)}</td>")
        table_rows.append(f"<tr>{''.join(cells)}</tr>")
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

    detail_data = json.dumps(records, ensure_ascii=False, allow_nan=False)
    detail_data = (
        detail_data.replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
    )
    detail_path = out / "cpvs_object_detail.html"
    detail_path.write_text(
        "<!doctype html><html lang='en'><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width,initial-scale=1'>"
        "<title>CPVS object evidence detail</title>"
        "<style>body{font:15px system-ui;margin:2rem}input{padding:.6rem;width:20rem}"
        "dt{font-weight:700;margin-top:.6rem}dd{margin-left:0;overflow-wrap:anywhere}"
        ".warning{padding:.8rem;border:1px solid #b66}</style>"
        "<h1>CPVS object evidence detail</h1>"
        "<p class='warning'>Membership difference is not a discovery claim. "
        "Historical publisher selection semantics remain UNRESOLVED.</p>"
        "<label for='object-id'>SourceID</label> "
        "<input id='object-id' type='search' placeholder='Enter SourceID'> "
        "<button id='show'>Show object</button><p id='status'></p><dl id='details'></dl>"
        "<script>const records = "
        + detail_data
        + ";const field=document.getElementById('object-id');"
        "const details=document.getElementById('details');"
        "function show(){const id=field.value.trim();"
        "const row=records.find(x=>String(x.SourceID)===id);details.replaceChildren();"
        "if(!row){document.getElementById('status').textContent='No matching object in this report.';return;}"
        "document.getElementById('status').textContent='Evidence fields for SourceID '+id;"
        "for(const [key,value] of Object.entries(row)){const dt=document.createElement('dt');"
        "dt.textContent=key;const dd=document.createElement('dd');"
        "dd.textContent=value===null?'MISSING':String(value);details.append(dt,dd);}}"
        "document.getElementById('show').addEventListener('click',show);"
        "field.addEventListener('keydown',e=>{if(e.key==='Enter')show();});"
        "if(location.hash){field.value=decodeURIComponent(location.hash.slice(1));show();}"
        "</script></html>\n",
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
            ("object_detail_html", detail_path),
            ("summary_json", out / "cpvs_discrepancy_summary.json"),
            ("markdown", md_path),
        )
    }
    (out / "cpvs_discrepancy_manifest.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return summary
