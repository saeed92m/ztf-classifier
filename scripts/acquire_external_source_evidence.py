"""Acquire live source-backed DR24 and ALeRCE evidence.

DR24 is acquired from IRSA's official HATS Objects Table through its secondary
OID index. ALeRCE remains a live TAP source. Both paths fail closed and emit
content-addressed normalized evidence; neither path fabricates benchmark data.
"""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import hashlib
from io import BytesIO
import json
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.dataset as ds
import pyarrow.fs as pafs
import pyarrow.parquet as pq
import requests
from astropy.io import votable

from ztf_classifier.validation.evidence import EvidenceArtifact, write_evidence_manifest
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
    from xml.etree import ElementTree

    try:
        root = ElementTree.fromstring(payload)
    except ElementTree.ParseError:
        return None
    for element in root.iter():
        local_name = element.tag.rsplit("}", 1)[-1].upper()
        if local_name != "INFO" or element.attrib.get("name", "").upper() != "QUERY_STATUS":
            continue
        if element.attrib.get("value", "").strip().upper() == "ERROR":
            message = " ".join((element.text or "").split())
            return message or "TAP returned QUERY_STATUS=ERROR"
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
        raise SourceQueryError("source response missing expected columns: " + ", ".join(missing))
    if len(frame) != limit:
        raise SourceQueryError(f"expected exactly {limit} rows, got {len(frame)}")
    if frame[object_id].isna().any():
        raise SourceQueryError(f"{object_id} contains null values")
    ids = frame[object_id].astype(str).tolist()
    if len(set(ids)) != len(ids):
        raise SourceQueryError(f"{object_id} contains duplicate values")
    if ids != sorted(ids):
        raise SourceQueryError(f"{object_id} is not deterministically sorted")


