"""Capture and verify a bounded DR24 API evidence bundle.

File hashes in this module cover the exact bytes written to each bundle file.
Per-OID canonical epoch hashes cover canonical JSON decoded from the API
response. The adapter does not expose original HATS/Parquet object bytes.
"""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import math
import re
import tomllib
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet
from packaging.utils import canonicalize_name
from packaging.version import InvalidVersion, Version

from ztf_classifier.io.dr24_lightcurve import canonical_epoch_json_bytes

LEGACY_MANIFEST_SCHEMA_VERSION = "ztf-dr24-evidence-manifest-v1"
MANIFEST_SCHEMA_VERSION = "ztf-dr24-evidence-manifest-v2"
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
    r"(?i)(?:authorization|cookie|set-cookie|api[_-]?key|access[_-]?key|"
    r"access[_-]?token|refresh[_-]?token|password|secret|credential|token)"
)
_SECRET_VALUE_PATTERNS = (
    (re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/-]+=*"), "bearer"),
    (
        re.compile(r"(?i)(authorization|proxy-authorization)\s*[:=]\s*[^\r\n]+"),
        "header",
    ),
    (re.compile(r"(?i)(cookie|set-cookie)\s*[:=]\s*[^\r\n]+"), "header"),
    (
        re.compile(
            r"(?i)\b(api[_-]?key|access[_-]?key|access[_-]?token|refresh[_-]?token|token|password|secret|credential|client_secret)\s*[:=]\s*[^\s,;]+"
        ),
        "assignment",
    ),
    (
        re.compile(
            r"(?i)\b([A-Z][A-Z0-9_]*(?:TOKEN|API[_-]?KEY|ACCESS[_-]?KEY|SECRET|PASSWORD|CREDENTIAL)[A-Z0-9_]*)\s*=\s*([^\s,;]+)"
        ),
        "environment",
    ),
    (re.compile(r"(?i)(https?://)[^/@\s:]+:[^/@\s]+@"), "url"),
    (
        re.compile(
            r"(?i)([?&](?:token|api[_-]?key|access[_-]?token|access[_-]?key|client_secret)=)[^&#\s]+"
        ),
        "query",
    ),
)
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_COMMIT_SHA_RE = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
_LOCK_FILES = ("requirements.lock", "requirements-dr24.lock")
_PROJECT_FILE = "pyproject.toml"
_BUNDLE_DEPENDENCY_DIR = "dependencies"
_DEPENDENCY_PATHS = {
    "requirements.lock": "dependencies/requirements.lock",
    "requirements-dr24.lock": "dependencies/requirements-dr24.lock",
    "pyproject.toml": "dependencies/pyproject.toml",
}
_MANIFEST_SCHEMA_PATHS = {
    LEGACY_MANIFEST_SCHEMA_VERSION: "dr24-evidence-manifest-v1.schema.json",
    MANIFEST_SCHEMA_VERSION: "dr24-evidence-manifest-v2.schema.json",
}


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
            elif kind == "header":
                replacement = lambda match: match.group(1) + ": [REDACTED]"
            elif kind == "query":
                replacement = lambda match: match.group(1) + "[REDACTED]"
            elif kind == "environment":
                replacement = lambda match: match.group(1) + "=[REDACTED]"
            else:
                replacement = lambda match: match.group(1) + "[REDACTED]@"
            result = pattern.sub(replacement, result)
        return result
    return value


def redact_log_text(value: str) -> str:
    """Redact credential-like values from diagnostics before artifact upload."""
    return str(redact_secrets(value))


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


def _finite_number(value: Any) -> bool:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    try:
        return math.isfinite(value)
    except (OverflowError, TypeError, ValueError):
        return False


def _repository_root() -> Path:
    return Path(__file__).resolve().parents[3]


