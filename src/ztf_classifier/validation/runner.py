"""Deterministic benchmark execution for externally prepared prediction tables."""

from __future__ import annotations

import hashlib
import json
import resource
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    log_loss,
    precision_score,
    recall_score,
    roc_auc_score,
)

from ztf_classifier.validation.checks import run_scientific_checks
from ztf_classifier.validation.manifest import BenchmarkManifest


@dataclass(frozen=True)
class BenchmarkRunResult:
    """Machine-readable scientific validation result."""

    benchmark_id: str
    evaluation_role: str
    status: str
    metrics: dict[str, Any]
    leakage: dict[str, str]
    checks: dict[str, dict[str, Any]]
    provenance_complete: bool
    input_sha256: str
    row_count: int
    output_path: str

    @property
    def passed(self) -> bool:
        return self.status == "PASS"

    def to_dict(self) -> dict[str, Any]:
        return {
            "benchmark_id": self.benchmark_id,
            "evaluation_role": self.evaluation_role,
            "status": self.status,
            "metrics": self.metrics, "leakage": self.leakage,
            "checks": self.checks,
            "provenance_complete": self.provenance_complete,
            "input_sha256": self.input_sha256, "row_count": self.row_count,
            "output_path": self.output_path,
        }


def _read_table(path: Path) -> pd.DataFrame:
    if not path.is_file():
        raise FileNotFoundError(f"Benchmark input does not exist: {path}")
    if path.suffix.lower() == ".parquet":
        return pd.read_parquet(path)
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path)
    raise ValueError("Benchmark input must be Parquet or CSV")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _ece(y_true: np.ndarray, probabilities: np.ndarray, bins: int = 10) -> float:
    confidence = probabilities.max(axis=1)
    predicted = probabilities.argmax(axis=1)
    correct = (predicted == y_true).astype(float)
    edges = np.linspace(0.0, 1.0, bins + 1)
    value = 0.0
    for index in range(bins):
        upper = edges[index + 1]
        mask = (confidence >= edges[index]) & (
            confidence <= upper if index == bins - 1 else confidence < upper
        )
        if mask.any():
            value += float(mask.mean()) * abs(
                float(correct[mask].mean()) - float(confidence[mask].mean())
            )
    return value


