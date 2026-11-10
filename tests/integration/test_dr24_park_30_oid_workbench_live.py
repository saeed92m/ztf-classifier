from __future__ import annotations

import hashlib
import json
import math
import os
import socket
import threading
import time
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from urllib.error import URLError

import pytest
import uvicorn

from ztf_classifier.api.app import create_app
from ztf_classifier.api.config import ApiSettings
from ztf_classifier.application.observations import ObservationService
from ztf_classifier.io.dr24_lightcurve import DR24LightcurveBackend

# Exact fixed OID/epoch/hash reference from the live 30-OID HATS retrieval.
# The sample is an engineering demonstration subset from a single catalog
# partition, not a sky-representative population or physical-source catalogue.
SAMPLE = (
    (199109100000004, 102, "ad40b73c0decd9fac6e1be35ba798c5511a8a2934866679787b2b27e4bea08aa"),
    (199109100000005, 139, "f29f7e9b65376e93cd5324aab721b5b68044777a78217c3303c3fdd9aed6669f"),
    (199109100000007, 148, "c7b81688f366d4943ee7b7e0ad1c281ac1d39ea135b77f9416f4fb7d51936f71"),
    (199109100000010, 149, "5085c0420146ddee64fb0e5874f7d7b564b201b1edd40c4956827ce6dc621dce"),
    (199109100000011, 133, "5883cf5c5720b4566e8589d9a13a3290075e307a59af5066514481c8d05f1460"),
    (199109100000013, 153, "86ea880072fd9cfd8aedf08651f2d6fa70ab1eaa74ff52dabc825ddef0c02fbd"),
    (199109100000018, 158, "ee11cd5c7b195612e071b39f1b6a1621a589a9b177c652c7064a07b22c7c68e4"),
    (199109100000029, 103, "d7b2eae5bc970c1a93c6450adff1b185abb32f0c86d844365b31b407367cd9ac"),
    (199109100000044, 140, "61272f5e2955cda4c0fdc7230a5f18413cc5aa7140e515b91dc0058fce1b4e65"),
    (199109100000046, 114, "e4bff72f293837a90bd12d09833755f2b258a1c393b4741332628aa7907da4d7"),
    (199109100000048, 131, "1ee9666717808f48c72b6cd4d8e11fb38b0e8c7f3ffedccf99c22b51b63bc47f"),
    (199109100000053, 127, "59d3684630cefadcccf29d4510f89175a6e7274a748a4b32a9e2ebb748b651c4"),
    (199109100000058, 160, "d5843d510001924fc701ede9f63469553d93e5627c5c7c04d4f2b4f9241f3fe8"),
    (199109100000062, 137, "bcc9a30ea82fefedda426fe15ef0ce9e06484a76055f1c96e6c69d7cbd275873"),
    (199109100000063, 155, "083baa2808ab25a92df15947e1ceda37c0a3a2f5aa617f1ae1c36d351b22459f"),
    (199109100000065, 101, "7e1f64265cdfa4202b4e65245e793576f5871cab9655b40893565aa7eefeff67"),
    (199109100000070, 109, "a3d9ab0acddee05237368d61f9583a99c824e1527556c2ef62be4d6305d93736"),
    (199109100000085, 149, "1244aa612b7c2e425e8b3168a6dc66f2280c91bc6f927c3787d28f5acfae639c"),
    (199109100000089, 162, "808ab2105e8ad85d4ed6f3ddf8e4158356661ad2ad178d0e3255c823fbed23a4"),
    (199109100000096, 162, "515eedcc6b092ea790500bffe17c4837da1d11b43a40c090c64058d0a8b0bde5"),
    (199109100000106, 107, "afab07d0faf1245123be901d49870453990c807953d7f19a58745b8408b8881b"),
    (199109100000108, 112, "75ba04f43bb1e13cd87ee368e15db403e7371faee9b0b41324d602d53b4563be"),
    (199109100000112, 123, "084d22ad962ea5d02bdf16d8ac70e2e01761bbcafb783254a8d1941962f01c4b"),
    (199109100000115, 107, "89780de148bb4e166ec09157a1e74c05ca95de15d5aabff12ddcccef2660cd72"),
    (199109100000117, 162, "5212f04dec7dac10f42f622fa9204b973ff4433bf24e73261e72e20456588945"),
    (199109100000122, 118, "6124b216e42abf419bcbe064a26c678aa6322b8d06d3e0c8502e9c6353bd6d83"),
    (199109100000134, 99, "4ce76603d3b7ad5d5b5699dea7ef4242b3a26773766a2e38b7998ee470bd6292"),
    (199109100000137, 162, "3b2d82fa0dee3ea04373e03306caaeb18432e2ccea1e65deb56a9a9517ce2b64"),
    (199109100000140, 162, "67d7bc34fe5e136b8ff1fa74ca13dcf8dfdb8dbb7aa41d070398504034010f81"),
    (199109100000145, 162, "8f2837a839e10c534a53401824865b167307fcb606a314d55617236d5771f217"),
)
CATALOG_RESPONSE_SHA256 = "4cc5827cd077252ceca99af587e4091e5cb5b4e7ca00a45d0d3a07bbfaaa52c7"
CATALOG_ARTIFACT_SHA256 = "31d0609322e6c5671d485a20c970ef3c4760844c3d38a28769ad8e30d1928058"
EXPECTED_EPOCH_TOTAL = 4046


