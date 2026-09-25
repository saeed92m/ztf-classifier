"""Command-line interface for ZTF Classifier."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from alerce.core import Alerce

from ztf_classifier.application.batch import BatchInferenceService
from ztf_classifier.application.errors import ApplicationError
from ztf_classifier.application.schemas import PredictionResponse
from ztf_classifier.application.service import ApplicationService
from ztf_classifier.dataset.config import DatasetConfig
from ztf_classifier.io.alerce_detection import AlerceDetectionBackend
from ztf_classifier.io.alerce_object import AlerceObjectBackend
from ztf_classifier.io.parquet_detection_store import ParquetDetectionStore
from ztf_classifier.models.classes import MODEL_CLASSES
from ztf_classifier.pipeline.dataset import DatasetPipeline

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
    predict.add_argument("--artifact", type=Path)
    predict.add_argument("--registry-dir", type=Path)
    predict.add_argument("--model-version")
    predict.add_argument("--input", required=True, type=Path)
    predict.add_argument("--output", required=True, type=Path)

    batch = subparsers.add_parser(
        "batch",
        help="Run batch production prediction and write Parquet output.",
    )
    batch.add_argument("--artifact", type=Path)
    batch.add_argument("--registry-dir", type=Path)
    batch.add_argument("--model-version")
    batch.add_argument("--input", required=True, type=Path)
    batch.add_argument("--output", required=True, type=Path)

    dataset = subparsers.add_parser(
        "dataset",
        help="Build canonical scientific datasets.",
    )

    dataset_subparsers = dataset.add_subparsers(
        dest="dataset_command",
        required=True,
    )

    build = dataset_subparsers.add_parser(
        "build",
        help="Build and validate a canonical dataset.",
    )

    build.add_argument(
        "--config",
        required=True,
        type=Path,
    )

    build.add_argument(
        "--output",
        required=True,
        type=Path,
    )

    build.add_argument(
        "--project-root",
        type=Path,
        default=Path("."),
    )

    build.add_argument(
        "--cache-dir",
        type=Path,
        default=Path("data/raw/alerce"),
    )

    build.add_argument(
        "--feature-schema",
        type=Path,
        default=Path(
            "runs/model_baseline_v0.2_production/artifact/"
            "feature_schema.parquet"
        ),
    )


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
        "provenance": {
            "artifact_version": response.provenance.artifact_version,
            "feature_schema_version": response.provenance.feature_schema_version,
            "dataset_version": response.provenance.dataset_version,
            "dataset_sha256": response.provenance.dataset_sha256,
            "feature_schema_sha256": (
                response.provenance.feature_schema_sha256
            ),
            "git_commit": response.provenance.git_commit,
            "git_dirty": response.provenance.git_dirty,
        },
        "sample_count": result.sample_count,
        "has_calibration": result.has_calibration,
        "has_conformal": result.has_conformal,
        "has_ood": result.has_ood,
        "calibration_status": result.calibration_status,
        "conformal_status": result.conformal_status,
        "ood_status": result.ood_status,
        "warnings": list(result.warnings),
        "artifact_schema_version": result.artifact_schema_version,
        "artifact_hash": result.artifact_hash,
        "feature_schema_hash": result.feature_schema_hash,
        "software_version": result.software_version,
        "predictions": predictions,
    }


def _run_predict(args: argparse.Namespace) -> int:
    """Run the predict command."""

    if not args.input.is_file():
        raise FileNotFoundError(
            f"Input dataset does not exist: {args.input}"
        )

    dataset = pd.read_parquet(args.input)

    if args.artifact is not None and (
        args.registry_dir is not None or args.model_version is not None
    ):
        raise ValueError(
            "Model selection is ambiguous: use --artifact or "
            "--registry-dir with --model-version, not both."
        )

    service = ApplicationService()
    if args.artifact is not None:
        response = service.predict_dataframe(
            dataset=dataset,
            artifact_dir=args.artifact,
        )
    else:
        if args.registry_dir is None or args.model_version is None:
            raise ValueError(
                "Provide --artifact or both --registry-dir and "
                "--model-version."
            )
        response = service.predict_registered_dataframe(
            dataset=dataset,
            registry_dir=args.registry_dir,
            model_version=args.model_version,
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

    if args.artifact is not None and (
        args.registry_dir is not None or args.model_version is not None
    ):
        raise ValueError(
            "Model selection is ambiguous: use --artifact or "
            "--registry-dir with --model-version, not both."
        )

    service = BatchInferenceService()

    if args.artifact is not None:
        result = service.predict(
            dataset=dataset,
            artifact_dir=args.artifact,
        )
    else:
        if args.registry_dir is None or args.model_version is None:
            raise ValueError(
                "Provide --artifact or both --registry-dir and "
                "--model-version."
            )
        result = service.predict_registered(
            dataset=dataset,
            registry_dir=args.registry_dir,
            model_version=args.model_version,
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)

    table = pa.Table.from_pandas(
        result.predictions,
        preserve_index=False,
    )

    metadata = dict(table.schema.metadata or {})
    metadata.update(
        {
            b"ztf_classifier.schema_version": (
                result.schema_version.encode("utf-8")
            ),
            b"ztf_classifier.model_version": (
                result.model_version.encode("utf-8")
            ),
            b"ztf_classifier.model_family": (
                result.model_family.encode("utf-8")
            ),
            b"ztf_classifier.has_calibration": (
                str(result.has_calibration).lower().encode("utf-8")
            ),
            b"ztf_classifier.has_conformal": (
                str(result.has_conformal).lower().encode("utf-8")
            ),
            b"ztf_classifier.has_ood": (
                str(result.has_ood).lower().encode("utf-8")
            ),
            b"ztf_classifier.calibration_status": result.calibration_status.encode("utf-8"),
            b"ztf_classifier.conformal_status": result.conformal_status.encode("utf-8"),
            b"ztf_classifier.ood_status": result.ood_status.encode("utf-8"),
            b"ztf_classifier.artifact_schema_version": result.artifact_schema_version.encode("utf-8"),
            b"ztf_classifier.artifact_hash": result.artifact_hash.encode("utf-8"),
            b"ztf_classifier.feature_schema_hash": result.feature_schema_hash.encode("utf-8"),
            b"ztf_classifier.software_version": result.software_version.encode("utf-8"),
        }
    )

    pq.write_table(
        table.replace_schema_metadata(metadata),
        args.output,
    )

    return 0


def _run_dataset_build(args: argparse.Namespace) -> int:
    """Build and validate a canonical dataset."""

    if not args.config.is_file():
        raise FileNotFoundError(
            f"Dataset configuration does not exist: {args.config}"
        )

    config = DatasetConfig.from_json(args.config)

    project_root = args.project_root.resolve()
    output_dir = args.output.resolve()

    if not args.feature_schema.is_file():
        raise FileNotFoundError(
            f"Feature schema does not exist: {args.feature_schema}"
        )

    feature_schema_path = args.feature_schema.resolve()

    client = Alerce()

    object_backend = AlerceObjectBackend(client)

    detection_store = ParquetDetectionStore(
        args.cache_dir.resolve()
    )

    detection_backend = AlerceDetectionBackend(
        client=client,
        store=detection_store,
    )

    command = (
        "ztf-classifier dataset build "
        f"--config {args.config} "
        f"--output {args.output}"
    )

    result = DatasetPipeline(
        config=config,
        object_acquisition_backend=object_backend,
        detection_acquisition_backend=detection_backend,
        project_root=project_root,
        output_dir=output_dir,
        feature_schema_path=feature_schema_path,
    ).run(
        command=command,
        configuration={
            "config_path": str(args.config.resolve()),
            "cache_dir": str(args.cache_dir.resolve()),
            "feature_schema_path": str(feature_schema_path),
        },
    )

    print(
        f"dataset_version={result.dataset.dataset_version}"
    )
    print(
        f"object_count={result.dataset.object_count}"
    )
    print(
        f"feature_count={result.dataset.feature_count}"
    )
    print(
        f"artifact={result.artifact.artifact_path}"
    )
    print(
        f"manifest={result.artifact.manifest_path}"
    )
    print(
        "reproducibility_manifest="
        f"{output_dir / 'reproducibility_manifest.json'}"
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

        if (
            args.command == "dataset"
            and args.dataset_command == "build"
        ):
            return _run_dataset_build(args)

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
