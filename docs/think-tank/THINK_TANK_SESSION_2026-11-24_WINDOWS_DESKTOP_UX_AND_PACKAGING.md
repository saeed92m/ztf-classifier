# Think Tank Session — Windows Desktop UX and Packaging Readiness

**Date:** 2026-11-24  
**Review type:** Simulated 16-seat multidisciplinary review  
**Scope:** Park application form, desktop UX brief, proposed Windows shell ADR, current repository evidence  
**Decision:** Accept the design foundation for a bounded technical spike; do not approve a production architecture or release yet.

> This is an AI-assisted role simulation using the project's 16 specialist seats. It is not review by 16 independent human experts or external scientific peer review.

## 1. Source and repository basis

The review used the owner-supplied Park application form, final Park presentation, technical project dossier, current main product architecture, live PR/issue metadata, and the proposed UX/ADR documents.

The Park form describes an end-to-end workflow: ZTF data acquisition, preprocessing/QC, light-curve feature engineering, XGBoost/LightGBM classification, confidence/abstention/anomaly outputs, dashboard and API, reports, and installable operating-system builds. The project dossier adds temporal/object-level leakage control, evaluation metrics, a reproducible run bundle, and a six-month delivery structure.

The software must not present a planned function as an implemented function.

## 2. Requirement-to-evidence matrix

