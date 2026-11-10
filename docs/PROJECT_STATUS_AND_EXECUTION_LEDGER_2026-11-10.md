# ZTF Classifier — Project Status & Execution Ledger
## Evidence snapshot: 2026-11-10

**Primary delivery:** Tabriz Science & Technology Park pilot  
**Main baseline:** `bc85f6c36b28f3c9ddc2b7b5aa00e0256148441c` (2026-11-03)  
**Park pilot branch:** `delivery/park-dr24-lightcurve-acceptance-20261110`  
**Documentation PR:** #266 — Draft / open / unmerged  
**Live DR24 rerun:** [workflow #42830475350](https://github.com/saeed92m/ztf-classifier/actions/runs/42830475350) — completed successfully (run conclusion: success; 2026-11-10 14:08 UTC).

## 1. Executive disposition

The deliverable produced for inspection is **ZTF Park Pilot v0.3**, an offline raw-data explorer. It packages source-backed DR24 HATS epoch records and provenance. It is not the full ZTF Classifier and does not classify DR24 data.

Verified source evidence:
- A 30-OID retrieval sample completed in three bounded batches.
- 30/30 requested OIDs were returned; no OID was missing.
- The payload contains 4,046 epochs.
- Per-OID counts match the HATS catalog counts and manifest.
- Every epoch has finite HMJD, finite magnitude and finite, non-negative magnitude error in the inspected payload.
- All 30 OIDs belong to filter g, field 199, rcid 32.
- The 30 OIDs are catalog records; physical-source identity is not established.
- An independent r-band control contains one separate OID with 123 epochs. It is not paired with the g sample.
- The full 150-row metadata snapshot is not included in the acquired evidence. The demo contains a 30-OID catalog only.

## 2. Current repository state

- Main is unchanged at the recorded HEAD. No merge or release was performed.
- PR #264: bounded DR24 adapter, open/unmerged.
- PR #273–#277: batch API, QC, source contract, Workbench and Zubercal adapters, draft/unmerged.
- PR #278: local scientific-artifact audit, draft/unmerged.
- PR #279/#280: data-adequacy and OOD work, draft/unmerged.
- PR #266: Park plan and evidence addendum, draft/unmerged.
- Issue #253: DR24 application integration remains open.
- Issue #158: Park MVP acceptance remains open.
- Issue #170/#180: CPVS membership discrepancy remains unresolved and deferred from the Park MVP.
- Issue #251/#252: CIN remains a proposed architecture. Runtime is not implemented.

The default application observation path on main remains ALeRCE. The DR24 feature branch work is not yet an accepted production application path.

## 3. Source and UI test evidence

| Test | Result | Boundary |
|---|---|---|
| 10-OID source retrieval and repeatability | PASS | 10 OIDs / 688 epochs; same hashes across repeat requests |
| 30-OID source retrieval | PASS | 30 OIDs / 4,046 epochs; three batches; no missing OIDs |
| Small-sample Workbench browser test | PASS | Bounded browser test only |
| 30-OID Workbench walkthrough, initial test | FAIL historical, corrected | The wait predicate expected the identical success status to change between batches; this was a test-harness defect |
| Test-harness correction | CI PASS | Commit `82f0812d07005dd521361f127f3e9f7d493060af`; tests the actual POST response, exact returned OID set and exact rendered OID panels |
| Corrected live source + 30-OID browser rerun | PASS | Run #42830475350: 10-OID repeatability, 30-OID acquisition in three batches, 30-OID Workbench in three batches and browser acceptance all passed; zero console/page errors; artifact 13771891432, SHA-256 `b2cd2885b6a1593404d8ad7c2ca15f2fa1a5effa06d7efec146972afdeb3532b` |
| Local offline UI browser test in build container | NOT VERIFIED | Managed Chromium URLBlocklist blocks all URLs; system policy was not altered |
| DR24 classifier inference | NOT RUN | No model inference on the 30-OID sample |
| Independent DR24 scientific evaluation | NOT ACCEPTED | No qualifying temporal/object-disjoint labeled evaluation |

The source-backed UI run now passes on the dedicated delivery branch. It verifies the tested OID-based retrieval/display flow only; it does not establish physical-source identity or scientific classifier validity. The offline HTML was not browser-tested in the build container.

## 4. Protected scientific baseline

Unchanged:
- software release v1.0.1;
- scientific baseline v0.2.0;
- 150 benchmark objects;
- 15 ALeRCE reference classes, 10 per class;
- 42 frozen features;
- XGBoost `baseline_v0.2`;
- historical cutoff 59447.224132;
- diagnostics schema 1.1.

ALeRCE labels remain benchmark/reference labels, not independent astrophysical ground truth. Raw DR24 input is not mapped to the frozen 42-feature contract. No production model, feature, class order, or acceptance threshold was modified.

## 5. Park acceptance gates

| Gate | Status | Evidence gap |
|---|---|---|
| G0 — baseline protection | PASS | Re-check after integration |
| G1 — DR24 acquisition | PARTIAL | Bounded source proof exists; application path not accepted |
| G2 — physical identity and OID grouping | NOT ACCEPTED | Crossmatch and ambiguity policy unresolved |
| G3 — time, photometry and QC contract | NOT ACCEPTED | Preserve HMJD/native values; no approved production transform or selection policy |
| G4 — 5–10 source application E2E | PARTIAL | Component tests exist; full accepted guided run needed |
| G5 — 30–50 source live Workbench | PARTIAL | 30 OID panels passed in three batches; OIDs are not confirmed physical sources and a 50-source guided demo has not been run |
| G6 — no-terminal usage | PARTIAL | Offline package exists; local browser acceptance not run in build container |
| G7 — independent DR24 scientific validation | NOT ACCEPTED | No feature mapping, labeled temporal test or calibrated DR24 evaluation |
| G8 — Park handover package | NOT ACCEPTED | Form, presentation revision and accepted demonstration still needed |

## 6. Progress scoring

Method: equal-weight acceptance checklist. VERIFIED/PASS = 1.0; PARTIAL = 0.5; NOT VERIFIED/NOT STARTED/NOT ACCEPTED = 0. Scores indicate evidence completion, not elapsed time or probability of acceptance.

### Active project: 48%

| Subsystem | Score |
|---|---:|
| Scientific core and reference model | 50% |
| Data acquisition and provenance | 60% |
| API and Workbench | 60% |
| Scientific validation, calibration and OOD | 20% |
| Productization, installation and documentation | 50% |

### Raw-data pilot v0.3: 82%

| Subsystem | Score |
|---|---:|
| 30-OID source retrieval | 100% |
| Provenance, hashes and repeatability | 95% |
| Raw light-curve view | 85% |
| Measurement summary and descriptive QC | 80% |
| Sample catalog | 50% |
| Live API and Workbench | 85% |
| Full exports and provenance | 90% |
| Offline package | 70% |

### Park MVP gate readiness: 33%

This is calculated from nine gates using PASS=1, PARTIAL=0.5 and NOT ACCEPTED=0. It is not interchangeable with the raw-data pilot score.

## 7. Work completed in this cycle

- Retrieved and checked the 30-OID raw payload and manifest.
- Built a standalone offline explorer with separate OID charts, error bars, measurement summaries, descriptive QC, catalog search, provenance and JSON/CSV exports.
- Preserved all raw epoch rows and source-native HMJD/mag/magerr/clrcoeff/catflags.
- Kept the independent r-band control separate.
- Completed run #42830475350: fixed 10-OID source/repeatability, 30-OID source acquisition, three-batch 30-OID Workbench browser walkthrough, and small-sample Workbench browser acceptance all passed. Artifact 13771891432; SHA-256 `b2cd2885b6a1593404d8ad7c2ca15f2fa1a5effa06d7efec146972afdeb3532b`.
- Added a test-only correction for the repeated status-string wait condition and passed ordinary CI.
- Fast-forwarded the correction onto the dedicated Park delivery branch. Main and the immutable release were not changed.
- Added the dated Park pilot readiness report and acceptance-form reconciliation to this documentation branch.

## 8. Remaining work and next actions

1. Preserve the successful live workflow #42830475350 artifact in the Park evidence package and manually rehearse the offline ZIP on the actual presentation laptop.
2. Retrieve the actual 150-row Objects Table artifact and include it only after hash verification.
3. Complete the DR24 adapter in the application service without silent fallback to ALeRCE.
4. Approve a versioned contract for OID, physical-source crossmatch, HMJD, photometry, catflags and QC.
5. Accept a complete 5–10 source application workflow.
6. Complete and inspect a 30–50 OID live Workbench demonstration.
7. Build a properly labeled DR24 dataset and run object-disjoint and temporal validation before making classifier claims.
8. Reconcile the park form's financial values, registration details and actual team before signature.
9. Revise the presentation and project proposal as separate versioned files.
10. Complete a clean-machine/manual demonstration rehearsal and generate the final Park handover report.

## 9. Deferred workstreams

- CPVS exact membership remains an independent scientific research blocker. Do not change filters or baseline to force the published count.
- CIN remains a proposed human-in-the-loop architecture. Do not represent it as implemented or part of the current pilot.
