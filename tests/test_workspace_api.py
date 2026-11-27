import json
from pathlib import Path

from fastapi.testclient import TestClient

from ztf_classifier.api.app import create_app
from ztf_classifier.api.config import ApiSettings


def _client(tmp_path: Path) -> TestClient:
    settings = ApiSettings(
        observation_cache_dir=tmp_path / "cache",
        job_store_path=tmp_path / "jobs.sqlite3",
        result_store_path=tmp_path / "results.sqlite3",
        application_state_path=tmp_path / "settings" / "settings.json",
        scientific_registry_dir=tmp_path / "benchmarks",
        scientific_evidence_dir=tmp_path / "evidence",
    )
    return TestClient(create_app(settings=settings))


def test_workspace_lifecycle_is_persistent_and_api_backed(tmp_path: Path) -> None:
    client = _client(tmp_path)

    initial = client.get("/v1/workspaces")
    assert initial.status_code == 200
    assert initial.json() == {"items": [], "active_workspace_id": None}
    assert client.get("/v1/workspaces/active").json() == {"workspace": None}

    created = client.post("/v1/workspaces", json={"name": "DR24 Research"})
    assert created.status_code == 200
    workspace = created.json()
    workspace_id = workspace["workspace_id"]
    assert workspace["name"] == "DR24 Research"
    assert workspace["is_active"] is True
    assert Path(workspace["directory"]).is_dir()

    active = client.get("/v1/workspaces/active")
    assert active.status_code == 200
    assert active.json()["workspace"]["workspace_id"] == workspace_id

    duplicate = client.post("/v1/workspaces", json={"name": "dr24 research"})
    assert duplicate.status_code == 409
    assert duplicate.json()["code"] == "workspace_name_conflict"

    another = client.post("/v1/workspaces", json={"name": "Second project"})
    assert another.status_code == 200
    assert another.json()["workspace_id"] != workspace_id

    reopened = client.post(f"/v1/workspaces/{workspace_id}/open")
    assert reopened.status_code == 200
    assert reopened.json()["workspace_id"] == workspace_id
    assert reopened.json()["is_active"] is True

    listing = client.get("/v1/workspaces").json()
    assert listing["active_workspace_id"] == workspace_id
    assert len(listing["items"]) == 2


def test_workspace_api_rejects_invalid_names_and_unknown_ids(tmp_path: Path) -> None:
    client = _client(tmp_path)

    invalid = client.post("/v1/workspaces", json={"name": "../outside"})
    assert invalid.status_code == 422
    assert invalid.json()["code"] == "workspace_name_invalid"

    missing = client.post(f"/v1/workspaces/{'0' * 32}/open")
    assert missing.status_code == 404
    assert missing.json()["code"] == "workspace_not_found"


def test_workspace_operation_and_export_are_persisted_with_hashes(
    tmp_path: Path,
) -> None:
    client = _client(tmp_path)
    created = client.post("/v1/workspaces", json={"name": "Park demo"})
    assert created.status_code == 200

    operation_id = "a" * 32
    running = client.post(
        "/v1/workspaces/operations",
        json={
            "operation_id": operation_id,
            "operation_type": "DR24_BATCH_QUERY",
            "source": "ztf_dr24_hats",
            "status": "RUNNING",
            "requested_oids": [123456],
        },
    )
    assert running.status_code == 200
    assert running.json()["status"] == "RUNNING"

    completed = client.post(
        "/v1/workspaces/operations",
        json={
            "operation_id": operation_id,
            "operation_type": "DR24_BATCH_QUERY",
            "source": "ztf_dr24_hats",
            "status": "SUCCEEDED",
            "requested_oids": [123456],
            "returned_oids": [123456],
            "missing_oids": [],
            "payload_sha256_by_oid": {"123456": "a" * 64},
        },
    )
    assert completed.status_code == 200
    assert completed.json()["status"] == "SUCCEEDED"

    export_payload = {
        "export_schema_version": "ztf-dr24-raw-export-v0.3",
        "source_payload": {
            "provenance": {
                "requested_oids": [123456],
                "returned_oids": [123456],
            }
        },
    }
    saved = client.post("/v1/workspaces/exports", json=export_payload)
    assert saved.status_code == 200
    metadata = saved.json()
    assert metadata["file_name"].startswith("dr24-raw-export-")
    assert len(metadata["sha256"]) == 64
    assert metadata["size_bytes"] > 0

    restored_export = client.get(
        "/v1/workspaces/exports/" + metadata["file_name"]
    )
    assert restored_export.status_code == 200
    assert restored_export.json() == export_payload

    unrelated_name = "dr24-raw-export-20260101T000000Z-ffffffff.json"
    unrelated_path = Path(metadata["path"]).parent / unrelated_name
    unrelated_path.write_text("{}\\n", encoding="utf-8")
    assert unrelated_path.is_file()
    unrelated_export = client.get("/v1/workspaces/exports/" + unrelated_name)
    assert unrelated_export.status_code == 404

    invalid_name = client.get("/v1/workspaces/exports/../workspace.json")
    assert invalid_name.status_code in {404, 422}

    restarted_client = _client(tmp_path)
    active_after_restart = restarted_client.get("/v1/workspaces/active").json()[
        "workspace"
    ]
    assert active_after_restart["last_operation"]["status"] == "SUCCEEDED"
    assert active_after_restart["last_export"]["sha256"] == metadata["sha256"]

    active = client.get("/v1/workspaces/active").json()["workspace"]
    assert active["last_operation"]["status"] == "SUCCEEDED"
    assert active["last_operation"]["export_file"] == metadata["file_name"]
    assert active["last_export"]["sha256"] == metadata["sha256"]
    assert Path(metadata["path"]).is_file()


