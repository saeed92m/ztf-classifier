"""Compare derived CPVS candidate membership with the published VizieR table.

Evidence model (issue #184 and its follow-up review):

* Raw ordered rows are preserved before set conversion, so duplicate IDs and
  per-ID multiplicities stay observable.
* Two independent equalities are required for a successful audit:

  ``unique_membership_equal``
      The *set* of IDs is identical.

  ``row_multiset_equal``
      The *exact* multiset of rows is identical, i.e. every ID occurs the
      same number of times in both inputs. This is decided by
      ``collections.Counter`` equality (authoritative) and cross-checked
      against ``row_multiset_sha256``, a canonical digest of the sorted
      ``(id, occurrence_count)`` pairs.

      Row count, unique-ID digest, the list of duplicated IDs and the total
      number of duplicate rows are *not* sufficient. The two sequences
      ``[1, 1, 2, 2, 2, 3]`` and ``[1, 1, 1, 2, 2, 3]`` agree on all four
      aggregates yet are different multisets.

* ``ordered_rows_sha256`` is kept separately as evidence of the original row
  order (file layout), never as a substitute for multiset equality: two files
  that list the same IDs in a different order have different ordered digests
  but equal multisets.

* Parsing is fail-closed. Invalid UTF-8, malformed data records, empty or
  non-numeric ID fields and truncated rows raise ``ValueError`` instead of
  being silently skipped, so a partial membership table can never be audited
  as if it were complete.

Exit status:

  0   audit completed and both equalities hold
  2   audit completed but at least one equality failed (report written)
  3   an input file could not be parsed fail-closed (no report written)

The report exposes ``comparison.exact_match`` and the top-level alias
``exact_membership_match``; both are true only when unique membership and the
exact row multiset agree, and the heavy scientific-validation workflow gates
on the alias.
"""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
from collections import Counter
from pathlib import Path

from ztf_classifier.validation.json_utils import dumps_strict

#: CDS ``table4.dat`` layout: the ``ID`` column occupies bytes 24-29 (1-based),
#: i.e. the 0-based slice ``[23:29]``.
_FIXED_WIDTH_ID_SLICE = slice(23, 29)

#: Characters that may make up a CDS separator/underline rule line.
_SEPARATOR_CHARS = frozenset("-=+|_ \t")

#: Strict ASCII decimal test. ``str.isdigit`` also accepts characters such as
#: ``"²"`` or Arabic-Indic digits, which ``int()`` then rejects.
_ASCII_DECIMAL = re.compile(r"[0-9]+")

#: Column tokens accepted alongside ``id`` in a headered VizieR TSV export.
_TSV_ZTF_COLUMNS = frozenset({"ztf", "ztf identifier", "ztf id"})

#: A ZTF object name (``ZTFJ000000.00+000000.0``) starts with ``ZTF`` followed
#: by a letter; a column header contains the bare token ``ZTF`` followed by
#: whitespace, so this distinguishes identifier rows from header rows.
_ZTF_NAME_PREFIX = re.compile(r"^\s*ZTF[A-Za-z]")


def _read_text_strict(path: Path) -> str:
    """Decode ``path`` as UTF-8, refusing to substitute replacement characters."""
    try:
        return path.read_text(encoding="utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise ValueError(
            f"{path}: invalid UTF-8 at byte offset {exc.start} ({exc.reason}); "
            "refusing to silently replace bytes"
        ) from exc


