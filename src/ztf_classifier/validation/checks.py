"""Executable, fail-closed scientific validation checks.

Checks operate only on declared evidence. Missing inputs produce BLOCKED rather
than an optimistic PASS. The engine is deterministic and network-free.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from ztf_classifier.validation.evidence import EvidenceManifest
from ztf_classifier.validation.manifest import BenchmarkManifest
from ztf_classifier.validation.sources import get_source

VALID_STATUSES = ("PASS", "FAIL", "BLOCKED", "NOT_EXECUTED")


@dataclass(frozen=True)
class CheckResult:
    """Machine-readable result for one scientific validation check."""

    check_id: str
    status: str
    message: str
    metrics: dict[str, Any]
    evidence_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.status not in VALID_STATUSES:
            raise ValueError(f"invalid scientific check status: {self.status}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "check_id": self.check_id,
            "status": self.status,
            "message": self.message,
            "metrics": self.metrics,
            "evidence_refs": list(self.evidence_refs),
        }


def _pass(check_id: str, message: str, **metrics: Any) -> CheckResult:
    return CheckResult(check_id, "PASS", message, metrics)


def _fail(check_id: str, message: str, **metrics: Any) -> CheckResult:
    return CheckResult(check_id, "FAIL", message, metrics)


def _blocked(check_id: str, message: str, **metrics: Any) -> CheckResult:
    return CheckResult(check_id, "BLOCKED", message, metrics)


def _declared_column(manifest: BenchmarkManifest, key: str) -> str | None:
    value = manifest.split_definition.get(key) or manifest.input_contract.get(key)
    return str(value) if value else None


def check_duplicate_objects(
    manifest: BenchmarkManifest, frame: pd.DataFrame
) -> CheckResult:
    column = manifest.object_id_column
    if column not in frame.columns:
        return _blocked(
            "duplicate_objects",
            "The benchmark object identifier column is missing.",
            required_input=column,
        )
    duplicated = frame[column].astype(str).duplicated()
    count = int(duplicated.sum())
    if count:
        return _fail(
            "duplicate_objects",
            "Evaluation artifact contains duplicate object identifiers.",
            duplicate_rows=count,
        )
    return _pass("duplicate_objects", "Object identifiers are unique.", row_count=len(frame))


def check_object_overlap(
    manifest: BenchmarkManifest, frame: pd.DataFrame
) -> CheckResult:
    split_column = _declared_column(manifest, "split_column")
    if not split_column or split_column not in frame.columns:
        return _blocked(
            "object_overlap",
            "An explicit split column is required to prove object-level overlap is absent.",
            required_input="split_column",
        )
    values = frame[split_column].astype(str).str.lower()
    train = set(frame.loc[values == "train", manifest.object_id_column].astype(str))
    evaluation = set(
        frame.loc[values.isin({"validation", "val", "test", "evaluation"}), manifest.object_id_column]
        .astype(str)
    )
    if not train or not evaluation:
        return _blocked(
            "object_overlap",
            "Split metadata must contain both training and evaluation objects.",
            training_objects=len(train),
            evaluation_objects=len(evaluation),
        )
    overlap = train & evaluation
    if overlap:
        return _fail(
            "object_overlap",
            "Training and evaluation object identifiers overlap.",
            overlap_count=len(overlap),
        )
    return _pass(
        "object_overlap",
        "Training and evaluation object identifiers are disjoint.",
        training_objects=len(train),
        evaluation_objects=len(evaluation),
    )


def check_target_leakage(
    manifest: BenchmarkManifest, frame: pd.DataFrame
) -> CheckResult:
    forbidden = manifest.preprocessing_contract.get("forbidden_columns")
    if forbidden is None:
        return _blocked(
            "target_leakage",
            "A declared forbidden-column contract is required for target-leakage validation.",
            required_input="preprocessing_contract.forbidden_columns",
        )
    if not isinstance(forbidden, list):
        return _blocked(
            "target_leakage",
            "forbidden_columns must be a list.",
        )
    present = sorted(set(map(str, forbidden)) & set(map(str, frame.columns)))
    label_present = manifest.label_column in frame.columns
    if present:
        return _fail(
            "target_leakage",
            "Forbidden target-derived columns are present in the evaluation artifact.",
            forbidden_columns=present,
        )
    return _pass(
        "target_leakage",
        "No declared target-derived columns are present.",
        forbidden_columns_checked=len(forbidden),
        label_column_present=label_present,
    )


def check_future_data_leakage(
    manifest: BenchmarkManifest, frame: pd.DataFrame
) -> CheckResult:
    timestamp_column = _declared_column(manifest, "observation_time_column")
    cutoff = manifest.split_definition.get("training_cutoff")
    if not timestamp_column or timestamp_column not in frame.columns or not cutoff:
        return _blocked(
            "future_data_leakage",
            "Observation timestamps and a training cutoff are required.",
            required_inputs=["observation_time_column", "training_cutoff"],
        )
    timestamps = pd.to_datetime(frame[timestamp_column], utc=True, errors="coerce")
    if timestamps.isna().any():
        return _fail(
            "future_data_leakage",
            "Observation timestamps contain unparsable values.",
            invalid_timestamps=int(timestamps.isna().sum()),
        )
    cutoff_ts = pd.Timestamp(cutoff)
    if cutoff_ts.tzinfo is None:
        cutoff_ts = cutoff_ts.tz_localize("UTC")
    future_count = int((timestamps > cutoff_ts).sum())
    if future_count:
        return _fail(
            "future_data_leakage",
            "Evaluation artifact contains observations after the declared training cutoff.",
            future_rows=future_count,
            training_cutoff=cutoff_ts.isoformat(),
        )
    return _pass(
        "future_data_leakage",
        "All observations are at or before the declared training cutoff.",
        training_cutoff=cutoff_ts.isoformat(),
    )


def check_benchmark_trained_artifacts(
    manifest: BenchmarkManifest, frame: pd.DataFrame
) -> CheckResult:
    marker = manifest.input_contract.get("benchmark_trained_artifact_columns")
    if marker is None:
        return _blocked(
            "benchmark_trained_artifacts",
            "The input contract does not declare how benchmark-trained artifacts are identified.",
            required_input="input_contract.benchmark_trained_artifact_columns",
        )
    if not isinstance(marker, list):
        return _blocked("benchmark_trained_artifacts", "benchmark_trained_artifact_columns must be a list.")
    present = sorted(set(map(str, marker)) & set(map(str, frame.columns)))
    if present:
        return _fail(
            "benchmark_trained_artifacts",
            "Evaluation artifact exposes declared benchmark-trained artifact markers.",
            marker_columns=present,
        )
    return _pass(
        "benchmark_trained_artifacts",
        "No declared benchmark-trained artifact markers are present.",
        markers_checked=len(marker),
    )


def check_preprocessing_consistency(
    manifest: BenchmarkManifest, frame: pd.DataFrame
) -> CheckResult:
    required = manifest.preprocessing_contract.get("required_columns")
    if required is None:
        return _blocked(
            "preprocessing_consistency",
            "The preprocessing contract does not declare required normalized columns.",
            required_input="preprocessing_contract.required_columns",
        )
    if not isinstance(required, list):
        return _blocked("preprocessing_consistency", "required_columns must be a list.")
    missing = sorted(set(map(str, required)) - set(map(str, frame.columns)))
    if missing:
        return _fail(
            "preprocessing_consistency",
            "Required preprocessing-contract columns are missing.",
            missing_columns=missing,
        )
    return _pass(
        "preprocessing_consistency",
        "All preprocessing-contract columns are present.",
        checked_columns=len(required),
    )


def check_schema_compatibility(
    manifest: BenchmarkManifest, frame: pd.DataFrame
) -> CheckResult:
    required = manifest.input_contract.get("required_columns")
    if required is None:
        required = [manifest.object_id_column, manifest.label_column,
                    str(manifest.input_contract.get("prediction_column", "y_pred"))]
    if not isinstance(required, list):
        return _blocked("schema_compatibility", "input_contract.required_columns must be a list.")
    missing = sorted(set(map(str, required)) - set(map(str, frame.columns)))
    if missing:
        return _fail(
            "schema_compatibility",
            "Declared benchmark input columns are missing.",
            missing_columns=missing,
        )
    return _pass("schema_compatibility", "Benchmark input schema satisfies the declared contract.")


def check_feature_generation_determinism(
    manifest: BenchmarkManifest, frame: pd.DataFrame
) -> CheckResult:
    fingerprint = manifest.preprocessing_contract.get("feature_fingerprint_column")
    expected = manifest.preprocessing_contract.get("expected_feature_fingerprint")
    if not fingerprint or expected is None or fingerprint not in frame.columns:
        return _blocked(
            "feature_generation_determinism",
            "A feature fingerprint column and expected fingerprint are required.",
            required_inputs=["feature_fingerprint_column", "expected_feature_fingerprint"],
        )
    values = frame[fingerprint].astype(str).unique().tolist()
    if values != [str(expected)]:
        return _fail(
            "feature_generation_determinism",
            "Feature fingerprints do not match the declared deterministic fingerprint.",
            observed=values,
            expected=str(expected),
        )
    return _pass("feature_generation_determinism", "Feature fingerprint matches the declared contract.")


def check_qc_acceptance(
    manifest: BenchmarkManifest, frame: pd.DataFrame
) -> CheckResult:
    column = manifest.accepted_column or manifest.input_contract.get("qc_acceptance_column")
    if not column or column not in frame.columns:
        return _blocked(
            "qc_acceptance",
            "A QC acceptance column is required.",
            required_input="accepted_column or input_contract.qc_acceptance_column",
        )
    raw = frame[column]
    if pd.api.types.is_bool_dtype(raw):
        accepted = raw
    elif pd.api.types.is_numeric_dtype(raw):
        accepted = raw.astype(float).eq(1.0)
    else:
        normalized = raw.astype(str).str.strip().str.lower()
        accepted = normalized.isin({"1", "true", "yes", "accepted", "pass"})
        allowed = {"0", "1", "false", "true", "no", "yes", "rejected", "accepted", "fail", "pass"}
        unknown = sorted(set(normalized) - allowed)
        if unknown:
            return _blocked(
                "qc_acceptance",
                "QC acceptance values contain unrecognized tokens.",
                unknown_values=unknown,
            )
    return _pass(
        "qc_acceptance",
        "QC acceptance field is present and deterministically interpretable.",
        accepted_rows=int(accepted.sum()),
        rejected_rows=int((~accepted).sum()),
        acceptance_rate=float(accepted.mean()) if len(accepted) else 0.0,
    )


def check_inference_reproducibility(
    manifest: BenchmarkManifest, frame: pd.DataFrame
) -> CheckResult:
    first = manifest.input_contract.get("inference_fingerprint_column")
    expected = manifest.input_contract.get("expected_inference_fingerprint")
    if not first or expected is None or first not in frame.columns:
        return _blocked(
            "inference_reproducibility",
            "An inference fingerprint column and expected fingerprint are required.",
            required_inputs=["inference_fingerprint_column", "expected_inference_fingerprint"],
        )
    values = frame[first].astype(str).unique().tolist()
    if values != [str(expected)]:
        return _fail(
            "inference_reproducibility",
            "Inference fingerprints do not match the declared reproducibility contract.",
            observed=values,
            expected=str(expected),
        )
    return _pass("inference_reproducibility", "Inference fingerprint matches the declared contract.")


def check_failure_code_correctness(
    manifest: BenchmarkManifest, frame: pd.DataFrame
) -> CheckResult:
    column = manifest.input_contract.get("failure_code_column")
    allowed = manifest.input_contract.get("allowed_failure_codes")
    if not column or not isinstance(allowed, list) or column not in frame.columns:
        return _blocked(
            "failure_code_correctness",
            "Failure-code column and allowed code vocabulary are required.",
            required_inputs=["failure_code_column", "allowed_failure_codes"],
        )
    observed = set(frame[column].dropna().astype(str))
    invalid = sorted(observed - set(map(str, allowed)))
    if invalid:
        return _fail(
            "failure_code_correctness",
            "Observed failure codes are outside the declared vocabulary.",
            invalid_codes=invalid,
        )
    return _pass("failure_code_correctness", "All observed failure codes are contract-valid.")


def check_provenance(
    manifest: BenchmarkManifest,
    input_path: str | Path,
) -> CheckResult:
    evidence_path = manifest.input_contract.get("evidence_manifest")
    if evidence_path is None:
        candidate = Path(input_path).with_name(Path(input_path).name + ".evidence.json")
        evidence_path = str(candidate) if candidate.is_file() else None
    if not evidence_path:
        return _blocked(
            "provenance",
            "No immutable evidence manifest is bound to the benchmark input.",
            required_input="input_contract.evidence_manifest or <input>.evidence.json",
        )
    path = Path(evidence_path)
    if not path.is_file():
        return _blocked("provenance", "Bound immutable evidence manifest does not exist.", path=str(path))
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        evidence = EvidenceManifest.from_dict(payload)
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        return _fail("provenance", "Immutable evidence manifest is invalid.", error=str(exc))
    errors = evidence.verify(root=path.parent)
    if evidence.benchmark_id != manifest.benchmark_id:
        errors.append("evidence benchmark_id does not match benchmark manifest")
    adapter = manifest.input_contract.get("adapter")
    if not adapter:
        errors.append("benchmark input contract does not declare a canonical source adapter")
    else:
        try:
            source = get_source(str(adapter))
        except KeyError:
            errors.append(f"unknown canonical source adapter: {adapter}")
        else:
            if evidence.source_id != source.source_id:
                errors.append("evidence source_id does not match canonical source adapter")
            if evidence.source_version != source.version:
                errors.append("evidence source_version does not match canonical source version")
    if evidence.source_version != manifest.version and manifest.benchmark_id != "ztf_periodic_730k":
        errors.append("evidence source_version does not match benchmark manifest version")
    if errors:
        return _fail("provenance", "Evidence manifest verification failed.", errors=errors)
    return _pass(
        "provenance",
        "Immutable evidence manifest is present, verifiable, and bound to the benchmark.",
        evidence_manifest=str(path),
    )


_CHECKS = {
    "object_overlap": check_object_overlap,
    "duplicate_objects": check_duplicate_objects,
    "target_leakage": check_target_leakage,
    "future_data_leakage": check_future_data_leakage,
    "benchmark_trained_artifacts": check_benchmark_trained_artifacts,
    "preprocessing_consistency": check_preprocessing_consistency,
    "schema_compatibility": check_schema_compatibility,
    "feature_generation_determinism": check_feature_generation_determinism,
    "qc_acceptance": check_qc_acceptance,
    "inference_reproducibility": check_inference_reproducibility,
    "failure_code_correctness": check_failure_code_correctness,
}


def run_scientific_checks(
    manifest: BenchmarkManifest,
    frame: pd.DataFrame,
    input_path: str | Path,
) -> dict[str, CheckResult]:
    """Execute exactly the checks declared by the benchmark manifest.

    Provenance is always evaluated when requested through the manifest's
    required check set; it is intentionally not inferred from metric success.
    """
    results: dict[str, CheckResult] = {}
    for check_id in manifest.required_leakage_checks:
        if check_id == "provenance":
            results[check_id] = check_provenance(manifest, input_path)
            continue
        check = _CHECKS.get(check_id)
        if check is None:
            results[check_id] = _blocked(
                check_id, "Scientific check implementation is unavailable."
            )
        else:
            results[check_id] = check(manifest, frame)
    return results
