# Scientific Findings Knowledge

| ID | Status | Finding | Scope | Required propagation |
|---|---|---|---|---|
| SF-001 | VERIFIED | Benchmark success is scope-specific evidence, not proof of universal correctness. | All scientific benchmarks | Reports and release decisions |
| SF-002 | VERIFIED | ALeRCE outputs are independent reference/prediction evidence, not absolute ground truth. | ALeRCE validation | Manifest and runner semantics |
| SF-003 | VERIFIED | Current live ALeRCE data has drifted from the frozen historical raw-cache snapshot. | Issue #51 | Preserve frozen assertions; obtain immutable snapshot |
| SF-004 | SUPPORTED | Scientific improvements must be assessed across correctness, calibration, OOD, reproducibility, provenance and relevant performance, not one metric. | Model/feature/inference changes | Benchmark decision record |
| SF-005 | VERIFIED | The current CPVS reconstruction contains all 730,184 published members but 11,604 additional candidate objects. | CPVS 781k/730k reconstruction | Treat exact historical membership as unresolved external-reproduction evidence; do not block unrelated product validation. |
| SF-006 | VERIFIED | Product validation and historical external-benchmark reproduction are distinct evidence scopes. | Scientific Validation recovery architecture / PR #124 | Product gate remains release-blocking; external exact-reproduction claims remain fail-closed. |
