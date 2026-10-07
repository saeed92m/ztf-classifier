# ZTF Classifier — Project Continuity Handbook v2.8

Status date: 2026-10-08
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
CPVS parent: 781,602. Published membership: 730,184. Current candidate: 741,787. Intersection: 730,184. Published-only: 0. Candidate-only: 11,604.

The exact historical reconstruction remains claim-specific UNRESOLVED. No predicate or threshold may be changed merely to force cardinality equality.

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
