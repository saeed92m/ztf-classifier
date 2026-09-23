from pathlib import Path

import numpy as np
import pandas as pd

from ztf_classifier.models.artifact import ModelArtifact
from ztf_classifier.models.artifact_io import ModelArtifactLoader, ModelArtifactWriter
from ztf_classifier.models.xgboost import XGBoostTrainingEngine

DATASET_PATH = Path(
    "data/processed/benchmark_v0.2/features.parquet"
)

FEATURE_SCHEMA_PATH = Path(
    "reports/tables/final_feature_set_v0.2.parquet"
)


def _build_artifact() -> tuple[
    ModelArtifact,
    pd.DataFrame,
]:
    dataset = pd.read_parquet(DATASET_PATH)

    engine = XGBoostTrainingEngine(
        feature_schema_path=FEATURE_SCHEMA_PATH,
    )

    model = engine.fit_full(dataset)
    feature_names = tuple(
        engine.prepare_features(dataset).columns
    )

    import hashlib

    digest = hashlib.sha256()

    with FEATURE_SCHEMA_PATH.open("rb") as handle:
        for chunk in iter(
            lambda: handle.read(1024 * 1024),
            b"",
        ):
            digest.update(chunk)

    artifact = ModelArtifact(
        model=model,
        model_version="baseline_v0.2",
        model_family="XGBoost",
        classes=tuple(
            engine.prepare_target(dataset)[1]
        ),
        feature_schema_version="v0.2",
        feature_names=feature_names,
        configuration=engine._config,
        dataset_sha256=(
            "0" * 64
        ),
        feature_schema_sha256=digest.hexdigest(),
    )

    return artifact, dataset


def test_model_artifact_writer_loader_roundtrip(
    tmp_path: Path,
) -> None:
    artifact, dataset = _build_artifact()

    output_dir = (
        tmp_path / "baseline_v0.2"
    )

    writer = ModelArtifactWriter()

    writer.write(
        artifact=artifact,
        output_dir=output_dir,
        feature_schema_path=FEATURE_SCHEMA_PATH,
    )

    expected_files = {
        "model.json",
        "model_contract.json",
        "feature_schema.parquet",
        "artifact_manifest.json",
    }

    assert {
        path.name
        for path in output_dir.iterdir()
    } == expected_files

    engine = XGBoostTrainingEngine(
        feature_schema_path=FEATURE_SCHEMA_PATH,
    )

    X = engine.prepare_features(dataset)

    before = artifact.model.predict_proba(X)

    loaded = ModelArtifactLoader().load(
        output_dir
    )

    after = loaded.model.predict_proba(X)

    assert loaded.model_version == artifact.model_version
    assert loaded.model_family == artifact.model_family
    assert loaded.feature_schema_version == "v0.2"
    assert loaded.classes == artifact.classes
    assert loaded.feature_names == artifact.feature_names
    assert (
        loaded.dataset_sha256
        == artifact.dataset_sha256
    )
    assert (
        loaded.feature_schema_sha256
        == artifact.feature_schema_sha256
    )

    np.testing.assert_array_equal(
        before,
        after,
    )
