# ZTF Classifier — Master Defect and Blocker Register

**Status date:** 2026-11-19

**Main revision:** `dcedccf50ae5a4541ababc29cfc7471a7d0ea14a`

> **Historical snapshot:** Register state and the local-worktree note below are dated 2026-11-19 and are not a current status query. PR #297 source is `5e9fbe02a954eadb2c8503890f77950ce7296ea7`; combined integration HEAD is `3e0159aafa53313c47052b7adbae1ac55514293c`. PR-associated CI must not be attributed to the combined HEAD. Local browser acceptance remains unverified because sandbox loopback permission is unavailable.

| ID | Priority | Area | Tracker | Current state | Closure evidence |
|---|---|---|---|---|---|
| D-01 | P0 | Local work preservation | Local WSL checkout | Historical output: 94 staged files, 2 untracked paths, branch 3 commits behind. Recheck. | Status snapshot, staged/unstaged patches, untracked archive, repository bundle, hashes; reconcile without loss. |
| D-02 | P0 | Park MVP | [#158](https://github.com/saeed92m/ztf-classifier/issues/158) | OPEN / NOT ACCEPTED | Full predeclared cohort passes all data, identity, QC, feature, model, Workbench, reproducibility, independent-evaluation, and delivery gates. |
| D-03 | P0 | DR24 application path | [#253](https://github.com/saeed92m/ztf-classifier/issues/253) | OPEN | Explicit DR24 selection through normal observation service and Workbench. ALeRCE remains separate. No silent fallback. |
| D-04 | P0 | Frozen production artifact | [#282](https://github.com/saeed92m/ztf-classifier/issues/282) | OPEN / UNKNOWN | Original artifact recovered, independently authenticated, audited, and inference tests executed. No lab-smoke substitute. |
| D-05 | P0 | Source identity / AOIC | [#249](https://github.com/saeed92m/ztf-classifier/issues/249) | OPEN | Versioned identity ledger with namespace, OID, filter/field/RCID, coordinate uncertainty, association method, status, and evidence. |
| D-06 | P1 | License and distribution | [#293](https://github.com/saeed92m/ztf-classifier/issues/293) | OPEN / OWNER DECISION REQUIRED | Owner-approved license and distribution policy. No license change without approval. |
| D-07 | P1 | Source/photometry semantics | PR #284 and related work | OPEN / REVIEW | Keep DR24 native values and supplementary source products separate by identifier, time scale, photometry, and QC. |
| D-08 | P1 | Documentation divergence | PRs #247, #266, #281, #297 | IN PROGRESS | Reconcile dated canonical handbook, roadmap, defect register, installation guide, model card, and Park addendum. |
| D-09 | P2 | CIN runtime | [#251](https://github.com/saeed92m/ztf-classifier/issues/251) | DEFERRED | Governance, privacy, annotation provenance, moderation, review, and security gates pass before runtime. |
| D-10 | P2 | Cross-platform distribution | [#158](https://github.com/saeed92m/ztf-classifier/issues/158) | NOT ACCEPTED | Clean-machine Windows/macOS/Linux install, update, rollback, backup, and restore tests pass. |

## Security and release

- PR #289 merged on 2026-11-19. Soup Sieve was upgraded to 4.1.
- Main CI #44515762167 passed: 702 tests passed, 13 skipped, 9 warnings.
- At least seven production-inference tests were skipped because the original model artifact or shared inputs were unavailable.
- No Park prerelease has been created.
- Issue #293 remains open. Do not publish a new distributable until the license policy is approved.

## Triage rule

Do not close an issue or PR because it is old. Close it only when work is merged, fully superseded with content preserved, or explicitly rejected with a reason and retained evidence. Keep unresolved scientific questions open.
