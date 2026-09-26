"""Deterministic derivation of the published 730,184-object CPVS subset."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import zipfile
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from datetime import UTC, datetime
from itertools import chain
from pathlib import Path

from ztf_classifier.validation.evidence import (
    EvidenceArtifact,
    write_evidence_manifest,
)


@dataclass(frozen=True)
class DerivationConfig:
    g_sigma: float = 2.5
    r_sigma: float = 3.0

    def validate(self) -> None:
        if self.g_sigma <= 0 or self.r_sigma <= 0:
            raise ValueError("sigma thresholds must be positive")


_DEFAULT_DERIVATION_CONFIG = DerivationConfig()


@dataclass(frozen=True)
class DerivationResult:
    parent_rows: int
    selected_rows: int
    selected_sha256: str
    output: Path
    config: DerivationConfig

    def to_dict(self) -> dict[str, object]:
        return {
            "parent_rows": self.parent_rows,
            "selected_rows": self.selected_rows,
            "selected_sha256": self.selected_sha256,
            "output": str(self.output),
            "selection": {
                "g_sigma": self.config.g_sigma,
                "r_sigma": self.config.r_sigma,
                "predicate": "at least one g-band detection >= g_sigma AND at least one r-band detection >= r_sigma",
                "snr_from_magnitude_error": "1.0857362047581296 / mag_error",
            },
        }


def _open_text(path: Path, member: str | None = None):
    if path.suffix.lower() == ".zip":
        zf = zipfile.ZipFile(path)
        names = [name for name in zf.namelist() if not name.endswith("/")]
        if member is None:
            if len(names) != 1:
                zf.close()
                raise ValueError(f"{path} contains {len(names)} files; specify member explicitly")
            member = names[0]
        if member not in names:
            zf.close()
            raise ValueError(f"member {member!r} not found in {path}")
        return zf, zf.open(member, "r")
    return None, path.open("rb")


def _iter_rows(path: Path, member: str | None = None) -> Iterator[dict[str, str]]:
    owner, raw = _open_text(path, member)
    try:
        lines = (line.decode("utf-8", errors="replace") for line in raw)
        header_line = next(
            (
                line
                for line in lines
                if line.strip()
                and not line.lstrip().startswith("#")
                and any(
                    token.strip().lower() in {"sourceid", "source_id", "oid", "ztf_id"}
                    for token in line.replace(",", "\t").split("\t")
                )
            ),
            None,
        )
        if header_line is None:
            return
        delimiter = "\t" if "\t" in header_line else ","
        header = [item.strip() for item in next(csv.reader([header_line], delimiter=delimiter))]
        for values in csv.reader(lines, delimiter=delimiter):
            if values and len(values) == len(header):
                yield dict(zip(header, values))
    finally:
        raw.close()
        if owner is not None:
            owner.close()


def _find_key(row: dict[str, str], candidates: Iterable[str]) -> str:
    normalized = {key.strip().lower(): key for key in row}
    for candidate in candidates:
        if candidate.lower() in normalized:
            return normalized[candidate.lower()]
    raise ValueError(f"none of {tuple(candidates)!r} found; columns={tuple(row)}")


def _snr_from_mag_error(value: str) -> float:
    try:
        error = float(value)
    except (TypeError, ValueError):
        return float("nan")
    if not math.isfinite(error) or error <= 0:
        return float("nan")
    return 1.0857362047581296 / error


def _source_ids(parent_path: Path, member: str | None) -> set[str]:
    rows = _iter_rows(parent_path, member)
    first = next(rows, None)
    if first is None:
        return set()
    key = _find_key(first, ("SourceID", "sourceid", "oid", "ztf_id"))
    return {first[key].strip(), *(row[key].strip() for row in rows if row.get(key, "").strip())}


def _qualified_ids(
    path: Path,
    *,
    sigma: float,
    parent_ids: set[str],
    member: str | None,
) -> set[str]:
    rows = _iter_rows(path, member)
    first = next(rows, None)
    if first is None:
        return set()
    id_key = _find_key(first, ("SourceID", "sourceid", "oid", "ztf_id"))
    error_key = _find_key(first, ("e_gmag", "e_rmag", "magerr", "mag_err", "error"))
    selected: set[str] = set()
    for row in chain((first,), rows):
        oid = row.get(id_key, "").strip()
        if oid in parent_ids and _snr_from_mag_error(row.get(error_key, "")) >= sigma:
            selected.add(oid)
    return selected


def derive_730k(
    parent_path: Path,
    g_lightcurve: Path,
    r_lightcurve: Path,
    output: Path,
    *,
    config: DerivationConfig = _DEFAULT_DERIVATION_CONFIG,
    parent_member: str | None = None,
    g_member: str | None = None,
    r_member: str | None = None,
    expected_parent_rows: int = 781_602,
    expected_selected_rows: int = 730_184,
    parent_evidence_sha256: str | None = None,
    code_version: str = "working-tree",
) -> DerivationResult:
    """Derive the published subset from the pinned parent and source lightcurves."""
    config.validate()
    parent_ids = _source_ids(parent_path, parent_member)
    if len(parent_ids) != expected_parent_rows:
        raise ValueError(f"parent row/object count mismatch: expected {expected_parent_rows}, got {len(parent_ids)}")

    g_ids = _qualified_ids(g_lightcurve, sigma=config.g_sigma, parent_ids=parent_ids, member=g_member)
    r_ids = _qualified_ids(r_lightcurve, sigma=config.r_sigma, parent_ids=parent_ids, member=r_member)
    selected = sorted(g_ids & r_ids)
    if len(selected) != expected_selected_rows:
        raise ValueError(f"derived subset count mismatch: expected {expected_selected_rows}, got {len(selected)}")

    output.parent.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256()
    with output.open("w", encoding="utf-8", newline="") as handle:
        handle.write("SourceID\n")
        digest.update(b"SourceID\n")
        for oid in selected:
            encoded = f"{oid}\n".encode()
            handle.write(encoded.decode("utf-8"))
            digest.update(encoded)

    result = DerivationResult(len(parent_ids), len(selected), digest.hexdigest(), output, config)
    if parent_evidence_sha256 is None:
        raise ValueError("parent_evidence_sha256 is required to emit scientific 730k evidence")
    selection_manifest = json.dumps(result.to_dict()["selection"], sort_keys=True, separators=(",", ":")).encode("utf-8")
    write_evidence_manifest(
        output.with_name(output.name + ".evidence.json"),
        benchmark_id="ztf_periodic_730k",
        source_id="ztf_periodic_730k",
        acquisition_timestamp=datetime.now(UTC).isoformat(),
        code_version=code_version,
        artifacts=(EvidenceArtifact.from_path(output, "derived_benchmark_snapshot"),),
        parent_evidence_sha256=parent_evidence_sha256,
        query_manifest_sha256=hashlib.sha256(selection_manifest).hexdigest(),
    )
    output.with_name(output.name + ".derivation.json").write_text(
        json.dumps(result.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return result
