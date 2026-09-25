from pathlib import Path

from fastapi.testclient import TestClient

from ztf_classifier.api.app import create_app
from ztf_classifier.api.config import ApiSettings
from ztf_classifier.jobs import JobStore
from ztf_classifier.reporting import ScientificReportService
from ztf_classifier.results import ScientificResultRecord, ScientificResultStore


def test_scientific_report_contains_persisted_analysis() -> None:
    record = ScientificResultRecord(
        result_id="result-1",
        job_id="job-1",
        oid="ZTF17report",
        survey="ztf",
        model_version="baseline_v0.2",
        schema_version="1.0",
        created_at="2026-09-25T12:00:00+00:00",
        payload={
            "prediction": {
                "predicted_class": "AGN",
                "probabilities": {"AGN": 0.9, "SN": 0.1},
            },
            "observations": [{"mjd": 60000.0}],
            "features": {"amplitude": 1.2},
            "diagnostics": {
                "calibration": "available",
                "conformal": "available",
                "ood": "available",
            },
            "observation_provenance": {"source": "ALeRCE"},
            "feature_provenance": {"backend": "native"},
            "model_provenance": {"model_version": "baseline_v0.2"},
            "warnings": [],
        },
    )

    report = ScientificReportService().render_markdown(record)

    assert "# ZTF Scientific Analysis Report" in report
    assert "ZTF17report" in report
    assert "Predicted class: AGN" in report
    assert "AGN: 0.90000000" in report
    assert "Observation source: ALeRCE" in report


def test_scientific_report_api_is_read_only(tmp_path: Path) -> None:
    settings = ApiSettings(result_store_path=tmp_path / "results.sqlite3")
    job = JobStore(settings.job_store_path).create(
        oid="ZTF17report",
        survey="ztf",
        model_version="baseline_v0.2",
    )
    store = ScientificResultStore(settings.result_store_path)
    stored = store.save(
        job_id=job.job_id,
        oid=job.oid,
        survey=job.survey,
        model_version="baseline_v0.2",
        payload={
            "prediction": {"predicted_class": "AGN"},
            "diagnostics": {},
        },
    )

    client = TestClient(create_app(settings))
    response = client.get(f"/v1/results/{stored.result_id}/report")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/markdown")
    assert "ZTF17report" in response.text
    assert response.headers["content-disposition"].startswith("attachment; filename=")
