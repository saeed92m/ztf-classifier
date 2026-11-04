"""Bounded, provenance-preserving access to native ZTF DR24 light curves.

This adapter returns source-native measurements. It does not convert HMJD to MJD,
apply a catflags policy, correct magnitudes, merge OIDs, or feed model inference.
Those operations require separately approved scientific contracts.
"""
from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict, dataclass
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

import pandas as pd

DR24_LIGHTCURVES_HATS = "s3://ipac-irsa-ztf/ztf/enhanced/dr24/lc/hats"
DR24_RELEASE = "DR24"
CATALOG_COLUMNS = (
    "objectid", "filterid", "fieldid", "rcid", "objra", "objdec",
    "nepochs", "lightcurve",
)
PAYLOAD_COLUMNS = ("hmjd", "mag", "magerr", "clrcoeff", "catflags")
MAX_OIDS_PER_REQUEST = 10


class DR24AcquisitionError(RuntimeError):
    """Raised when a DR24 request cannot be completed without ambiguity."""


@dataclass(frozen=True)
class DR24LightcurveRequest:
    """A bounded request for source-native DR24 object records."""

    objectids: tuple[int, ...]

    def __post_init__(self) -> None:
        values = tuple(self.objectids)
        if not values:
            raise ValueError("At least one DR24 objectid is required.")
        if len(values) > MAX_OIDS_PER_REQUEST:
            raise ValueError(f"At most {MAX_OIDS_PER_REQUEST} OIDs are allowed.")
        if any(
            not isinstance(value, int) or isinstance(value, bool) or value <= 0
            for value in values
        ):
            raise ValueError("DR24 objectids must be positive integers.")
        if len(values) != len(set(values)):
            raise ValueError("Duplicate DR24 objectids are not allowed.")
        object.__setattr__(self, "objectids", values)


@dataclass(frozen=True)
class DR24LightcurveRecord:
    """One OID with untouched epoch values and catalog partition metadata."""

    objectid: int
    filterid: int
    fieldid: int
    rcid: int
    objra: float
    objdec: float
    catalog_nepochs: int
    epochs: tuple[dict[str, Any], ...]
    payload_sha256: str


@dataclass(frozen=True)
class DR24LightcurveResult:
    """Acquired records and a reproducible source/query manifest."""

    records: tuple[DR24LightcurveRecord, ...]
    provenance: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "ztf-dr24-native-lightcurve-v1",
            "records": [asdict(record) for record in self.records],
            "provenance": self.provenance,
        }


def _json_scalar(value: Any) -> Any:
    """Convert one scalar to deterministic JSON-compatible data."""
    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        value = value.item()
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    raise DR24AcquisitionError(
        f"Unsupported DR24 payload scalar: {type(value).__name__}"
    )


