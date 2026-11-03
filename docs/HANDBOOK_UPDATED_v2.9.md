# ZTF Classifier — Project Continuity Handbook v2.9

Version note: v2.9 preserves the v2.8 historical record and adds the 2026-11-03 AOIC/CIN architecture addendum. It does not claim runtime implementation.

Status date: 2026-10-11
Software release: v1.0.1
Scientific baseline: v0.2.0 (immutable)
Production model: baseline_v0.2

## Current state
v1.0.1 is published and immutable. v1.0.0 remains immutable. Scientific Validation, CI, CodeQL, release asset verification, and release publication gates passed for v1.0.1.

The project is now in Platform Expansion: documentation alignment, cross-platform desktop UX, user-facing workflows, independent scientific benchmarking, and controlled discovery-platform expansion.

## Product identity
The canonical product is an Astronomical Data Analysis & Discovery Platform, not merely a classifier.

Canonical flow:
source data → ingestion → normalization/QC → scientific feature/context layers → analysis modes → uncertainty/calibration/OOD → candidate ranking → evidence/provenance → human/scientific validation → reproducible discovery outputs

## Immutable baseline
v0.2.0 remains immutable: 150 ZTF objects, 15 ALeRCE benchmark classes, 42 frozen features, XGBoost baseline_v0.2, historical cutoff 59447.224132.

## Scientific boundary
CPVS parent: 781,602 rows. Published membership: 730,184 objects. Prior candidate and membership reports are historical diagnostics only. Source-schema review found the audit converted published ZTF names to the parent table's physical row ordinal instead of Table2's documented `Seq` value. The official CPVS ReadMe specifies Table2 `Seq` in bytes 24–29 and the lightcurve attachment's `Seq` as its running SourceID; Table2 has 781,602 rows but Seq values span 1..781,604. Therefore, the comparison in run #38095650470 (725,101 intersection, 16,686 candidate-only, 5,083 published-only) is invalid and superseded. The Seq-based heavy run [#38121913146](https://github.com/saeed92m/ztf-classifier/actions/runs/38121913146) now reports 741,786 candidates, 730,184 intersection, 11,602 candidate-only, 0 published-only, 0 duplicate published names, and 0 unmapped names. Exact reconstruction remains UNRESOLVED because the candidate set still contains 11,602 extras. Do not tune thresholds or flag policy to force cardinality equality. Source: https://cdsarc.cds.unistra.fr/viz-bin/ReadMe/J/ApJS/249/18?format=html&tex=true

## Diagnostic semantics
Classification uncertainty, calibration, conformal prediction, OOD, scientific anomaly evidence, catalog evidence, and explainability evidence remain separate channels. The current production model does not claim a scientific-anomaly detector.

## Release rule
Every future release must have curated .github/release-notes/<tag>.md before publication. Immutable releases are never mutated.

## Ecosystem review and product expansion
The 2026-10-08 ecosystem review is recorded in `docs/ECOSYSTEM_REVIEW_PRODUCT_EXPANSION_2026-10-08.md`.

New product requirements are now canonical:
- cross-platform desktop application for Windows, macOS, and Linux;
- self-contained installation without requiring Python/pip/venv/Git/terminal;
- integrated contextual Help and Troubleshooting;
- Object/Source Explorer;
- data-ingestion abstraction;
- explainable classification, uncertainty, calibration, conformal and OOD presentation;
- first-class anomaly/discovery workflows;
- provenance/evidence UI;
- cross-match framework;
- similar-object search;
- human-in-the-loop review/feedback;
- transparent discovery ranking;
- separate Real/Bogus architecture boundary;
- future ZTF Alert/AVRO and offline/batch/streaming readiness.

These additions are layered around the immutable v0.2.0 scientific baseline and must not weaken scientific validation or provenance contracts.

