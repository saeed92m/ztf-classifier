# Documentation Index and Ownership

**Reviewed:** 2026-10-23 UTC  
**Repository source of truth:** GitHub main and immutable tagged releases.  
**Current proposed documentation alignment:** [PR #212](https://github.com/saeed92m/ztf-classifier/pull/212) (open/draft/unmerged at time of writing).

## Canonical current documents

| Document | Purpose | Rule |
|---|---|---|
| [Project charter and source-of-truth policy](PROJECT_CHARTER_AND_SOURCE_OF_TRUTH.md) | Product identity, vision, principles, architecture boundaries, documentation governance | Governs product intent and acceptance language once merged |
| [Current handbook](HANDBOOK_CURRENT.md) | Operational workflow, data contract, scientific boundaries, release rules | Current human-facing guidance; preserve old snapshots |
| [Project state register](PROJECT_STATE_REGISTER.md) | Verified release/PR/surface status, blockers and next actions | Update when verified status changes |
| [Project glossary](PROJECT_GLOSSARY.md) | Normative terminology and state definitions | Use terms consistently across UI, API and docs |
| [Platform expansion roadmap](roadmap/PLATFORM_EXPANSION_ROADMAP.md) | Tracks, gates, milestones and dependencies | No completion without evidence |
| [README](../README.md) | Repository entry point and high-level product overview | Link to canonical documents; avoid duplicating transient status |
| [Scientific validation benchmark](SCIENTIFIC_VALIDATION_BENCHMARK.md) | Frozen benchmark and validation contract | Scientific claims must follow its declared gates |
| [Scientific validation source adapters](SCIENTIFIC_VALIDATION_SOURCE_ADAPTERS.md) | Source-backed validation integrations | Do not claim an adapter ran unless evidence exists |
| [Feature provenance contract](FEATURE_PROVENANCE_CONTRACT.md) | Feature lineage and reproducibility | Required for scientific feature outputs |
| [Model card](MODEL_CARD.md) | Model intended use, limitations and evaluation | Do not generalize beyond validated domain |
| [Data card](DATA_CARD.md) | Dataset lineage, scope and limitations | Pin source version and hashes |
| [Production acceptance checklist](PRODUCTION_ACCEPTANCE_CHECKLIST.md) | Release gates | Fail-closed |

## Architecture and developer references

- `docs/architecture/APPLICATION_CORE_BOUNDARY.md` — application/scientific-core separation.
- `docs/architecture/ARCHITECTURE_v0.3.md` — architecture snapshot.
- `docs/architecture/CUMULATIVE_LEARNING_ARCHITECTURE.md` — how lessons and lifecycle records feed back into development.
- `docs/SCIENTIFIC_METHODOLOGY.md` and `docs/SCIENTIFIC_FEATURE_ENGINE_v0.1.md` — methodology and feature engine.
- `docs/SCIENTIFIC_FEATURE_ENGINE_CUMULATIVE_POLICY.md`, `docs/TESTING_STRATEGY_CUMULATIVE_LEARNING.md`, `docs/RELEASE_CUMULATIVE_IMPROVEMENT_POLICY.md` — cumulative quality policies.
- `docs/INSTALLATION.md`, `docs/QUICK_START.md`, `docs/USER_GUIDE.md`, `docs/TROUBLESHOOTING.md` — user setup and support.
- `docs/api/`, `docs/integrations/`, `docs/ui/`, `docs/knowledge/` — focused contracts and implementation notes.
- `CHANGELOG.md` and `.github/release-notes/<tag>.md` — version history and release notes.

## Historical snapshots

Files named `HANDBOOK_UPDATED_v*.md` are historical continuity snapshots. Preserve them for traceability. Do not overwrite them to represent today's state; update `HANDBOOK_CURRENT.md` and append a new dated snapshot when useful. Notion Handbook v2.9 (2026-10-16) is historical; the current Notion snapshot is v3.0 (2026-10-23).

## External mirrors and publication surfaces

- **Notion:** navigation and human-readable mirror; record exact Git SHA/PR and last-verified date. Never claim a page mirrors current main when its SHA is stale.
- **GitHub Wiki:** repository metadata says enabled, but the connected integration did not expose a writable `saeed92m/ztf-classifier.wiki` repository (404). Wiki changes are therefore blocked through the current connection; use links to canonical docs until write access is verified.
- **GitHub Pages:** repository metadata reports `has_pages=false`; no published Pages site is established.
- **Supabase:** connected projects are `company-platform-pilot` and `company-website`, neither verified as a ZTF Classifier backend. Do not change either database for this project.
- **GitHub snapshot ZIP in Notion:** marked stale, last recorded HEAD `9ab910ddd04d2352e81f7c02c5715bcddf5944c6`. Refresh only after canonical docs merge; record SHA-256 and verify the saved attachment.

## Synchronization protocol

1. Inspect the exact GitHub main SHA, release, PR and workflow status.
2. Update charter/state/roadmap and any affected detailed contract in one reviewable PR.
3. Verify edits by fetching files from the PR head.
4. Inspect tests and workflow jobs at the exact commit; distinguish success, failure, skipped and in-progress.
5. After merge, refresh the current handbook and Notion mirror with the new main SHA.
6. Create/attach a full repository snapshot only after generating it from that exact SHA and verifying checksum/readback.
7. Update Wiki/Pages/connected database only after destination identity and write access are verified.
8. Report completed writes and unresolved destinations separately.

## Status snapshot at review time

Main HEAD `d88e54a2eb70d5e4531bc950341ef3136c29a5e2`; published release v1.0.1; frozen baseline v0.2.0. PR #212 is open/draft/unmerged and its CI was in progress at last check. CPVS exact reconstruction remains unresolved. No cross-survey scientific validation claim is made.
