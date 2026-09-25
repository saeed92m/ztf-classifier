"""Canonical scientific observation contracts for ZTF light curves."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class Observation:
    """One normalized ZTF photometric observation."""

    mjd: float
    fid: int
    mag: float
    magerr: float
    mag_raw: float | None
    magerr_raw: float | None
    mag_corr: float | None
    magerr_corr: float | None
    photometry_source: str
    ra: float
    dec: float
    dubious: bool
    corrected: bool

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe observation record."""
        return asdict(self)


@dataclass(frozen=True)
class ObservationProvenance:
    """Acquisition and normalization provenance for an observation query."""

    source: str
    survey: str
    cache_hit: bool
    diagnostics: dict[str, int]

    def to_dict(self) -> dict[str, Any]:
        """Return provenance as a JSON-safe mapping."""
        return asdict(self)


@dataclass(frozen=True)
class ObjectObservationSummary:
    """Object-level summary derived only from normalized observations."""

    oid: str
    observation_count: int
    mjd_min: float
    mjd_max: float
    filters: tuple[int, ...]
    ra: float | None
    dec: float | None
    provenance: ObservationProvenance

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe object summary."""
        return {
            "oid": self.oid,
            "observation_count": self.observation_count,
            "mjd_min": self.mjd_min,
            "mjd_max": self.mjd_max,
            "filters": list(self.filters),
            "ra": self.ra,
            "dec": self.dec,
            "provenance": self.provenance.to_dict(),
        }
