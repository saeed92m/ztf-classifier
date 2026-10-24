"""Regression test for standards-compliant JSON diagnostics (issue #196).

The artifact `ztf_periodic_730k/selection_diagnostics.json` previously
contained NaN literals for absent gmag/Per-g/Per-r values. Python's
default json.dumps permits those non-standard tokens (allow_nan=True),
but RFC-compliant parsers (e.g., JavaScript JSON.parse) reject them.

This test ensures:
- strict dumps (allow_nan=False) fails on raw NaN
- dumps_strict sanitizes NaN->null and round-trips strict
- diagnostic payloads with missing parent fields serialize to valid JSON
"""

from __future__ import annotations

import json

from ztf_classifier.validation.json_utils import dumps_strict, sanitize_for_strict_json


def test_stdlib_rejects_nan_with_allow_nan_false():
    payload = {"gmag": float("nan"), "Per_g": float("nan"), "rmag": 17.5}
    # Standard strict mode must reject NaN
    try:
        json.dumps(payload, allow_nan=False)
        assert False, "allow_nan=False should raise ValueError on NaN"
    except ValueError:
        pass


def test_dumps_strict_sanitizes_nan_to_null_and_roundtrips():
    payload = {
        "candidate_only_all_objects": [
            {"oid": "1", "gmag": float("nan"), "Per_g": float("nan"), "rmag": 18.0},
            {"oid": "2", "gmag": 17.2, "Per_g": 1.5, "Per_r": float("inf")},
            {"oid": "3", "gmag": 16.0, "Per_g": float("-inf"), "rmag": 15.5},
        ],
        "counts": {"candidate_only": 3, "published_only": 0},
    }
    text = dumps_strict(payload, indent=2, sort_keys=True)
    # Must not contain NaN/Infinity literals
    assert "NaN" not in text
    assert "Infinity" not in text
    assert "-Infinity" not in text
    # Must contain null for those positions
    assert text.count("null") == 4  # 2 NaN + 1 Inf + 1 -Inf
    # Strict parser must accept
    parsed = json.loads(text)
    assert json.dumps(parsed, allow_nan=False)  # re-serialize strict still works
    # Semantic: missing parent fields became null, not silently dropped
    assert parsed["candidate_only_all_objects"][0]["gmag"] is None
    assert parsed["candidate_only_all_objects"][0]["Per_g"] is None
    assert parsed["candidate_only_all_objects"][1]["Per_r"] is None
    assert parsed["candidate_only_all_objects"][2]["Per_g"] is None


def test_sanitize_preserves_finite_values():
    payload = {"a": 1, "b": 1.5, "c": "text", "d": None, "e": [1, 2.0], "f": {"x": 3}}
    assert sanitize_for_strict_json(payload) == payload
    text = dumps_strict(payload, sort_keys=True)
    assert json.loads(text) == payload


def test_derivation_diagnostic_uses_strict_serialization(tmp_path):
    """Integration: derived diagnostic file must be strict-JSON parseable."""
    from ztf_classifier.validation.derivation import derive_730k

    parent = tmp_path / "parent.tsv"
    parent.write_text("SourceID\n1\n2\n3\n", encoding="utf-8")
    g = tmp_path / "g.tsv"
    g.write_text(
        "SourceID\tgmag\te_gmag\tg_flag\n"
        "1\t18.0\t0.1\t0\n"
        "2\t18.0\t0.1\t0\n"
        "3\t0.0\t0.1\t0\n",
        encoding="utf-8",
    )
    r = tmp_path / "r.tsv"
    r.write_text(
        "SourceID\trmag\te_rmag\tr_flag\n"
        "1\t17.0\t0.1\t0\n"
        "2\t17.0\t0.1\t0\n"
        "3\t17.0\t0.1\t0\n",
        encoding="utf-8",
    )
    # Trigger count mismatch to force diagnostic emission (expect 2 but get 2? we force mismatch)
    # Use expected 10 to force diagnostic + ValueError
    try:
        derive_730k(
            parent,
            g,
            r,
            tmp_path / "selected.tsv",
            expected_parent_rows=3,
            expected_selected_rows=99,  # intentional mismatch
            parent_evidence_sha256="0" * 64,
        )
        assert False, "should raise count mismatch"
    except ValueError:
        pass
    diag_path = tmp_path / "selected.tsv.diagnostic.json"
    assert diag_path.is_file()
    text = diag_path.read_text(encoding="utf-8")
    # Must be strict JSON
    assert "NaN" not in text
    parsed = json.loads(text)
    # Re-serializing strict must not raise
    json.dumps(parsed, allow_nan=False)
    assert parsed["status"] == "COUNT_MISMATCH"


