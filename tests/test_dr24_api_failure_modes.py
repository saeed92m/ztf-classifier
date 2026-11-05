"""Deterministic DR24 API missing-source and failure-path tests."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from ztf_classifier.api.app import create_app
from ztf_classifier.api.config import ApiSettings


class FakeDR24ObservationService:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.requested: list[int] = []

    def get_dr24_native_lightcurve(self, objectid: int) -> dict[str, object]:
        self.requested.append(objectid)
        if self.fail:
            raise RuntimeError("simulated HATS outage")
        return {
            "schema_version": "ztf-dr24-native-lightcurve-v1",
            "records": [],
            "provenance": {
                "source": "IRSA ZTF DR24 Lightcurves HATS",
                "requested_oids": [objectid],
                "returned_oids": [],
                "missing_oids": [objectid],
            },
        }


def _client(tmp_path: Path, service: FakeDR24ObservationService) -> TestClient:
    settings = ApiSettings(
        observation_cache_dir=tmp_path / "cache",
        job_store_path=tmp_path / "jobs.sqlite3",
        result_store_path=tmp_path / "results.sqlite3",
        application_state_path=tmp_path / "settings.json",
    )
    return TestClient(create_app(settings, observation_service=service))  # type: ignore[arg-type]


def test_missing_dr24_oid_is_reported_without_source_substitution(tmp_path: Path) -> None:
    service = FakeDR24ObservationService()
    response = _client(tmp_path, service).get(
        "/v1/dr24/objects/987654321/lightcurve"
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["records"] == []
    assert payload["provenance"]["requested_oids"] == [987654321]
    assert payload["provenance"]["returned_oids"] == []
    assert payload["provenance"]["missing_oids"] == [987654321]
    assert payload["provenance"]["source"] == "IRSA ZTF DR24 Lightcurves HATS"
    assert service.requested == [987654321]


def test_dr24_source_failure_returns_502_without_alerce_fallback(
    tmp_path: Path,
) -> None:
    service = FakeDR24ObservationService(fail=True)
    response = _client(tmp_path, service).get(
        "/v1/dr24/objects/987654321/lightcurve"
    )

    assert response.status_code == 502
    payload = response.json()
    assert payload["code"] == "dr24_acquisition_failed"
    assert "No alternate source was used" in payload["message"]
    assert service.requested == [987654321]
