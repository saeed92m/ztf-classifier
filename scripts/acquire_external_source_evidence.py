"""Acquire live source-backed DR24 and ALeRCE evidence through TAP.

The adapter is deliberately fail-closed: it executes only the query recorded in
the benchmark manifest, preserves the raw VOTable response, validates schema,
row count, ordering, and object-ID uniqueness, and emits an immutable evidence
manifest. It never invents labels or benchmark PASS results.
"""

from __future__ import annotations

import argparse
from io import BytesIO
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from xml.etree import ElementTree

import pandas as pd
import requests
from astropy.io import votable

from ztf_classifier.validation.evidence import EvidenceArtifact, write_evidence_manifest
from ztf_classifier.validation.manifest import BenchmarkManifest
from ztf_classifier.validation.registry import BenchmarkRegistry


class SourceQueryError(RuntimeError):
    """Raised when a source-backed query cannot produce valid evidence."""


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _tap_query(endpoint: str, query: str, timeout: float) -> bytes:
    response = requests.post(
        endpoint.rstrip("/") + "/sync",
        data={"REQUEST": "doQuery", "LANG": "ADQL", "FORMAT": "votable", "QUERY": query},
        timeout=timeout,
        headers={"User-Agent": "ztf-classifier-scientific-validation/0.4"},
    )
    response.raise_for_status()
    payload = response.content
    if not payload.lstrip().lower().startswith((b"<?xml", b"<votable", b"<vo:")):
        raise SourceQueryError("TAP response is not a VOTable")
    return payload


def _tap_error_message(payload: bytes) -> str | None:
    """Extract a TAP QUERY_STATUS error before table parsing hides the cause."""
    try:
        root = ElementTree.fromstring(payload)
    except ElementTree.ParseError:
        return None
    for element in root.iter():
        local_name = element.tag.rsplit("}", 1)[-1].upper()
        if local_name != "INFO" or element.attrib.get("name", "").upper() != "QUERY_STATUS":
            continue
        value = element.attrib.get("value", "").strip().upper()
        message = " ".join((element.text or "").split())
        if value == "ERROR":
            return message or "TAP returned QUERY_STATUS=ERROR"
    return None


def _tap_schema_hint(endpoint: str, timeout: float) -> str | None:
    """Return current TAP table names matching ZTF, for actionable failures."""
    query = (
        "SELECT TOP 50 table_name FROM TAP_SCHEMA.tables "
        "WHERE LOWER(table_name) LIKE '%ztf%' ORDER BY table_name"
    )
    try:
        response = requests.post(
            endpoint.rstrip("/") + "/sync",
            data={"REQUEST": "doQuery", "LANG": "ADQL", "FORMAT": "csv", "QUERY": query},
            timeout=timeout,
            headers={"User-Agent": "ztf-classifier-scientific-validation/0.4"},
        )
        response.raise_for_status()
        names = [
            line.strip()
            for line in response.text.splitlines()[1:]
            if line.strip()
        ]
        return ", ".join(names) if names else None
    except requests.RequestException:
        return None


def _table_from_votable(payload: bytes) -> pd.DataFrame:
    tap_error = _tap_error_message(payload)
    if tap_error:
        raise SourceQueryError(f"TAP query failed: {tap_error}")
    try:
        resource = votable.parse(BytesIO(payload))
        table = resource.get_first_table().to_table(use_names_over_ids=True)
    except Exception as exc:
        raise SourceQueryError(f"cannot parse TAP VOTable: {exc}") from exc
    frame = table.to_pandas()
    frame.columns = [str(column).lower() for column in frame.columns]
    return frame


def _validate(frame: pd.DataFrame, expected: list[str], object_id: str, limit: int) -> None:
    missing = [name for name in expected if name not in frame.columns]
    if missing:
        raise SourceQueryError("TAP response missing expected columns: " + ", ".join(missing))
    if len(frame) != limit:
        raise SourceQueryError(f"expected exactly {limit} rows, got {len(frame)}")
    if frame[object_id].isna().any():
        raise SourceQueryError(f"{object_id} contains null values")
    ids = frame[object_id].astype(str).tolist()
    if len(set(ids)) != len(ids):
        raise SourceQueryError(f"{object_id} contains duplicate values")
    if ids != sorted(ids):
        raise SourceQueryError(f"{object_id} is not deterministically sorted")


