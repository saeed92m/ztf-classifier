# Think Tank Session 08 — Source Identity Contract Type Safety and Deferred Evidence Integrity

**Session ID:** TT-2026-11-12-08  
**Date:** 2026-11-12  
**Scope:** Red-team review of PR #283 source-identity domain contracts, malformed optional field types and deferred-review evidence references  
**Review form:** All 16 simulated specialist seats plus independent Red Team pass  
**Reviewed PR #283 pre-hardening head:** `f582132f304f24783323102063ccc5daa64d87ea`  
**Implementation commits:** `e5f4fc4936f313647b00e81b09b8959a9f48b9d0`, `4570072319254d2bde94b975664e4c593f0a325f`  
**Status:** Narrow hardening implemented; current-head CI pending  
**Protected scientific baseline:** v0.2.0 unchanged

> This is a simulated 16-seat review. It does not claim that 16 external human experts attended.

## 1. Objective

Review the minimum source-identity contract after Session 05 and the multi-OID evidence-pair correction. The review focuses on malformed optional values and evidence consistency in `DEFERRED_REVIEW`.

The domain module is additive. It does not implement a matcher, source registry, persistence layer, OID merge, physical identity inference or model integration.

## 2. Evidence inspected

- PR #283 and its current code on branch `feature/minimum-source-identity-contract-20261112`.
- `src/ztf_classifier/domain/source_identity.py`.
- `src/ztf_classifier/domain/__init__.py`.
- `tests/test_source_identity_contracts.py`.
- `configs/process/cycles/minimum-source-identity-contract-20261112.json`.
- Issue #249 and Session 05.
- Prior current-head engineering run 43284976844: 736 passed, 13 skipped, zero failures, 9 warnings on head `988e3c5537a0278119b680d98e40d9978092ba3a`.

The prior CI result does not validate the new hardening commits. New current-head CI is required.

## 3. Findings from the 16 specialist seats

| Seat | Finding | Required control |
|---|---|---|
| 01 Chief Scientist / PI | Domain consistency is necessary but cannot prove physical identity. | Keep scientific validation separate from contract tests. |
| 02 ZTF Survey/Data | Survey/release/OID/band/field/RCID must remain source-native. | Preserve existing immutable survey object key. |
| 03 Time-Domain Astrophysics | Candidate associations need evidence that points to the declared source hypothesis. | Do not accept unrelated candidate evidence. |
| 04 Statistics/Time Series | Raw scores and calibrated probabilities have different semantics. | Keep calibration version typed and mandatory for calibrated probability. |
| 05 Astroinformatics/Big Data | Optional metadata can be malformed by JSON/API deserialization. | Validate types before calling string methods or set membership. |
| 06 Cross-Match/Identity | Deferred review may lack a final decision, but evidence supplied with it must still reference declared candidates or the no-candidate sentinel. | Enforce deferred candidate-reference integrity. |
| 07 AI/ML | No model or feature behavior should consume these contracts yet. | No inference integration in this change. |
| 08 Scientific Validation | Focused tests must cover malformed types and deferred evidence references. | Add regression cases and preserve UNKNOWN/deferred semantics. |
| 09 Software Architect | Frozen dataclasses need explicit runtime validation; type hints alone are not runtime enforcement. | Raise stable ValueError messages for malformed optional fields. |
| 10 Backend/Platform | API payloads commonly arrive as untrusted JSON values. | Reject malformed types before persistence or job execution. |
| 11 MLOps/Security | Unexpected AttributeError/TypeError paths can obscure bad input and weaken fail-closed behavior. | Use explicit input validation and deterministic errors. |
| 12 QA/Reliability | Existing tests cover pairwise OID evidence but not every optional metadata type. | Add five focused regression tests. |
| 13 Scientific UX/UI | These checks do not change user-facing behavior. | Keep UI out of scope. |
| 14 Product/Commercialization | This is foundational contract hardening, not a Park MVP feature. | Keep product scope unchanged. |
| 15 Documentation | Record the difference between contract validity and scientific identity proof. | Update session and lifecycle evidence. |
| 16 Independent Red Team | A deferred association could carry evidence for an undeclared candidate; several optional fields could throw AttributeError or TypeError instead of a stable validation error. | Close these fail-open/error-path gaps. |

## 4. Red Team defects and corrections

### Finding A — malformed optional strings

Before hardening, several optional fields called `.strip()` or participated in set membership without an explicit runtime string check:

- `AstrophysicalSourceRef.superseded_by`
- `AssociationEvidence.score_kind`
- `AssociationEvidence.calibration_version`
- `AssociationEvidence.content_hash`
- `SourceAssociation.reviewer_ref`
- `SourceAssociation.supersedes_association_id`
- `SourceAssociation.confirmed_source_id`

Malformed values could raise incidental `AttributeError` or `TypeError` rather than a stable domain validation error.

**Correction:** validate optional values as non-empty strings before string operations or set membership.

### Finding B — deferred evidence could reference an undeclared candidate

The contract already checked that every evidence `source_ref` referred to a declared survey object. Final states also checked exact candidate/source pair coverage. However, `DEFERRED_REVIEW` could carry evidence whose `candidate_ref` was not among the declared candidate IDs.

**Correction:** if deferred evidence is present, each candidate reference must match a declared candidate source or the explicit `no-candidate` sentinel. Deferred review may still have no evidence.

## 5. Implemented changes

On PR #283:

- Added explicit type validation for the optional string fields listed above.
- Added a deterministic error for non-string `score_kind`.
- Added candidate-reference validation for evidence attached to `DEFERRED_REVIEW`.
- Added five focused regression test functions:
  1. non-string `superseded_by`;
  2. non-string `score_kind`;
  3. non-string `calibration_version` and `content_hash`;
  4. non-string `reviewer_ref`, `supersedes_association_id` and `confirmed_source_id`;
  5. deferred evidence for an undeclared candidate.

The focused source-identity test module increases from 34 to 39 test functions.

## 6. Joint decision

**APPROVE WITH CONDITIONS** the additive domain hardening.

Conditions:

1. Current-head Format, Lint, focused tests, full Test Suite, Runtime Smoke, Build, Dependency Audit and CI Gate must pass.
2. The lifecycle record must preserve engineering regression PASS separately from scientific validation NOT_VERIFIED/BLOCKED.
3. API serialization and persistence compatibility remain a separate review.
4. No matcher, registry, ledger, automatic OID grouping or model inference is included.
5. Independent adjudicated cross-match validation remains required before any physical identity claim.
6. Keep PR #283 Draft and unmerged pending review.

## 7. Status and evidence boundary

- Implementation: **IMPLEMENTED** on the two listed commits.
- Focused test count: **39 test functions**.
- Current-head test result: **PENDING**.
- Prior CI result: 736 passed, 13 skipped, zero failures on the pre-hardening head only.
- Scientific identity validation: **NOT VERIFIED**.
- API/persistence compatibility: **NOT REVIEWED**.
- v0.2.0 and v1.0.1: unchanged.

This session closes only the identified input-validation gaps if the new current-head CI passes. It does not close Issue #249 or prove that any OIDs represent the same physical astrophysical source.
