#!/usr/bin/env python3
"""Diagnostic-only attribution of CPVS candidate IDs to non-finite SNR rows."""
from __future__ import annotations
import argparse, json, math, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT)]
from ztf_classifier.validation.derivation import _find_key, _iter_rows, _snr_from_mag_error, _source_ids
from scripts.audit_cpvs_membership import read_selected, read_vizier


def trace(path, parent_ids, sigma, band, member):
    errors = ("e_gmag", "magerr", "mag_err", "error") if band == "g" else ("e_rmag", "magerr", "mag_err", "error")
    mags = ("gmag",) if band == "g" else ("rmag",)
    rows = _iter_rows(path, member, required_columns=("SourceID", *errors, *mags))
    first = next(rows, None)
    if first is None:
        raise ValueError(f"{band}-band input has no data rows: {path}")
    id_key = _find_key(first, ("SourceID", "sourceid", "oid", "ztf_id"))
    error_key = _find_key(first, errors)
    mag_key = _find_key(first, mags)
    legacy, finite, nonfinite, invalid_mag = set(), set(), set(), set()
    nonfinite_rows = qualifying_rows = 0
    def all_rows():
        yield first
        yield from rows
    for row in all_rows():
        oid = row.get(id_key, "").strip()
        if oid not in parent_ids:
            continue
        snr = _snr_from_mag_error(row.get(error_key, ""))
        try:
            mag = float(row.get(mag_key, ""))
        except (TypeError, ValueError):
            mag = float("nan")
        if not math.isfinite(mag) or mag == 0.0:
            invalid_mag.add(oid)
        if not math.isfinite(snr):
            nonfinite_rows += 1
            # Historical negative-only predicate admits NaN because NaN < sigma is false.
            legacy.add(oid)
            nonfinite.add(oid)
        elif snr >= sigma:
            qualifying_rows += 1
            legacy.add(oid)
            finite.add(oid)
    return {
        "legacy_ids": legacy, "finite_ids": finite, "nonfinite_ids": nonfinite,\n        "nonfinite_only_ids": nonfinite - finite,
        "invalid_magnitude_ids": invalid_mag, "nonfinite_snr_rows": nonfinite_rows,
        "finite_qualifying_rows": qualifying_rows, "sigma": sigma, "input": str(path),
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--parent", type=Path, required=True)
    p.add_argument("--g-lightcurve", type=Path, required=True)
    p.add_argument("--r-lightcurve", type=Path, required=True)
    p.add_argument("--candidate", type=Path, required=True)
    p.add_argument("--published", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--parent-member")
    p.add_argument("--g-member")
    p.add_argument("--r-member")
    p.add_argument("--g-sigma", type=float, default=2.5)
    p.add_argument("--r-sigma", type=float, default=3.0)
    a = p.parse_args()
    parent = _source_ids(a.parent, a.parent_member)
    candidate = {str(value) for value in read_selected(a.candidate)}
    published = {str(value) for value in read_vizier(a.published)}
    g = trace(a.g_lightcurve, parent, a.g_sigma, "g", a.g_member)
    r = trace(a.r_lightcurve, parent, a.r_sigma, "r", a.r_member)
    cand_only = candidate - published
    g_old, r_old = g["legacy_ids"], r["legacy_ids"]
    g_finite, r_finite = g["finite_ids"], r["finite_ids"]
    g_bad, r_bad = g["nonfinite_only_ids"], r["nonfinite_only_ids"]
    legacy_intersection, finite_intersection = g_old & r_old, g_finite & r_finite
    report = {
        "diagnostic_only": True, "selection_rule_changed": False,
        "parent_id_count": len(parent), "candidate_id_count": len(candidate),
        "published_id_count": len(published), "candidate_only_count": len(cand_only),
        "published_only_count": len(published - candidate),
        "candidate_only_ids": sorted(cand_only),
        "g_band": {"nonfinite_snr_rows": g["nonfinite_snr_rows"], "finite_qualifying_rows": g["finite_qualifying_rows"], "nonfinite_admitted_id_count": len(g["nonfinite_ids"]), "nonfinite_only_id_count": len(g_bad)},
        "r_band": {"nonfinite_snr_rows": r["nonfinite_snr_rows"], "finite_qualifying_rows": r["finite_qualifying_rows"], "nonfinite_admitted_id_count": len(r["nonfinite_ids"]), "nonfinite_only_id_count": len(r_bad)},
        "legacy_snr_intersection_count": len(legacy_intersection),
        "finite_snr_intersection_count": len(finite_intersection),
        "legacy_intersection_removed_by_finite_guard": sorted(legacy_intersection - finite_intersection),
        "candidate_only_with_nonfinite_g": sorted(cand_only & g_bad),
        "candidate_only_with_nonfinite_r": sorted(cand_only & r_bad),
        "candidate_only_with_nonfinite_either_band": sorted(cand_only & (g_bad | r_bad)),
        "candidate_only_with_nonfinite_both_bands": sorted(cand_only & g_bad & r_bad),
        "interpretation": "SNR-stage attribution only; replay the magnitude predicate and reproduce with exact pinned inputs before asserting root cause."
    }
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k:v for k,v in report.items() if not k.endswith("_ids")}, indent=2, sort_keys=True))
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
