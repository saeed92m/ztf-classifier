# Supabase Assessment and Architecture Decision

**Status:** Optional future integration only — not adopted  
**Reviewed:** 2026-10-12  
**Scope:** ZTF Classifier

## Decision summary

Supabase is not a fix for scientific validation, data reconstruction, model quality, or the CPVS membership discrepancy. Keep the scientific pipeline, feature contracts, frozen baseline, model artifacts, taxonomy, benchmark provenance, and CPU-heavy processing independent of any backend vendor.

The connected Supabase account currently lists no projects. No project or production data was created, uploaded, or changed.

## Possible narrow use cases

If a demonstrated product requirement emerges, Supabase could be evaluated for account metadata, authorization-backed user workspaces, analysis-job metadata, links to durable reports, or small user-uploaded artifacts. Keep heavy jobs in the existing worker/runtime architecture. Do not run long scientific workloads in Edge Functions or move full light curves/large scientific datasets into managed object storage without a cost, provenance, and retention review.

## Non-negotiable scientific safeguards

- Preserve the immutable v0.2.0 scientific baseline, 15-class order, 42-feature schema, model artifacts, and benchmark/reproducibility contract.
- ALeRCE labels are reference labels, not independent ground truth.
- Keep data manifests, source identifiers, hashes, taxonomy/schema versions, splits, and provenance with every benchmark/result.
- Treat the CPVS row/membership reconstruction discrepancy as a scientific input/selection-semantics issue; resolve it with source-backed evidence and deterministic membership rules, not a database migration.
- Do not introduce Supabase as a required dependency for CLI operation, local analysis, tests, or scientific reproducibility.

## Gate for a future pilot

Require a concrete user-facing use case, architecture/cost comparison, threat model, RLS/authorization review, data-retention decision, tested export/backup and deletion paths, and tests proving the scientific pipeline runs unchanged with the integration absent.

## Changelog

- 2026-10-12: Added initial suitability assessment; no application, model, dataset, or infrastructure changes.
