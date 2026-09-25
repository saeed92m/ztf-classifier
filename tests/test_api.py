from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from fastapi.testclient import TestClient

from ztf_classifier.api.app import create_app
from ztf_classifier.api.config import ApiSettings
from ztf_classifier.application.schemas import PredictionResponse
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
        result = PredictionResult(
            raw_probabilities=probabilities,
            raw_predicted_class_indices=np.zeros(len(dataset), dtype=np.int64),
            raw_predicted_labels=tuple("AGN" for _ in dataset.index),
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
                    "runtime": {"python_version": "3.11", "platform": "test", "machine": "test"},
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
          "classes": ["AGN", "CEP", "DSCT", "EB", "LPV", "Periodic-Other", "QSO", "RR", "SLSN", "SNII", "SNIa", "SNIbc", "TDE", "CV/Nova", "YSO"],
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
