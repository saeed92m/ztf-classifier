# Application / Scientific Core Boundary

The application layer orchestrates user workflows without duplicating or bypassing scientific logic.

## Rules

1. Application code owns user workflow, state, orchestration, and presentation envelopes.
2. Scientific Core owns ingestion/QC, feature generation, model inference, calibration, conformal diagnostics, OOD diagnostics, and scientific validation.
3. GUI code must never directly mutate scientific artifacts.
4. Every analysis request identifies its input source and operation.
5. Results carry provenance identifying software/model/artifact/feature contracts.
6. OOD and scientific anomaly evidence remain separate channels.
7. Human review is annotation/review state, not implicit ground truth.
8. New scientific algorithms require explicit validation and versioning.

## Initial product flow

Import -> Normalize/QC -> Analyze -> Diagnose -> Present -> Export

## Packaging target

- Windows self-contained desktop distribution
- macOS application distribution
- Linux AppImage
- Advanced CLI/API access

Python remains an implementation detail for normal desktop users.
