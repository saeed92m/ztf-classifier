# ZTF Classifier — Think Tank Session Register

**Last updated:** 2026-11-12  
**Canonical protocol:** [CHARTER.md](CHARTER.md)  
**Project Source index:** [PROJECT_SOURCE_INDEX.md](../../sources/think_tank/PROJECT_SOURCE_INDEX.md)

| Session ID | Date | Scope | Review form | Decision status | Record |
|---|---|---|---|---|---|
| TT-BASELINE-2026-11-12 | 2026-11-12 | Project-wide science, product, architecture and execution baseline. | 16 simulated specialist perspectives and independent limitations review. | Baseline recorded; no full scientific or product acceptance. | [Master Review](../THINK_TANK_MASTER_REVIEW_2026-11-12.md) |
| TT-2026-11-12-07 | 2026-11-12 | CPVS research priority, retained artifact recheck, cost boundary and diagnostic execution plan. | All 16 simulated specialist seats plus independent Red Team. | P0 scientific research reaffirmed; not a Park MVP/release gate; root cause unresolved. | [Session 07](THINK_TANK_SESSION_2026-11-12_CPVS_PRIORITY_AND_EVIDENCE_RECHECK.md) |
| TT-2026-11-12-02 | 2026-11-12 | DR24 application, AOIC identity and Park source-product conflict. | 16 simulated roles plus Red Team. | Explicit source selection and separate adapters supported as design principles; Park primary-source choice and DR24 inference blocked. | [Session 02](THINK_TANK_SESSION_2026-11-12_DR24_APPLICATION_INTEGRATION.md) |
| TT-2026-11-12-03 | 2026-11-12 | ALeRCE, DR24 HATS and Zubercal source-selection boundaries. | 16 simulated roles plus Red Team. | Design accepted for planning; runtime implementation and model compatibility blocked. | [Session 03](THINK_TANK_SESSION_2026-11-12_EXPLICIT_SOURCE_SELECTION.md) · [Proposed ADR](../architecture/ADR_EXPLICIT_OBSERVATION_SOURCE_SELECTION_v0.1.md) |
| TT-2026-11-12-04 | 2026-11-12 | CPVS 11,602 residuals, raw-SNR diagnostic, samples, r-band and Seq identity. | 16 simulated roles plus Red Team. | Diagnostic design conditionally supported; scientific cause unproven; execution remained queued in inspected evidence. | [Session 04](THINK_TANK_SESSION_2026-11-12_CPVS_MEMBERSHIP_REVIEW.md) |
| TT-2026-11-12-05 | 2026-11-12 | Minimum source-identity domain contract, pairwise OID evidence coverage and CI regression. | Focused 8-role panel plus Red Team. | Contract design supported with conditions; engineering CI passed; API/serialization and independent scientific identity validation remain open. | [Session 05](THINK_TANK_SESSION_2026-11-12_SOURCE_IDENTITY_CONTRACT_REVIEW.md) |
| TT-2026-11-12-06 | 2026-11-12 | Integrate original Think Tank Project Sources, project chats, GitHub controls and Notion entry point. | All 16 simulated specialist seats plus independent Red Team. | Governance design approved; latest-head engineering CI passed; scientific source-backed jobs skipped. | [Session 06](THINK_TANK_SESSION_2026-11-12_GOVERNANCE_INTEGRATION.md) |

## Workstream mapping

| Workstream | Required sessions | Required roles |
|---|---|---|
| DR24 application and Park MVP | TT-02, TT-03 | 01, 02, 03, 04, 06, 08, 09, 10, 11, 12, 14, 15, 16 |
| AOIC / source identity | TT-02, TT-05 | 01, 02, 03, 04, 06, 08, 09, 10, 11, 12, 16 |
| CPVS discrepancy and research priority | TT-04, TT-07 | 01, 02, 03, 04, 05, 06, 08, 09, 11, 12, 15, 16 |
| CIN / collective data generation | CIN canonical source; create a dedicated session before implementation | 01, 06, 07, 08, 10, 11, 12, 13, 14, 15, 16 |
| CI, packaging and release | Relevant subsystem session; stage/release review where required | 09, 10, 11, 12, 15, 16; all 16 for major scientific or product release gates |

| Think Tank governance and source integration | TT-2026-11-12-06 | All 16 seats plus Red Team |
| CPVS research priority and artifact evidence recheck | TT-2026-11-12-07 | All 16 seats plus Red Team |

## Rules

1. Assign a stable Session ID before recording a material decision.
2. Link the exact commit, issue, PR, data release and artifact hashes reviewed.
3. Record active seats. Do not claim all 16 participated in a focused panel.
4. Preserve disagreements and rejected proposals.
5. Separate recommendation, implementation state, engineering tests and scientific validation.
6. Link the implementation PR and regression evidence.
7. Reopen a decision when new evidence contradicts it.
8. Update this register and the master status after each material session.
