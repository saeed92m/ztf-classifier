import pytest

from ztf_classifier.validation.mast import (
    MastResponseError,
    build_products_request,
    validate_products_response,
)


def test_products_request_uses_service_specific_obsid_parameter():
    request = build_products_request(61113566)
    assert request["service"] == "Mast.Caom.Products"
    assert request["params"] == {"obsid": 61113566}
    assert "filters" not in request["params"]


@pytest.mark.parametrize("obsid", [0, -1, True, "61113566", None])
def test_products_request_rejects_invalid_obsid(obsid):
    with pytest.raises(ValueError, match="obsid"):
        build_products_request(obsid)


def test_products_request_bounds_page_size_and_page():
    with pytest.raises(ValueError, match="page_size"):
        build_products_request(61113566, page_size=0)
    with pytest.raises(ValueError, match="page_size"):
        build_products_request(61113566, page_size=1001)
    with pytest.raises(ValueError, match="page"):
        build_products_request(61113566, page=0)


def test_validate_products_response_accepts_correct_products():
    payload = {
        "status": "COMPLETE",
        "data": [
            {
                "obsID": 61113566,
                "productFilename": "sample_lc.fits",
                "dataURI": "mast:TESS/product/sample_lc.fits",
            }
        ],
    }
    products = validate_products_response(payload, expected_obsid=61113566)
    assert len(products) == 1
    assert products[0]["productFilename"] == "sample_lc.fits"


def test_validate_products_response_fails_closed_on_empty_success_response():
    with pytest.raises(MastResponseError, match="empty"):
        validate_products_response(
            {"status": "COMPLETE", "data": []},
            expected_obsid=61113566,
        )


def test_validate_products_response_rejects_wrong_observation():
    payload = {
        "status": "COMPLETE",
        "data": [
            {
                "obsID": 999,
                "productFilename": "sample_lc.fits",
                "dataURI": "mast:TESS/product/sample_lc.fits",
            }
        ],
    }
    with pytest.raises(MastResponseError, match="expected 61113566"):
        validate_products_response(payload, expected_obsid=61113566)


def test_validate_products_response_rejects_missing_product_uri():
    payload = {
        "status": "COMPLETE",
        "data": [
            {
                "obsID": 61113566,
                "productFilename": "sample_lc.fits",
            }
        ],
    }
    with pytest.raises(MastResponseError, match="dataURI"):
        validate_products_response(payload, expected_obsid=61113566)
