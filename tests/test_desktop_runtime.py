from __future__ import annotations

from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from ztf_classifier.api.app import create_app
from ztf_classifier.api.config import ApiSettings
from ztf_classifier.desktop.runtime import (
    DesktopRuntimeError,
    LocalApiServer,
    build_desktop_settings,
    get_user_data_dir,
)


def test_user_data_directory_uses_explicit_windows_location(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr("ztf_classifier.desktop.runtime.os.name", "nt")
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))

    assert get_user_data_dir() == tmp_path / "ZTFClassifier"


def test_build_desktop_settings_uses_per_user_storage(
    tmp_path: Path,
) -> None:
    token = "test-only-session-token"
    base = ApiSettings(
        observation_cache_dir=Path("old-cache"),
        job_store_path=Path("old-jobs.sqlite3"),
        result_store_path=Path("old-results.sqlite3"),
        application_state_path=Path("old-settings.json"),
        scientific_evidence_dir=Path("old-reports"),
    )

    settings = build_desktop_settings(
        token,
        data_dir=tmp_path / "user-data",
        base_settings=base,
    )

    assert settings.api_key == token
    assert settings.observation_cache_dir == tmp_path / "user-data/cache/observations"
    assert settings.job_store_path == tmp_path / "user-data/jobs/jobs.sqlite3"
    assert settings.result_store_path == tmp_path / "user-data/results/results.sqlite3"
    assert (
        settings.application_state_path == tmp_path / "user-data/settings/settings.json"
    )
    assert settings.scientific_evidence_dir == (
        tmp_path / "user-data/reports/scientific_validation"
    )
    assert all(
        path.exists()
        for path in (
            settings.observation_cache_dir,
            settings.job_store_path.parent,
            settings.result_store_path.parent,
            settings.application_state_path.parent,
            settings.scientific_evidence_dir,
        )
    )


def test_build_desktop_settings_requires_a_token(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="token"):
        build_desktop_settings("", data_dir=tmp_path)


def test_desktop_api_requires_session_bearer_token(tmp_path: Path) -> None:
    token = "desktop-test-session-token"
    settings = ApiSettings(
        observation_cache_dir=tmp_path / "cache",
        job_store_path=tmp_path / "jobs.sqlite3",
        result_store_path=tmp_path / "results.sqlite3",
        application_state_path=tmp_path / "settings.json",
        api_key=token,
        scientific_registry_dir=tmp_path / "benchmarks",
        scientific_evidence_dir=tmp_path / "evidence",
    )
    app = create_app(settings=settings)

    with TestClient(app) as client:
        assert client.get("/health").status_code == 200

        unauthorized = client.get("/v1/settings")
        assert unauthorized.status_code == 401
        assert unauthorized.headers["www-authenticate"] == "Bearer"

        authorized = client.get(
            "/v1/settings",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert authorized.status_code == 200


def test_local_api_rejects_non_loopback_host() -> None:
    with pytest.raises(ValueError, match="loopback"):
        LocalApiServer(FastAPI(), host="0.0.0.0")


def test_local_api_starts_on_dynamic_loopback_port_and_stops() -> None:
    app = FastAPI()

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    runtime = LocalApiServer(app, startup_timeout=5, shutdown_timeout=5)
    base_url = runtime.start()

    try:
        assert runtime.is_running
        assert base_url.startswith("http://127.0.0.1:")
        assert 0 < runtime.port < 65536
    finally:
        runtime.stop()

    assert not runtime.is_running



def test_local_api_surfaces_unexpected_worker_exception(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FailingServer:
        def __init__(self, config: object) -> None:
            self.should_exit = False
            self.force_exit = False

        def run(self, sockets: list[object]) -> None:
            raise KeyError("unexpected worker failure")

    monkeypatch.setattr(
        "ztf_classifier.desktop.runtime.uvicorn.Server",
        FailingServer,
    )
    runtime = LocalApiServer(FastAPI(), startup_timeout=2, shutdown_timeout=1)

    with pytest.raises(DesktopRuntimeError) as error:
        runtime.start()

    assert isinstance(error.value.__cause__, KeyError)
    assert not runtime.is_running


def test_local_api_requires_ready_health_endpoint() -> None:
    app = FastAPI()

    @app.get("/not-health")
    def not_health() -> dict[str, str]:
        return {"status": "ok"}

    runtime = LocalApiServer(app, startup_timeout=0.25, shutdown_timeout=5)
    with pytest.raises(DesktopRuntimeError, match="did not become ready"):
        runtime.start()
    assert not runtime.is_running
