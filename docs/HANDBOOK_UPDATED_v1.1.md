# ZTF Classifier — Project Handbook Updated v1.1

**Status:** Active project handbook after the official v0.2.0 scientific baseline  
**Updated:** 2026-09-24  
**Repository:** `saeed92m/ztf-classifier`  
**Frozen baseline:** `v0.2.0` → `c1955676f9feeef10d480d8b8abd8452555c61d3`

## 1. Project mission

ZTF Classifier is being developed from a reproducible scientific ML pipeline into a complete astronomical analysis product.

The final system is intended to accept ZTF light-curve data at arbitrary practical dataset sizes, validate and normalize the input, extract a versioned feature schema, run auditable model inference, expose probabilities and uncertainty/diagnostic information, visualize the observations and analysis, and produce machine-readable and human-readable reports.

The 150-object v0.2 benchmark is a **frozen scientific benchmark**, not a product-size limit.

## 2. Immutable scientific baseline

Version v0.2.0 is the official frozen scientific baseline.

Frozen baseline facts:

- 42 canonical features
- 150-object benchmark dataset
- 15 ALeRCE benchmark classes
- 118-object historical cohort
- 94 historically evaluated objects
- 4 evaluated folds
- 1 skipped fold because SNIa was absent from its training partition under the configured multiclass evaluation contract
- cutoff MJD: 59447.224132
- historical cohort rule: `firstmjd <= cutoff`
- observation rule: `mjd <= cutoff`
- feature-level temporal leakage audit: PASS
- prediction integrity audit: PASS
- XGBoost model family
- model version: `baseline_v0.2`
- random seed: 42
- tuning disabled for the frozen evaluation
- Python 3.11.16

Scientific limitations remain part of the baseline record: benchmark labels are retrospective ALeRCE reference labels rather than independently established ground truth; byte-for-byte identity of the original historical raw-cache snapshot cannot be independently proven; and historical/full-history performance are different experimental settings.

**Rule:** no feature, label, split, artifact, evaluation result, or scientific claim in v0.2.0 is edited in place.

## 3. Current position

The project has completed the core research/baseline milestone and has entered productization.

Current state:

| Area | Status |
|---|---:|
| Project foundation | 100% |
| v0.2 scientific baseline | 100% |
| Feature engineering | ~95% |
| Model & evaluation | ~90% |
| Temporal/scientific validation | ~90% |
| Production inference | ~45% |
| API/application layer | ~25% |
| Data ingestion/automation | ~20% |
| Deployment/operations | ~15% |
| UI/UX/product | ~10% |
| Security/reliability | ~10% |
| Documentation/release engineering | ~65% |
| Scientific/research core | ~90% |
| Overall productization | ~20–30% |

These percentages are project-tracking estimates, not scientific performance metrics.

## 4. Target architecture

The target product architecture is:

```
INPUT DATA
   ↓
DATA CONTRACT
   ↓
INGESTION + VALIDATION
   ↓
CANONICAL DATA MODEL
   ↓
FEATURE ENGINE
   ↓
MODEL / INFERENCE ENGINE
   ↓
PREDICTION CONTRACT
   ↓
ANALYSIS RESULT
   ├── Visualization
   ├── Report Generation
   ├── JSON / CSV / Parquet Export
   └── API
          ↓
      WEB APPLICATION
          ↓
   Optional Desktop Clients
```

The scientific core remains independent from the user interface.

## 5. Product boundaries

### Scientific core

Owns:

- light-curve representation
- preprocessing
- feature extraction
- model loading and inference
- probability calibration
- conformal diagnostics
- OOD diagnostics
- provenance
- deterministic contracts
- scientific validation

### Application layer

Owns:

- dataset/job lifecycle
- user-facing validation
- batch orchestration
- result persistence
- API contracts
- report/export orchestration

### Presentation layer

Owns:

- Dashboard
- Data
- Objects
- Analysis workspace
- Predictions
- Visualizations
- Models
- Reports
- Settings

### Delivery layer

Owns:

- Web deployment
- containerization
- observability
- authentication/authorization when required
- optional Windows/Linux/macOS desktop packaging

## 6. Input and data strategy

The system must not assume 150 objects.

The benchmark and user data are separate classes of data:

```
FROZEN BENCHMARK
150 objects
   ↓
Scientific validation / regression

USER / FUTURE DATA
N objects
   ↓
Production ingestion → validation → feature extraction → inference
```

