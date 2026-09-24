"""Validation of canonical raw ZTF light-curve datasets."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd

DETECTION_REQUIRED_COLUMNS = frozenset({"mjd", "fid"})
NON_DETECTION_REQUIRED_COLUMNS = frozenset({"mjd", "fid", "diffmaglim"})

EXPECTED_DETECTION_SCHEMA = (
    "tid",
    "mjd",
    "candid",
    "fid",
    "pid",
    "diffmaglim",
    "isdiffpos",
    "nid",
    "distnr",
    "magpsf",
    "magpsf_corr",
    "magpsf_corr_ext",
    "magap",
    "magap_corr",
    "sigmapsf",
    "sigmapsf_corr",
    "sigmapsf_corr_ext",
    "sigmagap",
    "sigmagap_corr",
    "ra",
    "dec",
    "rb",
    "rbversion",
    "drb",
    "magapbig",
    "sigmagapbig",
    "rfid",
    "has_stamp",
    "corrected",
    "dubious",
    "candid_alert",
    "step_id_corr",
    "phase",
    "parent_candid",
)

EXPECTED_NON_DETECTION_SCHEMA = (
    "tid",
    "mjd",
    "fid",
    "diffmaglim",
)


@dataclass(frozen=True)
class RawDatasetValidationResult:
    """Machine-readable result of raw dataset validation."""

    status: str
    canonical_objects: int
    cache_objects: int
    missing_oids: tuple[str, ...]
    extra_oids: tuple[str, ...]
    incomplete_pairs: tuple[str, ...]
    schema_mismatches: tuple[str, ...]
    invalid_required_values: tuple[str, ...]
    detection_schema: tuple[str, ...]
    non_detection_schema: tuple[str, ...]
    fid_distribution: dict[str, int]
    fid_set_distribution: dict[str, int]
    ordering: dict[str, Any]
    detection_row_statistics: dict[str, float]
    non_detection_row_statistics: dict[str, float]
    low_observation_objects_lt10: tuple[str, ...]
    low_observation_objects_lt30: tuple[str, ...]
    corrected_statistics: dict[str, int]
    errors: tuple[str, ...] = field(default_factory=tuple)

    @property
    def passed(self) -> bool:
        """Return whether the raw dataset passed structural validation."""
        return self.status == "PASS"

    def to_dict(self) -> dict[str, Any]:
        """Serialize the validation result to JSON-compatible data."""
        return {
            "status": self.status,
            "canonical_objects": self.canonical_objects,
            "cache_objects": self.cache_objects,
            "missing_oids": list(self.missing_oids),
            "extra_oids": list(self.extra_oids),
            "incomplete_pairs": list(self.incomplete_pairs),
            "schema_mismatches": list(self.schema_mismatches),
            "invalid_required_values": list(self.invalid_required_values),
            "detection_schema": list(self.detection_schema),
            "non_detection_schema": list(self.non_detection_schema),
            "fid_distribution": self.fid_distribution,
            "fid_set_distribution": self.fid_set_distribution,
            "ordering": self.ordering,
            "detection_row_statistics": self.detection_row_statistics,
            "non_detection_row_statistics": self.non_detection_row_statistics,
            "low_observation_objects_lt10": list(
                self.low_observation_objects_lt10
            ),
            "low_observation_objects_lt30": list(
                self.low_observation_objects_lt30
            ),
            "corrected_statistics": self.corrected_statistics,
            "errors": list(self.errors),
        }


class RawDatasetValidator:
    """Validate raw ZTF cache data against canonical object identifiers."""

    def __init__(
        self,
        *,
        canonical_oids: set[str] | tuple[str, ...] | list[str],
        cache_dir: str | Path,
    ) -> None:
        self._canonical_oids = frozenset(str(oid) for oid in canonical_oids)
        self._cache_dir = Path(cache_dir)

    def validate(self) -> RawDatasetValidationResult:
        """Validate the complete raw cache contract."""

        cache_detection_oids = self._discover_oids("_detections.parquet")
        cache_non_detection_oids = self._discover_oids(
            "_non_detections.parquet"
        )
        cache_oids = cache_detection_oids | cache_non_detection_oids

        missing = tuple(
            sorted(self._canonical_oids - cache_oids)
        )
        extra = tuple(
            sorted(cache_oids - self._canonical_oids)
        )

        incomplete = tuple(
            sorted(cache_detection_oids ^ cache_non_detection_oids)
        )

        schema_mismatches: list[str] = []
        invalid_required_values: list[str] = []
        fid_distribution: dict[str, int] = {}
        fid_set_distribution: dict[str, int] = {}
        ordering_failures_detection: list[str] = []
        ordering_failures_non_detection: list[str] = []
        detection_rows: list[int] = []
        non_detection_rows: list[int] = []
        low_lt10: list[str] = []
        low_lt30: list[str] = []
        corrected_total = 0
        raw_fallback_total = 0

        canonical_existing = sorted(
            self._canonical_oids & cache_oids
        )

        detection_schema: tuple[str, ...] = ()
        non_detection_schema: tuple[str, ...] = ()

        for oid in canonical_existing:
            detection_path = (
                self._cache_dir / f"{oid}_detections.parquet"
            )
            non_detection_path = (
                self._cache_dir / f"{oid}_non_detections.parquet"
            )

            if not detection_path.exists() or not non_detection_path.exists():
                continue

            try:
                detections = pd.read_parquet(detection_path)
                non_detections = pd.read_parquet(non_detection_path)
            except (OSError, ValueError) as exc:
                schema_mismatches.append(
                    f"{oid}: unreadable parquet: {exc}"
                )
                continue

            if not detection_schema:
                detection_schema = tuple(detections.columns)

            if not non_detection_schema:
                non_detection_schema = tuple(
                    non_detections.columns
                )

            if tuple(detections.columns) != EXPECTED_DETECTION_SCHEMA:
                schema_mismatches.append(
                    f"{oid}: detection schema mismatch"
                )

            if (
                tuple(non_detections.columns)
                != EXPECTED_NON_DETECTION_SCHEMA
            ):
                schema_mismatches.append(
                    f"{oid}: non-detection schema mismatch"
                )

            if not DETECTION_REQUIRED_COLUMNS.issubset(
                detections.columns
            ):
                invalid_required_values.append(
                    f"{oid}: missing detection required columns"
                )

            if not NON_DETECTION_REQUIRED_COLUMNS.issubset(
                non_detections.columns
            ):
                invalid_required_values.append(
                    f"{oid}: missing non-detection required columns"
                )

            if not {"mjd", "fid"}.issubset(detections.columns):
                continue

            mjd = pd.to_numeric(detections["mjd"], errors="coerce")
            fid = pd.to_numeric(detections["fid"], errors="coerce")

            invalid_mjd = mjd.isna() | ~mjd.map(
                lambda value: pd.notna(value) and pd.api.types.is_number(value)
            )
            invalid_mjd |= mjd.map(
                lambda value: pd.notna(value) and not pd.api.types.is_number(value)
            )

            invalid_fid = fid.isna() | ~fid.map(
                lambda value: pd.notna(value) and pd.api.types.is_number(value)
            )

            if invalid_mjd.any():
                invalid_required_values.append(
                    f"{oid}: invalid detection mjd"
                )

            if invalid_fid.any():
                invalid_required_values.append(
                    f"{oid}: invalid detection fid"
                )

            if (
                not invalid_mjd.any()
                and not detections.empty
                and not mjd.is_monotonic_increasing
            ):
                ordering_failures_detection.append(oid)

            if not non_detections.empty and {
                "mjd",
                "fid",
            }.issubset(non_detections.columns):
                nd_mjd = pd.to_numeric(
                    non_detections["mjd"],
                    errors="coerce",
                )
                nd_fid = pd.to_numeric(
                    non_detections["fid"],
                    errors="coerce",
                )

                invalid_nd_mjd = nd_mjd.isna() | ~nd_mjd.map(
                    lambda value: pd.notna(value) and pd.api.types.is_number(value)
                )
                invalid_nd_fid = nd_fid.isna() | ~nd_fid.map(
                    lambda value: pd.notna(value) and pd.api.types.is_number(value)
                )

                if invalid_nd_mjd.any():
                    invalid_required_values.append(
                        f"{oid}: invalid non-detection mjd"
                    )

                if invalid_nd_fid.any():
                    invalid_required_values.append(
                        f"{oid}: invalid non-detection fid"
                    )

                if (
                    not invalid_nd_mjd.any()
                    and not non_detections.empty
                    and not nd_mjd.is_monotonic_increasing
                ):
                    ordering_failures_non_detection.append(oid)

            detection_count = len(detections)
            non_detection_count = len(non_detections)

            detection_rows.append(detection_count)
            non_detection_rows.append(non_detection_count)

            if detection_count < 10:
                low_lt10.append(oid)

            if detection_count < 30:
                low_lt30.append(oid)

            for value in sorted(
                fid.dropna().unique().tolist()
            ):
                key = str(int(value)) if float(value).is_integer() else str(value)
                fid_distribution[key] = (
                    fid_distribution.get(key, 0) + 1
                )

            fid_values = sorted(
                {
                    int(value)
                    if float(value).is_integer()
                    else float(value)
                    for value in fid.dropna().unique().tolist()
                }
            )
            fid_set_key = ",".join(str(value) for value in fid_values)

            if fid_set_key:
                fid_set_distribution[fid_set_key] = (
                    fid_set_distribution.get(fid_set_key, 0) + 1
                )

            if "corrected" in detections.columns:
                corrected = detections["corrected"].astype("boolean")
                corrected_total += int(corrected.fillna(False).sum())
                raw_fallback_total += int(
                    corrected.fillna(False).eq(False).sum()
                )

        errors = tuple(
            list(missing)
            + list(incomplete)
            + list(schema_mismatches)
            + list(invalid_required_values)
        )

        status = "PASS" if not errors else "FAIL"

        return RawDatasetValidationResult(
            status=status,
            canonical_objects=len(self._canonical_oids),
            cache_objects=len(cache_oids),
            missing_oids=missing,
            extra_oids=extra,
            incomplete_pairs=incomplete,
            schema_mismatches=tuple(schema_mismatches),
            invalid_required_values=tuple(
                invalid_required_values
            ),
            detection_schema=detection_schema,
            non_detection_schema=non_detection_schema,
            fid_distribution=dict(sorted(fid_distribution.items())),
            fid_set_distribution=dict(
                sorted(
                    fid_set_distribution.items(),
                    key=lambda item: tuple(
                        int(value) for value in item[0].split(",")
                    ),
                )
            ),
            ordering={
                "detections_sorted_by_mjd": not ordering_failures_detection,
                "non_detections_sorted_by_mjd": not ordering_failures_non_detection,
                "detection_ordering_failures": tuple(
                    sorted(ordering_failures_detection)
                ),
                "non_detection_ordering_failures": tuple(
                    sorted(ordering_failures_non_detection)
                ),
            },
            detection_row_statistics=self._statistics(detection_rows),
            non_detection_row_statistics=self._statistics(
                non_detection_rows
            ),
            low_observation_objects_lt10=tuple(low_lt10),
            low_observation_objects_lt30=tuple(low_lt30),
            corrected_statistics={
                "corrected_true": corrected_total,
                "corrected_false": raw_fallback_total,
            },
            errors=errors,
        )

    def _discover_oids(self, suffix: str) -> set[str]:
        """Discover object IDs from cache filenames."""
        if not self._cache_dir.exists():
            return set()

        result: set[str] = set()

        for path in self._cache_dir.iterdir():
            if not path.is_file():
                continue

            name = path.name

            if suffix == "_detections.parquet":
                if (
                    not name.endswith(suffix)
                    or name.endswith("_non_detections.parquet")
                ):
                    continue
            elif not name.endswith(suffix):
                continue

            oid = name[: -len(suffix)]

            if oid:
                result.add(oid)

        return result

    @staticmethod
    def _statistics(values: list[int]) -> dict[str, float]:
        """Return deterministic descriptive row-count statistics."""
        if not values:
            return {
                "count": 0,
                "min": 0,
                "median": 0,
                "max": 0,
                "mean": 0.0,
            }

        series = pd.Series(values, dtype="int64")

        return {
            "count": int(series.count()),
            "min": int(series.min()),
            "median": float(series.median()),
            "max": int(series.max()),
            "mean": float(series.mean()),
        }
