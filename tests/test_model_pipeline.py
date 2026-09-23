"""Tests for production model-pipeline validation."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from ztf_classifier.models.classes import MODEL_CLASSES
from ztf_classifier.pipeline.model import ModelPipeline

DATASET_PATH = Path(
    "data/processed/features_v0.2.parquet"
)
FOLDS_PATH = Path(
    "reports/tables/stratified_cv_fold_assignments_v0.1.parquet"
)
SCHEMA_PATH = Path(
    "reports/tables/final_feature_set_v0.2.parquet"
)
MODEL_CONFIG_PATH = Path(
    "reports/tables/final_model_config_v0.2.json"
)


@pytest.fixture()
def pipeline() -> ModelPipeline:
    """Build a pipeline instance without requiring execution."""

    return ModelPipeline(
        project_root=Path("."),
        dataset_path=DATASET_PATH,
        fold_assignments_path=FOLDS_PATH,
        feature_schema_path=SCHEMA_PATH,
        model_config_path=MODEL_CONFIG_PATH,
        output_dir=Path("tmp-test-model-pipeline"),
    )


def _valid_dataset() -> pd.DataFrame:
    """Load the frozen historical training dataset."""

    return pd.read_parquet(DATASET_PATH)


def _valid_folds() -> pd.DataFrame:
    """Load the frozen historical fold assignments."""

    return pd.read_parquet(FOLDS_PATH)


def test_validate_training_dataset_accepts_frozen_dataset() -> None:
    dataset = _valid_dataset()

    ModelPipeline._validate_training_dataset(dataset)


def test_validate_training_dataset_rejects_wrong_shape() -> None:
    dataset = _valid_dataset().drop(columns=["oid"])

    with pytest.raises(
        ValueError,
        match=r"shape \(150, 56\)",
    ):
        ModelPipeline._validate_training_dataset(dataset)


def test_validate_training_dataset_rejects_wrong_class_counts() -> None:
    dataset = _valid_dataset().copy()
    dataset.loc[0, "class"] = MODEL_CLASSES[1]

    with pytest.raises(
        ValueError,
        match="exactly 10 samples per class",
    ):
        ModelPipeline._validate_training_dataset(dataset)


def test_validate_fold_assignments_accepts_frozen_assignments() -> None:
    dataset = _valid_dataset()
    folds = _valid_folds()

    result = ModelPipeline._validate_fold_assignments(
        dataset,
        folds,
    )

    assert result.shape == (150,)
    assert np.array_equal(
        np.sort(result),
        np.repeat(np.arange(1, 6), 30),
    )


def test_validate_fold_assignments_rejects_missing_row() -> None:
    dataset = _valid_dataset()
    folds = _valid_folds().iloc[:-1].copy()

    with pytest.raises(
        ValueError,
        match="exactly one row",
    ):
        ModelPipeline._validate_fold_assignments(
            dataset,
            folds,
        )


def test_validate_fold_assignments_rejects_class_mismatch() -> None:
    dataset = _valid_dataset()
    folds = _valid_folds().copy()
    folds.loc[0, "class"] = MODEL_CLASSES[1]

    with pytest.raises(
        ValueError,
        match="classes do not match",
    ):
        ModelPipeline._validate_fold_assignments(
            dataset,
            folds,
        )


def test_validate_fold_assignments_rejects_invalid_fold() -> None:
    dataset = _valid_dataset()
    folds = _valid_folds().copy()
    folds.loc[0, "fold"] = 6

    with pytest.raises(
        ValueError,
        match="folds 1 through 5",
    ):
        ModelPipeline._validate_fold_assignments(
            dataset,
            folds,
        )


def test_validate_inputs_rejects_existing_output(
    pipeline: ModelPipeline,
    tmp_path: Path,
) -> None:
    output_dir = tmp_path / "existing-output"
    output_dir.mkdir()

    pipeline = ModelPipeline(
        project_root=Path("."),
        dataset_path=DATASET_PATH,
        fold_assignments_path=FOLDS_PATH,
        feature_schema_path=SCHEMA_PATH,
        model_config_path=MODEL_CONFIG_PATH,
        output_dir=output_dir,
    )

    with pytest.raises(
        FileExistsError,
        match="output already exists",
    ):
        pipeline._validate_inputs()


def test_validate_model_config_accepts_frozen_config(
    pipeline: ModelPipeline,
) -> None:
    pipeline._validate_model_config()


def test_validate_model_config_rejects_modified_config(
    pipeline: ModelPipeline,
    tmp_path: Path,
) -> None:
    import json

    payload = json.loads(
        MODEL_CONFIG_PATH.read_text(encoding="utf-8")
    )
    payload["n_estimators"] = 301

    config_path = tmp_path / "modified_model_config.json"
    config_path.write_text(
        json.dumps(payload),
        encoding="utf-8",
    )

    pipeline = ModelPipeline(
        project_root=Path("."),
        dataset_path=DATASET_PATH,
        fold_assignments_path=FOLDS_PATH,
        feature_schema_path=SCHEMA_PATH,
        model_config_path=config_path,
        output_dir=tmp_path / "output",
    )

    with pytest.raises(
        ValueError,
        match="does not match",
    ):
        pipeline._validate_model_config()


def test_validate_feature_schema_accepts_frozen_schema(
    pipeline: ModelPipeline,
) -> None:
    dataset = _valid_dataset()

    pipeline._validate_feature_schema(dataset)


def test_validate_feature_schema_rejects_wrong_columns(
    pipeline: ModelPipeline,
) -> None:
    dataset = _valid_dataset()
    schema = pd.read_parquet(SCHEMA_PATH).drop(
        columns=["feature_set"]
    )

    schema_path = SCHEMA_PATH.parent / "tmp_invalid_schema.parquet"
    schema.to_parquet(schema_path, index=False)

    try:
        invalid_pipeline = ModelPipeline(
            project_root=Path("."),
            dataset_path=DATASET_PATH,
            fold_assignments_path=FOLDS_PATH,
            feature_schema_path=schema_path,
            model_config_path=MODEL_CONFIG_PATH,
            output_dir=Path("tmp-test-invalid-schema"),
        )

        with pytest.raises(
            ValueError,
            match="must contain exactly",
        ):
            invalid_pipeline._validate_feature_schema(dataset)
    finally:
        schema_path.unlink(missing_ok=True)


def test_validate_feature_schema_rejects_wrong_order(
    pipeline: ModelPipeline,
    tmp_path: Path,
) -> None:
    dataset = _valid_dataset()
    schema = pd.read_parquet(SCHEMA_PATH).copy()
    schema.loc[0, "feature_order"] = 42

    schema_path = tmp_path / "invalid_schema.parquet"
    schema.to_parquet(schema_path, index=False)

    invalid_pipeline = ModelPipeline(
        project_root=Path("."),
        dataset_path=DATASET_PATH,
        fold_assignments_path=FOLDS_PATH,
        feature_schema_path=schema_path,
        model_config_path=MODEL_CONFIG_PATH,
        output_dir=tmp_path / "output",
    )

    with pytest.raises(
        ValueError,
        match="1 through 42",
    ):
        invalid_pipeline._validate_feature_schema(dataset)


def test_validate_feature_schema_rejects_missing_feature(
    pipeline: ModelPipeline,
    tmp_path: Path,
) -> None:
    dataset = _valid_dataset()
    schema = pd.read_parquet(SCHEMA_PATH).copy()
    schema.loc[0, "feature"] = "definitely_missing_feature"

    schema_path = tmp_path / "invalid_schema.parquet"
    schema.to_parquet(schema_path, index=False)

    invalid_pipeline = ModelPipeline(
        project_root=Path("."),
        dataset_path=DATASET_PATH,
        fold_assignments_path=FOLDS_PATH,
        feature_schema_path=schema_path,
        model_config_path=MODEL_CONFIG_PATH,
        output_dir=tmp_path / "output",
    )

    with pytest.raises(
        ValueError,
        match="missing schema features",
    ):
        invalid_pipeline._validate_feature_schema(dataset)
