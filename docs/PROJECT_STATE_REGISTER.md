# Current Project State Register

**As of:** 2026-10-23 UTC  
**Authoritative code branch:** `main`  
**Main HEAD verified:** `d88e54a2eb70d5e4531bc950341ef3136c29a5e2` (commit dated 2026-10-21)  
**Current published software release observed:** `v1.0.1`  
**Frozen scientific baseline:** `v0.2.0`  
**Status language:** current evidence only; open PRs are not shipped features.

## Verified repository facts

- Repository is public, default branch `main`, and the connected account has admin/push permission.
- GitHub release `v1.0.1` exists and is immutable; wheel and source archive assets are attached.
- PR #187 (documentation ecosystem alignment) is still open and unmerged as of this check.
- PR #212 (explicit multi-survey light-curve normalization contract and documentation control plane) is open, draft and unmerged, based on main. Read the live PR for the current head SHA; any SHA copied into a mirror is a dated snapshot.
- PR #212 now proposes the normalization module/tests/roadmap track plus canonical product charter, current handbook, state register, glossary, documentation index, and README links. These changes are not merged. This is not evidence of real external survey adapter execution or scientific cross-survey model compatibility.
- Repository metadata says Wiki is enabled; Pages are disabled (`has_pages=false`). Wiki write access has not been verified by this connection.
- The connected Supabase account currently lists projects `company-platform-pilot` and `company-website`; neither is identified as a ZTF Classifier backend. No ZTF-specific Supabase schema/project has been verified. Do not modify either company database as part of this project.
- The Notion Knowledge Base previously recorded HEAD `9ab910ddd04d2352e81f7c02c5715bcddf5944c6`, while main is `d88e54a2...`; a new dated Notion update now records this drift. The attached repository ZIP itself remains stale. The GitHub Snapshot Archive explicitly says its attached ZIP is old and should not be represented as a current backup.
- Notion’s latest discovered Handbook v2.9 is dated 2026-10-16 and references PR #187; it predates the current multi-survey PR and requires an evidence-based update.

## Product scope

The product is an Astronomical Data Analysis & Discovery Platform. ZTF is the first established domain, not the universal input requirement. User-supplied and cross-survey data ingestion is a core product requirement, but generic import does not authorize inference from the frozen ZTF model. The current open PR #212 is a proposal for a canonical normalization boundary, not a completed multi-survey product.

## Frozen baseline and scientific claims

Recorded baseline to verify against artifacts when used in scientific reporting:
- 150 benchmark objects, 15 ALeRCE reference classes, 10 objects/class.
- 42 features in `final_feature_set_v0.2`.
- XGBoost artifact `model_baseline_v0.2_production/artifact`.
- Historical cutoff `59447.224132`, schema 1.1 diagnostics, fail-closed scientific gate.
- ALeRCE labels are reference/benchmark labels, not independent ground truth.

CPVS latest recorded Seq-based comparison remains unresolved: parent 781,602; published membership 730,184; candidates 741,786; candidate-only 11,602; published-only 0. These are historical recorded values until freshly verified against current artifacts. The discrepancy must not block independent product-platform work and must not be “fixed” by tuning rules to force equality.

## Current open blockers

1. **Documentation drift:** handbook snapshots, README/roadmap, Notion KB/index and backup archive do not all point to the same revision.
2. **General input platform:** no verified evidence yet that multiple independent public survey sources have end-to-end adapters and source-backed test fixtures.
3. **PR #212:** draft and unmerged; its current CI status and tests must be inspected at the exact head before calling it validated.
4. **CPVS:** scientific membership reconstruction remains unresolved.
5. **Wiki:** enabled in repository metadata, but whether it can be edited with available connection is unverified.
6. **Pages:** repository metadata reports Pages disabled; no published Pages site is established.
7. **Supabase:** no ZTF-specific project/database verified in the connected account; do not assume a backend exists.

## Documentation update protocol

For every change:
1. Verify main HEAD, open PRs, release and relevant workflow checks.
2. Update the canonical charter/state register/roadmap and affected detailed guide together.
3. Preserve historical versioned handbooks; create a new current snapshot instead of rewriting history.
4. Update Notion mirrors only after source revision is known; include the exact commit and open PR links.
5. Verify edits by fetching the saved files/pages again.
6. Report only completed writes and verified results. Record anything blocked by connector permissions separately.

## Documentation work completed on the current PR branch

The following were added or aligned on this branch: project charter/source-of-truth policy; current handbook; project state register; glossary/status vocabulary; documentation index; README; platform roadmap; user guide; installation guide (v1.0.1); troubleshooting status/version; product architecture index; scientific validation source-adapter boundary; ecosystem expansion record. These are still proposed until PR #212 merges. No historical handbook snapshot or immutable release artifact was rewritten.

## Immediate work sequence

- [x] Add canonical project charter, state register, current handbook, glossary and documentation index on the documentation branch; preserve historical handbook snapshots.
- [x] Update README and roadmap to point to governing documents and distinguish product scope from shipped capabilities.
- [x] Create a current Notion handbook snapshot and update the Knowledge Base, documentation index, README mirror, ecosystem action plan, and archive-validity notice.
- [ ] Inspect PR #212 checks, fix concrete failures, add a pinned external-source fixture and run actual bounded ingestion tests before claiming cross-survey support.
- [ ] Update Notion Knowledge Base, Handbook, Documentation Index and Snapshot Archive with the correct current main SHA and pending PR status; do not fabricate a fresh ZIP attachment.
- [ ] Verify Wiki edit capability; if unavailable, record it as blocked and provide the canonical documentation link instead.
- [ ] Keep Pages disabled unless the user authorizes/needs a deployment and its security/maintenance implications are assessed.
- [ ] Verify whether any ZTF-specific Supabase project exists before adding database documentation or schema changes.
