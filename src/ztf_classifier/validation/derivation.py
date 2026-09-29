"""Deterministic derivation of the published 730,184-object CPVS subset."""

from __future__ import annotations

import csv
import gzip
import hashlib
import json
import math
import zipfile
from collections import Counter
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
                "predicate": "at least one g-band detection >= g_sigma AND at least one r-band detection >= r_sigma, with finite non-zero magnitudes",
                "snr_from_magnitude_error": "1.0857362047581296 / mag_error",
            },
        }


def _split_fields(line: str) -> list[str]:
    """Split CPVS text rows across tab-, comma-, or whitespace-delimited formats."""
    stripped = line.strip()
    if stripped.startswith("#"):
        stripped = stripped[1:].lstrip()
    if "\t" in stripped:
        return [item.strip() for item in stripped.split("\t")]
    if "," in stripped:
        return [item.strip() for item in next(csv.reader([stripped], delimiter=","))]
    return stripped.split()


def _zip_member_matches_header(
    zf: zipfile.ZipFile,
    member: str,
    required_columns: Iterable[str],
) -> bool:
    required = {column.strip().lower() for column in required_columns}
    if not required:
        return False
    with zf.open(member, "r") as raw:
        sample = raw.read(256 * 1024).decode("utf-8", errors="replace")
    for line in sample.splitlines():
        if not line.strip():
            continue
        tokens = {token.lower() for token in _split_fields(line)}
        if required.issubset(tokens):
            return True
    return False


def _headerless_lightcurve_schema(required_columns: Iterable[str]) -> list[str] | None:
    """Return the canonical CPVS light-curve schema when the source omits a header."""
    required = {column.strip().lower() for column in required_columns}
    if "e_gmag" in required:
        return ["SourceID", "RAdeg", "DEdeg", "HJD", "gmag", "e_gmag", "g_flag"]
    if "e_rmag" in required:
        return ["SourceID", "RAdeg", "DEdeg", "HJD", "rmag", "e_rmag", "r_flag"]
    return None


def _looks_like_headerless_lightcurve(path: Path, required_columns: Iterable[str]) -> bool:
    schema = _headerless_lightcurve_schema(required_columns)
    if schema is None:
        return False
    try:
        with path.open("rb") as raw:
            for encoded in raw:
                line = encoded.decode("utf-8", errors="replace").strip()
                if not line or line.startswith("#"):
                    continue
                values = _split_fields(line)
                if len(values) != len(schema):
                    return False
                int(values[0])
                for value in values[1:5]:
                    float(value)
                float(values[5])
                int(float(values[6]))
                return True
    except (OSError, TypeError, ValueError):
        return False
    return False


def _path_member_matches_header(
    path: Path,
    required_columns: Iterable[str],
) -> bool:
    required = {column.strip().lower() for column in required_columns}
    if not required:
        return False
    opener = gzip.open if path.suffix.lower() == ".gz" else open
    with opener(path, "rb") as raw:
        sample = raw.read(256 * 1024).decode("utf-8", errors="replace")
    for line in sample.splitlines():
        if not line.strip():
            continue
        tokens = {token.lower() for token in _split_fields(line)}
        if required.issubset(tokens):
            return True
    return _looks_like_headerless_lightcurve(path, required_columns)


def _open_text(
    path: Path,
    member: str | None = None,
    *,
    required_columns: Iterable[str] = (),
):
    if path.suffix.lower() == ".zip":
        zf = zipfile.ZipFile(path)
        names = [name for name in zf.namelist() if not name.endswith("/")]
        if member is None:
            if len(names) != 1:
                candidates = [
                    name
                    for name in names
                    if _zip_member_matches_header(zf, name, required_columns)
                ]
                if len(candidates) == 1:
                    member = candidates[0]
                else:
                    zf.close()
                    if not candidates:
                        raise ValueError(
                            f"{path} contains {len(names)} files; no member matches "
                            f"required columns {tuple(required_columns)!r}"
                        )
                    raise ValueError(
                        f"{path} has multiple members matching required columns "
                        f"{tuple(required_columns)!r}: {tuple(candidates)!r}; specify member explicitly"
                    )
            else:
                member = names[0]
        if member not in names:
            zf.close()
            raise ValueError(f"member {member!r} not found in {path}")
        return zf, zf.open(member, "r")
    if path.suffix.lower() == ".gz":
        return None, gzip.open(path, "rb")
    return None, path.open("rb")


