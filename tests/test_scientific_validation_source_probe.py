from ztf_classifier.validation.source_probe import PROBES, run


def test_source_probe_preserves_derived_730k_without_live_endpoint():
    assert "ztf_periodic_730k" not in PROBES


def test_source_probe_writes_derived_entry_without_network(tmp_path):
    def fake_fetch(url: str):
        return 200, b"fixture", "application/octet-stream"

    report = run(tmp_path / "probe.json", fetcher=fake_fetch)
    derived = next(item for item in report["sources"] if item["source_id"] == "ztf_periodic_730k")
    assert derived["status"] == "DERIVED"
    live = next(item for item in report["sources"] if item["source_id"] == "alerce_reference")
    assert live["status"] == "REACHABLE"
    assert live["sha256"]
