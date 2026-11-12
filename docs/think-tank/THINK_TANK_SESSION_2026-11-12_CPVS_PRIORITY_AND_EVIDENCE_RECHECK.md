# Think Tank Session 07 — CPVS Research Priority, Evidence Recheck and Execution Boundary

**Session ID:** TT-2026-11-12-07  
**Date:** 2026-11-12  
**Scope:** Reconcile the original approved CPVS convergence policy with the current GitHub disposition; independently recheck the retained raw CDS reconciliation artifact; define the next bounded scientific actions  
**Review form:** All 16 simulated specialist seats plus an independent Red Team pass  
**Status:** Research priority reaffirmed; scientific root cause remains unresolved  
**Protected scientific baseline:** v0.2.0 unchanged  
**Product/release boundary:** CPVS remains separate from the DR24-first Park MVP acceptance path

> This is a simulated 16-seat review. It does not claim that 16 external human experts attended.

## 1. Objective

The original user-approved CPVS handoff identifies the 11,602 candidate-only discrepancy as a critical scientific-validation problem and authorizes diagnostic analysis, fixed samples, raw-data provenance work, MGPR investigation and regression protection. A later GitHub disposition states that CPVS is deferred research and is not a DR24-first Park MVP or product-release gate.

These statements are not mutually exclusive if priority is defined correctly:

- CPVS is the project's **P0 scientific research workstream** and the highest-priority unresolved scientific discrepancy.
- CPVS is **not a product critical-path or Park MVP release gate**.
- Research work must not silently block the DR24 product track.
- No selector, threshold, model, benchmark or baseline change is authorized by this priority decision.

## 2. Sources and exact revisions inspected

### Approved Project Sources

- `تایید سیاست همگرایی پروژه.txt` — approved CPVS convergence policy and master handoff.
- `Branch · Branch · Branch · Branch · گزارش وضعیت پروژه (1) (6) (14) (1).txt` — historical evidence and previous diagnostic decisions.
- `تعیین اعضای اتاق فکر.txt` — original 16-seat Think Tank and 12-stage process.

The CPVS policy explicitly authorizes diagnostic work and requires that no hypothesis become a production selector without scientific proof. It requires exact object identity, provenance, fixed samples, raw photometry, SNR and MGPR review, and a root-cause classification for all residuals.

### GitHub

