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

# First 30 OIDs by ascending OID from the pinned 150-row, one-partition
# DR24 Objects Table metadata sample with ngoodobsrel >= 75.
# This is a curated engineering demonstration sample, not a survey-representative
# sample and not a scientific membership or epoch-quality rule.
GUIDED_30_OIDS = (
    199109100000004,
    199109100000005,
    199109100000007,
    199109100000010,
    199109100000011,
    199109100000013,
    199109100000018,
    199109100000029,
    199109100000044,
    199109100000046,
    199109100000048,
    199109100000053,
    199109100000058,
    199109100000062,
    199109100000063,
    199109100000065,
    199109100000070,
    199109100000085,
    199109100000089,
    199109100000096,
    199109100000106,
    199109100000108,
    199109100000112,
    199109100000115,
    199109100000117,
    199109100000122,
    199109100000134,
    199109100000137,
    199109100000140,
    199109100000145,
)
CATALOG_RESPONSE_SHA256 = (
    "4cc5827cd077252ceca99af587e4091e5cb5b4e7ca00a45d0d3a07bbfaaa52c7"
)
CATALOG_ARTIFACT_SHA256 = (
    "31d0609322e6c5671d485a20c970ef3c4760844c3d38a28769ad8e30d1928058"
)


@pytest.mark.skipif(
    os.getenv("ZTF_DR24_PARK_30OID_LIVE_TEST") != "1",
    reason="Set ZTF_DR24_PARK_30OID_LIVE_TEST=1 to retrieve the fixed 30-OID guided sample.",
)
def test_guided_30_oid_sample_retrieves_in_three_bounded_batches(tmp_path: Path) -> None:
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
    batch_size = 10
    batches = [
        GUIDED_30_OIDS[index : index + batch_size]
        for index in range(0, len(GUIDED_30_OIDS), batch_size)
    ]
    assert len(batches) == 3
    assert all(len(batch) <= 10 for batch in batches)

    all_records: dict[int, dict] = {}
    batch_evidence = []
    for batch_index, batch in enumerate(batches, start=1):
        response = client.post(
            "/v1/dr24/lightcurves",
            json={"objectids": list(batch)},
        )
        assert response.status_code == 200, response.text
        payload = response.json()
        records = {
            int(record["objectid"]): record
            for record in payload.get("records", [])
        }
        provenance = payload.get("provenance", {})
        missing = sorted(set(batch) - set(records))
        unexpected = sorted(set(records) - set(batch))
        assert not missing, f"Batch {batch_index} missing OIDs: {missing}"
        assert not unexpected, f"Batch {batch_index} returned unrequested OIDs: {unexpected}"
        assert provenance.get("requested_oids") == list(batch)
        assert set(provenance.get("returned_oids", [])) == set(batch)
        assert provenance.get("missing_oids") == []

        batch_records = []
        for oid in batch:
            record = records[oid]
            epoch_rows = record.get("epochs", [])
            assert record.get("catalog_nepochs") == len(epoch_rows), oid
            digest = record.get("payload_sha256")
            assert isinstance(digest, str) and len(digest) == 64, oid
            assert oid not in all_records
            all_records[oid] = record
            batch_records.append(
                {
                    "objectid": oid,
                    "filterid": record.get("filterid"),
                    "fieldid": record.get("fieldid"),
                    "rcid": record.get("rcid"),
                    "objra": record.get("objra"),
                    "objdec": record.get("objdec"),
                    "catalog_nepochs": record.get("catalog_nepochs"),
                    "returned_epoch_rows": len(epoch_rows),
                    "payload_sha256": digest,
                }
            )
        batch_evidence.append(
            {
                "batch_index": batch_index,
                "requested_oids": list(batch),
                "returned_oids": sorted(records),
                "missing_oids": [],
                "retrieved_at_utc": provenance.get("retrieved_at_utc"),
                "records": batch_records,
            }
        )

    assert set(all_records) == set(GUIDED_30_OIDS)
    total_epochs = sum(len(record.get("epochs", [])) for record in all_records.values())
    output_dir = Path("park-demo-evidence")
    output_dir.mkdir(parents=True, exist_ok=True)
    raw_path = output_dir / "ztf-dr24-park-30-oid-guided-raw-payload.json"
    raw_path.write_text(
        json.dumps(
            {
                "source": "IRSA ZTF DR24 Lightcurves HATS",
                "source_release": "DR24",
                "records": [
                    all_records[oid]
                    for oid in GUIDED_30_OIDS
                ],
            },
            indent=2,
            sort_keys=True,
            allow_nan=False,
        ),
        encoding="utf-8",
    )
    manifest = {
        "schema_version": "ztf-dr24-park-30-oid-guided-manifest-v1",
        "validation_status": "PASS",
        "created_at_utc": datetime.now(UTC).isoformat(),
        "source": "IRSA ZTF DR24 Lightcurves HATS",
        "source_release": "DR24",
        "source_uri": "s3://ipac-irsa-ztf/ztf/enhanced/dr24/lc/hats",
        "catalog_snapshot_sha256": CATALOG_RESPONSE_SHA256,
        "catalog_artifact_zip_sha256": CATALOG_ARTIFACT_SHA256,
        "catalog_snapshot_rows": 150,
        "catalog_snapshot_partition_count": 1,
        "catalog_snapshot_sky_representative": False,
        "selection_rule": (
            "First 30 ascending OIDs with ngoodobsrel >= 75 from the pinned "
            "150-row metadata snapshot. This is an engineering sample-selection "
            "rule only; it is not a scientific membership or epoch QC rule."
        ),
        "counting_unit": "OID records; not confirmed physical astrophysical sources",
        "requested_oid_count": len(GUIDED_30_OIDS),
        "returned_oid_count": len(all_records),
        "missing_oid_count": len(set(GUIDED_30_OIDS) - set(all_records)),
        "total_raw_epoch_rows": total_epochs,
        "batch_count": len(batches),
        "maximum_oids_per_request": batch_size,
        "batches": batch_evidence,
        "output_file": raw_path.name,
        "limitations": [
            "The metadata sample is lexicographically selected from one HATS partition; it is not representative of the full ZTF sky or population.",
            "ngoodobsrel is a catalog field and is not interchangeable with Lightcurves HATS nepochs.",
            "The sample consists of 30 OID records, not 30 confirmed unique physical sources.",
            "No cross-OID grouping, time conversion, color correction, epoch filtering, production QC, feature generation, model inference, calibration, OOD prediction, or astrophysical anomaly analysis is performed.",
            "Payload hashes are canonical adapter payload hashes, not provider Parquet-file hashes.",
        ],
    }
    manifest_path = output_dir / "ztf-dr24-park-30-oid-guided-manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True, allow_nan=False),
        encoding="utf-8",
    )
