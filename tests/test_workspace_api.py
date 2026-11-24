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
