# Think Tank Review — Park Windows Desktop Experimental Release

**Date:** 2026-11-24  
**Review type:** Evidence-led, simulated 16-role review with independent Red Team challenge  
**Primary tracker:** Issue #158  
**Decision authority:** Project owner  
**Status:** Initial convergence; implementation and acceptance remain open

## 1. Method and evidence

The review covers the submitted Park workbook AP-02-140503, current repository main, Park lab demonstrator runbook and roadmap, application/core boundary, product architecture, open PRs and recorded CI.

The 16 seats are role-based analytical perspectives. This is not a claim that 16 external human specialists participated. The project owner retains final decision authority. The Red Team must challenge assumptions.

### Verified facts

- Park workbook marks the current product state as a laboratory prototype with no sales.
- It describes a CPU-first ZTF light-curve platform for classification, candidate prioritisation, rare-object investigation, uncertainty and abstention, reporting and installable software.
- It defines a six-month four-phase plan: infrastructure/data/features; model; uncertainty/anomaly/validation; dashboard/documentation/commercialisation.
- It states that unimplemented or unvalidated capabilities are development objectives, not verified capabilities.
- Main has a Python package version 1.0.1, a CLI/API entry point and a browser Workbench.
- Package metadata requires Python >=3.11.5,<3.12 and does not yet define a desktop shell or Windows installer.
- API entry point currently binds to 127.0.0.1:8000.
- Application/core architecture says GUI must not bypass scientific logic or mutate model artifacts.
- Existing Park runbook describes bounded 1–10 OID DR24 retrieval, raw light-curve inspection, diagnostic QC, provenance and raw JSON export.
- The two pinned OIDs are separate survey OIDs. They are not proof of one physical source.
- Remote API/browser evidence exists for a small sample. It does not prove clean Windows installation.
- PR #307 is draft. It adds source-native per-OID descriptive statistics. The exact-head CI was still failing at the start of this review.
- Original production v0.2.0 artifact and DR24 feature compatibility are not established in current accessible evidence.
- AOIC identity, full predeclared cohort and written Park evaluation license remain blockers.

## 2. Findings from the 16 expert seats

### 01 — Chief Scientist / Principal Investigator
The first Park presentation must show a complete, traceable scientific workflow. It must not claim broad discovery before source identity, model and independent validation pass.

**Recommendation:** Present a real-data DR24 inspection and descriptive-analysis environment. Keep broader classification/discovery claims on the roadmap.

### 02 — ZTF Survey and Data Systems Specialist
DR24 values must remain source-native. HMJD, magnitude, magerr, clrcoeff and catflags have specific semantics.

**Recommendation:** Display HMJD explicitly. Do not apply unapproved catflags masks, convert photometry or silently switch to ALeRCE.

### 03 — Time-Domain Astrophysicist
Different OIDs, filters and partitions cannot be treated as one physical source by assumption. A two-OID demo does not prove multi-band association.

**Recommendation:** Use a predeclared, varied cohort only after identity evidence. Keep ambiguous and unmatched associations visible.

### 04 — Astronomical Statistics and Time-Series Specialist
Descriptive statistics aid inspection but are not automatically validated variability features. Duplicate times, finite values, measurement errors and cadence require explicit definitions.

**Recommendation:** Keep status DESCRIPTIVE_NOT_CLASSIFICATION. Do not present P05–P95 or cadence as a class or anomaly score.

### 05 — Astroinformatics and Big Data Architect
A full DR24 download is unnecessary for the first preview. The app needs bounded retrieval and a provenance-preserving workspace.

**Recommendation:** Start with a pinned small cohort; scale by resumable batches later. Preserve missing and partial records.

### 06 — Catalog and Cross-Matching Specialist
Survey OID, catalog entry, canonical object, observation and transient event are separate entities.

**Recommendation:** Complete the AOIC identity ledger before cross-OID or cross-catalog association. Do not infer identity from nearest-neighbour distance alone.

### 07 — Chief AI / Machine Learning Scientist
Current evidence does not establish an authenticated production model usable on DR24 inputs.

**Recommendation:** Do not expose live classification for this data path. Recover/authenticate v0.2.0 or define a separately versioned Park model with its own data, features and validation.

