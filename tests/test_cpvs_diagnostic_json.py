"""Tests for standards-compliant CPVS diagnostic JSON serialization."""

import json
import math
import sys
from pathlib import Path

# The script is also executable directly from scripts/, where its sibling import lives.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from diagnose_cpvs_selection import _json_safe


def test_json_safe_converts_nonfinite_values_to_null_and_preserves_finite_values() -> None:
    payload = {
        "missing": float("nan"),
        "positive_infinity": float("inf"),
        "negative_infinity": float("-inf"),
        "finite": 1.25,
        "nested": [{"missing_period": float("nan"), "count": 17}],
    }

    normalized = _json_safe(payload)
    encoded = json.dumps(normalized, allow_nan=False, sort_keys=True)
    decoded = json.loads(encoded)

    assert decoded == {
        "missing": None,
        "positive_infinity": None,
        "negative_infinity": None,
        "finite": 1.25,
        "nested": [{"missing_period": None, "count": 17}],
    }
    assert math.isnan(payload["missing"])
