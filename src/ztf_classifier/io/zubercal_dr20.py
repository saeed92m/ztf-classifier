"""Bounded, ambiguity-preserving access to Zubercal DR20 HATS.

This adapter returns PS1-matched Zubercal detections around a DR24 source
position. It never equates a PS1 object ID with a ZTF OID and never chooses
one candidate when multiple PS1 IDs are returned.
"""
from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from typing import Any

ZUBERCAL_DR20_HATS_URL = "https://data.lsdb.io/hats/ztf_dr20/zubercal/"
ZUBERCAL_DR20_COLUMNS = (
    "objectid",
    "mjd",
    "band",
    "mag",
    "magerr",
    "fieldid",
    "rcidin",
    "info",
    "flag",
    "objra",
    "objdec",
)
DEFAULT_MATCH_RADIUS_ARCSEC = 1.2
MAX_MATCH_RADIUS_ARCSEC = 1.2
MAX_RETURNED_ROWS = 5000


@dataclass(frozen=True)
class ZubercalDR20Request:
    """A bounded cone query centered on a DR24 OID position."""

    ztf_objectid: int
    ra_deg: float
    dec_deg: float
    radius_arcsec: float = DEFAULT_MATCH_RADIUS_ARCSEC

    def __post_init__(self) -> None:
        if (
            not isinstance(self.ztf_objectid, int)
            or isinstance(self.ztf_objectid, bool)
            or self.ztf_objectid <= 0
        ):
            raise ValueError("ztf_objectid must be a positive integer.")
        if (
            not isinstance(self.ra_deg, (int, float))
            or isinstance(self.ra_deg, bool)
            or not math.isfinite(self.ra_deg)
            or not 0.0 <= self.ra_deg < 360.0
        ):
            raise ValueError("ra_deg must be finite and in [0, 360).")
        if (
            not isinstance(self.dec_deg, (int, float))
            or isinstance(self.dec_deg, bool)
            or not math.isfinite(self.dec_deg)
            or not -90.0 <= self.dec_deg <= 90.0
        ):
            raise ValueError("dec_deg must be finite and in [-90, 90].")
        if (
            not isinstance(self.radius_arcsec, (int, float))
            or isinstance(self.radius_arcsec, bool)
            or not math.isfinite(self.radius_arcsec)
            or self.radius_arcsec <= 0.0
            or self.radius_arcsec > MAX_MATCH_RADIUS_ARCSEC
        ):
            raise ValueError("radius_arcsec must be in (0, 1.2].")


@dataclass(frozen=True)
class ZubercalDR20Result:
    """Raw Zubercal rows plus candidate summaries and immutable provenance."""

    ztf_objectid: int
    query: dict[str, Any]
    raw_rows: tuple[dict[str, Any], ...]
    row_annotations: tuple[dict[str, Any], ...]
    candidate_summary: tuple[dict[str, Any], ...]
    match_state: str
    payload_sha256: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "ztf-zubercal-dr20-crossmatch-v1",
            "source_release": "Zubercal DR20",
            "source": ZUBERCAL_DR20_HATS_URL,
            "ztf_objectid": self.ztf_objectid,
            "query": dict(self.query),
            "match_state": self.match_state,
            "crossmatch_decision": "NOT_SELECTED",
            "candidate_summary": [dict(item) for item in self.candidate_summary],
            "row_annotations": [dict(item) for item in self.row_annotations],
            "raw_rows": [dict(row) for row in self.raw_rows],
            "provenance": {
                "row_count": len(self.raw_rows),
                "candidate_ps1_id_count": len(self.candidate_summary),
                "payload_sha256": self.payload_sha256,
                "payload_hash_scope": "raw rows, canonical sorted order",
                "payload_hash_algorithm": "SHA-256",
                "raw_rows_preserved": True,
            },
            "semantics": {
                "objectid": "PS1 object ID; not a ZTF OID",
                "mjd": "MJD(TDB)",
                "magerr_raw_scale": "integer in 1e-4 mag units",
                "magerr_conversion": "magerr_raw / 10000",
                "flag_fields": ["flag", "info"],
                "flag_fields_are_not": "DR24 catflags",
            },
        }


