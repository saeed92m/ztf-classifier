# Park MVP — real-data end-to-end acceptance plan

**Date:** 2026-11-17  
**Status:** Proposed execution contract; no scientific acceptance is claimed  
**Owner:** Project Owner  
**Review basis:** 16 simulated specialist seats and a simulated independent Red Team. These are structured expert perspectives, not 16 external human reviewers.  
**Primary issue:** #253  
**Related:** #158, #170, #180, #210, #249, #282, #293  
**Frozen baseline:** v0.2.0; 42 features; frozen class order; historical cutoff 59447.224132.

## 1. Owner clarification

The Park MVP must be tested as a real product workflow on one coherent, pinned, real astronomical dataset package. Arbitrary 50-, 100-, or 1,000-object samples are not product acceptance criteria.

Small deterministic samples may be used only for a specific diagnostic, such as a parser regression or identity edge case. They must not represent product completion, population performance, or Park readiness.

The product acceptance run must process the complete predeclared cohort. If the workflow uses batches for memory or runtime reasons, every batch must be processed and reconciled to the complete cohort. Batching is an execution strategy, not sampling.

## 2. One coherent Park Pilot Dataset package

Create one immutable dataset package with linked, but scientifically separate, layers:

### A. Observation layer — primary product input

- Source: official ZTF DR24 Lightcurves HATS/Parquet.
- Include all DR24 observations returned for the complete predeclared target cohort.
- Preserve source-native OID, filter, field, CCD/quadrant or RCID, coordinates, epoch arrays, source release, schema/index, query, retrieval time, and hashes.
- Preserve missing targets, missing bands, empty light curves, partial retrievals and rejected rows in the manifest. Do not silently drop them.
- Keep DR24 HMJD, native magnitude, magerr, clrcoeff and catflags source-native.

### B. Multi-class reference layer — ALeRCE

- Pin the exact ALeRCE catalog/reference snapshot and its label schema.
- Preserve ALeRCE class labels as source-provided reference/weak labels, not independent astrophysical truth.
- Keep ALeRCE object identifiers and DR24 OIDs in an explicit association table.
- Do not merge taxonomies or assume a match is physically certain.

### C. Independent transient validation layer — BTS

- Pin the complete authoritative BTS catalog release used for the pilot.
- Preserve spectroscopic class, redshift and label provenance.
- Associate BTS targets to every candidate DR24 OID using the AOIC evidence contract.
- Preserve ambiguous and unmatched targets. Do not choose the nearest OID automatically.
- Use BTS only for the transient classes and population it actually represents. It is not a 15-class variable-star benchmark.

### D. Identity and provenance layer — AOIC

Keep these entities distinct:
- canonical platform object (object_id);
- catalog entry/alias;
- ZTF OID;
- detection;
- photometric observation;
- transient event;
- host galaxy;
- dataset snapshot;
- analysis execution;
- identity decision.

Every association must record catalog namespace/release, source IDs, coordinate frame and epoch, positional uncertainty, candidate count, separation, method/version, policy hash, status, evidence and decision provenance. Use explicit states such as CONFIRMED, AMBIGUOUS, UNMATCHED, PROVISIONAL and DISPUTED. Coordinate proximity alone does not prove identity. A missing or ambiguous match remains explicit.

The cohort definition must be source-defined and frozen before model evaluation. It must not be selected after looking at model scores. The exact cohort size is the complete eligible population in the pinned source release and its DR24 query result; do not invent a target count.

## 3. User workflow to test in the actual application

Run this workflow through the normal API and Workbench interface. Do not substitute direct helper-script execution for a user workflow.

1. Create or open a project workspace.
2. Select the pinned Park Pilot Dataset package.
3. Select DR24 HATS explicitly as the observation source.
4. Acquire the complete cohort and record the exact query, source release, schema, row/object counts and hashes.
5. Inspect the import report. It must show complete, partial, empty, unmatched and rejected records.
6. Run AOIC identity assessment. Display confirmed, ambiguous and unmatched links and their evidence.
7. Run DR24-specific quality control. Preserve raw values and distinguish diagnostic flags from any production-approved exclusion policy.
8. Generate features only through a documented DR24 mapping. Preserve feature units, semantics, missingness and derivation provenance.
9. Run the frozen v0.2.0 model only if the original production artifact is recovered and authenticated AND DR24 feature parity is independently established. Otherwise, stop at the model gate and report BLOCKED. Do not substitute the lab-smoke model or create synthetic predictions.
10. Where inference is valid, show class probabilities, calibration status, uncertainty, conformal set/rejection, OOD status and anomaly score. Do not label a raw score as calibrated confidence.
11. Show an object catalogue, object detail page, light curves by filter, QC summary, feature diagnostics, prediction explanation/limits and source provenance.
12. Export the result table, per-object provenance, exclusions, run manifest and a reproducible report.
13. Repeat the complete run from the same pinned inputs. Compare object-level outputs and hashes under declared deterministic tolerances.
14. Evaluate against BTS only for supported transient classes and a leakage-safe object-level split. Report coverage, ambiguous-match exclusions, per-class metrics and uncertainty. Report ALeRCE agreement separately; do not call it independent accuracy.

## 4. Required acceptance gates

