# Incremental Analysis Contract

The incremental layer consumes persisted scientific-result history in deterministic order and uses durable checkpoints to make restarts safe.

## Cursor semantics

Results are ordered by:

1. created_at ascending;
2. result_id ascending.

A checkpoint stores both values. The pair is the cursor, so results sharing the same timestamp cannot be skipped.

## Processing contract

1. read the current checkpoint;
2. read the next bounded batch;
3. process each result downstream;
4. acknowledge a result only after successful downstream processing.

The checkpoint never advances backwards.

## Persistence

Checkpoints are stored in a dedicated SQLite database and are independent from the scientific-result database. This keeps analysis history immutable while allowing multiple independent consumers to maintain separate stream positions.

## Deduplication

The cursor prevents replay of acknowledged results. If downstream processing fails before acknowledgement, the result remains available for retry.

## Scope

This is the deterministic history-consumption foundation for continuous analysis. External observation polling, scheduling, backpressure, and multi-worker coordination can build on this contract without changing scientific-result persistence.
