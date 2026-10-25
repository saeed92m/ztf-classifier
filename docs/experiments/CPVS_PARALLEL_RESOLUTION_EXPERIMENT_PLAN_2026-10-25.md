# CPVS Parallel Resolution Experiment Plan — 2026-10-25

## Purpose

Evaluate two independent approaches to the CPVS candidate/reference membership discrepancy without changing the immutable scientific baseline v0.2.0, model artifacts, production selection behavior, or release v1.0.1.

## Research question

Can a source-backed correction to the Jupyter/reconstruction path explain and correctly resolve the membership differences, and where the historical publisher rule cannot be established, can a provenance-rich discrepancy report make those differences safely usable without implying scientific resolution?

## Track A — reconstruction / Jupyter processing

Branch: `experiment/cpvs-jupyter-reconstruction-20261025`

1. Inventory the actual notebook/scripts and identify the exact code path that generated the candidate membership set.
2. Identify authoritative source versions, schemas, hashes, identifier definitions, and the meaning of Table2 `Seq` versus the light-curve attachment's SourceID.
3. Verify object-level versus light-curve-row-level grain; joins; normalization; filtering order; duplicate handling; missing, zero, NaN, and infinite values.
4. Reproduce the current candidate set from hash-identified inputs before changing any logic.
5. Run the four-field predicate `gmag > 0`, `rmag > 0`, `Per-g > 0`, `Per-r > 0` only as a separate diagnostic hypothesis. Do not assume it is the historical publisher rule.
6. Preserve the distinction between the paper's stated high-level criterion and our diagnostic predicate: Chan et al. (2022), CDS/VizieR ReadMe `J/ApJ/932/118`, says the 730,184 objects contain at least one 2.5σ and 3σ detection in g and r, respectively ([official ReadMe](https://cdsarc.cds.unistra.fr/viz-bin/ReadMe/J/ApJ/932/118?format=html&tex=true); [official catalogue directory](https://cdsarc.cds.unistra.fr/ftp/J/ApJ/932/118/)). The `gmag/rmag/Per-g/Per-r > 0` test is not interchangeable with that detection criterion and cannot be described as the authors' rule without a source-backed derivation.
6. Record every included/excluded object ID, source-row mapping, field values, reason, source hashes, environment, commands, and deterministic rerun result.
7. Add regression tests for non-contiguous identifiers, duplicate IDs, missing/non-finite values, object/row grain, and set equality/difference invariants.

## Track B — discrepancy reporting

