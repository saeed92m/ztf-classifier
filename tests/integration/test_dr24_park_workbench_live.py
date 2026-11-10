from __future__ import annotations

import json
import math
import os
import socket
import threading
import time
from datetime import UTC, datetime
from pathlib import Path
from urllib.error import URLError
import urllib.request

import pytest
import uvicorn

from ztf_classifier.api.app import create_app
from ztf_classifier.api.config import ApiSettings
from ztf_classifier.application.observations import ObservationService
from ztf_classifier.io.dr24_lightcurve import DR24LightcurveBackend

SAMPLE = (
    (199109100000000, 11, "f2bc8c8241d44e115515f318946612d0ffe7645468d3e8e9b15fe78c86c3ea51"),
    (199109100000014, 12, "2862e95d7a77feb6ef33d6fc57b36525f7c958331d0d1c4b22adcce547666b09"),
    (199109100000033, 9, "eee8dc283fa8a0243507fbd2fc4d132bd0704b7ad8c779cac3aa530aa1bd0abb"),
    (199109100000049, 1, "6d7819c6f766dd1abfe0ee7093f5306fd72a00fc727867e276508c3985c4ad1d"),
    (199109100000063, 155, "083baa2808ab25a92df15947e1ceda37c0a3a2f5aa617f1ae1c36d351b22459f"),
    (199109100000085, 149, "1244aa612b7c2e425e8b3168a6dc66f2280c91bc6f927c3787d28f5acfae639c"),
    (199109100000096, 162, "515eedcc6b092ea790500bffe17c4837da1d11b43a40c090c64058d0a8b0bde5"),
    (199109100000114, 1, "92dcc1e1ee9f849b38747e8eb2d029ea617d1d0bea833144e8d34215c4cf241e"),
    (199109100000128, 26, "5290505c1b71fed62ca5f5f427334beb0ce39efff04977d1f5f25486e0a5b7fd"),
    (199109100000148, 162, "b3b968d3c15bbd4410dcacd81a86b7151300611d40b94aba16ed839920f185f5"),
)
CATALOG_RESPONSE_SHA256 = "4cc5827cd077252ceca99af587e4091e5cb5b4e7ca00a45d0d3a07bbfaaa52c7"
CATALOG_ARTIFACT_SHA256 = "31d0609322e6c5671d485a20c970ef3c4760844c3d38a28769ad8e30d1928058"


