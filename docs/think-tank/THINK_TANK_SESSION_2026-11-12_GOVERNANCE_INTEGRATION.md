# Think Tank Session 06 — Project Source Integration and Governance Traceability

**Session ID:** TT-2026-11-12-06  
**Date:** 2026-11-12  
**Scope:** Connect the original project Think Tank sources, project conversations, GitHub session records, PR controls and Notion Knowledge Base  
**Review form:** All 16 simulated specialist seats plus an independent Red Team pass  
**Status:** Governance design approved; PR #281 CI remains in progress  
**Protected scientific baseline:** v0.2.0 unchanged  
**Software baseline:** v1.0.1 unchanged

> This is a simulated 16-seat review. It does not claim that 16 external human experts attended.

## 1. Objective

The Project Owner requested that all current technical work and prior decisions be explicitly referred to the same Think Tank already defined in the project's chats and supplied Project Sources.

The goal is to turn those references into one durable operating system across:

- original Project Source files;
- named project chats;
- version-controlled charter and session records;
- GitHub PR templates and review comments;
- Notion Knowledge Base and current status page.

The purpose is traceability. It is not to create a new Think Tank or replace its original membership and method.

## 2. Sources and records inspected

### Original Project Sources

- `تعیین اعضای اتاق فکر.txt` — both supplied copies.
- `تایید سیاست همگرایی پروژه.txt`.
- `Branch · Branch · Branch · Branch · گزارش وضعیت پروژه (1) (6) (14) (1).txt`.
- `ZTF CLASSIFIER — COSMIC INTELLIGENCE NETWORK.txt`.
- `ایده داده‌سازی جمعی.txt`.
- `ارائه پارک علم و فناوری نسخه نهایی.pdf`.
- `سند پروژه نسخه نهایی.pdf`.

### Project conversations

- `تعیین اعضای اتاق فکر`.
- `ایده داده‌سازی جمعی`.
- `ZTF - 01`.
- `Continue The Job`.
- Current status and continuation conversations.

Conversation titles are context references. They do not prove that an implementation or test completed.

### GitHub and Notion records

- [16-Expert Think Tank Master Review](../THINK_TANK_MASTER_REVIEW_2026-11-12.md).
- [Think Tank Charter](CHARTER.md).
- [Session Register](SESSION_REGISTER.md).
- [Project Source Index](../../sources/think_tank/PROJECT_SOURCE_INDEX.md).
- Master Defect Register, Master Execution Roadmap and Open PR Triage.
- PR #281 — governance and documentation convergence.
- PR #283 — minimum source identity contract.
- Notion Project Knowledge Base, Unified Project Baseline and the newly created Think Tank Charter & Session Register page.

## 3. Findings from the 16 specialist seats

| Seat | Finding | Governance requirement |
|---|---|---|
| 01 Chief Scientist / PI | Review governance must protect scientific claims from promotion without evidence. | Separate scientific validation from engineering test status. |
| 02 ZTF Survey Specialist | Data-source decisions depend on original survey products and release semantics. | Preserve original source references and exact data revisions. |
| 03 Time-Domain Astrophysicist | Source identity and physical interpretation need explicit evidence. | Never infer physical identity from an OID or a discussion summary. |
| 04 Statistics / Time-Series Specialist | Historical counts and sample metrics can be misread when dates and denominators are lost. | Store exact denominators, hashes, sample rules and unknown states. |
| 05 Astroinformatics / Big Data | Source files, data artifacts and derived reports need stable provenance. | Maintain a source index with clear authority and limits. |
| 06 Cross-Match / Source Identity | Discussions about OID grouping can become unsafe if decisions are not linked to the identity contract. | Link AOIC work to its exact session, issue, PR and evidence. |
| 07 AI / ML Scientist | A project source or session must not silently change the frozen model baseline. | Protect v0.2.0, 42 features, taxonomy and benchmark. |
| 08 Validation / Benchmark Specialist | A green CI workflow can still have skipped scientific evidence jobs. | Report engineering and scientific status separately. |
| 09 Software Architect | The original 12-stage process must be connected to current PR and architecture workflows. | Add stable session IDs and charter stages to material changes. |
| 10 Backend / Platform Engineer | The project needs an actionable change trail from requirement to implementation. | Link issue, PR, session, exact commit and tests. |
| 11 MLOps / Security | Broad source access and duplicated instructions can create security and configuration drift. | Use a canonical index, least privilege and no secret duplication. |
| 12 QA / Reliability | Test corrections must remain linked to the session that found the defect. | Record root cause, regression test and current-head result. |
| 13 Scientific UX/UI | The Think Tank must be easy to find from the project knowledge hub. | Add one Notion entry point and preserve historical knowledge pages. |
| 14 Product / Commercialization | Governance must not delay the Park MVP with optional future subsystems. | Use role-to-workstream mapping; keep CIN separate and proposed. |
| 15 Scientific Documentation | The same source can have different status in historical and current records. | Use dated addenda and a controlled source precedence. |
| 16 Independent Red Team | A list of links alone does not create traceability if PRs omit the session reference. | Require session ID, roles, evidence, unresolved objections and owner approval in PR templates. |

