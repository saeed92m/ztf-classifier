"""Small, testable MAST request contracts used by source-validation pilots.

This module deliberately separates request construction/response validation from
network I/O so API-contract regressions can be tested without a live archive.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


class MastResponseError(ValueError):
    """Raised when a MAST response is structurally invalid or unexpectedly empty."""


def build_products_request(obsid: int, *, page_size: int = 20, page: int = 1) -> dict[str, Any]:
    """Build the documented Mast.Caom.Products request for one observation.

    Unlike generic filtered-catalog services, this service accepts the
    observation identifier directly as params.obsid. Do not wrap it in
    params.filters: that request returned HTTP 200 with zero rows in the
    recorded TESS pilot.
    """
    if isinstance(obsid, bool) or not isinstance(obsid, int) or obsid <= 0:
        raise ValueError("obsid must be a positive integer")
    if isinstance(page_size, bool) or not isinstance(page_size, int) or not 1 <= page_size <= 1000:
        raise ValueError("page_size must be an integer between 1 and 1000")
    if isinstance(page, bool) or not isinstance(page, int) or page < 1:
        raise ValueError("page must be a positive integer")
    return {
        "service": "Mast.Caom.Products",
        "format": "json",
        "params": {"obsid": obsid},
        "pagesize": page_size,
        "page": page,
        "removenullcolumns": False,
    }


def validate_products_response(
    payload: Mapping[str, Any], *, expected_obsid: int
) -> list[dict[str, Any]]:
    """Validate MAST status, non-empty product list, and observation identity."""
    if isinstance(expected_obsid, bool) or not isinstance(expected_obsid, int) or expected_obsid <= 0:
        raise ValueError("expected_obsid must be a positive integer")
    status = payload.get("status")
    if status != "COMPLETE":
        raise MastResponseError(f"MAST products request did not complete: {status!r}")
    rows = payload.get("data")
    if not isinstance(rows, list) or not rows:
        raise MastResponseError(
            f"MAST products response is empty for obsid={expected_obsid}; "
            "check the service-specific request contract and record the failure"
        )

    products: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping):
            raise MastResponseError(f"MAST product row {index} is not an object")
        row_obsid = row.get("obsID", row.get("obsid"))
        try:
            normalized_obsid = int(row_obsid)
        except (TypeError, ValueError) as exc:
            raise MastResponseError(
                f"MAST product row {index} has no valid obsID/obsid"
            ) from exc
        if normalized_obsid != expected_obsid:
            raise MastResponseError(
                f"MAST product row {index} belongs to obsid={normalized_obsid}, "
                f"expected {expected_obsid}"
            )
        filename = row.get("productFilename")
        data_uri = row.get("dataURI")
        if not isinstance(filename, str) or not filename.strip():
            raise MastResponseError(f"MAST product row {index} has no productFilename")
        if not isinstance(data_uri, str) or not data_uri.startswith("mast:"):
            raise MastResponseError(f"MAST product row {index} has invalid dataURI")
        products.append(dict(row))
    return products
