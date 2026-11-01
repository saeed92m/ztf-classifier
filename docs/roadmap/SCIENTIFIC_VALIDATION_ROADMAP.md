# Scientific Validation Roadmap

Scientific validation is a permanent Product-Level Gate for the final Astronomical Data Analysis & Discovery Platform. Historical external-benchmark reconstruction is a separate evidence scope and must not be conflated with the product execution path.

## Stage V0 — Registry foundation

- [x] Versioned Benchmark Registry
- [x] Machine-readable benchmark manifests
- [x] Deterministic table runner
- [x] JSON + Markdown validation reports
- [x] SHA-256 input evidence
- [x] Explicit ground-truth/reference separation
- [x] Release-blocking regression comparison

## Stage V1 — Benchmark adapters

- [ ] StarEmbed ZTF_40k adapter and reproducible subset retrieval
- [x] ZTF periodic-variable published membership contract (~730k) — immutable Zenodo 5764899
- [ ] ZTF periodic-variable published membership acquisition + execution (~730k) — release-blocking evidence
- [x] historical ZTF periodic-variable catalog (~781k) adapter — Zenodo 3886372
- [ ] pinned ZTF DR24 source-backed adapter
- [x] ALeRCE API/TAP independent-reference adapter
- [x] ALeRCE frozen historical reference contract — Zenodo 4279623
- [ ] ALeRCE frozen historical reference acquisition + execution — release-blocking evidence

Each adapter must preserve source/version/DOI/retrieval date/object IDs/hashes/schema/taxonomy/split/leakage/preprocessing/provenance.

## Stage V2 — Leakage and scientific integrity

- [ ] object overlap and duplicate-object audits across all benchmark populations
- [ ] target-leakage audit
- [ ] future-data/temporal leakage audit
- [ ] benchmark-trained-artifact audit
- [ ] preprocessing compatibility audit
- [ ] deterministic feature-generation audit
- [ ] schema compatibility audit
- [ ] provenance completeness audit
- [ ] failure-code correctness audit

Any unresolved required check blocks release.

## Stage V3 — Full metric and failure analysis

For applicable benchmarks (engine support implemented; execution/evidence remains release-gated):

- [x] accuracy and balanced accuracy
- [x] macro/weighted precision, recall, F1
- [x] per-class metrics and confusion matrix
- [x] log loss and Brier score
- [x] calibration/reliability diagnostics
- [x] OOD metrics
- [x] coverage/rejection
- [x] false-accept/false-reject analysis
- [x] QC acceptance rate
- [x] inference reproducibility
- [x] resource/latency evidence where relevant

## Stage V4 — Product integration

- [x] validation service integrated with the application layer
- [ ] Benchmark Registry exposed through scientific operations APIs
- [x] Scientific Validation Dashboard/Report integrated into Workbench
- [ ] release evidence generated automatically
- [ ] benchmark regression status visible per release
- [ ] out-of-domain scope and known failure cases visible to users

## Stage V5 — CI/release operations

- [x] registry contract validation in ordinary CI
- [x] scheduled heavy benchmark execution
- [x] manual release-candidate benchmark execution
- [x] regression artifacts retained as release evidence
- [x] release workflow consumes scientific validation status
- [x] no final release can bypass the scientific gate

## Permanent change-trigger policy

Relevant benchmarks must rerun after changes to:

- feature generation;
- preprocessing;
- model or model artifact;
- inference;
- calibration;
- conformal prediction;
- OOD/anomaly handling;
- normalization;
- scientific API contracts.

Benchmark regressions are release-blocking until reviewed and dispositioned.

## Initial source registry

The permanent source set is:

1. StarEmbed ZTF_40k
2. ZTF periodic-variable classification release (~730k objects)
3. historical ZTF periodic-variable catalog (~781k objects)
4. pinned ZTF DR24 source-backed subset
5. ALeRCE API/TAP as an independent reference system

The benchmark source data remains external to Git; Git stores the contracts, manifests, hashes, configurations, and reports. Immutable publisher snapshots are preferred for historical claims; live services are retained for drift monitoring only. A benchmark contract is not considered evidence until its archive is acquired, hash-verified, schema-validated, and executed.

## V6 — Frozen historical reference completion

