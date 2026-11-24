"""Tests for the standalone desktop launcher contracts."""

from __future__ import annotations

from urllib.parse import parse_qs, urlsplit

import pytest

from ztf_classifier.desktop.launcher import (
    LOOPBACK_HOST,
    _configure_environment,
    _restore_environment,
    workbench_url,
)


def test_workbench_url_keeps_token_in_fragment() -> None:
    token = "sensitive-session-token"
    parsed = urlsplit(workbench_url(43210, token))

    assert parsed.scheme == "http"
    assert parsed.hostname == LOOPBACK_HOST
    assert parsed.port == 43210
    assert parsed.path == "/workbench/"
    assert parsed.query == ""
    assert parse_qs(parsed.fragment) == {"desktop-token": [token]}
    assert token not in parsed.netloc
    assert token not in parsed.path


@pytest.mark.parametrize("port", [0, -1, 65536])
def test_workbench_url_rejects_invalid_ports(port: int) -> None:
    with pytest.raises(ValueError, match="port"):
        workbench_url(port, "token")


def test_workbench_url_rejects_empty_token() -> None:
    with pytest.raises(ValueError, match="access_token"):
        workbench_url(43210, "")


def test_desktop_environment_uses_user_data_directory(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    variables = (
        "ZTF_API_KEY",
        "ZTF_API_OBSERVATION_CACHE_DIR",
        "ZTF_API_JOB_STORE",
        "ZTF_API_RESULT_STORE",
        "ZTF_API_STATE_PATH",
    )
    for name in variables:
        monkeypatch.delenv(name, raising=False)

    previous = _configure_environment(tmp_path, "test-token")
    try:
        assert __import__("os").environ["ZTF_API_KEY"] == "test-token"
        assert __import__("os").environ["ZTF_API_JOB_STORE"].endswith(
            "jobs/jobs.sqlite3"
        )
        assert (tmp_path / "cache" / "observations").is_dir()
        assert (tmp_path / "jobs").is_dir()
        assert (tmp_path / "results").is_dir()
    finally:
        _restore_environment(previous)

    for name in variables:
        assert name not in __import__("os").environ
