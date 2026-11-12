# ZTF Classifier — Master Defect and Risk Register

**Snapshot:** 2026-11-12  
**Authority:** Linked to `THINK_TANK_MASTER_REVIEW_2026-11-12.md` and the dated project master status.  
**Important:** Entries are a mixture of verified blockers, unresolved scientific questions, and acceptance risks. They are not all confirmed software bugs. A defect is confirmed only when code path, reproducible condition and failing evidence are recorded.

## Status definitions

- **OPEN / BLOCKED:** Required evidence or acceptance is missing.
- **IN PROGRESS:** Work exists but acceptance is incomplete.
- **DESIGN ONLY:** Architecture exists; production implementation does not.
- **NOT VERIFIED:** No current evidence of acceptance.
- **DEFERRED:** Intentionally outside the current milestone.
- **CLOSED:** Only after evidence and regression coverage are accepted.

## Register

| ID | Risk / defect area | Severity | Current evidence and status | Required closure evidence | Tracker |
|---|---|---|---|---|---|
| ZTF-001 | Astrophysical source identity across multiple OIDs | Critical / P0 | ZTF OID is not guaranteed to equal one physical source. BTS/DR24 and Zubercal probes show multiplicity and ambiguity. **OPEN** | Versioned identity contract; confirmed/ambiguous/unmatched/rejected/superseded states; epoch/uncertainty-aware association; reversible lineage; pinned regression samples. | #249, #253 |
| ZTF-002 | DR24 source-backed validation and normalization | Critical / P0 | Raw DR24 adapter and API exist; standard ObservationService remains ALeRCE-backed. HMJD and native photometry must not be silently mapped. **OPEN** | Explicit DR24 selection; time/photometry/QC contract; pinned live-source parity; raw-to-normalized traceability. | #253 |
| ZTF-003 | Multi-OID source grouping and model readiness | Critical / P0 | Multi-OID retrieval exists; current 30-OID demo is not 30 confirmed physical sources. **OPEN** | Source-level grouping evidence; filter/field/rcid preservation; validated multi-band association; model-ready lightcurve contract. | #158, #253, #249 |
| ZTF-004 | Benchmark scale and label independence | High | Frozen 150-object/15-class ALeRCE benchmark is useful as baseline, not population-representative ground truth. **OPEN research limitation** | Independent labels or carefully defined external reference; object/source-level splits; temporal/external validation; class coverage and bias report. | #158 |
| ZTF-005 | StarEmbed train/test source overlap | Critical | Prior review reported duplicate sourceid and source overlap across train/test. Independent benchmark status is not accepted. **OPEN** | Full identity and duplicate audit; group-aware split reconstruction; leakage tests; independent source-backed evaluation. | [Issue #210](https://github.com/saeed92m/ztf-classifier/issues/210) / PR #211 |
| ZTF-006 | CPVS 11,602 candidate-only membership discrepancy | P0-R / Scientific research blocker | Retained artifact independently rechecked 2026-11-12; historical counts remain parent 781,602; reference 730,184; candidate 741,786; candidate-only 11,602; published-only 0. Root cause unproven. **OPEN / P0 RESEARCH / NOT A PRODUCT GATE** | Fresh current-main derivation; hash-pinned inputs; full object-level provenance; fixed 100/1,000 samples; all-formula raw SNR diagnostics; MGPR; independent root cause. | #170, #180; TT-2026-11-12-07 |
| ZTF-007 | Fixed taxonomy and unknown-class handling | High | Frozen 15-class taxonomy is protected; long-term transient science may need versioned expansion. **DESIGN REQUIRED** | Taxonomy versioning, unknown/abstain semantics, migration and independent label validation. | #158 |
| ZTF-008 | Independent scientific anomaly engine | High | Existing OOD and classification outputs do not constitute a validated scientific anomaly detector. **FUTURE DESIGN** | Separate scientific question, features, controls, false-positive analysis, astrophysical review and benchmark. | Roadmap |
| ZTF-009 | Generalization to the wider ZTF population | Critical | 150-object benchmark and bounded demos do not establish population-wide performance. **OPEN** | Temporal and external validation on pinned, representative data; selection-bias analysis; calibrated performance intervals. | #158 |
| ZTF-010 | OOD, anomaly, novelty and discovery conflation | High | Contracts and docs distinguish them; implementation/UX must preserve the distinction. **IN PROGRESS** | Separate output schemas, independent validation and UI labels; no combined confidence score. | #279, #280 |
| ZTF-011 | Clean-machine installation | High | v1.0.1 release exists; complete current Windows/macOS/Linux clean-install acceptance is not established. **NOT VERIFIED** | Signed installers/packages; clean VM tests; offline/online behavior; rollback and troubleshooting evidence. | #158 |
| ZTF-012 | CPU/RAM/performance envelope | High | CPU-first target; comprehensive representative workload benchmark not established. **NOT VERIFIED** | Reproducible CPU/RAM/time benchmark on supported hardware and defined dataset sizes. | #158 |
| ZTF-013 | Job/checkpoint/recovery reliability | Medium | Job persistence and checkpoint components exist; complete crash/retry/lease/recovery acceptance needs evidence. **NOT VERIFIED** | Failure-injection tests, idempotency, retry/lease expiry, durable result and restart tests. | Product backlog |
| ZTF-014 | Production artifact integrity and secure model loading | High / BLOCKED | Frozen schema-1.0 production artifact not found in accessible repo/tag tree/release/CI/Dropbox; prior local WSL audit reported production path absent. Seven production inference tests skipped in CI. **OPEN** | Recover original artifact; independent trusted hash; manifest/provenance; secure loading; read-only audit; inference regression tests. | #282 |
| ZTF-015 | Cross-platform compatibility | High | Cross-platform product goal exists; full clean-machine OS matrix is not verified. **NOT VERIFIED** | Windows, macOS and Linux clean install, execution, file-path, permissions and uninstall/upgrade tests. | #158 |
| ZTF-016 | Documentation-to-code parity | Medium | 2026-11-12 convergence branch updates canonical docs; PR #281 is not merged. **IN PROGRESS** | Current-head CI, human review, authorized merge, post-merge link and version check. | #281 |
| ZTF-017 | Data licensing and provenance | High | Multiple external sources and proposed future survey integrations; complete license/redistribution matrix not established. **OPEN** | Source-by-source terms, attribution, redistribution limits, retention, provenance and release compliance. | Product/security backlog |
| ZTF-018 | Scientific discovery acceptance framework | Critical | Discovery ranking and anomaly vision is proposed; no complete independent scientific discovery gate is accepted. **DESIGN REQUIRED** | Explicit hypothesis, candidate selection, controls, false-positive rate, independent follow-up/reference, reproducibility and human review. | Roadmap |

## CPVS sub-register

The CPVS discrepancy is P0 for scientific research, but remains separate from the DR24/Park product critical path:
- `C` candidate set: 741,786.
- `P` published reference: 730,184.
- `C - P`: 11,602.
- `P - C`: 0.
- Historical four-field diagnostic `F`: 730,239.
- Corrected intersection: `C ∩ F = 730,184`.
- `F - C = 55`.
- The old policy file contained an inconsistent `C ∩ F = 730,239` line; the 2026-11-11 correction supersedes it.
- Historical `Ng >= 11 AND Nr >= 11` diagnostic removed 11,557 candidates and left 45, but is not an accepted membership rule.
- Direct MGPR testing remains outstanding.
- Missing raw data remains UNKNOWN, not SNR FAIL.

Do not change production selectors, thresholds, model or benchmark to reproduce a published count.

## Immediate priority order

1. **P0 Source identity + DR24 application contract:** minimum identity/association semantics must be implemented with no silent OID merging or ALeRCE fallback.
2. **P0 Frozen artifact recovery:** #282; do not rebuild or substitute.
3. **P0 Park MVP acceptance:** #158/#253; pinned 5–10 confirmed-source E2E, then 30–50-source demo with source identity evidence.
4. **P1 Independent benchmark/leakage:** StarEmbed and temporal/external evaluation.
5. **P0-R CPVS scientific research:** #170/#180; artifact recheck completed, but fresh raw SNR, fixed-sample raw coverage, MGPR and root-cause analysis remain outstanding. This is separate from the Park product critical path.
6. **P1 Desktop, reliability, security and cross-platform acceptance.**
7. **Future discovery engines and CIN:** only after their scientific and governance gates are defined.

## Change control

Every register update must include:
- exact source and version;
- date and commit SHA;
- reproducible command or experiment;
- input/output counts;
- hashes;
- result and limitation;
- regression test;
- disposition and approver.

Never close a blocker because a document was updated, a test was skipped, a count matches, or a workflow is green.


## 5. Think Tank Session 05 — source identity contract and current evidence

[Session 05](think-tank/THINK_TANK_SESSION_2026-11-12_SOURCE_IDENTITY_CONTRACT_REVIEW.md) reviewed Draft PR #283 with a focused 8-role panel and independent Red Team pass. The contract now requires exact evidence coverage for each declared survey-object/candidate-source pair and a no-candidate evidence record for every declared survey object in an unmatched decision.

The branch has 34 focused test functions. On the latest inspected head `90b6026e62e41bdff4d33c251ec2f0e1cbbb7ba9`, the full Test Suite passed 736 tests, skipped 13, and had zero failures and 9 warnings. Runtime Smoke, format, lint and lifecycle checks passed. Package build was still in progress; source-backed scientific jobs were skipped. The contract does not implement matching, persist identity decisions or prove astrophysical identity. Keep ZTF-001 OPEN until API/persistence compatibility and independent adjudicated association validation pass.


## Think Tank Session 07 — CPVS priority and evidence recheck

The retained artifact recheck independently confirmed the historical set arithmetic and sample strata. It did not derive the candidate set afresh from raw photometry. The CPVS issue remains open and is P0 for research, but not a Park MVP/release gate. See [Session 07](think-tank/THINK_TANK_SESSION_2026-11-12_CPVS_PRIORITY_AND_EVIDENCE_RECHECK.md).