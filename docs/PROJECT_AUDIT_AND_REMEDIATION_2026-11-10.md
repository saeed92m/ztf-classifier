# ZTF Classifier — Full Project Integrity Audit and Remediation Record

**Audit date:** 2026-11-10  
**Repository:** `saeed92m/ztf-classifier`  
**Audited main revision:** `bc85f6c36b28f3c9ddc2b7b5aa00e0256148441c`  
**Software release:** `v1.0.1` (published; immutable)  
**Scientific baseline:** `v0.2.0` (frozen)  
**Primary delivery:** bounded, reproducible ZTF DR24 prototype for the Tabriz Science & Technology Park  
**Scientific blocker:** CPVS exact historical membership remains unresolved.

## 1. Executive disposition

The repository contains a substantial scientific software foundation: a frozen 150-object / 15-class / 42-feature benchmark, an XGBoost baseline, calibration/conformal/OOD components, CLI, API, worker, a Workbench, provenance contracts, and release automation.

The product is **not yet accepted as a complete DR24-backed scientific analysis platform**. The current application observation service on `main` constructs the ALeRCE backend directly. DR24 HATS retrieval and display are being developed in open pull requests. They do not yet prove the complete path from DR24 bytes through identity, QC, normalization, feature generation, inference, uncertainty, exports, and offline replay.

The exact CPVS historical reconstruction remains a separate scientific blocker. The product roadmap correctly separates that research claim from the DR24-first Park delivery. The CPVS blocker must remain open until its source-level evidence is complete.

No model, feature, class order, benchmark, production selector, scientific threshold, release, or baseline artifact was changed by this audit.

## 2. Repository and release snapshot

| Item | Verified state |
|---|---|
| Default branch | `main` |
| Main revision | `bc85f6c36b28f3c9ddc2b7b5aa00e0256148441c` |
| Main branch latest push in inspected history | 2026-11-03 |
| Open pull requests | 42 |
| Open non-PR issues | 15 |
| Latest stable software release | `v1.0.1`, published 2026-10-07 |
| Frozen scientific baseline | `v0.2.0` |
| Production model identity | `baseline_v0.2` |

The main branch has not received a newer push in the inspected snapshot, although scheduled Scientific Validation ran on 2026-11-09. Several important changes remain in draft or stacked pull requests. A green check on a non-merged branch is not a released capability.

The GitHub integration could not read branch-protection settings (HTTP 403). It also did not provide a usable Dependabot-alert listing. These items are **not verified**; this report does not claim that no security alerts or protection gaps exist.

## 3. Scientific baseline and model-artifact availability

The repository manifests confirm the frozen baseline:

- 150 objects, 15 ALeRCE reference classes, 10 objects per class.
- 42 features in `final_feature_set_v0.2`.
- XGBoost model identity `baseline_v0.2`.
- Historical cutoff MJD `59447.224132`.
- Diagnostic artifact schema 1.1, with schema 1.0 compatibility.

The ALeRCE labels are reference/benchmark labels. They are not independent astrophysical ground truth.

The original production artifact at `runs/model_baseline_v0.2_production/artifact` is not present in the repository tree or the published Python wheel. Issue #253 records a local audit in which the original path was missing and no original backup/export location was documented. A separate lab-smoke artifact has some matching file hashes, but different manifest/provenance; it is not an authorized substitute.

Consequences:

1. The original production artifact remains **UNRECOVERED**, not proven destroyed.
2. Seven legacy production-inference tests and three raw-feature/data integration tests remain skipped when their required frozen inputs are absent.
3. These skipped tests are not passed.
4. Do not copy the lab-smoke artifact into the production path or change the frozen baseline to make the tests pass.
5. Recover the exact original artifact through a controlled, hash-verified source, or approve a separately versioned reproduction with a new model identity.

## 4. Latest verified source-backed evidence

### 4.1 Scheduled Scientific Validation on main

