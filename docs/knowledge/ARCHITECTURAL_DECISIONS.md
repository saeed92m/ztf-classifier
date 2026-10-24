# Architectural Decisions Knowledge

| ID | Status | Decision | Evidence / rationale | Propagated to |
|---|---|---|---|---|
| AD-CI-001 | VERIFIED | Scientific validation is a permanent product-level gate. | Registry, executable gate, release fail-closed contract. | Release, roadmap, testing |
| AD-CI-002 | VERIFIED | Ground truth and independent reference agreement remain separate. | Manifest evaluation-role contract and regression tests. | Benchmarks, reports |
| AD-CI-003 | VERIFIED | External scientific datasets are not committed to Git. | Reproducibility and provenance contract. | Benchmark registry |
| AD-CI-004 | VERIFIED | Cumulative learning is a lifecycle control, not documentation-only. | Stage contract, ledger, knowledge layer, and executable validation. | All future stages |
| AD-CI-005 | VERIFIED | Local optimization cannot override scientific validity or release integrity. | Multi-objective quality vector and trade-off rules. | Model, feature, performance, release |
| AD-CI-006 | VERIFIED | Historical external-benchmark reconstruction is a claim-specific evidence scope and is not the product execution path. | CPVS 730k discrepancy analysis and PR #124 recovery architecture. | Scientific validation gate, roadmap, CI |


| AD-PROD-001 | ADOPTED | The product is a cross-platform Astronomical Data Analysis & Discovery Platform, not classifier-only. | Ecosystem review and existing platform architecture. | README, handbook, architecture, roadmap |
| AD-PROD-002 | ADOPTED | Desktop GUI is a product layer over stable scientific Core contracts; CLI/API remain supported. | Prevents GUI-driven scientific-core rewrites and preserves automation. | Architecture, packaging, UX |
| AD-PROD-003 | ADOPTED | Normal users must have self-contained installation on Windows/macOS/Linux without Python/pip/venv/Git/terminal. | User-path review and product usability requirement. | Packaging, release, installation |
| AD-PROD-004 | ADOPTED | Object/Source Explorer and provenance/evidence UI are first-class product capabilities. | Scientific discovery workflows require source-level inspection and reproducibility. | GUI, results, reports |
| AD-PROD-005 | ADOPTED | Cross-match, similar-object search, human review, discovery ranking, and Real/Bogus are explicit architectural boundaries. | Ecosystem review identified these as reusable patterns with clear scientific semantics. | Discovery architecture, analysis modes |
| AD-PROD-006 | ADOPTED | OOD, uncertainty, scientific anomaly, catalog evidence, and explainability remain separate evidence channels. | Prevents semantic overclaiming. | Result contracts, UI, validation |
| AD-PROD-007 | ADOPTED | Future alert/streaming support must be enabled by contracts without weakening deterministic offline/batch workflows. | Preserves reproducibility while allowing operational scaling. | Ingestion, orchestration |

## Decisions — product alignment round (2026-10-24)

Recorded during the alignment audit in `docs/PRODUCT_ALIGNMENT_2026-10-24.md`.
Each entry states the consequence so a later reader can see what it forces.

| ID | Status | Decision | Evidence / rationale | Consequence |
|---|---|---|---|---|
| AD-ALIGN-001 | ADOPTED | A cross-platform claim is only valid when a per-operating-system CI job exercises it. | Before this round all eight CI jobs ran on `ubuntu-latest` while `pyproject.toml` declared `Operating System :: POSIX :: Linux` only; no macOS or Windows job existed anywhere. | `ci.yml` gains a `cross-platform` matrix job wired into `CI Gate`. A platform that is not in the matrix is not a supported platform and must not be described as one. |
| AD-ALIGN-002 | ADOPTED | Documentation authority is encoded as a machine-checked map, not as convention. | 14 near-duplicate handbook files, 4 roadmap files, three filename/version mismatches, and a README that called an 87-line amendment the canonical handbook. | `docs/README.md` is the authority map; `tests/test_documentation_authority.py` fails when a document is unlisted, a canonical target is missing, the frozen handbook series grows, or a recorded defect changes silently. |
| AD-ALIGN-003 | ADOPTED | ZTF Classifier has no runtime dependency on Company-Platform or Supabase, and any future integration is one-directional and versioned. | Verified zero references to either system in code, configuration, workflows and documentation; Supabase account holds only projects belonging to other products. | `docs/contracts/PLATFORM_INTEGRATION_BOUNDARY_V1.md`. Company-Platform may call ZTF's `/v1` API; ZTF never calls out. A breaking change requires a new contract version and a decision record. |
| AD-ALIGN-004 | ADOPTED | `requirements.lock` is a Linux/x86-64 freeze, not a cross-platform lock. The portable installation path is `pyproject.toml`. | The lock pins `nvidia-nccl-cu12` (CUDA, Linux x86-64), `jeepney` and `SecretStorage` (Linux). `pip install -r requirements.lock` cannot succeed on macOS or Windows. | Documentation must not present the lock as cross-platform. Per-platform locks are required work before Windows/macOS can claim a hermetic install. |
| AD-ALIGN-005 | OPEN — BLOCKER | The packaging requirement in AD-PROD-003 (self-contained install with no Python, pip, venv, Git or terminal) is **not met**. | Releases attach only `ztf_classifier-1.0.1-py3-none-any.whl` and `ztf_classifier-1.0.1.tar.gz`. There is no installer, no bundled runtime, and the package is not on PyPI (verified HTTP 404). | Until an installer exists, the product is installable only by a user with a Python 3.11 toolchain. Describing it as an end-user desktop product would be an overclaim. Tracked as remaining work item 10 in `docs/PRODUCT_ALIGNMENT_2026-10-24.md`. |
| AD-ALIGN-006 | ADOPTED | Unreferenced artefacts are archived by `git mv`, never deleted. | Four root files had zero inbound references; they record provenance of past fixes. | `docs/archive/` preserves them with history; `tests/test_documentation_authority.py` asserts they are neither deleted nor returned to the root. |

