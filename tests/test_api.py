from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from fastapi.testclient import TestClient

from ztf_classifier.api.app import create_app
from ztf_classifier.api.config import ApiSettings
from ztf_classifier.application.schemas import PredictionResponse
from ztf_classifier.domain.observations import (
    ObjectObservationSummary,
    Observation,
    ObservationProvenance,
)
from ztf_classifier.jobs import JobStore
from ztf_classifier.models.results import PredictionResult


class FakeApplicationService:
    def __init__(self) -> None:
        self.calls: list[tuple[pd.DataFrame, Path, str]] = []

    def predict_registered_dataframe(
        self,
        dataset: pd.DataFrame,
        registry_dir: Path,
        model_version: str,
    ) -> PredictionResponse:
        self.calls.append((dataset, registry_dir, model_version))
        probabilities = np.zeros((len(dataset), 15), dtype=np.float64)
        probabilities[:, 0] = 1.0
        raw_labels = tuple("AGN" for _ in dataset.index)
        result = PredictionResult(
            raw_probabilities=probabilities,
            raw_predicted_class_indices=np.zeros(len(dataset), dtype=np.int64),
            raw_predicted_labels=raw_labels,
            calibration_status="available",
            conformal_status="unavailable",
            ood_status="unavailable",
            model_version=model_version,
            artifact_schema_version="1.1",
            artifact_hash="a" * 64,
            feature_schema_hash="b" * 64,
            software_version="test",
        )

        class Provenance:
            def __init__(self, version: str) -> None:
                self.model_version = version
                self.model_family = "XGBoost"

            def to_dict(self) -> dict[str, object]:
                return {
                    "provenance_schema_version": "1.1",
                    "artifact_version": "test",
                    "model": {
                        "version": self.model_version,
                        "family": "XGBoost",
                    },
                    "dataset": {"version": "test", "path": "/secret"},
                    "feature_schema": {"version": "v0.2", "path": "/secret"},
                    "model_configuration": {"path": "/secret"},
                    "calibration": {
                        "method": "temperature",
                        "source_path": "/secret",
                    },
                    "source_control": {"git_commit": "test", "git_dirty": False},
                    "runtime": {
                        "python_version": "3.11",
                        "platform": "test",
                        "machine": "test",
                    },
                    "dependencies": {},
                    "software": {"version": "test"},
                }

        response = type(
            "Response",
            (),
            {
                "result": result,
                "model_version": model_version,
                "model_family": "XGBoost",
                "provenance": Provenance(model_version),
            },
        )()
        return response  # type: ignore[return-value]


def _make_registry(tmp_path: Path) -> None:
    artifact = tmp_path / "baseline_v0.2"
    artifact.mkdir()
    (artifact / "artifact_manifest.json").write_text(
        """{
          "artifact_schema_version": "1.1",
          "model_version": "baseline_v0.2",
          "model_family": "XGBoost",
          "feature_schema_version": "v0.2",
          "classes": ["AGN", "Blazar", "CEP", "CV/Nova", "DSCT", "E", "LPV", "Periodic-Other", "QSO", "RRL", "SLSN", "SNII", "SNIa", "SNIbc", "YSO"],
          "feature_count": 42,
          "dataset_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
          "feature_schema_source_sha256": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
          "files": {
            "model": {"path": "model.json", "sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"},
            "model_contract": {"path": "model_contract.json", "sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"},
            "feature_schema": {"path": "feature_schema.parquet", "sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"},
            "calibration": {"path": "calibration.json", "sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"},
            "provenance": {"path": "provenance.json", "sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"},
            "conformal": {"path": "conformal.json", "sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"},
            "ood": {"path": "ood.json", "sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"},
            "ood_model": {"path": "ood_model.joblib", "sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}
          }
        }""",
        encoding="utf-8",
    )


