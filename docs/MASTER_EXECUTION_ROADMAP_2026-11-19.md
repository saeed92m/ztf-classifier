# ZTF Classifier — Master Execution Roadmap

**Status date:** 2026-11-19

**Repository:** `saeed92m/ztf-classifier`

**Primary delivery:** Tabriz Science & Technology Park

**Frozen baseline:** v0.2.0 / 42 features / `baseline_v0.2`

> **Historical-status note (reviewed 2026-11-22):** This roadmap is a 2026-11-19 plan snapshot, not a claim that its phases have passed. PR #297 source is `5e9fbe02a954eadb2c8503890f77950ce7296ea7`; combined integration HEAD is `3e0159aafa53313c47052b7adbae1ac55514293c`. PR CI evidence is not local validation of the combined HEAD. The local Workbench/browser run remains unverified due to sandbox loopback permissions.

## Mission

Deliver one reliable, reproducible Astronomical Data Analysis & Discovery Platform. Use one repository and one product architecture. The Park demonstrator is an early milestone, not a second product or a fork.

## Phase 0 — Repository and evidence convergence

**Priority:** P0 — IN PROGRESS

1. Inventory all open PRs, issues, branches, workflows, releases, and local changes.
2. Identify PR dependency chains and duplicate work.
3. Preserve the local WSL staged patch, untracked files, and repository bundle before synchronization.
4. Integrate security fixes and validated work first.
5. Consolidate duplicate documentation and close only PRs whose full content has been preserved or superseded.
6. Keep unresolved research and future product work open with explicit exit criteria.

**Exit:** all local work is backed up and reconciled; PRs are merged, closed with content preserved, or retained with a reason; main README, handbook, roadmap, and defect register agree.

## Phase 1 — Park laboratory demonstrator

**Priority:** P0 — NOT YET ACCEPTED

Scope: bounded DR24 HATS raw-data retrieval, light-curve display, diagnostic QC, provenance, raw JSON export, and a repeatable operator procedure.

1. Run the pinned two-OID live source-parity test.
2. Run the Workbench procedure on the actual presentation machine.
3. Verify separate OID panels, filters, epochs, QC, provenance, and export.
4. Retain commit SHA, environment, logs, screenshot, JSON, and SHA-256.
5. Revise the Park slides. Do not claim DR24 classification, calibrated probabilities, physical-source identity, production QC, or scientific anomaly discovery.

**Exit:** live test PASS; local Workbench PASS; export hashes retained; a non-developer can repeat the procedure; limitations are visible. Then mark READY WITH LIMITATIONS.

## Phase 2 — Park Pilot dataset and identity

**Priority:** P0 — PLANNED / BLOCKED BY IDENTITY AND DATASET CONTRACT

1. Pin source releases, queries, licenses, schemas, and retrieval timestamps.
2. Define the complete eligible cohort before evaluation.
3. Use DR24 HATS as the primary observation stream.
4. Keep ALeRCE labels separate as weak/reference labels.
5. Keep any future labeled evaluation under a separately approved scientific plan; it is not part of this DR24 raw-data demonstrator.
6. Implement the minimum AOIC association ledger.
7. Preserve CONFIRMED, AMBIGUOUS, UNMATCHED, PROVISIONAL, and DISPUTED states.
8. Preserve every missing, empty, partial, and rejected record in the manifest.
9. Hash each raw payload and dataset artifact.

**Exit:** immutable cohort manifest, complete provenance and license record, association evidence, per-class/per-filter coverage, and no silent fallback.

## Phase 3 — DR24 application integration and scientific processing

**Priority:** P0 — PARTIAL

1. Add explicit DR24 source selection behind the normal observation-service boundary.
2. Keep ALeRCE separately selectable.
3. Do not silently substitute one source for another.
4. Preserve native HMJD, mag, magerr, clrcoeff, catflags, OID, filter, field, and RCID.
5. Define source-specific time and photometry contracts.
6. Approve versioned QC rules only after scientific review.
7. Test missing rows, duplicates, malformed schemas, filters, time handling, and failure modes.
8. Generate features only through a source-specific, tested mapping.
9. Preserve the frozen v0.2.0 feature contract.

**Exit:** end-to-end DR24 API and Workbench path, source provenance in every result, deterministic feature generation, and no unsupported feature-parity claim.

## Phase 4 — Model recovery or separately versioned Park model

**Priority:** P0 — BLOCKED

**Path A — recover original model**

- Recover the original v0.2.0 artifact.
- Verify its original manifest and independently trusted hashes.
- Verify model version, schema, 42-feature order, class order, dataset, and provenance.
- Run production inference tests.

**Path B — new Park model**

- Create a new model version.
- Use a pinned dataset and separate label contract.
- Use object-level and temporal leakage-safe splits.
- Keep training, calibration, and test partitions separate.
- Report per-class metrics, calibration, abstention, and coverage where sample size supports them.
- Do not overwrite or relabel the frozen baseline.

**Exit:** authenticated original artifact OR independently validated new model, with a versioned model card and dataset manifest.

## Phase 5 — Scientific Workbench and user workflow

**Priority:** P1 — PARTIAL

Build dataset manager, source selector, Object/Source Explorer, filter-aware light-curve viewer, identity/QC panel, feature diagnostics, model/uncertainty panel, results catalog, provenance views, human review, Help, troubleshooting, and reports.

**Exit:** normal user path from data selection to report export; repeated runs are reproducible; unsupported states are visible.

## Phase 6 — Cross-platform product beta

**Priority:** P1 — NOT STARTED AS A RELEASE GATE

Build Windows, macOS, and Linux packages. Verify clean install, update, rollback, uninstall, CPU/memory performance, offline behavior, backup, restore, API security, dependency audit, and software bill of materials.

**Exit:** clean-machine tests pass on supported operating systems; normal users do not need Python, pip, Git, or a terminal.

## Phase 7 — Stable scientific discovery platform

**Priority:** P2 — FUTURE

Add independent multi-survey adapters, cross-match, catalog context, similar-object search, scientific anomaly analysis, drift monitoring, human annotation, explainability, batch/streaming ingestion, ZTF alert/AVRO, Rubin/LSST readiness, and controlled CIN participation.

Every capability needs a versioned contract, source/license provenance, validation evidence, failure handling, UI representation, and regression tests.

## Park data-source boundary

- DR24 HATS is the raw observation source for this Park demonstrator.
- ALeRCE remains a separate reference-label and observation service; it is not a fallback for DR24 and its labels are not independent astrophysical truth.
- Supplementary photometry products are outside this DR24-only demonstrator workflow and must not be combined with DR24 records.
- The broader product roadmap and other research tracks are outside this Park execution plan.

## Priority order

1. Preserve local work and converge the repository.
2. Pass the bounded raw DR24 laboratory demonstration.
3. Correct the Park presentation and submit with explicit limitations.
4. Freeze the full Park cohort and identity ledger.
5. Integrate DR24 through the normal application service.
6. Recover the original model or validate a new model separately.
7. Complete future full-cohort API/Workbench execution and any independent evaluation only under a separately approved scientific plan.
8. Complete deployment, backup/restore, licensing, and release gates before distribution.
9. Continue the broader product roadmap separately from Park acceptance.

## Definition of done

A phase is complete only when all exit criteria pass and evidence is retained. A green CI run or a small sample does not establish scientific or product acceptance.
