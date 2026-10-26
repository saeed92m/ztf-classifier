# Scientific Findings Knowledge

| ID | Status | Finding | Scope | Required propagation |
|---|---|---|---|---|
| SF-001 | VERIFIED | Benchmark success is scope-specific evidence, not proof of universal correctness. | All scientific benchmarks | Reports and release decisions |
| SF-002 | VERIFIED | ALeRCE outputs are independent reference/prediction evidence, not absolute ground truth. | ALeRCE validation | Manifest and runner semantics |
| SF-003 | VERIFIED | Current live ALeRCE data has drifted from the frozen historical raw-cache snapshot. | Issue #51 | Preserve frozen assertions; obtain immutable snapshot |
| SF-004 | SUPPORTED | Scientific improvements must be assessed across correctness, calibration, OOD, reproducibility, provenance and relevant performance, not one metric. | Model/feature/inference changes | Benchmark decision record |
| SF-005 | SUPPORTED | The latest source-backed CPVS run #40397098709 reports 741,788 candidates, all 730,184 published members present, 11,604 candidate-only, and zero published-only IDs; exact membership remains UNRESOLVED and the two-ID shift from run #38121913146 is unexplained. | CPVS 781k/730k reconstruction; Issue #170; run #40397098709 | Generate and audit the report from the latest immutable artifact; compare source versions/hashes and per-object provenance; never tune predicates solely to match cardinality. |
| SF-006 | VERIFIED | Product validation and historical external-benchmark reproduction are distinct evidence scopes. | Scientific Validation recovery architecture / PR #124 | Product gate remains release-blocking; external exact-reproduction claims remain fail-closed. |
| SF-007 | VERIFIED | The current recovery run can complete source acquisition/integrity and product contract validation without treating unresolved CPVS membership as a product failure. | Scientific Validation run #447 / PR #124 | Keep source-backed execution evidence separate from the exact historical-reproduction claim. |
