# AOIC — Astronomical Object Identity & Cross-Match Architecture v0.1

**Status:** Proposed architecture decision; not implemented  
**Issue:** [#249](https://github.com/saeed92m/ztf-classifier/issues/249)  
**Baseline:** software v1.0.1; frozen scientific baseline v0.2.0  
**Scope:** canonical identity, catalog aliases, source association, observations/detections, and provenance

## 1. Decision summary

ZTF Classifier will define a dedicated **Astronomical Object Identity & Cross-Match (AOIC)** subsystem.

AOIC will maintain a stable internal identifier for each canonical astronomical source/entity hypothesis that the platform has sufficient evidence to track. It will preserve, not replace, identifiers assigned by ZTF and external catalogs. It will distinguish an astronomical source from a catalog row, a detection, an observation, a transient event, a dataset, and an analysis execution.

AOIC will not claim that identity matching is infallible. It will represent uncertainty and ambiguity explicitly. A missing or ambiguous match must remain missing or ambiguous until evidence supports a decision.

This document defines architecture and contracts only. It does not authorize changes to the frozen v0.2.0 scientific baseline, model artifacts, historical records, or acceptance thresholds.

## 2. Problem statement

A survey identifier is not necessarily a globally unique identifier for a physical astronomical object. A survey may partition source records by filter, field, CCD, quadrant, processing version, or another survey-specific rule. A source may also have multiple detections and observations. External catalogs may describe the same source with different identifiers, coordinate epochs, astrometric uncertainties, and resolution limits.

Therefore:

- An identifier such as a ZTF OID must be preserved as a survey/catalog identifier.
- Multiple catalog entries may refer to one canonical source.
- One catalog entry may represent an unresolved blend of multiple physical sources.
- One physical source may be represented by multiple survey records.
- A transient event is not the same entity as its host galaxy.
- Positional proximity alone does not prove identity.

AOIC provides explicit links and evidence for these relationships.

## 3. Terminology and entity boundaries

| Concept | Meaning | Identifier |
|---|---|---|
| Canonical astronomical entity/source | Internal identity record for a source or explicitly unresolved source hypothesis | `object_id` |
| Catalog | Named external or survey catalog and its access contract | `catalog_id` |
| Catalog release | Version/release of a catalog | `catalog_release_id` |
| Catalog entry / alias | A record identifier inside a catalog namespace | `catalog_entry_id` |
| Detection | A pipeline's detection of a source in an image/alert/exposure | `detection_id` |
| Observation | A measurement or observation record, including photometry | `observation_id` |
| Transient/physical event | An astrophysical event associated with a source and optionally a host | `event_id` |
| Dataset | An immutable, versioned input collection or snapshot | `dataset_id` |
| Analysis execution | One versioned execution of a scientific workflow | `analysis_id` |
| Identity decision | A versioned association, rejection, merge, split, or supersession decision | `identity_decision_id` |

### 3.1 Canonical identity is an evidence-backed record

An `object_id` identifies the platform's current canonical source/entity record. It is not a claim that the astrophysical interpretation is certainly correct or that the source is a single resolved physical body.

The record must include an entity kind and identity status. Initial kinds should include:

- `point_source`
- `extended_source`
- `transient_event_source`
- `solar_system_body`
- `unresolved_or_blended_source`
- `unknown_source`

A transient event and its host must have separate identities with an explicit relationship. A blended catalog entry must not be silently treated as a resolved single star.

### 3.2 Survey identifiers remain external aliases

An external alias is scoped by its catalog namespace and identifier. Release/version and retrieval metadata are recorded separately. Do not assume that every catalog identifier is globally unique or stable across every release.

For ZTF, preserve the original OID and all available partition/context fields. Do not reinterpret OID as a globally unique astrophysical identity until the source semantics for the relevant data product are documented and validated.

## 4. Core invariants

1. Internal IDs are opaque, stable, and independent of coordinates, names, catalog releases, or mutable attributes.
2. An internal ID is never recomputed from RA/Dec.
3. Raw source data and original identifiers are immutable.
4. Catalog aliases are preserved exactly as supplied, with namespace and release context.
5. A detection and an observation are not canonical objects.
6. A transient event is not automatically identical to its host or progenitor source.
7. Matching is evidence-based, epoch-aware, and uncertainty-aware.
8. Nearest-neighbour distance alone cannot produce a confirmed identity.
9. Ambiguous and unmatched records remain explicit states; the system must not force a match.
10. Match probability is not called calibrated unless calibration has been independently evaluated.
11. Catalog context and labels do not become ground truth by being attached to an object.
12. Every identity decision and correction has provenance and an audit trail.
13. Merge, split, and supersession operations preserve prior IDs and lineage.
14. Hashes establish byte-level integrity, not astrophysical identity correctness.
15. Existing v0.2.0 feature definitions, model artifacts, class order, benchmark, and scientific gates remain unchanged.

## 5. Logical architecture

```text
Catalog Registry ──> Catalog Adapters ──> Raw Catalog Snapshots
                                             │
ZTF Data Adapters ──> Raw Survey Records ─────┤
                                             v
                                  Normalization / QC
                                             │
                                             v
                                  Candidate Generation
                                             │
                                             v
                                   Match Assessment
                              (astrometry + uncertainty
                               + epoch + source evidence)
                                             │
                           ┌─────────────────┼─────────────────┐
                           v                 v                 v
                       Confirmed          Ambiguous         Unmatched
                           │                 │                 │
                           v                 v                 v
                    Identity Registry   Review Queue      New-source
                           │             / adjudication     candidate
                           └─────────────────┬─────────────────┘
                                             v
                                  Identity Decision Ledger
                                             │
                                             v
                                  Canonical Object Registry
                                             │
               ┌─────────────────────────────┼──────────────────────┐
               v                             v                      v
         Observations / detections      Features / models      Reports / discovery
```

The architecture separates source acquisition, candidate generation, match assessment, identity decisions, and downstream scientific analysis. A UI or model must not bypass these service boundaries.

## 6. Data contracts

The following are logical contracts, not final Python class names or a frozen database schema.

### 6.1 Canonical object record

Required fields:

- `object_id`
- `entity_kind`
- `identity_status` (for example: provisional, confirmed, disputed, superseded)
- creation timestamp
- record schema version
- current coordinate solution, if available
- coordinate reference frame
- coordinate epoch
- positional uncertainty/covariance where available
- optional proper motion, parallax, and their uncertainties
- provenance references

Coordinates are versioned measurements, not identity keys. Updated astrometry creates a new solution/version; it does not change `object_id`.

### 6.2 Catalog registry and entry

Catalog registry metadata:

- catalog namespace and human-readable name
- provider and access endpoint/adapter
- catalog release/version
- schema version
- coordinate frame and reference epoch
- supported identifier fields
- access and licensing constraints
- retrieval timestamp and query parameters
- source snapshot/response hash where practical

Catalog entry metadata:

- `catalog_entry_id`
- `catalog_id` and release reference
- exact external identifier
- original record reference or immutable snapshot location
- normalized attributes and their units
- original and normalized coordinate metadata
- provenance and content hash

### 6.3 Alias link

An alias link connects a catalog entry to an `object_id`. It records:

- link status
- identity decision reference
- matching method and algorithm version
- matching policy/configuration hash
- match evidence and probability/score, if computed
- decision timestamp and provenance

Uniqueness constraints must be based on the catalog namespace and the identifier semantics. A single external entry must not be attached to multiple active canonical identities unless an explicit blend/component relationship permits it.

### 6.4 Detection and observation

A detection references its survey record and the source/catalog entry from which it originated. An observation references its measurement context, including exposure/time, filter/band, instrument/pipeline, photometry, quality flags, and uncertainties.

A single `object_id` may link to many detections and observations. A single observation must not be counted as a new object.

### 6.5 Identity decision

Every decision stores:

- `identity_decision_id`
- decision type: link, confirm, reject, defer, merge, split, supersede, or reopen
- source catalog entries and candidate object IDs
- decision state and rationale
- evidence references
- algorithm, catalog, and policy versions
- thresholds/parameters and their configuration hash
- human reviewer reference when applicable
- timestamp and prior decision reference
- resulting object/alias relationships

Decisions are append-only. Corrections create new decisions that supersede prior decisions; they do not erase history.

## 7. Cross-match method

### 7.1 Candidate generation

Candidate generation may use spatial indexes and conservative search regions. It must account for coordinate frame, coordinate epoch, and positional uncertainty. It must not treat a fixed angular radius as universally valid for all catalogs and source classes.

### 7.2 Astrometric normalization

Where data supports it:

1. transform coordinates into a declared common reference frame;
2. propagate positions to a common epoch using proper motion;
3. propagate uncertainty, including covariance where available;
4. record assumptions and missing astrometric terms;
5. reject or flag incompatible coordinate metadata.

Do not invent proper motion, epoch, uncertainty, or coordinate-frame values when they are absent.

### 7.3 Match assessment

Assessment may combine:

- angular separation after epoch propagation;
- positional covariance and uncertainty;
- local source density and chance-coincidence probability;
- proper motion and parallax consistency;
- morphology/extended-source indicators;
- photometric/color evidence where comparable;
- time-domain behavior only when the scientific use case supports it;
- survey resolution, partition, and blending behavior.

The selected method must be documented and versioned. A Bayesian or likelihood-ratio method may be appropriate, but the exact method and thresholds must be selected and validated against representative, independently adjudicated data.

A score in [0, 1] must not be described as a probability unless calibration has been measured. Keep raw score, probability, and decision threshold as separate fields.

### 7.4 Decision states

Minimum operational states:

- `confirmed_match`: evidence meets a validated policy and no unresolved competing candidate invalidates the decision;
- `ambiguous_match`: multiple plausible candidates or insufficient evidence;
- `unmatched`: no candidate meets the policy;
- `rejected_match`: a proposed link was explicitly rejected;
- `deferred_review`: a decision requires additional data or human review.

A provisional canonical record may be created for an unmatched source record to preserve workflow continuity. Its status must remain provisional/unresolved. It must not be described as a confirmed new astrophysical object.

## 8. Merge, split, and identity lifecycle

Identity decisions can change when new evidence arrives. The system must support controlled operations:

- **Merge:** two internal records are determined to represent the same source. One record becomes the surviving canonical identity; the other remains addressable as superseded and points to the survivor.
- **Split:** one internal record is found to combine distinct sources. New identities are created and the previous record remains as a superseded historical record with explicit lineage.
- **Supersede:** a prior identity decision or source association is replaced by a newer decision.
- **Reopen:** new evidence invalidates confidence in a previous association.

No operation physically deletes prior IDs, aliases, observations, decisions, or provenance. Downstream records retain their original identity references and can resolve current lineage through an explicit mapping.

## 9. Human review

The review queue should prioritize ambiguous, conflicting, high-impact, or scientifically interesting cases. A review record must include:

- reviewer reference (or controlled pseudonymous reference);
- timestamp;
- candidates and evidence presented;
- decision and rationale;
- policy/algorithm version;
- any follow-up requirement.

Human review is evidence, not automatic ground truth. Review feedback must not silently alter benchmark labels or training data. Any later training use requires a separate versioned dataset and leakage-safe validation.

## 10. Provenance and integrity

Every input snapshot and identity decision should retain, where available:

- provider/catalog and release;
- retrieval timestamp;
- query and parameters;
- schema and normalization version;
- software commit and algorithm version;
- configuration hash;
- input/output content hashes;
- parent record references;
- execution environment;
- decision rationale and reviewer reference.

Use immutable manifests and append-only decision history. A hash can detect byte changes to a known artifact. It cannot prove that the catalog association or astrophysical interpretation is correct. A blockchain is not required for this design; an auditable, access-controlled, append-only ledger is sufficient unless a separate threat model demonstrates a need for distributed consensus.

## 11. Downstream integration

Every derived scientific record should be traceable through:

`object_id -> catalog entries / detections -> observations -> dataset snapshot -> feature set -> analysis_id -> model/artifact -> result/report`

Where an identity is unresolved, downstream results must preserve that state and avoid aggregating potentially distinct sources as one object.

The frozen v0.2.0 model contract currently uses survey OIDs in its data path. AOIC integration must be additive and versioned. Do not silently reinterpret historical OIDs or rewrite the frozen benchmark. A migration or adapter must preserve the original OID and demonstrate equivalence before any model-facing change.

## 12. Catalog onboarding strategy

Catalog support is adapter-based. Do not bulk-download every available catalog at the start.

Prioritize catalogs by scientific relevance, astrometric quality, coverage, access stability, licensing, and computational cost. An initial evaluation set should include:

- Gaia DR3 for astrometry and source context;
- Pan-STARRS DR2 for optical source context;
- SIMBAD for object names and cross-identifications;
- 2MASS for infrared source context.

This is a proposed initial set, not a claim that every catalog is a complete or independent truth source. Catalog adapters must record the exact release, access method, limits, and licensing terms. Additional domain-specific catalogs can be added when required by the analysis task.

## 13. Validation and acceptance plan

### Unit tests

- stable opaque ID creation and persistence;
- alias namespace and uniqueness rules;
- duplicate ingestion and idempotency;
- coordinate frame and epoch validation;
- proper-motion propagation and uncertainty propagation;
- candidate generation at boundaries;
- one-to-one, one-to-many, many-to-one, and blend cases;
- ambiguous and unmatched fail-closed outcomes;
- score/probability semantic validation;
- merge/split/supersession lineage;
- append-only audit history;
- provenance completeness and content-hash verification.

### Integration tests

- deterministic fixtures from at least two external catalog adapters;
- ZTF survey OIDs across filters and field/CCD/quadrant partitions;
- multiple detections/observations associated with one canonical source;
- a transient event linked separately from its host;
- duplicate and conflicting records;
- catalog/API unavailable, rate-limited, malformed, or schema-changed responses;
- repeat runs with the same inputs and configuration produce equivalent decisions.

### Scientific validation

Use a versioned, independently adjudicated sample that includes:

- isolated sources;
- crowded fields;
- high-proper-motion sources;
- extended sources;
- blends;
- sources with different coordinate epochs;
- transients and host associations;
- known unmatched and deliberately ambiguous cases.

Report precision, recall, false-association rate, missed-association rate, ambiguity rate, and calibration metrics where probability outputs are claimed. Stratify by catalog, source class, sky density, magnitude, and astrometric quality where sample size permits.

Do not use the same catalog both to create a match and as the sole independent truth for evaluating that match. Record adjudication protocol and limitations.

### Release gates

AOIC is not scientifically accepted until its declared test matrix, independent validation, provenance checks, failure handling, and documentation pass. A green unit-test workflow alone is not sufficient.

## 14. Implementation phases

| Phase | Deliverable | Exit condition |
|---|---|---|
| A0 | Architecture and terminology | ADR reviewed; no conflict with existing contracts |
| A1 | Versioned domain contracts | Schema/API contract tests pass |
| A2 | Canonical identity and alias registry | Persistence, uniqueness, idempotency, and lineage tests pass |
| A3 | Match candidate and assessment service | Epoch/uncertainty-aware deterministic tests pass |
| A4 | Initial catalog adapters | At least two versioned adapters with provenance and failure tests |
| A5 | Review and adjudication workflow | Ambiguous/unmatched cases can be reviewed without mutating raw data |
| A6 | Independent scientific validation | Predeclared metrics and adjudicated sample meet documented criteria |
| A7 | Downstream integration | Object Explorer, analysis, reports, and exports retain complete identity lineage |

## 15. Relationship to existing project contracts

- `CatalogMatch` / `CatalogContext` remain contextual cross-match evidence contracts. AOIC may extend or reference them, but must not silently redefine them.
- `ScientificCatalogService` remains a query/export service over persisted scientific results. It is not renamed or repurposed as the astronomical object registry.
- `Observation` and `ObjectObservationSummary` remain measurement-level contracts. Canonical identity linkage is an additive, versioned relation.
- `DiscoveryCandidate` should eventually reference canonical identity and event identity separately, while retaining original survey OID references.
- `ModelProvenance` remains model-artifact provenance. AOIC introduces source/catalog/identity-decision provenance; the two provenance domains are linked but not conflated.

## 16. Out of scope

- Reconstructing or resolving the CPVS publication membership discrepancy.
- Changing the v0.2.0 benchmark, 42-feature schema, model artifact, class order, or scientific acceptance criteria.
- Claiming any catalog is complete or absolute ground truth.
- Replacing raw ZTF identifiers with internal IDs.
- Bulk downloading all public astronomical catalogs.
- Requiring blockchain, GPU, or a distributed database.
- Automatically turning unknown sources into confirmed discoveries.

## 17. Open design questions

These questions must be resolved with evidence before implementation is frozen:

1. Should the canonical internal entity be named `AstronomicalObject`, `SourceEntity`, or a more general `AstronomicalEntity`? The API can still expose `object_id` for compatibility.
2. Which persistent store is appropriate for the first release, given expected scale, spatial queries, transactionality, backup, and local/offline operation?
3. Which astrometric matching method and calibration dataset are appropriate for the initial catalog pair?
4. How should unresolved blends and moving solar-system objects be represented without forcing them into the stellar-source model?
5. What is the exact semantic scope and stability of each ZTF identifier in every supported DR24 table?
6. Which catalog access methods, rate limits, and licensing terms permit reproducible use in a distributable desktop product?

## 18. Definition of done

AOIC is complete only when canonical identities, external aliases, observations, detections, events, datasets, and analysis runs have separate versioned contracts; match decisions are uncertainty-aware and auditable; ambiguous and unmatched cases remain explicit; merge/split lineage is preserved; at least two catalog adapters and ZTF source records pass deterministic integration tests; an independent adjudicated validation report supports the declared matching claims; and all downstream outputs retain complete identity provenance.

No scientific claim of perfect or error-free identity is permitted.