- [x] ALeRCE frozen-reference contract (Zenodo 4279623)
- [x] CPVS published-membership contract (Zenodo 5764899)
- [x] CPVS parent-source contract (Zenodo 3886372)
- [x] fail-closed acquisition utility
- [x] acquire and verify ALeRCE frozen archive
- [x] acquire and verify CPVS published membership archive
- [x] acquire and verify CPVS parent archive
- [x] execute historical-reference/source-backed adapters for the declared P0 recovery scope
- [x] close issues #51 and #63 with evidence
- [x] complete P0 scientific-validation recovery and classify the CPVS exact-reproduction claim fail-closed

**P0 exit status (2026-10-04): COMPLETE.** The remaining final-release work is leakage/integrity/temporal audit, full product-scope replay/evidence, release evidence generation, and release freeze; these are not retroactive blockers for the completed historical-reference recovery.


## Cumulative Learning overlay — permanent lifecycle control

Every Scientific Validation stage is cumulative and must consume validated knowledge from previous stages.

Required stage record:
- Previous knowledge consumed
- Baseline inherited
- Expected improvement
- Metrics and evidence
- New knowledge generated
- New risks discovered
- Regression status
- Lessons learned
- Knowledge carried forward

The lifecycle is:
AUDIT -> RETRIEVE PREVIOUS KNOWLEDGE -> DEFINE OBJECTIVE -> DEFINE BASELINE -> PLAN -> IMPLEMENT -> TEST -> MEASURE -> VALIDATE -> FAILURE/ROOT-CAUSE ANALYSIS -> KNOWLEDGE EXTRACTION -> UPDATE KNOWLEDGE BASE -> UPDATE TESTS/RULES -> COMPARE AGAINST PREVIOUS BASELINE -> ACCEPT/REVISE -> NEXT STAGE.

Knowledge Extraction is mandatory. Knowledge status must be FACT, VERIFIED, SUPPORTED, HYPOTHESIS, ASSUMPTION, UNRESOLVED, or REJECTED. Unverified findings must not silently become inherited facts.

### Scientific multi-objective quality

Relevant iterations evaluate a contextual quality vector:

Accuracy, Correctness, Speed, Efficiency, Reliability, Robustness, Coverage, Reproducibility, Scientific Validity.

A local improvement that weakens scientific validity, correctness, reproducibility, or release integrity is not an accepted improvement. Trade-offs must be measured and recorded.

### Benchmark-to-knowledge loop

Each benchmark execution should produce:
- result evidence;
- failure patterns;
- class-specific weaknesses;
- data-quality findings;
- leakage findings;
- calibration findings;
- OOD findings;
- provenance findings;
- reproducibility findings;
- reusable regression protection.

These outputs feed the project knowledge layer and subsequent benchmark planning.

### Performance evidence

Where relevant, validation records runtime, throughput, latency, memory, CPU/GPU utilization, I/O, batch efficiency, feature-generation time, and inference time. Missing measurements are recorded as NOT_MEASURED, never fabricated.

This overlay does not relax the permanent Scientific Validation Product-Level Gate.


## Recovery architecture — CPVS exact-membership reconstruction

The CPVS 730k reconstruction is now explicitly split from the product gate.

Observed historical Seq-space evidence:
- parent CPVS: 781,602 unique Seq values
- published membership: 730,184
- reconstructed candidates: 741,786
- candidate/published intersection: 730,184
- published-only: 0
- candidate-only: 11,602

The retained historical artifact records 11,602/11,602 candidate-only objects with `snr_exact=true` in both bands. Its metadata diagnostics show 11,585 fail at least one parent mean-magnitude field and 17 pass both mean magnitudes but fail one band-specific period field. These correlations do not prove the publisher's intended selection rule.

Policy:
1. Do not introduce thresholds, flags, metadata filters, or hardcoded IDs solely to force the candidate count to 730,184.
2. Preserve full candidate/reference ID sets, object-level provenance, source hashes, and diagnostic outputs.
3. Mark exact historical CPVS reproduction `UNRESOLVED` until source semantics are independently established.
4. Do not let this claim-specific unresolved state block unrelated product ingestion, feature, analysis, or product-scope validation work.
5. Keep the product Scientific Gate release-blocking for its own declared evidence scope.
6. Label any membership inferred from a retained audit as inferred; do not present it as a fresh join against raw Table 4 bytes.

### Product-scope validation path