def _write_result(root: Path, benchmark_id: str, query: str, endpoint: str, payload: bytes,
                  frame: pd.DataFrame, object_id: str, expected: list[str], limit: int,
                  code_version: str) -> None:
    root.mkdir(parents=True, exist_ok=True)
    raw = root / "response.vot"
    table = root / "response.tsv"
    query_file = root / "query.json"
    raw.write_bytes(payload)
    frame.to_csv(table, sep="\t", index=False, lineterminator="\n")
    query_file.write_text(
        json.dumps(
            {
                "provider_endpoint": endpoint,
                "query": query,
                "retrieval_timestamp": datetime.now(UTC).isoformat(),
                "response_sha256": _sha256(payload),
                "row_count": len(frame),
                "object_id_column": object_id,
                "expected_columns": expected,
                "max_rows": limit,
            },
            indent=2,
            sort_keys=True,
        ) + "\n",
        encoding="utf-8",
    )
    write_evidence_manifest(
        root / "response.vot.evidence.json",
        benchmark_id=benchmark_id,
        source_id=benchmark_id,
        acquisition_timestamp=datetime.now(UTC).isoformat(),
        code_version=code_version,
        artifacts=(
            EvidenceArtifact.from_path(raw, "benchmark_snapshot"),
            EvidenceArtifact.from_path(table, "normalized_response"),
            EvidenceArtifact.from_path(query_file, "query_manifest"),
        ),
        query_manifest_sha256=_sha256(query_file.read_bytes()),
        row_count=len(frame),
    )


def acquire_benchmark(registry_dir: Path, benchmark_id: str, output_root: Path,
                      code_version: str, timeout: float) -> Path:
    manifest = BenchmarkRegistry(registry_dir).load(benchmark_id)
    query = manifest.input_contract.get("query")
    qm = manifest.input_contract.get("query_manifest")
    if benchmark_id == "alerce_reference":
        if not isinstance(query, str) or not isinstance(qm, dict):
            raise SourceQueryError("ALeRCE query contract is incomplete")
        endpoint = str(qm["endpoint"])
        expected = [str(x) for x in qm["expected_columns"]]
        object_id = "oid"
        limit = int(qm["max_rows"])
    elif benchmark_id == "ztf_dr24_source_subset":
        if not isinstance(query, dict):
            raise SourceQueryError("DR24 query contract is incomplete")
        endpoint = str(query["tap_endpoint"])
        query_text = str(query["tap_query"])
        expected = [str(x) for x in query["expected_columns"]]
        object_id = str(query["object_id_column"])
        limit = int(query["selection"]["limit"])
        query = query_text
    else:
        raise SourceQueryError(f"unsupported external benchmark: {benchmark_id}")

    try:
        payload = _tap_query(endpoint, str(query), timeout)
    except SourceQueryError as exc:
        hint = _tap_schema_hint(endpoint, timeout)
        if hint:
            raise SourceQueryError(f"{exc}; available ZTF TAP tables: {hint}") from exc
        raise
    frame = _table_from_votable(payload)
    _validate(frame, expected, object_id, limit)
    root = output_root / benchmark_id
    _write_result(root, benchmark_id, str(query), endpoint, payload, frame,
                  object_id, expected, limit, code_version)
    return root


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry-dir", type=Path, default=Path("configs/benchmarks"))
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--code-version", default="working-tree")
    parser.add_argument("--timeout", type=float, default=120.0)
    args = parser.parse_args()

    for benchmark_id in ("ztf_dr24_source_subset", "alerce_reference"):
        acquire_benchmark(args.registry_dir, benchmark_id, args.output_root,
                          args.code_version, args.timeout)
        print(f"acquired={benchmark_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
