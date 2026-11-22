# Park Laboratory Demonstrator — Execution Plan

**Date:** 2026-11-17

**Status:** Owner-authorized execution plan; implementation and scientific acceptance are not yet complete

**Repository:** saeed92m/ztf-classifier

**Primary tracker:** #158, #253, #282

**Frozen baseline:** v0.2.0; preserve unchanged

## 1. Immediate objective

Deliver one compact, real-data laboratory demonstrator. A reviewer must be able to open the application, select a pinned dataset, inspect diverse astronomical objects and their light curves, run only scientifically supported analysis, inspect results and limitations, and export a reproducible report.

This demonstrator is an early proof of the product workflow. It does not replace the institutional six-month target of a provenance-backed 100,000-lightcurve labeled subset, independent evaluation, technical report and broader delivery.

## 2. Dataset strategy

### Demonstrator sample and future cohort

For the raw-data demonstration, use only the bounded DR24 OIDs and procedure recorded in the runbook. Their documented epoch counts and hashes are reference values until verified from retained raw payloads. This two-OID sample is not a Park acceptance cohort.

The frozen 150-object v0.2.0 benchmark remains separate. ALeRCE may provide reference labels under its own label and observation contracts, but it is not a DR24 observation fallback and does not establish independent astrophysical truth. No new Park cohort or model dataset is declared by this plan. Any future cohort requires a separately approved, predeclared source, selection, label, identity, and evaluation contract.

## 3. Source roles and scientific boundaries

### DR24 HATS — primary observation source
Use native DR24 light curves for acquisition, visualization, descriptive QC, source provenance and the DR24 Workbench path. Preserve:
- OID, filterid, fieldid, rcid, coordinates and catalog epoch count;
- HMJD, mag, magerr, clrcoeff and catflags;
- source release, query, schema, retrieval timestamp and content hashes.

Do not rename HMJD to MJD. Do not apply a catflags exclusion mask without a versioned policy. Do not apply color correction without a defensible color and uncertainty. Do not merge OIDs into a physical source based only on angular proximity.

### ALeRCE — reference labels and separate observation adapter
Preserve its label taxonomy, identifier and label provenance. Labels are weak/reference labels, not independent astrophysical truth. ALeRCE observations must remain explicitly identified as ALeRCE; they are not silently interchangeable with DR24 HATS photometry.

### Separate evaluation datasets — outside this demonstrator
The current Park demonstrator is limited to raw DR24 acquisition and Workbench inspection. No external dataset is part of this workflow or accepted as a DR24 model benchmark. Any future labeled evaluation requires a separate, approved scientific plan and its own provenance, identity, leakage, and validation evidence.

### Source-identity boundary
The raw demonstrator preserves each OID independently and makes no physical identity claim across OIDs. The minimum AOIC association ledger is a future Park requirement, not a capability claimed for this demonstrator. Any future association must distinguish catalog entry, platform object, OID, observation, transient event, and host galaxy, with evidence and uncertainty states.

## 4. Model decision tree

### Path A — recover the original production model
Use v0.2.0 only if the exact original production artifact is recovered and authenticated. Check:
- required files and schema 1.0;
- manifest and internal file hashes;
- provenance and model identity;
- frozen 42-feature order and class order;
- compatibility with the exact observation/feature input path.

The lab-smoke schema 1.1 artifact is not a substitute. Internal hash consistency alone does not prove original authenticity; a trusted original manifest/hash or equivalent provenance is required.

### Path B — new Park pilot model
If the original artifact cannot be recovered, a new model may be proposed as a separately versioned experiment. It requires:
- a new model version and model card;
- a pinned DR24-derived feature dataset;
- a declared label source and label limitations;
- a source-native time and photometry contract;
- object-level grouping before splitting;
- leakage-safe train/validation/test separation;
- per-class metrics, confusion matrix, calibration and abstention evaluation where sample size supports them;
- any independent scientific evaluation required by a future model gate, under a separately approved plan.

It must not overwrite, rename or replace the v0.2.0 baseline.

### Fail-closed rule
If neither path is scientifically valid, classification is BLOCKED. The demonstrator can still show acquisition, light curves, QC, descriptive features, object exploration and exports. It must not fabricate predictions or present an unvalidated score as confidence.