### 08 — ML Validation, Uncertainty and Benchmarking Scientist
A passing workflow contract is not scientific validation. Calibration, conformal coverage, abstention, OOD and anomaly outputs need separate evidence.

**Recommendation:** No confidence, calibrated probability, OOD-based discovery or anomaly claim on an unlabelled DR24 sample.

### 09 — Principal Software Architect
The existing Core/Application boundary is a sound starting point. The desktop UI must not duplicate scientific logic.

**Recommendation:** Keep the desktop presentation layer thin. Reuse the Workbench and API behind a desktop shell.

### 10 — Principal Backend and Platform Engineer
The server currently uses a fixed port. A desktop application needs managed startup, readiness checks and shutdown.

**Recommendation:** Add collision-safe port allocation, health check, timeout, cleanup and recovery. Store user data outside the installation directory.

### 11 — DevOps, MLOps, Security and Release Engineer
The Python package does not constitute desktop distribution.

**Recommendation:** Prototype pywebview/WebView2 and PySide6/WebEngine. Evaluate PyInstaller onedir first. Build on Windows. Check runtime, dependency, signing, installer, upgrade and legal requirements.

### 12 — QA and Reliability Engineer
Remote browser tests do not prove local Windows installation.

**Recommendation:** Make clean Windows install, start, shutdown, offline relaunch, live DR24 retrieval, export, upgrade and uninstall release gates.

### 13 — Scientific UX/UI and Visualization Architect
Current Workbench has a three-panel layout and reusable tokens, but the user journey is developer-oriented. Model-first indicators may confuse users when DR24 inference is blocked.

**Recommendation:** Redesign around Home → Data Sources → Object Explorer → Light-Curve Analysis → Quality/Summary → Provenance → Export. Label HMJD correctly, make blocked features explicit and add Persian UI for the domestic Park demonstration.

### 14 — Chief Product Officer / Commercialization Strategist
A Park reviewer needs one coherent workflow. A wide menu with inactive features weakens the product story.

**Recommendation:** Deliver a focused Windows preview. Keep the 100,000-light-curve cohort and independent model evaluation on the full six-month roadmap.

### 15 — Scientific Documentation and Research Communication Specialist
The application, workbook, README, handbook and release notes must use consistent claim language and version identities.

**Recommendation:** Ship Persian quick-start/demo guide, technical reference, source note, limitations, reproducibility bundle, release notes and checksums.

### 16 — Independent Red Team
The greatest risk is a convincing UI that hides wrong identity, source fallback, invalid model artifacts, unsupported calibration or missing legal permission.

**Recommendation:** Test missing/empty OIDs, source failure, port collision, local endpoint tampering, corrupted cache, export tampering, missing WebView2, blocked model, ambiguous identity and network loss.

## 3. Cross-expert synthesis

### Consensus decisions

1. The first preview must be a real and useful desktop product, not a slide-only mock-up.
2. Reuse the existing Workbench and application services. Do not replace the scientific Core.
3. First demonstrated features: DR24 raw retrieval, descriptive statistics, diagnostic QC, provenance and export.
4. Model inference remains blocked until artifact authentication and DR24 feature compatibility pass.
5. Start with a pinned small sample. The 100,000-light-curve target remains a full-Park-MVP gate.
6. Start UI/UX now and run it in parallel with desktop and backend engineering.
7. Verify the package on clean Windows, not only Linux CI.
8. Legal approval is a release blocker.
9. CPVS discrepancy remains unresolved and separate. Do not hide or change it to make the Park preview pass.

### Dissent and trade-offs

- The 17 November execution plan listed self-contained desktop installers as a non-goal for that compact milestone. The project owner later selected standalone Windows desktop delivery. This is an explicit product-scope change; update acceptance documents and do not mistake it for completed implementation.
- An embedded Workbench in a desktop shell is the lowest-change path, but it is not identical to a fully native control toolkit. Accept it only after desktop lifecycle, accessibility, security and performance tests.
- pywebview/WebView2 is a candidate, not a final choice. PySide6/WebEngine may have different packaging trade-offs.
- The workbook's six-month R&D plan remains the full product commitment. A small desktop preview cannot imply that all R&D phases are complete.

