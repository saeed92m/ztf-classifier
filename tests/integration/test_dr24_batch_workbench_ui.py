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
                catalog_nepochs=3,
                epochs=(
                    {
                        "hmjd": 60000.1,
                        "mag": 18.2,
                        "magerr": 0.03,
                        "clrcoeff": 0.1,
                        "catflags": 0,
                    },
                    {
                        "hmjd": 60000.2,
                        "mag": 18.3,
                        "magerr": 0.04,
                        "clrcoeff": 0.1,
                        "catflags": 32768,
                    },
                    {
                        "hmjd": None,
                        "mag": 18.4,
                        "magerr": 0.02,
                        "clrcoeff": 0.1,
                        "catflags": 0,
                    },
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
            page.add_init_script(
                "window.pywebview = {api: {get_api_token: () => Promise.resolve('test-only-token')}};"
            )
            page.goto(
                "http://127.0.0.1:8766/workbench/?desktop=1",
                wait_until="domcontentloaded",
            )
            assert page.locator("html").get_attribute("lang") == "fa"
            assert page.locator("html").get_attribute("dir") == "rtl"
            assert page.get_by_text("داشبورد").is_visible()
            assert page.locator('[data-view="classification"]').is_hidden()
            page.locator('[data-view="dr24"]').click()
            page.locator("#dr24ObjectIds").wait_for(state="visible")
            page.locator("#dr24ObjectIds").fill("101, 202")
            page.locator("#dr24LoadButton").click()
            page.wait_for_function(
                "() => document.querySelector('#dr24Status')?.textContent.includes('پاسخ خام DR24 دریافت شد')",
                timeout=10_000,
            )

            assert backend.calls == [(101, 202)]
            assert page.locator("#dr24Results .panel").count() == 2
            assert page.get_by_text("OID 101 · فیلتر g").is_visible()
            assert page.get_by_text("OID 202 · فیلتر r").is_visible()
            assert page.locator("#dr24Results svg circle").count() == 4
            assert page.locator("#dr24Results svg .dr24-error-bar").count() == 4
            assert page.locator("#dr24Results .report-content").count() == 2
            assert page.get_by_text("خلاصه توصیفی سری زمانی").count() == 2
            assert page.get_by_text("میانه فاصله نمونه‌برداری (روز)").count() == 2
            assert "DIAGNOSTIC_NOT_PRODUCTION_APPROVED" in page.locator(
                "#dr24Results"
            ).inner_text()
            assert '"invalid_photometry_epochs": 1' in page.locator(
                "#dr24Results .report-content"
            ).first.inner_text()
            assert page.locator("#dr24Results tbody tr").count() == 6
            provenance = json.loads(page.locator("#dr24Provenance").inner_text())
            assert provenance["requested_oids"] == [101, 202]
            assert provenance["returned_oids"] == [101, 202]
            assert provenance["missing_oids"] == []

            with page.expect_download(timeout=10_000) as download_info:
                page.locator("#dr24ExportButton").click()
            download = download_info.value
            exported = json.loads(Path(download.path()).read_text(encoding="utf-8"))
            assert exported["export_schema_version"] == "ztf-dr24-raw-export-v0.3"
            assert [
                record["objectid"]
                for record in exported["source_payload"]["records"]
            ] == [101, 202]
            assert len(exported["source_payload"]["qc_assessments"]) == 2
            assert exported["source_payload"]["records"][0]["epochs"][2]["hmjd"] is None

            page.locator('[data-view="desktop-provenance"]').click()
            assert "requested_oids" in page.locator("#desktopProvenanceJson").inner_text()
            page.locator('[data-view="desktop-export"]').click()
            assert page.locator("#desktopDownloadJson").is_enabled()

            page.locator('[data-view="dr24"]').click()
            page.locator("#dr24ObjectIds").fill("101,101")
            page.locator("#dr24LoadButton").click()
            assert "OID تکراری مجاز نیست" in page.locator("#dr24Status").inner_text()
            assert backend.calls == [(101, 202)]

            page.locator("#dr24ObjectIds").fill(
                ",".join(str(value) for value in range(1, 12))
            )
            page.locator("#dr24LoadButton").click()
            assert "بین ۱ تا ۱۰ شناسه وارد کنید" in page.locator("#dr24Status").inner_text()
            assert backend.calls == [(101, 202)]
            browser.close()
    finally:
        server.should_exit = True
        thread.join(timeout=10)
