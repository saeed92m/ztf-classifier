"""Offline validation of the bounded DR24 evidence bundle contract."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import pytest

import ztf_classifier.validation.dr24_evidence as evidence_module
from ztf_classifier.io.dr24_lightcurve import canonical_epoch_json_bytes
from ztf_classifier.validation.dr24_evidence import (
    API_SCHEMA_VERSION,
    CATALOG_URI,
    FIXED_OIDS,
    PINNED_OBJECTS,
    SOURCE_NAME,
    check_dependency_compatibility,
    redact_log_text,
    sha256_bytes,
    validate_api_payload,
    validate_evidence_bundle,
    validate_manifest_structure,
    write_evidence_bundle,
)


@pytest.fixture(autouse=True)
def _clean_git_state(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        evidence_module,
        "collect_git_state",
        lambda _root: {
            "git_commit": "b" * 40,
            "git_branch": "test",
            "git_dirty": False,
        },
    )


def _dependency_kwargs() -> dict:
    repository = Path(__file__).parents[1]
    pin_map: dict[str, str] = {}
    for filename in ("requirements.lock", "requirements-dr24.lock"):
        for line in (repository / filename).read_text(encoding="utf-8").splitlines():
            entry = line.partition("#")[0].strip()
            if "==" not in entry:
                continue
            name, version = entry.split("==", 1)
            canonical_name = re.sub(r"[-_.]+", "-", name).lower()
            if canonical_name in pin_map:
                assert pin_map[canonical_name] == version
            pin_map[canonical_name] = version
    return {
        "dependency_lock_sha256": hashlib.sha256(
            (repository / "requirements.lock").read_bytes()
        ).hexdigest(),
        "dr24_dependency_lock_sha256": hashlib.sha256(
            (repository / "requirements-dr24.lock").read_bytes()
        ).hexdigest(),
        "resolved_dependencies": pin_map,
    }


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
        **_dependency_kwargs(),
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
    assert validate_evidence_bundle(root, expected_objects=expected) == []
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
        **_dependency_kwargs(),
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
        **_dependency_kwargs(),
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
        "missing_manifest_fields:capture_status,execution,files,limitations,objects,request,schema_version,source,validation_errors"
    ]


def test_detects_modified_bundle_file_and_manifest(tmp_path: Path) -> None:
    payload, expected = _fixture_payload()
    root, _ = write_evidence_bundle(
        tmp_path / "bundle",
        api_response_bytes=json.dumps(payload).encode(),
        api_status_code=200,
        software_commit_sha="b" * 40,
        python_version="3.11.9",
        **_dependency_kwargs(),
        execution_started_at_utc="2026-11-23T10:00:00Z",
        execution_completed_at_utc="2026-11-23T10:00:01Z",
        test_command="offline fixture",
        expected_objects=expected,
    )
    with (root / "api_response.json").open("ab") as stream:
        stream.write(b" ")
    assert (
        "bundle_file_checksum_mismatch:api_response.json"
        in validate_evidence_bundle(root, expected_objects=expected)
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
            **_dependency_kwargs(),
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


@pytest.mark.parametrize(
    "epoch_value, expected_error",
    [
        ("missing", "missing_record_fields:epochs"),
        (None, f"epochs_not_array:{FIXED_OIDS[0]}"),
        (7, f"epochs_not_array:{FIXED_OIDS[0]}"),
        ("epochs", f"epochs_not_array:{FIXED_OIDS[0]}"),
        ({"unexpected": []}, f"epochs_not_array:{FIXED_OIDS[0]}"),
        ([], f"catalog_epoch_count_mismatch:{FIXED_OIDS[0]}"),
        ([None], f"epoch_schema_mismatch:{FIXED_OIDS[0]}"),
    ],
)
def test_malformed_epoch_containers_fail_without_raising(
    epoch_value: object, expected_error: str
) -> None:
    payload, expected = _fixture_payload()
    if epoch_value == "missing":
        del payload["records"][0]["epochs"]
    else:
        payload["records"][0]["epochs"] = epoch_value
    errors, _ = validate_api_payload(payload, expected_objects=expected)
    assert any(expected_error in error for error in errors)


def test_nullable_color_coefficient_is_preserved_as_valid_source_data() -> None:
    payload, expected = _fixture_payload()
    payload["records"][0]["epochs"][0]["clrcoeff"] = None
    for record in payload["records"]:
        digest = sha256_bytes(canonical_epoch_json_bytes(record["epochs"]))
        record["payload_sha256"] = digest
        expected[record["objectid"]]["canonical_epoch_sha256"] = digest
        payload["provenance"]["payload_sha256"][str(record["objectid"])] = digest
    errors, _ = validate_api_payload(payload, expected_objects=expected)
    assert errors == []


def test_dependency_compatibility_matches_both_locks_and_project_constraints() -> None:
    versions = _dependency_kwargs()["resolved_dependencies"]
    errors, normalized = check_dependency_compatibility(versions)
    assert errors == []
    assert normalized["pandas"] == "2.3.3"
    assert normalized["nested-pandas"] == "0.6.10"
    assert normalized["jsonschema"] == "4.26.0"

    mismatched = dict(versions)
    mismatched["pandas"] = "3.0.6"
    errors, _ = check_dependency_compatibility(mismatched)
    assert "runtime_lock_version_mismatch:pandas" in errors
    assert "runtime_violates_project_constraint:pandas" in errors
    assert "nested_pandas_runtime_constraint_mismatch" in errors


def test_manifest_schema_is_authoritative_versioned_and_fail_closed(
    tmp_path: Path,
) -> None:
    payload, expected = _fixture_payload()
    root, errors = write_evidence_bundle(
        tmp_path / "bundle",
        api_response_bytes=json.dumps(payload).encode(),
        api_status_code=200,
        software_commit_sha="b" * 40,
        python_version="3.11.9",
        **_dependency_kwargs(),
        execution_started_at_utc="2026-11-23T10:00:00Z",
        execution_completed_at_utc="2026-11-23T10:00:01Z",
        test_command="offline schema test",
        expected_objects=expected,
    )
    assert errors == []
    manifest = json.loads((root / "manifest.json").read_bytes())
    assert manifest["schema_version"] == "ztf-dr24-evidence-manifest-v2"
    assert validate_manifest_structure(manifest) == []

    invalid_revision = json.loads(json.dumps(manifest))
    invalid_revision["execution"]["software_commit_sha"] = "not-a-commit"
    assert any(
        error.startswith("manifest_json_schema_validation_failed")
        for error in validate_manifest_structure(invalid_revision)
    )

    unsupported = json.loads(json.dumps(manifest))
    unsupported["schema_version"] = "ztf-dr24-evidence-manifest-v99"
    assert validate_manifest_structure(unsupported) == [
        "manifest_schema_version_unsupported"
    ]

    inconsistent = json.loads(json.dumps(manifest))
    inconsistent["execution"]["test_result"] = "FAIL"
    assert (
        "manifest_json_schema_validation_failed:const"
        in validate_manifest_structure(inconsistent)
    )

    legacy = json.loads(json.dumps(manifest))
    legacy["schema_version"] = "ztf-dr24-evidence-manifest-v1"
    assert validate_manifest_structure(legacy) == []


def test_bundle_validator_detects_manifest_checksum_and_digest_map_tampering(
    tmp_path: Path,
) -> None:
    payload, expected = _fixture_payload()
    root, errors = write_evidence_bundle(
        tmp_path / "bundle",
        api_response_bytes=json.dumps(payload).encode(),
        api_status_code=200,
        software_commit_sha="b" * 40,
        python_version="3.11.9",
        **_dependency_kwargs(),
        execution_started_at_utc="2026-11-23T10:00:00Z",
        execution_completed_at_utc="2026-11-23T10:00:01Z",
        test_command="offline integrity test",
        expected_objects=expected,
    )
    assert errors == []

    manifest = json.loads((root / "manifest.json").read_bytes())
    manifest["files"]["canonical_epoch_sha256"][str(FIXED_OIDS[0])] = "0" * 64
    (root / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    errors = validate_evidence_bundle(root, expected_objects=expected)
    assert "manifest_file_sha256_mismatch" in errors
    assert "manifest_digest_map_inconsistent" in errors


def test_bundle_validator_reconstructs_api_and_export_provenance(
    tmp_path: Path,
) -> None:
    payload, expected = _fixture_payload()
    root, errors = write_evidence_bundle(
        tmp_path / "bundle",
        api_response_bytes=json.dumps(payload).encode(),
        api_status_code=200,
        software_commit_sha="b" * 40,
        python_version="3.11.9",
        **_dependency_kwargs(),
        execution_started_at_utc="2026-11-23T10:00:00Z",
        execution_completed_at_utc="2026-11-23T10:00:01Z",
        test_command="offline provenance test",
        expected_objects=expected,
    )
    assert errors == []

    export = json.loads((root / "workbench_export.json").read_bytes())
    export["source_payload"]["records"][0]["objectid"] = FIXED_OIDS[1]
    export["derived_from_api_response_sha256"] = "0" * 64
    (root / "workbench_export.json").write_text(json.dumps(export), encoding="utf-8")
    errors = validate_evidence_bundle(root, expected_objects=expected)
    assert "manifest_digest_mismatch:workbench_export.json" in errors
    assert "workbench_export_payload_mismatch" in errors
    assert "derived_export_provenance_mismatch" in errors


def test_bundle_validator_checks_oid_association_and_independent_epoch_count(
    tmp_path: Path,
) -> None:
    payload, expected = _fixture_payload()
    root, errors = write_evidence_bundle(
        tmp_path / "oid-bundle",
        api_response_bytes=json.dumps(payload).encode(),
        api_status_code=200,
        software_commit_sha="b" * 40,
        python_version="3.11.9",
        **_dependency_kwargs(),
        execution_started_at_utc="2026-11-23T10:00:00Z",
        execution_completed_at_utc="2026-11-23T10:00:01Z",
        test_command="offline OID test",
        expected_objects=expected,
    )
    assert errors == []
    source = json.loads((root / "api_response.json").read_bytes())
    source["records"][0]["objectid"] = FIXED_OIDS[1]
    (root / "api_response.json").write_text(json.dumps(source), encoding="utf-8")
    errors = validate_evidence_bundle(root, expected_objects=expected)
    assert any(error.startswith("duplicate_oid:") for error in errors)
    assert any(error.startswith("filter_band_mismatch:") for error in errors)

    count_root, count_errors = write_evidence_bundle(
        tmp_path / "count-bundle",
        api_response_bytes=json.dumps(payload).encode(),
        api_status_code=200,
        software_commit_sha="b" * 40,
        python_version="3.11.9",
        **_dependency_kwargs(),
        execution_started_at_utc="2026-11-23T10:00:00Z",
        execution_completed_at_utc="2026-11-23T10:00:01Z",
        test_command="offline epoch test",
        expected_objects=expected,
    )
    assert count_errors == []
    count_manifest = json.loads((count_root / "manifest.json").read_bytes())
    count_manifest["objects"][0]["catalog_epoch_count"] += 1
    (count_root / "manifest.json").write_text(
        json.dumps(count_manifest), encoding="utf-8"
    )
    count_errors = validate_evidence_bundle(count_root, expected_objects=expected)
    assert "manifest_file_sha256_mismatch" in count_errors
    assert any(
        error.startswith("manifest_object_epoch_count_mismatch:")
        for error in count_errors
    )


def test_bundle_validator_detects_canonical_file_modification(tmp_path: Path) -> None:
    payload, expected = _fixture_payload()
    root, errors = write_evidence_bundle(
        tmp_path / "bundle",
        api_response_bytes=json.dumps(payload).encode(),
        api_status_code=200,
        software_commit_sha="b" * 40,
        python_version="3.11.9",
        **_dependency_kwargs(),
        execution_started_at_utc="2026-11-23T10:00:00Z",
        execution_completed_at_utc="2026-11-23T10:00:01Z",
        test_command="offline canonical file test",
        expected_objects=expected,
    )
    assert errors == []
    canonical_file = root / f"canonical/oid_{FIXED_OIDS[0]}_epochs.json"
    canonical_file.write_bytes(canonical_file.read_bytes() + b" ")
    errors = validate_evidence_bundle(root, expected_objects=expected)
    assert f"canonical_epoch_content_mismatch:{FIXED_OIDS[0]}" in errors
    assert (
        f"bundle_file_checksum_mismatch:canonical/oid_{FIXED_OIDS[0]}_epochs.json"
        in errors
    )


@pytest.mark.parametrize(
    "response_bytes, status_code, transport_status, error_type, parse_status",
    [
        (b"", 200, "RESPONSE_RECEIVED", None, "EMPTY"),
        (b"{invalid", 200, "RESPONSE_RECEIVED", None, "INVALID"),
        (b'{"error":"source unavailable"}', 503, "RESPONSE_RECEIVED", None, "VALID"),
        (b"", None, "TIMEOUT", "ReadTimeout", "NOT_AVAILABLE"),
    ],
)
def test_failure_capture_records_transport_and_parse_states(
    tmp_path: Path,
    response_bytes: bytes,
    status_code: int | None,
    transport_status: str,
    error_type: str | None,
    parse_status: str,
) -> None:
    root, errors = write_evidence_bundle(
        tmp_path / "bundle",
        api_response_bytes=response_bytes,
        api_status_code=status_code,
        software_commit_sha="b" * 40,
        python_version="3.11.9",
        **_dependency_kwargs(),
        execution_started_at_utc="2026-11-23T10:00:00Z",
        execution_completed_at_utc="2026-11-23T10:00:01Z",
        test_command="offline transport test",
        transport_status=transport_status,
        transport_error_type=error_type,
    )
    manifest = json.loads((root / "manifest.json").read_bytes())
    assert manifest["capture_status"] == "FAIL"
    assert manifest["request"]["http_status_code"] == status_code
    assert manifest["request"]["transport_status"] == transport_status
    assert manifest["request"]["response_parse_status"] == parse_status
    assert manifest["request"]["transport_error_type"] == error_type
    assert manifest["execution"]["test_result"] == "FAIL"
    assert errors


def test_log_redaction_covers_headers_cookies_urls_tokens_and_environment_values() -> (
    None
):
    secrets = [
        "Bearer bearer-secret",
        "Authorization: Basic header-secret",
        "Cookie: session=cookie-secret",
        "https://user:url-secret@example.test/path?access_token=url-secret",
        "API_TOKEN=environment-secret",
        "token=message-secret",
    ]
    redacted = redact_log_text("\n".join(secrets))
    for secret in (
        "bearer-secret",
        "header-secret",
        "cookie-secret",
        "url-secret",
        "environment-secret",
        "message-secret",
    ):
        assert secret not in redacted
    assert "[REDACTED]" in redacted


def test_workflow_keeps_setup_failure_and_capture_failure_visible() -> None:
    workflow = (
        Path(__file__).parents[1] / ".github/workflows/dr24-evidence-capture.yml"
    ).read_text(encoding="utf-8")
    assert "workflow_dispatch:" in workflow
    assert "push:" not in workflow
    assert "if: ${{ always() && steps.install.outcome == 'failure' }}" in workflow
    assert "retention-days: 30" in workflow
    assert 'exit "$capture_status"' in workflow
    assert "$RUNNER_TEMP/dr24-evidence-runner-" in workflow
    assert "runner.log" in workflow
    assert ".raw.log" not in workflow.split("path: artifacts/dr24-evidence/", 1)[-1]



def test_writer_fails_closed_when_git_worktree_is_dirty(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload, expected = _fixture_payload()
    monkeypatch.setattr(
        evidence_module,
        "collect_git_state",
        lambda _root: {
            "git_commit": "b" * 40,
            "git_branch": "test",
            "git_dirty": True,
        },
    )
    root, errors = write_evidence_bundle(
        tmp_path / "dirty-bundle",
        api_response_bytes=json.dumps(payload).encode(),
        api_status_code=200,
        software_commit_sha="b" * 40,
        python_version="3.11.9",
        **_dependency_kwargs(),
        execution_started_at_utc="2026-11-23T10:00:00Z",
        execution_completed_at_utc="2026-11-23T10:00:01Z",
        test_command="dirty git provenance test",
        expected_objects=expected,
    )
    manifest = json.loads((root / "manifest.json").read_bytes())
    assert manifest["capture_status"] == "FAIL"
    assert manifest["execution"]["git_worktree_dirty"] is True
    assert manifest["execution"]["git_commit_match"] is True
    assert "git_worktree_dirty" in errors


def test_writer_fails_closed_when_supplied_commit_differs_from_head(
    tmp_path: Path,
) -> None:
    payload, expected = _fixture_payload()
    root, errors = write_evidence_bundle(
        tmp_path / "mismatch-bundle",
        api_response_bytes=json.dumps(payload).encode(),
        api_status_code=200,
        software_commit_sha="c" * 40,
        python_version="3.11.9",
        **_dependency_kwargs(),
        execution_started_at_utc="2026-11-23T10:00:00Z",
        execution_completed_at_utc="2026-11-23T10:00:01Z",
        test_command="git commit mismatch test",
        expected_objects=expected,
    )
    manifest = json.loads((root / "manifest.json").read_bytes())
    assert manifest["capture_status"] == "FAIL"
    assert manifest["execution"]["git_head_sha"] == "b" * 40
    assert manifest["execution"]["git_commit_match"] is False
    assert "software_commit_sha_head_mismatch" in errors


def test_writer_fails_closed_when_git_state_is_unavailable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload, expected = _fixture_payload()

    def unavailable(_root: Path) -> dict:
        raise RuntimeError("git unavailable")

    monkeypatch.setattr(evidence_module, "collect_git_state", unavailable)
    root, errors = write_evidence_bundle(
        tmp_path / "unavailable-git-bundle",
        api_response_bytes=json.dumps(payload).encode(),
        api_status_code=200,
        software_commit_sha="b" * 40,
        python_version="3.11.9",
        **_dependency_kwargs(),
        execution_started_at_utc="2026-11-23T10:00:00Z",
        execution_completed_at_utc="2026-11-23T10:00:01Z",
        test_command="git unavailable test",
        expected_objects=expected,
    )
    manifest = json.loads((root / "manifest.json").read_bytes())
    assert manifest["capture_status"] == "FAIL"
    assert manifest["execution"]["git_head_sha"] is None
    assert manifest["execution"]["git_worktree_dirty"] is None
    assert manifest["execution"]["git_commit_match"] is None
    assert "git_state_unavailable" in errors


def test_manifest_validator_detects_inconsistent_git_commit_attestation() -> None:
    payload, expected = _fixture_payload()
    # Reuse the normal writer fixture to obtain a schema-valid PASS manifest.
    import tempfile

    with tempfile.TemporaryDirectory() as temporary_directory:
        root, errors = write_evidence_bundle(
            Path(temporary_directory) / "bundle",
            api_response_bytes=json.dumps(payload).encode(),
            api_status_code=200,
            software_commit_sha="b" * 40,
            python_version="3.11.9",
            **_dependency_kwargs(),
            execution_started_at_utc="2026-11-23T10:00:00Z",
            execution_completed_at_utc="2026-11-23T10:00:01Z",
            test_command="git attestation consistency test",
            expected_objects=expected,
        )
        assert errors == []
        manifest = json.loads((root / "manifest.json").read_bytes())

    manifest["execution"]["software_commit_sha"] = "c" * 40
    manifest["execution"]["git_commit_match"] = True
    validation_errors = validate_manifest_structure(manifest)
    assert "manifest_git_commit_match_inconsistent" in validation_errors

def test_manifest_oid_order_is_canonical_when_api_records_are_reversed(
    tmp_path: Path,
) -> None:
    payload, expected = _fixture_payload()
    payload["records"] = list(reversed(payload["records"]))
    raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode()

    root, errors = write_evidence_bundle(
        tmp_path / "reversed-api-order",
        api_response_bytes=raw,
        api_status_code=200,
        software_commit_sha="b" * 40,
        python_version="3.11.9",
        **_dependency_kwargs(),
        execution_started_at_utc="2026-11-23T10:00:00Z",
        execution_completed_at_utc="2026-11-23T10:00:01Z",
        test_command="reversed API record order regression",
        expected_objects=expected,
    )

    assert errors == []
    manifest = json.loads((root / "manifest.json").read_bytes())
    assert manifest["capture_status"] == "PASS"
    assert manifest["request"]["returned_oids"] == list(FIXED_OIDS)
    assert (root / "api_response.json").read_bytes() == raw
    assert validate_evidence_bundle(root, expected_objects=expected) == []
