# Park Prototype Acceptance Matrix — 2026-11-24

## Source of requirements

This matrix is based on the submitted Park acceptance worksheet and the final project proposal. It preserves the declared six-month delivery structure:

| Phase | Duration | Required output |
|---|---:|---|
| 1. Infrastructure, data and feature engineering | 2 months | DR24 access, labelled subset, versioned feature set |
| 2. Main model | 1 month | Baseline and primary model with initial evaluation |
| 3. Uncertainty, anomaly detection and validation | 2 months | Calibrated confidence, abstention rule, anomaly score and transferability report |
| 4. Dashboard, documentation and commercialization preparation | 1 month | Live dashboard, documentation and software-registration package |

The worksheet requires a CPU-oriented, reproducible software product. It identifies XGBoost/LightGBM classification, probability calibration, explicit abstention, anomaly detection, explainability, independent and temporal validation, dashboard/API delivery, and an installable application as product goals.

**Acceptance rule:** a capability that is not implemented and tested must remain a roadmap item. A successful build or a user-interface element is not evidence of scientific capability.

## Current evidence

| Requirement | Current state | Evidence and limit |
|---|---|---|
| ZTF DR24 source access | PARTIAL | Indexed HATS acquisition exists for 1–10 OIDs. The desktop explorer uses the native DR24 endpoint. |
| Source provenance | PARTIAL | The raw adapter records source, release, query, OID accounting, schema hash and per-OID payload hashes. |
| Photometry and time normalization | BLOCKED | HMJD, DR24 native photometry, color term and quality semantics are preserved. No approved transformation to the frozen model input contract exists. |
| Data-quality reporting | PARTIAL | Raw-preserving QC and descriptive summaries are available. The QC policy is diagnostic and is not approved as a production mask. |
| Feature engineering | PARTIAL | The frozen v0.2.0 feature contract remains in the repository. DR24-to-feature parity is not established. |
| 100,000 labelled light curves | NOT VERIFIED | No reproducible, pinned Park dataset manifest and completed acquisition report were verified for this delivery branch. |
| XGBoost/LightGBM model | BLOCKED | The repository documents the frozen production artifact path, but the required production artifact is not committed. The separate lab-smoke artifact is not a substitute. |
| Calibrated probabilities and abstention | NOT VERIFIED | Historical diagnostics exist, but the complete DR24 Park population and deployed artifact have not passed the required validation chain. |
| Anomaly detection | NOT VERIFIED | Existing OOD diagnostics do not establish an independently evaluated Park anomaly detector. |
| Explainability | NOT VERIFIED | A complete, reproducible SHAP explanation path for the Park application has not been accepted. |
| Temporal and external validation | NOT VERIFIED | No final Park-population evaluation report was verified for this delivery branch. |
| Desktop application | PARTIAL | A Windows pywebview shell, loopback API, in-memory bearer token, native navigation guard and per-user data paths are implemented. Windows acceptance is still running. |
| Workspace lifecycle | IMPLEMENTED; CI PENDING | Create/open/list, operation logging, export persistence and export restoration APIs and UI are implemented. Exact-head tests are pending. |
| Reproducibility package | PARTIAL | Raw JSON export, source hashes and workspace metadata are supported. A full data/model/schema/split reproducibility bundle is not yet accepted. |
| Park guided demonstration | NOT VERIFIED | A 30–50-object end-to-end demonstration has not been accepted. The current desktop workflow is bounded to 1–10 OIDs per acquisition. |
| Windows installer | NOT VERIFIED | The workflow builds a frozen application, creates an NSIS installer, and tests installation and uninstallation. Exact-head Windows evidence is pending. |
| macOS/Linux desktop installers | NOT STARTED | The current standalone desktop preview targets Windows only. |

## Verified engineering boundaries

- The desktop preview starts a local API on a dynamically allocated loopback port.
- The desktop API uses a session token held in memory.
- Desktop application data is stored under the current user's application-data directory.
- DR24 acquisition preserves native source values. It does not silently substitute ALeRCE.
- DR24 raw acquisition does not perform model inference.
- Uninstall is designed to preserve user projects, logs and exports.
- The Windows preview installer is unsigned. A checksum is not a code signature.

## Scientific and delivery blockers

1. Obtain the exact frozen production model artifact and required feature/raw-data inputs through a controlled, hash-verified process. Do not replace them with lab-smoke artifacts.
2. Approve and validate the DR24 time, photometry, color, quality and object-identity contracts before using DR24 data for model inference.
3. Build a pinned, labelled Park dataset with source, label, taxonomy, split and provenance manifests.
4. Run leakage-safe temporal evaluation and an independent external evaluation.
5. Validate calibration, abstention, anomaly detection and explainability on the declared Park population.
6. Complete a 30–50-object guided demonstration and a reproducibility bundle.
7. Pass clean Windows install, launch, persistence, upgrade/uninstall and data-preservation tests.
8. Obtain the required written Park evaluation terms before external distribution of the installer.

## Current delivery decision

**REVISE — not ready for scientific acceptance or public release.**

The current branch advances the Windows desktop delivery and workspace persistence. It does not yet satisfy the worksheet's classification, calibration, anomaly, explainability or validation claims. Keep those capabilities disabled or explicitly marked as unavailable until the required scientific evidence passes.
