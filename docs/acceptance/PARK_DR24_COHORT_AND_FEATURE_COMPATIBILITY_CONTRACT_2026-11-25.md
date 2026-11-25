# Park DR24 Cohort and Feature-Compatibility Contract

- Date: 2026-11-25
- Status: **SOURCE-CODE AUDIT VERIFIED / COHORT NOT ACQUIRED / FEATURE COMPATIBILITY NOT VERIFIED**
- Audited revision: `main@3ba78f93727edf79321baa2a1796a5eb37ba0782`
- Scope: Park prototype Phases 1–3 and Issue #158
- Related issues: [#158](https://github.com/saeed92m/ztf-classifier/issues/158), [#253](https://github.com/saeed92m/ztf-classifier/issues/253), [#249](https://github.com/saeed92m/ztf-classifier/issues/249), [#282](https://github.com/saeed92m/ztf-classifier/issues/282)

This document records a read-only audit of the current source path and defines a proposed, testable cohort contract. It does not acquire data, change code, approve a quality mask, validate a feature mapping, or authorize model training.

## 1. Verified implementation facts

The following files were read from the exact main revision above.

| File | Blob SHA-256-like Git blob ID | Verified behavior |
|---|---|---|
| `application/observations.py` | `70de2b4b40e1046d1b59ab398eaac505385290ee` | Default `get_observations()` path uses ALeRCE. DR24 retrieval is a separate native-data method. |
| `io/dr24_lightcurve.py` | `e789e6de1cdc6522aae5345ea37c72e68b8752ea` | Reads DR24 HATS records and preserves native `hmjd`, `mag`, `magerr`, `clrcoeff`, and `catflags`. It does not convert time or photometry, apply a flag mask, or merge OIDs. |
| `features/pipeline.py` | `7e286981c965ef3d4d55eb6eb323942d7083de97` | Frozen v0.2 pipeline requires `mjd`, `fid`, `mag`, and `magerr`; it returns the exact 42-feature order. |
| `preprocessing/lightcurve.py` | `aca397f34652c2420d0334135cacbf2bbc07a986` | Selects one `fid`, rejects non-finite MJD/magnitude/error and non-positive errors, then sorts by MJD. |
| `io/alerce.py` | `41baf8001cfeb157c7f22613295a9b2ba72ee95c` | ALeRCE normalization prefers corrected magnitude/error when valid and otherwise uses raw photometry. |
| `domain/observations.py` | `67468beb4610a008755f4006417aafd3dd7e0c0b` | Normalized observations store `mjd` and `fid`; the contract does not identify a source time scale or native photometric system. |
| `domain/source_identity.py` | `7469f066874169da10645dccca9ce2a8c19085d0` | Defines identity and association data contracts. Its module docstring states that it does not perform cross-matching or infer identity. |
| `dataset/manifest.py` | `f42d3e47a79e70e69c9d4b7070499ad69eb6c102` | Existing object manifest requires a unique OID and label fields. It does not by itself represent the full DR24-to-catalog association and source-group lineage. |

The AOIC architecture document is marked **Proposed architecture; not implemented**. The source identity records are contracts, not a working cross-match service.

## 2. Root cause of the DR24 feature blocker

The current application has two distinct paths:

1. The normalized observation path uses ALeRCE.
2. The DR24 path returns source-native HATS data for raw inspection and descriptive summaries.

The current v0.2 feature pipeline expects an internal ALeRCE-like schema. The DR24 adapter returns a different source contract.

The following differences are material:

- DR24 time is `HMJD`. The current feature contract uses `MJD`.
- DR24 HATS uses native ZTF magnitudes. The ALeRCE adapter may use corrected photometry, with raw fallback.
- DR24 uses `filterid`; the feature pipeline uses `fid`. A tested mapping is not established here.
- DR24 `catflags` and ALeRCE quality fields have different meanings.
- The normalized observation model does not preserve a declared time scale or photometric system.

Therefore, a direct column rename is not an acceptable adapter. In particular, do not rename HMJD to MJD or pass native DR24 magnitudes into the v0.2 feature pipeline without a documented and tested transformation.

**Finding:** DR24-to-v0.2 feature parity is **NOT VERIFIED**. The current code does not establish that DR24 can safely use the frozen v0.2 model.

## 3. Proposed cohort data model

Keep these records separate. Do not collapse them into one object table.

### 3.1 Label manifest

One row per source in the selected label dataset.

Required fields:

- label dataset ID, version, DOI/URL, archive checksum and retrieval time;
- source-native catalog name and release;
- source-native object identifier;
- source-native class label and taxonomy version;
- label type and available label provenance;
- source row hash and validation status.

The ALeRCE 2020 archive is the primary candidate. Its published paper reports 123,496 labelled sources and 15 classes. This is a source-level count, not a DR24 light-curve count. Verify the actual CSV schema, row count, class counts, duplicates and missing values after acquisition.

Use only the labelled-set CSV as label input. Do not use the 868,371-row unlabeled prediction output as ground truth. Treat ALeRCE labels as reference labels with documented limitations, not independent astrophysical truth.

### 3.2 Cross-match ledger

One row per candidate association between a label-source record and a DR24 HATS record.

Required fields:

- both source-native identifiers and catalog releases;
- coordinates, coordinate epoch and uncertainties where available;
- matching method and version;
- search radius and angular separation;
- candidate count and candidate ranking;
- association status: confirmed, ambiguous, unmatched, rejected or deferred review;
- evidence references and decision provenance.

Preserve every candidate. Do not select the nearest candidate automatically. Do not equate ALeRCE OIDs, DR24 HATS OIDs or Zubercal PS1 identifiers.

### 3.3 DR24 light-curve manifest

One row per source-native DR24 HATS light-curve record.

Use the composite identity:

`(survey, release, objectid, filterid, fieldid, rcid)`

Record:

- query ID, query parameters and retrieval timestamp;
- catalog schema and HATS release;
- OID, filter, field, rcid and source coordinates;
- catalog epoch count and returned epoch count;
- payload hash and raw artifact location;
- status: complete, partial, empty, missing, rejected or failed;
- native units and time/photometry semantics.

Keep raw epochs immutable. Keep all failed, empty and ambiguous records in the audit ledger.

### 3.4 Feature and split manifests

Each feature record must identify:

- source light-curve manifest row and raw payload hash;
- feature schema ID and version;
- code commit and dependency lock;
- time, photometry and filter mapping versions;
- QC policy version and exclusion reasons;
- feature eligibility and missing-value reasons;
- feature output hash.

The split manifest must group records by confirmed canonical source identity. It must prevent the same physical source from appearing in training, calibration and test sets. A survey OID alone is not a safe cross-filter grouping key.

Keep BTS spectroscopic transient labels in a separate layer for scoped independent evaluation only. Do not use them as general training labels or collapse them into ALeRCE labels.

## 4. Proposed count definitions

The technical project document states a target of at least 100,000 labelled light curves. It does not define the counting grain in the material reviewed for this audit.

Report these counts separately:

- `n_label_sources`: unique source rows in the pinned label manifest.
- `n_hats_records_requested`: distinct DR24 HATS records requested.
- `n_hats_records_retrieved`: distinct records returned with raw payloads.
- `n_nonempty_hats_lightcurves`: records with at least one returned epoch.
- `n_label_associated_lightcurves`: non-empty HATS records with an accepted, non-ambiguous label association.
- `n_eligible_labelled_lightcurves`: records that also pass the approved, versioned feature/QC eligibility contract.
- `n_confirmed_source_groups`: distinct confirmed AOIC source identities.
- `n_ambiguous`, `n_unmatched`, `n_empty`, `n_partial`, `n_rejected`, and `n_failed`.

**Proposed acceptance interpretation:** apply the 100,000 target to `n_eligible_labelled_lightcurves), not to epochs, raw catalog rows, label-source rows or unique astrophysical sources. Report `n_confirmed_source_groups` separately.

This interpretation is a proposal. It must be confirmed against the Park acceptance authority before the cohort is declared to meet the target. Do not claim the target from the 123,496 ALeRCE source count or the 170,632 SCoPe DR16 light-curve count.

## 5. Source roles

| Source | Permitted role | Exclusion |
|---|---|---|
| ALeRCE 2020 / Zenodo 4279623 | Primary candidate historical label manifest and frozen reference | Not independent ground truth; not yet a DR24 cohort |
| ALeRCE TAP | Resolve source metadata and retrieve documented public tables | Broker probabilities are not independent labels |
| DR24 HATS | Primary raw light-curve source for the Park cohort | Native values are not yet validated v0.2 model inputs |
| SCoPe / Zenodo 8410825 | Candidate independent external evaluation after taxonomy review | DR16 multi-label data; do not count toward the DR24 cohort or merge labels directly |
| BTS spectroscopic labels | Scoped independent evaluation for supported transient classes after AOIC identity and leakage checks | Not a general training-label source; retain its separate provenance and selection limits |
| ALeRCE 2025 expansion | Request the labelled-source manifest and provenance | Do not assume the full manifest is publicly available; do not add TDE to the frozen 15-class taxonomy |
| Zubercal DR20 | Supplementary, separately versioned comparison stream | PS1 IDs, MJD(TDB), photometry and flags must not be merged with DR24 HATS fields |

## 6. Required execution sequence

1. Acquire the ALeRCE 2020 archive only through the approved manual acquisition path. Verify the published archive MD5 before extraction.
2. Extract only the labelled-set CSV. Record SHA-256, schema, row count, class counts, duplicates and missing values.
3. Resolve label-source metadata through the documented ALeRCE TAP/API. Do not use retired direct database access.
4. Build the cross-match ledger. Retain candidate counts and ambiguity.
5. Run a fixed 5–10 confirmed-source-group smoke test through label resolution, DR24 HATS retrieval, raw export and Workbench display. This is a diagnostic only.
6. Run a 30–50 confirmed-source-group guided UI workflow across multiple object types. This is also a diagnostic/demo only; it is not Park acceptance and must not replace the full cohort.
7. Reconcile all requested, matched, ambiguous, unmatched, retrieved, empty, partial, failed and rejected records.
8. Approve the time, photometry, filter, quality and feature contracts before generating model features.
9. Freeze the complete source-defined cohort and leakage-safe source-group split before model evaluation.
10. Process the complete eligible cohort. Batching is allowed for memory/runtime, but every batch must be processed and reconciled. Do not replace the cohort with a random sample.
11. Scale to and verify the 100,000-light-curve target through resumable, bounded batches. Do not download the full DR24 archive.

External DR24/ALeRCE acquisition remains manual-only through the repository's explicit heavy-workflow gate. This audit did not run a download or a live source query.

## 7. Feature-path acceptance tests

Before any DR24 model inference, add deterministic tests for:

1. HMJD semantics and the selected time treatment.
2. DR24 filter-ID mapping and unsupported filters.
3. Native magnitude, color coefficient and any approved color correction.
4. Magnitude-error validity and calibration uncertainty.
5. `catflags` semantics and a versioned QC policy.
6. Duplicate epochs, missing values, non-finite values and ordering.
7. Feature names, order, units, missing-value rules and numerical tolerances.
8. Raw-payload immutability and source-to-feature provenance.
9. Cross-filter source grouping and ambiguous identity.
10. Repeated-run hashes and declared numerical tolerances.

Do not change `extract_v0_2_features`, its 42-feature order, the frozen model artifact, class order, cutoff or acceptance thresholds to make DR24 data fit.

## 8. Model decision boundary

- Keep the v0.2.0 baseline immutable.
- Issue #282 remains BLOCKED until the original production artifact is recovered and independently authenticated.
- Do not rebuild the original model or substitute the schema-1.1 lab-smoke artifact.
- A new Park model may be considered only as a separately versioned model with its own data manifest, feature schema, taxonomy mapping, split, training configuration, artifact hashes, evaluation report, calibration and provenance.
- This audit does not authorize model training or claim any performance result.

## 9. Current disposition

| Item | State |
|---|---|
| Current code path audit | VERIFIED |
| DR24 native retrieval contract | IMPLEMENTED for bounded raw retrieval |
| ALeRCE-to-DR24 source mapping | NOT RUN |
| 100,000 labelled DR24 cohort | NOT ACQUIRED |
| Cross-match acceptance | NOT VERIFIED |
| Production QC policy for DR24 | NOT APPROVED |
| DR24 feature compatibility | NOT VERIFIED |
| Original v0.2.0 model artifact | BLOCKED |
| Park model training | NOT STARTED |
| Scientific validation | NOT PASSED |

The next implementation task is the manifest-first label-to-DR24 acquisition and reconciliation workflow. It must follow this contract and the manual external-acquisition gate. The Park prototype remains **NOT READY FOR PRESENTATION**.