def _canonical_records(frame: pd.DataFrame) -> tuple[tuple[dict[str, Any], ...], str]:
    missing = sorted(set(PAYLOAD_COLUMNS) - set(frame.columns))
    if missing:
        raise DR24AcquisitionError(
            "DR24 nested payload is missing required columns: " + ", ".join(missing)
        )
    records = tuple(
        {column: _json_scalar(value) for column, value in row.items()}
        for row in frame.loc[:, list(PAYLOAD_COLUMNS)].to_dict(orient="records")
    )
    encoded = json.dumps(
        records,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return records, hashlib.sha256(encoded).hexdigest()


class DR24LightcurveBackend:
    """Query the indexed DR24 HATS catalog without broad catalog scans.

    The catalog factory is injectable for deterministic tests. Production use
    imports LSDB only when acquisition is requested.
    """

    def __init__(self, catalog_factory: Callable[..., Any] | None = None) -> None:
        self._catalog_factory = catalog_factory

    def acquire(self, request: DR24LightcurveRequest) -> DR24LightcurveResult:
        factory = self._catalog_factory
        if factory is None:
            try:
                import lsdb
            except ImportError as exc:
                raise DR24AcquisitionError(
                    "DR24 acquisition requires the optional 'dr24' dependencies."
                ) from exc
            factory = lsdb.open_catalog

        try:
            catalog = factory(DR24_LIGHTCURVES_HATS, columns=list(CATALOG_COLUMNS))
            available = set(catalog.all_columns)
            missing = sorted(set(CATALOG_COLUMNS) - available)
            if missing:
                raise DR24AcquisitionError(
                    "DR24 HATS schema is missing required columns: "
                    + ", ".join(missing)
                )
            indexes = list(catalog.hc_collection.all_indexes.keys())
            if "objectid" not in indexes:
                raise DR24AcquisitionError(
                    "DR24 Lightcurves has no objectid index; refusing a full scan."
                )

            frame = catalog.id_search(
                values={"objectid": list(request.objectids)}
            ).compute()
            if "objectid" not in frame.columns:
                frame = frame.reset_index()
            if "objectid" not in frame.columns:
                raise DR24AcquisitionError("DR24 query result has no objectid column.")
            if frame["objectid"].duplicated().any():
                raise DR24AcquisitionError("DR24 returned duplicate objectid rows.")

            returned = {int(value) for value in frame["objectid"].tolist()}
            requested = set(request.objectids)
            unexpected = sorted(returned - requested)
            if unexpected:
                raise DR24AcquisitionError(
                    f"DR24 returned unrequested objectids: {unexpected}"
                )

            records: list[DR24LightcurveRecord] = []
            for row in frame.to_dict(orient="records"):
                oid = int(row["objectid"])
                payload = row["lightcurve"]
                if payload is None:
                    raise DR24AcquisitionError(
                        f"DR24 OID {oid} has a null lightcurve payload."
                    )
                try:
                    payload_frame = (
                        payload.copy()
                        if isinstance(payload, pd.DataFrame)
                        else pd.DataFrame(payload)
                    )
                except Exception as exc:
                    raise DR24AcquisitionError(
                        f"Cannot decode nested payload for DR24 OID {oid}."
                    ) from exc
                epochs, digest = _canonical_records(payload_frame)
                records.append(
                    DR24LightcurveRecord(
                        objectid=oid,
                        filterid=int(row["filterid"]),
                        fieldid=int(row["fieldid"]),
                        rcid=int(row["rcid"]),
                        objra=float(row["objra"]),
                        objdec=float(row["objdec"]),
                        catalog_nepochs=int(row["nepochs"]),
                        epochs=epochs,
                        payload_sha256=digest,
                    )
                )

            schema_columns = sorted(str(column) for column in available)
            schema_bytes = json.dumps(
                schema_columns, separators=(",", ":"), ensure_ascii=True
            ).encode("utf-8")
            missing_oids = sorted(requested - returned)
            provenance = {
                "source": "IRSA ZTF DR24 Lightcurves HATS",
                "release": DR24_RELEASE,
                "catalog_uri": DR24_LIGHTCURVES_HATS,
                "retrieved_at_utc": datetime.now(UTC).isoformat(),
                "query": {"index": "objectid", "objectids": list(request.objectids)},
                "requested_oids": list(request.objectids),
                "returned_oids": sorted(returned),
                "missing_oids": missing_oids,
                "schema_columns": schema_columns,
                "schema_columns_sha256": hashlib.sha256(schema_bytes).hexdigest(),
                "epoch_count": sum(len(record.epochs) for record in records),
                "payload_sha256": {
                    str(record.objectid): record.payload_sha256 for record in records
                },
                "interpretation": {
                    "time_column": "hmjd",
                    "time_scale": "heliocentric-based MJD; not MJD",
                    "photometry": "native DR24 mag and magerr; clrcoeff preserved",
                    "quality": "raw catflags preserved; no quality mask applied",
                    "identity": (
                        "objectid is a survey OID; no cross-OID grouping performed"
                    ),
                },
                "limitations": [
                    "Raw acquisition only; no production feature normalization.",
                    "HMJD is not relabeled as MJD.",
                    "No color correction or catflags selection is applied.",
                    "No physical-source identity is inferred across OIDs.",
                    "Missing OIDs are reported and are not replaced by another source.",
                ],
            }
            return DR24LightcurveResult(tuple(records), provenance)
        except DR24AcquisitionError:
            raise
        except Exception as exc:
            raise DR24AcquisitionError("DR24 Lightcurves acquisition failed.") from exc


__all__ = [
    "DR24AcquisitionError",
    "DR24LightcurveBackend",
    "DR24LightcurveRecord",
    "DR24LightcurveRequest",
    "DR24LightcurveResult",
]
