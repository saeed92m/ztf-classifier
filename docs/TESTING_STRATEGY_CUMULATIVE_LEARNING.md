# Testing Strategy — Cumulative Learning

Testing is the executable memory of the project.

## Rules

1. Every important bug gets a regression test when technically possible.
2. Stable discoveries become tests, invariants, contracts, validation rules, or benchmarks where appropriate.
3. Tests preserve failure semantics; a green suite is not allowed to erase a known scientific blocker.
4. Every meaningful iteration compares against its inherited baseline.
5. Scientific changes invoke the relevant external benchmark/regression suite according to the permanent change-trigger policy.
6. Missing external evidence remains explicit NOT_VERIFIED or NOT_EXECUTED evidence and cannot be silently treated as pass.

## Lifecycle evidence

A stage record must contain previous knowledge, baseline, measurement, validation, failure analysis, knowledge extraction, regression status, and next-stage impact.

The executable contract is ztf_classifier.lifecycle and is covered by tests/test_cumulative_lifecycle.py.

## Regression hierarchy

- unit regression: local behavior and invariants;
- contract regression: API/schema/provenance contracts;
- integration regression: subsystem boundaries;
- performance regression: before/after measurements where relevant;
- scientific regression: benchmark and leakage evidence;
- release regression: fail-closed acceptance and unresolved blocker disposition.

## Multi-objective interpretation

No single metric is sufficient to declare an improvement. Relevant dimensions include correctness, scientific validity, reproducibility, robustness, coverage, reliability, performance, and accuracy.

A trade-off is accepted only with evidence and an explicit decision record.
