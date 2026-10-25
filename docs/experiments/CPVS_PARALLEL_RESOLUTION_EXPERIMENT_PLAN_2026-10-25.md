# CPVS Parallel Resolution Experiment Plan — 2026-10-25

## Purpose

Evaluate two independent approaches to the CPVS candidate/reference membership discrepancy without changing the immutable scientific baseline v0.2.0, model artifacts, production selection behavior, or release v1.0.1.

## Research question

Can a source-backed correction to the Jupyter/reconstruction path explain and correctly resolve the membership differences, and where the historical publisher rule cannot be established, can a provenance-rich discrepancy report make those differences safely usable without implying scientific resolution?

## Track A — reconstruction / Jupyter processing

Branch: `experiment/cpvs-jupyter-reconstruction-20261025`

1. Inventory the actual notebook/scripts and identify the exact code path that generated the candidate membership set.
2. Identify authoritative source versions, schemas, hashes, identifier definitions, and the meaning of Table2 `Seq` versus the light-curve attachment's SourceID.
3. Verify object-level versus light-curve-row-level grain; joins; normalization; filtering order; duplicate handling; missing, zero, NaN, and infinite values.
4. Reproduce the current candidate set from hash-identified inputs before changing any logic.
5. Run the four-field predicate `gmag > 0`, `rmag > 0`, `Per-g > 0`, `Per-r > 0` only as a separate diagnostic hypothesis. Do not assume it is the historical publisher rule.
6. Record every included/excluded object ID, source-row mapping, field values, reason, source hashes, environment, commands, and deterministic rerun result.
7. Add regression tests for non-contiguous identifiers, duplicate IDs, missing/non-finite values, object/row grain, and set equality/difference invariants.

## Track B — discrepancy reporting

Implementation branch: `feature/cpvs-discrepancy-report-20261024`; PR [#224](https://github.com/saeed92m/ztf-classifier/pull/224).

1. Run the report builder against authoritative, hash-identified parent metadata, candidate IDs, and published Table4 IDs.
2. Verify all candidate-only IDs have parent provenance and no duplicate/unmapped IDs are silently dropped.
3. Reconcile counts and object IDs across CSV, HTML, Markdown, and strict JSON.
4. Verify deterministic hashes/manifests and preserve `NOT_ASSESSED` for raw-light-curve review or cross-match evidence that was not actually performed.
5. Keep the historical publisher-rule blocker open if source evidence does not establish the exact rule.

## Comparison matrix

Compare both tracks using the same source artifacts and explicit reference definition:

- source and object-identity integrity;
- exact deterministic reproducibility;
- false inclusion and false exclusion counts and IDs;
- missing/invalid/non-finite value behavior;
- sensitivity to schema and identifier mapping;
- provenance completeness and human interpretability;
- behavior on independent source-backed astronomical datasets outside CPVS.

A match to the published cardinality (730,184) alone is not sufficient. Do not choose or tune a predicate merely to force that number. ALeRCE v0.2 benchmark labels are separate and are not independent ground truth for this membership question.

## Decision gates

- **Gate 0 — source readiness:** all required inputs, schemas, source versions, and hashes identified.
- **Gate 1 — reproducibility:** current output reproduced from the recorded inputs and commands.
- **Gate 2 — correctness:** set-level comparison and all changed/excluded IDs are explained by evidence.
- **Gate 3 — generalization:** checks on independent source-backed astronomical inputs, with known limitations stated.
- **Gate 4 — acceptance:** review evidence, regression tests, and documentation; do not alter production selection until approved by evidence.

If the publisher's historical rule remains unknowable, keep that uncertainty explicit and use discrepancy reporting as a product capability. This is a valid product-handling outcome, but it is not proof that the historical scientific method was exactly reproduced.

## Current state

As of 2026-10-25, the experiment branch exists and the comparison plan is recorded in [Issue #170](https://github.com/saeed92m/ztf-classifier/issues/170). The two tracks have not yet been run and compared. The source-backed 11,602-row report has not yet been generated and audited. No method is selected as winner and the scientific blocker remains open.

The 100-object operational behavior test in [Issue #222](https://github.com/saeed92m/ztf-classifier/issues/222) is separate; it does not establish scientific accuracy or resolve CPVS membership.
