"""Tests for the ZTF Classifier command-line interface."""

from __future__ import annotations

import json
import shutil
import subprocess
from collections.abc import Iterator
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from ztf_classifier.application.schemas import PredictionResponse
from ztf_classifier.cli.main import (
    CLI_SCHEMA_VERSION,
    _build_parser,
    _prediction_payload,
    main,
)
from ztf_classifier.models.classes import MODEL_CLASSES
from ztf_classifier.models.results import PredictionResult


def _prediction_response(
    *,
    calibrated: bool = True,
) -> PredictionResponse:
    """Build a deterministic application response for CLI tests."""

    probabilities = np.full(
        (2, len(MODEL_CLASSES)),
        1.0 / len(MODEL_CLASSES),
    )

    probabilities[0, 0] = 0.5
    probabilities[0, 1:] = 0.5 / (len(MODEL_CLASSES) - 1)

    probabilities[1, :] = 0.4 / (len(MODEL_CLASSES) - 1)
    probabilities[1, 2] = 0.6

    if calibrated:
        result = PredictionResult(
            raw_probabilities=probabilities,
            raw_predicted_class_indices=np.array([0, 2]),
            raw_predicted_labels=(
                MODEL_CLASSES[0],
                MODEL_CLASSES[2],
            ),
            calibrated_probabilities=probabilities,
            calibrated_predicted_class_indices=np.array([0, 2]),
            calibrated_predicted_labels=(
                MODEL_CLASSES[0],
                MODEL_CLASSES[2],
            ),
        )
    else:
        result = PredictionResult(
            raw_probabilities=probabilities,
            raw_predicted_class_indices=np.array([0, 2]),
            raw_predicted_labels=(
                MODEL_CLASSES[0],
                MODEL_CLASSES[2],
            ),
        )

    return PredictionResponse(
        result=result,
        model_version="baseline_v0.2",
        model_family="XGBoost",
    )


def test_parser_requires_predict_command() -> None:
    """The CLI must require a command."""

    parser = _build_parser()

    with pytest.raises(SystemExit):
        parser.parse_args([])


def test_parser_accepts_predict_arguments(
    tmp_path: Path,
) -> None:
    """The predict command must parse its required paths."""

    parser = _build_parser()

    args = parser.parse_args(
        [
            "predict",
            "--artifact",
            str(tmp_path / "artifact"),
            "--input",
            str(tmp_path / "input.parquet"),
            "--output",
            str(tmp_path / "prediction.json"),
        ]
    )

    assert args.command == "predict"
    assert args.artifact == tmp_path / "artifact"
    assert args.input == tmp_path / "input.parquet"
    assert args.output == tmp_path / "prediction.json"


def test_prediction_payload_uses_calibrated_predictions() -> None:
    """Calibrated probabilities must be the primary CLI output."""

    dataset = pd.DataFrame(
        {
            "oid": ["ZTF001", "ZTF002"],
        }
    )

    response = _prediction_response(calibrated=True)

    payload = _prediction_payload(dataset, response)

    assert payload["schema_version"] == CLI_SCHEMA_VERSION
    assert payload["model_version"] == "baseline_v0.2"
    assert payload["model_family"] == "XGBoost"
    assert payload["sample_count"] == 2

    first = payload["predictions"][0]

    assert first["oid"] == "ZTF001"
    assert first["predicted_class"] == MODEL_CLASSES[0]
    assert first["predicted_class_index"] == 0
    assert list(first["probabilities"]) == list(MODEL_CLASSES)

    assert first["probabilities"][MODEL_CLASSES[0]] == pytest.approx(
        0.5
    )


def test_prediction_payload_falls_back_to_raw_predictions() -> None:
    """Raw predictions must be used when calibration is unavailable."""

    dataset = pd.DataFrame(
        {
            "oid": ["ZTF001", "ZTF002"],
        }
    )

    response = _prediction_response(calibrated=False)

    payload = _prediction_payload(dataset, response)

    assert payload["predictions"][0]["predicted_class"] == (
        MODEL_CLASSES[0]
    )

    assert payload["predictions"][1]["predicted_class_index"] == 2


def test_prediction_payload_works_without_oid() -> None:
    """OID is optional in the application output."""

    dataset = pd.DataFrame(
        {
            "feature": [1.0, 2.0],
        }
    )

    response = _prediction_response()

    payload = _prediction_payload(dataset, response)

    assert "oid" not in payload["predictions"][0]


