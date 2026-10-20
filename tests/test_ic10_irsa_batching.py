"""Regression tests for resilient IC 10 IRSA batch fetching."""
from __future__ import annotations

import pandas as pd

from scripts.validation import ic10_raw_photometry_reproduction as module


def test_fetch_raw_oids_resilient_uses_small_batches(monkeypatch):
    calls = []

    def fake_fetch(oids, collection=None, timeout=45):
        calls.append(list(oids))
        return (
            {oid: pd.DataFrame({"mag": [15.0]}) for oid in oids},
            {"requested_oids": list(oids), "sha256": "fixture"},
        )

    monkeypatch.setattr(module, "fetch_raw_batch", fake_fetch)
    monkeypatch.setattr(module.time, "sleep", lambda _: None)

    data, metadata_by_oid, log = module.fetch_raw_oids_resilient(
        ["a", "b", "c"], batch_size=2
    )

    assert calls == [["a", "b"], ["c"]]
    assert set(data) == {"a", "b", "c"}
    assert set(metadata_by_oid) == {"a", "b", "c"}
    assert all(item["request_mode"] == "batch" for item in log)


def test_fetch_raw_oids_resilient_falls_back_to_single_oid(monkeypatch):
    calls = []

    def fake_fetch(oids, collection=None, timeout=45):
        calls.append(list(oids))
        if len(oids) > 1:
            raise TimeoutError("batch timeout")
        return (
            {oids[0]: pd.DataFrame({"mag": [16.0]})},
            {"requested_oids": list(oids), "sha256": "single-fixture"},
        )

    monkeypatch.setattr(module, "fetch_raw_batch", fake_fetch)
    monkeypatch.setattr(module.time, "sleep", lambda _: None)

    data, metadata_by_oid, log = module.fetch_raw_oids_resilient(
        ["a", "b"], batch_size=2
    )

    assert calls == [["a", "b"], ["a"], ["b"]]
    assert set(data) == {"a", "b"}
    assert all(
        metadata_by_oid[oid]["request_mode"] == "single_oid_fallback"
        for oid in ("a", "b")
    )
    assert any(item["request_mode"] == "batch_failed" for item in log)
