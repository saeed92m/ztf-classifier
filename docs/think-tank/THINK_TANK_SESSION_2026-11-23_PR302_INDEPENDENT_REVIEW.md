# Think Tank Session — PR #302 Independent Review

**Date:** 2026-11-23  
**Method:** simulated review using the 16 specialist seats in the project charter. This is not external human peer review.

## Review scope

- Repository: `saeed92m/ztf-classifier`
- Base revision: `main` at `b933af4bf91c00d0cdbb9fdebeeec7ae7b799474`
- Review branch: `codex/park-integration-300-301`
- Reviewed head: `4bc71e436801d83a2ff6e0cfff0302824377987a`
- PR: [#302](https://github.com/saeed92m/ztf-classifier/pull/302)
- Compare result: 18 commits ahead, 0 behind; 29 changed files at review time.

This review is limited to the GitHub-hosted revision and retained workflow evidence. It does not inspect the user's current local WSL worktree or local scientific data.

## Evidence verified

### Engineering CI

CI run [45091270679](https://github.com/saeed92m/ztf-classifier/actions/runs/45091270679) completed successfully:

- Format Check: PASS
- Lint: PASS
- Cumulative Lifecycle Gate: PASS
- Test Suite: **783 passed, 14 skipped, 9 warnings**
- Total test coverage: **82%**
- Runtime Smoke Tests: PASS
- Build & Verify Package: PASS
- Dependency Audit: PASS
- CI Gate: PASS

The new `src/ztf_classifier/validation/dr24_evidence.py` module has 72% coverage in this run. The test log confirms the aggregate skip count. The log inspected here does not establish the reason for every skip.

Additional checks on the same head:

- CodeQL run [45091270660](https://github.com/saeed92m/ztf-classifier/actions/runs/45091270660): PASS
- Product Scope Audit run [45091270686](https://github.com/saeed92m/ztf-classifier/actions/runs/45091270686): PASS
- DR24 Batch Workbench UI Contract run [45091270655](https://github.com/saeed92m/ztf-classifier/actions/runs/45091270655): PASS
- Scientific Validation run [45091270706](https://github.com/saeed92m/ztf-classifier/actions/runs/45091270706): offline registry, lifecycle, and local-artifact-audit contracts PASS.

### Scientific workflow boundary

Four jobs in Scientific Validation were SKIPPED:

1. DR24 and ALeRCE source-backed evidence.
2. Independent StarEmbed product benchmark acquisition.
3. Source provenance acquisition and scientific gate readiness.
4. Immutable historical ALeRCE reference verification.

A successful workflow conclusion does not convert these skips into scientific passes.

### PR #302 evidence-capture workflow

The branch adds a manual-dispatch-only workflow for two fixed DR24 OIDs. It uses bounded acquisition, dependency locks, a versioned manifest, checksums, redacted logs, and a fail-closed validator.

The code and offline tests are present. The live workflow has not been shown to run on this head. In particular, the clean-runner installation of `requirements-dr24.lock` and the resulting live evidence bundle remain unverified.

The bundle correctly distinguishes decoded API response bytes from original HATS/Parquet bytes. Its default Workbench export is explicitly labelled as derived from the same API response, not as a real browser download.

## Sixteen-seat review

| Specialist seat | Review conclusion | Required control |
|---|---|---|
| Chief Scientist / PI | The raw DR24 capture is operational evidence, not a classifier result. | Keep scientific claims out of the capture acceptance. |
| ZTF data specialist | Native DR24 fields and per-OID records are preserved by the stated contract. | Verify the live response and pinned epoch digests. |
| Transient astrophysicist | Two OIDs do not establish one physical source. | Do not infer source identity from this sample. |
| Time-series statistician | The bundle preserves native HMJD and epochs. | Do not infer model-time or feature parity. |
| Astroinformatics engineer | The fixed two-OID bundle is bounded and reproducible in design. | Verify actual dependency installation and output inventory. |
| Cross-match specialist | AOIC is not delivered by this capture workflow. | Keep identity unresolved unless separate evidence exists. |
| ML lead | No validated DR24 inference is demonstrated. | Keep DR24 classification BLOCKED. |
| Benchmark lead | The workflow does not create a labeled cohort. | Do not count it toward the 100,000-lightcurve target. |
| Software architect | The capture path is separate from the normal observation/model path. | Keep source selection and inference boundaries explicit. |
| Backend engineer | The manual capture script and API contract are test-covered. | Verify live API behavior on the reviewed commit. |
| MLOps / DevSecOps | CI, CodeQL, and dependency audit passed. | Verify the DR24 lock install in the manual workflow. |
| QA / Reliability | Offline tests pass; 14 tests remain skipped. | Classify all skips and complete local Workbench acceptance. |
| Scientific UX / UI | Deterministic UI contract passed. | Demonstrate the actual browser workflow and downloaded export on the Park device. |
| Product manager | The work supports a limited laboratory demonstrator only. | Keep full Park MVP gates separate. |
| Technical writer | The branch adds useful runbook and evidence definitions. | Reconcile documentation that still describes the production artifact as available. |
| Independent Red Team | A green CI result could be misread as scientific readiness. | Keep this PR Draft and state every skipped or unrun gate. |

## Independent blockers retained

- Frozen v0.2.0 production artifact: not independently recovered or authenticated; see [Issue #282](https://github.com/saeed92m/ztf-classifier/issues/282).
- DR24 normal application observation-service integration: open; see [Issue #253](https://github.com/saeed92m/ztf-classifier/issues/253).
- Canonical astronomical identity and cross-match: open; see [Issue #249](https://github.com/saeed92m/ztf-classifier/issues/249).
- Park MVP: not accepted; see [Issue #158](https://github.com/saeed92m/ztf-classifier/issues/158).
- Licensing and distribution decision: open; see [Issue #293](https://github.com/saeed92m/ztf-classifier/issues/293).
- CPVS published-membership discrepancy: remains a separate scientific blocker; see [Issue #170](https://github.com/saeed92m/ztf-classifier/issues/170).

The repository README currently describes persisted production artifacts and production inference. That statement must be reconciled with Issue #282 before it is used as evidence that the original artifact is available. This review does not change the README or the frozen baseline.

## Decision

**PR #302: KEEP DRAFT — NOT READY TO MERGE.**

Reasons:

1. The new manual evidence-capture workflow has not been executed on this reviewed head.
2. Its DR24 dependency-lock installation has not been independently demonstrated on a clean runner.
3. No actual browser download is present in the evidence bundle.
4. The local Workbench run on the Park demonstration device remains unverified.
5. Four source-backed scientific jobs were skipped. Their skips are not passes.

## Next actions

1. Run the manual DR24 evidence-capture workflow on the exact reviewed head. Retain the complete artifact and job log.
2. Independently validate the downloaded bundle, including manifest, dependency snapshots, hashes, OID set, epoch counts, and canonical digests.
3. Run the pinned API parity test and actual Workbench procedure on the Park device. Retain screenshot, downloaded JSON, SHA-256, software SHA, and UTC timestamp.
4. Reconcile the README production-artifact claims with Issue #282.
5. Review the full PR diff again after new evidence is attached.
6. Keep v0.2.0, CPVS membership rules, feature definitions, model taxonomy, and scientific acceptance criteria unchanged.

**No scientific validation, full Park MVP acceptance, production-model recovery, or release readiness is claimed by this session.**
