"""Compare CPVS full-catalog and object-grouped batch decisions.

This diagnostic tool uses the same published CPVS predicate as derivation.py:
finite non-zero magnitude and SNR >= 2.5 in g / >= 3.0 in r. It never changes
selection policy. The two paths are intentionally separate passes over the
source light curves so batch-boundary errors can be detected.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections.abc import Iterable
from itertools import chain
from pathlib import Path

from ztf_classifier.validation.derivation import (
    _find_key,
    _iter_rows,
    _snr_from_mag_error,
)


def read_ids(path: Path) -> set[str]:
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    if lines and lines[0].strip().lower() in {"sourceid", "source_id", "id"}:
        lines = lines[1:]
    values = {line.strip() for line in lines if line.strip()}
    if not values or any(not value.isdigit() for value in values):
        raise ValueError(f"{path} must contain numeric SourceIDs")
    return values


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _band_values(path: Path, band: str) -> Iterable[tuple[str, float, float]]:
    error = "e_gmag" if band == "g" else "e_rmag"
    magnitude = "gmag" if band == "g" else "rmag"
    rows = _iter_rows(path, required_columns=("SourceID", error, magnitude))
    first = next(rows, None)
    if first is None:
        return
    id_key = _find_key(first, ("SourceID", "sourceid", "oid", "ztf_id"))
    error_key = _find_key(first, (error,))
    magnitude_key = _find_key(first, (magnitude,))
    for row in chain((first,), rows):
        try:
            yield (
                row.get(id_key, "").strip(),
                float(row.get(magnitude_key, "")),
                float(row.get(error_key, "")),
            )
        except (TypeError, ValueError):
            yield row.get(id_key, "").strip(), float("nan"), float("nan")


def _row_qualified(
    oid: str,
    magnitude: float,
    error: float,
    *,
    parent: set[str],
    sigma: float,
) -> tuple[str | None, bool]:
    snr = _snr_from_mag_error(str(error))
    # Match the production derivation's fail-closed handling: NaN < sigma is
    # False in Python, so a negative-only comparison would admit invalid SNR.
    if oid not in parent or not math.isfinite(snr) or snr < sigma:
        return None, False
    return oid, bool(math.isfinite(magnitude) and magnitude != 0.0)


def band_full(
    path: Path,
    *,
    parent: set[str],
    band: str,
    sigma: float,
) -> tuple[set[str], set[str], int, int]:
    snr: set[str] = set()
    valid: set[str] = set()
    rows = qualified_rows = 0
    for oid, magnitude, error in _band_values(path, band):
        rows += 1
        qualified_oid, valid_magnitude = _row_qualified(
            oid, magnitude, error, parent=parent, sigma=sigma
        )
        if qualified_oid is not None:
            snr.add(qualified_oid)
            qualified_rows += 1
            if valid_magnitude:
                valid.add(qualified_oid)
    return snr, valid, rows, qualified_rows


def band_batch(
    path: Path,
    *,
    parent: set[str],
    band: str,
    sigma: float,
    batch_rows: int,
) -> tuple[set[str], set[str], int, int, int]:
    snr: set[str] = set()
    valid: set[str] = set()
    batch_snr: set[str] = set()
    batch_valid: set[str] = set()
    rows = qualified_rows = batches = 0
    for oid, magnitude, error in _band_values(path, band):
        rows += 1
        qualified_oid, valid_magnitude = _row_qualified(
            oid, magnitude, error, parent=parent, sigma=sigma
        )
        if qualified_oid is not None:
            batch_snr.add(qualified_oid)
            qualified_rows += 1
            if valid_magnitude:
                batch_valid.add(qualified_oid)
        if rows % batch_rows == 0:
            snr.update(batch_snr)
            valid.update(batch_valid)
            batch_snr.clear()
            batch_valid.clear()
            batches += 1
    if batch_snr or batch_valid:
        snr.update(batch_snr)
        valid.update(batch_valid)
        batches += 1
    return snr, valid, rows, qualified_rows, batches


def write_decisions(path: Path, parent: set[str], selected: set[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(("SourceID", "selected"))
        for oid in sorted(parent, key=int):
            writer.writerow((oid, str(oid in selected).lower()))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--parent-ids", type=Path, required=True)
    parser.add_argument("--g-lightcurve", type=Path, required=True)
    parser.add_argument("--r-lightcurve", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--batch-rows", type=int, default=250_000)
    args = parser.parse_args()
    if args.batch_rows <= 0:
        parser.error("--batch-rows must be positive")
    parent = read_ids(args.parent_ids)
    if len(parent) != 781_602:
        raise ValueError(f"expected 781602 parent IDs, got {len(parent)}")
    args.output_dir.mkdir(parents=True, exist_ok=True)

    full_g_snr, full_g_valid, g_rows, g_qualified = band_full(
        args.g_lightcurve, parent=parent, band="g", sigma=2.5
    )
    full_r_snr, full_r_valid, r_rows, r_qualified = band_full(
        args.r_lightcurve, parent=parent, band="r", sigma=3.0
    )
    batch_g_snr, batch_g_valid, bg_rows, bg_qualified, g_batches = band_batch(
        args.g_lightcurve,
        parent=parent,
        band="g",
        sigma=2.5,
        batch_rows=args.batch_rows,
    )
    batch_r_snr, batch_r_valid, br_rows, br_qualified, r_batches = band_batch(
        args.r_lightcurve,
        parent=parent,
        band="r",
        sigma=3.0,
        batch_rows=args.batch_rows,
    )

    full = (full_g_snr & full_g_valid) & (full_r_snr & full_r_valid)
    batch = (batch_g_snr & batch_g_valid) & (batch_r_snr & batch_r_valid)
    full_path = args.output_dir / "full_decisions.csv"
    batch_path = args.output_dir / "batch_decisions.csv"
    write_decisions(full_path, parent, full)
    write_decisions(batch_path, parent, batch)
    disagreements = sorted(full ^ batch, key=int)
    report = {
        "status": "PASS" if not disagreements else "FAIL",
        "grouping_key": "complete CPVS SourceID; never light-curve row position",
        "predicate": "finite non-zero magnitude and SNR >= 2.5 (g) / >= 3.0 (r)",
        "parent_object_count": len(parent),
        "full_selected_count": len(full),
        "batch_selected_count": len(batch),
        "disagreement_count": len(disagreements),
        "disagreement_source_ids": disagreements,
        "full_metadata": {
            "g_rows": g_rows,
            "g_qualified_rows": g_qualified,
            "r_rows": r_rows,
            "r_qualified_rows": r_qualified,
        },
        "batch_metadata": {
            "g_rows": bg_rows,
            "g_qualified_rows": bg_qualified,
            "g_batches": g_batches,
            "r_rows": br_rows,
            "r_qualified_rows": br_qualified,
            "r_batches": r_batches,
            "batch_rows": args.batch_rows,
        },
        "decision_sha256": {
            "full_decisions_sha256": sha256(full_path),
            "batch_decisions_sha256": sha256(batch_path),
        },
        "input_parent_ids_sha256": sha256(args.parent_ids),
        "source_paths": {"g": str(args.g_lightcurve), "r": str(args.r_lightcurve)},
        "caveat": "Published membership is a comparison reference, not independent astrophysical ground truth.",
    }
    (args.output_dir / "full_batch_comparison.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