## 4. Joint governance decisions

1. Keep the existing 16 seats and original 12-stage Master Prompt. Do not create a second role structure.
2. Keep the Founder / Project Owner as final decision authority outside the 16 seats.
3. Use the original meeting composition: 7–9 roles for decision sessions, 3–5 for specialist panels, 6–10 for brainstorming, and all 16 for major stage and release gates.
4. Assign a stable Session ID to every material review. Record the exact commit, source files, data versions, roles, evidence, disagreements and decision.
5. Material PRs must cite the Think Tank session, active seats, relevant charter stages, source references, test evidence, Red Team findings and Project Owner approval state.
6. Keep GitHub as the execution source of truth. Notion is the navigation and knowledge surface. Project chats are conversation context. Uploaded Project Sources define original policy and background.
7. Preserve the difference between recommendation, implementation, engineering tests, scientific validation and release.
8. Keep all original submitted PDFs unchanged. Use dated corrections and addenda.
9. Do not merge PR #281 or #283 as part of this governance work. They remain Draft pending their separate review and CI.
10. Do not change the scientific baseline, model, benchmark, features, taxonomy, thresholds, production artifacts or scientific acceptance gates.

## 5. Implemented governance changes

The documentation branch now contains:

- `docs/think-tank/CHARTER.md` — canonical operating protocol.
- `docs/think-tank/SESSION_REGISTER.md` — stable session IDs and role-to-workstream mapping.
- `sources/think_tank/PROJECT_SOURCE_INDEX.md` — exact names and uses of supplied Project Sources and project chats.
- `docs/think-tank/THINK_TANK_SESSION_2026-11-12_SOURCE_IDENTITY_CONTRACT_REVIEW.md` — Session 05.
- This file — Session 06.
- A mandatory Think Tank Traceability section in `.github/pull_request_template.md`.
- Cross-links from the master review, master status, defect register and roadmap.
- A Notion Think Tank page linked from the main Knowledge Base and Unified Project Baseline.

## 6. Red Team challenges

### Challenge A — duplicated source files

Two copies of the member/charter source have the same filename. The Source Index records both as retained copies but treats them as one policy source, not two independent approvals.

### Challenge B — historical status as current truth

Old project reports and Notion sections contain older commit hashes, status values and progress scores. The Source Index states that those are historical until checked against current GitHub artifacts.

### Challenge C — simulated participation

The 16 seats are simulated roles. Records must state which roles were active and must not imply human attendance. Session 05 was an 8-seat panel, not a full 16-seat session.

### Challenge D — Notion and GitHub drift

Notion pages can lag behind GitHub. The current design makes GitHub the execution authority and Notion the navigation/knowledge layer. Every important Notion update must link the exact GitHub documents and PRs.

### Challenge E — PR template compliance

Adding fields to a PR template is a process control, not proof that all future PR authors will fill them in. QA must check the fields during PR review. The template itself is in Draft PR #281 and is not on main until that PR is reviewed and merged.

## 7. Current execution evidence

### PR #281 — Think Tank governance integration

- Head: `63e3b4531afdb2997dbfb71af36acee2029362a8`.
- State: OPEN / DRAFT / UNMERGED.
- Format Check: PASS.
- Lint: PASS.
- Cumulative Lifecycle Gate: PASS.
- Test Suite: IN PROGRESS at the last check.
- CodeQL: PASS.
- Product Scope Audit: PASS.
- Scientific Validation benchmark/lifecycle contract: PASS.
- Source-backed DR24/ALeRCE, historical ALeRCE, provenance and StarEmbed jobs: SKIPPED.

No full CI PASS is claimed for this head.

### PR #283 — source identity contract

- Head: `90b6026e62e41bdff4d33c251ec2f0e1cbbb7ba9`.
- State: OPEN / DRAFT / UNMERGED.
- All eight engineering CI jobs: PASS in run `43282419204`.
- Tests: 736 passed, 13 skipped, zero failures, 9 warnings.
- CodeQL, Product Scope Audit and the Scientific Validation benchmark/lifecycle contract: PASS.
- Source-backed DR24/ALeRCE, historical ALeRCE, provenance and StarEmbed jobs: SKIPPED.

API/serialization and persistence review and independent adjudicated astrophysical identity validation remain open.

## 8. Final decision

**APPROVE THE THINK TANK SOURCE INTEGRATION AND TRACEABILITY DESIGN.**

This approval applies to the governance design and documentation changes only. It does not authorize merging PRs, changing scientific baselines, accepting the AOIC implementation, declaring CPVS resolved, approving DR24 model inference or declaring the Park MVP scientifically accepted.

The PR #281 CI and documentation review remain open. The separate scientific blockers remain open.

