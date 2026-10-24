"""Regression tests for cross-platform peak-memory diagnostics."""

from ztf_classifier.validation import runner


def test_peak_memory_metric_is_positive_when_available():
    value = runner._peak_rss_mb()
    assert value is None or value > 0.0


def test_windows_memory_api_failure_is_reported_as_unavailable(monkeypatch):
    # On POSIX, ctypes has no WinDLL attribute. Simulating the Windows branch
    # therefore exercises the guarded API-failure path without requiring Windows.
    monkeypatch.setattr(runner.sys, "platform", "win32")
    assert runner._peak_rss_mb() is None
