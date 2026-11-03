# Park MVP — DR24 Application Readiness Audit

**Audit date:** 2026-11-04  
**Repository revision:** `5bb01ffe15926502bb96fee6e86e86c183ca7779`  
**Delivery tracker:** [Issue #158](https://github.com/saeed92m/ztf-classifier/issues/158)  
**Next implementation tracker:** [Issue #253](https://github.com/saeed92m/ztf-classifier/issues/253)  
**Independent recovery evidence:** [PR #246](https://github.com/saeed92m/ztf-classifier/pull/246); [merged bounded payload probe PR #259](https://github.com/saeed92m/ztf-classifier/pull/259)  
**Disposition:** PARTIAL — application-level DR24 acquisition is not implemented or validated.

## 1. Executive result

The repository contains a working API-backed scientific Workbench, local CSV/Parquet import, an ALeRCE observation backend, and a separate source-backed BTS-to-DR24 recovery diagnostic.

These components do not yet form a DR24-backed Park MVP. The default application observation path uses ALeRCE. The DR24 HATS work is a bounded recovery/availability experiment. It is not yet connected to the application's observation service, API, or Workbench as a selectable production source.

No scientific-performance, calibration, photometry-quality, anomaly-discovery, or 100,000-light-curve completion claim is supported by this audit.

## 2. Repository evidence

| Area | Inspected path or evidence | Finding |
|---|---|---|
| Application observation source | `src/ztf_classifier/application/observations.py` | Constructs `AlerceDetectionBackend` directly. |
| Default API wiring | `src/ztf_classifier/api/app.py` | Creates the default `ObservationService` with `Alerce()`. |
| ALeRCE normalization | `src/ztf_classifier/io/alerce.py` | Has explicit required columns, corrected/raw photometry priority, row validation, and ingestion diagnostics. This contract is ALeRCE-specific. |
| Local import | `src/ztf_classifier/application/ingestion.py` | Supports CSV/Parquet, a default 250 MiB limit, required-column checks, and SHA-256. This is local import, not DR24 HATS acquisition. |
| DR24 source-subset normalization | `src/ztf_classifier/data/source_subset.py` | Validates object-level `oid`, coordinates, and `ngoodobsrel`; it is not a light-curve photometry adapter. |
| Feature contract | `src/ztf_classifier/features/pipeline.py` | Preserves the frozen 42-feature v0.2 vector and g/r eligibility rules. Do not change it for this integration. |
| User interface | `src/ztf_classifier/web/static/index.html`, `app.js`, `styles.css` | API-backed Workbench exists. It is not proof of a complete guided Park workflow or a packaged desktop application. |
| Application execution | `src/ztf_classifier/jobs/executor.py` | Acquires observations through the application observation service, then computes features and inference. |

## 3. Source-backed DR24 pilot evidence

The independent recovery work is tracked in PR #246. Its latest recorded source-backed follow-up is workflow run [41527459598](https://github.com/saeed92m/ztf-classifier/actions/runs/41527459598).

The bounded pilot used 100 BTS targets and recovered 773 unique DR24 OIDs within a 5-arcsecond positional search radius. The indexed DR24 Lightcurves lookup reported the availability counts below. This earlier run proved row availability and filter/epoch metadata consistency only. It did not retrieve nested photometry. A later, separate bounded payload probe is recorded in Section 4.

| Measure | Result |
|---|---:|
| Recovered OIDs queried | 773 |
| OIDs with a Lightcurves row | 714 |
| OIDs without a Lightcurves row | 59 |
| Filter metadata pairs consistent | 773/773 |
| BTS targets with at least one g and one r OID | 87/100 |

This is evidence of catalog-row availability and metadata consistency for this sample only. It does not establish:
- clean or scientifically usable photometry;
- adequate cadence or temporal coverage;
- correct physical-source identity;
- classification labels or classification accuracy;
- calibration or conformal coverage;
- a validated anomaly detector;
- performance on 100,000 light curves.

The 5-arcsecond radius is a candidate-generation radius, not an accepted identity rule.

## 4. Bounded nested-payload evidence — PR #259

PR #260 and PR #259 are merged into main. PR #259 adds a manual-only, indexed HATS probe and source-mapping notes. The live probe run [41674212725](https://github.com/saeed92m/ztf-classifier/actions/runs/41674212725) returned all four requested OIDs and 626 epoch rows.

| OID | Filter | Epochs | catflags=0 | catflags=32768 |
|---:|---|---:|---:|---:|
| 264114400013085 | g | 78 | 71 | 7 |
| 264214400000912 | r | 123 | 115 | 8 |
| 278115200026587 | g | 216 | 191 | 25 |
| 278215200018105 | r | 209 | 193 | 16 |
| **Total** | **g + r** | **626** | **570** | **56** |

For this four-OID sample, all 626 rows had finite HMJD, magnitude, and magnitude error; all magnitude errors were positive; and returned epoch counts matched the catalog `nepochs` values. Artifact ZIP SHA-256: `d6918f6a9da9b9fce8c18bdc7bcca73c1ba99ea6d31df561585c2ee3ac06bb7f`.

This is a payload-retrieval result only. It does not establish production photometry compatibility, an approved `catflags` policy, physical-source identity, cadence sufficiency, model performance, or 100,000-light-curve readiness.

The source-mapping notes explicitly preserve:
- `hmjd` as HMJD; it must not be renamed to MJD.
- `mag`, `magerr`, and `clrcoeff` as native DR24 values.
- Raw `catflags` values without an unapproved exclusion policy.
- `objectid`, `filterid`, `fieldid`, and `rcid` as separate provenance.

The two sample g/r OID pairs have positional and partition evidence, but this is not a universal cross-OID grouping rule.

## 5. Acceptance matrix

Status meanings:
- **VERIFIED:** acceptance evidence is present and reproducible for the stated scope.
- **PARTIAL:** some implementation or bounded evidence exists; acceptance is incomplete.
- **BLOCKED:** a known dependency or scientific gap prevents acceptance.
- **NOT STARTED:** no implementation/evidence was found in this audit.

| Park MVP requirement | Status | Evidence / missing work |
|---|---|---|
| Frozen v0.2.0 scientific core preserved | VERIFIED | The inspected feature pipeline retains the 42-feature contract. This audit makes no model or benchmark change. |
| API-backed Workbench entry point | PARTIAL | Static Workbench and API routes exist; full guided scientist workflow is not demonstrated. |
| Local CSV/Parquet import | PARTIAL | Import service exists; end-to-end user workflow and supported light-curve schema coverage need acceptance tests. |
| Direct, selectable DR24 Lightcurves acquisition in application | BLOCKED | Default ObservationService is hard-wired to ALeRCE. Track implementation in #253. |
| DR24 object/filter/partition provenance in application results | BLOCKED | Pilot records recovery metadata; application observation/result provenance is not connected to it. |
| DR24 photometry mapping and quality audit | PARTIAL | A bounded four-OID nested payload was retrieved and inspected. Production mapping, color policy, time-basis decision, and quality policy remain unapproved. |
| Explicit missing-data and exclusion reporting | PARTIAL | Existing normalization diagnostics and source-subset validation exist; DR24 application-level reason codes are not implemented. |
| 100,000 labeled light curves | NOT STARTED | This is a delivery target, not a current dataset achievement. |
| Leakage-safe temporal model evaluation on the Park dataset | NOT STARTED | No qualifying Park-dataset evaluation artifact was verified. |
| Calibrated probabilities and abstention for the Park dataset | BLOCKED | Existing baseline diagnostics do not establish calibration on the proposed Park population. |
| Dedicated anomaly evaluation | NOT STARTED | OOD diagnostics are not equivalent to a validated anomaly detector. |
| 30–50-object guided demo using a pinned DR24 sample | NOT STARTED | No end-to-end DR24-backed Workbench demonstration was verified. |
| Reproducibility bundle for the Park demo | PARTIAL | Existing manifest/provenance utilities and pilot artifacts exist; a single end-to-end Park run bundle is not verified. |
| Clean-machine deployment and installer acceptance | NOT STARTED | v1.0.1 is a Python package; self-contained Windows/macOS/Linux installers are not verified. |
| Technical report and Park acceptance package | PARTIAL | Proposal and project documentation exist; results must be generated from the implemented and validated MVP. |

## 6. Immediate implementation sequence

1. **DR24 acquisition contract and adapter (#253).** Define an explicit request/result contract. Preserve release identity, retrieval time, object IDs, filter and partition metadata, schema/index identity, row counts, hashes, and failure reasons.
2. **Application integration.** Make DR24 an explicit source option behind the existing observation service boundary. Keep ALeRCE selectable. Never silently fall back between sources.
3. **Photometry normalization and QC.** Map DR24 columns explicitly. Preserve raw columns. Measure invalid values, exclusions, cadence, time coverage, and per-filter completeness.
4. **Fixture-backed regression coverage.** Test schema drift, duplicates, missing rows, filter identity, object grouping, photometry QC, provenance, and failures without live network calls in ordinary CI.
5. **Bounded source-backed integration run.** Use a pinned, limited sample. Save manifests and artifacts. Do not download the full DR24 archive.
6. **Workbench demo.** Demonstrate a 30–50-object workflow with source selection, light curves, analysis, uncertainty, explicit missing-data states, exports, and a reproducibility bundle.
7. **Scientific acceptance.** Build and evaluate the labeled dataset under a declared taxonomy and leakage-safe temporal split. Report only measured performance.
8. **Deployment acceptance.** Test the supported Park delivery mode on a clean machine. Treat self-contained desktop installers as a separate acceptance item unless required by the Park.

## 7. Open engineering and governance notes

- PR #246 is Draft and its branch is two commits behind and diverged from the current `main` revision. Do not merge it until the branch is reconciled, current-head checks pass, and the evidence is reviewed.
- PR #247 and PR #252 are documentation workstreams, not Park runtime delivery.
- PR #252's successful CI is engineering evidence for its own branch. Its source-backed scientific jobs were skipped by the ordinary documentation-PR event.
- The current status report in `docs/PROJECT_STATUS_REPORT_2026-11-03.md` names main revision `4f98a06`, while the inspected current main revision is `764ed5d`. Its 58% weighted estimate must not be treated as a current verified Park MVP completion percentage without a refreshed evidence-based scoring pass.
- Keep CPVS exact-reconstruction outside this Park MVP workstream, as directed.
- Keep CIN runtime outside the critical path. Preserve its architecture work without delaying the Park prototype.

## 8. Audit conclusion

The most important current correction is architectural and data-level: the Park MVP requires a DR24-backed application path, but the default application observation service currently uses ALeRCE. The earlier availability pilot queried Lightcurves index metadata only. The later four-OID probe retrieves and inspects nested epoch payloads, but remains an isolated evidence tool. Neither is a production observation adapter or an end-to-end application data path.

The next measurable exit condition is not a larger download. It is a tested, provenance-complete DR24 adapter that runs through the existing API and Workbench without silent source substitution. The critical scientific design decisions are still open: HMJD semantics, DR24-vs-ALeRCE photometry equivalence, color treatment, catflags policy, and explicit object/filter/partition grouping.
