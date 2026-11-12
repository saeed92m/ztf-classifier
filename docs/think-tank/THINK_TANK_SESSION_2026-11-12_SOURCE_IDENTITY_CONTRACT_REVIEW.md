# Think Tank Session 05 — Minimum Source Identity Contract and Multi-OID Evidence Review

**Session ID:** TT-2026-11-12-05  
**Date:** 2026-11-12  
**Scope:** Issue #249, Draft PR #283, source identity domain records, evidence linkage and multi-OID safety  
**Review form:** Focused 8-role panel plus independent Red Team  
**Status:** Contract design conditionally supported; CI acceptance blocked  
**Baseline:** v0.2.0 unchanged

> These are simulated specialist perspectives under the project's approved 16-seat charter. This is not a claim that external experts attended.

## 1. Roles activated

| Seat | Reason |
|---|---|
| 01 Chief Scientist / PI | Ensure identity status does not overstate astrophysical certainty. |
| 02 ZTF Survey and Data Specialist | Verify OID, band, field and RCID semantics. |
| 04 Astronomical Statistics and Time-Series Specialist | Review evidence completeness for cross-band claims. |
| 06 Catalog Cross-Matching and Source Identity Specialist | Review source-object/candidate evidence relationships. |
| 09 Scientific Software Architect | Review contract boundaries and compatibility. |
| 12 QA and Reliability Engineer | Review regression intent and CI outcomes. |
| 15 Scientific Documentation Specialist | Preserve decision and failure history. |
| 16 Independent Evaluator / Red Team | Search for fail-open paths and unsupported multi-OID associations. |

## 2. Inputs inspected

- Project Source `تعیین اعضای اتاق فکر.txt` and the 16-expert Master Prompt.
- Project Source `تایید سیاست همگرایی پروژه.txt` for evidence and regression discipline.
- Issue #249.
- Draft PR #283, branch `feature/minimum-source-identity-contract-20261112`.
- `source_identity.py`, `test_source_identity_contracts.py`, `domain/__init__.py` and its lifecycle record.
- CI runs `43244871653` and `43244896597`.
- Test correction commit `44369783e1b28248cf6e93832e1472a87540f09f`.

## 3. Contract findings

The domain contract distinguishes survey-native identifiers from astrophysical source identities. It does not perform matching, merge OIDs, persist decisions or alter inference.

The current branch contains:

1. Immutable survey-object, catalog-entry, astrophysical-source, evidence and association records.
2. A stable survey-object reference key using survey, release, OID, band, field and RCID.
3. Explicit confirmed, ambiguous, unmatched, rejected and deferred-review states.
4. A requirement that confirmed source identity references its confirmation association.
5. A validator that checks that the referenced association confirms the same source.
6. Exact evidence-pair coverage for each declared survey-object/candidate-source pair in confirmed, ambiguous and rejected decisions.
7. No-candidate evidence for every declared survey object in an unmatched decision.
8. Rejection of booleans in numeric partition and evidence fields.
9. 34 focused test functions.

These controls stop the domain record from accepting incomplete or unrelated references. They do not prove that the evidence is scientifically correct or that several OIDs represent one physical source.

## 4. CI evidence and root cause

Two CI runs on head `d9e17467ce9a3dca17116d6fa609a17f1c75b2fc` reported:

| Run | Passed | Failed | Skipped | Warnings |
|---|---:|---:|---:|---:|
| 43244871653 | 734 | 2 | 13 | 9 |
| 43244896597 | 734 | 2 | 13 | 9 |

Both failures were stale expected-message assertions in:

- `test_confirmed_association_rejects_evidence_for_different_candidate`
- `test_ambiguous_association_requires_evidence_for_every_candidate`

The actual guard was:

`association evidence must cover every declared survey-object/candidate pair.`

The invariant was deliberately strengthened. The tests still expected the older set-level wording. The assertions were corrected in commit `44369783e1b28248cf6e93832e1472a87540f09f`. The focused test count remains 34.

**Fresh CI on the corrected head was not available at the time of this record.**

On the failed runs, Format, Lint and Lifecycle Gate passed. CodeQL, Product Scope Audit and Scientific Validation contract checks passed. Source-backed DR24/ALeRCE, historical ALeRCE, provenance and StarEmbed jobs were skipped. Runtime Smoke, package build and dependency audit were skipped after the test failure.

## 5. Red Team findings

1. Checking the set of OIDs and the set of candidates separately is not enough. Evidence must cover each OID/candidate pair. The current branch applies this invariant.
2. An unmatched decision must describe each declared survey object. One no-candidate evidence record is not enough for a multi-OID decision. The current branch checks full object coverage.
3. A confirmed source must reference the specific association that confirms it. Generic provenance is not enough.
4. The contract checks references supplied by the caller. It does not authenticate evidence origin, method quality or scientific truth. These need a trusted evidence pipeline and adjudicated validation.
5. API serialization, persistence and backwards compatibility have not been demonstrated.
6. No matcher, candidate generation, angular probability model, proper-motion model, epoch transformation or automatic grouping is implemented.

## 6. Recommendation

**APPROVE THE DOMAIN INVARIANTS WITH CONDITIONS.**

Conditions:
- Fresh CI must pass Format, Lint, all 34 focused tests, the full suite, runtime smoke, package build, dependency audit and CI Gate on the same head.
- API serialization and persistence must preserve full survey-object and candidate evidence references.
- Do not use these records to group OIDs or create model-ready multi-band light curves until an independently adjudicated sample and association policy pass scientific validation.
- Keep PR #283 Draft until the conditions pass and the result is reviewed.

Implementation state: `IN_PROGRESS`, awaiting fresh CI.  
Scientific validation: `NOT_VALIDATED`.  
Issue #249 remains open.  
No v0.2.0 baseline, feature, model, taxonomy, benchmark or threshold changed.
