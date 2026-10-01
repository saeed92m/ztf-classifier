# Failure Database

| ID | Status | Failure | Root cause | Lesson | Prevention / regression protection |
|---|---|---|---|---|---|
| FD-001 | VERIFIED | Historical ALeRCE raw-cache reproduction mismatch. | Mutable external service drifted from frozen historical snapshot. | Live service cannot substitute for immutable historical evidence. | Strict frozen assertions and explicit unresolved gate; Issue #51. |
| FD-002 | VERIFIED | Reference-role regression test initially asserted the wrong semantics. | Test conflated reference provenance with ground-truth provenance. | Evaluation role must drive required provenance independently. | Dedicated reference-only regression test. |
| FD-003 | VERIFIED | CI quality-gate failures during validation rollout. | Contract implementation and test expectations temporarily diverged. | New scientific contracts require focused tests before merge. | Registry/gate tests and fail-closed CI. |
| FD-004 | VERIFIED | Cumulative lifecycle gate failed after PR #72 because the new CI shell variables were escaped and a lifecycle record used an unsupported pending regression status. | Generated workflow syntax preserved shell escaping literally; the process record did not encode an allowed merge-blocking state. | Process controls themselves require executable CI validation and explicit state-machine semantics. A green intended design is not enough; the actual workflow and record must execute correctly. | CI shell-variable regression coverage through the live workflow; lifecycle contract rejects unsupported statuses; accepted cycles require PASS/no blockers. |
| FD-005 | VERIFIED | CPVS 730k reconstruction remained a project-wide bottleneck despite the discrepancy occurring before ML. | Product validation and historical external reproduction were coupled too tightly in the gate/workflow. | Evidence scopes must be separated without weakening the exact-reproduction claim. | Product gate scoped to product benchmarks; CPVS reconstruction remains fail-closed for its own claim. |

## Required failure lifecycle

Failure -> Root Cause -> Lesson -> Rule or Design Change -> Regression Test -> Future Prevention

A failure is not fully learned until its prevention is encoded where technically possible.
