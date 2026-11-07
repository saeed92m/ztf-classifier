"""Raw-preserving, versioned quality assessment for ZTF DR24 epochs.

This is a diagnostic policy. It does not remove or modify source rows and it is
not an approved production model-input selection policy.

Source basis:
- ZTF DR24 release notes, section 13.6:
  https://irsa.ipac.caltech.edu/data/ZTF/docs/releases/dr24/ztf_release_notes_dr24.pdf
- IRSA DR24 HATS tutorial:
  https://caltech-ipac.github.io/irsa-tutorials/ztf-lightcurves/
"""
from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from typing import Any

QC_POLICY_ID = "ztf-dr24-raw-qc-diagnostic-v1"
CATFLAGS_BIT_15 = 1 << 15
SOURCE_DOCUMENTS = (
    "https://irsa.ipac.caltech.edu/data/ZTF/docs/releases/dr24/ztf_release_notes_dr24.pdf",
    "https://caltech-ipac.github.io/irsa-tutorials/ztf-lightcurves/",
)


def _finite_number(value: Any) -> bool:
    """Return True for finite JSON numeric values, excluding booleans."""
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def _valid_catflags(value: Any) -> bool:
    """Return True only for a non-negative integer flag value."""
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def assess_dr24_epochs(epochs: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Assess raw DR24 epochs without filtering, sorting, or mutating them.

    "likely_usable" means bit 15 is not set. "strict_clean" means catflags is
    exactly zero. Photometric validity is assessed separately. The combined
    candidate flag is diagnostic only and must not be treated as model QC.
    """
    assessments: list[dict[str, Any]] = []
    counts = {
        "total_epochs": len(epochs),
        "likely_usable_epochs": 0,
        "strict_clean_epochs": 0,
        "photometry_valid_epochs": 0,
        "provisional_analysis_candidates": 0,
        "bit_15_flagged_epochs": 0,
        "invalid_catflags_epochs": 0,
        "invalid_photometry_epochs": 0,
    }

    for index, epoch in enumerate(epochs):
        catflags = epoch.get("catflags")
        flags_valid = _valid_catflags(catflags)
        bit_15_flagged = flags_valid and bool(catflags & CATFLAGS_BIT_15)
        likely_usable = flags_valid and not bit_15_flagged
        strict_clean = flags_valid and catflags == 0

        photometry_reasons: list[str] = []
        for field in ("hmjd", "mag", "magerr"):
            if not _finite_number(epoch.get(field)):
                photometry_reasons.append(f"invalid_{field}")
        if _finite_number(epoch.get("magerr")) and epoch["magerr"] < 0:
            photometry_reasons.append("negative_magerr")
        photometry_valid = not photometry_reasons
        provisional_candidate = likely_usable and photometry_valid

        reasons: list[str] = []
        if not flags_valid:
            reasons.append("missing_or_invalid_catflags")
        elif bit_15_flagged:
            reasons.append("catflags_bit_15_set")
        reasons.extend(photometry_reasons)

        assessments.append(
            {
                "epoch_index": index,
                "catalog_likely_usable": likely_usable,
                "strict_clean": strict_clean,
                "photometry_valid": photometry_valid,
                "provisional_analysis_candidate": provisional_candidate,
                "bit_15_flagged": bit_15_flagged,
                "reasons": reasons,
            }
        )

        counts["likely_usable_epochs"] += int(likely_usable)
        counts["strict_clean_epochs"] += int(strict_clean)
        counts["photometry_valid_epochs"] += int(photometry_valid)
        counts["provisional_analysis_candidates"] += int(provisional_candidate)
        counts["bit_15_flagged_epochs"] += int(bit_15_flagged)
        counts["invalid_catflags_epochs"] += int(not flags_valid)
        counts["invalid_photometry_epochs"] += int(not photometry_valid)

    return {
        "schema_version": "ztf-dr24-qc-assessment-v1",
        "policy_id": QC_POLICY_ID,
        "policy_status": "DIAGNOSTIC_NOT_PRODUCTION_APPROVED",
        "raw_data_mutated": False,
        "epochs": assessments,
        "counts": counts,
        "interpretation": {
            "catalog_likely_usable": "catflags is a non-negative integer and bit 15 (32768) is not set.",
            "strict_clean": "catflags equals zero.",
            "photometry_valid": "hmjd, mag and magerr are finite numbers and magerr is non-negative.",
            "provisional_analysis_candidate": "catalog_likely_usable AND photometry_valid; diagnostic only.",
            "raw_epoch_policy": "No source epoch is deleted, reordered, or modified.",
            "model_policy": "This assessment is not an approved model-input QC or feature-generation policy.",
        },
        "source_documents": list(SOURCE_DOCUMENTS),
    }


__all__ = ["CATFLAGS_BIT_15", "QC_POLICY_ID", "SOURCE_DOCUMENTS", "assess_dr24_epochs"]