def run_table_benchmark(
    manifest: BenchmarkManifest,
    input_path: str | Path,
    output_dir: str | Path,
) -> BenchmarkRunResult:
    """Run a benchmark over an external labeled prediction table.

    Reference-system outputs remain separate columns and are never promoted
    to ground truth by this runner.
    """
    input_path = Path(input_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    frame = _read_table(input_path)

    prediction_column = str(manifest.input_contract.get("prediction_column", "y_pred"))
    required = {manifest.object_id_column, manifest.label_column, prediction_column}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError("Benchmark input is missing required columns: " + ", ".join(missing))

    y_true = frame[manifest.label_column].astype(str)
    y_pred = frame[prediction_column].astype(str)
    labels = list(manifest.class_mapping.values())

    unknown_truth = sorted(set(y_true) - set(labels))
    unknown_prediction = sorted(set(y_pred) - set(labels))
    if unknown_truth or unknown_prediction:
        raise ValueError(
            "Benchmark labels fall outside manifest class mapping: "
            f"truth={unknown_truth}, prediction={unknown_prediction}"
        )

    metrics: dict[str, Any] = {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
        "macro_precision": float(precision_score(y_true, y_pred, labels=labels, average="macro", zero_division=0)),
        "macro_recall": float(recall_score(y_true, y_pred, labels=labels, average="macro", zero_division=0)),
        "macro_f1": float(f1_score(y_true, y_pred, labels=labels, average="macro", zero_division=0)),
        "weighted_precision": float(precision_score(y_true, y_pred, labels=labels, average="weighted", zero_division=0)),
        "weighted_recall": float(recall_score(y_true, y_pred, labels=labels, average="weighted", zero_division=0)),
        "weighted_f1": float(f1_score(y_true, y_pred, labels=labels, average="weighted", zero_division=0)),
        "per_class": {
            "labels": labels,
            "precision": precision_score(y_true, y_pred, labels=labels, average=None, zero_division=0).tolist(),
            "recall": recall_score(y_true, y_pred, labels=labels, average=None, zero_division=0).tolist(),
            "f1": f1_score(y_true, y_pred, labels=labels, average=None, zero_division=0).tolist(),
        },
        "confusion_matrix": confusion_matrix(y_true, y_pred, labels=labels).tolist(),
    }

    probability_columns = manifest.probability_columns or []
    if probability_columns:
        missing_probabilities = sorted(set(probability_columns) - set(frame.columns))
        if missing_probabilities:
            raise ValueError("Benchmark input is missing probability columns: " + ", ".join(missing_probabilities))
        probabilities = frame[probability_columns].to_numpy(dtype=float)
        if probabilities.shape[1] != len(labels) or not np.isfinite(probabilities).all():
            raise ValueError("Probability columns must be finite and match the class count")
        if (probabilities < 0).any() or not np.allclose(probabilities.sum(axis=1), 1.0, atol=1e-6):
            raise ValueError("Probability rows must be non-negative and sum to 1")
        truth_indices = np.asarray([labels.index(label) for label in y_true])
        metrics["log_loss"] = float(log_loss(truth_indices, probabilities, labels=np.arange(len(labels))))
        one_hot = np.eye(len(labels))[truth_indices]
        metrics["brier_multiclass"] = float(np.mean(np.sum((probabilities - one_hot) ** 2, axis=1)))
        metrics["expected_calibration_error"] = _ece(truth_indices, probabilities)

    if manifest.ood_label_column and manifest.ood_score_column:
        if manifest.ood_label_column not in frame or manifest.ood_score_column not in frame:
            raise ValueError("OOD columns declared by manifest are missing")
        ood_labels = frame[manifest.ood_label_column].astype(int).to_numpy()
        ood_scores = frame[manifest.ood_score_column].to_numpy(dtype=float)
        if not np.isfinite(ood_scores).all():
            raise ValueError("OOD scores must be finite")
        if set(np.unique(ood_labels)) - {0, 1}:
            raise ValueError("OOD labels must be binary 0/1")
        ood = {
            "label_column": manifest.ood_label_column,
            "score_column": manifest.ood_score_column,
            "coverage": float((ood_labels == 0).mean()),
        }
        if len(np.unique(ood_labels)) == 2:
            ood["auroc"] = float(roc_auc_score(ood_labels, ood_scores))
            ood["average_precision"] = float(average_precision_score(ood_labels, ood_scores))
        else:
            ood["auroc"] = None
            ood["average_precision"] = None
        if manifest.accepted_column:
            accepted = frame[manifest.accepted_column].astype(bool).to_numpy()
            ood["false_accept_rate"] = float(np.mean(accepted[ood_labels == 1])) if np.any(ood_labels == 1) else None
            ood["false_reject_rate"] = float(np.mean(~accepted[ood_labels == 0])) if np.any(ood_labels == 0) else None
        metrics["ood"] = ood

    if manifest.accepted_column:
        if manifest.accepted_column not in frame:
            raise ValueError(f"Missing acceptance column: {manifest.accepted_column}")
        metrics["coverage"] = float(frame[manifest.accepted_column].mean())

    check_results = run_scientific_checks(manifest, frame, input_path)
    checks = {name: result.to_dict() for name, result in check_results.items()}
    leakage = {name: result.status for name, result in check_results.items()}

    provenance_result = check_results.get("provenance")
    provenance_complete = all((
        manifest.source, manifest.version, manifest.retrieval_date,
        manifest.label_taxonomy, manifest.benchmark_code_version,
    ))
    if manifest.evaluation_role == "ground_truth":
        provenance_complete = provenance_complete and bool(manifest.ground_truth_provenance)
    else:
        provenance_complete = provenance_complete and bool(manifest.reference_system_provenance)
    if provenance_result is not None:
        provenance_complete = provenance_complete and provenance_result.status == "PASS"

    blockers = [
        name for name in manifest.required_leakage_checks
        if leakage.get(name) != "PASS"
    ]
    if (provenance_result is not None and provenance_result.status != "PASS") or (
        provenance_result is None and not provenance_complete
    ):
        blockers.append("provenance")
    status = "PASS" if not blockers else "BLOCKED"
    elapsed = time.perf_counter() - started
    peak_rss_mb = float(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss) / 1024.0
    if sys.platform == "darwin":
        peak_rss_mb /= 1024.0
    metrics["performance"] = {"runtime_seconds": float(elapsed), "peak_rss_mb": peak_rss_mb}

    result = BenchmarkRunResult(
        benchmark_id=manifest.benchmark_id,
        evaluation_role=manifest.evaluation_role,
        status=status,
        metrics=metrics,
        leakage=leakage, checks=checks, provenance_complete=provenance_complete,
        input_sha256=_sha256(input_path), row_count=len(frame),
        output_path=str(output_dir / "benchmark_result.json"),
    )
    (output_dir / "benchmark_result.json").write_text(
        json.dumps(result.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (output_dir / "benchmark_result.md").write_text(_render_markdown(result), encoding="utf-8")
    return result


def _render_markdown(result: BenchmarkRunResult) -> str:
    lines = [
        f"# Scientific Benchmark Report — {result.benchmark_id}", "",
        f"- Status: **{result.status}**", f"- Population rows: {result.row_count}",
        f"- Input SHA-256: {result.input_sha256}",
        f"- Provenance complete: {result.provenance_complete}", "",
        "## Metrics", "",
    ]
    lines.extend(f"- **{key}**: {json.dumps(value, sort_keys=True)}" for key, value in result.metrics.items())
    lines.extend(["", "## Leakage", ""])
    lines.extend(f"- **{key}**: {value}" for key, value in result.leakage.items())
    lines.extend([
        "", "## Interpretation boundary", "",
        (
            "Benchmark success is not proof of universal correctness; it is quantitative, "
            "reproducible evidence for the defined population, labels, source versions, "
            "and evaluation conditions."
        ),
        "",
    ])
    return "\n".join(lines)
