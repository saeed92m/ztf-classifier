# ZTF Classifier — Master Execution Roadmap

**Snapshot:** 2026-11-12  
**Product target:** Independent CPU-first Astronomical Data Analysis & Discovery Platform  
**Protected baseline:** scientific v0.2.0; software v1.0.1  
**Primary delivery:** Park MVP using explicitly selected DR24 source data  
**Status:** Execution plan; phases are not claims of completed implementation.

## Guiding rules

1. Scientific integrity, reproducibility and traceability outrank feature count.
2. Keep v0.2.0, baseline_v0.2, 42 features, 150-object/15-class benchmark and v1.0.1 immutable.
3. Do not infer physical source identity from OID or angular proximity alone.
4. Keep raw acquisition, normalized observations, features, inference and discovery evidence separate.
5. No silent source fallback. If DR24 is selected and unavailable, fail explicitly.
6. Distinguish classification, calibration, conformal prediction, OOD, anomaly, novelty and discovery ranking.
7. A green CI with skipped source-backed tests is not Scientific-PASS.
8. Keep CIN optional and logically independent.
9. Do not publish releases, merge protected PRs or alter production artifacts without the required approval.

## Phase 0 — Scientific Integrity and Recovery

**Priority:** Immediate  
**Purpose:** Establish trustworthy inputs, identities and validation gates before extending inference.

### Work packages

