"""Tests for registry-backed batch CLI selection."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from ztf_classifier.application.batch import BatchPredictionResult
from ztf_classifier.cli.main import main


def test_cli_batch_uses_registry_selection(
    tmp_path: Path,
    monkeypatch,
) -> None:
    input_path = tmp_path / "input.parquet"
    output_path = tmp_path / "output.parquet"
    registry_dir = tmp_path / "registry"

    pd.DataFrame({"oid": ["ZTF001"]}).to_parquet(input_path)

    class StubBatchService:
        def predict_registered(
            self,
            dataset: pd.DataFrame,
            registry_dir: Path,
            model_version: str,
        ) -> BatchPredictionResult:
            assert list(dataset["oid"]) == ["ZTF001"]
            assert registry_dir == tmp_path / "registry"
            assert model_version == "baseline_v0.2"
            return BatchPredictionResult(
                predictions=pd.DataFrame(
                    {
                        "oid": ["ZTF001"],
                        "predicted_class": ["AGN"],
                        "predicted_class_index": [0],
                        "probability_AGN": [1.0],
                        "model_version": ["baseline_v0.2"],
                        "model_family": ["XGBoost"],
                    }
                ),
                model_version="baseline_v0.2",
                model_family="XGBoost",
                has_calibration=False,
                has_conformal=False,
                has_ood=False,
            )

        def predict(self, dataset, artifact_dir):
            raise AssertionError("direct artifact path must not be selected")

    monkeypatch.setattr(
        "ztf_classifier.cli.main.BatchInferenceService",
        StubBatchService,
    )

    exit_code = main(
        [
            "batch",
            "--registry-dir",
            str(registry_dir),
            "--model-version",
            "baseline_v0.2",
            "--input",
            str(input_path),
            "--output",
            str(output_path),
        ]
    )

    assert exit_code == 0
    assert output_path.is_file()


def test_cli_batch_requires_complete_model_selection(
    tmp_path: Path,
    capsys,
) -> None:
    input_path = tmp_path / "input.parquet"
    output_path = tmp_path / "output.parquet"
    pd.DataFrame({"oid": ["ZTF001"]}).to_parquet(input_path)

    exit_code = main(
        [
            "batch",
            "--registry-dir",
            str(tmp_path / "registry"),
            "--input",
            str(input_path),
            "--output",
            str(output_path),
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 2
    assert "Provide --artifact or both --registry-dir and --model-version." in captured.err
    assert not output_path.exists()