def _finite_nonnegative(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
        and value >= 0
    )


def _finite(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


@pytest.mark.skipif(
    os.getenv("ZTF_DR24_PARK_30OID_WORKBENCH_LIVE_TEST") != "1",
    reason="Set ZTF_DR24_PARK_30OID_WORKBENCH_LIVE_TEST=1 for the live 30-OID Workbench test.",
)
def test_live_30_oid_workbench_walkthrough_in_three_bounded_batches(
    tmp_path: Path,
) -> None:
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
    server = uvicorn.Server(
        uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning")
    )
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    output_dir = Path("park-demo-evidence")
    output_dir.mkdir(parents=True, exist_ok=True)
    all_records: dict[int, dict] = {}
    batch_exports: list[dict] = []
    browser_errors: list[str] = []
    console_errors: list[str] = []

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
            page.on(
                "console",
                lambda message: console_errors.append(message.text)
                if message.type == "error"
                else None,
            )
            page.on("pageerror", lambda error: browser_errors.append(str(error)))
            page.goto(base_url + "/workbench", wait_until="domcontentloaded")
            page.locator('[data-view="dr24"]').click()
            page.locator("#dr24ObjectIds").wait_for(state="visible")
            # Source provenance is asserted from each API response and export manifest.
            # The UI does not expose a dedicated #dr24Source element.

            # The application enforces a maximum of 10 unique OIDs per request.
            # Use three consecutive, explicitly bounded user-interface requests.
            for batch_index in range(3):
                batch = SAMPLE[batch_index * 10 : (batch_index + 1) * 10]
                requested = [str(row[0]) for row in batch]
                page.locator("#dr24ObjectIds").fill(",".join(requested))
                # The status text is intentionally identical for each successful
                # 10-OID batch. Wait for the actual POST response and the exact OIDs
                # rendered by the UI, not for a status-string change.
                with page.expect_response(
                    lambda response: (
                        response.url.endswith("/v1/dr24/lightcurves")
                        and response.request.method == "POST"
                    ),
                    timeout=60_000,
                ) as response_info:
                    page.locator("#dr24LoadButton").click()
                api_response = response_info.value
                assert api_response.status == 200, api_response.text()
                api_payload = api_response.json()
                api_records = api_payload.get("records", [])
                assert sorted(int(record["objectid"]) for record in api_records) == sorted(
                    int(value) for value in requested
                )
                assert api_payload.get("provenance", {}).get("missing_oids") == []

                page.wait_for_function(
                    """expected => {
                        const status = document.querySelector('#dr24Status')?.textContent || '';
                        if (!status.includes('Raw DR24 response received')) return false;
                        const panels = Array.from(
                            document.querySelectorAll('#dr24Results > .panel')
                        );
                        if (panels.length !== expected.length) return false;
                        const panelText = panels.map(panel => panel.textContent || '');
                        return expected.every(oid =>
                            panelText.some(text => text.includes('OID ' + oid + ' · filter g'))
                        );
                    }""",
                    arg=requested,
                    timeout=60_000,
                )
                status = page.locator("#dr24Status").inner_text()
                assert "Requested 10" in status, status
                assert "returned 10" in status, status
                assert "missing 0" in status, status
                assert page.locator("#dr24Results > .panel").count() == 10

                # The HATS result order is not a scientific identity guarantee.
                # Match UI panels by exact OID, never by array position.
                panel_texts = [
                    page.locator("#dr24Results > .panel").nth(index).inner_text()
                    for index in range(10)
                ]
                for oid, expected_epochs, expected_hash in batch:
                    matches = [
                        index
                        for index, panel_text in enumerate(panel_texts)
                        if f"OID {oid} · filter g" in panel_text
                    ]
                    assert len(matches) == 1, f"Expected one panel for OID {oid}"
                    panel = page.locator("#dr24Results > .panel").nth(matches[0])
                    panel_text = panel.inner_text()
                    assert f"epochs {expected_epochs} / catalog {expected_epochs}" in panel_text
                    # The UI abbreviates the digest for readability.
                    # The downloaded raw export is checked against the full SHA-256 below.
                    assert expected_hash[:16] in panel_text
                    assert panel.locator(".dr24-chart svg").count() == 1
                    assert panel.locator(".catalog-table-wrap").count() == 3
                    assert panel.locator(".catalog-table-wrap").nth(2).locator(
                        "tbody tr"
                    ).count() == 50
                    assert panel.locator(".dr24-data-point").count() == expected_epochs
                    assert panel.locator(".dr24-error-bar").count() == expected_epochs
                    assert panel.locator(".dr24-chart svg path").count() == 0

                with page.expect_download(timeout=30_000) as download_info:
                    page.locator("#dr24ExportButton").click()
                export_path = output_dir / f"ztf-dr24-park-30-oid-workbench-batch-{batch_index + 1}.json"
                download_info.value.save_as(str(export_path))
                exported = json.loads(export_path.read_text(encoding="utf-8"))
                exported_records = exported["source_payload"]["records"]
                by_oid = {
                    int(record["objectid"]): record
                    for record in exported_records
                }
                assert len(by_oid) == 10
                assert set(by_oid) == {row[0] for row in batch}

                for oid, expected_epochs, expected_hash in batch:
                    record = by_oid[oid]
                    epochs = record["epochs"]
                    assert record["catalog_nepochs"] == expected_epochs
                    assert len(epochs) == expected_epochs
                    assert record["payload_sha256"] == expected_hash
                    assert all(
                        _finite(epoch.get("hmjd")) and _finite(epoch.get("mag"))
                        for epoch in epochs
                    )
                    assert all(
                        _finite_nonnegative(epoch.get("magerr"))
                        for epoch in epochs
                    )
                    assert oid not in all_records
                    all_records[oid] = record

                batch_exports.append(
                    {
                        "batch_index": batch_index + 1,
                        "requested_oids": [row[0] for row in batch],
                        "returned_oids": sorted(by_oid),
                        "missing_oids": [],
                        "total_epoch_rows": sum(len(r["epochs"]) for r in by_oid.values()),
                        "export_file": export_path.name,
                        "export_sha256": hashlib.sha256(export_path.read_bytes()).hexdigest(),
                    }
                )
                page.screenshot(
                    path=str(
                        output_dir
                        / f"ztf-dr24-park-30-oid-workbench-batch-{batch_index + 1}.png"
                    ),
                    full_page=True,
                )

            assert len(all_records) == 30
            total_epochs = sum(len(record["epochs"]) for record in all_records.values())
            assert total_epochs == EXPECTED_EPOCH_TOTAL
            assert sorted(all_records) == sorted(row[0] for row in SAMPLE)
            assert not browser_errors, browser_errors
            assert not console_errors, console_errors

            combined_raw = {
                "source": "IRSA ZTF DR24 Lightcurves HATS",
                "source_release": "DR24",
                "sample_unit": "OID records; physical-source identity not established",
                "records": [all_records[row[0]] for row in SAMPLE],
            }
            combined_path = output_dir / "ztf-dr24-park-30-oid-workbench-all-raw.json"
            combined_path.write_text(
                json.dumps(combined_raw, indent=2, sort_keys=True, allow_nan=False),
                encoding="utf-8",
            )
            manifest = {
                "schema_version": "ztf-dr24-park-30-oid-live-workbench-manifest-v1",
                "validation_status": "PASS",
                "created_at_utc": datetime.now(UTC).isoformat(),
                "code_revision": os.getenv("GITHUB_SHA"),
                "workflow_run": os.getenv("GITHUB_RUN_ID"),
                "source": "IRSA ZTF DR24 Lightcurves HATS",
                "source_release": "DR24",
                "source_uri": "s3://ipac-irsa-ztf/ztf/enhanced/dr24/lc/hats",
                "catalog_snapshot_sha256": CATALOG_RESPONSE_SHA256,
                "catalog_artifact_zip_sha256": CATALOG_ARTIFACT_SHA256,
                "sample_selection": (
                    "First 30 ascending OIDs with ngoodobsrel >= 75 from a pinned "
                    "150-row lexicographic metadata subset in one HATS partition. "
                    "This rule selects an engineering demonstration sample only."
                ),
                "requested_oid_count": 30,
                "returned_oid_count": len(all_records),
                "missing_oid_count": 0,
                "batch_count": len(batch_exports),
                "maximum_oids_per_request": 10,
                "raw_epoch_rows": total_epochs,
                "batches": batch_exports,
                "all_raw_export": combined_path.name,
                "all_raw_export_sha256": hashlib.sha256(combined_path.read_bytes()).hexdigest(),
                "browser_page_errors": browser_errors,
                "browser_console_errors": console_errors,
                "interpretation_limits": [
                    "30 returned records are 30 ZTF OIDs, not 30 confirmed unique physical sources.",
                    "The 150-row metadata selection is lexicographic and from one partition; it is not a sky-representative population.",
                    "No cross-OID physical-source grouping or merge is performed.",
                    "No HMJD transformation, color correction, epoch filter, production QC, feature generation, classifier inference, calibration, OOD, or astrophysical anomaly assessment is performed.",
                    "QC is descriptive only and not a production model-input policy.",
                ],
            }
            (output_dir / "ztf-dr24-park-30-oid-workbench-manifest.json").write_text(
                json.dumps(manifest, indent=2, sort_keys=True, allow_nan=False),
                encoding="utf-8",
            )
            browser.close()
    finally:
        server.should_exit = True
        thread.join(timeout=10)
