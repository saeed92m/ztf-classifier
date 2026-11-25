"""Local, per-user workspaces for the Windows preview."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import tempfile
import time
from dataclasses import replace
from pathlib import Path
from threading import RLock
from typing import Any
from uuid import uuid4

from ztf_classifier.application.state import ApplicationStateStore

_WORKSPACE_ID_RE = re.compile(r"^[0-9a-f]{32}$")
_EXPORT_NAME_RE = re.compile(r"^dr24-raw-export-[0-9]{8}T[0-9]{6}Z-[0-9a-f]{8}\.json$")


class WorkspaceError(ValueError):
    """Raised when workspace input or persisted state is invalid."""


class WorkspaceNotFoundError(FileNotFoundError):
    """Raised when a requested workspace or export does not exist."""


class WorkspaceConflictError(RuntimeError):
    """Raised when a workspace operation conflicts with current state."""


class WorkspaceStore:
    """Manage versioned workspaces under one application-owned directory."""

    schema_version = "ztf-workspace-v1"

    def __init__(
        self,
        root: Path | str,
        settings_store: ApplicationStateStore,
        *,
        max_export_bytes: int = 250 * 1024 * 1024,
    ) -> None:
        self.root = Path(root).expanduser().resolve()
        self.settings_store = settings_store
        self.max_export_bytes = max_export_bytes
        self._lock = RLock()
        self._active_operation_ids: set[str] = set()
        self.root.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _now() -> str:
        return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    @staticmethod
    def _validate_name(name: str) -> str:
        cleaned = name.strip()
        if (
            not cleaned
            or len(cleaned) > 64
            or not cleaned.isprintable()
            or "/" in cleaned
            or "\\" in cleaned
        ):
            raise WorkspaceError(
                "Workspace name must contain 1–64 printable characters and no path separators."
            )
        return cleaned

    def _write_bytes_atomic(self, path: Path, content: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=".workspace-",
            suffix=".tmp",
            dir=path.parent,
        )
        temporary_path = Path(temporary_name)
        try:
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary_path, path)
        except Exception:
            temporary_path.unlink(missing_ok=True)
            raise

    def _write_json_atomic(self, path: Path, value: dict[str, Any]) -> None:
        encoded = (
            json.dumps(
                value,
                ensure_ascii=False,
                allow_nan=False,
                indent=2,
                sort_keys=True,
            )
            + "\n"
        ).encode("utf-8")
        self._write_bytes_atomic(path, encoded)

    def _append_operation_log(self, directory: Path, operation: dict[str, Any]) -> None:
        log_path = directory / "logs" / "operations.jsonl"
        existing: list[str] = []
        if log_path.is_file():
            existing = log_path.read_text(encoding="utf-8").splitlines()[-99:]
        line = json.dumps(
            operation,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
        )
        self._write_bytes_atomic(
            log_path,
            ("\n".join([*existing, line]) + "\n").encode("utf-8"),
        )

    def _resolve_workspace_id(self, workspace_id: str) -> Path:
        if not _WORKSPACE_ID_RE.fullmatch(workspace_id):
            raise WorkspaceError("Workspace identifier is invalid.")
        directory = (self.root / workspace_id).resolve(strict=False)
        if directory.parent != self.root or not directory.is_dir():
            raise WorkspaceNotFoundError("Workspace was not found.")
        return directory

    def _resolve_workspace_directory(self, directory: str | Path) -> Path:
        candidate = Path(directory).expanduser().resolve(strict=False)
        if candidate.parent != self.root or not _WORKSPACE_ID_RE.fullmatch(
            candidate.name
        ):
            raise WorkspaceError(
                "Workspace directory must be inside the application workspace root."
            )
        if not candidate.is_dir():
            raise WorkspaceNotFoundError("Workspace directory was not found.")
        return candidate

    def _read_manifest(self, directory: Path) -> dict[str, Any]:
        path = directory / "workspace.json"
        if not path.is_file():
            raise WorkspaceError("Workspace manifest is missing.")
        try:
            manifest = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise WorkspaceError("Workspace manifest cannot be read.") from exc
        if (
            not isinstance(manifest, dict)
            or manifest.get("schema_version") != self.schema_version
            or manifest.get("workspace_id") != directory.name
            or not isinstance(manifest.get("name"), str)
        ):
            raise WorkspaceError("Workspace manifest schema is invalid.")
        return manifest

    def _save_active_directory(self, directory: Path) -> None:
        current = self.settings_store.load()
        self.settings_store.save(
            replace(current, workspace_directory=str(directory))
        )

    def _summary(
        self,
        directory: Path,
        manifest: dict[str, Any],
        *,
        active: bool,
        status: str = "READY",
    ) -> dict[str, Any]:
        return {
            "workspace_id": manifest["workspace_id"],
            "name": manifest["name"],
            "directory": str(directory),
            "exports_directory": str(directory / "exports"),
            "logs_directory": str(directory / "logs"),
            "application_logs_directory": str(self.root.parent / "logs"),
            "created_at_utc": manifest["created_at_utc"],
            "last_opened_at_utc": manifest["last_opened_at_utc"],
            "last_operation": manifest.get("last_operation"),
            "last_export": manifest.get("last_export"),
            "is_active": active,
            "status": status,
        }

    def _mark_interrupted(
        self,
        directory: Path,
        manifest: dict[str, Any],
    ) -> dict[str, Any]:
        operation = manifest.get("last_operation")
        if (
            not isinstance(operation, dict)
            or operation.get("status") != "RUNNING"
            or operation.get("operation_id") in self._active_operation_ids
        ):
            return manifest
        operation["status"] = "INTERRUPTED"
        operation["completed_at_utc"] = self._now()
        operation["error_code"] = "application_restarted"
        operation["error_message"] = (
            "The application restarted before the operation completed."
        )
        self._write_json_atomic(directory / "workspace.json", manifest)
        self._append_operation_log(directory, operation)
        return manifest

    def create(self, name: str) -> dict[str, Any]:
        with self._lock:
            cleaned_name = self._validate_name(name)
            for item in self.list()["items"]:
                if (
                    item.get("status") != "CORRUPT"
                    and item.get("name", "").casefold() == cleaned_name.casefold()
                ):
                    raise WorkspaceConflictError(
                        "A workspace with this name already exists."
                    )
            workspace_id = uuid4().hex
            directory = self.root / workspace_id
            directory.mkdir(parents=False, exist_ok=False)
            (directory / "exports").mkdir()
            (directory / "logs").mkdir()
            now = self._now()
            manifest: dict[str, Any] = {
                "schema_version": self.schema_version,
                "workspace_id": workspace_id,
                "name": cleaned_name,
                "created_at_utc": now,
                "last_opened_at_utc": now,
                "last_operation": None,
                "last_export": None,
            }
            try:
                self._write_json_atomic(directory / "workspace.json", manifest)
                self._save_active_directory(directory)
            except Exception:
                shutil.rmtree(directory, ignore_errors=True)
                raise
            return self._summary(directory, manifest, active=True, status="ACTIVE")

    def open(self, workspace_id: str) -> dict[str, Any]:
        with self._lock:
            directory = self._resolve_workspace_id(workspace_id)
            manifest = self._read_manifest(directory)
            manifest = self._mark_interrupted(directory, manifest)
            manifest["last_opened_at_utc"] = self._now()
            self._write_json_atomic(directory / "workspace.json", manifest)
            self._save_active_directory(directory)
            return self._summary(directory, manifest, active=True, status="ACTIVE")

    def active(self) -> dict[str, Any] | None:
        with self._lock:
            settings = self.settings_store.load()
            if not settings.workspace_directory:
                return None
            directory = self._resolve_workspace_directory(
                settings.workspace_directory
            )
            manifest = self._read_manifest(directory)
            manifest = self._mark_interrupted(directory, manifest)
            return self._summary(directory, manifest, active=True, status="ACTIVE")

    def list(self) -> dict[str, Any]:
        with self._lock:
            try:
                active_workspace = self.active()
            except (WorkspaceError, WorkspaceNotFoundError):
                active_workspace = None
            active_id = (
                active_workspace["workspace_id"] if active_workspace else None
            )
            items: list[dict[str, Any]] = []
            for directory in self.root.iterdir():
                if (
                    not directory.is_dir()
                    or not _WORKSPACE_ID_RE.fullmatch(directory.name)
                ):
                    continue
                try:
                    resolved = directory.resolve(strict=True)
                    if resolved.parent != self.root:
                        continue
                    manifest = self._read_manifest(resolved)
                    is_active = manifest["workspace_id"] == active_id
                    items.append(
                        self._summary(
                            resolved,
                            manifest,
                            active=is_active,
                            status="ACTIVE" if is_active else "READY",
                        )
                    )
                except (OSError, WorkspaceError):
                    items.append(
                        {
                            "workspace_id": directory.name,
                            "name": "Invalid workspace",
                            "directory": str(directory),
                            "is_active": False,
                            "status": "CORRUPT",
                            "last_operation": None,
                            "last_export": None,
                        }
                    )
            items.sort(
                key=lambda item: (
                    item.get("status") == "CORRUPT",
                    str(item.get("name", "")).casefold(),
                )
            )
            return {"items": items, "active_workspace_id": active_id}

    def validate_workspace_directory(self, directory: str | Path) -> Path:
        with self._lock:
            resolved = self._resolve_workspace_directory(directory)
            self._read_manifest(resolved)
            return resolved

    def record_operation(self, payload: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            active = self.active()
            if active is None:
                raise WorkspaceNotFoundError("Create or open a workspace first.")
            directory = Path(active["directory"])
            manifest = self._read_manifest(directory)
            status = payload.get("status")
            operation_type = payload.get("operation_type")
            source = payload.get("source")
            if operation_type != "DR24_BATCH_QUERY":
                raise WorkspaceError("Unsupported workspace operation type.")
            if source != "ztf_dr24_hats":
                raise WorkspaceError("Unsupported DR24 data source.")
            current = manifest.get("last_operation")
            if status == "RUNNING":
                requested = payload.get("requested_oids")
                if (
                    not isinstance(requested, list)
                    or not requested
                    or len(requested) > 10
                    or any(type(value) is not int or value <= 0 for value in requested)
                    or len(requested) != len(set(requested))
                ):
                    raise WorkspaceError("Requested OIDs are invalid.")
                if (
                    isinstance(current, dict)
                    and current.get("status") == "RUNNING"
                    and current.get("operation_id") in self._active_operation_ids
                ):
                    raise WorkspaceConflictError(
                        "A workspace operation is already running."
                    )
                if isinstance(current, dict) and current.get("status") == "RUNNING":
                    current["status"] = "INTERRUPTED"
                    current["completed_at_utc"] = self._now()
                    current["error_code"] = "operation_replaced"
                    current["error_message"] = (
                        "A new operation replaced an incomplete operation."
                    )
                    self._active_operation_ids.discard(
                        str(current.get("operation_id", ""))
                    )
                    self._append_operation_log(directory, current)
                operation_id = payload.get("operation_id")
                if operation_id is None:
                    operation_id = uuid4().hex
                if (
                    not isinstance(operation_id, str)
                    or not _WORKSPACE_ID_RE.fullmatch(operation_id)
                ):
                    raise WorkspaceError("Operation identifier is invalid.")
                operation = {
                    "operation_id": operation_id,
                    "operation_type": operation_type,
                    "source": source,
                    "status": "RUNNING",
                    "started_at_utc": self._now(),
                    "completed_at_utc": None,
                    "requested_oids": requested,
                    "returned_oids": [],
                    "missing_oids": [],
                    "payload_sha256_by_oid": {},
                    "error_code": None,
                    "error_message": None,
                    "export_file": None,
                    "export_sha256": None,
                }
                self._active_operation_ids.add(operation_id)
            elif status in {"SUCCEEDED", "FAILED"}:
                operation_id = payload.get("operation_id")
                if (
                    not isinstance(current, dict)
                    or current.get("status") != "RUNNING"
                    or current.get("operation_id") != operation_id
                ):
                    raise WorkspaceConflictError(
                        "Operation completion does not match the active operation."
                    )
                operation = current
                requested = current.get("requested_oids")
                if (
                    not isinstance(requested, list)
                    or not requested
                    or len(requested) > 10
                    or any(type(value) is not int or value <= 0 for value in requested)
                    or len(requested) != len(set(requested))
                ):
                    raise WorkspaceError("Stored requested OIDs are invalid.")
                supplied_requested = payload.get("requested_oids")
                if supplied_requested is not None and supplied_requested != requested:
                    raise WorkspaceError(
                        "Completion requested OIDs do not match the active operation."
                    )
                returned = payload.get("returned_oids", [])
                missing = payload.get("missing_oids", [])
                hashes = payload.get("payload_sha256_by_oid", {})
                if (
                    not isinstance(returned, list)
                    or not isinstance(missing, list)
                    or any(type(value) is not int or value <= 0 for value in returned)
                    or any(type(value) is not int or value <= 0 for value in missing)
                    or len(returned) != len(set(returned))
                    or len(missing) != len(set(missing))
                ):
                    raise WorkspaceError("Returned or missing OIDs are invalid.")
                if status == "SUCCEEDED":
                    if (
                        set(returned) & set(missing)
                        or set(returned) | set(missing) != set(requested)
                    ):
                        raise WorkspaceError(
                            "Successful operation OID accounting is incomplete."
                        )
                    if not isinstance(hashes, dict) or set(hashes) != {
                        str(value) for value in returned
                    }:
                        raise WorkspaceError(
                            "Payload hash mapping does not match returned OIDs."
                        )
                    if any(
                        not isinstance(value, str)
                        or not re.fullmatch(r"[0-9a-f]{64}", value)
                        for value in hashes.values()
                    ):
                        raise WorkspaceError("Payload SHA-256 value is invalid.")
                operation.update(
                    {
                        "status": status,
                        "completed_at_utc": self._now(),
                        "returned_oids": returned,
                        "missing_oids": missing,
                        "payload_sha256_by_oid": hashes,
                        "error_code": payload.get("error_code"),
                        "error_message": payload.get("error_message"),
                    }
                )
                self._active_operation_ids.discard(str(operation_id))
            else:
                raise WorkspaceError("Operation status is invalid.")
            manifest["last_operation"] = operation
            self._write_json_atomic(directory / "workspace.json", manifest)
            self._append_operation_log(directory, operation)
            return operation

    def save_export(self, payload: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            active = self.active()
            if active is None:
                raise WorkspaceNotFoundError("Create or open a workspace first.")
            if not isinstance(payload, dict):
                raise WorkspaceError("Export payload must be a JSON object.")
            encoded = (
                json.dumps(
                    payload,
                    ensure_ascii=False,
                    allow_nan=False,
                    indent=2,
                    sort_keys=True,
                )
                + "\n"
            ).encode("utf-8")
            if len(encoded) > self.max_export_bytes:
                raise WorkspaceError("Export exceeds the workspace size limit.")
            directory = Path(active["directory"])
            manifest = self._read_manifest(directory)
            operation = manifest.get("last_operation")
            if not isinstance(operation, dict) or operation.get("status") != "SUCCEEDED":
                raise WorkspaceConflictError(
                    "A successful DR24 operation is required before export."
                )
            now = self._now()
            file_name = (
                "dr24-raw-export-"
                + time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
                + "-"
                + uuid4().hex[:8]
                + ".json"
            )
            export_path = directory / "exports" / file_name
            self._write_bytes_atomic(export_path, encoded)
            metadata = {
                "file_name": file_name,
                "path": str(export_path),
                "sha256": hashlib.sha256(encoded).hexdigest(),
                "size_bytes": len(encoded),
                "created_at_utc": now,
            }
            manifest["last_export"] = metadata
            operation["export_file"] = file_name
            operation["export_sha256"] = metadata["sha256"]
            self._write_json_atomic(directory / "workspace.json", manifest)
            return metadata

    def export_path(self, file_name: str) -> Path:
        with self._lock:
            if not _EXPORT_NAME_RE.fullmatch(file_name):
                raise WorkspaceError("Export filename is invalid.")
            active = self.active()
            if active is None:
                raise WorkspaceNotFoundError("Create or open a workspace first.")
            exports = (Path(active["directory"]) / "exports").resolve(strict=True)
            candidate = (exports / file_name).resolve(strict=True)
            if candidate.parent != exports or not candidate.is_file():
                raise WorkspaceNotFoundError("Workspace export was not found.")
            return candidate
