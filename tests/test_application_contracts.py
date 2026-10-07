from ztf_classifier.application.contracts import (
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

    try:
        source.source_id = "mutated"
    except AttributeError:
        pass
    else:
        raise AssertionError("DataSourceRef must remain immutable")
