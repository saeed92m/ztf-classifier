import json

import pytest

from ztf_classifier.application.errors import ApplicationInputError
from ztf_classifier.application.state import (
    ApplicationSettings,
    ApplicationStateStore,
)


def test_missing_state_returns_default_settings(tmp_path) -> None:
    store = ApplicationStateStore(tmp_path / "nested" / "state.json")

    assert store.load() == ApplicationSettings()


def test_settings_round_trip_and_atomic_file_shape(tmp_path) -> None:
    path = tmp_path / "config" / "state.json"
    store = ApplicationStateStore(path)
    settings = ApplicationSettings(
        theme="deep-space",
        workspace_directory="/data/ztf",
        max_import_bytes=1024,
    )

    store.save(settings)

    assert store.load() == settings
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload == {
        "schema_version": 1,
        "settings": {
            "theme": "deep-space",
            "workspace_directory": "/data/ztf",
            "max_import_bytes": 1024,
            "day_start": "06:00",
            "night_start": "18:00",
        },
    }
    assert list(path.parent.glob(".state.json.*.tmp")) == []


@pytest.mark.parametrize(
    "kwargs",
    [
        {"theme": "unknown"},
        {"workspace_directory": ""},
        {"max_import_bytes": 0},
        {"max_import_bytes": -1},
        {"max_import_bytes": True},
    ],
)
def test_invalid_settings_are_rejected(kwargs) -> None:
    with pytest.raises(ApplicationInputError):
        ApplicationSettings(**kwargs)


@pytest.mark.parametrize(
    "payload",
    [
        [],
        {"schema_version": 2, "settings": {}},
        {"schema_version": 1},
        {"schema_version": 1, "settings": []},
        {"schema_version": 1, "settings": {"unexpected": "value"}},
        {"schema_version": 1, "settings": {"theme": "unknown"}},
    ],
)
def test_invalid_or_unsupported_state_fails_closed(tmp_path, payload) -> None:
    path = tmp_path / "state.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ApplicationInputError):
        ApplicationStateStore(path).load()


def test_corrupt_state_is_not_silently_reset(tmp_path) -> None:
    path = tmp_path / "state.json"
    path.write_text("{not-json", encoding="utf-8")

    with pytest.raises(ApplicationInputError):
        ApplicationStateStore(path).load()

    assert path.read_text(encoding="utf-8") == "{not-json"


def test_state_store_rejects_non_settings_on_save(tmp_path) -> None:
    store = ApplicationStateStore(tmp_path / "state.json")

    with pytest.raises(ApplicationInputError):
        store.save({"theme": "light"})  # type: ignore[arg-type]

    assert not store.path.exists()
