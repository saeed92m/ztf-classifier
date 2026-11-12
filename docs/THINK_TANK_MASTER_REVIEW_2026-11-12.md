# ZTF Classifier — 16-Expert Think Tank Master Review

**Review date:** 2026-11-12  
**Repository:** https://github.com/saeed92m/ztf-classifier  
**Base main inspected:** `f681408fae8d8062dd72ff74791872c1590f6ee8`  
**Current review branch:** `docs/unified-project-baseline-20261112`  
**Status:** Evidence-based strategic and technical review; not a certification of full scientific or product acceptance.

## 1. Purpose and authority

This document operationalizes the project owner's proposed 16-role think-tank framework. It combines the supplied 16-role specification, the original think-tank report, the current repository evidence, the Park proposal and technical dossier, the CIN canonical source, and the CPVS convergence policy.

The 16 roles are simulated review perspectives. This document does not claim participation by 16 external human experts.

The review must challenge existing assumptions. It must not produce consensus by agreement alone. Each recommendation must be classified as:
- verified fact;
- historical evidence;
- hypothesis;
- proposed design;
- unresolved risk;
- completed implementation;
- tested implementation;
- scientifically validated result.

No status may be promoted without evidence.

## 2. Product identity and scope

The long-term product is an independent, cross-platform, CPU-first **Astronomical Data Analysis & Discovery Platform**.

It must evolve beyond a conventional classifier. Its scope includes:
- multi-source astronomical data acquisition;
- source identity and association;
- raw-preserving data quality control;
- normalized scientific observations;
- time-series and statistical analysis;
- versioned feature generation;
- machine-learning classification;
- calibrated uncertainty and abstention;
- conformal prediction;
- out-of-distribution detection;
- scientific anomaly and novelty investigation;
- cross-catalog evidence;
- candidate generation and prioritization;
- human review;
- reproducible reports and research outputs.

The product must remain useful without CIN, without a cloud account, and without a mandatory network connection for local analysis. CLI, API and desktop GUI are complementary interfaces.

## 3. Protected scientific and release baseline

| Item | Frozen reference |
|---|---|
| Scientific baseline | v0.2.0 |
| Software release | v1.0.1 |
| Model identity | baseline_v0.2 |
| Model family | XGBoost |
| Benchmark | 150 objects |
| Benchmark taxonomy | 15 ALeRCE reference classes |
| Objects per class | 10 |
| Feature contract | final_feature_set_v0.2 |
| Feature count | 42 |
| Historical cutoff | MJD 59447.224132 |
| Artifact audit contract | schema 1.0 production |
| Diagnostics | schema 1.1 where separately specified |

ALeRCE labels are benchmark/reference labels, not independent astrophysical ground truth. The 150-object benchmark is a frozen baseline, not a representative sample of the complete ZTF population.

No model, feature, taxonomy, class order, benchmark membership, threshold, selector or release artifact may change without a versioned, independently validated migration.

The schema-1.1 lab-smoke artifact is not a replacement for the missing frozen schema-1.0 production artifact.

## 4. The 16 expert perspectives

### 01 — Chief Scientist / Principal Investigator
Defines scientific questions, novelty, research value and scientific acceptance. Requires separate evidence for known-class classification, anomaly investigation and discovery prioritization. A classifier output or OOD score alone is not a discovery.

### 02 — ZTF Survey and Data Systems Specialist
Audits DR releases, HATS, OID semantics, filters, field/CCD/quadrant, cadence, photometry, time basis, selection effects and source adapters. DR24 HATS and Zubercal DR20 remain distinct products. Raw acquisition is not model-ready normalization.

### 03 — Time-Domain Astrophysicist
Reviews variable/transient taxonomy, ambiguous and multi-phenomenon sources, cadence, rare events and unknown classes. Requires taxonomy versioning and explicit unknown handling.

### 04 — Astronomical Statistics and Time-Series Specialist
Reviews irregular sampling, measurement uncertainty, cadence-aware features, periodicity, phase coverage, cross-band correlation and domain shift. Feature values must carry computation quality and limitations.

### 05 — Astroinformatics and Big Data Architect
Designs raw store, metadata store, source registry, normalized observation layer, feature store, result store and provenance. Requires bounded, incremental, restart-safe and idempotent processing.

