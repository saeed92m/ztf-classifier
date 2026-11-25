# Park Prototype — Labelled Data Source Assessment

- Review date: 2026-11-25
- Scope: Data and label inputs for the first Park prototype
- Decision state: SOURCE REVIEW COMPLETE / ACQUISITION NOT STARTED
- Related issue: #158
- Scope policy: PARK_WINDOWS_PRERELEASE_SCOPE_FREEZE_2026-11-24.md

## 1. Decision summary

No single inspected source can be treated as a drop-in, 100,000-object, 15-class, DR24-labelled training set.

Use separate roles for each source:
- Use ALeRCE 2020 as the frozen 15-class historical reference.
- Use ALeRCE TAP for current ZTF object, detection, feature and classifier-probability retrieval. Do not treat broker probabilities as independent ground-truth labels.
- Assess SCoPe as an independent external dataset. Its taxonomy and label structure differ from ALeRCE.
- Request the ALeRCE 2025 labelled-source manifest from the authors or an official data endpoint. Do not assume that the 219,792-source label list is downloadable from the paper.
- Acquire DR24 raw light curves only after the label-to-DR24 identity mapping has a tested contract.

The 150-object v0.2.0 benchmark is a frozen benchmark. It is not the Park cohort. Do not change it.

## 2. Candidate sources

### 2.1 ALeRCE 2020 labelled set — historical reference

- DOI: 10.5281/zenodo.4279623
- Public record: https://zenodo.org/records/4279623
- Archive size: 1.1 GB.
- The archive includes:
  - labelled_set_lc_classifier_SanchezSaez_2020.csv;
  - features_for_lc_classifier_20200609.csv;
  - ALeRCE_lc_classifier_outputs_ZTF_unlabeled_set_20200609.csv.
- The data ends on 2020-06-09.
- The labelled CSV is the 15-class ALeRCE labelled set.
- The 868,371-object output file contains predictions for an unlabeled set. Do not treat those predictions as ground truth.

Use:
- frozen historical benchmark comparison;
- taxonomy and label-source inspection;
- a historical reference for the v0.2.0 pipeline.

Do not use:
- the unlabeled prediction table as training labels;
- the frozen 2020 features as proof of DR24 feature parity;
- this dataset as the current DR24 cohort.

### 2.2 ALeRCE TAP — current ZTF data access

- TAP endpoint: https://tap.alerce.online/tap
- Official migration guide: https://science.alerce.online/services/accessing-data-tap/
- ALeRCE recommends TAP instead of direct database connections.
- The public service exposes ZTF tables such as object, detection, feature, probability, taxonomy, forced_photometry and dataquality.

Use:
- current object metadata and coordinates;
- detection and forced-photometry retrieval where required;
- published feature and taxonomy metadata;
- source-backed query provenance.

Limits:
- probability rows are classifier outputs. They are not independent labels.
- A taxonomy row defines classifier classes. It does not prove the true class of an object.
- The ALeRCE ZTF catalog and DR24 HATS are separate data products.
- Do not silently map ALeRCE OIDs to DR24 numeric object IDs.
- Use an explicit cross-match with candidate count, separation, ambiguity and provenance.

Do not use direct database credentials or raw SQL connections. Use the documented TAP or API interfaces.

### 2.3 SCoPe training set — external validation candidate

- Paper: Healy et al. (2024), The ZTF Source Classification Project. III.
- DOI: 10.3847/1538-4365/ad33c6
- Public dataset: https://zenodo.org/records/8410826
- Training set DOI: 10.5281/zenodo.8410825
- Current Zenodo record: https://zenodo.org/records/18891510
- The paper reports a manually constructed training set with 170,632 light curves. It is associated with 85,136 manually reviewed sources.
- The public training_set.parquet file is approximately 436 MB.
- The paper uses ZTF DR16 observations from 2018 March to 2023 January.
- The authors remove observations with nonzero catflags and require at least 50 epochs for the training light curves.
- SCoPe uses hierarchical ontological and phenomenological taxonomies.
- It trains separate binary classifiers. A source can have more than one label.
- The data used in the paper is based on ZTF DR16, not DR24.

Use:
- independent external evaluation for taxonomy classes with a defensible mapping;
- cross-taxonomy robustness analysis;
- a separate model comparison only when feature and label contracts are compatible.

The 170,632 light curves exceed the technical plan's numerical 100,000-curve target. They do not meet the DR24 cohort requirement. They use DR16 and a different multi-label taxonomy. Do not count them as the required DR24 cohort.

Do not use:
- the SCoPe XGBoost artifact as the ZTF Classifier production model;
- SCoPe labels as direct replacements for ALeRCE labels;
- a one-to-one class mapping without a documented review;
- SCoPe predictions as independent labels.

Before use:
1. Pin the exact Zenodo record and version.
2. Compare file size and checksums.
3. Inspect schema, row grain, source IDs, labels and feature definitions.
4. Determine whether each row is a source, a filter-specific light curve or another unit.
5. Build a reviewed mapping table. Keep unmapped and ambiguous labels.
6. Define a held-out external test. Do not tune the model on that test.

