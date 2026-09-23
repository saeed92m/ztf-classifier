"""Command-line interface for ZTF Classifier."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd

from ztf_classifier.application.batch import BatchInferenceService
from ztf_classifier.application.errors import ApplicationError
from ztf_classifier.application.schemas import PredictionResponse
from ztf_classifier.application.service import ApplicationService
from ztf_classifier.models.classes import MODEL_CLASSES

CLI_SCHEMA_VERSION = "1.1"


def _build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""

    parser = argparse.ArgumentParser(
        prog="ztf-classifier",
        description="Production inference for the ZTF Classifier.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    predict = subparsers.add_parser(
        "predict",
        help="Run production prediction on a Parquet dataset.",
    )
    predict.add_argument("--artifact", required=True, type=Path)
    predict.add_argument("--input", required=True, type=Path)
    predict.add_argument("--output", required=True, type=Path)

    batch = subparsers.add_parser(
        "batch",
        help="Run batch production prediction and write Parquet output.",
    )
    batch.add_argument("--artifact", required=True, type=Path)
    batch.add_argument("--input", required=True, type=Path)
    batch.add_argument("--output", required=True, type=Path)

    return parser


def _prediction_payload(
    dataset: pd.DataFrame,
    response: PredictionResponse,
) -> dict[str, Any]:
    """Build the stable JSON payload from an application response."""

    result = response.result

    probabilities = (
        result.calibrated_probabilities
        if result.has_calibration
        else result.raw_probabilities
    )

    if probabilities is None:
        raise ValueError("Prediction result does not contain probabilities.")

    predictions: list[dict[str, Any]] = []

    for row_index in range(result.sample_count):
        class_index = int(result.top1_class_indices[row_index])

        probability_map = {
            MODEL_CLASSES[index]: float(probabilities[row_index, index])
            for index in range(len(MODEL_CLASSES))
        }

        item: dict[str, Any] = {
            "predicted_class": result.top1_labels[row_index],
            "predicted_class_index": class_index,
            "probabilities": probability_map,
        }

        if "oid" in dataset.columns:
            item["oid"] = str(dataset.iloc[row_index]["oid"])

        if result.conformal is not None:
            item["conformal"] = [
                {
                    "alpha": float(diagnostic.alpha),
                    "threshold": float(diagnostic.threshold),
                    "prediction_set": list(
                        diagnostic.prediction_set_labels[row_index].split("|")
                    )
                    if diagnostic.prediction_set_labels[row_index]
                    else [],
                    "prediction_set_size": int(
                        diagnostic.prediction_sets[row_index].sum()
                    ),
                }
                for diagnostic in result.conformal.results
            ]

        if result.ood is not None:
            item["ood"] = {
                "anomaly_score": float(
                    result.ood.anomaly_score[row_index]
                ),
                "normality_score": float(
                    result.ood.normality_score[row_index]
                ),
                "anomaly_percentile": float(
                    result.ood.anomaly_percentile[row_index]
                ),
                "isolation_forest_label": int(
                    result.ood.isolation_forest_label[row_index]
                ),
                "anomaly_rank": int(
                    result.ood.anomaly_rank[row_index]
                ),
                "is_top_1pct_anomaly": bool(
                    result.ood.is_top_1pct_anomaly[row_index]
                ),
                "is_top_5pct_anomaly": bool(
                    result.ood.is_top_5pct_anomaly[row_index]
                ),
                "is_top_10pct_anomaly": bool(
                    result.ood.is_top_10pct_anomaly[row_index]
                ),
            }

        predictions.append(item)

    return {
        "schema_version": CLI_SCHEMA_VERSION,
        "model_version": response.model_version,
        "model_family": response.model_family,
        "sample_count": result.sample_count,
        "has_calibration": result.has_calibration,
        "has_conformal": result.has_conformal,
        "has_ood": result.has_ood,
        "predictions": predictions,
    }


def _run_predict(args: argparse.Namespace) -> int:
    """Run the predict command."""

    if not args.input.is_file():
        raise FileNotFoundError(
            f"Input dataset does not exist: {args.input}"
        )

    dataset = pd.read_parquet(args.input)

    response = ApplicationService().predict_dataframe(
        dataset=dataset,
        artifact_dir=args.artifact,
    )

    payload = _prediction_payload(dataset, response)

    args.output.parent.mkdir(parents=True, exist_ok=True)

    args.output.write_text(
        json.dumps(
            payload,
            indent=2,
            sort_keys=False,
            allow_nan=False,
        )
        + "\n",
        encoding="utf-8",
    )

    return 0


def _run_batch(args: argparse.Namespace) -> int:
    """Run the batch command."""

    if not args.input.is_file():
        raise FileNotFoundError(
            f"Input dataset does not exist: {args.input}"
        )

    if args.output.exists():
        raise FileExistsError(
            f"Output file already exists: {args.output}"
        )

    dataset = pd.read_parquet(args.input)

    result = BatchInferenceService().predict(
        dataset=dataset,
        artifact_dir=args.artifact,
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)

    result.predictions.to_parquet(
        args.output,
        index=False,
    )

    return 0


def main(argv: list[str] | None = None) -> int:
    """Run the ZTF Classifier command-line interface."""

    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "predict":
            return _run_predict(args)

        if args.command == "batch":
            return _run_batch(args)

        parser.error(f"Unsupported command: {args.command}")

    except ApplicationError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    except (
        FileNotFoundError,
        FileExistsError,
        ValueError,
        OSError,
    ) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