Production ingestion must support practical arbitrary batch sizes subject to explicit resource limits.

Initial canonical inputs should preserve:

- object identifier
- MJD/time
- magnitude or flux
- measurement uncertainty
- filter/band
- quality information
- coordinates where available
- source/provenance metadata

## 7. Result contract

A production analysis result should expose, at minimum:

1. object identity and provenance
2. observational statistics
3. quality diagnostics
4. canonical feature vector and feature schema version
5. predicted class
6. class probabilities
7. calibration metadata
8. conformal prediction diagnostics when available
9. OOD/anomaly diagnostics when available
10. model/artifact version
11. pipeline version
12. analysis timestamp
13. warnings and validation status

The user-facing product should provide more than a class label.

## 8. Product output

Supported target outputs:

- interactive light curves
- multi-band plots
- phase/variability views where scientifically applicable
- feature summaries
- probability distributions
- uncertainty/diagnostic panels
- JSON
- CSV
- Parquet
- HTML report
- PDF scientific analysis report

## 9. Technology strategy

Primary technologies:

- Python: scientific core, ML, feature engineering, backend
- PostgreSQL/SQL: persistent application data where required
- TypeScript + React: web UI
- Tauri/Rust + TypeScript: optional desktop delivery
- Docker: reproducible deployment
- GitHub Actions: CI/CD

The project should not introduce additional languages into the scientific core unless a measured engineering requirement justifies them.

## 10. Development governance

Every change follows:

**PLAN → IMPLEMENT → TEST → VALIDATE → DOCUMENT → COMMIT**

Development occurs on feature branches.

Example branches:

- `feature/production-api`
- `feature/data-ingestion`
- `feature/web-ui`
- `feature/lightcurve-visualization`
- `feature/report-generation`
- `feature/desktop-app`

The `main` branch represents the integrated project. Releases are versioned milestones.

## 11. Release line

Current:

- v0.2.0 — Scientific Baseline — frozen

Planned:

- v0.3.0 — Production Architecture & Contracts
- v0.4.0 — Production Data/Ingestion
- v0.5.0 — Application/API
- v0.6.0 — Web Analysis Workbench
- v0.7.0 — Reporting/Export/Observability
- v0.8.0 — Deployment & Cross-platform delivery
- v0.9.0 — End-to-end hardening and release candidate
- v1.0.0 — Complete product release

Version boundaries may be adjusted by evidence, but the frozen v0.2.0 baseline remains unchanged.

## 12. Quality gates

Before any major release:

- unit tests
- integration tests
- contract tests
- regression tests
- scientific validation
- temporal/leakage validation where applicable
- provenance verification
- reproducibility check
- end-to-end workflow validation
- documentation synchronization
- clean Git state
- release artifact verification

## 13. Immediate next milestone

The immediate milestone is **v0.3 Production Architecture & Contracts**.

Before implementing the UI or large-scale ingestion, define and freeze:

- canonical observation/data model
- input data contract
- validation contract
- feature-service boundary
- model/inference boundary
- prediction/result contract
- provenance contract
- job/batch contract
- API boundary
- storage boundary
- model/artifact registry boundary
- configuration and secret handling
- error taxonomy
- test strategy
- deployment boundary

The next implementation should begin only after this architecture is audited against the v0.2 baseline.

## 14. Non-negotiable scientific principles

- Do not mutate the frozen v0.2 benchmark to improve later results.
- Do not mix benchmark validation data with production/user data.
- Do not present ALeRCE reference labels as independently verified ground truth.
- Do not silently change feature definitions between model versions.
- Do not hide model/provenance metadata from downstream results.
- Do not claim production-scale scientific performance from the 150-object benchmark.
- Every new model version must have an explicit dataset, feature schema, configuration, provenance, and validation record.

## 15. Definition of project completion

The project is complete only when the system can:

1. accept supported user data;
2. validate it with explicit contracts;
3. process single objects and practical batches;
4. extract a versioned feature representation;
5. perform reproducible inference;
6. expose probabilities and supported diagnostics;
7. visualize the observations and results;
8. generate reports and exports;
9. preserve provenance;
10. survive automated regression and end-to-end validation;
11. be deployed reproducibly;
12. be documented as a coherent product;
13. maintain the v0.2 scientific baseline as a reproducible historical reference.