class FakeObservationService:
    def get_observations(
        self,
        oid: str,
        *,
        survey: str = "ztf",
    ) -> tuple[list[Observation], ObservationProvenance]:
        record = Observation(
            mjd=60000.5,
            fid=1,
            mag=19.2,
            magerr=0.08,
            mag_raw=19.3,
            magerr_raw=0.1,
            mag_corr=19.2,
            magerr_corr=0.08,
            photometry_source="corrected",
            ra=123.4,
            dec=-20.5,
            dubious=False,
            corrected=True,
        )
        provenance = ObservationProvenance(
            source="ALeRCE",
            survey=survey,
            cache_hit=True,
            diagnostics={"rows_input": 1, "rows_output": 1},
        )
        return [record], provenance

    def get_object_summary(
        self,
        oid: str,
        *,
        survey: str = "ztf",
    ) -> ObjectObservationSummary:
        _, provenance = self.get_observations(oid, survey=survey)
        return ObjectObservationSummary(
            oid=oid,
            observation_count=1,
            mjd_min=60000.5,
            mjd_max=60000.5,
            filters=(1,),
            ra=123.4,
            dec=-20.5,
            provenance=provenance,
        )


def test_object_observation_endpoints_use_normalized_contract() -> None:
    fake = FakeObservationService()
    client = TestClient(
        create_app(
            ApiSettings(),
            observation_service=fake,  # type: ignore[arg-type]
        )
    )

    summary = client.get("/v1/objects/ZTF17test")
    assert summary.status_code == 200
    assert summary.json()["object"]["observation_count"] == 1
    assert summary.json()["object"]["filters"] == [1]

    response = client.get("/v1/objects/ZTF17test/observations")
    assert response.status_code == 200
    payload = response.json()
    assert payload["oid"] == "ZTF17test"
    assert payload["observation_count"] == 1
    assert payload["observations"][0]["photometry_source"] == "corrected"
    assert payload["provenance"]["source"] == "ALeRCE"


def test_health_and_readiness(tmp_path: Path) -> None:
    _make_registry(tmp_path)
    client = TestClient(
        create_app(
            ApiSettings(
                registry_dir=tmp_path,
                default_model_version="baseline_v0.2",
            )
        )
    )

    assert client.get("/health").json()["status"] == "ok"
    ready = client.get("/ready")
    assert ready.status_code == 200
    assert ready.json()["model_version"] == "baseline_v0.2"


def test_model_metadata_does_not_expose_paths(tmp_path: Path) -> None:
    _make_registry(tmp_path)
    client = TestClient(
        create_app(
            ApiSettings(
                registry_dir=tmp_path,
                default_model_version="baseline_v0.2",
            )
        )
    )

    response = client.get("/v1/model")
    assert response.status_code == 200
    assert response.json()["feature_count"] == 42
    assert "artifact_dir" not in response.text


