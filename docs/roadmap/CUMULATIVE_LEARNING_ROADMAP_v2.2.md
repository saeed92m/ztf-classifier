# Cumulative Learning & Product Roadmap — v2.3

This roadmap combines the cumulative-learning lifecycle with the current product-unblocking direction. It does not erase domain-specific scientific-validation planning.

## 0. Current state

The project is an **Astronomical Data Analysis & Discovery Platform**. The immediate blocker has been reclassified:

- Product path: continue development and validation.
- CPVS exact 730,184-member reconstruction: external, claim-specific evidence.
- Current discrepancy: 741,788 candidate objects vs 730,184 published members; 730,184 intersection; 11,604 candidate-only.
- Do not force cardinality with unsupported thresholds.

## 1. P0 — Scientific validation recovery

**Exit criteria**
- [ ] PR #124 heavy validation completes.
- [x] Product vs external-reproduction scopes are encoded in validation logic.
- [x] CPVS unresolved state is represented explicitly.
- [x] CPVS diagnostic/audit evidence is retained.
- [x] Contract tests verify benchmark scope separation.
- [ ] Final release-gate behavior verified by a completed heavy run.
- [x] Product validation scope is separated from historical CPVS reproduction scope.
- [x] Current run #447 has passed registry/lifecycle contract validation; heavy derivation remains in progress.

## 2. P1 — Operational data platform

**Critical product principle:** the platform is source-driven. ZTF/DR24 is an operational input source, not a benchmark reconstruction exercise. Benchmark datasets validate the platform; they do not define its architecture.

**Goal:** real astronomical data enters through a deterministic, auditable pipeline.

- [ ] ZTF/DR24 source adapter
- [ ] acquisition manifests and checksums
- [ ] schema normalization
- [ ] observation/QC contract
- [ ] duplicate and invalid-observation handling
- [ ] temporal cutoff support
- [ ] provenance graph
- [ ] reproducible subset materialization
- [ ] source adapters for archive/HATS access patterns appropriate to the selected ZTF release
- [ ] source snapshot/version pinning and retrieval-date evidence

**Exit:** a pinned source subset can be acquired, normalized, validated, and replayed from its manifest.

## 3. P2 — Scientific feature engine

**Goal:** feature generation becomes a first-class extensible subsystem.

- [ ] feature-family registry
- [ ] deterministic feature computation
- [ ] missing-data semantics
- [ ] feature provenance
- [ ] quality and validity flags
- [ ] performance benchmarks
- [ ] schema/version compatibility
- [ ] extensible feature plugins beyond the historical 42-feature baseline

**Exit:** feature output is deterministic, versioned, provenance-aware, and scientifically validated.

## 4. P3 — Analysis and inference

**Goal:** move from classifier-only behavior to a general scientific analysis layer.

- [ ] model registry
- [ ] production inference service
- [ ] probability calibration
- [ ] conformal uncertainty where applicable
- [ ] OOD detection
- [ ] failure taxonomy
- [ ] reproducible result repository
- [ ] scientific report generation
- [ ] analysis job orchestration

**Exit:** an analysis request produces a versioned scientific result with diagnostics and provenance.

## 5. P4 — External scientific validation

**Goal:** establish independent evidence for scientific claims.

- [ ] StarEmbed adapter/reproducible fixture
- [ ] catalog/cross-match evidence
- [ ] ALeRCE API/TAP reference adapter using immutable evidence strategy
- [ ] pinned DR24 source-backed fixture
- [ ] leakage audits
- [ ] temporal/future-data audits
- [ ] benchmark-trained-artifact audits
- [ ] full OOD/failure suite
- [ ] CPVS exact-reproduction investigation
- [x] CPVS discrepancy classified as claim-specific external evidence; unresolved exact membership must not block unrelated product work

**CPVS rule:** unresolved historical reconstruction does not block unrelated product work, but the exact-reproduction claim remains fail-closed.

## 6. P5 — Scientific Analysis Workbench

- [ ] source/data selection
- [ ] feature selection
- [ ] model/analysis selection
- [ ] uncertainty and OOD inspection
- [ ] catalog and cross-match views
- [ ] experiment comparison
- [ ] provenance/evidence view
- [ ] exportable scientific reports

## 7. P6 — Discovery and continuous improvement

- [ ] cumulative knowledge ledger
- [ ] failure database
- [ ] benchmark lessons
- [ ] automated regression fixtures
- [ ] release evidence bundle
- [ ] performance/resource trend tracking
- [ ] feedback-to-retraining loop with leakage controls
- [ ] discovery workflows beyond predefined classification tasks

## 8. Release gates

**Gate architecture:**
- Product Scientific Gate: release-blocking for the actual platform.
- External CPVS Reproduction Gate: fail-closed only for the exact historical reproduction claim.

This separation is an architectural requirement, not a temporary CI workaround.

A release candidate must satisfy:

- product scientific gate;
- reproducibility;
- provenance completeness;
- leakage protection;
- calibration/OOD/failure validation as applicable;
- API/schema compatibility;
- security and reliability requirements;
- documented scope and limitations.

External benchmark claims must satisfy their own evidence contract and may not be promoted beyond what the source evidence supports.

## 9. Lifecycle control

Every roadmap stage uses:

AUDIT -> KNOWLEDGE -> BASELINE -> PLAN -> IMPLEMENT -> TEST -> MEASURE -> VALIDATE -> ROOT CAUSE -> LEARN -> UPDATE RULES -> REGRESSION -> ACCEPT/REVISE.

No stage starts from a conceptual clean slate when validated knowledge already exists.
