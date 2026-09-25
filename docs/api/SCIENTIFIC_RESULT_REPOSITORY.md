# Persistent Scientific Result Repository

The production analysis pipeline has two durable boundaries:

- `JobStore` owns asynchronous job lifecycle state (`queued`, `running`, `succeeded`, `failed`) and execution leases.
- `ScientificResultStore` owns the canonical scientific payload produced by a completed analysis.

## Storage

The default SQLite path is:

`data/results/results.sqlite3`

It can be overridden with:

`ZTF_API_RESULT_STORE`

The result repository stores:
- stable `result_id`;
- source `job_id`;
- object identifier and survey;
- resolved model version;
- scientific result schema version;
- creation timestamp;
- complete JSON-safe scientific payload.

Scientific source datasets are not committed to the repository. The SQLite database is a runtime artifact and is expected to remain outside version control.

## Idempotency

A job may have at most one scientific result. Repeating a persistence operation with the same job and identical scientific payload returns the existing record. A conflicting payload for an existing job is rejected.

This makes result persistence safe across worker retries after a successful database write but before the job lifecycle transition is committed.

## Compatibility

Existing job responses retain their result field. When a scientific result repository is configured for the worker, that field becomes a compact reference containing `result_id` and `schema_version`, while `scientific_result_id` explicitly links the job to the canonical repository record.

The versioned result retrieval API is the next application boundary and must read from this repository rather than reconstructing scientific results from job state.