def test_prediction_uses_server_side_model_selection(
    tmp_path: Path,
) -> None:
    _make_registry(tmp_path)
    fake_service = FakeApplicationService()
    client = TestClient(
        create_app(
            ApiSettings(
                registry_dir=tmp_path,
                default_model_version="baseline_v0.2",
            ),
            application_service=fake_service,  # type: ignore[arg-type]
        )
    )

    response = client.post(
        "/v1/predict",
        json={
            "records": [{"oid": "ZTF17test", "feature_1": 1.0}],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["model_version"] == "baseline_v0.2"
    assert payload["predictions"][0]["predicted_class"] == "AGN"
    assert "/secret" not in response.text
    assert fake_service.calls[0][2] == "baseline_v0.2"


def test_unknown_model_returns_stable_error(tmp_path: Path) -> None:
    _make_registry(tmp_path)
    client = TestClient(
        create_app(
            ApiSettings(
                registry_dir=tmp_path,
                default_model_version="missing",
            )
        )
    )

    response = client.get("/v1/model", headers={"X-Request-ID": "req-123"})
    assert response.status_code == 404
    assert response.json() == {
        "code": "model_not_found",
        "message": "Model version is not registered: missing",
        "request_id": "req-123",
        "details": [],
    }


def test_invalid_request_has_stable_error(tmp_path: Path) -> None:
    _make_registry(tmp_path)
    client = TestClient(
        create_app(
            ApiSettings(
                registry_dir=tmp_path,
                default_model_version="baseline_v0.2",
            )
        )
    )

    response = client.post("/v1/predict", json={"records": []})
    assert response.status_code == 422
    assert response.json()["code"] == "request_validation_failed"


def test_openapi_exposes_versioned_contract(tmp_path: Path) -> None:
    _make_registry(tmp_path)
    client = TestClient(
        create_app(
            ApiSettings(
                registry_dir=tmp_path,
                default_model_version="baseline_v0.2",
            )
        )
    )

    schema = client.get("/openapi.json").json()
    assert "/v1/predict" in schema["paths"]
    assert "/v1/batch" in schema["paths"]
    assert "/v1/model" in schema["paths"]


def test_missing_model_configuration_has_stable_error() -> None:
    client = TestClient(create_app(ApiSettings()))

    response = client.get("/ready", headers={"X-Request-ID": "req-456"})
    assert response.status_code == 503
    assert response.json() == {
        "code": "model_not_configured",
        "message": "No model registry is configured for this API instance.",
        "request_id": "req-456",
        "details": [],
    }


class FakeAnalysisService:
    def __init__(self) -> None:
        from ztf_classifier.application.service import ApplicationService

        self._service = ApplicationService()

    def predict_dataframe(self, dataset, artifact_dir):
        return self._service.predict_dataframe(dataset, artifact_dir)


def test_object_analysis_contract_uses_shared_executor(tmp_path: Path) -> None:
    class FakeExecutor:
        def execute(
            self,
            *,
            oid: str,
            survey: str,
            model_version: str | None,
            feature_backend: str = "native",
            feature_parameters: dict | None = None,
        ):
            assert oid == "ZTF17test"
            assert survey == "ztf"
            assert model_version is None
            assert feature_backend == "native"
            assert feature_parameters == {}
            return {
                "oid": oid,
                "survey": survey,
                "observation_count": 1,
                "observations": [{"mjd": 60000.5}],
                "features": {"feature_1": 1.0},
                "feature_schema_version": "v0.2",
                "feature_backend": "native",
                "feature_parameters": {},
                "feature_provenance": {},
                "prediction": {
                    "predicted_class": "AGN",
                    "predicted_class_index": 0,
                    "probabilities": {"AGN": 1.0},
                    "conformal": [],
                    "ood": None,
                },
                "model_version": "baseline_v0.2",
                "model_family": "XGBoost",
                "diagnostics": {
                    "calibration": "available",
                    "conformal": "unavailable",
                    "ood": "unavailable",
                },
                "model_provenance": {},
                "observation_provenance": {},
                "warnings": [],
            }

    settings = ApiSettings(
        registry_dir=tmp_path,
        default_model_version="baseline_v0.2",
    )
    client = TestClient(
        create_app(
            settings,
            observation_service=FakeObservationService(),
            analysis_executor=FakeExecutor(),  # type: ignore[arg-type]
        )
    )

    response = client.post(
        "/v1/objects/ZTF17test/analysis",
        json={"survey": "ztf"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["oid"] == "ZTF17test"
    assert payload["prediction"]["predicted_class"] == "AGN"


def test_persistent_analysis_job_lifecycle(tmp_path: Path) -> None:
    settings = ApiSettings(job_store_path=tmp_path / "jobs.sqlite3")
    client = TestClient(create_app(settings))

    submitted = client.post(
        "/v1/objects/ZTF17job/jobs",
        json={"survey": "ztf"},
    )
    assert submitted.status_code == 202
    payload = submitted.json()
    assert payload["status"] == "queued"
    assert payload["oid"] == "ZTF17job"

    fetched = client.get(f"/v1/jobs/{payload['job_id']}")
    assert fetched.status_code == 200
    assert fetched.json()["status"] == "queued"

    missing = client.get("/v1/jobs/not-found")
    assert missing.status_code == 404
    assert missing.json()["code"] == "job_not_found"


def test_durable_job_result_retrieval_uses_scientific_result_store(
    tmp_path: Path,
) -> None:
    from ztf_classifier.jobs import JobStore
    from ztf_classifier.results import ScientificResultStore

    settings = ApiSettings(
        job_store_path=tmp_path / "jobs.sqlite3",
        result_store_path=tmp_path / "results.sqlite3",
    )
    job_store = JobStore(settings.job_store_path)
    result_store = ScientificResultStore(settings.result_store_path)
    job = job_store.create(
        oid="ZTF17result",
        survey="ztf",
        model_version="baseline_v0.2",
    )
    scientific_payload = {
        "schema_version": "1.0",
        "oid": "ZTF17result",
        "prediction": {"predicted_class": "AGN"},
    }
    stored = result_store.save(
        job_id=job.job_id,
        oid=job.oid,
        survey=job.survey,
        model_version="baseline_v0.2",
        payload=scientific_payload,
    )
    running = job_store.claim_next()
    assert running is not None
    assert running.job_id == job.job_id
    job_store.transition(
        job.job_id,
        status="succeeded",
        result={"result_id": stored.result_id, "schema_version": "1.0"},
        scientific_result_id=stored.result_id,
    )

    client = TestClient(create_app(settings))
    response = client.get(f"/v1/jobs/{job.job_id}/result")

    assert response.status_code == 200
    assert response.json()["result_id"] == stored.result_id
    assert response.json()["payload"] == scientific_payload


def test_durable_job_result_is_not_ready_for_queued_job(tmp_path: Path) -> None:
    from ztf_classifier.jobs import JobStore

    settings = ApiSettings(
        job_store_path=tmp_path / "jobs.sqlite3",
        result_store_path=tmp_path / "results.sqlite3",
    )
    job_store = JobStore(settings.job_store_path)
    job = job_store.create(
        oid="ZTF17queued",
        survey="ztf",
        model_version="baseline_v0.2",
    )

    client = TestClient(create_app(settings))
    response = client.get(f"/v1/jobs/{job.job_id}/result")

    assert response.status_code == 409
    assert response.json()["code"] == "job_result_not_ready"


def test_latest_object_scientific_result_retrieval(tmp_path: Path) -> None:
    from ztf_classifier.jobs import JobStore
    from ztf_classifier.results import ScientificResultStore

    settings = ApiSettings(
        job_store_path=tmp_path / "jobs.sqlite3",
        result_store_path=tmp_path / "results.sqlite3",
    )
    job_store = JobStore(settings.job_store_path)
    result_store = ScientificResultStore(settings.result_store_path)
    job = job_store.create(
        oid="ZTF17latest",
        survey="ztf",
        model_version="baseline_v0.2",
    )
    stored = result_store.save(
        job_id=job.job_id,
        oid=job.oid,
        survey=job.survey,
        model_version="baseline_v0.2",
        payload={"schema_version": "1.0", "prediction": {"predicted_class": "AGN"}},
    )

    client = TestClient(create_app(settings))
    response = client.get("/v1/objects/ZTF17latest/results/latest?survey=ztf")

    assert response.status_code == 200
    assert response.json()["result_id"] == stored.result_id


def test_latest_object_scientific_result_missing_is_stable_not_found(
    tmp_path: Path,
) -> None:
    settings = ApiSettings(result_store_path=tmp_path / "results.sqlite3")
    client = TestClient(create_app(settings))

    response = client.get("/v1/objects/ZTF17missing/results/latest?survey=ztf")

    assert response.status_code == 404
    assert response.json()["code"] == "scientific_result_not_found"


def test_scientific_result_id_retrieval_has_stable_not_found_error(
    tmp_path: Path,
) -> None:
    settings = ApiSettings(
        result_store_path=tmp_path / "results.sqlite3",
    )
    client = TestClient(create_app(settings))

    response = client.get("/v1/results/missing")

    assert response.status_code == 404
    assert response.json()["code"] == "scientific_result_not_found"


def test_scientific_catalog_query_and_csv_export(tmp_path: Path) -> None:
    from ztf_classifier.jobs import JobStore
    from ztf_classifier.results import ScientificResultStore

    settings = ApiSettings(
        job_store_path=tmp_path / "jobs.sqlite3",
        result_store_path=tmp_path / "results.sqlite3",
    )
    job_store = JobStore(settings.job_store_path)
    result_store = ScientificResultStore(settings.result_store_path)
    job = job_store.create(
        oid="ZTF17catalog",
        survey="ztf",
        model_version="baseline_v0.2",
    )
    result_store.save(
        job_id=job.job_id,
        oid=job.oid,
        survey=job.survey,
        model_version="baseline_v0.2",
        payload={"schema_version": "1.0", "prediction": {"predicted_class": "AGN"}},
    )

    client = TestClient(create_app(settings))
    response = client.get(
        "/v1/catalog/results",
        params={"survey": "ztf", "model_version": "baseline_v0.2"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["oid"] == "ZTF17catalog"
    assert body["has_next"] is False

    exported = client.get("/v1/catalog/results.csv", params={"survey": "ztf"})
    assert exported.status_code == 200
    assert exported.headers["content-type"].startswith("text/csv")
    assert "ZTF17catalog" in exported.text
    assert "attachment; filename=" in exported.headers["content-disposition"]


def test_scientific_catalog_rejects_invalid_limit(tmp_path: Path) -> None:
    settings = ApiSettings(result_store_path=tmp_path / "results.sqlite3")
    client = TestClient(create_app(settings))

    response = client.get("/v1/catalog/results", params={"limit": 1001})

    assert response.status_code == 422
    assert response.json()["code"] == "request_validation_failed"


def test_durable_job_listing_endpoint(tmp_path: Path) -> None:
    settings = ApiSettings(job_store_path=tmp_path / "jobs.sqlite3")
    job_store = JobStore(settings.job_store_path)
    job_store.create(
        oid="ZTF17listed",
        survey="ztf",
        model_version="baseline_v0.2",
    )

    client = TestClient(create_app(settings))
    response = client.get("/v1/jobs", params={"status": "queued"})

    assert response.status_code == 200
    assert response.json()["items"][0]["oid"] == "ZTF17listed"


def test_durable_job_listing_rejects_invalid_status(tmp_path: Path) -> None:
    settings = ApiSettings(job_store_path=tmp_path / "jobs.sqlite3")
    client = TestClient(create_app(settings))

    response = client.get("/v1/jobs", params={"status": "invalid"})

    assert response.status_code == 422
    assert response.json()["code"] == "job_query_invalid"


def test_feature_backend_discovery_endpoint() -> None:
    client = TestClient(create_app())

    response = client.get("/v1/features/backends")

    assert response.status_code == 200
    assert response.json()["backends"][0] == {
        "name": "native",
        "software_version": "ztf-classifier-native-v0.2",
        "feature_schema_version": "v0.2",
    }


def test_object_analysis_rejects_unknown_feature_backend(tmp_path: Path) -> None:
    settings = ApiSettings()
    client = TestClient(create_app(settings))

    response = client.post(
        "/v1/objects/ZTF17test/analysis",
        json={"survey": "ztf", "feature_backend": "missing"},
    )

    assert response.status_code == 404
    assert response.json()["code"] == "feature_backend_not_found"


def test_optional_api_key_protects_versioned_endpoints(tmp_path: Path) -> None:
    settings = ApiSettings(
        api_key="secret-key", result_store_path=tmp_path / "results.sqlite3"
    )
    client = TestClient(create_app(settings))

    unauthorized = client.get("/v1/results/missing", headers={"X-Request-ID": "req-1"})
    assert unauthorized.status_code == 401
    assert unauthorized.json()["code"] == "authentication_required"
    assert unauthorized.headers["X-Request-ID"] == "req-1"

    authorized = client.get(
        "/v1/results/missing",
        headers={"Authorization": "Bearer secret-key"},
    )
    assert authorized.status_code == 404
    assert authorized.json()["code"] == "scientific_result_not_found"


def test_health_remains_public_when_api_key_is_configured() -> None:
    client = TestClient(create_app(ApiSettings(api_key="secret-key")))

    response = client.get("/health")

    assert response.status_code == 200
    assert response.headers["X-Request-ID"]


def test_scientific_validation_dashboard_is_fail_closed(tmp_path: Path) -> None:
    client = TestClient(
        create_app(
            ApiSettings(
                scientific_registry_dir=Path("configs/benchmarks"),
                scientific_evidence_dir=tmp_path / "evidence",
            )
        )
    )
    response = client.get("/v1/scientific-validation")
    assert response.status_code == 200
    payload = response.json()
    assert payload["release_blocking"] is True
    assert payload["status"] == "NOT_VERIFIED"
    assert len(payload["benchmarks"]) == 5
    assert payload["blockers"]
