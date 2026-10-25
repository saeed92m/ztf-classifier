"""Diagnose CPVS 730k selection semantics against the published VizieR membership."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

try:  # executed directly: python scripts/diagnose_cpvs_selection.py
    from audit_cpvs_membership import read_parent_name_map, read_vizier_names
except ImportError:  # imported as scripts.diagnose_cpvs_selection (tests)
    from scripts.audit_cpvs_membership import read_parent_name_map, read_vizier_names

from ztf_classifier.validation.derivation import _iter_rows


def band_metrics(path: Path, parent: set[int], error_key: str, mag_key: str):
    metrics = {
        oid: {"snr": False, "snr1": False, "mag206": False, "mag206_only": False}
        for oid in parent
    }
    threshold = 2.5 if error_key == "e_gmag" else 3.0
    for row in _iter_rows(path, required_columns=("SourceID", error_key, mag_key)):
        raw_oid = row.get("SourceID", "").strip()
        try:
            oid = int(raw_oid)
        except (TypeError, ValueError):
            continue
        if oid not in metrics:
            continue
        try:
            err = float(row.get(error_key, ""))
            mag = float(row.get(mag_key, ""))
        except (TypeError, ValueError):
            continue
        if not math.isfinite(err) or err <= 0 or not math.isfinite(mag) or mag == 0:
            continue
        snr = 1.0857362047581296 / err
        snr1 = 1.0 / err
        metrics[oid]["snr"] |= snr >= threshold
        metrics[oid]["snr1"] |= snr1 >= threshold
        metrics[oid]["mag206"] |= mag <= 20.6 and snr >= threshold
        metrics[oid]["mag206_only"] |= mag <= 20.6
    return metrics


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--parent", type=Path, required=True)
    p.add_argument("--g", type=Path, required=True)
    p.add_argument("--r", type=Path, required=True)
    p.add_argument("--published", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument(
        "--expect-parent-count",
        type=int,
        default=781_602,
        help=(
            "Fail-closed guard on the parent catalogue size. The default is the "
            "published CPVS count and must not be lowered for a real run; it is "
            "overridable only so the diagnostic can be smoke-tested on fixtures."
        ),
    )
    a = p.parse_args()

    # Published membership is resolved through the DOCUMENTED object-name join
    # against the parent crosswalk, not through table4's internal ID column.
    # The previous implementation called read_vizier(), which joined table4.ID
    # to parent SourceID. That treats the equivalence of table4.ID and
    # table2.Seq as established; no retrieved source states it (see
    # docs/CPVS_RESOLUTION_STATUS_2026-10-25.md section 5.2), so it is only a
    # corroborating cross-check and must not be the primary route.
    #
    # The parent side now also uses the documented Seq column rather than a row
    # ordinal. table2 has 781,602 rows while Seq spans [1/781604], so ordinals
    # diverge from Seq after the first gap.
    parent_name_map = read_parent_name_map(a.parent)
    parent = set(parent_name_map.values())
    if len(parent) != a.expect_parent_count:
        raise ValueError(
            f"expected {a.expect_parent_count} parent SourceIDs, got {len(parent)}"
        )

    published_names = read_vizier_names(a.published)
    unmapped = sorted(published_names - set(parent_name_map))
    if unmapped:
        raise ValueError(
            f"{len(unmapped)} published names are absent from the parent "
            f"catalogue, examples={unmapped[:10]}"
        )
    published = {parent_name_map[name] for name in published_names}
    g = band_metrics(a.g, parent, "e_gmag", "gmag")
    r = band_metrics(a.r, parent, "e_rmag", "rmag")
    predicates = {
        "baseline_1p085": {o for o in parent if g[o]["snr"] and r[o]["snr"]},
        "baseline_1p0": {o for o in parent if g[o]["snr1"] and r[o]["snr1"]},
        "baseline_plus_mag206": {
            o for o in parent if g[o]["mag206"] and r[o]["mag206"]
        },
        "baseline_plus_rmag206": {
            o for o in parent if g[o]["snr"] and r[o]["snr"] and r[o]["mag206_only"]
        },
    }
    report = {}
    for name, ids in predicates.items():
        report[name] = {
            "count": len(ids),
            "published_intersection": len(ids & published),
            "candidate_only": len(ids - published),
            "published_only": len(published - ids),
        }
    # allow_nan=False makes non-standard JSON impossible rather than merely
    # unlikely: RFC 8259 has no NaN or Infinity literals, and Python's encoder
    # emits them by default. If a non-finite value ever reaches this boundary
    # the run fails loudly instead of writing an artifact that json.loads() in
    # other toolchains will reject.
    report_json = json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n"
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(report_json, encoding="utf-8")
    print(report_json, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
