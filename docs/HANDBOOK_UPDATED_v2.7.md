# ZTF Classifier — Project Continuity Handbook v2.7

Status date: 2026-10-07
Software release: v1.0.0
Scientific baseline: v0.2.0 (immutable)
Production model: baseline_v0.2

## Current state
v1.0.0 is published and immutable. Scientific Validation, CI, CodeQL, release asset verification, and publication gates passed.

The project is now in Platform Expansion: documentation alignment, user-facing workflows, independent scientific benchmarking, and controlled discovery-platform expansion.

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

## Next work
1. Complete documentation alignment.
2. Publish canonical installation, quick-start, user, methodology, and troubleshooting documentation.
3. Add canonical architecture and roadmap entry points.
4. Perform clean-room/replay and user-path verification.
5. Establish independent labeled/cross-match scientific validation evidence.
6. Expand discovery workflows only where contracts and evidence are ready.

## Completion definition
v1.0.0 is complete as a published software milestone. The broader scientific/product platform is not declared scientifically complete merely because v1.0.0 is published.

Every meaningful change must update affected documentation, cumulative-learning records, failure-prevention knowledge, roadmap status, and release notes when release behavior changes.

Current status: v1.0.0 Released / Platform Expansion Active.
