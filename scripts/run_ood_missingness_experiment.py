"""Reproduce v0.2 OOD state and measure sensitivity to controlled missingness.

This is a diagnostic experiment. It does not define an OOD eligibility threshold.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import scipy
import sklearn

from ztf_classifier.features.basic import basic_band_features
from ztf_classifier.features.cross_band import basic_cross_band_features
from ztf_classifier.features.periodicity import lomb_scargle_features
from ztf_classifier.features.pipeline import V0_2_FEATURES
from ztf_classifier.models.config import OODConfig
from ztf_classifier.models.ood_artifact import OODArtifact
from ztf_classifier.models.ood_production import OODProductionModel

EXPECTED_DATASET_SHA256 = (
    "d08543cffe5db141d6a7e4ee429264acdaa50c6e4fd01f1b0fa2a36aa42a6a85"
)
EXPECTED_SCHEMA_SHA256 = (
    "fed07fc291070ecbdc7bbc597fad5aac6a3f4a1746feb12a9f4c2407108af329"
)
MASKED_FEATURE_COUNTS = (1, 2, 4, 8, 12, 21, 31, 41)
REPLICATES = 20
RANDOM_SEED = 20261109
OOD_THRESHOLDS = (90.0, 95.0, 99.0)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _finite_or_none(value: Any) -> float | None:
    number = float(value)
    return number if np.isfinite(number) else None


def run_masking_sensitivity(
    X: np.ndarray,
    oids: list[str],
    labels: list[str],
    model: OODProductionModel,
    reference: OODArtifact,
    *,
    masked_feature_counts: tuple[int, ...] = MASKED_FEATURE_COUNTS,
    replicates: int = REPLICATES,
    random_seed: int = RANDOM_SEED,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Measure paired score/rank changes on complete rows after MCAR masking."""

    matrix = np.asarray(X, dtype=np.float64)
    if matrix.ndim != 2 or matrix.shape[1] != 42:
        raise ValueError("OOD masking requires a two-dimensional 42-feature matrix.")
    if len(matrix) != len(oids) or len(matrix) != len(labels):
        raise ValueError("OID, label, and feature row counts must match.")
    if not np.isfinite(matrix).all():
        raise ValueError("Masking sensitivity input must contain complete rows.")
    if not masked_feature_counts:
        raise ValueError("At least one masking level is required.")
    if any(count < 1 or count > 41 for count in masked_feature_counts):
        raise ValueError("Masked feature counts must be between 1 and 41.")
    if replicates < 1:
        raise ValueError("replicates must be positive.")

    baseline_scores = model.anomaly_scores(matrix)
    baseline_percentiles = reference.anomaly_percentile(baseline_scores)
    baseline_flags = {
        threshold: baseline_percentiles >= threshold for threshold in OOD_THRESHOLDS
    }

    records: list[dict[str, Any]] = []
    summary_records: list[dict[str, Any]] = []

    for masked_count in masked_feature_counts:
        scenario_records: list[dict[str, Any]] = []
        replicate_correlations: list[float] = []

        for replicate in range(replicates):
            rng = np.random.default_rng(
                random_seed + masked_count * 100_003 + replicate
            )
            masked = matrix.copy()

            for row_index in range(len(masked)):
                selected = rng.choice(
                    matrix.shape[1],
                    size=masked_count,
                    replace=False,
                )
                masked[row_index, selected] = np.nan

            observed = np.isfinite(masked).sum(axis=1)
            if not np.all(observed == matrix.shape[1] - masked_count):
                raise RuntimeError("Masking did not preserve the requested coverage.")

            scores = model.anomaly_scores(masked)
            percentiles = reference.anomaly_percentile(scores)
            percentile_delta = percentiles - baseline_percentiles
            score_delta = scores - baseline_scores

            correlation = pd.Series(baseline_percentiles).corr(
                pd.Series(percentiles),
                method="spearman",
            )
            if np.isfinite(correlation):
                replicate_correlations.append(float(correlation))

            for row_index, oid in enumerate(oids):
                record: dict[str, Any] = {
                    "oid": oid,
                    "class": labels[row_index],
                    "masked_feature_count": masked_count,
                    "observed_feature_count": int(observed[row_index]),
                    "coverage_fraction": float(observed[row_index] / matrix.shape[1]),
                    "replicate": replicate,
                    "baseline_anomaly_score": float(baseline_scores[row_index]),
                    "masked_anomaly_score": float(scores[row_index]),
                    "anomaly_score_delta": float(score_delta[row_index]),
                    "baseline_anomaly_percentile": float(
                        baseline_percentiles[row_index]
                    ),
                    "masked_anomaly_percentile": float(percentiles[row_index]),
                    "anomaly_percentile_delta": float(percentile_delta[row_index]),
                }
                for threshold in OOD_THRESHOLDS:
                    record[f"flag_flip_{int(threshold)}"] = bool(
                        baseline_flags[threshold][row_index]
                        != (percentiles[row_index] >= threshold)
                    )
                records.append(record)
                scenario_records.append(record)

        scenario = pd.DataFrame(scenario_records)
        absolute_percentile_delta = scenario["anomaly_percentile_delta"].abs()
        absolute_score_delta = scenario["anomaly_score_delta"].abs()

        summary: dict[str, Any] = {
            "masked_feature_count": masked_count,
            "observed_feature_count": 42 - masked_count,
            "coverage_fraction": (42 - masked_count) / 42,
            "reference_objects": len(matrix),
            "replicates": replicates,
            "paired_evaluations": len(scenario),
            "median_absolute_percentile_delta": float(
                absolute_percentile_delta.median()
            ),
            "p90_absolute_percentile_delta": float(
                absolute_percentile_delta.quantile(0.90)
            ),
            "max_absolute_percentile_delta": float(absolute_percentile_delta.max()),
            "median_absolute_score_delta": float(absolute_score_delta.median()),
            "p90_absolute_score_delta": float(absolute_score_delta.quantile(0.90)),
            "median_signed_percentile_delta": float(
                scenario["anomaly_percentile_delta"].median()
            ),
            "mean_signed_percentile_delta": float(
                scenario["anomaly_percentile_delta"].mean()
            ),
            "fraction_with_lower_percentile": float(
                (scenario["anomaly_percentile_delta"] < 0).mean()
            ),
            "fraction_with_higher_percentile": float(
                (scenario["anomaly_percentile_delta"] > 0).mean()
            ),
            "median_spearman_rank_correlation": (
                float(np.median(replicate_correlations))
                if replicate_correlations
                else None
            ),
        }
        for threshold in OOD_THRESHOLDS:
            threshold_suffix = int(threshold)
            baseline_flagged = baseline_flags[threshold]
            masked_flagged = (
                scenario["masked_anomaly_percentile"].to_numpy() >= threshold
            )
            baseline_flagged_evaluations = int(baseline_flagged.sum()) * replicates
            masked_flagged_evaluations = int(masked_flagged.sum())
            baseline_percentile_values = scenario[
                "baseline_anomaly_percentile"
            ].to_numpy()
            suppressed = int(
                np.logical_and(
                    baseline_percentile_values >= threshold,
                    ~masked_flagged,
                ).sum()
            )
            newly_flagged = int(
                np.logical_and(
                    baseline_percentile_values < threshold,
                    masked_flagged,
                ).sum()
            )
            summary[f"flag_flip_rate_{threshold_suffix}"] = float(
                scenario[f"flag_flip_{threshold_suffix}"].mean()
            )
            summary[f"flag_flip_count_{threshold_suffix}"] = int(
                scenario[f"flag_flip_{threshold_suffix}"].sum()
            )
            summary[f"baseline_flagged_evaluations_{threshold_suffix}"] = (
                baseline_flagged_evaluations
            )
            summary[f"masked_flagged_evaluations_{threshold_suffix}"] = (
                masked_flagged_evaluations
            )
            summary[f"suppressed_flag_count_{threshold_suffix}"] = suppressed
            summary[f"new_flag_count_{threshold_suffix}"] = newly_flagged
            summary[f"suppressed_rate_of_baseline_flags_{threshold_suffix}"] = (
                float(suppressed / baseline_flagged_evaluations)
                if baseline_flagged_evaluations
                else None
            )
        summary_records.append(summary)

    return pd.DataFrame(records), pd.DataFrame(summary_records)


