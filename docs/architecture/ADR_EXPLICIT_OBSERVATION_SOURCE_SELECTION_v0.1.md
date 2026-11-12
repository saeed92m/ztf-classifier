# ADR — Explicit Observation Source Selection v0.1

**Status:** PROPOSED — design accepted for further review; implementation blocked  
**Date:** 2026-11-12  
**Issues:** #158, #249, #253  
**Related review:** [Think Tank Session 03](../think-tank/THINK_TANK_SESSION_2026-11-12_EXPLICIT_SOURCE_SELECTION.md)

## Context

The current application observation path uses ALeRCE. `ObservationService.get_observations()` acquires ALeRCE detections and normalizes them into the existing `Observation` domain record. The standard source-backed analysis executor calls this method before feature generation and model inference.

DR24 HATS has a separate raw-native adapter and API. It preserves HMJD, native photometry, color coefficient, catflags and OID partition metadata. It does not normalize, group OIDs or run inference.

Zubercal DR20 has a separate adapter. It returns PS1-matched photometry with MJD(TDB), scaled magnitude errors, PS1 identifiers and ambiguity metadata. It is not equivalent to DR24 HATS.

The current analysis request and persistent job record do not contain an explicit source identifier. The existing normalized observation record does not preserve the full native semantics of both DR24 and Zubercal.

The Park dossier and the repository's proposed source architecture do not yet have a confirmed primary-product decision.

## Decision proposed

1. Every new acquisition operation must explicitly identify one source product and contract version.
2. Keep three separate source identifiers:
   - `ALERCE_DETECTIONS`
   - `ZTF_DR24_HATS_NATIVE`
   - `ZTF_ZUBERCAL_DR20_NATIVE`
3. Keep source-specific request and result schemas. Do not convert native records into a universal payload that hides time, units, flags, identifiers or calibration semantics.
4. Preserve the current v1 analysis behavior during a versioned migration.
5. Require a registered, versioned source-compatibility profile before a source can enter model analysis. The profile must identify normalization, time conversion, photometry/error mapping, QC, identity/grouping, feature schema and compatible model evidence.
6. Reject unsupported source/operation combinations with a stable error such as `source_not_model_ready`.
7. Never fall back to another source when a selected source fails or returns no rows.
8. Persist source, source release, contract version, query, requested IDs and provenance hashes in any future analysis job/run manifest.
9. Keep `AD-DATA-001` proposed until the approved Park dossier is reconciled.

## Consequences

### Positive

- Users and reports can identify the actual data product used.
- Source failures cannot silently change the data source.
- Native time, photometry, flags and identifiers remain traceable.
- The model path cannot silently consume data that has not passed compatibility gates.
- Existing v1 behavior can remain compatible during staged migration.

### Costs and limitations

- Source-specific schemas and adapters require more tests.
- Job persistence may need an additive migration.
- DR24 and Zubercal remain native-data exploration streams until normalization and feature compatibility are approved.
- No single source is declared the Park primary product by this ADR.

## Implementation gates

- Review and accept the minimum source-identity domain contract in PR #283.
- Resolve the Park source-product requirement against the approved dossier.
- Define the versioned acquisition API and discriminated native result types.
- Add adapter-selection, failure, empty-response, no-fallback and provenance tests.
- Keep source-native acquisition separate from model-analysis capability.
- Validate any normalization and model compatibility in a separate scientific cycle.
- Complete the pinned 5–10 confirmed-source API-to-Workbench acceptance workflow.

## Explicit non-goals

This ADR does not authorize:
- a default switch from ALeRCE to DR24 or Zubercal;
- automatic retry through another source;
- HMJD or MJD(TDB) conversion;
- photometric/color correction;
- QC filtering;
- cross-OID grouping or physical-source matching;
- DR24/Zubercal inference using the frozen v0.2.0 model;
- changes to model weights, features, taxonomy, benchmark membership or thresholds.

## Decision state

**PROPOSED.** The design principles are suitable for implementation planning. Runtime implementation remains blocked by the identity-contract review and the unresolved Park source-product decision.
