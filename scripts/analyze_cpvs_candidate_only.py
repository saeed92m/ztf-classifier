"""Explain why SNR-qualified CPVS IDs are absent from published Table 4 membership."""

from __future__ import annotations

import argparse
import json
import math
import statistics
from pathlib import Path

from audit_cpvs_membership import read_vizier
from ztf_classifier.validation.derivation import _iter_rows, _source_ids


def collect(path: Path, parent: set[str], band: str, sigma: float) -> dict[str, dict[str, object]]:
    err_key = "e_gmag" if band == "g" else "e_rmag"
    mag_key = "gmag" if band == "g" else "rmag"
    flag_key = f"{band}_flag"
    out: dict[str, dict[str, object]] = {}
    for row in _iter_rows(path, required_columns=("SourceID", err_key, mag_key)):
        oid = row.get("SourceID", "").strip()
        if oid not in parent:
            continue
        try:
            err = float(row.get(err_key, ""))
            mag = float(row.get(mag_key, ""))
        except (TypeError, ValueError):
            continue
        if not math.isfinite(err) or err <= 0 or not math.isfinite(mag) or mag == 0:
            continue
        snr = 1.0857362047581296 / err
        try:
            flag: int | None = int(float(row.get(flag_key, "")))
        except (TypeError, ValueError):
            flag = None
        item = out.setdefault(oid, {
            "n_valid_measurements": 0,
            "max_snr": 0.0,
            "max_snr_error": None,
            "max_snr_magnitude": None,
            "max_snr_flag": None,
            "max_magnitude": -math.inf,
            "min_magnitude": math.inf,
            "n_snr_qualified": 0,
            "n_nonzero_flag_snr_qualified": 0,
            "n_mag_over_20p6_snr_qualified": 0,
        })
        item["n_valid_measurements"] = int(item["n_valid_measurements"]) + 1
        item["min_magnitude"] = min(float(item["min_magnitude"]), mag)
        item["max_magnitude"] = max(float(item["max_magnitude"]), mag)
        if snr >= sigma:
            item["n_snr_qualified"] = int(item["n_snr_qualified"]) + 1
            if flag not in (None, 0):
                item["n_nonzero_flag_snr_qualified"] = int(item["n_nonzero_flag_snr_qualified"]) + 1
            if mag > 20.6:
                item["n_mag_over_20p6_snr_qualified"] = int(item["n_mag_over_20p6_snr_qualified"]) + 1
        if snr > float(item["max_snr"]):
            item["max_snr"] = snr
            item["max_snr_error"] = err
            item["max_snr_magnitude"] = mag
            item["max_snr_flag"] = flag
    return out


def summarize(items: list[dict[str, object]]) -> dict[str, object]:
    if not items:
        return {"count": 0}
    def vals(key: str) -> list[float]:
        return [float(item[key]) for item in items if item.get(key) is not None]
    result: dict[str, object] = {"count": len(items)}
    for key in ("max_snr", "n_valid_measurements", "n_snr_qualified", "n_nonzero_flag_snr_qualified", "n_mag_over_20p6_snr_qualified"):
        values = vals(key)
        if values:
            ordered = sorted(values)
            result[key] = {
                "min": ordered[0],
                "median": statistics.median(ordered),
                "p90": ordered[min(len(ordered) - 1, int(0.90 * len(ordered)))],
                "max": ordered[-1],
            }
    result["max_snr_flag_nonzero_count"] = sum(item.get("max_snr_flag") not in (None, 0) for item in items)
    return result


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--parent", type=Path, required=True)
    p.add_argument("--g", type=Path, required=True)
    p.add_argument("--r", type=Path, required=True)
    p.add_argument("--published", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    parent_ids = {str(x) for x in _source_ids(a.parent, None)}
    published = {str(x) for x in read_vizier(a.published, a.parent)}
    g = collect(a.g, parent_ids, "g", 2.5)
    r = collect(a.r, parent_ids, "r", 3.0)
    candidate = {oid for oid in parent_ids if int(g.get(oid, {}).get("n_snr_qualified", 0)) > 0 and int(r.get(oid, {}).get("n_snr_qualified", 0)) > 0}
    extra = sorted(candidate - published, key=int)
    missing = sorted(published - candidate, key=int)
    details = [{"SourceID": oid, "g": g.get(oid, {}), "r": r.get(oid, {})} for oid in extra]
    report = {
        "status": "DIAGNOSTIC_ONLY",
        "selection": "at least one g measurement with 1.0857362047581296/e_gmag >= 2.5 and at least one r measurement with 1.0857362047581296/e_rmag >= 3.0",
        "parent_count": len(parent_ids),
        "published_count": len(published),
        "candidate_count": len(candidate),
        "candidate_only_count": len(extra),
        "published_only_count": len(missing),
        "candidate_only_summary_g": summarize([g[x] for x in extra if x in g]),
        "candidate_only_summary_r": summarize([r[x] for x in extra if x in r]),
        "published_summary_g": summarize([g[x] for x in published if x in g]),
        "published_summary_r": summarize([r[x] for x in published if x in r]),
        "candidate_only_details": details,
        "published_only_sample": missing[:100],
        "warning": "Diagnostic only. Do not change the scientific predicate until candidate-only objects are explained from source semantics.",
    }
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "candidate_only_details"}, indent=2, sort_keys=True))
    print(f"candidate-only detailed records written: {len(details)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