Implementation branch: `feature/cpvs-discrepancy-report-20261024`; PR [#224](https://github.com/saeed92m/ztf-classifier/pull/224).

1. Run the report builder against authoritative, hash-identified parent metadata, candidate IDs, and published Table4 IDs.
2. Verify all candidate-only IDs have parent provenance and no duplicate/unmapped IDs are silently dropped.
3. Reconcile counts and object IDs across CSV, HTML, Markdown, and strict JSON.
4. Verify deterministic hashes/manifests and preserve `NOT_ASSESSED` for raw-light-curve review or cross-match evidence that was not actually performed.
5. Keep the historical publisher-rule blocker open if source evidence does not establish the exact rule.

## Comparison matrix

Compare both tracks using the same source artifacts and explicit reference definition:

- source and object-identity integrity;
- exact deterministic reproducibility;
- false inclusion and false exclusion counts and IDs;
- missing/invalid/non-finite value behavior;
- sensitivity to schema and identifier mapping;
- provenance completeness and human interpretability;
- behavior on independent source-backed astronomical datasets outside CPVS.

A match to the published cardinality (730,184) alone is not sufficient. Do not choose or tune a predicate merely to force that number. ALeRCE v0.2 benchmark labels are separate and are not independent ground truth for this membership question.

## Decision gates

- **Gate 0 — source readiness:** all required inputs, schemas, source versions, and hashes identified.
- **Gate 1 — reproducibility:** current output reproduced from the recorded inputs and commands.
- **Gate 2 — correctness:** set-level comparison and all changed/excluded IDs are explained by evidence.
- **Gate 3 — generalization:** checks on independent source-backed astronomical inputs, with known limitations stated.
- **Gate 4 — acceptance:** review evidence, regression tests, and documentation; do not alter production selection until approved by evidence.

If the publisher's historical rule remains unknowable, keep that uncertainty explicit and use discrepancy reporting as a product capability. This is a valid product-handling outcome, but it is not proof that the historical scientific method was exactly reproduced.

## Current state

As of 2026-10-25, the experiment branch exists and the comparison plan is recorded in [Issue #170](https://github.com/saeed92m/ztf-classifier/issues/170). The two tracks have not yet been run and compared. A local 11,602-row report bundle has been generated and row-count/provenance-join/strict-JSON/ZIP checks passed, but it reuses the retained candidate-only diagnostic list and does not independently rerun the Table 4 join. No method is selected as winner and the scientific blocker remains open.

The 100-object operational behavior test in [Issue #222](https://github.com/saeed92m/ztf-classifier/issues/222) is separate; it does not establish scientific accuracy or resolve CPVS membership.


## Execution update — 2026-10-25

### Track B: retained-audit report generated (partial validation)

Downloaded and inspected GitHub Actions source-backed artifact run [#38635891449](https://github.com/saeed92m/ztf-classifier/actions/runs/38635891449), artifact `scientific-validation-heavy` (artifact ID `11935357767`). Generated a local report bundle from the retained `candidate_only_all_objects` diagnostic list, joined each ID to the authoritative Table 2 parent metadata, and verified the output:

- 11,602 unique candidate-only IDs; all 11,602 map to exactly one parent metadata row.
- Parent Table 2 metadata contains 781,602 rows.
- Diagnostic partition: 11,580 fail both the parent magnitude pair and per-band period pair; 17 have positive magnitudes but an incomplete/nonpositive period pair; 5 have positive per-band periods but incomplete/nonpositive `gmag`; 0 pass all four positivity checks.
- CSV and JSON row counts both equal 11,602; JSON parses strictly; output ZIP integrity check passed.
- Report ZIP SHA-256: `9ed3c52555f5ef892bf574f77f981c4955decbae7f134c7b542e2f0434e653bc`.

**Scope limitation:** this report reuses the candidate-only list from the existing membership-audit artifact. The raw published Table 4 file was not present in the retained artifact, so this run did **not** independently repeat the Table 4 join and does not replace the source-backed PR #224 CLI run. The report marks raw-light-curve review and external cross-match as `NOT_ASSESSED`. It is an auditable user-facing diagnostic deliverable, not a scientific resolution of the historical publisher rule.

### Track A: reconstruction / Jupyter

Still pending. The retained artifact is sufficient to establish an auditable baseline for the known candidate-only IDs, but it does not identify a justified code correction by itself. Do not edit the notebook or production selection until the exact derivation path, source inputs, and membership join have been inspected and reproduced.

### Next acceptance actions

1. Locate the exact Table 4 source input or a reproducible acquisition step and record its hash.
2. Run the PR #224 CLI using the complete authoritative parent metadata, candidate membership IDs, and published Table 4 IDs; compare all report outputs against the retained audit.
3. Inventory the actual Jupyter notebook and scripts used for reconstruction, reproduce the baseline, and test candidate changes only on the experiment branch.
4. Compare both tracks against the same source artifacts and explicit reference definition; do not select a winner based only on the count 730,184.


### Deterministic 100-object identity/membership spot-check — partial validation

A fixed stratified sample was generated from the retained Table 2 parent metadata and candidate list using SHA-256 ranking with seed string `CPVS-fixed-100-v1` (independent of Python RNG versions): 50 candidate/reference-overlap objects, 25 candidate-only objects, and 25 parent objects not selected by the candidate pipeline. For each selected Seq, the official CDS/VizieR TAP service was queried to retrieve the parent Table 2 ZTF object name, then published Table 4 membership was checked by that ZTF name, not by Table 4's internal ID.

Observed: 100/100 Seq values mapped to a parent ZTF name; 50/50 overlap-stratum objects were found in Table 4; 0/25 candidate-only objects were found; 0/25 parent-not-candidate objects were found. This supports the prior membership partition and join-key direction for this sample. It is not a full-dataset audit, not a raw per-epoch 2.5σ/3σ detection-semantic test, and not proof that the candidate algorithm reproduces the paper's rule. The fixed sample before adding the ZTF-name crosswalk had SHA-256 `1ffd4c94c6f707e68e77462b07b5daf2690e45a60e362bf80d7d6a53cf8f2a53`.

### Literature rule and unresolved implementation

Chan et al. (2022), Section 2.1, says the retained light curves have at least one 2.5σ detection in g and one 3σ detection in r, respectively, and that both bands are phase-folded using the common Table 2 period ([DOI](https://doi.org/10.3847/1538-4357/ac69d4)). The four-field positive-value predicate `gmag/rmag/Per-g/Per-r > 0` is not equivalent by definition. Full 1,000-object sampling, source-backed CLI run on complete inputs, raw photometry review, and independent reconstruction remain outstanding.


### Fixed 1,000-object sample preparation — membership query pending

Prepared a deterministic stratified 1,000-object sample from the full parent Table 2 identifier universe and the retained candidate set using SHA-256 rank with seed `CPVS-fixed-1000-v1`: 500 candidate/reference-overlap expected objects, 250 candidate-only objects, and 250 parent objects not selected by the candidate pipeline. Sample file: local `cpvs_fixed_1000_sample_ids.json`; file SHA-256 `94b4c966abaa059ff3c1f63172542e9eb2c11323a814f3b0d4eb7a9c506087b0`; compact sample-ID payload SHA-256 `2beb0912cbf1d12c48f7f82157eaf0dd31864204450e40d181afbdf61e6c29f7`. This is sample preparation only: the full 1,000-name crosswalk and published Table 4 membership query have not completed, so no validation outcome is claimed.
