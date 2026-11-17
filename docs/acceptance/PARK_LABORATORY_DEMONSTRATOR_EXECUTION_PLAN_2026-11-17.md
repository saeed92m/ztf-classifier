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

### Preferred first cohort

Recover and verify the exact frozen v0.2.0 benchmark inputs:
- 150 ZTF objects;
- 15 ALeRCE reference classes;
- 10 objects per class;
- frozen 42-feature contract and class order.

Do not assume that the object manifest, feature table, raw ALeRCE cache or original production model artifact are available. Verify file presence, schemas, hashes, object IDs, class counts, and source provenance before use.

### If the frozen inputs cannot be recovered

Create a separately versioned Park Pilot cohort from a pinned ALeRCE reference snapshot and a predeclared selection rule. The new cohort must:
- preserve source-native IDs and labels;
- report actual per-class coverage and unavailable records;
- avoid post-hoc substitution to force class balance;
- be frozen before feature generation or model evaluation;
- remain separate from the v0.2.0 benchmark.

The cohort is compact by design. Its size is determined by the complete eligible population under the declared query and availability rules. It is not selected by an arbitrary round number.

## 3. Source roles and scientific boundaries

### DR24 HATS — primary observation source
Use native DR24 light curves for acquisition, visualization, descriptive QC, source provenance and the DR24 Workbench path. Preserve:
- OID, filterid, fieldid, rcid, coordinates and catalog epoch count;
- HMJD, mag, magerr, clrcoeff and catflags;
- source release, query, schema, retrieval timestamp and content hashes.

Do not rename HMJD to MJD. Do not apply a catflags exclusion mask without a versioned policy. Do not apply color correction without a defensible color and uncertainty. Do not merge OIDs into a physical source based only on angular proximity.

### ALeRCE — reference labels and separate observation adapter
Preserve its label taxonomy, identifier and label provenance. Labels are weak/reference labels, not independent astrophysical truth. ALeRCE observations must remain explicitly identified as ALeRCE; they are not silently interchangeable with DR24 HATS photometry.

### BTS — limited independent evaluation
Use spectroscopically classified BTS records only for supported transient classes. Require source identity evidence, a leakage-safe object-level split and explicit ambiguous/unmatched accounting. BTS cannot validate all 15 v0.2.0 classes.

### AOIC — minimum demonstrator identity ledger
Keep these entities separate: catalog entry, canonical platform object, ZTF OID, filter/field/rcid partition, observation, transient event and host galaxy. Each association records source IDs, release, coordinate frame/epoch, separation, uncertainty, candidate count, method/version, status and evidence. Allowed states include CONFIRMED, AMBIGUOUS, UNMATCHED, PROVISIONAL and DISPUTED.

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
- an independent BTS evaluation for supported classes.

It must not overwrite, rename or replace the v0.2.0 baseline.

### Fail-closed rule
If neither path is scientifically valid, classification is BLOCKED. The demonstrator can still show acquisition, light curves, QC, descriptive features, object exploration and exports. It must not fabricate predictions or present an unvalidated score as confidence.

## 5. Required in-application workflow

1. Open or create a workspace.
2. Select the pinned Park Pilot cohort.
3. Select DR24 HATS explicitly for native observations.
4. Acquire every cohort record and reconcile requested, returned, missing, empty and rejected records.
5. Inspect source and schema provenance.
6. Inspect AOIC identity state and candidate associations.
7. Inspect per-filter light curves, epoch counts, time coverage, photometry and raw flags.
8. Run the versioned diagnostic QC report without deleting raw data.
9. Generate features only through the approved source-specific contract.
10. Run the authenticated model or separately validated Park pilot model, if its gate passes.
11. Display probabilities, calibration state, conformal set/rejection, OOD and scientific-anomaly outputs as distinct fields. Hide or mark BLOCKED any unsupported output.
12. Browse object-level results and export catalog, report, run manifest and provenance.
13. Repeat the complete cohort run and compare object-level results and hashes under declared tolerances.

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
| D9 Independent check | BTS evaluation passes for its limited supported population, or is explicitly NOT RUN |
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

CPVS exact reconstruction, StarEmbed benchmark acceptance, CIN runtime, broad multi-survey expansion, GPU/distributed infrastructure, self-contained desktop installers, and the full 100,000-lightcurve institutional milestone are not prerequisites for this compact demonstrator. They remain on the roadmap.

## 9. Park presentation guardrails

- Do not claim the demonstrator represents the full ZTF population.
- Do not claim ALeRCE agreement is independent astrophysical accuracy.
- Do not claim BTS validates all variable-star classes.
- Do not claim DR24-to-v0.2.0 feature parity without evidence.
- Do not claim calibrated confidence unless calibration is measured on eligible held-out data.
- Do not conflate OOD with scientific anomaly or discovery.
- Present the live application and its reproducible outputs, not only slides.
- State blocked and unmeasured capabilities plainly.

**Current disposition:** execution plan approved; demonstrator NOT YET ACCEPTED.