### 06 — Astronomical Catalog and Cross-Matching Specialist
Reviews Gaia, Pan-STARRS/PS1, BTS and other catalogs. Cross-match must preserve ambiguity, epoch, astrometric uncertainty and reversible lineage. Positional proximity alone is not physical identity.

### 07 — Chief AI / Machine Learning Scientist
Preserves XGBoost as a valid baseline and proposes fair benchmarking of XGBoost, LightGBM, CatBoost, Random Forest, Extra Trees, regularized logistic regression, SVM and time-series/representation models only on common data contracts and valid splits.

### 08 — ML Validation, Uncertainty and Benchmarking Scientist
Audits object-level and source-level split independence, temporal leakage, cross-match leakage, calibration population, conformal coverage and domain shift. StarEmbed identity overlap must be resolved before independent benchmark claims.

### 09 — Principal Software Architect
Keeps Desktop GUI, CLI and API above application services and stable core contracts. Separates scientific core, model artifacts, feature contracts, application state and source adapters. Requires versioned contracts and controlled schema migration.

### 10 — Principal Backend and Platform Engineer
Audits FastAPI, jobs, persistence, checkpoints, leases, retries, idempotency, transactions, result versioning, pagination and backpressure. Job lifecycle states must be explicit and recoverable.

### 11 — DevOps, MLOps, Security and Release Engineer
Requires SBOM, dependency policy, signed release artifacts, hash verification, secure model loading, installer integrity, secrets management, backup/restore and offline operation. Never load untrusted joblib artifacts.

### 12 — QA, Testing and Reliability Engineer
Requires unit, integration, scientific-contract, leakage, regression, E2E, performance, recovery, security, cross-platform and clean-install tests. Skips are not passes. CI is not scientific validation.

### 13 — Scientific UX/UI and Visualization Architect
Designs Dashboard, Data Manager, Object Explorer, Light Curve Workbench, Scientific Analysis, Discovery Workspace, Model Explorer, Cross-Match Explorer and Reports. Display identity, observations, features, predictions, uncertainty, OOD, anomaly evidence and provenance as distinct concepts.

### 14 — Chief Product Officer / Commercialization Strategist
Prioritizes research groups, universities, observatories and data centers. Park MVP is the immediate delivery priority. Do not build a public-scale platform before scientific value is proven. Keep demo and dataset-size targets separate.

### 15 — Scientific Documentation and Research Communication Specialist
Maintains specifications, implementation status, test evidence, scientific validation, limitations, user guides and version history. Every claim must trace to data, code, hash or experiment.

### 16 — Independent Red-Team Reviewer
Challenges identity, leakage, calibration, abstention, anomaly semantics, reproducibility, installation, artifact integrity and unsupported claims. Rejects any attempt to treat skipped tests or lab artifacts as production evidence.

## 5. Five decisive findings

### 5.1 Source identity is a P0 scientific dependency

Distinguish:
- ZTF OID;
- observation/detection;
- astrophysical source;
- catalog object/alias;
- candidate association.

`OID != Astrophysical Source Identity`.

One physical source may have multiple OIDs across filters, fields or quadrants. Incorrect grouping can corrupt light curves, features, model inputs, cross-match, benchmark splits and discovery candidates.

The project needs a versioned Astrophysical Source Identity & Association Engine. It must preserve confirmed, ambiguous, unmatched, rejected and superseded states, retain all original identifiers, and support reversible merge/split lineage. Do not automatically merge OIDs.

The minimum identity contract is P0 alongside DR24 application integration. Full AOIC can be phased, but no model-ready multi-OID light curve may be claimed without a valid association decision.

### 5.2 OOD is not scientific anomaly or discovery

Keep distinct outputs:
1. Classification — most likely known class.
2. Calibration — reliability of predicted probabilities.
3. Conformal prediction — prediction set under its stated assumptions.
4. OOD — distance from the reference distribution.
5. Scientific anomaly — unusual scientific behavior or properties.
6. Novelty — possible new class/population.
7. Discovery ranking — priority for scientific review.

