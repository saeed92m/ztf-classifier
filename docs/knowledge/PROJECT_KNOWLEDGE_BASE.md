# Project Knowledge Base

This is the operational memory layer for ZTF Classifier. It carries only knowledge classified by evidence status and intended to influence later engineering, scientific validation, testing, performance, and release decisions.

## Knowledge status

Every finding uses one of: FACT, VERIFIED, SUPPORTED, HYPOTHESIS, ASSUMPTION, UNRESOLVED, REJECTED.

Only FACT, VERIFIED, and SUPPORTED findings may become normative baseline rules without explicit qualification. Unverified knowledge must not silently propagate as fact.

## Cumulative-learning rule

Every implementation cycle consumes validated prior knowledge, records its inherited baseline, measures relevant change, extracts new knowledge, and carries that knowledge into the next cycle. A stage is never isolated from earlier stages.

## Current verified knowledge

- v0.2.0 is an immutable scientific baseline and must never be rewritten. — VERIFIED
- Scientific Validation & External Benchmarking is a permanent product-level release gate. — VERIFIED
- Ground truth is distinct from independent classifier/reference agreement; ALeRCE is reference evidence, not universal ground truth. — VERIFIED
- Large benchmark datasets stay outside Git; manifests, checksums, contracts, configurations, and reports are versioned. — VERIFIED
- Generic leakage checks that cannot be established are NOT_EXECUTED and block scientific acceptance. — VERIFIED
- Historical ALeRCE raw-cache reproduction is currently blocked by external-data drift; frozen assertions must not be weakened. — VERIFIED / UNRESOLVED for completion

## Addition rule

1. Identify evidence and status.
2. Record finding and scope.
3. Record failure/root cause when applicable.
4. Encode prevention as a test, invariant, contract, benchmark, or rule when possible.
5. Link the knowledge to the cumulative ledger and affected roadmap/architecture item.
6. Carry the knowledge into the next implementation cycle.
