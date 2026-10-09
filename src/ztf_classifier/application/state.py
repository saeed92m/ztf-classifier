"""Versioned, atomic persistence for non-scientific application preferences.

This store contains user-interface/workspace settings only. It must never be
used to persist, edit, or override scientific model artifacts or validation
results.
"""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from ztf_classifier.application.errors import ApplicationInputError

_STATE_SCHEMA_VERSION = 1
_ALLOWED_THEMES = frozenset({"system", "auto", "light", "deep-space", "alpha"})


@dataclass(frozen=True)
class ApplicationSettings:
    """Validated preferences safe to serialize as application state."""

    theme: str = "system"
    workspace_directory: str | None = None
    max_import_bytes: int = 250 * 1024 * 1024
    day_start: str = "06:00"
    night_start: str = "18:00"

    def __post_init__(self) -> None:
        if not isinstance(self.theme, str) or self.theme not in _ALLOWED_THEMES:
            raise ApplicationInputError(
                f"Unsupported theme {self.theme!r}; choose one of "
                f"{', '.join(sorted(_ALLOWED_THEMES))}."
            )
        if self.workspace_directory is not None:
            if not isinstance(self.workspace_directory, str):
                raise ApplicationInputError(
                    "workspace_directory must be a string or None."
                )
            if not self.workspace_directory.strip():
                raise ApplicationInputError(
                    "workspace_directory must be non-empty when provided."
                )
        for field_name, value in (("day_start", self.day_start), ("night_start", self.night_start)):
            if not isinstance(value, str) or len(value) != 5 or value[2] != ":" or not value[:2].isdigit() or not value[3:].isdigit() or not (0 <= int(value[:2]) <= 23 and 0 <= int(value[3:]) <= 59):
                raise ApplicationInputError(f"{field_name} must use HH:MM in 24-hour time.")
        if (
            not isinstance(self.max_import_bytes, int)
            or isinstance(self.max_import_bytes, bool)
            or self.max_import_bytes <= 0
        ):
            raise ApplicationInputError(
                "max_import_bytes must be a positive integer."
            )


class ApplicationStateStore:
    """Load/save versioned settings with atomic replacement.

    A missing state file returns defaults. Existing malformed or unsupported
    state fails closed instead of silently resetting the user's preferences.
    """

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path).expanduser()

    def load(self) -> ApplicationSettings:
        """Read settings or return defaults when no state file exists."""
        if not self.path.exists():
            return ApplicationSettings()
        if not self.path.is_file():
            raise ApplicationInputError(
                f"Application state path is not a file: {self.path}"
            )

        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise ApplicationInputError(
                f"Could not read application state: {self.path}"
            ) from exc

        if not isinstance(payload, dict):
            raise ApplicationInputError("Application state must be a JSON object.")
        version = payload.get("schema_version")
        if version != _STATE_SCHEMA_VERSION:
            raise ApplicationInputError(
                f"Unsupported application state schema: {version!r}."
            )
        settings = payload.get("settings")
        if not isinstance(settings, dict):
            raise ApplicationInputError(
                "Application state is missing its settings object."
            )
        allowed_keys = set(ApplicationSettings.__dataclass_fields__)
        if set(settings) - allowed_keys:
            raise ApplicationInputError(
                "Application state contains unknown settings."
            )
        try:
            return ApplicationSettings(**settings)
        except (TypeError, ApplicationInputError) as exc:
            raise ApplicationInputError(
                "Application state contains invalid settings."
            ) from exc

    def save(self, settings: ApplicationSettings) -> None:
        """Persist settings atomically; never partially overwrite prior state."""
        if not isinstance(settings, ApplicationSettings):
            raise ApplicationInputError(
                "settings must be an ApplicationSettings instance."
            )
        payload: dict[str, Any] = {
            "schema_version": _STATE_SCHEMA_VERSION,
            "settings": asdict(settings),
        }
        encoded = json.dumps(
            payload, ensure_ascii=False, indent=2, sort_keys=True
        ) + "\n"

        parent = self.path.parent
        try:
            parent.mkdir(parents=True, exist_ok=True)
            fd, temporary_name = tempfile.mkstemp(
                prefix=f".{self.path.name}.",
                suffix=".tmp",
                dir=parent,
                text=True,
            )
            temporary_path = Path(temporary_name)
            try:
                with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
                    handle.write(encoded)
                    handle.flush()
                    os.fsync(handle.fileno())
                os.replace(temporary_path, self.path)
            except BaseException:
                temporary_path.unlink(missing_ok=True)
                raise
        except OSError as exc:
            raise ApplicationInputError(
                f"Could not save application state: {self.path}"
            ) from exc


__all__ = ["ApplicationSettings", "ApplicationStateStore"]
