# Parallel dataset execution plan — 2026-11-17

**Status:** Research execution plan; no dataset is newly accepted by this document.
**Owner:** ZTF Classifier project
**Review:** 16-role project think tank (simulated multidisciplinary review; not external human approval)
**Related issues:** #170 (CPVS discrepancy), #210 (independent validation), #253 (DR24 application integration)
**Immutable baseline:** v0.2.0; 42-feature contract; frozen class order; historical cutoff 59447.224132.

## 1. Decision

**Park MVP acceptance is governed by the full-cohort contract in [PARK_MVP_REAL_DATASET_END_TO_END_ACCEPTANCE_2026-11-17.md](PARK_MVP_REAL_DATASET_END_TO_END_ACCEPTANCE_2026-11-17.md).** Product completion is not measured by arbitrary 50-, 100-, or 1,000-object samples. The Park acceptance run processes the complete predeclared real-data cohort; batches are allowed only as an execution method when all batches are reconciled.

CPVS reconstruction is no longer a prerequisite for general product development or the Park MVP data path. Keep the 11,602 candidate-only discrepancy open as a separate historical-reproduction research blocker.

Run three independent workstreams:

1. **Product ingestion:** official ZTF DR24 Lightcurves HATS is the broad-coverage, source-native time-series stream.
2. **Independent benchmark candidates:** StarEmbed ZTF_40k and BTS labels matched to DR24 are separate candidate evaluation datasets. Neither is accepted until its own provenance, identity, leakage, quality and reproducibility gates pass.
3. **Historical CPVS reproduction:** continue separately. Do not use it to block the other two workstreams and do not weaken its acceptance criteria.

Zubercal DR20 is a supplementary PS1-matched recalibrated-photometry stream. It is not a replacement for DR24 HATS and must remain a separate source adapter and data model.

## 2. Scientific boundaries

- DR24 HATS OID is defined per filter, field and quadrant. It is not a canonical astrophysical source identifier.
- Preserve OID, filter, field, quadrant/RCID, coordinates and source metadata. Any astrophysical grouping requires a versioned identity/cross-match layer with uncertainty and ambiguity states.
- DR24 HMJD and Zubercal MJD(TDB) are different time bases. Do not merge epochs or apply a numeric offset without a validated conversion.
- DR24 native magnitudes and Zubercal PS1-calibrated magnitudes are different photometric products. Preserve raw values and calibration semantics.
- Zubercal objectid is a PS1 identifier, not a ZTF OID. A positional association must record candidates, radius, separation, multiplicity, method and ambiguity. Never select an ambiguous counterpart automatically.
- DR24 catflags and Zubercal flag/info have separate definitions. Never reuse one source's QC policy for the other.
- ALeRCE outputs are reference-system predictions or benchmark labels with documented provenance, not independent universal ground truth.
- StarEmbed's seven classes, BTS transient classes and the frozen v0.2 15-class taxonomy are distinct label spaces. Do not combine them or force a mapping without an explicit scientific justification and versioned mapping.
- Do not feed new-source photometry to the frozen v0.2 model until feature semantics, preprocessing, time handling, calibration, parity and leakage checks pass. A successful feature extraction is not model validation.

## 3. Workstream A — DR24 product integration

### Objective
Allow a user to explicitly select DR24 as an observation source and receive source-native observations with complete provenance. Keep ALeRCE separately selectable. There must be no silent fallback.

### Implementation sequence
1. Define versioned request/response contracts for bounded DR24 HATS queries.
2. Implement the adapter behind the observation service boundary. Keep source-specific code out of the feature engine.
3. Preserve raw HATS records and epoch arrays. Record release, endpoint, query/object IDs, retrieval time, schema/index identity, counts, checksums and exclusions.
4. Preserve OID/filter/field/RCID and coordinate metadata. Do not merge OIDs based on proximity alone.
5. Add a DR24-specific, raw-preserving QC assessment. Separate diagnostic flags from any production-approved epoch mask.
6. Return explicit statuses for missing OIDs, empty results, malformed schemas, unsupported filters, partial retrievals, rate limits and timeouts.
7. Expose source, release, filters, epoch counts, QC summaries, exclusions and missing-data reasons through API and Workbench.
8. Add deterministic fixture tests for schema drift, duplicates, missing data, filter identity, QC, provenance hashes and failure behavior.
9. Add bounded opt-in live source tests. Keep live network calls out of ordinary CI.
10. Demonstrate repeatable end-to-end API/Workbench analysis on a pinned small sample.

