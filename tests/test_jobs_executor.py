from pathlib import Path

import numpy as np

from ztf_classifier.api.config import ApiSettings
from ztf_classifier.domain.observations import Observation, ObservationProvenance
from ztf_classifier.features.contracts import FeatureProvenance, FeatureResult
from ztf_classifier.jobs.executor import SourceBackedAnalysisExecutor
from ztf_classifier.jobs.store import JobRecord
from ztf_classifier.models.results import PredictionResult


class FakeObservationService:
    def get_observations(self, oid: str, *, survey: str = "ztf"):
        observation = Observation(
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
        return [observation], provenance


class FakeFeatureEngine:
    def compute(self, observations, *, backend: str = "native"):
        return FeatureResult(
            values={"feature_1": 1.0, "feature_2": 2.0},
            feature_schema_version="v0.2",
            provenance=FeatureProvenance(
                backend=backend,
                software_version="test",
                feature_schema_version="v0.2",
                parameters={},
                input_observation_sha256="a" * 64,
            ),
        )


class FakeApplicationService:
    def predict_dataframe(self, dataset, artifact_dir):
        result = PredictionResult(
            raw_probabilities=np.array([[1.0, *([0.0] * 14)]]),
            raw_predicted_class_indices=np.array([0], dtype=np.int64),
            raw_predicted_labels=("AGN",),
            calibration_status="available",
            conformal_status="unavailable",
            ood_status="unavailable",
            model_version="baseline_v0.2",
            artifact_schema_version="1.1",
            artifact_hash="b" * 64,
            feature_schema_hash="c" * 64,
            software_version="test",
        )
        return type(
            "Response",
            (),
            {
                "result": result,
                "model_version": "baseline_v0.2",
                "model_family": "XGBoost",
                "provenance": type(
                    "Provenance",
                    (),
                    {
                        "to_dict": lambda self: {
                            "dataset": {"path": "/secret"},
                            "feature_schema": {"source_path": "/secret"},
                            "model_configuration": {"path": "/secret"},
                            "calibration": {"source_path": "/secret"},
                        }
                    },
                )(),
            },
        )()


class FakeRegistryEntry:
    artifact_dir = Path("/models/baseline_v0.2")


class FakeRegistry:
    def __init__(self, root):
        self.root = root

    def get(self, model_version):
        assert model_version == "baseline_v0.2"
        return FakeRegistryEntry()


def test_source_backed_executor_runs_full_contract(monkeypatch):
    monkeypatch.setattr(
        "ztf_classifier.jobs.executor.FilesystemModelRegistry",
        FakeRegistry,
    )
    executor = SourceBackedAnalysisExecutor(
        ApiSettings(
            registry_dir=Path("/models"),
            default_model_version="baseline_v0.2",
        ),
        observation_service=FakeObservationService(),
        application_service=FakeApplicationService(),
        feature_engine=FakeFeatureEngine(),
    )
    job = JobRecord(
        job_id="job-1",
        oid="ZTF17test",
        survey="ztf",
        model_version=None,
        status="running",
        created_at="2026-09-25T00:00:00+00:00",
        updated_at="2026-09-25T00:00:00+00:00",
    )

    result = executor(job)

    assert result["oid"] == "ZTF17test"
    assert result["observation_count"] == 1
    assert result["feature_schema_version"] == "v0.2"
    assert result["prediction"]["predicted_class"] == "AGN"
    assert result["model_version"] == "baseline_v0.2"
    assert "/secret" not in str(result["model_provenance"])


def test_source_backed_executor_translates_expected_application_errors():
    from ztf_classifier.application.errors import ApplicationInferenceError

    class FailingApplicationService:
        def predict_dataframe(self, dataset, artifact_dir):
            raise ApplicationInferenceError("internal failure")

    executor = SourceBackedAnalysisExecutor(
        ApiSettings(registry_dir=Path("/models"), default_model_version="baseline_v0.2"),
        observation_service=FakeObservationService(),
        application_service=FailingApplicationService(),
        feature_engine=FakeFeatureEngine(),
    )
    job = JobRecord(
        job_id="job-2",
        oid="ZTF17test",
        survey="ztf",
        model_version="baseline_v0.2",
        status="running",
        created_at="2026-09-25T00:00:00+00:00",
        updated_at="2026-09-25T00:00:00+00:00",
    )

    import pytest
    from ztf_classifier.jobs.errors import AnalysisJobExecutionError

    with pytest.raises(AnalysisJobExecutionError):
        executor(job)