The release-blocking product path must continue independently through:
source acquisition -> ingestion -> normalization/QC -> feature generation -> analysis/inference -> calibration/OOD -> scientific result/provenance -> known-answer/external validation.

### External-reproduction path

The CPVS path remains responsible for proving the narrower claim of exact historical reproduction. It is fail-closed for that claim.


## Status update — 2026-10-11 (supersedes earlier operational assumptions)

The earlier **P0 exit status (2026-10-04): COMPLETE** describes the recovery milestone at that time; it does not establish that the CPVS exact-membership claim is now resolved. Issue [#170](https://github.com/saeed92m/ztf-classifier/issues/170) remains open.

- PR [#171](https://github.com/saeed92m/ztf-classifier/pull/171) made the CPVS status classifier fail-closed when audit evidence is absent or unsuccessful.
- PR [#173](https://github.com/saeed92m/ztf-classifier/pull/173) corrected a genuine derivation defect: finite, non-zero magnitude qualification was not applied to the final two-band membership intersection. The fix is necessary but insufficient; independent diagnostics with that magnitude filter still reported 741,785 candidates versus 730,184 published records.
- The source-backed run [#38005546758](https://github.com/saeed92m/ztf-classifier/actions/runs/38005546758) was green at workflow level but skipped the source-provenance/scientific-gate-readiness job. It is not evidence of final scientific release readiness.
- The published Table 4 ID ↔ ZTF name ↔ parent-catalog mapping (including IDs 781603 and 781604) is an investigation lead and must be verified against the pinned source tables; it is not yet a confirmed root cause.

**Required next action:** run the heavy source-backed workflow on its intended ci/heavy/* ref after the merged correction, confirm required jobs execute rather than skip, inspect derivation/acquisition artifacts, and independently audit the membership and ID/name mapping. Keep exact reconstruction UNRESOLVED until evidence justifies a different disposition. Do not weaken the product gate or alter the frozen v0.2.0 baseline.


## Current status update — 2026-11-01

**Issue [#170](https://github.com/saeed92m/ztf-classifier/issues/170) remains OPEN / UNRESOLVED.** The latest main commit is `4f98a06bde95b08a54a8844995b7717d6281ca33`. No new heavy source-backed CPVS run has completed on the current main revision.

### Verified historical-artifact recheck

The retained artifact from run [38635891449](https://github.com/saeed92m/ztf-classifier/actions/runs/38635891449) was downloaded and its actual bytes re-hashed. It contains 781,602 unique parent Seq IDs, 741,786 candidate IDs, the complete 11,602 candidate-only diagnostic list, and a membership audit reporting 730,184 published IDs with zero published-only IDs.

- Parent metadata SHA-256: `3675b1274f73fcb15d47e7a780f194ef8fa335cd248c6ff53ea4f01559c86591`.
- Candidate list SHA-256: `699ff34bcf8dd4b5043eed48384973cb5109fd86ca260f831a502097370238df`.
- Selection diagnostics SHA-256: `7e763d8804a57d75d1633d0a4089a4a6ac5aa40bb4695964d35e645b67ad5b61`.
- Membership audit SHA-256: `4c1a082569820af26cbca80320a4913a00e1849446b0ca0205fc872b5ce89c5c`.

The 100-object and 1,000-object stratified samples are documented in `docs/scientific_validation/CPVS_PARENT_SAMPLE_AUDIT_2026-11-01.md`. The sample uses three groups: inferred published members, candidate-only objects, and parent non-candidates. **The reference labels are inferred from the retained audit relation because the raw Table 4 bytes are not included in that artifact.** This is not a fresh independent Table 4 comparison.

### Engineering status

PR [#244](https://github.com/saeed92m/ztf-classifier/pull/244) adds a fail-closed candidate × metadata audit, a Table 4 ZTF-name-to-Table-2-Seq crosswalk, a synthetic regression for different Table 4 ID and Table 2 Seq namespaces, VizieR mirror fallback, and compact evidence. A parser/header-format issue found during review was corrected on the PR branch. The latest PR head remains Draft; its latest CI, CodeQL, Product Scope Audit, and Scientific Validation results must be checked before any merge decision.

The previous heavy run [40873746342](https://github.com/saeed92m/ztf-classifier/actions/runs/40873746342) acquired the parent and light-curve sources but failed to acquire Table 4 from configured CDS endpoints. The fallback changes in PR #244 have not yet been exercised by the full heavy path.

### Next acceptance gates

1. Finish ordinary CI and security/scope checks on the exact latest PR head.
2. Review the VizieR/Zenodo fallback against actual VizieR TSV header formats and strict schema/row-count checks.
3. Run the full source-backed workflow only after code review and resource approval; avoid repeating the multi-gigabyte photometry transfer without a clear need.
4. Acquire and hash raw Table 2 and Table 4/Zenodo membership bytes, validate the ZTF-name-to-Seq crosswalk, and produce full object-level differences.
5. Re-run the fixed 100/1,000 samples against the fresh membership set and preserve commands, hashes, and intermediate outputs.
6. Establish the documented detection/SNR semantics or record a source-supported limitation. Do not change production selection or acceptance criteria.

No production selector, SNR threshold, model, feature set, class order, v0.2.0 baseline, or release artifact has changed.

## Full Zenodo crosswalk result — 2026-11-01

The full metadata-only crosswalk job completed successfully in [CI run 41299576448](https://github.com/saeed92m/ztf-classifier/actions/runs/41299576448) on PR head `7c73a4a9d2260e080300303e6aac826630369539`. It mapped 730,184 unique frozen Zenodo `1st_layer.csv` ZTF names through Table 2 `ID` to the actual `Seq` / `SourceID` namespace, with 781,602 unique parent Seq values and zero unmapped published names. The full object-level comparison against the retained historical candidate IDs confirms 730,184 intersection, 11,602 candidate-only, and zero published-only. This does not resolve the discrepancy. The source and hash manifest, exact set hashes, and metadata diagnostics are recorded in `docs/scientific_validation/CPVS_FULL_ZENODO_MEMBERSHIP_COMPARISON_2026-11-01.md`.

**Limitation:** the crosswalk uses the frozen Zenodo membership archive, not raw Table 4 bytes; the candidate IDs and parent metadata are retained historical artifacts, not a fresh full photometry reconstruction on this PR head. Raw Table 4 acquisition and publisher-selection semantics remain outstanding.


## Raw CDS reconciliation update — 2026-11-02

**Issue #170 remains OPEN / BLOCKED.** The raw source-table identity and crosswalk are now independently verified. The 11,602 candidate excess is not resolved.

Successful workflow: 41360681445. It reused the previously acquired raw source and historical membership artifacts. It did not re-download the 1.6 GB photometry archives or re-derive the candidate set on the current PR head.

Verified results:

- Raw Chen et al. (2020) Table 2: 781,602 rows; SHA-256 2c77c5b6c14811f6abab6e1442ce82c6fb54dbdcfc141954165704fecfcb3881.
- Raw Chan et al. (2022) Table 4: 730,184 rows; SHA-256 4fa96379d47f851db7ecd80a83986d82201e8718f12ab727b5348a3914374e7d.
- Raw CDS rows versus IOP/AAS publisher MRT records: zero mismatches for both tables.
- Table 4 ZTF-name-to-Table-2-Seq crosswalk: 730,184/730,184 mapped; zero mismatches between Table 4 ID and Table 2 Seq.
- Raw Table 4 membership and frozen Zenodo 1st_layer.csv membership: exact set match.
- Historical candidate set: 741,786; candidate-only 11,602; reference-only zero.

A full-parent empirical conjunction test gives C ∩ F = P, where C is the historical two-band SNR candidate set, F is the Table 2 four-field-positive set, and P is raw Table 4 membership. F alone contains 55 nonmembers. The result is an exact set equality for archived inputs, not proof that the authors used this rule. Do not implement it in production.

The revised deterministic samples use five membership/diagnostic strata. The 100-object sample contains 50 reference-and-candidate, 25 candidate-only, 10 four-field-only controls, and 15 parent-neither. The 1,000-object sample contains 500, 250, all 55 controls, and 195 parent-neither. These samples are diagnostic oversamples, not prevalence estimates.

The 55 controls do not have per-object light-curve SNR diagnostics in the retained historical artifact. The next scientific action is to retrieve or reproduce their original per-band photometry and identify the exact failed detection condition. A fresh candidate derivation on the current PR head is also still required before exact reproduction can be claimed.

No production selector, SNR threshold, model, feature set, class order, v0.2.0 baseline, or acceptance criterion changed. PR #244 remains Draft and must not be merged as a scientific fix.