def test_main_returns_error_for_missing_input(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Missing input files must return a CLI error."""

    output = tmp_path / "prediction.json"

    exit_code = main(
        [
            "predict",
            "--artifact",
            str(tmp_path / "artifact"),
            "--input",
            str(tmp_path / "missing.parquet"),
            "--output",
            str(output),
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 2
    assert "Input dataset does not exist" in captured.err
    assert not output.exists()


def test_main_writes_prediction_json(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The predict command must write valid JSON output."""

    input_path = tmp_path / "input.parquet"
    output_path = tmp_path / "nested" / "prediction.json"

    dataset = pd.DataFrame(
        {
            "oid": ["ZTF001", "ZTF002"],
        }
    )
    dataset.to_parquet(input_path)

    response = _prediction_response()

    class StubApplicationService:
        """Stub application service for CLI integration."""

        def predict_dataframe(
            self,
            dataset: pd.DataFrame,
            artifact_dir: Path,
        ) -> PredictionResponse:
            """Return the deterministic test response."""

            assert artifact_dir == tmp_path / "artifact"
            assert list(dataset["oid"]) == ["ZTF001", "ZTF002"]

            return response

    monkeypatch.setattr(
        "ztf_classifier.cli.main.ApplicationService",
        StubApplicationService,
    )

    exit_code = main(
        [
            "predict",
            "--artifact",
            str(tmp_path / "artifact"),
            "--input",
            str(input_path),
            "--output",
            str(output_path),
        ]
    )

    assert exit_code == 0
    assert output_path.is_file()

    payload = json.loads(
        output_path.read_text(encoding="utf-8")
    )

    assert payload["schema_version"] == CLI_SCHEMA_VERSION
    assert payload["model_version"] == "baseline_v0.2"
    assert payload["model_family"] == "XGBoost"
    assert payload["sample_count"] == 2
    assert payload["predictions"][0]["oid"] == "ZTF001"


@pytest.fixture(scope="session")
def e2e_diagnostic_artifact(
    tmp_path_factory: pytest.TempPathFactory,
) -> Iterator[Path]:
    token = tmp_path_factory.mktemp("4c").name
    output_dir = Path(f"tmp-test-model-pipeline-{token}")

    try:
        from ztf_classifier.pipeline.model import ModelPipeline

        result = ModelPipeline(
            project_root=Path("."),
            dataset_path=Path("data/processed/features_v0.2.parquet"),
            fold_assignments_path=Path(
                "reports/tables/stratified_cv_fold_assignments_v0.1.parquet"
            ),
            feature_schema_path=Path(
                "reports/tables/final_feature_set_v0.2.parquet"
            ),
            model_config_path=Path(
                "reports/tables/final_model_config_v0.2.json"
            ),
            output_dir=output_dir,
        ).run()

        yield result.artifact_dir
    finally:
        shutil.rmtree(output_dir, ignore_errors=True)


def test_cli_predict_e2e_with_diagnostics(
    e2e_diagnostic_artifact: Path,
    tmp_path: Path,
) -> None:
    input_path = Path("data/processed/features_v0.2.parquet")
    output_path = tmp_path / "prediction.json"

    result = subprocess.run(
        [
            "ztf-classifier",
            "predict",
            "--artifact",
            str(e2e_diagnostic_artifact),
            "--input",
            str(input_path),
            "--output",
            str(output_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert output_path.exists()

    payload = json.loads(output_path.read_text())

    assert payload["schema_version"] == "1.1"
    assert payload["sample_count"] > 0
    assert payload["has_conformal"] is True
    assert payload["has_ood"] is True
    assert len(payload["predictions"]) == payload["sample_count"]

    prediction = payload["predictions"][0]

    assert prediction["predicted_class"] in MODEL_CLASSES
    assert len(prediction["probabilities"]) == len(MODEL_CLASSES)

    assert prediction["conformal"]
    conformal = prediction["conformal"][0]
    assert 0.0 < conformal["alpha"] < 1.0
    assert 0.0 <= conformal["threshold"] <= 1.0
    assert conformal["prediction_set_size"] >= 0

    ood = prediction["ood"]
    assert set(ood) == {
        "anomaly_score",
        "normality_score",
        "anomaly_percentile",
        "isolation_forest_label",
        "anomaly_rank",
        "is_top_1pct_anomaly",
        "is_top_5pct_anomaly",
        "is_top_10pct_anomaly",
    }


def test_cli_batch_e2e_with_diagnostics(
    e2e_diagnostic_artifact: Path,
    tmp_path: Path,
) -> None:
    input_path = Path("data/processed/features_v0.2.parquet")
    output_path = tmp_path / "batch.parquet"

    result = subprocess.run(
        [
            "ztf-classifier",
            "batch",
            "--artifact",
            str(e2e_diagnostic_artifact),
            "--input",
            str(input_path),
            "--output",
            str(output_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert output_path.exists()

    frame = pd.read_parquet(output_path)

    assert len(frame) > 0
    assert "predicted_class" in frame.columns
    assert "predicted_class_index" in frame.columns

    assert any(
        column.startswith("conformal_")
        for column in frame.columns
    )

    assert {
        "ood_anomaly_score",
        "ood_normality_score",
        "ood_anomaly_percentile",
        "ood_isolation_forest_label",
        "ood_anomaly_rank",
        "ood_is_top_1pct_anomaly",
        "ood_is_top_5pct_anomaly",
        "ood_is_top_10pct_anomaly",
    }.issubset(frame.columns)

    assert frame["predicted_class"].notna().all()
