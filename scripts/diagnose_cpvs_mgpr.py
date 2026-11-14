#!/usr/bin/env python3
"""Bounded MGPR feasibility diagnostic for the 17 CPVS residuals and controls.

This research-only diagnostic follows the published Chan et al. (2022) recipe
where specified. It does not define catalogue membership and does not reproduce
the authors' unpublished implementation details.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import statistics
from pathlib import Path
from typing import Any

import numpy as np
from scipy.optimize import minimize

try:
    from .diagnose_cpvs_phasefold_coverage import (
        ARCHIVES,
        INPUT_SHA256,
        choose_controls,
        choose_targets,
        load_parent,
        parse_tsv,
        scan_archive,
        verify_sha256,
    )
except ImportError:
    from diagnose_cpvs_phasefold_coverage import (
        ARCHIVES,
        INPUT_SHA256,
        choose_controls,
        choose_targets,
        load_parent,
        parse_tsv,
        scan_archive,
        verify_sha256,
    )

PAPER = {
    "reference": "Chan et al. 2022, ApJ 932, 118, Section 2.1",
    "doi": "10.3847/1538-4357/ac69d4",
    "gp_library": "george==0.4.4",
    "mean_function": "zero",
    "kernel": "C * exp(-dphase^2/lphase^2) * exp(-dlambda^2/llambda^2) + diagonal_white_noise",
    "optimizer": "scipy.optimize.minimize(method='L-BFGS-B')",
    "periodic_boundary": "repeat phase-folded data at phase offsets 0, 1, 2; predict on [2, 3]",
    "grid_points_per_band": 160,
    "normalization": "independent standard scaling per band; scale magnitude errors by the same band standard deviation",
    "wavelength_coordinate": "normalized two-filter coordinate: g=0, r=1",
}
# Bounds and starts are explicit diagnostic choices. The paper does not publish
# the authors' initial values, optimizer bounds, or exact george version.
LOG_BOUNDS = [(-16.0, 4.0), (-12.0, 12.0), (-14.0, 3.0), (-14.0, 3.0)]
STARTS = [
    (math.log(0.01), 0.0, math.log(0.1**2 / 2.0), math.log(0.5**2 / 2.0)),
    (math.log(0.1), 0.0, math.log(0.5**2 / 2.0), math.log(2.0**2 / 2.0)),
]


def prepare_training_data(
    g_rows: list[dict[str, Any]],
    r_rows: list[dict[str, Any]],
) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict[str, dict[str, float]]]:
    """Standardize each band, repeat the observations over three cycles."""
    arrays: list[np.ndarray] = []
    values: list[np.ndarray] = []
    errors: list[np.ndarray] = []
    scaling: dict[str, dict[str, float]] = {}
    for band, wavelength, rows in (("g", 0.0, g_rows), ("r", 1.0, r_rows)):
        if len(rows) < 3:
            raise ValueError(f"Insufficient valid {band}-band observations: {len(rows)}")
        mags = np.asarray([float(row["magnitude"]) for row in rows], dtype=float)
        mag_errors = np.asarray([float(row["mag_error"]) for row in rows], dtype=float)
        phases = np.asarray([float(row["phase"]) % 1.0 for row in rows], dtype=float)
        if not (np.isfinite(mags).all() and np.isfinite(mag_errors).all() and np.isfinite(phases).all()):
            raise ValueError(f"Non-finite {band}-band GP input")
        mean = float(np.mean(mags))
        std = float(np.std(mags, ddof=0))
        if not math.isfinite(std) or std <= 0:
            raise ValueError(f"Non-positive {band}-band standard deviation")
        normalized = (mags - mean) / std
        normalized_errors = mag_errors / std
        repeated_x = []
        repeated_y = []
        repeated_error = []
        for cycle in (0.0, 1.0, 2.0):
            repeated_x.append(np.column_stack((phases + cycle, np.full(len(phases), wavelength))))
            repeated_y.append(normalized)
            repeated_error.append(normalized_errors)
        arrays.append(np.vstack(repeated_x))
        values.append(np.concatenate(repeated_y))
        errors.append(np.concatenate(repeated_error))
        scaling[band] = {
            "mean_magnitude": mean,
            "std_magnitude": std,
            "valid_observations": int(len(rows)),
            "normalized_error_median": float(np.median(normalized_errors)),
        }
    x = np.vstack(arrays)
    y = np.concatenate(values)
    yerr = np.concatenate(errors)
    if x.shape != (len(y), 2) or len(yerr) != len(y):
        raise ValueError("Inconsistent GP training array dimensions")
    return x, y, yerr, scaling


def fit_one_gp(
    x: np.ndarray,
    y: np.ndarray,
    yerr: np.ndarray,
) -> tuple[Any, dict[str, Any]]:
    """Fit the published separable RBF plus diagonal white-noise kernel."""
    try:
        import george
        from george import kernels
    except ImportError as exc:
        raise RuntimeError("Install the pinned research dependency george==0.4.4") from exc

    best: tuple[float, Any, Any] | None = None
    attempts: list[dict[str, Any]] = []
    for start_index, start in enumerate(STARTS):
        kernel = (
            kernels.ConstantKernel(log_constant=start[1], ndim=2)
            * kernels.ExpSquaredKernel(
                metric=[math.exp(start[2]), math.exp(start[3])],
                ndim=2,
            )
        )
        gp = george.GP(
            kernel,
            mean=0.0,
            white_noise=start[0],
            fit_white_noise=True,
        )

        def objective(theta: np.ndarray) -> tuple[float, np.ndarray]:
            try:
                gp.set_parameter_vector(theta)
                gp.compute(x, yerr=yerr)
                loglike = float(gp.log_likelihood(y, quiet=True))
                if not math.isfinite(loglike):
                    return 1.0e100, np.zeros_like(theta)
                gradient = -np.asarray(gp.grad_log_likelihood(y, quiet=True), dtype=float)
                return -loglike, gradient
            except (ValueError, np.linalg.LinAlgError, FloatingPointError):
                return 1.0e100, np.zeros_like(theta)

        result = minimize(
            objective,
            gp.get_parameter_vector(),
            method="L-BFGS-B",
            jac=True,
            bounds=LOG_BOUNDS,
            options={"maxiter": 300, "ftol": 1.0e-9, "maxls": 30},
        )
        final_nll = float(result.fun)
        attempts.append({
            "start_index": start_index,
            "success": bool(result.success),
            "status": int(result.status),
            "message": str(result.message),
            "iterations": int(result.nit),
            "function_evaluations": int(result.nfev),
            "negative_log_likelihood": final_nll if math.isfinite(final_nll) else None,
        })
        if math.isfinite(final_nll) and (best is None or final_nll < best[0]):
            gp.set_parameter_vector(result.x)
            gp.compute(x, yerr=yerr)
            best = (final_nll, gp, result)

    if best is None:
        raise RuntimeError("All deterministic MGPR optimization starts failed")
    nll, gp, result = best
    theta = np.asarray(result.x, dtype=float)
    names = list(gp.get_parameter_names())
    params = {name: float(value) for name, value in zip(names, theta)}
    # The covariance condition number is measured on the fitted training matrix.
    white_noise_index = next(
        index for index, name in enumerate(names) if "white_noise" in name
    )
    delta = math.exp(theta[white_noise_index])
    covariance = gp.kernel.get_value(x)
    covariance = covariance + np.diag(yerr**2 + delta)
    condition_number = float(np.linalg.cond(covariance))
    if not math.isfinite(condition_number):
        condition_number = None
    return gp, {
        "negative_log_likelihood": nll,
        "optimizer_success": bool(result.success),
        "optimizer_message": str(result.message),
        "optimizer_iterations": int(result.nit),
        "optimizer_function_evaluations": int(result.nfev),
        "parameter_names": names,
        "parameters_log_space": params,
        "white_noise_variance": delta,
        "covariance_condition_number_2norm": condition_number,
        "optimizer_starts": attempts,
    }


def predict_object(
    source_id: int,
    obj: dict[str, Any],
    g_rows: list[dict[str, Any]],
    r_rows: list[dict[str, Any]],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    x, y, yerr, scaling = prepare_training_data(g_rows, r_rows)
    gp, fit = fit_one_gp(x, y, yerr)
    phase_grid = np.linspace(2.0, 3.0, 160, endpoint=True)
    prediction_x = np.vstack((
        np.column_stack((phase_grid, np.zeros(160))),
        np.column_stack((phase_grid, np.ones(160))),
    ))
    mean, variance = gp.predict(y, prediction_x, return_var=True)
    if not (np.isfinite(mean).all() and np.isfinite(variance).all()):
        raise ValueError(f"Non-finite MGPR prediction for SourceID={source_id}")
    curves: list[dict[str, Any]] = []
    band_summary: dict[str, Any] = {}
    for index, band in enumerate(("g", "r")):
        scale = scaling[band]
        predicted = mean[index * 160:(index + 1) * 160] * scale["std_magnitude"] + scale["mean_magnitude"]
        sigma = np.sqrt(np.maximum(variance[index * 160:(index + 1) * 160], 0.0)) * scale["std_magnitude"]
        observed = g_rows if band == "g" else r_rows
        observed_mags = np.asarray([float(row["magnitude"]) for row in observed], dtype=float)
        outside = (predicted < np.min(observed_mags)) | (predicted > np.max(observed_mags))
        band_summary[band] = {
            **scale,
            "prediction_min_magnitude": float(np.min(predicted)),
            "prediction_max_magnitude": float(np.max(predicted)),
            "median_predictive_sigma_magnitude": float(np.median(sigma)),
            "max_predictive_sigma_magnitude": float(np.max(sigma)),
            "fraction_predictions_outside_observed_range": float(np.mean(outside)),
        }
        for j in range(160):
            curves.append({
                "SourceID": source_id,
                "cohort": obj["cohort"],
                "band": band,
                "phase": float(phase_grid[j] - 2.0),
                "magnitude_mean": float(predicted[j]),
                "magnitude_sigma": float(sigma[j]),
            })
    metrics = {
        "SourceID": source_id,
        "cohort": obj["cohort"],
        "matched_target_SourceID": obj.get("matched_target_source_id"),
        "Type": obj.get("type"),
        "common_period_days": obj["period"],
        "g_observations": len(g_rows),
        "r_observations": len(r_rows),
        "g_phase_bins_160": len({min(159, int((float(x["phase"]) % 1.0) * 160)) for x in g_rows}),
        "r_phase_bins_160": len({min(159, int((float(x["phase"]) % 1.0) * 160)) for x in r_rows}),
        "fit": fit,
        "bands": band_summary,
    }
    return metrics, curves


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--g-archive", type=Path, required=True)
    parser.add_argument("--r-archive", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    data_dir = args.input_dir / "ztf_periodic_730k"
    input_hashes = {
        name: verify_sha256(data_dir / name, expected)
        for name, expected in INPUT_SHA256.items()
    }
    parent = load_parent(data_dir / "parent_metadata.tsv")
    diag = json.loads((data_dir / "selection_diagnostics.json").read_text(encoding="utf-8"))
    selected = {int(row["SourceID"]) for row in parse_tsv(data_dir / "selected.tsv")}
    residual = {int(row["source_id"]) for row in diag["candidate_only_all_objects"]}
    all_targets = choose_targets(parent, diag)
    targets = [row for row in all_targets if row["cohort"] == "all_17_both_magnitudes_period_incomplete"]
    if len(targets) != 17:
        raise ValueError(f"Expected 17 target residuals; got {len(targets)}")
    controls = choose_controls(parent, selected, residual, targets)
    if len(controls) != 17:
        raise ValueError(f"Expected 17 matched Table 4 controls; got {len(controls)}")
    objects: dict[int, dict[str, Any]] = {}
    for item in targets + controls:
        sid = int(item["source_id"])
        row = parent[sid]
        period = float(row["Per"])
        if not math.isfinite(period) or period <= 0:
            raise ValueError(f"Invalid common period for SourceID={sid}")
        objects[sid] = {
            **item,
            "type": row.get("Type"),
            "period": period,
        }

    raw = {}
    for band, path in (("g", args.g_archive), ("r", args.r_archive)):
        raw[band] = scan_archive(path, band, objects)

    records = []
    curves = []
    for sid in sorted(objects):
        obj = objects[sid]
        g_rows = raw["g"]["objects"][sid]["valid_rows"]
        r_rows = raw["r"]["objects"][sid]["valid_rows"]
        metrics, predictions = predict_object(sid, obj, g_rows, r_rows)
        records.append(metrics)
        curves.extend(predictions)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    report = {
        "schema_version": "1.0",
        "diagnostic": "Bounded Chan et al. (2022) MGPR feasibility audit",
        "scope": "17 candidate-only residuals and 17 deterministic matched Table 4 controls; not a membership selector",
        "reference_method": PAPER,
        "implementation_choices_not_specified_by_paper": {
            "george_version": "0.4.4",
            "optimizer_initial_values": STARTS,
            "optimizer_bounds": LOG_BOUNDS,
            "multi_start_count": len(STARTS),
            "wavelength_coordinate": "g=0, r=1 after normalized two-band mapping",
            "uncertainties": "scaled per-point magnitude errors passed to george.GP.compute; fitted white-noise variance added by george",
            "fit_policy": "all numerically valid raw archive rows; flag semantics are not assumed",
        },
        "input_sha256": input_hashes,
        "raw_archive_integrity": {
            band: {key: value for key, value in result.items() if key != "objects"}
            for band, result in raw.items()
        },
        "cohorts": {
            "residuals": [x for x in records if x["cohort"] == "all_17_both_magnitudes_period_incomplete"],
            "matched_controls": [x for x in records if x["cohort"] == "matched_table4_control"],
        },
        "summary": {
            "objects_total": len(records),
            "residual_count": sum(x["cohort"] == "all_17_both_magnitudes_period_incomplete" for x in records),
            "control_count": sum(x["cohort"] == "matched_table4_control" for x in records),
            "optimizer_success_count": sum(x["fit"]["optimizer_success"] for x in records),
            "optimizer_failure_count": sum(not x["fit"]["optimizer_success"] for x in records),
            "residual_median_g_sigma": statistics.median(x["bands"]["g"]["median_predictive_sigma_magnitude"] for x in records if x["cohort"] == "all_17_both_magnitudes_period_incomplete"),
            "control_median_g_sigma": statistics.median(x["bands"]["g"]["median_predictive_sigma_magnitude"] for x in records if x["cohort"] == "matched_table4_control"),
            "residual_median_r_sigma": statistics.median(x["bands"]["r"]["median_predictive_sigma_magnitude"] for x in records if x["cohort"] == "all_17_both_magnitudes_period_incomplete"),
            "control_median_r_sigma": statistics.median(x["bands"]["r"]["median_predictive_sigma_magnitude"] for x in records if x["cohort"] == "matched_table4_control"),
        },
        "interpretation_limit": (
            "A finite or converged GP fit does not establish historical CPVS membership. "
            "The original paper does not publish exact initialization, bounds, george version, "
            "or a complete reference implementation. Treat differences as feasibility evidence only."
        ),
    }
    report_path = args.output_dir / "cpvs_mgpr_feasibility_report.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    metrics_path = args.output_dir / "cpvs_mgpr_object_metrics.jsonl"
    metrics_path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in records),
        encoding="utf-8",
    )
    curves_path = args.output_dir / "cpvs_mgpr_interpolated_curves.tsv"
    with curves_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=["SourceID", "cohort", "band", "phase", "magnitude_mean", "magnitude_sigma"],
            delimiter="\t",
        )
        writer.writeheader()
        writer.writerows(curves)
    for path in (report_path, metrics_path, curves_path):
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        print(f"{path.name} sha256={digest} bytes={path.stat().st_size}")
    print(json.dumps(report["summary"], indent=2))


if __name__ == "__main__":
    main()
