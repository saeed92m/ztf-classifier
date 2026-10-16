"""Pure TESS QUALITY bitmask assessment; never silently drops source rows."""

from collections.abc import Iterable
from dataclasses import dataclass
from numbers import Integral


DEFAULT_TESS_QUALITY_MASK = 21183


@dataclass(frozen=True)
class QualityMaskAssessment:
    """Row-aligned assessment. The source rows remain untouched."""

    bitmask: int
    accepted: tuple[bool, ...]
    reasons: tuple[str | None, ...]

    @property
    def accepted_count(self) -> int:
        return sum(self.accepted)

    @property
    def rejected_count(self) -> int:
        return len(self.accepted) - self.accepted_count

    def to_dict(self) -> dict[str, object]:
        reason_counts: dict[str, int] = {}
        for reason in self.reasons:
            if reason is not None:
                reason_counts[reason] = reason_counts.get(reason, 0) + 1
        return {
            "bitmask": self.bitmask,
            "row_count": len(self.accepted),
            "accepted_count": self.accepted_count,
            "rejected_count": self.rejected_count,
            "rejection_reason_counts": reason_counts,
        }


def assess_tess_quality_flags(
    quality_values: Iterable[int], *, bitmask: int = DEFAULT_TESS_QUALITY_MASK
) -> QualityMaskAssessment:
    """Assess QUALITY values using the bitwise rule (quality & mask) == 0.

    Returns a boolean and reason for every input row, preserving positional
    alignment with the original light curve. This function does not mutate or
    remove rows, and it does not assess NaN/Inf values in TIME or flux columns.
    Invalid or missing QUALITY values fail closed with ValueError.
    """
    if isinstance(bitmask, bool) or not isinstance(bitmask, Integral) or bitmask < 0:
        raise ValueError("bitmask must be a non-negative integer")

    accepted: list[bool] = []
    reasons: list[str | None] = []
    for index, value in enumerate(quality_values):
        if isinstance(value, bool) or not isinstance(value, Integral) or value < 0:
            raise ValueError(f"QUALITY value at row {index} must be a non-negative integer")
        passes = (int(value) & int(bitmask)) == 0
        accepted.append(passes)
        reasons.append(None if passes else "quality_mask_nonzero")
    return QualityMaskAssessment(
        bitmask=int(bitmask), accepted=tuple(accepted), reasons=tuple(reasons)
    )