def _write_result(
    root: Path,
    benchmark_id: str,
    query_manifest: dict[str, object],
    frame: pd.DataFrame,
    code_version: str,
    source_artifacts: tuple[tuple[Path, str], ...] = (),
) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    table = root / "response.tsv"
    query_file = root / "query.json"
    frame.to_csv(table, sep="\t", index=False, lineterminator="\n")
    query_file.write_text(
        json.dumps(
            {
                **query_manifest,
                "retrieval_timestamp": datetime.now(UTC).isoformat(),
                "row_count": len(frame),
                "response_sha256": _sha256(table.read_bytes()),
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    artifacts = [
        EvidenceArtifact.from_path(table, "normalized_response"),
        EvidenceArtifact.from_path(query_file, "query_manifest"),
    ]
    artifacts.extend(EvidenceArtifact.from_path(path, role) for path, role in source_artifacts)
    write_evidence_manifest(
        root / "response.tsv.evidence.json",
        benchmark_id=benchmark_id,
        source_id=benchmark_id,
        acquisition_timestamp=datetime.now(UTC).isoformat(),
        code_version=code_version,
        artifacts=tuple(artifacts),
        query_manifest_sha256=_sha256(query_file.read_bytes()),
        row_count=len(frame),
    )
    return root


def _fragment_range(fragment: ds.Fragment, object_id: str) -> tuple[object, object, int]:
    metadata = fragment.metadata
    if metadata is None:
        raise SourceQueryError(f"HATS index fragment has no Parquet metadata: {fragment}")
    try:
        column_index = fragment.physical_schema.get_field_index(object_id)
    except KeyError as exc:
        raise SourceQueryError(f"HATS index has no {object_id!r} column") from exc
    if column_index < 0:
        raise SourceQueryError(f"HATS index has no {object_id!r} column")
    minima: list[object] = []
    maxima: list[object] = []
    for row_group in range(metadata.num_row_groups):
        stats = metadata.row_group(row_group).column(column_index).statistics
        if stats is None or not stats.has_min_max:
            raise SourceQueryError(
                f"HATS index fragment lacks min/max statistics for {object_id}: {fragment.path}"
            )
        minima.append(stats.min)
        maxima.append(stats.max)
    return min(minima), max(maxima), metadata.num_rows


def _select_hats_index_rows(
    filesystem: pafs.FileSystem,
    index_root: str,
    object_id: str,
    limit: int,
) -> pa.Table:
    dataset = ds.dataset(index_root, filesystem=filesystem, format="parquet")
    fragments = list(dataset.get_fragments())
    if not fragments:
        raise SourceQueryError("DR24 HATS OID index contains no Parquet fragments")
    ranges = sorted(
        (_fragment_range(fragment, object_id) + (fragment,))
        for fragment in fragments
    )
    previous_max: object | None = None
    selected_fragments: list[ds.Fragment] = []
    estimated_rows = 0
    for minimum, maximum, rows, fragment in ranges:
        if previous_max is not None and minimum <= previous_max:
            raise SourceQueryError("DR24 HATS OID index ranges overlap or are not strictly ordered")
        previous_max = maximum
        selected_fragments.append(fragment)
        estimated_rows += rows
        if estimated_rows >= limit:
            break
    else:
        raise SourceQueryError(
            f"DR24 HATS OID index contains fewer than {limit} indexed rows"
        )

    tables = [
        fragment.to_table(columns=[object_id, "Norder", "Npix"])
        for fragment in selected_fragments
    ]
    index = pa.concat_tables(tables, promote_options="default")
    index = index.sort_by([(object_id, "ascending")])
    if index.num_rows < limit:
        raise SourceQueryError(
            f"DR24 HATS OID index produced only {index.num_rows} rows from selected ranges"
        )
    return index.slice(0, limit)


def _read_hats_objects(
    filesystem: pafs.FileSystem,
    objects_root: str,
    index_rows: pa.Table,
    object_id: str,
    expected_columns: list[str],
) -> pd.DataFrame:
    ids = index_rows[object_id].to_pylist()
    grouped: dict[tuple[int, int, int], list[object]] = {}
    for oid, norder, npix in zip(
        ids,
        index_rows["Norder"].to_pylist(),
        index_rows["Npix"].to_pylist(),
    ):
        directory = (int(npix) // 10_000) * 10_000
        grouped.setdefault((int(norder), directory, int(npix)), []).append(oid)

    frames: list[pd.DataFrame] = []
    source_rows: list[dict[str, object]] = []
    for (norder, directory, npix), requested_ids in sorted(grouped.items()):
        partition = (
            f"{objects_root}/dataset/Norder={norder}/Dir={directory}/Npix={npix}"
        )
        direct = filesystem.get_file_info(partition)
        if direct.type == pafs.FileType.File:
            files = [partition] if partition.endswith(".parquet") else []
        else:
            info = filesystem.get_file_info(pafs.FileSelector(partition, recursive=True))
            files = [
                item.path
                for item in info
                if item.type == pafs.FileType.File and item.path.endswith(".parquet")
            ]
        if not files:
            raise SourceQueryError(f"DR24 HATS partition has no Parquet data: {partition}")
        partition_dataset = ds.dataset(files, filesystem=filesystem, format="parquet")
        filter_expr = pc.is_in(
            ds.field(object_id),
            value_set=pa.array(requested_ids),
        )
        table = partition_dataset.to_table(
            columns=[object_id, "ra", "dec", "ngoodobsrel"],
            filter=filter_expr,
        )
        frame = table.to_pandas()
        frames.append(frame)
        source_rows.append(
            {
                "partition": partition,
                "files": files,
                "requested_ids": [str(value) for value in requested_ids],
                "returned_rows": len(frame),
            }
        )

    if not frames:
        raise SourceQueryError("DR24 HATS returned no source partitions")
    frame = pd.concat(frames, ignore_index=True)
    frame.columns = [str(column).lower() for column in frame.columns]
    frame = frame.rename(columns={"oid": "oid", "ra": "ra", "dec": "dec"})
    _validate(frame, expected_columns, object_id, len(ids))
    frame.attrs["source_rows"] = source_rows
    return frame


def _acquire_dr24(
    registry_dir: Path,
    output_root: Path,
    code_version: str,
) -> Path:
    manifest = BenchmarkRegistry(registry_dir).load("ztf_dr24_source_subset")
    query = manifest.input_contract.get("query")
    if not isinstance(query, dict):
        raise SourceQueryError("DR24 query contract is incomplete")
    bucket = str(query["bucket"])
    objects_prefix = str(query["objects_prefix"])
    index_prefix = str(query["index_prefix"])
    object_id = str(query["object_id_column"])
    expected = [str(x) for x in query["expected_columns"]]
    limit = int(query["selection"]["limit"])

    filesystem = pafs.S3FileSystem(anonymous=True, region="us-east-1")
    index_root = f"{bucket}/{index_prefix}/dataset"
    objects_root = f"{bucket}/{objects_prefix}"
    index_rows = _select_hats_index_rows(filesystem, index_root, object_id, limit)
    frame = _read_hats_objects(filesystem, objects_root, index_rows, object_id, expected)

    root = output_root / "ztf_dr24_source_subset"
    source_manifest = root / "source_partitions.json"
    source_manifest.parent.mkdir(parents=True, exist_ok=True)
    source_manifest.write_text(
        json.dumps(
            {
                "bucket": bucket,
                "objects_prefix": objects_prefix,
                "index_prefix": index_prefix,
                "index_rows": limit,
                "partitions": frame.attrs.get("source_rows", []),
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    frame = frame.sort_values(object_id, kind="mergesort").reset_index(drop=True)
    return _write_result(
        root,
        "ztf_dr24_source_subset",
        {
            "provider": "IRSA ZTF DR24 HATS",
            "source": query["source"],
            "release": query["release"],
            "release_date": query["release_date"],
            "bucket": bucket,
            "objects_prefix": objects_prefix,
            "index_prefix": index_prefix,
            "object_id_column": object_id,
            "selection": query["selection"],
            "expected_columns": expected,
            "observation_cutoff": query["observation_cutoff"],
            "source_manifest": str(source_manifest.relative_to(root)),
        },
        frame,
        code_version,
        source_artifacts=((source_manifest, "source_partition_manifest"),),
    )


def _acquire_alerce(
    registry_dir: Path,
    output_root: Path,
    code_version: str,
    timeout: float,
) -> Path:
    manifest = BenchmarkRegistry(registry_dir).load("alerce_reference")
    query = manifest.input_contract.get("query")
    query_manifest = manifest.input_contract.get("query_manifest")
    if not isinstance(query, str) or not isinstance(query_manifest, dict):
        raise SourceQueryError("ALeRCE query contract is incomplete")
    endpoint = str(query_manifest["endpoint"])
    expected = [str(x) for x in query_manifest["expected_columns"]]
    object_id = "oid"
    limit = int(query_manifest["max_rows"])
    payload = _tap_query(endpoint, query, timeout)
    frame = _table_from_votable(payload)
    _validate(frame, expected, object_id, limit)
    root = output_root / "alerce_reference"
    raw = root / "response.vot"
    root.mkdir(parents=True, exist_ok=True)
    raw.write_bytes(payload)
    result = _write_result(
        root,
        "alerce_reference",
        {
            "provider_endpoint": endpoint,
            "query": query,
            "schema": query_manifest["schema"],
            "expected_columns": expected,
            "object_id_column": object_id,
            "max_rows": limit,
        },
        frame,
        code_version,
        source_artifacts=((raw, "benchmark_snapshot"),),
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry-dir", type=Path, default=Path("configs/benchmarks"))
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--code-version", default="working-tree")
    parser.add_argument("--timeout", type=float, default=120.0)
    args = parser.parse_args()

    _acquire_dr24(args.registry_dir, args.output_root, args.code_version)
    print("acquired=ztf_dr24_source_subset")
    _acquire_alerce(args.registry_dir, args.output_root, args.code_version, args.timeout)
    print("acquired=alerce_reference")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