| Park requirement | Current repository evidence | Disposition for first Windows build |
|---|---|---|
| Standalone installable desktop software | Current API and static Workbench exist; no Windows installer is present in v1.0.1 release | NOT IMPLEMENTED — desktop shell and installer are required |
| ZTF DR24 data access | Bounded API retrieval and Workbench evidence exists on specific PR revisions | PARTIAL — exact-head integrated flow and clean Windows test remain |
| Object lookup and light-curve display | Workbench UI/API path exists; bounded object samples were tested | PARTIAL — object identity and physical-source mapping remain distinct |
| Preprocessing and quality control | Some QC and source-native diagnostics exist | PARTIAL — complete approved DR24 policy/adapter contract still required |
| Frozen 42-feature extraction | Frozen feature engine exists; DR24 parity is not approved | BLOCKED for DR24 inference until Issue #305 passes |
| Production classifier | Frozen production model artifact not independently recovered (Issue #282) | BLOCKED — do not substitute lab-smoke or reconstructed model |
| Calibrated probabilities and abstention | Architecture/contracts exist, but current DR24 end-to-end behavior is not verified | BLOCKED until the model and evaluation gates pass |
| Anomaly outputs | OOD/anomaly channels exist in architecture; DR24 validation is incomplete | BLOCKED or NOT RUN in UI until its own protocol passes |
| Reproducible technical report/catalog | Provenance and export components exist in parts | PARTIAL — unified Run ID manifest, report, and schema round-trip needed |
| Scientific validation and performance claims | Some offline workflows pass; multiple source-backed jobs are skipped; CPVS is separately unresolved | NOT FULLY VALIDATED — claim-specific gates must stay visible |
| Park evaluation distribution | Proprietary direction approved; written evaluation/demo terms incomplete (Issue #293) | RELEASE BLOCKER for external binary distribution |

The 30-object pilot evidence is limited: 4,046 epochs, all g-band, in one field and camera quadrant. It is not 30 confirmed physical sources, not a two-band cohort, and not classifier inference. Two pinned OIDs also do not demonstrate physical identity.

## 3. Sixteen specialist seats

| Seat | Finding | Required action |
|---|---|---|
| 1. Chief Scientist / PI | The form's scientific promise is an end-to-end analysis platform, not a raw-data viewer. | Make scientific readiness and claim boundaries visible in every result. |
| 2. ZTF data specialist | DR24/HATS is the primary time-series route; source-native values must be preserved. | Keep HMJD, filter, catflags, OID, query and response hashes explicit. |
| 3. Transient astrophysicist | An OID is a survey record identifier, not proof of a unique physical source. | Show catalog identity and cross-match evidence separately. |
| 4. Time-series statistician | Irregular cadence, uncertainty and band separation affect interpretation. | Show cadence, gaps, counts, errors and per-band plots; do not silently filter. |
| 5. Astroinformatics engineer | The application needs an explicit data contract and reproducible run object. | Version adapters, schemas, configuration and every export. |
| 6. Cross-match specialist | AOIC is not yet an accepted canonical source registry. | Do not assert physical-source matches until evidence and tests exist. |
| 7. ML lead | The original frozen production artifact is still missing from accessible remote sources. | Keep inference disabled until recovery and independent authentication. |
| 8. Benchmark / validation lead | A green offline test suite does not prove external scientific performance. | Preserve source-backed skips as SKIPPED / NOT VERIFIED. |
| 9. Software architect | The existing API and static UI are reusable, but are not a desktop application. | Keep GUI, application service, scientific core, model, and adapters layered. |
| 10. Backend engineer | The current API binds to a fixed loopback port 8000. | Add managed process start/stop, ephemeral port, readiness, health and shutdown tests. |
| 11. MLOps / DevSecOps | Packaging a local API creates a local security boundary. | Loopback-only, per-process request protection, navigation controls, dependency and binary audit. |
| 12. QA / reliability | No Windows clean-machine installation evidence exists. | Test install, launch, upgrade, uninstall, process cleanup, missing runtime and offline start. |
| 13. Scientific UX/UI | The current Workbench is not yet guided for a non-developer Park evaluator. | Deliver user flows, Persian-first labels, explicit status language and keyboard support. |
| 14. Product manager | The first build must complete one valuable task end-to-end before broad feature expansion. | Prioritize DR24 retrieval → inspect → diagnose → export. |
| 15. Technical writer | The published README and installation guide contain stale or unverified claims. | Reconcile product status, model availability, installation instructions and release notes. |
| 16. Independent Red Team | Desktop shell must not expose local APIs or allow the UI to overstate validation. | Verify loopback isolation, token handling, external navigation, exports and claim controls. |

## 4. Consolidated decisions

1. The first target is a standalone Windows 11 application, as explicitly selected by the owner.
2. Persian is the proposed default for the Park demonstration; scientific abbreviations and names remain visible in English where needed.
3. UI/UX work proceeds in parallel with backend, scientific, and packaging work.
4. The first end-to-end value path is DR24 object selection, source retrieval, per-filter light-curve inspection, descriptive/QC view, provenance, and reproducible export.
5. Production classification and scientific metrics remain disabled until the matching model, feature, identity, and evaluation gates pass.
6. Use pywebview + the existing FastAPI/UI as the first candidate for a time-bounded engineering spike. This is provisional; keep PySide6 and Tauri as alternatives if packaging, security, reliability, or resource tests fail.
7. Prefer a PyInstaller one-folder build for internal testing. Build an installer only after the app runs on a clean Windows machine. One-file bundling is not the initial target.
8. The app must detect WebView2 Runtime availability. Windows 11 normally includes Evergreen WebView2, but runtime presence must still be checked at startup or installation.
9. No merge to main and no external release until the integrated head, science gates, local Windows acceptance and Issue #293 legal gate are reviewed.

## 5. Acceptance path

### Gate A — Desktop-shell feasibility
- local service starts on an available loopback port;
- readiness check succeeds before window launch;
- embedded view cannot navigate to untrusted external origins;
- service shuts down on app close and startup failure;
- WebView2 runtime detection is reliable;
- package starts on a clean Windows 11 environment.

### Gate B — Useful DR24 exploration
- supported object/query selection works;
- retrieved IDs and filters are explicit;
- data is plotted in source-native time and native magnitudes;
- quality flags and missing data are visible;
- source-native summaries are descriptive-only;
- exports pass schema and hash checks.

### Gate C — Scientific feature and inference
- DR24-to-v0.2 adapter passes Issue #305 requirements;
- exactly 42 features in frozen order, with no unapproved conversions or filters;
- original v0.2.0 artifact is recovered and independently authenticated;
- object-level, temporal and source-backed evaluation passes;
- probability calibration, abstention, OOD and anomaly outputs pass their own validation contracts.

### Gate D — Park distribution
- proprietary notice and third-party rights reviewed;
- limited written Park evaluation license approved;
- signed or checksum-verified installer;
- clean-machine install, launch, upgrade, uninstall and data-retention checks;
- release notes, limitations, help and handover guide complete.

## 6. Dissent and unresolved risk

- A web-rendered interface inside a native window can meet the operational meaning of a standalone desktop app, but it is not a fully native widget UI. The Park owner asked for independent desktop software, not specifically native widgets. The shell must be judged by install, reliability, privacy, and user tasks rather than by the implementation label.
- The first demonstrator can be useful before model recovery, but it cannot satisfy the full classification and scientific-performance claims in the form until the classifier gates pass.
- If the Park evaluation requires an offline demo, an approved small sample and a runtime/data bundle are needed. Do not package real datasets without provenance and redistribution review.

## 7. Review disposition

**DESIGN FOUNDATION ACCEPTED FOR SPIKE — RELEASE NOT APPROVED.**

The two companion documents are:
- `docs/product/WINDOWS_DESKTOP_UX_BRIEF_2026-11-24.md`
- `docs/architecture/ADR-001-WINDOWS-DESKTOP-SHELL.md`

No implementation or scientific acceptance is inferred from this review.


## 8. Follow-up review — exact Windows preview acceptance contract

**Review basis:** docs/acceptance/PARK_WINDOWS_DESKTOP_BETA_ACCEPTANCE_2026-11-24.md, current PR #310 head, API settings/state contracts, desktop runtime and Workbench source.

This follow-up applies the exact required user workflow. It does not treat the earlier design approval as implementation acceptance.

### New gaps confirmed by source inspection

| Requirement | Current evidence | Decision |
|---|---|---|
| Create or open a local workspace | Per-user directories and a persisted workspace_directory preference exist; no user-facing workspace lifecycle or manifest API exists | NOT IMPLEMENTED |
| Explicit source selection | DR24 endpoint is fixed to the HATS adapter; the Workbench does not require the user to select the source | NOT IMPLEMENTED |
| Reopen workspace and see last operation/status | Settings persist, but DR24 acquisition status and last operation are not persisted in a workspace record | NOT IMPLEMENTED |
| Export location and persistence | Browser JSON download exists; the current flow does not save a verified export inside a workspace | PARTIAL |
| Required analysis and QC screens | Chart, descriptive summary, raw rows and diagnostic QC appear in the DR24 result view; they are not yet separate guided views | PARTIAL |
| Clean Windows installer | Runtime tests and packaging workflow exist; clean target-machine acceptance is not complete | NOT VERIFIED |
| Park distribution | Issue #293 still requires written evaluation/demo terms | BLOCKED |

### Follow-up decisions by specialist seats

1. **Product and acceptance:** add a Welcome/Workspace flow before the Home screen. A default folder alone does not satisfy create/open.
2. **Data engineering:** require an explicit source selection and record the selected source in the request and provenance.
3. **Reproducibility:** persist the last operation, status, requested/returned/missing OIDs, timestamps and payload hashes in the active workspace.
4. **Application architecture:** use a versioned workspace manifest and atomic writes. Keep workspace state separate from scientific model state.
5. **Security:** constrain workspace IDs and paths to the per-user workspace root. Reject path traversal and invalid manifests.
6. **Scientific UX:** separate light-curve inspection from descriptive/QC summaries, while preserving raw values and the diagnostic-only claim boundary.
7. **Export engineering:** save the JSON export in the active workspace. Record its path, size and SHA-256. Keep the user download as an additional action.
8. **QA:** add API, store and browser tests for create, list, open, restart, interrupted operations, export and failure states.
9. **Windows engineering:** retain the managed loopback service, per-user storage, WebView2 detection and install/uninstall checks. Verify these again after workspace integration.
10. **Release and legal:** do not upload or distribute the installer until the written Park evaluation terms are approved. A CI build is not a distribution authorization.

### Required implementation order

1. Add a versioned workspace store under the per-user application data directory.
2. Add authenticated API contracts for create/list/open/active workspace, operation status and workspace export.
3. Add the Welcome/Workspace screen and persisted last-operation display.
4. Add an explicit ZTF DR24 HATS selection and include it in acquisition provenance.
5. Add separate Light-Curve Analysis and Quality/Summary views.
6. Add regression tests for persistence, path safety, restart and export hashes.
7. Re-run exact-head CI, Windows package/install tests and the pinned live DR24 browser workflow.
8. Complete target-device acceptance and the legal gate before Park handoff.

**Updated disposition: DESIGN FOUNDATION ACCEPTED; IMPLEMENTATION NOT YET ACCEPTED; DISTRIBUTION BLOCKED.**

The first preview remains distinct from the six-month full Park MVP. No classifier, calibrated probability, abstention, OOD or anomaly claim is added by this follow-up.