## 5. Required in-application workflow

1. Open the application and select the raw DR24 Explorer.
2. Enter the bounded OIDs from the runbook; do not treat them as a complete cohort.
3. Acquire source-native DR24 observations without fallback.
4. Inspect requested/returned status, per-OID light curves, native time/photometry fields, diagnostic QC, and acquisition provenance.
5. Export raw JSON and retain its hash, software revision, and run time.
6. Do not select normalized analysis or infer physical identity across OIDs.

Any full-cohort identity, feature, model, or repeatability workflow is a separate acceptance milestone and is not represented as an implemented path here.

A helper script or notebook alone does not pass the application acceptance gate. The normal API and Workbench path must be exercised.

## 6. Acceptance gates

| Gate | PASS evidence |
|---|---|
| D0 Dataset lock | Source release, query, cohort rule, license, schema, IDs and hashes pinned |
| D1 Identity | All associations traceable; ambiguity and missing links explicit |
| D2 Acquisition | Complete cohort acquired or every unavailable record has a reason |
| D3 QC | Raw values retained; units, time scales, flags and exclusions explicit |
| D4 Features | Source-specific feature contract tested; no unapproved v0.2 parity claim |
| D5 Model | Original artifact authenticated or new model separately validated |
| D6 ML diagnostics | Metrics and uncertainty reported only on eligible, leakage-safe labels |
| D7 Workbench | Normal user workflow displays source, identity, QC, analysis and limitations |
| D8 Reproducibility | Full cohort rerun reconciles object-level outputs |
| D9 Independent check | A separately approved independent evaluation passes for the declared population, or is explicitly NOT RUN |
| D10 Delivery | Reproducible environment, security review, backup/recovery and demo procedure verified |

Gate states: PASS, FAIL, BLOCKED, NOT RUN, NOT APPLICABLE. Missing evidence is never PASS.

## 7. First execution tasks

1. Recover the exact local artifact audit JSON and inventory from the existing local project checkout; do not ask for raw datasets or credentials.
2. Recover the original model artifact or establish that it remains unavailable after a bounded search. Do not substitute the lab artifact.
3. Recover the frozen benchmark manifest and feature/raw inputs; verify all hashes and object/class counts.
4. Inspect the current DR24 batch API and Workbench explorer implementation against the latest main commit.
5. Integrate DR24 source selection into the normal application service and analysis workflow without silent fallback. Preserve native values until the scientific contract is approved.
6. Implement the minimum AOIC association ledger for the selected cohort.
7. Execute the full cohort in the Workbench and retain all artifacts.
8. Convene the 16-role simulated think tank plus Red Team to review the actual run evidence and assign READY, READY WITH LIMITATIONS or NOT READY.

## 8. Non-goals for this milestone

Labeled-dataset benchmarking, broader multi-survey expansion, model evaluation, self-contained desktop installers, and the full 100,000-lightcurve institutional milestone are not acceptance claims for this raw-data demonstrator. Any such work remains a separately governed milestone.

## 9. Park presentation guardrails

- Do not claim the demonstrator represents the full ZTF population.
- Do not claim ALeRCE agreement is independent astrophysical accuracy.
- Do not imply that any external label source validates DR24 classification.
- Do not claim DR24-to-v0.2.0 feature parity without evidence.
- Do not claim calibrated confidence unless calibration is measured on eligible held-out data.
- Do not conflate OOD with scientific anomaly or discovery.
- Present the live application and its reproducible outputs, not only slides.
- State blocked and unmeasured capabilities plainly.

**Current disposition:** execution plan approved; demonstrator NOT YET ACCEPTED.

> **Integration review note (2026-11-22):** This is a historical plan from PR #297 head `5e9fbe02a954eadb2c8503890f77950ce7296ea7`. PR-associated CI evidence does not validate combined integration HEAD `3e0159aafa53313c47052b7adbae1ac55514293c`. Local Workbench execution remains unverified; the attempted browser run was blocked by sandbox loopback permissions, not by a demonstrated application failure. The original model remains unauthenticated and inference remains BLOCKED.
