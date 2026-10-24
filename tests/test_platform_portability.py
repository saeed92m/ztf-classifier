"""Guards the declared cross-platform support at the level of imports.

The product claims Windows, macOS and Ubuntu support. Imports are the cheapest
place for that claim to become false, and the most expensive place to discover it
late: a single top-level ``import resource`` in
``ztf_classifier.validation.runner`` made the module unimportable on Windows.

The rule enforced here is deliberately narrow: a POSIX-only standard-library
module may be imported, but not unconditionally at module scope. Guarding it
(inside ``try/except ImportError``) or deferring it into the function that needs
it is accepted. ``tests/test_dependency_declarations.py`` covers declarations;
this file covers imports.
"""

from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = PROJECT_ROOT / "src"

# Standard-library modules that exist only on POSIX systems.
POSIX_ONLY_MODULES = frozenset(
    {
        "fcntl",
        "grp",
        "pty",
        "pwd",
        "resource",
        "syslog",
        "termios",
        "tty",
    }
)


def python_files() -> list[Path]:
    return sorted(SOURCE_ROOT.rglob("*.py"))


def unconditional_top_level_imports(path: Path) -> list[tuple[int, str]]:
    """POSIX-only imports executed when the module is imported.

    Imports inside a function, a class body, an ``if``, or a ``try`` are not
    reported: those are the accepted ways to make a platform-specific import
    conditional or lazy.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    offenders: list[tuple[int, str]] = []
    for node in tree.body:
        names: list[str] = []
        if isinstance(node, ast.Import):
            names = [alias.name.split(".")[0] for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            names = [node.module.split(".")[0]]
        for name in names:
            if name in POSIX_ONLY_MODULES:
                offenders.append((node.lineno, name))
    return offenders


def test_no_unconditional_posix_only_import_in_package():
    offenders = {
        str(path.relative_to(PROJECT_ROOT)): unconditional_top_level_imports(path)
        for path in python_files()
    }
    offenders = {path: found for path, found in offenders.items() if found}
    assert offenders == {}, (
        "These modules import a POSIX-only standard-library module at module "
        f"scope and cannot be imported on Windows: {offenders}. Import it "
        "inside the function that needs it, or guard it with try/except "
        "ImportError."
    )


def test_validation_runner_imports_when_resource_is_unavailable():
    # `sys.modules["resource"] = None` makes `import resource` raise ImportError,
    # which is what Windows does. A subprocess keeps the simulation from leaking
    # into the rest of the session.
    script = (
        "import sys\n"
        "sys.modules['resource'] = None\n"
        "import ztf_classifier.validation.runner as runner\n"
        "assert callable(runner.run_table_benchmark)\n"
        "print('imported')\n"
    )
    completed = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
        check=False,
    )
    assert completed.returncode == 0, (
        "ztf_classifier.validation.runner must import without the Unix-only "
        f"`resource` module.\nstdout:\n{completed.stdout}\n"
        f"stderr:\n{completed.stderr}"
    )
    assert "imported" in completed.stdout


def test_failed_windows_memory_query_is_explicit_not_zero(monkeypatch):
    from ztf_classifier.validation import runner

    monkeypatch.setattr(runner.sys, "platform", "win32")
    monkeypatch.setattr(runner, "_windows_peak_rss_mb", lambda: None)

    assert runner._peak_rss_mb() is None


def test_peak_rss_is_reported_as_a_positive_number():
    from ztf_classifier.validation.runner import _peak_rss_mb

    # The metric feeds validation output, so a zero would silently corrupt a
    # reported figure rather than fail loudly.
    assert _peak_rss_mb() > 0.0


@pytest.mark.parametrize("module", sorted(POSIX_ONLY_MODULES))
def test_posix_only_module_list_is_actually_posix_only(module):
    # Sanity check on the rule itself: every module the guard forbids must be
    # absent on Windows, otherwise the guard would forbid portable code.
    if sys.platform != "win32":
        pytest.skip("the guarded modules are present on POSIX by definition")
    with pytest.raises(ImportError):
        __import__(module)
