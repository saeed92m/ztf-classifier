# ZTF Classifier — Project Continuity Handbook v3.1

**Status date:** 2026-11-19  
**Main revision:** `dcedccf50ae5a4541ababc29cfc7471a7d0ea14a`  
**Software release:** v1.0.1 (immutable)  
**Scientific baseline:** v0.2.0 (immutable)  
**Intended model identity:** `baseline_v0.2`

## Executive status

The project is an Astronomical Data Analysis & Discovery Platform. The v1.0.1 software release is published. The broader Park MVP and final product are not complete.

The current DR24 Explorer supports bounded raw-data acquisition and inspection. It can display source-native light curves, diagnostic QC, acquisition provenance, and raw JSON export. It is not a validated DR24 classifier.

The Park MVP remains **NOT ACCEPTED**. Its acceptance contract requires a complete predeclared dataset package and one end-to-end workflow through the normal API and Workbench.

## Latest verified evidence

### Main CI

[CI #44515762167](https://github.com/saeed92m/ztf-classifier/actions/runs/44515762167) on main completed successfully:
- 702 tests passed.
- 13 tests skipped.
- 9 warnings.
- Format, lint, runtime smoke, package build, dependency audit, and CI gate passed.
- PR #289 merged the Soup Sieve 4.1 security update. The latest main Dependency Audit passed.

At least seven production-inference tests remain skipped because the original production artifact or shared inputs are unavailable (Issue #282). The other skips still require review. A green CI run does not authenticate the model artifact.

### Scientific Validation

[Scientific Validation #44515762163](https://github.com/saeed92m/ztf-classifier/actions/runs/44515762163) completed all five workflow jobs.

It acquired:
- a 150-row DR24 Objects Table subset;
- a separate 150-row live ALeRCE reference response;
- the immutable ALeRCE reference archive manifest;
- source-provenance and heavy-validation artifacts.

The DR24 and ALeRCE 150-row responses are not cross-matched. They do not form a labeled DR24 cohort. They do not prove model accuracy, feature parity, physical identity, calibration, or Park acceptance.

### DR24 Explorer

The repository documents a previous seven-OID Workbench smoke with 2,183 epochs. This is raw retrieval/display evidence only. The pinned two-OID live parity test and local Workbench procedure in PR #297 still require execution for this handoff.

## Frozen scientific baseline

Preserve v0.2.0:
- 150 benchmark objects;
- 15 ALeRCE reference classes;
- 10 objects per class;
- 42 frozen features in `final_feature_set_v0.2`;
- XGBoost model identity `baseline_v0.2`;
- historical cutoff 59447.224132;
- diagnostic schema 1.1.

ALeRCE labels are weak/reference labels, not independent astrophysical truth. The 150-object benchmark is not representative of the full ZTF population.

### Production artifact status

The original production artifact has not been recovered or authenticated from the accessible repository, release assets, or retained CI reports. Recovery remains open in [Issue #282](https://github.com/saeed92m/ztf-classifier/issues/282).

- Expected original artifact contract: schema 1.0.
- The v1.0.1 package does not include model weights.
- The separate schema-1.1 lab-smoke artifact is not a production substitute.
- Do not rebuild or replace the original model and call it the frozen artifact.
- Keep production inference readiness UNKNOWN until the original artifact and trusted hashes are recovered.

## Data and identity contracts

- DR24 HATS is the primary source-native stream for raw inspection and planned application integration.
- ALeRCE is a separate observation adapter and reference-label source.
- BTS labels apply only to the transient population covered by BTS.
- Zubercal DR20 is a separate product. Do not merge its IDs, time scale, photometry, or QC with DR24 HATS.
- A ZTF OID is not a canonical astrophysical source ID.
- Preserve source, catalog entry, source group, OID, filter, field, RCID, observation, transient event, and host galaxy as distinct entities.
- Preserve native HMJD, mag, magerr, clrcoeff, and catflags. Do not apply unapproved time, color, or QC transformations.

## Park delivery

### Laboratory demonstrator

The bounded raw Explorer can show:
- public DR24 HATS retrieval;
- source-native light-curve display;
- diagnostic QC;
- acquisition provenance;
- raw JSON export.

It cannot show DR24 model inference, calibrated class probabilities, confirmed physical identity across OIDs, production QC, validated astrophysical anomaly discovery, or full-ZTF performance.

The pinned two-OID live test and local Workbench run must pass before the handoff is marked READY WITH LIMITATIONS.

### Full Park MVP

The full-cohort acceptance contract is in [PARK_MVP_REAL_DATASET_END_TO_END_ACCEPTANCE_2026-11-17.md](roadmap/PARK_MVP_REAL_DATASET_END_TO_END_ACCEPTANCE_2026-11-17.md). The complete predeclared cohort must pass through the normal API and Workbench. Batches are an execution method, not a smaller acceptance target.

## Open blockers

| Priority | Tracker | Status |
|---|---|---|
| P0 | [#158](https://github.com/saeed92m/ztf-classifier/issues/158) Park MVP | OPEN / NOT ACCEPTED |
| P0 | [#253](https://github.com/saeed92m/ztf-classifier/issues/253) DR24 application integration | OPEN |
| P0 | [#282](https://github.com/saeed92m/ztf-classifier/issues/282) Original model artifact | OPEN / UNKNOWN |
| P0 | [#249](https://github.com/saeed92m/ztf-classifier/issues/249) Source identity / AOIC | OPEN |
| P1 | [#293](https://github.com/saeed92m/ztf-classifier/issues/293) License policy | OPEN / OWNER DECISION REQUIRED |
| Research | [#170](https://github.com/saeed92m/ztf-classifier/issues/170) CPVS reconstruction | OPEN / UNRESOLVED |
| Later | [#251](https://github.com/saeed92m/ztf-classifier/issues/251) CIN | DEFERRED |

## CPVS boundary

The recorded Seq-based comparison reports 781,602 parent rows, 730,184 published members, and 741,786 reconstructed candidates. All published members are present, but 11,602 candidates are extra. Exact reconstruction remains UNRESOLVED. Reverify the counts against source artifacts before calling them a fresh run. Do not tune thresholds to force equality. CPVS is separate from the Park DR24 product path.

## Release and integration status

- Latest immutable software release: v1.0.1.
- PR #289 merged on 2026-11-19.
- No Park demo prerelease has been created.
- Issue #293 remains open. Do not publish a new distributable until the owner approves the license policy.
- PR #296 was closed as superseded after its five files were copied byte-for-byte and verified on PR #297.
- PR #297 is the consolidated Park documentation and acceptance PR. Its current-head CI passed.
- Other PRs remain under review. Do not merge or close a PR only because it is old.

A historical local WSL output reported 94 staged files and two untracked paths on a branch three commits behind remote. Recheck and preserve that working tree before any pull, checkout, reset, or merge.

## Next actions

1. Preserve and reconcile the local WSL working tree.
2. Complete review of PR #297.
3. Run the pinned two-OID live DR24 test and local Workbench procedure.
4. Correct the Park presentation and attach the Persian status addendum.
5. Freeze the full Park cohort and AOIC identity ledger.
6. Integrate DR24 through the normal observation service with no silent fallback.
7. Recover the original model artifact or keep the model gate BLOCKED.
8. Complete source-specific QC, feature semantics, full-cohort rerun, and independent evaluation.
9. Complete clean-machine deployment, backup/restore, license, and release gates.
10. Continue the final product roadmap.

## Definition of done

A milestone is complete only when its acceptance gates pass and evidence is retained. Code presence, a green CI run, or a successful small sample does not prove scientific or product acceptance.
