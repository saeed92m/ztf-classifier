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
- `requirements.lock`, `pyproject.toml`, `.github/release-manifest.json` and the
  release workflow were left untouched. Regenerating a lockfile or changing a
  licence is a separate, reviewable decision; the defects are documented instead.
- No Supabase project, schema or migration was created. The account's two
  projects belong to other products; issue #183 already records evaluation-only.
- Branch deletion and PR closure were **not** performed — destructive and
  irreversible, requiring maintainer approval.


## [1.0.1] — 2026-10-07

### Fixed
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
