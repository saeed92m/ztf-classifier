#!/usr/bin/env python3
"""Capture a bounded, fixed-OID DR24 API evidence bundle.

This command is intended for an explicit workflow dispatch. It makes one
application-boundary request for the two pinned OIDs and never emits the
process environment or request headers.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from fastapi.testclient import TestClient

from ztf_classifier.api.app import create_app
from ztf_classifier.api.config import ApiSettings
from ztf_classifier.application.observations import ObservationService
from ztf_classifier.io.dr24_lightcurve import DR24LightcurveBackend
from ztf_classifier.validation.dr24_evidence import (
    API_PATH,
    FIXED_OIDS,
    redact_secrets,
    utc_now,
    validate_api_payload,
    write_evidence_bundle,
)


def _git_sha() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return "unavailable"


def _json_log(path: Path, event: str, **fields: object) -> None:
    safe = redact_secrets({"event": event, **fields})
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(safe, ensure_ascii=False, sort_keys=True) + "\n")


def _transport_failure(exc: BaseException) -> tuple[str, str]:
    name = type(exc).__name__
    lowered = name.lower()
    if "timeout" in lowered:
        return "TIMEOUT", name
    if any(part in lowered for part in ("connect", "connection", "network")):
        return "CONNECTION_ERROR", name
    return "REQUEST_ERROR", name


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--software-commit", default=None)
    args = parser.parse_args()
    output = args.output_dir.resolve()
    if output.exists() and any(output.iterdir()):
        parser.error("output directory must be empty; refusing to overwrite")
    output.mkdir(parents=True, exist_ok=True)
    log_path = output / "capture.log"
    started = utc_now()
    _json_log(log_path, "capture_started", requested_oids=list(FIXED_OIDS))
    status_code: int | None = None
    transport_status = "NOT_ATTEMPTED"
    transport_error_type: str | None = None
    response_bytes = b""
    result = 1
    try:
        with tempfile.TemporaryDirectory(prefix="ztf-dr24-evidence-state-") as state:
            state_dir = Path(state)
            settings = ApiSettings(
                observation_cache_dir=state_dir / "cache",
                job_store_path=state_dir / "jobs.sqlite3",
                result_store_path=state_dir / "results.sqlite3",
                application_state_path=state_dir / "settings.json",
                scientific_registry_dir=state_dir / "registry",
                scientific_evidence_dir=state_dir / "scientific-evidence",
            )
            observations = ObservationService(
                client=object(),
                cache_dir=settings.observation_cache_dir,
                dr24_backend=DR24LightcurveBackend(),
            )
            app = create_app(settings=settings, observation_service=observations)
            with TestClient(app) as client:
                response = client.post(API_PATH, json={"objectids": list(FIXED_OIDS)})
                status_code = response.status_code
                transport_status = "RESPONSE_RECEIVED"
                response_bytes = response.content
        response_summary = None
        try:
            response_summary = json.loads(response_bytes)
            returned_oids = response_summary.get("provenance", {}).get(
                "returned_oids", []
            )
        except (UnicodeDecodeError, json.JSONDecodeError, AttributeError):
            returned_oids = []
        _json_log(
            log_path,
            "api_response_received",
            http_status_code=status_code,
            requested_oids=list(FIXED_OIDS),
            returned_oids=returned_oids,
            response_size_bytes=len(response_bytes),
        )
        payload_errors, _ = validate_api_payload(response_summary)
        validation_errors = payload_errors + (
            ["api_http_status_not_200"] if status_code != 200 else []
        )
        _json_log(
            log_path,
            "validation_result",
            status="PASS" if not validation_errors else "FAIL",
            errors=validation_errors,
        )
        result = 0 if status_code == 200 and not validation_errors else 1
    except Exception as exc:  # noqa: BLE001 - record all acquisition failures without leaking detail
        if status_code is None:
            transport_status, transport_error_type = _transport_failure(exc)
        else:
            transport_status = "RESPONSE_RECEIVED"
            transport_error_type = None
        _json_log(
            log_path,
            "capture_failed",
            transport_status=transport_status,
            error_type=type(exc).__name__,
        )

    completed = utc_now()
    _, bundle_errors = write_evidence_bundle(
        output,
        api_response_bytes=response_bytes,
        api_status_code=status_code,
        software_commit_sha=args.software_commit or _git_sha(),
        python_version=sys.version.split()[0],
        execution_started_at_utc=started,
        execution_completed_at_utc=completed,
        test_command="python scripts/capture_dr24_evidence.py --output-dir <bundle>",
        execution_log_path="capture.log",
        transport_status=transport_status,
        transport_error_type=transport_error_type,
    )
    return 0 if result == 0 and not bundle_errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
