"""ALeRCE implementation of object acquisition."""

from __future__ import annotations

from typing import Any

from ztf_classifier.dataset.selector import ObjectSelectionRequest
from ztf_classifier.io.object_acquisition import (
    ObjectAcquisitionBackend,
    ObjectAcquisitionResult,
)


class AlerceObjectBackend(ObjectAcquisitionBackend):
    """Acquire classified ZTF objects through ALeRCE."""

    def __init__(self, client: Any) -> None:
        self._client = client

    def acquire(
        self,
        request: ObjectSelectionRequest,
    ) -> ObjectAcquisitionResult:
        result = self._client.query_objects(
            survey=request.survey,
            classifier=request.classifier,
            class_name=request.class_name,
            probability=request.probability,
            page_size=request.page_size,
            format="pandas",
        )

        return ObjectAcquisitionResult(
            request=request,
            objects=(result,),
        )
