"""Descriptive per-row coverage diagnostics for the frozen model feature matrix."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


def _readonly_array(value: np.ndarray, *, dtype: np.dtype) -> np.ndarray:
    array = np.array(value, dtype=dtype, copy=True)
    array.setflags(write=False)
    return array


@dataclass(frozen=True)
class DataAdequacyResult:
    """Descriptive feature-coverage diagnostics; not an eligibility decision.

    This result reports missingness only. It does not declare a partially
    observed object scientifically adequate or inadequate, and it does not
    gate classification or OOD evaluation.
    """

    observed_feature_count: np.ndarray
    missing_feature_count: np.ndarray
    coverage_fraction: np.ndarray
    status: tuple[str, ...]
    missing_feature_names: tuple[tuple[str, ...], ...]
    reason_codes: tuple[tuple[str, ...], ...]
    feature_count: int = 42

    def __post_init__(self) -> None:
        observed = _readonly_array(
            self.observed_feature_count, dtype=np.dtype(np.int64)
        )
        missing = _readonly_array(
            self.missing_feature_count, dtype=np.dtype(np.int64)
        )
        coverage = _readonly_array(
            self.coverage_fraction, dtype=np.dtype(np.float64)
        )
        object.__setattr__(self, "observed_feature_count", observed)
        object.__setattr__(self, "missing_feature_count", missing)
        object.__setattr__(self, "coverage_fraction", coverage)

        if observed.ndim != 1 or missing.ndim != 1 or coverage.ndim != 1:
            raise ValueError("Data adequacy arrays must be one-dimensional.")
        sample_count = len(observed)
        if self.feature_count != 42:
            raise ValueError("Data adequacy requires the frozen 42-feature schema.")
        if len(missing) != sample_count or len(coverage) != sample_count:
            raise ValueError("Data adequacy arrays must have equal lengths.")
        if len(self.status) != sample_count:
            raise ValueError("Data adequacy status must match the sample count.")
        if len(self.missing_feature_names) != sample_count:
            raise ValueError("Missing feature names must match the sample count.")
        if len(self.reason_codes) != sample_count:
            raise ValueError("Reason codes must match the sample count.")
        if not np.isfinite(coverage).all():
            raise ValueError("Coverage fractions must be finite.")
        if ((observed < 0) | (observed > self.feature_count)).any():
            raise ValueError("Observed feature counts are outside the valid range.")
        if ((missing < 0) | (missing > self.feature_count)).any():
            raise ValueError("Missing feature counts are outside the valid range.")
        expected_count = np.full(sample_count, self.feature_count)
        if not np.array_equal(observed + missing, expected_count):
            raise ValueError("Observed and missing feature counts must sum to 42.")
        expected_coverage = observed / self.feature_count
        if not np.allclose(coverage, expected_coverage, rtol=0.0, atol=1e-12):
            raise ValueError("Coverage fractions do not match observed feature counts.")
        expected_status = tuple(
            "complete" if count == self.feature_count else "partial"
            for count in observed
        )
        if self.status != expected_status:
            raise ValueError("Data adequacy status does not match feature coverage.")
        if not all(
            isinstance(names, tuple) for names in self.missing_feature_names
        ):
            raise TypeError("Missing feature names must be tuples.")
        for index, names in enumerate(self.missing_feature_names):
            if len(names) != int(missing[index]):
                raise ValueError("Missing feature names do not match missing counts.")
            if len(set(names)) != len(names):
                raise ValueError("Missing feature names must be unique per row.")
        expected_reasons = tuple(
            () if count == 0 else ("MODEL_FEATURES_MISSING",)
            for count in missing
        )
        if self.reason_codes != expected_reasons:
            raise ValueError("Reason codes do not match feature missingness.")

    @property
    def sample_count(self) -> int:
        """Return the number of assessed rows."""
        return int(self.observed_feature_count.shape[0])

    @classmethod
    def from_matrix(
        cls,
        matrix: np.ndarray,
        feature_names: tuple[str, ...] | list[str],
    ) -> DataAdequacyResult:
        """Build descriptive coverage diagnostics from pre-imputation values."""
        values = np.asarray(matrix, dtype=np.float64)
        names = tuple(str(name) for name in feature_names)
        if values.ndim != 2:
            raise ValueError("Feature matrix must be two-dimensional.")
        if values.shape[1] != 42 or len(names) != 42:
            raise ValueError("Data adequacy requires exactly 42 named features.")
        if len(set(names)) != 42:
            raise ValueError("Feature names must be unique.")
        finite = np.isfinite(values)
        observed = finite.sum(axis=1).astype(np.int64)
        missing = 42 - observed
        coverage = observed.astype(np.float64) / 42.0
        missing_names = tuple(
            tuple(
                name
                for name, is_finite in zip(names, row, strict=True)
                if not is_finite
            )
            for row in finite
        )
        status = tuple(
            "complete" if count == 42 else "partial" for count in observed
        )
        reason_codes = tuple(
            () if count == 42 else ("MODEL_FEATURES_MISSING",)
            for count in observed
        )
        return cls(
            observed_feature_count=observed,
            missing_feature_count=missing,
            coverage_fraction=coverage,
            status=status,
            missing_feature_names=missing_names,
            reason_codes=reason_codes,
        )


__all__ = ["DataAdequacyResult"]
