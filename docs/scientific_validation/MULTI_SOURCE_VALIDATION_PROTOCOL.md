# Multi-source Scientific Validation and Audit Protocol

**Status:** Protocol proposed; no Gaia DR3 or TESS data acquisition has yet been performed by this cycle.  
**Tracking issue:** [#188](https://github.com/saeed92m/ztf-classifier/issues/188)  
**Related CPVS blockers:** [#170](https://github.com/saeed92m/ztf-classifier/issues/170), [#180](https://github.com/saeed92m/ztf-classifier/issues/180)

## 1. Purpose and scope

Validate the platform's data handling and scientific interfaces against several independently published astronomical data sources. This is not a claim that one model can be applied to every survey. Each source has its own schema, cadence, units, quality flags, selection function, identifier namespace, and reference-label semantics.

The work is split into distinct claims:
1. **Acquisition integrity:** the bytes and version acquired are identifiable and reproducible.
2. **Parsing/schema integrity:** records and fields are parsed according to the source's documented schema.
3. **Identity integrity:** source, object, observation, and cross-match identifiers are preserved and never silently conflated.
4. **Transformation integrity:** every normalization, filter, grouping, feature transform, and exclusion is explicit and measurable.
5. **Execution integrity:** repeated runs and full-vs-batch execution agree at the defined object-level grain.
6. **Reference agreement:** outputs agree with a precisely defined published reference where that comparison is valid.
7. **Model validity/generalization:** evaluated separately, only with a compatible feature contract and defensible labels, leakage controls, and held-out evaluation.

A successful lower layer does not prove a higher layer. In particular, a valid parser or successful CI does not establish astrophysical correctness.

## 2. Immutable safeguards

- Keep the v0.2.0 baseline and v1.0.1 release artifacts unchanged.
- Keep CPVS exact-membership reconstruction unresolved until its own evidence supports a different disposition.
- Do not tune thresholds, flags, object lists, or filters merely to match a published object count.
- Treat catalogue membership as a reference definition, not independent astrophysical ground truth.
- Keep raw external datasets and large derived tables out of Git. Store compact manifests, reports, and bounded artifacts in workflow artifacts or an approved data store.
- Do not put tokens, credentials, private identifiers, or secrets in logs.
- Never replace missing evidence with PASS. Use explicit states: PASS, FAIL, BLOCKED, NOT_RUN, NOT_MEASURED, or NOT_VERIFIED.

## 3. Source order

### Source A — ZTF / CPVS
Continue the existing source-backed investigation under #170 and #180. Record the exact source archive, version/DOI, publisher checksum where available, local SHA-256, query/retrieval time, parser mode, complete source-ID mapping, and membership-difference outputs. The currently documented 11,602 candidate-only IDs remain unresolved; this protocol does not alter that result.

### Source B — Gaia DR3
Use a bounded, pinned Gaia DR3 variable-star catalogue/table with documented release, stable `source_id`, class taxonomy, quality criteria, and reference semantics. Save the exact TAP/ADQL query or archive manifest. Record returned-row counts, unique source IDs, duplicates, nulls, and any cross-match method. Do not equate Gaia classes with ALeRCE classes without a justified mapping.

Official archive/documentation: https://gea.esac.esa.int/archive/documentation/GDR3/

### Source C — TESS via MAST
Select a bounded, reproducible set of photometry products with target identifiers, sector, cadence, product filename/version, quality flags, time units, flux units, and processing level. Record product-specific provenance and quality filtering. TESS data are not assumed to be directly compatible with ZTF feature definitions.

Official archive: https://archive.stsci.edu/missions-and-data/tess

### Source selection gate
Before acquisition, each dataset must have: a specific scientific/engineering question; authoritative source and version; documented schema; legal/access review; bounded query or subset; deterministic acquisition method; expected record/object counts or a way to validate them; and a clear reference-label role. If these are absent, record BLOCKED and why rather than downloading an arbitrary dataset.

## 4. Required per-run evidence

Every run must create:
- one JSON manifest based on `configs/experiments/multi_source_run_manifest.template.json`;
- a human-readable Markdown report;
- stage logs and validation summaries;
- compact source/ID manifests and discrepant-ID lists where appropriate;
- hashes for source bytes and every retained input/output artifact;
- exact code revision, commands, arguments, configuration, seeds, environment, and dependency versions;
- an error/incident table linking each failure to evidence, a verified or still-hypothetical cause, corrective change, regression test, and rerun.

Use UTC ISO-8601 timestamps. Hash files with SHA-256; hash canonicalized ID sets separately from original ordered rows so order and membership are not confused. Preserve both row counts and unique object counts. Never infer that a file is intact merely because its size matches.

Recommended run ID format: `<UTC timestamp>-<source>-<purpose>-<short commit>`. Do not reuse a run ID.

### Required counts at each stage
- bytes/files acquired;
- raw rows and parsed rows;
- unique survey object IDs;
- unique observation/measurement IDs when present;
- null/blank/malformed IDs;
- duplicate rows and duplicate object IDs (distinguished);
- rows/objects rejected per explicit reason code;
- output rows and objects after each transformation;
- reference intersection, candidate-only and reference-only counts where the comparison is meaningful;
- runtime/resource measurements or explicit NOT_MEASURED.

### Required event log fields
Each operation records `sequence`, `timestamp_utc`, `stage`, `operation`, `input_artifacts`, `output_artifacts`, `command_or_api_query`, `parameters`, `counts_before`, `counts_after`, `hashes`, `status`, `warnings`, `error_type`, `error_message`, `stack_trace_artifact`, and `notes`. Redact secrets before persistence.

## 5. Execution phases

1. **Plan:** define hypothesis/question, expected invariants, source, version, schema, sampling strategy, acceptance criteria, and failure conditions.
2. **Acquire:** download only a bounded subset; record exact query, retrieval time, HTTP/API metadata if available, publisher checksum, local SHA-256, and file size. No silent fallback to a different source/version.
3. **Verify bytes:** re-hash after acquisition/copy; check archive integrity and expected files.
4. **Parse:** validate required columns/types/units; retain original identifiers and source field names; report malformed records rather than dropping them silently.
5. **Normalize:** each transformation gets a named step, configuration, before/after counts, and input/output hashes.
6. **Identity audit:** test missing/duplicate IDs, row/object grain, cross-match cardinality, many-to-one joins, and identifier namespace collisions.
7. **Determinism:** rerun with identical inputs/configuration; compare canonical outputs. Compare full-catalog vs batch results at object level using complete source identifiers, not row positions.
8. **Reference evaluation:** report the reference definition, eligibility criteria, denominators, reference-positive/reference-negative agreement, false positives and false negatives relative to that reference, and unresolved records.
9. **Model evaluation (separate):** only after source schema and feature semantics are compatible. Prevent object leakage, target leakage, temporal leakage, and test-set label use in training/adaptation. Report per-class results, uncertainty/calibration, OOD/coverage, and known limitations.
10. **Root-cause and remediation:** every failure is preserved before fixing. Verify the cause with a targeted test; make the smallest justified correction; add regression coverage; rerun the same pinned inputs and compare before/after evidence.
11. **Knowledge capture:** update the cumulative ledger with facts vs hypotheses, tests, decisions, residual risks, and next action.

## 6. Error taxonomy

Use stable reason codes (extend deliberately, not ad hoc):
- `ACQUIRE_NETWORK`, `ACQUIRE_HTTP`, `ACQUIRE_AUTH`, `ACQUIRE_VERSION_UNPINNED`
- `CHECKSUM_MISMATCH`, `ARCHIVE_CORRUPT`, `EXPECTED_FILE_MISSING`
- `SCHEMA_MISSING_FIELD`, `SCHEMA_TYPE_MISMATCH`, `SCHEMA_UNIT_UNKNOWN`, `PARSE_MALFORMED_ROW`
- `IDENTIFIER_NULL`, `IDENTIFIER_DUPLICATE`, `IDENTIFIER_NAMESPACE_COLLISION`, `CROSSMATCH_AMBIGUOUS`
- `TRANSFORM_UNDECLARED`, `ROW_COUNT_UNEXPECTED`, `OBJECT_COUNT_UNEXPECTED`, `FILTER_REASON_UNRECORDED`
- `FULL_BATCH_MISMATCH`, `NONDETERMINISTIC_OUTPUT`, `REFERENCE_DEFINITION_AMBIGUOUS`
- `LEAKAGE_OBJECT`, `LEAKAGE_TARGET`, `LEAKAGE_TEMPORAL`, `LEAKAGE_TEST_LABEL`
- `FEATURE_CONTRACT_INCOMPATIBLE`, `OOD_UNREPORTED`, `METRIC_DENOMINATOR_MISSING`
- `ARTIFACT_HASH_MISSING`, `PROVENANCE_INCOMPLETE`, `LOG_REDACTION_FAILURE`

A suspected cause must be labelled HYPOTHESIS until confirmed by a discriminating test. Record rejected hypotheses and the evidence that rejected them.

## 7. Acceptance and stopping rules

A stage passes only if its declared assertions pass and all required evidence is present. A source may pass ingestion while failing reference reproduction; report those statuses separately. A failed acquisition is a recorded result, not a successful experiment. A skipped test is not a pass.

Do not close #188 until:
- a manifest/report contract is validated by tests;
- at least one pinned, bounded source run is completed end-to-end;
- at least one injected/known malformed-input test demonstrates useful error localization;
- repeated and full-vs-batch outputs are compared deterministically;
- all findings and remediation status are recorded;
- CPVS remains independently classified and is not silently marked fixed by success on Gaia/TESS.

## 8. First implementation target

Implement the audit schema and report generator before broad data downloads. Then run a small, pinned Gaia DR3 ingestion-only pilot, followed by a bounded TESS product pilot. These pilots first test provenance, schema, identity, and deterministic processing—not model accuracy. Acquire data only after the relevant source contract and query are recorded.
