from __future__ import annotations

from pathlib import Path

from ztf_classifier.application.observations import ObservationService
from ztf_classifier.io.dr24_lightcurve import (
    DR24LightcurveRecord,
    DR24LightcurveResult,
)


class FakeDR24Backend:
    def acquire(self, _request: object) -> DR24LightcurveResult:
        epochs = (
            {
                "hmjd": 60000.1,
                "mag": 18.2,
                "magerr": 0.03,
                "clrcoeff": 0.1,
                "catflags": 0,
            },
            {
                "hmjd": 60000.2,
                "mag": 18.3,
                "magerr": 0.04,
                "clrcoeff": 0.1,
                "catflags": 32768,
            },
        )
        record = DR24LightcurveRecord(
            objectid=123456,
            filterid=1,
            fieldid=100,
            rcid=4,
            objra=120.0,
            objdec=-20.0,
            catalog_nepochs=2,
            epochs=epochs,
            payload_sha256="a" * 64,
        )
        return DR24LightcurveResult(
            records=(record,),
            provenance={"requested_oids": [123456], "missing_oids": []},
        )


def test_observation_service_adds_separate_qc_without_mutating_raw_epochs(
    tmp_path: Path,
) -> None:
    service = ObservationService(
        client=object(),
        cache_dir=tmp_path,
        dr24_backend=FakeDR24Backend(),  # type: ignore[arg-type]
    )

    payload = service.get_dr24_native_lightcurves([123456])

    assert payload["records"][0]["epochs"] == (
        {
            "hmjd": 60000.1,
            "mag": 18.2,
            "magerr": 0.03,
            "clrcoeff": 0.1,
            "catflags": 0,
        },
        {
            "hmjd": 60000.2,
            "mag": 18.3,
            "magerr": 0.04,
            "clrcoeff": 0.1,
            "catflags": 32768,
        },
    )
    assert payload["qc_assessments"][0]["objectid"] == 123456
    assert payload["qc_assessments"][0]["counts"]["strict_clean_epochs"] == 1
    assert payload["qc_assessments"][0]["counts"]["bit_15_flagged_epochs"] == 1
    assert payload["qc_assessments"][0]["policy_status"] == (
        "DIAGNOSTIC_NOT_PRODUCTION_APPROVED"
    )