@lru_cache(maxsize=2)
def _load_manifest_schema(schema_version: str) -> dict[str, Any]:
    filename = _MANIFEST_SCHEMA_PATHS.get(schema_version)
    if filename is None:
        raise ValueError("unsupported_manifest_schema_version")
    path = _repository_root() / "schemas" / filename
    schema = json.loads(path.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return schema


@lru_cache(maxsize=2)
def _manifest_validator(schema_version: str) -> Draft202012Validator:
    schema = _load_manifest_schema(schema_version)
    return Draft202012Validator(schema, format_checker=FormatChecker())


def _lock_snapshot(
    lock_bytes: Mapping[str, bytes] | None = None,
) -> tuple[dict[str, bytes], dict[str, str], dict[str, str], list[str]]:
    snapshots: dict[str, bytes] = {}
    base_pins: dict[str, str] = {}
    dr24_pins: dict[str, str] = {}
    errors: list[str] = []
    root = _repository_root()
    for filename in _LOCK_FILES:
        try:
            data = (
                lock_bytes[filename]
                if lock_bytes is not None and filename in lock_bytes
                else (root / filename).read_bytes()
            )
        except OSError:
            errors.append(f"dependency_lock_unreadable:{filename}")
            continue
        if not isinstance(data, bytes):
            errors.append(f"dependency_lock_not_bytes:{filename}")
            continue
        snapshots[filename] = data
        pins = base_pins if filename == "requirements.lock" else dr24_pins
        try:
            for line in data.decode("utf-8").splitlines():
                item = line.partition("#")[0].strip()
                if not item:
                    continue
                match = re.fullmatch(r"([A-Za-z0-9_.-]+)==([^\s;]+)", item)
                if not match:
                    errors.append(f"dependency_lock_entry_not_exact_pin:{filename}")
                    continue
                name = canonicalize_name(match.group(1))
                version = match.group(2)
                try:
                    Version(version)
                except InvalidVersion:
                    errors.append(f"dependency_lock_version_invalid:{name}")
                pins[name] = version
            if not pins:
                errors.append(f"dependency_lock_empty:{filename}")
        except UnicodeDecodeError:
            errors.append(f"dependency_lock_not_utf8:{filename}")

    for name in sorted(base_pins.keys() & dr24_pins.keys()):
        if base_pins[name] != dr24_pins[name]:
            errors.append(f"dependency_lock_version_conflict:{name}")
    return snapshots, base_pins, dr24_pins, sorted(set(errors))


def check_dependency_compatibility(
    resolved_versions: Mapping[str, str] | None = None,
    *,
    lock_bytes: Mapping[str, bytes] | None = None,
    project_bytes: bytes | None = None,
) -> tuple[list[str], dict[str, str]]:
    """Compare resolved versions, exact locks, and declared project constraints."""
    snapshots, base_pins, dr24_pins, errors = _lock_snapshot(lock_bytes)
    pins = dict(base_pins)
    pins.update(dr24_pins)
    normalized_runtime: dict[str, str] = {}
    supplied: dict[str, str] | None = None
    if resolved_versions is not None:
        supplied = {}
        for name, version in resolved_versions.items():
            try:
                normalized_name = canonicalize_name(name)
            except (TypeError, ValueError):
                errors.append("resolved_dependency_name_invalid")
                continue
            if normalized_name in supplied:
                errors.append(f"resolved_dependency_duplicate:{normalized_name}")
            version_text = str(version)
            if version_text != "MISSING":
                try:
                    Version(version_text)
                except InvalidVersion:
                    version_text = "INVALID"
                    errors.append(
                        f"resolved_dependency_version_invalid:{normalized_name}"
                    )
            supplied[normalized_name] = version_text
        for name in sorted(supplied.keys() - pins.keys()):
            errors.append(f"resolved_dependency_not_locked:{name}")

    for name, locked in sorted(pins.items()):
        if supplied is not None:
            installed = supplied.get(name, "MISSING")
        else:
            try:
                installed = importlib.metadata.version(name)
            except importlib.metadata.PackageNotFoundError:
                installed = "MISSING"
        normalized_runtime[name] = installed
        if installed != locked:
            errors.append(f"runtime_lock_version_mismatch:{name}")

    try:
        if project_bytes is None:
            project_bytes = (_repository_root() / _PROJECT_FILE).read_bytes()
        project = tomllib.loads(project_bytes.decode("utf-8"))
        core_requirements = [
            Requirement(item) for item in project["project"]["dependencies"]
        ]
        dr24_requirements = [
            Requirement(item)
            for item in project["project"]["optional-dependencies"]["dr24"]
        ]
    except (OSError, UnicodeDecodeError, KeyError, TypeError, tomllib.TOMLDecodeError):
        core_requirements = []
        dr24_requirements = []
        errors.append("dr24_dependency_constraints_unreadable")

    for label, requirements, lock_pins in (
        ("project", core_requirements, base_pins),
        ("dr24", dr24_requirements, dr24_pins),
    ):
        for requirement in requirements:
            name = canonicalize_name(requirement.name)
            locked = lock_pins.get(name)
            if locked is None:
                errors.append(f"{label}_dependency_missing_from_lock:{name}")
                continue
            try:
                if (
                    requirement.specifier
                    and Version(locked) not in requirement.specifier
                ):
                    errors.append(f"{label}_lock_violates_project_constraint:{name}")
                installed = normalized_runtime.get(name, "MISSING")
                if (
                    installed != "MISSING"
                    and requirement.specifier
                    and Version(installed) not in requirement.specifier
                ):
                    errors.append(f"runtime_violates_project_constraint:{name}")
            except InvalidVersion:
                errors.append(f"dependency_version_invalid:{name}")

    nested_pandas_version = dr24_pins.get("nested-pandas")
    pandas_version = dr24_pins.get("pandas")
    if nested_pandas_version is not None:
        # nested-pandas 0.6.10 declares this upper bound; keep it explicit in
        # offline bundle verification as well as checking installed metadata.
        if nested_pandas_version == "0.6.10":
            nested_constraint = SpecifierSet(">=2.2.3,<2.4")
            try:
                if (
                    pandas_version is None
                    or Version(pandas_version) not in nested_constraint
                ):
                    errors.append("nested_pandas_pandas_constraint_mismatch")
            except InvalidVersion:
                errors.append("nested_pandas_pandas_version_invalid")
            resolved_pandas = normalized_runtime.get("pandas", "MISSING")
            try:
                if (
                    resolved_pandas == "MISSING"
                    or Version(resolved_pandas) not in nested_constraint
                ):
                    errors.append("nested_pandas_runtime_constraint_mismatch")
            except InvalidVersion:
                errors.append("nested_pandas_runtime_pandas_version_invalid")
        if resolved_versions is None:
            try:
                requirements = importlib.metadata.requires("nested-pandas") or []
                pandas_requirements = [
                    Requirement(item)
                    for item in requirements
                    if canonicalize_name(Requirement(item).name) == "pandas"
                ]
                if not pandas_requirements:
                    errors.append("nested_pandas_pandas_requirement_unavailable")
                for requirement in pandas_requirements:
                    actual = normalized_runtime.get("pandas", "MISSING")
                    if actual == "MISSING" or (
                        requirement.specifier
                        and Version(actual) not in requirement.specifier
                    ):
                        errors.append("installed_nested_pandas_constraint_mismatch")
            except (importlib.metadata.PackageNotFoundError, InvalidVersion):
                errors.append("nested_pandas_metadata_unavailable")

    # Preserve hashes as part of the returned dependency snapshot contract.
    for filename in _LOCK_FILES:
        if filename not in snapshots:
            errors.append(f"dependency_lock_unreadable:{filename}")
    return sorted(set(errors)), normalized_runtime


def _required_fields(
    value: Mapping[str, Any], fields: set[str], label: str
) -> list[str]:
    missing = sorted(fields - set(value))
    return [f"missing_{label}_fields:{','.join(missing)}"] if missing else []


def validate_api_payload(
    payload: Any,
    *,
    expected_objects: Mapping[int, Mapping[str, Any]] | None = None,
) -> tuple[list[str], dict[int, bytes]]:
    """Validate fixed OIDs and return canonical epoch bytes by OID.

    Errors are stable codes and never include arbitrary source text.
    """
    errors: list[str] = []
    canonical_by_oid: dict[int, bytes] = {}
    expected_objects = PINNED_OBJECTS if expected_objects is None else expected_objects
    if tuple(expected_objects) != FIXED_OIDS:
        errors.append("expected_oid_policy_invalid")
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
        malformed_values = False
        for epoch in epochs:
            for field in ("hmjd", "mag", "magerr"):
                value = epoch[field]
                if not _finite_number(value) or (field == "magerr" and value < 0):
                    malformed_values = True
            color_coefficient = epoch["clrcoeff"]
            if color_coefficient is not None and (
                not _finite_number(color_coefficient)
            ):
                malformed_values = True
            if isinstance(epoch["catflags"], bool) or not isinstance(
                epoch["catflags"], int
            ):
                malformed_values = True
        if malformed_values:
            errors.append(f"epoch_value_invalid:{oid}")
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
    total_counted_epochs = sum(
        len(record.get("epochs"))
        for record in records
        if isinstance(record, dict) and isinstance(record.get("epochs"), list)
    )
    provenance_count = provenance.get("epoch_count")
    if (
        isinstance(provenance_count, bool)
        or not isinstance(provenance_count, int)
        or provenance_count != total_counted_epochs
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
    """Validate a supported manifest instance with its versioned JSON Schema."""
    root_required = {
        "schema_version",
        "capture_status",
        "source",
        "request",
        "execution",
        "objects",
        "files",
        "validation_errors",
        "limitations",
    }
    if not isinstance(manifest, dict):
        return ["manifest_not_object"]
    missing = _required_fields(manifest, root_required, "manifest")
    if missing:
        return missing

    schema_version = manifest.get("schema_version")
    if schema_version not in _MANIFEST_SCHEMA_PATHS:
        return ["manifest_schema_version_unsupported"]
    try:
        validator = _manifest_validator(schema_version)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError):
        return ["manifest_schema_unavailable_or_invalid"]
    try:
        schema_errors = list(validator.iter_errors(manifest))
    except (TypeError, ValueError, RecursionError):
        return ["manifest_json_schema_validation_failed:runtime"]
    errors = [
        f"manifest_json_schema_validation_failed:{item.validator or 'unknown'}"
        for item in schema_errors
    ]
    if schema_errors or schema_version == LEGACY_MANIFEST_SCHEMA_VERSION:
        return sorted(set(errors))

    request = manifest["request"]
    execution = manifest["execution"]
    objects = manifest["objects"]
    files = manifest["files"]
    if request["requested_oids"] != list(FIXED_OIDS):
        errors.append("manifest_requested_oids_mismatch")
    returned = request["returned_oids"]
    missing = request["missing_oids"]
    if (
        len(returned) != len(set(returned))
        or any(oid not in FIXED_OIDS for oid in returned)
        or len(missing) != len(set(missing))
        or any(oid not in FIXED_OIDS for oid in missing)
        or set(returned) & set(missing)
        or set(returned) | set(missing) != set(FIXED_OIDS)
    ):
        errors.append("manifest_returned_missing_oid_partition_invalid")
    if execution["test_result"] != manifest["capture_status"]:
        errors.append("manifest_capture_test_result_mismatch")
    source_retrieved_at = manifest["source"].get("retrieved_at_utc")
    if source_retrieved_at is not None and not _valid_utc_timestamp(
        source_retrieved_at
    ):
        errors.append("manifest_source_retrieval_time_not_utc")
    for time_field in ("started_at_utc", "completed_at_utc"):
        timestamp = execution.get(time_field)
        if timestamp is not None and not _valid_utc_timestamp(timestamp):
            errors.append(f"manifest_execution_timestamp_not_utc:{time_field}")
    if execution["dependency_compatibility_status"] == "PASS":
        if any(
            version == "MISSING"
            for version in execution["resolved_dependencies"].values()
        ):
            errors.append("manifest_dependency_status_mismatch")
    elif manifest["capture_status"] == "PASS":
        errors.append("manifest_pass_with_incompatible_dependencies")

    object_oids: list[int] = []
    for item in objects:
        oid = item["objectid"]
        object_oids.append(oid)
        pinned = PINNED_OBJECTS.get(oid)
        if pinned and (
            item["filterid"] != pinned["filterid"] or item["band"] != pinned["band"]
        ):
            errors.append(f"manifest_object_filter_band_mismatch:{oid}")
        if item["catalog_epoch_count"] != item["counted_epoch_count"]:
            errors.append(f"manifest_object_epoch_count_mismatch:{oid}")
    if len(object_oids) != len(set(object_oids)):
        errors.append("manifest_object_oid_duplicate")
    if manifest["capture_status"] == "PASS" and object_oids != list(FIXED_OIDS):
        errors.append("passing_manifest_oid_set_mismatch")

    expected_digests = {
        str(item["objectid"]): item["canonical_epoch_sha256"] for item in objects
    }
    if files["canonical_epoch_sha256"] != expected_digests:
        errors.append("manifest_digest_map_inconsistent")
    if manifest["capture_status"] == "PASS":
        if returned != list(FIXED_OIDS) or missing:
            errors.append("passing_manifest_request_oid_set_mismatch")
        if request["http_status_code"] != 200:
            errors.append("passing_manifest_http_status_invalid")
        if execution["dependency_compatibility_status"] != "PASS":
            errors.append("manifest_pass_with_incompatible_dependencies")

    for field, relative in (
        ("dependency_lockfile_path", _DEPENDENCY_PATHS["requirements.lock"]),
        (
            "dr24_dependency_lockfile_path",
            _DEPENDENCY_PATHS["requirements-dr24.lock"],
        ),
        ("project_metadata_path", _DEPENDENCY_PATHS[_PROJECT_FILE]),
    ):
        if execution[field] != relative:
            errors.append("manifest_dependency_artifact_path_invalid")
    log_path = execution["log_file"]
    if log_path is not None and (
        ".." in Path(log_path).parts or Path(log_path).is_absolute()
    ):
        errors.append("manifest_log_path_unsafe")
    return sorted(set(errors))


def _safe_response_oids(payload: Any) -> list[int]:
    if not isinstance(payload, dict) or not isinstance(payload.get("records"), list):
        return []
    found: list[int] = []
    for record in payload["records"]:
        if not isinstance(record, dict):
            continue
        oid = record.get("objectid")
        if (
            isinstance(oid, int)
            and not isinstance(oid, bool)
            and oid in FIXED_OIDS
            and oid not in found
        ):
            found.append(oid)
    return found


def _parse_response_bytes(
    data: bytes,
) -> tuple[str, Any | None, bytes | None, list[str]]:
    if not data:
        return "EMPTY", None, None, ["api_response_empty"]

    def reject_nonstandard_number(_value: str) -> None:
        raise ValueError("nonstandard_json_number")

    try:
        parsed = json.loads(data, parse_constant=reject_nonstandard_number)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError, RecursionError):
        return "INVALID", None, None, ["api_response_invalid_json"]
    try:
        if _contains_secret_key(parsed):
            return "VALID", parsed, None, ["api_response_contains_sensitive_fields"]
    except RecursionError:
        return "INVALID", None, None, ["api_response_structure_too_deep"]
    return "VALID", parsed, data, []


