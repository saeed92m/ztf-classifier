# CPVS fixed 100/1,000-object sample reproduction — 2026-11-04

## Result

The retained CPVS reconciliation artifact was independently inspected and its deterministic sample-selection function was rerun against the retained Table 2 parent, Table 4 crosswalk, candidate-only IDs, and 55 four-field-only controls. Both sample files were reproduced exactly, including row order and stratum assignment.

Source workflow: https://github.com/saeed92m/ztf-classifier/actions/runs/41367972395
Artifact: `cpvs-raw-cds-reconciliation`, ID `13108147605`.

## Reproduction contract

- Seed: `ztf-cpvs-fixed-object-sample-v2`.
- Method: SHA-256 rank within five explicit membership/diagnostic strata.
- The sample deliberately oversamples discrepancy strata. It is not a prevalence estimator.
- Parent strata: reference_candidate 730,184; candidate_only 11,602; four_field_only 55; reference_only 0; parent_neither 39,761.

## Verified samples

| Sample | Rows | Unique IDs | Reference members | Candidate-only | Four-field-only | Parent-neither | SHA-256 |
|---:|---:|---:|---:|---:|---:|---:|---|
| 100 | 100 | 100 | 50 | 25 | 10 | 15 | `baf94d168b59b682d113015c8ab15a1d2e6ec414cb82e29875a13358f0e5b25b` |
| 1,000 | 1,000 | 1,000 | 500 | 250 | 55 | 195 | `0a713379eb274d380f7a399d4a719cd3572113d6dc5184442124f8a9e59ed340` |

Both samples contain 50% reference members and 50% nonmembers by design. All sampled IDs map to the Table 2 parent. The 1,000-object sample includes all 55 four-field-only controls.

## Scope and limitations

This verifies deterministic sample construction and retained-file integrity. It does not verify the source archive's complete row-level photometry, establish an unbiased prevalence estimate, explain the 11,602 candidate-only objects, or prove the publisher's selection rule. CPVS scientific membership remains unresolved.
