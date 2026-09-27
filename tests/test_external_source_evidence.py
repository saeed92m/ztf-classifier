from pathlib import Path

import pandas as pd
import pytest

from scripts.acquire_external_source_evidence import SourceQueryError, _validate


def test_external_source_validation_accepts_exact_sorted_subset():
    frame = pd.DataFrame(
        {
            "objectid": ["ZTF1", "ZTF2", "ZTF3"],
            "objra": [1.0, 2.0, 3.0],
            "objdec": [0.0, 1.0, 2.0],
            "nepochs": [10, 11, 12],
        }
    )
    _validate(frame, ["objectid", "objra", "objdec", "nepochs"], "objectid", 3)


@pytest.mark.parametrize(
    "frame, message",
    [
        (pd.DataFrame({"objectid": ["ZTF1", "ZTF1"]}), "duplicate"),
        (pd.DataFrame({"objectid": ["ZTF2", "ZTF1"]}), "not deterministically sorted"),
        (pd.DataFrame({"objectid": ["ZTF1"]}), "expected exactly"),
    ],
)
def test_external_source_validation_fails_closed(frame, message):
    with pytest.raises(SourceQueryError, match=message):
        _validate(frame, ["objectid"], "objectid", 2)