- Recover and independently authenticate the original schema-1.0 production model artifact (#282).
- Preserve the prior 2026-11-09 local audit findings; do not ask for a duplicate inventory before remote recovery sources are exhausted.
- Resolve StarEmbed train/test identity overlap and split leakage.
- Treat CPVS (#170/#180) as P0 scientific research and the highest-priority unresolved scientific discrepancy. Keep it separate from the DR24-first Park MVP critical path. Complete artifact-level traceability, then fresh raw SNR, fixed-sample raw coverage, MGPR and root-cause analysis; do not change selectors or baselines without proof.
- Establish source identity concepts and association states for DR24 OIDs (#249).
- Confirm data license and redistribution constraints for all current sources.
- Define source-backed validation inputs, hashes, retrieval versions and expected results.

### Exit gate

- Original production artifact authenticated, or explicitly recorded as unrecoverable with a versioned decision.
- Benchmark leakage risks either resolved or excluded from independent validation claims.
- Source identity contract approved.
- Scientific evidence is traceable and fail-closed.
- No CPVS selector or baseline change without root-cause proof.

## Phase 1 — Data Foundation and DR24 Application Integration

**Priority:** P0 Park MVP  
**Primary trackers:** #158, #253, #249

### Work packages

1. Define versioned source-selection contract:
   - `ALERCE`
   - `DR24_HATS`
2. Make selection explicit at request and job level.
3. Prohibit silent fallback between sources.
4. Preserve raw DR24 records and payload hashes.
5. Keep native HMJD and photometric fields intact until a separately validated conversion is applied.
6. Define time, filter, photometry, QC, missingness and duplicate/epoch contracts.
7. Implement minimum source identity/association semantics:
   - raw OID;
   - observation/detection;
   - candidate astrophysical source;
   - catalog alias;
   - association evidence and status.
8. Keep ambiguous and unmatched associations explicit; no automatic OID merge.
9. Display source, release, filter, field, rcid, time basis and provenance in the application.

### Exit gate

- Explicit backend selection works.
- Selecting DR24 never calls ALeRCE as a fallback.
- Raw values and hashes are retained.
- 5–10 confirmed-source E2E manifest passes with pinned inputs.
- No unverified physical-source grouping.
- Failure, missing data and ambiguity are explicit.

## Phase 2 — Scientific Core and Independent Validation

**Priority:** P0/P1  
**Dependencies:** Phases 0 and 1

### Work packages

- Preserve the frozen 42-feature v0.2 contract.
- Define a separate versioned DR24 feature adapter only after normalized observation contracts pass.
- Compare DR24 features with reference features without modifying production baseline.
- Validate source grouping and object-level split isolation.
- Resolve StarEmbed overlap before independent benchmark use.
- Add independent temporal and external evaluation.
- Keep calibration and conformal prediction tied to a declared reference population.
- Keep OOD, scientific anomaly and novelty as separate engines.
- Add unknown/abstention semantics and data-adequacy outputs.
- Run CPVS diagnostics at P0 research priority: raw provenance, fixed samples, all-formula SNR, duplicate/overlap accounting and MGPR. Keep this separate from Park product acceptance and do not trigger >11.2 GB archive jobs without approval.

### Exit gate

- No identity or temporal leakage.
- Versioned feature schema and data manifest.
- Reproducible independent benchmark.
- Calibration/coverage reports with stated assumptions.
- OOD and anomaly outputs separately validated.
- Missingness and uncertainty do not create unsupported confidence.

## Phase 3 — Application Foundation and Reliability

**Priority:** P1  
**Dependencies:** stable data and scientific contracts

### Work packages

- Stable Application/Core boundary.
- Job lifecycle and persistence contracts.
- Retry, idempotency, checkpoint and crash recovery.
- Database schema migrations and result versioning.
- API pagination and bounded batch handling.
- Structured logs and provenance.
- Secure model loading and artifact integrity.
- SBOM, dependency vulnerability policy and signed release artifacts.
- Backup/restore and offline operation.

### Exit gate

- Failure-injection and recovery tests pass.
- Repeated jobs do not create duplicate or corrupt outputs.
- Artifact hashes are verified before loading.
- Secrets and user data are protected.
- No silent data loss or hidden fallback.

## Phase 4 — Scientific Workbench and Desktop Product

**Priority:** P1  
**Dependencies:** stable APIs and source identity

### Work packages

- Dashboard and Data Manager.
- Object Explorer and Light Curve Workbench.
- Source Identity / Cross-Match Explorer.
- Scientific Analysis and Model Explorer.
- Discovery Workspace.
- Reports, exports and provenance inspection.
- Clear display of class probability, conformal set, OOD, anomaly and association state as separate outputs.
- Help, troubleshooting and reproducible job history.

### Exit gate

- Researcher can install, acquire, inspect, analyze and export without Python, Git or terminal use.
- CLI and API remain available for advanced use.
- User can trace each result to source data, hashes, model and configuration.

## Phase 5 — Discovery Intelligence

**Priority:** After data and validation gates

### Work packages

- Scientific anomaly detection.
- Novelty detection and unknown-population investigation.
- Similar-object search.
- Candidate generation and prioritization.
- Scientific context and catalog evidence.
- Human review and expert escalation.
- Independent evaluation of false positives and selection bias.

### Exit gate

- Explicit scientific question and acceptance criteria.
- Controlled reference and negative samples.
- Reproducible false-positive and sensitivity analysis.
- Human review does not silently become ground truth.
- Candidate priority is not presented as a discovery claim.

## Phase 6 — Final Product Acceptance and Release

**Priority:** Release gate

### Work packages

- Windows 10/11 clean installation.
- macOS clean installation.
- Linux clean installation.
- CPU/RAM/time performance benchmarks.
- Security and dependency audit.
- Signed and hash-verified release artifacts.
- Backup/restore and upgrade/rollback tests.
- Full documentation, model card, limitations and release notes.
- Independent scientific evaluation.

### Exit gate

- All supported OS acceptance matrices pass.
- All mandatory tests pass; skips are explained and accepted explicitly.
- Scientific claims are independently supported.
- Data and model provenance are complete.
- User documentation and upgrade instructions are complete.
- Release approval is recorded.

## Parallel future subsystem — Cosmic Intelligence Network

CIN is a proposed, optional human-intelligence subsystem. It must not be required by the ZTF scientific core.

Do not begin public-scale collection or automatic retraining. First complete:
1. privacy, security, retention and licensing review;
2. task/contribution/consensus data contracts;
3. blind control tasks and random audit samples;
4. contributor reliability by task type;
5. preservation of raw responses and disagreement;
6. expert escalation and independent validation.

A controlled LC-01 Light Curve Assessment pilot may follow only after the data-governance gates pass. Human consensus is not ground truth.

## Park MVP milestone definitions

Keep these milestones separate:

| Milestone | Target | What it proves | What it does not prove |
|---|---|---|---|
| Pinned technical E2E | 5–10 confirmed sources | Raw acquisition, source identity, QC, provenance and reproducible application flow | Population-wide model performance |
| Park demonstration | 30–50 confirmed astrophysical sources | Demonstrable workflow and source-level coverage | 100k dataset readiness or scientific discovery |
| Labeled dataset target | At least 100,000 light curves | Dataset-scale engineering and research substrate with explicit counting rules | 100,000 independent astrophysical sources or validated model performance |

Every target must define whether it counts OIDs, light curves, observations, or astrophysical source groups.

## Product-level acceptance checklist

- [ ] Data sources and license terms documented.
- [ ] Source identity and association contract validated.
- [ ] Explicit DR24 selection with no silent fallback.
- [ ] Raw payloads and provenance preserved.
- [ ] Time, filter, photometry and QC contracts tested.
- [ ] Model artifact independently authenticated.
- [ ] Feature and taxonomy schemas versioned.
- [ ] Benchmark split leakage audited.
- [ ] Calibration, conformal, OOD and anomaly claims separated.
- [ ] 5–10 confirmed-source E2E accepted.
- [ ] 30–50 confirmed-source demonstration accepted.
- [ ] 100k lightcurve dataset definition and lineage accepted.
- [ ] Job persistence and recovery tested.
- [ ] Windows/macOS/Linux clean installation tested.
- [ ] CPU/RAM/performance envelope measured.
- [ ] Security, SBOM and artifact integrity accepted.
- [ ] User documentation and release notes complete.
- [ ] Independent scientific evaluator signs off.

## Immediate next actions

1. Finish the current documentation PR checks and preserve the 13 known skips.
2. Review PR #281 diff and final documentation head; keep it Draft until current-head checks finish. Do not merge without separate approval.
3. Continue remote artifact recovery and authentication under #282.
4. Define the minimum source-identity and explicit DR24 selection contract under #249/#253.
5. Prepare the pinned 5–10 confirmed-source E2E manifest.
6. Continue CPVS P0 scientific research through fresh-main PR #285: verify formula-specific synthetic tests and duplicate/overlap accounting before any raw archive run. Keep StarEmbed evidence on its own validation track.
7. Update this roadmap only when a milestone has evidence and an accepted disposition.


## Think Tank governance and work traceability

Material roadmap tasks must link to the relevant Think Tank Session ID and charter stage. Use the [16-seat Charter](think-tank/CHARTER.md) and [Session Register](think-tank/SESSION_REGISTER.md) to select review roles. Routine low-risk work may use a focused 3–5 role panel; cross-cutting work uses a 7–9 role core and Red Team; major scientific, identity, benchmark, security, product-acceptance and release gates use all 16 seats.

Current required links:

- DR24 application and Park source choice: Sessions 02 and 03.
- AOIC/source identity: Sessions 02 and 05.
- CPVS discrepancy: Session 04.
- Material PR evidence: the Think Tank traceability block in `.github/pull_request_template.md`.

A Think Tank recommendation does not authorize a baseline change, PR merge or release. Preserve the separate Project Owner approval gate.


## CPVS P0 research lane — Think Tank Session 07

CPVS remains the highest-priority unresolved scientific research question. This does not make it a Park MVP or product-release gate. The retained artifact has been independently rechecked, but fresh raw-light-curve SNR derivation and MGPR are still not executed. Keep all hypotheses diagnostic only. See [Session 07](think-tank/THINK_TANK_SESSION_2026-11-12_CPVS_PRIORITY_AND_EVIDENCE_RECHECK.md).

## 2026-11-12 execution update

- PR #281 engineering CI passed on head `6490b5122ad544f785adf0f89dd045fef23a2ad9`; subsequent master-status updates require fresh CI.
- PR #283 engineering CI passed on head `4570072319254d2bde94b975664e4c593f0a325f` with 741 passed, 13 skipped, zero failures. API/persistence and scientific identity gates remain open.
- PR #284 bounded DR24 HATS API, Workbench UI and Zubercal DR20 tests passed; product integration Issue #253 remains open.
- PR #285 isolates the CPVS SNR formula and input accounting corrections on current main. Full CI is in progress; raw archives are not downloaded.