- Issue [#170](https://github.com/saeed92m/ztf-classifier/issues/170) — OPEN; current body says DEFERRED RESEARCH and not a Park/product-release gate.
- PR [#265](https://github.com/saeed92m/ztf-classifier/pull/265) — OPEN / DRAFT; 80 commits, 14 changed files; head `64ed7ec34ee2b2aeae919b228a4423dca7f9fdc9`; recorded base SHA `bc85f6c36b28f3c9ddc2b7b5aa00e0256148441c`, while current main is `f681408fae8d8062dd72ff74791872c1590f6ee8`. Treat the branch as stale until its unique changes are compared and safely rebased or reimplemented.
- Raw-SNR run [43097116480](https://github.com/saeed92m/ztf-classifier/actions/runs/43097116480), r-band run [43097116394](https://github.com/saeed92m/ztf-classifier/actions/runs/43097116394), and Seq run [43097116446](https://github.com/saeed92m/ztf-classifier/actions/runs/43097116446) are still QUEUED with no jobs created.
- Historical artifact run [41367972395](https://github.com/saeed92m/ztf-classifier/actions/runs/41367972395), artifact ID `13108147605`.

### Artifact inspected in this session

The retained artifact ZIP was downloaded and independently inspected read-only.

- Artifact size: 177,453,581 bytes.
- Artifact ZIP SHA-256: `130f3db65827afd83f5050e7eb91eb1cf7f6432e85456fd16586c8000a9aa6be`.
- Raw Table 2: 178,986,858 bytes; SHA-256 `2c77c5b6c14811f6abab6e1442ce82c6fb54dbdcfc141954165704fecfcb3881`.
- Raw Table 4: 46,650,697 bytes; SHA-256 `4fa96379d47f851db7ecd80a83986d82201e8718f12ab727b5348a3914374e7d`.
- The artifact's source manifest also records compressed-source hashes and publisher MRT comparisons. The raw CDS rows matched the retained publisher MRT rows byte-for-byte under the documented right-padding comparison.

This is a fresh independent recheck of a retained November 2 artifact. It is **not** a fresh download or raw-light-curve SNR re-derivation.

## 3. Independent object-level recheck

The following values were independently recomputed from the retained Table 2, Table 4 and compact TSV artifacts:

| Check | Recomputed result |
|---|---:|
| Table 2 unique Seq | 781,602 |
| Duplicate Table 2 Seq | 0 |
| Table 4 unique Seq | 730,184 |
| Candidate-only TSV rows | 11,602 |
| Candidate-only unique IDs | 11,602 |
| Candidate-only overlap with Table 4 | 0 |
| Candidate-only IDs present in Table 2 | 11,602 |
| Reconstructed set (C=P\cup R) | 741,786 |
| Published-only (P-C) | 0 |
| Candidate-only (C-P) | 11,602 |
| Four-field-positive parent set (F) | 730,239 |
| Candidate intersection (C\cap F) | 730,184 |
| Four-field-only (F-C) | 55 |
| Four-field-only IDs equal retained 55-control list | Yes |
| Candidate-only objects with all four fields positive | 0 |

The set (C) is reconstructed from the published set plus the retained candidate-only residual list. It is **not** a fresh derivation from the raw g/r light-curve archives.

The independently rechecked parent fields use the official Table 2 fixed-width definitions. The ReadMe defines zero as the null value for the magnitude and per-band period fields. The four-field-positive condition is therefore a metadata diagnostic; it is not a physical membership rule or proof of author intent.

## 4. Rechecked diagnostic clues

### 4.1 Four-field predicate

`gmag > 0 AND rmag > 0 AND Per-g > 0 AND Per-r > 0`

- Parent set F: 730,239.
- Candidate intersection C∩F: 730,184.
- Four-field-only controls F−C: 55.
- Candidate-only residuals passing all four fields: 0.

This exact empirical intersection does not prove that the 2022 paper used the predicate. Keep it diagnostic only.

### 4.2 Minimum observations per band

`Ng >= 11 AND Nr >= 11`

Recomputed directly from Table 2 for the 11,602 retained candidate-only IDs:

- Both bands at least 11: 45.
- At least one band below 11: 11,557.
- Ng below 11: 11,443.
- Nr below 11: 114.
- Both below 11: 0.

This is a strong diagnostic clue. The paper does not state this as a membership rule. Do not add it to production.

### 4.3 Historical candidate diagnostics

The retained candidate-only TSV reports:

- g qualifying-detection median: 5.
- r qualifying-detection median: 118.
- All 11,602 had historical g_snr=true and r_snr=true in that retained diagnostic.
- Both-band zero qualifying flag OR: 10,887.
- Non-zero qualifying flag OR: g=171, r=680.

These values are inherited from the retained historical artifact. They are not a new raw-data SNR execution.

### 4.4 Fixed sample composition

The retained deterministic samples were re-read:

| Stratum | Sample 100 | Sample 1,000 |
|---|---:|---:|
| Reference candidate | 50 | 500 |
| Candidate-only | 25 | 250 |
| Parent neither | 15 | 195 |
| Four-field-only | 10 | 55 |

Sampling uses SHA-256 rank within five strata and seed `ztf-cpvs-fixed-object-sample-v2`. This is diagnostic oversampling, not a prevalence estimator. Preserve the exact samples and report per-stratum outcomes.

### 4.5 55-object raw control

The retained 55-control photometry report is PARTIAL:

- g-band: 1 object has raw photometry; 54 are UNKNOWN.
- r-band: 51 objects have raw photometry; 4 are UNKNOWN.
- Both-band SNR candidate reconstruction: zero.
- No object is reported as a two-band SNR candidate.
- Missing raw data remains UNKNOWN, not FAIL.

## 5. Cost and execution boundary

The raw SNR workflow pins the original Zenodo g/r archives. The script records uncompressed member sizes of:

- g: 5,034,066,142 bytes.
- r: 6,175,667,360 bytes.

Combined uncompressed data exceeds 11.2 GB. The three existing workflows remain queued without jobs. The workflow configuration includes long-running jobs (up to 120 minutes for the raw-SNR workflow).

Do not trigger duplicate multi-gigabyte downloads or repeated long-running Actions jobs without an explicit cost/compute approval. First fix the diagnostic contract and branch freshness. Prefer reuse of pinned artifacts and compact outputs. The bounded 55-control report is partial and cannot replace the full residual analysis.

## 6. Findings from the 16 specialist seats

| Seat | Finding | Required control |
|---|---|---|
| 01 Chief Scientist / PI | The discrepancy remains a critical scientific question. Product scheduling must not erase research priority. | Keep CPVS P0 research; do not call it resolved. |
| 02 ZTF Survey/Data | Source archive and CDS Table 2/4 are distinct datasets with different sizes and identifiers. | Pin source bytes, releases, and native identifiers. |
| 03 Time-Domain Astrophysics | A low number of g detections may affect period reliability, but is not proof of the published selection. | Separate astrophysical interpretation from empirical membership correlation. |
| 04 Statistics/Time Series | Stratified samples cannot estimate population prevalence without weighting. | Report each stratum separately; preserve sample hashes and seed. |
| 05 Astroinformatics/Big Data | The retained artifact supports compact membership checks; raw archive acquisition is a separate high-cost task. | Use immutable manifests and bounded processing. |
| 06 Cross-Match/Identity | Seq 615170/615172 remains an identity investigation, not an established mapping. | Preserve both IDs until coordinate/time/photometry/hash evidence supports a mapping. |
| 07 AI/ML | CPVS membership rules must not change v0.2.0 model or feature semantics. | Keep all selectors diagnostic until validated. |
| 08 Scientific Validation | Artifact membership counts are verified; fresh raw derivation and MGPR are not. | Separate artifact recheck from source-backed scientific PASS. |
| 09 Software Architecture | CPVS diagnostics should be a separate research pipeline, not a hidden product dependency. | Isolate diagnostic outputs and schemas from production inference. |
| 10 Backend/Platform | Long-running archive jobs need bounded retries, status visibility and compact artifact output. | Do not launch repeated queued jobs blindly. |
| 11 MLOps/Security | Reuse pinned artifacts, verify hashes, and avoid unnecessary transfers. | No unapproved large downloads or credentials. |
| 12 QA/Reliability | The current raw-SNR diagnostic needs per-formula confusion summaries and explicit duplicate/overlap accounting. | Add regression tests before expensive execution. |
| 13 Scientific UX | Reports must distinguish VERIFIED, PARTIAL, UNKNOWN and NOT RUN. | No missing-data-as-failure display. |
| 14 Product/Commercialization | CPVS should not block the DR24-first Park MVP. | Maintain separate product and research tracks. |
| 15 Documentation | The original approved handoff and current issue state must both be visible. | Record the dual-priority decision and dated evidence. |
| 16 Independent Red Team | A successful metadata intersection could be misrepresented as reproduced author selection. | Label it as empirical diagnostic correlation, not method reproduction. |

## 7. Red Team findings

1. **Candidate set provenance:** The retained C set is P plus a residual list. It is not a fresh current-main raw-SNR reconstruction.
2. **SNR aggregation:** The existing raw-SNR script calculates multiple per-band formulas, but the combined two-band membership/confusion summary uses only the approximate formula. Separate all-formula outputs are required.
3. **Sampling:** The fixed samples are stratified. Pooled counts must not be presented as population prevalence.
4. **Duplicate accounting:** The metadata loader merges repeated IDs and checks field conflicts, but must explicitly report within-file duplicates and cross-file overlap before merging.
5. **Missingness:** Zero-row band coverage remains UNKNOWN. It must not be interpreted as SNR FAIL.
6. **Seq identity:** No replacement or merge of 615170 and 615172 without independent coordinate, time, photometry and provenance evidence.
7. **MGPR:** No direct MGPR execution evidence is present in the inspected artifact.
8. **Branch risk:** PR #265 is an old research stack. Do not merge or extend it until unique changes are isolated against current main.

## 8. Joint decision

**APPROVE WITH CONDITIONS:**

1. CPVS remains P0 for scientific research and root-cause work.
2. CPVS remains separate from the DR24-first Park MVP and is not a product/release gate.
3. Keep Issue #170 OPEN / UNRESOLVED.
4. Preserve the 11,602 residuals and all 55 four-field-only controls.
5. Keep the four-field predicate and 11-observation rule diagnostic only.
6. Keep v0.2.0, v1.0.1, model, features, taxonomy, benchmark and production selector unchanged.
7. Do not claim raw SNR or MGPR re-derivation from the artifact-only recheck.
8. Do not start repeated >11 GB raw archive workflows without approval.
9. Extract unique PR #265 code into a current-main-based research branch only after reviewing tests, contracts and branch history.
10. Add tests for all three SNR formulas, per-stratum output, duplicate/overlap counts, UNKNOWN states and source hashes before expensive execution.

## 9. Next actions

| Priority | Action | Owner seat | Acceptance |
|---|---|---|---|
| P0-R1 | Update CPVS cycle record and Issue #170 with artifact-only recheck and exact evidence boundary. | 15, 08 | All hashes, counts and limitations recorded. |
| P0-R2 | Reconcile PR #265 against current main; extract only unique diagnostic code. | 09, 10, 12, 16 | No stale stack merge; tests pass on current main. |
| P0-R3 | Correct SNR diagnostic aggregation for approximate, exact and inverse-error formulas. | 04, 05, 12 | Separate g/r/two-band outputs and confusion metrics per formula. |
| P0-R4 | Add explicit duplicate/overlap and per-stratum accounting. | 05, 08, 12 | Synthetic tests cover duplicates, overlaps, missing bands and strata. |
| P0-R5 | Review MGPR input and failure contract before any full execution. | 03, 04, 07, 08 | PASS/FAIL/UNKNOWN/ERROR states and numerical diagnostics defined. |
| P0-R6 | Obtain authorization before >11.2 GB raw archive transfer and long Actions runs. | 10, 11, 14 | Cost and execution scope approved. |

## 10. Final status

- Historical membership artifact: **RECHECKED** in this session.
- Exact root cause of the 11,602 discrepancy: **UNRESOLVED**.
- Fresh raw SNR derivation: **NOT EXECUTED**.
- MGPR analysis: **NOT EXECUTED**.
- Fixed sample membership and stratum counts: **RECHECKED**.
- CPVS production selector change: **NOT AUTHORIZED**.
- Product/Park release gate: **NOT BLOCKED BY CPVS**.
- CPVS scientific research priority: **P0**.

This session updates priority and evidence traceability. It does not resolve the scientific discrepancy or authorize a production algorithm change.
