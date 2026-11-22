"""Offline validation of the bounded DR24 evidence bundle contract."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from ztf_classifier.io.dr24_lightcurve import canonical_epoch_json_bytes
from ztf_classifier.validation.dr24_evidence import (
    API_SCHEMA_VERSION,
    CATALOG_URI,
    FIXED_OIDS,
    PINNED_OBJECTS,
    SOURCE_NAME,
    sha256_bytes,
    validate_api_payload,
    validate_evidence_bundle,
    validate_manifest_structure,
    write_evidence_bundle,
)


def _fixture_payload() -> tuple[dict, dict[int, dict]]:
    records = []
    expected: dict[int, dict] = {}
    epochs_by_oid = {
        FIXED_OIDS[0]: [
            {
                "hmjd": 59400.0,
                "mag": 18.1,
                "magerr": 0.1,
                "clrcoeff": 0.0,
                "catflags": 0,
            },
            {
                "hmjd": 59401.0,
                "mag": 18.2,
                "magerr": 0.1,
                "clrcoeff": 0.0,
                "catflags": 0,
            },
        ],
        FIXED_OIDS[1]: [
            {
                "hmjd": 59402.0,
                "mag": 19.1,
                "magerr": 0.2,
                "clrcoeff": 0.0,
                "catflags": 0,
            }
        ],
    }
    filters = {FIXED_OIDS[0]: 1, FIXED_OIDS[1]: 2}
    for oid in FIXED_OIDS:
        epochs = epochs_by_oid[oid]
        digest = sha256_bytes(canonical_epoch_json_bytes(epochs))
        expected[oid] = {
            "filterid": filters[oid],
            "band": "g" if filters[oid] == 1 else "r",
            "epoch_count": len(epochs),
            "canonical_epoch_sha256": digest,
        }
        records.append(
            {
                "objectid": oid,
                "filterid": filters[oid],
                "fieldid": 100,
                "rcid": 3,
                "objra": 10.0,
                "objdec": 20.0,
                "catalog_nepochs": len(epochs),
                "epochs": epochs,
                "payload_sha256": digest,
            }
        )
    all_oids = list(FIXED_OIDS)
    payload = {
        "schema_version": API_SCHEMA_VERSION,
        "records": records,
        "provenance": {
            "source": SOURCE_NAME,
            "release": "DR24",
            "catalog_uri": CATALOG_URI,
            "retrieved_at_utc": "2026-11-23T10:00:00Z",
            "query": {"index": "objectid", "objectids": all_oids},
            "requested_oids": all_oids,
            "returned_oids": all_oids,
            "missing_oids": [],
            "schema_columns": ["objectid", "filterid", "lightcurve"],
            "schema_columns_sha256": hashlib.sha256(
                json.dumps(
                    ["objectid", "filterid", "lightcurve"],
                    separators=(",", ":"),
                    ensure_ascii=True,
                ).encode()
            ).hexdigest(),
            "epoch_count": sum(len(record["epochs"]) for record in records),
            "payload_sha256": {
                str(record["objectid"]): record["payload_sha256"] for record in records
            },
            "interpretation": "native decoded epoch data",
            "limitations": [],
        },
        "qc_assessments": [
            {
                "objectid": oid,
                "schema_version": "ztf-dr24-qc-assessment-v1",
                "policy_id": "ztf-dr24-raw-qc-diagnostic-v1",
                "policy_status": "DIAGNOSTIC_NOT_PRODUCTION_APPROVED",
                "raw_data_mutated": False,
                "epochs": [],
                "counts": {},
                "interpretation": {},
                "source_documents": [],
            }
            for oid in all_oids
        ],
    }
    return payload, expected


def test_fixed_oids_and_independently_counted_epochs_pass() -> None:
    payload, expected = _fixture_payload()
    errors, canonical = validate_api_payload(payload, expected_objects=expected)
    assert errors == []
    assert set(canonical) == set(FIXED_OIDS)
    assert [len(item["epochs"]) for item in payload["records"]] == [2, 1]


def test_production_pin_contract_matches_recorded_e2e_identity() -> None:
    assert PINNED_OBJECTS[FIXED_OIDS[0]] == {
        "filterid": 1,
        "band": "g",
        "epoch_count": 78,
        "canonical_epoch_sha256": "735ee15135670a1a28b03b76edfb394e9c0c193d528f3da56ebb593468baf2a0",
    }
    assert PINNED_OBJECTS[FIXED_OIDS[1]] == {
        "filterid": 2,
        "band": "r",
        "epoch_count": 123,
        "canonical_epoch_sha256": "a37f6fa2ee91009805b6fab3a5563b793cba9e84f6a82ec333bae507442c70ae",
    }


@pytest.mark.parametrize(
    "mutation, expected_error",
    [
        ("missing", "fixed_oid_set_mismatch"),
        ("empty", "fixed_oid_set_mismatch"),
        ("malformed", "api_payload_not_object"),
        ("filter", f"filter_band_mismatch:{FIXED_OIDS[0]}"),
        ("count", f"catalog_epoch_count_mismatch:{FIXED_OIDS[0]}"),
        ("schema_digest", "schema_columns_digest_mismatch"),
        ("provenance", "missing_provenance_fields:"),
    ],
)
def test_fail_closed_response_validation(mutation: str, expected_error: str) -> None:
    payload, expected = _fixture_payload()
    if mutation == "missing":
        payload["records"].pop()
        payload["provenance"]["returned_oids"].pop()
    elif mutation == "empty":
        payload["records"] = []
        payload["provenance"]["returned_oids"] = []
        payload["provenance"]["epoch_count"] = 0
    elif mutation == "malformed":
        payload = "not-json-object"
    elif mutation == "filter":
        payload["records"][0]["filterid"] = 2
    elif mutation == "count":
        payload["records"][0]["catalog_nepochs"] += 1
    elif mutation == "schema_digest":
        payload["provenance"]["schema_columns_sha256"] = "0" * 64
    elif mutation == "provenance":
        del payload["provenance"]["catalog_uri"]
    errors, _ = validate_api_payload(payload, expected_objects=expected)
    assert any(expected_error in error for error in errors)


def test_canonical_digest_and_exact_file_byte_digests(tmp_path: Path) -> None:
    payload, expected = _fixture_payload()
    raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode()
    root, errors = write_evidence_bundle(
        tmp_path / "bundle",
        api_response_bytes=raw,
        api_status_code=200,
        software_commit_sha="b" * 40,
        python_version="3.11.9",
        dependency_lock_sha256="c" * 64,
        dr24_dependency_lock_sha256="d" * 64,
        execution_started_at_utc="2026-11-23T10:00:00Z",
        execution_completed_at_utc="2026-11-23T10:00:01Z",
        test_command="offline fixture",
        expected_objects=expected,
    )
    assert errors == []
    assert hashlib.sha256(
        (root / "api_response.json").read_bytes()
    ).hexdigest() == sha256_bytes(raw)
    manifest = json.loads((root / "manifest.json").read_bytes())
    checksums = json.loads((root / "checksums.json").read_bytes())
    assert checksums["manifest_file_sha256"] == sha256_bytes(
        (root / "manifest.json").read_bytes()
    )
    assert manifest["files"]["api_response_file_sha256"] == sha256_bytes(raw)
    assert (
        manifest["files"]["workbench_export_capture_mode"]
        == "derived_from_same_api_response_not_browser_download"
    )
    assert manifest["source"]["original_source_file_sha256"] is None
    export = json.loads((root / "workbench_export.json").read_bytes())
    assert export["source_payload"] == payload
    assert validate_evidence_bundle(root) == []
    assert validate_manifest_structure(manifest) == []


def test_rejects_workbench_export_from_a_different_response(tmp_path: Path) -> None:
    payload, expected = _fixture_payload()
    altered = dict(payload)
    altered["records"] = []
    export = {
        "export_schema_version": "ztf-dr24-raw-export-v0.2",
        "exported_at_utc": "2026-11-23T10:00:01Z",
        "source_payload": altered,
    }
    _, errors = write_evidence_bundle(
        tmp_path / "bundle",
        api_response_bytes=json.dumps(payload).encode(),
        api_status_code=200,
        software_commit_sha="b" * 40,
        python_version="3.11.9",
        dependency_lock_sha256="c" * 64,
        dr24_dependency_lock_sha256="d" * 64,
        execution_started_at_utc="2026-11-23T10:00:00Z",
        execution_completed_at_utc="2026-11-23T10:00:01Z",
        test_command="offline fixture",
        workbench_export_bytes=json.dumps(export).encode(),
        expected_objects=expected,
    )
    assert "workbench_export_payload_mismatch" in errors


def test_malformed_api_bytes_produce_fail_manifest_without_fake_payload(
    tmp_path: Path,
) -> None:
    root, errors = write_evidence_bundle(
        tmp_path / "bundle",
        api_response_bytes=b"not-json",
        api_status_code=502,
        software_commit_sha="b" * 40,
        python_version="3.11.9",
        dependency_lock_sha256="c" * 64,
        dr24_dependency_lock_sha256="d" * 64,
        execution_started_at_utc="2026-11-23T10:00:00Z",
        execution_completed_at_utc="2026-11-23T10:00:01Z",
        test_command="offline fixture",
    )
    manifest = json.loads((root / "manifest.json").read_bytes())
    assert manifest["capture_status"] == "FAIL"
    assert not (root / "api_response.json").exists()
    assert manifest["files"]["api_response_file_sha256"] is None
    assert "api_response_invalid_json" in errors


def test_manifest_structure_rejects_missing_required_fields() -> None:
    assert validate_manifest_structure({}) == [
        "missing_manifest_fields:capture_status,execution,files,limitations,objects,request,schema_version,source"
    ]


def test_detects_modified_bundle_file_and_manifest(tmp_path: Path) -> None:
    payload, expected = _fixture_payload()
    root, _ = write_evidence_bundle(
        tmp_path / "bundle",
        api_response_bytes=json.dumps(payload).encode(),
        api_status_code=200,
        software_commit_sha="b" * 40,
        python_version="3.11.9",
        dependency_lock_sha256="c" * 64,
        dr24_dependency_lock_sha256="d" * 64,
        execution_started_at_utc="2026-11-23T10:00:00Z",
        execution_completed_at_utc="2026-11-23T10:00:01Z",
        test_command="offline fixture",
        expected_objects=expected,
    )
    with (root / "api_response.json").open("ab") as stream:
        stream.write(b" ")
    assert (
        "bundle_file_checksum_mismatch:api_response.json"
        in validate_evidence_bundle(root)
    )


def test_rejects_secret_fields_and_redacts_them() -> None:
    payload, expected = _fixture_payload()
    payload["Authorization"] = "Bearer test-secret-token"
    errors, _ = validate_api_payload(payload, expected_objects=expected)
    assert errors == ["api_payload_contains_sensitive_fields"]
    from ztf_classifier.validation.dr24_evidence import redact_secrets

    redacted = redact_secrets(
        {"access_token": "not-for-output", "message": "Bearer abc.def"}
    )
    assert redacted["access_token"] == "[REDACTED]"
    assert "abc.def" not in redacted["message"]


def test_reproducible_bundle_structure_with_fixed_execution_metadata(
    tmp_path: Path,
) -> None:
    payload, expected = _fixture_payload()
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    for name in ("a", "b"):
        write_evidence_bundle(
            tmp_path / name,
            api_response_bytes=raw,
            api_status_code=200,
            software_commit_sha="b" * 40,
            python_version="3.11.9",
            dependency_lock_sha256="c" * 64,
            dr24_dependency_lock_sha256="d" * 64,
            execution_started_at_utc="2026-11-23T10:00:00Z",
            execution_completed_at_utc="2026-11-23T10:00:01Z",
            test_command="offline fixture",
            expected_objects=expected,
        )
    first = {
        p.relative_to(tmp_path / "a").as_posix(): p.read_bytes()
        for p in (tmp_path / "a").rglob("*")
        if p.is_file()
    }
    second = {
        p.relative_to(tmp_path / "b").as_posix(): p.read_bytes()
        for p in (tmp_path / "b").rglob("*")
        if p.is_file()
    }
    assert first == second
