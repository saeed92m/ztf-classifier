# Think Tank Session — Park Readiness and Repository Convergence

**Date:** 2026-11-19

**Method:** structured review by the established 16 specialist seats. This is a simulated multidisciplinary review, not 16 external human reviewers or formal peer review.

> **Historical record:** This review records simulated perspectives as of 2026-11-19. It is not external scientific review and is not a current acceptance decision. PR #297 source is `5e9fbe02a954eadb2c8503890f77950ce7296ea7`; combined integration HEAD is `3e0159aafa53313c47052b7adbae1ac55514293c`. PR-associated CI is not validation of that combined HEAD. Local Workbench/browser acceptance remains unverified because the sandbox blocked loopback socket access.

## Evidence reviewed

- Main revision: `dcedccf50ae5a4541ababc29cfc7471a7d0ea14a`.
- Main CI #44515762167: 702 passed, 13 skipped, 9 warnings; engineering gates passed.
- Scientific Validation #44515762163: all five jobs succeeded. It acquired separate 150-row DR24 Objects Table and ALeRCE reference snapshots plus the frozen ALeRCE reference manifest. The two 150-row responses are not joined.
- A previous seven-OID Workbench smoke with 2,183 epochs is recorded. It proves raw retrieval/display only.
- PR #297 adds a pinned two-OID live parity test and Workbench runbook. Those two operations remain unverified for this handoff.
- Issue #282: original v0.2.0 production artifact is not available in accessible remote sources.
- Issues #253 and #249: DR24 application integration and minimum source identity remain open.
- Issue #293: license/distribution decision remains open.

## Sixteen specialist seats

| Seat | Conclusion | Required control |
|---|---|---|
| Chief Scientist / PI | Raw DR24 demo is useful, but it is not scientific classification. | State scope and unknowns. |
| ZTF data specialist | DR24 must retain native HMJD, photometry, flags, OID, filter, field, and RCID. | No unapproved conversion or mask. |
| Transient astrophysicist | OID does not prove a physical source; ALeRCE labels are not independent truth. | Preserve ambiguous and unmatched cases. |
| Time-series statistician | Cadence, uncertainty, and time semantics affect feature validity. | Approve time and feature contracts. |
| Astroinformatics engineer | A 150-row metadata response is not a 100k light-curve dataset. | Pin the complete cohort and hashes. |
| Cross-match specialist | Nearest-neighbour matching alone is not identity evidence. | Implement AOIC association records. |
| ML lead | Frozen model cannot run on DR24 until artifact and feature compatibility pass. | Keep inference BLOCKED; version new models separately. |
| Benchmark lead | 150 balanced ALeRCE objects are not population truth. | Object-level and temporal leakage-safe evaluation. |
| Software architect | Raw Explorer and model inference are separate paths today. | Integrate DR24 through the normal service. |
| Backend engineer | API and Workbench foundations exist; full-cohort orchestration is incomplete. | Explicit source selection; no silent fallback. |
| DevSecOps | Main dependency audit passes after PR #289; license remains unresolved. | Keep security and licensing gates active. |
| QA/reliability | Green CI is good engineering evidence; 13 skips and missing artifact matter. | Run live test, local UI, export, and recovery tests. |
| Scientific UX | UI must show source, OID, filter, epochs, QC, provenance, and blocked model state. | Never show placeholder predictions. |
| Product manager | Park needs a demonstrable workflow with realistic scope. | Present raw demo, then complete full-cohort MVP. |
| Technical writer | Docs contain conflicting release, artifact, and roadmap statements. | One canonical handbook, roadmap, model card, and Persian addendum. |
| Independent Red Team | Main risk is a convincing demo that implies unsupported identity or classification. | Challenge every claim against retained evidence. |

## Consensus

### Gate A — laboratory demonstrator

A limited presentation is reasonable only after the pinned two-OID live test and local Workbench run pass. Permitted claims:
- bounded public DR24 HATS retrieval;
- raw light-curve inspection;
- diagnostic QC;
- acquisition provenance;
- raw JSON export.

Do not claim DR24 classification, calibrated confidence, validated anomaly detection, production QC, physical-source identity, or full-ZTF performance.

### Gate B — Park MVP

MVP acceptance requires the complete predeclared cohort and the full API/Workbench workflow. Arbitrary 50-, 100-, or 1,000-object samples are diagnostic only. The cohort must pass dataset, identity, acquisition, QC, feature, model, uncertainty/OOD, Workbench, reproducibility, independent-evaluation, and delivery gates.

## Final disposition

- Laboratory demonstrator: **NOT YET VERIFIED** for this handoff. If the live test and local Workbench pass, mark **READY WITH LIMITATIONS**.
- Full Park MVP: **NOT ACCEPTED**.
- Validated DR24 classifier: **NOT ESTABLISHED**.
- Final product: continue in the same repository and architecture after the Park milestone.

## Ordered actions

1. Preserve and reconcile the local WSL worktree.
2. Complete and review PR #297.
3. Run the pinned live DR24 test and Workbench procedure.
4. Correct the Park slides and attach the Persian status addendum.
5. Freeze the full Park cohort and AOIC identity ledger.
6. Integrate DR24 through the normal observation service.
7. Recover the original model or validate a separately versioned model.
8. Plan any full-cohort analysis or independent evaluation only under a separately approved scientific plan.
9. Complete deployment, backup/restore, licensing, and release gates.
10. Continue separately governed product work after Park scope and evidence are settled.

The 16 seats are simulated perspectives. External scientific review remains a separate future requirement.
