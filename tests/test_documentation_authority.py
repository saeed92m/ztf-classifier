"""Enforce the documentation authority map in docs/README.md.

These tests exist because the repository accumulated 14 near-duplicate
"continuity handbook" files, three roadmap files whose internal version disagrees
with their filename, and four unreferenced artefacts in the repository root.
Documentation rot is silent; these checks make it fail loudly.

The authority map is documentation, so it is enforced by test rather than by
convention.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]
_DOCS = _REPO_ROOT / "docs"
_INDEX = _DOCS / "README.md"


def _index_text() -> str:
    return _INDEX.read_text(encoding="utf-8")


def _documented_paths() -> set[str]:
    """Relative paths under docs/ mentioned anywhere in the authority map."""
    text = _index_text()
    found: set[str] = set()
    # Markdown links and backticked paths, resolved relative to docs/.
    for match in re.finditer(r"\]\(([^)]+)\)", text):
        target = match.group(1).split("#", 1)[0].strip()
        if not target or target.startswith(("http://", "https://", "mailto:")):
            continue
        found.add(str((_DOCS / target).resolve()))
    for match in re.finditer(r"`([^`]+\.(?:md|json|py|ipynb|ya?ml))`", text):
        candidate = _DOCS / match.group(1)
        found.add(str(candidate.resolve()))
    return found


def test_documentation_index_exists():
    assert _INDEX.is_file(), "docs/README.md (documentation authority map) is missing"


def test_canonical_documents_exist():
    """Every file the authority map calls canonical must actually exist."""
    text = _index_text()
    canonical_rows = [
        line for line in text.splitlines() if line.startswith("|") and "|" in line[1:]
    ]
    referenced: list[str] = []
    for row in canonical_rows:
        for match in re.finditer(r"\]\(([^)#]+)", row):
            target = match.group(1).strip()
            if target.startswith(("http://", "https://", "mailto:")):
                continue
            referenced.append(target)

    assert referenced, "authority map declares no canonical documents"

    missing = []
    for target in referenced:
        resolved = (_DOCS / target).resolve()
        # Rows explicitly marked as declared-but-absent are allowed to be absent.
        if "declared gap" in text and "CPVS_SELECTION_RULE_EVIDENCE" in target:
            continue
        if not resolved.exists():
            missing.append(target)

    assert not missing, (
        f"authority map points at missing documents: {sorted(set(missing))}"
    )


def test_no_unlisted_documents_under_docs():
    """Any .md under docs/ must be reachable from the authority map.

    Archive contents and the index itself are exempt: the archive is declared
    as a directory, and the index cannot list itself meaningfully.
    """
    documented = _documented_paths()
    unlisted = []
    for path in _DOCS.rglob("*.md"):
        if path == _INDEX:
            continue
        if "archive" in path.parts:
            continue
        if str(path.resolve()) not in documented:
            unlisted.append(str(path.relative_to(_REPO_ROOT)))
    assert not unlisted, (
        "documents exist under docs/ but are not declared in docs/README.md: "
        f"{sorted(unlisted)}"
    )


def test_handbook_series_is_frozen():
    """New HANDBOOK_UPDATED_v* files must not be added.

    The series is historical. Continuity updates belong in docs/knowledge/ or a
    dated document. The highest existing version is pinned here on purpose: this
    assertion is meant to be updated only by an explicit decision.
    """
    handbooks = sorted(p.name for p in _DOCS.glob("HANDBOOK_UPDATED_v*.md"))
    assert len(handbooks) == 14, (
        "the historical handbook series changed size; if this is intentional, "
        f"record the decision in docs/knowledge/ARCHITECTURAL_DECISIONS.md. Found: {handbooks}"
    )
    assert "HANDBOOK_UPDATED_v2.8.md" in handbooks


@pytest.mark.parametrize(
    ("filename", "expected_internal_version"),
    [
        ("HANDBOOK_UPDATED_v1.3.md", "1.4"),
        ("HANDBOOK_UPDATED_v2.2.md", "2.3"),
        ("HANDBOOK_UPDATED_v2.4.md", "2.3"),
    ],
)
def test_known_handbook_version_drift_is_recorded(
    filename: str, expected_internal_version: str
):
    """Pin the known filename/version mismatches so they cannot silently spread.

    These are documented defects in docs/README.md §2. The test asserts the
    defect still exists exactly as recorded; if someone repairs the files, this
    test fails and the authority map must be updated in the same change.
    """
    path = _DOCS / filename
    assert path.is_file(), f"{filename} disappeared; update docs/README.md §2"
    title = path.read_text(encoding="utf-8").splitlines()[0]
    assert expected_internal_version in title


def test_repository_root_has_no_archived_artefacts():
    """The four archived orphans must not reappear in the repository root."""
    forbidden = [
        "P0_FIXES.patch",
        "ZTF_CLASSIFIER_COMPLETE_UPGRADE_PATCH.md",
        "FINAL_SESSION_SUMMARY.md",
        "01_environment_and_first_ztf_lightcurve.ipynb",
    ]
    present = [name for name in forbidden if (_REPO_ROOT / name).exists()]
    assert not present, f"archived artefacts returned to the repository root: {present}"


def test_archived_artefacts_are_preserved():
    """Archiving must move, never delete."""
    expected = [
        _DOCS / "archive" / "P0_FIXES.patch.md",
        _DOCS / "archive" / "ZTF_CLASSIFIER_COMPLETE_UPGRADE_PATCH.md",
        _DOCS / "archive" / "FINAL_SESSION_SUMMARY.md",
        _DOCS
        / "archive"
        / "notebooks"
        / "01_environment_and_first_ztf_lightcurve.ipynb",
    ]
    missing = [str(p.relative_to(_REPO_ROOT)) for p in expected if not p.exists()]
    assert not missing, f"archived artefacts were deleted instead of moved: {missing}"


def test_platform_support_is_declared_per_operating_system():
    """The cross-platform claim must be stated with an evidence source per OS."""
    text = _index_text()
    for os_name in ("Ubuntu", "macOS", "Windows"):
        assert os_name in text, (
            f"docs/README.md does not declare support status for {os_name}"
        )


def test_lockfile_platform_scope_is_documented():
    """requirements.lock is Linux-only; that must be stated where people look."""
    text = _index_text()
    assert "requirements.lock" in text
    assert "Linux" in text
    assert "nvidia-nccl-cu12" in text, (
        "docs/README.md must name the concrete Linux-only pins that make "
        "requirements.lock unusable on macOS/Windows"
    )


def test_external_system_non_dependency_is_recorded():
    """Supabase and Company-Platform must be described as non-dependencies."""
    text = _index_text()
    assert "Supabase" in text
    assert "Company-Platform" in text
    assert "Not used" in text or "not used" in text