def build_feature_group_mapping() -> dict[str, dict[str, Any]]:
    """Derive v0.2 feature families from the canonical extraction functions."""

    time = np.linspace(0.0, 50.0, 60)
    g_sample = pd.DataFrame(
        {
            "mjd": time,
            "mag": 15.0 + 0.2 * np.sin(2.0 * np.pi * time / 1.7),
            "magerr": np.full(len(time), 0.05),
        }
    )
    r_sample = pd.DataFrame(
        {
            "mjd": time,
            "mag": 15.5 + 0.15 * np.sin(2.0 * np.pi * time / 2.3),
            "magerr": np.full(len(time), 0.06),
        }
    )

    schema = tuple(V0_2_FEATURES)
    basic_keys = set(basic_band_features(g_sample))
    g_basic = {f"g_{name}" for name in basic_keys}
    r_basic = {f"r_{name}" for name in basic_keys}
    g_periodicity = set(lomb_scargle_features(g_sample, "g"))
    r_periodicity = set(lomb_scargle_features(r_sample, "r"))
    cross_band = set(basic_cross_band_features(g_sample, r_sample))

    candidates = {
        "g_basic": g_basic,
        "g_periodicity": g_periodicity,
        "r_basic": r_basic,
        "r_periodicity": r_periodicity,
        "cross_band": cross_band,
    }
    groups: dict[str, dict[str, Any]] = {}
    assigned: list[str] = []

    for name, candidate_features in candidates.items():
        selected = [feature for feature in schema if feature in candidate_features]
        assigned.extend(selected)
        if name == "g_basic":
            metadata = {
                "source_columns": ["mjd", "mag", "magerr"],
                "band_selector": "fid == 1",
                "minimum_valid_observations": 10,
                "eligibility": "g-band valid observation count >= 10",
            }
        elif name == "r_basic":
            metadata = {
                "source_columns": ["mjd", "mag", "magerr"],
                "band_selector": "fid == 2",
                "minimum_valid_observations": 10,
                "eligibility": "r-band valid observation count >= 10",
            }
        elif name == "g_periodicity":
            metadata = {
                "source_columns": ["mjd", "mag", "magerr"],
                "band_selector": "fid == 1",
                "minimum_valid_observations": 30,
                "eligibility": "g-band valid observation count >= 30",
            }
        elif name == "r_periodicity":
            metadata = {
                "source_columns": ["mjd", "mag", "magerr"],
                "band_selector": "fid == 2",
                "minimum_valid_observations": 30,
                "eligibility": "r-band valid observation count >= 30",
            }
        else:
            metadata = {
                "source_columns": ["mag"],
                "band_selector": {"g": "fid == 1", "r": "fid == 2"},
                "minimum_valid_observations": 1,
                "eligibility": "at least one valid observation in both bands",
            }
        groups[name] = {
            "features": selected,
            **metadata,
            "missing_behavior": "NaN when the extraction eligibility rule is not met",
        }

    if len(assigned) != len(set(assigned)):
        raise ValueError("A v0.2 feature was assigned to more than one family.")
    if set(assigned) != set(schema):
        missing = sorted(set(schema) - set(assigned))
        extra = sorted(set(assigned) - set(schema))
        raise ValueError(
            f"Feature-family mapping does not partition v0.2 schema; "
            f"missing={missing}, extra={extra}"
        )

    return groups


