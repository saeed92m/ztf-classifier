# ZTF Classifier — Pre-Product Build Snapshot

Date: 2026-10-08
Repository: saeed92m/ztf-classifier
Default branch: main
Baseline commit captured: 839a3d8010a66b6d99b19c8f5e0b91fa51f3567c

## Purpose
Immutable checkpoint before implementation of the cross-platform public desktop product.

## Preserved scientific identity
- Immutable v0.2.0 scientific baseline remains protected.
- v1.0.1 is the current public software release.
- Scientific validation, provenance, leakage, OOD/anomaly separation, and benchmark guardrails remain mandatory.
- Final product name is intentionally deferred.

## Product direction
Astronomical Data Analysis & Discovery Platform.

Target user flow:
Download → Install → Open → Import Data → Analyze → Results → Export

Target platforms:
- Windows: self-contained installer
- macOS: .app/.dmg distribution
- Linux: AppImage baseline, optional .deb

## P0 implementation scope
1. Desktop application shell
2. Stable Application/Core API boundary
3. Data Manager / ingestion abstraction
4. Object/Source Explorer
5. Analysis and Results workflow
6. Visualization
7. Discovery/Anomaly workflow with scientific guardrails
8. Provenance/Evidence UI
9. Explainability/uncertainty/calibration/conformal/OOD presentation
10. Integrated Help and Troubleshooting
11. Cross-platform packaging and release CI

## P1
- Cross-match framework
- Similar-object search
- Human review
- Transparent discovery ranking
- Real/Bogus integration boundary
- Additional validated analysis modes

## P2
- ZTF Alert/AVRO
- Offline/batch/streaming contracts
- Follow-up integrations
- Additional validated models/features

## Non-negotiable guardrails
- v0.2.0 is immutable.
- OOD is not automatically scientific anomaly detection.
- Human feedback is not ground truth unless formally validated.
- Discovery score is prioritization, not truth.
- External data requires provenance/version/retrieval/access review.
- GUI must not bypass scientific validation or mutate scientific artifacts unsafely.

## Existing canonical product records
- docs/ECOSYSTEM_REVIEW_PRODUCT_EXPANSION_2026-10-08.md
- docs/architecture/V1_PRODUCT_ARCHITECTURE.md
- docs/knowledge/ARCHITECTURAL_DECISIONS.md
- docs/HANDBOOK_UPDATED_v2.8.md
- docs/roadmap/CUMULATIVE_LEARNING_ROADMAP_v2.2.md
- GitHub Issue #157

## Backup policy
This branch is a recovery checkpoint. Do not delete or rewrite it until the first stable product milestone is released and independently verified.
