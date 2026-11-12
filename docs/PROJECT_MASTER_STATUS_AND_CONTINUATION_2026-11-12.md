# ZTF Classifier — Unified Project Baseline & Continuation Point

**Snapshot date:** 2026-11-12  
**Repository:** https://github.com/saeed92m/ztf-classifier  
**Verified `main` HEAD:** `f681408fae8d8062dd72ff74791872c1590f6ee8`  
**Software release:** `v1.0.1` (published; immutable)  
**Scientific baseline:** `v0.2.0` (frozen; immutable)  
**Document status:** Current evidence-based handoff; supersedes older undated/current-status summaries, but does not rewrite historical reports.  
**Scope:** Scientific core, product, data, source adapters, engineering, research, governance, Notion alignment, and the 16-role review process.

> This document is a dated integration point. It is not a claim that the full platform has passed acceptance. It distinguishes merged code, tested engineering behavior, scientifically validated behavior, proposals, and unresolved research.

## 1. Executive disposition

ZTF Classifier is a CPU-first, cross-platform Astronomical Data Analysis & Discovery Platform. The current scientific core and software release remain protected. The most recent work delivered a meaningful DR24 raw-data acquisition and inspection foundation. It did not yet deliver a complete DR24 scientific analysis and inference workflow.

**The primary delivery track is the Park prototype (Issue #158), with DR24 application integration (Issue #253) as its immediate technical dependency.** The application observation service must support an explicit DR24 backend. It currently constructs the ALeRCE path directly. The application must not silently fall back to ALeRCE when a user selects DR24.

The next product acceptance action is a bounded, pinned end-to-end run for 5–10 confirmed astrophysical sources. The run must preserve native data, identity state, QC decisions, provenance, export, hashes, and offline replay. After that, run the 30–50 source guided demonstration. These tests do not replace the separate Park target of at least 100,000 provenance-recorded labeled light curves.

CPVS exact historical reconstruction remains unresolved and is deferred research. It is not a blocker for the DR24-first Park MVP. The exact v0.2.0 baseline, feature schema, class order, model identity, reference labels, and release artifacts remain unchanged.

AOIC and CIN are proposed, separately staged subsystems. Neither has a production runtime. CIN must not delay the Park MVP.

## 2. Authority and evidence rules

Use this source order when records disagree:

1. Original external scientific source bytes, publisher documentation, and independently verified source artifacts.
2. The exact repository commit, code, configuration, and workflow artifacts that produced a result.
3. The latest dated GitHub issue/PR evidence tied to a specific commit, run, or artifact.
4. Current canonical repository contracts and this dated status snapshot.
5. Notion handbooks, status pages, and Knowledge Base entries, after checking their dates and evidence references.
6. Historical reports, old handbook versions, project proposals, and conversation summaries.

A newer edit timestamp does not automatically supersede older evidence. A claim is current only when it has a traceable source, revision, run, or explicit decision.

Use these statuses consistently:

- **VERIFIED:** source or result was directly inspected and has a traceable revision/hash.
- **ENGINEERING-PASS:** defined software behavior passed its tests. This does not establish scientific validity.
- **SCIENTIFIC-PASS:** the declared scientific protocol and independent evidence gates passed.
- **PROPOSED:** architecture or feature design only.
- **PARTIAL:** some required evidence exists; acceptance criteria remain open.
- **UNKNOWN:** evidence is absent or insufficient. Missing data is not a FAIL.
- **UNRESOLVED / BLOCKED:** a required question has no supported resolution.
- **DEFERRED RESEARCH:** preserve the question and evidence, but do not place it on the active product critical path.

Never change an old report to make it appear current. Add a dated correction or superseding record. Keep raw scientific inputs outside Git. Version manifests, code, schemas, hashes, methods, and compact evidence.

## 3. Frozen scientific and software baselines

| Item | Protected baseline |
|---|---|
| Scientific baseline | `v0.2.0`, immutable |
| Software release | `v1.0.1`, published and immutable |
| Model | XGBoost, `baseline_v0.2` |
| Benchmark | 150 objects; 15 ALeRCE reference classes; 10 objects per class |
| Features | `final_feature_set_v0.2`; 42 features |
| Historical cutoff | MJD 59447.224132 |
| Class order | Frozen; preserve the established 15-class ordering |
| Label semantics | ALeRCE labels are reference/weak labels, not independent astrophysical ground truth |
| Production artifact | Frozen v0.2 production artifact is expected to use artifact schema 1.0 |
| Later diagnostics | Schema 1.1/lab-smoke artifacts are not substitutes for the frozen production artifact |
| Runtime target | CPU-first; Windows, macOS, Linux; normal users should not need Python, Git, or a terminal |

Do not mix software release version, scientific baseline version, model version, CLI/API output schema, and artifact schema. They are different version domains.

**Artifact availability blocker:** PR #278 added a read-only local audit script and regression tests. The script does not prove the local artifact exists. The user's WSL audit has not been run in this status review. The original production artifact remains **UNRECOVERED / NOT AUTHENTICATED** from the accessible evidence. Its expected directory is `runs/model_baseline_v0.2_production/artifact/`. The audit requires schema 1.0 and checks the artifact's internal manifest/file hashes. Internal consistency does not authenticate it against a trusted original external hash. The separate 2026-10-27 lab-smoke artifact uses schema 1.1 and must never be copied or linked into the production path.

The merged audit command is:

```bash
cd ~/projects/ztf-classifier
python scripts/audit_scientific_artifacts.py
```

Expected output: `reports/scientific_validation/local_scientific_artifact_audit.json`. Share only this JSON report. Do not upload model weights, raw light curves, credentials, or large datasets.

## 4. Latest verified repository state

The repository is public, not archived, and uses `main` as its default branch. The linked GitHub account reports push, maintain, and admin permissions. The inspected `main` commit is:

- SHA: `f681408fae8d8062dd72ff74791872c1590f6ee8`
- Date: 2026-11-11 22:46:55 UTC
- Message: read-only v0.2 artifact audit, including the Zubercal DR20 adapter and audit hardening.

### 4.1 Merged delivery chain

The following PRs are merged into `main`:

| PR | Merged capability | Verified boundary |
|---|---|---|
| [#264](https://github.com/saeed92m/ztf-classifier/pull/264) | Bounded native DR24 Lightcurves HATS adapter | Raw source-native retrieval; no production normalization or inference |
| [#273](https://github.com/saeed92m/ztf-classifier/pull/273) | Bounded multi-OID API | Raw retrieval and API contract |
| [#274](https://github.com/saeed92m/ztf-classifier/pull/274) | Raw-preserving diagnostic QC | Descriptive diagnostics; not an approved production filter |
| [#275](https://github.com/saeed92m/ztf-classifier/pull/275) | HATS / Zubercal product contract | Separate source products and semantics |
| [#276](https://github.com/saeed92m/ztf-classifier/pull/276) | Multi-OID Workbench Explorer | Bounded browser workflow for OID inspection |
| [#277](https://github.com/saeed92m/ztf-classifier/pull/277) | Ambiguity-preserving Zubercal DR20 adapter | Retains all candidate PS1 matches; does not select one |
| [#278](https://github.com/saeed92m/ztf-classifier/pull/278) | Read-only frozen-artifact audit | Inventory and internal hash checks; local execution still required |

The merged sequence proves that these code paths exist in `main`. It does not prove end-to-end scientific acceptance.

### 4.2 DR24 and Zubercal contracts

**DR24 HATS** is the primary native ZTF light-curve discovery stream. The adapter preserves source-native HMJD, magnitude, magnitude error, color coefficient, catflags, OID/filter/field/RCID metadata, retrieval context, and payload hashes.

**Zubercal DR20** is a separate supplementary recalibrated PSF-photometry stream. It uses PS1 object IDs, MJD(TDB), its own flag/info semantics, and stored magnitude errors scaled by 10,000. It does not cover sources without suitable PS1 matches. Never treat its IDs, times, flags, units, or magnitudes as equivalent to DR24 HATS fields.

A bounded Zubercal probe returned 123 rows and two candidate PS1 IDs for one ZTF OID. The observed state was `AMBIGUOUS_MULTIPLE_PS1_IDS`; the adapter preserved both and set the decision to `NOT_SELECTED`. This is a demonstrated ambiguity, not an identity resolution or photometric parity result.

Keep DR24 HMJD and Zubercal MJD(TDB) separate until a validated time transformation exists. Preserve raw values. Do not send either stream into the frozen 42-feature model until the feature mapping, time rules, photometric semantics, identity, and leakage controls have passed independent validation.

### 4.3 Current engineering test evidence

- PR #264 exact-head suite: 666 passed, 10 skipped, 9 warnings. CodeQL, Product Scope, build/package, dependency, and other listed engineering jobs passed. Its source-backed scientific jobs were skipped.
- PR #277 exact-head suite: 698 passed, 12 skipped, 9 warnings; the bounded one-object live Zubercal parity test passed. This is adapter evidence, not cross-match validation.
- PR #278 focused artifact-audit regression tests: 4/4 passed. The actual local WSL artifact audit remains pending.
- PR #266 documentation branch reported 642 passed, 10 skipped, 9 warnings and eight passing CI jobs. It remains a draft PR, not part of `main`.

The 10–12 skipped tests depend on external/frozen scientific artifacts or source data. A green CI result with skipped source-backed jobs is not a Scientific-PASS. Do not describe a contract-only workflow as a scientific validation run.

## 5. Product acceptance and active critical path

**Primary tracker:** [Issue #158 — Park prototype and cross-platform product](https://github.com/saeed92m/ztf-classifier/issues/158)  
**DR24 application integration:** [Issue #253](https://github.com/saeed92m/ztf-classifier/issues/253)

### 5.1 Verified current state

- Raw DR24 adapter, bounded API, diagnostic QC, multi-OID Explorer, and Zubercal adapter are merged.
- Bounded live-source tests and browser tests passed for the declared OIDs.
- The Park Pilot v0.5 evidence package covers 30 OIDs and 4,046 epochs. All records are g-band from one partition/field/RCID. These are not 30 confirmed independent astrophysical sources.
- A separate r-band OID has 123 epochs, but its physical-source relationship to the g-band group is not established.
- The complete 150-row Objects Table is absent from the archived demo evidence package.
- The current application observation service still constructs the ALeRCE path directly. DR24 is not yet an explicit, selectable application backend.
- No silent ALeRCE fallback is acceptable when a user selects DR24.
- Raw inspection and descriptive QC are not production feature generation, normalized photometry, inference, or scientific anomaly detection.

### 5.2 Park acceptance outputs

Issue #158 requires a reproducible, provenance-recorded DR24 labeled subset targeting at least 100,000 light curves; source identity and cross-filter grouping; a documented preprocessing/feature pipeline; a measured CPU-first baseline and main model; leakage-safe temporal evaluation; calibrated probabilities; explicit abstention; anomaly outputs separated from OOD; dashboard/API; catalog/report export; run manifest; and demonstration procedure.

Define the unit behind the 100,000 target. Do not interchange:
- ZTF OID count;
- per-filter light-curve count;
- unique astrophysical source-group count;
- exposure/detection row count.

The bounded engineering sequence is separate:
1. 5–10 confirmed-source end-to-end acceptance.
2. 30–50 confirmed-source guided demonstration.
3. The ≥100,000 light-curve labeled Park dataset and scientific evaluation.

### 5.3 Immediate implementation order

1. Define and test the application observation-service interface.
2. Add explicit DR24 HATS backend selection to the application.
3. Keep the ALeRCE backend as a separate explicit option; prohibit silent fallback.
4. Preserve OID, filter, field, quadrant, source-native units, times, flags, and raw response.
5. Implement identity review and ambiguity states. Do not merge OIDs automatically.
6. Define versioned time, photometry, normalization, and QC contracts. Preserve native data and log every exclusion.
7. Run one pinned 5–10 source end-to-end application/API workflow: acquisition → source/identity review → raw-preserving QC → visualization → output/export → manifest/hashes → offline replay.
8. Expand to 30–50 confirmed astrophysical sources.
9. Build the labeled DR24 subset and complete object-disjoint and temporal validation.
10. Only then evaluate the DR24 feature mapping, model inference, calibration, conformal output, OOD, and scientific anomaly analysis.

## 6. Scientific validation and CPVS

### 6.1 CPVS disposition

**Issues:** [#170](https://github.com/saeed92m/ztf-classifier/issues/170) and [#180](https://github.com/saeed92m/ztf-classifier/issues/180)  
**Disposition:** OPEN / UNRESOLVED / DEFERRED RESEARCH  
**Product impact:** not on the DR24-first Park critical path.

The latest 2026-11-11 independent re-analysis verified the raw CDS Table 2 and Table 4 file hashes:

- Table 2 SHA-256: `2c77c5b6c14811f6abab6e1442ce82c6fb54dbdcfc141954165704fecfcb3881`
- Table 4 SHA-256: `4fa96379d47f851db7ecd80a83986d82201e8718f12ab727b5348a3914374e7d`

Compressed source files matched their recorded hashes and decompressed byte-for-byte to those raw files. The Table 4 ZTF-name-to-Table-2-Seq crosswalk has 730,184 mapped members, zero unmapped names, and zero duplicate names.

The retained historical candidate set is not a fresh derivation on current `main`. For this retained evidence:

| Set | Meaning | Count |
|---|---|---:|
| Parent | Table 2 unique Seq IDs | 781,602 |
| P | Published Table 4 membership mapped to Table 2 Seq | 730,184 |
| C | Retained historical candidate set (published members plus retained extras) | 741,786 |
| C ∩ P | Intersection | 730,184 |
| C − P | Candidate-only | 11,602 |
| P − C | Published-only | 0 |
| F | Table 2 rows with finite positive gmag, rmag, Per-g, Per-r | 730,239 |
| C ∩ F | Diagnostic intersection | 730,184 |
| F − C | Four-field-positive controls | 55 |

The value 730,239 is the size of F. It is not the size of C ∩ F.

The four-field predicate reproduces the published set when intersected with this retained historical candidate set. It is an empirical diagnostic. The paper and Table 4 ReadMe do not explicitly establish that all four fields were mandatory publisher selection filters. Do not promote it to a production rule. A separate `Ng >= 11 AND Nr >= 11` diagnostic is also not an approved publisher rule.

The latest corrected raw-archive status for the 55 four-field-positive controls is:

- g band: PASS 1, FAIL 0, UNKNOWN 54.
- r band: PASS 51, FAIL 0, UNKNOWN 4.
- joint two-band status: PASS 0, FAIL 0, UNKNOWN 55.

Earlier reports counted missing archive rows as SNR failures. That was incorrect. Missing data is UNKNOWN. FAIL requires observed raw rows that demonstrably do not meet the declared threshold.

A separate deterministic 1,000-object control sample was selected from the 51,418 parent objects outside Table 4. Seed: `ztf-cpvs-nonmember-control-v1-2026-11-11`. It contains 1,000 unique IDs and zero published members. TSV SHA-256: `0accb53fa41bab1f03b2fc259b68ec1d1e40f6d94decbf59459bb67263a560e9`; sorted ID-list SHA-256: `698c5f93850f9bfdf8c34fc4fe5b48ff9abfdd4d66570084c51826dceada4b46`. Raw g/r archive coverage and SNR are UNKNOWN for this sample because its source archives were not included in the retained artifact.

Separate archive-integrity leads remain:
- 91 g-band Seq-level count mismatches and a net 4,916-row difference.
- An earlier r-band comparison found a +718-row difference between archive rows and summed Table 2 Nr.
- Seq 615170 has no inspected rows under that ID, while orphan Seq 615172 has a matching row count in g and r and a coordinate separation near 0.52 arcsec. This is a strong identity lead, not proof. No ID remapping is authorized.

**The 11,602 residuals are not explained.** The current candidate set must be freshly derived on current code and pinned source inputs. The fixed 100-object, stratified 1,000-object, and separate 1,000 nonmember-control cohorts must be retained separately. Re-run raw g/r coverage, finite-SNR and full-versus-batch object-level checks. Report false positives/negatives only relative to the published membership reference, not astrophysical truth. Keep all missing raw data UNKNOWN.

Older run records contain 11,604 extras. That figure belongs to an earlier revision/input space and must not replace the current retained 11,602 comparison. Do not merge figures from different source hashes or code revisions.

No CPVS selector, threshold, class rule, model, feature, v0.2.0 baseline, or release was changed.

### 6.2 Product scientific-validation gate

Keep two lanes separate:
- **Product Scientific Validation:** validates the actual DR24 application workflow and the declared production inference path. This remains incomplete.
- **CPVS historical reproduction:** an external claim-specific research investigation. It remains unresolved but does not block the DR24-first Park MVP.

## 7. Other scientific and architecture workstreams

### 7.1 Frozen model artifact and skipped tests

PR #278 provides a local read-only audit. The real WSL audit and the dependent integration tests remain outstanding. Do not rebuild the frozen model or substitute the lab-smoke model. Recover the original model, feature dataset, ALeRCE raw cache, and folds from an authoritative source, with hashes and provenance. If they cannot be recovered, preserve the blocker. Any replacement baseline requires a new, explicit scientific versioning and acceptance process.

### 7.2 OOD and missing-data work

- [PR #279](https://github.com/saeed92m/ztf-classifier/pull/279) proposes per-row data-adequacy/OOD-basis diagnostics.
- [PR #280](https://github.com/saeed92m/ztf-classifier/pull/280) contains a missing-feature sensitivity experiment.

The experiment found missingness patterns consistent with the extraction record for the frozen 150-object matrix: 59 complete, 91 partial, and 0 unmatched. In diagnostic masking tests, missing features suppressed baseline top-percentile flags. The experiment uses reconstructed OOD components from the feature matrix, not byte-identical verified production model artifacts; it has no independent astrophysical OOD labels and must not set a production threshold. These PRs are draft and based on an older `main` commit. Rebase and validate before merge.

OOD, scientific anomaly, data adequacy, classification uncertainty, calibration, and conformal prediction are separate outputs.

### 7.3 AOIC — identity and cross-match

- **Issue:** [#249](https://github.com/saeed92m/ztf-classifier/issues/249)
- **Architecture:** merged in PR #261; design only.
- **Status:** PROPOSED, not implemented.

AOIC must distinguish canonical source/entity, catalog entry/alias, detection, observation, transient event, dataset, and analysis run. Preserve all external identifiers. Matching must be epoch-aware, uncertainty-aware, and evidence-based. Use confirmed, ambiguous, unmatched, rejected, and superseded states. Add a decision ledger and reversible merge/split lineage. Positional proximity alone is not proof of identity. ZTF OID is not a global astrophysical source ID.

### 7.4 CIN — Cosmic Intelligence Network

- **Issue:** [#251](https://github.com/saeed92m/ztf-classifier/issues/251)
- **Draft architecture PR:** [#252](https://github.com/saeed92m/ztf-classifier/pull/252)
- **Canonical source:** `ZTF-CIN-ARCH-001`, version 1.0.0.
- **Status:** PROPOSED; no production runtime or pilot.

CIN is a separate human contribution and annotation infrastructure. It will support small scientific tasks, pairwise comparison, annotation, contributor quality estimation, consensus, human–AI disagreement, expert review, provenance, and curated dataset versions.

Keep these data domains separate: original observations; derived features; machine predictions; raw human contributions; aggregated human assessments; expert-reviewed annotations; curated research datasets; training datasets; frozen benchmarks. Crowdsourced labels must not enter the frozen 150-object benchmark or automatically retrain production models. Consensus is not ground truth. ZTF Classifier must remain useful without CIN. Build CIN only after the Park product path and the data governance contracts are stable.

## 8. 16-role continuous think tank

The 16-seat panel is a standing review method, not evidence that 16 external experts have been recruited. Use independent roles, structured disagreement, and a final red-team challenge.

| # | Role | Required review |
|---:|---|---|
| 1 | Chief Scientist / PI | Scientific objective, claims, acceptance decisions |
| 2 | ZTF data and survey expert | Source schemas, release, data semantics and cadence |
| 3 | Variable/transient astrophysicist | Class meaning, physical interpretation, artifacts |
| 4 | Astronomical statistician / time-series expert | Sampling, uncertainty, period and temporal methods |
| 5 | Astroinformatics / data engineer | Ingestion, storage, scale, data provenance |
| 6 | Catalog and cross-match expert | Identifier semantics, match uncertainty, catalog roles |
| 7 | ML lead | Features, model selection, calibration, inference |
| 8 | Scientific validation / benchmark expert | Leakage, splits, reference roles, evidence gates |
| 9 | Scientific software architect | Core boundaries, contracts, extensibility |
| 10 | Backend / platform engineer | Application services, API, persistence, integration |
| 11 | MLOps / DevOps / security engineer | CI, artifacts, packaging, secrets, supply chain |
| 12 | QA / reliability engineer | Regression, integration, platform and failure tests |
| 13 | Scientific UX/UI designer | Workbench, visualization, interpretation and accessibility |
| 14 | Product manager / commercialization | User needs, Park deliverables, scope and value |
| 15 | Scientific documentation lead | Methods, handbook, model/data cards, releases |
| 16 | Independent evaluator / red team | Counter-evidence, hidden assumptions, failure modes |

For each major decision or pull request:
1. Give the relevant source files and exact task to each role.
2. Ask each role for facts, assumptions, counter-evidence, risks, and tests.
3. Record disagreements. Do not force artificial consensus.
4. Let the Chief Scientist and validation expert decide scientific acceptance.
5. Let the software architect and reliability expert decide engineering acceptance.
6. Require the independent evaluator to challenge the final claim.
7. Store the decision, evidence, code revision, hashes, and regression tests.

Simulated role reviews are useful design analysis. They are not a substitute for external peer review or expert sign-off.

## 9. Notion and documentation convergence

Notion contains Handbook v3.0 (2026-10-23), a project Knowledge Base, Park Pilot Readiness, CPVS audit pages, AOIC/CIN notes, glossary, and older status pages. They are useful records, but they do not all reflect the merged PR chain through 2026-11-11.

The GitHub repository contains many historical handbook snapshots (v1.1–v2.8); a v2.9 status copy exists in the open draft PR #266. Older status reports dated 2026-11-03 and audits dated 2026-11-04 are historical evidence, not current status.

Use this document as the current dated continuation point. Keep the historical PDFs as submitted institutional records. The latest Persian Park technical addendum from PR #266 must be rebased and reviewed before it becomes canonical. Do not replace the original proposal or presentation PDF silently.

Corrected documentation facts:
- Current software release is v1.0.1, not v1.0.0.
- Current retained CPVS candidate-only value is 11,602, not the old 11,604 figure.
- 730,239 is the size of the four-field-positive Table 2 diagnostic set; the intersection with retained C is 730,184.
- Missing raw archive rows are UNKNOWN, not SNR FAIL.
- HATS and Zubercal are separate data products.
- A merged adapter or passing contract test is not end-to-end scientific acceptance.
- AOIC and CIN remain proposed.
- Park MVP remains open.

## 10. Open PR and issue control

### Current work to review/rebase

| PR | Status in this review | Action |
|---|---|---|
| #279, #280 | Draft/open; old base SHA `bc85f6c...` | Rebase on current main; review experiments separately; do not set thresholds |
| #265 | Draft/open; CPVS raw Seq identity investigation | Continue only as bounded research; complete source-level checks |
| #266 | Draft/open; Park docs/addendum; old base | Rebase; update status and remove superseded PR references |
| #268, #269, #270 | Draft/open; overlapping DR24 evidence branches | Compare against merged #264/#273/#276; retain only unique evidence |
| #252 | Draft/open; old CIN docs branch | Keep proposal; rebase only after product priority review |
| #244 and older CPVS PRs | Draft/open or non-mergeable historical branches | Do not merge as a stack; extract useful evidence into #170/#180 and close only after owner review |

The repository search surfaced 27 open PR records, including old stacked PRs. Open state alone does not mean work is active. Several older PRs have obsolete base commits or duplicate work. Do not mass-merge, close, or delete them. The current canonical trackers are Issues #158, #253, #249, #251, #170, and #180, plus the distinct operational test Issue #222.

### Priority issues

- **P0 product:** #158, #253.
- **P1 identity design:** #249.
- **P1 model/artifact diagnostics:** #279, #280 after rebase and review.
- **Deferred research:** #170, #180, with #265 as a bounded archive-identity investigation.
- **Future subsystem:** #251 CIN.
- **Separate operational smoke test:** #222; exactly 100 object-level inputs and full accounting, not a benchmark.

## 11. Consolidated execution roadmap

### Phase A — Integrate DR24 into the application
Deliver: selectable backend, no silent fallback, pinned 5–10 confirmed-source workflow, raw-preserving QC, provenance/export/offline replay.  
Exit: every source and failure is accounted for; identity ambiguity remains explicit.

### Phase B — Establish AOIC minimum contracts
Deliver: stable object IDs, catalog aliases, OID grouping decisions, epoch/uncertainty-aware cross-match and review queue.  
Exit: deterministic fixtures, ambiguity tests, and an adjudicated validation sample. No forced identity.

### Phase C — Approve DR24 scientific normalization
Deliver: time transformation, photometric conversion/color, unit semantics, versioned QC policy, feature-input contract, row-level exclusion reasons.  
Exit: independent source-parity tests and documented scientific review.

### Phase D — Build the labeled data cohort
Deliver: definition of a light curve, source group, observation and label; provenance manifest; duplicate and leakage audit; target cohort.  
Exit: measured count and composition; no unsupported claim about 100,000 unique astrophysical objects.

### Phase E — Scientific model evaluation
Deliver: baseline comparisons, object-disjoint and temporal validation, per-class metrics, calibration, abstention, OOD and anomaly evaluations.  
Exit: independent evidence; unknown outputs remain explicit; no leakage.

### Phase F — Park demonstration and handover
Deliver: 30–50 confirmed-source guided demonstration, technical report, catalog, reproducibility bundle, offline replay, demo script and Persian acceptance addendum.  
Exit: Park acceptance authority can reproduce the declared workflow.

### Phase G — Product distribution
Deliver: Windows, macOS, and Linux packaging, clean-machine tests, upgrades, uninstall/rollback, offline operation, help and troubleshooting.  
Exit: non-developer scientist can complete the declared workflow without Python, pip, Git, or terminal.

### Phase H — CIN and broader survey integrations
Deliver only after governance, user need, operating cost, and independent validation justify them. Keep CIN modular and separate from the scientific core. Treat TESS, Gaia, Rubin/LSST, JWST and other surveys as future adapters, not current capabilities or partnerships.

## 12. Institutional proposal, business model, and commercialization boundary

The two submitted Persian institutional documents define the original positioning and proposed business path. They are planning evidence. They do not prove current customers, revenue, grants, market validation, or completed product acceptance.

### 12.1 Institutional positioning

The proposal was prepared for **Pishgaman Novandish Fanavargostar Keyhan LLC**, the East Azerbaijan Science and Technology Park, and the Innovation and Prosperity Fund. It positions the product as software for astronomical data analysis and discovery using public ZTF data. It does not require the company to own or operate a telescope.

The value proposition is not to replace global brokers such as ALeRCE or SNAD. It is to provide an inspectable analysis layer with calibrated confidence, uncertainty, explicit abstention, anomaly investigation, provenance, and reproducible reports.

Public data can remove telescope acquisition costs. It does not remove staff, compute, storage, networking, maintenance, data-rights review, or support costs.

### 12.2 Target customers and market path

The dossier identifies:
- Primary segment: domestic astronomical research groups, universities, and scientific data centers.
- Secondary segment: international astronomical brokers, surveys, and research consortia, including future ZTF/Rubin-related workflows where compatible.
- Early value: targeted scientific analysis, classification and uncertainty assessment, candidate prioritization, and reproducible custom reports.

These are target segments, not verified demand or signed partnerships. This review found no evidence of a customer contract, paid pilot, letter of intent, or institutional partnership.

### 12.3 Proposed revenue channels

The business plan proposes:
1. Custom research and data-analysis services.
2. Machine-learning and scientific-data consulting.
3. Subscription or recurring service access.
4. Maintenance and support contracts.
5. Research collaborations and service agreements.

The dossier sets a **month 16–18 target** of at least one revenue-generating contract or cooperation memorandum. This is a planning target, not an achieved outcome.

The proposed institutional path begins with a prototype/incubation-stage company. The plan allows a later move toward a service-oriented classification after stable revenue. Any knowledge-based-company classification, park support, loan, guarantee, or Innovation Fund facility depends on separate assessment and current call conditions. No funding award is established by this review.

### 12.4 Team, schedule, and financial assumptions

The technical dossier uses a **four-to-five-person team** as a six-month planning assumption. It identifies technical staffing as the largest relative cost category (about 50% in the planning model). Other cost categories cover infrastructure, compute/hosting, administration, and establishment costs. These are relative assumptions. They are not current payroll, a verified budget, or guaranteed prices.

The proposed break-even definition is monthly contract revenue sufficient to cover fixed team and infrastructure costs. Customer acquisition cost (CAC) and customer lifetime value (LTV) are proposed measures. They cannot be calculated until actual sales, retention, pricing, and delivery-cost data exist.

### 12.5 Commercialization risks and controls

The proposal identifies a small team, limited compute, no exclusive observational data, dependence on public sources, international competition, funding delays, and the need to establish scientific credibility as risks.

Controls:
- Start with a narrow and reproducible DR24 workflow. Do not claim that the current product processes the full ZTF archive in production.
- Demonstrate value through uncertainty, traceability, and source-backed evidence. Do not make unsupported accuracy comparisons.
- Validate customer needs before finalizing pricing.
- Track delivery, network, storage, compute, and support costs for each pilot.
- Do not describe public data as zero-cost operations.
- Do not announce funding, partnerships, paid customers, or revenue without documentary evidence.
- Define every service by source, population, version, input contract, output, limitations, and acceptance criteria.

### 12.6 Commercialization acceptance gates

A credible commercial milestone should contain:
- A reproducible demonstration for a defined customer workflow.
- A written scope, user/customer, data rights, delivery terms, and acceptance criteria.
- A documented price and cost basis.
- Measured delivery and support effort.
- A signed contract, paid pilot, or formal cooperation record before reporting commercial traction.
- Security, privacy, data-retention, and service-support terms where customer data or accounts are involved.

Keep the original PDFs as immutable institutional proposal records. Use dated addenda when the product scope or evidence changes. Do not silently rewrite submitted documents to make proposed capabilities appear implemented.

## 13. Immediate next actions

1. Recover and independently authenticate the frozen v0.2.0 production artifact through the controlled recovery tracker [Issue #282](https://github.com/saeed92m/ztf-classifier/issues/282). Use a local read-only inventory only if the artifact is known to exist solely in a local checkout; it is not a routine prerequisite for continuing repository-side work.
2. Inspect the actual application observation-service implementation and define the DR24 backend selection contract.
3. Create a pinned 5–10 confirmed-source E2E manifest with exact IDs, filters, source version, query parameters, and expected outcomes.
4. Validate raw-source handling, QC semantics, HMJD and photometry contracts without changing the frozen model.
5. Rebase and triage open PRs against `f681408...`; remove duplicate work from the active queue after review.
6. Rebase PR #266 and align the Persian Park status addendum with the merged PR chain.
7. Update the Notion Handbook/Knowledge Base from this dated source. Preserve old pages as historical versions.
8. Keep the 16-role think tank attached to every architecture, science, product, and release decision.

## 14. Acceptance and change control

No percentage-complete figure is assigned in this document. The current evidence does not support one consistent denominator across product, scientific, infrastructure, and research scope.

A milestone is complete only when its exact acceptance criteria, source versions, run artifacts, hashes, test results, known limitations, and approval are recorded. Code presence, a green CI badge, a matching row count, model confidence, or an OOD flag cannot independently establish scientific success.

No changes in this documentation update modify production selection rules, thresholds, model weights, features, taxonomy, class order, benchmark membership, v0.2.0, or v1.0.1.


## 15. Verified CI evidence for this documentation convergence PR

**PR head tested:** `3241955ebb918bd79f9b15263d16f6bf541f00e9`  
**CI run:** [43118116290](https://github.com/saeed92m/ztf-classifier/actions/runs/43118116290)  
**Scientific Validation run:** [43118116243](https://github.com/saeed92m/ztf-classifier/actions/runs/43118116243)  
**Product Scope Audit:** [43118116301](https://github.com/saeed92m/ztf-classifier/actions/runs/43118116301)  
**CodeQL:** [43118116285](https://github.com/saeed92m/ztf-classifier/actions/runs/43118116285)

The completed CI jobs report:
- Format Check: PASS.
- Lint: PASS.
- Cumulative Lifecycle Gate: PASS.
- Test Suite: PASS — 715 collected tests, 0 failures, 0 errors, 13 skipped; runtime 101.819 seconds.
- Runtime Smoke Tests: PASS.
- Build & Verify Package: PASS.
- Dependency Audit: PASS.
- CI Gate: PASS.
- Product Scope Audit: PASS.
- CodeQL Python: PASS.
- Scientific benchmark and cumulative lifecycle contract: PASS.

The retained pytest XML report records 13 skips:
1. Collection skipped: `test_feature_pipeline_parity`.
2. Collection skipped: `test_offline_feature_dataset_reproduction`.
3. Collection skipped: `test_raw_dataset_validation_integration`.
4. DR24 multi-OID workbench browser test requires `ZTF_DR24_BATCH_UI_TEST=1`.
5. Live DR24 HATS parity requires `ZTF_DR24_BATCH_LIVE_TEST=1`.
6–12. Seven production-inference tests skipped because the frozen legacy production artifact or shared model inputs are unavailable.
13. Live Zubercal DR20 adapter parity requires `ZTF_ZUBERCAL_ADAPTER_LIVE_TEST=1`.

Coverage report: 6,468 / 7,761 executable lines, 83.34% line coverage. Branch coverage was not measured (zero branch opportunities were reported by the XML export); do not interpret this as 100% branch coverage.

The four source-backed Scientific Validation jobs for source provenance, DR24/ALeRCE evidence, independent StarEmbed evidence, and frozen historical ALeRCE verification were SKIPPED. This documentation PR therefore has a green engineering CI result, but it does not establish Scientific-PASS, model artifact readiness, DR24 live-source parity, or end-to-end Park MVP acceptance.

The missing frozen v0.2.0 production artifact remains a separate blocker. The repository audit contract expects `runs/model_baseline_v0.2_production/artifact/`, schema 1.0, model version `baseline_v0.2`, 42 frozen features, and manifest-declared file hashes. The schema-1.1 lab-smoke artifact is not a substitute. An independently pinned original artifact hash is still unavailable. See `docs/scientific/LOCAL_ARTIFACT_VALIDATION.md` and `configs/process/cycles/local-scientific-artifact-audit-20261107.json`.


## 16. Historical local artifact inventory — 2026-11-09

A prior WSL audit was recorded in the project conversation on 2026-11-09. It reported:
- The frozen production artifact directory was absent in the inspected checkout.
- The separate 2026-10-27 lab-smoke artifact was present, but it is schema 1.1 and is not eligible to replace the schema-1.0 production artifact.
- The ALeRCE raw-detection Parquet cache was absent.
- The processed feature/config artifacts and four dependent test modules were present.
- The then-current audit summary reported nine production artifact paths missing. The later corrected audit contract requires six core production files and treats three conformal/OOD diagnostics as optional. The older nine-file count must not be interpreted as the current required-file contract.
- A search of accessible Git history and the `release/recover-v1.0.1` branch path did not recover the original production files.

The exact historical JSON report and its full nine-path list are not available in the current mounted project sources. This section preserves the recorded summary and does not claim a fresh filesystem read in this session. The recovery tracker is [Issue #282](https://github.com/saeed92m/ztf-classifier/issues/282). Do not ask the user to repeat the same local inventory unless a new, specific validation requirement arises after remote recovery sources have been exhausted.


## 17. Sixteen-role think-tank review — 2026-11-12

This review uses the 16 proposed expert roles as a structured review method. It does not claim that 16 external human experts participated.

| Role | Review finding | Required control |
|---|---|---|
| Chief Scientist / PI | No Scientific-PASS is established. | No discovery or accuracy claim without independent evidence. |
| ZTF Survey & Data Specialist | DR24 HATS and Zubercal DR20 are distinct products; HMJD and MJD(TDB) differ. | Preserve raw release, band, field, rcid, time basis and hashes. |
| Time-Domain Astrophysicist | A ZTF OID is not necessarily one physical source. | Never merge OIDs without versioned, evidence-backed identity. |
| Statistics / Time-Series Specialist | Irregular sampling, time conversion and photometry need separate contracts. | Validate HMJD, QC and normalization before inference. |
| Astroinformatics / Big Data Architect | Bounded indexed retrieval is preferable to full-archive acquisition. | Keep requests bounded, pinned and reproducible. |
| Catalog / Cross-Match Specialist | Zubercal probe returned multiple PS1 candidates for one position. | Preserve ambiguity; no automatic nearest-match selection. |
| Chief AI / ML Scientist | Frozen v0.2.0 and baseline_v0.2 remain the reference. | ALeRCE remains weak/reference labels; preserve unknown and abstention. |
| Scientific Validation Scientist | 13 tests skipped; source-backed validation jobs skipped. | Green CI is not Scientific-PASS. |
| Principal Software Architect | Raw DR24 adapter is separate from the normalized ALeRCE service. | Add explicit versioned source selection; no silent fallback. |
| Backend / Platform Engineer | Raw DR24 endpoints exist; standard object analysis remains ALeRCE-backed. | Connect application only after time, photometry and QC contracts pass. |
| DevOps / MLOps / Security | Engineering CI passed on the previously tested head; production model absent from accessible repo/release assets. | Recover artifact through trusted source; keep large data out of Git. |
| QA / Reliability | 715 tests, 0 failures, 13 skips; line coverage 83.34%. | Investigate skips; branch coverage is unmeasured. |
| Scientific UX/UI | Multi-OID Explorer supports raw inspection, not full scientific analysis. | Display source, release, filters, counts, missingness and ambiguity. |
| Product Manager / Commercialization | Park MVP is the priority; CIN is not on its critical path. | Keep 5–10 OID, 30–50 object demo and 100k lightcurve target as separate gates. |
| Documentation Lead | Current status and historical records are now linked through a dated master source. | Record each decision with date, SHA, evidence and disposition. |
| Independent Evaluator / Red Team | Main risk is treating skipped tests or lab artifacts as production evidence. | Do not weaken acceptance gates or overstate results. |

### Joint decision

1. Prioritize the DR24-first Park MVP; defer CIN runtime and optional expansion until MVP acceptance.
2. Keep DR24 raw acquisition separate from DR24 model inference. Validate time, photometry, QC, source identity and feature parity independently.
3. Preserve v0.2.0, its 42-feature contract, 150-object/15-class benchmark and v1.0.1 software release.
4. Recover and authenticate the schema-1.0 production artifact through Issue #282. Never substitute schema-1.1 lab-smoke files.
5. Keep the CPVS 11,602 discrepancy unresolved and separate. Do not promote the four-field diagnostic to a production selector.
6. Keep CIN optional; human contributions require governance, privacy, QC and independent evaluation before they can enter research or training datasets.
7. Preserve all CI skips and scientific blockers in the status report. Do not weaken gates to obtain a green workflow.

**Disposition:** development may continue within these boundaries. DR24 inference, scientific acceptance, artifact readiness and discovery claims remain BLOCKED until their own acceptance gates pass.


## 18. Open PR inventory and triage

The read-only GitHub snapshot on 2026-11-12 returned 29 open PRs. Many are historical, stacked on old bases, or duplicate work later integrated through newer PRs. No PR was mass-merged or closed.

See [OPEN_PR_TRIAGE_2026-11-12.md](OPEN_PR_TRIAGE_2026-11-12.md) for the full inventory, current review groups, mergeable flags, dependencies and safe disposition protocol.

The current critical path remains #158/#253; CPVS #170/#180; AOIC #249; CIN #251/#252; artifact recovery #282; documentation convergence #281. Open state and GitHub's mergeable flag do not establish review, validation or acceptance.


## 19. Canonical think-tank, defect and execution documents

The original supplied think-tank source proposed three durable project artifacts. They are now represented by dated, evidence-based repository documents:

- [16-Expert Think Tank Master Review](THINK_TANK_MASTER_REVIEW_2026-11-12.md) — roles, consensus, target architecture and scientific/product boundaries.
- [Master Defect and Risk Register](MASTER_DEFECT_REGISTER_2026-11-12.md) — 18 tracked risk areas with evidence, status, closure criteria and issue links.
- [Master Execution Roadmap](MASTER_EXECUTION_ROADMAP_2026-11-12.md) — seven gated phases from scientific integrity/recovery through final product acceptance, plus separate optional CIN track.
- [Open PR Triage](OPEN_PR_TRIAGE_2026-11-12.md) — 29 open PR snapshot and safe disposition protocol.

These are dated snapshots and must be updated from new evidence, not treated as immutable status. The original source files remain preserved in Project Sources.

**P0 correction:** minimum source identity and association semantics are a critical dependency alongside DR24 application integration. Full AOIC can be staged, but model-ready multi-OID data must not be produced without explicit association evidence and ambiguity states.
