"""Strict JSON serialization for scientific diagnostic artifacts.

RFC-compliant JSON forbids NaN/Infinity literals. Python's json.dumps
permits them by default (allow_nan=True) but that produces non-standard
tokens rejected by strict parsers (e.g., JavaScript JSON.parse).

This module provides a fail-closed helper: non-finite floats are
serialized as JSON null, and any attempt to serialize a non-finite
value without explicit sanitization raises via allow_nan=False.
"""

from __future__ import annotations

import json
import math
from typing import Any


def sanitize_for_strict_json(payload: Any) -> Any:
    """Recursively replace non-finite floats with None for strict JSON.

    None maps to JSON null. Integers, strings, booleans, and finite
    floats pass through unchanged. Containers are traversed. Numeric
    numpy scalars are normalized to Python types.
    """
    if isinstance(payload, float):
        return None if not math.isfinite(payload) else payload
    # numpy scalar handling (optional, no hard dependency)
    try:
        import numpy as np

        if isinstance(payload, np.floating):
            return None if not np.isfinite(payload) else float(payload)
        if isinstance(payload, np.integer):
            return int(payload)
        # numpy bool is subclass of generic, but not needed
    except (ImportError, AttributeError, TypeError):
        pass
    if isinstance(payload, dict):
        return {key: sanitize_for_strict_json(value) for key, value in payload.items()}
    if isinstance(payload, (list, tuple)):
        return [sanitize_for_strict_json(item) for item in payload]
    return payload


def dumps_strict(obj: Any, **kwargs: Any) -> str:
    """Dump JSON with RFC 8259 compliance (allow_nan=False).

    The payload is sanitized so that non-finite floats become null
    before serialization. kwargs are forwarded to json.dumps (e.g.,
    indent, sort_keys, separators).
    """
    sanitized = sanitize_for_strict_json(obj)
    return json.dumps(sanitized, allow_nan=False, **kwargs)


def dump_strict(obj: Any, fp: Any, **kwargs: Any) -> None:
    """Write JSON to file object with strict compliance."""
    fp.write(dumps_strict(obj, **kwargs))
