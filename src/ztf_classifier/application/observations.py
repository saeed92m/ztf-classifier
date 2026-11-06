"""Application service for scientific observation retrieval."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from ztf_classifier.application.errors import ObservationAcquisitionError
from ztf_classifier.domain.observations import (
    ObjectObservationSummary,
    Observation,
    ObservationProvenance,
)
from ztf_classifier.io.alerce import alerce_to_internal_lc_robust
from ztf_classifier.io.alerce_detection import AlerceDetectionBackend
from ztf_classifier.io.detection_acquisition import DetectionAcquisitionRequest
from ztf_classifier.io.dr24_lightcurve import (
    DR24LightcurveBackend,
    DR24LightcurveRequest,
)
from ztf_classifier.io.parquet_detection_store import ParquetDetectionStore


class ObservationService:
    """Retrieve and normalize ZTF observations through a source adapter."""

    def __init__(
        self,
        client: object,
        cache_dir: Path,
        *,
        dr24_backend: DR24LightcurveBackend | None = None,
    ) -> None:
        self._backend = AlerceDetectionBackend(
            client=client,
            store=ParquetDetectionStore(cache_dir),
        )
        self._dr24_backend = dr24_backend or DR24LightcurveBackend()

    def get_dr24_native_lightcurve(self, objectid: int) -> dict[str, object]:
        """Acquire source-native DR24 epochs without model normalization.

        This method deliberately does not convert HMJD to MJD, apply a
        catflags mask, perform color correction, or merge survey OIDs.
        """
        result = self._dr24_backend.acquire(
            DR24LightcurveRequest((objectid,))
        )
        return result.to_dict()

    def get_observations(
        self,
        oid: str,
        *,
        survey: str = "ztf",
    ) -> tuple[list[Observation], ObservationProvenance]:
        """Fetch one object's detections and normalize them."""
        try:
            result = self._backend.acquire(
                DetectionAcquisitionRequest(oid=oid, survey=survey)
            )
        except Exception as exc:
            raise ObservationAcquisitionError(
                "Observation acquisition failed."
            ) from exc
        normalized, diagnostics = alerce_to_internal_lc_robust(
            result.detections,
            return_diagnostics=True,
        )
        provenance = ObservationProvenance(
            source="ALeRCE",
            survey=survey,
            cache_hit=result.cache_hit,
            diagnostics=diagnostics.to_dict(),
        )
        observations = [
            Observation(
                mjd=float(row.mjd),
                fid=int(row.fid),
                mag=float(row.mag),
                magerr=float(row.magerr),
                mag_raw=None if pd.isna(row.mag_raw) else float(row.mag_raw),
                magerr_raw=(None if pd.isna(row.magerr_raw) else float(row.magerr_raw)),
                mag_corr=None if pd.isna(row.mag_corr) else float(row.mag_corr),
                magerr_corr=(
                    None if pd.isna(row.magerr_corr) else float(row.magerr_corr)
                ),
                photometry_source=str(row.photometry_source),
                ra=float(row.ra),
                dec=float(row.dec),
                dubious=bool(row.dubious),
                corrected=bool(row.corrected),
            )
            for row in normalized.itertuples(index=False)
        ]
        return observations, provenance

    def get_object_summary(
        self,
        oid: str,
        *,
        survey: str = "ztf",
    ) -> ObjectObservationSummary:
        """Build an object summary from normalized observations."""
        observations, provenance = self.get_observations(oid, survey=survey)
        if not observations:
            raise ValueError(f"No valid observations available for object: {oid}")
        return ObjectObservationSummary(
            oid=oid,
            observation_count=len(observations),
            mjd_min=min(item.mjd for item in observations),
            mjd_max=max(item.mjd for item in observations),
            filters=tuple(sorted({item.fid for item in observations})),
            ra=observations[0].ra,
            dec=observations[0].dec,
            provenance=provenance,
        )


__all__ = ["ObservationService"]