def test_workspace_operation_requires_active_workspace(tmp_path: Path) -> None:
    response = _client(tmp_path).post(
        "/v1/workspaces/operations",
        json={
            "operation_id": "b" * 32,
            "operation_type": "DR24_BATCH_QUERY",
            "source": "ztf_dr24_hats",
            "status": "RUNNING",
            "requested_oids": [123456],
        },
    )
    assert response.status_code == 409
    assert response.json()["code"] == "workspace_not_found"


def test_workspace_operation_completion_uses_stored_requested_oids(
    tmp_path: Path,
) -> None:
    client = _client(tmp_path)
    created = client.post("/v1/workspaces", json={"name": "OID accounting"})
    assert created.status_code == 200

    operation_id = "c" * 32
    running_payload = {
        "operation_id": operation_id,
        "operation_type": "DR24_BATCH_QUERY",
        "source": "ztf_dr24_hats",
        "status": "RUNNING",
        "requested_oids": [123456, 234567],
    }
    running = client.post("/v1/workspaces/operations", json=running_payload)
    assert running.status_code == 200

    tampered_completion = {
        **running_payload,
        "status": "SUCCEEDED",
        "requested_oids": [123456],
        "returned_oids": [123456],
        "missing_oids": [],
        "payload_sha256_by_oid": {"123456": "a" * 64},
    }
    rejected = client.post(
        "/v1/workspaces/operations", json=tampered_completion
    )
    assert rejected.status_code == 422

    active = client.get("/v1/workspaces/active").json()["workspace"]
    assert active["last_operation"]["status"] == "RUNNING"
    assert active["last_operation"]["requested_oids"] == [123456, 234567]

    valid_completion = {
        **running_payload,
        "status": "SUCCEEDED",
        "returned_oids": [123456],
        "missing_oids": [234567],
        "payload_sha256_by_oid": {"123456": "a" * 64},
    }
    valid_completion.pop("requested_oids")
    completed = client.post(
        "/v1/workspaces/operations", json=valid_completion
    )
    assert completed.status_code == 200
    assert completed.json()["status"] == "SUCCEEDED"


def test_workspace_operation_rejects_non_string_operation_id(
    tmp_path: Path,
) -> None:
    client = _client(tmp_path)
    created = client.post("/v1/workspaces", json={"name": "Invalid operation ID"})
    assert created.status_code == 200

    response = client.post(
        "/v1/workspaces/operations",
        json={
            "operation_id": 123,
            "operation_type": "DR24_BATCH_QUERY",
            "source": "ztf_dr24_hats",
            "status": "RUNNING",
            "requested_oids": [123456],
        },
    )
    assert response.status_code == 422



def test_failed_workspace_operation_marks_oid_accounting_unknown(
    tmp_path: Path,
) -> None:
    client = _client(tmp_path)
    created = client.post("/v1/workspaces", json={"name": "Failed DR24 query"})
    assert created.status_code == 200

    running_payload = {
        "operation_id": "f" * 32,
        "operation_type": "DR24_BATCH_QUERY",
        "source": "ztf_dr24_hats",
        "status": "RUNNING",
        "requested_oids": [264114400013085, 264214400000912],
    }
    running = client.post("/v1/workspaces/operations", json=running_payload)
    assert running.status_code == 200
    assert running.json()["oid_accounting_status"] == "PENDING"

    failed = client.post(
        "/v1/workspaces/operations",
        json={
            **running_payload,
            "status": "FAILED",
            "returned_oids": [],
            "missing_oids": [],
            "payload_sha256_by_oid": {},
            "error_code": "dr24_acquisition_failed",
            "error_message": "Source request failed before OID accounting completed.",
        },
    )
    assert failed.status_code == 200
    assert failed.json()["oid_accounting_status"] == "UNKNOWN"
    assert failed.json()["missing_oids"] == []


def test_restarted_workspace_operation_marks_oid_accounting_unknown(
    tmp_path: Path,
) -> None:
    client = _client(tmp_path)
    created = client.post(
        "/v1/workspaces", json={"name": "Interrupted DR24 query"}
    )
    assert created.status_code == 200
    workspace_directory = Path(created.json()["directory"])

    running = client.post(
        "/v1/workspaces/operations",
        json={
            "operation_id": "d" * 32,
            "operation_type": "DR24_BATCH_QUERY",
            "source": "ztf_dr24_hats",
            "status": "RUNNING",
            "requested_oids": [264114400013085, 264214400000912],
        },
    )
    assert running.status_code == 200
    assert running.json()["oid_accounting_status"] == "PENDING"

    restarted_client = _client(tmp_path)
    active = restarted_client.get("/v1/workspaces/active")
    assert active.status_code == 200
    operation = active.json()["workspace"]["last_operation"]
    assert operation["status"] == "INTERRUPTED"
    assert operation["oid_accounting_status"] == "UNKNOWN"
    assert operation["missing_oids"] == []

    operation_log = (
        workspace_directory / "logs" / "operations.jsonl"
    ).read_text(encoding="utf-8").splitlines()
    logged_operation = json.loads(operation_log[-1])
    assert logged_operation["status"] == "INTERRUPTED"
    assert logged_operation["oid_accounting_status"] == "UNKNOWN"

