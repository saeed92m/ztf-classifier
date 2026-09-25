# Release Policy — Cumulative Improvement

Every release candidate inherits the previous accepted release baseline and its validated knowledge.

## Release evidence

A release candidate must record:
- inherited baseline and immutable references;
- changes and affected subsystems;
- expected improvement or justified trade-off;
- relevant before/after measurements;
- test and benchmark evidence;
- regression status and disposition;
- new knowledge and evidence status;
- unresolved limitations and scope;
- next-stage impact;
- a validated cumulative cycle record under `configs/process/cycles/`.

Meaningful pull requests contributing to a release must carry their own cycle record. The release evidence is cumulative: it consumes those records rather than reconstructing project history from scratch.

## Release integrity

The cumulative process never relaxes the permanent Scientific Validation Product-Level Gate.

A release cannot claim scientific completion while required benchmark evidence, leakage checks, provenance, reproducibility evidence, or external historical evidence remain unresolved.

## Heavy validation

Large source-backed benchmarks may be staged or scheduled, but the release process must consume an explicit validation result and fail closed when required evidence is missing or blocked.

## Optimization rule

A local performance gain is not a release improvement if it materially damages scientific validity, correctness, reproducibility, reliability, or robustness.

## Knowledge handoff

The release package must point to the cumulative improvement ledger and relevant knowledge IDs so the next development cycle begins from accepted evidence rather than from a fresh conceptual baseline.
