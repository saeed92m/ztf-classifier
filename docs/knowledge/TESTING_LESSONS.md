# Testing Lessons

Testing is executable project memory.

- Every important bug receives a regression test when technically possible.
- Every stable discovery becomes a test, invariant, contract, validation rule, or benchmark where appropriate.
- Tests must preserve failure semantics rather than merely make CI green.
- Scientific validation tests must distinguish ground truth from reference agreement.
- Unexecutable external-data checks remain explicit blockers rather than being downgraded to warnings.
- Process-contract tests must execute the real CI entrypoint; syntactically valid Python is insufficient if the workflow shell prevents the contract from running.
- Merge-blocking lifecycle records must use explicit allowed states; "pending" is not a valid terminal regression state.