def _json_scalar(value: Any) -> Any:
    """Convert common NumPy/Pandas scalars to JSON-safe Python values."""
    if value is None:
        return None
    if hasattr(value, "item"):
        value = value.item()
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def summarize_zubercal_rows(
    rows: list[dict[str, Any]] | tuple[dict[str, Any], ...],
    *,
    ztf_objectid: int,
    ra_deg: float,
    dec_deg: float,
    radius_arcsec: float,
) -> ZubercalDR20Result:
    """Summarize candidate PS1 IDs without selecting or merging a candidate."""
    from astropy import units as u
    from astropy.coordinates import SkyCoord

    ZubercalDR20Request(
        ztf_objectid=ztf_objectid,
        ra_deg=ra_deg,
        dec_deg=dec_deg,
        radius_arcsec=radius_arcsec,
    )
    center = SkyCoord(ra=ra_deg * u.deg, dec=dec_deg * u.deg, frame="icrs")
    normalized_rows: list[dict[str, Any]] = []
    row_annotations: list[dict[str, Any]] = []
    distances: dict[int, list[float]] = {}
    bands: dict[int, set[str]] = {}

    for raw in rows:
        row = {key: _json_scalar(value) for key, value in raw.items()}
        ps1_id = row.get("objectid")
        row_ra = row.get("objra")
        row_dec = row.get("objdec")
        if not isinstance(ps1_id, int) or isinstance(ps1_id, bool) or ps1_id <= 0:
            raise ValueError("Zubercal row has an invalid PS1 objectid.")
        if row_ra is None or row_dec is None:
            raise ValueError("Zubercal row is missing objra/objdec.")
        if (
            isinstance(row_ra, bool)
            or isinstance(row_dec, bool)
            or not isinstance(row_ra, (int, float))
            or not isinstance(row_dec, (int, float))
        ):
            raise TypeError("Zubercal row objra/objdec must be numeric.")
        row_ra = float(row_ra)
        row_dec = float(row_dec)
        if not math.isfinite(row_ra) or not 0.0 <= row_ra < 360.0:
            raise ValueError("Zubercal row objra must be finite and in [0, 360).")
        if not math.isfinite(row_dec) or not -90.0 <= row_dec <= 90.0:
            raise ValueError("Zubercal row objdec must be finite and in [-90, 90].")
        coordinate = SkyCoord(ra=row_ra * u.deg, dec=row_dec * u.deg)
        separation = float(center.separation(coordinate).arcsec)
        if separation > radius_arcsec + 1e-6:
            raise ValueError("Zubercal row falls outside the requested cone.")
        distances.setdefault(ps1_id, []).append(separation)
        band = row.get("band")
        if isinstance(band, str):
            bands.setdefault(ps1_id, set()).add(band)
        normalized_rows.append(row)
        row_annotations.append(
            {
                "row_index": len(normalized_rows) - 1,
                "ps1_objectid": ps1_id,
                "separation_arcsec": separation,
            }
        )

    candidates = tuple(
        {
            "ps1_objectid": ps1_id,
            "row_count": len(distances[ps1_id]),
            "bands": sorted(bands.get(ps1_id, set())),
            "min_separation_arcsec": min(distances[ps1_id]),
            "max_separation_arcsec": max(distances[ps1_id]),
        }
        for ps1_id in sorted(distances, key=lambda key: min(distances[key]))
    )
    if not candidates:
        match_state = "NO_PS1_MATCH"
    elif len(candidates) == 1:
        match_state = "SINGLE_PS1_ID"
    else:
        match_state = "AMBIGUOUS_MULTIPLE_PS1_IDS"

    query = {
        "ztf_objectid": ztf_objectid,
        "center_ra_deg": ra_deg,
        "center_dec_deg": dec_deg,
        "radius_arcsec": radius_arcsec,
    }
    hash_columns = (
        "objectid",
        "band",
        "mjd",
        "fieldid",
        "rcidin",
        "objra",
        "objdec",
        "mag",
        "magerr",
        "info",
        "flag",
    )
    canonical_rows = sorted(
        normalized_rows,
        key=lambda row: tuple(
            (
                row.get(column) is None,
                row.get(column) if row.get(column) is not None else "",
            )
            for column in hash_columns
        ),
    )
    canonical = json.dumps(
        canonical_rows,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return ZubercalDR20Result(
        ztf_objectid=ztf_objectid,
        query=query,
        raw_rows=tuple(normalized_rows),
        row_annotations=tuple(row_annotations),
        candidate_summary=candidates,
        match_state=match_state,
        payload_sha256=hashlib.sha256(canonical).hexdigest(),
    )


class ZubercalDR20Backend:
    """Query the public Zubercal DR20 HATS catalog for one DR24 sky position."""

    def __init__(self, *, max_returned_rows: int = MAX_RETURNED_ROWS) -> None:
        if (
            not isinstance(max_returned_rows, int)
            or isinstance(max_returned_rows, bool)
            or not 1 <= max_returned_rows <= MAX_RETURNED_ROWS
        ):
            raise ValueError(
                f"max_returned_rows must be an integer in [1, {MAX_RETURNED_ROWS}]."
            )
        self.max_returned_rows = max_returned_rows

    def acquire(self, request: ZubercalDR20Request) -> ZubercalDR20Result:
        try:
            import lsdb
            from dask.distributed import Client
        except ImportError as exc:
            raise RuntimeError(
                "Zubercal DR20 access requires the optional dr24 dependencies."
            ) from exc

        spatial_filter = lsdb.ConeSearch(
            ra=request.ra_deg,
            dec=request.dec_deg,
            radius_arcsec=request.radius_arcsec,
        )
        catalog = lsdb.open_catalog(
            ZUBERCAL_DR20_HATS_URL,
            search_filter=spatial_filter,
            columns=list(ZUBERCAL_DR20_COLUMNS),
        )
        with Client(
            n_workers=1,
            threads_per_worker=1,
            processes=False,
            memory_limit="2GB",
            dashboard_address=None,
        ):
            frame = catalog.compute()

        if len(frame) > self.max_returned_rows:
            raise ValueError(
                f"Zubercal query returned {len(frame)} rows; "
                f"limit is {self.max_returned_rows}."
            )
        rows = tuple(frame.to_dict(orient="records"))
        return summarize_zubercal_rows(
            rows,
            ztf_objectid=request.ztf_objectid,
            ra_deg=request.ra_deg,
            dec_deg=request.dec_deg,
            radius_arcsec=request.radius_arcsec,
        )


__all__ = [
    "DEFAULT_MATCH_RADIUS_ARCSEC",
    "MAX_MATCH_RADIUS_ARCSEC",
    "MAX_RETURNED_ROWS",
    "ZUBERCAL_DR20_COLUMNS",
    "ZUBERCAL_DR20_HATS_URL",
    "ZubercalDR20Backend",
    "ZubercalDR20Request",
    "ZubercalDR20Result",
    "summarize_zubercal_rows",
]
