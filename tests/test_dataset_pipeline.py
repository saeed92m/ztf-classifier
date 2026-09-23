"""Tests for production dataset-pipeline orchestration."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pandas as pd
import pytest

from ztf_classifier.dataset.artifact import sha256_file
from ztf_classifier.dataset.config import DatasetConfig
from ztf_classifier.dataset.features import (
    FEATURE_DATASET_METADATA_COLUMNS,
)
from ztf_classifier.dataset.manifest import REQUIRED_OBJECT_COLUMNS
from ztf_classifier.features.pipeline import V0_2_FEATURES
from ztf_classifier.io.detection_acquisition import (
    DetectionAcquisitionBackend,
    DetectionAcquisitionRequest,
    DetectionAcquisitionResult,
)
from ztf_classifier.io.object_acquisition import (
    ObjectAcquisitionBackend,
    ObjectAcquisitionResult,
)
from ztf_classifier.pipeline.dataset import DatasetPipeline


class FakeObjectBackend(ObjectAcquisitionBackend):
    """Deterministic in-memory object backend."""

    def __init__(self, frames: dict[str, pd.DataFrame]) -> None:
        self.frames = frames
        self.requests: list[str] = []

    def acquire(
        self,
        request,
    ) -> ObjectAcquisitionResult:
        self.requests.append(request.class_name)
        return ObjectAcquisitionResult(
            request=request,
            objects=(self.frames[request.class_name].copy(),),
        )


class FakeDetectionBackend(DetectionAcquisitionBackend):
    """Deterministic in-memory detection backend."""

    def __init__(self, detections: dict[str, pd.DataFrame]) -> None:
        self.detections = detections
        self.requests: list[str] = []

    def acquire(
        self,
        request: DetectionAcquisitionRequest,
    ) -> DetectionAcquisitionResult:
        self.requests.append(request.oid)

        return DetectionAcquisitionResult(
            request=request,
            detections=self.detections[request.oid].copy(),
            non_detections=pd.DataFrame(),
            cache_hit=True,
        )


def _object_frame(class_name: str, oid: str) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "oid": oid,
                "class": class_name,
                "classifier": "stamp_classifier",
                "probability": 0.9,
                "label_source": "alerce",
                "label_type": "classifier",
                "label_probability": 0.9,
                "classifier_version": "v1",
                "survey": "ztf",
            }
        ],
        columns=REQUIRED_OBJECT_COLUMNS,
    )


def _detections(oid: str) -> pd.DataFrame:
    """Create a minimal ALeRCE raw detection frame for ingestion tests."""

    mjd = [59000.0 + i for i in range(30)]
    mag = [19.0 + 0.01 * i for i in range(30)]
    magerr = [0.05] * 30

    return pd.DataFrame(
        {
            "oid": [oid] * 30,
            "mjd": mjd,
            "fid": [1] * 15 + [2] * 15,
            "magpsf": mag,
            "sigmapsf": magerr,
            "magpsf_corr": mag,
            "sigmapsf_corr": magerr,
            "sigmapsf_corr_ext": magerr,
            "ra": [100.0] * 30,
            "dec": [20.0] * 30,
            "dubious": [False] * 30,
            "corrected": [True] * 30,
        }
    )


@pytest.fixture()
def project(tmp_path: Path) -> Path:
    root = tmp_path / "project"
    root.mkdir()

    schema = root / "reports" / "tables"
    schema.mkdir(parents=True)

    pd.DataFrame(
        {
            "feature_order": [1],
            "feature": ["g_baseline_days"],
            "scientific_group": ["observation_quality"],
            "feature_set": ["v0.2"],
        }
    ).to_parquet(
        schema / "final_feature_set_v0.2.parquet",
        index=False,
    )

    subprocess.run(
        ["git", "init"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )

    subprocess.run(
        ["git", "config", "user.email", "pytest@example.com"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )

    subprocess.run(
        ["git", "config", "user.name", "Pytest"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )

    subprocess.run(
        ["git", "add", "."],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )

    subprocess.run(
        ["git", "commit", "-m", "test fixture baseline"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )

    return root


def test_pipeline_orchestrates_all_stages(project: Path) -> None:
    config = DatasetConfig(
        dataset_version="test-v1",
        survey="ztf",
        source="alerce",
        classifier="stamp_classifier",
        classes=("class_a", "class_b"),
        probability_min=0.9,
        samples_per_class=1,
    )

    object_backend = FakeObjectBackend(
        {
            "class_a": _object_frame("class_a", "ZTF_A"),
            "class_b": _object_frame("class_b", "ZTF_B"),
        }
    )

    detection_backend = FakeDetectionBackend(
        {
            "ZTF_A": _detections("ZTF_A"),
            "ZTF_B": _detections("ZTF_B"),
        }
    )

    output_dir = project / "data" / "processed" / "test"

    result = DatasetPipeline(
        config=config,
        object_acquisition_backend=object_backend,
        detection_acquisition_backend=detection_backend,
        project_root=project,
        output_dir=output_dir,
        feature_schema_path=(
            project
            / "reports"
            / "tables"
            / "final_feature_set_v0.2.parquet"
        ),
    ).run(
        command="pytest test_pipeline_orchestrates_all_stages"
    )

    assert object_backend.requests == [
        "class_a",
        "class_b",
    ]

    assert detection_backend.requests == [
        "ZTF_A",
        "ZTF_B",
    ]

    assert result.object_manifest.object_count == 2
    assert result.dataset.object_count == 2
    assert result.dataset.feature_count == 42

    assert result.artifact_validation.object_count == 2
    assert result.artifact_validation.feature_count == 42

    assert result.artifact.artifact_path.is_file()
    assert result.artifact.manifest_path.is_file()
    assert result.reproducibility_manifest.manifest_path.is_file()

    assert result.reproducibility_validation.dataset_sha256 == (
        sha256_file(result.artifact.artifact_path)
    )


def test_pipeline_writes_canonical_artifact_schema(project: Path) -> None:
    config = DatasetConfig(
        dataset_version="test-v1",
        survey="ztf",
        source="alerce",
        classifier="stamp_classifier",
        classes=("class_a",),
        probability_min=0.9,
        samples_per_class=1,
    )

    object_backend = FakeObjectBackend(
        {
            "class_a": _object_frame(
                "class_a",
                "ZTF_A",
            )
        }
    )

    detection_backend = FakeDetectionBackend(
        {
            "ZTF_A": _detections("ZTF_A")
        }
    )

    output_dir = project / "artifact"

    result = DatasetPipeline(
        config=config,
        object_acquisition_backend=object_backend,
        detection_acquisition_backend=detection_backend,
        project_root=project,
        output_dir=output_dir,
        feature_schema_path=(
            project
            / "reports"
            / "tables"
            / "final_feature_set_v0.2.parquet"
        ),
    ).run()

    data = pd.read_parquet(
        result.artifact.artifact_path
    )

    assert tuple(data.columns) == (
        FEATURE_DATASET_METADATA_COLUMNS
        + V0_2_FEATURES
    )

    manifest = json.loads(
        result.artifact.manifest_path.read_text(
            encoding="utf-8"
        )
    )

    assert manifest["object_count"] == 1
    assert manifest["feature_count"] == 42


def test_pipeline_rejects_multiple_object_payloads(
    project: Path,
) -> None:
    class BadObjectBackend(ObjectAcquisitionBackend):
        def acquire(self, request):
            frame = _object_frame(
                "class_a",
                "ZTF_A",
            )

            return ObjectAcquisitionResult(
                request=request,
                objects=(frame, frame),
            )

    config = DatasetConfig(
        dataset_version="test-v1",
        survey="ztf",
        source="alerce",
        classifier="stamp_classifier",
        classes=("class_a",),
        probability_min=0.9,
        samples_per_class=1,
    )

    detection_backend = FakeDetectionBackend(
        {
            "ZTF_A": _detections("ZTF_A")
        }
    )

    with pytest.raises(
        ValueError,
        match="exactly one",
    ):
        DatasetPipeline(
            config=config,
            object_acquisition_backend=BadObjectBackend(),
            detection_acquisition_backend=detection_backend,
            project_root=project,
            output_dir=project / "bad",
            feature_schema_path=(
                project
                / "reports"
                / "tables"
                / "final_feature_set_v0.2.parquet"
            ),
        ).run()


def test_pipeline_rejects_non_dataframe_object_payload(
    project: Path,
) -> None:
    class BadObjectBackend(ObjectAcquisitionBackend):
        def acquire(self, request):
            return ObjectAcquisitionResult(
                request=request,
                objects=("not-a-dataframe",),
            )

    config = DatasetConfig(
        dataset_version="test-v1",
        survey="ztf",
        source="alerce",
        classifier="stamp_classifier",
        classes=("class_a",),
        probability_min=0.9,
        samples_per_class=1,
    )

    detection_backend = FakeDetectionBackend(
        {
            "ZTF_A": _detections("ZTF_A")
        }
    )

    with pytest.raises(
        TypeError,
        match="pandas DataFrame",
    ):
        DatasetPipeline(
            config=config,
            object_acquisition_backend=BadObjectBackend(),
            detection_acquisition_backend=detection_backend,
            project_root=project,
            output_dir=project / "bad",
            feature_schema_path=(
                project
                / "reports"
                / "tables"
                / "final_feature_set_v0.2.parquet"
            ),
        ).run()
