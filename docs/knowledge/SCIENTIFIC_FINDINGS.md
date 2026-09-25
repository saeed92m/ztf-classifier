# Scientific Findings Knowledge

| ID | Status | Finding | Scope | Required propagation |
|---|---|---|---|---|
| SF-001 | VERIFIED | Benchmark success is scope-specific evidence, not proof of universal correctness. | All scientific benchmarks | Reports and release decisions |
| SF-002 | VERIFIED | ALeRCE outputs are independent reference/prediction evidence, not absolute ground truth. | ALeRCE validation | Manifest and runner semantics |
| SF-003 | VERIFIED | Current live ALeRCE data has drifted from the frozen historical raw-cache snapshot. | Issue #51 | Preserve frozen assertions; obtain immutable snapshot |
| SF-004 | SUPPORTED | Scientific improvements must be assessed across correctness, calibration, OOD, reproducibility, provenance and relevant performance, not one metric. | Model/feature/inference changes | Benchmark decision record |
