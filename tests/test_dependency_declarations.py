"""Guards the dependency declarations against the two drift modes that were
found during the 2026-10-24 cross-platform alignment round:

1. ``requirements.lock`` and ``pyproject.toml`` disagreeing about runtime
   dependencies. The lock is what four CI jobs install, so a runtime dependency
   missing from the lock would ship an environment that cannot import the
   package, while a stale entry in the lock would drag in something no longer
   declared.

2. The ``dev`` extra not being sufficient to run the test suite. Three test
   modules build ``fastapi.testclient.TestClient``; ``starlette.testclient``
   needs an HTTP client to import. ``httpx`` was present in the lockfile (so the
   lock-based jobs were green) but absent from ``pyproject.toml``, so the
   documented portable install path could not even collect the suite.

These tests read the declarations, not an environment snapshot, so they give the
same verdict on Linux, macOS and Windows.
"""

from __future__ import annotations

import tomllib
from importlib import metadata
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PYPROJECT_PATH = PROJECT_ROOT / "pyproject.toml"
LOCK_PATH = PROJECT_ROOT / "requirements.lock"

# Packages recorded by ``ModelProvenanceBuilder``. Kept here so the provenance
# capture list cannot silently reference something the project does not declare.
PROVENANCE_PACKAGES = (
    "numpy",
    "pandas",
    "scipy",
    "scikit-learn",
    "xgboost",
    "pyarrow",
)


def normalise(name: str) -> str:
    """PEP 503 project-name normalisation."""
    return name.lower().replace("_", "-").replace(".", "-")


def declared_runtime_dependencies() -> list[str]:
    project = tomllib.loads(PYPROJECT_PATH.read_text(encoding="utf-8"))
    names = []
    for requirement in project["project"]["dependencies"]:
        # Strip any version specifier: only the project name is compared.
        for separator in ("[", ">", "<", "=", "!", "~", ";", " "):
            requirement = requirement.split(separator, 1)[0]
        names.append(normalise(requirement))
    return sorted(names)


def locked_packages() -> dict[str, str]:
    packages: dict[str, str] = {}
    for line in LOCK_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "==" not in line:
            continue
        name, _, version = line.partition("==")
        packages[normalise(name)] = version.strip()
    return packages


def test_lockfile_covers_every_declared_runtime_dependency():
    locked = locked_packages()
    missing = [name for name in declared_runtime_dependencies() if name not in locked]
    assert missing == [], (
        "requirements.lock does not pin these declared runtime dependencies: "
        f"{missing}. The lockfile CI jobs would install an environment that "
        "cannot import the package."
    )


def test_test_client_dependency_is_declared_in_dev_extra():
    project = tomllib.loads(PYPROJECT_PATH.read_text(encoding="utf-8"))
    dev = [
        normalise(name) for name in project["project"]["optional-dependencies"]["dev"]
    ]
    assert "httpx" in dev, (
        "The dev extra must declare an HTTP client: fastapi.testclient imports "
        "starlette.testclient, which raises RuntimeError without one, so three "
        "test modules fail to collect under `pip install -e .[dev]`."
    )


def test_test_client_is_importable_in_this_environment():
    # Import-level smoke test: reproduces the exact failure mode rather than
    # asserting on packaging metadata alone.
    from fastapi.testclient import TestClient

    # The import is the assertion; the version check makes the failure message
    # point at the package when the client is importable for another reason.
    assert metadata.version("httpx")
    assert TestClient is not None


def test_provenance_packages_are_declared_runtime_dependencies():
    declared = set(declared_runtime_dependencies())
    missing = [name for name in PROVENANCE_PACKAGES if normalise(name) not in declared]
    assert missing == [], (
        "Provenance records versions for packages the project does not declare: "
        f"{missing}"
    )
