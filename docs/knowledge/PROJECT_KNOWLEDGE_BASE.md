# Project Knowledge Base

This is the operational memory layer for ZTF Classifier. It carries only knowledge classified by evidence status and intended to influence later engineering, scientific validation, testing, performance, and release decisions.

## Knowledge status

Every finding uses one of: FACT, VERIFIED, SUPPORTED, HYPOTHESIS, ASSUMPTION, UNRESOLVED, REJECTED.

Only FACT, VERIFIED, and SUPPORTED findings may become normative baseline rules without explicit qualification. Unverified knowledge must not silently propagate as fact.

## Cumulative-learning rule

Every implementation cycle consumes validated prior knowledge, records its inherited baseline, measures relevant change, extracts new knowledge, and carries that knowledge into the next cycle. A stage is never isolated from earlier stages.

## Current verified knowledge

- v0.2.0 is an immutable scientific baseline and must never be rewritten. — VERIFIED
- Scientific Validation & External Benchmarking is a permanent product-level release gate. — VERIFIED
- Ground truth is distinct from independent classifier/reference agreement; ALeRCE is reference evidence, not universal ground truth. — VERIFIED
- Large benchmark datasets stay outside Git; manifests, checksums, contracts, configurations, and reports are versioned. — VERIFIED
- Generic leakage checks that cannot be established are NOT_EXECUTED and block scientific acceptance. — VERIFIED
- Historical ALeRCE raw-cache reproduction is currently blocked by external-data drift; frozen assertions must not be weakened. — VERIFIED / UNRESOLVED for completion
- Meaningful PRs must carry a validated machine-readable cumulative cycle record; CI must reject changes that bypass this evidence. — VERIFIED
- The cumulative lifecycle gate itself must be validated as executable CI infrastructure; shell expansion and lifecycle-state errors are process regressions, not reasons to bypass the gate. — VERIFIED (AD-CI-008)
- A lifecycle cycle record may remain BLOCKED during review, but an accepted merged cycle must end with regression PASS and no open blockers. — VERIFIED (AD-CI-008)

## Addition rule

1. Identify evidence and status.
2. Record finding and scope.
3. Record failure/root cause when applicable.
4. Encode prevention as a test, invariant, contract, benchmark, or rule when possible.
5. Link the knowledge to the cumulative ledger and affected roadmap/architecture item.
6. Carry the knowledge into the next implementation cycle.


## Frozen historical-reference knowledge — 2026-10-04

- ALeRCE Zenodo **4279623** is the immutable historical reference for the 2020-06-09 classifier/features/output state. — VERIFIED
- Live ALeRCE API/TAP is a mutable current-source drift/reference lane and must not be substituted for the frozen historical snapshot. — VERIFIED
- ZTF CPVS parent population is **781,602** from Zenodo **3886372**. — VERIFIED
- Published CPVS quality-selected membership is **730,184** from Zenodo **5764899**. — VERIFIED
- Published 730,184 membership is the historical membership benchmark; current-source reconstruction is diagnostic only. — VERIFIED
- Archive acquisition must validate published checksums and emit SHA-256/member evidence before benchmark execution. — VERIFIED
- Public ecosystem review supports explicit preprocessing/feature lineage, versioned frozen data releases, and source-specific feature mappings. — SUPPORTED
- Cross-match/catalog context, explainability, human review, and multimodal/image readiness are roadmap capabilities; they are not reasons to add unnecessary GPU infrastructure to the current release. — SUPPORTED
- Ground truth, reference predictions, classification uncertainty, OOD, and scientific anomaly remain separate semantic layers. — VERIFIED

### New permanent prevention rules

1. Never reconstruct a historical published benchmark solely from today's mutable API/source if an immutable publisher snapshot exists.
2. Never tune a scientific selection predicate to reproduce a published row count.
3. Never allow a reference-system prediction to satisfy an independent-ground-truth requirement.
4. Every immutable external archive used for release validation must be hash-verified and provenance-recorded.


## AOIC and CIN architecture knowledge — 2026-11-03

- Canonical CIN source ZTF-CIN-ARCH-001 v1.0.0 has been read in full and translated into a proposed repository workstream. — VERIFIED (source review)
- CIN is an optional, logically independent human-in-the-loop annotation subsystem; it must not be required for local ZTF analysis, inference, benchmark evaluation or reporting. — PROPOSED
- Human contributions, QC-approved responses, aggregates, expert adjudications and research-ready annotations are separate evidence types. — PROPOSED
- Community consensus is not ground truth; novelty is not discovery; human annotations do not automatically retrain production models. — PROPOSED
- Active learning must retain random audits and representative samples to measure selection bias. — PROPOSED
- AOIC canonical identity is a separate proposed dependency. CIN must preserve original survey/catalog identifiers and unresolved identity state until AOIC is validated. — PROPOSED
- The first CIN pilot should be controlled LC-01 light-curve assessment; no fixed sample size is set before feasibility and statistical-power review. — PROPOSED
- The current repository has reusable observation, catalog-context, discovery, human-review, API, Workbench and model-provenance boundaries, but no verified end-to-end CIN task/contribution/consensus pipeline. — SUPPORTED at assessment base 764ed5d9dcf43693f5c2e5a278afe326b432d578
- CIN documentation and planning do not increase the existing platform readiness estimate or scientific acceptance status. — VERIFIED (scope rule)

Canonical documents: docs/architecture/COSMIC_INTELLIGENCE_NETWORK_v1.0.0.md; docs/CIN_INTEGRATION_ASSESSMENT_2026-11-03.md; docs/api/CIN_DATA_CONTRACTS_v0.1.md; docs/research/CIN_LC01_PILOT_PROTOCOL_v0.1.md; docs/roadmap/CIN_IMPLEMENTATION_ROADMAP.md. Tracking: Issue #251.
