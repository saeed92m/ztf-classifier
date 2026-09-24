# ZTF Classifier — End-to-End Roadmap

**Roadmap baseline:** v0.2.0 frozen  
**Current milestone:** v0.3 Production Architecture & Contracts

## 0 → 100% project map

```
PHASE 0  FOUNDATION
██████████████████████████████ 100%
Environment • Git • package • CI • project structure
                    ↓
PHASE 1  SCIENTIFIC DATA FOUNDATION
████████████████████████████░░ ~80%
ZTF/ALeRCE access • provenance • benchmark • schemas
                    ↓
PHASE 2  FEATURE ENGINEERING
█████████████████████████████░ ~95%
preprocessing • 42 frozen v0.2 features • feature contracts
                    ↓
PHASE 3  MODEL & UNCERTAINTY
████████████████████████████░░ ~90%
XGBoost • calibration • conformal • OOD • artifacts
                    ↓
PHASE 4  SCIENTIFIC VALIDATION
████████████████████████████░░ ~90%
CV • historical evaluation • temporal audit • integrity
                    ↓
                 v0.2.0
          SCIENTIFIC BASELINE
             █████ 100%
                    │
                    ▼
PHASE 5  PRODUCTION ARCHITECTURE
██████████░░░░░░░░░░░░░░░░░░ ~25%
Data contracts • canonical model • API boundaries
storage • jobs • provenance • errors • security model
                    ↓
PHASE 6  PRODUCTION INGESTION
██████░░░░░░░░░░░░░░░░░░░░░░ ~20%
single object • batch • arbitrary practical N
validation • provenance • scalable processing
                    ↓
PHASE 7  PRODUCTION APPLICATION/API
███████░░░░░░░░░░░░░░░░░░░░ ~25%
REST/API • job lifecycle • persistence • auth boundary
                    ↓
PHASE 8  WEB ANALYSIS WORKBENCH
███░░░░░░░░░░░░░░░░░░░░░░░ ~10%
Dashboard • Data • Objects • Analysis • Predictions
Visualization • Models • Reports • Settings
                    ↓
PHASE 9  REPORTING & EXPORT
███░░░░░░░░░░░░░░░░░░░░░░░ ~10%
JSON • CSV • Parquet • HTML • PDF
scientific provenance and reproducibility in reports
                    ↓
PHASE 10  DEPLOYMENT & OPERATIONS
███░░░░░░░░░░░░░░░░░░░░░░░ ~15%
Docker • CI/CD • observability • logging • metrics
backup/recovery • configuration/secrets
                    ↓
PHASE 11  CROSS-PLATFORM DELIVERY
██░░░░░░░░░░░░░░░░░░░░░░░░ ~5%
Web first → optional Tauri desktop
Windows • Linux • macOS
                    ↓
PHASE 12  END-TO-END HARDENING
░░░░░░░░░░░░░░░░░░░░░░░░░░ 0%
full workflow • failure modes • performance • security
reproducibility • scientific acceptance
                    ↓
PHASE 13  RELEASE CANDIDATE
░░░░░░░░░░░░░░░░░░░░░░░░░░ 0%
v0.9.0 RC • documentation freeze • deployment verification
                    ↓
PHASE 14  FINAL PRODUCT
░░░░░░░░░░░░░░░░░░░░░░░░░░ 0%
v1.0.0
Complete ZTF Classifier product
```

## Current exact position

**We are here:**

```
v0.2.0 FROZEN
     │
     ▼
FINAL SYSTEM AUDIT
     │
     ▼
>>> v0.3 ARCHITECTURE & CONTRACTS <<<
     │
     ├── Data Contract
     ├── Canonical Observation Model
     ├── Validation Contract
     ├── Feature Service Boundary
     ├── Inference Boundary
     ├── Prediction/Result Contract
     ├── Provenance Contract
     ├── Job/Batch Contract
     ├── API Boundary
     ├── Storage Boundary
     ├── Model Registry Boundary
     └── Test/Deployment Strategy
```

The current task is **not** to rewrite the scientific core and **not** to build the UI first. The next engineering objective is to establish stable production contracts around the validated scientific core.

## Milestones

| Version | Milestone | Primary outcome |
|---|---|---|
| v0.2.0 | Scientific Baseline | Frozen, reproducible research baseline |
| v0.3.0 | Architecture & Contracts | Stable system boundaries |
| v0.4.0 | Data/Ingestion | User data and practical batch processing |
| v0.5.0 | API/Application | Service orchestration and persistence |
| v0.6.0 | Web Workbench | Full analysis-oriented UI |
| v0.7.0 | Reporting/Operations | Reports, exports, observability |
| v0.8.0 | Deployment/Cross-platform | Reproducible delivery |
| v0.9.0 | Hardening/RC | End-to-end release candidate |
| v1.0.0 | Final Product | Complete validated product |

## Architectural principle

One scientific core, multiple delivery surfaces:

```
                 ┌──────────── Web UI
                 │
User Data → API → Production Application
                 │
                 ├──────────── Optional Desktop
                 │
                 ▼
          Scientific Core
                 │
        Feature + Model + Diagnostics
                 │
                 ▼
          Versioned Results
```

This prevents separate implementations of the scientific logic for Web, Windows, Linux, and macOS.

## Definition of Done for v0.3

v0.3 is complete when the following are documented, reviewed, tested where applicable, and stable enough to implement:

- input formats and canonical observation schema
- validation rules and failure semantics
- batch/job model
- feature extraction interface
- model artifact/inference interface
- prediction/result schema
- provenance schema
- API resource model
- persistence model
- model registry/versioning rules
- configuration/secrets boundary
- logging/error taxonomy
- test pyramid and contract-test strategy
- deployment topology
- explicit separation of benchmark, research datasets, and user/production datasets

## Strategic order

The order is deliberate:

**Scientific correctness → contracts → scalability → service layer → UX → deployment → hardening → v1.0**

This prevents product features from becoming coupled to unstable scientific internals and preserves the reproducibility of v0.2.0.
