from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from ztf_classifier.api.app import create_app
from ztf_classifier.api.config import ApiSettings
from ztf_classifier.application.observations import ObservationService
from ztf_classifier.io.dr24_lightcurve import DR24LightcurveBackend


# Fixed engineering sample drawn from the 2026-11-09, 150-row DR24 Objects
# Table HATS snapshot. The source snapshot is lexicographically selected from
# one partition and is not a sky-representative scientific sample.
SAMPLE = (
    {"oid": 199109100000000, "ra": 3.9569313, "dec": -29.5634754, "ngoodobsrel": 7},
    {"oid": 199109100000014, "ra": 4.5206852, "dec": -29.5524481, "ngoodobsrel": 8},
    {"oid": 199109100000033, "ra": 4.4284818, "dec": -29.5611962, "ngoodobsrel": 7},
    {"oid": 199109100000049, "ra": 4.4885644, "dec": -29.5643897, "ngoodobsrel": 1},
    {"oid": 199109100000063, "ra": 4.7256528, "dec": -29.5625810, "ngoodobsrel": 114},
    {"oid": 199109100000085, "ra": 4.0320271, "dec": -29.5904744, "ngoodobsrel": 114},
    {"oid": 199109100000096, "ra": 4.7694331, "dec": -29.5724818, "ngoodobsrel": 119},
    {"oid": 199109100000114, "ra": 4.0473178, "dec": -29.5980514, "ngoodobsrel": 1},
    {"oid": 199109100000128, "ra": 4.7185657, "dec": -29.5826487, "ngoodobsrel": 24},
    {"oid": 199109100000148, "ra": 4.7657855, "dec": -29.5874696, "ngoodobsrel": 119},
)
CATALOG_RESPONSE_SHA256 = (
    "4cc5827cd077252ce99af587e4091e5cb5b4e7ca00a45d0d3a07bbfaaa52c7"
)
CATALOG_ARTIFACT_SHA256 = (
    "31d0609322e6c5671d485a20c970ef3c4760844c3d38a28769ad8e30d1928058"
)