def test_strict_json_preserves_finite_types():
    """Finite values, booleans, strings, arrays, nested objects, numeric types stay correct."""

    payload = {
        "int": 42,
        "float": 3.1415,
        "bool_true": True,
        "bool_false": False,
        "str": "hello",
        "null": None,
        "array": [1, 2.0, "x", False, None],
        "nested": {"a": {"b": [1, {"c": 2}]}, "d": "e"},
        "zero": 0,
        "neg": -1.5,
    }
    text = dumps_strict(payload, sort_keys=True)
    assert "NaN" not in text
    parsed = json.loads(text)
    # json round-trip preserves types (int vs float may coerce, but values equal)
    assert parsed["int"] == 42
    assert parsed["float"] == 3.1415
    assert parsed["bool_true"] is True
    assert parsed["bool_false"] is False
    assert parsed["str"] == "hello"
    assert parsed["null"] is None
    assert parsed["array"] == [1, 2.0, "x", False, None]
    assert parsed["nested"]["a"]["b"][1]["c"] == 2
    # Strict re-dump must succeed
    json.dumps(parsed, allow_nan=False)


def test_strict_json_handles_numpy_scalars():
    pytest = pytest_import()
    # numpy NaN/Inf should become null, finite becomes Python float/int
    try:
        import numpy as np

        payload = {
            "np_nan": np.float64(float("nan")),
            "np_inf": np.float64(float("inf")),
            "np_ninf": np.float64(float("-inf")),
            "np_finite": np.float64(1.5),
            "np_int": np.int64(42),
        }
        text = dumps_strict(payload, sort_keys=True)
        assert "NaN" not in text
        assert "Infinity" not in text
        parsed = json.loads(text)
        assert parsed["np_nan"] is None
        assert parsed["np_inf"] is None
        assert parsed["np_ninf"] is None
        assert parsed["np_finite"] == 1.5
        assert parsed["np_int"] == 42
        json.dumps(parsed, allow_nan=False)
    except ImportError:
        pytest.skip("numpy not available")


def test_strict_json_rejects_malformed_unsupported_explicitly():
    # Sets and other non-serializable types must raise explicitly, not silently corrupt
    try:
        dumps_strict({"bad": {1, 2, 3}})
        assert False, "sets should raise TypeError"
    except TypeError:
        pass
    try:
        import datetime

        dumps_strict({"bad": datetime.datetime.now(datetime.UTC)})
        assert False, "datetime should raise TypeError without custom serializer"
    except TypeError:
        pass
    # Tuples are sanitized to lists (our sanitize converts tuple->list) — should succeed
    text = dumps_strict({"t": (1, 2, float("nan"))})
    parsed = json.loads(text)
    assert parsed["t"] == [1, 2, None]


def test_strict_json_distinguishes_missing_from_invalid_scientifically():
    """Downstream check: missing (null) remains distinguishable from valid/invalid.

    Original code checked `if gmag > 0` etc.; NaN fails >0, null also fails >0 if handled
    as `value is not None and value > 0`. We verify both map to not-passing, preserving counts.
    """
    payload_pre = {
        "objects": [
            {"oid": "1", "gmag": float("nan"), "Per_g": float("nan")},  # missing
            {"oid": "2", "gmag": 0.0, "Per_g": 1.5},  # invalid (0 not >0)
            {"oid": "3", "gmag": 18.0, "Per_g": 1.5},  # valid
        ]
    }
    # Pre-fix would have produced NaN literals (non-strict) -> not strict-parseable
    pre_text = json.dumps(payload_pre)  # allow_nan=True default produces NaN
    assert "NaN" in pre_text
    try:
        json.dumps(payload_pre, allow_nan=False)
        assert False, "pre-fix payload should fail strict"
    except ValueError:
        pass
    # Post-fix: nulls
    post_text = dumps_strict(payload_pre, sort_keys=True)
    assert "NaN" not in post_text
    assert post_text.count("null") == 2
    post = json.loads(post_text)

    # Scientific meaning: both missing and invalid fail >0, valid passes — counts same
    def is_valid(obj):
        g = obj["gmag"]
        p = obj["Per_g"]
        return g is not None and p is not None and g > 0 and p > 0

    pre_valid_count = sum(
        1
        for o in payload_pre["objects"]
        if is_valid(
            {
                "gmag": None
                if isinstance(o["gmag"], float)
                and not __import__("math").isfinite(o["gmag"])
                else o["gmag"],
                "Per_g": None
                if isinstance(o["Per_g"], float)
                and not __import__("math").isfinite(o["Per_g"])
                else o["Per_g"],
            }
        )
    )
    post_valid_count = sum(1 for o in post["objects"] if is_valid(o))
    assert pre_valid_count == post_valid_count == 1


