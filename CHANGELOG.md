# Changelog

All notable changes to the ZTF Classifier platform are documented here.

## [Unreleased]

### Added
- **Cross-platform CI matrix** (`Cross-platform (ubuntu-latest | macos-latest | windows-latest)`).
  Installs from `pyproject.toml` — the portable path — and runs the full test
  suite plus the CLI smoke test on each OS. Wired into the `CI Gate`, so a
  platform regression fails CI instead of going unnoticed. Previously every one
  of the eight CI jobs ran on `ubuntu-latest` only.
- `docs/README.md` — documentation authority map. Declares the single canonical
  document per topic, the supersession chain of the handbook and roadmap series,
  per-OS support status, and the status of external systems.
- `docs/contracts/PLATFORM_INTEGRATION_BOUNDARY_V1.md` — versioned, one-directional
  integration contract between ZTF Classifier (provider) and Company-Platform
  (optional consumer). Records that no runtime dependency exists today.
- `docs/PRODUCT_ALIGNMENT_2026-10-24.md` — point-in-time alignment audit with
  per-subsystem progress against measurable criteria.
- `docs/REPOSITORY_HYGIENE_POLICY.md` — branch classes, lifetimes, and a
  proposed batched cleanup for the 216 remote branches / 27 open PRs.
- `tests/test_documentation_authority.py` — 12 tests that make the authority map
  enforceable: unlisted documents, missing canonical targets, growth of the frozen
  handbook series, known version drift, and re-appearance of archived artefacts.
- `tests/test_dependency_declarations.py` — 4 tests guarding the declarations the
  test suite depends on: the lockfile must cover every declared runtime
  dependency, the `dev` extra must declare an HTTP client, `fastapi.testclient`
  must import in the running environment, and every package that provenance
  records must be a declared runtime dependency.
- `tests/test_platform_portability.py` — 2 tests plus a parametrized sanity check
  guarding imports: no module in `src/` may import a POSIX-only standard-library
  module at module scope, and `ztf_classifier.validation.runner` must import with
  `resource` unavailable, which is how it behaves on Windows.

### Changed
- `docs/INSTALLATION.md` rewritten. It previously instructed
  `pip install ztf-classifier==1.0.0`, which cannot work: the package is not
  published on PyPI (verified: HTTP 404). It now documents installation from the
  GitHub Release wheel, with per-platform activation commands, and states that
  `requirements.lock` is a Linux/x86-64-only freeze.
- `README.md` roadmap section: the handbook link no longer calls the 87-line
  `HANDBOOK_UPDATED_v2.8.md` a "canonical continuity handbook". It now points at
  `docs/README.md` as the authority and describes the handbook series as frozen
  history.
- `pyproject.toml`: `httpx` added to the `dev` extra. `tests/test_api.py`,
  `tests/test_reporting.py` and `tests/test_web_workbench.py` build
  `fastapi.testclient.TestClient`, whose import requires an HTTP client.
  `httpx` was in `requirements.lock`, so every lock-based job was green, but it
  was missing from the package metadata, so the documented portable install path
  (`pip install -e .[dev]`) failed to collect three test modules with exit code
  2. Test-only: no module under `src/` imports `httpx`.
- `tests/test_model_provenance.py`: third-party version assertions now compare
  against `importlib.metadata.version(...)` instead of hardcoded patch versions.
  The literals only reproduced under `requirements.lock`; under a portable
  install pandas resolves to a newer patch and the test failed for a reason
  unrelated to the code under test. Coverage is unchanged (the same six
  packages) and the project's own version is still asserted literally as a
  release guard.
- CI: the `Cross-platform` job requests `python-version: "3.11"` rather than
  `"3.11.16"`. The runner manifests do not publish every 3.11.x patch for every
  OS/architecture, so `setup-python` failed on macOS arm64 and on Windows before
  any test ran. The minor-version request resolves per platform and matches the
  declared floor `requires-python = ">=3.11,<3.12"`.

### Moved
- Four unreferenced files were moved out of the repository root into
  `docs/archive/` with `git mv` (history preserved, reversible):
  `P0_FIXES.patch`, `ZTF_CLASSIFIER_COMPLETE_UPGRADE_PATCH.md`,
  `FINAL_SESSION_SUMMARY.md`, and the 3.1 MB
  `01_environment_and_first_ztf_lightcurve.ipynb`. Each had zero inbound
  references across the whole repository.

### Not changed, deliberately
- No release, tag, merge or scientific baseline change. `v1.0.1` remains the
  current immutable release and `v0.2.0` the frozen scientific baseline.
- `requirements.lock`, `.github/release-manifest.json`, the licence declaration
  (`license = {text = "Proprietary"}`, no `LICENSE` file) and the release
  workflow were left untouched. Regenerating a lockfile, choosing a licence or
  changing the release path are separate, reviewable decisions; the defects are
  documented instead.
- No Supabase project, schema or migration was created. The account's two
  projects belong to other products; issue #183 already records evaluation-only.
- Branch deletion and PR closure were **not** performed — destructive and
  irreversible, requiring maintainer approval.


## [1.0.1] — 2026-10-07

### Fixed
- **`ztf_classifier.validation.runner` was unimportable on Windows.**
  It imported `resource`, a Unix-only standard-library module, at module scope,
  so the declared Windows support was false for any code path touching the
  validation runner. Peak memory is now obtained through a small portable
  helper: `resource.getrusage` on Linux/macOS, and `GetProcessMemoryInfo`
  (psapi, via `ctypes`) on Windows. Both report the same OS-level quantity, so
  the `peak_rss_mb` figure in validation output keeps the same meaning, and it
  stays 0.0 rather than fabricated if the OS call fails.
- CI: the `Cross-platform` job's test step now re-emits pytest failures as
  GitHub annotations. Without it a failing matrix job could only be diagnosed
  through the runner's log storage, which is not always reachable from the
  tooling that needs to read it.
- Made the FastAPI and Uvicorn runtime dependencies part of the standard package installation because `ztf-classifier-api` is a published production entrypoint.
- Kept optional `web` dependencies limited to presentation-only packages (`plotly` and `streamlit`).
- Preserved the v0.2 scientific baseline and `baseline_v0.2` model identity; this is a packaging/productization patch, not a scientific-model change.

### Verification
- Existing API test coverage exercises health/readiness, OpenAPI, prediction, authentication, durable jobs/results, catalog export, feature backends, and fail-closed scientific validation.
- Release v1.0.1 requires the same CI, CodeQL, scientific-validation, and curated-release-note gates.

## [1.0.0] — 2026-10-06

### Release identity
- Software release: `v1.0.0`
- Scientific baseline: immutable `v0.2.0`
- Production model identity: `baseline_v0.2`

### Highlights
- Promoted the repository to the Astronomical Data Analysis & Discovery Platform product identity.
- Added production inference, diagnostics, provenance, API/workbench foundations, durable analysis jobs and scientific result persistence.
- Added canonical installation, quick-start, user, scientific-methodology, troubleshooting, model-card and architecture documentation.
- Release automation now validates source-backed scientific evidence and requires curated release notes.

### Scientific validation
- Source-backed DR24/ALeRCE evidence and immutable historical reference checks pass the scientific gate.
- CPVS historical reconstruction boundary remains explicitly documented and claim-specific.

### Scope
- v1.0.0 is a production software release; it does not change the immutable v0.2 scientific benchmark or baseline model identity.