### AD-ALIGN-007 — A green lockfile job is not evidence that the product installs

**Date:** 2026-10-24
**Status:** Accepted
**Consequences:** `pyproject.toml` must be sufficient to install and run the
product on every supported OS; `requirements.lock` is an additional, narrower
guarantee.

The first run of the new `Cross-platform` CI job failed on all three operating
systems. Neither cause was visible in any document or in the eight previously
existing jobs:

1. `httpx` was in `requirements.lock` but not in `pyproject.toml`. Every
   lock-based job was green, while `pip install -e .[dev]` — the documented
   portable path — could not collect three test modules (`TestClient` import).
2. A test asserted hardcoded third-party patch versions and therefore asserted
   the sandbox rather than the code under test.

**Decision.** A platform claim is only supported by a job that installs through
the path a user on that platform has. The four lock-based jobs keep their role
(the pinned scientific stack), and the matrix job installs from
`pyproject.toml`. When the two disagree, `pyproject.toml` is the product and the
lock is the reproducibility artefact; disagreement is a defect to fix, not a
reason to relax the assertion.

**Also decided.** Tests must not assert environment snapshots. Where a test
needs to verify that a value was captured, it compares against the live source
of that value (`importlib.metadata`), so the test keeps its meaning on every OS.
Guards against environment drift belong in the declaration files and in CI, not
in per-platform assertions.

### AD-ALIGN-008 — The project's own version is a literal; third-party versions are not

**Date:** 2026-10-24
**Status:** Accepted
**Consequences:** Bumping the release version requires updating
`tests/test_model_provenance.py`; that is intentional and is part of the release
checklist.

`assert provenance.dependencies["ztf-classifier"] == "1.0.1"` is a release
guard: it fails if the packaged metadata and the tagged release diverge, which is
a defect worth failing on. Third-party versions are compared with the installed
distribution metadata instead, because a literal there can only ever describe one
machine.

### AD-ALIGN-009 — A declared platform is a claim about imports, not about CI

**Date:** 2026-10-24
**Status:** Accepted
**Consequences:** `tests/test_platform_portability.py` fails the build if a
module-scope import of a POSIX-only standard-library module appears in `src/`.

`ztf_classifier.validation.runner` imported `resource` at module scope. Every
Linux job was green, the Linux install worked, and nothing in the documentation
was wrong: the code simply could not be imported on Windows. Declaring an
Operating System classifier does not test the declaration; running an import on
that platform does, and it is far cheaper than running a full suite there.

**Decision.** Platform-specific standard-library modules may be imported only
inside the function that needs them or behind `try/except ImportError`. Where a
platform needs a genuinely different implementation, implement it and document
why the two are comparable — for peak memory, `resource.getrusage` and
`GetProcessMemoryInfo` both report the process peak working set, so one metric
name is honest across platforms.

**Related:** AD-ALIGN-001 (claims require per-OS CI) and AD-ALIGN-007 (a green
lockfile job is not evidence that the product installs).

### AD-ALIGN-010 — Recorded values are platform-neutral; numerical identity is not claimed across platforms

**Date:** 2026-10-24
**Status:** Accepted
**Consequences:** any field written into provenance, manifests or contract
output must be produced with an explicit, platform-independent serialisation.

Two different questions were conflated by the previous code:

1. *Is the record the same shape and meaning on every OS?* This must be true, and
   it was not: `str(Path)` writes backslashes on Windows, so the same project
   produced two different provenance strings. Fixed with `as_posix()`, matching
   `reproducibility/manifest.py`.
2. *Do the numbers match bit-for-bit on every OS?* For XGBoost histogram
   training, this is not guaranteed. The frozen OOF artefact belongs to the
   environment recorded in `reproducibility_manifest_v0.2.json`.

**Decision.** Records are platform-neutral; scientific reproducibility claims are
scoped to the environment that produced the artefact. A test that compares
against a frozen artefact must state which environment that artefact belongs to
and gate the value-level comparison on it, while still asserting structure and
internal consistency everywhere. Skipping the comparison silently would be
dishonest; asserting it everywhere would be false.

**Related:** AD-PROD-003 (install without a Python toolchain — still open),
AD-ALIGN-009 (platform claims are claims about imports).