@pytest.mark.skipif(
    os.getenv("ZTF_DR24_PARK_SAMPLE_LIVE_TEST") != "1",
    reason="Set ZTF_DR24_PARK_SAMPLE_LIVE_TEST=1 to query the fixed 10-OID DR24 sample.",
)
def test_park_sample_retrieves_and_repeats_ten_dr24_oids(tmp_path: Path) -> None:
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
    requested = [row["oid"] for row in SAMPLE]

    first_response = client.post(
        "/v1/dr24/lightcurves",
        json={"objectids": requested},
    )
    assert first_response.status_code == 200, first_response.text
    first_payload = first_response.json()

    # Run a second, independent API request against the frozen DR24 release.
    second_response = client.post(
        "/v1/dr24/lightcurves",
        json={"objectids": requested},
    )
    assert second_response.status_code == 200, second_response.text
    second_payload = second_response.json()

    first_records = {
        record["objectid"]: record for record in first_payload.get("records", [])
    }
    second_records = {
        record["objectid"]: record for record in second_payload.get("records", [])
    }
    first_provenance = first_payload.get("provenance", {})
    second_provenance = second_payload.get("provenance", {})
    missing = sorted(set(requested) - set(first_records))
    unexpected = sorted(set(first_records) - set(requested))

    manifest = {
        "schema_version": "ztf-dr24-park-live-sample-manifest-v1",
        "validation_status": "RETRIEVED_PENDING_ASSERTIONS",
        "created_at_utc": datetime.now(UTC).isoformat(),
        "sample_definition": {
            "unit": "ZTF objectid / OID record",
            "requested_oid_count": len(requested),
            "selection": "10 fixed positive-ngoodobsrel OIDs spaced deterministically across a 150-row lexicographic, single-partition metadata snapshot",
            "catalog_snapshot_sha256": CATALOG_RESPONSE_SHA256,
            "catalog_artifact_zip_sha256": CATALOG_ARTIFACT_SHA256,
            "catalog_snapshot_row_count": 150,
            "catalog_snapshot_is_sky_representative": False,
            "physical_source_grouping_performed": False,
        },
        "source": {
            "name": first_provenance.get("source"),
            "release": first_provenance.get("release"),
            "catalog_uri": first_provenance.get("catalog_uri"),
            "retrieval_timestamp_first": first_provenance.get("retrieved_at_utc"),
            "retrieval_timestamp_second": second_provenance.get("retrieved_at_utc"),
            "requested_oids": first_provenance.get("requested_oids"),
            "returned_oids": first_provenance.get("returned_oids"),
            "missing_oids": first_provenance.get("missing_oids"),
        },
        "metadata_reference": list(SAMPLE),
        "first_request": [
            {
                "objectid": oid,
                "filterid": record.get("filterid"),
                "fieldid": record.get("fieldid"),
                "rcid": record.get("rcid"),
                "objra": record.get("objra"),
                "objdec": record.get("objdec"),
                "catalog_nepochs": record.get("catalog_nepochs"),
                "returned_epoch_rows": len(record.get("epochs", [])),
                "payload_sha256": record.get("payload_sha256"),
            }
            for oid, record in sorted(first_records.items())
        ],
        "repeatability": {
            "same_returned_oid_set": set(first_records) == set(second_records),
            "same_epoch_count_and_payload_hash": {
                str(oid): (
                    oid in second_records
                    and len(first_records[oid].get("epochs", []))
                    == len(second_records[oid].get("epochs", []))
                    and first_records[oid].get("payload_sha256")
                    == second_records[oid].get("payload_sha256")
                )
                for oid in first_records
            },
        },
        "checks": {
            "http_status_first": first_response.status_code,
            "http_status_second": second_response.status_code,
            "all_oids_returned": not missing and not unexpected,
            "epoch_count_matches_catalog": all(
                len(record.get("epochs", [])) == record.get("catalog_nepochs")
                for record in first_records.values()
            ),
            "payload_hash_is_sha256": all(
                isinstance(record.get("payload_sha256"), str)
                and len(record["payload_sha256"]) == 64
                for record in first_records.values()
            ),
        },
        "interpretation_limits": [
            "This is an OID-level engineering sample, not ten confirmed astrophysical sources.",
            "The 150-row metadata snapshot is lexicographic and comes from one HATS partition; it is not a representative survey sample.",
            "The Objects Table ngoodobsrel field is not treated as the lightcurve nepochs count.",
            "No cross-OID grouping, color correction, HMJD conversion, epoch filtering, feature generation, classification, calibration, OOD inference, or scientific anomaly claim is performed.",
            "The returned payload hashes are canonical JSON hashes produced by the application adapter; they are not hashes of the provider's underlying Parquet files.",
            "QC remains diagnostic and is not an approved model-input policy.",
        ],
    }

    out_dir = Path("park-demo-evidence")
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "ztf-dr24-park-10-oid-raw-payload.json").write_text(
        json.dumps(first_payload, indent=2, sort_keys=True, allow_nan=False),
        encoding="utf-8",
    )
    manifest_path = out_dir / "ztf-dr24-park-10-oid-manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True, allow_nan=False),
        encoding="utf-8",
    )

    assert first_provenance.get("source") == "IRSA ZTF DR24 Lightcurves HATS"
    assert first_provenance.get("requested_oids") == requested
    assert not missing, f"Missing requested OIDs: {missing}"
    assert not unexpected, f"Unrequested OIDs returned: {unexpected}"
    assert set(first_records) == set(requested)
    assert set(second_records) == set(requested)

    for oid in requested:
        record = first_records[oid]
        repeat = second_records[oid]
        assert record["catalog_nepochs"] == len(record["epochs"]), oid
        assert len(record["payload_sha256"]) == 64, oid
        assert len(record["epochs"]) == len(repeat["epochs"]), oid
        assert record["payload_sha256"] == repeat["payload_sha256"], oid

    manifest["validation_status"] = "PASS"
    manifest["checks"]["all_oids_returned"] = True
    manifest["checks"]["epoch_count_matches_catalog"] = True
    manifest["checks"]["payload_hash_is_sha256"] = True
    manifest["checks"]["repeat_request_hashes_identical"] = True
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True, allow_nan=False),
        encoding="utf-8",
    )