### 2.4 ALeRCE 2025 TDE expansion — source manifest request

- Paper: Pavez-Herrera et al. (2025), ALeRCE light curve classifier: Tidal disruption event expansion pack.
- DOI: 10.1051/0004-6361/202451951
- arXiv: https://arxiv.org/abs/2503.19698
- The paper reports 219,792 labelled sources and 16 subclasses, including 60 TDEs.
- The updated model uses 176 features.
- The paper describes labels from multiple catalog sources. It does not provide a clear public DOI for the complete labelled-source manifest in the inspected text.

Use:
- taxonomy and methodology review;
- a request for the source manifest and label provenance;
- a possible later TDE extension after a new taxonomy decision.

Do not:
- add TDE to the frozen 15-class v0.2.0 taxonomy;
- claim that the 219,792 source IDs are available through the paper;
- treat ALeRCE model predictions as ground-truth labels;
- change the frozen class order.

## 3. Data-source risks

| Risk | Why it matters | Required control |
|---|---|---|
| Label source differs by class | Labels may have different evidence quality | Keep source catalog, label type and confidence per object |
| Broker predictions are mistaken for labels | This creates circular evaluation | Separate reference labels from model probabilities |
| Different taxonomies | Class names do not imply equivalent definitions | Use a reviewed, versioned mapping table |
| Multi-label versus single-label data | A source may belong to more than one class | Define the conversion policy before training |
| DR16 versus DR24 | Cadence, coverage and photometry may differ | Reacquire the mapped cohort from DR24 and compare |
| OID mismatch | ALeRCE OID and DR24 numeric objectid may differ | Use an explicit cross-match with ambiguity states |
| Filter-specific records | One source may have separate records per filter | Preserve filter and identity evidence |
| Selection bias | Catalogs favour known and observable classes | Report class and population limits |
| Data leakage | The same source can occur in multiple datasets or splits | Use source-level and temporal deduplication |

## 4. Recommended acquisition sequence

1. Recover the complete ALeRCE 2020 labelled-set archive. Verify its DOI, archive checksum, file checksums, row counts and class counts.
2. Inspect the exact SCoPe training_set.parquet version. Record its schema and row grain. Do not yet use it for training.
3. Request the ALeRCE 2025 labelled-source manifest and its class-level provenance from the ALeRCE authors or an official data endpoint.
4. Build a source-label table. Preserve all source labels and conflicts. Do not collapse them without a declared rule.
5. Select a predeclared cohort of at least 100,000 labelled light curves, as required by the technical project document.
6. Cross-match the selected labels to DR24 HATS. Preserve all candidate matches and ambiguity states.
7. Retrieve DR24 light curves in bounded batches. Save input, output and failure manifests.
8. Validate photometry, time, quality, cadence, identity and feature compatibility.
9. Freeze the dataset manifest before training and before viewing model results.
10. Use a source-level and temporal split. Keep external validation separate.

## 5. Model-artifact decision

The original v0.2.0 production model artifact is missing from the inspected repository and recovery sources. Do not recreate it and call it the original model.

Keep these paths separate:
- Frozen v0.2.0 baseline: unchanged. Recover only from an authenticated original source.
- Park prototype model: a new version, if required. It must have a new model ID, feature schema, training manifest, split manifest, metrics, calibration artifact and provenance.

A new model does not resolve the missing original artifact. Record both facts.

## 6. Current status

| Item | State |
|---|---|
| ALeRCE 2020 record identified | VERIFIED |
| ALeRCE 2020 archive acquired and hashed in the current run | NOT RUN |
| ALeRCE TAP endpoint and current schema identified | VERIFIED |
| ALeRCE 2025 paper and labelled-set size identified | VERIFIED |
| ALeRCE 2025 source manifest acquired | BLOCKED / NOT FOUND IN INSPECTED PAPER |
| SCoPe training set and paper identified | VERIFIED |
| SCoPe schema and row grain inspected locally | NOT RUN |
| Taxonomy mapping approved | NOT RUN |
| SCoPe numerical 100,000-curve target | CANDIDATE | 170,632 DR16 light curves are reported. They are not a DR24 cohort and do not use the ALeRCE 15-class taxonomy. |
| 100,000 labelled DR24 light curves acquired | NOT RUN |
| DR24 cross-match validated | NOT RUN |
| DR24 feature compatibility validated | NOT RUN |
| New Park model trained | NOT RUN |
| Independent validation completed | NOT RUN |

## 7. Scope controls

- This assessment supports the four active Park prototype phases.
- CPVS and the 11,602-object discrepancy remain frozen until Park presentation.
- Do not run CPVS workflows or change CPVS code during this delivery stage.
- Do not download the full DR24 archive.
- Do not acquire the full 90.6 GB SCoPe prediction catalog. The training set file is a separate, bounded download and still requires approval of its use.
- Do not run large downloads or paid compute without the required authorization.
- Do not change the v0.2.0 baseline, taxonomy or class order.
