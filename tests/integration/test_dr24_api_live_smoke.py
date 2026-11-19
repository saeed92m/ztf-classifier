"""Live DR24 API smoke test; disabled in ordinary offline CI."""

from __future__ import annotations

import json
import os
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from ztf_classifier.api.app import create_app
from ztf_classifier.api.config import ApiSettings
from ztf_classifier.application.observations import ObservationService
from ztf_classifier.io.dr24_lightcurve import DR24LightcurveBackend

EXPECTED = {
    264114400013085: {
        "filterid": 1, "fieldid": 264, "rcid": 55, "epochs": 78,
        "payload_sha256": "735ee15135670a1a28b03b76edfb394e9c0c193d528f3da56ebb593468baf2a0",
        "catflags": {"0": 71, "32768": 7},
    },
    264214400000912: {
        "filterid": 2, "fieldid": 264, "rcid": 55, "epochs": 123,
        "payload_sha256": "a37f6fa2ee91009805b6fab3a5563b793cba9e84f6a82ec333bae507442c70ae",
        "catflags": {"0": 115, "32768": 8},
    },
    278115200026587: {
        "filterid": 1, "fieldid": 278, "rcid": 57, "epochs": 216,
        "payload_sha256": "03d865e1ce0dc76c721eb09534f0441370c45d4fbb1fffb715e5433899d2ed5f",
        "catflags": {"0": 191, "32768": 25},
    },
}


@pytest.mark.skipif(
    os.getenv("ZTF_DR24_LIVE_TEST") != "1",
    reason="Set ZTF_DR24_LIVE_TEST=1 to run the bounded live HATS integration test.",
)
def test_live_dr24_api_matches_verified_hats_payloads(tmp_path: Path) -> None:
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

    objects: list[dict[str, object]] = []
    for objectid, expected in EXPECTED.items():
        response = client.get(f"/v1/dr24/objects/{objectid}/lightcurve")
        assert response.status_code == 200, response.text
        payload = response.json()
        assert payload["schema_version"] == "ztf-dr24-native-lightcurve-v1"
        assert payload["provenance"]["source"] == "IRSA ZTF DR24 Lightcurves HATS"
        assert payload["provenance"]["release"] == "DR24"
        assert payload["provenance"]["query"] == {
            "index": "objectid",
            "objectids": [objectid],
        }
        assert payload["provenance"]["missing_oids"] == []
        assert len(payload["records"]) == 1

        record = payload["records"][0]
        epochs = record["epochs"]
        assert record["objectid"] == objectid
        assert record["filterid"] == expected["filterid"]
        assert record["fieldid"] == expected["fieldid"]
        assert record["rcid"] == expected["rcid"]
        assert record["catalog_nepochs"] == expected["epochs"]
        assert len(epochs) == expected["epochs"]
        assert record["payload_sha256"] == expected["payload_sha256"]
        assert set(epochs[0]) == {"hmjd", "mag", "magerr", "clrcoeff", "catflags"}
        assert dict(Counter(str(row["catflags"]) for row in epochs)) == expected["catflags"]
        assert all(row["hmjd"] is not None for row in epochs)
        assert all(row["mag"] is not None for row in epochs)
        assert all(row["magerr"] is not None and row["magerr"] > 0 for row in epochs)

        objects.append(
            {
                "objectid": objectid,
                "filterid": record["filterid"],
                "fieldid": record["fieldid"],
                "rcid": record["rcid"],
                "catalog_nepochs": record["catalog_nepochs"],
                "returned_epochs": len(epochs),
                "payload_sha256": record["payload_sha256"],
                "expected_payload_sha256": expected["payload_sha256"],
                "payload_hash_match": True,
                "catflags_counts": expected["catflags"],
                "retrieved_at_utc": payload["provenance"]["retrieved_at_utc"],
            }
        )

    report = {
        "schema_version": "ztf-dr24-api-live-smoke-v1",
        "status": "PASS",
        "code_revision": os.getenv("GITHUB_SHA"),
        "workflow_run_id": os.getenv("GITHUB_RUN_ID"),
        "source": "IRSA ZTF DR24 Lightcurves HATS",
        "index": "objectid",
        "retrieved_at_utc": datetime.now(UTC).isoformat(),
        "objects": objects,
        "total_epochs": sum(int(item["returned_epochs"]) for item in objects),
        "limitations": [
            "This verifies the FastAPI raw acquisition route for three OIDs only.",
            "No photometry normalization, color correction, HMJD conversion, or catflags filtering is applied.",
            "No OID grouping, feature generation, model inference, or scientific performance is evaluated.",
        ],
    }
    output = os.getenv("DR24_LIVE_SMOKE_OUTPUT")
    if output:
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
