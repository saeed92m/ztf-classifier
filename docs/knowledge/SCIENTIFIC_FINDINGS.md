# Scientific Findings Knowledge

| ID | Status | Finding | Scope | Required propagation |
|---|---|---|---|---|
| SF-001 | VERIFIED | Benchmark success is scope-specific evidence, not proof of universal correctness. | All scientific benchmarks | Reports and release decisions |
| SF-002 | VERIFIED | ALeRCE outputs are independent reference/prediction evidence, not absolute ground truth. | ALeRCE validation | Manifest and runner semantics |
| SF-003 | VERIFIED | Current live ALeRCE data has drifted from the frozen historical raw-cache snapshot. | Issue #51 | Preserve frozen assertions; obtain immutable snapshot |
| SF-004 | SUPPORTED | Scientific improvements must be assessed across correctness, calibration, OOD, reproducibility, provenance and relevant performance, not one metric. | Model/feature/inference changes | Benchmark decision record |
| SF-005 | SUPPORTED | The latest recorded Seq-based CPVS audit reports 741,786 candidates, containing all 730,184 published members plus 11,602 candidate-only objects, with zero published-only/unmapped names; primary artifact re-audit is still required before new claims. | CPVS 781k/730k reconstruction; Issue #170; run #38121913146 | Keep exact historical selection semantics unresolved; compare source-backed reconstruction and discrepancy-reporting tracks; never tune predicates solely to match cardinality. |
| SF-006 | VERIFIED | Product validation and historical external-benchmark reproduction are distinct evidence scopes. | Scientific Validation recovery architecture / PR #124 | Product gate remains release-blocking; external exact-reproduction claims remain fail-closed. |
| SF-007 | VERIFIED | The current recovery run can complete source acquisition/integrity and product contract validation without treating unresolved CPVS membership as a product failure. | Scientific Validation run #447 / PR #124 | Keep source-backed execution evidence separate from the exact historical-reproduction claim. |