### Acceptance
- Explicit DR24 source selection works end-to-end.
- ALeRCE remains separately selectable and the actual source is recorded in every result.
- No silent fallback occurs.
- Pinned source-backed responses reproduce within declared deterministic tolerances.
- OID and filter identity remain intact.
- Raw records are immutable and provenance is complete.
- No baseline/model changes are needed for ingestion acceptance.

### Scope guard
The previously reported BTS pilot (100 targets; 773 OIDs; 714 Lightcurves rows; 87 targets with at least one g and r OID) is availability evidence only. It does not establish astrophysical identity, photometric quality, adequate cadence, labels, or classification performance.

## 4. Workstream B1 — StarEmbed ZTF_40k candidate benchmark

### Objective
Test an independently sourced variable-star dataset for source integrity and compatibility with the existing feature-input contract. Do not assume it is a valid benchmark.

### Required evidence
1. Acquire the exact published Parquet artifacts from the pinned source.
2. Record source URL/DOI, version, license, retrieval timestamp, file sizes and SHA-256.
3. Audit every SourceID across train, validation, test and anomaly/OOD partitions.
4. Report duplicates within each split and every cross-split overlap with source-file and row provenance.
5. Trace each discrepant ID to upstream records. Do not silently deduplicate or move records between splits.
6. Establish whether the upstream split is row-wise or object-wise and whether duplicate rows represent repeated observations, duplicated objects or source packaging defects.
7. The previously executed deterministic 50-object probe is an input-path diagnostic only. Do not use its size or result as a product acceptance criterion or population-performance claim. Further sampling is justified only for a named diagnostic question.
8. Verify array alignment, finite values, units, cadence, band identity and the explicit mapping to the internal light-curve schema.
9. Run the frozen 42-feature extractor as an input-compatibility experiment only. Record missing/unsupported feature semantics; do not invent replacements.
10. Keep StarEmbed labels in their own taxonomy. Do not report v0.2 model accuracy from this experiment.

### Acceptance
- No unresolved object-level duplicate or cross-split overlap in the evaluated partition.
- All 50 requested objects are present and processed, or the run is explicitly BLOCKED. No reduced sample may report PASS.
- Source IDs and data lineage are traceable.
- Every feature mapping has documented units and semantics.
- The run is deterministic and produces a machine-readable report.
- Benchmark acceptance requires a separate scientific review of label provenance and population suitability.

### Current known blocker
A previous source audit reported one duplicate SourceID in train and one train/test overlap. The source-level provenance remains unresolved. A contract-only CI pass or unit tests on synthetic fixtures do not resolve this blocker. PR #290's latest visible Scientific Validation run passed only the benchmark/lifecycle contract job; source-backed acquisition jobs were skipped. Do not claim source audit or 50-object execution until the actual workflow artifact proves it.

## 5. Workstream B2 — BTS-labeled transient benchmark matched to DR24

### Objective
Build an independent transient benchmark using externally documented BTS spectroscopic labels and DR24 lightcurves. Treat this as a separate taxonomy and population from StarEmbed and CPVS.

### Required evidence
1. Pin the authoritative BTS catalog/release and its license, version, retrieval date and checksum.
2. Preserve original BTS identifiers, class labels, redshift/spectroscopic metadata and label provenance.
3. Resolve BTS targets to sky positions with coordinate epoch and uncertainty where available.
4. Query DR24 HATS using a bounded, reproducible strategy. Preserve all candidate OIDs and per-filter/field/quadrant metadata.
5. Create an explicit association table: BTS target ID, DR24 OID, angular separation, match radius, candidate count, method, ambiguity and decision provenance.
6. Do not assume nearest-neighbour matching proves physical identity. Keep ambiguous and unmatched targets in the audit report.
7. Measure lightcurve coverage, usable epochs, cadence, time span, band availability, catflags, negative/invalid magerr and missingness by class.
8. Establish object-level grouping before any split. All OIDs belonging to the same astrophysical target must remain in one partition.
9. Use a time-aware split where scientifically appropriate. Prevent future observations from leaking into historical evaluation.
10. Freeze a manifest before model selection. Keep a final untouched evaluation split.
11. Report per-class sample counts and coverage. Do not hide class imbalance or absent classes.
12. Run a deterministic 50-object diagnostic sample first; expand only after the diagnostic gate passes.