def _safe_metadata_string(value: Any, *, pattern: re.Pattern[str]) -> str | None:
    return value if isinstance(value, str) and pattern.fullmatch(value) else None


def _write_manifest_and_checksums(root: Path, manifest: dict[str, Any]) -> None:
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
            checksums["files"][relative] = _artifact_entry(relative, path.read_bytes())
    (root / "checksums.json").write_bytes(_json_bytes(checksums))


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
    api_status_code: int | None,
    software_commit_sha: str,
    python_version: str,
    dependency_lock_sha256: str | None = None,
    dr24_dependency_lock_sha256: str | None = None,
    execution_started_at_utc: str,
    execution_completed_at_utc: str,
    test_command: str,
    execution_log_path: str | None = None,
    workbench_export_bytes: bytes | None = None,
    transport_status: str | None = None,
    transport_error_type: str | None = None,
    resolved_dependencies: Mapping[str, str] | None = None,
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
    if (root / "capture.log").is_symlink():
        raise EvidenceBundleError("capture log must not be a symlink")

    source_root = _repository_root()
    dependency_sources: dict[str, bytes] = {}
    for filename in (*_LOCK_FILES, _PROJECT_FILE):
        try:
            dependency_sources[filename] = (source_root / filename).read_bytes()
        except OSError:
            dependency_sources[filename] = b""
            errors.append(f"dependency_artifact_unreadable:{filename}")
        destination = root / _DEPENDENCY_PATHS[filename]
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(dependency_sources[filename])

    base_digest = sha256_bytes(dependency_sources["requirements.lock"])
    dr24_digest = sha256_bytes(dependency_sources["requirements-dr24.lock"])
    if dependency_lock_sha256 is not None and dependency_lock_sha256 != base_digest:
        errors.append("dependency_lockfile_sha256_input_mismatch")
    if (
        dr24_dependency_lock_sha256 is not None
        and dr24_dependency_lock_sha256 != dr24_digest
    ):
        errors.append("dr24_dependency_lockfile_sha256_input_mismatch")
    dependency_errors, resolved = check_dependency_compatibility(
        resolved_dependencies,
        lock_bytes={filename: dependency_sources[filename] for filename in _LOCK_FILES},
        project_bytes=dependency_sources[_PROJECT_FILE],
    )
    errors.extend(dependency_errors)

    normalized_sha = _safe_metadata_string(software_commit_sha, pattern=_COMMIT_SHA_RE)
    if normalized_sha is None:
        errors.append("software_commit_sha_invalid")
    normalized_python = _safe_metadata_string(
        python_version,
        pattern=re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+(?:[A-Za-z0-9.+-]*)$"),
    )
    if normalized_python is None:
        errors.append("python_version_invalid")

    started_value = (
        execution_started_at_utc
        if isinstance(execution_started_at_utc, str)
        and _valid_utc_timestamp(execution_started_at_utc)
        else None
    )
    completed_value = (
        execution_completed_at_utc
        if isinstance(execution_completed_at_utc, str)
        and _valid_utc_timestamp(execution_completed_at_utc)
        else None
    )
    if started_value is None:
        errors.append("execution_started_at_utc_invalid")
    if completed_value is None:
        errors.append("execution_completed_at_utc_invalid")
    if (
        started_value
        and completed_value
        and datetime.fromisoformat(completed_value)
        < datetime.fromisoformat(started_value)
    ):
        errors.append("execution_timestamp_order_invalid")

    sanitized_command = redact_log_text(str(test_command)).strip()
    if not sanitized_command:
        sanitized_command = "unavailable"
        errors.append("execution_test_command_missing")

    if execution_log_path is not None:
        log_path = Path(execution_log_path)
        if log_path.is_absolute() or ".." in log_path.parts:
            execution_log_path = None
            errors.append("execution_log_path_unsafe")
        else:
            log_file = root / log_path
            if not log_file.is_file() or log_file.is_symlink():
                execution_log_path = None
                errors.append("execution_log_file_missing_or_unsafe")
            else:
                try:
                    safe_log = redact_log_text(
                        log_file.read_text(encoding="utf-8", errors="replace")
                    )
                    log_file.write_text(safe_log, encoding="utf-8")
                except OSError:
                    execution_log_path = None
                    errors.append("execution_log_file_unreadable")

    status = transport_status or (
        "RESPONSE_RECEIVED" if api_status_code is not None else "NOT_ATTEMPTED"
    )
    if not isinstance(status, str) or status not in {
        "NOT_ATTEMPTED",
        "RESPONSE_RECEIVED",
        "CONNECTION_ERROR",
        "TIMEOUT",
        "REQUEST_ERROR",
    }:
        status = "REQUEST_ERROR"
        errors.append("transport_status_invalid")
    if status == "RESPONSE_RECEIVED":
        if (
            isinstance(api_status_code, bool)
            or not isinstance(api_status_code, int)
            or not 100 <= api_status_code <= 599
        ):
            http_status = None
            errors.append("http_status_missing_or_invalid")
        else:
            http_status = api_status_code
            if http_status != 200:
                errors.append("api_http_status_not_200")
    else:
        http_status = None
        if api_status_code is not None:
            errors.append("http_status_supplied_without_response")
        errors.append(f"api_transport_status:{status.lower()}")
    if status in {"CONNECTION_ERROR", "TIMEOUT", "REQUEST_ERROR"}:
        transport_error = _safe_metadata_string(
            transport_error_type,
            pattern=re.compile(r"^[A-Za-z][A-Za-z0-9_.]{0,127}$"),
        )
        if transport_error is None:
            transport_error = "UnknownError"
            errors.append("transport_error_type_missing_or_invalid")
    else:
        transport_error = None
        if transport_error_type is not None:
            errors.append("transport_error_without_transport_failure")
    if status == "NOT_ATTEMPTED":
        errors.append("api_request_not_attempted")

    response_parse_status = "NOT_AVAILABLE"
    safe_payload: dict[str, Any] | None = None
    api_file_bytes: bytes | None = None
    if status == "RESPONSE_RECEIVED":
        if not isinstance(api_response_bytes, bytes):
            response_parse_status = "INVALID"
            errors.append("api_response_bytes_invalid")
        else:
            response_parse_status, parsed, api_file_bytes, parse_errors = (
                _parse_response_bytes(api_response_bytes)
            )
            errors.extend(parse_errors)
            if isinstance(parsed, dict) and api_file_bytes is not None:
                safe_payload = parsed
            elif parsed is not None and api_file_bytes is not None:
                errors.append("api_payload_not_object")
        if api_file_bytes is not None:
            (root / "api_response.json").write_bytes(api_file_bytes)
        elif (root / "api_response.json").exists():
            (root / "api_response.json").unlink()
    elif api_response_bytes:
        errors.append("response_bytes_without_http_response")

    canonical_by_oid: dict[int, bytes] = {}
    if safe_payload is not None:
        try:
            payload_errors, canonical_by_oid = validate_api_payload(
                safe_payload, expected_objects=expected_objects
            )
            errors.extend(payload_errors)
        except (TypeError, ValueError, OverflowError, RecursionError):
            errors.append("api_payload_validation_failed_safely")

    record_map: dict[int, dict[str, Any]] = {}
    if safe_payload is not None and isinstance(safe_payload.get("records"), list):
        for record in safe_payload["records"]:
            if isinstance(record, dict):
                oid = record.get("objectid")
                if isinstance(oid, int) and not isinstance(oid, bool):
                    record_map.setdefault(oid, record)

    object_entries: list[dict[str, Any]] = []
    for oid, canonical_bytes in sorted(canonical_by_oid.items()):
        record = record_map.get(oid)
        if record is None:
            errors.append(f"canonical_record_missing:{oid}")
            continue
        relative = f"canonical/oid_{oid}_epochs.json"
        destination = root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(canonical_bytes)
        epochs = record.get("epochs")
        object_entries.append(
            {
                "objectid": oid,
                "filterid": record.get("filterid"),
                "band": FILTER_BANDS.get(record.get("filterid")),
                "catalog_epoch_count": record.get("catalog_nepochs"),
                "counted_epoch_count": len(epochs) if isinstance(epochs, list) else 0,
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
                "exported_at_utc": completed_value or utc_now(),
                "source_payload": safe_payload,
                "derived_from_api_response_sha256": sha256_bytes(api_file_bytes or b""),
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
    elif (root / "workbench_export.json").exists():
        (root / "workbench_export.json").unlink()

    provenance = safe_payload.get("provenance", {}) if safe_payload else {}
    if not isinstance(provenance, dict):
        provenance = {}
    returned_oids = _safe_response_oids(safe_payload)
    missing_oids = [oid for oid in FIXED_OIDS if oid not in returned_oids]
    retrieved_at = provenance.get("retrieved_at_utc")
    if not isinstance(retrieved_at, str) or not _valid_utc_timestamp(retrieved_at):
        retrieved_at = None

    files = {
        "api_response_file_sha256": (
            sha256_bytes(api_file_bytes) if api_file_bytes is not None else None
        ),
        "api_response_sha256_covers": (
            "exact bytes of api_response.json; decoded API response JSON, "
            "not original HATS/Parquet source bytes"
        ),
        "workbench_export_file_sha256": (
            sha256_bytes(export_bytes) if export_bytes is not None else None
        ),
        "workbench_export_sha256_covers": (
            "exact bytes of workbench_export.json; capture mode is recorded separately"
        ),
        "workbench_export_capture_mode": export_mode,
        "canonical_epoch_sha256": {
            str(item["objectid"]): item["canonical_epoch_sha256"]
            for item in object_entries
        },
    }
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
            "retrieved_at_utc": retrieved_at,
        },
        "request": {
            "api_method": API_METHOD,
            "api_path": API_PATH,
            "query": {"index": "objectid", "objectids": list(FIXED_OIDS)},
            "requested_oids": list(FIXED_OIDS),
            "returned_oids": returned_oids,
            "missing_oids": missing_oids,
            "http_status_code": http_status,
            "transport_status": status,
            "response_parse_status": response_parse_status,
            "transport_error_type": transport_error,
        },
        "execution": {
            "started_at_utc": started_value,
            "completed_at_utc": completed_value,
            "software_commit_sha": normalized_sha,
            "python_version": normalized_python,
            "dependency_lockfile": "requirements.lock",
            "dependency_lockfile_path": _DEPENDENCY_PATHS["requirements.lock"],
            "dependency_lockfile_sha256": base_digest,
            "dr24_dependency_lockfile": "requirements-dr24.lock",
            "dr24_dependency_lockfile_path": _DEPENDENCY_PATHS[
                "requirements-dr24.lock"
            ],
            "dr24_dependency_lockfile_sha256": dr24_digest,
            "project_metadata_path": _DEPENDENCY_PATHS[_PROJECT_FILE],
            "project_metadata_sha256": sha256_bytes(dependency_sources[_PROJECT_FILE]),
            "resolved_dependencies": resolved,
            "dependency_compatibility_status": (
                "PASS" if not dependency_errors else "FAIL"
            ),
            "test_command": sanitized_command,
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
    _write_manifest_and_checksums(root, manifest)

    independent_errors = validate_evidence_bundle(
        root, expected_objects=expected_objects
    )
    if independent_errors:
        errors.extend(independent_errors)
        manifest["capture_status"] = "FAIL"
        manifest["execution"]["test_result"] = "FAIL"
        manifest["validation_errors"] = sorted(set(errors))
        _write_manifest_and_checksums(root, manifest)
        independent_errors = validate_evidence_bundle(
            root, expected_objects=expected_objects
        )
        errors.extend(independent_errors)
    return root, sorted(set(errors))


def validate_evidence_bundle(
    bundle_dir: str | Path,
    *,
    expected_objects: Mapping[int, Mapping[str, Any]] = PINNED_OBJECTS,
) -> list[str]:
    """Independently verify a bundle from its manifest and saved file bytes."""
    root = Path(bundle_dir)
    errors: list[str] = []
    manifest_path = root / "manifest.json"
    checksums_path = root / "checksums.json"
    if manifest_path.is_symlink() or checksums_path.is_symlink():
        return ["bundle_manifest_or_checksum_file_unsafe"]
    try:
        manifest_bytes = manifest_path.read_bytes()
        manifest = json.loads(manifest_bytes)
        checksums = json.loads(checksums_path.read_bytes())
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, RecursionError):
        return ["bundle_manifest_or_checksum_file_unreadable"]
    errors.extend(validate_manifest_structure(manifest))
    if not isinstance(manifest, dict):
        return sorted(set(errors))
    if (
        not isinstance(checksums, dict)
        or checksums.get("schema_version") != CHECKSUM_SCHEMA_VERSION
        or checksums.get("manifest_file_sha256_covers")
        != "exact bytes of manifest.json"
    ):
        return sorted(set(errors + ["checksums_schema_invalid"]))
    if checksums.get("manifest_file_sha256") != sha256_bytes(manifest_bytes):
        errors.append("manifest_file_sha256_mismatch")

    expected_files = checksums.get("files")
    if not isinstance(expected_files, dict):
        errors.append("checksums_files_not_object")
        expected_files = {}
    actual_files: set[str] = set()
    for path in root.rglob("*"):
        if path.name in {"manifest.json", "checksums.json"}:
            continue
        if path.is_symlink():
            errors.append("bundle_symlink_not_allowed")
            continue
        if path.is_file():
            actual_files.add(path.relative_to(root).as_posix())
    if actual_files != set(expected_files):
        errors.append("bundle_file_inventory_mismatch")
    for relative, entry in expected_files.items():
        if (
            not isinstance(relative, str)
            or Path(relative).is_absolute()
            or ".." in Path(relative).parts
        ):
            errors.append("bundle_file_path_invalid")
            continue
        target = root / relative
        if target.is_symlink() or not target.is_file():
            errors.append("bundle_file_missing_or_unsafe")
            continue
        if (
            not isinstance(entry, dict)
            or entry.get("path") != relative
            or entry.get("sha256_covers") != "exact file bytes"
        ):
            errors.append("bundle_file_checksum_metadata_invalid")
            continue
        data = target.read_bytes()
        if entry.get("sha256") != sha256_bytes(data) or entry.get("size_bytes") != len(
            data
        ):
            errors.append(f"bundle_file_checksum_mismatch:{relative}")

    if manifest.get("schema_version") == LEGACY_MANIFEST_SCHEMA_VERSION:
        return sorted(set(errors + _validate_legacy_bundle_payloads(root, manifest)))
    if manifest.get("schema_version") != MANIFEST_SCHEMA_VERSION:
        return sorted(set(errors))

    request = manifest.get("request", {})
    execution = manifest.get("execution", {})
    manifest_files = manifest.get("files", {})
    objects = manifest.get("objects", [])
    if not all(isinstance(item, dict) for item in (request, execution, manifest_files)):
        return sorted(set(errors + ["manifest_sections_invalid_for_bundle_validation"]))

    dependency_bytes: dict[str, bytes] = {}
    for filename in (*_LOCK_FILES, _PROJECT_FILE):
        relative = _DEPENDENCY_PATHS[filename]
        target = root / relative
        try:
            if target.is_symlink() or not target.is_file():
                raise OSError
            data = target.read_bytes()
        except OSError:
            errors.append(f"dependency_artifact_missing_or_unsafe:{filename}")
            continue
        dependency_bytes[filename] = data
        digest_field = {
            "requirements.lock": "dependency_lockfile_sha256",
            "requirements-dr24.lock": "dr24_dependency_lockfile_sha256",
            "pyproject.toml": "project_metadata_sha256",
        }[filename]
        if execution.get(digest_field) != sha256_bytes(data):
            errors.append(f"dependency_artifact_digest_mismatch:{filename}")

    if len(dependency_bytes) == 3:
        dependency_errors, _ = check_dependency_compatibility(
            execution.get("resolved_dependencies", {}),
            lock_bytes={
                filename: dependency_bytes[filename] for filename in _LOCK_FILES
            },
            project_bytes=dependency_bytes[_PROJECT_FILE],
        )
        expected_dependency_status = "PASS" if not dependency_errors else "FAIL"
        if (
            execution.get("dependency_compatibility_status")
            != expected_dependency_status
        ):
            errors.append("dependency_compatibility_status_mismatch")
        errors.extend(dependency_errors)

    log_relative = execution.get("log_file")
    if log_relative is not None:
        log_path = root / log_relative
        if log_path.is_symlink() or not log_path.is_file():
            errors.append("execution_log_file_missing_or_unsafe")
        else:
            try:
                log_text = log_path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                errors.append("execution_log_file_unreadable")
            else:
                if redact_log_text(log_text) != log_text:
                    errors.append("execution_log_contains_unredacted_secret")

    api_path = root / "api_response.json"
    api_digest = manifest_files.get("api_response_file_sha256")
    parsed_payload: dict[str, Any] | None = None
    if api_digest is None:
        if api_path.exists():
            errors.append("unexpected_bundle_file:api_response.json")
        if request.get("response_parse_status") == "VALID":
            errors.append("api_response_file_missing")
    else:
        if api_path.is_symlink() or not api_path.is_file():
            errors.append("api_response_file_missing")
        else:
            api_bytes = api_path.read_bytes()
            if sha256_bytes(api_bytes) != api_digest:
                errors.append("manifest_digest_mismatch:api_response.json")
            parse_status, parsed, safe_bytes, parse_errors = _parse_response_bytes(
                api_bytes
            )
            if parse_status != request.get("response_parse_status"):
                errors.append("api_response_parse_status_mismatch")
            if safe_bytes is None:
                errors.extend(parse_errors)
            elif isinstance(parsed, dict):
                parsed_payload = parsed
            else:
                errors.append("api_payload_not_object")

    transport_status = request.get("transport_status")
    http_status = request.get("http_status_code")
    if transport_status == "RESPONSE_RECEIVED":
        if isinstance(http_status, bool) or not isinstance(http_status, int):
            errors.append("http_status_missing_for_response")
        elif http_status != 200:
            errors.append("api_http_status_not_200")
    elif http_status is not None:
        errors.append("http_status_supplied_without_response")

    canonical_by_oid: dict[int, bytes] = {}
    response_records: dict[int, dict[str, Any]] = {}
    if parsed_payload is not None:
        try:
            payload_errors, canonical_by_oid = validate_api_payload(
                parsed_payload, expected_objects=expected_objects
            )
            errors.extend(payload_errors)
        except (TypeError, ValueError, OverflowError, RecursionError):
            errors.append("api_payload_validation_failed_safely")
        records = parsed_payload.get("records")
        if isinstance(records, list):
            for record in records:
                if isinstance(record, dict):
                    oid = record.get("objectid")
                    if isinstance(oid, int) and not isinstance(oid, bool):
                        response_records.setdefault(oid, record)
        returned = _safe_response_oids(parsed_payload)
        missing = [oid for oid in FIXED_OIDS if oid not in returned]
        if request.get("returned_oids") != returned:
            errors.append("manifest_returned_oids_do_not_match_api")
        if request.get("missing_oids") != missing:
            errors.append("manifest_missing_oids_do_not_match_api")
        provenance = parsed_payload.get("provenance")
        if isinstance(provenance, dict) and manifest["source"].get(
            "retrieved_at_utc"
        ) != provenance.get("retrieved_at_utc"):
            errors.append("manifest_retrieval_time_does_not_match_api")

    object_oids: list[int] = []
    canonical_paths: set[str] = set()
    observed_digest_map: dict[str, str] = {}
    for item in objects if isinstance(objects, list) else []:
        if not isinstance(item, dict):
            errors.append("manifest_object_not_object")
            continue
        oid = item.get("objectid")
        if not isinstance(oid, int) or isinstance(oid, bool):
            errors.append("manifest_object_oid_invalid")
            continue
        object_oids.append(oid)
        record = response_records.get(oid)
        canonical = canonical_by_oid.get(oid)
        if record is None or canonical is None:
            errors.append(f"manifest_object_missing_from_api:{oid}")
            continue
        epochs = record.get("epochs")
        expected_count = len(epochs) if isinstance(epochs, list) else None
        expected_band = FILTER_BANDS.get(record.get("filterid"))
        if (
            item.get("filterid") != record.get("filterid")
            or item.get("band") != expected_band
        ):
            errors.append(f"manifest_object_filter_band_mismatch:{oid}")
        if (
            item.get("catalog_epoch_count") != record.get("catalog_nepochs")
            or item.get("counted_epoch_count") != expected_count
            or record.get("catalog_nepochs") != expected_count
        ):
            errors.append(f"manifest_object_epoch_count_mismatch:{oid}")
        expected_canonical_digest = sha256_bytes(canonical)
        if item.get("canonical_epoch_sha256") != expected_canonical_digest:
            errors.append(f"canonical_epoch_digest_mismatch:{oid}")
        relative = item.get("canonical_epoch_file")
        if (
            not isinstance(relative, str)
            or Path(relative).is_absolute()
            or ".." in Path(relative).parts
        ):
            errors.append(f"canonical_epoch_file_path_invalid:{oid}")
            continue
        canonical_paths.add(relative)
        target = root / relative
        if target.is_symlink() or not target.is_file():
            errors.append(f"canonical_epoch_file_missing:{oid}")
            continue
        actual_bytes = target.read_bytes()
        if actual_bytes != canonical:
            errors.append(f"canonical_epoch_content_mismatch:{oid}")
        actual_digest = sha256_bytes(actual_bytes)
        if actual_digest != item.get("canonical_epoch_file_sha256"):
            errors.append(f"canonical_epoch_file_sha256_mismatch:{oid}")
        observed_digest_map[str(oid)] = expected_canonical_digest
    if len(object_oids) != len(set(object_oids)):
        errors.append("manifest_object_oid_duplicate")
    if manifest_files.get("canonical_epoch_sha256") != observed_digest_map:
        errors.append("manifest_digest_map_inconsistent")
    actual_canonical_paths = {
        relative for relative in actual_files if relative.startswith("canonical/")
    }
    if actual_canonical_paths != canonical_paths:
        errors.append("canonical_epoch_file_inventory_mismatch")

    export_path = root / "workbench_export.json"
    export_digest = manifest_files.get("workbench_export_file_sha256")
    export_mode = manifest_files.get("workbench_export_capture_mode")
    if export_digest is None:
        if export_path.exists() or export_mode != "unavailable":
            errors.append("workbench_export_availability_mismatch")
    elif export_path.is_symlink() or not export_path.is_file():
        errors.append("workbench_export_file_missing")
    else:
        export_bytes = export_path.read_bytes()
        if sha256_bytes(export_bytes) != export_digest:
            errors.append("manifest_digest_mismatch:workbench_export.json")
        if parsed_payload is None:
            errors.append("workbench_export_without_safe_api_payload")
        else:
            errors.extend(_validate_workbench_export(export_bytes, parsed_payload))
            try:
                export_value = json.loads(export_bytes)
            except (UnicodeDecodeError, json.JSONDecodeError, RecursionError):
                export_value = None
            if export_mode == "derived_from_same_api_response_not_browser_download":
                if (
                    not isinstance(export_value, dict)
                    or export_value.get("derived_from_api_response_sha256")
                    != api_digest
                ):
                    errors.append("derived_export_provenance_mismatch")
            elif export_mode != "provided_actual_workbench_download":
                errors.append("workbench_export_capture_mode_invalid")

    if manifest.get("capture_status") == "PASS":
        if manifest.get("validation_errors"):
            errors.append("passing_manifest_contains_validation_errors")
        if errors:
            errors.append("passing_bundle_failed_independent_validation")
    return sorted(set(errors))


def _validate_legacy_bundle_payloads(
    root: Path, manifest: Mapping[str, Any]
) -> list[str]:
    """Retain checksum verification for Phase 2M v1 bundles."""
    errors: list[str] = []
    files = manifest.get("files", {})
    if not isinstance(files, Mapping):
        return ["legacy_manifest_files_invalid"]
    for key, relative in (
        ("api_response_file_sha256", "api_response.json"),
        ("workbench_export_file_sha256", "workbench_export.json"),
    ):
        target = root / relative
        digest = files.get(key)
        if digest is None:
            if target.exists():
                errors.append(f"unexpected_bundle_file:{relative}")
        elif (
            target.is_symlink()
            or not target.is_file()
            or sha256_bytes(target.read_bytes()) != digest
        ):
            errors.append(f"manifest_digest_mismatch:{relative}")
    objects = manifest.get("objects", [])
    if isinstance(objects, list):
        for item in objects:
            if not isinstance(item, Mapping):
                errors.append("legacy_manifest_object_invalid")
                continue
            relative = item.get("canonical_epoch_file")
            if (
                not isinstance(relative, str)
                or Path(relative).is_absolute()
                or ".." in Path(relative).parts
            ):
                errors.append("legacy_canonical_path_invalid")
                continue
            target = root / relative
            if target.is_symlink() or not target.is_file():
                errors.append("legacy_canonical_file_missing")
                continue
            digest = sha256_bytes(target.read_bytes())
            if digest != item.get("canonical_epoch_sha256") or digest != item.get(
                "canonical_epoch_file_sha256"
            ):
                errors.append("legacy_canonical_digest_mismatch")
    return errors


__all__ = [
    "API_PATH",
    "CATALOG_URI",
    "FIXED_OIDS",
    "MANIFEST_SCHEMA_VERSION",
    "PINNED_OBJECTS",
    "EvidenceBundleError",
    "check_dependency_compatibility",
    "redact_log_text",
    "redact_secrets",
    "sha256_bytes",
    "utc_now",
    "validate_api_payload",
    "validate_evidence_bundle",
    "validate_manifest_structure",
    "write_evidence_bundle",
]
