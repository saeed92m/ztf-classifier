import pandas as pd

from ztf_classifier.dataset.config import DatasetConfig
from ztf_classifier.dataset.features import (
    FEATURE_DATASET_METADATA_COLUMNS,
    FeatureDatasetBuilder,
)
from ztf_classifier.dataset.manifest import ObjectManifest
from ztf_classifier.features.pipeline import V0_2_FEATURES
from ztf_classifier.io.detection_acquisition import (
    DetectionAcquisitionBackend,
    DetectionAcquisitionResult,
)


class FakeDetectionBackend(DetectionAcquisitionBackend):
    def __init__(self, detections: pd.DataFrame) -> None:
        self.detections = detections
        self.requests = []

    def acquire(self, request):
        self.requests.append(request)

        return DetectionAcquisitionResult(
            request=request,
            detections=self.detections,
            non_detections=pd.DataFrame(),
            cache_hit=True,
        )


def make_manifest() -> ObjectManifest:
    config = DatasetConfig(
        dataset_version="benchmark_v0.2",
        survey="ZTF",
        source="ALeRCE",
        classifier="lc_classifier",
        classes=("QSO",),
        probability_min=0.50,
        samples_per_class=1,
    )

    objects = pd.DataFrame(
        {
            "oid": ["ZTF_TEST"],
            "class": ["QSO"],
            "classifier": ["lc_classifier"],
            "probability": [0.501],
            "label_source": ["ALeRCE"],
            "label_type": ["benchmark"],
            "label_probability": [0.501],
            "classifier_version": [
                "hierarchical_random_forest_1.0.0"
            ],
            "survey": ["ZTF"],
        }
    )

    return ObjectManifest(
        objects=objects,
        dataset_version=config.dataset_version,
        probability_min=config.probability_min,
        samples_per_class=config.samples_per_class,
    )


def make_detections() -> pd.DataFrame:
    rows = []

    for fid in (1, 2):
        for index in range(30):
            rows.append(
                {
                    "mjd": 59000.0 + index,
                    "fid": fid,
                    "magpsf": 19.0 + 0.01 * index,
                    "sigmapsf": 0.05,
                    "magpsf_corr": 19.0 + 0.01 * index,
                    "sigmapsf_corr_ext": 0.05,
                    "ra": 10.0,
                    "dec": 20.0,
                    "dubious": False,
                    "corrected": True,
                }
            )

    return pd.DataFrame(rows)


def test_feature_dataset_has_canonical_schema() -> None:
    backend = FakeDetectionBackend(make_detections())

    dataset = FeatureDatasetBuilder(
        manifest=make_manifest(),
        acquisition_backend=backend,
    ).build()

    assert dataset.object_count == 1
    assert dataset.feature_count == 42

    assert tuple(dataset.data.columns) == (
        FEATURE_DATASET_METADATA_COLUMNS
        + V0_2_FEATURES
    )


def test_feature_dataset_preserves_manifest_metadata() -> None:
    backend = FakeDetectionBackend(make_detections())

    dataset = FeatureDatasetBuilder(
        manifest=make_manifest(),
        acquisition_backend=backend,
    ).build()

    row = dataset.data.iloc[0]

    assert row["oid"] == "ZTF_TEST"
    assert row["class"] == "QSO"
    assert row["probability"] == 0.501
    assert row["label_probability"] == 0.501
    assert row["classifier"] == "lc_classifier"
    assert row["survey"] == "ZTF"


def test_feature_dataset_uses_manifest_oid_and_survey() -> None:
    backend = FakeDetectionBackend(make_detections())

    FeatureDatasetBuilder(
        manifest=make_manifest(),
        acquisition_backend=backend,
    ).build()

    assert len(backend.requests) == 1
    assert backend.requests[0].oid == "ZTF_TEST"
    assert backend.requests[0].survey == "ZTF"
