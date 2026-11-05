"""Live browser smoke test for the DR24 Explorer in the Workbench."""

from __future__ import annotations

import json
import os
import threading
import time
import urllib.request
from urllib.error import URLError
from datetime import UTC, datetime
from pathlib import Path

import pytest
import uvicorn

from ztf_classifier.api.app import create_app
from ztf_classifier.api.config import ApiSettings
from ztf_classifier.application.observations import ObservationService
from ztf_classifier.io.dr24_lightcurve import DR24LightcurveBackend

EXPECTED = {
    264114400013085: {
        "epochs": 78, "flagged": 7, "clean": 71,
        "payload_sha256": "735ee15135670a1a28b03b76edfb394e9c0c193d528f3da56ebb593468baf2a0",
    },
    264214400000912: {
        "epochs": 123, "flagged": 8, "clean": 115,
        "payload_sha256": "a37f6fa2ee91009805b6fab3a5563b793cba9e84f6a82ec333bae507442c70ae",
    },
    278115200026587: {
        "epochs": 216, "flagged": 25, "clean": 191,
        "payload_sha256": "03d865e1ce0dc76c721eb09534f0441370c45d4fbb1fffb715e5433899d2ed5f",
    },
}


@pytest.mark.skipif(
    os.getenv("ZTF_DR24_WORKBENCH_LIVE_TEST") != "1",
    reason="Set ZTF_DR24_WORKBENCH_LIVE_TEST=1 to run the live browser test.",
)
def test_workbench_dr24_explorer_renders_live_hats_epochs(tmp_path: Path) -> None:
    from playwright.sync_api import sync_playwright

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
    app = create_app(settings, observation_service=service)
    server = uvicorn.Server(
        uvicorn.Config(app, host="127.0.0.1", port=8765, log_level="warning")
    )
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    try:
        ready = False
        for _ in range(120):
            try:
                with urllib.request.urlopen("http://127.0.0.1:8765/health", timeout=1) as response:
                    ready = response.status == 200
                if ready:
                    break
            except (URLError, TimeoutError, ConnectionError):
                time.sleep(0.5)
        assert ready, "FastAPI did not become ready within 60 seconds"

        results: list[dict[str, object]] = []
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto("http://127.0.0.1:8765/workbench", wait_until="domcontentloaded")
            page.locator('[data-view="dr24"]').click()
            page.locator("#dr24LoadButton").wait_for(state="visible")

            for objectid, expected in EXPECTED.items():
                page.locator("#dr24ObjectId").fill(str(objectid))
                page.locator("#dr24LoadButton").click()
                page.wait_for_function(
                    "() => document.querySelector('#dr24Status')?.textContent.includes('Querying indexed DR24 source')",
                    timeout=10_000,
                )
                page.wait_for_function(
                    "() => document.querySelector('#dr24Status')?.textContent.includes('Raw DR24 response received')",
                    timeout=180_000,
                )

                summary = page.locator("#dr24Summary").inner_text()
                assert f"OID {objectid}" in summary
                assert f"epochs {expected['epochs']} / catalog {expected['epochs']}" in summary
                assert expected["payload_sha256"] in summary
                assert page.locator("#dr24Chart circle").count() == expected["epochs"]
                assert page.locator('#dr24Chart circle[fill="#e0a34a"]').count() == expected["flagged"]
                assert page.locator('#dr24Chart circle[fill="#55b8df"]').count() == expected["clean"]
                assert page.locator("#dr24EpochRows tr").count() == 50

                provenance = json.loads(page.locator("#dr24Provenance").inner_text())
                assert provenance["source"] == "IRSA ZTF DR24 Lightcurves HATS"
                assert provenance["query"]["index"] == "objectid"
                assert provenance["returned_oids"] == [objectid]
                assert provenance["missing_oids"] == []

                results.append(
                    {
                        "objectid": objectid,
                        "epochs": expected["epochs"],
                        "chart_points": page.locator("#dr24Chart circle").count(),
                        "flagged_points": expected["flagged"],
                        "clean_points": expected["clean"],
                        "payload_sha256": expected["payload_sha256"],
                        "payload_hash_match": True,
                        "table_rows_rendered": 50,
                        "provenance_source": provenance["source"],
                    }
                )
            browser.close()

        report = {
            "schema_version": "ztf-dr24-workbench-live-smoke-v1",
            "status": "PASS",
            "code_revision": os.getenv("GITHUB_SHA"),
            "workflow_run_id": os.getenv("GITHUB_RUN_ID"),
            "source": "IRSA ZTF DR24 Lightcurves HATS",
            "tested_view": "DR24 Explorer (raw)",
            "retrieved_at_utc": datetime.now(UTC).isoformat(),
            "objects": results,
            "total_epochs": sum(int(item["epochs"]) for item in results),
            "limitations": [
                "This verifies the DR24 Explorer UI for three OIDs only.",
                "The UI displays at most 50 raw epoch rows per OID.",
                "No feature generation, inference, color correction, HMJD conversion, or quality filtering is performed.",
                "This is not a 5–10 object application acceptance test or a 30–50 object Park demonstration.",
            ],
        }
        output = os.getenv("DR24_WORKBENCH_SMOKE_OUTPUT")
        if output:
            output_path = Path(output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    finally:
        server.should_exit = True
        thread.join(timeout=10)
