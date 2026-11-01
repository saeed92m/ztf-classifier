# ZTF Classifier — Project Continuity Handbook v2.9

Status date: 2026-11-01
Software release: v1.0.1
Scientific baseline: v0.2.0 (immutable)
Production model: baseline_v0.2

## Current state
v1.0.1 is published and immutable. v1.0.0 remains immutable. The current main branch is at `4f98a06`. PR #244 is an open Draft investigation branch. Its ordinary CI checks have passed on earlier heads, but the latest reviewed head and its full source-backed heavy workflow are not yet verified. No new software release is authorized or required by this diagnostic work.

The project remains in Platform Expansion. The highest-priority scientific blocker is still CPVS exact historical membership reconstruction. Desktop product work, cross-platform delivery, independent benchmark execution, and discovery-platform expansion remain separate workstreams.

## Product identity
The canonical product is an Astronomical Data Analysis & Discovery Platform, not merely a classifier.

Canonical flow:
source data → ingestion → normalization/QC → scientific feature/context layers → analysis modes → uncertainty/calibration/OOD → candidate ranking → evidence/provenance → human/scientific validation → reproducible discovery outputs

## Immutable baseline
v0.2.0 remains immutable: 150 ZTF objects, 15 ALeRCE benchmark classes, 42 frozen features, XGBoost baseline_v0.2, historical cutoff 59447.224132.

## Scientific boundary
CPVS parent: 781,602 unique Seq values. Published membership: 730,184 objects. The corrected historical Seq-space comparison reports 741,786 candidates, 730,184 intersection, 11,602 candidate-only, and zero published-only. The retained artifact shows all 11,602 candidate-only objects pass the recorded exact per-band SNR diagnostics in both bands. A four-field metadata predicate reproduces the retained historical membership set, but the paper does not explicitly state that both mean magnitudes and both band-specific periods must be positive. The predicate is therefore diagnostic, not an accepted production rule. A fixed 100/1,000-object stratified sample was generated from the retained historical parent artifact; its membership labels are inferred from the retained audit because the raw Table 4 bytes are not included in that artifact. See `docs/scientific_validation/CPVS_PARENT_SAMPLE_AUDIT_2026-11-01.md`. Issue #170 remains OPEN / UNRESOLVED. Do not tune thresholds, flags, metadata filters, or acceptance criteria to force cardinality equality.

## Diagnostic semantics
Classification uncertainty, calibration, conformal prediction, OOD, scientific anomaly evidence, catalog evidence, and explainability evidence remain separate channels. The current production model does not claim a scientific-anomaly detector.

## Release rule
Every future release must have curated .github/release-notes/<tag>.md before publication. Immutable releases are never mutated.

## Ecosystem review and product expansion
The 2026-10-08 ecosystem review is recorded in `docs/ECOSYSTEM_REVIEW_PRODUCT_EXPANSION_2026-10-08.md`.

New product requirements are now canonical:
- cross-platform desktop application for Windows, macOS, and Linux;
- self-contained installation without requiring Python/pip/venv/Git/terminal;
- integrated contextual Help and Troubleshooting;
- Object/Source Explorer;
- data-ingestion abstraction;
- explainable classification, uncertainty, calibration, conformal and OOD presentation;
- first-class anomaly/discovery workflows;
- provenance/evidence UI;
- cross-match framework;
- similar-object search;
- human-in-the-loop review/feedback;
- transparent discovery ranking;
- separate Real/Bogus architecture boundary;
- future ZTF Alert/AVRO and offline/batch/streaming readiness.

These additions are layered around the immutable v0.2.0 scientific baseline and must not weaken scientific validation or provenance contracts.

## Next work
1. Complete documentation alignment for v1.0.1 and the platform-expansion requirements.
2. Establish the desktop Application/Core API boundary and cross-platform packaging architecture.
3. Implement the user-facing Data Manager and Object/Source Explorer.
4. Integrate Help/Troubleshooting into the GUI.
5. Perform clean-room/replay and real user-path verification on supported operating systems.
6. Establish independent labeled/cross-match scientific validation evidence.
7. Expand discovery workflows only where contracts and evidence are ready.
8. Maintain cumulative learning, failure-prevention, roadmap, and release-note records for every meaningful change.

## Completion definition
v1.0.0 is complete as a published software milestone. The broader scientific/product platform is not declared scientifically complete merely because v1.0.0 is published.

Every meaningful change must update affected documentation, cumulative-learning records, failure-prevention knowledge, roadmap status, and release notes when release behavior changes.

Current status: v1.0.1 Released / Platform Expansion Active.


## Current scientific status — 2026-11-01

### CPVS exact reconstruction: OPEN / UNRESOLVED

