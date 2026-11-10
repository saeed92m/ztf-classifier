from __future__ import annotations

import json
import os
import threading
import time
import urllib.request
from pathlib import Path
from urllib.error import URLError

import pytest
import uvicorn

from ztf_classifier.api.app import create_app
from ztf_classifier.api.config import ApiSettings
from ztf_classifier.application.observations import ObservationService
from ztf_classifier.io.dr24_lightcurve import (
    DR24LightcurveRecord,
    DR24LightcurveResult,
)


class FakeDR24Backend:
    def __init__(self) -> None:
        self.calls: list[tuple[int, ...]] = []

    def acquire(self, request: object) -> DR24LightcurveResult:
        objectids = tuple(request.objectids)  # type: ignore[attr-defined]
        self.calls.append(objectids)
        records = tuple(
            DR24LightcurveRecord(
                objectid=objectid,
                filterid=1 if objectid == 101 else 2,
                fieldid=100,
                rcid=4,
                objra=120.0 + objectid / 1000,
                objdec=-20.0,
                catalog_nepochs=78 if objectid == 101 else 123,
                epochs=tuple(
                    {
                        "hmjd": (
                            None
                            if objectid == 101 and index == 0
                            else 60000.0 + index * (0.04 if objectid == 101 else 0.02)
                        ),
                        "mag": 18.0 + index * 0.01,
                        "magerr": (
                            -0.01
                            if objectid == 101 and index == 1
                            else 0.02 + (index % 3) * 0.001
                        ),
                        "clrcoeff": 0.1,
                        "catflags": 32768 if index in (2, 20) else 0,
                    }
                    for index in range(78 if objectid == 101 else 123)
                ),
                payload_sha256=f"{objectid:064x}",
            )
            for objectid in objectids
        )
        return DR24LightcurveResult(
            records=records,
            provenance={
                "source": "IRSA ZTF DR24 Lightcurves HATS",
                "query": {"index": "objectid", "objectids": list(objectids)},
                "requested_oids": list(objectids),
                "returned_oids": list(objectids),
                "missing_oids": [],
            },
        )


@pytest.mark.skipif(
    os.getenv("ZTF_DR24_BATCH_UI_TEST") != "1",
    reason="Set ZTF_DR24_BATCH_UI_TEST=1 to run the deterministic browser test.",
)
def test_workbench_loads_and_exports_multiple_dr24_oids(tmp_path: Path) -> None:
    from playwright.sync_api import sync_playwright

    settings = ApiSettings(
        observation_cache_dir=tmp_path / "cache",
        job_store_path=tmp_path / "jobs.sqlite3",
        result_store_path=tmp_path / "results.sqlite3",
        application_state_path=tmp_path / "settings.json",
    )
    backend = FakeDR24Backend()
    service = ObservationService(
        client=object(),
        cache_dir=settings.observation_cache_dir,
        dr24_backend=backend,  # type: ignore[arg-type]
    )
    app = create_app(settings, observation_service=service)
    server = uvicorn.Server(
        uvicorn.Config(app, host="127.0.0.1", port=8766, log_level="warning")
    )
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    try:
        ready = False
        for _ in range(120):
            try:
                with urllib.request.urlopen("http://127.0.0.1:8766/health", timeout=1) as response:
                    ready = response.status == 200
                if ready:
                    break
            except (URLError, TimeoutError, ConnectionError):
                time.sleep(0.5)
        assert ready, "FastAPI did not become ready within 60 seconds"

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto("http://127.0.0.1:8766/workbench", wait_until="domcontentloaded")
            page.locator('[data-view="dr24"]').click()
            page.locator("#dr24ObjectIds").wait_for(state="visible")
            page.locator("#dr24ObjectIds").fill("101, 202")
            page.locator("#dr24LoadButton").click()
            page.wait_for_function(
                "() => document.querySelector('#dr24Status')?.textContent.includes('Raw DR24 response received')",
                timeout=10_000,
            )

            assert backend.calls == [(101, 202)]
            assert page.locator("#dr24Results .panel").count() == 2
            assert page.get_by_text("OID 101 · filter g").is_visible()
            assert page.get_by_text("OID 202 · filter r").is_visible()

            # Every finite raw HMJD/magnitude pair is plotted. Non-drawable raw
            # rows remain in the table preview and complete JSON export.
            assert page.locator("#dr24Results .dr24-data-point").count() == 200
            assert page.locator("#dr24Results .dr24-error-bar").count() == 199
            assert page.locator("#dr24Results .dr24-axis-labels text").count() == 10
            assert page.locator("#dr24Results svg path").count() == 0
            assert page.locator("#dr24Results .catalog-table-wrap tbody tr").count() == 100
            assert "HMJD (HJD − 2400000.5)" in page.locator("#dr24Results").inner_text()
            assert "Points only; no interpolation or smoothing" in page.locator(
                "#dr24Results"
            ).inner_text()
            assert "first 50 of 78" in page.locator("#dr24Results").inner_text()
            assert "first 50 of 123" in page.locator("#dr24Results").inner_text()

            # Lower numerical magnitude must appear higher on the plot.
            first_panel = page.locator("#dr24Results .panel").nth(0)
            y_bright = float(
                first_panel.locator('[data-epoch-index="1"].dr24-data-point').get_attribute("cy")
            )
            y_faint = float(
                first_panel.locator('[data-epoch-index="2"].dr24-data-point').get_attribute("cy")
            )
            assert y_bright < y_faint
            # A negative raw magerr is retained but does not receive an error bar.
            assert first_panel.locator('.dr24-error-bar[data-epoch-index="1"]').count() == 0

            assert "DIAGNOSTIC_NOT_PRODUCTION_APPROVED" in page.locator(
                "#dr24Results"
            ).inner_text()
            provenance = json.loads(page.locator("#dr24Provenance").inner_text())
            assert provenance["requested_oids"] == [101, 202]
            assert provenance["returned_oids"] == [101, 202]
            assert provenance["missing_oids"] == []

            with page.expect_download(timeout=10_000) as download_info:
                page.locator("#dr24ExportButton").click()
            download = download_info.value
            exported = json.loads(Path(download.path()).read_text(encoding="utf-8"))
            assert exported["export_schema_version"] == "ztf-dr24-raw-export-v0.2"
            assert [
                record["objectid"]
                for record in exported["source_payload"]["records"]
            ] == [101, 202]
            assert len(exported["source_payload"]["qc_assessments"]) == 2
            exported_records = {
                record["objectid"]: record
                for record in exported["source_payload"]["records"]
            }
            assert len(exported_records[101]["epochs"]) == 78
            assert len(exported_records[202]["epochs"]) == 123
            assert exported_records[101]["epochs"][0]["hmjd"] is None
            assert exported_records[101]["epochs"][1]["magerr"] == -0.01
            assert exported_records[101]["epochs"][1]["clrcoeff"] == 0.1

            page.locator("#dr24ObjectIds").fill("101,101")
            page.locator("#dr24LoadButton").click()
            assert "Duplicate object IDs" in page.locator("#dr24Status").inner_text()
            assert backend.calls == [(101, 202)]

            page.locator("#dr24ObjectIds").fill(
                ",".join(str(value) for value in range(1, 12))
            )
            page.locator("#dr24LoadButton").click()
            assert "between 1 and 10" in page.locator("#dr24Status").inner_text()
            assert backend.calls == [(101, 202)]
            browser.close()
    finally:
        server.should_exit = True
        thread.join(timeout=10)