def _finite(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


@pytest.mark.skipif(
    os.getenv("ZTF_DR24_PARK_WORKBENCH_LIVE_TEST") != "1",
    reason="Set ZTF_DR24_PARK_WORKBENCH_LIVE_TEST=1 to run live DR24 Workbench validation.",
)
def test_live_dr24_hats_workbench_renders_and_exports_ten_oids(tmp_path: Path) -> None:
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
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    base_url = f"http://127.0.0.1:{port}"
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning"))
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    out = Path("park-demo-evidence")
    out.mkdir(parents=True, exist_ok=True)

    try:
        ready = False
        for _ in range(120):
            try:
                with urllib.request.urlopen(base_url + "/health", timeout=1) as response:
                    ready = response.status == 200
                if ready:
                    break
            except (URLError, TimeoutError, ConnectionError):
                time.sleep(0.5)
        assert ready, "FastAPI did not become ready within 60 seconds"

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1600, "height": 1000})
            console_errors: list[str] = []
            page_errors: list[str] = []
            page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
            page.on("pageerror", lambda err: page_errors.append(str(err)))
            page.goto(base_url + "/workbench", wait_until="domcontentloaded")
            page.locator('[data-view="dr24"]').click()
            page.locator("#dr24ObjectIds").wait_for(state="visible")
            requested = [str(row[0]) for row in SAMPLE]
            page.locator("#dr24ObjectIds").fill(",".join(requested))
            page.locator("#dr24LoadButton").click()
            page.wait_for_function(
                "() => document.querySelector('#dr24Status')?.textContent.includes('Raw DR24 response received')",
                timeout=60_000,
            )

            status = page.locator("#dr24Status").inner_text()
            assert "Requested 10" in status and "returned 10" in status and "missing 0" in status
            panels = page.locator("#dr24Results > .panel")
            assert panels.count() == 10

            for index, (oid, epochs, digest) in enumerate(SAMPLE):
                panel = panels.nth(index)
                summary = panel.inner_text()
                assert f"OID {oid} · filter g" in summary
                assert f"epochs {epochs} / catalog {epochs}" in summary
                assert digest in summary
                assert panel.locator(".dr24-chart svg").count() == 1
                assert panel.locator(".catalog-table-wrap").count() == 3
                assert panel.locator(".catalog-table-wrap").nth(2).locator("tbody tr").count() == min(50, epochs)

            with page.expect_download(timeout=30_000) as download_info:
                page.locator("#dr24ExportButton").click()
            download_path = out / "ztf-dr24-park-10-oid-workbench-raw-export.json"
            download_info.value.save_as(str(download_path))
            exported = json.loads(download_path.read_text(encoding="utf-8"))
            records = exported["source_payload"]["records"]
            by_oid = {int(record["objectid"]): record for record in records}
            assert len(by_oid) == 10
            assert set(by_oid) == {row[0] for row in SAMPLE}

            expected_epochs = expected_points = expected_errorbars = 0
            per_oid = []
            for oid, expected_count, expected_hash in SAMPLE:
                record = by_oid[oid]
                epochs = record["epochs"]
                assert len(epochs) == expected_count == record["catalog_nepochs"]
                assert record["payload_sha256"] == expected_hash
                drawable = [
                    row for row in epochs
                    if _finite(row.get("hmjd")) and _finite(row.get("mag"))
                ]
                errorbars = [
                    row for row in drawable
                    if _finite(row.get("magerr")) and row["magerr"] >= 0
                ]
                expected_epochs += len(epochs)
                expected_points += len(drawable)
                expected_errorbars += len(errorbars)
                per_oid.append({
                    "objectid": oid,
                    "filterid": record["filterid"],
                    "fieldid": record["fieldid"],
                    "rcid": record["rcid"],
                    "raw_rows": len(epochs),
                    "drawable_points": len(drawable),
                    "valid_magerr_errorbars": len(errorbars),
                    "payload_sha256": expected_hash,
                })

            assert expected_epochs == 688
            assert page.locator("#dr24Results .dr24-data-point").count() == expected_points
            assert page.locator("#dr24Results .dr24-error-bar").count() == expected_errorbars
            assert page.locator("#dr24Results .dr24-axis-labels text").count() == 100
            assert page.locator("#dr24Results .dr24-chart svg path").count() == 0
            assert "HMJD (HJD − 2400000.5)" in page.locator("#dr24Results").inner_text()
            assert "Points only; no interpolation or smoothing" in page.locator("#dr24Results").inner_text()
            assert "DIAGNOSTIC_NOT_PRODUCTION_APPROVED" in page.locator("#dr24Results").inner_text()

            orientation_verified = False
            for panel_index in range(10):
                nodes = panels.nth(panel_index).locator(".dr24-data-point")
                samples = []
                for point_index in range(nodes.count()):
                    node = nodes.nth(point_index)
                    samples.append((
                        float(node.get_attribute("data-mag")),
                        float(node.get_attribute("cy")),
                    ))
                if len(samples) > 1 and min(p[0] for p in samples) < max(p[0] for p in samples):
                    brightest = min(samples, key=lambda p: p[0])
                    faintest = max(samples, key=lambda p: p[0])
                    assert brightest[1] < faintest[1]
                    orientation_verified = True
                    break
            assert orientation_verified

            page.screenshot(path=str(out / "ztf-dr24-park-10-oid-workbench-full.png"), full_page=True)
            panels.nth(4).screenshot(path=str(out / "ztf-dr24-park-single-oid-lightcurve.png"))
            assert not page_errors, page_errors
            assert not console_errors, console_errors

            manifest = {
                "schema_version": "ztf-dr24-park-live-workbench-evidence-v1",
                "validation_status": "PASS",
                "created_at_utc": datetime.now(UTC).isoformat(),
                "code_revision": os.getenv("GITHUB_SHA"),
                "source": "IRSA ZTF DR24 Lightcurves HATS",
                "source_release": "DR24",
                "source_uri": "s3://ipac-irsa-ztf/ztf/enhanced/dr24/lc/hats",
                "catalog_snapshot_sha256": CATALOG_RESPONSE_SHA256,
                "catalog_artifact_zip_sha256": CATALOG_ARTIFACT_SHA256,
                "sample_unit": "OID records; not confirmed astrophysical source groups",
                "requested_oids": requested,
                "returned_oids": sorted(by_oid),
                "missing_oids": [],
                "raw_epoch_rows": expected_epochs,
                "drawable_points": expected_points,
                "valid_magerr_errorbars": expected_errorbars,
                "browser_checks": {
                    "ten_oid_panels": True,
                    "raw_export_all_epochs": True,
                    "points_match_finite_hmjd_mag_pairs": True,
                    "errorbars_match_valid_magerr": True,
                    "no_lines_or_interpolation": True,
                    "hmjd_axis_label": True,
                    "magnitude_axis_direction": True,
                    "diagnostic_qc_disclosed": True,
                    "page_errors": page_errors,
                    "console_errors": console_errors,
                },
                "objects": per_oid,
                "limitations": [
                    "Ten OID records do not establish ten unique physical sources.",
                    "The 150-row metadata snapshot is lexicographic and from one HATS partition; it is not sky-representative.",
                    "No cross-OID identity grouping, time conversion, color correction, epoch filtering, features, classification, calibration, OOD, or scientific anomaly analysis is performed.",
                    "QC is diagnostic only and is not an approved model-input policy.",
                ],
                "export": download_path.name,
                "screenshots": [
                    "ztf-dr24-park-10-oid-workbench-full.png",
                    "ztf-dr24-park-single-oid-lightcurve.png",
                ],
            }
            (out / "ztf-dr24-park-live-workbench-manifest.json").write_text(
                json.dumps(manifest, indent=2, sort_keys=True, allow_nan=False),
                encoding="utf-8",
            )
            browser.close()
    finally:
        server.should_exit = True
        thread.join(timeout=10)
