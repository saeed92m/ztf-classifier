import pytest

from ztf_classifier.application.contracts import (
    AnalysisExecution,
    ApplicationService,
    AnalysisRequest,
    AnalysisResult,
    DataSourceRef,
    ProvenanceRecord,
)


def test_application_contracts_are_immutable_and_composable():
    source = DataSourceRef(
        source_id="ZTF-test-1",
        source_type="ztf_lightcurve",
        locator="fixture://ztf-test-1",
        schema_version="1",
    )
    request = AnalysisRequest(
        request_id="req-1", sources=(source,), operation="classify"
    )
    provenance = ProvenanceRecord(
        source=source,
        operation=request.operation,
        software_version="1.0.1",
    )
    result = AnalysisResult(
        request_id=request.request_id,
        status="success",
        result_type="classification",
        payload={"class": "test"},
        provenance=(provenance,),
    )
    assert result.request_id == "req-1"
    assert result.provenance[0].source.source_id == "ZTF-test-1"

    with pytest.raises(AttributeError):
        source.source_id = "mutated"


def test_application_service_validates_and_envelopes_execution() -> None:
    source = DataSourceRef(
        source_id="ZTF-test-1",
        source_type="ztf_lightcurve",
        locator="fixture://ztf-test-1",
        schema_version="1",
    )
    request = AnalysisRequest(
        request_id="req-2",
        sources=(source,),
        operation="classify",
    )
    provenance = ProvenanceRecord(
        source=source,
        operation="classify",
        software_version="1.0.1",
    )

    service = ApplicationService(
        lambda received: AnalysisExecution(
            result_type="classification",
            payload={"class": "test"},
            diagnostics={"qc": "pass"},
            provenance=(provenance,),
        ),
        software_version="1.0.1",
    )

    result = service.analyze(request)

    assert result.status == "success"
    assert result.result_type == "classification"
    assert result.payload["class"] == "test"
    assert result.diagnostics["qc"] == "pass"
    assert result.provenance == (provenance,)


@pytest.mark.parametrize(
    "request",
    [
        AnalysisRequest(request_id="", sources=(), operation="classify"),
        AnalysisRequest(request_id="req", sources=(), operation="classify"),
        AnalysisRequest(
            request_id="req",
            sources=(
                DataSourceRef(
                    source_id="",
                    source_type="ztf_lightcurve",
                    locator="fixture://x",
                    schema_version="1",
                ),
            ),
            operation="classify",
        ),
    ],
)
def test_application_service_rejects_invalid_requests(
    request: AnalysisRequest,
) -> None:
    service = ApplicationService(
        lambda _: pytest.fail("executor must not be called"),
        software_version="1.0.1",
    )

    with pytest.raises(Exception):
        service.analyze(request)
