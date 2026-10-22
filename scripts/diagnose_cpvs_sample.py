"""Reproducible CPVS 100/1000-object provenance and SNR diagnostics.

This is diagnostic-only: it does not alter production thresholds or acceptance
criteria. It compares the current linear magnitude-error approximation with a
nonlinear inverse as a hypothesis, while retaining per-object source evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter
from itertools import chain
from pathlib import Path
from typing import Any

from scripts.audit_cpvs_membership import read_parent_catalog, read_selected, read_vizier_rows
from ztf_classifier.validation.derivation import _find_key, _iter_rows

_LINEAR_FACTOR = 1.0857362047581296


def exact_snr_from_mag_error(error: float) -> float:
    """Diagnostic alternative; do not treat as the accepted rule without evidence."""
    if not math.isfinite(error) or error <= 0:
        return float("nan")
    try:
        denominator = math.expm1(0.4 * math.log(10.0) * error)
    except OverflowError:
        return 0.0
    return 1.0 / denominator if denominator > 0 else float("inf")


def _rank(seed: int, source_id: int) -> str:
    return hashlib.sha256(f"{seed}:{source_id}".encode("ascii")).hexdigest()


def select_stratified_ids(
    parent_ids: set[int],
    published_ids: set[int],
    *,
    seed: int = 20261022,
    sample_size: int = 1000,
    diagnostic_size: int = 100,
) -> tuple[list[int], list[int]]:
    """Return deterministic balanced sample IDs; diagnostic sample is nested."""
    if sample_size <= 0 or sample_size % 2:
        raise ValueError("sample_size must be a positive even number")
    if diagnostic_size <= 0 or diagnostic_size % 2 or diagnostic_size > sample_size:
        raise ValueError("diagnostic_size must be even, positive, and <= sample_size")
    members = sorted(parent_ids & published_ids, key=lambda oid: _rank(seed, oid))
    nonmembers = sorted(parent_ids - published_ids, key=lambda oid: _rank(seed, oid))
    per_stratum = sample_size // 2
    diagnostic_per_stratum = diagnostic_size // 2
    if len(members) < per_stratum or len(nonmembers) < per_stratum:
        raise ValueError("parent does not contain enough reference members/non-members")
    sample = members[:per_stratum] + nonmembers[:per_stratum]
    diagnostic = members[:diagnostic_per_stratum] + nonmembers[:diagnostic_per_stratum]
    return sample, diagnostic


def _float_value(value: str | None) -> float:
    try:
        return float(value) if value is not None else float("nan")
    except (TypeError, ValueError):
        return float("nan")


def _row_evidence(
    row: dict[str, str],
    *,
    source_id: int,
    mag_key: str,
    error_key: str,
    flag_key: str | None,
    snr_linear: float,
    snr_exact: float,
) -> dict[str, Any]:
    return {
        "SourceID": source_id,
        "HJD": row.get("HJD"),
        "magnitude": row.get(mag_key),
        "magnitude_error": row.get(error_key),
        "flag": row.get(flag_key) if flag_key else None,
        "snr_linear": snr_linear if math.isfinite(snr_linear) else None,
        "snr_exact_diagnostic": snr_exact if math.isfinite(snr_exact) else None,
    }


def _band_diagnostics(
    path: Path,
    *,
    parent_ids: set[int],
    sample_ids: set[int],
    error_column: str,
    mag_column: str,
    flag_column: str,
    sigma: float,
) -> tuple[set[int], set[int], dict[int, dict[str, Any]]]:
    """Stream one band once; return linear/exact-qualified object sets and sample evidence."""
    rows = _iter_rows(
        path,
        required_columns=("SourceID", error_column, mag_column),
    )
    first = next(rows, None)
    if first is None:
        raise ValueError(f"no usable light-curve rows found in {path}")
    id_key = _find_key(first, ("SourceID", "sourceid", "oid", "ztf_id"))
    error_key = _find_key(first, (error_column,))
    mag_key = _find_key(first, (mag_column,))
    try:
        flag_key = _find_key(first, (flag_column,))
    except ValueError:
        flag_key = None

    linear_qualified: set[int] = set()
    exact_qualified: set[int] = set()
    sample: dict[int, dict[str, Any]] = {
        oid: {
            "rows": 0,
            "valid_error_rows": 0,
            "valid_nonzero_magnitude_rows": 0,
            "linear_qualifying_rows": 0,
            "exact_qualifying_rows": 0,
            "flag_zero_rows": 0,
            "flag_nonzero_rows": 0,
            "max_snr_linear": None,
            "max_snr_exact_diagnostic": None,
            "max_snr_linear_row": None,
            "max_snr_exact_row": None,
            "first_linear_qualifying_row": None,
            "first_exact_qualifying_row": None,
        }
        for oid in sample_ids
    }

    for row in chain((first,), rows):
        raw_id = row.get(id_key, "").strip()
        try:
            source_id = int(raw_id)
        except (TypeError, ValueError):
            continue
        if source_id not in parent_ids:
            continue

        is_sample = source_id in sample
        stats = sample.get(source_id)
        if stats is not None:
            stats["rows"] += 1

        error = _float_value(row.get(error_key))
        magnitude = _float_value(row.get(mag_key))
        if not math.isfinite(error) or error <= 0:
            continue
        if stats is not None:
            stats["valid_error_rows"] += 1

        snr_linear = _LINEAR_FACTOR / error
        snr_exact = exact_snr_from_mag_error(error)
        flag_value = row.get(flag_key, "").strip() if flag_key else ""
        if stats is not None and flag_key:
            try:
                flag = int(float(flag_value))
                if flag == 0:
                    stats["flag_zero_rows"] += 1
                else:
                    stats["flag_nonzero_rows"] += 1
            except (TypeError, ValueError):
                pass

        valid_magnitude = math.isfinite(magnitude) and magnitude != 0.0
        if not valid_magnitude:
            continue
        if stats is not None:
            stats["valid_nonzero_magnitude_rows"] += 1

        record = _row_evidence(
            row,
            source_id=source_id,
            mag_key=mag_key,
            error_key=error_key,
            flag_key=flag_key,
            snr_linear=snr_linear,
            snr_exact=snr_exact,
        )
        if stats is not None and (
            stats["max_snr_linear"] is None or snr_linear > stats["max_snr_linear"]
        ):
            stats["max_snr_linear"] = snr_linear
            stats["max_snr_linear_row"] = record
        if stats is not None and (
            stats["max_snr_exact_diagnostic"] is None
            or snr_exact > stats["max_snr_exact_diagnostic"]
        ):
            stats["max_snr_exact_diagnostic"] = snr_exact
            stats["max_snr_exact_row"] = record

        if snr_linear >= sigma:
            linear_qualified.add(source_id)
            if stats is not None:
                stats["linear_qualifying_rows"] += 1
                if stats["first_linear_qualifying_row"] is None:
                    stats["first_linear_qualifying_row"] = record
        if snr_exact >= sigma:
            exact_qualified.add(source_id)
            if stats is not None:
                stats["exact_qualifying_rows"] += 1
                if stats["first_exact_qualifying_row"] is None:
                    stats["first_exact_qualifying_row"] = record

    return linear_qualified, exact_qualified, sample


def _membership_class(candidate: bool, reference: bool) -> str:
    if candidate and reference:
        return "TP"
    if candidate:
        return "FP"
    if reference:
        return "FN"
    return "TN"


def _comparison(candidate: set[int], reference: set[int], parent_rows: dict[int, str]) -> dict[str, Any]:
    candidate_only = sorted(candidate - reference)
    published_only = sorted(reference - candidate)
    return {
        "candidate_count": len(candidate),
        "reference_count": len(reference),
        "intersection_count": len(candidate & reference),
        "candidate_only_count": len(candidate_only),
        "published_only_count": len(published_only),
        "candidate_only_sourceids_sample": candidate_only[:100],
        "published_only_sourceids_sample": published_only[:100],
        "candidate_only_objects_sample": [
            {"SourceID": oid, "ZTF": parent_rows.get(oid)} for oid in candidate_only[:100]
        ],
        "published_only_objects_sample": [
            {"SourceID": oid, "ZTF": parent_rows.get(oid)} for oid in published_only[:100]
        ],
        "candidate_only_sha256": hashlib.sha256(
            ("\n".join(map(str, candidate_only)) + "\n").encode()
        ).hexdigest(),
        "published_only_sha256": hashlib.sha256(
            ("\n".join(map(str, published_only)) + "\n").encode()
        ).hexdigest(),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--parent", type=Path, required=True)
    parser.add_argument("--g", type=Path, required=True)
    parser.add_argument("--r", type=Path, required=True)
    parser.add_argument("--published", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=20261022)
    parser.add_argument("--sample-size", type=int, default=1000)
    parser.add_argument("--diagnostic-size", type=int, default=100)
    args = parser.parse_args()

    parent_rows = read_parent_catalog(args.parent)
    parent_ids = set(parent_rows)
    if len(parent_ids) != 781_602:
        raise ValueError(f"expected 781602 explicit Table2 Seq IDs, got {len(parent_ids)}")
    parent_name_counts = Counter(parent_rows.values())
    duplicate_parent_names = sorted(name for name, count in parent_name_counts.items() if count > 1)

    published_rows = read_vizier_rows(args.published)
    published_names = list(published_rows.values())
    duplicate_published_names = sorted(
        name for name, count in Counter(published_names).items() if count > 1
    )
    name_to_ids: dict[str, list[int]] = {}
    for source_id, name in parent_rows.items():
        name_to_ids.setdefault(name, []).append(source_id)
    missing_published_names = sorted(set(published_names) - set(name_to_ids))
    if duplicate_parent_names or duplicate_published_names or missing_published_names:
        raise ValueError(
            "invalid object-name crosswalk: "
            f"duplicate_parent_names={len(duplicate_parent_names)}, "
            f"duplicate_published_names={len(duplicate_published_names)}, "
            f"published_names_missing_from_parent={len(missing_published_names)}"
        )
    published_ids = {name_to_ids[name][0] for name in published_names}
    candidate_ids = read_selected(args.candidate)
    candidate_ids_outside_parent = sorted(candidate_ids - parent_ids)

    sample_1000, sample_100 = select_stratified_ids(
        parent_ids,
        published_ids,
        seed=args.seed,
        sample_size=args.sample_size,
        diagnostic_size=args.diagnostic_size,
    )
    sample_ids = set(sample_1000)

    g_linear, g_exact, g_sample = _band_diagnostics(
        args.g,
        parent_ids=parent_ids,
        sample_ids=sample_ids,
        error_column="e_gmag",
        mag_column="gmag",
        flag_column="g_flag",
        sigma=2.5,
    )
    r_linear, r_exact, r_sample = _band_diagnostics(
        args.r,
        parent_ids=parent_ids,
        sample_ids=sample_ids,
        error_column="e_rmag",
        mag_column="rmag",
        flag_column="r_flag",
        sigma=3.0,
    )

    candidate_linear = g_linear & r_linear
    candidate_exact = g_exact & r_exact
    comparisons = {
        "current_linear_snr": _comparison(candidate_ids, published_ids, parent_rows),
        "recomputed_linear_snr": _comparison(candidate_linear, published_ids, parent_rows),
        "nonlinear_exact_snr_diagnostic": _comparison(candidate_exact, published_ids, parent_rows),
    }

    def object_detail(source_id: int) -> dict[str, Any]:
        reference = source_id in published_ids
        current = source_id in candidate_ids
        linear = source_id in candidate_linear
        exact = source_id in candidate_exact
        return {
            "SourceID": source_id,
            "ZTF": parent_rows[source_id],
            "reference_member": reference,
            "candidate_current": current,
            "candidate_recomputed_linear": linear,
            "candidate_nonlinear_exact_diagnostic": exact,
            "classification_current": _membership_class(current, reference),
            "classification_nonlinear_exact_diagnostic": _membership_class(exact, reference),
            "g": g_sample[source_id],
            "r": r_sample[source_id],
        }

    def sample_confusion(ids: list[int], candidate: set[int]) -> dict[str, int]:
        labels = Counter(_membership_class(source_id in candidate, source_id in published_ids) for source_id in ids)
        return {key: labels.get(key, 0) for key in ("TP", "FP", "FN", "TN")}

    report = {
        "schema_version": "1.0",
        "diagnostic_only": True,
        "selection_rule_change_proposed": False,
        "seed": args.seed,
        "sample_design": {
            "sample_size": len(sample_1000),
            "diagnostic_size": len(sample_100),
            "stratification": "equal numbers of published reference members and non-members",
            "ranking": "ascending SHA256(f'{seed}:{SourceID}') within each stratum",
            "diagnostic_sample_is_nested_in_full_sample": True,
            "reference_member_count_in_sample_1000": sum(oid in published_ids for oid in sample_1000),
            "nonmember_count_in_sample_1000": sum(oid not in published_ids for oid in sample_1000),
        },
        "parent_count": len(parent_ids),
        "published_count": len(published_ids),
        "candidate_current_count": len(candidate_ids),
        "candidate_ids_outside_parent_count": len(candidate_ids_outside_parent),
        "candidate_ids_outside_parent_sample": candidate_ids_outside_parent[:100],
        "membership_comparisons": comparisons,
        "sample_1000_confusion_current": sample_confusion(sample_1000, candidate_ids),
        "sample_1000_confusion_recomputed_linear": sample_confusion(sample_1000, candidate_linear),
        "sample_1000_confusion_nonlinear_exact_diagnostic": sample_confusion(sample_1000, candidate_exact),
        "sample_100_confusion_current": sample_confusion(sample_100, candidate_ids),
        "sample_100_confusion_nonlinear_exact_diagnostic": sample_confusion(sample_100, candidate_exact),
        "sample_1000": [object_detail(oid) for oid in sample_1000],
        "sample_100": [object_detail(oid) for oid in sample_100],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in (
        "parent_count",
        "published_count",
        "candidate_current_count",
        "candidate_ids_outside_parent_count",
        "membership_comparisons",
        "sample_design",
        "sample_1000_confusion_current",
        "sample_1000_confusion_nonlinear_exact_diagnostic",
        "sample_100_confusion_current",
        "sample_100_confusion_nonlinear_exact_diagnostic",
    )}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
