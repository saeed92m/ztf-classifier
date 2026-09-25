# Cumulative Improvement Ledger

This ledger is the auditable growth record for meaningful implementation cycles. It must never contain fabricated measurements.

| Stage / PR | Baseline | Change | Metrics Before | Metrics After | Improvement / Trade-off | Regression | Root Cause | Knowledge IDs | Tests Added | Decision | Next-stage impact |
|---|---|---|---|---|---|---|---|---|---|---|---|
| PR #62 | Scientific validation contracts before registry foundation | Registry, runner, regression, CI gate | Registry absent | Registry/runner operational; external evidence still pending | Validation capability increased | External source evidence unresolved | Immutable external evidence not yet available | SF-001, SF-002 | Registry/gate tests | Accepted foundation; scientific gate remains unverified | Adapter/evidence implementation |
| PR #64-66 | Scientific validation semantics | DoD plus reference-role regression fixes | Reference semantics test incomplete | Ground-truth/reference separation executable | Correctness improved without weakening gate | Historical ALeRCE drift remains | Mutable external source | FD-001, FD-002 | Reference-role regressions | Accepted | Source-backed evidence plus cumulative lifecycle |
| Current cycle | Linear stage workflow | Cumulative lifecycle control | Prior knowledge implicit | Explicit lifecycle, ledger, knowledge contract | Process correctness becomes measurable | External benchmark completion remains pending | N/A | AD-CI-004, AD-CI-005 | Lifecycle contract tests | Pending merge and CI | Apply contract to every future stage |

## Measurement rule

If numeric measurement is not applicable or not yet available, record NOT_MEASURED rather than inventing a value and explain why in the cycle evidence.
