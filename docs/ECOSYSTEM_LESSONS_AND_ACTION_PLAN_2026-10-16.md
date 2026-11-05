# Astronomy Ecosystem Review — Decisions and Action Plan
Status date: 2026-10-16
Scope: prior GitHub astronomy/classifier repository review plus the two follow-up package references (mcp-stargazing and GNU Astronomy Utilities/Gnuastro).
Status vocabulary: VERIFIED = directly supported by repository/workflow evidence; SUPPORTED = reusable design lesson; PROPOSED = roadmap action not yet implemented; UNRESOLVED = evidence remains insufficient.

## Executive decision
Adopt evidence-backed engineering patterns and product requirements, not wholesale code or dependencies. Keep ZTF Classifier as a CPU-first Astronomical Data Analysis & Discovery Platform. Preserve immutable scientific baseline v0.2.0 and released software artifacts. No external repository's reported score, labels, or selection rule becomes our scientific truth without independent verification.

## New follow-up references
- [mcp-stargazing](https://github.com/StarGazer1995/mcp-stargazing): SUPPORTED as an optional MCP/AI interface pattern for observational planning (sky coordinates, rise/set, targets, observing conditions). It is not a replacement for ZTF light-curve ingestion, classifier inference, CPVS reconstruction, or validation. Do not add as a required dependency now.
- [GNU Astronomy Utilities](https://www.gnu.org/software/gnuastro/) and [Homebrew formula](https://github.com/Homebrew/homebrew-core/blob/HEAD/Formula/g/gnuastro.rb): SUPPORTED as established tools for FITS/image/numeric/catalog processing. Trial only against a concrete pipeline requirement and trusted fixtures; compare results, platform compatibility, license and packaging costs before adoption. Not a default dependency for the current tabular light-curve path.

## Cross-repository lessons to adopt
1. **Object-level identity is the unit of scientific separation.** Split train/validation/test, sample diagnostics, compare batches and report errors by stable full object/source ID—not by individual observations or alert rows. Explicitly test that one object's observations never cross a prohibited split.
2. **Reference labels are not independent ground truth.** Record label source and role (training, reference, adjudicated truth, pseudo-label). Threshold-derived real/bogus labels and mutable API labels cannot be presented as independent truth.
3. **External test-label leakage is release-blocking.** Audit meta-model training, calibration, feature selection, augmentation, thresholds and model selection for any use of held-out labels or outcomes. Any target-data adaptation/transduction must be explicitly declared and separately evaluated.
4. **Scope claims to demonstrated data.** Small benchmarks, synthetic labels, few/no positive examples, class imbalance, survey/domain shift, GPU-only assumptions, and old/unmaintained code limit what an external repo can establish. Record coverage and known failure modes rather than generalizing.
5. **Separate pipeline stages and semantics.** Ingestion, QC/real-bogus, object aggregation, feature generation, classification, calibration, conformal prediction, OOD, scientific-anomaly evidence, cross-match and candidate ranking need explicit contracts and distinct meanings. OOD or model explainability is not proof of an astrophysical discovery.
6. **Make provenance inspectable.** Persist source/version/DOI/retrieval context, hashes, schema, object IDs, preprocessing/feature versions, model artifact, configuration, split policy, commands, runtime and evidence links. Large datasets remain outside Git.
7. **Test operational equivalence.** Compare deterministic full-catalog and batched execution by complete object ID; add known-answer, malformed-input, duplicate, missing-value, non-finite-value, schema-drift, retry and packaging tests.
8. **Use existing scientific tooling selectively.** Prefer small isolated adapters and reproducible comparison tests over adding heavyweight or system-level dependencies without demonstrated benefit.
9. **Keep AI as a controlled interface.** MCP/agent workflows may explain, plan or invoke permitted operations; they must not silently modify model artifacts, bypass scientific gates, or convert generated interpretations into validated scientific claims.

## Decisions and non-decisions
- ADOPT: object-ID-based split/leakage invariants; explicit reference/ground-truth/pseudo-label roles; evidence lineage in UI and reports; regression tests for every confirmed defect; separate Real/Bogus and science-classification contracts; a claim-specific CPVS audit distinct from product-scope validation.
- DEFER: Gnuastro integration until an actual FITS/image/catalog use case is defined and measured.
- DEFER: mcp-stargazing integration until observational-planning is an explicit product workflow; if pursued, keep it optional and permission-scoped.
- REJECT: copying external selection thresholds to force count equality; adopting models solely from headline metrics; treating OOD as anomaly proof; importing code before license/security/maintenance review.
- NO CHANGE: immutable v0.2.0 baseline, frozen feature/class contracts, production release artifacts, scientific gate and CPU-first posture.

## Verified current blocker state — CPVS
As recorded in open [Issue #170](https://github.com/saeed92m/ztf-classifier/issues/170), the latest source-backed comparison reported:
- parent: 781,602 rows;
- published reference membership: 730,184 IDs;
- candidates: 741,786 IDs;
- intersection: 730,184;
- candidate-only: 11,602;
- published-only: 0.
The earlier row-ordinal comparison was invalid and is superseded by Seq-based identity mapping. The remaining 11,602 candidate-only IDs are unexplained. This is UNRESOLVED; do not tune thresholds or flags to force cardinality equality.
[Issue #182](https://github.com/saeed92m/ztf-classifier/issues/182) tracks deterministic 100/1,000-object manifests and full-vs-batch auditing. Its recorded status says source-backed sample artifacts still require generation/review and full-vs-batch comparison has not yet been executed/wired. Do not claim those experiments passed until artifacts and output are inspected.
A separate roadmap text still contains 741,788 / 11,604 in an older section; treat that as a documentation inconsistency to correct to the latest verified issue evidence, preserving the older result only if explicitly marked as historical.

## Prioritized implementation plan
### P0 — scientific correctness and provenance
- [ ] Reconcile all current CPVS count statements to the latest evidence; preserve old invalid row-ordinal counts as superseded historical evidence.
- [ ] Run and review source-backed deterministic 100-object and stratified 1,000-object samples; publish exact IDs, seed/method, hashes, reference-relative FP/FN and discrepant IDs.
- [ ] Execute full-catalog vs batched comparison grouped by full SourceID; prove boundary invariance or record a reproducible failure.
- [ ] Audit object-level train/test overlap, target/temporal leakage, held-out label use, pseudo-label provenance and duplicate handling.
- [ ] Keep CPVS exact reproduction UNRESOLVED until source semantics explain the residual set; product-scope validation proceeds separately but remains fail-closed for its own required evidence.
### P1 — robust platform
- [ ] Enforce data adapter contracts for ID, units, schema/version, null/NaN/infinity, duplicates, QC state and provenance.
- [ ] Build source-level evidence/provenance display and reproducible export/report.
- [ ] Convert known failure modes into unit/integration/scientific regression tests.
- [ ] Add benchmark coverage, domain shift, per-class failure analysis, calibration, OOD and known-limitations reporting.
### P2 — product expansion
- [ ] Verify desktop clean-install/user-path tests on each supported OS.
- [ ] Add cross-match evidence, similar-object search, human review and transparent ranking under explicit scientific contracts.
- [ ] Evaluate Gnuastro or MCP integration only through a scoped prototype with license, security, compatibility and performance evidence.
- [ ] Consider streaming/alert adapters only after deterministic offline and batch behavior is verified.

## Documentation and backup synchronization rules
- GitHub is the code and versioned documentation source of truth; Notion is a linked operational knowledge mirror; backups must record exact commit/ref, timestamp, manifest and hashes.
- Do not label a backup current unless its snapshot has been generated from and verified against a named commit. Do not put raw large scientific datasets into Git.
- Every adopted lesson must be recorded in the handbook, roadmap, knowledge base/architectural decisions, cumulative improvement ledger and relevant regression tests. Only implementation changes affect release notes; documentation-only work does not imply a new software release.
- This review updates decisions and priorities; it does not certify new scientific capability as implemented.

## Sources reviewed
- [ZTF-DR11-classifier](https://github.com/PaulaSanchezSaez/ZTF-DR11-classifier)
- [snad-binary-classifiers](https://github.com/snad-space/snad-binary-classifiers)
- [multi-survey-lc-classifier](https://github.com/elekaroz/multi-survey-lc-classifier)
- [flare-classifier](https://github.com/snad-space/flare-classifier)
- [lasair_needle2.0](https://github.com/XinyueSheng2019/lasair_needle2.0)
- [ztf-realbogus-cnn](https://github.com/Paul0112/ztf-real-bogus-cnn)
- [ztf-machine-learning](https://github.com/StevieG47/ztf-machine-learning)
- [mcp-stargazing](https://github.com/StarGazer1995/mcp-stargazing)
- [GNU Astronomy Utilities](https://www.gnu.org/software/gnuastro/)
- [Open CPVS discrepancy issue #170](https://github.com/saeed92m/ztf-classifier/issues/170)
- [Open deterministic sampling issue #182](https://github.com/saeed92m/ztf-classifier/issues/182)

## Current implementation status
This file is a decision and planning record. It does not mean the P0/P1/P2 checkboxes above are completed. Status date: 2026-10-16.
