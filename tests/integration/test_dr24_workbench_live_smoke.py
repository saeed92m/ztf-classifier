"""Live browser smoke test for the DR24 Explorer in the Workbench."""

from __future__ import annotations

import json
import os
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
    278215200018105: {
        "epochs": 209, "flagged": 16, "clean": 193,
        "payload_sha256": "8fc2f95b389cb9cca129538f647dc83a1cf3b82cde37635a90f2d35ad9c596b8",
    },
    289111400013506: {
        "epochs": 24, "flagged": None, "clean": None,
        "payload_sha256": None,
    },
    347104300029855: {
        "epochs": 368, "flagged": None, "clean": None,
        "payload_sha256": None,
    },
    725113200004086: {
        "epochs": 1165, "flagged": None, "clean": None,
        "payload_sha256": None,
    },
}


@pytest.mark.skipif(
    os.getenv("ZTF_DR24_WORKBENCH_LIVE_TEST") != "1",
    reason="Set ZTF_DR24_WORKBENCH_LIVE_TEST=1 to run the live browser test.",
)
def test_workbench_dr24_explorer_renders_live_hats_epochs(tmp_path: Path) -> None:
    manifest = json.loads(
        Path("configs/samples/dr24_park_raw_candidate_sample_v0.1.json").read_text(
            encoding="utf-8"
        )
    )
    manifest_oids = {
        int(item["objectid"])
        for target in manifest["targets"]
        for item in target["oids"]
    }
    assert manifest_oids == set(EXPECTED)
    assert manifest["identity_policy"]["grouping_approved"] is False
    assert manifest["identity_policy"]["physical_identity_confirmed"] is False
    assert manifest["totals"]["candidate_external_ids"] == 5
    assert manifest["totals"]["oids"] == 7
    assert all(
        target["association_status"] == "SPATIAL_CANDIDATE_ONLY"
        for target in manifest["targets"]
    )
    assert len({target["candidate_external_id"] for target in manifest["targets"]}) == 5
    assert manifest["totals"]["catalog_epochs"] == sum(
        item["epochs"] for item in EXPECTED.values()
    )
    manifest_hashes = {
        int(item["objectid"]): item["independent_payload_hash"]
        for target in manifest["targets"]
        for item in target["oids"]
    }
    assert manifest_hashes == {
        objectid: expected["payload_sha256"]
        for objectid, expected in EXPECTED.items()
    }
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
                payload_hash = summary.rsplit("payload SHA-256 ", 1)[1]
                assert len(payload_hash) == 64
                assert all(character in "0123456789abcdef" for character in payload_hash)
                if expected["payload_sha256"] is not None:
                    assert payload_hash == expected["payload_sha256"]
                chart_points = page.locator("#dr24Chart circle").count()
                flagged_points = page.locator('#dr24Chart circle[fill="#e0a34a"]').count()
                clean_points = page.locator('#dr24Chart circle[fill="#55b8df"]').count()
                unknown_points = page.locator('#dr24Chart circle[fill="#9aa4b2"]').count()
                assert chart_points == expected["epochs"]
                if expected["flagged"] is not None:
                    assert flagged_points == expected["flagged"]
                    assert clean_points == expected["clean"]
                else:
                    assert flagged_points + clean_points + unknown_points == expected["epochs"]
                raw_qc = json.loads(page.locator("#dr24RawQc").inner_text())
                assert raw_qc["contract_version"] == "dr24-raw-qc-v0.1"
                assert raw_qc["total_epochs"] == expected["epochs"]
                assert raw_qc["catflags_bit15_set_count"] == flagged_points
                assert raw_qc["catflags_bit15_not_set_count"] == clean_points
                assert raw_qc["catflags_missing_count"] + raw_qc["catflags_invalid_count"] == unknown_points
                assert raw_qc["epochs_excluded"] == 0
                assert raw_qc["filtering_applied"] is False
                assert page.locator("#dr24EpochRows tr").count() == min(50, expected["epochs"])
                if objectid == next(iter(EXPECTED)):
                    assert not page.locator("#dr24ExportButton").is_disabled()
                    with page.expect_download(timeout=10000) as download_info:
                        page.locator("#dr24ExportButton").click()
                    download = download_info.value
                    assert download.suggested_filename == f"ztf-dr24-{objectid}-raw-export.json"
                    exported = json.loads(
                        Path(download.path()).read_text(encoding="utf-8")
                    )
                    assert exported["export_schema_version"] == "ztf-dr24-raw-export-v0.1"
                    assert exported["source_payload"]["records"][0]["objectid"] == objectid
                    assert exported["raw_qc"] == raw_qc
                    assert exported["raw_qc"]["epochs_excluded"] == 0

                provenance = json.loads(page.locator("#dr24Provenance").inner_text())
                assert provenance["source"] == "IRSA ZTF DR24 Lightcurves HATS"
                assert provenance["query"]["index"] == "objectid"
                assert provenance["returned_oids"] == [objectid]
                assert provenance["missing_oids"] == []

                results.append(
                    {
                        "objectid": objectid,
                        "epochs": expected["epochs"],
                        "chart_points": chart_points,
                        "flagged_points": flagged_points,
                        "clean_points": clean_points,
                        "unknown_flag_points": unknown_points,
                        "payload_sha256": payload_hash,
                        "payload_hash_validation": (
                            "MATCHED_INDEPENDENT_HATS"
                            if expected["payload_sha256"] is not None
                            else "FORMAT_ONLY_NO_INDEPENDENT_REFERENCE"
                        ),
                        "table_rows_rendered": min(50, expected["epochs"]),
                        "raw_qc": raw_qc,
                        "provenance_source": provenance["source"],
                    }
                )


            unknown_flags_oid = 987654323
            unknown_flags_payload = {
                "schema_version": "ztf-dr24-native-lightcurve-v1",
                "records": [
                    {
                        "objectid": unknown_flags_oid,
                        "filterid": 1,
                        "fieldid": 100,
                        "rcid": 4,
                        "catalog_nepochs": 1,
                        "payload_sha256": "unknown-flags-test",
                        "epochs": [
                            {
                                "hmjd": 60000.1,
                                "mag": 18.2,
                                "magerr": 0.03,
                                "clrcoeff": 0.1,
                                "catflags": None,
                            }
                        ],
                    }
                ],
                "provenance": {
                    "source": "IRSA ZTF DR24 Lightcurves HATS",
                    "query": {"index": "objectid", "objectids": [unknown_flags_oid]},
                    "returned_oids": [unknown_flags_oid],
                    "missing_oids": [],
                },
            }
            page.route(
                f"**/v1/dr24/objects/{unknown_flags_oid}/lightcurve",
                lambda route: route.fulfill(
                    status=200,
                    content_type="application/json",
                    body=json.dumps(unknown_flags_payload),
                ),
            )
            page.locator("#dr24ObjectId").fill(str(unknown_flags_oid))
            page.locator("#dr24LoadButton").click()
            page.wait_for_function(
                "() => document.querySelector('#dr24Status')?.textContent.includes('Raw DR24 response received')",
                timeout=10_000,
            )
            assert page.locator('#dr24Chart circle[fill="#9aa4b2"]').count() == 1
            assert page.locator('#dr24Chart circle[fill="#55b8df"]').count() == 0
            assert page.get_by_text(
                "Blue: bit 15 not set · amber: bit 15 set · gray: catflags unavailable"
            ).is_visible()
            null_qc = json.loads(page.locator("#dr24RawQc").inner_text())
            assert null_qc["catflags_missing_count"] == 1
            assert null_qc["catflags_valid_count"] == 0
            assert null_qc["epochs_excluded"] == 0
            assert null_qc["filtering_applied"] is False

            no_record_oid = 987654321
            no_record_payload = {
                "schema_version": "ztf-dr24-native-lightcurve-v1",
                "records": [],
                "provenance": {
                    "source": "IRSA ZTF DR24 Lightcurves HATS",
                    "query": {"index": "objectid", "objectids": [no_record_oid]},
                    "returned_oids": [],
                    "missing_oids": [no_record_oid],
                },
            }
            page.route(
                f"**/v1/dr24/objects/{no_record_oid}/lightcurve",
                lambda route: route.fulfill(
                    status=200,
                    content_type="application/json",
                    body=json.dumps(no_record_payload),
                ),
            )
            page.locator("#dr24ObjectId").fill(str(no_record_oid))
            page.locator("#dr24LoadButton").click()
            page.wait_for_function(
                "() => document.querySelector('#dr24Status')?.textContent.includes('Raw DR24 response received')",
                timeout=10_000,
            )
            assert "No catalog row returned for this OID. No alternate source was used." in page.locator("#dr24Summary").inner_text()
            assert "No DR24 row." in page.locator("#dr24EpochRows").inner_text()
            assert page.locator("#dr24Chart circle").count() == 0
            assert page.locator("#dr24ExportButton").is_disabled()
            no_record_provenance = json.loads(page.locator("#dr24Provenance").inner_text())
            assert no_record_provenance["missing_oids"] == [no_record_oid]

            failed_oid = 987654322
            page.route(
                f"**/v1/dr24/objects/{failed_oid}/lightcurve",
                lambda route: route.fulfill(
                    status=502,
                    content_type="application/json",
                    body=json.dumps(
                        {
                            "code": "dr24_acquisition_failed",
                            "message": "Simulated HATS outage. No alternate source was used.",
                        }
                    ),
                ),
            )
            page.locator("#dr24ObjectId").fill(str(failed_oid))
            page.locator("#dr24LoadButton").click()
            page.wait_for_function(
                "() => document.querySelector('#dr24Status')?.textContent.includes('DR24 acquisition failed (502)')",
                timeout=10_000,
            )
            assert "No fallback source was used." in page.locator("#dr24Status").inner_text()
            assert page.locator("#dr24ExportButton").is_disabled()
            assert "DR24 acquisition failed" in page.locator(".connection-state").inner_text()

            browser.close()

        report = {
            "schema_version": "ztf-dr24-workbench-live-smoke-v1",
            "status": "PASS",
            "code_revision": os.getenv("DR24_WORKBENCH_HEAD_SHA") or os.getenv("GITHUB_SHA"),
            "base_revision": os.getenv("DR24_WORKBENCH_BASE_SHA"),
            "workflow_revision": os.getenv("DR24_WORKBENCH_WORKFLOW_SHA") or os.getenv("GITHUB_SHA"),
            "workflow_run_id": os.getenv("GITHUB_RUN_ID"),
            "source": "IRSA ZTF DR24 Lightcurves HATS",
            "tested_view": "DR24 Explorer (raw)",
            "retrieved_at_utc": datetime.now(UTC).isoformat(),
            "objects": results,
            "total_epochs": sum(int(item["epochs"]) for item in results),
            "failure_contracts": {
                "missing_oid_ui": "PASS",
                "source_failure_ui": "PASS",
                "unknown_catflags_ui": "PASS",
                "unknown_catflags_not_clean": "PASS",
                "raw_qc_contract": "dr24-raw-qc-v0.1",
                "raw_json_export": "PASS",
                "export_disabled_on_missing_or_failure": "PASS",
                "fallback_used": False,
            },
            "limitations": [
                "This verifies the DR24 Explorer UI for seven pinned OIDs; four have independent HATS hash references and three have availability-only references.",
                "The UI displays at most 50 raw epoch rows per OID.",
                "No feature generation, inference, color correction, HMJD conversion, or quality filtering is performed.",
                "The seven OIDs represent five BTS-associated spatial candidates and are not seven confirmed astrophysical objects. This is not the 5–10 object application acceptance test or a 30–50 object Park demonstration.",
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