### Acceptance
- Label provenance is authoritative and independently documented.
- Every included target has traceable object identity and DR24 source lineage.
- Ambiguous matches are excluded from the primary metric set or reported in a separate uncertainty stratum.
- Split integrity is verified at astrophysical object level and by time.
- Photometry/QC acceptance criteria are predeclared and source-specific.
- The benchmark taxonomy is separate from v0.2.0 unless an approved mapping is scientifically defensible.
- Metrics include class-wise results, confusion matrix, calibrated probability diagnostics where applicable, coverage/rejection and failure analysis.

### Important limitation
BTS labels are spectroscopic transient classifications. They do not provide a complete benchmark for periodic variable stars or all ZTF object classes. A DR24 match does not itself guarantee sufficient or suitable photometry.

## 6. Workstream C — CPVS historical reproduction

Keep Issue #170 open. Preserve the reported discrepancy as a historical research problem until the full parent and reference membership artifacts are re-audited.

- Compare unique object-level IDs, not lightcurve rows.
- Reverify dataset versions, hashes, schema, normalization, filters, duplicates, grouping and cross-match.
- Trace all candidate-only IDs and sample reference members/non-members.
- Report false positives and false negatives against an explicit reference definition.
- Do not interpret zero missing reference IDs as an explanation for the 11,602 excess.
- Do not change thresholds or filtering rules to force agreement.

This workstream does not block DR24 ingestion or independent benchmark construction.

## 7. Dataset selection scorecard

Do not choose a benchmark by convenience or by whether it makes the model score look better. Evaluate each candidate against the same criteria:

| Criterion | Required evidence |
|---|---|
| Source authority | Publisher, release, DOI/URL, license |
| Identity | Stable IDs and object-level lineage |
| Uniqueness | Duplicate audit and explicit grouping |
| Split integrity | No object leakage; temporal policy |
| Labels | Independent provenance and taxonomy |
| Coverage | Per-class objects, bands, epochs and time span |
| Photometry | Units, calibration, uncertainties and QC |
| Reproducibility | Pinned artifacts, hashes, deterministic sample |
| Population fit | Clearly stated scientific scope and limitations |
| Cost | Bounded access, storage, runtime and network cost |

A candidate that fails a hard scientific gate is not accepted, regardless of its aggregate score. Keep product ingestion acceptance separate from benchmark acceptance.

## 8. Required artifacts in Git

Store only small, reviewable metadata and code:
- source manifests and schema contracts;
- checksums and retrieval metadata;
- sample ID lists where licensing permits;
- source audit and leakage reports;
- association/cross-match reports;
- QC policy versions;
- deterministic run manifests;
- test fixtures that do not redistribute restricted source data;
- concise human-readable validation reports.

Do not commit bulk Parquet/HATS archives, credentials, or unlicensed data.

## 9. Execution order and exit criteria

The primary Park product acceptance target is the complete, source-defined dataset package described in PARK_MVP_REAL_DATASET_END_TO_END_ACCEPTANCE_2026-11-17.md. StarEmbed and CPVS diagnostic sample sizes remain scoped to their independent research questions and are not MVP completion measures.

| Priority | Task | Exit condition |
|---|---|---|
| P0 | DR24 adapter and explicit source selection | End-to-end bounded API/Workbench run with provenance |
| P0 | StarEmbed source audit and clean 50-object probe | Full source-ID audit and exact 50-object report |
| P0 | BTS-to-DR24 identity/coverage audit | Pinned manifest, ambiguity report and 50-object diagnostic |
| P1 | Compare candidate benchmark suitability | Evidence-backed selection decision |
| P1 | Freeze independent benchmark protocol | Versioned taxonomy, splits, metrics and manifest |
| P2 | CPVS reproduction | Root cause supported by reproducible evidence |
| P2 | v0.2 production artifact recovery | Original artifact hash-verified or separately approved new baseline |

Parallelize P0 tasks where their inputs are independent. Do not wait for CPVS.

## 10. Reporting rules

Every workstream report must separate:
- **PASS:** acceptance evidence exists and was inspected.
- **FAIL:** a required test ran and failed.
- **BLOCKED:** required input, permission or evidence is missing.
- **NOT RUN:** the workflow did not execute the test.
- **SKIPPED:** the workflow explicitly skipped the job/test, with reason.

A green CI contract job does not imply source-backed scientific validation. A diagnostic sample does not establish population-level accuracy. A successful source download does not establish correct identity, labels or photometry.

No model, feature schema, class order, thresholds, baseline artifact, acceptance criterion or release is changed by this plan.