Workflow run [42611080798](https://github.com/saeed92m/ztf-classifier/actions/runs/42611080798), on main revision `bc85f6c`, completed with all five jobs successful:

- source-provenance endpoint probe;
- immutable historical ALeRCE reference acquisition and manifest validation;
- benchmark/lifecycle contract validation;
- StarEmbed source-package acquisition;
- DR24 and live ALeRCE evidence acquisition.

The retained artifacts were inspected. Their actual scope is:

| Artifact | Contents | What it establishes |
|---|---|---|
| `scientific-validation-provenance` | Reachability, HTTP status, response hashes for StarEmbed, CPVS Zenodo, DR24 and ALeRCE endpoints | Endpoint reachability and source-response provenance |
| `frozen-reference-evidence-alerce_reference_frozen_20200609` | Immutable ALeRCE archive manifest, MD5/SHA-256 and required member list | Frozen publisher snapshot identity contract |
| `scientific-validation-external-source-evidence` | 150 DR24 Objects Table HATS records and 150 live ALeRCE reference-response rows, with query and content hashes | Bounded catalog/response acquisition and provenance; not epoch-level light curves or model evaluation |
| `scientific-validation-heavy` | StarEmbed train/test/validation/anomaly Parquet files and acquisition manifest | Independent dataset package acquisition; no model training or evaluation was run |

Important details from the retained manifests:

- The DR24 query uses a deterministic lexicographic selection of 150 OIDs from the HATS secondary index. It returns object-catalog fields (`oid`, `ra`, `dec`, `ngoodobsrel`) and a partition manifest. It does not contain nested epoch photometry. It is a bounded engineering sample, not a representative survey sample.
- The live ALeRCE response contains 150 top-ranked classifier-output rows. It is a reference-system response, not independent astrophysical ground truth.
- The frozen ALeRCE artifact is represented in this run by an evidence manifest with the publisher archive MD5/SHA-256 and required member names. The archive members themselves were not included in that 487-byte manifest artifact.
- The StarEmbed manifest pins revision `33046797fb619f93a991aa4e38a9dc36f27e2d24` and the five Parquet file hashes. Its `row_count` is `null`; the workflow verifies artifact presence and provenance, not row-level suitability or model performance.
- The source-provenance probe records HTTP 200 reachability and response hashes. Its own text states that reachability is not benchmark validation or ground truth.

This run proves successful acquisition and evidence-contract execution for the stated scope. It does **not** prove epoch-level DR24 acquisition for those 150 Objects Table records, DR24 model performance, StarEmbed model performance, full-population scientific validation, the 100,000-light-curve target, or Park acceptance. Its workflow conclusion must not be interpreted as a complete scientific acceptance decision.

### 4.2 OOD missingness experiment

PR #280, experiment run [42698425064](https://github.com/saeed92m/ztf-classifier/actions/runs/42698425064), retained artifact `13710761158` (ZIP SHA-256 `bb12f5f6f511e27c4ab2f62c9c76e4825d4a08501ee0e2af96d6c6dc3c26546f`). The downloaded artifact was inspected.

Verified scope and results:

- 150 objects, 42 features; 59 complete rows and 91 partial rows.
- All 150 natural missingness patterns match the recorded v0.2 extraction rules; no unmatched or ambiguous pattern.
- MCAR masking used eight feature-removal levels and 20 deterministic replicates.
- 17 extraction-aligned correlated missingness scenarios were evaluated.
- MCAR removed 65% of baseline 99th-percentile flags with four masked features, 95% with eight, and 100% with twelve.
- The scenario with 2–9 valid observations in both bands removed all baseline flags at the 90th, 95th and 99th reference percentiles in the paired experiment.

Limits:

- Paired masking used only the 59 complete benchmark rows.
- Reference OOD scores are in-sample.
- The model was reconstructed from the frozen feature matrix and OOD configuration. The persisted original production artifact was not loaded; this is not a byte-for-byte artifact replay.
- No independent astrophysical ID/OOD labels were used.
- The result is diagnostic only. It does not define an eligibility threshold or authorize automatic suppression of OOD scores.

PR #279 adds row-level data-adequacy reporting. Its latest CI head reports 648 passed, 10 skipped, 0 failed, 9 warnings and 83% coverage. The 10 skipped tests remain unverified. On that pull-request event, the source-backed DR24/ALeRCE/StarEmbed jobs were skipped.

## 5. DR24 product path

The current `main` implementation in `src/ztf_classifier/application/observations.py` constructs `AlerceDetectionBackend` directly. Therefore the default application observation path is ALeRCE, not DR24 HATS.

The active DR24 work is split across an open review chain:

- PR #264 — bounded provenance-backed DR24 native observation adapter (open, not merged).
- PR #273 — bounded multi-OID raw API (draft).
- PR #274 — raw-preserving QC diagnostics (draft).
- PR #276 — multi-OID Workbench explorer (draft).
- PR #275 — HATS versus Zubercal source-contract decision (draft).
- PR #277 — ambiguity-preserving Zubercal DR20 adapter (draft).
- PR #278 — read-only local artifact audit (draft).

Earlier PRs #267 and #270–#272 target older adapter revisions and are not the current delivery chain.

Source documentation establishes that DR24 HATS Lightcurves contain nested epoch rows with HMJD, magnitude, magnitude error, color coefficient and raw quality flags. ZTF OIDs are defined per filter, field and quadrant; they are not universal physical-source identities. A spatially close match is not proof of identity.

Required unresolved decisions:

1. Preserve OID, filter, field, readout-channel and coordinates.
2. Define a versioned astrophysical source-group identifier and ambiguity states; do not merge OIDs from proximity alone.
3. Preserve native HMJD; do not label it MJD without a validated conversion.
4. Define photometry and color semantics before model normalization.
5. Preserve raw `catflags`; distinguish likely-usable flags from the stricter `catflags == 0` diagnostic. No production mask is approved yet.
6. Keep HATS and Zubercal as separate products and adapters. Do not equate their IDs, time systems, magnitude scales or uncertainties.
7. Do not feed raw DR24 data into the frozen v0.2.0 model until feature parity and leakage-safe evaluation pass.
8. No silent fallback between DR24 and ALeRCE.

Issue #253 and the Park ledger still require a bounded 5–10 confirmed-source end-to-end path, followed by a 30–50 object guided demonstration. The 100,000-light-curve target is a future deliverable, not a current result. The counting unit must be defined (OID, per-filter light curve, or unique astrophysical source group).

## 6. CPVS — unresolved scientific blocker

Issue #170 remains OPEN. The historical Seq-based membership comparison in retained evidence reports:

| Set | Count |
|---|---:|
| Parent Table 2 | 781,602 |
| Published Table 4 | 730,184 |
| Reconstructed two-band SNR candidates | 741,786 |
| Candidate-only | 11,602 |
| Published-only | 0 |

The Table 4 ZTF-name to Table 2 Seq crosswalk is documented as 730,184 mapped names and zero unmapped names. The 11,602 residuals remain unexplained under the published method. Zero published-only IDs does not explain the excess.

### 6.1 Corrected interpretation of the 55-control raw-photometry audit

An earlier note claimed that 0/55 controls passed both SNR thresholds. That conclusion is invalid because the retained archive evidence shows:

- g-band archive rows exist for only 1/55 controls;
- r-band rows exist for 51/55 controls;
- no control has both bands represented in the retained attachments.

Missing raw photometry is **UNKNOWN**, not an SNR failure. The earlier `failed_g_snr` and `failed_r_snr` counters treated missing rows as non-passes and must not be used as evidence that the controls fail SNR. The 55-control audit is PARTIAL and does not independently validate the two-band SNR predicate.

### 6.2 Newly supplied Master Handoff diagnostics — not yet artifact-verified

The user-approved CPVS Master Handoff additionally reports:

- a four-field-positive set of 730,239 objects, with 55 outside the published set and zero published members missing;
- a diagnostic `Ng >= 11 and Nr >= 11` result of 730,229 candidates, leaving 45 candidate-only objects and removing 11,557 of the 11,602 residuals;
- a 45-object breakdown of 17, 4 and 24 objects by metadata completeness;
- a 1,000-object nonmember control sample from the 51,418 nonmembers, in addition to the existing fixed stratified samples.

These are **reported findings from the approved handoff**, not independently re-run results in this audit. The handoff does not attach the complete source/output hashes and commands for these new diagnostics to the current GitHub evidence.

The handoff also contains an internal set-arithmetic inconsistency in Section 4.1: it lists `|F| = 730,239`, `|F \\ P| = 55`, `|P \\ F| = 0`, but also lists `|C ∩ F| = 730,239` while stating `C ∩ F = P` and `|P| = 730,184`. These statements cannot all be true under the same set definitions. Reconcile the actual ID lists and definitions before updating the official diagnostic result.

Neither the four-field rule nor the 11-observation-per-band rule is documented as the publisher's membership predicate. Both remain diagnostic hypotheses. Do not introduce either into the production selector.

### 6.3 Archive identity and row-count anomalies

The approved handoff records a g-band archive/Table 2 difference of 4,916 rows and 91 per-Seq mismatches. It also records the Seq 615170 / 615172 lead: Table 2 lists 132 g and 113 r observations for Seq 615170, while inspected archive rows appear under orphan Seq 615172. The targeted g/r scans and coordinate/time similarities are strong identity leads, not an approved remapping. No SourceID correction is authorized by these counts.

### 6.4 PR and sample limitations

- PR #244 is open and Draft. Its recorded base SHA is `4f98a06...`, while current main is `bc85f6c...`. Its latest listed checks are push-event runs; a current-head pull-request validation after rebasing is not verified.
- PR #265 has successful ordinary CI and a targeted Seq-identity diagnostic. That test is not a full reconciliation of every g/r Seq count and does not explain the 11,602 residuals.
- The fixed 100/1,000 stratified samples reproduced from retained artifacts are not prevalence estimators.
- The approved handoff's separate 1,000-object nonmember control sample from the 51,418 parent nonmembers still needs its exact ID manifest, seed, inclusion method and hashes.
- A full MGPR diagnostic across the required groups has not been verified.

Required CPVS acceptance remains: exact source versions and hashes; full object-level ID crosswalk; all 11,602 object records; reference and nonmember controls; raw g/r epoch traceability; SNR and QC diagnostics; MGPR status; fixed samples; and root-cause/regression evidence. Preserve `PASS`, `FAIL`, `UNKNOWN` and `ERROR` as distinct states.

## 7. Other product subsystems

| Subsystem | Current verified disposition |
|---|---|
| Scientific core | Frozen v0.2.0 contract and 42-feature baseline preserved |
| API / CLI / worker | Implemented; standard CI and runtime smoke tests exist |
| Workbench | API-backed features exist; complete DR24 scientist workflow is not accepted |
| Cross-platform installers | Not verified; v1.0.1 is a Python package, not a self-contained Windows/macOS/Linux installer |
| AOIC | Proposed architecture under Issue #249; no complete canonical identity registry is merged |
| CIN | Architecture and staged plan under Issue #251 / PR #252; no runtime or controlled pilot is claimed |
| Discovery / scientific anomaly | Contracts exist; OOD is not scientific anomaly detection; validated end-to-end discovery remains incomplete |
| Reproducibility / operations | Manifests and hashes exist; one complete Park run bundle and clean-machine replay remain open |
| Institutional submission | Original 13-page presentation and 21-page proposal remain preserved; the 2026-11-07 Persian status addendum is a separate proposed update on PR #266 |

The 5.32-billion figure in the Park dossier describes the DR24 release-scale light-curve volume. It is not the volume processed by this project. The 4–5-person team is a proposed staffing model, not verified current staffing. The current delivery ledger and Persian addendum correctly state these limits.

## 8. Documentation defects found and corrections in this PR

1. `docs/MODEL_CARD.md` identified software release `v1.0.0` and repeated that stale milestone at the end. The current immutable software release is `v1.0.1`; the scientific model remains `baseline_v0.2`.
2. The 2026-11-07 execution ledger and Handbook v2.9 contained an invalid interpretation of the 55-control audit. Both now state that g-band rows exist for 1/55, r-band rows for 51/55, and none has both bands. Missing rows are UNKNOWN, not SNR failure. The Handbook also records the Master Handoff's four-field set-arithmetic conflict and leaves the `Ng/Nr >= 11` result diagnostic-only.
3. The README carried an obsolete 2026-10-11 status block, handbook v2.8 link and superseded row-ordinal narrative. This PR replaces it with the current evidence boundaries and links to the v2.9 handbook, execution ledger and this audit.
4. The approved CPVS Master Handoff's conflicting set arithmetic and new 11-observation diagnostic are recorded as unresolved evidence-reconciliation items, not silently merged into old results.

## 9. Remediation sequence

1. **PR #266 documentation synchronization:** review this audit, corrected ledger, README and Model Card. Run current-head CI, CodeQL, Product Scope Audit and Scientific Validation contract checks.
2. **CPVS evidence recovery:** attach full ID lists, hashes, commands and source manifests for the four-field and `Ng/Nr >= 11` diagnostics; resolve the handoff's set arithmetic; run the separate nonmember control sample.
3. **CPVS archive reconciliation:** complete per-Seq g/r reconciliation and compare raw coordinates/timestamps for 615170/615172. Do not remap automatically.
4. **CPVS MGPR:** execute on declared groups with full logs and `PASS/FAIL/UNKNOWN/ERROR`; do not infer scientific failure from missing input or process error.
5. **DR24 application path:** review PR #264 and its downstream stack, resolve source/identity/time/photometry/QC decisions, then run 5–10 confirmed sources through the API and Workbench with a replayable evidence bundle.
6. **Park demonstration and scale:** pass the 30–50 object guided workflow before starting the 100,000-light-curve dataset deliverable.
7. **Model artifact:** recover the exact original artifact through a controlled hash-verified source or approve a separately versioned reproduction. Keep the v0.2.0 production identity immutable.
8. **AOIC and CIN:** continue as separate staged workstreams after their interface, scientific governance, privacy and acceptance criteria are reviewed.
9. **Desktop distribution:** implement clean-machine tests and platform-specific installers as a separate product milestone.

## 10. Definition of done and authority

A code change is complete only after tests and evidence on the exact commit pass. A scientific claim is complete only after its source-backed acceptance criteria pass. A documentation update does not resolve a scientific blocker.

This PR does not merge branches, change issue state, publish a release, create tags, change production data, replace model artifacts, change credentials, or alter scientific acceptance criteria.
