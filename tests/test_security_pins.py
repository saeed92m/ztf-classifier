"""Offline guards for the dependency pins that were raised for security reasons.

CI runs ``python -m pip_audit`` against the installed environment, and that is the
authoritative check. It needs network access to the advisory database, so it
cannot run in an offline checkout and it reports the *current* state only: it
cannot tell a deliberate remediation apart from a silent revert.

These tests close that gap. They assert that the pins which were raised to clear
known vulnerabilities have not gone back down. They read declarations rather than
an environment, so they give the same verdict everywhere and without network.

Context (2026-10-25): the ``Dependency Audit`` job failed on
``feature/cpvs-discrepancy-report-20261024`` at run 40178020768. Reproduced
locally, the old pins produced 4 advisories and exit code 1:

    filelock   4.0.3   CVE-2026-112940, CVE-2026-112913, CVE-2026-112907  -> 4.2.1
    setuptools 84.0.0  GHSA-xmj3-9gf7-h52w                                -> 84.1.0

Raising those two (and nothing else) gives "No known vulnerabilities found" and
exit code 0.

Keep this list minimal and justified. A floor is only recorded here once the
corresponding advisory was actually reproduced and the fix verified.
"""

from __future__ import annotations

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOCK_PATH = PROJECT_ROOT / "requirements.lock"
CI_PATH = PROJECT_ROOT / ".github" / "workflows" / "ci.yml"

#: Packages pinned in requirements.lock -> (minimum safe version, advisory).
LOCKED_FLOORS = {
    "filelock": ("4.2.1", "CVE-2026-112940 / CVE-2026-112913 / CVE-2026-112907"),
}

#: Packages the CI workflow installs by explicit pin -> (minimum safe version,
#: advisory). setuptools is deliberately absent from requirements.lock: it is a
#: build tool installed into the audited environment by the workflow, so its
#: floor belongs to the workflow, not to the runtime lock.
CI_PIN_FLOORS = {
    "setuptools": ("84.1.0", "GHSA-xmj3-9gf7-h52w"),
}


def parse_version(text: str) -> tuple[int, ...]:
    return tuple(int(part) for part in re.findall(r"\d+", text))


def locked_pins() -> dict[str, str]:
    pins: dict[str, str] = {}
    for line in LOCK_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "==" not in line:
            continue
        name, _, version = line.partition("==")
        pins[name.strip().lower()] = version.strip()
    return pins


def test_lockfile_pins_are_at_or_above_security_floors():
    pins = locked_pins()
    for package, (floor, advisory) in LOCKED_FLOORS.items():
        assert package in pins, (
            f"{package} is no longer pinned in requirements.lock; the floor "
            f"{floor} established by {advisory} is not enforced"
        )
        actual = pins[package]
        assert parse_version(actual) >= parse_version(floor), (
            f"requirements.lock pins {package}=={actual}, below the security "
            f"floor {floor} required by {advisory}. Restoring this pin "
            "reintroduces a known vulnerability."
        )


def test_ci_does_not_pin_a_vulnerable_setuptools():
    """The install steps upgrade setuptools to an explicit version.

    That version is installed into the audited environment, so a pin below the
    floor keeps the advisory alive even if the lockfile is correct.
    """
    floor, advisory = CI_PIN_FLOORS["setuptools"]
    workflow = CI_PATH.read_text(encoding="utf-8")
    pinned = set(re.findall(r"setuptools==([0-9][0-9.]*)", workflow))
    assert pinned, "no setuptools pin found in the CI workflow"
    for version in sorted(pinned):
        assert parse_version(version) >= parse_version(floor), (
            f"ci.yml installs setuptools=={version}, below the security floor "
            f"{floor} required by {advisory}"
        )


def test_every_ci_setuptools_pin_is_the_same_version():
    """Divergent pins mean one job installs a different setuptools than the rest."""
    workflow = CI_PATH.read_text(encoding="utf-8")
    pinned = set(re.findall(r"setuptools==([0-9][0-9.]*)", workflow))
    assert len(pinned) == 1, (
        f"ci.yml pins multiple setuptools versions: {sorted(pinned)}"
    )