def _file_sha256(path: Path) -> str:
    """Return the SHA-256 of the raw source file bytes."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _parse_id(raw: str, path: Path, line_number: int) -> int:
    """Parse one ID field, raising on empty or non-numeric content."""
    text = raw.strip()
    if not text:
        raise ValueError(f"{path}:{line_number}: empty ID field")
    if _ASCII_DECIMAL.fullmatch(text) is None:
        raise ValueError(f"{path}:{line_number}: non-numeric ID field {text!r}")
    return int(text)


def _canonical_multiset_digest(counts: Counter) -> str:
    """SHA-256 over the sorted ``(id, occurrence_count)`` pairs."""
    payload = "\n".join(f"{oid}:{counts[oid]}" for oid in sorted(counts))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _is_fixed_width_column_header(stripped: str) -> bool:
    """True for a CDS column-name line such as ``ZTF   ID      Type``."""
    if _ASCII_DECIMAL.search(stripped) is not None:
        return False
    tokens = stripped.split()
    if "ID" not in tokens:
        return False
    return any(token.isalpha() for token in tokens)


def _is_fixed_width_preamble(line: str) -> bool:
    """Classify a pre-data fixed-width line as header/units/description metadata.

    A line is preamble metadata only while no data record has been seen, only
    if it contains no ASCII digits (every real ``ZTFJ...`` record does), and
    only if it does not look like a truncated ZTF identifier row.
    """
    stripped = line.strip()
    if _ASCII_DECIMAL.search(stripped) is not None:
        return False
    if _ZTF_NAME_PREFIX.match(line) is not None:
        return False
    return True


def _build_result(
    rows: list[int],
    parser_mode: str,
    source_sha256: str,
    metadata_line_count: int,
    include_full_multiplicities: bool = False,
) -> dict:
    """Assemble row-level evidence for one parsed membership table."""
    counts = Counter(rows)
    unique = set(counts)
    ordered_bytes = "\n".join(str(oid) for oid in rows).encode("utf-8")
    unique_bytes = "\n".join(str(oid) for oid in sorted(unique)).encode("utf-8")
    histogram = Counter(counts.values())
    duplicated = {oid: counts[oid] for oid in sorted(counts) if counts[oid] > 1}

    result = {
        "rows": rows,
        "unique": unique,
        "source_sha256": source_sha256,
        "parser_mode": parser_mode,
        "metadata_line_count": metadata_line_count,
        "row_count": len(rows),
        "unique_count": len(unique),
        "duplicate_ids": sorted(duplicated),
        "duplicate_id_counts": {str(oid): duplicated[oid] for oid in duplicated},
        "duplicate_row_count": len(rows) - len(unique),
        "multiplicity_histogram": {str(n): histogram[n] for n in sorted(histogram)},
        "max_multiplicity": max(counts.values()) if counts else 0,
        "ordered_rows_sha256": hashlib.sha256(ordered_bytes).hexdigest(),
        "unique_ids_sha256": hashlib.sha256(unique_bytes).hexdigest(),
        "row_multiset_sha256": _canonical_multiset_digest(counts),
        "all_id_multiplicities_included": include_full_multiplicities,
    }
    if include_full_multiplicities:
        result["all_id_multiplicities"] = {
            str(oid): counts[oid] for oid in sorted(counts)
        }
    return result


def read_selected(path: Path, *, include_full_multiplicities: bool = False) -> dict:
    """Read a ``SourceID``-selected file, preserving ordered rows and duplicates.

    Grammar (fail-closed):

    * the first non-blank line must be the ``SourceID`` header
      (case-insensitive);
    * every later non-blank line must be exactly one ASCII decimal ID;
    * blank lines are ignored; anything else raises ``ValueError``.

    Returns a dict with row-level evidence, including ``rows`` (ordered,
    duplicates preserved), ``unique``, ``row_count``, ``unique_count``,
    ``duplicate_ids``, ``duplicate_id_counts``, ``multiplicity_histogram``,
    ``source_sha256``, ``parser_mode``, ``ordered_rows_sha256``,
    ``unique_ids_sha256`` and ``row_multiset_sha256``.
    """
    text = _read_text_strict(path)
    lines = text.splitlines()

    header_index: int | None = None
    metadata_line_count = 0
    for index, line in enumerate(lines):
        if not line.strip():
            metadata_line_count += 1
            continue
        header_index = index
        if line.strip().lower() != "sourceid":
            raise ValueError(
                f"{path}:{index + 1}: expected 'SourceID' header, got {line.strip()!r}"
            )
        metadata_line_count += 1
        break

    if header_index is None:
        raise ValueError(f"{path}: empty file, expected 'SourceID' header")

    rows: list[int] = []
    for offset, line in enumerate(lines[header_index + 1 :], start=header_index + 2):
        if not line.strip():
            metadata_line_count += 1
            continue
        rows.append(_parse_id(line, path, offset))

    return _build_result(
        rows,
        "tsv",
        _file_sha256(path),
        metadata_line_count,
        include_full_multiplicities,
    )


def read_vizier(path: Path, *, include_full_multiplicities: bool = False) -> dict:
    """Read VizieR membership IDs, preserving ordered rows and duplicates.

    Two layouts are recognized, documented rather than guessed:

    ``tsv``
        A headered tab-separated export. The header is the first non-blank
        line whose tab-split tokens contain ``id`` together with one of
        ``ztf`` / ``ztf identifier`` / ``ztf id``, either bare or ``#``-
        prefixed. Every later non-blank, non-``#`` line is a data record and
        must carry a non-empty ASCII-decimal ID in that column.

    ``fixed-width``
        CDS ``table4.dat`` layout with the ID in bytes 24-29 (0-based
        ``[23:29]``). A line is metadata when it is blank, starts with ``#``,
        consists only of separator punctuation (``- = + | _``), or -- strictly
        before the first data record -- is a column-name/units/description
        line with no ASCII digits and no ZTF identifier prefix. Every other
        line is a data record and must carry a non-empty ASCII-decimal ID in
        that slice.

    Fail-closed guarantees: invalid UTF-8, malformed data records, empty or
    non-numeric IDs and truncated rows raise ``ValueError``. No data row is
    ever silently discarded, so a partial table can never be reported as a
    successful audit.

    Returns the same dict shape as :func:`read_selected`, plus
    ``metadata_line_count``.
    """
    text = _read_text_strict(path)
    lines = text.splitlines()

    parser_mode = "fixed-width"
    header_index: int | None = None
    id_index: int | None = None
    rows: list[int] = []
    metadata_line_count = 0

    # Locate a headered TSV layout. The header must be the first non-blank
    # line that is either bare or a "#"-prefixed comment; a bare first line
    # that is not a column header means the file uses the fixed-width layout.
    for index, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue
        candidate = stripped[1:].strip() if stripped.startswith("#") else stripped
        columns = [item.strip().lower() for item in candidate.split("\t")]
        if "id" in columns and _TSV_ZTF_COLUMNS.intersection(columns):
            header_index = index
            id_index = columns.index("id")
            parser_mode = "tsv"
            break
        if not stripped.startswith("#"):
            break

    if header_index is not None and id_index is not None:
        metadata_line_count = header_index + 1
        for offset, line in enumerate(
            lines[header_index + 1 :], start=header_index + 2
        ):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                metadata_line_count += 1
                continue
            columns = [item.strip() for item in line.split("\t")]
            if id_index >= len(columns):
                raise ValueError(
                    f"{path}:{offset}: data row exposes {len(columns)} tab-separated "
                    f"column(s); ID column {id_index} is missing"
                )
            rows.append(_parse_id(columns[id_index], path, offset))
    else:
        seen_data = False
        for line_number, line in enumerate(lines, start=1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                metadata_line_count += 1
                continue
            if set(stripped) <= _SEPARATOR_CHARS:
                metadata_line_count += 1
                continue
            if not seen_data and (
                _is_fixed_width_column_header(stripped)
                or _is_fixed_width_preamble(line)
            ):
                metadata_line_count += 1
                continue
            rows.append(_parse_id(line[_FIXED_WIDTH_ID_SLICE], path, line_number))
            seen_data = True

    return _build_result(
        rows,
        parser_mode,
        _file_sha256(path),
        metadata_line_count,
        include_full_multiplicities,
    )


def _report_block(result: dict) -> dict:
    """Project a parse result onto the report fields (drops the raw row list)."""
    block = {
        "source_sha256": result["source_sha256"],
        "parser_mode": result["parser_mode"],
        "metadata_line_count": result["metadata_line_count"],
        "row_count": result["row_count"],
        "unique_count": result["unique_count"],
        "duplicate_row_count": result["duplicate_row_count"],
        "duplicate_ids": result["duplicate_ids"],
        "duplicate_id_counts": result["duplicate_id_counts"],
        "multiplicity_histogram": result["multiplicity_histogram"],
        "max_multiplicity": result["max_multiplicity"],
        "ordered_rows_sha256": result["ordered_rows_sha256"],
        "unique_ids_sha256": result["unique_ids_sha256"],
        "row_multiset_sha256": result["row_multiset_sha256"],
        "all_id_multiplicities_included": result["all_id_multiplicities_included"],
    }
    if result["all_id_multiplicities_included"]:
        block["all_id_multiplicities"] = result["all_id_multiplicities"]
    return block


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--published", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--include-full-multiplicities",
        action="store_true",
        help=(
            "emit every (ID, occurrence_count) pair instead of only the IDs "
            "that occur more than once; exhaustive but large for 730k-row tables"
        ),
    )
    args = parser.parse_args()

    try:
        candidate = read_selected(
            args.candidate,
            include_full_multiplicities=args.include_full_multiplicities,
        )
        published = read_vizier(
            args.published,
            include_full_multiplicities=args.include_full_multiplicities,
        )
    except (OSError, ValueError) as exc:
        # Fail closed: never write a report from partially parsed input.
        print(f"audit_cpvs_membership: input error: {exc}", file=sys.stderr)
        return 3

    candidate_counts = Counter(candidate["rows"])
    published_counts = Counter(published["rows"])

    unique_membership_equal = candidate["unique"] == published["unique"]
    # Authoritative exact-multiset check: every ID occurs equally often.
    row_multiset_equal = candidate_counts == published_counts
    # Canonical cross-check; a deterministic function of the counts, so a
    # disagreement with the check above would signal an internal defect.
    row_multiset_digest_equal = (
        candidate["row_multiset_sha256"] == published["row_multiset_sha256"]
    )

    candidate_only = candidate["unique"] - published["unique"]
    published_only = published["unique"] - candidate["unique"]

    differing_ids = sorted(
        oid
        for oid in candidate_counts.keys() | published_counts.keys()
        if candidate_counts.get(oid, 0) != published_counts.get(oid, 0)
    )

    exact_match = (
        unique_membership_equal and row_multiset_equal and row_multiset_digest_equal
    )

    report = {
        "candidate": _report_block(candidate),
        "published": _report_block(published),
        "comparison": {
            "candidate_count": candidate["unique_count"],
            "published_count": published["unique_count"],
            "intersection_count": len(candidate["unique"] & published["unique"]),
            "candidate_only_count": len(candidate_only),
            "published_only_count": len(published_only),
            "candidate_only_sample": sorted(candidate_only)[:25],
            "published_only_sample": sorted(published_only)[:25],
            "unique_membership_equal": unique_membership_equal,
            "row_multiset_equal": row_multiset_equal,
            "row_multiset_digest_equal": row_multiset_digest_equal,
            "multiplicity_difference_count": len(differing_ids),
            "multiplicity_difference_sample": [
                {
                    "id": oid,
                    "candidate": candidate_counts.get(oid, 0),
                    "published": published_counts.get(oid, 0),
                }
                for oid in differing_ids[:25]
            ],
            "exact_match": exact_match,
        },
        # Top-level alias consumed by .github/workflows/scientific-validation.yml.
        # It is exact only when unique membership AND the exact row multiset
        # both hold, so the heavy workflow can never classify a multiplicity
        # mismatch as a reproduction.
        "exact_membership_match": exact_match,
        "published_source": "VizieR J/ApJ/932/118 table4.dat",
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        dumps_strict(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(dumps_strict(report, indent=2, sort_keys=True))

    # Exit 0 only if unique membership AND exact row multiset both match.
    if exact_match:
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
