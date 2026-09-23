"""Runtime, dependency, and source-control environment inspection."""

from __future__ import annotations

import importlib.metadata
import platform
import subprocess
import sys


def _run_git(project_root, *args: str) -> str:
    """Run a git command and return stripped stdout."""
    result = subprocess.run(
        ["git", *args],
        cwd=project_root,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def collect_git_state(project_root) -> dict[str, object]:
    """Collect reproducibility-relevant Git state."""
    try:
        commit = _run_git(project_root, "rev-parse", "HEAD")
        branch = _run_git(
            project_root,
            "rev-parse",
            "--abbrev-ref",
            "HEAD",
        )
        status = _run_git(project_root, "status", "--porcelain")
    except (OSError, subprocess.CalledProcessError) as exc:
        raise RuntimeError(
            f"Unable to inspect Git repository: {project_root}"
        ) from exc

    return {
        "git_commit": commit,
        "git_branch": branch,
        "git_dirty": bool(status),
    }


def collect_dependency_versions() -> dict[str, str]:
    """Return all installed Python distributions and their versions."""
    distributions = importlib.metadata.distributions()

    versions: dict[str, str] = {}

    for distribution in distributions:
        name = distribution.metadata.get("Name")
        if not name:
            continue

        normalized_name = name.lower().replace("_", "-")
        versions[normalized_name] = distribution.version

    return dict(sorted(versions.items()))


def collect_environment() -> dict[str, object]:
    """Collect portable runtime information."""
    return {
        "python": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "architecture": platform.machine(),
        "executable": sys.executable.split("/")[-1],
    }