## Next work
1. Complete documentation alignment for v1.0.1 and the platform-expansion requirements.
2. Establish the desktop Application/Core API boundary and cross-platform packaging architecture.
3. Implement the user-facing Data Manager and Object/Source Explorer.
4. Integrate Help/Troubleshooting into the GUI.
5. Perform clean-room/replay and real user-path verification on supported operating systems.
6. Establish independent labeled/cross-match scientific validation evidence.
7. Expand discovery workflows only where contracts and evidence are ready.
8. Maintain cumulative learning, failure-prevention, roadmap, and release-note records for every meaningful change.

## Completion definition
v1.0.0 is complete as a published software milestone. The broader scientific/product platform is not declared scientifically complete merely because v1.0.0 is published.

Every meaningful change must update affected documentation, cumulative-learning records, failure-prevention knowledge, roadmap status, and release notes when release behavior changes.

Current status: v1.0.1 Released / Platform Expansion Active.


## Current scientific status — 2026-10-11

### CPVS exact reconstruction: unresolved
- Issue [#170](https://github.com/saeed92m/ztf-classifier/issues/170) remains open.
- PR [#171](https://github.com/saeed92m/ztf-classifier/pull/171) ensures missing or failed membership-audit evidence cannot default to PASS.
- PR [#173](https://github.com/saeed92m/ztf-classifier/pull/173) corrected a genuine derivation defect but did not establish exact membership.
- Source-backed run [#38005546758](https://github.com/saeed92m/ztf-classifier/actions/runs/38005546758) completed successfully at workflow level but skipped source-provenance/scientific-gate-readiness. A green workflow with a skipped required job is not scientific release readiness.
- A concrete audit defect has been identified in the comparison code: it read Table 4's catalog-internal ID and compared it directly with SourceID values derived from Table2 row order. The source ReadMe describes Table 4 ID as an internal catalog identifier, so the defensible join is by ZTF object name. PR #176 implements this name-based join and adds tests; CI and source-backed results are pending.
- The parser reads all 730,184 published names without duplicates; however, the previous mapping to row ordinals was semantically wrong. The membership comparison is not valid as a SourceID-space audit until it uses the documented CPVS Table2 Seq column.
- Heavy run [#38095650470](https://github.com/saeed92m/ztf-classifier/actions/runs/38095650470) did not produce a valid membership comparison: it mapped object names to physical parent row ordinals, not the catalog's SourceID. The 725,101 / 16,686 / 5,083 metrics are invalid and superseded. A fresh Seq-based derivation and independent membership audit is required.
- The follow-up CI found one stale test calling `read_vizier()` without its required parent path. It was fixed in commit [6416958](https://github.com/saeed92m/ztf-classifier/commit/641695863195edccb4305cb4884aac727baa30e1). Fresh CI [#38097993359](https://github.com/saeed92m/ztf-classifier/actions/runs/38097993359) and heavy Scientific Validation [#38097993346](https://github.com/saeed92m/ztf-classifier/actions/runs/38097993346) are running. Keep Issue #170 open until the mismatch is explained and required checks pass.

### Desktop product: active implementation
Issue [#158](https://github.com/saeed92m/ztf-classifier/issues/158) is the tracked target for a complete scientist-facing desktop product: dashboard, Data Manager, Object/Source Explorer, analysis/discovery workspaces, visualization, reproducible reports, integrated Help, and self-contained Windows/macOS/Linux packaging. The exit criterion is successful end-to-end use by a non-developer on a clean supported OS without Python, pip, Git, or terminal use for normal operation.

### Documentation synchronization
The documentation update is under review in [PR #175](https://github.com/saeed92m/ztf-classifier/pull/175). It adds a canonical product roadmap, updates the scientific-validation roadmap and troubleshooting, links the handbook/roadmap from README, and records this stage in the cumulative lifecycle ledger.

**Immutable constraints:** v1.0.1 remains unchanged; scientific baseline v0.2.0 remains frozen; scientific validation stays fail-closed; OOD is not represented as scientific anomaly detection.

---

# Handbook v2.9 Addendum — AOIC and Cosmic Intelligence Network

**Addendum date:** 2026-11-03  
**Canonical CIN source:** ZTF-CIN-ARCH-001 v1.0.0  
**Tracking:** [CIN Issue #251](https://github.com/saeed92m/ztf-classifier/issues/251) · [AOIC Issue #249](https://github.com/saeed92m/ztf-classifier/issues/249)

This addendum extends the product architecture. It does not rewrite the historical v2.8 record above. Current implementation and release status must still be read from the latest verified repository state and evidence-based status report.

## 1. Product architecture expansion

The long-term platform has three interoperable but separate systems:

1. **ZTF Classifier:** computational astronomical data analysis, machine learning, uncertainty, OOD, anomaly evidence and reproducible reports.
2. **AOIC:** proposed identity and cross-match layer for canonical source identity, catalog aliases, detections, observations, events and provenance.
3. **CIN:** proposed human-in-the-loop subsystem for annotation tasks, immutable contributions, quality control, consensus, expert review, active learning and research datasets.

The three systems use versioned contracts. None is an unquestionable source of truth for another. CIN must remain optional; its outage must not interrupt local analysis, inference, benchmark evaluation or reporting.

## 2. CIN status and scope

CIN is proposed, not implemented. Its canonical source is ZTF-CIN-ARCH-001 v1.0.0. The first recommended scientific pilot is LC-01 Light Curve Assessment. Later task families are IMG-01, PAIR-01, PAT-01, NOV-01 and SIM-01.

Human contributions, QC-approved responses, aggregated assessments, expert reviews and research-ready annotations are separate evidence types. Consensus is not ground truth. Novelty is not discovery. Human annotations do not trigger automatic production retraining.

## 3. AOIC dependency and subject references

CIN task records must use typed subject references. Preserve original ZTF/catalog identifiers and unresolved identity state. Do not treat a ZTF OID as a globally unique physical-object identity. A canonical object_id may be used only after AOIC identity contracts are accepted and the identity is evidence-backed.

## 4. Scientific and operational guardrails

- Preserve frozen scientific baseline v0.2.0 and immutable software release v1.0.1.
- Do not contaminate the protected benchmark with crowdsourced annotations.
- Preserve raw contributions and disagreement.
- Use independent controls and adjudication evidence.
- Hide machine predictions from ordinary participants where practical.
- Maintain random audit and representative sampling beside active learning.
- Do not use response speed as a standalone quality metric.
- Evaluate selection bias, correlated errors, uncertainty and downstream value.
- Require separate scientific validation before any model experiment or public dataset claim.
- Keep CIN optional and avoid premature microservices, paid infrastructure and broad public launch.

## 5. Current CIN deliverables

- Architecture: docs/architecture/COSMIC_INTELLIGENCE_NETWORK_v1.0.0.md
- Repository fit and gap analysis: docs/CIN_INTEGRATION_ASSESSMENT_2026-11-03.md
- Logical data/API contracts: docs/api/CIN_DATA_CONTRACTS_v0.1.md
- LC-01 pilot protocol: docs/research/CIN_LC01_PILOT_PROTOCOL_v0.1.md
- Staged implementation roadmap: docs/roadmap/CIN_IMPLEMENTATION_ROADMAP.md

These are proposed design documents. No runtime implementation or pilot execution is claimed.

## 6. Next work

Complete the detailed route, persistence, authentication, job, UI, data availability, licensing, privacy, retention and threat-model audit. Then review and approve the task/contribution contracts and pilot protocol. Implement only the smallest end-to-end LC-01 pilot after these gates. Track work in Issue #251 and maintain evidence for every proposed, designed, implemented, tested, validated and released state.

## 7. Status boundary

This addendum is architecture and planning work. It does not change the platform readiness estimate, scientific validation status, model card claims, benchmark, feature schema, taxonomy, model artifacts or release criteria. CPVS remains outside the CIN workstream.