| Gate | PASS requires |
|---|---|
| G0 — Dataset lock | Complete source release, cohort rule, license, schema, query, versions and hashes are pinned |
| G1 — Identity | All target associations are traceable; ambiguous/unmatched records are retained; no OID is treated as a physical identity |
| G2 — Acquisition | Complete cohort is acquired or every unavailable record has an explicit reason; no silent fallback |
| G3 — Photometry/QC | Raw values are preserved; units, time scales, filters, flags and exclusions are explicit |
| G4 — Features | DR24 feature mapping is documented, tested and scientifically comparable where claimed |
| G5 — Model | Original model is authenticated and inference is compatible; otherwise BLOCKED, with no substitute |
| G6 — Uncertainty/OOD | Calibration, conformal behavior, unknown/reject policy and OOD outputs are tested on eligible data |
| G7 — Workbench | The normal user workflow displays source, identity, QC, analysis, limits and exports |
| G8 — Reproducibility | Full-cohort rerun produces the same object-level results within declared tolerances |
| G9 — Independent evaluation | BTS label provenance, identity, coverage, object-level split and per-class results pass for its limited scope |
| G10 — Delivery | Clean-machine install, security review, backup/recovery, documentation and demo procedure pass |

A gate may be PASS, FAIL, BLOCKED, NOT RUN or NOT APPLICABLE. Missing evidence is not PASS. Overall Park MVP readiness is the weighted status of these gates, with G1–G9 treated as hard scientific/product gates. A green unit-test workflow alone cannot close them.

## 5. What the existing evidence says

### Verified

- DR24 HATS acquisition and payload probes exist.
- DR24 HATS and Zubercal DR20 have separate identifiers, time scales, photometry and QC semantics.
- The ordinary application ObservationService still needs explicit DR24 source integration and end-to-end Workbench proof.
- A previous BTS availability pilot queried 773 OIDs from 100 targets, found 714 Lightcurves rows and at least one g and r OID for 87 targets. This is availability evidence only.
- AOIC v0.1 defines the required identity boundaries and uncertainty-aware association ledger, but is an architecture proposal, not a completed identity service.
- The frozen production v0.2.0 model artifact remains unavailable/unauthenticated in accessible remote locations (Issue #282).
- StarEmbed feature-input preparation succeeded for 50 clean test objects with 42 features and deterministic repeated logical output. Its source package still contains one duplicate train SourceID and one train/test overlap. It is not an accepted benchmark.
- CPVS remains a separate unresolved historical investigation. It does not block the DR24 Park product workflow.

### Not established

- End-to-end DR24 analysis through the ordinary API and Workbench.
- DR24-to-v0.2 feature parity.
- Production inference on DR24.
- Calibrated prediction quality on independent data.
- Full BTS-to-DR24 identity and benchmark acceptance.
- Clean-machine installation and recovery.
- Overall scientific acceptance or Park MVP readiness.

## 6. Execution order

1. Recover and authenticate the original v0.2.0 production artifact. Do not rebuild it.
2. Finish DR24 request/response and observation-service integration, with explicit source selection and no fallback.
3. Implement the minimum AOIC identity and association ledger required by the cohort.
4. Freeze the complete Park Pilot Dataset manifest and run the full cohort through acquisition and QC.
5. Validate DR24 feature semantics and parity. If parity fails, document the incompatibility and keep inference blocked.
6. Execute the full Workbench workflow and repeat it.
7. Run BTS independent evaluation for its supported scope; keep ALeRCE agreement separate.
8. Run clean-machine, security, backup/recovery and Park demonstration checks.
9. Convene the full think-tank review on the resulting artifacts and decide whether to present, present with limitations, or defer.

CPVS, StarEmbed source remediation, CIN implementation and Zubercal calibration remain separate workstreams. They must not displace the primary Park MVP end-to-end test.

## 7. Think-tank decision

The simulated 16-seat review converges on these decisions:

- Chief Scientist, ZTF data specialist, time-series statistician and validation lead: a complete, pinned real cohort is the only meaningful product-level test. Preserve all missingness and identity ambiguity. Do not equate ALeRCE labels with truth.
- Astroinformatics and cross-match specialists: DR24 HATS is the primary observation stream. AOIC must distinguish OID, catalog entry, source, event and observation. Zubercal remains supplementary and separate.
- ML and reliability specialists: do not run the frozen model on DR24 until the original artifact and feature parity are proven. Unknown, OOD and failed inference states must be visible.
- Software architect and backend lead: route acquisition through the normal service boundary and API; do not validate the product with scripts that bypass Workbench.
- QA and DevSecOps: acceptance must include complete-cohort reconciliation, deterministic rerun, clean-machine installation, dependency audit, backup and recovery.
- Scientific UX and documentation specialists: the user must see the data source, identity status, filters, epochs, QC, model limits and exportable provenance.
- Product manager: the Park demo should prove one coherent workflow, not claim the entire long-term discovery platform is complete.
- Independent Red Team: the largest risk is a convincing-looking demo that silently uses the wrong identity, source, model artifact or calibration semantics. Block such a demo.

### Dissent and limitations

- BTS is independent and valuable, but it covers spectroscopically classified transients. It cannot validate all 15 v0.2.0 classes.
- ALeRCE provides broad class references but is not independent ground truth.
- A single cohort can prove product operation and scoped performance. It cannot prove universal performance across all ZTF objects or future surveys.
- The 16 seats are simulated expert perspectives. External expert review remains a separate future activity.

## 8. Park presentation decision rule

- **READY:** all hard gates G0–G10 pass and the full cohort is reproducible.
- **READY WITH LIMITATIONS:** the user workflow and data/provenance gates pass, but clearly scoped scientific gates remain blocked; the presentation must state those limitations and must not claim validated classification accuracy.
- **NOT READY:** acquisition, identity, model provenance, data integrity, or user workflow cannot be demonstrated reliably.

No readiness label is assigned by this planning document. It must be assigned only after the full-cohort evidence is reviewed.