- Issue [#170](https://github.com/saeed92m/ztf-classifier/issues/170) remains open and fail-closed.
- The last corrected Seq-space historical comparison reports 781,602 parent objects, 730,184 published members, 741,786 candidates, 730,184 intersection, 11,602 candidate-only, and zero published-only.
- The retained heavy artifact from run [#38635891449](https://github.com/saeed92m/ztf-classifier/actions/runs/38635891449) was rechecked without downloading the multi-gigabyte photometry archives again. Its full candidate-only diagnostics show 11,602/11,602 have `snr_exact=true` in both bands.
- The retained metadata diagnostic partitions the residual: 11,585 fail at least one parent mean-magnitude field; 17 have both mean magnitudes but lack one band-specific period field. This correlation does not prove author intent.
- The 100-object and 1,000-object stratified samples are recorded in `docs/scientific_validation/CPVS_PARENT_SAMPLE_AUDIT_2026-11-01.md`. Reference membership labels in these samples are inferred from the retained audit because raw Table 4 bytes are absent from the retained artifact. They are not a fresh independent membership join.
- PR [#244](https://github.com/saeed92m/ztf-classifier/pull/244) adds a fail-closed candidate × metadata audit, ZTF-name-to-Seq crosswalk tests, VizieR mirror fallback, and compact evidence. It remains Draft. The full heavy source-backed path has not been executed on the latest reviewed head.
- A previous heavy run [#40873746342](https://github.com/saeed92m/ztf-classifier/actions/runs/40873746342) acquired the parent and light-curve sources but failed to acquire Table 4 from the configured CDS endpoints. Its membership comparison is not a fresh valid result.
- No production selector, SNR threshold, model, feature set, class order, v0.2.0 baseline, or acceptance criterion has changed.

**Next scientific gate:** validate the VizieR/Zenodo source fallback on the reviewed PR head, run the full source-backed comparison only after code review and resource approval, verify raw source hashes and object-level IDs, and reconcile all 11,602 residuals. Keep the issue open until source-supported selection semantics or a clearly bounded limitation is established.

### Research compute boundary

Molab/marimo is an optional research and GPU experimentation environment. It is not a runtime dependency for ZTF Classifier and is not the source of truth. GitHub remains the versioned source of truth for code, tests, manifests, and approved model artifacts. A research model or checkpoint must not enter a product release only because a notebook ran successfully. It requires pinned data, configuration, dependencies, metrics, provenance, reproducibility checks, and review. The product remains CPU-first; GPU support is optional and must not become a user requirement.

### Desktop product: active implementation

Issue [#158](https://github.com/saeed92m/ztf-classifier/issues/158) remains the tracked target for a complete scientist-facing desktop product. The acceptance target remains a clean-machine, non-developer workflow on supported operating systems without Python, pip, Git, or terminal use for normal operation. No cross-platform installer acceptance is claimed here.

### Documentation synchronization

This handbook is the current continuity snapshot. The README and scientific/platform roadmaps must link to this version and retain the CPVS claim-specific blocker. Historical handbook versions remain historical records.

**Immutable constraints:** v1.0.1 remains unchanged; scientific baseline v0.2.0 remains frozen; scientific validation stays fail-closed; OOD is not represented as scientific anomaly detection.

## CPVS full membership crosswalk update — 2026-11-01

The full Zenodo membership crosswalk job completed successfully in [CI run 41299576448](https://github.com/saeed92m/ztf-classifier/actions/runs/41299576448) on PR head `7c73a4a9d2260e080300303e6aac826630369539`. It mapped 730,184 unique published ZTF names to 730,184 unique Table 2 Seq IDs, with no unmapped names. A complete comparison against the retained historical candidate set confirms 730,184 intersection, 11,602 candidate-only, and zero published-only. The full result and hashes are in `docs/scientific_validation/CPVS_FULL_ZENODO_MEMBERSHIP_COMPARISON_2026-11-01.md`.

This does not resolve CPVS. The comparison uses the frozen Zenodo membership archive, not raw Table 4 bytes, and it compares against retained historical candidate IDs rather than a fresh full derivation on the current PR head. Issue #170 remains OPEN / UNRESOLVED. No production selection, threshold, model, feature, class order, v0.2.0 baseline, or acceptance criterion changed.


## CPVS raw CDS reconciliation — 2026-11-02

The raw Table 2 and Table 4 files are now verified in GitHub Actions run 41360681445. The raw CDS records match the original IOP/AAS publisher MRT records row by row. The Table 4 ZTF-name-to-Table-2-Seq crosswalk has zero unmapped rows and zero ID/Seq mismatches. Table 4 membership exactly matches the frozen Zenodo membership.

The historical SNR candidate set still has 741,786 IDs. It contains all 730,184 reference members and 11,602 extra IDs. A full-parent diagnostic shows that the intersection of this candidate set with the four-field-positive Table 2 set is exactly the 730,184-object reference. The four-field set alone has 55 nonmembers. This is an empirical conjunction, not proof of the authors' selection rule.

The revised 100-object and 1,000-object deterministic samples include the 55 four-field-only controls. The 1,000-object sample includes all 55. Per-object light-curve SNR diagnostics for these controls are not present in the retained historical artifact. The next action is to reproduce or retrieve their original per-band photometry and identify the failed detection condition.

**Scientific status:** Issue #170 remains OPEN / BLOCKED. PR #244 remains Draft. Do not change the production selector, SNR thresholds, model, features, class order, v0.2.0 baseline, or acceptance criteria. The candidate set has not been freshly re-derived on the current PR head.

