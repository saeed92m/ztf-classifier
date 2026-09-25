# Persistent Analysis Job Worker

The API persists object-analysis requests as durable SQLite jobs. The worker layer now consumes those jobs without coupling queue state to the scientific execution implementation.

## Contract

- queued jobs are claimed atomically in creation order.
- a claimed job becomes running before execution starts.
- a successful executor result is persisted as succeeded.
- executor exceptions are converted to a stable analysis_job_failed error and persisted as failed.
- non-dictionary executor results are rejected as analysis_job_invalid_result.
- the worker does not expose exception text through the job API.
- drain(max_jobs=...) provides bounded batch processing for a future scheduler or service process.

## Execution boundary

AnalysisJobWorker accepts an injected callable:

executor(JobRecord) -> dict

This deliberately keeps persistence/orchestration separate from the scientific analysis implementation. The next integration step can bind this executor to the existing source-backed object-analysis workflow without changing the public jobs API contracts.

## Concurrency

SQLite BEGIN IMMEDIATE is used during queue claiming. The state transition from queued to running is conditional, so multiple worker processes cannot claim the same queued record through the store API.

## Validation

The worker tests cover:

- oldest-job claiming;
- successful result persistence;
- executor failure isolation;
- invalid executor result handling;
- draining multiple jobs.
