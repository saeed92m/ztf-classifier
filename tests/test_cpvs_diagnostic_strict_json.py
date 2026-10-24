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
import math

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