def _iter_rows(
    path: Path,
    member: str | None = None,
    *,
    required_columns: Iterable[str] = (),
) -> Iterator[dict[str, str]]:
    """Yield rows from CPVS files while handling metadata and common delimiters."""
    if path.is_dir():
        candidates = sorted(
            item
            for item in path.rglob("*")
            if item.is_file()
            and item.suffix.lower() in {".csv", ".txt", ".dat", ".json", ".gz", ""}
            and _path_member_matches_header(item, required_columns)
        )
        if not candidates:
            raise ValueError(
                f"{path} contains no file matching required columns "
                f"{tuple(required_columns)!r}"
            )
        for candidate in candidates:
            yield from _iter_rows(
                candidate,
                required_columns=required_columns,
            )
        return

    owner, raw = _open_text(path, member, required_columns=required_columns)
    try:
        lines = (line.decode("utf-8", errors="replace") for line in raw)
        header_line = None
        header_tokens: list[str] = []
        source_tokens = {"sourceid", "source_id", "oid", "ztf_id"}
        first_data_line: str | None = None
        for line in lines:
            if not line.strip():
                continue
            stripped = line.strip()
            tokens = _split_fields(stripped)
            normalized = {token.strip().lower() for token in tokens}
            if source_tokens.intersection(normalized):
                header_line = stripped
                header_tokens = tokens
                break
            if _headerless_lightcurve_schema(required_columns) is not None:
                first_data_line = stripped
                break
        if header_line is None:
            schema = _headerless_lightcurve_schema(required_columns)
            if schema is None:
                return
            header = schema
            if first_data_line is not None:
                values = _split_fields(first_data_line)
                if len(values) == len(header):
                    yield dict(zip(header, values))
            for line in lines:
                if not line.strip():
                    continue
                stripped = line.strip()
                if stripped.startswith("#"):
                    continue
                values = _split_fields(stripped)
                if len(values) == len(header):
                    yield dict(zip(header, values))
            return

        if "	" in header_line:
            parse = lambda value: [item.strip() for item in value.split("	")]
        elif "," in header_line:
            parse = lambda value: [
                item.strip() for item in next(csv.reader([value], delimiter=","))
            ]
        else:
            parse = lambda value: value.split()

        header = header_tokens
        if not header:
            header = parse(header_line)

        for line in lines:
            if not line.strip():
                continue
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            values = parse(stripped)
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


def _source_ids_from_catalog(parent_path: Path, member: str | None) -> set[str]:
    """Resolve CPVS SourceIDs from the published Table2 row order."""
    owner, raw = _open_text(parent_path, member)
    try:
        source_ids: set[str] = set()
        ordinal = 0
        for encoded in raw:
            line = encoded.decode("utf-8", errors="replace").strip()
            if not line:
                continue
            first_token = line.split()[0]
            if not first_token.upper().startswith("ZTF"):
                continue
            fields = _split_fields(line)
            if len(fields) < 2:
                continue
            try:
                source_id = str(int(float(fields[1])))
            except (TypeError, ValueError):
                continue
            source_ids.add(source_id)
        return source_ids
    finally:
        raw.close()
        if owner is not None:
            owner.close()


def _source_ids(parent_path: Path, member: str | None) -> set[str]:
    """Resolve IDs for either published CPVS Table2 or generic test/artifact tables."""
    owner, raw = _open_text(parent_path, member)
    try:
        saw_catalog_row = False
        for encoded in raw:
            line = encoded.decode("utf-8", errors="replace").strip()
            if line and line.split()[0].upper().startswith("ZTF"):
                saw_catalog_row = True
                break
    finally:
        raw.close()
        if owner is not None:
            owner.close()

    if saw_catalog_row:
        # CPVS Table2 uses ZTF names as row identifiers; SourceID is the
        # published ordinal. Metadata/header sections must not terminate scan.
        return _source_ids_from_catalog(parent_path, member)

    rows = _iter_rows(parent_path, member, required_columns=("SourceID",))
    first = next(rows, None)
    if first is None:
        return set()
    key = _find_key(first, ("SourceID", "sourceid", "oid", "ztf_id"))
    return {
        row[key].strip()
        for row in chain((first,), rows)
        if row.get(key, "").strip()
    }


