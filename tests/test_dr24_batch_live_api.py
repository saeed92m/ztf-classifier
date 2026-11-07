from __future__ import annotations

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from ztf_classifier.api.app import create_app
from ztf_classifier.api.config import ApiSettings
from ztf_classifier.application.observations import ObservationService
from ztf_classifier.io.dr24_lightcurve import DR24LightcurveBackend

EXPECTED = {
    264114400013085: {
        "epochs": 78,
        "sha256": "735ee15135670a1a28b03b76edfb394e9c0c193d528f3da56ebb593468baf2a0",
    },
    264214400000912: {
        "epochs": 123,
        "sha256": "a37f6fa2ee91009805b6fab3a5563b793cba9e84f6a82ec333bae507442c70ae",
    },
}


@pytest.mark.skipif(
    os.getenv("ZTF_DR24_BATCH_LIVE_TEST") != "1",
    reason="Set ZTF_DR24_BATCH_LIVE_TEST=1 to run live DR24 HATS parity.",
)
def test_batch_api_matches_pinned_independent_hats_payloads(tmp_path: Path) -> None:
    settings = ApiSettings(
        observation_cache_dir=tmp_path / "cache",
        job_store_path=tmp_path / "jobs.sqlite3",
        result_store_path=tmp_path / "results.sqlite3",
        application_state_path=tmp_path / "settings.json",
    )
    service = ObservationService(
        client=object(),
        cache_dir=settings.observation_cache_dir,
        dr24_backend=DR24LightcurveBackend(),
    )
    client = TestClient(create_app(settings, observation_service=service))

    objectids = list(EXPECTED)
    response = client.post(
        "/v1/dr24/lightcurves",
        json={"objectids": objectids},
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["provenance"]["source"] == "IRSA ZTF DR24 Lightcurves HATS"
    assert payload["provenance"]["requested_oids"] == objectids
    assert payload["provenance"]["returned_oids"] == objectids
    assert payload["provenance"]["missing_oids"] == []

    records = {record["objectid"]: record for record in payload["records"]}
    assert set(records) == set(EXPECTED)
    for objectid, expected in EXPECTED.items():
        record = records[objectid]
        assert record["catalog_nepochs"] == expected["epochs"]
        assert len(record["epochs"]) == expected["epochs"]
        assert record["payload_sha256"] == expected["sha256"]

    assessments = {
        item["objectid"]: item for item in payload["qc_assessments"]
    }
    assert set(assessments) == set(EXPECTED)
    assert all(
        item["policy_status"] == "DIAGNOSTIC_NOT_PRODUCTION_APPROVED"
        for item in assessments.values()
    )
