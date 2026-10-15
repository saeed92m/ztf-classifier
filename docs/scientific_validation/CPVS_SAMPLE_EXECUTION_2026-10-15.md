# CPVS deterministic sample and full-vs-batch execution record

Date: 2026-10-15
Purpose: execute the source-backed scientific-validation workflow against the current CPVS sampling and full-vs-batch audit implementation.

## Required interpretation

- The published CPVS membership is a comparison reference, not independent astrophysical ground truth.
- The historical 11,602 candidate-only IDs remain unresolved until a reproducible cause is established.
- Do not alter selection thresholds, hardcode discrepant IDs, or change frozen release artifacts to force agreement.
- Preserve parent SourceID identity across full-catalog and batch processing.
- Record the workflow run ID, commit SHA, source archive checksums, deterministic 100/1,000 sample manifests, object-level comparison outputs, and all disagreements.
- A skipped heavy job, green lightweight CI, or count equality alone is not proof of scientific validity.

## Acceptance checks

1. Parent population is verified against the expected 781,602 unique SourceIDs.
2. Published reference membership and candidate membership are compared by complete object ID.
3. The 100-object diagnostic and deterministic 1,000-object stratified sample include both reference members and non-members.
4. Full-vs-batch decisions cover every parent SourceID and produce either exact agreement or a complete discrepancy list.
5. Output manifests contain reproducible seeds/configuration, code revision, source hashes, and explicit reference-relative FP/FN counts.
6. If execution fails or required evidence is missing, CPVS exact reconstruction remains UNRESOLVED.

This file is an execution record template, not a claim that the run has passed.