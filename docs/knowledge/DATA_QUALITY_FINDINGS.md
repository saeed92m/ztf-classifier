# Data Quality Findings

| ID | Status | Finding | Prevention |
|---|---|---|---|
| DQ-001 | VERIFIED | External-source data is mutable and can drift from historical snapshots. | Record retrieval date/version/hash and retain immutable source-backed evidence. |
| DQ-002 | VERIFIED | Duplicate/object overlap can invalidate benchmark independence. | Release-blocking object and split-overlap checks. |
| DQ-003 | SUPPORTED | Preprocessing incompatibility can masquerade as model improvement or regression. | Version and validate preprocessing/input contracts with each affected benchmark. |