def test_representative_cpvs_diagnostic_roundtrip_and_scientific_meaning():
    """Generate representative CPVS diagnostic (3-object sample mimicking 11,602 case) and compare pre/post.

    Heavy artifact partition: 11,580 fail both pairs, 17 valid mags but missing Per, 5 valid Pers but missing gmag.
    We generate a 3-object synthetic proxy covering each partition and verify:
    - pre-fix text contains NaN/Infinity and fails strict parsing
    - post-fix text is strict, preserves objects, and partition counts identical
    """
    # Synthetic proxy for heavy diagnostic's candidate_only_all_objects
    pre_payload = {
        "candidate_count": 3,
        "published_count": 0,
        "partition": {
            "both_fail": 1,
            "valid_mag_missing_per": 1,
            "valid_per_missing_gmag": 1,
        },
        "candidate_only_all_objects": [
            {
                "oid": "100",
                "gmag": float("nan"),
                "rmag": float("nan"),
                "Per_g": float("nan"),
                "Per_r": float("nan"),
            },  # both fail
            {
                "oid": "101",
                "gmag": 18.0,
                "rmag": 17.5,
                "Per_g": float("nan"),
                "Per_r": float("nan"),
            },  # valid mags, missing Per
            {
                "oid": "102",
                "gmag": float("nan"),
                "rmag": 17.5,
                "Per_g": 1.2,
                "Per_r": 1.3,
            },  # valid Pers, missing gmag
        ],
    }
    # Pre-fix: NaN literals
    pre_text = json.dumps(
        pre_payload, indent=2, sort_keys=True
    )  # default allow_nan=True
    assert pre_text.count("NaN") == 7
    assert "NaN" in pre_text
    try:
        json.dumps(pre_payload, indent=2, sort_keys=True, allow_nan=False)
        assert False
    except ValueError:
        pass
    # Post-fix
    post_text = dumps_strict(pre_payload, indent=2, sort_keys=True)
    assert "NaN" not in post_text
    assert "Infinity" not in post_text
    assert post_text.count("null") == 7  # same count as NaN
    parsed = json.loads(post_text)
    # Strict re-dump succeeds
    json.dumps(parsed, indent=2, sort_keys=True, allow_nan=False)

    # Compare scientific meaning: counts of objects failing all-four >0 same
    def passes_all_four(o):
        return all(
            v is not None and v > 0
            for v in [o["gmag"], o["rmag"], o["Per_g"], o["Per_r"]]
        )

    pre_pass = sum(
        1
        for o in pre_payload["candidate_only_all_objects"]
        if passes_all_four(
            {
                "gmag": None
                if isinstance(o["gmag"], float)
                and not __import__("math").isfinite(o["gmag"])
                else o["gmag"],
                "rmag": None
                if isinstance(o["rmag"], float)
                and not __import__("math").isfinite(o["rmag"])
                else o["rmag"],
                "Per_g": None
                if isinstance(o["Per_g"], float)
                and not __import__("math").isfinite(o["Per_g"])
                else o["Per_g"],
                "Per_r": None
                if isinstance(o["Per_r"], float)
                and not __import__("math").isfinite(o["Per_r"])
                else o["Per_r"],
            }
        )
    )
    post_pass = sum(
        1 for o in parsed["candidate_only_all_objects"] if passes_all_four(o)
    )
    assert (
        pre_pass == post_pass == 0
    )  # none pass all four, matches heavy partition logic
    # Ensure structure preserved
    assert len(parsed["candidate_only_all_objects"]) == 3
    assert parsed["partition"] == pre_payload["partition"]


def pytest_import():
    import pytest

    return pytest
