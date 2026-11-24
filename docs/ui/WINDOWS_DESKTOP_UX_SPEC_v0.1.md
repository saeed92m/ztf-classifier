# Windows Desktop UX Specification — v0.1

**Date:** 2026-11-24  
**Status:** Design baseline for implementation review  
**Target:** First standalone Windows experimental release  
**Source design:** SCIENTIFIC_WORKBENCH_UI_v0.1  
**Scientific boundary:** DR24 raw inspection and descriptive summaries only until model gates pass

## 1. Product design goal

Enable a researcher to complete one real ZTF DR24 workflow without Python, Git or terminal commands:

**Open workspace → select source → retrieve object → inspect light curve → review QC and provenance → export evidence.**

Every screen must show what the software did, which data it used and what it did not establish. This is a scientific workbench, not a generic AI dashboard.

## 2. Primary user and tasks

Primary user: researcher or technical evaluator who understands astronomical objects and light curves but does not want developer tools.

Tasks:
1. Locate a DR24 object by OID.
2. Retrieve and inspect source-native observations.
3. Compare available filters without merging unrelated OIDs.
4. Review diagnostic QC and descriptive statistics.
5. Identify missing data and retrieval failures.
6. Export a reproducible record for review.

## 3. Information architecture

1. Home — workspace, connection and source status, recent runs.
2. Data Sources — DR24 connection, source description and retrieval history.
3. Object Explorer — OID search, records, filters and source metadata.
4. Light-Curve Analysis — plots and epoch table.
5. Quality & Summary — diagnostic QC and descriptive statistics.
6. Provenance — source, query, retrieval time, schema and hashes.
7. Reports & Export — JSON and run evidence.
8. Settings — language, theme, workspace, cache and logs.
9. Help — quick start, interpretation, known limits and troubleshooting.

Do not present model inference, calibrated confidence, conformal prediction, OOD or scientific anomaly analysis as active workflows until their gates pass.

## 4. Core screens

### 4.1 Home

Show product name and version, workspace path, local service state, DR24 source state, last retrieval and recent runs. Do not show fabricated counts, performance or discoveries.

Connection must distinguish:
- Local app ready.
- External network unavailable.
- DR24 source reachable.
- Last acquisition succeeded or failed.

### 4.2 Data Sources

Show ZTF DR24 HATS as the explicit source for this preview. Display release, service status, network requirement, supported fields, retrieval limitations and last checked time.

Do not switch silently to ALeRCE when DR24 fails. ALeRCE is a separate source and requires explicit selection.

### 4.3 Object Explorer

Controls: OID input, validation, retrieve action, recent OIDs, filter selector when applicable.

Result states: Retrieved, Missing, Empty, Partial, Rejected, Source Error.

Display objectid, filterid, available field/partition identifiers, and available coordinates/source metadata. Do not group OIDs by proximity or claim one astrophysical source without accepted AOIC evidence.

### 4.4 Light-Curve Analysis

- One plot per OID/filter by default.
- Explicit filter legend.
- X-axis uses actual source time scale. DR24 must show HMJD, never MJD.
- Y-axis identifies the native measurement and unit.
- Magnitude direction follows astronomical convention and is explained.
- Error bars represent reported magerr when available.
- Show epoch count, time span and missing/non-finite count.
- Keep raw observations available in a table.
- Do not convert time or photometry without a separately approved contract.

Interactions: pan, zoom, reset, filter toggle, point inspection and chart export. Raw-data export remains separate from chart export.

### 4.5 Quality & Summary

Keep three separate sections.

**Raw observation fields:** HMJD, mag, magerr, clrcoeff, catflags and available metadata.

**Diagnostic QC:** policy version/status, warnings, counts and reasons. State that diagnostic QC does not approve or exclude data for model inference.

**Descriptive summary:** raw epoch count, finite HMJD/magnitude pairs, HMJD span, unique and duplicate times, median interval between unique HMJD values, native magnitude min/median/max/P05/P95, median finite non-negative magerr, statistic definitions and percentile method.

Show **DESCRIPTIVE — NOT CLASSIFICATION** beside the summary. Do not call these values model features, variability scores, anomaly scores or confidence.

### 4.6 Provenance

Display source/release, query context, OID/filter, available partition identifiers, retrieval timestamp, payload hash, API/schema version, app version/commit, run ID, warnings and missing records.

Provide a copyable evidence summary. Attach provenance to JSON export. Do not expose secrets or private filesystem paths.

### 4.7 Reports & Export

Required first-release export:
- Raw DR24 records.
- Descriptive summary.
- Diagnostic QC.
- Retrieval metadata.
- Provenance and hashes.
- Software/schema version.
- Warnings and missing/rejected records.

JSON is mandatory. CSV can follow after field/missingness contracts are defined. PDF reporting follows after JSON stability.

### 4.8 Settings and Help

Settings: Persian/English language, theme, workspace directory, cache policy, log directory, retry policy and export path.

Help explains OID, HMJD, magnitude, magerr, catflags, diagnostic QC, source identity, current limitations and troubleshooting.

## 5. Visual language

Use current Workbench tokens as a starting point: Deep Space, Alpha blue, neutral surfaces, semantic warning/error/success and shared panel/card components.

Create shared components for status, source badge, quality notice, metric card, table, plot control, provenance row, empty/loading/error state.

Default the first domestic Park presentation to Persian. Preserve English scientific names and standard acronyms when translation could reduce precision. Language must not change data or exported values.

## 6. Interaction and accessibility

- Important actions are keyboard accessible.
- Focus state is visible.
- Status does not rely on colour alone.
- Table units appear in headers.
- Long retrieval shows progress, cancel and recovery.
- Repeated clicks do not create duplicate jobs.
- Warn before overwriting exports.
- A failed new request must not make an older result appear current.

## 7. Scientific claim controls

Capability state must come from application service or release configuration, not from the existence of a navigation item.

Use one of:
- AVAILABLE — tested and accepted.
- DIAGNOSTIC — inspection only.
- BLOCKED — gate not passed.
- NOT IMPLEMENTED — absent from this build.

When classification is blocked, hide/disable the action and explain why. Do not show sample, synthetic or stale predictions as live DR24 results. Do not label raw scores as calibrated probabilities. Keep OOD and scientific anomaly separate.

## 8. UX acceptance tests

A non-developer must be able to install and launch, create a workspace, find an OID, retrieve DR24 data, identify source/filter, read axes, locate QC/summary, distinguish missing from empty, inspect provenance, export JSON, reopen the app, and recover from network loss or local-service failure.

Record task completion and observed errors. An internal developer walkthrough alone does not pass usability acceptance.

## 9. Open design decisions

- Desktop shell: pywebview/WebView2 versus PySide6/WebEngine.
- Installer format and signing.
- Persian terminology review.
- Workspace and cache policy.
- CSV/PDF export need for the first Park presentation.
- Minimum Windows version and x64/ARM64 scope.

Reuse the current Workbench and API contracts where possible. Keep scientific calculations outside the GUI.