## 4. Ranked blockers

| ID | Severity | Blocker | Required closure |
|---|---|---|---|
| PWD-01 | CRITICAL | No verified desktop shell or installer | Build and test desktop shell/package |
| PWD-02 | CRITICAL | No clean Windows acceptance evidence | Clean Windows 11 install and end-to-end test |
| PWD-03 | HIGH | Fixed API port and unmanaged service lifecycle | Managed lifecycle and port/security tests |
| PWD-04 | HIGH | PR #307 exact-head CI not green | Fix lint and pass exact-head CI |
| PWD-05 | HIGH | PR #300/#302/#307 overlap | Fresh integration branch and conflict review |
| PWD-06 | HIGH | Written Park evaluation license missing | Approved legal terms |
| PWD-07 | HIGH | Original production model and DR24 feature parity unproven | Artifact authentication and feature contract |
| PWD-08 | HIGH | AOIC and multi-object cohort incomplete | Confirm identity and lock cohort |
| PWD-09 | MEDIUM | Existing UI is English and model-first | Persian-first user flow and usability test |
| PWD-10 | MEDIUM | Desktop framework unselected | Comparative prototype and architecture decision |

## 5. Execution order

### A. Stabilise DR24
1. Finish exact-head CI and test PR #307.
2. Review PR #300, #302 and #307 as one integrated change set. Do not merge blindly.
3. Create a fresh integration branch from a verified base and rerun tests.
4. Preserve v0.2.0.
5. Expand the OID sample only after availability and identity checks.

### B. Build Windows shell
1. Add desktop entry point and managed API lifecycle.
2. Prototype two shell candidates.
3. Test local endpoint security, port allocation, shutdown and user-data paths.
4. Build Windows x64 preview.
5. Build installer and test on clean Windows 11.
6. Retain commit, package hash, logs and screenshots.

### C. UI/UX
1. Use the companion UX specification.
2. Create wireframes for the nine core screens.
3. Implement retrieval and inspection first.
4. Add Persian language and review terminology.
5. Run non-developer usability tests.
6. Hide or block unsupported classification and discovery controls.

### D. Scientific evidence
1. Lock the diagnostic cohort.
2. Record source metadata and per-object retrieval status.
3. Complete AOIC evidence for multi-OID associations.
4. Validate diagnostic QC, summary schema and export.
5. Keep classifier claims blocked until model and feature gates pass.

### E. Release
1. Approve licensing and third-party component rights.
2. Build reproducible Windows package.
3. Complete security/dependency review.
4. Test clean install, start, offline relaunch, live retrieval, export, upgrade and uninstall.
5. Ship notes, limitations, checksum, SBOM and demo guide.
6. Assign release version only after reconciling desktop and Python package versions.

## 6. Initial release recommendation

**Recommended:** Windows desktop experimental preview for DR24 exploration and descriptive analysis.

**Not recommended:** Release as a validated 15-class DR24 classifier or completed rare-transient discovery engine.

**Verdict:** NOT READY FOR DISTRIBUTION.

A later verdict may become READY WITH LIMITATIONS after desktop, data, export, Windows, security and legal gates pass. The full Park MVP has a separate acceptance decision.

## 7. Evidence trail

- Submitted Park workbook AP-02-140503, sections 2–4 and pages 6–9.
- docs/architecture/APPLICATION_CORE_BOUNDARY.md
- docs/architecture/V1_PRODUCT_ARCHITECTURE.md
- docs/ui/SCIENTIFIC_WORKBENCH_UI_v0.1.md
- docs/acceptance/PARK_LABORATORY_DEMONSTRATOR_EXECUTION_PLAN_2026-11-17.md
- docs/acceptance/PARK_LABORATORY_DEMONSTRATOR_RUNBOOK_2026-11-18.md
- docs/roadmap/PARK_MVP_REAL_DATASET_END_TO_END_ACCEPTANCE_2026-11-17.md
- GitHub Issues #158 and #293
- PRs #297, #300, #302, #306 and #307
- main API entry point and pyproject.toml
- Microsoft WebView2, pywebview and PyInstaller documentation

These sources support the review. They do not mean the proposed desktop application is implemented.