def build_feature_masking_scenarios(
    groups: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Build correlated missingness patterns from v0.2 extraction thresholds."""

    members = {
        name: set(definition["features"])
        for name, definition in groups.items()
    }
    scenarios = {
        "g_periodicity_unavailable": (
            members["g_periodicity"],
            "10-29 valid g observations; g basic and cross-band features remain",
        ),
        "r_periodicity_unavailable": (
            members["r_periodicity"],
            "10-29 valid r observations; r basic and cross-band features remain",
        ),
        "both_periodicity_unavailable": (
            members["g_periodicity"] | members["r_periodicity"],
            "10-29 valid observations in both bands",
        ),
        "g_low_observation_1_to_9": (
            members["g_basic"] | members["g_periodicity"],
            "1-9 valid g observations; r band remains available",
        ),
        "r_low_observation_1_to_9": (
            members["r_basic"] | members["r_periodicity"],
            "1-9 valid r observations; g band remains available",
        ),
        "g_band_absent": (
            members["g_basic"] | members["g_periodicity"] | members["cross_band"],
            "No valid g observations; r-band features remain available",
        ),
        "r_band_absent": (
            members["r_basic"] | members["r_periodicity"] | members["cross_band"],
            "No valid r observations; g-band features remain available",
        ),
        "both_bands_low_observation_1_to_9": (
            members["g_basic"]
            | members["r_basic"]
            | members["g_periodicity"]
            | members["r_periodicity"],
            "1-9 valid observations in both bands; cross-band features remain",
        ),
        "g_low_1_to_9_r_low_10_to_29": (
            members["g_basic"]
            | members["g_periodicity"]
            | members["r_periodicity"],
            "1-9 valid g observations and 10-29 valid r observations",
        ),
        "r_low_1_to_9_g_low_10_to_29": (
            members["r_basic"]
            | members["r_periodicity"]
            | members["g_periodicity"],
            "1-9 valid r observations and 10-29 valid g observations",
        ),
        "g_band_absent_r_low_10_to_29": (
            members["g_basic"]
            | members["g_periodicity"]
            | members["cross_band"]
            | members["r_periodicity"],
            "No valid g observations and 10-29 valid r observations",
        ),
        "r_band_absent_g_low_10_to_29": (
            members["r_basic"]
            | members["r_periodicity"]
            | members["cross_band"]
            | members["g_periodicity"],
            "No valid r observations and 10-29 valid g observations",
        ),
    }
    result = {}
    for name, (missing_features, interpretation) in scenarios.items():
        ordered = [feature for feature in V0_2_FEATURES if feature in missing_features]
        result[name] = {
            "missing_features": ordered,
            "missing_feature_count": len(ordered),
            "observed_feature_count": len(V0_2_FEATURES) - len(ordered),
            "coverage_fraction": (
                len(V0_2_FEATURES) - len(ordered)
            ) / len(V0_2_FEATURES),
            "interpretation": interpretation,
        }
    return result


def run_family_masking_sensitivity(
    X: np.ndarray,
    oids: list[str],
    labels: list[str],
    model: OODProductionModel,
    reference: OODArtifact,
    scenarios: dict[str, dict[str, Any]],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Evaluate physically motivated feature-group missingness patterns."""

    matrix = np.asarray(X, dtype=np.float64)
    if matrix.ndim != 2 or matrix.shape[1] != len(V0_2_FEATURES):
        raise ValueError("Feature-family masking requires the frozen v0.2 schema.")
    if not np.isfinite(matrix).all():
        raise ValueError("Feature-family masking input must contain complete rows.")
    if len(matrix) != len(oids) or len(matrix) != len(labels):
        raise ValueError("OID, label, and feature row counts must match.")

    baseline_scores = model.anomaly_scores(matrix)
    baseline_percentiles = reference.anomaly_percentile(baseline_scores)
    baseline_flags = {
        threshold: baseline_percentiles >= threshold
        for threshold in OOD_THRESHOLDS
    }

    object_records: list[dict[str, Any]] = []
    summary_records: list[dict[str, Any]] = []

    for scenario_name, scenario in scenarios.items():
        missing_features = set(scenario["missing_features"])
        indices = [
            index
            for index, feature in enumerate(V0_2_FEATURES)
            if feature in missing_features
        ]
        masked = matrix.copy()
        masked[:, indices] = np.nan
        observed_counts = np.isfinite(masked).sum(axis=1)
        expected_observed = scenario["observed_feature_count"]
        if not np.all(observed_counts == expected_observed):
            raise RuntimeError(f"Scenario {scenario_name} produced invalid coverage.")

        scores = model.anomaly_scores(masked)
        percentiles = reference.anomaly_percentile(scores)
        percentile_delta = percentiles - baseline_percentiles
        score_delta = scores - baseline_scores

        for row_index, oid in enumerate(oids):
            object_records.append(
                {
                    "scenario": scenario_name,
                    "oid": oid,
                    "class": labels[row_index],
                    "masked_feature_count": len(indices),
                    "observed_feature_count": int(observed_counts[row_index]),
                    "coverage_fraction": float(
                        observed_counts[row_index] / len(V0_2_FEATURES)
                    ),
                    "baseline_anomaly_score": float(baseline_scores[row_index]),
                    "masked_anomaly_score": float(scores[row_index]),
                    "anomaly_score_delta": float(score_delta[row_index]),
                    "baseline_anomaly_percentile": float(
                        baseline_percentiles[row_index]
                    ),
                    "masked_anomaly_percentile": float(percentiles[row_index]),
                    "anomaly_percentile_delta": float(
                        percentile_delta[row_index]
                    ),
                }
            )

        baseline_values = pd.Series(baseline_percentiles)
        masked_values = pd.Series(percentiles)
        summary: dict[str, Any] = {
            "scenario": scenario_name,
            "interpretation": scenario["interpretation"],
            "masked_feature_count": len(indices),
            "observed_feature_count": expected_observed,
            "coverage_fraction": scenario["coverage_fraction"],
            "reference_objects": len(matrix),
            "median_absolute_percentile_delta": float(
                np.median(np.abs(percentile_delta))
            ),
            "p90_absolute_percentile_delta": float(
                np.quantile(np.abs(percentile_delta), 0.90)
            ),
            "median_signed_percentile_delta": float(
                np.median(percentile_delta)
            ),
            "mean_signed_percentile_delta": float(np.mean(percentile_delta)),
            "spearman_rank_correlation": _finite_or_none(
                baseline_values.corr(masked_values, method="spearman")
            ),
            "median_absolute_score_delta": float(np.median(np.abs(score_delta))),
        }
        for threshold in OOD_THRESHOLDS:
            baseline_flagged = baseline_flags[threshold]
            masked_flagged = percentiles >= threshold
            suppressed = int(
                np.logical_and(baseline_flagged, ~masked_flagged).sum()
            )
            newly_flagged = int(
                np.logical_and(~baseline_flagged, masked_flagged).sum()
            )
            baseline_count = int(baseline_flagged.sum())
            summary[f"baseline_flagged_count_{int(threshold)}"] = baseline_count
            summary[f"masked_flagged_count_{int(threshold)}"] = int(
                masked_flagged.sum()
            )
            summary[f"suppressed_flag_count_{int(threshold)}"] = suppressed
            summary[f"new_flag_count_{int(threshold)}"] = newly_flagged
            summary[f"flag_flip_count_{int(threshold)}"] = (
                suppressed + newly_flagged
            )
            summary[f"suppressed_rate_of_baseline_flags_{int(threshold)}"] = (
                float(suppressed / baseline_count) if baseline_count else None
            )
        summary_records.append(summary)

    return pd.DataFrame(object_records), pd.DataFrame(summary_records)


def build_natural_missingness_patterns(
    X: np.ndarray,
    oids: list[str],
    labels: list[str],
    scenarios: dict[str, dict[str, Any]],
    metadata: pd.DataFrame | None = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Match natural missing-feature sets to extraction-threshold patterns."""

    matrix = np.asarray(X, dtype=np.float64)
    scenario_sets = {
        name: set(scenario["missing_features"])
        for name, scenario in scenarios.items()
    }
    metadata_columns = (
        [
            column
            for column in (
                "n_g",
                "n_r",
                "has_g",
                "has_r",
                "has_both_bands",
                "n_valid_total",
            )
            if metadata is not None and column in metadata.columns
        ]
        if metadata is not None
        else []
    )

    records = []
    for row_index, oid in enumerate(oids):
        missing = {
            V0_2_FEATURES[index]
            for index in np.flatnonzero(~np.isfinite(matrix[row_index]))
        }
        if not missing:
            matched = "complete"
        else:
            matches = [
                name for name, expected in scenario_sets.items() if expected == missing
            ]
            matched = matches[0] if len(matches) == 1 else (
                "ambiguous" if matches else "unmatched"
            )
        record: dict[str, Any] = {
            "oid": oid,
            "class": labels[row_index],
            "missing_feature_count": len(missing),
            "observed_feature_count": len(V0_2_FEATURES) - len(missing),
            "coverage_fraction": (
                len(V0_2_FEATURES) - len(missing)
            ) / len(V0_2_FEATURES),
            "matched_extraction_pattern": matched,
            "missing_features": json.dumps(
                [feature for feature in V0_2_FEATURES if feature in missing]
            ),
        }
        if metadata is not None:
            for column in metadata_columns:
                value = metadata.iloc[row_index][column]
                record[column] = (
                    value.item() if hasattr(value, "item") else value
                )
        records.append(record)

    result = pd.DataFrame(records)
    counts = result["matched_extraction_pattern"].value_counts().to_dict()
    summary = {
        "object_count": len(result),
        "exact_pattern_matches": int(
            result["matched_extraction_pattern"].isin(
                ["complete", *scenario_sets.keys()]
            ).sum()
        ),
        "unmatched_objects": int(
            (result["matched_extraction_pattern"] == "unmatched").sum()
        ),
        "ambiguous_objects": int(
            (result["matched_extraction_pattern"] == "ambiguous").sum()
        ),
        "pattern_counts": {str(key): int(value) for key, value in counts.items()},
        "metadata_columns_available": metadata_columns,
    }
    return result, summary


def run_experiment(
    *,
    dataset_path: Path,
    feature_schema_path: Path,
    output_dir: Path,
    expected_dataset_sha256: str = EXPECTED_DATASET_SHA256,
    expected_schema_sha256: str = EXPECTED_SCHEMA_SHA256,
    masked_feature_counts: tuple[int, ...] = MASKED_FEATURE_COUNTS,
    replicates: int = REPLICATES,
    random_seed: int = RANDOM_SEED,
) -> dict[str, Any]:
    """Load frozen v0.2 inputs, fit the configured OOD model, and run diagnostics."""

    dataset_path = Path(dataset_path)
    feature_schema_path = Path(feature_schema_path)
    output_dir = Path(output_dir)

    if not dataset_path.is_file() or not feature_schema_path.is_file():
        raise FileNotFoundError("Frozen dataset and feature schema are required.")

    dataset_sha256 = sha256_file(dataset_path)
    schema_sha256 = sha256_file(feature_schema_path)
    if dataset_sha256 != expected_dataset_sha256:
        raise ValueError(
            "Frozen feature dataset SHA-256 mismatch: "
            f"expected {expected_dataset_sha256}, got {dataset_sha256}"
        )
    if schema_sha256 != expected_schema_sha256:
        raise ValueError(
            "Frozen feature schema SHA-256 mismatch: "
            f"expected {expected_schema_sha256}, got {schema_sha256}"
        )

    dataset = pd.read_parquet(dataset_path)
    schema = pd.read_parquet(feature_schema_path)

    if dataset.shape != (150, 56):
        raise ValueError(
            f"Expected frozen dataset shape (150, 56), got {dataset.shape}."
        )
    if not {"oid", "class"}.issubset(dataset.columns):
        raise ValueError("Frozen dataset must contain oid and class columns.")
    if dataset["oid"].isna().any() or dataset["oid"].astype(str).duplicated().any():
        raise ValueError("Frozen dataset OIDs must be present and unique.")
    class_counts = dataset["class"].astype(str).value_counts()
    if len(class_counts) != 15 or not (class_counts == 10).all():
        raise ValueError(
            "Frozen benchmark must contain 15 classes with 10 objects each."
        )

    required_schema_columns = {"feature_order", "feature"}
    if not required_schema_columns.issubset(schema.columns):
        raise ValueError("Feature schema lacks feature_order or feature.")
    schema = schema.sort_values("feature_order").reset_index(drop=True)
    feature_names = schema["feature"].astype(str).tolist()
    if len(feature_names) != 42 or len(set(feature_names)) != 42:
        raise ValueError(
            "Frozen feature schema must define 42 unique ordered features."
        )
    if feature_names != list(V0_2_FEATURES):
        raise ValueError(
            "Parquet feature schema does not match the canonical v0.2 extraction order."
        )
    missing_columns = sorted(set(feature_names) - set(dataset.columns))
    if missing_columns:
        raise ValueError(f"Dataset is missing frozen features: {missing_columns}")

    features = dataset.loc[:, feature_names].apply(
        pd.to_numeric,
        errors="coerce",
    )
    features = features.replace([np.inf, -np.inf], np.nan)
    X = features.to_numpy(dtype=np.float64)

    if not np.isfinite(X).any():
        raise ValueError("Frozen feature matrix contains no finite values.")
    if np.isnan(X).all(axis=0).any():
        raise ValueError("Frozen feature matrix contains an all-missing feature.")

    config = OODConfig()
    model = OODProductionModel(config).fit(X)
    if model.reference_anomaly_scores is None:
        raise RuntimeError("Fitted OOD model has no reference anomaly scores.")
    reference = OODArtifact.from_config(config, model.reference_anomaly_scores)

    natural_scores = model.anomaly_scores(X)
    natural_percentiles = reference.anomaly_percentile(natural_scores)
    natural_observed = np.isfinite(X).sum(axis=1)

    natural_rows = pd.DataFrame(
        {
            "oid": dataset["oid"].astype(str),
            "class": dataset["class"].astype(str),
            "observed_feature_count": natural_observed,
            "missing_feature_count": 42 - natural_observed,
            "coverage_fraction": natural_observed / 42.0,
            "anomaly_score": natural_scores,
            "anomaly_percentile": natural_percentiles,
            "input_status": np.where(natural_observed == 42, "complete", "partial"),
        }
    )

    complete_mask = natural_observed == 42
    complete_X = X[complete_mask]
    complete_oids = dataset.loc[complete_mask, "oid"].astype(str).tolist()
    complete_labels = dataset.loc[complete_mask, "class"].astype(str).tolist()
    if len(complete_X) < 20:
        raise ValueError(
            "At least 20 complete reference rows are required for paired masking."
        )

    masked_rows, masked_summary = run_masking_sensitivity(
        complete_X,
        complete_oids,
        complete_labels,
        model,
        reference,
        masked_feature_counts=masked_feature_counts,
        replicates=replicates,
        random_seed=random_seed,
    )

    feature_groups = build_feature_group_mapping()
    family_scenarios = build_feature_masking_scenarios(feature_groups)
    family_rows, family_summary = run_family_masking_sensitivity(
        complete_X,
        complete_oids,
        complete_labels,
        model,
        reference,
        family_scenarios,
    )
    natural_patterns, natural_pattern_summary = build_natural_missingness_patterns(
        X,
        dataset["oid"].astype(str).tolist(),
        dataset["class"].astype(str).tolist(),
        family_scenarios,
        metadata=dataset,
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    natural_path = output_dir / "natural_reference_ood_scores.csv"
    masked_path = output_dir / "masked_object_level_results.csv"
    summary_path = output_dir / "masked_sensitivity_summary.csv"
    feature_missingness_path = output_dir / "feature_missingness.csv"
    family_rows_path = output_dir / "family_masked_object_level_results.csv"
    family_summary_path = output_dir / "family_masking_summary.csv"
    natural_patterns_path = output_dir / "natural_missingness_patterns.csv"
    natural_pattern_summary_path = (
        output_dir / "natural_missingness_pattern_summary.json"
    )
    feature_group_mapping_path = output_dir / "feature_group_mapping.json"

    natural_rows.to_csv(natural_path, index=False)
    masked_rows.to_csv(masked_path, index=False)
    masked_summary.to_csv(summary_path, index=False)
    family_rows.to_csv(family_rows_path, index=False)
    family_summary.to_csv(family_summary_path, index=False)
    natural_patterns.to_csv(natural_patterns_path, index=False)
    natural_pattern_summary_path.write_text(
        json.dumps(natural_pattern_summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    feature_group_mapping_path.write_text(
        json.dumps(
            {"groups": feature_groups, "scenarios": family_scenarios},
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    pd.DataFrame(
        {
            "feature_order": schema["feature_order"],
            "feature": feature_names,
            "missing_object_count": np.isnan(X).sum(axis=0),
            "missing_fraction": np.isnan(X).mean(axis=0),
        }
    ).to_csv(feature_missingness_path, index=False)

    report = {
        "report_type": "v0.2_ood_missingness_sensitivity",
        "status": "DIAGNOSTIC_ONLY",
        "scientific_interpretation": (
            "This experiment measures score and rank sensitivity to controlled "
            "MCAR feature masking. It does not establish scientific OOD eligibility, "
            "a calibrated probability, or a production rejection threshold."
        ),
        "reference": {
            "dataset_path": str(dataset_path),
            "dataset_sha256": dataset_sha256,
            "schema_path": str(feature_schema_path),
            "schema_sha256": schema_sha256,
            "object_count": len(dataset),
            "class_count": len(class_counts),
            "features": int(X.shape[1]),
            "complete_objects": int(complete_mask.sum()),
            "partial_objects": int((~complete_mask).sum()),
            "feature_missing_cells": int(np.isnan(X).sum()),
            "feature_cell_count": int(X.size),
            "feature_missing_fraction": float(np.isnan(X).mean()),
        },
        "natural_missingness_association": {
            "complete_objects": int(complete_mask.sum()),
            "partial_objects": int((~complete_mask).sum()),
            "median_ood_percentile_complete": float(
                np.median(natural_percentiles[complete_mask])
            ),
            "median_ood_percentile_partial": float(
                np.median(natural_percentiles[~complete_mask])
            ),
            "spearman_missing_count_vs_ood_percentile": _finite_or_none(
                pd.Series(42 - natural_observed).corr(
                    pd.Series(natural_percentiles),
                    method="spearman",
                )
            ),
            "interpretation": (
                "Descriptive association on the fitted reference dataset. "
                "It is confounded by object and feature-pattern differences "
                "and is not a causal estimate."
            ),
        },
        "feature_group_mapping": feature_groups,
        "natural_missingness_pattern_summary": natural_pattern_summary,
        "model_state_basis": (
            "Reconstructed by fitting OODProductionModel to the exact frozen "
            "v0.2 feature matrix with the frozen OODConfig. The persisted "
            "production artifact was not loaded; this is not a byte-for-byte "
            "artifact replay."
        ),
        "reference_scores_are_in_sample": True,
        "benchmark_label_role": (
            "ALeRCE reference labels; not independent astrophysical ground truth. "
            "Labels are recorded for traceability and are not used by the masking experiment."
        ),
        "ood_configuration": {
            "method": config.method,
            "n_estimators": config.n_estimators,
            "contamination": config.contamination,
            "random_state": config.random_state,
            "n_jobs": config.n_jobs,
            "reference_score_count": len(model.reference_anomaly_scores),
            "thresholds_are_existing_reference_percentiles": list(
                config.anomaly_thresholds
            ),
        },
        "experiment": {
            "masking_mechanism": "MCAR, uniformly sampled feature positions per object",
            "masking_scope": (
                "Controlled perturbation of complete rows only; does not model "
                "correlated survey or feature-family missingness."
            ),
            "complete_subset_limitation": (
                "Paired masking uses only complete rows from the 150-object "
                "reference dataset; report the exact count and do not generalize "
                "to the full ZTF population."
            ),
            "masked_feature_counts": list(masked_feature_counts),
            "replicates_per_level": replicates,
            "random_seed": random_seed,
            "paired_complete_objects": len(complete_X),
            "feature_family_masking": {
                "method": (
                    "Correlated masks derived from canonical v0.2 extraction "
                    "functions and their 10/30 observation eligibility rules."
                ),
                "scenarios": list(family_scenarios),
                "scenario_missing_feature_counts": {
                    name: scenario["missing_feature_count"]
                    for name, scenario in family_scenarios.items()
                },
                "paired_complete_objects": len(complete_X),
                "natural_pattern_summary": natural_pattern_summary,
            },
            "production_eligibility_policy": "NOT_ESTABLISHED",
        },
        "environment": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scipy": scipy.__version__,
            "scikit_learn": sklearn.__version__,
            "git_commit": os.environ.get("GITHUB_SHA", "NOT_AVAILABLE"),
        },
        "outputs": {
            "natural_reference_ood_scores.csv": sha256_file(natural_path),
            "masked_object_level_results.csv": sha256_file(masked_path),
            "masked_sensitivity_summary.csv": sha256_file(summary_path),
            "feature_missingness.csv": sha256_file(feature_missingness_path),
            "family_masked_object_level_results.csv": sha256_file(family_rows_path),
            "family_masking_summary.csv": sha256_file(family_summary_path),
            "natural_missingness_patterns.csv": sha256_file(natural_patterns_path),
            "natural_missingness_pattern_summary.json": sha256_file(
                natural_pattern_summary_path
            ),
            "feature_group_mapping.json": sha256_file(feature_group_mapping_path),
        },
    }

    report_path = output_dir / "ood_missingness_experiment.json"
    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dataset",
        type=Path,
        default=Path("data/processed/features_v0.2.parquet"),
    )
    parser.add_argument(
        "--feature-schema",
        type=Path,
        default=Path("reports/tables/final_feature_set_v0.2.parquet"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("artifacts/ood-missingness-experiment"),
    )
    parser.add_argument("--replicates", type=int, default=REPLICATES)
    parser.add_argument("--seed", type=int, default=RANDOM_SEED)
    args = parser.parse_args()

    report = run_experiment(
        dataset_path=args.dataset,
        feature_schema_path=args.feature_schema,
        output_dir=args.output_dir,
        replicates=args.replicates,
        random_seed=args.seed,
    )
    print(json.dumps(report, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
