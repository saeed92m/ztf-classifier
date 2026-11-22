"""Capture and verify a bounded DR24 API evidence bundle.

File hashes in this module cover the exact bytes written to each bundle file.
Per-OID canonical epoch hashes cover canonical JSON decoded from the API
response. The adapter does not expose original HATS/Parquet object bytes.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ztf_classifier.io.dr24_lightcurve import canonical_epoch_json_bytes

MANIFEST_SCHEMA_VERSION = "ztf-dr24-evidence-manifest-v1"
CHECKSUM_SCHEMA_VERSION = "ztf-dr24-evidence-checksums-v1"
API_SCHEMA_VERSION = "ztf-dr24-native-lightcurve-v1"
EXPORT_SCHEMA_VERSION = "ztf-dr24-raw-export-v0.2"
SOURCE_NAME = "IRSA ZTF DR24 Lightcurves HATS"
CATALOG_URI = "s3://ipac-irsa-ztf/ztf/enhanced/dr24/lc/hats"
API_METHOD = "POST"
API_PATH = "/v1/dr24/lightcurves"
FIXED_OIDS = (264114400013085, 264214400000912)
FILTER_BANDS = {1: "g", 2: "r", 3: "i"}
PINNED_OBJECTS: dict[int, dict[str, Any]] = {
    264114400013085: {
        "filterid": 1,
        "band": "g",
        "epoch_count": 78,
        "canonical_epoch_sha256": "735ee15135670a1a28b03b76edfb394e9c0c193d528f3da56ebb593468baf2a0",
    },
    264214400000912: {
        "filterid": 2,
        "band": "r",
        "epoch_count": 123,
        "canonical_epoch_sha256": "a37f6fa2ee91009805b6fab3a5563b793cba9e84f6a82ec333bae507442c70ae",
    },
}

_PROVENANCE_FIELDS = {
    "source",
    "release",
    "catalog_uri",
    "retrieved_at_utc",
    "query",
    "requested_oids",
    "returned_oids",
    "missing_oids",
    "schema_columns",
    "schema_columns_sha256",
    "epoch_count",
    "payload_sha256",
    "interpretation",
    "limitations",
}
_RECORD_FIELDS = {
    "objectid",
    "filterid",
    "fieldid",
    "rcid",
    "objra",
    "objdec",
    "catalog_nepochs",
    "epochs",
    "payload_sha256",
}
_EPOCH_FIELDS = {"hmjd", "mag", "magerr", "clrcoeff", "catflags"}
_QC_FIELDS = {
    "objectid",
    "schema_version",
    "policy_id",
    "policy_status",
    "raw_data_mutated",
    "epochs",
    "counts",
    "interpretation",
    "source_documents",
}
_SECRET_KEY_RE = re.compile(
    r"(?i)(?:authorization|cookie|set-cookie|api[_-]?key|access[_-]?token|"
    r"refresh[_-]?token|password|secret|credential)"
)
_SECRET_VALUE_PATTERNS = (
    (re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/-]+=*"), "bearer"),
    (
        re.compile(
            r"(?i)\b(api[_-]?key|access[_-]?token|password|secret)\s*[:=]\s*[^\s,;]+"
        ),
        "assignment",
    ),
    (re.compile(r"(?i)(https?://)[^/@\s:]+:[^/@\s]+@"), "url"),
)
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class EvidenceBundleError(ValueError):
    """Raised when an evidence bundle is malformed or fails a required gate."""


def utc_now() -> str:
    """Return an ISO-8601 UTC timestamp."""
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def sha256_bytes(data: bytes) -> str:
    """Hash the exact supplied bytes."""
    return hashlib.sha256(data).hexdigest()


def redact_secrets(value: Any) -> Any:
    """Recursively redact credential-like keys and values before logging."""
    if isinstance(value, Mapping):
        return {
            str(key): "[REDACTED]"
            if _SECRET_KEY_RE.search(str(key))
            else redact_secrets(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact_secrets(item) for item in value]
    if isinstance(value, tuple):
        return tuple(redact_secrets(item) for item in value)
    if isinstance(value, str):
        result = value
        for pattern, kind in _SECRET_VALUE_PATTERNS:
            if kind == "bearer":
                replacement = "Bearer [REDACTED]"
            elif kind == "assignment":
                replacement = lambda match: match.group(1) + "=[REDACTED]"
            else:
                replacement = lambda match: match.group(1) + "[REDACTED]@"
            result = pattern.sub(replacement, result)
        return result
    return value


def _contains_secret_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        return any(
            _SECRET_KEY_RE.search(str(key)) or _contains_secret_key(item)
            for key, item in value.items()
        )
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return any(_contains_secret_key(item) for item in value)
    if isinstance(value, str):
        return any(pattern.search(value) for pattern, _ in _SECRET_VALUE_PATTERNS)
    return False


def _json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)
        + "\n"
    ).encode("utf-8")


def _is_sha256(value: Any) -> bool:
    return isinstance(value, str) and _SHA256_RE.fullmatch(value) is not None


def _required_fields(
    value: Mapping[str, Any], fields: set[str], label: str
) -> list[str]:
    missing = sorted(fields - set(value))
    return [f"missing_{label}_fields:{','.join(missing)}"] if missing else []


def validate_api_payload(
    payload: Any,
    *,
    expected_objects: Mapping[int, Mapping[str, Any]] = PINNED_OBJECTS,
) -> tuple[list[str], dict[int, bytes]]:
    """Validate fixed OIDs and return canonical epoch bytes by OID.

    Errors are stable codes and never include arbitrary source text.
    """
    errors: list[str] = []
    canonical_by_oid: dict[int, bytes] = {}
    if not isinstance(payload, dict):
        return ["api_payload_not_object"], canonical_by_oid
    if _contains_secret_key(payload):
        return ["api_payload_contains_sensitive_fields"], canonical_by_oid
    if payload.get("schema_version") != API_SCHEMA_VERSION:
        errors.append("api_schema_version_mismatch")
    provenance = payload.get("provenance")
    if not isinstance(provenance, dict):
        return errors + ["provenance_not_object"], canonical_by_oid
    errors.extend(_required_fields(provenance, _PROVENANCE_FIELDS, "provenance"))
    if any(item.startswith("missing_provenance_fields") for item in errors):
        return errors, canonical_by_oid

    if provenance.get("source") != SOURCE_NAME:
        errors.append("provenance_source_mismatch")
    if provenance.get("release") != "DR24":
        errors.append("provenance_release_mismatch")
    if provenance.get("catalog_uri") != CATALOG_URI:
        errors.append("provenance_catalog_uri_mismatch")
    query = provenance.get("query")
    expected_oid_list = list(expected_objects)
    if query != {"index": "objectid", "objectids": expected_oid_list}:
        errors.append("request_parameters_mismatch")
    if provenance.get("requested_oids") != expected_oid_list:
        errors.append("requested_oids_mismatch")
    if provenance.get("returned_oids") != expected_oid_list:
        errors.append("returned_oids_mismatch")
    if provenance.get("missing_oids") != []:
        errors.append("missing_oids_present")
    retrieved_at = provenance.get("retrieved_at_utc")
    if not isinstance(retrieved_at, str) or not _valid_utc_timestamp(retrieved_at):
        errors.append("invalid_retrieved_at_utc")
    if not isinstance(provenance.get("schema_columns"), list) or not _is_sha256(
        provenance.get("schema_columns_sha256")
    ):
        errors.append("invalid_schema_provenance")
    else:
        columns = provenance["schema_columns"]
        if any(not isinstance(column, str) for column in columns):
            errors.append("invalid_schema_columns")
        else:
            schema_bytes = json.dumps(
                columns, separators=(",", ":"), ensure_ascii=True
            ).encode("utf-8")
            if sha256_bytes(schema_bytes) != provenance["schema_columns_sha256"]:
                errors.append("schema_columns_digest_mismatch")

    records = payload.get("records")
    if not isinstance(records, list):
        return errors + ["records_not_array"], canonical_by_oid
    seen: set[int] = set()
    for record in records:
        if not isinstance(record, dict):
            errors.append("record_not_object")
            continue
        errors.extend(_required_fields(record, _RECORD_FIELDS, "record"))
        oid = record.get("objectid")
        if (
            isinstance(oid, bool)
            or not isinstance(oid, int)
            or oid not in expected_objects
        ):
            errors.append("unexpected_or_invalid_oid")
            continue
        if oid in seen:
            errors.append(f"duplicate_oid:{oid}")
            continue
        seen.add(oid)
        expected = expected_objects[oid]
        filterid = record.get("filterid")
        band = FILTER_BANDS.get(filterid) if isinstance(filterid, int) else None
        if (
            isinstance(filterid, bool)
            or not isinstance(filterid, int)
            or filterid != expected["filterid"]
            or band != expected["band"]
        ):
            errors.append(f"filter_band_mismatch:{oid}")
        epochs = record.get("epochs")
        if not isinstance(epochs, list):
            errors.append(f"epochs_not_array:{oid}")
            continue
        if any(
            not isinstance(epoch, dict) or set(epoch) != _EPOCH_FIELDS
            for epoch in epochs
        ):
            errors.append(f"epoch_schema_mismatch:{oid}")
            continue
        counted = len(epochs)
        catalog_count = record.get("catalog_nepochs")
        if isinstance(catalog_count, bool) or not isinstance(catalog_count, int):
            errors.append(f"invalid_catalog_epoch_count:{oid}")
        elif catalog_count != counted:
            errors.append(f"catalog_epoch_count_mismatch:{oid}")
        if counted != expected["epoch_count"]:
            errors.append(f"pinned_epoch_count_mismatch:{oid}")
        try:
            canonical_bytes = canonical_epoch_json_bytes(epochs)
        except (TypeError, ValueError):
            errors.append(f"canonical_epoch_encoding_failed:{oid}")
            continue
        canonical_by_oid[oid] = canonical_bytes
        digest = sha256_bytes(canonical_bytes)
        if (
            not _is_sha256(record.get("payload_sha256"))
            or record["payload_sha256"] != digest
        ):
            errors.append(f"record_canonical_digest_mismatch:{oid}")
        if digest != expected["canonical_epoch_sha256"]:
            errors.append(f"pinned_canonical_digest_mismatch:{oid}")
        provenance_digests = provenance.get("payload_sha256")
        if (
            not isinstance(provenance_digests, dict)
            or provenance_digests.get(str(oid)) != digest
        ):
            errors.append(f"provenance_canonical_digest_mismatch:{oid}")

    if seen != set(expected_objects):
        errors.append("fixed_oid_set_mismatch")
    if provenance.get("epoch_count") != sum(
        len(record.get("epochs", [])) for record in records if isinstance(record, dict)
    ):
        errors.append("provenance_epoch_count_mismatch")
    qc = payload.get("qc_assessments")
    if not isinstance(qc, list) or len(qc) != len(expected_objects):
        errors.append("qc_assessment_set_mismatch")
    else:
        qc_oids: list[int] = []
        for item in qc:
            if (
                not isinstance(item, dict)
                or item.get("objectid") not in expected_objects
            ):
                errors.append("qc_assessment_oid_mismatch")
                continue
            qc_oids.append(item["objectid"])
            if not _QC_FIELDS.issubset(item):
                errors.append(f"qc_assessment_schema_mismatch:{item['objectid']}")
        if len(qc_oids) != len(expected_oid_list) or set(qc_oids) != set(
            expected_oid_list
        ):
            errors.append("qc_assessment_oid_set_mismatch")
    return sorted(set(errors)), canonical_by_oid


def _valid_utc_timestamp(value: str) -> bool:
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return False
    return (
        parsed.tzinfo is not None
        and parsed.utcoffset() is not None
        and parsed.utcoffset().total_seconds() == 0
    )


def _validate_workbench_export(
    export_bytes: bytes,
    payload: dict[str, Any],
) -> list[str]:
    try:
        exported = json.loads(export_bytes)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return ["workbench_export_invalid_json"]
    if not isinstance(exported, dict) or _contains_secret_key(exported):
        return ["workbench_export_unsafe_or_not_object"]
    if exported.get("export_schema_version") != EXPORT_SCHEMA_VERSION:
        return ["workbench_export_schema_mismatch"]
    if exported.get("source_payload") != payload:
        return ["workbench_export_payload_mismatch"]
    if not isinstance(exported.get("exported_at_utc"), str) or not _valid_utc_timestamp(
        exported["exported_at_utc"]
    ):
        return ["workbench_export_timestamp_invalid"]
    return []


def validate_manifest_structure(manifest: Any) -> list[str]:
    """Check the versioned evidence-manifest shape without third-party deps."""
    required = {
        "schema_version",
        "capture_status",
        "source",
        "request",
        "execution",
        "objects",
        "files",
        "limitations",
    }
    if not isinstance(manifest, dict):
        return ["manifest_not_object"]
    errors = _required_fields(manifest, required, "manifest")
    if errors:
        return errors
    if manifest.get("schema_version") != MANIFEST_SCHEMA_VERSION:
        errors.append("manifest_schema_version_mismatch")
    if manifest.get("capture_status") not in {"PASS", "FAIL"}:
        errors.append("manifest_capture_status_invalid")
    for section in ("source", "request", "execution", "files"):
        if not isinstance(manifest.get(section), dict):
            errors.append(f"manifest_{section}_not_object")
    if not isinstance(manifest.get("objects"), list):
        errors.append("manifest_objects_not_array")
    if not isinstance(manifest.get("limitations"), list):
        errors.append("manifest_limitations_not_array")
    request = manifest.get("request")
    if isinstance(request, dict):
        errors.extend(
            _required_fields(
                request,
                {
                    "api_method",
                    "api_path",
                    "query",
                    "requested_oids",
                    "returned_oids",
                    "missing_oids",
                    "http_status_code",
                },
                "manifest_request",
            )
        )
        if request.get("requested_oids") != list(FIXED_OIDS):
            errors.append("manifest_requested_oids_mismatch")
        if not isinstance(request.get("returned_oids"), list):
            errors.append("manifest_returned_oids_invalid")
        if not isinstance(request.get("missing_oids"), list):
            errors.append("manifest_missing_oids_invalid")
    source = manifest.get("source")
    if isinstance(source, dict):
        errors.extend(
            _required_fields(
                source,
                {
                    "name",
                    "release",
                    "catalog_uri",
                    "original_source_files_available",
                    "original_source_file_sha256",
                    "source_bytes_note",
                    "retrieved_at_utc",
                },
                "manifest_source",
            )
        )
        if (
            source.get("original_source_files_available") is not False
            or source.get("original_source_file_sha256") is not None
        ):
            errors.append("manifest_original_source_bytes_claim_invalid")
    execution = manifest.get("execution")
    if isinstance(execution, dict):
        errors.extend(
            _required_fields(
                execution,
                {
                    "started_at_utc",
                    "completed_at_utc",
                    "software_commit_sha",
                    "python_version",
                    "dependency_lockfile",
                    "dependency_lockfile_sha256",
                    "dr24_dependency_lockfile",
                    "dr24_dependency_lockfile_sha256",
                    "test_command",
                    "test_result",
                    "log_file",
                },
                "manifest_execution",
            )
        )
        if not _is_sha256(execution.get("dependency_lockfile_sha256")):
            errors.append("manifest_dependency_lock_digest_invalid")
        if not _is_sha256(execution.get("dr24_dependency_lockfile_sha256")):
            errors.append("manifest_dr24_dependency_lock_digest_invalid")
        for field in ("started_at_utc", "completed_at_utc"):
            value = execution.get(field)
            if not isinstance(value, str) or not _valid_utc_timestamp(value):
                errors.append(f"manifest_execution_timestamp_invalid:{field}")
        if execution.get("test_result") not in {"PASS", "FAIL"}:
            errors.append("manifest_execution_test_result_invalid")
    if isinstance(manifest.get("objects"), list):
        manifest_oids: list[int] = []
        for item in manifest["objects"]:
            if not isinstance(item, dict):
                errors.append("manifest_object_not_object")
                continue
            oid = item.get("objectid")
            if isinstance(oid, int) and not isinstance(oid, bool):
                manifest_oids.append(oid)
            for field in (
                "objectid",
                "filterid",
                "band",
                "catalog_epoch_count",
                "counted_epoch_count",
                "canonical_epoch_sha256",
                "canonical_epoch_file",
                "canonical_epoch_file_sha256",
            ):
                if field not in item:
                    errors.append(f"manifest_object_missing:{field}")
            for field in ("canonical_epoch_sha256", "canonical_epoch_file_sha256"):
                if field in item and not _is_sha256(item[field]):
                    errors.append(f"manifest_object_invalid:{field}")
            if oid in PINNED_OBJECTS:
                pinned = PINNED_OBJECTS[oid]
                if (
                    item.get("filterid") != pinned["filterid"]
                    or item.get("band") != pinned["band"]
                ):
                    errors.append(f"manifest_object_filter_band_mismatch:{oid}")
                if item.get("catalog_epoch_count") != item.get("counted_epoch_count"):
                    errors.append(f"manifest_object_epoch_count_mismatch:{oid}")
        if manifest.get("capture_status") == "PASS" and manifest_oids != list(
            FIXED_OIDS
        ):
            errors.append("passing_manifest_oid_set_mismatch")
    files = manifest.get("files")
    if isinstance(files, dict):
        errors.extend(
            _required_fields(
                files,
                {
                    "api_response_file_sha256",
                    "api_response_sha256_covers",
                    "workbench_export_file_sha256",
                    "workbench_export_sha256_covers",
                    "workbench_export_capture_mode",
                    "canonical_epoch_sha256",
                },
                "manifest_files",
            )
        )
        for field in ("api_response_file_sha256", "workbench_export_file_sha256"):
            digest = files.get(field)
            if digest is not None and not _is_sha256(digest):
                errors.append(f"manifest_files_invalid:{field}")
        if manifest.get("capture_status") == "PASS" and any(
            not _is_sha256(files.get(field))
            for field in ("api_response_file_sha256", "workbench_export_file_sha256")
        ):
            errors.append("passing_manifest_missing_payload_digest")
    if (
        manifest.get("capture_status") == "PASS"
        and isinstance(request, dict)
        and (
            request.get("returned_oids") != list(FIXED_OIDS)
            or request.get("missing_oids") != []
        )
    ):
        errors.append("passing_manifest_request_oid_set_mismatch")
    return sorted(set(errors))


def _artifact_entry(path: str, data: bytes) -> dict[str, Any]:
    return {
        "path": path,
        "sha256": sha256_bytes(data),
        "sha256_covers": "exact file bytes",
        "size_bytes": len(data),
    }


def write_evidence_bundle(
    output_dir: str | Path,
    *,
    api_response_bytes: bytes,
    api_status_code: int,
    software_commit_sha: str,
    python_version: str,
    dependency_lock_sha256: str | None,
    dr24_dependency_lock_sha256: str | None,
    execution_started_at_utc: str,
    execution_completed_at_utc: str,
    test_command: str,
    execution_log_path: str | None = None,
    workbench_export_bytes: bytes | None = None,
    expected_objects: Mapping[int, Mapping[str, Any]] = PINNED_OBJECTS,
) -> tuple[Path, list[str]]:
    """Write a non-overwriting bundle and return its directory and gate errors.

    If no actual browser download is supplied, the Workbench export file is
    projected from this same API payload and labelled as derived, never as a
    browser execution.
    """
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    existing = {item.name for item in root.iterdir()}
    if existing - {"capture.log"}:
        raise EvidenceBundleError("output directory must be empty; refusing overwrite")
    errors: list[str] = []
    if not _is_sha256(dependency_lock_sha256):
        errors.append("dependency_lockfile_sha256_missing_or_invalid")
    if not _is_sha256(dr24_dependency_lock_sha256):
        errors.append("dr24_dependency_lockfile_sha256_missing_or_invalid")
    safe_payload: dict[str, Any] | None = None
    api_file_bytes: bytes | None = None
    try:
        parsed = json.loads(api_response_bytes)
        if isinstance(parsed, dict) and not _contains_secret_key(parsed):
            safe_payload = parsed
            api_file_bytes = api_response_bytes
        else:
            errors.append("api_response_unsafe_or_not_object")
    except (UnicodeDecodeError, json.JSONDecodeError):
        errors.append("api_response_invalid_json")
    if api_status_code != 200:
        errors.append("api_http_status_not_200")

    canonical_by_oid: dict[int, bytes] = {}
    if safe_payload is not None:
        payload_errors, canonical_by_oid = validate_api_payload(
            safe_payload, expected_objects=expected_objects
        )
        errors.extend(payload_errors)
    if api_file_bytes is not None:
        (root / "api_response.json").write_bytes(api_file_bytes)

    object_entries: list[dict[str, Any]] = []
    if safe_payload is not None:
        for oid, canonical_bytes in sorted(canonical_by_oid.items()):
            relative = f"canonical/oid_{oid}_epochs.json"
            destination = root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(canonical_bytes)
            record = next(
                item
                for item in safe_payload.get("records", [])
                if isinstance(item, dict) and item.get("objectid") == oid
            )
            object_entries.append(
                {
                    "objectid": oid,
                    "filterid": record.get("filterid"),
                    "band": FILTER_BANDS.get(record.get("filterid")),
                    "catalog_epoch_count": record.get("catalog_nepochs"),
                    "counted_epoch_count": len(record.get("epochs", [])),
                    "canonical_epoch_sha256": sha256_bytes(canonical_bytes),
                    "canonical_epoch_sha256_covers": (
                        "canonical UTF-8 JSON of this OID's decoded epoch array; "
                        "sorted object keys, compact separators, source epoch order preserved"
                    ),
                    "canonical_epoch_file": relative,
                    "canonical_epoch_file_sha256": sha256_bytes(canonical_bytes),
                }
            )

    export_bytes: bytes | None = None
    export_mode = "unavailable"
    if safe_payload is not None:
        if workbench_export_bytes is None:
            export = {
                "export_schema_version": EXPORT_SCHEMA_VERSION,
                "exported_at_utc": execution_completed_at_utc,
                "source_payload": safe_payload,
                "interpretation": (
                    "Raw source payload preserved. QC is diagnostic only; "
                    "no epochs were filtered or grouped."
                ),
            }
            export_bytes = _json_bytes(export)
            export_mode = "derived_from_same_api_response_not_browser_download"
        else:
            export_errors = _validate_workbench_export(
                workbench_export_bytes, safe_payload
            )
            errors.extend(export_errors)
            if not export_errors:
                export_bytes = workbench_export_bytes
                export_mode = "provided_actual_workbench_download"
        if export_bytes is not None:
            (root / "workbench_export.json").write_bytes(export_bytes)

    files = {
        "api_response_file_sha256": (
            sha256_bytes(api_file_bytes) if api_file_bytes is not None else None
        ),
        "api_response_sha256_covers": "exact bytes of api_response.json; decoded API JSON, not source HATS/Parquet bytes",
        "workbench_export_file_sha256": (
            sha256_bytes(export_bytes) if export_bytes is not None else None
        ),
        "workbench_export_sha256_covers": (
            "exact bytes of workbench_export.json; mode is recorded separately"
        ),
        "workbench_export_capture_mode": export_mode,
        "canonical_epoch_sha256": {
            str(item["objectid"]): item["canonical_epoch_sha256"]
            for item in object_entries
        },
    }
    provenance = safe_payload.get("provenance", {}) if safe_payload else {}
    manifest = {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "capture_status": "PASS" if not errors else "FAIL",
        "source": {
            "name": SOURCE_NAME,
            "release": "DR24",
            "catalog_uri": CATALOG_URI,
            "original_source_files_available": False,
            "original_source_file_sha256": None,
            "source_bytes_note": (
                "The current LSDB/API adapter exposes decoded native records, "
                "not original HATS/Parquet object bytes."
            ),
            "retrieved_at_utc": provenance.get("retrieved_at_utc"),
        },
        "request": {
            "api_method": API_METHOD,
            "api_path": API_PATH,
            "query": {"index": "objectid", "objectids": list(expected_objects)},
            "requested_oids": list(expected_objects),
            "returned_oids": provenance.get("returned_oids", []),
            "missing_oids": provenance.get("missing_oids", list(expected_objects)),
            "http_status_code": api_status_code,
        },
        "execution": {
            "started_at_utc": execution_started_at_utc,
            "completed_at_utc": execution_completed_at_utc,
            "software_commit_sha": software_commit_sha,
            "python_version": python_version,
            "dependency_lockfile": "requirements.lock",
            "dependency_lockfile_sha256": dependency_lock_sha256,
            "dr24_dependency_lockfile": "requirements-dr24.lock",
            "dr24_dependency_lockfile_sha256": dr24_dependency_lock_sha256,
            "test_command": test_command,
            "test_result": "PASS" if not errors else "FAIL",
            "log_file": execution_log_path,
        },
        "objects": object_entries,
        "files": files,
        "validation_errors": sorted(set(errors)),
        "limitations": [
            "Decoded source records are not original HATS/Parquet bytes.",
            "A derived Workbench export is not evidence of browser execution.",
            "This bundle is acquisition and provenance evidence, not scientific validation.",
        ],
    }
    manifest_errors = validate_manifest_structure(manifest)
    if manifest_errors:
        errors.extend(manifest_errors)
        manifest["capture_status"] = "FAIL"
        manifest["execution"]["test_result"] = "FAIL"
        manifest["validation_errors"] = sorted(set(errors))
    manifest_bytes = _json_bytes(manifest)
    (root / "manifest.json").write_bytes(manifest_bytes)

    checksums: dict[str, Any] = {
        "schema_version": CHECKSUM_SCHEMA_VERSION,
        "manifest_file_sha256": sha256_bytes(manifest_bytes),
        "manifest_file_sha256_covers": "exact bytes of manifest.json",
        "files": {},
    }
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.name not in {"manifest.json", "checksums.json"}:
            relative = path.relative_to(root).as_posix()
            data = path.read_bytes()
            checksums["files"][relative] = _artifact_entry(relative, data)
    checksums_bytes = _json_bytes(checksums)
    (root / "checksums.json").write_bytes(checksums_bytes)
    errors.extend(validate_evidence_bundle(root))
    return root, sorted(set(errors))


def validate_evidence_bundle(bundle_dir: str | Path) -> list[str]:
    """Verify manifest schema, sidecar checksums, and each recorded file hash."""
    root = Path(bundle_dir)
    errors: list[str] = []
    try:
        manifest_bytes = (root / "manifest.json").read_bytes()
        manifest = json.loads(manifest_bytes)
        checksums = json.loads((root / "checksums.json").read_bytes())
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return ["bundle_manifest_or_checksum_file_unreadable"]
    errors.extend(validate_manifest_structure(manifest))
    if (
        not isinstance(checksums, dict)
        or checksums.get("schema_version") != CHECKSUM_SCHEMA_VERSION
    ):
        return sorted(set(errors + ["checksums_schema_invalid"]))
    if checksums.get("manifest_file_sha256") != sha256_bytes(manifest_bytes):
        errors.append("manifest_file_sha256_mismatch")
    expected_files = checksums.get("files")
    if not isinstance(expected_files, dict):
        errors.append("checksums_files_not_object")
        expected_files = {}
    actual_files = {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file() and path.name not in {"manifest.json", "checksums.json"}
    }
    if actual_files != set(expected_files):
        errors.append("bundle_file_inventory_mismatch")
    for relative, entry in expected_files.items():
        target = (root / relative).resolve()
        if root.resolve() not in target.parents or not target.is_file():
            errors.append(f"bundle_file_missing_or_unsafe:{relative}")
            continue
        if (
            not isinstance(entry, dict)
            or entry.get("sha256_covers") != "exact file bytes"
        ):
            errors.append(f"bundle_file_checksum_metadata_invalid:{relative}")
            continue
        data = target.read_bytes()
        if entry.get("sha256") != sha256_bytes(data) or entry.get("size_bytes") != len(
            data
        ):
            errors.append(f"bundle_file_checksum_mismatch:{relative}")

    files = manifest.get("files", {}) if isinstance(manifest, dict) else {}
    for manifest_key, relative in (
        ("api_response_file_sha256", "api_response.json"),
        ("workbench_export_file_sha256", "workbench_export.json"),
    ):
        expected = files.get(manifest_key) if isinstance(files, dict) else None
        target = root / relative
        if expected is None:
            if target.exists():
                errors.append(f"unexpected_bundle_file:{relative}")
        elif not target.is_file() or sha256_bytes(target.read_bytes()) != expected:
            errors.append(f"manifest_digest_mismatch:{relative}")

    objects = manifest.get("objects", []) if isinstance(manifest, dict) else []
    for item in objects:
        if not isinstance(item, dict):
            errors.append("manifest_object_not_object")
            continue
        relative = item.get("canonical_epoch_file")
        if not isinstance(relative, str):
            errors.append(f"canonical_epoch_file_path_invalid:{item.get('objectid')}")
            continue
        target = (root / relative).resolve()
        if root.resolve() not in target.parents or not target.is_file():
            errors.append(f"canonical_epoch_file_missing:{item.get('objectid')}")
            continue
        actual = sha256_bytes(target.read_bytes())
        if actual != item.get("canonical_epoch_sha256"):
            errors.append(f"canonical_epoch_digest_mismatch:{item.get('objectid')}")
        if actual != item.get("canonical_epoch_file_sha256"):
            errors.append(
                f"canonical_epoch_file_sha256_mismatch:{item.get('objectid')}"
            )

    if manifest.get("capture_status") == "PASS" and manifest.get("validation_errors"):
        errors.append("passing_manifest_contains_validation_errors")
    return sorted(set(errors))


__all__ = [
    "API_PATH",
    "CATALOG_URI",
    "FIXED_OIDS",
    "MANIFEST_SCHEMA_VERSION",
    "PINNED_OBJECTS",
    "EvidenceBundleError",
    "redact_secrets",
    "sha256_bytes",
    "utc_now",
    "validate_api_payload",
    "validate_evidence_bundle",
    "validate_manifest_structure",
    "write_evidence_bundle",
]