def _qualified_ids(
    path: Path,
    *,
    sigma: float,
    parent_ids: set[str],
    member: str | None,
    error_columns: Iterable[str],
    flag_columns: Iterable[str] = (),
    diagnostics: dict[str, object] | None = None,
) -> tuple[set[str], set[str]]:
    rows = _iter_rows(
        path,
        member,
        required_columns=("SourceID", *error_columns, "gmag" if "e_gmag" in error_columns else "rmag"),
    )
    first = next(rows, None)
    if first is None:
        return set()
    id_key = _find_key(first, ("SourceID", "sourceid", "oid", "ztf_id"))
    error_key = _find_key(first, error_columns)
    mag_key = _find_key(first, ("gmag",) if "e_gmag" in error_columns else ("rmag",))
    flag_key = None
    try:
        flag_key = _find_key(first, flag_columns)
    except ValueError:
        pass

    selected: set[str] = set()
    flag_zero: set[str] = set()
    flag_lt_32768: set[str] = set()
    flag_values: Counter[str] = Counter()
    valid_magnitude: set[str] = set()

    for row in chain((first,), rows):
        oid = row.get(id_key, "").strip()
        if oid not in parent_ids or _snr_from_mag_error(row.get(error_key, "")) < sigma:
            continue
        try:
            magnitude = float(row.get(mag_key, ""))
        except (TypeError, ValueError):
            magnitude = float("nan")
        if math.isfinite(magnitude) and magnitude != 0.0:
            valid_magnitude.add(oid)
        selected.add(oid)
        if flag_key is None:
            continue
        raw_flag = row.get(flag_key, "").strip()
        flag_values[raw_flag] += 1
        try:
            flag = int(float(raw_flag))
        except (TypeError, ValueError):
            continue
        if flag == 0:
            flag_zero.add(oid)
        if 0 <= flag < 32768:
            flag_lt_32768.add(oid)

    if diagnostics is not None:
        band = "g" if "e_gmag" in {c.strip().lower() for c in error_columns} else "r"
        diagnostics[band] = {
            "flag_column": flag_key,
            "eligible": len(selected),
            "flag_zero": len(flag_zero),
            "flag_nonzero": len(selected - flag_zero),
            "valid_magnitude": len(valid_magnitude),
            "flag_zero_valid_magnitude": len(flag_zero & valid_magnitude),
            "flag_lt_32768": len(flag_lt_32768),
            "top_flags": flag_values.most_common(10),
        }
    quality_ids = flag_zero & valid_magnitude if flag_key is not None else valid_magnitude
    return selected, quality_ids


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
        raise ValueError(
            f"parent row/object count mismatch: expected {expected_parent_rows}, got {len(parent_ids)}"
        )

    diagnostics: dict[str, object] = {}
    g_ids, g_flag_zero = _qualified_ids(
        g_lightcurve,
        sigma=config.g_sigma,
        parent_ids=parent_ids,
        member=g_member,
        error_columns=("e_gmag", "magerr", "mag_err", "error"),
        flag_columns=(),
        diagnostics=diagnostics,
    )
    r_ids, r_flag_zero = _qualified_ids(
        r_lightcurve,
        sigma=config.r_sigma,
        parent_ids=parent_ids,
        member=r_member,
        error_columns=("e_rmag", "magerr", "mag_err", "error"),
        flag_columns=(),
        diagnostics=diagnostics,
    )
    snr_selected = g_ids & r_ids
    flag_zero_selected = g_flag_zero & r_flag_zero
    diagnostics["intersection"] = {
        "snr_only_count": len(snr_selected),
        "both_bands_flag_zero_count": len(flag_zero_selected),
        "snr_removed_by_flag_quality": len(snr_selected - flag_zero_selected),
        "selection_predicate": "g SNR >= 2.5 AND r SNR >= 3.0 AND finite non-zero g/r magnitudes",
    }
    selected = sorted(flag_zero_selected)

    # Always materialize the candidate membership before asserting the
    # published cardinality. This is diagnostic evidence, not acceptance:
    # a cardinality mismatch must remain a hard failure, but the candidate
    # set must be available for an independent membership audit.
    output.parent.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256()
    with output.open("w", encoding="utf-8", newline="") as handle:
        handle.write("SourceID\n")
        digest.update(b"SourceID\n")
        for oid in selected:
            encoded = f"{oid}\n".encode()
            handle.write(encoded.decode("utf-8"))
            digest.update(encoded)

    if len(selected) != expected_selected_rows:
        diagnostic = {
            "status": "COUNT_MISMATCH",
            "expected_selected_rows": expected_selected_rows,
            "observed_selected_rows": len(selected),
            "quality_diagnostics": diagnostics,
            "candidate_sha256": digest.hexdigest(),
        }
        output.with_name(output.name + ".diagnostic.json").write_text(
            json.dumps(diagnostic, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        raise ValueError(
            "derived subset count mismatch: "
            f"expected {expected_selected_rows}, got {len(selected)}; "
            f"quality diagnostics={json.dumps(diagnostics, sort_keys=True)}"
        )

    result = DerivationResult(
        len(parent_ids),
        len(selected),
        digest.hexdigest(),
        output,
        config,
    )
    if parent_evidence_sha256 is None:
        raise ValueError("parent_evidence_sha256 is required to emit scientific 730k evidence")
    selection_manifest = json.dumps(
        result.to_dict()["selection"],
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
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