The future architecture may expose five independent engines: Classification, Uncertainty, Anomaly & Novelty, Scientific Context, and Discovery Prioritization. Their outputs must not be collapsed into one confidence score.

### 5.3 Benchmark independence is a release gate

The 150-object/15-class benchmark remains a frozen baseline. It does not prove population-level performance. StarEmbed has a reported duplicate source identifier and source overlap between train and test; resolve object/source identity and split semantics before using it as an independent benchmark. New benchmarks require object/source-level isolation, temporal validation, provenance and independent evaluation.

### 5.4 DR24 raw acquisition is not model-ready inference

Merged DR24 components provide bounded raw acquisition, API, QC diagnostics and Explorer functionality. Standard normalized ObservationService remains ALeRCE-backed. DR24 must not silently fall back to ALeRCE when selected.

Before DR24 inference, validate:
- source and OID association;
- HMJD/time conversion;
- filter and photometry mapping;
- quality and missing-data semantics;
- duplicate/epoch handling;
- feature parity and leakage;
- immutable source manifests and hashes.

### 5.5 Product maturity is not scientific maturity

Software v1.0.1 is released, but this does not mean Park MVP or full scientific discovery acceptance is complete. The prior exact-head CI run passed engineering checks but had 13 skipped tests and skipped source-backed validation jobs. It is not a Scientific-PASS.

## 6. Historical evidence requiring careful interpretation

A prior BTS/DR24 investigation reported:
- 100 BTS objects;
- 773 OIDs returned by a 5-arcsec positional search;
- 97 objects with at least one match;
- 714 OIDs with Lightcurve rows and 59 without;
- 87 BTS objects with at least one OID having both g and r;
- 96 objects with at least one OID with lightcurve data.

These are historical bounded retrieval statistics. They are not 100 confirmed source identities, not photometric parity, and not model-readiness evidence. A 5-arcsec radius is not an identity rule.

A later Park demo evidence package covered 30 OIDs and 4,046 epochs, all g-band from one partition/field/RCID. It does not prove 30 independent astrophysical sources. The separate r-band OID's physical relation to the g-band group remains unestablished.

## 7. Target architecture — nine conceptual layers

1. **Application & UX:** Desktop GUI, CLI, API, Workbench, reports.
2. **Data & Evidence Infrastructure:** raw store, metadata, feature store, result store, provenance.
3. **Data Acquisition & Adapters:** ZTF DR24, ALeRCE, BTS, Gaia and other catalog adapters.
4. **Normalization & QC:** schema, photometry, time basis, quality and validation.
5. **Source Identity & Association:** OID mapping, source registry, astrometric/temporal association.
6. **Scientific Feature & Analysis:** features, time-series, statistics, periodicity.
7. **Scientific Context & Evidence:** cross-match, catalogs, explainability, provenance.
8. **Scientific Intelligence:** classification, anomaly, novelty and uncertainty.
9. **Scientific Discovery & Research:** candidate prioritization and research outputs.

This is a conceptual target architecture, not a claim that all layers are implemented. The layers must interact through stable contracts; they are not required to form a one-way pipeline.

## 8. Joint decisions

1. Preserve v0.2.0, baseline_v0.2, 42 features, 150-object benchmark and v1.0.1.
2. Prioritize minimum source identity and explicit DR24 application integration as P0.
3. Keep raw acquisition separate from normalized/model-ready data.
4. Resolve StarEmbed split integrity before independent benchmark claims.
5. Keep CPVS 11,602 discrepancy open and separate.
6. Keep OOD, anomaly, novelty and discovery ranking independent.
7. Build the Desktop product with clean-install, cross-platform, performance and recovery gates.
8. Keep CIN optional and independent. No public-scale annotation or retraining until governance, privacy, QC and independent scientific evaluation pass.
9. Preserve CPU-first operation; GPU/distributed infrastructure is not required without measured justification.
10. Never merge a PR, publish a release or alter production artifacts without the required authorization.

## 9. Limitations of this review

This review combines the supplied original think-tank report and current repository/status evidence. It is not a line-by-line audit of every source module, a fresh full-dataset scientific rerun, a complete installer test across operating systems, or a certificate of production readiness.

Every historical measurement must retain its date, source hash and execution context. New measurements must be recorded separately.
