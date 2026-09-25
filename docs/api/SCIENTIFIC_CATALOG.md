# Scientific Catalog Contract

## Purpose

The scientific catalog is a query/export boundary over the canonical ScientificResultStore. It does not execute inference and does not create alternate scientific records.

## Query

GET /v1/catalog/results

Supported filters:

- oid
- survey
- model_version
- created_after
- created_before
- limit (1–1000)
- offset (>=0)

Results are ordered deterministically by created_at DESC, result_id DESC.

The response contains:

- items: durable scientific-result records;
- total: total matching rows;
- limit / offset;
- has_next.

## Export

GET /v1/catalog/results.csv returns a bounded CSV page using the same filters and ordering. The CSV contains durable result metadata plus a canonical JSON representation of the persisted payload.

Catalog queries and exports are read-only with respect to scientific history.

## Boundary

The catalog is deliberately layered:

ScientificResultStore -> ScientificCatalogService -> API/UI

This prevents the Workbench or future reporting code from querying SQLite directly or duplicating scientific persistence rules.

## Versioning

The catalog exposes the existing durable-result schema version. Changes to result semantics require a new scientific result schema contract rather than silent reinterpretation of historical records.
